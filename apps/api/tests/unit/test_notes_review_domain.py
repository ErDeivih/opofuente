"""El motivo de un borrador y la decisión sobre él: dominio puro, sin base de datos (F24).

Lo que se prueba aquí es lo que el propietario **lee** en el panel y lo que el sistema guarda:

1. **cada motivo con su cifra**, y con la cifra buena: el caso que decide es el de un tema que
   cumple las dos puertas y no está publicado (I.4 medido el 14 de octubre de 2026:
   489/542 = 90,2 %), que tiene que decir eso y no «le falta cobertura»;
2. **cuántas preguntas le faltan**, contadas con enteros: `0,9 por 10` en coma flotante da
   9,000000000000002 y su techo diría 10 donde el listón pide 9. Una cifra que se le enseña al
   propietario no puede fallar por un decimal;
3. **nada de cifras inventadas**: un tema que la tabla no ha medido **no** lleva cifra de puerta (un
   «0/0 = 0,0 %» se leería como «cero preguntas cubiertas»);
4. **rechazar exige motivo**, y es un error de entrada (`InvalidReviewError`, que la API traduce a
   422 con su campo) y no un `ValueError` cualquiera, que acabaría en un 500;
5. **el rechazo no esconde el motivo de datos**: el titular pasa a ser «lo rechazaste, y por esto» y
   debajo sigue el desglose con sus cifras.
"""

from __future__ import annotations

import pytest

from opofuente.domain.errors import InvalidReviewError
from opofuente.domain.notes_review import (
    UMBRAL_TEXTO,
    CifrasDelTema,
    MotivoDelBorrador,
    ReviewDecision,
    normalise_decision_note,
    razones_del_tema,
)
from opofuente.domain.topic_notes import CategoriaIncidencia


def _cifras(**campos: object) -> CifrasDelTema:
    """Unas cifras de partida: un borrador medido, con una cobertura que no llega al listón."""
    base: dict[str, object] = {
        "has_sections": True,
        "published": False,
        "measured": True,
        "covered": 40,
        "with_key": 100,
        "covered_all_keys": 40,
        "with_key_all_keys": 120,
        "form_passes": True,
    }
    return CifrasDelTema(**(base | campos))  # type: ignore[arg-type]


def _codigos(cifras: CifrasDelTema) -> list[MotivoDelBorrador]:
    return [razon.code for razon in razones_del_tema(cifras)]


def _razon(cifras: CifrasDelTema, code: MotivoDelBorrador):  # type: ignore[no-untyped-def]
    for razon in razones_del_tema(cifras):
        if razon.code is code:
            return razon
    raise AssertionError(f"no hay ninguna razón «{code.value}» en {_codigos(cifras)}")


