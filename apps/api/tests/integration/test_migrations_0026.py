"""Migración 0026: los exámenes oficiales del INAP pasan a `public` en los datos.

Lo que se prueba, con datos que se parecen a los de verdad:

- los **cuatro exámenes oficiales del INAP de TAI 2025** quedan en `public`;
- los **bancos privados** del propietario se quedan en `personal` (la migración no toca lo que no es
  suyo: un banco privado que se hiciera público por descuido sería el fallo más caro de esta fase);
- las copias **archivadas** de esos mismos exámenes —la base real tiene cuatro, de una primera
  importación— no se marcan: ya no son los exámenes vigentes;
- la vuelta atrás devuelve esos conjuntos a `personal`, sin tocar los demás.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import text

from alembic import command
from opofuente.config import Settings
from opofuente.infrastructure.db import build_engine
from opofuente.infrastructure.migrations import alembic_config, run_migrations

AHORA = datetime(2026, 10, 7, 9, 0, tzinfo=UTC)
DESDE = "0025_question_set_distribution"

#: Un examen oficial del INAP con su clave activa (el que se hace hoy).
_EXAMEN_VIGENTE = (
    "INSERT INTO question_sets (id, title, opposition_id, set_type, model_code, status, "
    "created_at, updated_at) VALUES (:id, :titulo, 'op-1', 'official_exam', 'A', 'draft', "
    ":ahora, :ahora)"
)

#: La copia archivada del mismo examen, de una importación anterior.
_EXAMEN_ARCHIVADO = (
    "INSERT INTO question_sets (id, title, opposition_id, set_type, model_code, status, "
    "created_at, updated_at) VALUES (:id, :titulo, 'op-1', 'official_exam', 'A', 'archived', "
    ":ahora, :ahora)"
)

#: Un banco privado del propietario.
_BANCO_PRIVADO = (
    "INSERT INTO question_sets (id, title, opposition_id, set_type, status, created_at, "
    "updated_at) VALUES (:id, :titulo, 'op-1', 'private_bank', 'draft', :ahora, :ahora)"
)

CINCO_TITULOS: tuple[str, ...] = (
    "TAI ingreso libre 2025 · modelo A (examen oficial INAP)",
    "TAI ingreso libre 2025 · modelo B (examen oficial INAP)",
    "TAI promoción interna 2025 · modelo A (examen oficial INAP)",
    "TAI promoción interna 2025 · modelo B (examen oficial INAP)",
)


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "datos", _env_file=None)


def _ejecutar(settings: Settings, sentencia: str, parametros: dict[str, object]) -> None:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.begin() as conexion:
            conexion.execute(text(sentencia), parametros)
    finally:
        engine.dispose()


def _filas(settings: Settings) -> list[tuple[object, object]]:
    engine = build_engine(settings.data_paths.database)
    try:
        with engine.connect() as conexion:
            return list(
                conexion.execute(
                    text("SELECT id, distribution FROM question_sets ORDER BY id")
                ).all()
            )
    finally:
        engine.dispose()


def _sembrar(settings: Settings) -> None:
    _ejecutar(
        settings,
        "INSERT INTO oppositions (id, code, name, active, created_at, updated_at) VALUES "
        "('op-1', 'tai', 'TAI', 0, :ahora, :ahora)",
        {"ahora": AHORA},
    )
    for indice, titulo in enumerate(CINCO_TITULOS, start=1):
        _ejecutar(
            settings,
            _EXAMEN_VIGENTE,
            {"id": f"examen-{indice}", "titulo": titulo, "ahora": AHORA},
        )
        _ejecutar(
            settings,
            _EXAMEN_ARCHIVADO,
            {"id": f"examen-{indice}-archivado", "titulo": titulo, "ahora": AHORA},
        )
    _ejecutar(
        settings,
        _BANCO_PRIVADO,
        {"id": "banco-1", "titulo": "Rojo - General (banco privado)", "ahora": AHORA},
    )


def test_los_examenes_oficiales_quedan_publicos_y_lo_demas_no(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision=DESDE)
    _sembrar(settings)

    run_migrations(settings, revision="head")

    distribucion = dict(_filas(settings))
    for indice in range(1, len(CINCO_TITULOS) + 1):
        assert distribucion[f"examen-{indice}"] == "public"
        assert distribucion[f"examen-{indice}-archivado"] == "personal"
    assert distribucion["banco-1"] == "personal"


def test_la_vuelta_atras_los_devuelve_a_personal(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    run_migrations(settings, revision=DESDE)
    _sembrar(settings)
    run_migrations(settings, revision="head")

    command.downgrade(alembic_config(settings), DESDE)

    assert {str(fila[1]) for fila in _filas(settings)} == {"personal"}


def test_sobre_una_base_vacia_no_hace_nada(tmp_path: Path) -> None:
    """La puerta 13 migra desde cero: la sentencia tiene que poder ejecutarse sin filas."""
    settings = _settings(tmp_path)

    run_migrations(settings, revision="head")

    assert _filas(settings) == []
