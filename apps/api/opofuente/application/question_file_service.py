"""La ficha de pregunta: se lee para decidir y se escribe para arreglarla (F20, §4.2 del objetivo).

El servicio hace tres cosas:

1. **armar la ficha**: junta lo que ya saben los repositorios del banco (la pregunta con su clave,
las
   plantillas del conjunto, el conjunto) con lo que solo sabe este (`question_file_repository`: el
   material del que salió la clave, lo que contestaron los apuntes, las incidencias, la marca de
fuera
   de temario y el veredicto de fiabilidad del §1). Nada se recalcula: la fiabilidad la mantiene la
   puerta de datos de aquel bloque y aquí solo se lee;
2. **marcar la correcta**: una escritura auditada sobre la plantilla del conjunto, con la anterior
   `superseded`. El repositorio la hace en una transacción; aquí solo se decide que la pregunta
exista y
   que quien llama no se equivoque de identificador;
3. **reparar**: le pide la reparación **al dominio** (`reparacion_disponible`) y escribe una versión
   nueva. La ruta no acepta texto inventado: lo que se escribe lo decide una regla del dominio, y si
   ninguna regla vale, la ficha lo dice y no se escribe nada.

Y una cosa que **no** hace: recalcular la fiabilidad de la clave de un conjunto. Esa cifra es del §1
y
vive en `question_sets.key_reliability`; aquí se lee si está y, si no está, se dice que no está.
"""

from __future__ import annotations

from collections.abc import Sequence

from opofuente.application.question_file_models import (
    AnswerKeyMarkOutcome,
    AnswerKeyVersionBriefView,
    KeyProvenanceView,
    OptionView,
    ProtectionView,
    QuestionFileView,
    RepairOptionView,
    RepairOutcome,
)
from opofuente.application.question_models import AnswerKeyView
from opofuente.application.question_service import QuestionService
from opofuente.domain.errors import (
    ClassificationConflictError,
    NotFoundError,
)
from opofuente.domain.question_file import (
    TITULO_DE_REGLA,
    motivo_de_no_reparar,
    protege_cambiar_la_clave,
    reparacion_disponible,
)
from opofuente.infrastructure.clock import SystemClock
from opofuente.infrastructure.question_file_repository import (
    SqlAlchemyQuestionFileRepository,
)

#: Quién firma las reparaciones que lanza el comando. Se distingue de la persona (`local`) y de la
#: máquina (`llm:…`): es una decisión tomada con el encargo delante.
ACTOR_REPARACION = "f20:reparacion-preguntas"

#: El vocabulario del estado de una plantilla, para la procedencia de la clave.
_ESTADOS_DE_PLANTILLA = {
    "active": "activa (es la que corrige)",
    "draft": "en borrador (no corrige todavía)",
    "superseded": "sustituida",
    "rejected": "rechazada",
}


def _traduce_estado_plantilla(estado: str) -> str:
    """El estado de la plantilla, tal cual, para que la pantalla no invente el texto.

        Se devuelve el valor **del contrato** y no una frase: el vocabulario es del servidor y
    traducirlo
        aquí otra vez crearía una segunda lista que se queda vieja.
    """
    return estado


