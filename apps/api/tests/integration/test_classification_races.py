"""Pruebas de la tolerancia a carreras al guardar propuestas de clasificación (S04, cerrada en S05).

El worker clasifica el material en cuanto se extrae (`JobType.CLASSIFY_DOCUMENT`) y una pasada
explícita puede coincidir con él: los dos guardan **las mismas** propuestas y SQLite rechaza la
segunda inserción con `IntegrityError`. Antes, eso salía como un **500** en la ruta de pasadas de
clasificación (lo destapó el E2E de la biblioteca al compartir servidor con el worker).

Aquí el choque se reproduce **de forma determinista**: la primera confirmación falla con el mismo
error que produce el choque real, y la segunda tiene que salir bien contando la propuesta como
existente. Va en su propio fichero porque es una prueba de infraestructura —necesita una fábrica de
sesiones que falle a la primera— y no del guion del usuario.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.exc import IntegrityError

from opofuente.config import Settings
from opofuente.domain.classification import Axis, Proposal, SubjectType
from opofuente.infrastructure.classification_repository import SqlAlchemyClassificationRepository
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.migrations import run_migrations
from opofuente.infrastructure.representation_store import RepresentationStore

AHORA = datetime(2026, 9, 17, 12, 0, tzinfo=UTC)


class _SesionQueChoca:
    """Sesión que falla al confirmar, como cuando otro escritor se adelantó con la misma fila."""

    def __init__(self, real: Any, control: dict[str, int]) -> None:
        self._real = real
        self._control = control

    def __enter__(self) -> _SesionQueChoca:
        self._real.__enter__()
        return self

    def __exit__(self, *args: object) -> object:
        return self._real.__exit__(*args)

    def __getattr__(self, nombre: str) -> Any:
        return getattr(self._real, nombre)

    def commit(self) -> None:
        if self._control["choques"] < self._control["limite"]:
            self._control["choques"] += 1
            raise IntegrityError(
                "INSERT INTO classification_proposals ...",
                {},
                Exception(
                    "UNIQUE constraint failed: classification_proposals.subject_type, "
                    "classification_proposals.subject_id, classification_proposals.axis"
                ),
            )
        self._real.commit()

    def rollback(self) -> None:
        self._real.rollback()


def _fabrica_que_choca(sesiones: Any, control: dict[str, int]) -> Any:
    def crear() -> _SesionQueChoca:
        return _SesionQueChoca(sesiones(), control)

    return crear


def _propuesta(axis: Axis, valor: str) -> Proposal:
    return Proposal(
        id=f"prop-{axis.value}-{valor}",
        subject_type=SubjectType.REPRESENTATION,
        subject_id="rep-1",
        axis=axis,
        proposed_value=valor,
        confidence=0.7,
        engine_name="determinista",
        engine_version="1",
    )


def test_un_choque_de_unicidad_se_reintenta_y_no_deja_la_pasada_a_medias(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path / "datos", _env_file=None)
    settings.data_paths.ensure_directories()
    run_migrations(settings, revision="head")
    engine = build_engine(settings.data_paths.database)
    sesiones = build_session_factory(engine)
    store = RepresentationStore(settings.data_paths)

    propuestas = (
        _propuesta(Axis.DOCUMENT_TYPE, "curriculum"),
        _propuesta(Axis.AUTHORITY, "A"),
    )
    control = {"choques": 0, "limite": 1}
    con_choque = SqlAlchemyClassificationRepository(_fabrica_que_choca(sesiones, control), store)

    creadas, existentes = con_choque.save_proposals(propuestas, now=AHORA)

    assert control["choques"] == 1, "la prueba tiene que haber provocado el choque"
    assert (creadas, existentes) == (2, 0), "el reintento guarda lo que faltaba, sin duplicar"

    real = SqlAlchemyClassificationRepository(sesiones, store)
    guardadas = real.list_proposals(subject_id="rep-1")
    assert guardadas.total == 2, "el choque no puede dejar propuestas a medias ni repetidas"
    assert {propuesta.proposed_value for propuesta in guardadas.proposals} == {"curriculum", "A"}

    # Y repetir la misma pasada no duplica nada: las dos ya estaban.
    assert real.save_proposals(propuestas, now=AHORA) == (0, 2)
    assert real.list_proposals(subject_id="rep-1").total == 2


def test_dos_choques_seguidos_no_se_esconden(tmp_path: Path) -> None:
    """Si el segundo intento también choca, el problema es real y se propaga."""
    settings = Settings(data_dir=tmp_path / "datos", _env_file=None)
    settings.data_paths.ensure_directories()
    run_migrations(settings, revision="head")
    engine = build_engine(settings.data_paths.database)
    sesiones = build_session_factory(engine)
    store = RepresentationStore(settings.data_paths)

    control = {"choques": 0, "limite": 5}
    siempre_choca = SqlAlchemyClassificationRepository(_fabrica_que_choca(sesiones, control), store)

    try:
        siempre_choca.save_proposals((_propuesta(Axis.DOCUMENT_TYPE, "curriculum"),), now=AHORA)
    except Exception as error:
        assert type(error).__name__ == "IntegrityError"
    else:  # pragma: no cover - si no choca, la prueba no está midiendo lo que dice
        raise AssertionError("un choque que se repite tiene que propagarse, no silenciarse")

    assert control["choques"] == 2, "solo se reintenta una vez, no en bucle"
    assert SqlAlchemyClassificationRepository(sesiones, store).list_proposals().total == 0
