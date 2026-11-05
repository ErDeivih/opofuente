"""Re-atribución del banco del programa publicado al temario común (B-003).

Operación de datos, con su informe y su inverso. Hace tres cosas en una sola transacción:

1. **Guarda las equivalencias** del fixture en `curriculum_equivalences`, con su relación, su
   confianza, su estado y su motivo; las `accepted` quedan con fecha de decisión (lo exige la base);
2. **Re-apunta el material**: cada `curriculum_mappings` y cada `learning_errors` que cuelga de un
   nodo publicado cuyo equivalente está `accepted` pasa al nodo común;
3. **No toca lo dudoso**: las equivalencias `proposed` (y `rejected`) no se aplican; su material se
   queda donde estaba y el informe dice por qué.

Los choques de unicidad (`uq_mapping_identity`: mismo material ya mapeado al nodo destino) **no se
resuelven a la brava**: la fila se informa como conflicto y el mapeo se queda en el nodo publicado
para revisión. Re-ejecutar la misma operación no duplica ni cambia nada.

El inverso se calcula desde el informe (`changes` y `created_equivalence_ids`): devuelve el
material a su nodo publicado y retira las equivalencias que creó esta ejecución, dejando las que ya
existieran.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.remap_models import (
    EquivalenceReportRow,
    InverseResult,
    NodeChange,
    RemapPlan,
)
from opofuente.domain.equivalences import EquivalenceFixture, EquivalenceRow
from opofuente.domain.errors import InvariantViolationError
from opofuente.infrastructure.db_models import (
    CurriculumEquivalenceRecord,
    CurriculumMappingRecord,
    CurriculumNodeRecord,
    CurriculumRecord,
    CurriculumVersionRecord,
    LearningErrorRecord,
)


def _new_id() -> str:
    return str(uuid4())


class _MappingSnapshot:
    __slots__ = ("id", "node_id", "subject_id", "subject_type")

    def __init__(self, id: str, node_id: str, subject_type: str, subject_id: str) -> None:
        self.id = id
        self.node_id = node_id
        self.subject_type = subject_type
        self.subject_id = subject_id


class _ErrorSnapshot:
    __slots__ = ("id", "node_id")

    def __init__(self, id: str, node_id: str) -> None:
        self.id = id
        self.node_id = node_id


class _EquivalenceSnapshot:
    __slots__ = ("confidence", "evidence_note", "id", "relation", "status")

    def __init__(
        self, id: str, relation: str, confidence: float, status: str, evidence_note: str
    ) -> None:
        self.id = id
        self.relation = relation
        self.confidence = confidence
        self.status = status
        self.evidence_note = evidence_note


class SqlAlchemyRemapRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    # ------------------------------------------------------------------ plan y aplicación

    def plan(self, fixture: EquivalenceFixture) -> RemapPlan:
        """Calcula lo que haría la operación, sin escribir nada (dry-run del tool)."""
        with self._session_factory() as session:
            return self._plan(session, fixture)

    def apply(self, fixture: EquivalenceFixture, *, now: datetime) -> RemapPlan:
        """Ejecuta el plan en una transacción y devuelve el informe con los ids creados."""
        with self._session_factory() as session:
            plan = self._plan(session, fixture)
            creadas = self._execute(session, plan, now=now)
            session.commit()
            return replace(plan, created_equivalence_ids=creadas)

    def inverse(self, report: dict[str, Any]) -> InverseResult:
        """Deshace la re-atribución descrita por el informe de una ejecución anterior."""
        changes = report.get("changes")
        created_ids = report.get("created_equivalence_ids")
        if not isinstance(changes, list) or not isinstance(created_ids, list):
            raise InvariantViolationError(
                "el informe no tiene el formato esperado: faltan changes o created_equivalence_ids"
            )

        mapeos = 0
        fallos = 0
        omitidas = 0
        with self._session_factory() as session:
            for change in reversed(changes):
                if not isinstance(change, dict):
                    raise InvariantViolationError("el informe contiene un cambio mal formado")
                tipo = str(change.get("object_type", ""))
                objeto = str(change.get("object_id", ""))
                desde = str(change.get("from_node_id", ""))
                hasta = str(change.get("to_node_id", ""))
                if tipo == "curriculum_mapping":
                    fila = session.get(CurriculumMappingRecord, objeto)
                    if fila is not None and str(fila.curriculum_node_id) == hasta:
                        fila.curriculum_node_id = desde
                        mapeos += 1
                    else:
                        omitidas += 1
                elif tipo == "learning_error":
                    error = session.get(LearningErrorRecord, objeto)
                    if error is not None and str(error.curriculum_node_id) == hasta:
                        error.curriculum_node_id = desde
                        fallos += 1
                    else:
                        omitidas += 1
                else:
                    raise InvariantViolationError(
                        f"tipo de cambio desconocido en el informe: {tipo}"
                    )

            retiradas = 0
            for identificador in created_ids:
                equivalencia = session.get(CurriculumEquivalenceRecord, str(identificador))
                if equivalencia is not None:
                    session.delete(equivalencia)
                    retiradas += 1
            session.commit()

        return InverseResult(
            mappings_reverted=mapeos,
            errors_reverted=fallos,
            equivalences_removed=retiradas,
            skipped=omitidas,
        )

    # ------------------------------------------------------------------ cálculo

    def _plan(self, session: Session, fixture: EquivalenceFixture) -> RemapPlan:
        origen = self._version(session, fixture.source_version_code)
        destino = self._version(session, fixture.target_version_code)
        if origen is None:
            raise InvariantViolationError(
                f"no existe la versión de programa {fixture.source_version_code}; "
                "siembra antes los perfiles"
            )
        if destino is None:
            raise InvariantViolationError(
                f"no existe la versión de temario {fixture.target_version_code}; "
                "siembra antes el temario común"
            )
        origen_id, origen_kind = origen
        destino_id, destino_kind = destino
        if origen_kind != "published":
            raise InvariantViolationError(
                f"{fixture.source_version_code} no es un programa publicado (kind={origen_kind})"
            )
        if destino_kind != "common":
            raise InvariantViolationError(
                f"{fixture.target_version_code} no es el temario común (kind={destino_kind})"
            )

        nodos_origen = self._nodes(session, origen_id)
        nodos_destino = self._nodes(session, destino_id)
        temas_origen = {path: node_id for path, node_id, tipo in nodos_origen if tipo == "topic"}
        temas_destino = {path: node_id for path, node_id, tipo in nodos_destino if tipo == "topic"}

        # Ningún tema publicado puede quedarse sin propuesta: si falta, el banco se re-atribuiría a
        # medias y la ficha del común seguiría vacía sin que nadie lo sepa.
        declarados = {fila.source_path for fila in fixture.rows}
        faltan = sorted(set(temas_origen) - declarados)
        sobran = sorted(declarados - set(temas_origen))
        if faltan or sobran:
            raise InvariantViolationError(
                "el fixture no cubre exactamente los temas publicados: "
                f"faltan {faltan}; sobran {sobran}"
            )

        filas: list[EquivalenceReportRow] = []
        creadas = actualizadas = sin_cambios = 0
        mapeos_vistos = mapeos_movidos = conflictos = 0
        fallos_vistos = fallos_movidos = 0

        for fila in sorted(fixture.rows, key=lambda item: item.source_path):
            source_id = temas_origen[fila.source_path]
            target_id = temas_destino.get(fila.target_path)
            if target_id is None:
                raise InvariantViolationError(
                    f"{fila.source_path}: el tema común {fila.target_path} no existe en "
                    f"{fixture.target_version_code}"
                )
            existente = self._equivalence(session, source_id, target_id)
            accion = self._action(existente, fila)
            if accion == "create":
                creadas += 1
            elif accion == "update":
                actualizadas += 1
            else:
                sin_cambios += 1

            aplicada = fila.status == "accepted"
            cambios_mapeo: list[NodeChange] = []
            cambios_error: list[NodeChange] = []
            avisos: list[str] = []
            mapeos_quedan = 0
            fallos_quedan = 0

            mapeos = self._mappings_of(session, source_id)
            errores = self._errors_of(session, source_id)
            mapeos_vistos += len(mapeos)
            fallos_vistos += len(errores)
            if aplicada:
                for mapeo in mapeos:
                    if self._mapping_exists(
                        session, target_id, mapeo.subject_type, mapeo.subject_id, mapeo.id
                    ):
                        conflictos += 1
                        avisos.append(
                            f"mapeo {mapeo.id} ({mapeo.subject_type} {mapeo.subject_id}): el nodo "
                            f"común {fila.target_path} ya tiene ese material; se queda en "
                            f"{fila.source_path} para revisar"
                        )
                        continue
                    mapeos_movidos += 1
                    cambios_mapeo.append(
                        NodeChange(
                            object_type="curriculum_mapping",
                            object_id=mapeo.id,
                            subject_type=mapeo.subject_type,
                            subject_id=mapeo.subject_id,
                            from_node_id=source_id,
                            from_path=fila.source_path,
                            to_node_id=target_id,
                            to_path=fila.target_path,
                        )
                    )
                for error in errores:
                    fallos_movidos += 1
                    cambios_error.append(
                        NodeChange(
                            object_type="learning_error",
                            object_id=error.id,
                            subject_type=None,
                            subject_id=None,
                            from_node_id=source_id,
                            from_path=fila.source_path,
                            to_node_id=target_id,
                            to_path=fila.target_path,
                        )
                    )
            else:
                mapeos_quedan = len(mapeos)
                fallos_quedan = len(errores)

            filas.append(
                EquivalenceReportRow(
                    source_path=fila.source_path,
                    target_path=fila.target_path,
                    relation=fila.relation,
                    status=fila.status,
                    confidence=fila.confidence,
                    evidence_note=fila.evidence_note,
                    applied=aplicada,
                    source_node_id=source_id,
                    target_node_id=target_id,
                    equivalence_id=existente.id if existente is not None else None,
                    equivalence_action=accion,
                    mappings=tuple(cambios_mapeo),
                    learning_errors=tuple(cambios_error),
                    conflicts=tuple(avisos),
                    kept_mappings=mapeos_quedan,
                    kept_learning_errors=fallos_quedan,
                )
            )

        return RemapPlan(
            source_version_code=fixture.source_version_code,
            target_version_code=fixture.target_version_code,
            rows=tuple(filas),
            equivalences_created=creadas,
            equivalences_updated=actualizadas,
            equivalences_unchanged=sin_cambios,
            mappings_examined=mapeos_vistos,
            mappings_moved=mapeos_movidos,
            mappings_conflicts=conflictos,
            errors_examined=fallos_vistos,
            errors_moved=fallos_movidos,
        )

    @staticmethod
    def _action(existente: _EquivalenceSnapshot | None, fila: EquivalenceRow) -> str:
        if existente is None:
            return "create"
        if (
            existente.relation != fila.relation
            or existente.confidence != fila.confidence
            or existente.status != fila.status
            or existente.evidence_note != fila.evidence_note
        ):
            return "update"
        return "none"

    def _execute(self, session: Session, plan: RemapPlan, *, now: datetime) -> tuple[str, ...]:
        creadas: list[str] = []
        for fila in plan.rows:
            if fila.equivalence_action == "create":
                identificador = _new_id()
                session.add(
                    CurriculumEquivalenceRecord(
                        id=identificador,
                        source_node_id=fila.source_node_id,
                        target_node_id=fila.target_node_id,
                        relation=fila.relation,
                        confidence=fila.confidence,
                        status=fila.status,
                        evidence_note=fila.evidence_note,
                        created_at=now,
                        decided_at=now if fila.status == "accepted" else None,
                    )
                )
                creadas.append(identificador)
            elif fila.equivalence_action == "update" and fila.equivalence_id is not None:
                equivalencia = session.get(CurriculumEquivalenceRecord, fila.equivalence_id)
                if equivalencia is not None:  # pragma: no cover - el plan la ha leído
                    equivalencia.relation = fila.relation
                    equivalencia.confidence = fila.confidence
                    equivalencia.status = fila.status
                    equivalencia.evidence_note = fila.evidence_note
                    if fila.status == "accepted":
                        equivalencia.decided_at = now

            for cambio in fila.mappings:
                mapeo = session.get(CurriculumMappingRecord, cambio.object_id)
                if mapeo is not None:  # pragma: no cover - el plan lo ha leído
                    mapeo.curriculum_node_id = cambio.to_node_id
            for cambio in fila.learning_errors:
                error = session.get(LearningErrorRecord, cambio.object_id)
                if error is not None:  # pragma: no cover - el plan lo ha leído
                    error.curriculum_node_id = cambio.to_node_id
        return tuple(creadas)

    # ------------------------------------------------------------------ lecturas

    @staticmethod
    def _version(session: Session, code: str) -> tuple[str, str] | None:
        fila = session.execute(
            select(CurriculumVersionRecord, CurriculumVersionRecord.curriculum_id)
            .where(CurriculumVersionRecord.code == code)
            .limit(1)
        ).first()
        if fila is None:
            return None
        version = fila[0]
        return version.id, _curriculum_kind(session, version.curriculum_id)

    @staticmethod
    def _nodes(session: Session, version_id: str) -> list[tuple[str, str, str]]:
        return [
            (str(fila.path), str(fila.id), str(fila.node_type))
            for fila in session.execute(
                select(CurriculumNodeRecord).where(
                    CurriculumNodeRecord.curriculum_version_id == version_id
                )
            )
            .scalars()
            .all()
        ]

    @staticmethod
    def _equivalence(
        session: Session, source_id: str, target_id: str
    ) -> _EquivalenceSnapshot | None:
        fila = session.execute(
            select(CurriculumEquivalenceRecord).where(
                CurriculumEquivalenceRecord.source_node_id == source_id,
                CurriculumEquivalenceRecord.target_node_id == target_id,
            )
        ).scalar_one_or_none()
        if fila is None:
            return None
        return _EquivalenceSnapshot(
            id=fila.id,
            relation=fila.relation,
            confidence=fila.confidence,
            status=fila.status,
            evidence_note=fila.evidence_note or "",
        )

    @staticmethod
    def _mappings_of(session: Session, node_id: str) -> list[_MappingSnapshot]:
        filas = (
            session.execute(
                select(CurriculumMappingRecord).where(
                    CurriculumMappingRecord.curriculum_node_id == node_id
                )
            )
            .scalars()
            .all()
        )
        return [
            _MappingSnapshot(
                id=fila.id,
                node_id=fila.curriculum_node_id,
                subject_type=fila.subject_type,
                subject_id=fila.subject_id,
            )
            for fila in filas
        ]

    @staticmethod
    def _errors_of(session: Session, node_id: str) -> list[_ErrorSnapshot]:
        filas = (
            session.execute(
                select(LearningErrorRecord).where(LearningErrorRecord.curriculum_node_id == node_id)
            )
            .scalars()
            .all()
        )
        return [_ErrorSnapshot(id=fila.id, node_id=str(fila.curriculum_node_id)) for fila in filas]

    @staticmethod
    def _mapping_exists(
        session: Session,
        node_id: str,
        subject_type: str,
        subject_id: str,
        exclude_id: str,
    ) -> bool:
        fila = session.execute(
            select(CurriculumMappingRecord.id).where(
                CurriculumMappingRecord.curriculum_node_id == node_id,
                CurriculumMappingRecord.subject_type == subject_type,
                CurriculumMappingRecord.subject_id == subject_id,
                CurriculumMappingRecord.id != exclude_id,
            )
        ).first()
        return fila is not None


def _curriculum_kind(session: Session, curriculum_id: str) -> str:
    """Tipo del temario (`common` o `published`) al que pertenece una versión."""
    fila = session.execute(
        select(CurriculumRecord.kind).where(CurriculumRecord.id == curriculum_id)
    ).scalar_one_or_none()
    if fila is None:  # pragma: no cover - la clave foránea lo impide
        raise InvariantViolationError("una versión de temario sin temario")
    return str(fila)
