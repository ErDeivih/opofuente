"""Contrato de la zona del alumno (F2).

Estos esquemas son la garantía del contrato de la fase, y conviene leerlos por lo que **no**
tienen: ni evidencia, ni cita, ni conjunto de origen (`question_set_id`), ni clave
(`answer_key_version_id`, `correct_option_keys`), ni versión de documento, ni ruta de fichero, ni
identificador de nodo del programa. La regla del plan —«se consigue con esquemas propios que no
tienen esos campos, no filtrando al final»— se cumple aquí: aunque alguien devolviera por error una
vista con todo eso, no habría dónde ponerlo, porque FastAPI valida la respuesta contra este modelo
y descarta lo que no está declarado.

Dos cosas que sí viajan y son deliberadas:

- **el código legible del tema** (`IV.10`), que es la dirección del alumno; ningún UUID a la vista;
- **el identificador de la sesión**, que es lo que la pantalla necesita para pedir el siguiente
  test. Es lo único que se parece a un identificador interno, y no se puede evitar: es la dirección
  del propio test. Lo que no viaja es de dónde salieron sus preguntas.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from opofuente.api.study_schemas import SessionModeName, SessionStatusName


class StudentOppositionSchema(BaseModel):
    """La oposición que sirve la zona del alumno."""

    code: str
    name: str


class StudentScoreSchema(BaseModel):
    """Cómo fue un test: aciertos, fallos, blancos y la puntuación directa con su penalización.

    La puntuación viaja como fracción exacta en texto (`128/3`) **y** como decimal redondeado: el
    decimal es para leerlo, el exacto es el que vale (DEBT-006). `passed` es `None` cuando la
    convocatoria no publica el umbral, en lugar de inventar un aprobado.
    """

    correct: int = Field(ge=0)
    wrong: int = Field(ge=0)
    blank: int = Field(ge=0)
    points: str
    points_decimal: str
    maximum: float | None = None
    passed: bool | None = None


class StudentSessionSchema(BaseModel):
    """Un test del alumno: lo que se pinta en «Continuar», en el historial y al terminar.

    `title` lo compone la capa del alumno a partir de lo que se eligió; **nunca** es el título del
    conjunto de origen.
    """

    id: str
    mode: SessionModeName
    status: SessionStatusName
    title: str
    total_questions: int = Field(ge=0)
    answered_questions: int = Field(ge=0)
    time_limit_minutes: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime
    result: StudentScoreSchema | None = None


class StudentTopicProgressSchema(BaseModel):
    """Un tema con lo que tiene y lo que se ha hecho en él.

    `accuracy` es `None` cuando no hay nada corregido todavía: un tema sin tocar no está
    suspendido.
    """

    code: str
    number: int | None = None
    title: str
    available_questions: int = Field(ge=0)
    answered: int = Field(ge=0)
    correct: int = Field(ge=0)
    accuracy: float | None = Field(default=None, ge=0, le=1)
    due_reviews: int = Field(default=0, ge=0)


class StudentBlockProgressSchema(BaseModel):
    """Un bloque del programa con sus temas y el agregado del bloque."""

    code: str
    title: str
    position: int
    available_questions: int = Field(ge=0)
    answered: int = Field(ge=0)
    correct: int = Field(ge=0)
    accuracy: float | None = Field(default=None, ge=0, le=1)
    due_reviews: int = Field(default=0, ge=0)
    topics: list[StudentTopicProgressSchema]


class StudentOverviewSchema(BaseModel):
    """Inicio: el test a medias, los fallos vencidos, el progreso por bloque y lo último hecho."""

    opposition: StudentOppositionSchema
    in_progress: StudentSessionSchema | None = None
    due_reviews: int = Field(ge=0)
    blocks: list[StudentBlockProgressSchema]
    recent_tests: list[StudentSessionSchema]


class StudentSyllabusSchema(BaseModel):
    """El temario: bloques y temas **en orden numérico** (IV.1 antes de IV.10)."""

    opposition: StudentOppositionSchema
    blocks: list[StudentBlockProgressSchema]


class StudentEpigraphSchema(BaseModel):
    """Un epígrafe del tema: solo su código y su título."""

    code: str
    title: str


class StudentTopicSchema(BaseModel):
    """Un tema por su código legible, con sus epígrafes y su progreso."""

    code: str
    number: int | None = None
    title: str
    description: str | None = None
    block_code: str
    block_title: str
    epigraphs: list[StudentEpigraphSchema]
    progress: StudentTopicProgressSchema | None = None


class StudentProgressSchema(BaseModel):
    """El progreso: acierto por bloque y por tema, los cinco más flojos e historial."""

    opposition: StudentOppositionSchema
    blocks: list[StudentBlockProgressSchema]
    weakest_topics: list[StudentTopicProgressSchema]
    history: list[StudentSessionSchema]
