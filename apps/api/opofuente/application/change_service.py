"""Caso de uso: cambios, derivados e invalidación selectiva (S11).

Lo que decide este servicio:

1. **cuándo hay un cambio que proponer**: cuando llega una versión nueva de un documento que ya
   tenía una aceptada. Se calcula el diff por sección, se recorren las dependencias guardadas y se
   dice qué queda afectado. **No se aplica nada**: aceptar la versión, sustituir la anterior y
   marcar derivados ocurre al confirmar;
2. **qué se invalida**: solo los derivados que dependen de una sección que cambió o se quitó (la
   regla vive en el dominio). Un derivado que solo depende de secciones intactas no se toca;
3. **qué no se decide**: el efecto jurídico del cambio. La aplicación describe y la persona decide;
   el aviso viaja con el cambio y se enseña antes de confirmar.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from opofuente.application.change_models import (
    AffectedView,
    ChangeOutcome,
    ChangeSetView,
    DerivedArtifactView,
    SectionChangeView,
)
from opofuente.application.ports import ChangeRecorder, Clock
from opofuente.domain.changes import (
    LEGAL_EFFECT_NOTE,
    ArtifactKind,
    ArtifactReview,
    ChangeStatus,
    EdgeSource,
    EdgeTarget,
    SectionChange,
    SectionChangeKind,
    assert_can_confirm,
    assert_can_review,
    assess_change,
)
from opofuente.domain.errors import InvariantViolationError, NotFoundError, UnsupportedError
from opofuente.infrastructure.change_repository import SqlAlchemyChangeRepository
from opofuente.infrastructure.document_repository import SqlAlchemyDocumentRepository

#: Identificador del generador de resúmenes. No hay modelo: es composición extractiva, como en S09.
SUMMARY_GENERATOR = "extractive-summary-v1"

#: Cuánto texto de cada sección entra en un resumen y cuántas secciones como mucho.
SUMMARY_CHARS_PER_SECTION = 600
SUMMARY_MAX_SECTIONS = 40


class ChangeService(ChangeRecorder):
    def __init__(
        self,
        *,
        changes: SqlAlchemyChangeRepository,
        documents: SqlAlchemyDocumentRepository,
        clock: Clock,
    ) -> None:
        self._changes = changes
        self._documents = documents
        self._clock = clock

    # ------------------------------------------------------------------ proponer un cambio

    def record_version_change(
        self, *, document_id: str, new_version_id: str
    ) -> ChangeSetView | None:
        """Propone el cambio de una versión nueva sobre la aceptada anterior. No aplica nada.

        Devuelve `None` cuando no hay nada que proponer: la versión nueva no sustituye a ninguna
        aceptada (es la primera del documento) o ya hay una propuesta pendiente para ella.
        """
        anterior = self._accepted_before(document_id, new_version_id)
        if anterior is None:
            return None
        if self._changes.proposed_for_version(new_version_id) is not None:
            return None
        diff = self._documents.document_diff(
            document_id, from_version_id=anterior, to_version_id=new_version_id
        )
        if diff is None:
            return None

        secciones = tuple(
            SectionChange(label=seccion.label, kind=SectionChangeKind(seccion.kind))
            for seccion in diff.sections
        )
        valoracion = assess_change(
            sections=secciones, dependents=self._changes.dependents_by_section(anterior)
        )
        return self._changes.create_change_set(
            document_id=document_id,
            previous_version_id=anterior,
            new_version_id=new_version_id,
            sections=tuple(
                SectionChangeView(
                    label=seccion.label, kind=seccion.kind, left=seccion.left, right=seccion.right
                )
                for seccion in diff.sections
            ),
            affected=tuple(
                AffectedView(
                    kind=item.kind.value,
                    id=item.id,
                    title=item.title,
                    sections=item.sections,
                    reason=item.reason,
                    reviewable=item.reviewable,
                )
                for item in valoracion.affected
            ),
            counters={
                "changed": valoracion.changed,
                "added": valoracion.added,
                "removed": valoracion.removed,
                "unchanged": valoracion.unchanged,
            },
            effect_note=valoracion.note,
            notes=valoracion.extra_notes,
            now=self._clock.now(),
        )

    def _accepted_before(self, document_id: str, new_version_id: str) -> str | None:
        """La versión aceptada del documento que la nueva viene a sustituir, si la hay."""
        detalle = self._documents.get_document(document_id)
        if detalle is None:
            return None
        activa = next(
            (version for version in detalle.versions if version.status == "accepted"), None
        )
        if activa is None or activa.id == new_version_id:
            return None
        return activa.id

    # ------------------------------------------------------------------ leer

    def change_sets(
        self, *, document_id: str | None = None, status: str | None = None, limit: int = 100
    ) -> tuple[ChangeSetView, ...]:
        return self._changes.change_sets(document_id=document_id, status=status, limit=limit)

    def change_set(self, change_id: str) -> ChangeSetView:
        return self._require(change_id)

    def affected(self, change_id: str) -> ChangeSetView:
        """Lo que se invalidaría al confirmar: es la simulación del cambio, sin aplicar nada."""
        return self._require(change_id)

    # ------------------------------------------------------------------ decidir

    def confirm(self, change_id: str, *, actor: str = "local") -> ChangeOutcome:
        """Confirma el cambio: acepta la versión nueva, sustituye la anterior y marca derivados.

        Las tres cosas van juntas y en ese orden, y quedan auditadas por la biblioteca (aceptación
        y sustitución) y por el propio cambio. La versión anterior **no** se borra: queda
        `superseded` y accesible como histórica.
        """
        vista = self._require(change_id)
        assert_can_confirm(ChangeStatus(vista.status))
        momento = self._clock.now()

        aceptada = self._documents.accept_version(vista.new_version_id, now=momento, actor=actor)
        if not aceptada.applied:
            return ChangeOutcome(
                change=vista,
                applied=False,
                reason=aceptada.reason or "la versión nueva no se pudo aceptar",
            )
        sustitucion = self._documents.mark_supersedes(
            vista.new_version_id, superseded_id=vista.previous_version_id, now=momento, actor=actor
        )
        if not sustitucion.applied:
            return ChangeOutcome(
                change=vista,
                applied=False,
                reason=sustitucion.reason or "la versión anterior no se pudo sustituir",
            )

        motivo = (
            f"el material del que sale ha cambiado: «{vista.document_title}» "
            f"(«{vista.previous_version_label or vista.previous_version_id}» → "
            f"«{vista.new_version_label or vista.new_version_id}»)"
        )
        marcados = self._changes.mark_artifacts_for_review(
            [
                item.id
                for item in vista.affected
                if item.reviewable and item.kind == EdgeTarget.DERIVED_ARTIFACT.value
            ],
            reason=motivo,
            now=momento,
        )
        confirmado = self._changes.set_status(
            change_id, status=ChangeStatus.CONFIRMED.value, now=momento, actor=actor
        )
        return ChangeOutcome(
            change=confirmado or vista,
            applied=True,
            marked=marcados,
            superseded_version_id=vista.previous_version_id,
        )

    def discard(self, change_id: str, *, actor: str = "local") -> ChangeOutcome:
        """Descarta la propuesta. La versión nueva sigue ahí, sin aceptar y sin invalidar nada."""
        vista = self._require(change_id)
        assert_can_confirm(ChangeStatus(vista.status))
        descartado = self._changes.set_status(
            change_id, status=ChangeStatus.DISCARDED.value, now=self._clock.now(), actor=actor
        )
        return ChangeOutcome(
            change=descartado or vista,
            applied=True,
            reason="propuesta descartada: nada se ha invalidado",
        )

    # ------------------------------------------------------------------ derivados

    def create_summary(
        self, *, document_version_id: str, section_ids: Sequence[str], title: str | None
    ) -> DerivedArtifactView:
        """Resumen **extractivo** de unas secciones: texto del material, con su cita, sin modelo.

        No redacta nada: junta los fragmentos de las secciones elegidas con su cita y su página. Es
        un derivado de verdad —tiene entradas exactas y se invalida si cambian—, así que sirve para
        lo que S11 necesita demostrar sin depender de un proveedor de lenguaje.
        """
        if not section_ids:
            raise InvariantViolationError(
                "un resumen necesita al menos una sección: sin material no hay nada que resumir"
            )
        detalle = self._documents.version_detail(document_version_id)
        if detalle is None:
            raise NotFoundError("versión del documento", document_version_id)
        secciones = self._documents.list_sections(document_version_id)
        elegidas = [seccion for seccion in secciones if seccion.id in set(section_ids)]
        if not elegidas:
            raise NotFoundError("secciones de la versión", ", ".join(section_ids))
        if len(elegidas) > SUMMARY_MAX_SECTIONS:
            raise UnsupportedError(
                f"un resumen admite {SUMMARY_MAX_SECTIONS} secciones como mucho: se han pedido "
                f"{len(elegidas)}"
            )
        fragmentos = [
            evidencia
            for evidencia in self._documents.list_evidence(document_version_id)
            if evidencia.section_id in {seccion.id for seccion in elegidas}
        ]
        if not fragmentos:
            raise UnsupportedError(
                "esas secciones no tienen texto extraído: no hay nada que resumir sin inventarlo"
            )
        lineas = [
            f"- {evidencia.citation_label or 'sin cita'}: "
            f"{' '.join(evidencia.text.split())[:SUMMARY_CHARS_PER_SECTION]}"
            for evidencia in fragmentos
        ]
        momento = self._clock.now()
        creado = self._changes.create_artifact(
            kind=ArtifactKind.SUMMARY.value,
            title=title or f"Resumen de {detalle.document_title}",
            content="\n".join(lineas),
            document_version_id=document_version_id,
            generator=SUMMARY_GENERATOR,
            prompt_template_version=SUMMARY_GENERATOR,
            model=None,
            now=momento,
        )
        if creado is None:
            raise NotFoundError("versión del documento", document_version_id)
        self._changes.add_edges(
            from_type=EdgeSource.EVIDENCE_SPAN,
            from_ids=[evidencia.id for evidencia in fragmentos],
            to_type=EdgeTarget.DERIVED_ARTIFACT,
            to_id=creado.id,
            now=momento,
            role="input",
        )
        return replace(creado, sections=self._changes.artifact_sections(creado.id))

    def artifacts(
        self,
        *,
        document_version_id: str | None = None,
        needs_review: bool | None = None,
        limit: int = 200,
    ) -> tuple[DerivedArtifactView, ...]:
        return self._changes.artifacts(
            document_version_id=document_version_id, needs_review=needs_review, limit=limit
        )

    def artifact(self, artifact_id: str) -> DerivedArtifactView:
        vista = self._changes.artifact(artifact_id)
        if vista is None:
            raise NotFoundError("derivado", artifact_id)
        return vista

    def review_artifact(
        self, artifact_id: str, *, resolution: str, actor: str = "local"
    ) -> DerivedArtifactView:
        """Cierra la revisión: sigue valiendo (`reviewed`) o se aparta (`discarded`)."""
        vista = self.artifact(artifact_id)
        assert_can_review(needs_review=vista.needs_review)
        if resolution not in (ArtifactReview.REVIEWED.value, ArtifactReview.DISCARDED.value):
            raise InvariantViolationError(
                f"«{resolution}» no es una forma de cerrar una revisión: "
                f"{ArtifactReview.REVIEWED.value} o {ArtifactReview.DISCARDED.value}"
            )
        resuelto = self._changes.resolve_artifact(
            artifact_id, resolution=resolution, now=self._clock.now()
        )
        if resuelto is None:  # pragma: no cover - acaba de leerse
            raise NotFoundError("derivado", artifact_id)
        return resuelto

    # ------------------------------------------------------------------ ayudas

    def _require(self, change_id: str) -> ChangeSetView:
        vista = self._changes.change_set(change_id)
        if vista is None:
            raise NotFoundError("cambio", change_id)
        return vista


def change_summary(vista: ChangeSetView) -> str:
    """Texto corto de un cambio, para la interfaz y los informes."""
    if not vista.affected:
        return f"sin cambios o sin derivados afectados ({vista.status})"
    revisables = sum(1 for item in vista.affected if item.reviewable)
    return (
        f"{len(vista.affected)} afectado(s), {revisables} por revisar · {vista.status}"
        if revisables
        else f"{len(vista.affected)} afectado(s), ninguno revisable · {vista.status}"
    )


__all__ = [
    "LEGAL_EFFECT_NOTE",
    "SUMMARY_GENERATOR",
    "ChangeService",
    "change_summary",
]
