"""Pruebas unitarias del dominio de clasificación (S04): vocabulario, bandas y transiciones."""

from __future__ import annotations

import pytest

from opofuente.domain.classification import (
    CRITICAL_AXES,
    UNDOABLE_STATUSES,
    Alternative,
    AuthorityTier,
    Axis,
    Band,
    ConfidenceBands,
    CoverageType,
    DocumentType,
    MappingStatus,
    Proposal,
    ProposalStatus,
    RightsStatus,
    SubjectType,
    can_undo,
    coverage_counts_as_accepted,
    decision_allowed,
    group_key,
    value_matches_axis,
)
from opofuente.domain.extraction import Quality


def _propuesta(
    *,
    axis: Axis = Axis.DOCUMENT_TYPE,
    proposed_value: str = DocumentType.PERSONAL_NOTES.value,
    confidence: float = 0.9,
    alternatives: tuple[Alternative, ...] = (),
    evidence: tuple[str, ...] = (),
) -> Proposal:
    return Proposal(
        id="prop-1",
        subject_type=SubjectType.ARTIFACT,
        subject_id="art-1",
        axis=axis,
        proposed_value=proposed_value,
        confidence=confidence,
        engine_name="determinista",
        engine_version="1",
        alternatives=alternatives,
        evidence=evidence,
    )


def test_los_ejes_criticos_no_se_aplican_solos_aunque_la_confianza_sea_maxima() -> None:
    """Autoridad y derechos siempre pasan por revisión (04 §8): no se otorgan solos."""
    bandas = ConfidenceBands(high=0.75, medium=0.45)

    assert bandas.band_for(0.99, axis=Axis.DOCUMENT_TYPE) is Band.HIGH
    assert bandas.decides_itself(0.99, axis=Axis.DOCUMENT_TYPE) is True

    for eje in sorted(CRITICAL_AXES, key=lambda item: item.value):
        assert bandas.band_for(0.99, axis=eje) is Band.MEDIUM
        assert bandas.decides_itself(0.99, axis=eje) is False


@pytest.mark.parametrize(
    ("confianza", "esperada"),
    [
        (0.10, Band.LOW),
        (0.45, Band.MEDIUM),
        (0.74, Band.MEDIUM),
        (0.75, Band.HIGH),
        (1.0, Band.HIGH),
    ],
)
def test_las_bandas_son_monotonas_y_los_limites_pertenecen_a_la_banda_alta(
    confianza: float, esperada: Band
) -> None:
    """Los umbrales son inclusivos: 0,75 es banda alta, no media."""
    assert ConfidenceBands().band_for(confianza, axis=Axis.TOPIC) is esperada


def test_unas_bandas_incoherentes_no_se_aceptan() -> None:
    """Media por encima de alta sería una configuración sin sentido y se rechaza al construirla."""
    with pytest.raises(ValueError):
        ConfidenceBands(high=0.4, medium=0.8)


def test_la_confianza_fuera_de_rango_se_rechaza() -> None:
    with pytest.raises(ValueError):
        ConfidenceBands().band_for(1.5, axis=Axis.TOPIC)


def test_un_valor_fuera_del_vocabulario_no_es_un_valor_valido() -> None:
    """El vocabulario cerrado evita que un motor invente tipos o niveles de autoridad."""
    assert value_matches_axis(Axis.DOCUMENT_TYPE, "personal_notes") is True
    assert value_matches_axis(Axis.DOCUMENT_TYPE, "resumen_inventado") is False
    assert value_matches_axis(Axis.AUTHORITY, AuthorityTier.A.value) is True
    assert value_matches_axis(Axis.AUTHORITY, "Z") is False
    assert value_matches_axis(Axis.RIGHTS, RightsStatus.PRIVATE_USE_ONLY.value) is True
    assert value_matches_axis(Axis.RIGHTS, "libre_total") is False
    assert value_matches_axis(Axis.DOCUMENT_TYPE, "") is False
    # Los ejes que se validan contra datos reales solo exigen que vengan informados.
    assert value_matches_axis(Axis.TOPIC, "tema-1") is True
    assert value_matches_axis(Axis.TOPIC, "") is False


def test_una_propuesta_con_valor_invalido_no_se_construye() -> None:
    with pytest.raises(ValueError):
        _propuesta(axis=Axis.AUTHORITY, proposed_value="oficialísimo")
    with pytest.raises(ValueError):
        _propuesta(confidence=1.4)


