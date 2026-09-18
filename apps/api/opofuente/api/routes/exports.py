"""Rutas de exportación (08_API-CONTRACT §11): Anki CSV y Markdown/Obsidian.

Las dos rutas de §11, sin añadidos. Escriben el fichero en `<datos>/exports` y devuelven su
contenido y su procedencia: la interfaz puede entonces ofrecer la descarga y decir, antes de que
nadie use el fichero fuera de aquí, qué material restringido lleva dentro.
"""

from __future__ import annotations

from fastapi import APIRouter

from opofuente.api.deps import ExportServiceDep
from opofuente.api.error_responses import INGESTION_WRITE_ERRORS
from opofuente.api.export_schemas import ExportFormatName, ExportRequestSchema, ExportSchema
from opofuente.application.export_service import ExportRequest
from opofuente.domain.export import ExportDocument

router = APIRouter(tags=["exportación"])


def _request(schema: ExportRequestSchema) -> ExportRequest:
    return ExportRequest(
        opposition_id=schema.opposition_id,
        question_set_id=schema.question_set_id,
        node_id=schema.node_id,
        include_restricted=schema.include_restricted,
        title=schema.title,
    )


def _export(documento: ExportDocument) -> ExportSchema:
    # El formato es texto libre en el servicio; el contrato declara dos valores, y aquí se
    # traducen sin inventar un tercero.
    formato: ExportFormatName = "anki_csv" if documento.format == "anki_csv" else "markdown"
    return ExportSchema(
        filename=documento.filename,
        format=formato,
        path=documento.provenance.get("path", documento.filename),
        bytes=len(documento.content.encode("utf-8")),
        item_count=documento.item_count,
        documents=list(documento.documents),
        warnings=list(documento.warnings),
        provenance=dict(documento.provenance),
        content=documento.content,
    )


@router.post(
    "/exports/anki-csv",
    response_model=ExportSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Exporta el banco a CSV de Anki, con su procedencia",
)
def export_anki_csv(request: ExportRequestSchema, service: ExportServiceDep) -> ExportSchema:
    return _export(service.anki_csv(_request(request)))


@router.post(
    "/exports/markdown",
    response_model=ExportSchema,
    responses=INGESTION_WRITE_ERRORS,
    summary="Exporta el banco a Markdown para Obsidian, con sus citas",
)
def export_markdown(request: ExportRequestSchema, service: ExportServiceDep) -> ExportSchema:
    return _export(service.markdown(_request(request)))
