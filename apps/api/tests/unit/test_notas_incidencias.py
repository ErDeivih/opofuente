"""El bucle de huecos y la bandeja del propietario: categoría, motivo y la frase que lo prueba.

Es el arreglo §2.1.4 del objetivo: antes de cerrar un tema se intenta rellenar el hueco y lo que
siga sin resolverse va a la bandeja **con su categoría**, que es lo que dice quién lo arregla. Sin
categoría, la bandeja es una lista de preguntas sin saber qué hacer con ellas; y «conflictos de
letra sin categorizar» es una de las puertas del §2.3.
"""

from __future__ import annotations

from opofuente.domain.topic_notes import (
    CategoriaIncidencia,
    Coverage,
    FactKind,
    KeyStatus,
    Motivo,
    NotesCheck,
    NoteSection,
    QuestionForNotes,
    agrupar,
    categoria_de,
    detalle_de_incidencia,
)

_SECCION = NoteSection(
    key="iv-7-1",
    epigraph_code="IV.7.1",
    title="El modelo OSI",
    anchor="iv-7-1",
    position=1,
)


def _grupo(enunciado: str = "¿Cuántas capas tiene el modelo OSI?"):
    return agrupar(
        [
            QuestionForNotes(
                question_version_id="q1",
                set_id="conjunto-1",
                stem=enunciado,
                options=(("a", "Cuatro"), ("b", "Siete")),
                correct_keys=("b",),
                key_status=KeyStatus.ACTIVE,
                epigraph_code="IV.7.1",
                mapping_status="accepted",
            )
        ]
    )[0]


def _check(
    *,
    coverage: Coverage,
    note: Motivo | None,
    quote: str | None = None,
    letter: str | None = "a",
    attempts: int = 3,
) -> NotesCheck:
    return NotesCheck(
        question_version_id="q1",
        group_signature="firma",
        section_key=_SECCION.key,
        anchor=_SECCION.anchor,
        coverage=coverage,
        note=note,
        quote=quote,
        letter=letter,
        expected=("b",),
        key_status=KeyStatus.ACTIVE,
        attempts=attempts,
    )


def test_lo_que_queda_sin_cubrir_recibe_la_categoria_de_quien_lo_arregla() -> None:
    """Las cuatro categorías del §2.1.4, una por motivo, y ninguna pregunta sin categoría."""
    assert (
        categoria_de(Coverage.DUDOSA, Motivo.SIN_FRASE_EN_LOS_APUNTES)
        is CategoriaIncidencia.HUECO_SIN_MATERIAL
    )
    assert (
        categoria_de(Coverage.CONFLICTO, Motivo.LETRA_NO_COINCIDE)
        is CategoriaIncidencia.CLAVE_SOSPECHOSA
    )
    assert (
        categoria_de(Coverage.DUDOSA, Motivo.CLAVE_CONTRADICE_LA_NORMA)
        is CategoriaIncidencia.NORMA_CAMBIADA
    )
    assert (
        categoria_de(Coverage.DUDOSA, Motivo.CLAVE_SIN_DEFINIR)
        is CategoriaIncidencia.PREGUNTA_AMBIGUA
    )


def test_una_pregunta_cubierta_no_entra_en_la_bandeja() -> None:
    """La bandeja es lo que falta, no un listado del tema: lo cubierto no tiene categoría."""
    assert categoria_de(Coverage.CUBIERTA, None) is None
    assert categoria_de(Coverage.CUBIERTA, Motivo.SIN_FRASE_EN_LOS_APUNTES) is None
    # Y un hueco **no** es una incidencia: es trabajo de la corrida, que todavía puede rellenarlo.
    assert categoria_de(Coverage.HUECO, Motivo.SIN_FRASE_EN_LOS_APUNTES) is None


def test_el_detalle_de_una_clave_sospechosa_lleva_la_frase_que_lo_demuestra() -> None:
    """«Con la frase que lo demuestra»: sin la cita, el propietario no puede decidir."""
    resultado = _check(
        coverage=Coverage.CONFLICTO,
        note=Motivo.LETRA_NO_COINCIDE,
        quote="el modelo OSI tiene siete capas",
    )

    detalle = detalle_de_incidencia(resultado, _grupo())

    assert "otra letra que su clave" in detalle
    assert "siete capas" in detalle
    assert "clave: b" in detalle
    assert "los apuntes dicen: a" in detalle


def test_el_detalle_de_un_hueco_dice_que_falta_material() -> None:
    """Un hueco no tiene frase (no está escrita) y aun así la incidencia dice qué hacer."""
    resultado = _check(coverage=Coverage.DUDOSA, note=Motivo.SIN_FRASE_EN_LOS_APUNTES, letter=None)

    detalle = detalle_de_incidencia(resultado, _grupo())

    assert "no contienen el dato" in detalle
    assert "frase de los apuntes" not in detalle
    assert "vueltas: 3" in detalle


def test_la_tercera_vuelta_existe_y_es_la_ultima() -> None:
    """El bucle de huecos da una vuelta más, y no más: más vueltas sobre el hueco lo tapan."""
    from opofuente.domain.topic_notes import VUELTAS_CON_HUECOS, VUELTAS_MAXIMAS, evaluar

    assert VUELTAS_CON_HUECOS == 3
    assert VUELTAS_CON_HUECOS > VUELTAS_MAXIMAS
    apuntes = "El modelo OSI tiene siete capas y se estudia por niveles."
    final = evaluar(
        grupo=_grupo(),
        check=None,
        apuntes=apuntes,
        section=_SECCION,
        attempts=VUELTAS_CON_HUECOS,
    )
    assert final.coverage is Coverage.DUDOSA
    assert final.attempts == VUELTAS_CON_HUECOS


def test_un_hecho_no_es_un_apartado_de_revision() -> None:
    """El detalle lleva la pregunta entera, no un volcado de la base."""
    detalle = detalle_de_incidencia(
        _check(coverage=Coverage.CONFLICTO, note=Motivo.LETRA_NO_COINCIDE, quote="una frase"),
        _grupo("¿Cuál de estas afirmaciones sobre las capas del modelo OSI es la correcta?"),
    )

    assert "las capas del modelo OSI" in detalle
    assert FactKind.TECNICO.value not in detalle
