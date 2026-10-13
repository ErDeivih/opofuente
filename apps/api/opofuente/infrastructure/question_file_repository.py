"""La ficha de pregunta: lo que falta leer para decidirla y las dos escrituras auditadas (F20).

Tres cosas y las tres con una regla detrás:

1. **leer lo que la ficha necesita y no está en la pregunta**: de qué material salió la clave y en
qué
   estado está esa versión, qué contestaron los apuntes con la frase que lo demuestra, qué señaló el
   motor, si la pregunta está fuera del temario, y el veredicto de fiabilidad del conjunto. Nada de
eso
   se copia dentro de la pregunta: se lee por `JOIN` en el momento, porque los apuntes se
reescriben,
   una versión se sustituye y una incidencia se despacha;
2. **`mark_correct`**: escribe la respuesta correcta como **plantilla nueva** del conjunto, con la
   anterior `superseded`. El antes y el después, el actor y el evento entran en **una sola
   transacción**. Una clave oficial no se toca: se rechaza **antes** de escribir nada y con el
motivo;
3. **`repair`**: escribe una **versión nueva de la pregunta** —el texto viejo no se pisa— y **se
lleva
   consigo el sitio de la pregunta**: sus temas, sus anclas de apuntes y su marca de fuera de
temario.
   Sin eso, reparar el enunciado de una pregunta la sacaría del temario en silencio, que es un
cambio
   mucho mayor que quitarle una referencia al enunciado.

La clave que manda en un conjunto la elige **la misma regla** que el banco (`_active_entries` de
`question_repository`): la activa y, si no hay ninguna activa, la última plantilla. Se escribe aquí
otra vez porque esta consulta pide **una** clave con su procedencia y aquella pide las de una página
entera de preguntas, pero la regla es la misma y está dicha en los dos sitios.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, inspect, select, text, update
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.question_file_models import (
    ExclusionView,
    IncidentBriefView,
    NotesContrastView,
    ProtectedSetView,
    QuestionVersionBriefView,
)
from opofuente.domain.errors import (
    ClassificationConflictError,
    InvalidAnswerError,
    InvariantViolationError,
    NotFoundError,
)
from opofuente.domain.question_file import (
    TITULO_DE_REGLA,
    letras_que_no_existen,
    normalizar_letras,
    protege_cambiar_la_clave,
)
from opofuente.infrastructure.db_models import (
    AnswerKeyEntryRecord,
    AnswerKeyVersionRecord,
    AuditEventRecord,
    CurriculumMappingRecord,
    CurriculumNodeRecord,
    DocumentVersionRecord,
    LogicalDocumentRecord,
    NotesIncidentRecord,
    OptionVersionRecord,
    QuestionCurriculumExclusionRecord,
    QuestionNoteAnchorRecord,
    QuestionSetRecord,
    QuestionVersionRecord,
    TopicNoteSectionRecord,
)

#: La acción del evento de marcar la respuesta correcta. El objeto es **la pregunta**: marcar la
#: correcta es un acto sobre una pregunta, aunque lo que se escriba sea la plantilla del conjunto.
ACCION_MARCAR = "question.answer_key_marked"

#: La acción del evento de reparar. Se distingue de `question.corrected` (la corrección local que ya
#: existía) porque no es lo mismo escribir un texto nuevo a mano que aplicar una regla: quien lea la
#: auditoría tiene que poder separar las dos.
ACCION_REPARAR = "question.repaired"

#: El objeto de la auditoría cuando lo que cambia es el conjunto entero (la plantilla nueva).
OBJETO_PREGUNTA = "question_version"
OBJETO_CLAVE = "answer_key_version"


@dataclass(frozen=True, slots=True)
class MarkCorrectData:
    """Lo que ha pasado al marcar la correcta, para que el servicio pueda armar la respuesta."""

    key_version_id: str
    superseded_key_version_id: str | None
    previous_option_keys: tuple[str, ...]
    correct_option_keys: tuple[str, ...]
    previous_outcome: str | None
    outcome: str
    status: str
    activated: bool
    has_note: bool


@dataclass(frozen=True, slots=True)
class RepairData:
    """Lo que ha pasado al reparar: la versión nueva, qué se llevó consigo y qué plantilla se
    escribió."""

    new_question_version_id: str
    superseded_question_version_id: str
    key_version_id: str | None
    moved_topics: int
    moved_anchors: int
    moved_exclusion: bool


def _new_id() -> str:
    return str(uuid4())


def _json(valor: object) -> str:
    return json.dumps(valor, ensure_ascii=False, sort_keys=True)


def _letras(crudo: str | None) -> tuple[str, ...]:
    if crudo is None:
        return ()
    try:
        datos = json.loads(crudo)
    except json.JSONDecodeError:
        return ()
    if not isinstance(datos, list):
        return ()
    return tuple(str(letra) for letra in datos)


class SqlAlchemyQuestionFileRepository:
    """Lee lo que la ficha necesita y escribe las dos cosas que se pueden hacer desde ella."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ lectura

    def key_source_document(
        self, document_version_id: str
    ) -> tuple[str, str, str | None, str | None, str | None] | None:
        """De dónde salió la clave: `(documento, tipo, etiqueta, estado, id del documento lógico)`.

                Es la mitad de «de dónde sale esta clave»: la plantilla de un conjunto puede venir
                de un PDF
                de la biblioteca, y sin saber **cuál** y en qué estado está su versión, la letra no
                se puede
                juzgar. `None` cuando la versión del documento ya no está: la plantilla se queda
                huérfana y
        la
                ficha lo dice en vez de inventarse el material.
        """
        with self._session_factory() as session:
            fila = session.execute(
                select(
                    LogicalDocumentRecord.canonical_title,
                    LogicalDocumentRecord.document_type,
                    DocumentVersionRecord.version_label,
                    DocumentVersionRecord.status,
                    LogicalDocumentRecord.id,
                )
                .join(
                    DocumentVersionRecord,
                    DocumentVersionRecord.logical_document_id == LogicalDocumentRecord.id,
                )
                .where(DocumentVersionRecord.id == document_version_id)
            ).first()
        if fila is None:
            return None
        return (
            str(fila[0]),
            str(fila[1]),
            None if fila[2] is None else str(fila[2]),
            None if fila[3] is None else str(fila[3]),
            str(fila[4]),
        )

    def notes_contrast(self, question_version_id: str) -> tuple[NotesContrastView, ...]:
        """Lo que contestaron los apuntes de esta pregunta, con su apartado y su frase.

                Una fila por tema: una pregunta puede estar en dos temas y los apuntes contestarla
                en los
        dos.
                Se devuelven todas porque la ficha tiene que poder decir «en este tema los apuntes
                dicen C y
        en
                este otro no hay frase», que es información distinta de «no hay nada».
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(
                    QuestionNoteAnchorRecord,
                    CurriculumNodeRecord,
                    TopicNoteSectionRecord.title,
                )
                .join(
                    CurriculumNodeRecord,
                    CurriculumNodeRecord.id == QuestionNoteAnchorRecord.curriculum_node_id,
                )
                .outerjoin(
                    # El apartado se resuelve por `(tema, ancla)` y no por `section_id`: esa columna
                    # apunta a la sección del **documento** del que se extrajo el texto, y el título
                    # que se enseña es el del apartado de los apuntes. Es el mismo `JOIN` que usa la
                    # bandeja del motor, y por eso el enlace del ancla lleva al punto exacto.
                    TopicNoteSectionRecord,
                    (
                        TopicNoteSectionRecord.curriculum_node_id
                        == QuestionNoteAnchorRecord.curriculum_node_id
                    )
                    & (TopicNoteSectionRecord.anchor == QuestionNoteAnchorRecord.anchor),
                )
                .where(QuestionNoteAnchorRecord.question_version_id == question_version_id)
                .order_by(CurriculumNodeRecord.path)
            ).all()
        contraste: list[NotesContrastView] = []
        for ancla, nodo, titulo in filas:
            esperadas = _letras(ancla.expected_letters)
            letra = None if ancla.answer_letter is None else str(ancla.answer_letter)
            contraste.append(
                NotesContrastView(
                    answer_letter=letra,
                    expected_letters=esperadas,
                    result=None if ancla.result is None else str(ancla.result),
                    phrase=None if ancla.quoted_sentence is None else str(ancla.quoted_sentence),
                    anchor=str(ancla.anchor),
                    section_title=None if titulo is None else str(titulo),
                    topic_code=str(nodo.path),
                    topic_title=str(nodo.title),
                    key_status=str(ancla.key_status),
                    checked_at=ancla.checked_at,
                    coincides=letra is not None
                    and letra.strip().lower() in {cual.strip().lower() for cual in esperadas},
                )
            )
        return tuple(contraste)

    def incidents_of(self, question_version_id: str) -> tuple[IncidentBriefView, ...]:
        """Las incidencias que cuelgan de esta pregunta, con su categoría y su estado.

                Se leen las del motor (`notes_incidents`) y **también** las que apuntan a la versión
        anterior
                cuando la ficha se abre por una incidencia que quedó de antes de una corrección:
                quien llega
                desde la bandeja tiene que ver de qué se le estaba hablando.
        """
        with self._session_factory() as session:
            ids = self._chain_ids(session, question_version_id)
            filas = session.execute(
                select(NotesIncidentRecord, CurriculumNodeRecord)
                .join(
                    CurriculumNodeRecord,
                    CurriculumNodeRecord.id == NotesIncidentRecord.curriculum_node_id,
                )
                .where(NotesIncidentRecord.question_version_id.in_(list(ids)))
                .order_by(NotesIncidentRecord.category, NotesIncidentRecord.id)
            ).all()
        return tuple(
            IncidentBriefView(
                id=str(incidencia.id),
                category=str(incidencia.category),
                reason=str(incidencia.reason),
                status=str(incidencia.status),
                coverage=str(incidencia.coverage),
                detail=str(incidencia.detail),
                phrase=None if incidencia.phrase is None else str(incidencia.phrase),
                topic_code=str(nodo.path),
                topic_title=str(nodo.title),
                resolution_note=(
                    None if incidencia.resolution_note is None else str(incidencia.resolution_note)
                ),
                reviewed_at=incidencia.reviewed_at,
            )
            for incidencia, nodo in filas
        )

    def incident_ids_of(self, question_version_id: str) -> tuple[str, ...]:
        """Los identificadores de las incidencias de esta pregunta y de sus versiones anteriores.

        Lo necesita el comando de reparación y la propia ruta: al reparar una pregunta, sus
        incidencias se despachan (con `reviewed` y la nota de lo hecho), y una bandeja que siguiera
        enseñando una pregunta ya reparada estaría mintiendo. Se resuelve aquí y no en quien llama
        porque la cadena de versiones es de este repositorio.
        """
        with self._session_factory() as session:
            ids = self._chain_ids(session, question_version_id)
            filas = session.execute(
                select(NotesIncidentRecord.id).where(
                    NotesIncidentRecord.question_version_id.in_(list(ids))
                )
            ).scalars()
            return tuple(str(identificador) for identificador in filas)

    def exclusion_of(self, question_version_id: str) -> ExclusionView | None:
        """La marca de fuera del temario de esta pregunta, si la tiene."""
        with self._session_factory() as session:
            fila = session.get(QuestionCurriculumExclusionRecord, question_version_id)
        if fila is None:
            return None
        return ExclusionView(
            reason=str(fila.reason),
            note=None if fila.note is None else str(fila.note),
            actor=str(fila.actor),
            created_at=fila.created_at,
        )

    def key_reliability_of(self, set_id: str) -> tuple[str | None, str]:
        """El veredicto del §1 para este conjunto y **de dónde sale**.

                `(estado, fuente)`. Si la columna `question_sets.key_reliability` existe, manda
                ella; si no
                existe todavía —el bloque del §1 llega en su rama— devuelve `None` y una frase que
                lo dice.
        Lo
                que **no** hace: recalcular la discrepancia aquí. Sería una segunda verdad sobre lo
                mismo, y
        la
                primera la mantiene la puerta de datos de aquel bloque.

                La columna se lee por su **nombre** y no por el modelo, igual que en la bandeja del
                motor:
        no
                es de esta tanda y traerla al modelo crearía un choque de ficheros entre dos
                bloques.
        """
        with self._session_factory() as session:
            columnas = {
                str(columna["name"])
                for columna in inspect(session.get_bind()).get_columns("question_sets")
            }
            if "key_reliability" not in columnas:
                return (
                    None,
                    "la columna question_sets.key_reliability todavía no existe en esta base: la "
                    "mantiene la puerta de datos del §1 y aquí no se recalcula",
                )
            estado = session.execute(
                text("SELECT key_reliability FROM question_sets WHERE id = :conjunto"),
                {"conjunto": set_id},
            ).scalar_one_or_none()
        return (
            None if estado is None else str(estado),
            "la columna question_sets.key_reliability (§1)",
        )

    def protected_sets(self) -> tuple[ProtectedSetView, ...]:
        """Los conjuntos cuya clave no se cambia desde aquí, con el porqué de cada uno.

                Son dos caminos y la lista los une: los que **son** un examen oficial
                (`official_exam`) y
        los
                que tienen una plantilla enlazada a un documento, que es una plantilla salida de un
                papel
                aunque el conjunto esté marcado como banco. Medido el 13 de octubre de 2026 sobre la
                copia
        de
                la base: los dos caminos dan **los mismos diez conjuntos** —los cuatro exámenes del
                INAP en
        sus
                dos modelos, dos de ellos archivados, y los dos de la Guardia Civil—, y por eso la
                lista no
                lleva dos secciones.
        """
        with self._session_factory() as session:
            con_plantilla = (
                select(AnswerKeyVersionRecord.question_set_id)
                .where(AnswerKeyVersionRecord.source_document_version_id.is_not(None))
                .distinct()
            )
            # Una sola consulta: el título de la plantilla más nueva de cada conjunto protegido se
            # resuelve con un `LEFT JOIN` y no con una consulta por conjunto. La lista se enseña en
            # cada ficha —es lo que explica por qué una clave no se toca—, así que hacer diez viajes
            # a
            # la base por ficha sería pagar diez veces por lo mismo.
            filas = session.execute(
                select(
                    QuestionSetRecord.id,
                    QuestionSetRecord.title,
                    QuestionSetRecord.set_type,
                    LogicalDocumentRecord.canonical_title,
                )
                .outerjoin(
                    AnswerKeyVersionRecord,
                    AnswerKeyVersionRecord.question_set_id == QuestionSetRecord.id,
                )
                .outerjoin(
                    DocumentVersionRecord,
                    DocumentVersionRecord.id == AnswerKeyVersionRecord.source_document_version_id,
                )
                .outerjoin(
                    LogicalDocumentRecord,
                    LogicalDocumentRecord.id == DocumentVersionRecord.logical_document_id,
                )
                .where(
                    (QuestionSetRecord.set_type == "official_exam")
                    | (QuestionSetRecord.id.in_(con_plantilla))
                )
                .order_by(
                    QuestionSetRecord.title,
                    QuestionSetRecord.id,
                    AnswerKeyVersionRecord.version_no.desc(),
                )
            ).all()
        vistos: dict[str, ProtectedSetView] = {}
        for identificador, titulo, tipo, plantilla in filas:
            clave = str(identificador)
            if clave in vistos:
                continue
            titulo_plantilla = None if plantilla is None else str(plantilla)
            motivo = protege_cambiar_la_clave(
                set_type=str(tipo),
                tiene_plantilla_enlazada=titulo_plantilla is not None,
            )
            vistos[clave] = ProtectedSetView(
                id=clave,
                title=str(titulo),
                set_type=str(tipo),
                source_document_title=titulo_plantilla,
                reason=motivo or "",
            )
        return tuple(vistos.values())

    def versions_of(self, question_version_id: str) -> tuple[QuestionVersionBriefView, ...]:
        """El historial de la pregunta: todas sus versiones, de la más nueva a la más vieja.

                Se cuentan las opciones de cada versión y se leen las letras que **la plantilla que
                manda**
                daba a esa versión: sin las letras, el historial diría qué se escribió pero no qué
                se
        corrigió
                con ello, que es lo que hay que poder comparar al marcar la correcta.
        """
        with self._session_factory() as session:
            fila = session.get(QuestionVersionRecord, question_version_id)
            if fila is None:
                return ()
            versiones = (
                session.execute(
                    select(QuestionVersionRecord)
                    .where(
                        QuestionVersionRecord.question_set_id == fila.question_set_id,
                        QuestionVersionRecord.stable_key == fila.stable_key,
                    )
                    .order_by(QuestionVersionRecord.version_no.desc())
                )
                .scalars()
                .all()
            )
            ids = [str(version.id) for version in versiones]
            opciones: dict[str, int] = {
                str(pregunta_id): int(cuantas)
                for pregunta_id, cuantas in session.execute(
                    select(OptionVersionRecord.question_version_id, func.count())
                    .where(OptionVersionRecord.question_version_id.in_(ids))
                    .group_by(OptionVersionRecord.question_version_id)
                ).all()
            }
            vigente = self._effective_key(session, str(fila.question_set_id))
            entradas = (
                ()
                if vigente is None
                else session.execute(
                    select(
                        AnswerKeyEntryRecord.question_version_id,
                        AnswerKeyEntryRecord.correct_option_keys_json,
                    ).where(
                        AnswerKeyEntryRecord.answer_key_version_id == str(vigente.id),
                        AnswerKeyEntryRecord.question_version_id.in_(ids),
                    )
                ).all()
            )
        letras_por_version: dict[str, tuple[str, ...]] = {}
        for pregunta_id, crudo in entradas:
            letras_por_version[str(pregunta_id)] = _letras(None if crudo is None else str(crudo))
        return tuple(
            QuestionVersionBriefView(
                id=str(version.id),
                version_no=int(version.version_no),
                status=str(version.status),
                stem=str(version.stem),
                note=None if version.note is None else str(version.note),
                created_at=version.created_at,
                option_count=int(opciones.get(str(version.id), 0)),
                correct_option_keys=letras_por_version.get(str(version.id), ()),
            )
            for version in versiones
        )

    # ------------------------------------------------------------------ escritura: marcar la
    # correcta

    def mark_correct(
        self,
        question_version_id: str,
        *,
        correct_option_keys: Sequence[str],
        note: str | None,
        actor: str,
        now: datetime,
    ) -> MarkCorrectData:
        """Marca la respuesta correcta de esta pregunta, en una **plantilla nueva** del conjunto.

                Lo que garantiza:

                - **la anterior no se pisa**: la plantilla que mandaba pasa a `superseded` y la
                nueva guarda
                  el mismo número de versión más uno, con `supersedes_id` apuntándola. Las dos se
                  pueden
        leer
                  después, que es lo que el historial de la ficha enseña;
                - **el estado se conserva**: una plantilla activa se sustituye por otra activa (si
                no,
        marcar
                  la correcta no cambiaría lo que corrige el alumno y la pantalla mentiría) y una en
        borrador
                  por otra en borrador (activar una clave es un acto aparte y no se hace aquí);
                - **una clave oficial no se toca**: se comprueba **antes** de escribir y se lanza
                  `ClassificationConflictError` con el motivo del dominio. Comprobarlo aquí, en la
                  misma
                  transacción, es lo que hace imposible que dos caminos escriban la clave de un
                  examen
        oficial;
                - **una letra que no existe no entra**: `d` en una pregunta de tres opciones es un
                422 con
        el
                  campo, no una fila con una respuesta que nadie puede elegir;
                - **el antes, el después y el actor van juntos**: el evento de auditoría se escribe
                en la
        misma
                  transacción que la plantilla, así que no puede quedar una clave cambiada sin su
                  traza ni
        una
                  traza de un cambio que no ocurrió. La nota **no** viaja al evento (es texto de una
        persona,
                  como en la bandeja del motor): el evento dice si la había.
        """
        limpia = None if note is None or not note.strip() else note.strip()
        with self._session_factory() as session:
            pregunta = session.get(QuestionVersionRecord, question_version_id)
            if pregunta is None:
                raise NotFoundError("pregunta", question_version_id)
            conjunto = session.get(QuestionSetRecord, str(pregunta.question_set_id))
            if conjunto is None:  # pragma: no cover - una pregunta sin conjunto no existe
                raise NotFoundError("conjunto de preguntas", str(pregunta.question_set_id))
            disponibles = tuple(
                str(clave)
                for clave in session.execute(
                    select(OptionVersionRecord.stable_key)
                    .where(OptionVersionRecord.question_version_id == question_version_id)
                    .order_by(OptionVersionRecord.position)
                ).scalars()
            )
            letras = normalizar_letras(correct_option_keys)
            if not letras:
                raise InvalidAnswerError(
                    "una respuesta correcta necesita al menos una opción",
                    field="correct_option_keys",
                )
            sobrantes = letras_que_no_existen(pedidas=letras, disponibles=disponibles)
            if sobrantes:
                raise InvalidAnswerError(
                    "la pregunta no tiene "
                    + ", ".join(f"la opción «{letra}»" for letra in sobrantes)
                    + f": sus opciones son {', '.join(disponibles)}",
                    field="correct_option_keys",
                )
            tiene_plantilla = bool(
                session.execute(
                    select(AnswerKeyVersionRecord.id)
                    .where(
                        AnswerKeyVersionRecord.question_set_id == str(conjunto.id),
                        AnswerKeyVersionRecord.source_document_version_id.is_not(None),
                    )
                    .limit(1)
                ).first()
            )
            motivo = protege_cambiar_la_clave(
                set_type=str(conjunto.set_type), tiene_plantilla_enlazada=tiene_plantilla
            )
            if motivo is not None:
                raise ClassificationConflictError(motivo)
            actual = self._effective_key(session, str(conjunto.id))
            anterior_entrada = None
            if actual is not None:
                anterior_entrada = session.get(
                    AnswerKeyEntryRecord, (str(actual.id), question_version_id)
                )
            antes_letras = (
                ()
                if anterior_entrada is None
                else _letras(anterior_entrada.correct_option_keys_json)
            )
            antes_desenlace = None if anterior_entrada is None else str(anterior_entrada.outcome)
            version = (
                int(
                    session.execute(
                        select(func.coalesce(func.max(AnswerKeyVersionRecord.version_no), 0)).where(
                            AnswerKeyVersionRecord.question_set_id == str(conjunto.id)
                        )
                    ).scalar_one()
                )
                + 1
            )
            estado = "draft" if actual is None else str(actual.status)
            nueva = AnswerKeyVersionRecord(
                id=_new_id(),
                question_set_id=str(conjunto.id),
                source_document_version_id=(
                    None if actual is None else actual.source_document_version_id
                ),
                version_no=version,
                status=estado,
                supersedes_id=None if actual is None else str(actual.id),
                published_at=None if actual is None else actual.published_at,
                # Activar es aprobar (invariante 4): una plantilla activa tiene que llevar fecha de
                # aprobación, y la lleva la de ahora porque activarla es lo que se está haciendo.
                approved_at=now if estado == "active" else None,
                created_at=now,
            )
            # Primero se retira la que estaba activa y **después** se escribe la nueva: el índice
            # único parcial solo admite una activa por conjunto, así que el orden importa (lo mismo
            # que hace `activate_key`).
            if actual is not None:
                actual.status = "superseded"
                session.flush()
            session.add(nueva)
            session.flush()
            if actual is not None:
                self._copy_entries(session, actual.id, nueva.id, question_version_id)
            existente = session.get(AnswerKeyEntryRecord, (nueva.id, question_version_id))
            if existente is None:
                session.add(
                    AnswerKeyEntryRecord(
                        answer_key_version_id=nueva.id,
                        question_version_id=question_version_id,
                        outcome="keyed",
                        correct_option_keys_json=_json(list(letras)),
                        notes=None if limpia is None else limpia,
                    )
                )
            else:
                existente.outcome = "keyed"
                existente.correct_option_keys_json = _json(list(letras))
                existente.notes = limpia
            session.add(
                AuditEventRecord(
                    id=_new_id(),
                    actor=actor,
                    action=ACCION_MARCAR,
                    object_type=OBJETO_PREGUNTA,
                    object_id=question_version_id,
                    before_json=_json(
                        {
                            "correct_option_keys": list(antes_letras),
                            "outcome": antes_desenlace,
                            "key_version_id": None if actual is None else str(actual.id),
                            "key_version_no": None if actual is None else int(actual.version_no),
                        }
                    ),
                    after_json=_json(
                        {
                            "correct_option_keys": list(letras),
                            "outcome": "keyed",
                            "key_version_id": nueva.id,
                            "key_version_no": version,
                            "superseded_key_version_id": None if actual is None else str(actual.id),
                            "question_set_id": str(conjunto.id),
                            "has_note": limpia is not None,
                        }
                    ),
                    correlation_id=None,
                    created_at=now,
                )
            )
            session.commit()
            return MarkCorrectData(
                key_version_id=nueva.id,
                superseded_key_version_id=None if actual is None else str(actual.id),
                previous_option_keys=antes_letras,
                correct_option_keys=letras,
                previous_outcome=antes_desenlace,
                outcome="keyed",
                status=estado,
                activated=estado == "active",
                has_note=limpia is not None,
            )

    # ------------------------------------------------------------------ escritura: reparar

    def repair(
        self,
        question_version_id: str,
        *,
        stem: str | None,
        opciones: Sequence[str] | None,
        reglas: Sequence[str],
        note: str,
        actor: str,
        now: datetime,
    ) -> RepairData:
        """Escribe la **versión nueva** de la pregunta y se lleva consigo su sitio.

                Cinco decisiones, y las cinco se ven en lo que devuelve:

                1. **el texto viejo no se pisa**: la versión anterior pasa a `superseded` y la nueva
                guarda
        su
                   `supersedes_id` y su `note`. Es la misma regla que la corrección local que ya
                   existía;
                2. **el sitio viaja**: los temas (`curriculum_mappings`), las anclas de apuntes
                   (`question_note_anchors`) y la marca de fuera de temario
                   (`question_curriculum_exclusions`) se **mueven** a la versión nueva. Sin esto,
                   reparar el
                   enunciado de una pregunta la sacaría del temario y de los tests por tema sin
                   decirlo, y
        la
                   cobertura de los apuntes cambiaría de denominador por una referencia quitada. Se
                   mueven y
        no
                   se copian para que no haya dos filas que cuenten la misma pregunta;
                3. **la plantilla sigue a la pregunta con las MISMAS letras**: si el conjunto tenía
                una
        clave
                   que apuntaba a la versión anterior, se escribe una plantilla nueva con la misma
                   entrada
                   re-apuntada. Nunca cambia una letra, y ese es el invariante que hace que reparar
                   el
                   enunciado de un examen oficial no toque su clave;
                4. **a un conjunto protegido no se le mueven las opciones**: cambiar el número de
                opciones
        de
                   un examen oficial cambiaría lo que significan las letras de su plantilla, así que
                   se
                   rechaza con el motivo. El enunciado sí se puede limpiar, porque no mueve ninguna
                   letra;
                5. **el antes, el después y el actor van juntos**: el evento de auditoría
        (`question.repaired`)
                   se escribe en la misma transacción. La nota **no** viaja al evento: el evento
                   dice si la
                   había.
        """
        reglas_limpias = tuple(regla for regla in reglas if regla in TITULO_DE_REGLA)
        if not reglas_limpias:
            raise InvariantViolationError(
                "una reparación necesita al menos una regla del vocabulario conocido: "
                + ", ".join(sorted(TITULO_DE_REGLA))
            )
        if stem is None and opciones is None:
            raise InvariantViolationError("una reparación que no cambia nada no es una reparación")
        if not note.strip():
            raise InvariantViolationError("una reparación necesita motivo")
        with self._session_factory() as session:
            anterior = session.get(QuestionVersionRecord, question_version_id)
            if anterior is None:
                raise NotFoundError("pregunta", question_version_id)
            conjunto = session.get(QuestionSetRecord, str(anterior.question_set_id))
            if conjunto is None:  # pragma: no cover
                raise NotFoundError("conjunto de preguntas", str(anterior.question_set_id))
            textos_previos = tuple(
                str(texto)
                for texto in session.execute(
                    select(OptionVersionRecord.text)
                    .where(OptionVersionRecord.question_version_id == question_version_id)
                    .order_by(OptionVersionRecord.position)
                ).scalars()
            )
            textos = textos_previos if opciones is None else tuple(opciones)
            if not textos:
                raise InvariantViolationError(
                    "una pregunta reparada se queda sin opciones: ninguna regla puede dejarla así"
                )
            tiene_plantilla = bool(
                session.execute(
                    select(AnswerKeyVersionRecord.id)
                    .where(
                        AnswerKeyVersionRecord.question_set_id == str(conjunto.id),
                        AnswerKeyVersionRecord.source_document_version_id.is_not(None),
                    )
                    .limit(1)
                ).first()
            )
            motivo_oficial = protege_cambiar_la_clave(
                set_type=str(conjunto.set_type), tiene_plantilla_enlazada=tiene_plantilla
            )
            if motivo_oficial is not None and opciones is not None:
                raise ClassificationConflictError(
                    "no se le cambian las opciones a una pregunta de un examen oficial: moverlas "
                    "cambiaría lo que significan las letras de su plantilla oficial. "
                    + motivo_oficial
                )
            version = (
                int(
                    session.execute(
                        select(func.coalesce(func.max(QuestionVersionRecord.version_no), 0)).where(
                            QuestionVersionRecord.question_set_id == str(conjunto.id),
                            QuestionVersionRecord.stable_key == str(anterior.stable_key),
                        )
                    ).scalar_one()
                )
                + 1
            )
            nueva_id = _new_id()
            estado_previo = str(anterior.status)
            session.add(
                QuestionVersionRecord(
                    id=nueva_id,
                    question_set_id=str(conjunto.id),
                    stable_key=str(anterior.stable_key),
                    version_no=version,
                    stem=(anterior.stem if stem is None else stem).strip(),
                    question_type=str(anterior.question_type),
                    position=int(anterior.position),
                    is_reserve=bool(anterior.is_reserve),
                    reserve_order=anterior.reserve_order,
                    # Una reparación escribe un texto que el importador no trajo: la versión nueva
                    # está completa por construcción (se comprueba arriba que no se queda sin
                    # opciones), y dejarla `incomplete` la sacaría de los tests sin motivo.
                    status="complete",
                    origin_type=str(anterior.origin_type),
                    source_section_id=anterior.source_section_id,
                    supersedes_id=question_version_id,
                    created_at=now,
                    note=note.strip(),
                )
            )
            session.flush()
            for orden, texto in enumerate(textos, start=1):
                session.add(
                    OptionVersionRecord(
                        id=_new_id(),
                        question_version_id=nueva_id,
                        stable_key=chr(ord("a") + orden - 1),
                        label=chr(ord("A") + orden - 1),
                        text=texto.strip(),
                        position=orden,
                    )
                )
            anterior.status = "superseded"
            movidos = self._carry_place(session, question_version_id, nueva_id)
            clave_nueva = self._carry_key(
                session,
                set_id=str(conjunto.id),
                anterior_id=question_version_id,
                nueva_id=nueva_id,
                now=now,
            )
            session.add(
                AuditEventRecord(
                    id=_new_id(),
                    actor=actor,
                    action=ACCION_REPARAR,
                    object_type=OBJETO_PREGUNTA,
                    object_id=nueva_id,
                    before_json=_json(
                        {
                            "supersedes_id": question_version_id,
                            "status": estado_previo,
                            "opciones": len(textos_previos),
                        }
                    ),
                    after_json=_json(
                        {
                            "version_no": version,
                            "reglas": list(reglas_limpias),
                            "opciones": len(textos),
                            "temas_movidos": movidos[0],
                            "anclas_movidas": movidos[1],
                            "exclusion_movida": movidos[2],
                            "key_version_id": clave_nueva,
                            "has_note": True,
                        }
                    ),
                    correlation_id=None,
                    created_at=now,
                )
            )
            session.commit()
            return RepairData(
                new_question_version_id=nueva_id,
                superseded_question_version_id=question_version_id,
                key_version_id=clave_nueva,
                moved_topics=movidos[0],
                moved_anchors=movidos[1],
                moved_exclusion=movidos[2],
            )

    # ------------------------------------------------------------------ piezas compartidas

    @staticmethod
    def _effective_key(session: Session, set_id: str) -> AnswerKeyVersionRecord | None:
        """La plantilla que manda en el conjunto: la activa y, si no hay, la última.

                Es la misma regla que `SqlAlchemyQuestionRepository._active_entries`, escrita aquí
                porque
        esta
                consulta pide **una** clave con su procedencia y aquella pide las de toda una
                página.
        """
        return session.execute(
            select(AnswerKeyVersionRecord)
            .where(AnswerKeyVersionRecord.question_set_id == set_id)
            .order_by(
                (AnswerKeyVersionRecord.status == "active").desc(),
                AnswerKeyVersionRecord.version_no.desc(),
            )
            .limit(1)
        ).scalar_one_or_none()

    @staticmethod
    def _chain_ids(session: Session, question_version_id: str) -> frozenset[str]:
        """La pregunta y toda su cadena de versiones (hacia delante y hacia atrás).

        Una incidencia o un ancla puede apuntar a la versión anterior de una pregunta corregida, y
        quien llega desde la bandeja tiene que ver de qué se le estaba hablando. Se recorren las dos
        direcciones: `supersedes_id` hacia atrás y las versiones que la sustituyen hacia delante.
        """
        primera = session.get(QuestionVersionRecord, question_version_id)
        if primera is None:
            return frozenset({question_version_id})
        cadena = {str(primera.id)}
        actual = primera
        while actual.supersedes_id is not None:
            padre = session.get(QuestionVersionRecord, str(actual.supersedes_id))
            if padre is None or str(padre.id) in cadena:
                break
            cadena.add(str(padre.id))
            actual = padre
        seguidoras = (
            session.execute(
                select(QuestionVersionRecord)
                .where(
                    QuestionVersionRecord.question_set_id == str(primera.question_set_id),
                    QuestionVersionRecord.stable_key == str(primera.stable_key),
                )
                .order_by(QuestionVersionRecord.version_no)
            )
            .scalars()
            .all()
        )
        for version in seguidoras:
            cadena.add(str(version.id))
        return frozenset(cadena)

    @staticmethod
    def _copy_entries(
        session: Session,
        origen_id: str,
        destino_id: str,
        saltar: str,
    ) -> None:
        """Copia las entradas de una plantilla a la nueva, sin la pregunta que se cambia.

                La pregunta que se está marcando se escribe aparte, con su letra nueva: copiarla y
                luego
                pisarla dejaría la fila con dos escrituras en la misma transacción y un `flush` de
                por
        medio.
        """
        entradas = (
            session.execute(
                select(AnswerKeyEntryRecord).where(
                    AnswerKeyEntryRecord.answer_key_version_id == origen_id
                )
            )
            .scalars()
            .all()
        )
        for entrada in entradas:
            if str(entrada.question_version_id) == saltar:
                continue
            session.add(
                AnswerKeyEntryRecord(
                    answer_key_version_id=destino_id,
                    question_version_id=str(entrada.question_version_id),
                    outcome=str(entrada.outcome),
                    correct_option_keys_json=entrada.correct_option_keys_json,
                    notes=entrada.notes,
                )
            )

    @staticmethod
    def _carry_place(session: Session, anterior_id: str, nueva_id: str) -> tuple[int, int, bool]:
        """Mueve a la versión nueva los temas, las anclas de apuntes y la marca de fuera de temario.

                Devuelve cuántas cosas se movieron, para que el evento de auditoría lo diga: si esto
                se
                rompiera, la pregunta saldría del temario en silencio y la traza tiene que poder
                enseñar que
        no
                se movió nada.
        """
        # Se **cuenta** antes de mover en vez de leer el `rowcount` del `UPDATE`: la cifra viaja al
        # evento de auditoría y a la respuesta, y contarla antes es la forma de que sea la misma que
        # la del informe (es lo que hace el resto de la casa).
        temas_movidos = int(
            session.execute(
                select(func.count())
                .select_from(CurriculumMappingRecord)
                .where(
                    CurriculumMappingRecord.subject_type == "question_version",
                    CurriculumMappingRecord.subject_id == anterior_id,
                )
            ).scalar_one()
        )
        anclas_movidas = int(
            session.execute(
                select(func.count())
                .select_from(QuestionNoteAnchorRecord)
                .where(QuestionNoteAnchorRecord.question_version_id == anterior_id)
            ).scalar_one()
        )
        session.execute(
            update(CurriculumMappingRecord)
            .where(
                CurriculumMappingRecord.subject_type == "question_version",
                CurriculumMappingRecord.subject_id == anterior_id,
            )
            .values(subject_id=nueva_id)
        )
        session.execute(
            update(QuestionNoteAnchorRecord)
            .where(QuestionNoteAnchorRecord.question_version_id == anterior_id)
            .values(question_version_id=nueva_id)
        )
        excluida = session.get(QuestionCurriculumExclusionRecord, anterior_id)
        movida = False
        if excluida is not None:
            # Los valores se copian **antes** de borrar: después del `delete` y el `flush` la fila
            # ya no está y leerla dispararía un refresco contra una fila que no existe.
            motivo = str(excluida.reason)
            nota = None if excluida.note is None else str(excluida.note)
            quien = str(excluida.actor)
            cuando = excluida.created_at
            session.delete(excluida)
            session.flush()
            session.add(
                QuestionCurriculumExclusionRecord(
                    question_version_id=nueva_id,
                    reason=motivo,
                    note=nota,
                    actor=quien,
                    created_at=cuando,
                )
            )
            movida = True
        return temas_movidos, anclas_movidas, movida

    @staticmethod
    def _carry_key(
        session: Session,
        *,
        set_id: str,
        anterior_id: str,
        nueva_id: str,
        now: datetime,
    ) -> str | None:
        """Escribe la plantilla nueva con la entrada de esta pregunta re-apuntada, **sin cambiar sus
                letras**.

                `None` cuando la plantilla que manda no tenía entrada para esta pregunta: entonces
                no hay
        nada
                que llevarse y la ficha dirá que la versión nueva no tiene respuesta correcta
                todavía.
        Inventar
                una entrada con las letras de otra pregunta sería peor que no tener ninguna.
        """
        actual = SqlAlchemyQuestionFileRepository._effective_key(session, set_id)
        if actual is None:
            return None
        entrada = session.get(AnswerKeyEntryRecord, (str(actual.id), anterior_id))
        if entrada is None:
            return None
        version = (
            int(
                session.execute(
                    select(func.coalesce(func.max(AnswerKeyVersionRecord.version_no), 0)).where(
                        AnswerKeyVersionRecord.question_set_id == set_id
                    )
                ).scalar_one()
            )
            + 1
        )
        estado = str(actual.status)
        nueva = AnswerKeyVersionRecord(
            id=_new_id(),
            question_set_id=set_id,
            source_document_version_id=actual.source_document_version_id,
            version_no=version,
            status=estado,
            supersedes_id=str(actual.id),
            published_at=actual.published_at,
            approved_at=now if estado == "active" else None,
            created_at=now,
        )
        if estado == "active":
            actual.status = "superseded"
            session.flush()
        session.add(nueva)
        session.flush()
        entradas = (
            session.execute(
                select(AnswerKeyEntryRecord).where(
                    AnswerKeyEntryRecord.answer_key_version_id == str(actual.id)
                )
            )
            .scalars()
            .all()
        )
        for fila in entradas:
            es_la_de_esta = str(fila.question_version_id) == anterior_id
            session.add(
                AnswerKeyEntryRecord(
                    answer_key_version_id=nueva.id,
                    question_version_id=nueva_id
                    if es_la_de_esta
                    else str(fila.question_version_id),
                    outcome=str(fila.outcome),
                    correct_option_keys_json=fila.correct_option_keys_json,
                    notes=fila.notes,
                )
            )
        return nueva.id


__all__ = [
    "ACCION_MARCAR",
    "ACCION_REPARAR",
    "MarkCorrectData",
    "RepairData",
    "SqlAlchemyQuestionFileRepository",
]
