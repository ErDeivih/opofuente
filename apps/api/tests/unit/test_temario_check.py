"""El chequeo del temario guardado, tema a tema, sin red y sin modelo (O3).

Lo que se comprueba aquí es lo que el `REFERENCIA-OPOSICIONESINFORMATICA` exige a un tema escrito:
que todos los epígrafes del enunciado oficial tengan apartado, que estén las seis partes de la
estructura fija (índice, desarrollo, normativa, resumen, mapa conceptual y preguntas), que haya
entre 10 y 20 preguntas de autoevaluación con clave, explicación y evidencia **separadas**, y que
las normas citadas lleven fecha de consolidación. La vigencia y la derogación **no** se inventan:
sin catálogo autorizado del BOE quedan `no evaluable`, con su motivo.

El chequeo es informativo: un tema en `parcial` no se bloquea ni cambia las puertas de forma y
cobertura que ya existen. Por eso las pruebas miran el estado que se informa, no un booleano de
paso.
"""

from __future__ import annotations

from dataclasses import dataclass

from opofuente.domain.temario_check import (
    MOTIVO_SIN_CATALOGO_BOE,
    Estado,
    revisar_temario,
)

NODO = (
    ("IV.7.1", "Modelo OSI"),
    ("IV.7.2", "Protocolos TCP/IP"),
)


@dataclass(frozen=True)
class _Apartado:
    key: str
    title: str
    epigraph_code: str
    body_markdown: str


def _bloque_pregunta(numero: int) -> str:
    return "\n".join(
        (
            f"{numero}. ¿Cuántas capas tiene el modelo OSI?",
            "   a) 5",
            "   b) 7",
            "   c) 9",
            "   d) 11",
            "   **Respuesta correcta:** b",
            "   **Explicación:** El modelo OSI tiene siete capas.",
            "   **Evidencia:** IV.7.1, apartado «El modelo OSI».",
        )
    )


def _preguntas_texto(cuantas: int) -> str:
    return "\n\n".join(_bloque_pregunta(numero) for numero in range(1, cuantas + 1))


def _seis_partes(epigraph_code: str = "IV.7.1") -> list[_Apartado]:
    """Un tema con las seis partes, todas con texto y bajo un epígrafe oficial."""
    return [
        _Apartado("indice", "Índice", epigraph_code, "1. Modelo OSI. 2. Protocolos."),
        _Apartado(
            "desarrollo",
            "El modelo OSI",
            epigraph_code,
            "El modelo OSI tiene siete capas y cada una cumple una función distinta.",
        ),
        _Apartado(
            "normativa",
            "Normativa vigente",
            epigraph_code,
            "Ley 39/2015, de 1 de octubre. Texto consolidado a 2 de abril de 2024.",
        ),
        _Apartado(
            "resumen",
            "Resumen",
            epigraph_code,
            "Siete capas, de la física a la aplicación.",
        ),
        _Apartado(
            "mapa",
            "Mapa conceptual",
            epigraph_code,
            "OSI -> capas -> protocolos -> servicios.",
        ),
        _Apartado(
            "preguntas",
            "Preguntas de autoevaluación",
            epigraph_code,
            _preguntas_texto(10),
        ),
        _Apartado(
            "protocolos",
            "Protocolos TCP/IP",
            "IV.7.2",
            "La familia TCP/IP agrupa los protocolos de transporte y de aplicación.",
        ),
    ]


def _revisar(apartados: list[_Apartado], *, nodo: tuple[tuple[str, str], ...] = NODO):
    return revisar_temario(
        code="IV.7",
        title="Redes",
        epigraphs=nodo,
        apartados=apartados,
    )


def test_un_tema_con_todos_los_epigrafes_y_las_seis_partes_esta_ok() -> None:
    revision = _revisar(_seis_partes())
    assert revision.estado is Estado.OK
    assert revision.epigrafes_cubiertos == ("IV.7.1", "IV.7.2")
    assert revision.epigrafes_sin_apartado == ()


def test_un_epigrafe_sin_apartado_deja_el_tema_en_parcial() -> None:
    apartados = [apartado for apartado in _seis_partes() if apartado.epigraph_code != "IV.7.2"]
    revision = _revisar(apartados)
    assert revision.estado is Estado.PARCIAL
    assert revision.epigrafes_sin_apartado == ("IV.7.2",)


def test_un_apartado_sin_texto_no_cubre_su_epigrafe() -> None:
    apartados = [apartado for apartado in _seis_partes() if apartado.epigraph_code != "IV.7.2"]
    apartados.append(_Apartado("vacio", "Protocolos", "IV.7.2", "   \n"))
    revision = _revisar(apartados)
    assert revision.epigrafes_sin_apartado == ("IV.7.2",)
    assert revision.estado is Estado.PARCIAL


def test_faltan_resumen_mapa_conceptual_y_preguntas() -> None:
    apartados = [
        apartado
        for apartado in _seis_partes()
        if apartado.key not in {"resumen", "mapa", "preguntas"}
    ]
    revision = _revisar(apartados)
    assert revision.partes_ausentes == ("resumen", "mapa_conceptual", "preguntas")
    assert revision.estado is Estado.PARCIAL


