"""Caso de uso: errores, repaso y dominio (S10).

Lo que decide este servicio, y no el repositorio:

1. **cuándo vuelve a tocar** (`06_QUESTIONS` §8): el intervalo lo calcula el dominio y aquí se
   convierte en una fecha, se guarda en el elemento de repaso y se escribe en el historial con su
   motivo. Nada cambia de fecha sin dejar rastro;
2. **qué es un fallo**: un fallo de verdad (una respuesta equivocada) entra en el repaso; un blanco
   **no** entra solo, porque no demuestra que no se sepa y convertiría un examen a medias en veinte
   repasos que nadie ha pedido. Se puede clasificar a mano como error si se quiere;
3. **qué se puede decir del dominio**: con menos intentos recientes que el mínimo, «evidencia
   insuficiente» y el recuento; nunca un porcentaje que parezca una medición.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

from opofuente.application.ports import Clock
from opofuente.application.review_models import (
    ConceptGroupView,
    ConceptSummaryView,
    DueItemView,
    ErrorDetailView,
    ErrorView,
    ReviewEventView,
    ReviewItemView,
    ReviewQueueView,
    ReviewStatsView,
)
from opofuente.domain.errors import InvariantViolationError, NotFoundError
from opofuente.domain.review import (
    AttemptStat,
    ErrorCause,
    Mastery,
    ReviewEventKind,
    ReviewOutcome,
    mastery_from,
    next_due_at,
    review_outcome_for,
    schedule,
)
from opofuente.domain.study import AttemptOutcome, Confidence
from opofuente.infrastructure.review_repository import (
    DEFAULT_QUEUE_LIMIT,
    SqlAlchemyReviewRepository,
    group_summary,
)

#: Cuántos días se puede aplazar un repaso de una vez. Un año sería «no volver a verlo», que es otra
#: decisión (resolver el error, no aplazarlo).
MAX_SNOOZE_DAYS = 90


class ReviewService:
    def __init__(self, *, reviews: SqlAlchemyReviewRepository, clock: Clock) -> None:
        self._reviews = reviews
        self._clock = clock

    # ------------------------------------------------------------------ desde una sesión

    def record_attempt(
        self,
        *,
        attempt_id: str,
        question_version_id: str,
        opposition_id: str,
        outcome: AttemptOutcome,
        confidence: Confidence | None = None,
        now: datetime | None = None,
    ) -> ReviewItemView | None:
        """Reprograma el repaso de una pregunta según lo que ha pasado en un intento.

        Devuelve `None` cuando el desenlace no dice nada del saber (un blanco, una pregunta anulada
        o conflictiva): en ese caso **no** se crea ni se toca ningún repaso.
        """
        resultado = review_outcome_for(outcome)
        if resultado is None:
            return None
        momento = now if now is not None else self._clock.now()
        item = self._reviews.active_item(question_version_id)
        if item is None:
            plan = schedule(
                outcome=resultado, previous_interval_days=0, repetitions=0, confidence=confidence
            )
            due = next_due_at(momento, plan.interval_days)
            guardado = self._reviews.save_item(
                review_id=None,
                question_version_id=question_version_id,
                opposition_id=opposition_id,
                learning_error_id=None,
                due_at=due,
                interval_days=plan.interval_days,
                repetitions=plan.repetitions,
                lapses=0 if resultado is ReviewOutcome.CORRECT else 1,
                reason=plan.reason,
                reviewed_at=None,
                now=momento,
            )
            self._reviews.record_event(
                review_item_id=guardado.id,
                kind=ReviewEventKind.CREATED,
                outcome=resultado.value,
                confidence=None if confidence is None else confidence.value,
                cause=None,
                note=None,
                previous_due_at=None,
                due_at=due,
                previous_interval_days=None,
                interval_days=plan.interval_days,
                repetitions=plan.repetitions,
                reason=plan.reason,
                now=momento,
            )
            return guardado

        return self._reschedule(
            item,
            outcome=resultado,
            confidence=confidence,
            kind=ReviewEventKind.ATTEMPT,
            cause=None,
            note=None,
            now=momento,
        )

    # ------------------------------------------------------------------ la cola de hoy

    def queue(
        self, *, opposition_id: str | None, limit: int = DEFAULT_QUEUE_LIMIT
    ) -> ReviewQueueView:
        """Lo que toca hoy: la cola, sus cifras, los conceptos y lo que no se puede decir."""
        momento = self._clock.now()
        items = self._reviews.due(opposition_id=opposition_id, now=momento, limit=limit)
        cifras = self._reviews.stats(opposition_id=opposition_id, now=momento)
        conceptos = self._reviews.concepts(opposition_id=opposition_id, now=momento)
        notas: list[str] = []
        if cifras.active == 0:
            notas.append(
                "No hay ningún repaso todavía: se crean solos al fallar una pregunta en una sesión."
            )
        elif not items:
            proximo = cifras.next_due_at
            notas.append(
                "No hay nada vencido."
                if proximo is None
                else f"No hay nada vencido: lo siguiente toca el {proximo:%Y-%m-%d}."
            )
        return ReviewQueueView(
            items=items,
            stats=cifras,
            concepts=conceptos,
            notes=tuple(notas),
        )

    def due_for_session(self, *, opposition_id: str, limit: int) -> tuple[DueItemView, ...]:
        """Las preguntas vencidas, para montar una sesión de repaso con ellas."""
        return self._reviews.due(opposition_id=opposition_id, now=self._clock.now(), limit=limit)

    def complete(
        self,
        review_id: str,
        *,
        outcome: ReviewOutcome,
        confidence: Confidence | None = None,
        cause: ErrorCause | None = None,
        note: str | None = None,
    ) -> ReviewItemView:
        """Declara el resultado de un repaso hecho fuera de una sesión y reprograma.

        Es el camino para lo que se repasa de viva voz o en papel: la persona dice qué tal le fue y
        el intervalo se recalcula igual que si hubiera contestado aquí. Queda registrado que el
        desenlace es **declarado**, no medido.
        """
        item = self._require(review_id)
        return self._reschedule(
            item,
            outcome=outcome,
            confidence=confidence,
            kind=ReviewEventKind.REVIEWED,
            cause=cause,
            note=note,
            now=self._clock.now(),
        )

    def snooze(self, review_id: str, *, days: int) -> ReviewItemView:
        """Aplaza un repaso sin contarlo como repasado: el historial guarda que se aplazó."""
        if days < 1 or days > MAX_SNOOZE_DAYS:
            raise InvariantViolationError(
                f"un aplazamiento va de 1 a {MAX_SNOOZE_DAYS} días: «{days}» no es un aplazamiento"
            )
        item = self._require(review_id)
        momento = self._clock.now()
        due = momento + timedelta(days=days)
        motivo = f"aplazado a mano {days} día(s), sin contar como repaso"
        guardado = self._reviews.save_item(
            review_id=item.id,
            question_version_id=item.question_version_id,
            opposition_id=item.opposition_id,
            learning_error_id=item.learning_error_id,
            due_at=due,
            interval_days=item.interval_days,
            repetitions=item.repetitions,
            lapses=item.lapses,
            reason=motivo,
            reviewed_at=None,
            now=momento,
        )
        self._reviews.record_event(
            review_item_id=guardado.id,
            kind=ReviewEventKind.SNOOZED,
            outcome=None,
            confidence=None,
            cause=None,
            note=None,
            previous_due_at=item.due_at,
            due_at=due,
            previous_interval_days=item.interval_days,
            interval_days=item.interval_days,
            repetitions=item.repetitions,
            reason=motivo,
            now=momento,
        )
        return guardado

    def item(self, review_id: str) -> ReviewItemView:
        return self._require(review_id)

    def history(self, review_id: str) -> tuple[ReviewEventView, ...]:
        """El historial de un repaso, del cambio más reciente al más antiguo."""
        self._require(review_id)
        return self._reviews.events(review_id)

    # ------------------------------------------------------------------ errores

    def classify(
        self,
        attempt_id: str,
        *,
        cause: ErrorCause,
        concept_label: str | None = None,
        curriculum_node_id: str | None = None,
        note: str | None = None,
    ) -> ErrorView:
        """Declara por qué se ha fallado.

        La causa es obligatoria; el concepto **no**: el modelo de datos lo admite vacío y forzarlo
        obligaría a inventar una etiqueta para poder anotar un fallo. Un error sin concepto aparece
        agrupado como «sin concepto declarado», y se puede poner después (volver a clasificarlo
        actualiza el mismo error en lugar de crear otro).
        """
        momento = self._clock.now()
        guardado = self._reviews.save_error(
            attempt_id=attempt_id,
            cause=cause.value,
            concept_label=concept_label,
            curriculum_node_id=curriculum_node_id,
            note=note,
            now=momento,
        )
        if guardado is None:
            raise NotFoundError("intento", attempt_id)
        return guardado

    def error(self, error_id: str) -> ErrorDetailView:
        detalle = self._reviews.error(error_id)
        if detalle is None:
            raise NotFoundError("error", error_id)
        return detalle

    def resolve_error(self, error_id: str, *, note: str | None = None) -> ErrorView:
        """Marca un error como resuelto. El repaso **sigue**: resolver el error no es saberlo."""
        resuelto = self._reviews.resolve_error(error_id, note=note, now=self._clock.now())
        if resuelto is None:
            raise NotFoundError("error", error_id)
        return resuelto

    def reopen_error(self, error_id: str) -> ErrorView:
        reabierto = self._reviews.reopen_error(error_id, now=self._clock.now())
        if reabierto is None:
            raise NotFoundError("error", error_id)
        return reabierto

    def concepts(self, *, opposition_id: str | None) -> ConceptGroupView:
        return group_summary(
            self._reviews.concepts(opposition_id=opposition_id, now=self._clock.now())
        )

    # ------------------------------------------------------------------ dominio

    def mastery(self, node_ids: Sequence[str]) -> dict[str, Mastery]:
        """El dominio estimado de cada nodo, con la misma regla para todos."""
        momento = self._clock.now()
        intentos = self._reviews.node_attempts(tuple(node_ids), now=momento)
        return {
            node_id: mastery_from(
                tuple(
                    AttemptStat(correct=correcto, answered_at=momento_intento)
                    for correcto, momento_intento in intentos.get(node_id, ())
                ),
                now=momento,
            )
            for node_id in node_ids
        }

    # ------------------------------------------------------------------ ayudas

    def _reschedule(
        self,
        item: ReviewItemView,
        *,
        outcome: ReviewOutcome,
        confidence: Confidence | None,
        kind: ReviewEventKind,
        cause: ErrorCause | None,
        note: str | None,
        now: datetime,
    ) -> ReviewItemView:
        plan = schedule(
            outcome=outcome,
            previous_interval_days=item.interval_days,
            repetitions=item.repetitions,
            confidence=confidence,
        )
        due = next_due_at(now, plan.interval_days)
        guardado = self._reviews.save_item(
            review_id=item.id,
            question_version_id=item.question_version_id,
            opposition_id=item.opposition_id,
            learning_error_id=item.learning_error_id,
            due_at=due,
            interval_days=plan.interval_days,
            repetitions=plan.repetitions,
            lapses=item.lapses + (1 if outcome is ReviewOutcome.WRONG else 0),
            reason=plan.reason,
            reviewed_at=now,
            now=now,
        )
        self._reviews.record_event(
            review_item_id=guardado.id,
            kind=kind,
            outcome=outcome.value,
            confidence=None if confidence is None else confidence.value,
            cause=None if cause is None else cause.value,
            note=note,
            previous_due_at=item.due_at,
            due_at=due,
            previous_interval_days=item.interval_days,
            interval_days=plan.interval_days,
            repetitions=plan.repetitions,
            reason=plan.reason,
            now=now,
        )
        return guardado

    def _require(self, review_id: str) -> ReviewItemView:
        item = self._reviews.item(review_id)
        if item is None:
            raise NotFoundError("repaso", review_id)
        return item


def review_summary(stats: ReviewStatsView) -> str:
    """Texto corto de la cola, para la interfaz y los informes."""
    if stats.active == 0:
        return "sin repasos"
    if stats.due == 0:
        return f"{stats.active} en cola, ninguno vencido"
    return f"{stats.due} de {stats.active} vencidos"


def concepts_without_node(groups: Sequence[ConceptSummaryView]) -> tuple[str, ...]:
    """Los conceptos que no cuelgan de ningún nodo del programa: se dicen, no se esconden."""
    return tuple(grupo.label for grupo in groups if grupo.node_id is None)


__all__ = [
    "MAX_SNOOZE_DAYS",
    "ReviewService",
    "concepts_without_node",
    "review_summary",
]
