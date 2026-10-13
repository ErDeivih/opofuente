"""El veredicto de la clave de un conjunto: las dos fronteras y la cuenta, sin base de datos.

Lo que se prueba es la regla del §1 del objetivo, que es corta y conviene que lo siga siendo:

- por encima del **30 %** de discrepancia, `no_fiable`;
- entre el **15 %** y el **30 %**, `dudosa`;
- por debajo, `fiable`;
- y con menos de **15** preguntas medidas, `fiable` **por no poder medirse**, que es distinto de
  medirse bien.

Además, la cuenta: una pregunta con ancla en dos temas cuenta **una** vez (si no, el denominador del
conjunto se inflaría sin añadir información).
"""

from __future__ import annotations

import pytest

from opofuente.domain.key_reliability import (
    MINIMO_COMPROBADAS,
    AnclaMedible,
    KeyReliability,
    MedidaDeConjunto,
    discrepante,
    letras_de_clave,
    medir_conjuntos,
    probar_desplazamientos,
    veredicto,
)


@pytest.mark.parametrize(
    ("comprobadas", "discrepantes", "esperado"),
    [
        # Las dos fronteras, con el valor exacto: 15 % es `dudosa` (no `fiable`) y 30 % es `dudosa`
        # (no `no_fiable`): la frontera de arriba es **estricta** («por encima del 30 %»).
        (20, 6, KeyReliability.DUDOSA),
        (20, 7, KeyReliability.NO_FIABLE),
        (20, 3, KeyReliability.DUDOSA),
        (20, 2, KeyReliability.FIABLE),
        (100, 30, KeyReliability.DUDOSA),
        (100, 31, KeyReliability.NO_FIABLE),
        (100, 15, KeyReliability.DUDOSA),
        (100, 14, KeyReliability.FIABLE),
        # Un conjunto sin nada comprobado no es un conjunto en cuarentena.
        (0, 0, KeyReliability.FIABLE),
        # Los casos reales medidos: el peor conjunto de la base y el que roza la frontera.
        (18, 16, KeyReliability.NO_FIABLE),
        (60, 9, KeyReliability.DUDOSA),
    ],
)
def test_las_fronteras_del_30_y_del_15(
    comprobadas: int, discrepantes: int, esperado: KeyReliability
) -> None:
    assert veredicto(comprobadas, discrepantes) is esperado


def test_por_debajo_del_minimo_no_se_opina() -> None:
    """14 de 14 son un 100 % que no dice nada: no se puede medir, así que no se cuarentena.

    Es la decisión conservadora: castigar un conjunto por una muestra que no llega al mínimo sería
    dejar fuera de los tests material por ruido estadístico.
    """
    assert MINIMO_COMPROBADAS == 15
    assert veredicto(14, 14) is KeyReliability.FIABLE
    assert veredicto(15, 5) is KeyReliability.NO_FIABLE, "con 15 ya se opina"


@pytest.mark.parametrize(
    ("crudo", "esperado"),
    [
        ('["a"]', ("a",)),
        ('["A", "c"]', ("a", "c")),
        ("b", ("b",)),
        ("a,c", ("a", "c")),
        ("", ()),
        (None, ()),
    ],
)
def test_las_letras_de_la_clave_se_leen_en_las_dos_formas(crudo, esperado) -> None:
    """La clave se guarda como JSON, pero una importación vieja puede traer `a` o `a,c`."""
    assert letras_de_clave(crudo) == esperado


@pytest.mark.parametrize(
    ("letra", "clave", "esperado"),
    [
        ("b", ("b",), False),
        ("B", ("b",), False),
        ("b.", ("b",), False),
        ("c", ("b",), True),
        ("a", ("a", "c"), False),
        (None, ("a",), False),
        ("a", (), False),
        ("", ("a",), False),
    ],
)
def test_una_letra_distinta_de_la_clave_es_discrepancia(letra, clave, esperado) -> None:
    assert discrepante(letra, clave) is esperado


