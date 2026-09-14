"""Repositorio SQLAlchemy de perfiles: oposiciones, convocatorias, programa y reglas.

Decisiones:

- cada método abre su propia sesión y hace `commit` al terminar, porque en S01 ninguna operación
  necesita tocar dos agregados a la vez. Cuando haga falta (S02 en adelante), esto se sustituye
  por una unidad de trabajo explícita;
- la siembra (`upsert_profile`) es **idempotente**: se compara campo a campo, se crea lo que falta,
  se actualiza lo que cambió y se elimina lo que ya no está en el fixture, de modo que ejecutarla
  dos veces deja el mismo estado y el informe lo dice.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from uuid import uuid4

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.read_models import (
    ConvocationDetail,
    ConvocationSummary,
    CurriculumView,
    EntityOutcome,
    NodeDetail,
    NodeView,
    OppositionDetail,
    OppositionSummary,
    SeedOutcome,
)
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.profiles import (
    Convocation,
    ConvocationStatus,
    CurriculumNode,
    ExamPart,
    ExamRule,
    NodeType,
    Opposition,
    PartFormat,
    PartKind,
    Profile,
    RuleKind,
    flatten,
)
from opofuente.infrastructure.db_models import (
    ConvocationVersionRecord,
    CurriculumNodeRecord,
    ExamPartRecord,
    ExamRuleRecord,
    OppositionRecord,
)


def _new_id() -> str:
    return str(uuid4())


class SqlAlchemyProfileRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ lectura

    def list_oppositions(self) -> Sequence[OppositionSummary]:
        with self._session_factory() as session:
            records = (
                session.execute(select(OppositionRecord).order_by(OppositionRecord.name))
                .scalars()
                .all()
            )
            return [self._summary(session, record) for record in records]

    def get_opposition(self, opposition_id: str) -> OppositionDetail | None:
        with self._session_factory() as session:
            record = session.get(OppositionRecord, opposition_id)
            if record is None:
                return None
            convocations = (
                session.execute(
                    select(ConvocationVersionRecord)
                    .where(ConvocationVersionRecord.opposition_id == record.id)
                    .order_by(ConvocationVersionRecord.published_at.desc())
                )
                .scalars()
                .all()
            )
            return OppositionDetail(
                opposition=self._summary(session, record),
                convocations=tuple(self._convocation_summary(row) for row in convocations),
            )

    def list_convocations(self, opposition_id: str) -> Sequence[ConvocationSummary]:
        with self._session_factory() as session:
            records = (
                session.execute(
                    select(ConvocationVersionRecord)
                    .where(ConvocationVersionRecord.opposition_id == opposition_id)
                    .order_by(ConvocationVersionRecord.published_at.desc())
                )
                .scalars()
                .all()
            )
            return [self._convocation_summary(row) for row in records]

    def get_convocation(self, convocation_id: str) -> ConvocationDetail | None:
        with self._session_factory() as session:
            record = session.get(ConvocationVersionRecord, convocation_id)
            if record is None:
                return None
            opposition = session.get(OppositionRecord, record.opposition_id)
            if opposition is None:  # pragma: no cover - la clave foránea lo impide
                raise InvariantViolationError("convocatoria sin oposición asociada")
            parts = (
                session.execute(
                    select(ExamPartRecord)
                    .where(ExamPartRecord.convocation_version_id == record.id)
                    .order_by(ExamPartRecord.position)
                )
                .scalars()
                .all()
            )
            codes_by_id = {row.id: row.code for row in parts}
            rules = (
                session.execute(
                    select(ExamRuleRecord)
                    .where(ExamRuleRecord.convocation_version_id == record.id)
                    .order_by(ExamRuleRecord.code)
                )
                .scalars()
                .all()
            )
            return ConvocationDetail(
                summary=self._convocation_summary(record),
                opposition_code=opposition.code,
                opposition_name=opposition.name,
                source_reference=record.source_reference,
                parts=tuple(self._part(row, codes_by_id) for row in parts),
                rules=tuple(self._rule(row) for row in rules),
            )

    def get_curriculum(self, convocation_id: str) -> CurriculumView | None:
        with self._session_factory() as session:
            convocation = session.get(ConvocationVersionRecord, convocation_id)
            if convocation is None:
                return None
            opposition = session.get(OppositionRecord, convocation.opposition_id)
            rows = (
                session.execute(
                    select(CurriculumNodeRecord)
                    .where(CurriculumNodeRecord.convocation_version_id == convocation_id)
                    .order_by(CurriculumNodeRecord.depth, CurriculumNodeRecord.position)
                )
                .scalars()
                .all()
            )
            nodes = self._tree(rows)
            counts: dict[str, int] = {node_type.value: 0 for node_type in NodeType}
            for row in rows:
                counts[row.node_type] += 1
            return CurriculumView(
                convocation_id=convocation_id,
                convocation_code=convocation.code,
                opposition_code=opposition.code if opposition else "",
                counts=counts,
                nodes=nodes,
            )

    def get_node(self, node_id: str) -> NodeDetail | None:
        with self._session_factory() as session:
            record = session.get(CurriculumNodeRecord, node_id)
            if record is None:
                return None
            convocation = session.get(ConvocationVersionRecord, record.convocation_version_id)
            if convocation is None:  # pragma: no cover - la clave foránea lo impide
                raise InvariantViolationError("nodo de programa sin convocatoria")
            opposition = session.get(OppositionRecord, convocation.opposition_id)

            ancestors: list[CurriculumNodeRecord] = []
            parent_id = record.parent_id
            while parent_id is not None:
                parent = session.get(CurriculumNodeRecord, parent_id)
                if parent is None:  # pragma: no cover - la clave foránea lo impide
                    break
                ancestors.append(parent)
                parent_id = parent.parent_id

            return NodeDetail(
                node=self._node(record),
                convocation_id=convocation.id,
                convocation_code=convocation.code,
                convocation_title=convocation.title,
                official_url=convocation.official_url,
                published_at=convocation.published_at,
                opposition_code=opposition.code if opposition else "",
                opposition_name=opposition.name if opposition else "",
                source_reference=convocation.source_reference,
                ancestors=tuple(self._node(row) for row in reversed(ancestors)),
            )

    # ------------------------------------------------------------------ escritura

    def activate_opposition(self, opposition_id: str, *, now: datetime) -> OppositionSummary | None:
        with self._session_factory() as session:
            target = session.get(OppositionRecord, opposition_id)
            if target is None:
                return None
            # Primero se desactivan las demás: el índice único parcial no permite dos activas ni
            # de forma momentánea dentro de la misma transacción.
            session.execute(
                update(OppositionRecord)
                .where(OppositionRecord.id != opposition_id)
                .values(active=False, updated_at=now)
            )
            if not target.active:
                target.active = True
                target.updated_at = now
            session.commit()
            return self._summary(session, target)

    def upsert_profile(self, profile: Profile, *, now: datetime) -> SeedOutcome:
        with self._session_factory() as session:
            outcomes: list[EntityOutcome] = []
            opposition, outcome = self._upsert_opposition(session, profile.opposition, now)
            outcomes.append(outcome)
            convocation, outcome = self._upsert_convocation(
                session, profile.convocation, opposition, now
            )
            outcomes.append(outcome)
            outcomes.extend(self._sync_curriculum(session, profile.curriculum, convocation))
            outcomes.extend(self._sync_parts(session, profile.parts, convocation))
            outcomes.extend(self._sync_rules(session, profile.rules, convocation))
            session.commit()
            return SeedOutcome(profile_code=profile.convocation.code, entities=tuple(outcomes))

    # ------------------------------------------------------------------ siembra

    def _upsert_opposition(
        self, session: Session, opposition: Opposition, now: datetime
    ) -> tuple[OppositionRecord, EntityOutcome]:
        record = session.execute(
            select(OppositionRecord).where(OppositionRecord.code == opposition.code)
        ).scalar_one_or_none()
        changed = False
        if record is None:
            record = OppositionRecord(
                id=_new_id(),
                code=opposition.code,
                name=opposition.name,
                description=opposition.description,
                active=False,
                created_at=now,
                updated_at=now,
            )
            session.add(record)
            session.flush()
            created = True
        else:
            created = False
            if record.name != opposition.name:
                record.name = opposition.name
                changed = True
            if record.description != opposition.description:
                record.description = opposition.description
                changed = True

        # La activación se comprueba siempre, también cuando la oposición ya existía y sus datos no
        # han cambiado: el fixture decide cuál queda activa, no el orden de siembra.
        if opposition.active and not record.active:
            session.execute(
                update(OppositionRecord)
                .where(OppositionRecord.id != record.id)
                .values(active=False, updated_at=now)
            )
            record.active = True
            changed = True

        if changed:
            record.updated_at = now
        return record, EntityOutcome(
            code=opposition.code, created=created, updated=changed and not created
        )

    def _upsert_convocation(
        self,
        session: Session,
        convocation: Convocation,
        opposition: OppositionRecord,
        now: datetime,
    ) -> tuple[ConvocationVersionRecord, EntityOutcome]:
        record = session.execute(
            select(ConvocationVersionRecord).where(
                ConvocationVersionRecord.code == convocation.code
            )
        ).scalar_one_or_none()
        values = {
            "opposition_id": opposition.id,
            "title": convocation.title,
            "official_url": convocation.official_url,
            "published_at": convocation.published_at,
            "exam_date": convocation.exam_date,
            "status": convocation.status.value,
            "source_reference": convocation.source_reference,
        }
        if record is None:
            record = ConvocationVersionRecord(
                id=_new_id(), code=convocation.code, **values, created_at=now, updated_at=now
            )
            session.add(record)
            session.flush()
            return record, EntityOutcome(code=convocation.code, created=True, updated=False)

        changed = any(getattr(record, key) != value for key, value in values.items())
        if changed:
            for key, value in values.items():
                setattr(record, key, value)
            record.updated_at = now
        return record, EntityOutcome(code=convocation.code, created=False, updated=changed)

    def _sync_curriculum(
        self,
        session: Session,
        nodes: tuple[CurriculumNode, ...],
        convocation: ConvocationVersionRecord,
    ) -> list[EntityOutcome]:
        existing = {
            row.path: row
            for row in session.execute(
                select(CurriculumNodeRecord).where(
                    CurriculumNodeRecord.convocation_version_id == convocation.id
                )
            )
            .scalars()
            .all()
        }
        outcomes: list[EntityOutcome] = []
        ids_by_path: dict[str, str] = {}
        seen: set[str] = set()

        for node, parent_path in flatten(nodes):
            seen.add(node.path)
            parent_id = ids_by_path.get(parent_path) if parent_path else None
            row = existing.get(node.path)
            if row is None:
                row = CurriculumNodeRecord(
                    id=_new_id(),
                    convocation_version_id=convocation.id,
                    parent_id=parent_id,
                    node_type=node.node_type.value,
                    official_code=node.official_code,
                    title=node.title,
                    description=node.description,
                    position=node.position,
                    path=node.path,
                    depth=node.depth,
                )
                session.add(row)
                session.flush()
                outcomes.append(
                    EntityOutcome(code=f"node:{node.path}", created=True, updated=False)
                )
            else:
                changed = (
                    row.parent_id != parent_id
                    or row.official_code != node.official_code
                    or row.title != node.title
                    or row.description != node.description
                    or row.position != node.position
                    or row.depth != node.depth
                )
                if changed:
                    row.parent_id = parent_id
                    row.official_code = node.official_code
                    row.title = node.title
                    row.description = node.description
                    row.position = node.position
                    row.depth = node.depth
                    outcomes.append(
                        EntityOutcome(code=f"node:{node.path}", created=False, updated=True)
                    )
                else:
                    outcomes.append(
                        EntityOutcome(code=f"node:{node.path}", created=False, updated=False)
                    )
            ids_by_path[node.path] = row.id

        # Nodos que ya no están en el fixture: se eliminan. Hoy nada los referencia; cuando existan
        # mapeos de documentos (S05) habrá que decidir qué hacer antes de borrar, y esa decisión
        # será una migración de datos, no un cambio silencioso aquí.
        stale = [path for path in existing if path not in seen]
        if stale:
            session.execute(
                delete(CurriculumNodeRecord).where(
                    CurriculumNodeRecord.convocation_version_id == convocation.id,
                    CurriculumNodeRecord.path.in_(stale),
                )
            )
            outcomes.extend(
                EntityOutcome(code=f"node:{path}", created=False, updated=True) for path in stale
            )
        return outcomes

    def _sync_parts(
        self, session: Session, parts: tuple[ExamPart, ...], convocation: ConvocationVersionRecord
    ) -> list[EntityOutcome]:
        existing = {
            row.code: row
            for row in session.execute(
                select(ExamPartRecord).where(
                    ExamPartRecord.convocation_version_id == convocation.id
                )
            )
            .scalars()
            .all()
        }
        outcomes: list[EntityOutcome] = []
        ids_by_code: dict[str, str] = {}
        # Primero las agrupaciones (sin padre) y después sus pruebas: así el padre existe al
        # enlazar la clave foránea.
        ordered = sorted(parts, key=lambda part: (part.parent_code is not None, part.position))

        for part in ordered:
            parent_id = ids_by_code.get(part.parent_code) if part.parent_code else None
            values = {
                "parent_id": parent_id,
                "name": part.name,
                "kind": part.kind.value,
                "format": part.format.value if part.format else None,
                "position": part.position,
                "ordinary_items": part.ordinary_items,
                "reserve_items": part.reserve_items,
                "options_per_question": part.options_per_question,
                "score_min": part.score_min,
                "score_max": part.score_max,
                "pass_score": part.pass_score,
                "wrong_penalty_fraction": part.wrong_penalty_fraction,
                "fail_if_errors_gte": part.fail_if_errors_gte,
                "time_minutes": part.time_minutes,
                "structure_note": part.structure_note,
                "notes": part.notes,
                "evidence_quote": part.evidence_quote,
            }
            row = existing.get(part.code)
            if row is None:
                row = ExamPartRecord(
                    id=_new_id(), convocation_version_id=convocation.id, code=part.code, **values
                )
                session.add(row)
                session.flush()
                outcomes.append(
                    EntityOutcome(code=f"part:{part.code}", created=True, updated=False)
                )
            else:
                changed = any(getattr(row, key) != value for key, value in values.items())
                if changed:
                    for key, value in values.items():
                        setattr(row, key, value)
                    outcomes.append(
                        EntityOutcome(code=f"part:{part.code}", created=False, updated=True)
                    )
                else:
                    outcomes.append(
                        EntityOutcome(code=f"part:{part.code}", created=False, updated=False)
                    )
            ids_by_code[part.code] = row.id

        stale = [code for code in existing if code not in ids_by_code]
        if stale:
            session.execute(
                delete(ExamPartRecord).where(
                    ExamPartRecord.convocation_version_id == convocation.id,
                    ExamPartRecord.code.in_(stale),
                )
            )
            outcomes.extend(
                EntityOutcome(code=f"part:{code}", created=False, updated=True) for code in stale
            )
        return outcomes

    def _sync_rules(
        self, session: Session, rules: tuple[ExamRule, ...], convocation: ConvocationVersionRecord
    ) -> list[EntityOutcome]:
        existing = {
            row.code: row
            for row in session.execute(
                select(ExamRuleRecord).where(
                    ExamRuleRecord.convocation_version_id == convocation.id
                )
            )
            .scalars()
            .all()
        }
        outcomes: list[EntityOutcome] = []
        seen: set[str] = set()
        for rule in rules:
            seen.add(rule.code)
            values = {
                "kind": rule.kind.value,
                "value_text": rule.value_text,
                "description": rule.description,
                "evidence_quote": rule.evidence_quote,
            }
            row = existing.get(rule.code)
            if row is None:
                session.add(
                    ExamRuleRecord(
                        id=_new_id(),
                        convocation_version_id=convocation.id,
                        code=rule.code,
                        **values,
                    )
                )
                outcomes.append(
                    EntityOutcome(code=f"rule:{rule.code}", created=True, updated=False)
                )
            else:
                changed = any(getattr(row, key) != value for key, value in values.items())
                if changed:
                    for key, value in values.items():
                        setattr(row, key, value)
                    outcomes.append(
                        EntityOutcome(code=f"rule:{rule.code}", created=False, updated=True)
                    )
                else:
                    outcomes.append(
                        EntityOutcome(code=f"rule:{rule.code}", created=False, updated=False)
                    )
        stale = [code for code in existing if code not in seen]
        if stale:
            session.execute(
                delete(ExamRuleRecord).where(
                    ExamRuleRecord.convocation_version_id == convocation.id,
                    ExamRuleRecord.code.in_(stale),
                )
            )
            outcomes.extend(
                EntityOutcome(code=f"rule:{code}", created=False, updated=True) for code in stale
            )
        return outcomes

    # ------------------------------------------------------------------ conversión

    @staticmethod
    def _convocation_summary(record: ConvocationVersionRecord) -> ConvocationSummary:
        return ConvocationSummary(
            id=record.id,
            opposition_id=record.opposition_id,
            code=record.code,
            title=record.title,
            official_url=record.official_url,
            published_at=record.published_at,
            exam_date=record.exam_date,
            status=ConvocationStatus(record.status),
        )

    def _summary(self, session: Session, record: OppositionRecord) -> OppositionSummary:
        active = session.execute(
            select(ConvocationVersionRecord).where(
                ConvocationVersionRecord.opposition_id == record.id,
                ConvocationVersionRecord.status == ConvocationStatus.ACTIVE.value,
            )
        ).scalar_one_or_none()
        return OppositionSummary(
            id=record.id,
            code=record.code,
            name=record.name,
            description=record.description,
            active=record.active,
            convocation_id=active.id if active else None,
            convocation_code=active.code if active else None,
            convocation_status=ConvocationStatus(active.status) if active else None,
            convocation_published_at=active.published_at if active else None,
        )

    @staticmethod
    def _node(record: CurriculumNodeRecord) -> NodeView:
        return NodeView(
            id=record.id,
            node_type=NodeType(record.node_type),
            official_code=record.official_code,
            title=record.title,
            description=record.description,
            position=record.position,
            path=record.path,
            depth=record.depth,
        )

    def _tree(self, rows: Iterable[CurriculumNodeRecord]) -> tuple[NodeView, ...]:
        by_parent: dict[str | None, list[CurriculumNodeRecord]] = {}
        for row in rows:
            by_parent.setdefault(row.parent_id, []).append(row)

        def build(parent_id: str | None) -> tuple[NodeView, ...]:
            children = sorted(by_parent.get(parent_id, []), key=lambda row: row.position)
            return tuple(
                NodeView(
                    id=row.id,
                    node_type=NodeType(row.node_type),
                    official_code=row.official_code,
                    title=row.title,
                    description=row.description,
                    position=row.position,
                    path=row.path,
                    depth=row.depth,
                    children=build(row.id),
                )
                for row in children
            )

        return build(None)

    @staticmethod
    def _part(record: ExamPartRecord, codes_by_id: dict[str, str]) -> ExamPart:
        return ExamPart(
            code=record.code,
            name=record.name,
            kind=PartKind(record.kind),
            format=PartFormat(record.format) if record.format else None,
            position=record.position,
            parent_code=codes_by_id.get(record.parent_id) if record.parent_id else None,
            ordinary_items=record.ordinary_items,
            reserve_items=record.reserve_items,
            options_per_question=record.options_per_question,
            score_min=record.score_min,
            score_max=record.score_max,
            pass_score=record.pass_score,
            wrong_penalty_fraction=record.wrong_penalty_fraction,
            fail_if_errors_gte=record.fail_if_errors_gte,
            time_minutes=record.time_minutes,
            structure_note=record.structure_note,
            notes=record.notes,
            evidence_quote=record.evidence_quote,
        )

    @staticmethod
    def _rule(record: ExamRuleRecord) -> ExamRule:
        return ExamRule(
            code=record.code,
            kind=RuleKind(record.kind),
            value_text=record.value_text,
            description=record.description,
            evidence_quote=record.evidence_quote,
        )
