"""Repositorio SQLAlchemy del temario común y de las referencias de las convocatorias.

La siembra es idempotente por ruta dentro de la edición (`ADR-007`, `ESPECIFICACION.md` §6.7):

- la fila del temario y su versión se buscan por `code`; repetir la siembra no las duplica;
- los nodos se sincronizan por `path` dentro de la versión: se crean los que faltan, se actualizan
  los que cambiaron y se retiran los que ya no están, **salvo** los que tienen material asignado
  (`curriculum_mappings` con `ON DELETE RESTRICT`, la red de seguridad de ADR-007);
- la versión se publica (`draft` → `active`) solo cuando el recuento real cuadra con el de
  publicación; un temario incompleto se queda en borrador;
- una versión **activa no se edita** (I9): si el fixture cambia, la siembra avisa y no reescribe la
  edición que ya estudian las convocatorias;
- las referencias del fixture se crean o se actualizan en su cita, pero **no se re-apuntan solas** a
  otra versión: cambiar qué edición estudia una convocatoria es una decisión de publicación.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.read_models import CurriculumSeedReport, EntityOutcome
from opofuente.domain.curricula import CommonCurriculum, publication_counts
from opofuente.domain.errors import InvariantViolationError
from opofuente.domain.profiles import CurriculumNode, flatten
from opofuente.infrastructure.db_models import (
    ConvocationCurriculumRefRecord,
    ConvocationVersionRecord,
    CurriculumMappingRecord,
    CurriculumNodeRecord,
    CurriculumRecord,
    CurriculumVersionRecord,
)


def _new_id() -> str:
    return str(uuid4())


def _nodo_cambia(fila: CurriculumNodeRecord, node: CurriculumNode, parent_id: str | None) -> bool:
    """¿Difiere el nodo guardado del que trae el fixture? (incluida la procedencia)."""
    return (
        fila.parent_id != parent_id
        or fila.node_type != node.node_type.value
        or fila.official_code != node.official_code
        or fila.title != node.title
        or fila.description != node.description
        or fila.position != node.position
        or fila.depth != node.depth
        or fila.origin_kind != "base"
    )


class SqlAlchemyCurriculumRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def upsert_common_curriculum(
        self, curriculum: CommonCurriculum, *, now: datetime
    ) -> CurriculumSeedReport:
        with self._session_factory() as session:
            outcomes: list[EntityOutcome] = []
            fila = self._ensure_curriculum(session, curriculum, now, outcomes)
            version = self._ensure_version(session, fila, curriculum, now, outcomes)
            counts = self._sync_nodes(session, version, curriculum, outcomes)
            publicado = self._publish_if_complete(
                session, version, curriculum, counts, now, outcomes
            )
            self._sync_references(session, version, curriculum, now, outcomes)
            session.commit()
            return CurriculumSeedReport(
                entities=tuple(outcomes), published=publicado, counts=counts
            )

    # ------------------------------------------------------------------ fila y edición

    def _ensure_curriculum(
        self,
        session: Session,
        curriculum: CommonCurriculum,
        now: datetime,
        outcomes: list[EntityOutcome],
    ) -> CurriculumRecord:
        fila = session.execute(
            select(CurriculumRecord).where(CurriculumRecord.code == curriculum.code)
        ).scalar_one_or_none()
        if fila is None:
            fila = CurriculumRecord(
                id=_new_id(),
                code=curriculum.code,
                kind="common",
                name=curriculum.name,
                description=None,
                group_code=curriculum.group_code,
                family=curriculum.family,
                created_at=now,
                updated_at=now,
            )
            session.add(fila)
            session.flush()
            outcomes.append(
                EntityOutcome(code=f"curriculum:{curriculum.code}", created=True, updated=False)
            )
            return fila

        values = {
            "kind": "common",
            "name": curriculum.name,
            "group_code": curriculum.group_code,
            "family": curriculum.family,
        }
        changed = any(getattr(fila, key) != value for key, value in values.items())
        if changed:
            for key, value in values.items():
                setattr(fila, key, value)
            fila.updated_at = now
        outcomes.append(
            EntityOutcome(code=f"curriculum:{curriculum.code}", created=False, updated=changed)
        )
        return fila

    def _ensure_version(
        self,
        session: Session,
        curriculum_row: CurriculumRecord,
        curriculum: CommonCurriculum,
        now: datetime,
        outcomes: list[EntityOutcome],
    ) -> CurriculumVersionRecord:
        version = session.execute(
            select(CurriculumVersionRecord).where(
                CurriculumVersionRecord.code == curriculum.version_code
            )
        ).scalar_one_or_none()
        source_reference = f"{curriculum.source.document}, sha256 {curriculum.source.sha256}"

        if version is None:
            version = CurriculumVersionRecord(
                id=_new_id(),
                curriculum_id=curriculum_row.id,
                version_no=curriculum.version_no,
                code=curriculum.version_code,
                title=curriculum.title,
                status="draft",
                source_reference=source_reference,
                supersedes_id=None,
                created_at=now,
                updated_at=now,
            )
            session.add(version)
            session.flush()
            outcomes.append(
                EntityOutcome(
                    code=f"curriculum-version:{curriculum.version_code}",
                    created=True,
                    updated=False,
                )
            )
            return version

        if version.curriculum_id != curriculum_row.id:
            raise InvariantViolationError(
                f"{curriculum.version_code} ya existe bajo otro temario; no se reutiliza un código"
            )
        values = {
            "curriculum_id": curriculum_row.id,
            "version_no": curriculum.version_no,
            "title": curriculum.title,
            "source_reference": source_reference,
        }
        changed = any(getattr(version, key) != value for key, value in values.items())
        if version.status == "active" and changed:
            raise InvariantViolationError(
                f"{curriculum.version_code} está activa: una versión activa no se edita (I9); "
                "publica una edición nueva con su número de versión"
            )
        if changed:
            for key, value in values.items():
                setattr(version, key, value)
            version.updated_at = now
        outcomes.append(
            EntityOutcome(
                code=f"curriculum-version:{curriculum.version_code}",
                created=False,
                updated=changed,
            )
        )
        return version

    # ------------------------------------------------------------------ nodos

    def _sync_nodes(
        self,
        session: Session,
        version: CurriculumVersionRecord,
        curriculum: CommonCurriculum,
        outcomes: list[EntityOutcome],
    ) -> dict[str, int]:
        existentes = {
            fila.path: fila
            for fila in session.execute(
                select(CurriculumNodeRecord).where(
                    CurriculumNodeRecord.curriculum_version_id == version.id
                )
            )
            .scalars()
            .all()
        }

        # Planificación antes de escribir: si la versión está activa hay que saber si algo cambiaría
        # **antes** de tocarla, no a mitad.
        ids_por_ruta: dict[str, str] = {}
        crea: list[tuple[CurriculumNode, str | None, str]] = []
        actualiza: list[tuple[CurriculumNode, CurriculumNodeRecord, str | None]] = []
        sin_cambios: list[str] = []
        for node, parent_path in flatten(curriculum.nodes):
            parent_id = ids_por_ruta.get(parent_path) if parent_path else None
            fila = existentes.get(node.path)
            if fila is None:
                nuevo_id = _new_id()
                ids_por_ruta[node.path] = nuevo_id
                crea.append((node, parent_id, nuevo_id))
                continue
            ids_por_ruta[node.path] = fila.id
            if _nodo_cambia(fila, node, parent_id):
                actualiza.append((node, fila, parent_id))
            else:
                sin_cambios.append(node.path)

        vistas = set(ids_por_ruta)
        stale = [path for path in existentes if path not in vistas]
        con_material = self._nodes_with_material(session, [existentes[path].id for path in stale])
        retirables = [path for path in stale if existentes[path].id not in con_material]
        retirables_set = set(retirables)
        bloqueados = [path for path in stale if path not in retirables_set]

        if version.status == "active" and (crea or actualiza or retirables):
            raise InvariantViolationError(
                f"{curriculum.version_code} está activa: una versión activa no se edita (I9); "
                "crea la siguiente edición en lugar de cambiar la que estudian las convocatorias"
            )

        for node, parent_id, nuevo_id in crea:
            session.add(
                CurriculumNodeRecord(
                    id=nuevo_id,
                    curriculum_version_id=version.id,
                    parent_id=parent_id,
                    node_type=node.node_type.value,
                    official_code=node.official_code,
                    title=node.title,
                    description=node.description,
                    position=node.position,
                    path=node.path,
                    depth=node.depth,
                    origin_kind="base",
                )
            )
            # En preorden el padre siempre se ha creado antes: la clave foránea se puede comprobar.
            session.flush()
        for node, fila, parent_id in actualiza:
            fila.parent_id = parent_id
            fila.official_code = node.official_code
            fila.title = node.title
            fila.description = node.description
            fila.position = node.position
            fila.depth = node.depth
            fila.node_type = node.node_type.value

        if retirables:
            session.execute(
                delete(CurriculumNodeRecord).where(
                    CurriculumNodeRecord.curriculum_version_id == version.id,
                    CurriculumNodeRecord.path.in_(retirables),
                )
            )

        outcomes.extend(
            EntityOutcome(code=f"node:{node.path}", created=True, updated=False)
            for node, _parent, _identificador in crea
        )
        outcomes.extend(
            EntityOutcome(code=f"node:{path}", created=False, updated=False) for path in sin_cambios
        )
        outcomes.extend(
            EntityOutcome(code=f"node:{node.path}", created=False, updated=True)
            for node, _fila, _parent in actualiza
        )
        outcomes.extend(
            EntityOutcome(code=f"node:{path}", created=False, updated=True) for path in retirables
        )
        outcomes.extend(
            EntityOutcome(code=f"node:{path}", created=False, updated=False, blocked=True)
            for path in bloqueados
        )
        return self._counts(session, version.id)

    @staticmethod
    def _nodes_with_material(session: Session, node_ids: list[str]) -> set[str]:
        if not node_ids:
            return set()
        filas = session.execute(
            select(CurriculumMappingRecord.curriculum_node_id).where(
                CurriculumMappingRecord.curriculum_node_id.in_(node_ids)
            )
        ).all()
        return {str(fila[0]) for fila in filas}

    @staticmethod
    def _counts(session: Session, version_id: str) -> dict[str, int]:
        filas = session.execute(
            select(CurriculumNodeRecord.node_type, func.count())
            .where(CurriculumNodeRecord.curriculum_version_id == version_id)
            .group_by(CurriculumNodeRecord.node_type)
        ).all()
        por_tipo = {str(tipo): int(total) for tipo, total in filas}
        return {
            "blocks": por_tipo.get("block", 0),
            "topics": por_tipo.get("topic", 0),
            "nodes": sum(por_tipo.values()),
        }

    # ------------------------------------------------------------------ publicación y referencias

    def _publish_if_complete(
        self,
        session: Session,
        version: CurriculumVersionRecord,
        curriculum: CommonCurriculum,
        counts: dict[str, int],
        now: datetime,
        outcomes: list[EntityOutcome],
    ) -> bool:
        esperados = publication_counts(curriculum)
        if counts != esperados:
            if version.status == "active":
                raise InvariantViolationError(
                    f"{curriculum.version_code} está activa pero tiene {counts} y el contrato de "
                    f"publicación es {esperados}: alguien editó la edición publicada"
                )
            return False
        if version.status == "active":
            return True
        if version.status != "draft":
            raise InvariantViolationError(
                f"{curriculum.version_code} está {version.status}: solo una versión en borrador "
                "se puede publicar"
            )
        otra_activa = session.execute(
            select(CurriculumVersionRecord.id).where(
                CurriculumVersionRecord.curriculum_id == version.curriculum_id,
                CurriculumVersionRecord.status == "active",
                CurriculumVersionRecord.id != version.id,
            )
        ).first()
        if otra_activa is not None:
            raise InvariantViolationError(
                f"{curriculum.code}: ya hay otra versión activa; publica esta desde la anterior "
                "en lugar de dejar dos ediciones vivas"
            )
        version.status = "active"
        version.updated_at = now
        outcomes.append(
            EntityOutcome(
                code=f"curriculum-published:{curriculum.version_code}", created=False, updated=True
            )
        )
        return True

    def _sync_references(
        self,
        session: Session,
        version: CurriculumVersionRecord,
        curriculum: CommonCurriculum,
        now: datetime,
        outcomes: list[EntityOutcome],
    ) -> None:
        for referencia in curriculum.references:
            convocatoria = session.execute(
                select(ConvocationVersionRecord).where(
                    ConvocationVersionRecord.code == referencia.convocation_code
                )
            ).scalar_one_or_none()
            if convocatoria is None:
                raise InvariantViolationError(
                    f"{curriculum.code}: la referencia apunta a la convocatoria "
                    f"{referencia.convocation_code}, que no existe; siembra antes los perfiles"
                )
            codigo = f"ref:{referencia.role}:{referencia.convocation_code}"
            existente = session.execute(
                select(ConvocationCurriculumRefRecord).where(
                    ConvocationCurriculumRefRecord.convocation_version_id == convocatoria.id,
                    ConvocationCurriculumRefRecord.role == referencia.role,
                )
            ).scalar_one_or_none()
            if existente is not None:
                if existente.curriculum_version_id != version.id:
                    raise InvariantViolationError(
                        f"{referencia.convocation_code}: su referencia {referencia.role} apunta a "
                        "otra versión del temario; la siembra no la re-apunta sola"
                    )
                changed = existente.source_reference != referencia.source_reference
                if changed:
                    existente.source_reference = referencia.source_reference
                    existente.updated_at = now
                outcomes.append(EntityOutcome(code=codigo, created=False, updated=changed))
                continue

            mismo_par = session.execute(
                select(ConvocationCurriculumRefRecord).where(
                    ConvocationCurriculumRefRecord.convocation_version_id == convocatoria.id,
                    ConvocationCurriculumRefRecord.curriculum_version_id == version.id,
                )
            ).scalar_one_or_none()
            if mismo_par is not None:
                raise InvariantViolationError(
                    f"{referencia.convocation_code}: ya referencia esta versión con el papel "
                    f"{mismo_par.role}; no se duplica la referencia"
                )
            session.add(
                ConvocationCurriculumRefRecord(
                    id=_new_id(),
                    convocation_version_id=convocatoria.id,
                    curriculum_version_id=version.id,
                    role=referencia.role,
                    source_reference=referencia.source_reference,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.flush()
            outcomes.append(EntityOutcome(code=codigo, created=True, updated=False))
