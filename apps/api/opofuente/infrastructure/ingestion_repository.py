"""Persistencia de lotes, entradas, incidencias y artefactos.

Cada método abre su propia sesión y confirma al terminar. La siembra de artefactos es idempotente:
el mismo contenido con el mismo origen no crea filas nuevas (dos ficheros idénticos con nombres
distintos sí: son **dos orígenes** del **mismo** artefacto, que es lo que exige S02).
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.read_models import (
    BatchDetail,
    BatchView,
    EntryPage,
    EntryView,
    IssuePage,
    IssueView,
)
from opofuente.domain.artifacts import OriginType, Sha256
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.ingestion import (
    COPIED_ITEM_STATUSES,
    BatchKind,
    BatchMode,
    BatchStatus,
    CountersLike,
    DiscoveredEntry,
    ImportCounters,
    ImportIssue,
    IssueCode,
    ItemStatus,
)
from opofuente.infrastructure.db import as_utc
from opofuente.infrastructure.db_models import (
    ArtifactOriginRecord,
    ImportIssueRecord,
    IngestionBatchRecord,
    IngestionItemRecord,
    SourceArtifactRecord,
)

#: Los estados «copiados» en su forma persistida, para poder filtrar en SQL.
_COPIED_VALUES = tuple(status.value for status in COPIED_ITEM_STATUSES)


def _new_id() -> str:
    return str(uuid4())


class SqlAlchemyIngestionRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ lotes

    def create_batch(
        self,
        *,
        kind: BatchKind,
        mode: BatchMode,
        source_path_display: str,
        now: datetime,
        status: BatchStatus,
        manifest_hash: str | None = None,
        inventory_batch_id: str | None = None,
        job_id: str | None = None,
        source_root: str | None = None,
    ) -> str:
        with self._session_factory() as session:
            record = IngestionBatchRecord(
                id=_new_id(),
                kind=kind.value,
                mode=mode.value,
                status=status.value,
                source_path_display=source_path_display,
                source_root=source_root,
                counters_json=json.dumps({}),
                manifest_hash=manifest_hash,
                created_at=now,
                inventory_batch_id=inventory_batch_id,
                job_id=job_id,
            )
            session.add(record)
            session.commit()
            return record.id

    def add_entries(
        self,
        batch_id: str,
        entries: Iterable[DiscoveredEntry],
        *,
        status: ItemStatus | None = None,
    ) -> int:
        with self._session_factory() as session:
            existing = set(
                session.execute(
                    select(IngestionItemRecord.relative_path).where(
                        IngestionItemRecord.batch_id == batch_id
                    )
                ).scalars()
            )
            position = len(existing)
            created = 0
            for entry in entries:
                if entry.relative_path in existing:
                    continue
                position += 1
                session.add(
                    IngestionItemRecord(
                        id=_new_id(),
                        batch_id=batch_id,
                        relative_path=entry.relative_path,
                        original_name=entry.original_name,
                        size_bytes=entry.size_bytes,
                        mtime=entry.mtime,
                        media_type=entry.media_type or None,
                        status=(status or entry.status).value,
                        detail=entry.issue.safe_message if entry.issue else None,
                        position=position,
                    )
                )
                created += 1
            session.commit()
            return created

    def add_issues(self, batch_id: str, issues: Iterable[ImportIssue], *, now: datetime) -> int:
        with self._session_factory() as session:
            items = {
                row.relative_path: row.id
                for row in session.execute(
                    select(IngestionItemRecord).where(IngestionItemRecord.batch_id == batch_id)
                )
                .scalars()
                .all()
            }
            created = 0
            for issue in issues:
                session.add(
                    ImportIssueRecord(
                        id=_new_id(),
                        batch_id=batch_id,
                        item_id=items.get(issue.relative_path) if issue.relative_path else None,
                        code=issue.code.value,
                        severity=issue.severity.value,
                        safe_message=issue.safe_message,
                        # La ruta se guarda también aquí: un directorio omitido o un enlace que sale
                        # de la carpeta no tienen entrada propia, y sin ella el informe diría *qué*
                        # se omitió pero no *dónde*.
                        relative_path=issue.relative_path,
                        details_json=json.dumps(issue.details) if issue.details else None,
                        created_at=now,
                    )
                )
                created += 1
            session.commit()
            return created

    def set_counters(
        self,
        batch_id: str,
        counters: CountersLike,
        *,
        manifest_hash: str | None = None,
    ) -> None:
        with self._session_factory() as session:
            record = session.get(IngestionBatchRecord, batch_id)
            if record is None:
                raise InvariantViolationError("el lote no existe")
            record.counters_json = json.dumps(counters.to_dict())
            if manifest_hash is not None:
                record.manifest_hash = manifest_hash
            session.commit()

    def find_import_for(self, inventory_batch_id: str) -> BatchView | None:
        """Importación ya creada para ese inventario (para que confirmar dos veces no duplique)."""
        with self._session_factory() as session:
            record = session.execute(
                select(IngestionBatchRecord)
                .where(IngestionBatchRecord.inventory_batch_id == inventory_batch_id)
                .order_by(IngestionBatchRecord.created_at.desc())
                .limit(1)
            ).scalar_one_or_none()
            return self._batch_view(session, record) if record is not None else None

    def source_root_of(self, batch_id: str) -> str | None:
        with self._session_factory() as session:
            record = session.get(IngestionBatchRecord, batch_id)
            return record.source_root if record is not None else None

    def summarize_import(self, batch_id: str) -> ImportCounters:
        """Cuenta el estado real del lote: lo que hay copiado, fallido y cancelado ahora mismo.

        Es lo que hace que el informe cuadre también después de reintentar o reanudar un lote.
        """
        with self._session_factory() as session:
            status_rows = session.execute(
                select(IngestionItemRecord.status, func.count())
                .where(IngestionItemRecord.batch_id == batch_id)
                .group_by(IngestionItemRecord.status)
            ).all()
            bytes_copied = session.execute(
                select(func.coalesce(func.sum(IngestionItemRecord.size_bytes), 0)).where(
                    IngestionItemRecord.batch_id == batch_id,
                    IngestionItemRecord.status.in_(_COPIED_VALUES),
                )
            ).scalar_one()
            source_changed = session.execute(
                select(func.count())
                .select_from(ImportIssueRecord)
                .where(
                    ImportIssueRecord.batch_id == batch_id,
                    ImportIssueRecord.code == IssueCode.SOURCE_CHANGED.value,
                )
            ).scalar_one()

        counts = {str(row[0]): int(row[1]) for row in status_rows}
        failed = counts.get(ItemStatus.FAILED.value, 0) - source_changed
        # Desde S03 una entrada copiada puede estar `hashed` (sin extraer todavía), `extracted`
        # (con texto), `expanded` (un ZIP cuyos miembros son entradas aparte) o `ocr_pending`. La
        # lista la comparten el recuento y los bytes: lo conservado **sin** extraer se cuenta aparte
        # (`preserved_unsupported`), porque no es texto (DEBT-008).
        copied = sum(counts.get(value, 0) for value in _COPIED_VALUES)
        return ImportCounters(
            total=sum(counts.values()),
            copied=copied,
            copied_bytes=int(bytes_copied),
            pending=counts.get(ItemStatus.INVENTORIED.value, 0)
            + counts.get(ItemStatus.DISCOVERED.value, 0),
            source_changed=source_changed,
            failed=max(failed, 0),
            cancelled=counts.get(ItemStatus.CANCELLED.value, 0),
            preserved_unsupported=counts.get(ItemStatus.UNSUPPORTED_PRESERVED.value, 0),
        )

    def reset_items_for_retry(self, batch_id: str) -> int:
        """Devuelve a `inventoried` las entradas recuperables, para volver a intentarlas.

        Se recuperan las canceladas y los fallos transitorios (permisos, fichero bloqueado, fallo de
        copia). **No** se recuperan las entradas cuyo fichero cambió desde el inventario: ese
        inventario ya no describe lo que hay en el origen, así que insistir con él volvería a fallar
        una y otra vez. Para esas hace falta un inventario nuevo, y el servicio lo explica.
        """
        with self._session_factory() as session:
            changed = select(ImportIssueRecord.item_id).where(
                ImportIssueRecord.batch_id == batch_id,
                ImportIssueRecord.code == IssueCode.SOURCE_CHANGED.value,
                ImportIssueRecord.item_id.is_not(None),
            )
            recoverable = (
                IngestionItemRecord.batch_id == batch_id,
                IngestionItemRecord.status.in_(
                    [ItemStatus.CANCELLED.value, ItemStatus.FAILED.value]
                ),
                IngestionItemRecord.id.not_in(changed),
            )
            pending = session.execute(
                select(func.count()).select_from(IngestionItemRecord).where(*recoverable)
            ).scalar_one()
            if pending:
                session.execute(
                    update(IngestionItemRecord)
                    .where(*recoverable)
                    .values(status=ItemStatus.INVENTORIED.value, detail=None)
                )
                session.commit()
            return int(pending)

    def pending_extraction_count(self, batch_id: str) -> int:
        """Entradas copiadas y todavía sin extraer (las que el trabajo de extracción procesará)."""
        with self._session_factory() as session:
            return session.execute(
                select(func.count())
                .select_from(IngestionItemRecord)
                .where(
                    IngestionItemRecord.batch_id == batch_id,
                    IngestionItemRecord.status == ItemStatus.HASHED.value,
                    IngestionItemRecord.artifact_id.is_not(None),
                )
            ).scalar_one()

    def item_id_for(self, batch_id: str, relative_path: str) -> str | None:
        """Identificador de una entrada del lote por su ruta relativa."""
        with self._session_factory() as session:
            return session.execute(
                select(IngestionItemRecord.id).where(
                    IngestionItemRecord.batch_id == batch_id,
                    IngestionItemRecord.relative_path == relative_path,
                )
            ).scalar_one_or_none()

    def count_batch_artifacts(self, batch_id: str) -> int:
        with self._session_factory() as session:
            return session.execute(
                select(func.count(func.distinct(IngestionItemRecord.artifact_id))).where(
                    IngestionItemRecord.batch_id == batch_id,
                    IngestionItemRecord.artifact_id.is_not(None),
                )
            ).scalar_one()

    def issue_exists(self, batch_id: str, code: str, relative_path: str | None) -> bool:
        """¿Ya está esa incidencia en el lote?

        Reintentar un lote vuelve a intentar las mismas entradas: sin esta comprobación, cada
        intento añadiría otra incidencia idéntica y el contador del informe crecería sin que haya
        nada nuevo que contar (y el informe dejaría de cuadrar).
        """
        with self._session_factory() as session:
            conditions = [
                ImportIssueRecord.batch_id == batch_id,
                ImportIssueRecord.code == code,
                ImportIssueRecord.relative_path.is_(None)
                if relative_path is None
                else ImportIssueRecord.relative_path == relative_path,
            ]
            total = session.execute(
                select(func.count()).select_from(ImportIssueRecord).where(*conditions)
            ).scalar_one()
            return int(total) > 0

    def set_status(
        self,
        batch_id: str,
        status: BatchStatus,
        *,
        now: datetime,
        error_summary: str | None = None,
    ) -> None:
        with self._session_factory() as session:
            record = session.get(IngestionBatchRecord, batch_id)
            if record is None:
                raise InvariantViolationError("el lote no existe")
            record.status = status.value
            if status is BatchStatus.RUNNING and record.started_at is None:
                record.started_at = now
            if status in {BatchStatus.SUCCEEDED, BatchStatus.FAILED, BatchStatus.CANCELLED}:
                record.finished_at = now
            if error_summary is not None:
                record.error_summary = error_summary
            session.commit()

    def set_job(self, batch_id: str, job_id: str) -> None:
        with self._session_factory() as session:
            record = session.get(IngestionBatchRecord, batch_id)
            if record is None:
                raise InvariantViolationError("el lote no existe")
            record.job_id = job_id
            session.commit()

    def request_cancel(self, batch_id: str) -> bool:
        """Marca el lote para cancelar. El worker lo detiene entre entradas."""
        with self._session_factory() as session:
            record = session.get(IngestionBatchRecord, batch_id)
            if record is None:
                return False
            if record.status in {
                BatchStatus.SUCCEEDED.value,
                BatchStatus.FAILED.value,
                BatchStatus.CANCELLED.value,
            }:
                return False
            record.status = BatchStatus.CANCEL_REQUESTED.value
            session.commit()
            return True

    def get_batch(self, batch_id: str) -> BatchView | None:
        with self._session_factory() as session:
            record = session.get(IngestionBatchRecord, batch_id)
            if record is None:
                return None
            return self._batch_view(session, record)

    def list_batches(self, *, limit: int, offset: int) -> tuple[BatchView, ...]:
        with self._session_factory() as session:
            records = (
                session.execute(
                    select(IngestionBatchRecord)
                    .order_by(IngestionBatchRecord.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
                .scalars()
                .all()
            )
            return tuple(self._batch_view(session, record) for record in records)

    def get_batch_detail(
        self, batch_id: str, *, entry_limit: int, issue_limit: int
    ) -> BatchDetail | None:
        with self._session_factory() as session:
            record = session.get(IngestionBatchRecord, batch_id)
            if record is None:
                return None
            entries = (
                session.execute(
                    select(IngestionItemRecord)
                    .where(IngestionItemRecord.batch_id == batch_id)
                    .order_by(IngestionItemRecord.position)
                    .limit(entry_limit)
                )
                .scalars()
                .all()
            )
            issues = (
                session.execute(
                    select(ImportIssueRecord)
                    .where(ImportIssueRecord.batch_id == batch_id)
                    .order_by(ImportIssueRecord.created_at)
                    .limit(issue_limit)
                )
                .scalars()
                .all()
            )
            return BatchDetail(
                batch=self._batch_view(session, record),
                entries=tuple(self._entry_view(row) for row in entries),
                issues=tuple(self._issue_view(row) for row in issues),
                artifacts_total=self.count_batch_artifacts(batch_id),
            )

    def list_entries(
        self,
        batch_id: str,
        *,
        limit: int,
        offset: int,
        status: ItemStatus | None = None,
    ) -> EntryPage:
        with self._session_factory() as session:
            query = select(IngestionItemRecord).where(IngestionItemRecord.batch_id == batch_id)
            count_query = (
                select(func.count())
                .select_from(IngestionItemRecord)
                .where(IngestionItemRecord.batch_id == batch_id)
            )
            if status is not None:
                query = query.where(IngestionItemRecord.status == status.value)
                count_query = count_query.where(IngestionItemRecord.status == status.value)
            rows = (
                session.execute(
                    query.order_by(IngestionItemRecord.position).limit(limit).offset(offset)
                )
                .scalars()
                .all()
            )
            total = session.execute(count_query).scalar_one()
            return EntryPage(
                entries=tuple(self._entry_view(row) for row in rows),
                total=total,
                limit=limit,
                offset=offset,
            )

    def list_issues(self, batch_id: str, *, limit: int, offset: int) -> IssuePage:
        with self._session_factory() as session:
            rows = (
                session.execute(
                    select(ImportIssueRecord)
                    .where(ImportIssueRecord.batch_id == batch_id)
                    .order_by(ImportIssueRecord.created_at)
                    .limit(limit)
                    .offset(offset)
                )
                .scalars()
                .all()
            )
            total = session.execute(
                select(func.count())
                .select_from(ImportIssueRecord)
                .where(ImportIssueRecord.batch_id == batch_id)
            ).scalar_one()
            return IssuePage(
                issues=tuple(self._issue_view(row) for row in rows),
                total=total,
                limit=limit,
                offset=offset,
            )

    def pending_entries(self, batch_id: str) -> Sequence[EntryView]:
        """Entradas todavía sin copiar, en orden: es lo que consume el worker."""
        with self._session_factory() as session:
            rows = (
                session.execute(
                    select(IngestionItemRecord)
                    .where(
                        IngestionItemRecord.batch_id == batch_id,
                        IngestionItemRecord.status.in_(
                            [ItemStatus.INVENTORIED.value, ItemStatus.DISCOVERED.value]
                        ),
                    )
                    .order_by(IngestionItemRecord.position)
                )
                .scalars()
                .all()
            )
            return tuple(self._entry_view(row) for row in rows)

    def mark_item(
        self,
        item_id: str,
        status: ItemStatus,
        *,
        artifact_id: str | None = None,
        detail: str | None = None,
    ) -> None:
        with self._session_factory() as session:
            record = session.get(IngestionItemRecord, item_id)
            if record is None:
                raise InvariantViolationError("la entrada del lote no existe")
            record.status = status.value
            if artifact_id is not None:
                record.artifact_id = artifact_id
            if detail is not None:
                record.detail = detail
            session.commit()

    # ------------------------------------------------------------------ artefactos

    def register_artifact(
        self,
        *,
        digest: Sha256,
        size_bytes: int,
        media_type: str,
        storage_key: str,
        origin_type: OriginType,
        display_location: str,
        original_name: str | None,
        source_path_display: str | None,
        file_mtime: datetime | None,
        now: datetime,
    ) -> tuple[str, bool]:
        """Registra el artefacto y su origen. Devuelve (id, es_nuevo)."""
        with self._session_factory() as session:
            record = session.execute(
                select(SourceArtifactRecord).where(SourceArtifactRecord.sha256 == digest.value)
            ).scalar_one_or_none()
            created = False
            if record is None:
                record = SourceArtifactRecord(
                    id=_new_id(),
                    sha256=digest.value,
                    size_bytes=size_bytes,
                    media_type=media_type,
                    storage_key=storage_key,
                    first_seen_at=now,
                    quarantine_status="none",
                )
                session.add(record)
                session.flush()
                created = True

            origin = session.execute(
                select(ArtifactOriginRecord).where(
                    ArtifactOriginRecord.artifact_id == record.id,
                    ArtifactOriginRecord.display_location == display_location,
                )
            ).scalar_one_or_none()
            if origin is None:
                session.add(
                    ArtifactOriginRecord(
                        id=_new_id(),
                        artifact_id=record.id,
                        origin_type=origin_type.value,
                        display_location=display_location,
                        source_path_display=source_path_display,
                        original_name=original_name,
                        accessed_at=now,
                        size_bytes=size_bytes,
                        mtime=file_mtime,
                    )
                )
            else:
                origin.accessed_at = now
                origin.size_bytes = size_bytes
                origin.mtime = file_mtime
            session.commit()
            return record.id, created

    # ------------------------------------------------------------------ conversión

    def _batch_view(self, session: Session, record: IngestionBatchRecord) -> BatchView:
        counters = json.loads(record.counters_json or "{}")
        formats: dict[str, int] = {}
        rows = session.execute(
            select(IngestionItemRecord.original_name, IngestionItemRecord.status).where(
                IngestionItemRecord.batch_id == record.id
            )
        ).all()
        for name, item_status in rows:
            if item_status != ItemStatus.INVENTORIED.value:
                continue
            suffix = Path(name).suffix.lower() or "(sin extensión)"
            formats[suffix] = formats.get(suffix, 0) + 1
        issue_rows = session.execute(
            select(ImportIssueRecord.code, func.count())
            .where(ImportIssueRecord.batch_id == record.id)
            .group_by(ImportIssueRecord.code)
        ).all()
        return BatchView(
            id=record.id,
            kind=record.kind,
            mode=record.mode,
            status=record.status,
            source_path_display=record.source_path_display,
            counters={key: int(value) for key, value in counters.items()},
            created_at=record.created_at,
            started_at=record.started_at,
            finished_at=record.finished_at,
            job_id=record.job_id,
            inventory_batch_id=record.inventory_batch_id,
            manifest_hash=record.manifest_hash,
            error_summary=record.error_summary,
            formats=dict(sorted(formats.items())),
            issue_counts={str(row[0]): int(row[1]) for row in issue_rows},
            total_items=len(rows),
        )

    @staticmethod
    def _entry_view(record: IngestionItemRecord) -> EntryView:
        return EntryView(
            id=record.id,
            relative_path=record.relative_path,
            original_name=record.original_name,
            size_bytes=record.size_bytes,
            media_type=record.media_type,
            status=record.status,
            detail=record.detail,
            artifact_sha256=None,
            mtime=as_utc(record.mtime),
        )

    @staticmethod
    def _issue_view(record: ImportIssueRecord) -> IssueView:
        return IssueView(
            code=record.code,
            severity=record.severity,
            safe_message=record.safe_message,
            relative_path=record.relative_path,
            details=json.loads(record.details_json) if record.details_json else {},
        )
