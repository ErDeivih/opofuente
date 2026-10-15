"""El contrato de la revisión de apuntes del panel (F24, §4.3 del objetivo).

Tres rutas y sus cuerpos: la tabla de los temas, la ficha de un tema y la decisión.

Dos cosas que se ven en los esquemas y son decisiones, no descripciones:

1. **las frases del motivo las compone el servidor**, con sus cifras, y viajan ya escritas
   (`NotesReviewReasonSchema`). La pantalla las pinta tal cual, como hace con el resumen de
   preparación: dos sitios componiendo la misma frase acaban diciendo cosas distintas;
2. **la cobertura viaja en dos números** —cubiertas y con clave utilizable— y no en un porcentaje:
   el porcentaje se pinta, pero el par es el que permite comprobar la cuenta y el que dice si pasa
   el listón. Un porcentaje redondeado solo no se puede recontar.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from opofuente.domain.notes_reports import MAX_REASON_CHARS
from opofuente.domain.topic_notes import COBERTURA_MINIMA

#: Los nombres del estado de los apuntes, tal como los publica el servidor de la zona del alumno.
NotesStateName = Literal["published", "draft", "none"]

#: El vocabulario de la decisión. Son dos: aprobar y rechazar.
ReviewDecisionName = Literal["approved", "rejected"]

#: Qué puerta impide publicar cuando el tema está aprobado y no se ha podido archivar su versión.
ReviewBlockName = Literal["cobertura", "forma"]


class NotesReviewCountersSchema(BaseModel):
    """Los números de la cabecera: cuántos temas hay de cada clase y cuántos esperan decisión."""

    topics_total: int = Field(description="Temas del programa activo.")
    with_notes: int = Field(description="Temas con apuntes escritos.")
    published: int = Field(description="Con versión archivada: se leen como publicados.")
    draft: int = Field(description="Con apuntes escritos y **sin** versión archivada.")
    without_notes: int = Field(description="Temas que todavía no tienen apuntes escritos.")
    approved: int = Field(description="Con una decisión de aprobación escrita por el propietario.")
    rejected: int = Field(description="Rechazados: esperan a que el texto se arregle.")
    pending_decision: int = Field(
        description="Borradores sin aprobar: es lo que espera al propietario."
    )


class NotesReviewReasonSchema(BaseModel):
    """Por qué un tema está como está, en una frase con su cifra.

    `code` es el vocabulario del dominio (para filtrar o probar) y `text` lo que se lee. El orden de
    la lista **es** el orden de lectura: la primera razón es el titular.
    """

    code: str = Field(description="El código del motivo, del vocabulario del dominio.")
    text: str = Field(description="La frase, ya compuesta con su cifra.")
    figure: str | None = Field(
        default=None, description="La cifra sola, para pintarla aparte del texto."
    )


class NotesReviewVersionSchema(BaseModel):
    """La versión archivada de un tema: lo que lo hace «publicado»."""

    id: str
    built_at: datetime


class NotesReviewDecisionSchema(BaseModel):
    """Lo que el propietario decidió sobre un tema, con su nota, su fecha y quién lo firmó."""

    decision: ReviewDecisionName
    note: str | None = None
    actor: str
    reviewed_at: datetime


class NotesReviewChecksSchema(BaseModel):
    """Las comprobaciones guardadas del tema, contadas en la base.

    No son la puerta de cobertura —esa tiene otro denominador— y por eso van con su propio nombre:
    «de las preguntas que el motor ha comprobado, cuántas quedaron cubiertas, sin frase, dudosas o
    en conflicto con su respuesta correcta».
    """

    total: int
    covered: int
    gaps: int
    doubtful: int
    conflicts: int


class NotesReviewTopicSchema(BaseModel):
    """Una fila de la tabla: el tema, su estado, sus cifras, su motivo y su decisión."""

    code: str = Field(description="Código legible del tema, como `IV.7`.")
    title: str
    block_code: str
    block_title: str
    state: NotesStateName = Field(description="`published`, `draft` o `none`.")
    sections_written: int = Field(description="Apartados con texto.")
    facts: int = Field(description="Hechos guardados del tema (paso B).")
    checks: NotesReviewChecksSchema
    incidents_open: int = Field(description="Incidencias del motor sin despachar de este tema.")
    incidents_by_category: dict[str, int] = Field(
        description="Esas incidencias, por categoría. Vacío cuando no hay ninguna."
    )
    version: NotesReviewVersionSchema | None = None
    review: NotesReviewDecisionSchema | None = None
    reasons: list[NotesReviewReasonSchema] = Field(
        description=(
            "Por qué el tema está como está, con sus cifras. Vacío en los temas publicados que la "
            "tabla no mide (ya pasaron las puertas): su ficha sí los mide."
        ),
    )
    measured: bool = Field(
        description="Si esta lectura ha medido la cobertura del tema (sin modelo y sin coste)."
    )
    coverage: tuple[int, int] | None = Field(
        default=None,
        description="`(cubiertas, con clave utilizable)`: el par que decide la puerta del §2.3.",
    )
    coverage_all_keys: tuple[int, int] | None = Field(
        default=None,
        description="`(cubiertas, con clave)` sobre **todas** las que tienen clave. Se enseña.",
    )
    coverage_threshold: float = Field(
        default=COBERTURA_MINIMA, description="El listón del §2.3, que no se toca."
    )


class NotesReviewListSchema(BaseModel):
    """La tabla entera, con los contadores de la cabecera."""

    counters: NotesReviewCountersSchema
    topics: list[NotesReviewTopicSchema] = Field(
        description="Los temas del programa activo, en orden del temario. Siempre la lista entera."
    )


class NotesReviewSectionSchema(BaseModel):
    """Un apartado de los apuntes, tal como se lee, con lo que se ha comprobado en él."""

    key: str
    title: str
    epigraph_code: str
    anchor: str
    position: int = Field(description="El número con el que se lee, en orden de lectura.")
    body_markdown: str
    words: int
    facts_total: int
    covered: int
    gaps: int
    doubtful: int
    conflicts: int
    needs_review_reason: str | None = None
    worst: int = Field(
        description=(
            "Cuánto queda sin resolver en este apartado (conflictos + dudosas + sin frase): es lo "
            "que ordena «los peores primero»."
        )
    )


class NotesReviewFileSchema(BaseModel):
    """La ficha de un tema: su fila de la tabla y sus apartados en orden de lectura."""

    topic: NotesReviewTopicSchema
    sections: list[NotesReviewSectionSchema] = Field(
        description="Los apartados, en orden de lectura. Vacío si el tema no tiene texto escrito."
    )


class NotesReviewDecisionRequestSchema(BaseModel):
    """Aprobar o rechazar los apuntes de un tema, con la nota de lo decidido.

    La nota es **opcional al aprobar** y **obligatoria al rechazar**: un rechazo sin motivo deja el
    borrador donde estaba y encima sin saber por qué. Lo comprueba el esquema (para contestar un 422
    con su campo) y lo vuelve a comprobar el dominio (para cualquier camino que no pase por aquí).

    `validate_default` no es decorativo: sin él, un cuerpo que **no trae** `note` no pasa por el
    validador del campo —pydantic no valida los campos que no vienen— y el rechazo sin motivo se
    colaba hasta la última línea, donde solo quedaba un 500. Con él, el validador corre también
    cuando la nota no viene, y el 422 señala `note`, que es el campo que hay que rellenar.
    """

    model_config = ConfigDict(validate_default=True, extra="forbid")

    decision: ReviewDecisionName
    note: str | None = Field(default=None, max_length=MAX_REASON_CHARS)
    actor: str | None = Field(
        default=None,
        max_length=120,
        description="Quién decide. Si no viene, la cabecera `X-OpoFuente-Actor`; si no, `local`.",
    )

    @field_validator("note")
    @classmethod
    def _el_rechazo_necesita_motivo(cls, valor: str | None, info: ValidationInfo) -> str | None:
        """Una nota en una línea y, al rechazar, obligatoria.

        Se valida **en el campo** y no en el modelo entero para que el 422 señale `note` y no el
        cuerpo: la pantalla tiene que poder marcar el campo que falta. El dominio vuelve a
        comprobarlo (`normalise_decision_note`) para cualquier camino que no pase por aquí.
        """
        if valor is None:
            if info.data.get("decision") == "rejected":
                raise ValueError("un tema que se rechaza necesita su motivo")
            return None
        limpia = " ".join(valor.split())
        if limpia == "" and info.data.get("decision") == "rejected":
            raise ValueError("un tema que se rechaza necesita su motivo")
        return None if limpia == "" else limpia


class NotesReviewDecisionResultSchema(BaseModel):
    """Lo que ha pasado al decidir: la decisión y **si eso ha publicado** el tema.

    `published` no es «aprobado»: aprobar un tema que no pasa las puertas lo deja aprobado y sin
    publicar, y `blocked_by` dice cuál de las dos lo frena. El listón no se toca.
    """

    topic: NotesReviewTopicSchema
    published: bool
    version_created: bool | None = Field(
        default=None,
        description=(
            "Si la aprobación ha archivado una versión nueva. `false` si la que había ya era la "
            "misma lectura; `null` si no se ha intentado archivar."
        ),
    )
    blocked_by: ReviewBlockName | None = Field(
        default=None,
        description="Qué puerta impide publicar, cuando el tema está aprobado y no sale.",
    )
