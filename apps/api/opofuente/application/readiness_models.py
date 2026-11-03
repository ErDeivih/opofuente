"""Modelo de lectura de «¿esto está listo para estudiar?» (S12.6).

No es una entidad de dominio ni una tabla: es la composición de lo que **ya está** en la base
—material por papel, preguntas por tema, claves activas— y de lo que sigue esperando una decisión de
una persona. Cada cifra sale de una consulta; lo que no se puede saber se declara como tal, no se
rellena con cero.

Vive aparte de `read_models.py` porque allí están los modelos que la API ya servía desde S01, y este
responde a otra pregunta: no cuánto hay, sino **qué falta** para poder estudiar.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

#: Estados de un paso: listo, a medias, o sin nada todavía.
StepStatus = Literal["ready", "incomplete", "empty"]

#: Un paso está listo cuando hay algo y no le falta nada; `incomplete`, cuando hay algo a medias;
#: `empty`, cuando todavía no hay nada. Los tres se dicen con palabras en la pantalla.
STEP_READY: StepStatus = "ready"
STEP_INCOMPLETE: StepStatus = "incomplete"
STEP_EMPTY: StepStatus = "empty"


@dataclass(frozen=True, slots=True)
class ReadinessStepView:
    """Un paso hacia poder estudiar: qué es, cómo está, cuánto hay y por dónde se resuelve."""

    key: str
    title: str
    status: StepStatus
    detail: str
    count: int
    action_href: str
    action_label: str


@dataclass(frozen=True, slots=True)
class StudyReadinessView:
    """Si esta oposición se puede estudiar ya, paso a paso, y qué falta si falta algo."""

    opposition_id: str
    opposition_name: str
    convocation_code: str | None
    ready: bool
    steps: tuple[ReadinessStepView, ...]
    #: Frases enteras, compuestas en el servidor: la pantalla no las reinterpreta.
    missing: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PendingActionView:
    """Algo que espera a una persona, con la pantalla donde se resuelve."""

    key: str
    title: str
    detail: str
    count: int
    href: str
    label: str


@dataclass(frozen=True, slots=True)
class PendingActionsView:
    """Todo lo que espera a una persona ahora mismo, en el orden en que conviene mirarlo."""

    actions: tuple[PendingActionView, ...]
    total: int


# --- lo que devuelve el repositorio (cifras crudas, sin frases) --------------------------------


@dataclass(frozen=True, slots=True)
class OppositionRef:
    """La oposición a la que se refiere el resumen, con su convocatoria si la tiene."""

    id: str
    name: str
    convocation_code: str | None


@dataclass(frozen=True, slots=True)
class MaterialSummary:
    """Material aceptado, por papel documental, más lo que todavía no está asignado al programa.

    `total` y `by_role` cuentan **todo** el material aceptado —un documento no deja de ser apuntes
    por no estar asignado—; `unassigned`, en cambio, se mira contra una oposición concreta: son los
    documentos aceptados que no dicen a qué parte de **ese** programa pertenecen.
    """

    by_role: tuple[tuple[str, int], ...]
    total: int
    unassigned: int


@dataclass(frozen=True, slots=True)
class QuestionSummary:
    """Preguntas de la oposición: conjuntos, claves y cuántas están catalogadas por tema."""

    sets_total: int
    sets_with_active_key: int
    questions: int
    questions_with_topic: int


@dataclass(frozen=True, slots=True)
class PendingCounts:
    """Lo que espera a una persona, contado: incidencias, decisiones, cambios y versiones.

    `pending_decisions` cuenta **decisiones**, no propuestas: el motor propone lo mismo sobre el
    material y sobre su texto, y esas dos propuestas son una sola pregunta para quien revisa (ver
    `reconcile_pending_proposals`). Contar filas aquí sería inflar la cola a ojos del usuario.
    """

    import_issues: int
    pending_decisions: int
    proposed_changes: int
    unaccepted_versions: int
