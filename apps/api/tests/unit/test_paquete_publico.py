"""La prueba del paquete publico: que no se lleve a nadie (M8).

**Lo que se prueba aqui es lo unico del exportador que puede hacer dano**:
**que un paquete con datos de una persona se detecte antes de repartirlo.**

**Y se prueba sin base de datos**: `revisar` lee un fichero y decide, **y esa
decision es la que hay que poder afirmar sin montar nada**. **La ida y vuelta
—exportar, importar y volver a exportar— necesita la base y va en su propio
test de integracion.**
"""

from __future__ import annotations

import json
from pathlib import Path

from opofuente.tools.paquete_publico import FORMATO, revisar


def _paquete(ruta: Path, tablas: dict[str, list[dict[str, object]]]) -> Path:
    ruta.write_text(
        json.dumps(
            {"formato": FORMATO, "creado": "2026-10-22T00:00:00", "tablas": tablas},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return ruta


def test_un_paquete_solo_con_material_publico_pasa(tmp_path: Path) -> None:
    """El caso bueno: lo que viaja de verdad."""
    ruta = _paquete(
        tmp_path / "bueno.json",
        {
            "question_sets": [{"id": "s1", "distribution": "public"}],
            "question_explanations": [{"id": "e1", "origin": "generated"}],
        },
    )
    bien, problemas = revisar(ruta)
    assert bien is True
    assert problemas == ()


def test_una_explicacion_privada_tumba_el_paquete(tmp_path: Path) -> None:
    """**La que de verdad puede pasar**: el filtro de las explicaciones es una
    condicion, y una condicion mal puesta deja pasar once mil filas privadas."""
    ruta = _paquete(
        tmp_path / "con-privada.json",
        {"question_explanations": [{"id": "e1", "origin": "private"}]},
    )
    bien, problemas = revisar(ruta)
    assert bien is False
    assert "1 explicaciones privadas" in problemas[0]


def test_una_tabla_de_una_persona_tumba_el_paquete(tmp_path: Path) -> None:
    """Una tabla prohibida, **aunque sea una sola fila**."""
    ruta = _paquete(tmp_path / "con-usuarios.json", {"users": [{"id": "u1"}]})
    bien, problemas = revisar(ruta)
    assert bien is False
    assert "users" in problemas[0]


def test_una_tabla_prohibida_vacia_no_tumba_nada(tmp_path: Path) -> None:
    """**Una lista vacia no es material**: el exportador escribe las trece tablas
    aunque alguna venga a cero, y eso no puede dar el paquete por malo."""
    ruta = _paquete(tmp_path / "vacia.json", {"users": [], "cards": []})
    bien, _ = revisar(ruta)
    assert bien is True
