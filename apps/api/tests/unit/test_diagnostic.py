"""Pruebas del simulacro y del diagnóstico (DEBT-012): la muestra, el intervalo y sus límites.

Lo que se comprueba aquí, y por qué importa:

- el **reparto de la muestra** cubre temas antes de repetir en uno, y dice qué temas quedaron fuera
por
  el tope: un diagnóstico que no mira cuatro temas no puede decir nada de ellos;
- el **intervalo** con dos aciertos de dos **no** es «dominio perfecto»: es exactamente lo que
  `06_QUESTIONS` §5 prohíbe enseñar como porcentaje;
- un tema sin respuestas en la muestra se declara, en lugar de quedarse con un cero que parecería un
  suspenso.
"""

from __future__ import annotations

from opofuente.domain.diagnostic import (
    DiagnosticTopic,
    order_for_mock,
    read_diagnostic,
    stratified_sample,
    wilson_interval,
)


def _tema(node_id: str, titulo: str, cuantas: int) -> DiagnosticTopic:
    return DiagnosticTopic(
        node_id=node_id,
        title=titulo,
        question_ids=tuple(f"{node_id}-q{numero}" for numero in range(1, cuantas + 1)),
    )


# --- simulacro ------------------------------------------------------------------------------------


def test_el_simulacro_prefiere_lo_que_no_se_ha_visto_y_no_pierde_ninguna() -> None:
    """Ordena sin descartar: la composición decide cuántas repite y eso se dice después."""
    frescas, repetidas = order_for_mock(
        ["q1", "q2", "q3", "q4"], recently_seen=frozenset({"q2", "q4"})
    )

    assert frescas == ("q1", "q3")
    assert repetidas == ("q2", "q4")


def test_sin_preguntas_vistas_no_hay_nada_que_reordenar() -> None:
    frescas, repetidas = order_for_mock(["q1", "q2"], recently_seen=frozenset())

    assert frescas == ("q1", "q2")
    assert repetidas == ()


# --- muestra del diagnóstico ----------------------------------------------------------------------


def test_la_muestra_reparte_antes_de_repetir_en_un_tema() -> None:
    """Con tres temas y dos preguntas por tema, la primera vuelta entra antes que la segunda."""
    muestra = stratified_sample(
        [_tema("t1", "Tema 1", 2), _tema("t2", "Tema 2", 2), _tema("t3", "Tema 3", 2)]
    )

    assert muestra.question_ids == ("t1-q1", "t2-q1", "t3-q1", "t1-q2", "t2-q2", "t3-q2")
    assert len(muestra.topics) == 3
    assert "6 preguntas en 3 tema(s) de 3 con preguntas" in muestra.detail


def test_el_tope_recorta_la_muestra_y_dice_que_temas_se_quedan_fuera() -> None:
    """Un tope que deja temas sin mirar no se calla: se dice cuáles, para poder subirlo.

    El reparto es round-robin, así que con tope 3 y cinco temas entran los tres primeros y los otros
    dos se quedan fuera **sin ninguna pregunta**: eso es lo que hay que decir.
    """
    muestra = stratified_sample(
        [
            _tema("t1", "Tema 1", 2),
            _tema("t2", "Tema 2", 2),
            _tema("t3", "Tema 3", 2),
            _tema("t4", "Tema 4", 2),
            _tema("t5", "Tema 5", 2),
        ],
        per_topic=2,
        limit=3,
    )

    assert muestra.question_ids == ("t1-q1", "t2-q1", "t3-q1")
    assert len(muestra.topics) == 3
    assert muestra.uncovered_topics == ("Tema 4", "Tema 5")
    assert "el tope de la muestra dejó fuera 2 tema(s)" in muestra.detail


