"""La conversión de un cuestionario del INAP al texto que el importador entiende (D10).

Lo que se comprueba aquí no es «el extractor devuelve algo»: es que **la numeración oficial llega
intacta** (posiciones repetidas por sección incluidas), que las reservas quedan marcadas, que una
opción partida en dos líneas se junta, que una cabecera de página no se pega al final de una opción,
que una línea que empieza por un número pero no es la pregunta que toca **se declara** en vez de
partir la pregunta en dos, y que un PDF sin capa de texto se rechaza diciéndolo.

El último caso es el que cierra el círculo: el texto convertido se le da al **parser de verdad** del
proyecto (`parse_questions`) y se comprueba que de ahí salen las mismas preguntas, con sus mismas
posiciones y sus reservas. Un conversor que solo se prueba contra sí mismo no prueba nada.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf
import pytest

from opofuente.domain.questions import parse_answer_key, parse_questions
from opofuente.infrastructure.inap import (
    SIN_ROTULO,
    extraer_cuestionario,
    lineas_del_pdf,
    secciones_de_plantilla,
    texto_de_importacion,
    texto_de_plantilla,
)

#: Cabecera y pie como los repite el INAP en cada página.
CABECERA = "2024 - TAI-L - MODELO A"
PIE = "Página 1 de 4"


def _escribir_pdf(path: Path, paginas: list[list[str]]) -> Path:
    """Un PDF con una lista de líneas por página, tal como las pondría el extractor del INAP."""
    documento = pymupdf.open()
    for lineas in paginas:
        pagina = documento.new_page()
        y = 72.0
        for linea in lineas:
            pagina.insert_text((60, y), linea, fontsize=10)
            y += 14
    documento.save(str(path))
    documento.close()
    return path


def _cuestionario_de_ejemplo(path: Path) -> Path:
    """Un cuestionario en miniatura con la estructura real: dos partes, reservas y numeración que
    vuelve a empezar en cada sección."""
    pagina_1 = [
        CABECERA,
        PIE,
        "PRIMERA PARTE",
        "1. ¿Cuál es la capital de España?",
        "a)",
        "Madrid.",
        "b) Barcelona.",
        "c) Lisboa.",
        "d)",
        "Oporto, que está en Portugal y no es la capital de nada.",
        "2. ¿Cuántos lados tiene un triángulo?",
        "a) Tres.",
        "b) Cuatro.",
        "c) Cinco.",
        "d) Seis.",
        "Preguntas de reserva",
        "1.",
        "¿Cuál es el río más largo de España?",
        "a) El Ebro.",
        "b) El Tajo.",
        "c) El Duero.",
        "d) El Guadalquivir.",
    ]
    pagina_2 = [
        CABECERA,
        "Página 2 de 4",
        "SUPUESTO I",
        "1. Con los datos del escenario, ¿qué tabla usaría?",
        "a) La primera.",
        "b) La segunda.",
        "c) La tercera.",
        "d) Ninguna.",
        "2. Y si el escenario cambiara, ¿qué haría?",
        "a) Nada.",
        "b) Algo.",
        "c) Otra cosa.",
        "d) Todo.",
    ]
    return _escribir_pdf(path, [pagina_1, pagina_2])


def test_la_numeracion_oficial_y_las_reservas_llegan_al_texto(tmp_path: Path) -> None:
    """Dos secciones, la numeración vuelve a empezar y la reserva va marcada con `(R)`."""
    extraido = extraer_cuestionario(_cuestionario_de_ejemplo(tmp_path / "cuestionario.pdf"))

    assert [seccion.rotulo for seccion in extraido.secciones] == [
        "PRIMERA PARTE",
        "Preguntas de reserva",
        "SUPUESTO I",
    ]
    assert [seccion.es_reserva for seccion in extraido.secciones] == [False, True, False]
    # La numeración **no** se renumera: la reserva es la 1 de su sección y el supuesto empieza en 1.
    assert [pregunta.numero for pregunta in extraido.preguntas] == [1, 2, 1, 1, 2]
    assert [pregunta.es_reserva for pregunta in extraido.preguntas] == [
        False,
        False,
        True,
        False,
        False,
    ]
    assert extraido.ordinarias == 4
    assert extraido.reservas == 1

    texto = texto_de_importacion(extraido)
    assert "## PRIMERA PARTE" in texto
    assert "## Preguntas de reserva" in texto
    assert "1. (R) ¿Cuál es el río más largo de España?" in texto
    # La opción partida en dos líneas se junta en **una** línea, como pide el parser.
    assert "d) Oporto, que está en Portugal y no es la capital de nada." in texto


def test_el_texto_convertido_lo_lee_el_parser_de_verdad(tmp_path: Path) -> None:
    """El contrato del conversor es el parser del proyecto, no una idea propia de su formato."""
    extraido = extraer_cuestionario(_cuestionario_de_ejemplo(tmp_path / "cuestionario.pdf"))
    parseado = parse_questions(texto_de_importacion(extraido))

    assert [pregunta.number for pregunta in parseado.questions] == [1, 2, 1, 1, 2]
    assert [pregunta.is_reserve for pregunta in parseado.questions] == [
        False,
        False,
        True,
        False,
        False,
    ]
    # La marca `(R)` **no** forma parte del enunciado: el parser la quita.
    reserva = next(pregunta for pregunta in parseado.questions if pregunta.is_reserve)
    assert reserva.stem == "¿Cuál es el río más largo de España?"
    assert [opcion.text for opcion in reserva.options] == [
        "El Ebro.",
        "El Tajo.",
        "El Duero.",
        "El Guadalquivir.",
    ]
    assert not parseado.issues, [incidencia.detail for incidencia in parseado.issues]


def test_una_linea_que_empieza_por_un_numero_no_parte_la_pregunta(tmp_path: Path) -> None:
    """Dos trampas reales: una opción que empieza por cifra y un número que no es el que toca."""
    paginas = [
        [
            CABECERA,
            PIE,
            "PRIMERA PARTE",
            "1. ¿Qué velocidad tiene el estándar?",
            "a) 802.1w.",
            "b) La velocidad es 400",
            "57. es el otro valor del enunciado, no una pregunta.",
            "c) 802.11az.",
            "d) 22",
            "2. ¿Cuál de estos es un puerto?",
            "a) 22.",
            "b) 443.",
            "c) 8080.",
            "d) 3306.",
        ]
    ]
    extraido = extraer_cuestionario(_escribir_pdf(tmp_path / "cuestionario.pdf", paginas))

    assert [pregunta.numero for pregunta in extraido.preguntas] == [1, 2]
    assert extraido.preguntas[0].opciones[0].texto == "802.1w."
    # La línea que empieza por «57.» **no** abre una pregunta: es la continuación de la opción b).
    assert extraido.preguntas[0].opciones[1].texto == (
        "La velocidad es 400 57. es el otro valor del enunciado, no una pregunta."
    )
    # Y lo que se leyó como continuación **se declara**: no se tira en silencio.
    saltados = [descarte for descarte in extraido.descartes if descarte.clase == "numero_saltado"]
    assert len(saltados) == 1
    assert "57" in saltados[0].detalle


def test_la_cabecera_repetida_no_ensucia_la_ultima_opcion(tmp_path: Path) -> None:
    """La cabecera va entre la última opción de una página y la primera pregunta de la siguiente."""
    paginas = [
        [CABECERA, PIE, "1. Primera pregunta:", "a) Uno.", "b) Dos.", "c) Tres.", "d) Cuatro."],
        [
            CABECERA,
            "Página 2 de 2",
            "2. Segunda pregunta:",
            "a) Uno.",
            "b) Dos.",
            "c) Tres.",
            "d) Cuatro.",
        ],
    ]
    extraido = extraer_cuestionario(_escribir_pdf(tmp_path / "cuestionario.pdf", paginas))

    primera = extraido.preguntas[0]
    assert primera.opciones[-1].texto == "Cuatro."
    assert "Página" not in primera.opciones[-1].texto
    # Dos cabeceras y dos pies: cada página trae los suyos, y los cuatro se declaran.
    assert len(extraido.cabeceras_quitadas) == 4
    assert extraido.secciones[0].rotulo == SIN_ROTULO


def test_un_pdf_sin_capa_de_texto_se_declara_y_no_se_inventa(tmp_path: Path) -> None:
    """Un escaneo no se transcribe a mano: se rechaza con su motivo (los tres de 2018)."""
    documento = pymupdf.open()
    documento.new_page()
    ruta = tmp_path / "escaneado.pdf"
    documento.save(str(ruta))
    documento.close()

    extraido = extraer_cuestionario(ruta)
    assert extraido.preguntas == ()
    assert [descarte.clase for descarte in extraido.descartes] == ["sin_capa_de_texto"]
    assert texto_de_importacion(extraido).strip() == ""


def test_la_plantilla_se_manda_tal_cual(tmp_path: Path) -> None:
    """Ni una letra se toca: `ANULADA`, `MODIFICADA` y la numeración repetida se quedan."""
    pagina = [
        "PLANTILLA DEFINITIVA DE RESPUESTAS DEL EJERCICIO ÚNICO",
        "Cuerpo de Técnicos Auxiliares de Informática de la Administración del Estado",
        "MODELO A",
        "Primera parte",
        "1.",
        "b",
        "2.",
        "c",
        "3. ANULADA",
        "Reserva",
        "1. a",
        "Supuesto I",
        "1.",
        "d MODIFICADA",
    ]
    ruta = _escribir_pdf(tmp_path / "plantilla.pdf", [pagina])

    texto = texto_de_plantilla(ruta)
    assert "PLANTILLA DEFINITIVA" not in texto
    assert "Primera parte" not in texto
    assert "Reserva" not in texto
    # Las respuestas, con sus marcas y su numeración reiniciada, siguen ahí.
    assert texto.splitlines()[:6] == ["1.", "b", "2.", "c", "3. ANULADA", "1. a"]
    assert "d MODIFICADA" in texto

    lineas, incidencias = parse_answer_key(texto)
    assert not incidencias, [incidencia.detail for incidencia in incidencias]
    assert [(linea.position, linea.outcome.value) for linea in lineas] == [
        (1, "keyed"),
        (2, "keyed"),
        (3, "annulled"),
        (1, "keyed"),
        (1, "keyed"),
    ]
    assert lineas[-1].note == "respuesta modificada"


def test_los_recuentos_de_la_plantilla_se_comparan_con_los_del_cuestionario(tmp_path: Path) -> None:
    """La comprobación que evita el error de la numeración, sección a sección."""
    cuestionario = _cuestionario_de_ejemplo(tmp_path / "cuestionario.pdf")
    plantilla = _escribir_pdf(
        tmp_path / "plantilla.pdf",
        [
            [
                "PLANTILLA",
                "PRIMERA PARTE",
                "1. a",
                "2. b",
                "Preguntas de reserva",
                "1. c",
                "SUPUESTO I",
                "1. d",
                "2. a",
            ]
        ],
    )
    extraido = extraer_cuestionario(cuestionario)
    secciones = [seccion for seccion in secciones_de_plantilla(plantilla) if seccion.lineas]
    assert [len(seccion.lineas) for seccion in secciones] == [2, 1, 2]
    assert [len(seccion.preguntas) for seccion in extraido.secciones] == [2, 1, 2]


def test_las_lineas_del_pdf_conservan_su_orden_y_su_numero(tmp_path: Path) -> None:
    ruta = _cuestionario_de_ejemplo(tmp_path / "cuestionario.pdf")
    lineas = lineas_del_pdf(ruta)
    numeros = [numero for numero, _texto in lineas]
    assert numeros == sorted(numeros)
    assert all("Página" not in texto for _numero, texto in lineas)


@pytest.mark.parametrize("nombre", ["TAI-2024-libre-cuestionario-unico-A.pdf"])
def test_el_cuestionario_de_verdad_no_pierde_preguntas_si_esta_disponible(
    nombre: str,
) -> None:
    """Si el PDF original está en la máquina, la conversión se mide contra él (no se hereda).

    Se salta cuando el fichero no está: la suite de puertas tiene que poder correr en cualquier
    máquina, pero en la del propietario —que es donde se importa— esta comprobación sí corre y dice
    los números que importan.
    """
    base = Path(r"F:\OpoFuente\fuentes\inap-tai")
    if not (base / nombre).exists():
        pytest.skip(f"el cuestionario original no está en {base}")
    extraido = extraer_cuestionario(base / nombre)
    assert [len(seccion.preguntas) for seccion in extraido.secciones] == [80, 5, 20, 5, 20, 5]
    assert extraido.ordinarias == 120
    assert extraido.reservas == 15
    assert not [descarte for descarte in extraido.descartes if descarte.clase == "linea_descartada"]
