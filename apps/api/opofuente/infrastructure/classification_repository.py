"""Repositorio SQLAlchemy de clasificación, revisión, cobertura, duplicados y auditoría (S04).

Decisiones que se ven en el código y conviene tener claras:

- **Cada decisión es una transacción.** Decidir una propuesta escribe su estado, su efecto (el mapeo
  cuando el eje es el tema) y su evento de auditoría en la misma sesión: o queda todo, o no queda
  nada. Por eso el lote no es todo-o-nada entre ítems, pero cada ítem sí lo es.
- **Una propuesta aceptada no cambia el material**: en S04 no existen todavía documentos lógicos
  (llegan en S05), así que el valor aceptado se lee de la propia propuesta y S05 lo materializará en
  `logical_documents` sin reescribir la historia.
- **Rechazar retira el efecto.** Si un mapeo salió de esa propuesta, se retira: dejar cobertura de
  rechazado sería mentir con números.
- **Nada de borrado silencioso de propuestas.** Una propuesta nueva sobre el mismo sujeto y eje
  sustituye a la anterior **pendiente** (queda `superseded`, con fecha y motivo); una propuesta ya
  aplicada provisionalmente no se pisa: se revisa o se deshace.
- **El deshacer no borra historia**: revierte el estado, retira el mapeo que salió de esa decisión y
  deja su propio evento de auditoría apuntando a la decisión deshecha.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.read_models import (
    AlternativeView,
    AuditEventView,
    CoverageNodeView,
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
    CRITICAL_AXES,
    AuthorityTier,
    Axis,
    ClassificationSubject,
    ConfidenceBands,
    CoverageType,
    DocumentType,
    MappingStatus,
    ProfileCandidate,
    Proposal,
    ProposalStatus,
    RightsStatus,
    SubjectType,
    TopicCandidate,
    coverage_counts_as_accepted,
    decision_allowed,
    group_key,
    value_matches_axis,
)
from opofuente.domain.duplicates import TextDocument
from opofuente.domain.extraction import Quality
from opofuente.infrastructure.db_models import (
    AuditEventRecord,
    ClassificationProposalRecord,
    ConvocationVersionRecord,
    CurriculumMappingRecord,
    CurriculumNodeRecord,
    DuplicateClusterMemberRecord,
    DuplicateClusterRecord,
    ExtractedRepresentationRecord,
    IngestionItemRecord,
    ItemRepresentationRecord,
    OppositionRecord,
    SourceArtifactRecord,
)
from opofuente.infrastructure.representation_store import RepresentationStore

#: Extracto de texto que se entrega a un motor: el principio del documento basta para las señales.
EXCERPT_CHARS = 20_000

#: Orden de calidad de una representación, de mejor a peor: decide con qué texto se clasifica.
_QUALITY_ORDER = {
    Quality.GOOD.value: 0,
    Quality.USABLE_WITH_WARNINGS.value: 1,
    Quality.OCR_UNREVIEWED.value: 2,
    Quality.POOR.value: 3,
    Quality.FAILED.value: 4,
}

#: Acciones de auditoría que se pueden deshacer (una decisión). El propio deshacer no se deshace.
_DECISION_ACTIONS = (
    "proposal.accepted",
    "proposal.rejected",
    "proposal.auto_applied_provisional",
)


def _new_id() -> str:
    return str(uuid4())


def _json_list(values: Iterable[str]) -> str:
    return json.dumps(list(values), ensure_ascii=False)


def _load_str_list(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    try:
        datos = json.loads(raw)
    except json.JSONDecodeError:
        return ()
    if not isinstance(datos, list):
        return ()
    return tuple(str(item) for item in datos)


def _load_alternatives(raw: str | None) -> tuple[AlternativeView, ...]:
    if not raw:
        return ()
    try:
        datos = json.loads(raw)
    except json.JSONDecodeError:
        return ()
    if not isinstance(datos, list):
        return ()
    alternativas: list[AlternativeView] = []
    for item in datos:
        if not isinstance(item, dict):
            continue
        valor = item.get("value")
        confianza = item.get("confidence")
        if isinstance(valor, str) and isinstance(confianza, int | float):
            alternativas.append(AlternativeView(value=valor, confidence=float(confianza)))
    return tuple(alternativas)


def _quality(valor: str | None) -> Quality | None:
    if valor is None:
        return None
    try:
        return Quality(valor)
    except ValueError:
        return None


def value_label(axis: str, valor: str) -> str | None:
    """Etiqueta legible de un valor propuesto, para los vocabularios cerrados."""
    if axis == Axis.DOCUMENT_TYPE.value:
        return _DOCUMENT_TYPE_LABELS.get(valor)
    if axis == Axis.AUTHORITY.value:
        return _AUTHORITY_LABELS.get(valor)
    if axis == Axis.RIGHTS.value:
        return _RIGHTS_LABELS.get(valor)
    return None


_DOCUMENT_TYPE_LABELS = {
    DocumentType.CONVOCATION.value: "Convocatoria",
    DocumentType.CURRICULUM.value: "Temario o programa",
    DocumentType.LAW_OR_REGULATION.value: "Norma legal",
    DocumentType.OFFICIAL_TECHNICAL.value: "Documentación técnica oficial",
    DocumentType.PRIVATE_SYLLABUS.value: "Temario particular",
    DocumentType.PERSONAL_NOTES.value: "Apuntes personales",
    DocumentType.OFFICIAL_EXAM.value: "Examen oficial",
    DocumentType.ANSWER_KEY.value: "Plantilla de respuestas",
    DocumentType.PRIVATE_QUESTION_BANK.value: "Banco de preguntas privado",
    DocumentType.PRACTICAL_CASE.value: "Caso práctico",
    DocumentType.FLASHCARDS.value: "Tarjetas de repaso",
    DocumentType.COMMUNITY_MATERIAL.value: "Material de la comunidad",
    DocumentType.UNKNOWN.value: "Sin determinar",
}

_AUTHORITY_LABELS = {
    AuthorityTier.A.value: "Publicación oficial",
    AuthorityTier.B.value: "Administración pública",
    AuthorityTier.C.value: "Tercero identificable",
    AuthorityTier.D.value: "Origen comunitario o anónimo",
    AuthorityTier.UNKNOWN.value: "Sin determinar",
}

_RIGHTS_LABELS = {
    RightsStatus.REUSE_WITH_CONDITIONS.value: "Reutilización con condiciones",
    RightsStatus.PRIVATE_USE_ONLY.value: "Solo uso privado",
    RightsStatus.RIGHTS_DOCUMENT.value: "Documento de condiciones de uso",
    RightsStatus.UNKNOWN.value: "Derechos sin determinar",
}


class SqlAlchemyClassificationRepository:
    """Clasificación y revisión sobre SQLite, con el texto leído del almacén de representaciones."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        store: RepresentationStore,
        *,
        bands: ConfidenceBands | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._store = store
        self._bands = bands or ConfidenceBands()

    # ------------------------------------------------------------------ insumos

    def classification_targets(self, *, limit: int) -> tuple[ClassificationSubject, ...]:
        """Sujetos clasificables: cada representación y cada artefacto con su mejor texto."""
        with self._session_factory() as session:
            perfiles = self._profile_candidates(session)
            filas = session.execute(
                select(ExtractedRepresentationRecord, SourceArtifactRecord)
                .join(
                    SourceArtifactRecord,
                    SourceArtifactRecord.id == ExtractedRepresentationRecord.artifact_id,
                )
                .where(ExtractedRepresentationRecord.status == "extracted")
                .order_by(
                    ExtractedRepresentationRecord.created_at, ExtractedRepresentationRecord.id
                )
                .limit(limit)
            ).all()
            enlaces = self._item_links(session, [representacion.id for representacion, _ in filas])

        sujetos: list[ClassificationSubject] = []
        mejores: dict[str, tuple[tuple[int, int], ClassificationSubject]] = {}
        for representacion, artefacto in filas:
            entrada = enlaces.get(representacion.id)
            original_name = entrada.original_name if entrada is not None else None
            origin_type = entrada.origin_type if entrada is not None else None
            origin_display = entrada.origin_display if entrada is not None else None
            texto = self._excerpt(representacion)
            sujetos.append(
                ClassificationSubject(
                    subject_type=SubjectType.REPRESENTATION,
                    subject_id=representacion.id,
                    text=texto,
                    original_name=original_name,
                    media_type=artefacto.media_type,
                    origin_type=origin_type,
                    origin_display=origin_display,
                    profiles=perfiles,
                )
            )
            # El artefacto se clasifica con su representación de mejor calidad y más texto: es la
            # misma información que vería una persona abriendo el material.
            clave = (_QUALITY_ORDER.get(representacion.quality, 9), -len(texto))
            anterior = mejores.get(artefacto.id)
            if anterior is None or clave < anterior[0]:
                mejores[artefacto.id] = (
                    clave,
                    ClassificationSubject(
                        subject_type=SubjectType.ARTIFACT,
                        subject_id=artefacto.id,
                        text=texto,
                        original_name=original_name,
                        media_type=artefacto.media_type,
                        origin_type=origin_type,
                        origin_display=origin_display,
                        profiles=perfiles,
                    ),
                )
        sujetos.extend(sujeto for _, sujeto in mejores.values())
        return tuple(sujetos)

    def text_documents(self, *, limit: int) -> tuple[TextDocument, ...]:
        """Textos comparables para los duplicados: un documento por artefacto, con su mejor texto.

        Se compara por artefacto y no por representación: el duplicado que le importa al usuario
        es el **material** repetido, no que un mismo PDF tenga texto nativo y OCR.
        """
        documentos: list[TextDocument] = []
        for sujeto in self.classification_targets(limit=limit):
            if sujeto.subject_type is not SubjectType.ARTIFACT:
                continue
            documentos.append(
                TextDocument(
                    subject_type=sujeto.subject_type.value,
                    subject_id=sujeto.subject_id,
                    label=sujeto.original_name or sujeto.origin_display,
                    text=sujeto.text,
                )
            )
        documentos.sort(key=lambda documento: (documento.subject_type, documento.subject_id))
        return tuple(documentos)

    def _excerpt(self, representacion: ExtractedRepresentationRecord) -> str:
        if not representacion.text_storage_key:
            return ""
        try:
            return self._store.read(representacion.text_storage_key, limit=EXCERPT_CHARS).text
        except OSError:
            # Un texto que ya no está en el almacén no sostiene propuestas: se clasifica
            # con lo que sí consta (nombre y procedencia) en lugar de tumbar la pasada entera.
            return ""

    def _profile_candidates(self, session: Session) -> tuple[ProfileCandidate, ...]:
        """Perfiles con los nodos de su convocatoria: lo que un motor necesita para el tema."""
        candidatos: list[ProfileCandidate] = []
        oposiciones = session.execute(
            select(OppositionRecord).order_by(OppositionRecord.code)
        ).scalars()
        for oposicion in oposiciones:
            convocatoria = session.execute(
                select(ConvocationVersionRecord)
                .where(ConvocationVersionRecord.opposition_id == oposicion.id)
                .order_by(ConvocationVersionRecord.code)
                .limit(1)
            ).scalar_one_or_none()
            nodos: tuple[TopicCandidate, ...] = ()
            if convocatoria is not None:
                nodos = self._nodes_of(session, convocatoria.id)
            candidatos.append(
                ProfileCandidate(
                    opposition_code=oposicion.code,
                    opposition_name=oposicion.name,
                    convocation_code=convocatoria.code if convocatoria is not None else "",
                    topics=nodos,
                )
            )
        return tuple(candidatos)

    @staticmethod
    def _nodes_of(session: Session, convocation_id: str) -> tuple[TopicCandidate, ...]:
        filas = (
            session.execute(
                select(CurriculumNodeRecord)
                .where(CurriculumNodeRecord.convocation_version_id == convocation_id)
                .order_by(CurriculumNodeRecord.path)
            )
            .scalars()
            .all()
        )
        return tuple(
            TopicCandidate(node_id=fila.id, path=fila.path, title=fila.title, depth=fila.depth)
            for fila in filas
        )

    @staticmethod
    def _item_links(
        session: Session, representation_ids: Sequence[str]
    ) -> dict[str, IngestionItemRecord]:
        if not representation_ids:
            return {}
        filas = session.execute(
            select(ItemRepresentationRecord.representation_id, IngestionItemRecord)
            .join(IngestionItemRecord, IngestionItemRecord.id == ItemRepresentationRecord.item_id)
            .where(ItemRepresentationRecord.representation_id.in_(representation_ids))
            .order_by(IngestionItemRecord.position)
        ).all()
        enlaces: dict[str, IngestionItemRecord] = {}
        for representation_id, entrada in filas:
            enlaces.setdefault(str(representation_id), entrada)
        return enlaces

    # ------------------------------------------------------------------ propuestas

    def save_proposals(self, proposals: Sequence[Proposal], *, now: datetime) -> tuple[int, int]:
        """Guarda las propuestas de una pasada, tolerando que otro escritor se adelante.

        El worker clasifica el material en cuanto se extrae (`JobType.CLASSIFY_DOCUMENT`) y una
        pasada explícita puede coincidir con él: las dos guardan las **mismas** propuestas. Cuando
        eso pasa, la propuesta ya existe y eso **no** es un fallo de quien la pidió, así que el
        choque de unicidad se reintenta una vez (en el segundo intento la deduplicación ya la ve y
        solo entra lo que faltaba) en lugar de devolver un 500. Si el segundo intento también choca,
        el problema es real y se propaga en vez de esconderse.
        """
        intentos = 0
        while True:
            intentos += 1
            with self._session_factory() as session:
                creadas, existentes = self._guardar_propuestas(session, proposals, now=now)
                try:
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    if intentos >= 2:
                        raise
                    continue
            return creadas, existentes

    def _guardar_propuestas(
        self, session: Session, proposals: Sequence[Proposal], *, now: datetime
    ) -> tuple[int, int]:
        """Deduplica, retira las pendientes que sustituye y añade lo nuevo. No confirma nada."""
        creadas = 0
        existentes = 0
        for propuesta in proposals:
            ya = session.execute(
                select(ClassificationProposalRecord.id).where(
                    ClassificationProposalRecord.subject_type == propuesta.subject_type.value,
                    ClassificationProposalRecord.subject_id == propuesta.subject_id,
                    ClassificationProposalRecord.axis == propuesta.axis.value,
                    ClassificationProposalRecord.engine_name == propuesta.engine_name,
                    ClassificationProposalRecord.engine_version == propuesta.engine_version,
                    ClassificationProposalRecord.proposed_value == propuesta.proposed_value,
                )
            ).first()
            if ya is not None:
                existentes += 1
                continue
            pendientes = (
                session.execute(
                    select(ClassificationProposalRecord).where(
                        ClassificationProposalRecord.subject_type == propuesta.subject_type.value,
                        ClassificationProposalRecord.subject_id == propuesta.subject_id,
                        ClassificationProposalRecord.axis == propuesta.axis.value,
                        ClassificationProposalRecord.status == ProposalStatus.PENDING.value,
                    )
                )
                .scalars()
                .all()
            )
            for anterior in pendientes:
                anterior.status = ProposalStatus.SUPERSEDED.value
                anterior.decided_at = now
                anterior.decision_note = "Sustituida por una propuesta nueva del mismo motor"
            session.add(
                ClassificationProposalRecord(
                    id=_new_id(),
                    subject_type=propuesta.subject_type.value,
                    subject_id=propuesta.subject_id,
                    axis=propuesta.axis.value,
                    proposed_value=propuesta.proposed_value,
                    confidence=propuesta.confidence,
                    alternatives_json=json.dumps(
                        [
                            {"value": alternativa.value, "confidence": alternativa.confidence}
                            for alternativa in propuesta.alternatives
                        ],
                        ensure_ascii=False,
                    ),
                    evidence_json=_json_list(propuesta.evidence),
                    engine_name=propuesta.engine_name,
                    engine_version=propuesta.engine_version,
                    status=ProposalStatus.PENDING.value,
                    created_at=now,
                    decided_at=None,
                    decision_note=None,
                )
            )
            creadas += 1
        return creadas, existentes

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
        filtros = []
        if subject_type is not None:
            filtros.append(ClassificationProposalRecord.subject_type == subject_type)
        if subject_id is not None:
            filtros.append(ClassificationProposalRecord.subject_id == subject_id)
        if axis is not None:
            filtros.append(ClassificationProposalRecord.axis == axis)
        if status is not None:
            filtros.append(ClassificationProposalRecord.status == status)
        with self._session_factory() as session:
            total = session.execute(
                select(func.count()).select_from(ClassificationProposalRecord).where(*filtros)
            ).scalar_one()
            filas = (
                session.execute(
                    select(ClassificationProposalRecord)
                    .where(*filtros)
                    .order_by(
                        ClassificationProposalRecord.created_at.desc(),
                        ClassificationProposalRecord.id,
                    )
                    .limit(limit)
                    .offset(offset)
                )
                .scalars()
                .all()
            )
            etiquetas = self._subject_labels(
                session, [(fila.subject_type, fila.subject_id) for fila in filas]
            )
            valores = self._value_labels(session, filas)
        return ProposalPage(
            proposals=tuple(self._proposal_view(fila, etiquetas, valores) for fila in filas),
            total=int(total),
            limit=limit,
            offset=offset,
        )

    def get_proposal(self, proposal_id: str) -> ProposalView | None:
        with self._session_factory() as session:
            fila = session.get(ClassificationProposalRecord, proposal_id)
            if fila is None:
                return None
            etiquetas = self._subject_labels(session, [(fila.subject_type, fila.subject_id)])
            valores = self._value_labels(session, [fila])
            return self._proposal_view(fila, etiquetas, valores)

    def pending_groups(self) -> tuple[ReviewGroupView, ...]:
        with self._session_factory() as session:
            filas = (
                session.execute(
                    select(ClassificationProposalRecord)
                    .where(ClassificationProposalRecord.status == ProposalStatus.PENDING.value)
                    .order_by(
                        ClassificationProposalRecord.axis,
                        ClassificationProposalRecord.proposed_value,
                        ClassificationProposalRecord.confidence.desc(),
                    )
                )
                .scalars()
                .all()
            )
            valores = self._value_labels(session, filas)

        agrupadas: dict[str, list[ClassificationProposalRecord]] = defaultdict(list)
        for fila in filas:
            clave = group_key(SubjectType(fila.subject_type), Axis(fila.axis), fila.proposed_value)
            agrupadas[clave].append(fila)

        grupos: list[ReviewGroupView] = []
        for clave, miembros in agrupadas.items():
            primero = miembros[0]
            confianzas = [fila.confidence for fila in miembros]
            grupos.append(
                ReviewGroupView(
                    key=clave,
                    subject_type=primero.subject_type,
                    axis=primero.axis,
                    proposed_value=primero.proposed_value,
                    label=valores.get((primero.axis, primero.proposed_value))
                    or primero.proposed_value,
                    proposal_ids=tuple(fila.id for fila in miembros),
                    min_confidence=min(confianzas),
                    max_confidence=max(confianzas),
                    is_critical=Axis(primero.axis) in CRITICAL_AXES,
                )
            )
        return tuple(sorted(grupos, key=lambda grupo: (-grupo.max_confidence, grupo.key)))

    # ------------------------------------------------------------------ decisiones

    def decide(
        self,
        proposal_id: str,
        *,
        status: ProposalStatus,
        note: str | None,
        now: datetime,
        override_value: str | None = None,
        coverage_type: CoverageType = CoverageType.PARTIAL,
        actor: str = "local",
    ) -> DecisionOutcome:
        with self._session_factory() as session:
            fila = session.get(ClassificationProposalRecord, proposal_id)
            if fila is None:
                return DecisionOutcome(
                    proposal_id=proposal_id,
                    status="missing",
                    applied=False,
                    reason="La propuesta no existe",
                )
            actual = ProposalStatus(fila.status)
            if not decision_allowed(actual, status):
                return DecisionOutcome(
                    proposal_id=proposal_id,
                    status=fila.status,
                    applied=False,
                    reason=f"No se puede pasar de «{actual.value}» a «{status.value}»",
                )

            valor = override_value or fila.proposed_value
            if override_value is not None and not value_matches_axis(
                Axis(fila.axis), override_value
            ):
                return DecisionOutcome(
                    proposal_id=proposal_id,
                    status=fila.status,
                    applied=False,
                    reason=f"«{override_value}» no es un valor válido para el eje {fila.axis}",
                )

            nodo: CurriculumNodeRecord | None = None
            aplica_mapeo = Axis(fila.axis) is Axis.TOPIC and status in {
                ProposalStatus.ACCEPTED,
                ProposalStatus.AUTO_APPLIED_PROVISIONAL,
            }
            if aplica_mapeo:
                nodo = session.execute(
                    select(CurriculumNodeRecord).where(CurriculumNodeRecord.path == valor).limit(1)
                ).scalar_one_or_none()
                if nodo is None:
                    return DecisionOutcome(
                        proposal_id=proposal_id,
                        status=fila.status,
                        applied=False,
                        reason=f"El nodo «{valor}» no está en el programa sembrado",
                    )

            anterior = self._estado_previo(session, fila, nodo)
            fila.proposed_value = valor
            fila.status = status.value
            fila.decided_at = now
            fila.decision_note = note

            mapeo: CurriculumMappingRecord | None = None
            if nodo is not None:
                mapeo = self._upsert_mapping(
                    session,
                    fila=fila,
                    nodo=nodo,
                    status=status,
                    coverage_type=coverage_type,
                    now=now,
                )
            elif status is ProposalStatus.REJECTED:
                self._remove_mappings(session, fila.id)

            evento = self._audit(
                session,
                actor=actor,
                action=f"proposal.{status.value}",
                object_type="classification_proposal",
                object_id=fila.id,
                before=anterior,
                after={
                    "status": fila.status,
                    "proposed_value": fila.proposed_value,
                    "mapping_id": mapeo.id if mapeo is not None else None,
                },
                now=now,
            )
            session.commit()
            return DecisionOutcome(
                proposal_id=fila.id,
                status=fila.status,
                applied=True,
                mapping_id=mapeo.id if mapeo is not None else None,
                audit_event_id=evento,
            )

    def undo(self, proposal_id: str, *, now: datetime, actor: str = "local") -> DecisionOutcome:
        with self._session_factory() as session:
            fila = session.get(ClassificationProposalRecord, proposal_id)
            if fila is None:
                # El contrato llama a esta ruta `/classification-decisions/{id}/undo`: si llega
                # el identificador de una **decisión** (su evento de auditoría), se resuelve aquí
                # la propuesta sobre la que se tomó. Así la interfaz puede deshacer con lo que le
                # devolvió la propia decisión, sin manejar dos identificadores distintos.
                decision = session.get(AuditEventRecord, proposal_id)
                if decision is not None and decision.object_type == "classification_proposal":
                    fila = session.get(ClassificationProposalRecord, decision.object_id)
            if fila is None:
                return DecisionOutcome(
                    proposal_id=proposal_id,
                    status="missing",
                    applied=False,
                    reason="La propuesta no existe",
                )
            ultimo = session.execute(
                select(AuditEventRecord)
                .where(
                    AuditEventRecord.object_type == "classification_proposal",
                    AuditEventRecord.object_id == fila.id,
                    AuditEventRecord.action.in_(_DECISION_ACTIONS),
                )
                .order_by(AuditEventRecord.created_at.desc(), AuditEventRecord.id.desc())
                .limit(1)
            ).scalar_one_or_none()
            if ultimo is None:
                return DecisionOutcome(
                    proposal_id=proposal_id,
                    status=fila.status,
                    applied=False,
                    reason="No hay ninguna decisión que deshacer",
                )
            anterior = self._estado_previo(session, fila, None)
            previo = _estado_auditado(ultimo.before_json)
            fila.status = str(previo.get("status") or ProposalStatus.PENDING.value)
            fila.proposed_value = str(previo.get("proposed_value") or fila.proposed_value)
            fila.decided_at = _fecha(previo.get("decided_at"))
            fila.decision_note = _texto(previo.get("decision_note"))
            # El efecto se devuelve igual que el estado: el mapeo que había antes se restaura (o se
            # retira si antes no había ninguno). Deshacer no puede dejar cobertura de algo deshecho
            # ni borrar la cobertura provisional que ya existía.
            retirados = self._restaurar_efecto(session, fila, previo)
            evento = self._audit(
                session,
                actor=actor,
                action="proposal.undo",
                object_type="classification_proposal",
                object_id=fila.id,
                before=anterior,
                after={
                    "status": fila.status,
                    "proposed_value": fila.proposed_value,
                    "mappings_removed": retirados,
                    "undone_event": ultimo.id,
                },
                now=now,
            )
            session.commit()
            return DecisionOutcome(
                proposal_id=fila.id,
                status=fila.status,
                applied=True,
                audit_event_id=evento,
            )

    def last_decision_event(self, proposal_id: str) -> AuditEventView | None:
        with self._session_factory() as session:
            fila = session.execute(
                select(AuditEventRecord)
                .where(
                    AuditEventRecord.object_type == "classification_proposal",
                    AuditEventRecord.object_id == proposal_id,
                    AuditEventRecord.action.in_(_DECISION_ACTIONS),
                )
                .order_by(AuditEventRecord.created_at.desc(), AuditEventRecord.id.desc())
                .limit(1)
            ).scalar_one_or_none()
            if fila is None:
                return None
            return AuditEventView(
                id=fila.id,
                actor=fila.actor,
                action=fila.action,
                object_type=fila.object_type,
                object_id=fila.object_id,
                created_at=fila.created_at,
                before=json.loads(fila.before_json or "{}"),
                after=json.loads(fila.after_json or "{}"),
            )

    def _upsert_mapping(
        self,
        session: Session,
        *,
        fila: ClassificationProposalRecord,
        nodo: CurriculumNodeRecord,
        status: ProposalStatus,
        coverage_type: CoverageType,
        now: datetime,
    ) -> CurriculumMappingRecord:
        estado = (
            MappingStatus.ACCEPTED
            if status is ProposalStatus.ACCEPTED
            else MappingStatus.PROVISIONAL
        )
        existente = session.execute(
            select(CurriculumMappingRecord).where(
                CurriculumMappingRecord.curriculum_node_id == nodo.id,
                CurriculumMappingRecord.subject_type == fila.subject_type,
                CurriculumMappingRecord.subject_id == fila.subject_id,
            )
        ).scalar_one_or_none()
        if existente is None:
            existente = CurriculumMappingRecord(
                id=_new_id(),
                curriculum_node_id=nodo.id,
                subject_type=fila.subject_type,
                subject_id=fila.subject_id,
                coverage_type=coverage_type.value,
                depth=nodo.depth,
                confidence=fila.confidence,
                status=estado.value,
                source_proposal_id=fila.id,
                created_at=now,
                approved_at=now if estado is MappingStatus.ACCEPTED else None,
            )
            session.add(existente)
            return existente
        existente.coverage_type = coverage_type.value
        existente.depth = nodo.depth
        existente.confidence = fila.confidence
        existente.status = estado.value
        existente.source_proposal_id = fila.id
        existente.approved_at = now if estado is MappingStatus.ACCEPTED else None
        return existente

    @staticmethod
    def _estado_previo(
        session: Session,
        fila: ClassificationProposalRecord,
        nodo: CurriculumNodeRecord | None,
    ) -> dict[str, object]:
        """Estado **y efecto** antes de decidir: lo que hay que devolver al deshacer.

        Se guarda en el evento de auditoría porque deshacer tiene que restaurar lo que había, no
        adivinar: sin esto, deshacer una aceptación que venía de una aplicación provisional dejaba
        propuesta en «pendiente» y borraba el mapeo provisional que ya existía.
        """
        mapeo = None
        if nodo is not None:
            mapeo = session.execute(
                select(CurriculumMappingRecord).where(
                    CurriculumMappingRecord.curriculum_node_id == nodo.id,
                    CurriculumMappingRecord.subject_type == fila.subject_type,
                    CurriculumMappingRecord.subject_id == fila.subject_id,
                )
            ).scalar_one_or_none()
        return {
            "status": fila.status,
            "proposed_value": fila.proposed_value,
            "decided_at": fila.decided_at.isoformat() if fila.decided_at is not None else None,
            "decision_note": fila.decision_note,
            "mapping_id": mapeo.id if mapeo is not None else None,
            "mapping_status": mapeo.status if mapeo is not None else None,
            "mapping_coverage": mapeo.coverage_type if mapeo is not None else None,
            "mapping_approved_at": (
                mapeo.approved_at.isoformat()
                if mapeo is not None and mapeo.approved_at is not None
                else None
            ),
        }

    @staticmethod
    def _restaurar_efecto(
        session: Session, fila: ClassificationProposalRecord, previo: Mapping[str, object]
    ) -> int:
        """Devuelve los mapeos al estado anterior y retira los que creó la decisión deshecha."""
        previo_id = previo.get("mapping_id")
        filas = (
            session.execute(
                select(CurriculumMappingRecord).where(
                    CurriculumMappingRecord.source_proposal_id == fila.id
                )
            )
            .scalars()
            .all()
        )
        retirados = 0
        for mapeo in filas:
            if previo_id is not None and mapeo.id == str(previo_id):
                mapeo.status = str(previo.get("mapping_status") or mapeo.status)
                cobertura = previo.get("mapping_coverage")
                if cobertura is not None:
                    mapeo.coverage_type = str(cobertura)
                mapeo.approved_at = _fecha(previo.get("mapping_approved_at"))
                continue
            session.delete(mapeo)
            retirados += 1
        return retirados

    @staticmethod
    def _remove_mappings(session: Session, proposal_id: str) -> int:
        filas = (
            session.execute(
                select(CurriculumMappingRecord).where(
                    CurriculumMappingRecord.source_proposal_id == proposal_id
                )
            )
            .scalars()
            .all()
        )
        for fila in filas:
            session.delete(fila)
        return len(filas)

    # ------------------------------------------------------------------ mapeos y cobertura

    def list_mappings(
        self, *, subject_type: str | None = None, subject_id: str | None = None
    ) -> tuple[MappingView, ...]:
        filtros = []
        if subject_type is not None:
            filtros.append(CurriculumMappingRecord.subject_type == subject_type)
        if subject_id is not None:
            filtros.append(CurriculumMappingRecord.subject_id == subject_id)
        with self._session_factory() as session:
            filas = session.execute(
                select(CurriculumMappingRecord, CurriculumNodeRecord)
                .join(
                    CurriculumNodeRecord,
                    CurriculumNodeRecord.id == CurriculumMappingRecord.curriculum_node_id,
                )
                .where(*filtros)
                .order_by(CurriculumNodeRecord.path)
            ).all()
            etiquetas = self._subject_labels(
                session, [(mapeo.subject_type, mapeo.subject_id) for mapeo, _ in filas]
            )
        return tuple(
            MappingView(
                id=mapeo.id,
                node_id=nodo.id,
                node_path=nodo.path,
                node_title=nodo.title,
                node_depth=nodo.depth,
                subject_type=mapeo.subject_type,
                subject_id=mapeo.subject_id,
                subject_label=etiquetas.get((mapeo.subject_type, mapeo.subject_id)),
                coverage_type=mapeo.coverage_type,
                depth=mapeo.depth,
                confidence=mapeo.confidence,
                status=mapeo.status,
                source_proposal_id=mapeo.source_proposal_id,
                approved_at=mapeo.approved_at,
            )
            for mapeo, nodo in filas
        )

    def delete_mapping(self, mapping_id: str, *, now: datetime, actor: str = "local") -> bool:
        with self._session_factory() as session:
            fila = session.get(CurriculumMappingRecord, mapping_id)
            if fila is None:
                return False
            anterior = {
                "node_id": fila.curriculum_node_id,
                "subject_type": fila.subject_type,
                "subject_id": fila.subject_id,
                "status": fila.status,
            }
            session.delete(fila)
            self._audit(
                session,
                actor=actor,
                action="mapping.deleted",
                object_type="curriculum_mapping",
                object_id=mapping_id,
                before=anterior,
                after={},
                now=now,
            )
            session.commit()
            return True

    def coverage(self, *, convocation_code: str) -> CoverageView:
        with self._session_factory() as session:
            nodos = (
                session.execute(
                    select(CurriculumNodeRecord)
                    .join(
                        ConvocationVersionRecord,
                        ConvocationVersionRecord.id == CurriculumNodeRecord.convocation_version_id,
                    )
                    .where(ConvocationVersionRecord.code == convocation_code)
                    .order_by(CurriculumNodeRecord.path)
                )
                .scalars()
                .all()
            )
            ids = [nodo.id for nodo in nodos]
            mapeos = (
                session.execute(
                    select(CurriculumMappingRecord).where(
                        CurriculumMappingRecord.curriculum_node_id.in_(ids)
                    )
                )
                .scalars()
                .all()
                if ids
                else []
            )
            pares = [(mapeo.subject_type, mapeo.subject_id) for mapeo in mapeos]
            etiquetas = self._subject_labels(session, pares)
            calidades = self._subject_qualities(session, pares)
            # Un mismo material puede estar clasificado como artefacto y como representación: la
            # cobertura cuenta **materiales**, no mapeos, para no contar dos veces el mismo fichero.
            claves = self._material_keys(session, pares)
            propuestas = session.execute(
                select(
                    ClassificationProposalRecord.subject_type,
                    ClassificationProposalRecord.subject_id,
                ).distinct()
            ).all()
            artefactos = int(
                session.execute(
                    select(func.count(func.distinct(ExtractedRepresentationRecord.artifact_id)))
                ).scalar_one()
            )

        provisional: dict[str, set[str]] = defaultdict(set)
        aceptada: dict[str, set[str]] = defaultdict(set)
        materiales: dict[str, list[str]] = defaultdict(list)
        ya_listados: dict[str, set[str]] = defaultdict(set)
        for mapeo in mapeos:
            clave = claves.get((mapeo.subject_type, mapeo.subject_id), mapeo.subject_id)
            etiqueta = etiquetas.get((mapeo.subject_type, mapeo.subject_id)) or clave
            if mapeo.status == MappingStatus.PROVISIONAL.value:
                provisional[mapeo.curriculum_node_id].add(clave)
            elif coverage_counts_as_accepted(
                calidades.get((mapeo.subject_type, mapeo.subject_id)), MappingStatus(mapeo.status)
            ):
                aceptada[mapeo.curriculum_node_id].add(clave)
            if (
                clave not in ya_listados[mapeo.curriculum_node_id]
                and len(materiales[mapeo.curriculum_node_id]) < 3
            ):
                materiales[mapeo.curriculum_node_id].append(etiqueta)
                ya_listados[mapeo.curriculum_node_id].add(clave)

        # Lo aceptado manda: un material no se cuenta como provisional y aceptado a la vez.
        for nodo_id, claves_aceptadas in aceptada.items():
            provisional[nodo_id] -= claves_aceptadas

        vistas = tuple(
            CoverageNodeView(
                node_id=nodo.id,
                path=nodo.path,
                title=nodo.title,
                depth=nodo.depth,
                provisional=len(provisional.get(nodo.id, ())),
                accepted=len(aceptada.get(nodo.id, ())),
                materials=tuple(materiales.get(nodo.id, ())),
            )
            for nodo in nodos
        )
        clasificados = {str(fila[0]) for fila in propuestas if str(fila[0]) == "artifact"}
        artefactos_con_propuesta = {
            str(fila[1]) for fila in propuestas if str(fila[0]) == "artifact"
        }
        return CoverageView(
            convocation_code=convocation_code,
            nodes=vistas,
            provisional_total=sum(len(valor) for valor in provisional.values()),
            accepted_total=sum(len(valor) for valor in aceptada.values()),
            classified_subjects=len(artefactos_con_propuesta) if clasificados else 0,
            unclassified_subjects=max(0, artefactos - len(artefactos_con_propuesta)),
            materials_total=artefactos,
        )

    def node_coverage(self, node_id: str) -> NodeCoverageView | None:
        """Cobertura de un nodo y de su subárbol: lo que pinta el árbol del programa."""
        with self._session_factory() as session:
            nodo = session.get(CurriculumNodeRecord, node_id)
            if nodo is None:
                return None
            convocatoria = session.get(ConvocationVersionRecord, nodo.convocation_version_id)
            if convocatoria is None:
                return None
            vista = self.coverage(convocation_code=convocatoria.code)
        prefijo = f"{nodo.path}/"
        subarbol = tuple(
            fila for fila in vista.nodes if fila.path == nodo.path or fila.path.startswith(prefijo)
        )
        return NodeCoverageView(
            node_id=nodo.id,
            path=nodo.path,
            title=nodo.title,
            depth=nodo.depth,
            provisional=sum(fila.provisional for fila in subarbol),
            accepted=sum(fila.accepted for fila in subarbol),
            unclassified_subjects=vista.unclassified_subjects,
            materials_total=vista.materials_total,
            subtree=subarbol,
        )

    # ------------------------------------------------------------------ duplicados

    def record_text_duplicates(
        self, clusters: Sequence[DuplicateClusterDraft], *, now: datetime
    ) -> tuple[DuplicateClusterView, ...]:
        with self._session_factory() as session:
            for borrador in clusters:
                existente = session.execute(
                    select(DuplicateClusterRecord).where(
                        DuplicateClusterRecord.kind == borrador.kind,
                        DuplicateClusterRecord.signature == borrador.signature,
                    )
                ).scalar_one_or_none()
                if existente is None:
                    existente = DuplicateClusterRecord(
                        id=_new_id(),
                        kind=borrador.kind,
                        relation=borrador.relation,
                        signature=borrador.signature,
                        status="open",
                        created_at=now,
                        resolved_at=None,
                        resolution_note=None,
                    )
                    session.add(existente)
                    session.flush()
                for miembro in borrador.members:
                    ya = session.execute(
                        select(DuplicateClusterMemberRecord.id).where(
                            DuplicateClusterMemberRecord.cluster_id == existente.id,
                            DuplicateClusterMemberRecord.subject_type == miembro.subject_type,
                            DuplicateClusterMemberRecord.subject_id == miembro.subject_id,
                        )
                    ).first()
                    if ya is None:
                        session.add(
                            DuplicateClusterMemberRecord(
                                id=_new_id(),
                                cluster_id=existente.id,
                                subject_type=miembro.subject_type,
                                subject_id=miembro.subject_id,
                                similarity=miembro.similarity,
                                is_representative=miembro.is_representative,
                            )
                        )
            session.commit()
            return tuple(self._clusters(session, status=None))

    def list_duplicate_clusters(
        self, *, status: str | None = None
    ) -> tuple[DuplicateClusterView, ...]:
        with self._session_factory() as session:
            return tuple(self._clusters(session, status=status))

    def resolve_duplicate_cluster(
        self,
        cluster_id: str,
        *,
        relation: str,
        note: str | None,
        now: datetime,
        actor: str = "local",
    ) -> DuplicateClusterView | None:
        with self._session_factory() as session:
            fila = session.get(DuplicateClusterRecord, cluster_id)
            if fila is None:
                return None
            anterior = {"status": fila.status, "relation": fila.relation}
            fila.relation = relation
            fila.status = "resolved"
            fila.resolved_at = now
            fila.resolution_note = note
            self._audit(
                session,
                actor=actor,
                action="duplicate_cluster.resolved",
                object_type="duplicate_cluster",
                object_id=cluster_id,
                before=anterior,
                after={"status": fila.status, "relation": fila.relation},
                now=now,
            )
            session.commit()
            vistas = self._clusters(session, status=None, cluster_id=cluster_id)
        return vistas[0] if vistas else None

    def _clusters(
        self, session: Session, *, status: str | None, cluster_id: str | None = None
    ) -> list[DuplicateClusterView]:
        filtros = []
        if status is not None:
            filtros.append(DuplicateClusterRecord.status == status)
        if cluster_id is not None:
            filtros.append(DuplicateClusterRecord.id == cluster_id)
        filas = (
            session.execute(
                select(DuplicateClusterRecord)
                .where(*filtros)
                .order_by(DuplicateClusterRecord.created_at.desc(), DuplicateClusterRecord.id)
            )
            .scalars()
            .all()
        )
        miembros = (
            session.execute(
                select(DuplicateClusterMemberRecord).where(
                    DuplicateClusterMemberRecord.cluster_id.in_([fila.id for fila in filas])
                )
            )
            .scalars()
            .all()
            if filas
            else []
        )
        etiquetas = self._subject_labels(
            session, [(miembro.subject_type, miembro.subject_id) for miembro in miembros]
        )
        por_cluster: dict[str, list[DuplicateMemberView]] = defaultdict(list)
        for miembro in miembros:
            por_cluster[miembro.cluster_id].append(
                DuplicateMemberView(
                    subject_type=miembro.subject_type,
                    subject_id=miembro.subject_id,
                    subject_label=etiquetas.get((miembro.subject_type, miembro.subject_id)),
                    similarity=miembro.similarity,
                    is_representative=miembro.is_representative,
                )
            )
        return [
            DuplicateClusterView(
                id=fila.id,
                kind=fila.kind,
                relation=fila.relation,
                signature=fila.signature,
                status=fila.status,
                members=tuple(por_cluster.get(fila.id, ())),
                created_at=fila.created_at,
                resolved_at=fila.resolved_at,
                resolution_note=fila.resolution_note,
            )
            for fila in filas
        ]

    # ------------------------------------------------------------------ auxiliares

    @staticmethod
    def _audit(
        session: Session,
        *,
        actor: str,
        action: str,
        object_type: str,
        object_id: str,
        before: Mapping[str, object],
        after: Mapping[str, object],
        now: datetime,
    ) -> str:
        evento = AuditEventRecord(
            id=_new_id(),
            actor=actor,
            action=action,
            object_type=object_type,
            object_id=object_id,
            before_json=json.dumps(before, ensure_ascii=False),
            after_json=json.dumps(after, ensure_ascii=False),
            correlation_id=None,
            created_at=now,
        )
        session.add(evento)
        return evento.id

    @staticmethod
    def _subject_labels(
        session: Session, pares: Sequence[tuple[str, str]]
    ) -> dict[tuple[str, str], str | None]:
        """Nombre visible de cada sujeto: el del fichero del que salió, si consta."""
        representaciones = [
            sujeto for tipo, sujeto in pares if tipo == SubjectType.REPRESENTATION.value
        ]
        artefactos = [sujeto for tipo, sujeto in pares if tipo == SubjectType.ARTIFACT.value]
        etiquetas: dict[tuple[str, str], str | None] = {}
        if representaciones:
            filas = session.execute(
                select(
                    ItemRepresentationRecord.representation_id,
                    IngestionItemRecord.original_name,
                )
                .join(
                    IngestionItemRecord, IngestionItemRecord.id == ItemRepresentationRecord.item_id
                )
                .where(ItemRepresentationRecord.representation_id.in_(representaciones))
            ).all()
            for representation_id, nombre in filas:
                etiquetas.setdefault(
                    (SubjectType.REPRESENTATION.value, str(representation_id)), str(nombre)
                )
        if artefactos:
            filas_artefacto = session.execute(
                select(IngestionItemRecord.artifact_id, IngestionItemRecord.original_name)
                .where(IngestionItemRecord.artifact_id.in_(artefactos))
                .order_by(IngestionItemRecord.position)
            ).all()
            for artifact_id, nombre in filas_artefacto:
                etiquetas.setdefault((SubjectType.ARTIFACT.value, str(artifact_id)), str(nombre))
        return etiquetas

    @staticmethod
    def _value_labels(
        session: Session, filas: Sequence[ClassificationProposalRecord]
    ) -> dict[tuple[str, str], str]:
        """Etiqueta legible del valor propuesto: nodos, oposiciones y vocabularios cerrados."""
        etiquetas: dict[tuple[str, str], str] = {}
        temas = [fila.proposed_value for fila in filas if fila.axis == Axis.TOPIC.value]
        if temas:
            nodos = session.execute(
                select(CurriculumNodeRecord.path, CurriculumNodeRecord.title).where(
                    CurriculumNodeRecord.path.in_(temas)
                )
            ).all()
            for path, title in nodos:
                etiquetas[(Axis.TOPIC.value, str(path))] = str(title)
        oposiciones = [fila.proposed_value for fila in filas if fila.axis == Axis.OPPOSITION.value]
        if oposiciones:
            nombres = session.execute(
                select(OppositionRecord.code, OppositionRecord.name).where(
                    OppositionRecord.code.in_(oposiciones)
                )
            ).all()
            for code, name in nombres:
                etiquetas[(Axis.OPPOSITION.value, str(code))] = str(name)
        for fila in filas:
            etiqueta = value_label(fila.axis, fila.proposed_value)
            if etiqueta is not None:
                etiquetas[(fila.axis, fila.proposed_value)] = etiqueta
        return etiquetas

    @staticmethod
    def _material_keys(
        session: Session, pares: Sequence[tuple[str, str]]
    ) -> dict[tuple[str, str], str]:
        """Clave del **material** de cada sujeto: una representación pertenece a su artefacto.

        Sirve para que la cobertura cuente materiales y no mapeos: el mismo fichero clasificado como
        artefacto y como representación es un solo material, y sumarlo dos veces inflaría la
        cobertura que ve el usuario.
        """
        claves: dict[tuple[str, str], str] = {}
        representaciones = [
            sujeto for tipo, sujeto in pares if tipo == SubjectType.REPRESENTATION.value
        ]
        if representaciones:
            filas = session.execute(
                select(
                    ExtractedRepresentationRecord.id,
                    ExtractedRepresentationRecord.artifact_id,
                ).where(ExtractedRepresentationRecord.id.in_(representaciones))
            ).all()
            for representation_id, artifact_id in filas:
                claves[(SubjectType.REPRESENTATION.value, str(representation_id))] = str(
                    artifact_id
                )
        return claves

    @staticmethod
    def _subject_qualities(
        session: Session, pares: Sequence[tuple[str, str]]
    ) -> dict[tuple[str, str], Quality | None]:
        """Calidad del texto que respalda a cada sujeto: la mejor de sus representaciones."""
        calidades: dict[tuple[str, str], Quality | None] = {}
        representaciones = [
            sujeto for tipo, sujeto in pares if tipo == SubjectType.REPRESENTATION.value
        ]
        artefactos = [sujeto for tipo, sujeto in pares if tipo == SubjectType.ARTIFACT.value]
        if representaciones:
            filas = session.execute(
                select(
                    ExtractedRepresentationRecord.id, ExtractedRepresentationRecord.quality
                ).where(ExtractedRepresentationRecord.id.in_(representaciones))
            ).all()
            for representation_id, quality in filas:
                calidades[(SubjectType.REPRESENTATION.value, str(representation_id))] = _quality(
                    str(quality)
                )
        if artefactos:
            filas = session.execute(
                select(
                    ExtractedRepresentationRecord.artifact_id,
                    ExtractedRepresentationRecord.quality,
                ).where(ExtractedRepresentationRecord.artifact_id.in_(artefactos))
            ).all()
            mejores: dict[str, Quality] = {}
            for artifact_id, quality in filas:
                valor = _quality(str(quality))
                if valor is None:
                    continue
                actual = mejores.get(str(artifact_id))
                if actual is None or _QUALITY_ORDER[valor.value] < _QUALITY_ORDER[actual.value]:
                    mejores[str(artifact_id)] = valor
            for artifact_id, valor in mejores.items():
                calidades[(SubjectType.ARTIFACT.value, artifact_id)] = valor
        return calidades

    def _proposal_view(
        self,
        fila: ClassificationProposalRecord,
        etiquetas: dict[tuple[str, str], str | None],
        valores: dict[tuple[str, str], str],
    ) -> ProposalView:
        eje = Axis(fila.axis)
        return ProposalView(
            id=fila.id,
            subject_type=fila.subject_type,
            subject_id=fila.subject_id,
            subject_label=etiquetas.get((fila.subject_type, fila.subject_id)),
            axis=fila.axis,
            proposed_value=fila.proposed_value,
            value_label=valores.get((fila.axis, fila.proposed_value)),
            confidence=fila.confidence,
            band=self._bands.band_for(fila.confidence, axis=eje).value,
            is_critical=eje in CRITICAL_AXES,
            status=fila.status,
            engine_name=fila.engine_name,
            engine_version=fila.engine_version,
            alternatives=_load_alternatives(fila.alternatives_json),
            evidence=_load_str_list(fila.evidence_json),
            created_at=fila.created_at,
            decided_at=fila.decided_at,
            decision_note=fila.decision_note,
        )


def _estado_auditado(before_json: str | None) -> dict[str, object]:
    """Estado anterior tal como se guardó en la auditoría (vacío si no se puede leer)."""
    if not before_json:
        return {}
    try:
        datos = json.loads(before_json)
    except json.JSONDecodeError:
        return {}
    return datos if isinstance(datos, dict) else {}


def _fecha(valor: object) -> datetime | None:
    """Fecha ISO del evento auditado, o `None` si no hay o no se puede leer."""
    if isinstance(valor, str) and valor:
        try:
            return datetime.fromisoformat(valor)
        except ValueError:
            return None
    return None


def _texto(valor: object) -> str | None:
    return valor if isinstance(valor, str) else None
