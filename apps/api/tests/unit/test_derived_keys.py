"""La clave derivada: cuando dos fuentes independientes dicen la misma letra (§1 del encargo F29).

Todo lo de este fichero es **puro**: no hay base de datos ni modelo. Es la regla la que se prueba
—cuándo se deriva, cuándo no y por qué—, y las tres palabras que la sostienen:

- **la coincidencia** no se inventa: letra de los apuntes **con cita verificada** y letra del modelo
  **sin apuntes**, comparadas de la misma forma en que se comparan en todo el motor de claves;
- **los tres motivos** de quedarse fuera, en el orden del informe (sin material → sin cita → sin
  coincidencia), porque cambiar el orden cambia a quién se le echa la culpa;
- **las claves oficiales no se derivan**, por los tres caminos que llevan a «oficial»: el tipo del
  conjunto, la plantilla enlazada a un documento y la procedencia de la AGE.
"""

from __future__ import annotations

import pytest

from opofuente.domain.derived_keys import (
    UMBRAL_VUELVE_A_LOS_TESTS,
    DecisionDeConjunto,
    Derivacion,
    FuenteDeLosApuntes,
    KeyTrust,
    MotivoDeFuera,
    RespuestaDelModelo,
    coinciden,
    decidir_conjuntos,
    derivar,
    protege_derivar,
    recuento_de_fuera,
)


def _apuntes(
    letra: str | None = "b",
    cita: str | None = "La respuesta correcta es la b.",
    *,
    key_status: str = "active",
) -> FuenteDeLosApuntes:
    return FuenteDeLosApuntes(
        question_version_id="p1",
        anchor_id="a1",
        letra=letra or "",
        cita=cita or "",
        key_status=key_status,
    )


def _modelo(letra: str | None) -> RespuestaDelModelo:
    return RespuestaDelModelo(question_version_id="p1", letra=letra)


# --- la coincidencia ------------------------------------------------------------------------------


def test_deriva_cuando_los_apuntes_y_el_modelo_dicen_la_misma_letra() -> None:
    resultado = derivar(_apuntes("b"), _modelo("b"))

    assert isinstance(resultado, Derivacion)
    assert resultado.letra == "b"
    assert resultado.apuntes.cita == "La respuesta correcta es la b."
    assert resultado.modelo.letra == "b"


def test_la_misma_letra_escrita_de_otra_forma_es_la_misma_letra() -> None:
    """`A.` y `a` son la misma respuesta: tratarlas como distintas dejaría fuera preguntas.

    La comparación es la del motor de claves (`normalizar_letra`: sin espacios, sin punto y en
    minúscula) y **no** una nueva: dos formas de comparar una letra serían dos verdades sobre si una
    pregunta se puede derivar.
    """
    assert coinciden(_apuntes("A."), _modelo("a"))
    assert coinciden(_apuntes(" b "), _modelo("B"))


def test_una_respuesta_vacia_no_coincide_con_nada() -> None:
    """Un modelo que dice «no lo sé» no sostiene ninguna letra: la pregunta se queda fuera."""
    assert not coinciden(_apuntes("a"), _modelo(None))
    assert not coinciden(_apuntes(""), _modelo(""))


# --- los tres motivos, en el orden del informe ----------------------------------------------------


def test_sin_material_cuando_los_apuntes_no_han_mirado_la_pregunta() -> None:
    assert derivar(None, _modelo("b")) is MotivoDeFuera.SIN_MATERIAL


def test_sin_material_cuando_el_ancla_no_trae_letra() -> None:
    assert derivar(_apuntes(letra=None, cita=None), _modelo("b")) is MotivoDeFuera.SIN_MATERIAL


def test_sin_cita_cuando_los_apuntes_dan_una_letra_pero_no_la_sostienen() -> None:
    """Una letra sin la frase que la sostiene no es una fuente: es una opinión."""
    assert derivar(_apuntes("b", cita=None), _modelo("b")) is MotivoDeFuera.SIN_CITA


def test_sin_coincidencia_cuando_las_dos_fuentes_no_dicen_lo_mismo() -> None:
    """Es el caso que va al propietario: aquí no decide una regla."""
    assert derivar(_apuntes("b"), _modelo("c")) is MotivoDeFuera.SIN_COINCIDENCIA


def test_el_orden_de_los_motivos_no_se_cambia() -> None:
    """Una pregunta **sin material** no puede salir «sin coincidencia» aunque el modelo conteste.

    Es lo que decide a quién se le echa la culpa: a los apuntes (falta material) o al propietario
    (las dos fuentes hablan y no coinciden).
    """
    assert derivar(None, _modelo("b")) is MotivoDeFuera.SIN_MATERIAL
    assert derivar(_apuntes("b", cita=None), _modelo("c")) is MotivoDeFuera.SIN_CITA


# --- las claves oficiales no se derivan -----------------------------------------------------------


