"""Los avisos del alumno sobre los apuntes: se guardan y se leen (decisión D2).

Dos cosas y las dos con una regla detrás:

1. **guardar es una escritura auditada**, no un apunte suelto: la fila del aviso y el evento de
   auditoría entran en la **misma transacción**. Un aviso sin su evento sería una escritura que
   nadie puede reconstruir, y un evento sin aviso, una traza que miente. El evento lleva la
   referencia (tema, apartado, identificador del aviso) y **no** el texto que escribió el alumno:
   `audit_events` guarda el antes/después sanitizado y nunca contenido.
2. **leer resuelve el título del apartado contra los apuntajes de hoy**, con un `LEFT JOIN`. Un
   aviso que apuntaba a un apartado que ya no existe se sigue leyendo (con el título vacío), porque
   borrarlo sería perder justo el caso que hay que mirar: el texto cambió debajo del aviso.
"""

from __future__ import annotations

import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.domain.notes_reports import NoteReport, NoteReportFilter, NoteReportStatus
from opofuente.infrastructure.db_models import (
    AuditEventRecord,
    CurriculumNodeRecord,
    NotesReportRecord,
    TopicNoteSectionRecord,
)

#: Quién firma el evento de auditoría cuando el aviso lo escribe el alumno.
ACTOR_ALUMNO = "alumno"

#: La acción del evento, con el mismo vocabulario `objeto.verbo` que el resto de la auditoría.
ACCION_AVISO = "notes.report_created"


class SqlAlchemyNotesReportRepository:
    """Guarda un aviso del alumno y lista los que esperan al propietario."""

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

    def list_reports(self, filtro: NoteReportFilter | None = None) -> tuple[NoteReport, ...]:
        """Los avisos, del más nuevo al más viejo, con el tema y el apartado resueltos.

        El `LEFT JOIN` con los apartados es deliberado: un aviso cuyo apartado ya no existe sigue
        saliendo en la bandeja con `section_title` vacío. Es el aviso más interesante de todos —el
        texto se ha reescrito debajo— y esconderlo sería justo lo contrario de lo que hace falta.
        """
        consulta = (
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
            .order_by(NotesReportRecord.created_at.desc(), NotesReportRecord.id.desc())
        )
        if filtro is not None:
            if filtro.status is not None:
                consulta = consulta.where(NotesReportRecord.status == filtro.status.value)
            if filtro.topic_code is not None:
                consulta = consulta.where(CurriculumNodeRecord.path == filtro.topic_code)
            consulta = consulta.limit(filtro.limit)
        with self._session_factory() as session:
            filas = session.execute(consulta).all()
        return tuple(_aviso(aviso, nodo, apartado) for aviso, nodo, apartado in filas)

    def count_open(self) -> int:
        """Cuántos avisos esperan a que alguien los lea."""
        with self._session_factory() as session:
            return int(
                session.execute(
                    select(func.count())
                    .select_from(NotesReportRecord)
                    .where(NotesReportRecord.status == NoteReportStatus.OPEN.value)
                ).scalar_one()
            )


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
        topic_code=str(nodo.path),
        topic_title=str(nodo.title),
        section_title=None if apartado is None else str(apartado.title),
    )


__all__ = ["ACCION_AVISO", "ACTOR_ALUMNO", "SqlAlchemyNotesReportRepository"]