class QuestionFileService:
    """Lee la ficha de una pregunta y hace las dos escrituras que permite."""

    def __init__(
        self,
        questions: QuestionService,
        files: SqlAlchemyQuestionFileRepository,
        clock: SystemClock | None = None,
    ) -> None:
        self._questions = questions
        self._files = files
        self._clock = clock if clock is not None else SystemClock()

    # ------------------------------------------------------------------ lectura

    def file(self, question_version_id: str) -> QuestionFileView:
        """La ficha entera de una pregunta, o 404 si no existe.

        Se arma en **una** lectura por pieza y no en una por dato: la ficha se abre desde la bandeja
        muchas veces seguidas, y una consulta por incidente haría de la revisión de la bandeja un
        ejercicio de paciencia.
        """
        pregunta = self._questions.question(question_version_id, include_key=True)
        if pregunta is None:
            raise NotFoundError("pregunta", question_version_id)
        conjunto = self._questions.set_detail(pregunta.question_set_id)
        if conjunto is None:  # pragma: no cover - una pregunta sin conjunto no existe
            raise NotFoundError("conjunto de preguntas", pregunta.question_set_id)
        claves = self._questions.keys(pregunta.question_set_id)
        vigente = _clave_que_manda(claves)
        fiabilidad, fuente = self._files.key_reliability_of(pregunta.question_set_id)
        protegidos = self._files.protected_sets()
        plantilla_enlazada = any(clave.source_document_version_id is not None for clave in claves)
        motivo_proteccion = protege_cambiar_la_clave(
            set_type=conjunto.set_type, tiene_plantilla_enlazada=plantilla_enlazada
        )
        versiones = self._files.versions_of(question_version_id)
        superseded_by = None
        if versiones and versiones[0].id != question_version_id:
            superseded_by = versiones[0].id
        opciones = tuple(
            OptionView(
                stable_key=opcion.stable_key,
                position=opcion.position,
                text=opcion.text,
                label=opcion.label,
            )
            for opcion in pregunta.options
        )
        return QuestionFileView(
            question_version_id=pregunta.id,
            question_set_id=pregunta.question_set_id,
            set_title=conjunto.title,
            set_type=conjunto.set_type,
            set_distribution=conjunto.distribution,
            stable_key=pregunta.stable_key,
            version_no=pregunta.version_no,
            position=pregunta.position,
            question_type=pregunta.question_type,
            status=pregunta.status,
            origin_type=pregunta.origin_type,
            is_reserve=pregunta.is_reserve,
            reserve_order=pregunta.reserve_order,
            created_at=pregunta.created_at,
            note=pregunta.note,
            stem=pregunta.stem,
            options=opciones,
            key=self._provenance(
                vigente,
                pregunta.correct_option_keys,
                pregunta.key_outcome,
                _nota_de_la_entrada(vigente, question_version_id),
            ),
            key_reliability=fiabilidad,
            reliability_source=fuente,
            notes=self._files.notes_contrast(question_version_id),
            incidents=self._files.incidents_of(question_version_id),
            exclusion=self._files.exclusion_of(question_version_id),
            protection=ProtectionView(
                protected=motivo_proteccion is not None,
                reason=motivo_proteccion,
                sets=protegidos,
            ),
            repair=self._repair_option(
                stem=pregunta.stem,
                opciones=tuple(opcion.text for opcion in opciones),
                tipo=pregunta.question_type,
            ),
            versions=versiones,
            keys=tuple(
                AnswerKeyVersionBriefView(
                    id=clave.id,
                    version_no=clave.version_no,
                    status=clave.status,
                    approved_at=clave.approved_at,
                    created_at=clave.created_at,
                    source_document_title=self._titulo_del_material(clave),
                    correct_option_keys=next(
                        (
                            entrada.correct_option_keys
                            for entrada in clave.entries
                            if entrada.question_version_id == question_version_id
                        ),
                        (),
                    ),
                )
                for clave in reversed(claves)
            ),
            superseded_by=superseded_by,
        )

    def _titulo_del_material(self, clave: AnswerKeyView) -> str | None:
        """El título del documento del que salió la plantilla, para el historial de la clave."""
        if clave.source_document_version_id is None:
            return None
        documento = self._files.key_source_document(str(clave.source_document_version_id))
        return None if documento is None else documento[0]

    def _provenance(
        self,
        clave: AnswerKeyView | None,
        letras: Sequence[str],
        desenlace: str | None,
        notas: str | None,
    ) -> KeyProvenanceView | None:
        """De dónde sale la respuesta correcta que manda hoy.

        `None` cuando la pregunta no tiene ninguna: sin plantilla, o con plantilla pero sin entrada
        para esta pregunta. Se dice, no se inventa una letra vacía.
        """
        if desenlace is None or clave is None:
            # Sin desenlace no hay clave que enseñar; y con desenlace pero sin plantilla sería un
            # estado imposible: en los dos casos se devuelve vacío en vez de una procedencia
            # inventada.
            return None
        documento = None
        if clave.source_document_version_id is not None:
            documento = self._files.key_source_document(str(clave.source_document_version_id))
        return KeyProvenanceView(
            answer_key_version_id=clave.id,
            version_no=clave.version_no,
            status=_traduce_estado_plantilla(clave.status),
            outcome=str(desenlace),
            correct_option_keys=tuple(letras),
            approved_at=clave.approved_at,
            published_at=clave.published_at,
            source_document_id=None if documento is None else documento[4],
            source_document_title=None if documento is None else documento[0],
            source_document_type=None if documento is None else documento[1],
            source_version_label=None if documento is None else documento[2],
            source_version_status=None if documento is None else documento[3],
            notes=notas,
        )

    @staticmethod
    def _repair_option(*, stem: str, opciones: tuple[str, ...], tipo: str) -> RepairOptionView:
        """Qué reparación ofrece la ficha: la que hay, o el porqué de que no haya ninguna.

                Las dos cosas viajan en el mismo objeto porque son la misma pregunta: «¿se puede
                arreglar
                esto?». Cuando hay reparación, `por_que_no` va nulo; cuando no la hay, `reglas` va
                vacío y
        lo
                que viaja es el motivo. Y cuando el motor no señaló nada, las dos van vacías y la
                pantalla
        no
                ofrece nada, que es lo correcto para una pregunta que está bien.
        """
        reparacion = reparacion_disponible(stem=stem, opciones=opciones, tipo=tipo)
        if reparacion is not None:
            return RepairOptionView(
                reglas=reparacion.reglas,
                titulos=tuple(TITULO_DE_REGLA[regla] for regla in reparacion.reglas),
                detalle=reparacion.detalle,
                stem=reparacion.stem,
                opciones=reparacion.opciones,
            )
        return RepairOptionView(
            reglas=(),
            titulos=(),
            detalle="",
            stem=None,
            opciones=None,
            por_que_no=motivo_de_no_reparar(stem=stem, opciones=opciones, tipo=tipo),
        )

    # ------------------------------------------------------------------ escritura

    def mark_correct(
        self,
        question_version_id: str,
        *,
        correct_option_keys: Sequence[str],
        note: str | None = None,
        actor: str = "local",
    ) -> AnswerKeyMarkOutcome:
        """Marca la respuesta correcta de una pregunta, por la ruta auditada.

                El repositorio escribe la plantilla nueva, retira la anterior y deja el evento en
                una sola
                transacción; aquí solo se comprueba que la pregunta exista **antes** de escribir y
                se rearma
        la
                ficha para que la respuesta enseñe el estado de después y no el de antes.
        """
        if self._questions.question(question_version_id) is None:
            raise NotFoundError("pregunta", question_version_id)
        datos = self._files.mark_correct(
            question_version_id,
            correct_option_keys=correct_option_keys,
            note=note,
            actor=actor,
            now=self._clock.now(),
        )
        return AnswerKeyMarkOutcome(
            file=self.file(question_version_id),
            key_version_id=datos.key_version_id,
            superseded_key_version_id=datos.superseded_key_version_id,
            previous_option_keys=datos.previous_option_keys,
            correct_option_keys=datos.correct_option_keys,
            moved_versions=datos.previous_option_keys != datos.correct_option_keys,
            actor=actor,
        )

    def repair(
        self,
        question_version_id: str,
        *,
        note: str,
        reglas: Sequence[str] | None = None,
        actor: str = ACTOR_REPARACION,
    ) -> RepairOutcome:
        """Repara lo que una regla pueda reparar de esta pregunta, con su motivo.

                `reglas` es opcional y solo puede **restringir** lo que el dominio ofrece: pedir una
                regla
        que
                esta pregunta no necesita no inventa una reparación, se contesta que no hay nada que
                hacer.
                La reparación la calcula el dominio con el texto de la pregunta; la ruta no manda
                texto.
        """
        actual = self.file(question_version_id)
        reparacion = reparacion_disponible(
            stem=actual.stem,
            opciones=tuple(opcion.text for opcion in actual.options),
            tipo=actual.question_type,
        )
        if reparacion is None:
            raise ClassificationConflictError(
                actual.repair.por_que_no
                if actual.repair is not None and actual.repair.por_que_no is not None
                else "esta pregunta no tiene ninguna reparación que una regla pueda hacer"
            )
        aplicables = reparacion.reglas
        if reglas is not None:
            pedidas = tuple(regla for regla in reglas if regla in reparacion.reglas)
            if not pedidas:
                raise ClassificationConflictError(
                    "las reglas pedidas no son ninguna de las que esta pregunta necesita: "
                    + ", ".join(reparacion.reglas)
                )
            aplicables = pedidas
        quiere_stem = any(regla == "quitar_referencia_del_examen" for regla in aplicables)
        quiere_opciones = any(regla == "partir_opcion_fundida" for regla in aplicables)
        datos = self._files.repair(
            question_version_id,
            stem=reparacion.stem if quiere_stem else None,
            opciones=reparacion.opciones if quiere_opciones else None,
            reglas=aplicables,
            note=note,
            actor=actor,
            now=self._clock.now(),
        )
        return RepairOutcome(
            file=self.file(datos.new_question_version_id),
            new_question_version_id=datos.new_question_version_id,
            superseded_question_version_id=datos.superseded_question_version_id,
            reglas=aplicables,
            key_version_id=datos.key_version_id,
            moved_topics=datos.moved_topics,
            moved_anchors=datos.moved_anchors,
            moved_exclusion=datos.moved_exclusion,
            actor=actor,
        )

    def incident_ids_of(self, question_version_id: str) -> tuple[str, ...]:
        """Las incidencias que cuelgan de esta pregunta y de sus versiones anteriores.

        Lo usa la ruta al reparar: una bandeja que siga enseñando una pregunta ya reparada miente,
        así que sus incidencias se despachan por la ruta auditada de la bandeja y con su nota.
        """
        return self._files.incident_ids_of(question_version_id)


