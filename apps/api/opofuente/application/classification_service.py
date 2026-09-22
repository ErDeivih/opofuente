"""Servicio de clasificación y revisión (S04).

Orquesta lo que ya existe por separado: los motores proponen, el repositorio guarda y decide, y este
servicio decide **qué se aplica solo y qué va a revisión** según las bandas de confianza.

Reglas que se aplican aquí y no en el repositorio:

- **una pasada de clasificación es idempotente**: volver a ejecutarla no duplica propuestas (la
  identidad incluye motor, versión y valor) y no revive decisiones;
- **solo se aplica solo lo que la banda permite**: una propuesta de banda alta en un eje no crítico
  queda `auto_applied_provisional` (visible y reversible, con su mapeo **provisional**); en los ejes
  críticos —autoridad y derechos— no se aplica nada nunca sin que alguien lo confirme;
- **el lote nunca es todo-o-nada entre ítems**, pero cada ítem sí lo es, y las excepciones
  viajan aparte para que se vean en la respuesta.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence

from opofuente.application.job_service import JobExecution
from opofuente.application.ports import (
    ClassificationRepository,
    ClassifierPort,
    Clock,
    JobQueue,
)
from opofuente.application.read_models import (
    AcceptedClassificationView,
    AcceptedValueView,
    BulkDecisionResult,
    ClassificationRunReport,
    CoverageView,
    DecisionOutcome,
    DuplicateClusterDraft,
    DuplicateClusterView,
    DuplicateMemberView,
    MappingView,
    NodeCoverageView,
    ProposalPage,
    ProposalView,
    ReviewGroupView,
)
from opofuente.domain.classification import (
    ConfidenceBands,
    CoverageType,
    Proposal,
    ProposalStatus,
)
from opofuente.domain.duplicates import DuplicateGroup, find_duplicates
from opofuente.domain.jobs import Job, JobType

logger = logging.getLogger("opofuente.application.classification_service")

#: Sujetos que se clasifican en una pasada cuando el trabajo no dice otra cosa.
DEFAULT_LIMIT = 200

#: Cómo informa una pasada de por dónde va: valor entre 0 y 1 y paso legible para la pantalla.
#: El valor es **relativo a la pasada**; quien llama decide en qué tramo del trabajo cae (DEBT-024).
ProgressReporter = Callable[[float, str], None]

#: Cada cuántos sujetos se informa. Con el corpus real (miles de sujetos) da pasos visibles sin
#: escribir en la base de datos en cada vuelta; con un corpus pequeño siguen viéndose los tramos.
PROGRESS_EVERY = 10

#: Reparto del avance de una pasada: clasificar sujetos, guardar, aplicar y buscar duplicados.
_PHASE_SUBJECTS = 0.7
_PHASE_SAVE = 0.7
_PHASE_APPLY = 0.8
_PHASE_DUPLICATES = 0.9


class ClassificationService:
    """Clasifica, agrupa para revisar, decide (una a una o en lote), deshace y mide cobertura."""

    def __init__(
        self,
        repository: ClassificationRepository,
        engines: Sequence[ClassifierPort],
        clock: Clock,
        jobs: JobQueue,
    ) -> None:
        self._repository = repository
        self._engines = tuple(engines)
        self._clock = clock
        self._jobs = jobs

    # ------------------------------------------------------------------ trabajo

    def enqueue_run(self, *, limit: int | None = None) -> Job:
        """Encola una pasada de clasificación del corpus y devuelve el trabajo.

        Clasificar todo el material es una operación larga —con el corpus real del propietario, 46,7
        segundos— y no puede vivir dentro de una petición: el usuario se queda mirando un botón
        bloqueado y la interfaz no dice en qué va (DEBT-024). Es el mismo camino que ya hacían la
        extracción y el recálculo de claves: se encola, el trabajador lo ejecuta y la pantalla sigue
        el progreso.

        La clave de idempotencia es **una sola para el corpus**: si ya hay una pasada viva, esto
        devuelve esa en lugar de encolar otra, así que pulsar dos veces no clasifica dos veces.
        """
        trabajo, _creado = self._jobs.enqueue(
            job_type=JobType.CLASSIFY_DOCUMENT,
            payload={"limit": limit if limit is not None else DEFAULT_LIMIT},
            now=self._clock.now(),
            idempotency_key="classify_document:corpus",
        )
        logger.info(
            "classification.enqueued",
            extra={"event": "classification_enqueued", "path": trabajo.id},
        )
        return trabajo

    def run_classification_job(self, execution: JobExecution) -> None:
        """Manejador del trabajo `classify_document`: clasifica lo extraído y lo deja para revisar.

        El trabajo es idempotente (volver a ejecutarlo no duplica propuestas) y **nunca** aplica
        nada de forma definitiva: lo que se aplica solo queda `auto_applied_provisional`, visible y
        reversible. Clasificar no es obligatorio para leer el material: si este trabajo no se
        ejecuta, el texto sigue estando y la interfaz dice que no está clasificado.

        El avance no salta de 0,05 a 1 (DEBT-024): la pasada informa de sus tramos —clasificar,
        guardar, aplicar y buscar duplicados— y cada informe es también el punto donde se comprueba
        si han pedido cancelar.
        """
        execution.require_not_cancelled()
        limite = execution.payload.get("limit", DEFAULT_LIMIT)
        limit = limite if isinstance(limite, int) else DEFAULT_LIMIT
        execution.progress(0.05, "clasificando material")

        def informar(valor: float, paso: str) -> None:
            # Entre tramo y tramo es donde se puede parar: cancelar a mitad no deja el trabajo vivo.
            execution.require_not_cancelled()
            execution.progress(0.05 + 0.95 * valor, paso)

        report = self.run(limit=limit, on_progress=informar)
        execution.progress(1.0, report.summary())

    # ------------------------------------------------------------------ clasificar

    def run(
        self,
        *,
        limit: int = 200,
        detect_duplicates: bool = True,
        on_progress: ProgressReporter | None = None,
    ) -> ClassificationRunReport:
        """Ejecuta todos los motores sobre los sujetos y guarda lo que propongan.

        `on_progress` es opcional a propósito: clasificar también se llama desde sitios que no son
        un trabajo —pruebas, herramientas de línea de órdenes— y ahí no hay a quién informar. Cuando
        se pasa, recibe el avance **dentro de la pasada** (0..1) y el paso en palabras.
        """
        sujetos = self._repository.classification_targets(limit=limit)
        propuestas: list[Proposal] = []
        con_senales = 0
        for indice, sujeto in enumerate(sujetos, start=1):
            del_sujeto: list[Proposal] = []
            for motor in self._engines:
                del_sujeto.extend(motor.propose(sujeto))
            if del_sujeto:
                con_senales += 1
            propuestas.extend(del_sujeto)
            if indice % PROGRESS_EVERY == 0 or indice == len(sujetos):
                self._informar(
                    on_progress,
                    _PHASE_SUBJECTS * indice / len(sujetos),
                    f"clasificando material ({indice} de {len(sujetos)})",
                )

        self._informar(on_progress, _PHASE_SAVE, "guardando propuestas")
        creadas, existentes = self._repository.save_proposals(propuestas, now=self._clock.now())
        self._informar(on_progress, _PHASE_APPLY, "aplicando lo que se decide solo")
        aplicadas = self._apply_high_band(propuestas)
        duplicados = 0
        if detect_duplicates:
            self._informar(on_progress, _PHASE_DUPLICATES, "buscando duplicados")
            duplicados = len(self.detect_duplicates(limit=limit))
        self._informar(on_progress, 1.0, "clasificación terminada")

        return ClassificationRunReport(
            subjects=len(sujetos),
            proposals_created=creadas,
            proposals_unchanged=existentes,
            subjects_without_signals=len(sujetos) - con_senales,
            auto_applied=aplicadas,
            duplicates_found=duplicados,
        )

    @staticmethod
    def _informar(on_progress: ProgressReporter | None, value: float, step: str) -> None:
        """Informa del avance si alguien escucha; sin escucha no hay nada que hacer."""
        if on_progress is not None:
            on_progress(value, step)

    def _apply_high_band(self, propuestas: Sequence[Proposal]) -> int:
        """Aplica provisionalmente lo que la banda permite y deja el resto para revisión.

        Solo se aplican las propuestas que **acaban de salir** de un motor y solo si su banda lo
        permite: una propuesta ya aplicada no se vuelve a tocar (su estado lo decide el usuario).
        """
        bandas = ConfidenceBands()
        candidatas = {
            (
                propuesta.subject_type.value,
                propuesta.subject_id,
                propuesta.axis.value,
                propuesta.proposed_value,
            )
            for propuesta in propuestas
            if bandas.decides_itself(propuesta.confidence, axis=propuesta.axis)
        }
        if not candidatas:
            return 0
        pendientes = self._repository.list_proposals(
            status=ProposalStatus.PENDING.value, limit=1000
        )
        aplicadas = 0
        for vista in pendientes.proposals:
            clave = (vista.subject_type, vista.subject_id, vista.axis, vista.proposed_value)
            if clave not in candidatas:
                continue
            resultado = self._repository.decide(
                vista.id,
                status=ProposalStatus.AUTO_APPLIED_PROVISIONAL,
                note="Aplicada provisionalmente: banda alta y eje no crítico",
                now=self._clock.now(),
            )
            if resultado.applied:
                aplicadas += 1
        return aplicadas

    # ------------------------------------------------------------------ consultar

    def list_proposals(
        self,
        *,
        subject_type: str | None = None,
        subject_id: str | None = None,
        axis: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> ProposalPage:
        return self._repository.list_proposals(
            subject_type=subject_type,
            subject_id=subject_id,
            axis=axis,
            status=status,
            limit=limit,
            offset=offset,
        )

    def get_proposal(self, proposal_id: str) -> ProposalView | None:
        return self._repository.get_proposal(proposal_id)

    def accepted_classification(
        self, *, subject_type: str, subject_id: str
    ) -> AcceptedClassificationView:
        """Clasificación vigente de un material: lo aceptado y lo aplicado provisionalmente.

        Se lee de las propuestas porque en S04 no hay documentos lógicos: el valor aceptado vive
        ahí y S05 lo materializará sin reescribir historia. Un eje puede tener varias propuestas
        decididas
        (una aceptada y otra provisional, por ejemplo): manda la aceptada, que es la que decidió el
        usuario.
        """
        pagina = self._repository.list_proposals(
            subject_type=subject_type, subject_id=subject_id, limit=200
        )
        vigentes: dict[str, ProposalView] = {}
        etiqueta: str | None = None
        for propuesta in pagina.proposals:
            if propuesta.status not in {"accepted", "auto_applied_provisional"}:
                continue
            etiqueta = etiqueta or propuesta.subject_label
            actual = vigentes.get(propuesta.axis)
            if actual is None or (
                actual.status != ProposalStatus.ACCEPTED.value
                and propuesta.status == ProposalStatus.ACCEPTED.value
            ):
                vigentes[propuesta.axis] = propuesta
        return AcceptedClassificationView(
            subject_type=subject_type,
            subject_id=subject_id,
            subject_label=etiqueta,
            values=tuple(
                AcceptedValueView(
                    axis=propuesta.axis,
                    value=propuesta.proposed_value,
                    value_label=propuesta.value_label,
                    status=propuesta.status,
                    confidence=propuesta.confidence,
                    is_critical=propuesta.is_critical,
                    decided_at=propuesta.decided_at,
                )
                for _, propuesta in sorted(vigentes.items())
            ),
        )

    def review_groups(self) -> tuple[ReviewGroupView, ...]:
        return self._repository.pending_groups()

    # ------------------------------------------------------------------ decidir

    def decide(
        self,
        proposal_id: str,
        *,
        decision: str,
        note: str | None = None,
        override_value: str | None = None,
        coverage_type: CoverageType = CoverageType.PARTIAL,
    ) -> DecisionOutcome:
        return self._repository.decide(
            proposal_id,
            status=ProposalStatus(decision),
            note=note,
            override_value=override_value,
            coverage_type=coverage_type,
            now=self._clock.now(),
        )

    def bulk_decide(
        self,
        proposal_ids: Sequence[str],
        *,
        decision: str,
        note: str | None = None,
        overrides: Mapping[str, str] | None = None,
        excluded: Sequence[str] = (),
    ) -> BulkDecisionResult:
        """Decide en lote respetando excepciones: lo excluido no se toca y se informa aparte."""
        excluidas = tuple(excluded)
        resultados: list[DecisionOutcome] = []
        for proposal_id in proposal_ids:
            if proposal_id in excluidas:
                continue
            override = (overrides or {}).get(proposal_id)
            resultados.append(
                self.decide(
                    proposal_id,
                    decision=decision,
                    note=note,
                    override_value=override,
                )
            )
        return BulkDecisionResult(outcomes=tuple(resultados), excluded=excluidas)

    def undo(self, proposal_id: str) -> DecisionOutcome:
        return self._repository.undo(proposal_id, now=self._clock.now())

    # ------------------------------------------------------------------ cobertura

    def mappings(
        self, *, subject_type: str | None = None, subject_id: str | None = None
    ) -> tuple[MappingView, ...]:
        return self._repository.list_mappings(subject_type=subject_type, subject_id=subject_id)

    def delete_mapping(self, mapping_id: str) -> bool:
        return self._repository.delete_mapping(mapping_id, now=self._clock.now())

    def coverage(self, *, convocation_code: str) -> CoverageView:
        return self._repository.coverage(convocation_code=convocation_code)

    def node_coverage(self, node_id: str) -> NodeCoverageView | None:
        return self._repository.node_coverage(node_id)

    # ------------------------------------------------------------------ duplicados

    def detect_duplicates(self, *, limit: int = 500) -> tuple[DuplicateClusterView, ...]:
        """Detecta el mismo texto y los casi duplicados y los guarda como clusters abiertos."""
        documentos = self._repository.text_documents(limit=limit)
        grupos: tuple[DuplicateGroup, ...] = find_duplicates(documentos)
        if not grupos:
            return ()
        borradores = [
            DuplicateClusterDraft(
                kind=grupo.kind,
                relation=grupo.relation,
                signature=grupo.signature,
                members=tuple(
                    DuplicateMemberView(
                        subject_type=subject_type,
                        subject_id=subject_id,
                        subject_label=label,
                        similarity=similitud,
                        is_representative=indice == 0,
                    )
                    for indice, (subject_type, subject_id, label, similitud) in enumerate(
                        grupo.members
                    )
                ),
            )
            for grupo in grupos
        ]
        return self._repository.record_text_duplicates(borradores, now=self._clock.now())

    def list_duplicate_clusters(
        self, *, status: str | None = None
    ) -> tuple[DuplicateClusterView, ...]:
        return self._repository.list_duplicate_clusters(status=status)

    def resolve_duplicate_cluster(
        self, cluster_id: str, *, relation: str, note: str | None = None
    ) -> DuplicateClusterView | None:
        return self._repository.resolve_duplicate_cluster(
            cluster_id, relation=relation, note=note, now=self._clock.now()
        )