def test_una_pregunta_con_ancla_en_dos_temas_cuenta_una_vez() -> None:
    """La pregunta es del **conjunto**, no del tema: contarla dos veces infla el denominador."""
    anclas = [
        AnclaMedible("set-1", "Banco malo", "p1", "a", '["b"]'),
        AnclaMedible("set-1", "Banco malo", "p1", "a", '["b"]'),
        AnclaMedible("set-1", "Banco malo", "p2", "a", '["b"]'),
    ]
    medidas = medir_conjuntos(anclas)
    assert len(medidas) == 1
    assert medidas[0].comprobadas == 2
    assert medidas[0].discrepantes == 2


def test_las_anclas_sin_letra_o_sin_clave_no_cuentan() -> None:
    """No se puede comparar lo que no está: sin letra o sin clave la pregunta no entra."""
    anclas = [
        AnclaMedible("set-1", "Banco", "p1", None, '["b"]'),
        AnclaMedible("set-1", "Banco", "p2", "a", None),
        AnclaMedible("set-1", "Banco", "p3", "a", "[]"),
        AnclaMedible("set-1", "Banco", "p4", "a", '["b"]'),
    ]
    medidas = medir_conjuntos(anclas)
    assert medidas[0].comprobadas == 1
    assert medidas[0].discrepantes == 1


def test_una_clave_vacia_no_es_una_discrepancia() -> None:
    """`expected_letters = '[]'` es una pregunta **sin clave**, no una clave que discute.

    Es la reconciliación de dos mediciones de la misma base, y va con prueba porque el error es
        fácil de cometer: un test de subcadena sobre el texto guardado (`instr('[]', 'c') = 0` en
      SQLite)
    da «discrepancia» para toda pregunta sin clave, y eso sube a `no_fiable` conjuntos que solo
    tienen preguntas sin clave. Medido en la base real: en «Doc Adicional» son 10 anclas de 38, y
    contarlas como discrepancia lo llevaba del 25 % al 44,7 %; lo mismo en otros tres conjuntos.
    """
    # 20 preguntas con clave de las que 5 discrepan, más 10 sin clave: la clave vacía **no** es un
    # numerador ni un denominador.
    anclas = [
        *(AnclaMedible("set-1", "Banco", f"ok{i}", "a", '["a"]') for i in range(15)),
        *(AnclaMedible("set-1", "Banco", f"mal{i}", "a", '["b"]') for i in range(5)),
        *(AnclaMedible("set-1", "Banco", f"sin{i}", "a", "[]") for i in range(10)),
    ]
    medidas = medir_conjuntos(anclas)
    assert medidas[0].comprobadas == 20, "las diez sin clave no entran en el denominador"
    assert medidas[0].discrepantes == 5
    # 5/20 = 25 % → `dudosa`. Contando las diez sin clave como discrepancia saldría 15/30 = 50 % →
    # `no_fiable`: el mismo dato, dos veredictos, y el bueno es el que no cuenta lo que no se puede
    # comparar.
    assert medidas[0].veredicto is KeyReliability.DUDOSA
    assert 15 / 30 > 0.30, "la definición que sí las cuenta cruzaría el 30 %"


def test_si_alguna_ancla_de_la_pregunta_discrepa_la_pregunta_discrepa() -> None:
    """La variante conservadora: no se tira la evidencia de un tema porque otro tema salió bien.

    Una pregunta comprobada en dos temas puede salir «bien» en uno y «mal» en el otro: la clave no
    puede ser buena y mala a la vez, así que la pregunta **discrepa**. Es la regla que evita que un
    segundo tema esconda un problema del primero.
    """
    anclas = [
        # La misma pregunta, comprobada en dos temas: en uno cuadra y en el otro no.
        AnclaMedible("set-1", "Banco", "p1", "a", '["a"]'),
        AnclaMedible("set-1", "Banco", "p1", "c", '["a"]'),
        # Otra que cuadra en los dos: esa no discrepa.
        AnclaMedible("set-1", "Banco", "p2", "a", '["a"]'),
        AnclaMedible("set-1", "Banco", "p2", "a", '["a"]'),
    ]
    medidas = medir_conjuntos(anclas)
    assert medidas[0].comprobadas == 2, "dos preguntas, no cuatro anclas"
    assert medidas[0].discrepantes == 1


