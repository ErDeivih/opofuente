"""Persistencia de representaciones extraídas y de lo que necesita la extracción (S03).

Dos responsabilidades, y ninguna más:

- guardar y leer `extracted_representations`, que es la memoria de qué texto se ha sacado de cada
  artefacto, por qué extractor, con qué calidad y con qué avisos;
- responder a la pregunta «qué queda por extraer en este lote y de qué artefacto», que es lo que
  consume el trabajo del worker.

El texto no se guarda aquí: vive en el árbol de datos y esta tabla apunta a él.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.read_models import RepresentationSource, RepresentationView
from opofuente.domain.extraction import ExtractionResult
from opofuente.domain.ingestion import ItemStatus
from opofuente.infrastructure.db import as_utc
from opofuente.infrastructure.db_models import (
    ExtractedRepresentationRecord,
    IngestionItemRecord,
    ItemRepresentationRecord,
    SourceArtifactRecord,
)


def _new_id() -> str:
    return str(uuid4())


def _source_of(item: IngestionItemRecord) -> RepresentationSource:
    """Procedencia de una entrada: cómo se muestra su origen, su tipo y su profundidad.

    Se usa `origin_display` (la URL saneada, el título del texto pegado o la ruta relativa del
    fichero) y no `relative_path`: si no, la procedencia que ve el usuario no era la saneada que se
    había guardado, y una descarga aparecía con el nombre del artefacto en lugar de su dirección.
    """
    return RepresentationSource(
        location=str(item.origin_display or item.relative_path),
        origin_type=item.origin_type,
        depth=int(item.container_depth or 0),
    )


@dataclass(frozen=True, slots=True)
class PendingExtraction:
    """Una entrada copiada que todavía no se ha extraído, con lo necesario para hacerlo."""

    item_id: str
    batch_id: str
    relative_path: str
    original_name: str
    media_type: str | None
    size_bytes: int
    artifact_id: str
    sha256: str
    storage_key: str
    origin_type: str | None = None
    """De dónde vino **esta** entrada (`file`, `url`, `paste`): el texto pegado se marca aparte."""
    container_depth: int = 0
    """Niveles de contenedor recorridos: decide si un ZIP que está dentro de otro se expande."""


class SqlAlchemyExtractionRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ representaciones

    def save(
        self,
        *,
        result: ExtractionResult,
        artifact_id: str,
        representation_id: str | None = None,
        text_storage_key: str | None = None,
        now: datetime,
        format_version: int = 1,
    ) -> tuple[str, bool]:
        """Guarda la representación. Devuelve `(id, es_nueva)`.

        Es idempotente por `(artefacto, extractor, versión, tipo)`: volver a ejecutar el mismo
        extractor sobre el mismo artefacto devuelve la representación que ya había, así que
        reintentar un lote no multiplica filas. Otra versión del extractor **sí** crea otra.

        El llamante puede proponer el identificador (`representation_id`) para poder escribir antes
        el texto en `data/extracted/<id>/` y guardar la fila una sola vez, ya con su clave.
        """
        with self._session_factory() as session:
            existing = session.execute(
                select(ExtractedRepresentationRecord).where(
                    ExtractedRepresentationRecord.artifact_id == artifact_id,
                    ExtractedRepresentationRecord.extractor_name == result.extractor.name,
                    ExtractedRepresentationRecord.extractor_version == result.extractor.version,
                    ExtractedRepresentationRecord.kind == result.kind.value,
                )
            ).scalar_one_or_none()
            if existing is not None:
                return existing.id, False
            record = ExtractedRepresentationRecord(
                id=representation_id or _new_id(),
                artifact_id=artifact_id,
                extractor_name=result.extractor.name,
                extractor_version=result.extractor.version,
                kind=result.kind.value,
                status=result.status.value,
                quality=result.quality.value,
                language=result.language,
                text_storage_key=text_storage_key,
                char_count=result.char_count,
                page_count=result.page_count,
                ocr_candidate=result.ocr_candidate,
                sections_json=json.dumps(
                    [
                        {
                            "section_type": section.section_type.value,
                            "position": section.position,
                            "char_start": section.char_start,
                            "char_end": section.char_end,
                            "label": section.label,
                            "title": section.title,
                            "page_start": section.page_start,
                            "page_end": section.page_end,
                        }
                        for section in result.sections
                    ],
                    ensure_ascii=False,
                ),
                warnings_json=json.dumps([code.value for code in result.warnings]),
                metadata_json=json.dumps(result.metadata, ensure_ascii=False, default=str),
                format_version=format_version,
                created_at=now,
            )
            session.add(record)
            session.commit()
            return record.id, True

    def find_id(
        self,
        *,
        artifact_id: str,
        extractor_name: str,
        extractor_version: str,
        kind: str,
    ) -> str | None:
        """Identificador de la representación que ya existe para esa clave, si la hay.

        Se consulta **antes** de escribir el texto: el texto se guarda en un directorio propio y, si
        la fila ya existía, ese directorio quedaba huérfano (basura física que nadie lee).
        """
        with self._session_factory() as session:
            return session.execute(
                select(ExtractedRepresentationRecord.id).where(
                    ExtractedRepresentationRecord.artifact_id == artifact_id,
                    ExtractedRepresentationRecord.extractor_name == extractor_name,
                    ExtractedRepresentationRecord.extractor_version == extractor_version,
                    ExtractedRepresentationRecord.kind == kind,
                )
            ).scalar_one_or_none()

    def get(self, representation_id: str) -> RepresentationView | None:
        with self._session_factory() as session:
            record = session.get(ExtractedRepresentationRecord, representation_id)
            if record is None:
                return None
            return replace(
                self._view(record), sources=self._sources_of_representation(session, record.id)
            )

    def list_for_batch(self, batch_id: str) -> tuple[RepresentationView, ...]:
        """Representaciones que salieron de las entradas de un lote, en orden de entrada.

        El enlace es la tabla `item_representations`, no el artefacto: un artefacto puede tener
        varias representaciones (texto nativo, OCR y una por versión de extractor) y unirlas por
        artefacto enseñaba en un lote el texto producido en otro. Dos entradas con el mismo
        contenido sí comparten representación: ahí sale **una** fila con las dos procedencias.
        """
        with self._session_factory() as session:
            rows = session.execute(
                select(ExtractedRepresentationRecord, IngestionItemRecord)
                .join(
                    ItemRepresentationRecord,
                    ItemRepresentationRecord.representation_id == ExtractedRepresentationRecord.id,
                )
                .join(
                    IngestionItemRecord,
                    IngestionItemRecord.id == ItemRepresentationRecord.item_id,
                )
                .where(IngestionItemRecord.batch_id == batch_id)
                .order_by(IngestionItemRecord.position, ExtractedRepresentationRecord.created_at)
            ).all()
            vistas: dict[str, RepresentationView] = {}
            fuentes: dict[str, list[RepresentationSource]] = {}
            for record, item in rows:
                if record.id not in vistas:
                    vistas[record.id] = self._view(record)
                    fuentes[record.id] = []
                source = _source_of(item)
                if source not in fuentes[record.id]:
                    fuentes[record.id].append(source)
            return tuple(replace(view, sources=tuple(fuentes[view.id])) for view in vistas.values())

    # ------------------------------------------------------------------ entradas pendientes

    def pending_extraction(self, batch_id: str, *, limit: int) -> tuple[PendingExtraction, ...]:
        """Entradas copiadas y todavía sin extraer, con el artefacto del que sale su contenido.

        `unsupported_preserved` no aparece aquí: esas entradas ya están decididas y no se extraen.
        El origen de la entrada (`paste`, `url`, `file`) y su profundidad de contenedor viajan con
        ella: el texto pegado se marca con un tipo de representación distinto y el anidamiento de
        ZIP se decide con un dato persistido, no con el nombre del fichero.
        """
        with self._session_factory() as session:
            rows = session.execute(
                select(IngestionItemRecord, SourceArtifactRecord)
                .join(
                    SourceArtifactRecord,
                    SourceArtifactRecord.id == IngestionItemRecord.artifact_id,
                )
                .where(
                    IngestionItemRecord.batch_id == batch_id,
                    IngestionItemRecord.status == ItemStatus.HASHED.value,
                    IngestionItemRecord.artifact_id.is_not(None),
                )
                .order_by(IngestionItemRecord.position)
                .limit(limit)
            ).all()
            return tuple(
                PendingExtraction(
                    item_id=item.id,
                    batch_id=item.batch_id,
                    relative_path=item.relative_path,
                    original_name=item.original_name,
                    media_type=item.media_type,
                    size_bytes=item.size_bytes,
                    artifact_id=artifact.id,
                    sha256=artifact.sha256,
                    storage_key=artifact.storage_key,
                    origin_type=item.origin_type,
                    container_depth=int(item.container_depth or 0),
                )
                for item, artifact in rows
            )

    def pending_extraction_count(self, batch_id: str) -> int:
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

    # ------------------------------------------------------------------ conversión

    @staticmethod
    def _sources_of_representation(
        session: Session, representation_id: str
    ) -> tuple[RepresentationSource, ...]:
        """Procedencia de un texto leído sin contexto de lote: las entradas que lo produjeron.

        Cada entrada aporta **su** origen y su profundidad, así que no se puede atribuir a unos
        bytes el tipo de origen de otros bytes parecidos.
        """
        items = (
            session.execute(
                select(IngestionItemRecord)
                .join(
                    ItemRepresentationRecord,
                    ItemRepresentationRecord.item_id == IngestionItemRecord.id,
                )
                .where(ItemRepresentationRecord.representation_id == representation_id)
                .order_by(IngestionItemRecord.batch_id, IngestionItemRecord.position)
            )
            .scalars()
            .all()
        )
        fuentes: list[RepresentationSource] = []
        for item in items:
            source = _source_of(item)
            if source not in fuentes:
                fuentes.append(source)
        return tuple(fuentes)

    @staticmethod
    def _view(record: ExtractedRepresentationRecord) -> RepresentationView:
        warnings = tuple(json.loads(record.warnings_json or "[]"))
        return RepresentationView(
            id=record.id,
            artifact_id=record.artifact_id,
            kind=record.kind,
            status=record.status,
            quality=record.quality,
            extractor_name=record.extractor_name,
            extractor_version=record.extractor_version,
            language=record.language,
            char_count=int(record.char_count),
            page_count=record.page_count,
            ocr_candidate=bool(record.ocr_candidate),
            warnings=warnings,
            created_at=as_utc(record.created_at) or record.created_at,
            has_text=record.text_storage_key is not None,
            storage_key=record.text_storage_key,
            format_version=int(record.format_version),
        )
