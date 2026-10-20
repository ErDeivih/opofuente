"""La cola del día: entrelaza tarjetas y fallos y respeta el tope (M3 de la fase 3)."""

from __future__ import annotations

import pytest

from opofuente.domain.cola_del_dia import TipoDeEntrada, cola_del_dia


def test_mezcla_tarjetas_y_fallos() -> None:
    cola = cola_del_dia(["t1", "t2"], ["f1"], tope=60)
    assert [e.tipo for e in cola] == [
        TipoDeEntrada.TARJETA,
        TipoDeEntrada.FALLO,
        TipoDeEntrada.TARJETA,
    ]
    assert [e.id for e in cola] == ["t1", "f1", "t2"]


def test_el_tope_recorta_la_mezcla_y_no_una_de_las_dos_listas() -> None:
    cola = cola_del_dia(["t1", "t2", "t3"], ["f1", "f2"], tope=4)
    assert len(cola) == 4
    # Los dos fallos entran aunque haya más tarjetas: van los primeros de la mezcla.
    assert {e.tipo for e in cola} == {TipoDeEntrada.TARJETA, TipoDeEntrada.FALLO}


def test_si_sobra_una_lista_la_otra_se_agota_primero() -> None:
    cola = cola_del_dia(["t1"], ["f1", "f2", "f3"], tope=60)
    assert len(cola) == 4
    assert cola[0].tipo == TipoDeEntrada.TARJETA
    assert cola[1].tipo == TipoDeEntrada.FALLO


def test_sin_nada_no_hay_cola() -> None:
    assert cola_del_dia([], [], tope=60) == ()


def test_un_tope_de_cero_no_vale() -> None:
    with pytest.raises(ValueError):
        cola_del_dia(["t1"], [], tope=0)
