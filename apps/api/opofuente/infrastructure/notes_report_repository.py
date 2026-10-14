"""Los avisos del alumno: se guardan, se leen y se despachan (decisiones D2 y F16).

Tres cosas y las tres con una regla detrás:

1. **guardar es una escritura auditada**, no un apunte suelto: la fila del aviso y el evento de
   auditoría entran en la **misma transacción**. Un aviso sin su evento sería una escritura que
   nadie puede reconstruir, y un evento sin aviso, una traza que miente. El evento lleva la
   referencia (tema, apartado, identificador del aviso) y **no** el texto que escribió el alumno:
   `audit_events` guarda el antes/después sanitizado y nunca contenido.
2. **despachar es lo mismo**: cambiar el estado y dejar la nota de lo que se ha hecho es una sola
   operación, con su evento, y también en una transacción. La nota **no** viaja al evento —es texto
   de una persona, igual que el motivo del alumno—: el evento guarda qué estado había, cuál queda y
   si el aviso llevaba nota, que es lo que hace falta para reconstruir el despacho sin copiar el
   contenido a la traza.
3. **leer resuelve el título del apartado contra los apuntajes de hoy**, con un `LEFT JOIN`. Un
   aviso que apuntaba a un apartado que ya no existe se sigue leyendo (con el título vacío), porque
   borrarlo sería perder justo el caso que hay que mirar: el texto cambió debajo del aviso.
"""

from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql.elements import ColumnElement

from opofuente.domain.notes_reports import (
    NoteReport,
    NoteReportFilter,
    NoteReportStatus,
    normalise_note,
    reviewed_at_for,
)
from opofuente.infrastructure.db_models import (
    AuditEventRecord,
    CurriculumNodeRecord,
    NotesReportRecord,
    TopicNoteSectionRecord,
)

#: Quién firma el evento de auditoría cuando el aviso lo escribe el alumno.
ACTOR_ALUMNO = "alumno"

#: La acción del evento de creación, con el mismo vocabulario `objeto.verbo` que el resto.
ACCION_AVISO = "notes.report_created"

#: La acción del evento de despacho: el propietario cambia el estado y deja su nota.
ACCION_DESPACHO = "notes.report_updated"

#: El objeto de la auditoría de un despacho es **el aviso**, no el tema: el despacho es del aviso.
OBJETO_AVISO = "note_report"


