"""Pruebas unitarias de la detección de índice incompleto (DEBT-015).

El caso «faltan fragmentos» **no se puede simular desde SQL**: `evidence_fts` es una tabla FTS5 de
contenido externo, así que un `DELETE` no la vacía y `delete-all` tampoco (comprobado con SQLite
real). Por eso el descuadre se simula aquí, con un doble del repositorio que devuelve números
distintos: es la forma honesta de probar la rama que decide si ofrecer la reparación.
"""

from __future__ import annotations

from opofuente.application.search_service import SearchService


class _RepositorioDoble:
    """Doble del repositorio de búsqueda que solo sabe contestar a los dos recuentos."""

    def __init__(self, *, en_indice: int, en_tabla: int) -> None:
        self._en_indice = en_indice
        self._en_tabla = en_tabla
        self.rebuilds = 0

    def indexed_count(self) -> int:
        return self._en_indice

    def indexed_spans(self) -> int:
        return self._en_tabla

    def rebuild_index(self) -> int:
        self.rebuilds += 1
        self._en_indice = self._en_tabla
        return self._en_tabla

    # Del resto del contrato del repositorio no se usa nada más en estas pruebas.
    def __getattr__(self, name: str) -> object:  # pragma: no cover - el doble no lo necesita
        raise AssertionError(f"el doble no implementa {name}")


def _servicio(repositorio: _RepositorioDoble) -> SearchService:
    return SearchService(
        search=repositorio,  # type: ignore[arg-type]
        clock=lambda: None,  # type: ignore[arg-type,return-value]
    )


def test_un_indice_completo_se_declara_completo_con_su_recuento() -> None:
    servicio = _servicio(_RepositorioDoble(en_indice=12, en_tabla=12))

    sano, detalle, faltan = servicio.index_health()

    assert sano is True
    assert faltan == 0
    assert "12 fragmentos" in detalle


def test_un_indice_al_que_le_faltan_fragmentos_lo_dice_con_la_cifra() -> None:
    """Es el caso que justifica la acción de Ajustes: el índice se ha quedado atrás."""
    servicio = _servicio(_RepositorioDoble(en_indice=10, en_tabla=17))

    sano, detalle, faltan = servicio.index_health()

    assert sano is False
    assert faltan == 7
    assert "10 de 17" in detalle
    assert "rehaciéndolo" in detalle


def test_rehacer_el_indice_cuenta_antes_y_despues() -> None:
    repositorio = _RepositorioDoble(en_indice=4, en_tabla=9)

    informe = _servicio(repositorio).reindex()

    assert informe.before == 4
    assert informe.after == 9
    assert informe.indexed == 9
    assert informe.took_seconds >= 0
    assert repositorio.rebuilds == 1


def test_rehacer_el_indice_vacio_lo_dice_sin_fingir_trabajo() -> None:
    informe = _servicio(_RepositorioDoble(en_indice=0, en_tabla=0)).reindex()

    assert informe.indexed == 0
    assert "no hay fragmentos" in informe.detail