def test_las_preguntas_sin_tema_no_entran_y_se_cuentan() -> None:
    """Sin tema no se puede estratificar: se quedan fuera y el número se declara."""
    muestra = stratified_sample(
        [_tema("t1", "Tema 1", 2), _tema("t2", "Tema 2", 2), _tema("t3", "Tema 3", 2)],
        without_topic=7,
    )

    assert len(muestra.question_ids) == 6
    assert muestra.without_topic == 7
    assert "7 pregunta(s) del banco no tienen tema asignado" in muestra.detail


def test_un_tema_sin_preguntas_no_estratifica_nada() -> None:
    muestra = stratified_sample([_tema("t1", "Tema 1", 0), _tema("t2", "Tema 2", 2)])

    assert muestra.question_ids == ("t2-q1", "t2-q2")
    assert muestra.topics == ("t2",)
    assert "1 tema(s) de 1 con preguntas" in muestra.detail


# --- intervalo ------------------------------------------------------------------------------------


def test_dos_de_dos_no_es_dominio_perfecto() -> None:
    """El caso que la spec prohíbe leer como un porcentaje: Wilson lo deja claro."""
    intervalo = wilson_interval(2, 2)

    assert intervalo is not None
    assert intervalo.high == 1.0
    assert 0.3 < intervalo.low < 0.4, "el límite inferior real de 2/2 al 95 % ronda 0,34"
    assert intervalo.width > 0.6, "un intervalo así de ancho no es una nota"


def test_mas_muestra_estrecha_el_intervalo() -> None:
    """La incertidumbre baja al crecer la muestra: es lo que hace útil el intervalo.

    Se compara **la misma proporción** con dos tamaños (9 de 10 y 180 de 200) y no 2 de 20 con 18 de
    20:
    Wilson es simétrico, así que un 10 % y un 90 % con la misma `n` dan el mismo ancho. Comparar
    esos
    dos no diría nada de la muestra.
    """
    estrecho = wilson_interval(180, 200)
    ancho = wilson_interval(18, 20)

    assert estrecho is not None and ancho is not None
    assert estrecho.width < ancho.width / 3
    # 180 de 200 con Wilson al 95 %: de 0,851 a 0,934 (calculado a mano, no copiado del código).
    assert 0.84 < estrecho.low < 0.86
    assert 0.93 < estrecho.high < 0.94


def test_sin_respuestas_no_hay_intervalo() -> None:
    assert wilson_interval(0, 0) is None


def test_ningun_acierto_de_cuatro_da_un_intervalo_desde_cero() -> None:
    intervalo = wilson_interval(0, 4)

    assert intervalo is not None
    assert intervalo.low == 0.0
    assert 0.4 < intervalo.high < 0.6, "con 0 de 4 el techo sigue siendo alto: es la verdad"


# --- lectura --------------------------------------------------------------------------------------


def test_la_lectura_declara_la_muestra_corta_de_cada_tema() -> None:
    lectura = read_diagnostic(
        {
            "t1": ("Tema 1", 2, 2),
            "t2": ("Tema 2", 1, 0),
            "t3": ("Tema 3", 0, 0),
        },
        sample_size=6,
    )

    assert lectura.sample_size == 6
    assert lectura.answered == 3
    assert [ficha.title for ficha in lectura.topics] == ["Tema 1", "Tema 2", "Tema 3"]
    primera, segunda, tercera = lectura.topics
    assert primera.interval is not None and primera.interval.width > 0.6
    assert "la muestra solo trae 1 pregunta(s) de este tema" in segunda.note
    # 0 de 1 con Wilson al 95 %: de 0,0 a 0,79. Ni cero redondo ni dominio: lo que la muestra dice.
    assert segunda.interval is not None
    assert segunda.interval.low == 0.0
    assert 0.78 < segunda.interval.high < 0.80
    assert "no se contestó ninguna pregunta de este tema" in tercera.note
    assert tercera.interval is None, "sin respuestas no se inventa un intervalo"
    assert "no son una nota ni un dominio del tema" in lectura.detail
