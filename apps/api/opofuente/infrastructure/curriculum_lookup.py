"""Consultas compartidas del vínculo entre una convocatoria y su versión de temario.

Desde `0021` el programa no cuelga de la convocatoria: cuelga de una versión de temario, y la
convocatoria la referencia con un papel (`official` para el programa que publica, `primary` para el
temario común que estudia). Varios repositorios necesitan resolver ese camino —
convocatoria → referencia → versión → nodos— y no conviene que cada uno lo escriba a su manera: una
diferencia de criterio aquí cambia en silencio qué árbol ve el usuario.

Este módulo no decide producto: solo dice **dónde está** el programa publicado de una convocatoria.
Cuando el alumno pase a estudiar el temario común (B-002/B-004) se añadirá aquí la resolución de
`primary`, con su propia prueba, en lugar de repartir la regla por los repositorios.
"""

from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from opofuente.infrastructure.db_models import (
    ConvocationCurriculumRefRecord,
    ConvocationVersionRecord,
    CurriculumNodeRecord,
)

#: Papel de la referencia que enlaza una convocatoria con el programa que publica.
ROLE_OFFICIAL = "official"


def official_version_id(session: Session, convocation_id: str) -> str | None:
    """Versión del programa publicado de una convocatoria, o `None` si no publica temario.

    Devuelve `None` en vez de fallar: una convocatoria sin programa existe y no es un error (§6.4).
    """
    return session.execute(official_version_query(convocation_id)).scalar_one_or_none()


def official_version_query(convocation_id: str) -> Select[tuple[str]]:
    return (
        select(ConvocationCurriculumRefRecord.curriculum_version_id)
        .where(
            ConvocationCurriculumRefRecord.convocation_version_id == convocation_id,
            ConvocationCurriculumRefRecord.role == ROLE_OFFICIAL,
        )
        .limit(1)
    )


def convocation_of_version(
    session: Session, curriculum_version_id: str
) -> ConvocationVersionRecord | None:
    """Convocatoria cuyo programa publicado es esa versión, si la hay.

    Un nodo del temario común no tendrá convocatoria: es justamente lo que distingue un nodo común
    de uno publicado, y por eso se devuelve `None` en lugar de inventar una.
    """
    return session.execute(convocation_of_version_query(curriculum_version_id)).scalar_one_or_none()


def convocation_of_version_query(
    curriculum_version_id: str,
) -> Select[tuple[ConvocationVersionRecord]]:
    return (
        select(ConvocationVersionRecord)
        .join(
            ConvocationCurriculumRefRecord,
            ConvocationCurriculumRefRecord.convocation_version_id == ConvocationVersionRecord.id,
        )
        .where(
            ConvocationCurriculumRefRecord.curriculum_version_id == curriculum_version_id,
            ConvocationCurriculumRefRecord.role == ROLE_OFFICIAL,
        )
        .limit(1)
    )


def official_version_id_by_convocation_code(session: Session, convocation_code: str) -> str | None:
    """Versión del programa publicado de una convocatoria, buscándola por su código.

    La cobertura y varias vistas de administración piden el programa por `convocation_code` (es lo
    que viaja en sus DTO), no por id. El código es único, así que la búsqueda es determinista.
    """
    return session.execute(
        select(ConvocationCurriculumRefRecord.curriculum_version_id)
        .join(
            ConvocationVersionRecord,
            ConvocationVersionRecord.id == ConvocationCurriculumRefRecord.convocation_version_id,
        )
        .where(
            ConvocationVersionRecord.code == convocation_code,
            ConvocationCurriculumRefRecord.role == ROLE_OFFICIAL,
        )
        .limit(1)
    ).scalar_one_or_none()


def version_ids_of_opposition(opposition_id: str) -> Select[tuple[str]]:
    """Versiones de los programas publicados por las convocatorias de una oposición."""
    return (
        select(ConvocationCurriculumRefRecord.curriculum_version_id)
        .join(
            ConvocationVersionRecord,
            ConvocationVersionRecord.id == ConvocationCurriculumRefRecord.convocation_version_id,
        )
        .where(
            ConvocationVersionRecord.opposition_id == opposition_id,
            ConvocationCurriculumRefRecord.role == ROLE_OFFICIAL,
        )
    )


def node_ids_of_opposition(opposition_id: str) -> Select[tuple[str]]:
    """Nodos de los programas publicados por las convocatorias de una oposición."""
    return select(CurriculumNodeRecord.id).where(
        CurriculumNodeRecord.curriculum_version_id.in_(version_ids_of_opposition(opposition_id))
    )


def nodes_of_version_query(curriculum_version_id: str) -> Select[tuple[CurriculumNodeRecord]]:
    return select(CurriculumNodeRecord).where(
        CurriculumNodeRecord.curriculum_version_id == curriculum_version_id
    )
