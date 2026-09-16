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

from collections.abc import Mapping, Sequence

from opofuente.application.job_service import JobExecution
from opofuente.application.ports import ClassificationRepository, ClassifierPort, Clock
from opofuente.application.read_models import (
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

#: Sujetos que se clasifican en una pasada cuando el trabajo no dice otra cosa.
DEFAULT_LIMIT = 200


class ClassificationService:
    """Clasifica, agrupa para revisar, decide (una a una o en lote), deshace y mide cobertura."""

    def __init__(
        self,
        repository: ClassificationRepository,
        engines: Sequence[ClassifierPort],
        clock: Clock,
    ) -> None:
        self._repository = repository
        self._engines = tuple(engines)
        self._clock = clock

    # ------------------------------------------------------------------ trabajo

    def run_classification_job(self, execution: JobExecution) -> None:
        """Manejador del trabajo `classify_document`: clasifica lo extraído y lo deja para revisar.

        El trabajo es idempotente (volver a ejecutarlo no duplica propuestas) y **nunca** aplica
        nada de forma definitiva: lo que se aplica solo queda `auto_applied_provisional`, visible y
        reversible. Clasificar no es obligatorio para leer el material: si este trabajo no se
        ejecuta, el texto sigue estando y la interfaz dice que no está clasificado.
        """
        execution.require_not_cancelled()
        limite = execution.payload.get("limit", DEFAULT_LIMIT)
        limit = limite if isinstance(limite, int) else DEFAULT_LIMIT
        execution.progress(0.05, "clasificando material")
        report = self.run(limit=limit)
        execution.progress(1.0, report.summary())

    # ------------------------------------------------------------------ clasificar

    def run(self, *, limit: int = 200, detect_duplicates: bool = True) -> ClassificationRunReport:
        """Ejecuta todos los motores sobre los sujetos y guarda lo que propongan."""
        sujetos = self._repository.classification_targets(limit=limit)
        propuestas: list[Proposal] = []
        con_senales = 0
        for sujeto in sujetos:
            del_sujeto: list[Proposal] = []
            for motor in self._engines:
                del_sujeto.extend(motor.propose(sujeto))
            if del_sujeto:
                con_senales += 1
            propuestas.extend(del_sujeto)

        creadas, existentes = self._repository.save_proposals(propuestas, now=self._clock.now())
        aplicadas = self._apply_high_band(propuestas)
        duplicados = 0
        if detect_duplicates:
            duplicados = len(self.detect_duplicates(limit=limit))

        return ClassificationRunReport(
            subjects=len(sujetos),
            proposals_created=creadas,
            proposals_unchanged=existentes,
            subjects_without_signals=len(sujetos) - con_senales,
            auto_applied=aplicadas,
            duplicates_found=duplicados,
        )

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
