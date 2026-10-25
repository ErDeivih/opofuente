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

from opofuente.application.review_models import DueItemView
from opofuente.domain.cola_del_dia import TipoDeEntrada, cola_del_dia
from opofuente.domain.errors import NotFoundError
from opofuente.domain.repaso import EstadoDeRepaso, Respuesta, repasar
from opofuente.domain.tarjetas import tarjeta_estructural
from opofuente.infrastructure.card_repository import (
    CardView,
    SqlAlchemyCardRepository,
)
from opofuente.infrastructure.review_repository import SqlAlchemyReviewRepository


@dataclass(frozen=True, slots=True)
class ResultadoDeGeneracion:
    """Lo que salio de una pasada: las tarjetas y los hechos que se miraron."""

    tarjetas: int
    hechos: int

    @property
    def fuera(self) -> int:
        """Los hechos que **no** se convirtieron en tarjeta."""
        return self.hechos - self.tarjetas


@dataclass(frozen=True, slots=True)
class CorreccionDeFallo:
    """**La corrección de un fallo de la cola**: si está bien, qué valía y por qué.

    `letras` son las que corrigen —una sola, salvo que la pregunta admita más—, y `explicacion`
    y `cita` llegan **con** la corrección y no antes: antes filtrarían la respuesta.
    """

    correcto: bool
    letras: tuple[str, ...]
    explicacion: str | None
    cita: str | None


class CardService:
    """Genera tarjetas, sirve la cola y avanza una tarjeta al responderla."""

    def __init__(
        self,
        cards: SqlAlchemyCardRepository,
        review: SqlAlchemyReviewRepository | None = None,
    ) -> None:
        self._cards = cards
        # **Opcional a propósito**: sin él la cola sirve solo tarjetas, que es lo que hacía antes
        # de este punto. Con él, entran los fallos vencidos.
        self._review = review

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
    ) -> tuple[CardView, ...]:
        """Las tarjetas que hay que repasar hoy, **ya ordenadas y con el tope**."""
        return self.cola_del_dia(ahora=ahora, tope=tope)[0]

    def cola_del_dia(
        self,
        *,
        ahora: datetime | None = None,
        tope: int = 60,
    ) -> tuple[tuple[CardView, ...], tuple[DueItemView, ...]]:
        """**La cola del día entera**: tarjetas y fallos vencidos, entrelazados y con el tope.

        **El tope es de las dos cosas juntas** (fase «lo que ve el alumno», punto 3): sesenta
        entradas, no sesenta de cada. **Y van alternas**: si primero fueran todas las tarjetas y
        después todos los fallos, quien se cansa nunca llega a los fallos, **que son lo que más
        cuesta**.

        **Los fallos se devuelven enteros** —enunciado y opciones—: contestar uno es lo que lo saca
        de la cola, y el enunciado no está en la tarjeta. **La clave no viaja**: se corrige en el
        servidor.
        """
        dia = ahora or datetime.now(UTC)
        vencidas = self._cards.due(dia=dia, limit=200)
        por_id = {tarjeta.id: tarjeta for tarjeta in vencidas}
        pendientes: tuple[DueItemView, ...] = ()
        if self._review is not None:
            pendientes = self._review.due(opposition_id=None, now=dia, limit=200)
        por_pregunta = {str(item.question_version_id): item for item in pendientes}
        entradas = cola_del_dia(
            tarjetas=[tarjeta.id for tarjeta in vencidas],
            fallos=list(por_pregunta),
            tope=tope,
        )
        return (
            tuple(
                por_id[entrada.id]
                for entrada in entradas
                if entrada.tipo is TipoDeEntrada.TARJETA and entrada.id in por_id
            ),
            tuple(
                por_pregunta[entrada.id]
                for entrada in entradas
                if entrada.tipo is TipoDeEntrada.FALLO and entrada.id in por_pregunta
            ),
        )

    def una(self, card_id: str) -> CardView | None:
        """Una tarjeta por su id. `None` si no existe, para que la ruta diga 404."""
        return self._cards.by_id(card_id)

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

    def corregir_fallo(self, *, question_version_id: str, option_key: str) -> CorreccionDeFallo:
        """**Corrige una pregunta suelta de la cola**, sin montar una sesión (punto 3).

        **La clave no sale de aquí**: se compara en el servidor y solo se devuelve si acertó, cuál
        valía y el porqué.
        """
        datos = self._cards.clave_y_explicacion(question_version_id)
        if datos is None:
            raise NotFoundError("clave de la pregunta", question_version_id)
        letras, explicacion, cita = datos
        elegida = option_key.strip().lower()
        return CorreccionDeFallo(
            correcto=elegida in {letra.strip().lower() for letra in letras},
            letras=letras,
            explicacion=explicacion,
            cita=cita,
        )