def _nota_de_la_entrada(clave: AnswerKeyView | None, question_version_id: str) -> str | None:
    """La nota que la plantilla que manda lleva escrita sobre **esta** pregunta.

    La nota de una clave es de la entrada y no de la plantilla —una plantilla tiene una entrada por
    pregunta— y por eso hay que buscarla: leerla de la plantilla devolvería nada y la ficha diría
    que nadie anotó por qué se corrigió cuando sí hay nota.
    """
    if clave is None:
        return None
    for entrada in clave.entries:
        if entrada.question_version_id == question_version_id:
            return entrada.notes
    return None


def _clave_que_manda(claves: Sequence[AnswerKeyView]) -> AnswerKeyView | None:
    """La plantilla que manda en un conjunto: la activa y, si no hay, la última.

    Es la misma regla que el banco (`_active_entries` de `question_repository`): una plantilla en
    borrador es lo que se está revisando en el banco, y esconderla dejaría la ficha sin lo único que
    hay que mirar. Activar sigue siendo lo que decide qué clave corrige un examen.
    """
    if not claves:
        return None
    activas = [clave for clave in claves if clave.status == "active"]
    if activas:
        return max(activas, key=lambda clave: clave.version_no)
    return max(claves, key=lambda clave: clave.version_no)


__all__ = ["ACTOR_REPARACION", "QuestionFileService"]
