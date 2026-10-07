"""Modelos de lectura de la zona del alumno (F2).

Estos modelos son la mitad de la regla del contrato de esta fase: **lo que no está aquí no puede
salir por la API**. Deliberadamente **no** tienen campo para la evidencia, el conjunto de origen, la
clave, la versión del documento, la ruta de un fichero ni el título de un banco. No es que se
filtren al final: es que no hay dónde ponerlos (REDISENO-ALUMNO §3.11, F2 §4).

Dos convenciones que se repiten y conviene leer una vez:

1. **El tema viaja por su código legible** (`IV.10`), no por su identificador. Ninguna respuesta de
   esta capa enseña un UUID de nodo del programa.
2. **`accuracy` es `None` cuando no hay nada respondido**, no `0.0`. Un tema sin tocar no está
   «suspendido»: está sin empezar, y confundir las dos cosas es mentir con un número.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class StudentOppositionView:
    """La oposición que sirve la zona del alumno, tal como se enseña: código y nombre."""

    code: str
    name: str


@dataclass(frozen=True, slots=True)
class StudentScoreView:
    """Cómo fue un test: aciertos, fallos, blancos y la puntuación directa con su penalización.

    `points` es la fracción exacta en texto (`128/3`, `42`) porque un tercio no es un decimal
    (DEBT-006) y `points_decimal` es la misma cifra redondeada, solo para leerla.
    """

    correct: int
    wrong: int
    blank: int
    points: str
    points_decimal: str
    maximum: float | None = None
    passed: bool | None = None


@dataclass(frozen=True, slots=True)
class StudentSessionView:
    """Un test del alumno: lo que se pinta en «Continuar», en el historial y al terminar.

    `title` lo compone esta capa a partir de lo que el alumno eligió, **nunca** del título del
    conjunto de origen: el nombre del banco del propietario no se le enseña a nadie (§3.10).
    """

    id: str
    mode: str
    status: str
    title: str
    total_questions: int
    answered_questions: int
    time_limit_minutes: int | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    result: StudentScoreView | None = None

    @property
    def finished(self) -> bool:
        return self.status == "finished"


@dataclass(frozen=True, slots=True)
class StudentTopicProgressView:
    """Un tema con lo que el alumno tiene y lo que ha hecho en él."""

    code: str
    number: int | None
    title: str
    available_questions: int
    answered: int
    correct: int
    accuracy: float | None
    due_reviews: int = 0

    @property
    def started(self) -> bool:
        return self.answered > 0


@dataclass(frozen=True, slots=True)
class StudentBlockProgressView:
    """Un bloque del programa con sus temas y el agregado del bloque.

    El agregado **no** es la media de los temas: es el total del bloque (aciertos entre corregidas).
    Promediar medias daría a un tema con dos preguntas el mismo peso que a uno con cincuenta.
    """

    code: str
    title: str
    position: int
    available_questions: int
    answered: int
    correct: int
    accuracy: float | None
    due_reviews: int = 0
    topics: tuple[StudentTopicProgressView, ...] = ()


@dataclass(frozen=True, slots=True)
class StudentOverviewView:
    """Lo que se pinta al entrar: el test a medias, los fallos vencidos y el progreso por bloque."""

    opposition: StudentOppositionView
    in_progress: StudentSessionView | None
    due_reviews: int
    blocks: tuple[StudentBlockProgressView, ...]
    recent_tests: tuple[StudentSessionView, ...] = ()


@dataclass(frozen=True, slots=True)
class StudentEpigraphView:
    """Un epígrafe del tema: solo código y título (el programa de TAI no publica epígrafes)."""

    code: str
    title: str


@dataclass(frozen=True, slots=True)
class StudentTopicView:
    """Un tema por su código legible: título, epígrafes, recuentos y progreso."""

    code: str
    number: int | None
    title: str
    description: str | None
    block_code: str
    block_title: str
    epigraphs: tuple[StudentEpigraphView, ...] = ()
    progress: StudentTopicProgressView | None = None


@dataclass(frozen=True, slots=True)
class StudentProgressView:
    """El progreso: acierto por bloque y por tema, los cinco más flojos e historial.

    «Los más flojos» solo mira temas **empezados**: un tema sin responder no es un punto débil, es
    un tema sin empezar, y colarlo en la lista empujaría fuera al que de verdad hay que repasar.
    """

    opposition: StudentOppositionView
    blocks: tuple[StudentBlockProgressView, ...]
    weakest_topics: tuple[StudentTopicProgressView, ...] = ()
    history: tuple[StudentSessionView, ...] = ()
