"""Repositorio de higiene: consultas de «qué hay» y «qué sobra» (DEBT-007).

La pieza delicada de este módulo es la consulta de **artefactos huérfanos**: un artefacto solo se
propone retirar si **ninguna** tabla lo referencia. Se comprueban todas las que pueden hacerlo, y
añadir una tabla nueva que apunte a `source_artifacts` obliga a añadirla aquí: si no, la higiene
propondría retirar material en uso, que es el fallo que esta consulta existe para impedir.

Las referencias que se comprueban, una por una y con su motivo:

- `artifact_origins`: de dónde entró (la más habitual: un artefacto sin origen no se puede citar);
- `document_versions`: una versión de documento se apoya en un artefacto;
- `extracted_representations`: el texto extraído apunta al artefacto del que salió;
- `item_representations`: la relación entrada-representación de la bandeja;
- `ingestion_items.artifact_id`: lo que el lote copió.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session, sessionmaker

from opofuente.domain.housekeeping import HousekeepingAction, HousekeepingCandidate
from opofuente.infrastructure.db_models import (
    ArtifactOriginRecord,
    DocumentVersionRecord,
    ExtractedRepresentationRecord,
    JobRecord,
    SourceArtifactRecord,
)

#: Estados de trabajo en los que nadie va a volver a mirarlo: son los candidatos a retirar.
TERMINAL_JOB_STATUSES = ("succeeded", "failed", "cancelled")


class SqlAlchemyHousekeepingRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def counts(self) -> dict[str, int]:
        """Recuentos de material: lo que la pantalla de diagnóstico enseña sin exponer contenido."""
        with self._session_factory() as session:
            return {
                "artifacts": _count(session, SourceArtifactRecord),
                "artifact_origins": _count(session, ArtifactOriginRecord),
                "document_versions": _count(session, DocumentVersionRecord),
                "representations": _count(session, ExtractedRepresentationRecord),
                "jobs": _count(session, JobRecord),
                "jobs_pending": int(
                    session.execute(
                        select(func.count())
                        .select_from(JobRecord)
                        .where(JobRecord.status.not_in(TERMINAL_JOB_STATUSES))
                    ).scalar_one()
                ),
                "evidence_spans": _scalar(session, "SELECT COUNT(*) FROM evidence_spans"),
                "questions": _scalar(session, "SELECT COUNT(*) FROM question_versions"),
                "study_sessions": _scalar(session, "SELECT COUNT(*) FROM study_sessions"),
                "rag_queries": _scalar(session, "SELECT COUNT(*) FROM rag_queries"),
                "learning_errors": _scalar(session, "SELECT COUNT(*) FROM learning_errors"),
                "change_sets": _scalar(session, "SELECT COUNT(*) FROM change_sets"),
            }

    def orphan_artifacts(self) -> tuple[tuple[str, str], ...]:
        """Artefactos sin ninguna referencia: `(id, storage_key)`.

        La guarda es un `NOT EXISTS` por cada tabla que puede referenciar un artefacto; si alguna
        encuentra algo, el artefacto **no** entra en la lista.
        """
        with self._session_factory() as session:
            filas = session.execute(
                text(
                    """
                    SELECT a.id, a.storage_key, a.size_bytes
                    FROM source_artifacts a
                    WHERE NOT EXISTS (
                            SELECT 1 FROM artifact_origins o WHERE o.artifact_id = a.id
                          )
                      AND NOT EXISTS (
                            SELECT 1 FROM document_versions v WHERE v.artifact_id = a.id
                          )
                      AND NOT EXISTS (
                            SELECT 1 FROM extracted_representations r WHERE r.artifact_id = a.id
                          )
                      AND NOT EXISTS (
                            SELECT 1 FROM item_representations ir
                            JOIN extracted_representations r2 ON r2.id = ir.representation_id
                            WHERE r2.artifact_id = a.id
                          )
                      AND NOT EXISTS (
                            SELECT 1 FROM ingestion_items i WHERE i.artifact_id = a.id
                          )
                    ORDER BY a.first_seen_at
                    """
                )
            ).all()
            return tuple((str(fila[0]), str(fila[1])) for fila in filas)

    def artifact_sizes(self, identifiers: tuple[str, ...]) -> dict[str, int]:
        if not identifiers:
            return {}
        with self._session_factory() as session:
            filas = session.execute(
                select(SourceArtifactRecord.id, SourceArtifactRecord.size_bytes).where(
                    SourceArtifactRecord.id.in_(identifiers)
                )
            ).all()
            return {str(fila[0]): int(fila[1]) for fila in filas}

    def delete_artifacts(self, identifiers: tuple[str, ...]) -> int:
        """Retira las filas de artefactos **sin referencia**, y solo esas.

        La condición se repite en el `DELETE`: entre la foto y la retirada puede haber pasado
        tiempo y
        alguien puede haber promocionado el artefacto. Retirar por identificador sin volver a
        comprobar sería confiar en una foto vieja.
        """
        if not identifiers:
            return 0
        with self._session_factory() as session:
            # Se vuelve a comprobar la huerfandad **aquí** y se cuentan los identificadores que
            # quedan: entre la foto y la retirada puede haber pasado tiempo y alguien puede haber
            # promocionado el artefacto. Contar lo que se va a borrar, en vez de leer el `rowcount`,
            # hace que el número informado sea el de la comprobación, no el del motor.
            restantes = tuple(
                identificador
                for identificador, _ in self.orphan_artifacts()
                if identificador in set(identifiers)
            )
            if not restantes:
                return 0
            session.execute(
                delete(SourceArtifactRecord).where(SourceArtifactRecord.id.in_(restantes))
            )
            session.commit()
            return len(restantes)

    def old_jobs(self, *, older_than_days: int, now: datetime) -> tuple[tuple[str, str], ...]:
        """Trabajos en estado terminal anteriores al periodo de retención: `(id, status)`."""
        limite = now - timedelta(days=older_than_days)
        with self._session_factory() as session:
            filas = session.execute(
                select(JobRecord.id, JobRecord.status)
                .where(JobRecord.status.in_(TERMINAL_JOB_STATUSES))
                .where(JobRecord.updated_at < limite)
                .order_by(JobRecord.updated_at)
            ).all()
            return tuple((str(fila[0]), str(fila[1])) for fila in filas)

    def delete_jobs(self, identifiers: tuple[str, ...]) -> int:
        """Retira trabajos terminados y antiguos. Cuenta los que había, no lo que diga el motor."""
        if not identifiers:
            return 0
        with self._session_factory() as session:
            existentes = tuple(
                str(fila)
                for fila in session.execute(
                    select(JobRecord.id)
                    .where(JobRecord.id.in_(identifiers))
                    .where(JobRecord.status.in_(TERMINAL_JOB_STATUSES))
                ).scalars()
            )
            if not existentes:
                return 0
            session.execute(delete(JobRecord).where(JobRecord.id.in_(existentes)))
            session.commit()
            return len(existentes)

    def unused_document_versions_without_artifact(self) -> tuple[str, ...]:
        """Versiones cuya fila sigue ahí pero cuyo artefacto ya no está: es un descuadre, no basura.

        Se informa en el diagnóstico para que se vea, y **no** se toca: una versión sin su artefacto
        es un problema de integridad que se resuelve a mano y con la copia de seguridad delante.
        """
        with self._session_factory() as session:
            filas = session.execute(
                text(
                    """
                    SELECT v.id
                    FROM document_versions v
                    LEFT JOIN source_artifacts a ON a.id = v.artifact_id
                    WHERE a.id IS NULL
                    """
                )
            ).all()
            return tuple(str(fila[0]) for fila in filas)


def _count(session: Session, model: type[object]) -> int:
    return int(session.execute(select(func.count()).select_from(model)).scalar_one())


def _scalar(session: Session, sql: str) -> int:
    """Recuento de una tabla que puede no existir todavía (migración a medias): se declara cero."""
    try:
        return int(session.execute(text(sql)).scalar_one())
    except Exception:
        # Una tabla ausente (migración a medias) no puede tumbar el diagnóstico: se declara cero.
        session.rollback()
        return 0


def candidate_for_artifact(
    identifier: str, storage_key: str, size_bytes: int
) -> HousekeepingCandidate:
    return HousekeepingCandidate(
        action=HousekeepingAction.ORPHAN_ARTIFACT,
        reference=identifier,
        detail=(
            f"artefacto sin origen ni documento que lo use ({storage_key}); "
            "no sostiene ninguna cita ni cobertura"
        ),
        size_bytes=size_bytes,
        relative_path=storage_key,
    )


__all__ = [
    "TERMINAL_JOB_STATUSES",
    "SqlAlchemyHousekeepingRepository",
    "candidate_for_artifact",
]
