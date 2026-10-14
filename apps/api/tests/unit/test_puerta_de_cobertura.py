"""La puerta de cobertura del §2.3: dos denominadores, y el que decide es el de la clave utilizable.

No es una comprobación de forma: mide si los apuntes contestan a las preguntas. Y su número importa
tanto como su umbral: una pregunta cuya **respuesta marcada contradice la norma** no tiene una
respuesta con la que se pueda acertar, así que contarla en contra de los apuntes sería culpar al
texto de un fallo del banco. Por eso se miden los dos números:

- (a) cubiertas sobre **todas** las que tienen clave (activa o en borrador);
- (b) cubiertas sobre las que tienen clave **utilizable**, que es el que decide.

Antes de esto la puerta existía en el documento y no en el código, así que un tema con el 85 % podía
quedar archivado.
"""

from __future__ import annotations

from opofuente.application.topic_notes_models import CoverageReport
from opofuente.domain.topic_notes import COBERTURA_MINIMA, Coverage, Motivo


def _informe(
    *,
    cubiertas: int,
    dudosas: int,
    conflictos: int,
    marcadas: int,
    preguntas: int = 1,
    sin_clave: int = 0,
) -> CoverageReport:
    """Un recuento con los cinco desenlaces, contando `preguntas` por grupo."""
    informe = CoverageReport()
    for _ in range(cubiertas):
        informe.add(
            Coverage.CUBIERTA,
            None,
            attempts=1,
            clave_activa=False,
            preguntas=preguntas,
            clave_utilizable=True,
        )
    for _ in range(dudosas):
        informe.add(
            Coverage.DUDOSA,
            Motivo.SIN_FRASE_EN_LOS_APUNTES,
            attempts=3,
            clave_activa=False,
            preguntas=preguntas,
            clave_utilizable=True,
        )
    for _ in range(conflictos):
        informe.add(
            Coverage.CONFLICTO,
            Motivo.LETRA_NO_COINCIDE,
            attempts=2,
            clave_activa=False,
            preguntas=preguntas,
            clave_utilizable=True,
        )
    for _ in range(marcadas):
        # El paso B marcó la clave: queda fuera del denominador que decide, aunque cuente como duda.
        informe.add(
            Coverage.DUDOSA,
            Motivo.CLAVE_CONTRADICE_LA_NORMA,
            attempts=1,
            clave_activa=False,
            preguntas=preguntas,
            clave_utilizable=False,
        )
    for _ in range(sin_clave):
        informe.add(
            Coverage.CUBIERTA,
            None,
            attempts=1,
            clave_activa=False,
            preguntas=preguntas,
            tiene_clave=False,
        )
    return informe


def test_el_umbral_es_el_del_documento() -> None:
    assert COBERTURA_MINIMA == 0.90


def test_los_dos_denominadores_se_miden_y_dicen_lo_mismo_cuando_no_hay_claves_marcadas() -> None:
    informe = _informe(cubiertas=90, dudosas=8, conflictos=2, marcadas=0)

    assert informe.preguntas_con_clave == 100
    assert informe.cobertura_con_clave == 0.9
    assert informe.cobertura_con_clave_utilizable == 0.9
    assert informe.pasa_cobertura


def test_las_claves_marcadas_por_el_paso_b_no_cuentan_en_el_denominador_que_decide() -> None:
    """El caso de IV.7: 40 claves que contradicen la norma, fuera de la cuenta que decide."""
    informe = _informe(cubiertas=435, dudosas=35, conflictos=10, marcadas=40)

    # (a) todas las que tienen clave: 520
    assert informe.preguntas_con_clave == 520
    assert round(100 * informe.cobertura_con_clave, 1) == 83.7
    # (b) las que tienen clave utilizable: 480, y es la que decide
    assert informe.preguntas_con_clave_utilizable == 480
    assert round(100 * informe.cobertura_con_clave_utilizable, 1) == 90.6
    assert informe.pasa_cobertura, "con el denominador utilizable, IV.7 pasa"


def test_un_tema_por_debajo_del_umbral_no_pasa_la_puerta() -> None:
    """El caso de I.6: no llega con ninguno de los dos denominadores."""
    informe = _informe(cubiertas=125, dudosas=21, conflictos=45, marcadas=20)

    assert not informe.pasa_cobertura
    assert round(100 * informe.cobertura_con_clave_utilizable, 1) < 90


def test_la_puerta_esta_en_la_frontera() -> None:
    """89,99 % no pasa y 90 % sí: el umbral no se redondea a favor."""
    justo = _informe(cubiertas=90, dudosas=10, conflictos=0, marcadas=0)
    casi = _informe(cubiertas=89, dudosas=11, conflictos=0, marcadas=0)

    assert justo.pasa_cobertura
    assert not casi.pasa_cobertura


def test_la_puerta_se_mide_aunque_el_tema_quede_en_borrador() -> None:
    """«Deja la puerta medida aunque el tema esté en borrador»: el número siempre está."""
    informe = _informe(cubiertas=1, dudosas=99, conflictos=0, marcadas=0)

    assert informe.preguntas_con_clave == 100
    assert informe.cobertura_con_clave_utilizable == 0.01
    assert not informe.pasa_cobertura


def test_se_cuenta_pregunta_a_pregunta_y_no_grupo_a_grupo() -> None:
    """Una pregunta repetida en dos bancos cuenta dos veces: el §2.3 habla de preguntas."""
    informe = _informe(cubiertas=1, dudosas=0, conflictos=0, marcadas=0, preguntas=3)

    assert informe.covered == 1, "un grupo"
    assert informe.preguntas_cubiertas_con_clave == 3, "tres preguntas"
    assert informe.preguntas_con_clave == 3


def test_las_preguntas_sin_clave_no_entran_en_la_puerta() -> None:
    """Sin clave no hay letra con la que acertar: se cuentan aparte, no en el denominador."""
    informe = _informe(cubiertas=10, dudosas=0, conflictos=0, marcadas=0, sin_clave=5)

    assert informe.preguntas_con_clave == 10
    assert informe.preguntas_con_clave_utilizable == 10
    assert informe.covered == 15, "las cinco sin clave sí se cuentan como cubiertas"
    assert informe.pasa_cobertura
