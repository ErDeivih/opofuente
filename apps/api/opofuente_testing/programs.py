"""Ayudas de siembra sintética para las pruebas de integración.

Las pruebas que insertan nodos de programa con SQL crudo necesitan antes el envoltorio publicado que
introdujo `0021`: un temario `published`, su versión `active` y la referencia `official` de la
convocatoria. Centralizarlo aquí evita que cada prueba invente códigos o columnas distintas de las
que crea la siembra real, y sigue la convención del proyecto: los ayudantes de prueba viven en
`opofuente_testing`, no en la carpeta de pruebas (ver `pyproject.toml`).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import Connection


def insert_published_program(
    connection: Connection, *, convocation_id: str, convocation_code: str
) -> str:
    """Crea el envoltorio publicado de una convocatoria y devuelve su versión de temario.

    Desde `0021` los nodos de programa no cuelgan de la convocatoria: cuelgan de una versión de
    temario, y la convocatoria la referencia con `role='official'`. Las pruebas que insertan nodos
    con SQL crudo necesitan ese envoltorio primero. Los códigos son los mismos que usan la migración
    y la siembra (`<convocation>-programa` y `<convocation>-programa-v1`).
    """
    ahora = datetime.now(UTC)
    curriculum_id = str(uuid4())
    version_id = str(uuid4())
    code = f"{convocation_code}-programa"
    connection.execute(
        text(
            "INSERT INTO curricula (id, code, kind, name, description, group_code, family, "
            "created_at, updated_at) VALUES (:id, :code, 'published', :nombre, NULL, NULL, NULL, "
            ":ahora, :ahora)"
        ),
        {"id": curriculum_id, "code": code, "nombre": convocation_code, "ahora": ahora},
    )
    connection.execute(
        text(
            "INSERT INTO curriculum_versions (id, curriculum_id, version_no, code, title, status, "
            "source_reference, supersedes_id, created_at, updated_at) VALUES "
            "(:id, :curriculum, 1, :code, :nombre, 'active', NULL, NULL, :ahora, :ahora)"
        ),
        {
            "id": version_id,
            "curriculum": curriculum_id,
            "code": f"{code}-v1",
            "nombre": convocation_code,
            "ahora": ahora,
        },
    )
    connection.execute(
        text(
            "INSERT INTO convocation_curriculum_refs (id, convocation_version_id, "
            "curriculum_version_id, role, source_reference, created_at, updated_at) VALUES "
            "(:id, :convocatoria, :version, 'official', NULL, :ahora, :ahora)"
        ),
        {
            "id": str(uuid4()),
            "convocatoria": convocation_id,
            "version": version_id,
            "ahora": ahora,
        },
    )
    return version_id
