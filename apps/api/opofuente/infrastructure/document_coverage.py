"""Cobertura de programa calculada sobre **documentos** (S05).

S04 dejó la cobertura contando artefactos y representaciones. Con la biblioteca, lo que cubre
un tema
es un **documento** con su versión, y eso cambia dos cosas que importan:

- una versión **candidata** es una propuesta de cambio: **no** sostiene cobertura aceptada, aunque
  su mapeo esté aceptado;
- una versión cuya representación es **pobre** o no revisada tampoco: la regla de calidad ya existía
  (`coverage_counts_as_accepted`) y aquí se aplica a documentos.

El resultado se sirve con el mismo `CoverageView` de S04, para que la interfaz no tenga que
conocer dos
formas de contar lo mismo.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.read_models import CoverageNodeView, CoverageView
from opofuente.domain.classification import MappingStatus, coverage_counts_as_accepted
from opofuente.domain.documents import VersionStatus
from opofuente.domain.extraction import Quality
from opofuente.infrastructure.curriculum_order import curriculum_order
from opofuente.infrastructure.db_models import (
    ConvocationVersionRecord,
    CurriculumMappingRecord,
    CurriculumNodeRecord,
    DocumentVersionRecord,
    ExtractedRepresentationRecord,
    LogicalDocumentRecord,
)

#: Tipo de sujeto de un mapeo que apunta a una versión de documento.
SUBJECT_DOCUMENT_VERSION = "document_version"

_ORDEN_CALIDAD = {
    Quality.GOOD.value: 0,
    Quality.USABLE_WITH_WARNINGS.value: 1,
    Quality.OCR_UNREVIEWED.value: 2,
    Quality.POOR.value: 3,
    Quality.FAILED.value: 4,
}


def _quality(valor: str | None) -> Quality | None:
    if valor is None:
        return None
    try:
        return Quality(valor)
    except ValueError:
        return None


def _mejor_calidad(session: Session, artifact_ids: Sequence[str]) -> dict[str, Quality]:
    """Mejor calidad de las representaciones de cada artefacto."""
    if not artifact_ids:
        return {}
    filas = session.execute(
        select(
            ExtractedRepresentationRecord.artifact_id,
            ExtractedRepresentationRecord.quality,
        ).where(ExtractedRepresentationRecord.artifact_id.in_(artifact_ids))
    ).all()
    mejores: dict[str, Quality] = {}
    for artifact_id, quality in filas:
        valor = _quality(str(quality))
        if valor is None:
            continue
        actual = mejores.get(str(artifact_id))
        if actual is None or _ORDEN_CALIDAD[valor.value] < _ORDEN_CALIDAD[actual.value]:
            mejores[str(artifact_id)] = valor
    return mejores


def document_coverage(
    session_factory: sessionmaker[Session], *, convocation_code: str
) -> CoverageView:
    """Cobertura provisional y aceptada de una convocatoria, contando documentos."""
    with session_factory() as session:
        nodos = (
            session.execute(
                select(CurriculumNodeRecord)
                .join(
                    ConvocationVersionRecord,
                    ConvocationVersionRecord.id == CurriculumNodeRecord.convocation_version_id,
                )
                .where(ConvocationVersionRecord.code == convocation_code)
                .order_by(*curriculum_order(CurriculumNodeRecord.path))
            )
            .scalars()
            .all()
        )
        ids_nodos = [nodo.id for nodo in nodos]
        mapeos = (
            session.execute(
                select(CurriculumMappingRecord).where(
                    CurriculumMappingRecord.curriculum_node_id.in_(ids_nodos),
                    CurriculumMappingRecord.subject_type == SUBJECT_DOCUMENT_VERSION,
                )
            )
            .scalars()
            .all()
            if ids_nodos
            else []
        )
        versiones = {
            version.id: version
            for version in session.execute(
                select(DocumentVersionRecord).where(
                    DocumentVersionRecord.id.in_([mapeo.subject_id for mapeo in mapeos])
                )
            )
            .scalars()
            .all()
        }
        documentos = {
            documento.id: documento.canonical_title
            for documento in session.execute(
                select(LogicalDocumentRecord).where(
                    LogicalDocumentRecord.id.in_(
                        [version.logical_document_id for version in versiones.values()]
                    )
                )
            )
            .scalars()
            .all()
        }
        calidades = _mejor_calidad(session, [version.artifact_id for version in versiones.values()])
        documentos_con_version = int(
            session.execute(
                select(func.count(func.distinct(DocumentVersionRecord.logical_document_id)))
            ).scalar_one()
        )
        documentos_mapeados = {
            versiones[mapeo.subject_id].logical_document_id
            for mapeo in mapeos
            if mapeo.subject_id in versiones
        }

    provisional: dict[str, set[str]] = defaultdict(set)
    aceptada: dict[str, set[str]] = defaultdict(set)
    materiales: dict[str, list[str]] = defaultdict(list)
    for mapeo in mapeos:
        version = versiones.get(mapeo.subject_id)
        if version is None:
            continue
        documento_id = version.logical_document_id
        titulo = documentos.get(documento_id, documento_id)
        if mapeo.status == MappingStatus.PROVISIONAL.value:
            provisional[mapeo.curriculum_node_id].add(documento_id)
        elif version.status == VersionStatus.ACCEPTED.value and coverage_counts_as_accepted(
            calidades.get(version.artifact_id), MappingStatus(mapeo.status)
        ):
            aceptada[mapeo.curriculum_node_id].add(documento_id)
        else:
            # El mapeo está aceptado, pero la versión no lo sostiene (es candidata o su texto es
            # pobre): cuenta como provisional. Ni se esconde ni se vende como cobertura confirmada.
            provisional[mapeo.curriculum_node_id].add(documento_id)
        if (
            documento_id not in materiales[mapeo.curriculum_node_id][:3]
            and len(materiales[mapeo.curriculum_node_id]) < 3
        ):
            materiales[mapeo.curriculum_node_id].append(titulo)

    # Lo aceptado manda: un documento no se cuenta a la vez como provisional y como aceptado.
    for nodo_id, claves in aceptada.items():
        provisional[nodo_id] -= claves

    vistas = tuple(
        CoverageNodeView(
            node_id=nodo.id,
            path=nodo.path,
            title=nodo.title,
            depth=nodo.depth,
            provisional=len(provisional.get(nodo.id, ())),
            accepted=len(aceptada.get(nodo.id, ())),
            materials=tuple(materiales.get(nodo.id, ())),
        )
        for nodo in nodos
    )
    return CoverageView(
        convocation_code=convocation_code,
        nodes=vistas,
        provisional_total=sum(len(valor) for valor in provisional.values()),
        accepted_total=sum(len(valor) for valor in aceptada.values()),
        classified_subjects=len(documentos_mapeados),
        unclassified_subjects=max(0, documentos_con_version - len(documentos_mapeados)),
        materials_total=documentos_con_version,
    )
