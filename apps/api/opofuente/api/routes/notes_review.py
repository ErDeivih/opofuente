"""La revisión de los apuntes: la tabla de los temas, la ficha y la decisión (F24, §4.3).

Es la pantalla que faltaba del punto (4) del objetivo. Lo que estas rutas garantizan:

- **se ven los temas con su estado** y, en los que esperan una decisión, **lo que se sabe sin
  medir**; la cifra de la puerta se mide al abrir la ficha, que es donde se decide, y la fila dice
  dónde está (razón `sin_medida`) en lugar de enseñar un cero;
- **un borrador se lee entero dentro del panel**, apartado a apartado —**de seis en seis**, porque
  los cuerpos de todos eran el 92 % de la respuesta—, con el mismo texto que sirve la zona del
  alumno;
- **se decide por la ruta auditada**: `POST /notes-review/{codigo}/decision` escribe la decisión y
  su evento en la misma transacción, con el actor en el cuerpo o en la cabecera
  `X-OpoFuente-Actor` como el resto de escrituras del panel;
- **aprobar publica** cuando las dos puertas del §2.3 pasan (archiva la versión, por el camino de
  siempre) y, cuando no pasan, la respuesta dice **qué puerta** lo frena. El listón no se toca.

Un tema que no existe es un 404; una decisión sin el motivo que exige es un 422 con su campo.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Path, Query

from opofuente.api.deps import NotesReviewServiceDep
from opofuente.api.error_responses import RESOURCE_ERRORS, WRITE_ERRORS
from opofuente.api.notes_review_schemas import (
    NotesReviewChecksSchema,
    NotesReviewCountersSchema,
    NotesReviewDecisionRequestSchema,
    NotesReviewDecisionResultSchema,
    NotesReviewDecisionSchema,
    NotesReviewFileSchema,
    NotesReviewListSchema,
    NotesReviewReasonSchema,
    NotesReviewSectionSchema,
    NotesReviewTopicSchema,
    NotesReviewVersionSchema,
    ReviewOrderName,
)
from opofuente.application.notes_report_service import ACTOR_PROPIETARIO
from opofuente.application.notes_review_models import (
    FichaDeRevision,
    ResultadoDeDecision,
    RevisionDeApuntes,
    SeccionDeRevision,
    TemaEnRevision,
)
from opofuente.domain.notes_review import ReviewDecision
from opofuente.infrastructure.notes_review_repository import ContadoresDeRevision

router = APIRouter(tags=["panel"])

#: La cabecera con la que el panel dice quién escribe, igual que en el resto del panel.
ACTOR_HEADER = "X-OpoFuente-Actor"


def _actor(*, declared: str | None, header: str | None) -> str:
    """Quién decide: lo que dice el cuerpo, si no la cabecera y, si no, la persona local.

    Un actor en blanco se ignora: en la auditoría es peor un actor vacío que el de por defecto.
    """
    for candidato in (declared, header):
        if candidato is not None and candidato.strip() != "":
            return candidato.strip()
    return ACTOR_PROPIETARIO


def _contadores(contadores: ContadoresDeRevision) -> NotesReviewCountersSchema:
    return NotesReviewCountersSchema(
        topics_total=contadores.topics_total,
        with_notes=contadores.with_notes,
        published=contadores.published,
        draft=contadores.draft,
        without_notes=contadores.without_notes,
        approved=contadores.approved,
        rejected=contadores.rejected,
        pending_decision=contadores.pending_decision,
    )


def _tema(tema: TemaEnRevision) -> NotesReviewTopicSchema:
    return NotesReviewTopicSchema(
        code=tema.code,
        title=tema.title,
        block_code=tema.block_code,
        block_title=tema.block_title,
        state=tema.state.value,
        sections_written=tema.sections_written,
        facts=tema.facts,
        checks=NotesReviewChecksSchema(
            total=tema.checks.total,
            covered=tema.checks.covered,
            gaps=tema.checks.gaps,
            doubtful=tema.checks.doubtful,
            conflicts=tema.checks.conflicts,
        ),
        incidents_open=tema.incidents_open,
        incidents_by_category={
            categoria.value: cuantas for categoria, cuantas in tema.incidents_by_category
        },
        version=(
            None
            if tema.version is None
            else NotesReviewVersionSchema(id=tema.version.id, built_at=tema.version.built_at)
        ),
        review=(
            None
            if tema.review is None
            else NotesReviewDecisionSchema(
                decision=tema.review.decision.value,
                note=tema.review.note,
                actor=tema.review.actor,
                reviewed_at=tema.review.reviewed_at,
            )
        ),
        reasons=[
            NotesReviewReasonSchema(code=razon.code.value, text=razon.text, figure=razon.figure)
            for razon in tema.razones
        ],
        measured=tema.medida,
        coverage=tema.cobertura,
        coverage_all_keys=tema.cobertura_todas_las_claves,
    )


def _seccion(apartado: SeccionDeRevision) -> NotesReviewSectionSchema:
    return NotesReviewSectionSchema(
        key=apartado.key,
        title=apartado.title,
        epigraph_code=apartado.epigraph_code,
        anchor=apartado.anchor,
        position=apartado.position,
        body_markdown=apartado.body_markdown,
        words=apartado.words,
        facts_total=apartado.facts_total,
        covered=apartado.covered,
        gaps=apartado.gaps,
        doubtful=apartado.doubtful,
        conflicts=apartado.conflicts,
        needs_review_reason=apartado.needs_review_reason,
        worst=apartado.peor,
    )


def _lista(vista: RevisionDeApuntes) -> NotesReviewListSchema:
    return NotesReviewListSchema(
        counters=_contadores(vista.counters),
        topics=[_tema(tema) for tema in vista.topics],
    )


@router.get(
    "/notes-review",
    response_model=NotesReviewListSchema,
    responses=RESOURCE_ERRORS,
    summary="Los temas con su estado, sus puertas y el motivo de los que están en borrador",
)
def list_notes_review(service: NotesReviewServiceDep) -> NotesReviewListSchema:
    """La tabla del panel: los temas del programa activo, en orden, con lo que se sabe **sin
    medir**.

    **No mide** ningún tema: lee el estado, las cifras guardadas y la decisión escrita con cinco
    consultas agregadas (0,03 s medidos sobre la copia del propietario, 17-oct-2026). Medir los dos
    borradores costaba 3,7 s de los 5,37 s de la pantalla, y la cifra de la puerta **no se hereda**:
    se mide al abrir la ficha del tema, que es donde se decide, y la fila lo dice con la razón
    `sin_medida` en vez de enseñar un cero que parecería un suspenso.
    """
    return _lista(service.revisar())


@router.get(
    "/notes-review/summary",
    response_model=NotesReviewCountersSchema,
    responses=RESOURCE_ERRORS,
    summary="Cuántos borradores esperan una decisión (el número del menú, sin medir nada)",
)
def notes_review_summary(service: NotesReviewServiceDep) -> NotesReviewCountersSchema:
    """Los contadores del menú. No mide la cobertura de nada: se pide en todas las pantallas."""
    return _contadores(service.contadores_del_menu())


@router.get(
    "/notes-review/{codigo}",
    response_model=NotesReviewFileSchema,
    responses=RESOURCE_ERRORS,
    summary="Una página de la ficha: sus apartados, como se leerán en la zona del alumno",
)
def notes_review_file(
    service: NotesReviewServiceDep,
    codigo: str = Path(
        description="Código legible del tema, como `I.4` (también se acepta `I-4`).",
        examples=["I.4"],
    ),
    pagina: Annotated[
        int,
        Query(
            ge=1,
            description=(
                "Qué hoja de apartados se sirve, empezando por la 1. Una hoja son seis apartados: "
                "los cuerpos de todos a la vez eran el 92 % de la respuesta y el navegador tardaba "
                "en pintar el primero."
            ),
        ),
    ] = 1,
    orden: Annotated[
        ReviewOrderName,
        Query(
            description="`lectura` es el orden del tema; `peores`, lo que queda sin resolver antes."
        ),
    ] = "lectura",
) -> NotesReviewFileSchema:
    """Una **página** de un tema, apartado a apartado, con su texto, su forma y lo comprobado.

    Un tema sin apuntes escritos sale con su estado (`none`) y sin apartados: no es un error que un
    tema no tenga texto, y devolver un 404 obligaría a la pantalla a distinguir «no existe» de «no
    está escrito», que es justo lo que el estado contesta.

    El orden lo decide el servidor porque la página se corta aquí: «los peores primero» ordena los
    apartados del **tema**, no los de la hoja que se acaba de enviar.
    """
    ficha: FichaDeRevision = service.ficha(codigo, page=pagina, order=orden)
    return NotesReviewFileSchema(
        topic=_tema(ficha.topic),
        sections=[_seccion(apartado) for apartado in ficha.sections],
        sections_total=ficha.sections_total,
        page=ficha.page,
        pages=ficha.pages,
        page_size=ficha.page_size,
    )


@router.post(
    "/notes-review/{codigo}/decision",
    response_model=NotesReviewDecisionResultSchema,
    responses=WRITE_ERRORS,
    summary="Aprueba o rechaza los apuntes de un tema, con su nota y su evento de auditoría",
)
def decide_notes_review(
    service: NotesReviewServiceDep,
    body: NotesReviewDecisionRequestSchema,
    codigo: str = Path(description="Código legible del tema, como `I.4`.", examples=["I.4"]),
    actor: Annotated[str | None, Header(alias=ACTOR_HEADER)] = None,
) -> NotesReviewDecisionResultSchema:
    """Aprueba (y publica, si las puertas pasan) o rechaza el texto de un tema.

    Aprobar **no salta el listón**: si la cobertura del §2.3 no llega, el tema queda aprobado y sin
    publicar, y `blocked_by` dice qué puerta lo frena con su cifra en el motivo. Rechazar exige
    motivo, y una nota de más de una línea se recorta a una.
    """
    resultado: ResultadoDeDecision = service.decidir(
        codigo,
        decision=ReviewDecision(body.decision),
        note=body.note,
        actor=_actor(declared=body.actor, header=actor),
    )
    return NotesReviewDecisionResultSchema(
        topic=_tema(resultado.topic),
        published=resultado.published,
        version_created=resultado.version_created,
        blocked_by=resultado.blocked_by,
    )