class SqlAlchemyNotesReportRepository:
    """Guarda un aviso del alumno, lista los que esperan y despacha los que ya están mirados."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save(
        self,
        *,
        node_id: str,
        owner_id: str,
        section_key: str,
        anchor: str,
        reason: str,
        now: datetime,
    ) -> NoteReport:
        """Guarda el aviso y su evento de auditoría. Devuelve el aviso guardado."""
        report_id = str(uuid4())
        with self._session_factory() as session:
            session.add(
                NotesReportRecord(
                    id=report_id,
                    curriculum_node_id=node_id,
                    owner_id=owner_id,
                    section_key=section_key,
                    anchor=anchor,
                    reason=reason,
                    status=NoteReportStatus.OPEN.value,
                    created_at=now,
                    reviewed_at=None,
                    resolution_note=None,
                )
            )
            session.add(
                AuditEventRecord(
                    id=str(uuid4()),
                    actor=ACTOR_ALUMNO,
                    action=ACCION_AVISO,
                    object_type="topic",
                    object_id=node_id,
                    before_json=None,
                    after_json=json.dumps(
                        {"report_id": report_id, "section_key": section_key, "anchor": anchor},
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    correlation_id=None,
                    created_at=now,
                )
            )
            session.commit()
        return NoteReport(
            id=report_id,
            node_id=node_id,
            owner_id=owner_id,
            section_key=section_key,
            anchor=anchor,
            reason=reason,
            status=NoteReportStatus.OPEN,
            created_at=now,
        )

    def update(
        self,
        *,
        report_id: str,
        status: NoteReportStatus,
        note: str | None,
        actor: str,
        now: datetime,
    ) -> NoteReport | None:
        """Despacha un aviso: el estado, la nota y su evento, en una sola transacción.

        Devuelve el aviso **tal como queda**, con el tema y el apartado resueltos, para que la ruta
        pueda contestar con lo mismo que enseña la bandeja. `None` si el aviso no existe.

        Dos decisiones que se ven aquí:

        - la nota **no se borra** al cambiar de estado: si el propietario ya escribió «arreglado en
          la versión del 12-oct», volver a poner el aviso en curso no puede tirar eso. Solo se
          sustituye cuando esta operación trae otra cosa escrita;
        - `reviewed_at` lo decide el dominio (`reviewed_at_for`), y por eso reabrir un aviso
          **borra** la fecha: la columna dice cuándo se despachó, y un aviso abierto con fecha de
          revisión es una traza que miente.
        """
        limpia = normalise_note(note)
        with self._session_factory() as session:
            fila = session.get(NotesReportRecord, report_id)
            if fila is None:
                return None
            antes = {
                "report_id": report_id,
                "status": str(fila.status),
                "has_note": fila.resolution_note is not None,
            }
            fila.status = status.value
            fila.reviewed_at = reviewed_at_for(status, now)
            if limpia is not None:
                fila.resolution_note = limpia
            despues = {
                "report_id": report_id,
                "status": status.value,
                "has_note": fila.resolution_note is not None,
            }
            session.add(
                AuditEventRecord(
                    id=str(uuid4()),
                    actor=actor,
                    action=ACCION_DESPACHO,
                    object_type=OBJETO_AVISO,
                    object_id=report_id,
                    before_json=json.dumps(antes, ensure_ascii=False, sort_keys=True),
                    after_json=json.dumps(despues, ensure_ascii=False, sort_keys=True),
                    correlation_id=None,
                    created_at=now,
                )
            )
            session.commit()
        return self.get(report_id)

    def get(self, report_id: str) -> NoteReport | None:
        """Un aviso por su identificador, con el tema y el apartado resueltos como en la lista."""
        with self._session_factory() as session:
            fila = session.execute(_consulta().where(NotesReportRecord.id == report_id)).first()
        if fila is None:
            return None
        aviso, nodo, apartado = fila
        return _aviso(aviso, nodo, apartado)

    def list_reports(self, filtro: NoteReportFilter | None = None) -> tuple[NoteReport, ...]:
        """Los avisos, del más nuevo al más viejo, con el tema y el apartado resueltos.

        El `LEFT JOIN` con los apartados es deliberado: un aviso cuyo apartado ya no existe sigue
        saliendo en la bandeja con `section_title` vacío. Es el aviso más interesante de todos —el
        texto se ha reescrito debajo— y esconderlo sería justo lo contrario de lo que hace falta.
        """
        consulta = _consulta().order_by(
            NotesReportRecord.created_at.desc(), NotesReportRecord.id.desc()
        )
        if filtro is not None:
            if filtro.status is not None:
                consulta = consulta.where(NotesReportRecord.status == filtro.status.value)
            if filtro.topic_code is not None:
                consulta = consulta.where(CurriculumNodeRecord.path == filtro.topic_code)
            if filtro.q is not None:
                consulta = consulta.where(_busqueda(filtro.q))
            consulta = consulta.limit(filtro.limit)
        with self._session_factory() as session:
            filas = session.execute(consulta).all()
        return tuple(_aviso(aviso, nodo, apartado) for aviso, nodo, apartado in filas)

    def count_open(self) -> int:
        """Cuántos avisos esperan a que alguien los lea."""
        return self.counts()[NoteReportStatus.OPEN]

    def count(
        self,
        *,
        status: NoteReportStatus | None = None,
        topic_code: str | None = None,
        q: str | None = None,
    ) -> int:
        """Cuántos avisos hay, con el mismo filtro que la lista.

        Existe para que la pantalla pueda decir «37 de 333» sin traerse las 333 filas: contar en
        Python lo que se ha traído con un tope da un número que miente.
        """
        consulta = select(func.count()).select_from(NotesReportRecord)
        if topic_code is not None:
            consulta = consulta.join(
                CurriculumNodeRecord,
                CurriculumNodeRecord.id == NotesReportRecord.curriculum_node_id,
            ).where(CurriculumNodeRecord.path == topic_code)
        if q is not None:
            consulta = consulta.outerjoin(
                TopicNoteSectionRecord,
                (TopicNoteSectionRecord.curriculum_node_id == NotesReportRecord.curriculum_node_id)
                & (TopicNoteSectionRecord.subsection_key == NotesReportRecord.section_key),
            )
            consulta = consulta.where(_busqueda(q))
        if status is not None:
            consulta = consulta.where(NotesReportRecord.status == status.value)
        with self._session_factory() as session:
            return int(session.execute(consulta).scalar_one())

    def counts(self) -> dict[NoteReportStatus, int]:
        """Cuántos avisos hay en cada estado: los números de los filtros de la bandeja.

        Los cuatro estados salen **siempre**, con cero incluido: quien pinta los filtros necesita
        saber que `dismissed` está vacío, y un diccionario al que le falten claves obliga a la
        pantalla a inventarse el cero.
        """
        with self._session_factory() as session:
            filas = session.execute(
                select(NotesReportRecord.status, func.count()).group_by(NotesReportRecord.status)
            ).all()
        contados: dict[NoteReportStatus, int] = dict.fromkeys(NoteReportStatus, 0)
        for estado, total in filas:
            contados[NoteReportStatus(str(estado))] = int(total)
        return contados


def _consulta() -> Select[tuple[NotesReportRecord, CurriculumNodeRecord, TopicNoteSectionRecord]]:
    """La consulta de un aviso con su tema y su apartado, sin orden ni filtros."""
    return (
        select(NotesReportRecord, CurriculumNodeRecord, TopicNoteSectionRecord)
        .join(
            CurriculumNodeRecord,
            CurriculumNodeRecord.id == NotesReportRecord.curriculum_node_id,
        )
        .outerjoin(
            TopicNoteSectionRecord,
            (TopicNoteSectionRecord.curriculum_node_id == NotesReportRecord.curriculum_node_id)
            & (TopicNoteSectionRecord.subsection_key == NotesReportRecord.section_key),
        )
    )


def _busqueda(texto: str) -> ColumnElement[bool]:
    """El filtro de la búsqueda: lo que escribió el alumno **o** el título de su apartado.

    `LIKE` sin `lower()` a propósito: SQLite ya compara `LIKE` sin distinguir mayúsculas en ASCII,
    y envolver la columna en una función impediría usar el índice si algún día lo hay. Lo que no
    iguala son los acentos («version» no encuentra «versión»), y eso se dice en la pantalla.
    """
    patron = f"%{texto.strip()}%"
    return or_(NotesReportRecord.reason.like(patron), TopicNoteSectionRecord.title.like(patron))


def _aviso(
    aviso: NotesReportRecord,
    nodo: CurriculumNodeRecord,
    apartado: TopicNoteSectionRecord | None,
) -> NoteReport:
    return NoteReport(
        id=str(aviso.id),
        node_id=str(aviso.curriculum_node_id),
        owner_id=str(aviso.owner_id),
        section_key=str(aviso.section_key),
        anchor=str(aviso.anchor),
        reason=str(aviso.reason),
        status=NoteReportStatus(str(aviso.status)),
        created_at=aviso.created_at,
        reviewed_at=aviso.reviewed_at,
        resolution_note=None if aviso.resolution_note is None else str(aviso.resolution_note),
        topic_code=str(nodo.path),
        topic_title=str(nodo.title),
        section_title=None if apartado is None else str(apartado.title),
    )


__all__ = [
    "ACCION_AVISO",
    "ACCION_DESPACHO",
    "ACTOR_ALUMNO",
    "OBJETO_AVISO",
    "SqlAlchemyNotesReportRepository",
]
