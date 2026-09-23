"""¿Está esto listo para estudiar, y qué falta? (S12.6).

El propietario pidió que la aplicación le dijera si puede ponerse a estudiar con lo que ha soltado
y, si no, qué le falta. Esta es esa respuesta, en tres pasos y una lista:

1. **material por papel**: cuántos documentos aceptados hay y de qué tipo, y cuántos no dicen aún a
   qué parte del programa pertenecen;
2. **preguntas por tema**: cuántas hay y cuántas están catalogadas en un nodo del programa;
3. **claves activas**: sin clave no hay corrección, así que un conjunto sin plantilla activa no se
   puede estudiar de verdad.

Y aparte, lo que espera a una persona (incidencias de importación, propuestas de clasificación,
cambios sin confirmar y material sin aceptar): eso no se arregla solo y por eso se dice.

**Las frases se componen aquí**, no en la pantalla: el mismo resumen que se lee en Inicio es el que
viaja en la respuesta, así que no hay dos versiones de la misma cifra (igual que el paso de un
trabajo).
"""

from __future__ import annotations

from opofuente.application.ports import ReadinessRepository
from opofuente.application.readiness_models import (
    STEP_EMPTY,
    STEP_INCOMPLETE,
    STEP_READY,
    MaterialSummary,
    PendingActionsView,
    PendingActionView,
    PendingCounts,
    QuestionSummary,
    ReadinessStepView,
    StudyReadinessView,
)
from opofuente.domain.classification import DOCUMENT_TYPE_LABELS

#: Dónde se resuelve cada paso y cada pendiente, en la propia aplicación.
LIBRARY_HREF = "/biblioteca"
QUESTIONS_HREF = "/preguntas"
TRAY_HREF = "/bandeja"
REVIEW_HREF = "/revision"
CHANGES_HREF = "/cambios"

#: Papeles que hacen falta para poder estudiar de verdad, no para tener material.
#: Un temario dice qué entra; un banco de preguntas o un examen oficial, con qué se practica.
_STUDY_ROLES = ("curriculum", "private_syllabus", "personal_notes")


