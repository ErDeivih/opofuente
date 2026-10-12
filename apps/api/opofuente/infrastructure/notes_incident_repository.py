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
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql.elements import ColumnElement

from opofuente.domain.notes_incidents import (
    IncidentCoverage,
    IncidentFilter,
    IncidentStatus,
    NotesIncident,
    normalise_note,
    reviewed_at_for,
)
from opofuente.domain.topic_notes import CategoriaIncidencia, Motivo
from opofuente.infrastructure.db_models import (
    AuditEventRecord,
    CurriculumNodeRecord,
    DocumentSectionRecord,
    DocumentVersionRecord,
    LogicalDocumentRecord,
    NotesIncidentRecord,
    QuestionSetRecord,
    QuestionVersionRecord,
    TopicNoteSectionRecord,
)

#: La acción del evento de despacho, con el mismo vocabulario `objeto.verbo` que el resto.
ACCION_DESPACHO = "notes.incident_updated"

#: El objeto de la auditoría es **la incidencia**, no el tema: el despacho es de la incidencia.
OBJETO_INCIDENCIA = "note_incident"

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
    "ACCION_DESPACHO",
    "OBJETO_INCIDENCIA",
    "SqlAlchemyNotesIncidentRepository",
]
