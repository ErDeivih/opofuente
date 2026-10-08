"""El clasificador de preguntas por tema y epígrafe (F4, pilotaje del paso A).

Lo que hace, en orden:

1. **selecciona** las preguntas sin tema de la oposición que se le diga, agrupadas por banco (su
   conjunto de origen) y de mayor a menor: es lo que permite parar tras los dos primeros y mirar la
   calidad antes de gastar en el resto;
2. **construye el prompt con el temario real**: los bloques, los temas y los epígrafes salen de la
   base (la convocatoria sembrada), no de una lista escrita a mano que se quedaría vieja;
3. **pregunta al modelo en lotes** (20 por llamada, que es lo que se midió: 0,0000366 $ por
   pregunta) y aplica los **umbrales** del dominio a lo que contesta;
4. **escribe por el servicio**, nunca por SQL: lo que entra por confianza alta va como asignación
   aceptada, lo dudoso va como **propuesta provisional** (la cola de revisión del propietario) y lo
   que no es del programa se declara **fuera de temario**. El actor queda como `llm:…` en la
   auditoría, para poder distinguir lo que hizo la máquina de lo que decidió una persona.

No inventa nada en ningún punto: un código que no está en el temario es un error de la propuesta (va
al informe), y una pregunta que el modelo no contesta queda sin clasificar y se cuenta.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence

from opofuente.application.ports import ProfileRepository, TopicProposer
from opofuente.application.question_models import TopicAssignmentBatch, TopicAssignmentRequest
from opofuente.application.question_service import QuestionService
from opofuente.application.read_models import NodeView
from opofuente.application.topic_classification_models import (
    BankReport,
    BankToClassify,
    ClassificationReport,
)
from opofuente.domain.errors import (
    ExternalServiceError,
    NotFoundError,
    OpoFuenteError,
    UnsupportedError,
)
from opofuente.domain.profiles import NodeType
from opofuente.domain.topic_classification import (
    ClassifiableQuestion,
    Decision,
    ProposalBatch,
    ProposalOutcome,
    Syllabus,
    SyllabusEpigraph,
    SyllabusTopic,
    TopicProposal,
    decide,
)
from opofuente.infrastructure.topic_classification_repository import (
    SqlAlchemyTopicClassificationRepository,
)

logger = logging.getLogger("opofuente.application.topic_classification_service")

#: Cuántas preguntas van en cada llamada al modelo. Veinte es lo que se midió en el trabajo de
#: apuntes (0,0000366 $ por pregunta): más preguntas por llamada abaratan la entrada por caché pero
#: hacen que una respuesta mal formada cueste más caro en preguntas sin clasificar.
LOTE_POR_DEFECTO = 20

#: El actor con el que se firma lo que escribe la máquina. Es lo que permite auditar qué clasificó
#: el modelo y qué decidió una persona.
ACTOR_CLASIFICADOR = "llm:deepseek-flash"


def syllabus_from_curriculum(opposition_code: str, nodes: Sequence[NodeView]) -> Syllabus:
    """El temario del prompt, leído del programa sembrado.

    Se recorre el árbol real —bloques, temas y epígrafes— en lugar de una lista escrita a mano: si
    el BOE cambia y la siembra cambia, el prompt cambia con ella. Un tema sin epígrafes se queda con
    su código y su título, que es lo que hay.
    """
    temas: list[SyllabusTopic] = []
    for bloque in nodes:
        if bloque.node_type is not NodeType.BLOCK:
            continue
        for tema in bloque.children:
            if tema.node_type is not NodeType.TOPIC:
                continue
            temas.append(
                SyllabusTopic(
                    code=tema.path,
                    title=tema.title,
                    node_id=tema.id,
                    block_code=bloque.path,
                    epigraphs=tuple(
                        SyllabusEpigraph(
                            code=hijo.path,
                            title=hijo.title,
                            node_id=hijo.id,
                            topic_code=tema.path,
                        )
                        for hijo in tema.children
                        if hijo.node_type is NodeType.EPIGRAPH
                    ),
                )
            )
    return Syllabus(opposition_code=opposition_code, topics=tuple(temas))


class TopicClassificationService:
    """Clasifica por bancos y escribe por el servicio del banco de preguntas."""

    def __init__(
        self,
        *,
        classification: SqlAlchemyTopicClassificationRepository,
        profiles: ProfileRepository,
        questions: QuestionService,
        proposer: TopicProposer,
        actor: str = ACTOR_CLASIFICADOR,
        batch_size: int = LOTE_POR_DEFECTO,
    ) -> None:
        self._classification = classification
        self._profiles = profiles
        self._questions = questions
        self._proposer = proposer
        self._actor = actor
        self._batch_size = max(1, batch_size)

    # ------------------------------------------------------------------ lectura

    def opposition_id(self, code: str) -> str:
        """El identificador de la oposición por su código. Se dice cuál falla si no existe."""
        for oposicion in self._profiles.list_oppositions():
            if oposicion.code == code:
                return oposicion.id
        raise NotFoundError("oposición", code)

    def syllabus(self, code: str) -> Syllabus:
        """El temario del prompt, de la convocatoria vigente de esa oposición."""
        for oposicion in self._profiles.list_oppositions():
            if oposicion.code != code:
                continue
            if oposicion.convocation_id is None:
                raise UnsupportedError(
                    f"la oposición «{code}» no tiene convocatoria: sin programa no hay temario "
                    "que enseñarle al modelo (siembra los perfiles oficiales)"
                )
            curriculum = self._profiles.get_curriculum(oposicion.convocation_id)
            if curriculum is None:
                raise NotFoundError("programa de la convocatoria", oposicion.convocation_id)
            return syllabus_from_curriculum(code, curriculum.nodes)
        raise NotFoundError("oposición", code)

    def banks(self, code: str, *, limit: int | None = None) -> tuple[BankToClassify, ...]:
        """Los bancos con preguntas sin tema, de mayor a menor."""
        return self._classification.banks(self.opposition_id(code), limit=limit)

    # ------------------------------------------------------------------ la corrida

    def run(
        self,
        code: str,
        *,
        banks: int | None = None,
        limit: int | None = None,
        dry_run: bool = False,
    ) -> ClassificationReport:
        """Clasifica los bancos indicados y devuelve el informe. `dry_run` no escribe nada.

        `banks` corta por número de bancos (los que más preguntas tienen primero) y `limit` por
        número total de preguntas: el propietario quiere parar tras dos bancos para revisar la
        calidad, y las dos formas de cortar tienen que poder decirse.
        """
        syllabus = self.syllabus(code)
        if not syllabus.topics:
            raise UnsupportedError(
                f"el programa de «{code}» no tiene temas: sin temario no hay nada que asignar"
            )
        seleccionados = self._classification.banks(
            self.opposition_id(code),
            limit=banks if banks is not None else None,
        )
        informes: list[BankReport] = []
        restantes = limit
        entrada = 0
        salida = 0
        for banco in seleccionados:
            if restantes is not None and restantes <= 0:
                break
            tope = restantes
            informe, tokens = self._classify_bank(
                banco, syllabus=syllabus, limit=tope, dry_run=dry_run
            )
            informes.append(informe)
            entrada += tokens[0]
            salida += tokens[1]
            if restantes is not None:
                restantes -= informe.processed
        return ClassificationReport(
            opposition_code=code,
            dry_run=dry_run,
            banks=tuple(informes),
            input_tokens=entrada,
            output_tokens=salida,
        )

    # ------------------------------------------------------------------ un banco

    def _classify_bank(
        self,
        bank: BankToClassify,
        *,
        syllabus: Syllabus,
        limit: int | None,
        dry_run: bool,
    ) -> tuple[BankReport, tuple[int, int]]:
        preguntas = self._classification.pending_questions(bank.set_id, limit=limit)
        informe = BankReport(set_id=bank.set_id, title=bank.title, pending=bank.pending)
        entrada = 0
        salida = 0
        for lote in _chunks(preguntas, self._batch_size):
            propuestas = self._ask(lote, syllabus=syllabus, informe=informe)
            entrada += propuestas.input_tokens
            salida += propuestas.output_tokens
            informe.batches += 1
            self._apply(
                lote, propuestas.proposals, syllabus=syllabus, informe=informe, dry_run=dry_run
            )
        return informe, (entrada, salida)

    def _ask(
        self, lote: Sequence[ClassifiableQuestion], *, syllabus: Syllabus, informe: BankReport
    ) -> ProposalBatch:
        """Una llamada al modelo. Un fallo del servicio de fuera **para la corrida**, diciéndolo.

        Un clasificador que sigue después de que el modelo deje de responder gastaría llamadas para
        nada y llenaría el informe de huecos: es mejor parar y que el propietario lo vea.
        """
        try:
            return self._proposer.propose(lote, syllabus=syllabus)
        except OpoFuenteError as error:
            raise ExternalServiceError(
                f"{error} (banco «{informe.title}», {len(lote)} pregunta(s) en el lote)"
            ) from error

    def _apply(
        self,
        lote: Sequence[ClassifiableQuestion],
        propuestas: Sequence[TopicProposal],
        *,
        syllabus: Syllabus,
        informe: BankReport,
        dry_run: bool,
    ) -> None:
        """Aplica los umbrales al lote y escribe lo que salga, por el servicio del banco."""
        por_pregunta = {propuesta.question_version_id: propuesta for propuesta in propuestas}
        decisiones: list[Decision] = []
        for pregunta in lote:
            informe.processed += 1
            propuesta = por_pregunta.get(pregunta.question_version_id)
            if propuesta is None:
                informe.nothing += 1
                informe.add_note(
                    f"{pregunta.question_version_id}: el modelo no contestó por esta pregunta"
                )
                continue
            decision = decide(propuesta, syllabus=syllabus)
            decisiones.append(decision)
            self._count(decision, informe)

        peticiones = [
            peticion for peticion in (self._request(d) for d in decisiones) if peticion is not None
        ]
        if not peticiones or dry_run:
            return
        resultado = self._questions.apply_topic_batch(peticiones, actor=self._actor)
        self._read_back(resultado, informe)

    def _count(self, decision: Decision, informe: BankReport) -> None:
        """Cuenta lo que ha decidido el dominio. El informe se lee de aquí, no de la escritura."""
        if decision.outcome is ProposalOutcome.ASSIGN:
            informe.assigned += 1
        elif decision.outcome is ProposalOutcome.REVIEW:
            informe.proposed += 1
        elif decision.outcome is ProposalOutcome.OUT_OF_SYLLABUS:
            informe.out_of_syllabus += 1
        elif decision.outcome is ProposalOutcome.ERROR:
            informe.errors += 1
        else:
            informe.nothing += 1
        if decision.note and decision.outcome is not ProposalOutcome.ASSIGN:
            informe.add_note(f"{decision.question_version_id}: {decision.note}")

    @staticmethod
    def _request(decision: Decision) -> TopicAssignmentRequest | None:
        """La petición de escritura de una decisión. `None` si la decisión no escribe nada."""
        if decision.outcome is ProposalOutcome.ASSIGN and decision.topic is not None:
            return TopicAssignmentRequest(
                question_version_id=decision.question_version_id,
                curriculum_node_id=decision.topic.node_id,
                epigraph_node_id=(None if decision.epigraph is None else decision.epigraph.node_id),
                confidence=decision.confidence,
                reason=decision.note,
                status="accepted",
            )
        if decision.outcome is ProposalOutcome.REVIEW and decision.topic is not None:
            return TopicAssignmentRequest(
                question_version_id=decision.question_version_id,
                curriculum_node_id=decision.topic.node_id,
                epigraph_node_id=(None if decision.epigraph is None else decision.epigraph.node_id),
                confidence=decision.confidence,
                reason=decision.note or "propuesta con confianza media: a la cola de revisión",
                status="provisional",
            )
        if decision.outcome is ProposalOutcome.OUT_OF_SYLLABUS and decision.out_of_syllabus:
            return TopicAssignmentRequest(
                question_version_id=decision.question_version_id,
                exclusion_reason=decision.out_of_syllabus,
                confidence=decision.confidence,
                reason=decision.note,
            )
        return None

    @staticmethod
    def _read_back(resultado: TopicAssignmentBatch, informe: BankReport) -> None:
        """Lo que dijo la escritura: lo que ya estaba y lo que el servicio rechazó.

        Las filas rechazadas se cuentan **además** de la decisión: una cosa es lo que el
        clasificador decidió y otra lo que la base aceptó, y confundirlas escondería un fallo de
        escritura.
        """
        for fila in resultado.rows:
            if fila.outcome == "existing":
                informe.existing += 1
            elif fila.outcome == "error":
                informe.write_errors += 1
                informe.add_note(f"{fila.question_version_id}: no se pudo escribir: {fila.detail}")


def _chunks(
    questions: Sequence[ClassifiableQuestion], size: int
) -> Iterable[Sequence[ClassifiableQuestion]]:
    """El lote partido en trozos de `size`, en el orden de la selección."""
    for inicio in range(0, len(questions), size):
        yield questions[inicio : inicio + size]


__all__ = [
    "ACTOR_CLASIFICADOR",
    "LOTE_POR_DEFECTO",
    "TopicClassificationService",
    "syllabus_from_curriculum",
]
