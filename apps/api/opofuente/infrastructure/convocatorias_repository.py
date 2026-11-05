"""Siembra idempotente de convocatorias C1 que referencian el temario común (B-006).

Cada convocatoria importada:

1. cuelga de una oposición propia `informatica-c1` (inactiva: la oposición activa sigue siendo la
   que el alumno elige en el selector);
2. conserva su estado de confianza: `draft` si viene de un listado sin bases verificadas, `archived`
   si es una convocatoria cerrada del inventario;
3. referencia la **versión activa del temario común** con papel `primary` y su cita.

No se copia el temario: solo la referencia. Repetir la siembra no duplica nada y `--check` lo
comprueba igual que con los perfiles y el temario.
"""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from opofuente.application.read_models import ConvocatoriasSeedReport, EntityOutcome
from opofuente.domain.convocatorias_c1 import C1Convocatoria, C1ConvocatoriasFixture
from opofuente.domain.errors import InvariantViolationError
from opofuente.infrastructure.db_models import (
    ConvocationCurriculumRefRecord,
    ConvocationVersionRecord,
    CurriculumRecord,
    CurriculumVersionRecord,
    OppositionRecord,
)


def _new_id() -> str:
    return str(uuid4())


class SqlAlchemyConvocatoriasRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def upsert_c1_convocatorias(
        self, fixture: C1ConvocatoriasFixture, *, now: datetime
    ) -> ConvocatoriasSeedReport:
        with self._session_factory() as session:
            common_version = self._common_active_version(session)
            outcomes: list[EntityOutcome] = []
            opposition = self._ensure_opposition(session, fixture, now, outcomes)

            importadas = 0
            por_confirmar = 0
            for convocatoria in fixture.convocatorias:
                convocation = self._ensure_convocation(
                    session, opposition, convocatoria, now, outcomes
                )
                self._ensure_primary_ref(
                    session, convocation, common_version, convocatoria, now, outcomes
                )
                importadas += 1
                if convocatoria.status == "draft":
                    por_confirmar += 1
            session.commit()
            return ConvocatoriasSeedReport(
                entities=tuple(outcomes),
                imported=importadas,
                unverified=por_confirmar,
                discarded=len(fixture.discarded),
            )

    # ------------------------------------------------------------------ piezas

    @staticmethod
    def _common_active_version(session: Session) -> CurriculumVersionRecord:
        version = session.execute(
            select(CurriculumVersionRecord)
            .join(CurriculumRecord, CurriculumRecord.id == CurriculumVersionRecord.curriculum_id)
            .where(
                CurriculumRecord.code == "informatica-c1",
                CurriculumVersionRecord.status == "active",
            )
            .limit(1)
        ).scalar_one_or_none()
        if version is None:
            raise InvariantViolationError(
                "no hay versión activa del temario común: siembra antes el temario (B-002)"
            )
        return version

    @staticmethod
    def _ensure_opposition(
        session: Session,
        fixture: C1ConvocatoriasFixture,
        now: datetime,
        outcomes: list[EntityOutcome],
    ) -> OppositionRecord:
        fila = session.execute(
            select(OppositionRecord).where(OppositionRecord.code == fixture.opposition_code)
        ).scalar_one_or_none()
        if fila is None:
            fila = OppositionRecord(
                id=_new_id(),
                code=fixture.opposition_code,
                name=fixture.opposition_name,
                description=fixture.opposition_description,
                active=False,
                created_at=now,
                updated_at=now,
            )
            session.add(fila)
            session.flush()
            outcomes.append(
                EntityOutcome(
                    code=f"opposition:{fixture.opposition_code}", created=True, updated=False
                )
            )
            return fila
        values = {
            "name": fixture.opposition_name,
            "description": fixture.opposition_description,
            "active": False,
        }
        changed = any(getattr(fila, key) != value for key, value in values.items())
        if changed:
            for key, value in values.items():
                setattr(fila, key, value)
            fila.updated_at = now
        outcomes.append(
            EntityOutcome(
                code=f"opposition:{fixture.opposition_code}",
                created=False,
                updated=changed,
            )
        )
        return fila

    @staticmethod
    def _ensure_convocation(
        session: Session,
        opposition: OppositionRecord,
        convocatoria: C1Convocatoria,
        now: datetime,
        outcomes: list[EntityOutcome],
    ) -> ConvocationVersionRecord:
        fila = session.execute(
            select(ConvocationVersionRecord).where(
                ConvocationVersionRecord.code == convocatoria.code
            )
        ).scalar_one_or_none()
        valores = {
            "opposition_id": opposition.id,
            "title": convocatoria.title,
            "official_url": convocatoria.official_url,
            "published_at": convocatoria.published_at,
            "status": convocatoria.status,
            "source_reference": convocatoria.source_reference,
        }
        if fila is None:
            fila = ConvocationVersionRecord(
                id=_new_id(),
                code=convocatoria.code,
                exam_date=None,
                supersedes_id=None,
                created_at=now,
                updated_at=now,
                **valores,
            )
            session.add(fila)
            session.flush()
            outcomes.append(
                EntityOutcome(code=f"convocation:{convocatoria.code}", created=True, updated=False)
            )
            return fila
        if fila.opposition_id != opposition.id:
            raise InvariantViolationError(
                f"{convocatoria.code} ya existe en otra oposición: el código de convocatoria es "
                "único y no se reutiliza"
            )
        changed = any(getattr(fila, key) != value for key, value in valores.items())
        if changed:
            for key, value in valores.items():
                setattr(fila, key, value)
            fila.updated_at = now
        outcomes.append(
            EntityOutcome(code=f"convocation:{convocatoria.code}", created=False, updated=changed)
        )
        return fila

    @staticmethod
    def _ensure_primary_ref(
        session: Session,
        convocation: ConvocationVersionRecord,
        common_version: CurriculumVersionRecord,
        convocatoria: C1Convocatoria,
        now: datetime,
        outcomes: list[EntityOutcome],
    ) -> None:
        codigo = f"ref:primary:{convocatoria.code}"
        fila = session.execute(
            select(ConvocationCurriculumRefRecord).where(
                ConvocationCurriculumRefRecord.convocation_version_id == convocation.id,
                ConvocationCurriculumRefRecord.role == "primary",
            )
        ).scalar_one_or_none()
        if fila is None:
            mismo_par = session.execute(
                select(ConvocationCurriculumRefRecord).where(
                    ConvocationCurriculumRefRecord.convocation_version_id == convocation.id,
                    ConvocationCurriculumRefRecord.curriculum_version_id == common_version.id,
                )
            ).scalar_one_or_none()
            if mismo_par is not None:
                raise InvariantViolationError(
                    f"{convocatoria.code}: ya referencia el temario común con el papel "
                    f"{mismo_par.role}; no se duplica"
                )
            session.add(
                ConvocationCurriculumRefRecord(
                    id=_new_id(),
                    convocation_version_id=convocation.id,
                    curriculum_version_id=common_version.id,
                    role="primary",
                    source_reference=convocatoria.source_reference,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.flush()
            outcomes.append(EntityOutcome(code=codigo, created=True, updated=False))
            return
        if fila.curriculum_version_id != common_version.id:
            raise InvariantViolationError(
                f"{convocatoria.code}: su referencia primary apunta a otra versión del temario; "
                "la siembra no la re-apunta sola"
            )
        changed = fila.source_reference != convocatoria.source_reference
        if changed:
            fila.source_reference = convocatoria.source_reference
            fila.updated_at = now
        outcomes.append(EntityOutcome(code=codigo, created=False, updated=changed))
