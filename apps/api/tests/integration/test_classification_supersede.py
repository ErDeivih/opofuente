"""Quién sustituye a quién al guardar propuestas de clasificación (S04).

La identidad de una propuesta incluye el motor (`uq_proposal_identity`), así que dos motores pueden
opinar a la vez sobre el mismo sujeto y eje. El guardado, en cambio, retiraba **todas** las
pendientes del sujeto y el eje al añadir un valor nuevo, sin mirar de qué motor venían. Con dos
motores eso es una pérdida silenciosa de señal: el motor determinista ve el título oficial en el
texto y propone un tema con 0,80, y el de fragmentos —que corre después y propone hasta tres nodos
con confianzas más bajas— dejaba su propuesta de 0,80 en `superseded` antes de que la banda pudiera
aplicarla.

Medido sobre el material real del propietario: cinco temas del temario se quedaban **sin nada** por
esto, con su propuesta fuerte ya escrita en la base y en estado `superseded`.

Estas pruebas fijan las tres reglas del guardado con la infraestructura real (SQLite y migraciones),
porque lo que se mide es una escritura, no una función pura.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from opofuente.config import Settings
from opofuente.domain.classification import Axis, Proposal, ProposalStatus, SubjectType
from opofuente.infrastructure.classification_repository import SqlAlchemyClassificationRepository
from opofuente.infrastructure.db import build_engine, build_session_factory
from opofuente.infrastructure.migrations import run_migrations
from opofuente.infrastructure.representation_store import RepresentationStore

AHORA = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
DESPUES = datetime(2026, 9, 28, 13, 0, tzinfo=UTC)

DETERMINISTA = "determinista"
FRAGMENTOS = "temas-por-fragmento"


@pytest.fixture
def repositorio(tmp_path: Path) -> SqlAlchemyClassificationRepository:
    """El repositorio de verdad, sobre una base recién migrada."""
    settings = Settings(data_dir=tmp_path / "datos", _env_file=None)
    settings.data_paths.ensure_directories()
    run_migrations(settings, revision="head")
    engine = build_engine(settings.data_paths.database)
    return SqlAlchemyClassificationRepository(
        build_session_factory(engine), RepresentationStore(settings.data_paths)
    )


def _propuesta(
    valor: str,
    *,
    motor: str,
    confianza: float,
    axis: Axis = Axis.TOPIC,
    sujeto: str = "rep-1",
) -> Proposal:
    return Proposal(
        id="",
        subject_type=SubjectType.REPRESENTATION,
        subject_id=sujeto,
        axis=axis,
        proposed_value=valor,
        confidence=confianza,
        engine_name=motor,
        engine_version="1",
        evidence=(f"propuesta de {motor}",),
    )


def _estados(repositorio: SqlAlchemyClassificationRepository) -> dict[str, str]:
    pagina = repositorio.list_proposals(subject_id="rep-1", limit=200)
    return {vista.proposed_value: vista.status for vista in pagina.proposals}


def _valor_por_estado(repositorio: SqlAlchemyClassificationRepository, estado: str) -> list[str]:
    pagina = repositorio.list_proposals(subject_id="rep-1", limit=200)
    return sorted(vista.proposed_value for vista in pagina.proposals if vista.status == estado)


def test_la_opinion_fuerte_de_un_motor_no_la_retira_otro_motor(
    repositorio: SqlAlchemyClassificationRepository,
) -> None:
    """El motor de fragmentos no puede dejar en `superseded` la señal fuerte del determinista."""
    fuerte = _propuesta("I.3", motor=DETERMINISTA, confianza=0.8)
    debiles = (
        _propuesta("III.2", motor=FRAGMENTOS, confianza=0.25),
        _propuesta("I.3", motor=FRAGMENTOS, confianza=0.35),
    )

    creadas, existentes = repositorio.save_proposals((fuerte, *debiles), now=AHORA)

    assert (creadas, existentes) == (3, 0)
    # Las tres filas están: I.3 se guarda dos veces, una por motor, y las dos siguen vivas.
    assert _valor_por_estado(repositorio, "pending") == ["I.3", "I.3", "III.2"]
    assert _valor_por_estado(repositorio, "superseded") == []
    # La fuerte sigue viva y con su confianza: es la que la banda puede aplicar sola.
    pagina = repositorio.list_proposals(subject_id="rep-1", limit=200)
    fuertes = [
        vista
        for vista in pagina.proposals
        if vista.proposed_value == "I.3" and vista.engine_name == DETERMINISTA
    ]
    assert [vista.confidence for vista in fuertes] == [0.8]
    assert fuertes[0].status == "pending"


def test_los_hermanos_de_una_misma_pasada_no_se_pisan(
    repositorio: SqlAlchemyClassificationRepository,
) -> None:
    """El tema admite hasta tres nodos (04 §7): proponer tres no es cambiar de opinión dos veces."""
    propuestas = tuple(
        _propuesta(valor, motor=FRAGMENTOS, confianza=confianza)
        for valor, confianza in (("I.5", 0.74), ("III.4", 0.59), ("IV.2", 0.53))
    )

    creadas, _ = repositorio.save_proposals(propuestas, now=AHORA)

    assert creadas == 3
    assert _valor_por_estado(repositorio, "pending") == ["I.5", "III.4", "IV.2"]
    assert _valor_por_estado(repositorio, "superseded") == [], "ninguno retira a sus hermanos"


def test_un_motor_que_cambia_de_opinion_retira_la_suya(
    repositorio: SqlAlchemyClassificationRepository,
) -> None:
    """Lo que ya no sostiene su propio motor queda retirado, con su motivo."""
    repositorio.save_proposals(
        (_propuesta("curriculum", motor=DETERMINISTA, confianza=0.7, axis=Axis.DOCUMENT_TYPE),),
        now=AHORA,
    )
    repositorio.save_proposals(
        (_propuesta("personal_notes", motor=DETERMINISTA, confianza=0.7, axis=Axis.DOCUMENT_TYPE),),
        now=DESPUES,
    )

    assert _estados(repositorio) == {"curriculum": "superseded", "personal_notes": "pending"}


def test_un_valor_que_el_motor_vuelve_a_sostener_vuelve_a_pendiente(
    repositorio: SqlAlchemyClassificationRepository,
) -> None:
    """`superseded` es contabilidad de la máquina, no una decisión: un valor puede volver."""
    repositorio.save_proposals(
        (
            _propuesta("I.3", motor=FRAGMENTOS, confianza=0.78),
            _propuesta("III.2", motor=FRAGMENTOS, confianza=0.30),
        ),
        now=AHORA,
    )
    # Segunda pasada: el motor ya no ve I.3.
    repositorio.save_proposals(
        (_propuesta("III.2", motor=FRAGMENTOS, confianza=0.30),), now=DESPUES
    )
    assert _estados(repositorio) == {"I.3": "superseded", "III.2": "pending"}

    # Tercera pasada: vuelve a verlo. Sin esto, un valor propuesto una vez no podría volver nunca.
    repositorio.save_proposals(
        (
            _propuesta("I.3", motor=FRAGMENTOS, confianza=0.78),
            _propuesta("III.2", motor=FRAGMENTOS, confianza=0.30),
        ),
        now=DESPUES,
    )

    assert _estados(repositorio) == {"I.3": "pending", "III.2": "pending"}
    assert repositorio.list_proposals(subject_id="rep-1", limit=200).total == 2, "sin duplicar"


def test_una_decision_humana_no_la_revive_una_pasada_nueva(
    repositorio: SqlAlchemyClassificationRepository,
) -> None:
    """Un rechazo sigue siendo un rechazo aunque el motor vuelva a proponer lo mismo."""
    repositorio.save_proposals(
        (
            _propuesta("I.3", motor=FRAGMENTOS, confianza=0.4),
            _propuesta("III.2", motor=FRAGMENTOS, confianza=0.3),
        ),
        now=AHORA,
    )
    pagina = repositorio.list_proposals(subject_id="rep-1", limit=200)
    rechazada = next(vista for vista in pagina.proposals if vista.proposed_value == "I.3")
    resultado = repositorio.decide(
        rechazada.id, status=ProposalStatus.REJECTED, note="no es el tema", now=DESPUES
    )
    assert resultado.applied is True, resultado.reason

    repositorio.save_proposals(
        (
            _propuesta("I.3", motor=FRAGMENTOS, confianza=0.4),
            _propuesta("III.2", motor=FRAGMENTOS, confianza=0.3),
        ),
        now=DESPUES,
    )

    assert _estados(repositorio) == {"I.3": "rejected", "III.2": "pending"}


def test_repetir_la_pasada_no_cambia_nada(
    repositorio: SqlAlchemyClassificationRepository,
) -> None:
    """Idempotencia: la misma pasada dos veces deja lo mismo y no inventa filas."""
    propuestas = (
        _propuesta("I.3", motor=DETERMINISTA, confianza=0.8),
        _propuesta("I.3", motor=FRAGMENTOS, confianza=0.78),
        _propuesta("III.2", motor=FRAGMENTOS, confianza=0.3),
    )

    assert repositorio.save_proposals(propuestas, now=AHORA) == (3, 0)
    assert repositorio.save_proposals(propuestas, now=DESPUES) == (0, 3)

    assert _valor_por_estado(repositorio, "pending") == ["I.3", "I.3", "III.2"]
    assert _valor_por_estado(repositorio, "superseded") == []
