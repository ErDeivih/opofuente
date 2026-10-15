"""La bandeja del motor: se lee con todo lo que la provoca y se despacha con su evento (F18).

Tres cosas y las tres con una regla detrás:

1. **leer resuelve lo que la incidencia no guarda**, con `JOIN`: el tema, el apartado del que habla
   (por su `anchor`, que es el mismo ancla que usan los apuntes), el enunciado de la pregunta y el
   material del que salió. Se resuelve al leer y no se copia dentro de la fila porque las cuatro
   cosas cambian debajo de la incidencia —los apuntes se reescriben, una pregunta se corrige, una
   versión se sustituye— y una copia dentro sería una segunda versión de lo mismo, esta vieja.
   Los `JOIN` del apartado y del material son **externos**: una incidencia sin apartado
   (`sin_materia_en_el_indice`, la pregunta que no se pudo situar) sigue saliendo, y ese es el caso
   que más hay que mirar.
2. **despachar es una escritura auditada**: el estado, la nota y su evento entran en la **misma
   transacción**. La nota **no** viaja al evento —es texto de una persona, igual que el motivo del
   alumno—: el evento guarda qué estado había, cuál queda y si la incidencia llevaba nota, que es lo
   que hace falta para reconstruir el despacho sin copiar el contenido a la traza.
3. **contar no cuenta la página**: los cuatro números de las categorías y los cuatro de los estados
   salen de un `GROUP BY` sobre la tabla entera. Contar en Python las filas de una página con tope
   daría un número que miente, que es justo lo que el objetivo prohíbe heredar.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Select, func, inspect, or_, select, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql.elements import ColumnElement

from opofuente.domain.key_reliability import letras_de_clave, normalizar_letra
from opofuente.domain.notes_incidents import (
    MINIMO_COMPROBADO,
    UMBRAL_NO_FIABLE,
    IncidentCoverage,
    IncidentFilter,
    IncidentStatus,
    NotesIncident,
    Reclasificacion,
    ResolucionDeBandeja,
    fiabilidad_por_discrepancia,
    normalise_note,
    reviewed_at_for,
)
from opofuente.domain.topic_notes import CategoriaIncidencia, Motivo
from opofuente.domain.tray import ESTADOS_ESPERANDO, TrayRefusalError, TraySet
from opofuente.infrastructure.db_models import (
    AnswerKeyEntryRecord,
    AnswerKeyVersionRecord,
    AuditEventRecord,
    CurriculumNodeRecord,
    DocumentSectionRecord,
    DocumentVersionRecord,
    LogicalDocumentRecord,
    NotesIncidentRecord,
    OptionVersionRecord,
    QuestionNoteAnchorRecord,
    QuestionSetRecord,
    QuestionVersionRecord,
    TopicNoteSectionRecord,
)

#: La acción del evento de despacho, con el mismo vocabulario `objeto.verbo` que el resto.
ACCION_DESPACHO = "notes.incident_updated"

#: La acción del evento de la reclasificación del §2: la incidencia cambia de categoría.
ACCION_RECLASIFICACION = "notes.incident_reclassified"

#: Y la de la incidencia que **sale** de la bandeja porque no era una incidencia (falso positivo).
ACCION_RETIRADA = "notes.incident_dropped"

#: El objeto de la auditoría es **la incidencia**, no el tema: el despacho es de la incidencia.
OBJETO_INCIDENCIA = "note_incident"

#: La acción del despacho **en bloque** (F31): una incidencia de un conjunto que se decide entero.
#: Va aparte del despacho de una en una porque la decisión fue otra —«todo el conjunto»— y la
#: auditoría tiene que poder decir cuál de las dos se tomó.
ACCION_BLOQUE = "notes.incident_bulk_dispatched"

#: Y la del conjunto que se deja fuera de tests: es la misma escritura que la puerta de datos del §1
#: hace sola, pero aquí la pidió una persona y el evento lo dice.
ACCION_CLAVE_DERIVADA_ACEPTADA = "answer_key.derived_accepted"

#: La acción de la **resolución automática** (F31, §3): una regla cierra o propone una incidencia.
ACCION_RESOLUCION = "notes.incident_resolved_by_rule"


@dataclass(frozen=True, slots=True)
class IncidentProposal:
    """Una clave derivada que espera la aprobación del propietario, con sus dos fuentes.

    `letters` es la letra **derivada** —la que coinciden los apuntes con cita y una respuesta
    independiente del modelo—, y por eso es distinta de la clave que el conjunto tiene hoy: si
    coincidieran, no habría nada que proponer. Las dos fuentes viajan para que el propietario pueda
    juzgar la propuesta sin abrir la pregunta.
    """

    incident_id: str
    question_version_id: str
    set_id: str
    letters: tuple[str, ...]
    notes_letter: str
    model_letter: str
    quote: str | None


@dataclass(frozen=True, slots=True)
class BulkSummary:
    """Lo que hizo una acción en bloque: cuántas incidencias cerró y cuántas claves escribió."""

    action: str
    set_id: str
    incidents: int
    keys_written: int = 0


@dataclass(slots=True)
class _FilaEnConstruccion:
    """Un conjunto mientras se cuenta la bandeja: los datos fijos y lo que espera por categoría.

    Es un tipo con nombre y no un diccionario de objetos porque `mypy` en estricto no puede
    comprobar un `dict[str, object]` sin `type: ignore`, y un `ignore` en el sitio donde se cuenta
    la cifra de la medida de éxito es justo donde no se quiere.
    """

    title: str
    set_type: str
    origin_scope: str
    key_reliability: str
    pendientes: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReclassificationSummary:
    """Lo que hizo una pasada de reclasificación: cuántas cambiaron, cuántas salieron y el total."""

    actualizadas: int
    retiradas: int
    total: int


@dataclass(frozen=True, slots=True)
class IncidentEvidence:
    """Todo lo que hace falta para decidir la categoría de una incidencia, en una sola lectura.

    `letra`, `esperadas`, `resultado` y `frase_del_ancla` salen de la **comprobación** del motor
    (`question_note_anchors`), que es donde está lo que los apuntes contestaron de verdad: la
    incidencia guarda el desenlace que el motor contó, pero la comprobación de hoy es la que dice si
    la letra de los apuntes está en la clave (el falso positivo) y cuál es la frase que lo
    demuestra.
    """

    incident_id: str
    categoria: CategoriaIncidencia
    motivo: Motivo
    detalle: str
    phrase: str | None
    question_version_id: str
    question_set_id: str
    question_type: str
    stem: str
    opciones: tuple[str, ...]
    letra: str | None
    esperadas: tuple[str, ...]
    resultado: str | None
    frase_del_ancla: str | None


@dataclass(frozen=True, slots=True)
class KeyReliability:
    """La fiabilidad de las claves por conjunto, y **de dónde** ha salido.

    `fuente` viaja con el mapa a propósito: hay dos caminos posibles —la columna `question_sets.
    key_reliability` que añade el §1, o la regla del §1 calculada aquí como respaldo— y el informe
    del
    comando tiene que poder decir cuál se usó. Dos verdades calladas sobre lo mismo es lo que este
    campo evita.
    """

    por_conjunto: dict[str, str]
    fuente: str


#: Las siete piezas de una fila de la bandeja, en el orden en que las devuelve `_consulta`.
#:
#: Las tres últimas pueden ser **nulas** al leer: el apartado no existe cuando la pregunta no se
#: pudo situar en ninguna materia y el material falta cuando la pregunta no vino de un documento. Se
#: declaran como no nulas porque SQLAlchemy tipa el resultado de un `OUTER JOIN` igual que el de uno
#: interno —no los distingue—, y quien las consume (`_incidencia`) sí las acepta nulas.
_Fila = tuple[
    NotesIncidentRecord,
    CurriculumNodeRecord,
    QuestionVersionRecord,
    QuestionSetRecord,
    TopicNoteSectionRecord,
    LogicalDocumentRecord,
    DocumentVersionRecord,
]


class SqlAlchemyNotesIncidentRepository:
    """Lee la bandeja del motor y despacha las incidencias que el propietario ya ha decidido."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_incidents(self, filtro: IncidentFilter | None = None) -> tuple[NotesIncident, ...]:
        """Las incidencias, de la más nueva a la más vieja, con todo lo que las provoca resuelto."""
        efecto = filtro if filtro is not None else IncidentFilter()
        consulta = _consulta().order_by(
            NotesIncidentRecord.created_at.desc(), NotesIncidentRecord.id.desc()
        )
        if efecto.category is not None:
            consulta = consulta.where(NotesIncidentRecord.category == efecto.category.value)
        if efecto.status is not None:
            consulta = consulta.where(NotesIncidentRecord.status == efecto.status.value)
        if efecto.topic_code is not None:
            consulta = consulta.where(CurriculumNodeRecord.path == efecto.topic_code)
        if efecto.set_id is not None:
            # El `JOIN` de la pregunta ya está en `_consulta()`: aquí solo se filtra por su
            # conjunto, que es lo que despliega una fila de la bandeja agrupada.
            consulta = consulta.where(QuestionVersionRecord.question_set_id == efecto.set_id)
        if efecto.q is not None:
            consulta = consulta.where(_busqueda(efecto.q))
        consulta = consulta.limit(efecto.limit)
        with self._session_factory() as session:
            filas = session.execute(consulta).all()
        return tuple(
            _incidencia(incidencia, nodo, pregunta, conjunto, apartado, documento, version)
            for incidencia, nodo, pregunta, conjunto, apartado, documento, version in filas
        )

    def get(self, incident_id: str) -> NotesIncident | None:
        """Una incidencia por su identificador, resuelta como en la lista."""
        with self._session_factory() as session:
            fila = session.execute(_consulta().where(NotesIncidentRecord.id == incident_id)).first()
        if fila is None:
            return None
        return _incidencia(*fila)

    def count(
        self,
        *,
        category: CategoriaIncidencia | None = None,
        status: IncidentStatus | None = None,
        topic_code: str | None = None,
        set_id: str | None = None,
        q: str | None = None,
    ) -> int:
        """Cuántas incidencias hay con ese filtro, sin traerse las filas para contarlas.

        Los `JOIN` entran **solo si el filtro los necesita**, como en la bandeja del alumno: un
        recuento que arrastre siete tablas para decir «453» es trabajo tirado. Y se cuentan
        identificadores **distintos**: los `JOIN` son de uno a uno hoy, pero pedirle al `LEFT JOIN`
        que no duplique nada no es asunto de quien cuenta.
        """
        consulta = select(func.count(func.distinct(NotesIncidentRecord.id))).select_from(
            NotesIncidentRecord
        )
        if topic_code is not None:
            consulta = consulta.join(
                CurriculumNodeRecord,
                CurriculumNodeRecord.id == NotesIncidentRecord.curriculum_node_id,
            ).where(CurriculumNodeRecord.path == topic_code)
        if q is not None:
            consulta = consulta.join(
                QuestionVersionRecord,
                QuestionVersionRecord.id == NotesIncidentRecord.question_version_id,
            ).outerjoin(
                TopicNoteSectionRecord,
                (
                    TopicNoteSectionRecord.curriculum_node_id
                    == NotesIncidentRecord.curriculum_node_id
                )
                & (TopicNoteSectionRecord.anchor == NotesIncidentRecord.anchor),
            )
            consulta = consulta.where(_busqueda(q))
        if set_id is not None:
            consulta = consulta.join(
                QuestionVersionRecord,
                QuestionVersionRecord.id == NotesIncidentRecord.question_version_id,
            ).where(QuestionVersionRecord.question_set_id == set_id)
        if category is not None:
            consulta = consulta.where(NotesIncidentRecord.category == category.value)
        if status is not None:
            consulta = consulta.where(NotesIncidentRecord.status == status.value)
        with self._session_factory() as session:
            return int(session.execute(consulta).scalar_one())

    def counts_by_status(self) -> dict[IncidentStatus, int]:
        """Cuántas incidencias hay en cada estado. Los cuatro salen siempre, con cero incluido.

        Que salgan los cuatro con cero no es un detalle: quien pinta los filtros necesita saber que
        `dismissed` está vacío, y un diccionario al que le falte una clave obliga a la pantalla a
        inventarse el cero.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(NotesIncidentRecord.status, func.count()).group_by(
                    NotesIncidentRecord.status
                )
            ).all()
        contados: dict[IncidentStatus, int] = dict.fromkeys(IncidentStatus, 0)
        for estado, total in filas:
            contados[IncidentStatus(str(estado))] = int(total)
        return contados

    def counts_by_category(self) -> dict[CategoriaIncidencia, int]:
        """Cuántas incidencias hay de cada categoría. Las cuatro salen siempre, con cero incluido.

        Son **las cuatro cifras** de la bandeja, contadas en la base con un `GROUP BY`: es lo que
        permite decir cuántas hay de cada clase sin leerlas para contarlas, y sin heredar el número
        de ningún documento.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(NotesIncidentRecord.category, func.count()).group_by(
                    NotesIncidentRecord.category
                )
            ).all()
        contados: dict[CategoriaIncidencia, int] = dict.fromkeys(CategoriaIncidencia, 0)
        for categoria, total in filas:
            contados[CategoriaIncidencia(str(categoria))] = int(total)
        return contados

    def count_open(self) -> int:
        """Cuántas incidencias esperan a que alguien las mire. Es el número del menú."""
        return self.counts_by_status()[IncidentStatus.OPEN]

    def update(
        self,
        *,
        incident_id: str,
        status: IncidentStatus,
        note: str | None,
        actor: str,
        now: datetime,
    ) -> NotesIncident | None:
        """Despacha una incidencia: el estado, la nota y su evento, en una sola transacción.

        Devuelve la incidencia **tal como queda**, con todo lo que la provoca resuelto, para que la
        ruta pueda contestar con lo mismo que enseña la bandeja. `None` si no existe.

        Dos decisiones que se ven aquí:

        - la nota **no se borra** al cambiar de estado: si el propietario ya escribió «la clave está
          bien, los apuntes son los que sobran», volver a ponerla en curso no puede tirar eso. Solo
          se sustituye cuando esta operación trae otra cosa escrita;
        - `reviewed_at` lo decide el dominio (`reviewed_at_for`), y por eso reabrir una incidencia
          **borra** la fecha: la columna dice cuándo se despachó, y una incidencia abierta con fecha
          de revisión es una traza que miente.
        """
        limpia = normalise_note(note)
        with self._session_factory() as session:
            fila = session.get(NotesIncidentRecord, incident_id)
            if fila is None:
                return None
            antes = {
                "incident_id": incident_id,
                "status": str(fila.status),
                "has_note": fila.resolution_note is not None,
            }
            fila.status = status.value
            fila.reviewed_at = reviewed_at_for(status, now)
            if limpia is not None:
                fila.resolution_note = limpia
            despues = {
                "incident_id": incident_id,
                "status": status.value,
                "has_note": fila.resolution_note is not None,
            }
            session.add(
                AuditEventRecord(
                    id=str(uuid4()),
                    actor=actor,
                    action=ACCION_DESPACHO,
                    object_type=OBJETO_INCIDENCIA,
                    object_id=incident_id,
                    before_json=json.dumps(antes, ensure_ascii=False, sort_keys=True),
                    after_json=json.dumps(despues, ensure_ascii=False, sort_keys=True),
                    correlation_id=None,
                    created_at=now,
                )
            )
            session.commit()
        return self.get(incident_id)

    # ------------------------------------------------------------------ la reclasificación (§2)

    def reclassification_evidence(self) -> tuple[IncidentEvidence, ...]:
        """Lo que hace falta para reclasificar: la incidencia, su pregunta, sus opciones y su
        comprobación.

        Se lee **todo de una vez** y no pregunta a pregunta porque la reclasificación es una pasada
        sobre la bandeja entera: 453 consultas para leer 453 filas es la forma de tardar un minuto
        en
        lo que se hace en un segundo, y de paso el resultado es una foto coherente —las cuatro
        lecturas son de la misma transacción— en lugar de una mezcla de instantes distintos.
        """
        with self._session_factory() as session:
            incidencias = session.execute(
                select(NotesIncidentRecord, QuestionVersionRecord, QuestionSetRecord)
                .join(
                    QuestionVersionRecord,
                    QuestionVersionRecord.id == NotesIncidentRecord.question_version_id,
                )
                .join(
                    QuestionSetRecord, QuestionSetRecord.id == QuestionVersionRecord.question_set_id
                )
                .order_by(NotesIncidentRecord.id)
            ).all()
            opciones: dict[str, list[str]] = {}
            for pregunta_id, texto in session.execute(
                select(OptionVersionRecord.question_version_id, OptionVersionRecord.text).order_by(
                    OptionVersionRecord.position
                )
            ).all():
                opciones.setdefault(str(pregunta_id), []).append(str(texto))
            anclas: dict[tuple[str, str], QuestionNoteAnchorRecord] = {}
            for fila_ancla in session.execute(select(QuestionNoteAnchorRecord)).scalars():
                anclas[
                    (
                        str(fila_ancla.question_version_id),
                        str(fila_ancla.curriculum_node_id),
                    )
                ] = fila_ancla

        evidencias: list[IncidentEvidence] = []
        for incidencia, pregunta, conjunto in incidencias:
            comprobacion = anclas.get(
                (str(incidencia.question_version_id), str(incidencia.curriculum_node_id))
            )
            evidencias.append(
                IncidentEvidence(
                    incident_id=str(incidencia.id),
                    categoria=CategoriaIncidencia(str(incidencia.category)),
                    motivo=Motivo(str(incidencia.reason)),
                    detalle=str(incidencia.detail),
                    phrase=None if incidencia.phrase is None else str(incidencia.phrase),
                    question_version_id=str(incidencia.question_version_id),
                    question_set_id=str(conjunto.id),
                    question_type=str(pregunta.question_type),
                    stem=str(pregunta.stem),
                    opciones=tuple(opciones.get(str(pregunta.id), ())),
                    letra=(
                        None
                        if comprobacion is None or comprobacion.answer_letter is None
                        else str(comprobacion.answer_letter)
                    ),
                    esperadas=(
                        () if comprobacion is None else _letras(comprobacion.expected_letters)
                    ),
                    resultado=None if comprobacion is None else str(comprobacion.result),
                    frase_del_ancla=(
                        None
                        if comprobacion is None or comprobacion.quoted_sentence is None
                        else str(comprobacion.quoted_sentence)
                    ),
                )
            )
        return tuple(evidencias)

    def key_reliability(self) -> KeyReliability:
        """La fiabilidad de la clave de cada conjunto, con la columna del §1 si ya existe.

        Si la columna `question_sets.key_reliability` está, **manda ella**: es la que el §1 mantiene
        como puerta de datos permanente y la que el alumno acabará viendo. Si no está —este bloque
        llega antes—, se calcula aquí la regla del §1 (mínimo 15 comprobaciones, más del 30 % de
        discrepancias) para poder medir y publicar la reclasificación, y `fuente` lo dice.

        La columna se lee por su **nombre** (`SELECT id, key_reliability …`) y no por el modelo: no
        es
        de esta tanda y no está en `db_models.py`, así que traerla al modelo sería adelantar el
        trabajo del §1 y crear un choque de ficheros entre los dos bloques. Lo que sí se comprueba
        —con `inspect`— es que la columna existe antes de leerla.
        """
        with self._session_factory() as session:
            columnas = {
                str(columna["name"])
                for columna in inspect(session.get_bind()).get_columns("question_sets")
            }
            if "key_reliability" in columnas:
                mapa = {
                    str(set_id): str(estado)
                    for set_id, estado in session.execute(
                        text("SELECT id, key_reliability FROM question_sets")
                    ).all()
                    if estado is not None
                }
                return KeyReliability(
                    por_conjunto=mapa, fuente="la columna question_sets.key_reliability (§1)"
                )
        return KeyReliability(
            por_conjunto=self._discrepancia_por_conjunto(),
            fuente=(
                "calculada con la regla del §1 (mínimo "
                f"{MINIMO_COMPROBADO} comprobaciones, más del {UMBRAL_NO_FIABLE:.0%}) porque la "
                "columna key_reliability todavía no existe"
            ),
        )

    def _discrepancia_por_conjunto(self) -> dict[str, str]:
        """La regla del §1 medible hoy: por conjunto, cuántas letras de los apuntes contradicen la
        clave sobre las que se pudieron comprobar."""
        with self._session_factory() as session:
            conjunto_de = {
                str(pregunta_id): str(set_id)
                for pregunta_id, set_id in session.execute(
                    select(QuestionVersionRecord.id, QuestionVersionRecord.question_set_id)
                ).all()
            }
            cuenta: dict[str, list[int]] = {}
            for pregunta_id, letra, esperadas in session.execute(
                select(
                    QuestionNoteAnchorRecord.question_version_id,
                    QuestionNoteAnchorRecord.answer_letter,
                    QuestionNoteAnchorRecord.expected_letters,
                ).where(QuestionNoteAnchorRecord.answer_letter.is_not(None))
            ).all():
                set_id = conjunto_de.get(str(pregunta_id))
                if set_id is None or not _letras(esperadas):
                    continue
                par = cuenta.setdefault(set_id, [0, 0])
                par[1] += 1
                if str(letra).strip().lower() not in _letras(esperadas):
                    par[0] += 1
        fiabilidad: dict[str, str] = {}
        for set_id, (mal, comprobadas) in cuenta.items():
            estado = fiabilidad_por_discrepancia(mal, comprobadas)
            if estado is not None:
                fiabilidad[set_id] = estado
        return fiabilidad

    def reclassify(
        self, cambios: Sequence[Reclasificacion], *, actor: str, now: datetime
    ) -> ReclassificationSummary:
        """Reescribe la categoría de una tanda y saca de la bandeja las que no lo son.

        Es la escritura del §2 del documento de ajustes, y va por aquí —y no por un `UPDATE` suelto—
        por las mismas razones que el despacho: cada cambio deja su **evento de auditoría** con lo
        que había y lo que queda, y los cambios de una tanda entran en **una sola transacción**, así
        que una ejecución interrumpida no deja media bandeja reclasificada.

        Lo que **no** hace: tocar el estado (`status`). Una incidencia reclasificada es el mismo
        hallazgo con la etiqueta que le tocaba, y si alguien ya la había puesto en curso o la había
        despachado, eso es su decisión y no la de este comando. El motor hace lo mismo cuando vuelve
        a
        comprobar un tema.
        """
        actualizadas = 0
        retiradas = 0
        with self._session_factory() as session:
            for cambio in cambios:
                fila = session.get(NotesIncidentRecord, cambio.incident_id)
                if fila is None:
                    continue
                antes = {
                    "incident_id": cambio.incident_id,
                    "category": str(fila.category),
                }
                if cambio.categoria is None:
                    session.delete(fila)
                    retiradas += 1
                    despues = {"incident_id": cambio.incident_id, "category": None}
                    accion = ACCION_RETIRADA
                else:
                    fila.category = cambio.categoria.value
                    fila.detail = cambio.detalle
                    if cambio.phrase is not None:
                        fila.phrase = cambio.phrase
                    actualizadas += 1
                    despues = {
                        "incident_id": cambio.incident_id,
                        "category": cambio.categoria.value,
                    }
                    accion = ACCION_RECLASIFICACION
                session.add(
                    AuditEventRecord(
                        id=str(uuid4()),
                        actor=actor,
                        action=accion,
                        object_type=OBJETO_INCIDENCIA,
                        object_id=cambio.incident_id,
                        before_json=json.dumps(antes, ensure_ascii=False, sort_keys=True),
                        after_json=json.dumps(despues, ensure_ascii=False, sort_keys=True),
                        correlation_id=None,
                        created_at=now,
                    )
                )
            session.commit()
        return ReclassificationSummary(
            actualizadas=actualizadas, retiradas=retiradas, total=len(cambios)
        )

    # --------------------------------------------------- la bandeja por conjunto (F31, §2)

    def resolve_by_rule(
        self, resoluciones: Sequence[ResolucionDeBandeja], *, actor: str, now: datetime
    ) -> ReclassificationSummary:
        """Aplica la resolución automática del §3: cierra lo que decide una regla, propone lo demás.

        Lo que la distingue de `reclassify` (y por lo que no se reutiliza) es que **no borra nada**:
        un falso positivo se marca `dismissed` y su fila se queda, porque el motor vuelve a
        comprobar los temas y «los falsos positivos ya descartados no vuelven a entrar» exige que
        haya algo que lo recuerde. El motor respeta estas columnas al reescribir (desde `0035`), así
        que la decisión sobrevive a la corrida siguiente.

        Solo toca incidencias que **siguen esperando** (`open`): una que el propietario ya puso en
        curso o resolvió es su decisión, y una regla no la reabre. En cambio, `propuesta_lista` sí
        vuelve a resolver, porque una propuesta no es una decisión: es lo que una regla dejó dicho.
        """
        actualizadas = 0
        retiradas = 0
        with self._session_factory() as session:
            for resolucion in resoluciones:
                fila = session.get(NotesIncidentRecord, resolucion.incident_id)
                if fila is None:
                    continue
                if str(fila.status) not in {
                    IncidentStatus.OPEN.value,
                    IncidentStatus.PROPUESTA_LISTA.value,
                }:
                    continue
                antes = {
                    "incident_id": resolucion.incident_id,
                    "category": str(fila.category),
                    "status": str(fila.status),
                }
                fila.status = resolucion.status.value
                fila.reviewed_at = reviewed_at_for(resolucion.status, now)
                fila.resolution_note = resolucion.note
                if resolucion.status is IncidentStatus.DISMISSED:
                    retiradas += 1
                else:
                    actualizadas += 1
                despues = {
                    "incident_id": resolucion.incident_id,
                    "category": str(fila.category),
                    "status": resolucion.status.value,
                }
                session.add(
                    AuditEventRecord(
                        id=str(uuid4()),
                        actor=actor,
                        action=ACCION_RESOLUCION,
                        object_type=OBJETO_INCIDENCIA,
                        object_id=resolucion.incident_id,
                        before_json=json.dumps(antes, ensure_ascii=False, sort_keys=True),
                        after_json=json.dumps(despues, ensure_ascii=False, sort_keys=True),
                        correlation_id=None,
                        created_at=now,
                    )
                )
            session.commit()
        return ReclassificationSummary(
            actualizadas=actualizadas, retiradas=retiradas, total=len(resoluciones)
        )

    def tray_sets(self) -> tuple[TraySet, ...]:
        """La bandeja agrupada por **conjunto de origen**: una fila por conjunto, con lo que espera.

        Se cuenta en la base con un `GROUP BY` de dos columnas —estado y categoría— y no en Python
        sobre la lista entera: la bandeja tiene cientos de filas y la pantalla solo necesita los
        números de cada conjunto.

        Los conjuntos **sin nada pendiente no salen**: una fila que no hay que atender es ruido en
        una bandeja que existe justo para que no lo haya. Las que sí salen traen sus dos cifras
        separadas —lo que espera criterio y lo que ya está propuesto—, porque significan cosas
        distintas y la medida de éxito del §2.4 se cuenta con la primera.
        """
        with self._session_factory() as session:
            conteos = session.execute(
                select(
                    QuestionSetRecord.id,
                    QuestionSetRecord.title,
                    QuestionSetRecord.set_type,
                    QuestionSetRecord.origin_scope,
                    QuestionSetRecord.key_reliability,
                    NotesIncidentRecord.status,
                    NotesIncidentRecord.category,
                    func.count(NotesIncidentRecord.id),
                )
                .join(
                    QuestionVersionRecord,
                    QuestionVersionRecord.id == NotesIncidentRecord.question_version_id,
                )
                .join(
                    QuestionSetRecord, QuestionSetRecord.id == QuestionVersionRecord.question_set_id
                )
                .where(
                    NotesIncidentRecord.status.in_(
                        [
                            estado.value
                            for estado in (*ESTADOS_ESPERANDO, IncidentStatus.PROPUESTA_LISTA)
                        ]
                    )
                )
                .group_by(
                    QuestionSetRecord.id,
                    NotesIncidentRecord.status,
                    NotesIncidentRecord.category,
                )
            ).all()
            plantillas = {
                str(set_id)
                for (set_id,) in session.execute(
                    select(AnswerKeyVersionRecord.question_set_id)
                    .where(AnswerKeyVersionRecord.source_document_version_id.is_not(None))
                    .distinct()
                ).all()
            }

        acumulado: dict[str, _FilaEnConstruccion] = {}
        for set_id, titulo, tipo, origen, fiabilidad, estado, categoria, cuantas in conteos:
            clave = str(set_id)
            fila = acumulado.setdefault(
                clave,
                _FilaEnConstruccion(
                    title=str(titulo),
                    set_type=str(tipo),
                    origin_scope=str(origen),
                    key_reliability=str(fiabilidad),
                ),
            )
            if str(estado) == IncidentStatus.PROPUESTA_LISTA.value:
                # Una propuesta **no** se cuenta aquí: lo que el conjunto tiene propuesto lo dice
                # `proposals()`, que es la única fuente de las propuestas, y contarlas en los dos
                # sitios las contaría dos veces. El estado `propuesta_lista` solo sirve para que la
                # corrida de resolución deje dicho qué ya está resuelto por regla.
                continue
            fila.pendientes[str(categoria)] = int(cuantas)

        return tuple(
            TraySet(
                set_id=set_id,
                title=fila.title,
                set_type=fila.set_type,
                origin_scope=fila.origin_scope,
                key_reliability=fila.key_reliability,
                tiene_plantilla_enlazada=set_id in plantillas,
                pendientes=dict(fila.pendientes),
            )
            for set_id, fila in acumulado.items()
        )

    def tray_set(self, set_id: str) -> TraySet | None:
        """Un conjunto con lo que espera, **aunque ya no quede nada pendiente**, o `None` si no hay.

        Es la lectura que necesita una acción en bloque para ser idempotente: la segunda pasada no
        encuentra la fila en la bandeja —la primera la cerró— y tiene que poder contestar «cero» en
        vez de «no existe». Una acción que se puede pedir dos veces y la segunda revienta no es
        idempotente; es frágil.
        """
        with self._session_factory() as session:
            fila = session.get(QuestionSetRecord, set_id)
            if fila is None:
                return None
            pendientes = session.execute(
                select(NotesIncidentRecord.category, func.count(NotesIncidentRecord.id))
                .join(
                    QuestionVersionRecord,
                    QuestionVersionRecord.id == NotesIncidentRecord.question_version_id,
                )
                .where(
                    QuestionVersionRecord.question_set_id == set_id,
                    NotesIncidentRecord.status.in_([estado.value for estado in ESTADOS_ESPERANDO]),
                )
                .group_by(NotesIncidentRecord.category)
            ).all()
            plantilla = session.execute(
                select(AnswerKeyVersionRecord.id)
                .where(
                    AnswerKeyVersionRecord.question_set_id == set_id,
                    AnswerKeyVersionRecord.source_document_version_id.is_not(None),
                )
                .limit(1)
            ).first()
        return TraySet(
            set_id=set_id,
            title=str(fila.title),
            set_type=str(fila.set_type),
            origin_scope=str(fila.origin_scope),
            key_reliability=str(fila.key_reliability),
            tiene_plantilla_enlazada=plantilla is not None,
            pendientes={str(categoria): int(cuantas) for categoria, cuantas in pendientes},
        )

    def proposals(self) -> tuple[IncidentProposal, ...]:
        """Las claves derivadas que esperan aprobación, con sus dos fuentes.

        La tabla `question_derived_keys` la escribe la ruta de las claves derivadas (el §1 del
        encargo), y **puede no estar**: este bloque llega antes que su migración. Cuando no está, no
        hay propuestas y se dice —que es distinto de decir que no hay ninguna pendiente—, con el
        mismo patrón que ya usa `key_reliability()` para la columna del §1: se comprueba con
        `inspect` antes de leer, y no se adelanta el trabajo de otro bloque.

        Una propuesta es una fila de esa tabla con `key_state = 'derived'` cuya letra **no está** en
        la clave que el conjunto tiene hoy: si estuviera, el motor ya la habría dado por buena y
        habría incidencia que aprobar.
        """
        with self._session_factory() as session:
            if not inspect(session.get_bind()).has_table("question_derived_keys"):
                return ()
            filas = session.execute(
                text(
                    "SELECT i.id, i.question_version_id, v.question_set_id, "
                    "       d.correct_option_keys_json, d.notes_letter, d.model_letter, "
                    "       d.notes_quote, a.expected_letters "
                    "  FROM notes_incidents i "
                    "  JOIN question_versions v ON v.id = i.question_version_id "
                    "  JOIN question_derived_keys d "
                    "    ON d.question_version_id = i.question_version_id "
                    "  LEFT JOIN question_note_anchors a "
                    "    ON a.question_version_id = i.question_version_id "
                    "   AND a.curriculum_node_id = i.curriculum_node_id "
                    " WHERE i.status IN ('open', 'in_progress', 'propuesta_lista') "
                    "   AND i.category IN ('clave_sospechosa', 'clave_no_fiable') "
                    "   AND d.key_state = 'derived'"
                )
            ).all()

        propuestas: list[IncidentProposal] = []
        for fila in filas:
            letras = letras_de_clave(None if fila[3] is None else str(fila[3]))
            if len(letras) != 1:
                continue
            esperadas = {
                normalizar_letra(cual)
                for cual in letras_de_clave(None if fila[7] is None else str(fila[7]))
            }
            if letras[0] in esperadas:
                continue
            propuestas.append(
                IncidentProposal(
                    incident_id=str(fila[0]),
                    question_version_id=str(fila[1]),
                    set_id=str(fila[2]),
                    letters=letras,
                    notes_letter=normalizar_letra(None if fila[4] is None else str(fila[4])),
                    model_letter=normalizar_letra(None if fila[5] is None else str(fila[5])),
                    quote=None if fila[6] is None else str(fila[6]),
                )
            )
        return tuple(propuestas)

    def accept_derived(
        self,
        *,
        set_id: str,
        plan: Sequence[IncidentProposal],
        note: str,
        actor: str,
        now: datetime,
    ) -> BulkSummary:
        """Acepta en bloque las claves derivadas de un conjunto, y cierra sus incidencias.

        Escribe la letra derivada en la entrada de la **clave que manda** en el conjunto —la activa
        y, si no hay ninguna activa todavía, la última plantilla, la misma regla con la que la
        lee el banco— y deja la incidencia resuelta. Las dos escrituras y sus eventos entran en
        **una sola transacción**: una aprobación a medias dejaría claves escritas sin su incidencia
        cerrada, o al revés.

        Lo que **no** hace, a propósito: comprobar si el conjunto es oficial. Eso lo decide
        `protege_cambiar_la_clave` y lo comprueba el servicio antes de llamar; aquí solo se escribe
        lo que se ha aprobado.
        """
        escritas = 0
        cerradas = 0
        with self._session_factory() as session:
            clave = self._manda_la_clave(session, set_id)
            if clave is None:
                raise TrayRefusalError(
                    "este conjunto no tiene ninguna plantilla de respuestas donde escribir la "
                    "clave derivada: no hay nada que aprobar"
                )
            for propuesta in plan:
                entrada = session.execute(
                    select(AnswerKeyEntryRecord).where(
                        AnswerKeyEntryRecord.answer_key_version_id == clave.id,
                        AnswerKeyEntryRecord.question_version_id == propuesta.question_version_id,
                    )
                ).scalar_one_or_none()
                if entrada is not None:
                    nuevo = json.dumps(list(propuesta.letters), ensure_ascii=False)
                    if str(entrada.correct_option_keys_json) != nuevo:
                        antes = str(entrada.correct_option_keys_json)
                        entrada.correct_option_keys_json = nuevo
                        escritas += 1
                        session.add(
                            AuditEventRecord(
                                id=str(uuid4()),
                                actor=actor,
                                action=ACCION_CLAVE_DERIVADA_ACEPTADA,
                                object_type="question_version",
                                object_id=propuesta.question_version_id,
                                before_json=json.dumps(
                                    {"correct_option_keys": antes}, ensure_ascii=False
                                ),
                                after_json=json.dumps(
                                    {
                                        "correct_option_keys": nuevo,
                                        "from": "derived",
                                        "notes_letter": propuesta.notes_letter,
                                        "model_letter": propuesta.model_letter,
                                    },
                                    ensure_ascii=False,
                                ),
                                correlation_id=None,
                                created_at=now,
                            )
                        )
                if self._cerrar(
                    session,
                    incident_id=propuesta.incident_id,
                    status=IncidentStatus.REVIEWED,
                    note=note,
                    actor=actor,
                    now=now,
                    action=ACCION_BLOQUE,
                    extra={"set_id": set_id, "letters": list(propuesta.letters)},
                ):
                    cerradas += 1
            session.commit()
        return BulkSummary(
            action="aceptar_derivadas", set_id=set_id, incidents=cerradas, keys_written=escritas
        )

    def leave_out(self, *, set_id: str, note: str, actor: str, now: datetime) -> BulkSummary:
        """Deja el conjunto fuera de tests y cierra lo que esperaba criterio dentro de él.

        El veredicto (`key_reliability`) **no** se escribe aquí: lo escribe la ruta auditada que ya
        existe para eso (`SqlAlchemyKeyReliabilityRepository.set_verdict`), y este método solo
        cierra las incidencias, para que no haya dos sitios que decidan lo mismo.
        """
        return self._cerrar_todo(
            set_id=set_id,
            status=IncidentStatus.REVIEWED,
            note=note,
            actor=actor,
            now=now,
            action="dejar_fuera",
        )

    def close_as_not_questions(
        self, *, set_id: str, note: str, actor: str, now: datetime
    ) -> BulkSummary:
        """Saca de la bandeja lo que hay en un conjunto que no son preguntas contestables.

        Las preguntas salen del temario por la ruta auditada de siempre
        (`QuestionService.apply_topic_batch`, con `enunciado_roto`), que escribe la marca y
        su evento; aquí solo se cierra la bandeja, que es de lo que este repositorio es dueño.
        """
        return self._cerrar_todo(
            set_id=set_id,
            status=IncidentStatus.NO_SON_PREGUNTAS,
            note=note,
            actor=actor,
            now=now,
            action="no_son_preguntas",
        )

    def question_ids_of_set(self, set_id: str) -> tuple[str, ...]:
        """Las preguntas que este conjunto tiene **dentro de la bandeja**, sin repetir.

        Es lo que la acción «no son preguntas» saca del temario: lo que está señalado, no el banco
        entero. Sacar del temario las 900 preguntas de un conjunto porque tres estén rotas sería
        exactamente el daño que esta bandeja viene a evitar.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(NotesIncidentRecord.question_version_id)
                .join(
                    QuestionVersionRecord,
                    QuestionVersionRecord.id == NotesIncidentRecord.question_version_id,
                )
                .where(
                    QuestionVersionRecord.question_set_id == set_id,
                    NotesIncidentRecord.status.in_([estado.value for estado in ESTADOS_ESPERANDO]),
                )
                .distinct()
            ).all()
        return tuple(str(fila[0]) for fila in filas)

    def _cerrar_todo(
        self,
        *,
        set_id: str,
        status: IncidentStatus,
        note: str,
        actor: str,
        now: datetime,
        action: str,
    ) -> BulkSummary:
        """Cierra de una vez lo que espera criterio en un conjunto, con su evento por incidencia."""
        cerradas = 0
        with self._session_factory() as session:
            ids = [
                str(fila[0])
                for fila in session.execute(
                    select(NotesIncidentRecord.id)
                    .join(
                        QuestionVersionRecord,
                        QuestionVersionRecord.id == NotesIncidentRecord.question_version_id,
                    )
                    .where(
                        QuestionVersionRecord.question_set_id == set_id,
                        NotesIncidentRecord.status.in_(
                            [estado.value for estado in ESTADOS_ESPERANDO]
                        ),
                    )
                ).all()
            ]
            for incident_id in ids:
                if self._cerrar(
                    session,
                    incident_id=incident_id,
                    status=status,
                    note=note,
                    actor=actor,
                    now=now,
                    action=ACCION_BLOQUE,
                    extra={"set_id": set_id, "bulk": action},
                ):
                    cerradas += 1
            session.commit()
        return BulkSummary(action=action, set_id=set_id, incidents=cerradas)

    def _cerrar(
        self,
        session: Session,
        *,
        incident_id: str,
        status: IncidentStatus,
        note: str,
        actor: str,
        now: datetime,
        action: str,
        extra: Mapping[str, object],
    ) -> bool:
        """Cierra una incidencia dentro de la transacción que le pasa quien llama.

        Devuelve `False` si la incidencia ya no estaba esperando: es lo que hace **idempotente** una
        acción en bloque. Aplicarla dos veces no vuelve a escribir ni a proponer nada, porque la
        segunda pasada encuentra las incidencias ya cerradas y no las toca.
        """
        fila = session.get(NotesIncidentRecord, incident_id)
        if fila is None or str(fila.status) not in {estado.value for estado in ESTADOS_ESPERANDO}:
            return False
        antes = {"incident_id": incident_id, "status": str(fila.status)}
        fila.status = status.value
        fila.reviewed_at = reviewed_at_for(status, now)
        fila.resolution_note = note
        despues: dict[str, object] = {
            "incident_id": incident_id,
            "status": status.value,
            **extra,
        }
        session.add(
            AuditEventRecord(
                id=str(uuid4()),
                actor=actor,
                action=action,
                object_type=OBJETO_INCIDENCIA,
                object_id=incident_id,
                before_json=json.dumps(antes, ensure_ascii=False, sort_keys=True),
                after_json=json.dumps(despues, ensure_ascii=False, sort_keys=True),
                correlation_id=None,
                created_at=now,
            )
        )
        return True

    @staticmethod
    def _manda_la_clave(session: Session, set_id: str) -> AnswerKeyVersionRecord | None:
        """La clave que manda en un conjunto: la activa y, si no la hay, la última plantilla.

        Es la misma regla con la que el banco lee la clave de una pregunta (`_active_entries`), y se
        repite aquí a propósito: si escribiéramos en una plantilla que la pantalla no lee, la clave
        aprobada no le llegaría a nadie.
        """
        claves = (
            session.execute(
                select(AnswerKeyVersionRecord).where(
                    AnswerKeyVersionRecord.question_set_id == set_id
                )
            )
            .scalars()
            .all()
        )
        if not claves:
            return None
        return sorted(
            claves, key=lambda fila: (str(fila.status) == "active", int(fila.version_no))
        )[-1]


def _consulta() -> Select[_Fila]:
    """La incidencia con su tema, su apartado, su pregunta y el material del que salió.

    El `JOIN` con el apartado va por el **ancla** y no por `section_key`: el motor guarda el ancla
    del apartado del que habla (es la dirección que entienden los apuntes) y deja `section_key` nulo
    —medido en la base real, el 13 de octubre de 2026: **0 de 453** lo tienen—, así que unir por
    `section_key` no encontraría ni un apartado. El ancla sí casa: **449 de las 453**.
    """
    return (
        select(
            NotesIncidentRecord,
            CurriculumNodeRecord,
            QuestionVersionRecord,
            QuestionSetRecord,
            TopicNoteSectionRecord,
            LogicalDocumentRecord,
            DocumentVersionRecord,
        )
        .join(
            CurriculumNodeRecord,
            CurriculumNodeRecord.id == NotesIncidentRecord.curriculum_node_id,
        )
        .join(
            QuestionVersionRecord,
            QuestionVersionRecord.id == NotesIncidentRecord.question_version_id,
        )
        .join(QuestionSetRecord, QuestionSetRecord.id == QuestionVersionRecord.question_set_id)
        .outerjoin(
            TopicNoteSectionRecord,
            (TopicNoteSectionRecord.curriculum_node_id == NotesIncidentRecord.curriculum_node_id)
            & (TopicNoteSectionRecord.anchor == NotesIncidentRecord.anchor),
        )
        .outerjoin(
            DocumentSectionRecord,
            DocumentSectionRecord.id == QuestionVersionRecord.source_section_id,
        )
        .outerjoin(
            DocumentVersionRecord,
            DocumentVersionRecord.id == DocumentSectionRecord.document_version_id,
        )
        .outerjoin(
            LogicalDocumentRecord,
            LogicalDocumentRecord.id == DocumentVersionRecord.logical_document_id,
        )
    )


def _letras(texto: str | None) -> tuple[str, ...]:
    """Las letras esperadas de una comprobación, que viajan como JSON en una columna de texto.

    La columna la escribe el motor como `["a"]`; se defiende de un texto suelto —una fila vieja o de
    una migración a medias— porque una excepción aquí tumbaría la reclasificación entera por una
    fila.
    """
    if texto is None:
        return ()
    try:
        cargado = json.loads(texto)
    except json.JSONDecodeError:
        return tuple(parte.strip() for parte in texto.split(",") if parte.strip())
    return tuple(str(cual).strip() for cual in cargado if str(cual).strip())


def _busqueda(texto: str) -> ColumnElement[bool]:
    """El filtro de la búsqueda: el enunciado, el motivo, la frase citada o el título del apartado.

    `LIKE` sin `lower()` a propósito: SQLite ya compara `LIKE` sin distinguir mayúsculas en ASCII, y
    envolver la columna en una función impediría usar el índice si algún día lo hay. Lo que no
    iguala son los acentos («version» no encuentra «versión»), y eso se dice en la pantalla.
    """
    patron = f"%{texto.strip()}%"
    return or_(
        QuestionVersionRecord.stem.like(patron),
        NotesIncidentRecord.detail.like(patron),
        NotesIncidentRecord.phrase.like(patron),
        TopicNoteSectionRecord.title.like(patron),
    )


def _incidencia(
    incidencia: NotesIncidentRecord,
    nodo: CurriculumNodeRecord,
    pregunta: QuestionVersionRecord,
    conjunto: QuestionSetRecord,
    apartado: TopicNoteSectionRecord | None,
    documento: LogicalDocumentRecord | None,
    version: DocumentVersionRecord | None,
) -> NotesIncident:
    """La fila de la bandeja con lo que la provoca, ya resuelto."""
    return NotesIncident(
        id=str(incidencia.id),
        node_id=str(incidencia.curriculum_node_id),
        question_version_id=str(incidencia.question_version_id),
        group_signature=str(incidencia.group_signature),
        category=CategoriaIncidencia(str(incidencia.category)),
        reason=Motivo(str(incidencia.reason)),
        coverage=IncidentCoverage(str(incidencia.coverage)),
        detail=str(incidencia.detail),
        attempts=int(incidencia.attempts),
        created_at=incidencia.created_at,
        status=IncidentStatus(str(incidencia.status)),
        reviewed_at=incidencia.reviewed_at,
        resolution_note=(
            None if incidencia.resolution_note is None else str(incidencia.resolution_note)
        ),
        phrase=None if incidencia.phrase is None else str(incidencia.phrase),
        section_key="" if incidencia.section_key is None else str(incidencia.section_key),
        anchor="" if incidencia.anchor is None else str(incidencia.anchor),
        section_title=None if apartado is None else str(apartado.title),
        topic_code=str(nodo.path),
        topic_title=str(nodo.title),
        stem=str(pregunta.stem),
        set_title=str(conjunto.title),
        source_document_id=None if documento is None else str(documento.id),
        source_document_title=None if documento is None else str(documento.canonical_title),
        source_document_type=None if documento is None else str(documento.document_type),
        source_version_status=None if version is None else str(version.status),
        source_version_label=(
            None if version is None or version.version_label is None else str(version.version_label)
        ),
    )


__all__ = [
    "ACCION_BLOQUE",
    "ACCION_CLAVE_DERIVADA_ACEPTADA",
    "ACCION_DESPACHO",
    "ACCION_RECLASIFICACION",
    "ACCION_RESOLUCION",
    "ACCION_RETIRADA",
    "OBJETO_INCIDENCIA",
    "BulkSummary",
    "IncidentEvidence",
    "IncidentProposal",
    "KeyReliability",
    "ReclassificationSummary",
    "SqlAlchemyNotesIncidentRepository",
]