class ReadinessService:
    """Compone el resumen de preparación y la lista de lo que espera a una persona."""

    def __init__(self, repository: ReadinessRepository) -> None:
        self._repository = repository

    # ------------------------------------------------------------------ preparación

    def readiness(self, opposition_id: str) -> StudyReadinessView | None:
        """Los tres pasos, con lo que falta dicho en palabras. `None` si la oposición no existe."""
        oposicion = self._repository.opposition(opposition_id)
        if oposicion is None:
            return None
        material = self._repository.material(opposition_id=opposition_id)
        preguntas = self._repository.questions(opposition_id=opposition_id)
        pasos = (
            self._material_step(material),
            self._questions_step(preguntas),
            self._keys_step(preguntas),
        )
        faltan = tuple(paso.detail for paso in pasos if paso.status != STEP_READY)
        return StudyReadinessView(
            opposition_id=oposicion.id,
            opposition_name=oposicion.name,
            convocation_code=oposicion.convocation_code,
            ready=not faltan,
            steps=pasos,
            missing=faltan,
        )

    def _material_step(self, material: MaterialSummary) -> ReadinessStepView:
        """El material aceptado, por papel, y cuánto no dice a qué parte del programa pertenece.

        Lo que decide el estado es si hay **con qué estudiar** (un temario o unos apuntes): un banco
        de preguntas y un examen oficial sirven para practicar, no para estudiar el temario. El
        material sin asignar se dice, pero no bloquea: se puede estudiar sin que la cobertura lo ve.
        """
        if material.total == 0:
            return ReadinessStepView(
                key="material",
                title="Material por papel",
                status=STEP_EMPTY,
                detail=(
                    "Todavía no hay ningún documento aceptado en este programa: suelta tus "
                    "carpetas y la aplicación las analizará."
                ),
                count=0,
                action_href=TRAY_HREF,
                action_label="Ir a la bandeja",
            )
        desglose = ", ".join(
            f"{DOCUMENT_TYPE_LABELS.get(papel, papel)} ({cantidad})"
            for papel, cantidad in material.by_role
        )
        de_estudio = sum(cantidad for papel, cantidad in material.by_role if papel in _STUDY_ROLES)
        detalle = f"{material.total} documento(s) aceptado(s)"
        if desglose:
            detalle += f": {desglose}"
        if de_estudio == 0:
            detalle += ". Ninguno es temario ni apuntes: hay con qué practicar, no qué estudiar"
        if material.unassigned:
            detalle += (
                f". Y {material.unassigned} sin decir todavía a qué parte de este programa "
                "pertenece(n), así que la cobertura por temas no los ve"
            )
        return ReadinessStepView(
            key="material",
            title="Material por papel",
            status=STEP_READY if de_estudio > 0 else STEP_INCOMPLETE,
            detail=detalle,
            count=material.total,
            action_href=LIBRARY_HREF,
            action_label="Ver la biblioteca",
        )

    def _questions_step(self, preguntas: QuestionSummary) -> ReadinessStepView:
        """Preguntas importadas y cuántas están catalogadas por tema."""
        if preguntas.questions == 0:
            return ReadinessStepView(
                key="preguntas",
                title="Preguntas por tema",
                status=STEP_EMPTY,
                detail=(
                    "Todavía no hay preguntas importadas: entran solas al aceptar un documento con "
                    "preguntas, o a mano desde el banco."
                ),
                count=0,
                action_href=QUESTIONS_HREF,
                action_label="Ir al banco",
            )
        sin_tema = preguntas.questions - preguntas.questions_with_topic
        detalle = (
            f"{preguntas.questions} pregunta(s) en {preguntas.sets_total} conjunto(s); "
            f"{preguntas.questions_with_topic} catalogada(s) por tema"
        )
        if sin_tema:
            detalle += (
                f". Quedan {sin_tema} sin tema, y sin tema el diagnóstico por temas no las "
                "reparte: se catalogan al aceptar la asignación del documento del que salen"
            )
        return ReadinessStepView(
            key="preguntas",
            title="Preguntas por tema",
            status=STEP_READY if sin_tema == 0 else STEP_INCOMPLETE,
            detail=detalle,
            count=preguntas.questions,
            action_href=QUESTIONS_HREF,
            action_label="Ver el banco",
        )

    def _keys_step(self, preguntas: QuestionSummary) -> ReadinessStepView:
        """Conjuntos con clave activa: sin clave no hay corrección."""
        if preguntas.sets_total == 0:
            return ReadinessStepView(
                key="claves",
                title="Claves activas",
                status=STEP_EMPTY,
                detail="Sin conjuntos de preguntas no hay clave que activar.",
                count=0,
                action_href=QUESTIONS_HREF,
                action_label="Ir al banco",
            )
        sin_clave = preguntas.sets_total - preguntas.sets_with_active_key
        detalle = (
            f"{preguntas.sets_with_active_key} de {preguntas.sets_total} conjunto(s) "
            "con clave activa"
        )
        if sin_clave:
            detalle += (
                f". {sin_clave} sin ella: sin clave activa no se puede corregir ni empezar una "
                "sesión sobre ese conjunto"
            )
        return ReadinessStepView(
            key="claves",
            title="Claves activas",
            status=STEP_READY if sin_clave == 0 else STEP_INCOMPLETE,
            detail=detalle,
            count=preguntas.sets_with_active_key,
            action_href=QUESTIONS_HREF,
            action_label="Ver las plantillas",
        )

    # ------------------------------------------------------------------ pendientes

    def pending_actions(self) -> PendingActionsView:
        """Lo que espera a una persona, en el orden en que conviene mirarlo.

        El orden no es decorativo: primero lo que impide entrar material (incidencias), después lo
        que deja el material sin clasificar (decisiones), luego lo que puede haber cambiado bajo los
        pies (cambios) y por último lo que solo espera un visto bueno (material sin aceptar).
        """
        cuentas = self._repository.pending()
        acciones = tuple(
            accion
            for accion in (
                self._import_issues(cuentas),
                self._pending_decisions(cuentas),
                self._proposed_changes(cuentas),
                self._unaccepted_versions(cuentas),
            )
            if accion is not None
        )
        return PendingActionsView(
            actions=acciones,
            total=sum(accion.count for accion in acciones),
        )

    @staticmethod
    def _import_issues(cuentas: PendingCounts) -> PendingActionView | None:
        if cuentas.import_issues == 0:
            return None
        return PendingActionView(
            key="importaciones",
            title="Importaciones con avisos o errores",
            detail=(
                f"{cuentas.import_issues} aviso(s) y error(es) de importación sin resolver: "
                "dicen qué fichero no entró y por qué"
            ),
            count=cuentas.import_issues,
            href=TRAY_HREF,
            label="Ver la bandeja",
        )

    @staticmethod
    def _pending_decisions(cuentas: PendingCounts) -> PendingActionView | None:
        if cuentas.pending_decisions == 0:
            return None
        return PendingActionView(
            key="clasificaciones",
            title="Clasificaciones esperando tu decisión",
            detail=(
                f"{cuentas.pending_decisions} decisión(es) sin tomar: mientras no se tomen, ese "
                "material no está en ningún tema del programa"
            ),
            count=cuentas.pending_decisions,
            href=REVIEW_HREF,
            label="Revisar propuestas",
        )

    @staticmethod
    def _proposed_changes(cuentas: PendingCounts) -> PendingActionView | None:
        if cuentas.proposed_changes == 0:
            return None
        return PendingActionView(
            key="cambios",
            title="Cambios de fuente sin confirmar",
            detail=(
                f"{cuentas.proposed_changes} cambio(s) propuesto(s) entre versiones: hay que "
                "decir si valen o no antes de seguir estudiando con ellos"
            ),
            count=cuentas.proposed_changes,
            href=CHANGES_HREF,
            label="Ver los cambios",
        )

    @staticmethod
    def _unaccepted_versions(cuentas: PendingCounts) -> PendingActionView | None:
        if cuentas.unaccepted_versions == 0:
            return None
        return PendingActionView(
            key="versiones",
            title="Material sin aceptar",
            detail=(
                f"{cuentas.unaccepted_versions} versión(es) de documento sin aceptar: "
                "aceptarlas es lo que las convierte en material de estudio y dispara la "
                "importación de sus preguntas"
            ),
            count=cuentas.unaccepted_versions,
            href=LIBRARY_HREF,
            label="Ver la biblioteca",
        )


__all__ = ["ReadinessService"]