class TestElMotivoDeUnBorrador:
    def test_un_tema_que_cumple_las_puertas_y_no_esta_publicado_lo_dice_con_su_cifra(
        self,
    ) -> None:
        """El caso de I.4: no le falta nada, es que nadie ha archivado su versión."""
        cifras = _cifras(covered=489, with_key=542)

        razon = _razon(cifras, MotivoDelBorrador.A_LAS_PUERTAS)

        assert razon.figure == "489/542 = 90,2 %"
        assert "Cumple las dos puertas" in razon.text
        assert "Aprobarlo la publica" in razon.text
        # Y **no** dice que le falte cobertura: sería mentira.
        assert MotivoDelBorrador.COBERTURA not in _codigos(cifras)

    def test_un_tema_que_no_llega_dice_cuantas_le_faltan_y_cual_es_el_liston(self) -> None:
        razon = _razon(_cifras(covered=40, with_key=100), MotivoDelBorrador.COBERTURA)

        # El §2.2 alcanza también a la prosa del servidor: la cifra va con **coma**. Esta aserción
        # esperaba `40.0 %`, el formato viejo —el punto del decimal—, que es el mismo defecto que el
        # propietario vio en su captura.
        assert razon.figure == "40/100 = 40,0 %"
        assert "le faltan 50 preguntas cubiertas" in razon.text
        assert UMBRAL_TEXTO in razon.text

    @pytest.mark.parametrize(
        ("cubiertas", "con_clave", "esperadas"),
        [
            (8, 10, 1),  # el techo de 0,9 x 10 es 9, no 10: en coma flotante sí sería 10
            (0, 10, 9),
            (89, 100, 1),
            (9, 10, 0),  # justo en el listón: no le falta ninguna
            (0, 0, 0),  # sin preguntas con clave no se inventa una cifra
        ],
    )
    def test_las_que_faltan_se_cuentan_con_enteros(
        self, cubiertas: int, con_clave: int, esperadas: int
    ) -> None:
        cifras = _cifras(covered=cubiertas, with_key=con_clave)

        assert cifras.le_faltan == esperadas
        assert cifras.pasa_cobertura is (con_clave > 0 and cubiertas / con_clave >= 0.9)

    def test_sin_medir_no_se_ensena_una_cifra_de_puerta(self) -> None:
        """Un tema publicado que la tabla no mide no lleva cifra: un «0/0» sería una mentira."""
        cifras = _cifras(published=True, measured=False, covered=0, with_key=0)

        razon = _razon(cifras, MotivoDelBorrador.PUBLICADO)

        assert razon.figure is None
        assert "publicado" in razon.text

    def test_un_tema_sin_preguntas_comprobables_lo_dice_en_vez_de_un_cero(self) -> None:
        """Medido, con apartados y sin ninguna pregunta con la que comprobar: la puerta no pasa."""
        cifras = _cifras(covered=0, with_key=0, covered_all_keys=0, with_key_all_keys=0)

        razon = _razon(cifras, MotivoDelBorrador.COBERTURA)

        assert razon.figure is None
        assert "no hay ninguna pregunta con respuesta correcta utilizable" in razon.text
        assert cifras.pasa_cobertura is False

    def test_un_tema_publicado_no_dice_que_nadie_lo_ha_revisado(self) -> None:
        cifras = _cifras(published=True)

        assert MotivoDelBorrador.SIN_DECISION not in _codigos(cifras)
        assert MotivoDelBorrador.PUBLICADO in _codigos(cifras)

    def test_un_tema_sin_apartados_lo_dice_y_nada_mas(self) -> None:
        cifras = _cifras(has_sections=False, measured=False, covered=0, with_key=0)

        assert _codigos(cifras) == [MotivoDelBorrador.SIN_APARTADOS]

    def test_el_desglose_de_a_quien_le_toca_cada_parte_va_con_su_cifra(self) -> None:
        """Los cuatro motivos de datos y la bandeja, cada uno con su número y su nombre."""
        cifras = _cifras(
            covered=40,
            with_key=100,
            sin_frase=20,
            conflictos=19,
            claves_marcadas=10,
            sin_materia=2,
            incidencias_abiertas=63,
            incidencias_por_categoria=(
                (CategoriaIncidencia.CLAVE_SOSPECHOSA, 20),
                (CategoriaIncidencia.HUECO_SIN_MATERIAL, 20),
                (CategoriaIncidencia.NORMA_CAMBIADA, 20),
                (CategoriaIncidencia.PREGUNTA_AMBIGUA, 3),
            ),
        )

        # La cifra va en su forma: «20 preguntas», no «20 pregunta(s)». Y en singular también,
        # que era el defecto que se vio en pantalla: «1 pregunta(s) 1 preguntas no tienen…».
        assert _razon(cifras, MotivoDelBorrador.HUECOS).figure == "20 preguntas"
        assert _razon(cifras, MotivoDelBorrador.CONFLICTOS).figure == "19 preguntas"
        assert _razon(cifras, MotivoDelBorrador.CLAVES_EN_REVISION).figure == "10 preguntas"
        assert _razon(cifras, MotivoDelBorrador.SIN_MATERIA).figure == "2 preguntas"
        incidencias = _razon(cifras, MotivoDelBorrador.INCIDENCIAS)
        assert incidencias.figure == "63 incidencias"
        # El desglose va de mayor a menor, que es el orden en el que se trabaja la bandeja.
        assert incidencias.text.index("20 respuestas correctas") < incidencias.text.index(
            "3 preguntas que no se pueden juzgar"
        )

    def test_un_rechazo_es_el_titular_y_el_motivo_de_datos_sigue_debajo(self) -> None:
        cifras = _cifras(
            covered=40,
            with_key=100,
            decision=ReviewDecision.REJECTED,
            decision_note="Faltan 43 preguntas por contestar",
        )

        assert _codigos(cifras) == [
            MotivoDelBorrador.RECHAZADO,
            MotivoDelBorrador.COBERTURA,
        ]
        titular = _razon(cifras, MotivoDelBorrador.RECHAZADO)
        assert "Faltan 43 preguntas por contestar" in titular.text
        # Y no se vuelve a pedir una decisión que ya está tomada.
        assert MotivoDelBorrador.SIN_DECISION not in _codigos(cifras)

    def test_la_forma_rota_se_dice_con_lo_que_no_pasa(self) -> None:
        cifras = _cifras(
            covered=100,
            with_key=100,
            form_passes=False,
            form_failures=("hay 3 encabezado(s) repetido(s)",),
        )

        razon = _razon(cifras, MotivoDelBorrador.FORMA)
        assert "hay 3 encabezado(s) repetido(s)" in razon.text
        # Con la cobertura pasando y la forma rota, no se dice que cumpla las dos puertas.
        assert MotivoDelBorrador.A_LAS_PUERTAS not in _codigos(cifras)


class TestLaNotaDeLaDecision:
    def test_al_aprobar_la_nota_es_opcional(self) -> None:
        assert normalise_decision_note(ReviewDecision.APPROVED, None) is None
        assert normalise_decision_note(ReviewDecision.APPROVED, "  ") is None
        assert (
            normalise_decision_note(ReviewDecision.APPROVED, "  leído el 14  de octubre ")
            == "leído el 14 de octubre"
        )

    def test_rechazar_sin_motivo_no_pasa_y_se_sabe_que_campo_falta(self) -> None:
        for vacia in (None, "", "   ", "\n"):
            with pytest.raises(InvalidReviewError) as fallo:
                normalise_decision_note(ReviewDecision.REJECTED, vacia)
            assert fallo.value.field == "note"
            assert fallo.value.code == "invalid_review"

    def test_la_nota_de_un_rechazo_es_una_linea(self) -> None:
        limpia = normalise_decision_note(
            ReviewDecision.REJECTED, "  faltan 43 preguntas\n  por contestar  "
        )

        assert limpia == "faltan 43 preguntas por contestar"
