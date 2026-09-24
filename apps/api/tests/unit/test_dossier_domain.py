"""Pruebas del dossier del tema: las reglas puras (S13, parte 1).

Lo que se comprueba aquí es lo que decide **qué se puede citar y qué se declara**, sin base de datos
ni
API: la vigencia y la calidad de las versiones, la agrupación por fuente, la ordenación estable, la
repetición de un mismo texto y los huecos. Todo con material inventado, escrito en la propia prueba.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from opofuente.domain.dossier import (
    HoleCode,
    PassageFacts,
    build_dossier,
)

AHORA = datetime(2026, 9, 24, 10, 0, tzinfo=UTC)
HOY = date(2026, 9, 24)


def _tramo(
    *,
    evidence_id: str,
    texto: str,
    documento: str = "Temario TAI",
    version: str = "v1",
    estado: str = "accepted",
    calidad: str | None = "good",
    pagina: int | None = 1,
    ordinal: int = 1,
    mapeos: tuple[str, ...] = ("accepted",),
    etiqueta: str | None = None,
    vigencia_desde: date | None = None,
    vigencia_hasta: date | None = None,
) -> PassageFacts:
    return PassageFacts(
        evidence_id=evidence_id,
        text=texto,
        normalized=texto,
        citation_label=etiqueta or f"{documento}, pág. {pagina}",
        page=pagina,
        section_title="Tema 1",
        ordinal=ordinal,
        document_id=f"doc-{documento}",
        document_title=documento,
        document_type="private_syllabus",
        authority_tier="B",
        version_id=version,
        version_label=version,
        version_status=estado,
        quality=calidad,
        mappings=mapeos,
        valid_from=vigencia_desde,
        valid_to=vigencia_hasta,
    )


def _dossier(facts: tuple[PassageFacts, ...], *, mappings_total: int = 1):
    return build_dossier(
        node_id="nodo-1",
        path="tema-1",
        title="Tema 1: procedimiento",
        depth=1,
        generated_at=AHORA,
        facts=facts,
        mappings_total=mappings_total,
        reference_date=HOY,
    )


def test_un_tema_con_tres_fuentes_enseña_los_pasajes_de_las_tres_ordenados() -> None:
    dossier = _dossier(
        (
            _tramo(evidence_id="e-3", texto="Tercero", documento="Zeta", pagina=5),
            _tramo(evidence_id="e-1", texto="Primero", documento="Alfa", pagina=2),
            _tramo(evidence_id="e-2", texto="Segundo", documento="Alfa", pagina=9),
        )
    )

    assert [fuente.document_title for fuente in dossier.sources] == ["Alfa", "Zeta"]
    alfa = dossier.sources[0]
    assert [pasaje.text for pasaje in alfa.passages] == ["Primero", "Segundo"]
    assert [pasaje.page for pasaje in alfa.passages] == [2, 9]
    assert dossier.passages_total == 3
    assert dossier.sources_total == 2
    assert dossier.holes == (), "un tema con material citable no declara huecos"


def test_el_mismo_texto_en_dos_fuentes_se_cita_una_vez_y_se_dice_donde_mas_esta() -> None:
    dossier = _dossier(
        (
            _tramo(
                evidence_id="e-1",
                texto="El plazo es de diez días.",
                documento="Alfa",
                etiqueta="Alfa, pág. 3",
            ),
            _tramo(
                evidence_id="e-2",
                texto="  el plazo   es de diez días.  ",
                documento="Beta",
                etiqueta="Beta, pág. 8",
            ),
        )
    )

    assert dossier.passages_total == 1, "el mismo texto no se enseña dos veces"
    assert [fuente.document_title for fuente in dossier.sources] == ["Alfa"], (
        "la fuente que solo repetía no aporta nada nuevo"
    )
    repetido = dossier.sources[0].passages[0]
    assert repetido.repeated_in == ("Beta, pág. 8",), "se dice dónde más está"
    assert HoleCode.REPETIDO_EN_OTRA_FUENTE in [hueco.code for hueco in dossier.holes]


def test_una_version_sin_aceptar_no_sostiene_una_cita_y_se_declara_el_motivo() -> None:
    dossier = _dossier((_tramo(evidence_id="e-1", texto="Borrador", estado="candidate"),))

    assert dossier.sources == ()
    assert dossier.passages_total == 0
    huecos = {hueco.code: hueco for hueco in dossier.holes}
    assert HoleCode.NO_CITABLE in huecos
    assert "candidate" in (huecos[HoleCode.NO_CITABLE].reason or "")
    assert huecos[HoleCode.NO_CITABLE].count == 1


def test_un_texto_pobre_no_sostiene_una_cita() -> None:
    dossier = _dossier((_tramo(evidence_id="e-1", texto="Basura", calidad="poor"),))

    assert dossier.sources == ()
    motivos = [hueco.reason for hueco in dossier.holes if hueco.code is HoleCode.NO_CITABLE]
    assert motivos and "poor" in motivos[0]


def test_un_tema_sin_material_lo_dice_con_su_hueco_y_no_con_un_cero() -> None:
    dossier = _dossier((), mappings_total=0)

    assert dossier.empty is True
    assert dossier.sources == ()
    assert [hueco.code for hueco in dossier.holes] == [HoleCode.SIN_MATERIAL]


def test_un_tema_con_material_asignado_y_sin_texto_citable_no_dice_que_no_tiene_material() -> None:
    """No es lo mismo no tener material que tenerlo y que todavía no tenga nada que citar."""
    dossier = _dossier((), mappings_total=2)

    assert dossier.empty is True
    huecos = {hueco.code: hueco for hueco in dossier.holes}
    assert HoleCode.SIN_MATERIAL not in huecos
    assert huecos[HoleCode.SIN_TEXTO].count == 2


def test_un_tema_sostenido_solo_por_mapeos_sin_confirmar_lo_declara() -> None:
    dossier = _dossier((_tramo(evidence_id="e-1", texto="Sin confirmar", mapeos=("provisional",)),))

    assert dossier.provisional is True
    assert dossier.accepted_sources == 0
    assert dossier.provisional_sources == 1
    assert HoleCode.MAPEO_PROVISIONAL in [hueco.code for hueco in dossier.holes]


def test_si_algo_esta_sostenido_por_un_mapeo_confirmado_no_se_declara_provisional() -> None:
    dossier = _dossier(
        (
            _tramo(evidence_id="e-1", texto="Un tramo", mapeos=("provisional",)),
            _tramo(evidence_id="e-2", texto="Otro tramo", mapeos=("accepted", "provisional")),
        )
    )

    assert dossier.provisional is False
    assert dossier.accepted_sources == 1


def test_una_version_fuera_de_vigencia_no_se_cita() -> None:
    dossier = _dossier(
        (
            _tramo(
                evidence_id="e-1",
                texto="Derogado",
                estado="accepted",
                vigencia_hasta=date(2026, 1, 1),
            ),
        )
    )

    assert dossier.sources == ()
    assert any("vigente" in (hueco.reason or "") for hueco in dossier.holes)


def test_la_huella_de_contenido_no_cambia_por_volver_a_leer_el_mismo_tema() -> None:
    """Releer no puede crear una versión nueva: la huella no depende de la fecha."""
    tramos = (_tramo(evidence_id="e-1", texto="Estable"),)
    primera = _dossier(tramos)
    segunda = build_dossier(
        node_id="nodo-1",
        path="tema-1",
        title="Tema 1: procedimiento",
        depth=1,
        generated_at=datetime(2026, 9, 25, 8, 0, tzinfo=UTC),
        facts=tramos,
        mappings_total=1,
        reference_date=date(2026, 9, 25),
    )

    assert primera.content_hash == segunda.content_hash

    con_otra_fuente = _dossier(
        (*tramos, _tramo(evidence_id="e-2", texto="Nuevo", documento="Beta"))
    )
    assert con_otra_fuente.content_hash != primera.content_hash, (
        "con material nuevo la huella cambia: es lo que hace que se guarde una versión nueva"
    )


def test_el_documento_canonico_se_puede_leer_de_vuelta() -> None:
    """Lo que se archiva y lo que se sirve es lo mismo: se comprueba el ida y vuelta entero."""
    from opofuente.domain.dossier import dossier_document, dossier_from_document

    dossier = _dossier(
        (
            _tramo(evidence_id="e-1", texto="Primero", documento="Alfa", pagina=2),
            _tramo(evidence_id="e-2", texto="Repetido", documento="Alfa", pagina=3),
            _tramo(evidence_id="e-3", texto="Repetido", documento="Beta", pagina=7),
            _tramo(evidence_id="e-4", texto="Sin publicar", estado="candidate"),
        )
    )

    vuelto = dossier_from_document(dossier_document(dossier))

    assert vuelto.sources == dossier.sources
    assert vuelto.holes == dossier.holes
    assert vuelto.content_hash == dossier.content_hash
    assert vuelto.passages_total == dossier.passages_total
    assert vuelto.generated_at == dossier.generated_at


def test_un_documento_de_otra_version_de_formato_se_rechaza_en_lugar_de_leerse_mal() -> None:
    from opofuente.domain.dossier import dossier_document, dossier_from_document

    documento = dossier_document(_dossier((_tramo(evidence_id="e-1", texto="Uno"),)))
    documento["format_version"] = 99

    try:
        dossier_from_document(documento)
    except ValueError as error:
        assert "99" in str(error)
    else:  # pragma: no cover - solo si el lector deja de comprobar la versión
        raise AssertionError("un formato desconocido debe rechazarse, no interpretarse")
