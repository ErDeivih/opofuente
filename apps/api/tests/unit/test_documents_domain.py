"""Pruebas unitarias de documentos, versiones y derechos (S05).

Fijan las tres reglas que no pueden depender del criterio de nadie en tiempo de ejecución: un
documento privado no se hace público solo, la versión activa es la aceptada (no la última) y
los derechos desconocidos se tratan como restringidos.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from opofuente.domain.documents import (
    DocumentVersion,
    LogicalDocument,
    OwnerScope,
    RightsProfile,
    RightsReview,
    SectionType,
    VersionStatus,
    active_version,
    can_promote_to_public,
    diff_versions,
    document_section_type,
    supersedes_chain,
)

AHORA = datetime(2026, 9, 16, 12, 0, tzinfo=UTC)


def _version(
    identificador: str,
    *,
    estado: VersionStatus = VersionStatus.CANDIDATE,
    supersedes: str | None = None,
    aprobada: datetime | None = None,
) -> DocumentVersion:
    return DocumentVersion(
        id=identificador,
        logical_document_id="doc-1",
        artifact_id=f"art-{identificador}",
        representation_id=None,
        version_label=identificador,
        status=estado,
        supersedes_id=supersedes,
        approved_at=aprobada,
        retrieved_at=AHORA,
    )


def _documento(scope: OwnerScope = OwnerScope.PRIVATE_USER) -> LogicalDocument:
    return LogicalDocument(
        id="doc-1",
        canonical_title="Temario de TAI",
        document_type="curriculum",
        owner_scope=scope,
    )


def test_la_version_activa_es_la_aceptada_y_no_la_ultima_que_llego() -> None:
    """Una candidata es una propuesta de cambio: no puede presentarse como la versión buena."""
    aceptada = _version("v1", estado=VersionStatus.ACCEPTED, aprobada=AHORA)
    candidata = _version("v2")

    activa = active_version((aceptada, candidata))

    assert activa is not None
    assert activa.id == "v1", "manda la aceptada, no la candidata más reciente"


def test_sin_version_aceptada_manda_la_candidata_y_se_sabe_que_lo_es() -> None:
    candidata = _version("v2")

    activa = active_version((candidata,))

    assert activa is not None
    assert activa.status is VersionStatus.CANDIDATE
    assert activa.can_accept() is True


def test_una_version_retirada_o_rechazada_no_se_puede_aceptar() -> None:
    retirada = _version("v3", estado=VersionStatus.WITHDRAWN)
    rechazada = _version("v4", estado=VersionStatus.REJECTED)

    assert retirada.can_accept() is False
    assert rechazada.can_accept() is False
    assert retirada.is_live is False


def test_aceptar_una_version_siempre_lo_confirma_una_persona() -> None:
    """La promoción de una versión es crítica (D006): la aplicación no la hace sola nunca."""
    assert _version("v1").acceptance_requires_approval() is True


def test_un_documento_privado_no_se_hace_publico_solo() -> None:
    privado = _documento()
    derechos = RightsProfile(
        code="reuse_with_conditions", review_status=RightsReview.REVIEWED, sharing=True
    )

    assert privado.is_public is False
    assert can_promote_to_public(privado, derechos) is False

    publico = _documento(OwnerScope.PUBLIC)
    assert publico.is_public is True
    assert can_promote_to_public(publico, derechos) is True


def test_los_derechos_desconocidos_son_restringidos() -> None:
    """09_SECURITY §8: sin revisar la licencia no se puede afirmar reutilización."""
    desconocidos = RightsProfile(code="unknown")

    assert desconocidos.review_status is RightsReview.UNKNOWN
    assert desconocidos.is_restricted is True
    assert desconocidos.is_reusable is False

    revisados = RightsProfile(
        code="private_use_only",
        review_status=RightsReview.REVIEWED,
        sharing=False,
        attribution="Dirección General de la Guardia Civil",
        license_url="https://example.invalid/condiciones",
    )
    assert revisados.is_restricted is False
    assert revisados.is_reusable is False, "revisado no significa compartible"


def test_una_fuente_sin_atribucion_lo_dice() -> None:
    sin_nada = RightsProfile(code="reuse_with_conditions", review_status=RightsReview.REVIEWED)
    completa = RightsProfile(
        code="reuse_with_conditions",
        review_status=RightsReview.REVIEWED,
        attribution="Agencia Estatal BOE",
        license_url="https://www.boe.es/informacion/aviso_legal/index.php",
    )

    assert sin_nada.missing_attribution() == ("attribution", "license_url")
    assert completa.missing_attribution() == ()


def test_la_cadena_de_sustituciones_se_recorre_sin_colgarse() -> None:
    v1 = _version("v1", estado=VersionStatus.SUPERSEDED)
    v2 = _version("v2", estado=VersionStatus.SUPERSEDED, supersedes="v1")
    v3 = _version("v3", estado=VersionStatus.ACCEPTED, supersedes="v2", aprobada=AHORA)

    cadena = supersedes_chain((v1, v2, v3), "v3")

    assert [version.id for version in cadena] == ["v3", "v2", "v1"]
    assert active_version((v1, v2, v3)) is not None

    # Y con un ciclo no se cuelga: se detiene y devuelve lo que ha podido recorrer.
    a = _version("a", supersedes="b")
    b = _version("b", supersedes="a")
    assert len(supersedes_chain((a, b), "a")) == 2


def test_una_version_no_puede_sustituirse_a_si_misma() -> None:
    with pytest.raises(ValueError):
        _version("v1", supersedes="v1")


def test_la_vigencia_no_puede_terminar_antes_de_empezar() -> None:
    with pytest.raises(ValueError):
        DocumentVersion(
            id="v1",
            logical_document_id="doc-1",
            artifact_id="art-1",
            representation_id=None,
            version_label="v1",
            valid_from=date(2026, 5, 1),
            valid_to=date(2026, 4, 1),
        )


def test_un_documento_necesita_titulo_y_tipo_del_vocabulario() -> None:
    with pytest.raises(ValueError):
        LogicalDocument(id="doc-2", canonical_title="   ", document_type="curriculum")
    with pytest.raises(ValueError):
        LogicalDocument(id="doc-3", canonical_title="Algo", document_type="tipo_inventado")


@pytest.mark.parametrize(
    ("tramo", "esperado"),
    [
        ("page", SectionType.PAGE),
        ("title", SectionType.TITLE),
        ("heading", SectionType.TITLE),
        ("article", SectionType.ARTICLE),
        ("paragraph", SectionType.TECHNICAL),
        ("list", SectionType.TECHNICAL),
        ("table", SectionType.TECHNICAL),
        ("question_block", SectionType.TECHNICAL),
        ("metadata", SectionType.TECHNICAL),
        ("lo-que-sea", SectionType.TECHNICAL),
    ],
)
def test_los_tramos_del_extractor_se_traducen_al_vocabulario_del_documento(
    tramo: str, esperado: SectionType
) -> None:
    """Regresión: sin esta traducción, promocionar un documento fallaba al guardar sus secciones.

    El extractor parte el texto en tramos (`paragraph`, `table`, `question_block`…) y el documento
    se organiza con su propio vocabulario. Copiar el valor del extractor hacía fallar el `CHECK` de
    `document_sections` en cuanto la sección no fuera `page`, `title` o `article`, es decir, casi
    siempre. Lo que el extractor no distingue se queda en `technical`: no se inventa estructura.
    """
    assert document_section_type(tramo) is esperado


def test_el_vocabulario_del_documento_no_promete_lo_que_el_extractor_no_sabe() -> None:
    """`chapter` y `provision` existen en el vocabulario, pero ningún tramo los produce todavía."""
    producidos = {
        document_section_type(tramo)
        for tramo in ("page", "title", "heading", "article", "paragraph", "list", "table")
    }

    assert SectionType.CHAPTER not in producidos
    assert SectionType.PROVISION not in producidos


# --- diff de versiones -------------------------------------------------------------------------


def test_el_diff_dice_que_cambio_sin_fusionar_nada() -> None:
    """Compara sección a sección: añadida, quitada, cambiada e igual, cada una con su etiqueta."""
    antes = (("Tema 1", "Texto uno"), ("Tema 2", "Texto dos"), ("Anexo", "Anexo viejo"))
    despues = (("Tema 1", "Texto uno"), ("Tema 2", "Texto dos corregido"), ("Tema 3", "Nuevo"))

    diff = diff_versions("v1", "v2", before=antes, after=despues)

    tipos = {seccion.label: seccion.kind for seccion in diff.sections}
    assert tipos == {
        "Tema 1": "unchanged",
        "Tema 2": "changed",
        "Tema 3": "added",
        "Anexo": "removed",
    }
    assert (diff.added, diff.removed, diff.changed, diff.unchanged) == (1, 1, 1, 1)
    assert diff.has_changes is True
    cambiada = next(seccion for seccion in diff.sections if seccion.kind == "changed")
    assert cambiada.left == "Texto dos"
    assert cambiada.right == "Texto dos corregido"


def test_el_diff_es_determinista_y_sin_cambios_lo_dice() -> None:
    secciones = (("Tema 1", "Texto uno"), ("Tema 2", "Texto dos"))

    primera = diff_versions("v1", "v2", before=secciones, after=secciones)
    segunda = diff_versions("v1", "v2", before=secciones, after=secciones)

    assert primera == segunda
    assert primera.has_changes is False
    assert primera.unchanged == 2


def test_una_seccion_sin_titulo_se_identifica_por_su_orden() -> None:
    """Sin título no hay etiqueta estable: se nombra por su posición, no se inventa un título."""
    diff = diff_versions("v1", "v2", before=((None, "a"),), after=((None, "a"), (None, "b")))

    etiquetas = [seccion.label for seccion in diff.sections]
    assert etiquetas == ["sección 1", "sección 2"]
    assert diff.added == 1


def test_renombrar_una_seccion_es_quitarla_y_añadirla() -> None:
    """El emparejado es por etiqueta: un título nuevo es una sección nueva, y la vieja desaparece.

    Es conservador a propósito: decir que «Tema 1» y «Capítulo 1» son la misma sección sería afirmar
    algo que el texto no dice.
    """
    diff = diff_versions(
        "v1", "v2", before=(("Tema 1", "Texto"),), after=(("Capítulo 1", "Texto"),)
    )

    assert {seccion.kind for seccion in diff.sections} == {"added", "removed"}
