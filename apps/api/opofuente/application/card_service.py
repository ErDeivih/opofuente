"""El servicio de las tarjetas: de un hecho a una tarjeta (M3).

**Por que esta separado del repositorio**: aqui se decide que hecho se
convierte en tarjeta y que respuesta se le da. Las dos decisiones son del
dominio (`tarjeta_estructural` y `repasar`), y este servicio las llama en orden.

**La regla del hito**: **una tarjeta mal formada es peor que un hueco**. Si el
hecho no encaja en una plantilla, no se convierte a la fuerza.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from opofuente.domain.cola_del_dia import EntradaDeLaCola, cola_del_dia
from opofuente.domain.repaso import EstadoDeRepaso, Respuesta, repasar
from opofuente.domain.tarjetas import tarjeta_estructural
from opofuente.infrastructure.card_repository import (
    CardView,
    SqlAlchemyCardRepository,
)


@dataclass(frozen=True, slots=True)
class ResultadoDeGeneracion:
    """Lo que salio de una pasada: las tarjetas y los hechos que se miraron."""

    tarjetas: int
    hechos: int

    @property
    def fuera(self) -> int:
        """Los hechos que **no** se convirtieron en tarjeta."""
        return self.hechos - self.tarjetas


class CardService:
    """Genera tarjetas, sirve la cola y avanza una tarjeta al responderla."""

    def __init__(self, cards: SqlAlchemyCardRepository) -> None:
        self._cards = cards

    def generar(self, *, limite: int = 1000) -> ResultadoDeGeneracion:
        """Convierte en tarjeta **los hechos que encajan en una plantilla**.

        **No usa el modelo**: los quince que salen salen sin gastar un centimo.
        Los demas necesitan modelo, y eso es otra accion que se pide aparte.
        """
        hechos = self._cards.facts(limit=limite)
        ahora = datetime.now(UTC)
        creadas = 0
        for fact_id, texto in hechos:
            tarjeta = tarjeta_estructural(texto)
            if tarjeta is None:
                continue
            guardada = self._cards.add(
                card_id=str(uuid.uuid4()),
                topic_fact_id=fact_id,
                front=tarjeta.anverso,
                back=tarjeta.reverso,
                citation=texto,
                origin="structural",
                now=ahora,
            )
            if guardada is not None:
                creadas += 1
        return ResultadoDeGeneracion(tarjetas=creadas, hechos=len(hechos))

    def cola(
        self,
        *,
        ahora: datetime | None = None,
        tope: int = 60,
    ) -> tuple[EntradaDeLaCola, ...]:
        """Lo que hay que repasar hoy: las tarjetas vencidas, con su tope.

        **Los fallos van vacios todavia**: mezclarlos necesita la tabla de repasos
        de las preguntas, que no es de este hito. Cuando exista, se pasa aqui y la
        mezcla ya esta hecha en `cola_del_dia`.
        """
        dia = ahora or datetime.now(UTC)
        vencidas = self._cards.due(dia=dia, limit=200)
        return cola_del_dia(
            tarjetas=[tarjeta.id for tarjeta in vencidas],
            fallos=[],
            tope=tope,
        )

    def vencen(self, *, ahora: datetime | None = None) -> int:
        """**Cuántas vencen**, para que la cola enseñe el número antes."""
        return self._cards.pending(dia=ahora or datetime.now(UTC))

    def responder(
        self,
        card_id: str,
        respuesta: Respuesta,
        *,
        ahora: datetime | None = None,
    ) -> bool:
        """Aplica SM-2 a una tarjeta y la reprograma. `False` si no existe.

        **El estado viejo sale de la fila y el nuevo lo calcula el dominio**: aqui
        no se decide cuanto crece el intervalo, solo se escribe.
        """
        dia = ahora or datetime.now(UTC)
        tarjetas = self._cards.due(dia=dia, limit=200)
        actual = next((t for t in tarjetas if t.id == card_id), None)
        if actual is None:
            return False
        estado = repasar(
            EstadoDeRepaso(
                factor=actual.ease,
                intervalo_dias=actual.interval_days,
                aciertos_seguidos=actual.repetitions,
            ),
            respuesta,
        )
        return self._cards.reschedule(
            card_id=card_id,
            ease=estado.factor,
            interval_days=estado.intervalo_dias,
            repetitions=estado.aciertos_seguidos,
            due_at=dia + timedelta(days=max(estado.intervalo_dias, 0)),
            now=dia,
        )

    def tarjetas_de(self, topic_fact_id: str) -> Sequence[CardView]:
        """Las tarjetas de un hecho: **lo que el fallo de una prueba adelanta**."""
        return self._cards.of_fact(topic_fact_id)
