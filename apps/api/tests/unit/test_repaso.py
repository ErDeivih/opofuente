"""SM-2 escrito en el dominio: los intervalos que promete el artículo (M3 de la fase 3)."""

from __future__ import annotations

from opofuente.domain.repaso import FACTOR_MINIMO, EstadoDeRepaso, Respuesta, repasar


def test_los_dos_primeros_intervalos_son_uno_y_seis() -> None:
    estado = EstadoDeRepaso()
    estado = repasar(estado, Respuesta.BIEN)
    assert estado.intervalo_dias == 1
    estado = repasar(estado, Respuesta.BIEN)
    assert estado.intervalo_dias == 6


def test_el_tercero_crece_por_el_factor() -> None:
    estado = EstadoDeRepaso()
    estado = repasar(estado, Respuesta.BIEN)
    estado = repasar(estado, Respuesta.BIEN)
    tercero = repasar(estado, Respuesta.BIEN)
    assert tercero.intervalo_dias > 6


def test_suspender_vuelve_a_empezar() -> None:
    estado = EstadoDeRepaso()
    for _ in range(3):
        estado = repasar(estado, Respuesta.BIEN)
    fallada = repasar(estado, Respuesta.OTRA_VEZ)
    assert fallada.intervalo_dias == 1
    assert fallada.aciertos_seguidos == 0


def test_el_factor_no_baja_del_minimo() -> None:
    estado = EstadoDeRepaso()
    for _ in range(20):
        estado = repasar(estado, Respuesta.OTRA_VEZ)
    assert estado.factor >= FACTOR_MINIMO


def test_facil_sube_el_factor_y_dificil_lo_baja() -> None:
    base = EstadoDeRepaso()
    assert repasar(base, Respuesta.FACIL).factor > base.factor
    assert repasar(base, Respuesta.DIFICIL).factor < base.factor
