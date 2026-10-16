"""Las cifras que la API **escribe en prosa**: en español, con coma y sin ceros de más (§2.2).

El encargo del propietario era «números en español», no «números en español en el navegador». Esta
prueba existe porque lo segundo fue exactamente lo que pasó: el frontend quedó unificado en un
módulo y **la frase que compone el servidor se quedó con el punto**, así que en la **misma fila**
de la tabla del diagnóstico convivían `0,34 - 1,00` (la columna, la pinta la pantalla) y
`0.3424 a 1.0` (la nota de esa fila, la escribe el servidor). Medido por el bloque que mide.

Se comprueban las cuatro frases que **el alumno o el propietario leen** y el módulo que las escribe,
una a una:

1. la estimación de una parte (`estimated_verdict_note`): nota con dos decimales, máximo y mínimo
   sin ceros de más;
2. el mínimo publicado de una parte corregida en directo: `el mínimo de 25`, no `25.0`;
3. el intervalo de un diagnóstico: `0,34 a 1,00`;
4. la cobertura de los apuntes del panel: `489/542 = 90,2 %` —que es **como su propio docstring
   decía que se enseña** desde antes de este arreglo—.

Y una cosa que **no** se toca, a propósito: ni los identificadores (`IV.1`, `50 preguntas`, una
versión) ni los informes de consola de los comandos (`apuntes --medir`, `claves_derivadas`), que no
los lee nadie desde la interfaz.
"""

from __future__ import annotations

import re
from fractions import Fraction

import pytest

from opofuente.domain.diagnostic import read_diagnostic
from opofuente.domain.notes_review import CifrasDelTema, razones_del_tema
from opofuente.domain.numeros import escala, nota, porcentaje
from opofuente.domain.study import PartRule, ScoringKind, estimated_verdict_note, verdict_for

#: Un decimal con punto: lo que **no** puede quedar a la vista en una frase que lee una persona.
PUNTO_DECIMAL = re.compile(r"\d\.\d")


def test_una_nota_va_con_coma_y_dos_decimales() -> None:
    assert nota(Fraction(1, 3)) == "0,33"
    assert nota(Fraction(0)) == "0,00"
    assert nota(Fraction(-1, 3)) == "-0,33"
    assert nota(Fraction(38, 3)) == "12,67"
    # Se redondea a la mitad hacia arriba, como `decimal_text`: lo que espera quien lee una nota.
    assert nota(Fraction(2, 3)) == "0,67"


def test_un_maximo_o_un_minimo_va_sin_ceros_de_mas() -> None:
    # «sobre 50» y no «sobre 50,00»: es la cifra que publica la convocatoria, y no se le añade
    # precisión. Con decimales de verdad, se enseñan (y con coma).
    assert escala(50) == "50"
    assert escala(25.0) == "25"
    assert escala(25.5) == "25,5"
    assert escala(Fraction(1, 3)) == "0,33"


def test_un_porcentaje_a_partir_de_una_proporcion() -> None:
    assert porcentaje(0.902) == "90,2 %"
    assert porcentaje(1.0) == "100,0 %"
    assert porcentaje(0.0) == "0,0 %"


def test_la_estimacion_de_una_parte_va_en_espanol() -> None:
    regla = PartRule(
        code="primera_parte",
        name="Primera parte",
        kind=ScoringKind.ESTIMATED,
        ordinary_items=80,
        score_max=50.0,
        pass_score=25.0,
        penalty=Fraction(1, 3),
    )

    texto = estimated_verdict_note(regla, Fraction(1, 3))

    assert "es 0,33 sobre 50" in texto
    assert "(25)" in texto
    assert not PUNTO_DECIMAL.search(texto), f"quedan decimales con punto: {texto}"


def test_el_minimo_publicado_de_una_parte_directa_va_en_espanol() -> None:
    regla = PartRule(
        code="primera_parte",
        name="Primera parte",
        kind=ScoringKind.DIRECT,
        score_max=50.0,
        pass_score=25.0,
        penalty=Fraction(1, 3),
    )

    veredicto = verdict_for(regla, Fraction(1, 3), wrong=0)

    assert "el mínimo de 25 es de la calificación oficial" in veredicto.reason
    assert not PUNTO_DECIMAL.search(veredicto.reason), veredicto.reason


def test_la_nota_de_un_diagnostico_va_en_espanol_y_cuadra_con_la_columna() -> None:
    lectura = read_diagnostic(
        {"nodo": ("La Constitución Española de 1978", 2, 2)},
        sample_size=2,
        per_topic=1,
    )

    ficha = lectura.topics[0]
    assert ficha.interval is not None
    # El intervalo de 2/2 al 95 % ronda 0,34 por abajo; aquí importa **el formato**: la nota del
    # servidor y la columna que pinta la pantalla tienen que decir lo mismo.
    assert re.search(r"va de 0,3\d a 1,00$", ficha.note), ficha.note
    assert not PUNTO_DECIMAL.search(ficha.note), ficha.note


def test_la_cobertura_de_los_apuntes_va_en_espanol() -> None:
    """La cifra que el docstring de `Razon` escribe con coma desde antes de este arreglo."""
    cifras = CifrasDelTema(
        has_sections=True,
        published=False,
        measured=True,
        covered=489,
        with_key=542,
        covered_all_keys=489,
        with_key_all_keys=542,
    )

    assert cifras.cobertura_texto == "489/542 = 90,2 %"
    assert cifras.cobertura_todas_las_claves_texto == "489/542 = 90,2 %"
    assert not PUNTO_DECIMAL.search(cifras.cobertura_texto)


def test_el_motivo_del_borrador_que_lleva_la_cifra_tambien() -> None:
    """La frase del motivo —«Contesta al … % de las preguntas…»— y su cifra: las dos en español."""
    cifras = CifrasDelTema(
        has_sections=True, published=False, measured=True, covered=40, with_key=100
    )
    razones = razones_del_tema(cifras)

    textos = " ".join(razon.text for razon in razones)
    cifras_sueltas = " ".join(razon.figure or "" for razon in razones)
    assert "40,0 %" in textos
    assert "40/100 = 40,0 %" in cifras_sueltas
    assert not PUNTO_DECIMAL.search(textos), textos
    assert not PUNTO_DECIMAL.search(cifras_sueltas), cifras_sueltas


@pytest.mark.parametrize("valor", [0.0, 1.0, 0.5, 0.902])
def test_el_porcentaje_nunca_deja_un_punto(valor: float) -> None:
    assert not PUNTO_DECIMAL.search(porcentaje(valor))
