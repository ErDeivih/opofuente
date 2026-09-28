"""Aplicar la banda alta: todas las candidatas, no las primeras mil (S04 / ADR-017).

`_apply_high_band` era la última pieza que se quedaba corta con el corpus real: miraba **una**
página de mil propuestas pendientes y decidía entre las que cupieran ahí. Mientras una pasada dejaba
un puñado de propuestas vivas eso bastaba; con el material real, una sola pasada escribió 14.162
filas, y como todas las de una pasada **comparten instante**, el orden por fecha no dice cuáles caen
en la ventana: entraban mil al azar y el resto se quedaba pendiente sin que se pudiera explicar por
qué unos temas se aplicaban y otros no.

Se prueba aquí el método que aplica (es la pieza con el defecto), sobre la infraestructura real:
base migrada y sembrada, propuestas guardadas por el repositorio de verdad y decisiones de verdad.
La página se acorta por prueba para no escribir mil filas solo para demostrar un recorrido.
"""

from __future__ import annotations

from typing import Any

import pytest

from opofuente.application import classification_service as modulo_servicio
from opofuente.application.classification_service import ClassificationService
from opofuente.config import Settings
from opofuente.domain.classification import Axis, Proposal, SubjectType
from opofuente.infrastructure.classification_repository import SqlAlchemyClassificationRepository
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.representation_store import RepresentationStore
from opofuente_testing.jobs import FixedClock

#: Cinco nodos del temario de TAI, que es el programa que siembra la fixture.
TEMAS = ("I.1", "I.2", "I.3", "I.4", "I.5")


class _SinCola:
    """Cola que no hace nada: estas pruebas llaman a aplicar, no encolan trabajos."""

    def enqueue(self, **_: Any) -> Any:  # pragma: no cover - no se usa
        raise AssertionError("estas pruebas no encolan trabajos")


@pytest.fixture
def repositorio(seeded_settings: Settings) -> SqlAlchemyClassificationRepository:
    """El repositorio de verdad, sobre una base migrada y con los programas sembrados.

    Los programas importan: aplicar un tema crea su mapeo, y eso exige que el nodo exista.
    """
    engine = build_engine(seeded_settings.data_paths.database)
    return SqlAlchemyClassificationRepository(
        build_session_factory(engine), RepresentationStore(seeded_settings.data_paths)
    )


def _candidatas(confianza: float = 0.8) -> tuple[Proposal, ...]:
    return tuple(
        Proposal(
            id="",
            subject_type=SubjectType.REPRESENTATION,
            subject_id="rep-temas",
            axis=Axis.TOPIC,
            proposed_value=tema,
            confidence=confianza,
            engine_name="prueba",
            engine_version="1",
            evidence=("evidencia de prueba",),
        )
        for tema in TEMAS
    )


def test_aplicar_la_banda_alta_recorre_todas_las_pendientes(
    repositorio: SqlAlchemyClassificationRepository, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Con más candidatas que una página, se aplican todas (antes se aplicaba una sola página)."""
    propuestas = _candidatas()
    repositorio.save_proposals(propuestas, now=FixedClock().now())
    monkeypatch.setattr(modulo_servicio, "PAGINA_DE_APLICACION", 2)
    servicio = ClassificationService(repositorio, (), FixedClock(), _SinCola())

    aplicadas = servicio._apply_high_band(propuestas)

    assert aplicadas == len(TEMAS), "se aplican las cinco, no las dos de la primera página"
    pagina = repositorio.list_proposals(subject_id="rep-temas", limit=50)
    assert {vista.status for vista in pagina.proposals} == {"auto_applied_provisional"}
    mapeos = repositorio.list_mappings(subject_id="rep-temas")
    assert len(mapeos) == len(TEMAS), (
        "aplicar un tema deja su mapeo provisional: sin mapeo no hay cobertura"
    )


def test_aplicar_la_banda_alta_no_aplica_lo_que_no_es_candidata(
    repositorio: SqlAlchemyClassificationRepository,
) -> None:
    """La banda manda: una propuesta por debajo del umbral se queda pendiente y sin mapeo."""
    altas = _candidatas()
    bajas = tuple(
        Proposal(
            id="",
            subject_type=SubjectType.REPRESENTATION,
            subject_id="rep-otro",
            axis=Axis.TOPIC,
            proposed_value=tema,
            confidence=0.3,
            engine_name="prueba",
            engine_version="1",
        )
        for tema in TEMAS
    )
    repositorio.save_proposals((*altas, *bajas), now=FixedClock().now())
    servicio = ClassificationService(repositorio, (), FixedClock(), _SinCola())

    aplicadas = servicio._apply_high_band((*altas, *bajas))

    assert aplicadas == len(TEMAS)
    assert {
        vista.status
        for vista in repositorio.list_proposals(subject_id="rep-otro", limit=50).proposals
    } == {"pending"}