def test_las_transiciones_de_una_propuesta_son_las_documentadas() -> None:
    """De `pending` se sale a cualquier decisión; de una decisión solo se pasa a `superseded`."""
    assert decision_allowed(ProposalStatus.PENDING, ProposalStatus.ACCEPTED)
    assert decision_allowed(ProposalStatus.PENDING, ProposalStatus.REJECTED)
    assert decision_allowed(ProposalStatus.PENDING, ProposalStatus.AUTO_APPLIED_PROVISIONAL)
    assert decision_allowed(ProposalStatus.AUTO_APPLIED_PROVISIONAL, ProposalStatus.ACCEPTED)
    assert decision_allowed(ProposalStatus.ACCEPTED, ProposalStatus.SUPERSEDED)

    assert decision_allowed(ProposalStatus.ACCEPTED, ProposalStatus.REJECTED) is False
    assert decision_allowed(ProposalStatus.REJECTED, ProposalStatus.ACCEPTED) is False
    assert decision_allowed(ProposalStatus.SUPERSEDED, ProposalStatus.ACCEPTED) is False
    assert decision_allowed(ProposalStatus.PENDING, ProposalStatus.PENDING) is False


def test_solo_las_propuestas_decididas_se_pueden_deshacer() -> None:
    assert ProposalStatus.ACCEPTED in UNDOABLE_STATUSES
    assert ProposalStatus.REJECTED in UNDOABLE_STATUSES
    assert ProposalStatus.AUTO_APPLIED_PROVISIONAL in UNDOABLE_STATUSES
    assert can_undo(ProposalStatus.PENDING) is False
    assert can_undo(ProposalStatus.SUPERSEDED) is False


@pytest.mark.parametrize(
    ("calidad", "estado", "cuenta"),
    [
        (Quality.GOOD, MappingStatus.ACCEPTED, True),
        (Quality.USABLE_WITH_WARNINGS, MappingStatus.ACCEPTED, True),
        (Quality.POOR, MappingStatus.ACCEPTED, False),
        (Quality.OCR_UNREVIEWED, MappingStatus.ACCEPTED, False),
        (Quality.FAILED, MappingStatus.ACCEPTED, False),
        (None, MappingStatus.ACCEPTED, False),
        (Quality.GOOD, MappingStatus.PROVISIONAL, False),
        (Quality.GOOD, MappingStatus.REJECTED, False),
    ],
)
def test_la_cobertura_aceptada_exige_decision_y_texto_utilizable(
    calidad: Quality | None, estado: MappingStatus, cuenta: bool
) -> None:
    """Una fuente pobre o candidata no sostiene cobertura aceptada (S05)."""
    assert coverage_counts_as_accepted(calidad, estado) is cuenta


def test_las_alternativas_no_cambian_el_valor_propuesto() -> None:
    """Las alternativas se guardan para la revisión; la propuesta sigue siendo una sola."""
    propuesta = _propuesta(
        alternatives=(Alternative(value="community_material", confidence=0.4),),
        evidence=("página 1: «Mis apuntes de TAI»",),
    )

    assert propuesta.proposed_value == DocumentType.PERSONAL_NOTES.value
    assert propuesta.alternatives[0].value == "community_material"
    assert propuesta.status is ProposalStatus.PENDING
    assert propuesta.is_critical is False
    assert (
        _propuesta(axis=Axis.RIGHTS, proposed_value=RightsStatus.UNKNOWN.value).is_critical is True
    )


def test_la_clave_de_grupo_es_determinista() -> None:
    """Dos propuestas del mismo sujeto, eje y valor caen en el mismo grupo de revisión."""
    primera = group_key(SubjectType.ARTIFACT, Axis.DOCUMENT_TYPE, DocumentType.PERSONAL_NOTES.value)
    segunda = group_key(SubjectType.ARTIFACT, Axis.DOCUMENT_TYPE, DocumentType.PERSONAL_NOTES.value)
    otra = group_key(
        SubjectType.REPRESENTATION, Axis.DOCUMENT_TYPE, DocumentType.PERSONAL_NOTES.value
    )

    assert primera == segunda
    assert primera != otra
    assert CoverageType.PARTIAL.value == "partial"
