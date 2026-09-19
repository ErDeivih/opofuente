"""Pruebas unitarias de cambios e invalidación selectiva (S11).

Lo que se comprueba aquí es el criterio de aceptación del slice, que es una regla y su contraria:

- **solo se invalidan los derivados que dependen de lo que cambió**, y
- **lo que solo depende de secciones intactas no se toca**.

Y, además, que la aplicación no interpreta el efecto jurídico de un cambio y que un conjunto de
cambios no se confirma dos veces.
"""

from __future__ import annotations

import pytest

from opofuente.domain.changes import (
    LEGAL_EFFECT_NOTE,
    ArtifactKind,
    ArtifactReview,
    ChangeStatus,
    Dependent,
    EdgeSource,
    EdgeTarget,
    SectionChange,
    SectionChangeKind,
    assert_can_confirm,
    assert_can_review,
    assess_change,
)
from opofuente.domain.errors import InvalidStateError

RESUMEN_A = Dependent(kind=EdgeTarget.DERIVED_ARTIFACT, id="art-1", title="Resumen del tema 1")
RESUMEN_B = Dependent(kind=EdgeTarget.DERIVED_ARTIFACT, id="art-2", title="Resumen del tema 2")
RESPUESTA = Dependent(
    kind=EdgeTarget.RAG_ANSWER, id="rag-1", title="¿Cuál es el plazo?", reviewable=False
)


def test_los_vocabularios_son_los_de_la_migracion() -> None:
    assert [estado.value for estado in ChangeStatus] == ["proposed", "confirmed", "discarded"]
    assert [tipo.value for tipo in SectionChangeKind] == [
        "added",
        "removed",
        "changed",
        "unchanged",
    ]
    assert [tipo.value for tipo in ArtifactKind] == ["summary"]
    assert [estado.value for estado in ArtifactReview] == ["pending", "reviewed", "discarded"]
    assert [lado.value for lado in EdgeSource] == [
        "document_version",
        "document_section",
        "evidence_span",
    ]
    assert [lado.value for lado in EdgeTarget] == [
        "derived_artifact",
        "question_version",
        "rag_answer",
    ]


def test_solo_se_invalida_lo_que_depende_de_lo_que_cambio() -> None:
    """El criterio de aceptación, con sus dos mitades: el que depende, sí; el que no, no."""
    valoracion = assess_change(
        sections=(
            SectionChange(label="Título primero", kind=SectionChangeKind.CHANGED),
            SectionChange(label="Título segundo", kind=SectionChangeKind.UNCHANGED),
        ),
        dependents={
            "Título primero": (RESUMEN_A,),
            "Título segundo": (RESUMEN_B,),
        },
    )

    assert [item.id for item in valoracion.affected] == ["art-1"]
    assert valoracion.affected[0].sections == ("Título primero",)
    assert "que ha cambiado" in valoracion.affected[0].reason
    assert valoracion.changed == 1
    assert valoracion.unchanged == 1
    assert valoracion.has_changes


def test_una_seccion_nueva_no_invalida_nada_por_si_sola() -> None:
    valoracion = assess_change(
        sections=(SectionChange(label="Título nuevo", kind=SectionChangeKind.ADDED),),
        dependents={"Título nuevo": (RESUMEN_A,)},
    )
    assert valoracion.affected == ()
    assert valoracion.added == 1


def test_una_seccion_quitada_invalida_a_quien_dependia_de_ella() -> None:
    valoracion = assess_change(
        sections=(SectionChange(label="Título tercero", kind=SectionChangeKind.REMOVED),),
        dependents={"Título tercero": (RESUMEN_B,)},
    )
    assert [item.id for item in valoracion.affected] == ["art-2"]
    assert "ya no está en la versión nueva" in valoracion.affected[0].reason
    assert valoracion.removed == 1


def test_un_dependiente_de_dos_secciones_cambiadas_se_marca_una_vez_con_sus_dos_motivos() -> None:
    valoracion = assess_change(
        sections=(
            SectionChange(label="Uno", kind=SectionChangeKind.CHANGED),
            SectionChange(label="Dos", kind=SectionChangeKind.CHANGED),
        ),
        dependents={"Uno": (RESUMEN_A,), "Dos": (RESUMEN_A,)},
    )
    assert len(valoracion.affected) == 1
    assert valoracion.affected[0].sections == ("Uno", "Dos")
    assert valoracion.affected[0].reason.count("depende de") == 2


def test_un_cambio_que_no_toca_nada_guardado_lo_dice() -> None:
    valoracion = assess_change(
        sections=(SectionChange(label="Título primero", kind=SectionChangeKind.CHANGED),),
        dependents={},
    )
    assert valoracion.affected == ()
    assert any("no obliga a revisar nada" in nota for nota in valoracion.extra_notes)


def test_lo_que_no_se_puede_revisar_se_distingue_de_lo_que_si() -> None:
    valoracion = assess_change(
        sections=(SectionChange(label="Título primero", kind=SectionChangeKind.CHANGED),),
        dependents={"Título primero": (RESPUESTA,)},
    )
    assert [item.id for item in valoracion.affected] == ["rag-1"]
    assert valoracion.reviewable == ()
    assert any("no se reescriben" in nota for nota in valoracion.extra_notes)


def test_la_aplicacion_no_interpreta_el_efecto_juridico() -> None:
    valoracion = assess_change(
        sections=(SectionChange(label="Título primero", kind=SectionChangeKind.CHANGED),),
        dependents={"Título primero": (RESUMEN_A,)},
    )
    assert valoracion.note == LEGAL_EFFECT_NOTE
    assert "No decide si una norma sigue vigente" in valoracion.note
    assert "lo decide una persona" in valoracion.note


@pytest.mark.parametrize(
    ("estado", "mensaje"),
    [
        (ChangeStatus.CONFIRMED, "ya está confirmado"),
        (ChangeStatus.DISCARDED, "se descartó"),
    ],
)
def test_un_cambio_no_se_confirma_dos_veces(estado: ChangeStatus, mensaje: str) -> None:
    with pytest.raises(InvalidStateError, match=mensaje):
        assert_can_confirm(estado)


def test_un_cambio_propuesto_se_puede_confirmar() -> None:
    assert_can_confirm(ChangeStatus.PROPOSED)


def test_solo_se_revisa_lo_que_esta_pendiente() -> None:
    assert_can_review(needs_review=True)
    with pytest.raises(InvalidStateError, match="no está pendiente"):
        assert_can_review(needs_review=False)