def test_las_citas_sin_fecha_de_consolidacion_se_listan() -> None:
    apartados = _seis_partes()
    apartados[2] = _Apartado(
        "normativa",
        "Normativa vigente",
        "IV.7.1",
        "Ley 39/2015, de 1 de octubre. Real Decreto 3/2010, de 8 de enero.",
    )
    revision = _revisar(apartados)
    assert [cita.referencia for cita in revision.citas_sin_fecha] == [
        "Ley 39/2015",
        "Real Decreto 3/2010",
    ]
    assert revision.estado is Estado.PARCIAL


def test_la_fecha_de_la_propia_norma_no_cuenta_como_consolidacion() -> None:
    apartados = _seis_partes()
    apartados[2] = _Apartado(
        "normativa",
        "Normativa vigente",
        "IV.7.1",
        "Ley 39/2015, de 1 de octubre.",
    )
    revision = _revisar(apartados)
    assert revision.citas_sin_fecha, "la fecha de promulgación no es la de consolidación"


def test_la_vigencia_no_se_puede_evaluar_sin_catalogo_autorizado_del_boe() -> None:
    revision = _revisar(_seis_partes())
    assert revision.estado_vigencia is Estado.NO_EVALUABLE
    assert revision.motivo_vigencia == MOTIVO_SIN_CATALOGO_BOE


def test_un_tema_sin_apartados_esta_ausente() -> None:
    revision = _revisar([])
    assert revision.estado is Estado.AUSENTE
    assert revision.epigrafes_sin_apartado == ("IV.7.1", "IV.7.2")


def test_un_tema_sin_epigrafes_oficiales_no_se_puede_evaluar() -> None:
    revision = _revisar(_seis_partes(), nodo=())
    assert revision.estado is Estado.NO_EVALUABLE
    assert revision.motivo is not None


def test_el_resumen_de_stdout_dice_el_estado_y_lo_que_falta() -> None:
    revision = _revisar(_seis_partes())
    texto = "\n".join(revision.lines())
    assert "IV.7" in texto
    assert "ok" in texto
    assert "IV.7.2" in texto
    assert "preguntas: 10" in texto


def _con_preguntas(texto: str) -> list[_Apartado]:
    apartados = _seis_partes()
    apartados[5] = _Apartado("preguntas", "Preguntas de autoevaluación", "IV.7.1", texto)
    return apartados


def test_diez_preguntas_completas_bastan_y_se_cuentan() -> None:
    revision = _revisar(_con_preguntas(_preguntas_texto(10)))
    assert len(revision.preguntas) == 10
    assert revision.preguntas_completas == revision.preguntas
    assert revision.estado is Estado.OK


def test_veinte_preguntas_completas_bastan() -> None:
    revision = _revisar(_con_preguntas(_preguntas_texto(20)))
    assert len(revision.preguntas) == 20
    assert revision.estado is Estado.OK


def test_nueve_preguntas_dejan_el_tema_en_parcial() -> None:
    revision = _revisar(_con_preguntas(_preguntas_texto(9)))
    assert revision.preguntas_fuera_de_rango
    assert revision.estado is Estado.PARCIAL
    assert revision.motivo is not None
    assert "fuera de 10-20: 9" in revision.motivo


def test_veintiuna_preguntas_dejan_el_tema_en_parcial() -> None:
    revision = _revisar(_con_preguntas(_preguntas_texto(21)))
    assert revision.preguntas_fuera_de_rango
    assert revision.estado is Estado.PARCIAL


def test_una_pregunta_sin_evidencia_es_incompleta_y_se_lista() -> None:
    texto = _preguntas_texto(10).replace(
        "   **Evidencia:** IV.7.1, apartado «El modelo OSI».\n\n", "", 1
    )
    revision = _revisar(_con_preguntas(texto))
    assert [pregunta.numero for pregunta in revision.preguntas_incompletas] == [1]
    assert revision.preguntas_incompletas[0].tiene_clave
    assert revision.preguntas_incompletas[0].tiene_explicacion
    assert not revision.preguntas_incompletas[0].tiene_evidencia
    assert revision.estado is Estado.PARCIAL
    assert revision.motivo is not None
    assert "1" in revision.motivo


def test_una_clave_que_no_es_una_letra_no_cuenta() -> None:
    texto = _preguntas_texto(10).replace(
        "**Respuesta correcta:** b", "**Respuesta correcta:** la segunda", 1
    )
    revision = _revisar(_con_preguntas(texto))
    assert not revision.preguntas[0].tiene_clave
    assert revision.estado is Estado.PARCIAL


def test_la_evidencia_igual_a_la_explicacion_no_cuenta_como_separada() -> None:
    texto = _preguntas_texto(10).replace(
        "**Evidencia:** IV.7.1, apartado «El modelo OSI».",
        "**Evidencia:** El modelo OSI tiene siete capas.",
        1,
    )
    revision = _revisar(_con_preguntas(texto))
    assert not revision.preguntas[0].tiene_evidencia
    assert revision.estado is Estado.PARCIAL


def test_las_preguntas_de_dos_apartados_se_suman() -> None:
    apartados = _con_preguntas(_preguntas_texto(5))
    apartados.append(
        _Apartado(
            "preguntas-2",
            "Preguntas de autoevaluación (segunda parte)",
            "IV.7.1",
            "\n\n".join(_bloque_pregunta(numero) for numero in range(6, 11)),
        )
    )
    revision = _revisar(apartados)
    assert len(revision.preguntas) == 10
    assert revision.estado is Estado.OK
    assert [pregunta.ubicacion for pregunta in revision.preguntas] == ["preguntas"] * 5 + [
        "preguntas-2"
    ] * 5