def test_un_examen_oficial_no_se_deriva() -> None:
    motivo = protege_derivar(
        set_type="official_exam", tiene_plantilla_enlazada=False, origin_scope="age"
    )

    assert motivo is not None
    assert "examen oficial" in motivo


def test_una_plantilla_enlazada_a_un_documento_no_se_deriva() -> None:
    motivo = protege_derivar(
        set_type="private_bank", tiene_plantilla_enlazada=True, origin_scope="desconocida"
    )

    assert motivo is not None
    assert "documento" in motivo


def test_un_ejercicio_de_la_age_con_su_respuesta_publicada_no_se_deriva() -> None:
    """Tercer camino: `private_bank`, sin plantilla enlazada, pero de la AGE con clave publicada."""
    motivo = protege_derivar(
        set_type="private_bank", tiene_plantilla_enlazada=False, origin_scope="age"
    )

    assert motivo is not None
    assert "Administración General del Estado" in motivo


def test_un_banco_privado_corriente_si_se_deriva() -> None:
    assert (
        protege_derivar(
            set_type="private_bank", tiene_plantilla_enlazada=False, origin_scope="desconocida"
        )
        is None
    )


# --- la decision por conjunto, con su cifra -------------------------------------------------------


def _decision(preguntas: int, con_clave: int, *, derivadas: int = 0) -> DecisionDeConjunto:
    return DecisionDeConjunto(
        set_id="s1",
        set_title="TEST VARIOS",
        preguntas=preguntas,
        con_clave=con_clave,
        derivadas=derivadas,
        corroboradas=con_clave - derivadas,
    )


def test_el_liston_es_el_90_por_cien_y_es_inclusivo() -> None:
    assert UMBRAL_VUELVE_A_LOS_TESTS == 0.90
    assert _decision(100, 90).vuelve_a_los_tests, "el 90 % exacto vuelve"
    assert not _decision(100, 89).vuelve_a_los_tests, "con 89 no"


def test_la_decision_dice_cuantas_faltan_para_el_liston() -> None:
    decision = _decision(100, 89)

    assert decision.para_el_liston() == 1
    assert "sigue fuera" in decision.linea()
    assert "89/100 = 89.0 %" in decision.linea()


def test_la_decision_dice_que_vuelve_cuando_llega() -> None:
    decision = _decision(10, 9)

    assert decision.vuelve_a_los_tests
    assert "VUELVE" in decision.linea()
    assert decision.fuera == 1


def test_un_conjunto_sin_preguntas_no_vuelve_a_los_tests() -> None:
    """Un conjunto sin preguntas no tiene nada que devolver: no se declara ganador por 0 de 0."""
    assert not _decision(0, 0).vuelve_a_los_tests


def test_decidir_conjuntos_cuenta_derivadas_y_corroboradas_por_su_conjunto() -> None:
    decisiones = decidir_conjuntos(
        [("s1", "uno", 10), ("s2", "dos", 4)],
        derivadas=[("s1", "p1"), ("s1", "p2"), ("s2", "p3")],
        corroboradas=[("s1", "p4")],
    )

    por_id = {decision.set_id: decision for decision in decisiones}
    assert por_id["s1"].derivadas == 2
    assert por_id["s1"].corroboradas == 1
    assert por_id["s1"].con_clave == 3
    assert por_id["s1"].proporcion == pytest.approx(0.3)
    assert por_id["s2"].con_clave == 1
    assert not por_id["s2"].vuelve_a_los_tests


def test_decidir_conjuntos_ordena_por_lo_que_esta_mas_cerca_de_volver() -> None:
    decisiones = decidir_conjuntos(
        [("s1", "lejos", 10), ("s2", "cerca", 10)],
        derivadas=[("s2", f"p{i}") for i in range(9)],
        corroboradas=[],
    )

    assert [decision.set_id for decision in decisiones] == ["s2", "s1"]


# --- las palabras de la clave ---------------------------------------------------------------------


def test_la_clave_derivada_es_una_clave_y_lleva_su_marca() -> None:
    """`derived` es el nombre del estado, y **nunca** `active`: son dos palabras distintas."""
    assert KeyTrust.DERIVED.value == "derived"
    assert KeyTrust.DERIVED.es_una_clave
    assert KeyTrust.DERIVED.se_marca_al_alumno, "la clave derivada se le enseña al alumno"
    assert not KeyTrust.ACTIVE.se_marca_al_alumno
    assert not KeyTrust.NINGUNA.es_una_clave


def test_el_recuento_de_fuera_ordena_y_dice_el_motivo() -> None:
    recuentos = recuento_de_fuera(
        [
            MotivoDeFuera.SIN_MATERIAL,
            MotivoDeFuera.SIN_MATERIAL,
            MotivoDeFuera.SIN_COINCIDENCIA,
        ]
    )

    assert [(r.motivo, r.preguntas) for r in recuentos] == [
        (MotivoDeFuera.SIN_MATERIAL, 2),
        (MotivoDeFuera.SIN_COINCIDENCIA, 1),
    ]
    assert "sin_material" in recuentos[0].linea()