def test_la_medida_ordena_lo_peor_primero_y_dice_su_veredicto() -> None:
    anclas = [
        *(AnclaMedible("set-peor", "Banco peor", f"a{i}", "a", '["b"]') for i in range(18)),
        *(AnclaMedible("set-bueno", "Banco bueno", f"b{i}", "a", '["a"]') for i in range(20)),
        *(AnclaMedible("set-corto", "Banco corto", f"c{i}", "a", '["b"]') for i in range(5)),
    ]
    medidas = medir_conjuntos(anclas)
    assert [medida.set_id for medida in medidas] == ["set-peor", "set-corto", "set-bueno"]
    por_id = {medida.set_id: medida for medida in medidas}
    assert por_id["set-peor"].veredicto is KeyReliability.NO_FIABLE
    assert por_id["set-bueno"].veredicto is KeyReliability.FIABLE
    assert por_id["set-corto"].veredicto is KeyReliability.FIABLE
    assert not por_id["set-corto"].medible, "5 comprobadas no llegan al mínimo"
    assert "sin medir" in por_id["set-corto"].linea()


def test_el_veredicto_dice_quien_entra_en_los_tests_y_quien_se_marca() -> None:
    """Las dos propiedades que usan el motor y la pantalla, en un solo sitio."""
    assert KeyReliability.FIABLE.entra_en_los_tests
    assert KeyReliability.DUDOSA.entra_en_los_tests
    assert not KeyReliability.NO_FIABLE.entra_en_los_tests

    assert not KeyReliability.FIABLE.se_marca_al_alumno
    assert KeyReliability.DUDOSA.se_marca_al_alumno
    assert not KeyReliability.NO_FIABLE.se_marca_al_alumno, (
        "no entra en los tests, así que no hay nada que marcar"
    )


def test_la_prueba_del_desplazamiento_encuentra_la_clave_corrida() -> None:
    """Si la clave está una pregunta más allá, la prueba lo dice y baja del 10 %.

    Es el paso barato del §1: antes de dar por mala una clave, se comprueba si la extracción se fue
    una pregunta. Aquí las 20 preguntas de los apuntes dicen «a» y la clave guardada dice «a» en la
    posición de al lado: movida una, coincide todo.
    """
    anclas = [(posicion, "a") for posicion in range(1, 21)]
    # La clave de la posición `p` es la de la pregunta `p - 1`: está corrida una posición.
    claves = dict.fromkeys(range(0, 20), "a")

    lecturas = probar_desplazamientos(
        anclas,
        claves,
        actual=MedidaDeConjunto("s", "Banco", comprobadas=20, discrepantes=20),
    )

    por_descripcion = {lectura.descripcion: lectura for lectura in lecturas}
    assert por_descripcion["lectura de hoy"].discrepancia == 1.0
    assert por_descripcion["la clave, -1 pregunta(s)"].discrepancia == 0.0
    assert por_descripcion["la clave, -1 pregunta(s)"].explica_la_discrepancia
    assert not por_descripcion["lectura de hoy"].explica_la_discrepancia


def test_la_prueba_del_desplazamiento_no_inventa_una_explicacion() -> None:
    """Cuando la clave no está corrida, ninguna alternativa baja del 10 % y se dice.

    Es el caso de los nueve conjuntos de «respuestas marcadas» de la base real: probadas las cuatro
    preguntas vecinas y los tres giros de opciones, la mejor sigue por encima del 10 %, así que la
    clave no está corrida.
    """
    anclas = [(posicion, "a") for posicion in range(1, 21)]
    # Una clave que no tiene nada que ver: la mitad «c», la mitad «d», y sin relación con la vecina.
    claves = {posicion: ("c" if posicion % 2 else "d") for posicion in range(1, 21)}

    lecturas = probar_desplazamientos(
        anclas,
        claves,
        actual=MedidaDeConjunto("s", "Banco", comprobadas=20, discrepantes=20),
    )

    assert len(lecturas) == 8, "la de hoy, cuatro preguntas vecinas y tres giros de opciones"
    assert not any(lectura.explica_la_discrepancia for lectura in lecturas)
