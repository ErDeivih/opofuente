"""Lecturas del temario común, sus referencias, particularidades y avance (B-004/B-005).

Todo se resuelve en SQL y se compone aquí: la API no consulta tablas. El avance se calcula al leer a
partir de las marcas de estudio y de la actividad real (preguntas mapeadas y fallos declarados);
no se guarda ningún porcentaje, igual que la cobertura.

Las particularidades de una convocatoria (`omitted`, `renamed`, `renumbered`) se aplican al componer
el temario efectivo: lo omitido se excluye con su subárbol, lo renombrado cambia el título
mostrado y lo renumerado el código. `weighted` no cambia el árbol: se usará al componer
simulacros.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.curriculum_models import (
    AdjustmentView,
    AppearanceView,
    BlockProgressView,
    ConvocationIdentityView,
    CurriculumDetailView,
    CurriculumIdentityView,
    CurriculumNodeDetailView,
    CurriculumSummaryView,
    CurriculumVersionView,
    ProgressView,
    ReferenceView,
    StudyMarkView,
    TemarioView,
    percent,
)
from opofuente.application.read_models import NodeView
from opofuente.domain.profiles import NodeType
from opofuente.infrastructure.db_models import (
    ConvocationCurriculumAdjustmentRecord,
    ConvocationCurriculumRefRecord,
    ConvocationVersionRecord,
    CurriculumMappingRecord,
    CurriculumNodeRecord,
    CurriculumRecord,
    CurriculumStudyMarkRecord,
    CurriculumVersionRecord,
    LearningErrorRecord,
    OppositionRecord,
)


def _new_id() -> str:
    return str(uuid4())


class SqlAlchemyCurriculumReadRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ temarios

    def list_curricula(self, *, kind: str | None) -> tuple[CurriculumSummaryView, ...]:
        with self._session_factory() as session:
            consulta = select(CurriculumRecord).order_by(CurriculumRecord.code)
            if kind is not None:
                consulta = consulta.where(CurriculumRecord.kind == kind)
            filas = session.execute(consulta).scalars().all()
            return tuple(self._summary(session, fila) for fila in filas)

    def get_curriculum(self, code: str) -> CurriculumDetailView | None:
        with self._session_factory() as session:
            fila = session.execute(
                select(CurriculumRecord).where(CurriculumRecord.code == code)
            ).scalar_one_or_none()
            if fila is None:
                return None
            versiones = self._versions(session, fila.id)
            activa = next((v for v in versiones if v.status == "active"), None)
            rows: list[CurriculumNodeRecord] = []
            marks: dict[str, datetime] = {}
            counts: dict[str, int] = {"block": 0, "topic": 0, "epigraph": 0}
            progress: ProgressView | None = None
            if activa is not None:
                version_id = self._version_id(session, activa.code)
                if version_id is not None:
                    rows = self._nodes(session, version_id)
                    marks = self._marks(session, [fila.id for fila in rows])
                    counts = self._counts(rows)
                    if fila.kind == "common":
                        progress = self._progress(fila.code, activa, rows, marks, session)
            return CurriculumDetailView(
                code=fila.code,
                name=fila.name,
                kind=fila.kind,
                group_code=fila.group_code,
                family=fila.family,
                versions=versiones,
                active_version=activa,
                counts=counts,
                nodes=self._tree(rows, studied=marks),
                progress=progress,
            )

    def list_versions(self, code: str) -> tuple[CurriculumVersionView, ...] | None:
        with self._session_factory() as session:
            fila = session.execute(
                select(CurriculumRecord).where(CurriculumRecord.code == code)
            ).scalar_one_or_none()
            if fila is None:
                return None
            return self._versions(session, fila.id)

    # ------------------------------------------------------------------ convocatorias

    def list_references(self, convocation_id: str) -> tuple[ReferenceView, ...] | None:
        with self._session_factory() as session:
            convocation = session.get(ConvocationVersionRecord, convocation_id)
            if convocation is None:
                return None
            filas = session.execute(
                select(
                    ConvocationCurriculumRefRecord,
                    CurriculumVersionRecord,
                    CurriculumRecord,
                )
                .join(
                    CurriculumVersionRecord,
                    CurriculumVersionRecord.id
                    == ConvocationCurriculumRefRecord.curriculum_version_id,
                )
                .join(
                    CurriculumRecord,
                    CurriculumRecord.id == CurriculumVersionRecord.curriculum_id,
                )
                .where(ConvocationCurriculumRefRecord.convocation_version_id == convocation_id)
                .order_by(ConvocationCurriculumRefRecord.role, CurriculumRecord.code)
            ).all()
            return tuple(
                ReferenceView(
                    role=referencia.role,
                    curriculum_code=curriculum.code,
                    curriculum_name=curriculum.name,
                    curriculum_kind=curriculum.kind,
                    version_code=version.code,
                    version_no=version.version_no,
                    version_title=version.title,
                    source_reference=referencia.source_reference,
                )
                for referencia, version, curriculum in filas
            )

    def get_temario(self, convocation_id: str) -> TemarioView | None:
        """Temario que estudia la convocatoria; `None` si la convocatoria no referencia el común."""
        with self._session_factory() as session:
            convocation = session.get(ConvocationVersionRecord, convocation_id)
            if convocation is None:
                return None
            referencia = session.execute(
                select(ConvocationCurriculumRefRecord).where(
                    ConvocationCurriculumRefRecord.convocation_version_id == convocation_id,
                    ConvocationCurriculumRefRecord.role == "primary",
                )
            ).scalar_one_or_none()
            if referencia is None:
                return None
            version_id = referencia.curriculum_version_id
            version = session.get(CurriculumVersionRecord, version_id)
            if version is None:  # pragma: no cover - la clave foránea lo impide
                return None
            curriculum = session.get(CurriculumRecord, version.curriculum_id)
            if curriculum is None:  # pragma: no cover
                return None

            rows = self._nodes(session, version_id)
            ajustes = self._adjustments(session, referencia.id)
            excluidos = self._excluded(rows, ajustes)
            overrides = self._overrides(ajustes)
            mantenidos = [fila for fila in rows if fila.id not in excluidos]
            filtrados = [fila for fila in rows if fila.id in excluidos]
            return TemarioView(
                convocation=self._convocation_identity(session, convocation),
                curriculum=CurriculumIdentityView(
                    code=curriculum.code,
                    name=curriculum.name,
                    kind=curriculum.kind,
                    version_code=version.code,
                    version_title=version.title,
                ),
                version=self._version_view(version),
                counts=self._counts(mantenidos),
                nodes=self._tree(mantenidos, overrides=overrides),
                omitted_topics=sum(1 for fila in filtrados if fila.node_type == "topic"),
            )

    # ------------------------------------------------------------------ nodos

    def get_node(
        self, node_id: str, *, convocation_id: str | None = None
    ) -> CurriculumNodeDetailView | None:
        with self._session_factory() as session:
            nodo = session.get(CurriculumNodeRecord, node_id)
            if nodo is None:
                return None
            version = session.get(CurriculumVersionRecord, nodo.curriculum_version_id)
            if version is None:  # pragma: no cover - la clave foránea lo impide
                return None
            curriculum = session.get(CurriculumRecord, version.curriculum_id)
            if curriculum is None:  # pragma: no cover
                return None

            convocation = self._official_convocation(session, version.id)
            appearances: tuple[AppearanceView, ...] = ()
            if curriculum.kind == "common":
                appearances = self._appearances(session, nodo, version, curriculum)
            particularities: tuple[AdjustmentView, ...] = ()
            if convocation_id is not None:
                particularities = self._particularities(session, nodo, version, convocation_id)
            mark = session.execute(
                select(CurriculumStudyMarkRecord).where(
                    CurriculumStudyMarkRecord.curriculum_node_id == nodo.id
                )
            ).scalar_one_or_none()
            return CurriculumNodeDetailView(
                node=self._node_view(nodo, studied=mark.marked_at if mark is not None else None),
                curriculum=CurriculumIdentityView(
                    code=curriculum.code,
                    name=curriculum.name,
                    kind=curriculum.kind,
                    version_code=version.code,
                    version_title=version.title,
                ),
                convocation=convocation,
                appears_in=appearances,
                particularities=particularities,
                studied_at=mark.marked_at if mark is not None else None,
                ancestors=self._ancestors(session, nodo),
            )

    # ------------------------------------------------------------------ avance

    def get_progress(self, code: str) -> ProgressView | None:
        with self._session_factory() as session:
            curriculum = session.execute(
                select(CurriculumRecord).where(CurriculumRecord.code == code)
            ).scalar_one_or_none()
            if curriculum is None:
                return None
            versiones = self._versions(session, curriculum.id)
            activa = next((v for v in versiones if v.status == "active"), None)
            if activa is None:
                return ProgressView(
                    curriculum_code=code,
                    version_code="",
                    blocks=(),
                    topics_total=0,
                    topics_studied=0,
                    topics_with_activity=0,
                    percent=0.0,
                )
            version_id = self._version_id(session, activa.code)
            if version_id is None:  # pragma: no cover
                return None
            rows = self._nodes(session, version_id)
            marks = self._marks(session, [fila.id for fila in rows])
            return self._progress(code, activa, rows, marks, session)

    def mark_studied(self, node_id: str, *, now: datetime) -> StudyMarkView | None:
        with self._session_factory() as session:
            nodo = session.get(CurriculumNodeRecord, node_id)
            if nodo is None:
                return None
            marca = session.execute(
                select(CurriculumStudyMarkRecord).where(
                    CurriculumStudyMarkRecord.curriculum_node_id == node_id
                )
            ).scalar_one_or_none()
            if marca is None:
                marca = CurriculumStudyMarkRecord(
                    id=_new_id(), curriculum_node_id=node_id, marked_at=now, note=None
                )
                session.add(marca)
            session.commit()
            return StudyMarkView(node_id=node_id, studied_at=marca.marked_at)

    def unmark_studied(self, node_id: str) -> bool | None:
        with self._session_factory() as session:
            if session.get(CurriculumNodeRecord, node_id) is None:
                return None
            marca = session.execute(
                select(CurriculumStudyMarkRecord).where(
                    CurriculumStudyMarkRecord.curriculum_node_id == node_id
                )
            ).scalar_one_or_none()
            if marca is None:
                return False
            session.delete(marca)
            session.commit()
            return True

    # ------------------------------------------------------------------ composición

    @staticmethod
    def _summary(session: Session, fila: CurriculumRecord) -> CurriculumSummaryView:
        versiones = SqlAlchemyCurriculumReadRepository._versions(session, fila.id)
        activa = next((v for v in versiones if v.status == "active"), None)
        return CurriculumSummaryView(
            code=fila.code,
            name=fila.name,
            kind=fila.kind,
            group_code=fila.group_code,
            family=fila.family,
            versions=versiones,
            active_version=activa,
        )

    @staticmethod
    def _versions(session: Session, curriculum_id: str) -> tuple[CurriculumVersionView, ...]:
        filas = (
            session.execute(
                select(CurriculumVersionRecord)
                .where(CurriculumVersionRecord.curriculum_id == curriculum_id)
                .order_by(CurriculumVersionRecord.version_no)
            )
            .scalars()
            .all()
        )
        return tuple(SqlAlchemyCurriculumReadRepository._version_view(fila) for fila in filas)

    @staticmethod
    def _version_view(fila: CurriculumVersionRecord) -> CurriculumVersionView:
        return CurriculumVersionView(
            code=fila.code,
            version_no=fila.version_no,
            title=fila.title,
            status=fila.status,
        )

    @staticmethod
    def _version_id(session: Session, code: str) -> str | None:
        return session.execute(
            select(CurriculumVersionRecord.id).where(CurriculumVersionRecord.code == code)
        ).scalar_one_or_none()

    @staticmethod
    def _nodes(session: Session, version_id: str) -> list[CurriculumNodeRecord]:
        return list(
            session.execute(
                select(CurriculumNodeRecord)
                .where(CurriculumNodeRecord.curriculum_version_id == version_id)
                .order_by(CurriculumNodeRecord.depth, CurriculumNodeRecord.position)
            )
            .scalars()
            .all()
        )

    @staticmethod
    def _marks(session: Session, node_ids: list[str]) -> dict[str, datetime]:
        if not node_ids:
            return {}
        filas = session.execute(
            select(
                CurriculumStudyMarkRecord.curriculum_node_id,
                CurriculumStudyMarkRecord.marked_at,
            ).where(CurriculumStudyMarkRecord.curriculum_node_id.in_(node_ids))
        ).all()
        return {str(fila[0]): fila[1] for fila in filas}

    @staticmethod
    def _counts(rows: list[CurriculumNodeRecord]) -> dict[str, int]:
        counts: dict[str, int] = {"block": 0, "topic": 0, "epigraph": 0}
        for fila in rows:
            counts[fila.node_type] = counts.get(fila.node_type, 0) + 1
        return counts

    @staticmethod
    def _tree(
        rows: list[CurriculumNodeRecord],
        *,
        studied: dict[str, datetime] | None = None,
        overrides: dict[str, tuple[str | None, str | None]] | None = None,
    ) -> tuple[NodeView, ...]:
        by_parent: dict[str | None, list[CurriculumNodeRecord]] = defaultdict(list)
        for fila in rows:
            by_parent[fila.parent_id].append(fila)
        marcas = studied or {}
        cambios = overrides or {}

        def build(parent_id: str | None) -> tuple[NodeView, ...]:
            children = sorted(by_parent.get(parent_id, []), key=lambda fila: fila.position)
            return tuple(
                NodeView(
                    id=fila.id,
                    node_type=NodeType(fila.node_type),
                    official_code=cambios.get(fila.id, (None, None))[0] or fila.official_code,
                    title=cambios.get(fila.id, (None, None))[1] or fila.title,
                    description=fila.description,
                    position=fila.position,
                    path=fila.path,
                    depth=fila.depth,
                    studied_at=marcas.get(fila.id),
                    children=build(fila.id),
                )
                for fila in children
            )

        return build(None)

    @staticmethod
    def _node_view(fila: CurriculumNodeRecord, *, studied: datetime | None) -> NodeView:
        return NodeView(
            id=fila.id,
            node_type=NodeType(fila.node_type),
            official_code=fila.official_code,
            title=fila.title,
            description=fila.description,
            position=fila.position,
            path=fila.path,
            depth=fila.depth,
            studied_at=studied,
        )

    @staticmethod
    def _ancestors(session: Session, nodo: CurriculumNodeRecord) -> tuple[NodeView, ...]:
        ancestros: list[NodeView] = []
        parent_id = nodo.parent_id
        while parent_id is not None:
            padre = session.get(CurriculumNodeRecord, parent_id)
            if padre is None:  # pragma: no cover - la clave foránea lo impide
                break
            ancestros.append(SqlAlchemyCurriculumReadRepository._node_view(padre, studied=None))
            parent_id = padre.parent_id
        return tuple(reversed(ancestros))

    @staticmethod
    def _official_convocation(session: Session, version_id: str) -> ConvocationIdentityView | None:
        fila = session.execute(
            select(ConvocationVersionRecord)
            .join(
                ConvocationCurriculumRefRecord,
                ConvocationCurriculumRefRecord.convocation_version_id
                == ConvocationVersionRecord.id,
            )
            .where(
                ConvocationCurriculumRefRecord.curriculum_version_id == version_id,
                ConvocationCurriculumRefRecord.role == "official",
            )
            .limit(1)
        ).scalar_one_or_none()
        if fila is None:
            return None
        return SqlAlchemyCurriculumReadRepository._convocation_identity(session, fila)

    @staticmethod
    def _convocation_identity(
        session: Session, convocation: ConvocationVersionRecord
    ) -> ConvocationIdentityView:
        oposicion = session.get(OppositionRecord, convocation.opposition_id)
        return ConvocationIdentityView(
            id=convocation.id,
            code=convocation.code,
            title=convocation.title,
            official_url=convocation.official_url,
            published_at=convocation.published_at,
            opposition_code=oposicion.code if oposicion is not None else "",
            opposition_name=oposicion.name if oposicion is not None else "",
            source_reference=convocation.source_reference,
        )

    @staticmethod
    def _adjustments(session: Session, ref_id: str) -> list[ConvocationCurriculumAdjustmentRecord]:
        return list(
            session.execute(
                select(ConvocationCurriculumAdjustmentRecord).where(
                    ConvocationCurriculumAdjustmentRecord.ref_id == ref_id
                )
            )
            .scalars()
            .all()
        )

    @staticmethod
    def _excluded(
        rows: list[CurriculumNodeRecord],
        adjustments: list[ConvocationCurriculumAdjustmentRecord],
    ) -> set[str]:
        """Nodos omitidos y sus descendientes (la omisión de un bloque arrastra sus temas)."""
        children: dict[str | None, list[str]] = defaultdict(list)
        for fila in rows:
            children[fila.parent_id].append(fila.id)
        excluidos: set[str] = set()
        pendientes = [
            ajuste.curriculum_node_id for ajuste in adjustments if ajuste.kind == "omitted"
        ]
        while pendientes:
            actual = pendientes.pop()
            if actual in excluidos:
                continue
            excluidos.add(actual)
            pendientes.extend(children.get(actual, []))
        return excluidos

    @staticmethod
    def _overrides(
        adjustments: list[ConvocationCurriculumAdjustmentRecord],
    ) -> dict[str, tuple[str | None, str | None]]:
        overrides: dict[str, tuple[str | None, str | None]] = {}
        for ajuste in adjustments:
            codigo, titulo = overrides.get(ajuste.curriculum_node_id, (None, None))
            overrides[ajuste.curriculum_node_id] = (
                ajuste.official_code_override or codigo,
                ajuste.title_override or titulo,
            )
        return overrides

    @staticmethod
    def _adjustment_view(ajuste: ConvocationCurriculumAdjustmentRecord) -> AdjustmentView:
        return AdjustmentView(
            kind=ajuste.kind,
            weight=ajuste.weight,
            official_code_override=ajuste.official_code_override,
            title_override=ajuste.title_override,
            evidence_quote=ajuste.evidence_quote,
        )

    def _appearances(
        self,
        session: Session,
        node: CurriculumNodeRecord,
        version: CurriculumVersionRecord,
        curriculum: CurriculumRecord,
    ) -> tuple[AppearanceView, ...]:
        """Convocatorias que estudian el temario (primary/complementary) y no omiten el tema."""
        versiones = (
            session.execute(
                select(CurriculumVersionRecord.id).where(
                    CurriculumVersionRecord.curriculum_id == curriculum.id
                )
            )
            .scalars()
            .all()
        )
        filas = session.execute(
            select(ConvocationCurriculumRefRecord, ConvocationVersionRecord)
            .join(
                ConvocationVersionRecord,
                ConvocationVersionRecord.id
                == ConvocationCurriculumRefRecord.convocation_version_id,
            )
            .where(
                ConvocationCurriculumRefRecord.curriculum_version_id.in_(versiones),
                ConvocationCurriculumRefRecord.role.in_(("primary", "complementary")),
            )
            .order_by(ConvocationVersionRecord.published_at.desc())
        ).all()
        apariciones: list[AppearanceView] = []
        for referencia, convocation in filas:
            ajustes = self._adjustments(session, referencia.id)
            rows = self._nodes(session, referencia.curriculum_version_id)
            excluidos = self._excluded(rows, ajustes)
            propios = [ajuste for ajuste in ajustes if ajuste.curriculum_node_id == node.id]
            apariciones.append(
                AppearanceView(
                    convocation_id=convocation.id,
                    convocation_code=convocation.code,
                    convocation_title=convocation.title,
                    convocation_status=convocation.status,
                    role=referencia.role,
                    source_reference=referencia.source_reference,
                    omitted=node.id in excluidos,
                    adjustments=tuple(self._adjustment_view(ajuste) for ajuste in propios),
                )
            )
        return tuple(apariciones)

    def _particularities(
        self,
        session: Session,
        node: CurriculumNodeRecord,
        version: CurriculumVersionRecord,
        convocation_id: str,
    ) -> tuple[AdjustmentView, ...]:
        referencia = session.execute(
            select(ConvocationCurriculumRefRecord).where(
                ConvocationCurriculumRefRecord.convocation_version_id == convocation_id,
                ConvocationCurriculumRefRecord.curriculum_version_id == version.id,
            )
        ).scalar_one_or_none()
        if referencia is None:
            return ()
        ajustes = self._adjustments(session, referencia.id)
        return tuple(
            self._adjustment_view(ajuste)
            for ajuste in ajustes
            if ajuste.curriculum_node_id == node.id
        )

    def _progress(
        self,
        curriculum_code: str,
        version: CurriculumVersionView,
        rows: list[CurriculumNodeRecord],
        marks: dict[str, datetime],
        session: Session,
    ) -> ProgressView:
        bloques = [fila for fila in rows if fila.node_type == "block"]
        temas = [fila for fila in rows if fila.node_type == "topic"]
        activity = self._activity(session, [fila.id for fila in rows])
        bloques_vista: list[BlockProgressView] = []
        for bloque in sorted(bloques, key=lambda fila: fila.position):
            hijos = [fila for fila in temas if fila.parent_id == bloque.id]
            estudiados = sum(1 for fila in hijos if fila.id in marks)
            con_actividad = sum(1 for fila in hijos if fila.id in activity)
            bloques_vista.append(
                BlockProgressView(
                    block_id=bloque.id,
                    path=bloque.path,
                    title=bloque.title,
                    position=bloque.position,
                    topics_total=len(hijos),
                    topics_studied=estudiados,
                    topics_with_activity=con_actividad,
                    percent=percent(estudiados, len(hijos)),
                )
            )
        estudiados_total = sum(1 for fila in temas if fila.id in marks)
        return ProgressView(
            curriculum_code=curriculum_code,
            version_code=version.code,
            blocks=tuple(bloques_vista),
            topics_total=len(temas),
            topics_studied=estudiados_total,
            topics_with_activity=sum(1 for fila in temas if fila.id in activity),
            percent=percent(estudiados_total, len(temas)),
        )

    @staticmethod
    def _activity(session: Session, node_ids: list[str]) -> set[str]:
        """Temas con actividad real: preguntas mapeadas (aceptadas) o fallos declarados."""
        if not node_ids:
            return set()
        preguntas = session.execute(
            select(func.distinct(CurriculumMappingRecord.curriculum_node_id)).where(
                CurriculumMappingRecord.curriculum_node_id.in_(node_ids),
                CurriculumMappingRecord.subject_type == "question_version",
                CurriculumMappingRecord.status == "accepted",
            )
        ).scalars()
        fallos = session.execute(
            select(func.distinct(LearningErrorRecord.curriculum_node_id)).where(
                LearningErrorRecord.curriculum_node_id.in_(node_ids)
            )
        ).scalars()
        return {str(valor) for valor in preguntas} | {
            str(valor) for valor in fallos if valor is not None
        }
