"""Pruebas unitarias de las rutas seguras y del saneado de mensajes.

La regla que se comprueba: la ruta real del usuario no sale de aquí. Ni la de la carpeta elegida
(`abbreviate`) ni la que trae el texto de una excepción de terceros (`redact_paths`).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from opofuente.infrastructure.safe_paths import (
    PathOutsideRootError,
    abbreviate,
    is_within,
    redact_paths,
    relative_display,
    resolve_within,
    safe_display_name,
)
from opofuente.workers.job_worker import _safe_message

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


def test_abbreviate_nunca_devuelve_la_raiz() -> None:
    """Regresión: `abbreviate(C:\\Material)` devolvía la ruta entera."""
    abreviada = abbreviate(Path("C:/Material"))
    assert abreviada == "…/Material"
    assert "C:" not in abreviada


def test_abbreviate_conserva_los_ultimos_componentes() -> None:
    abreviada = abbreviate(Path("C:/Users/David/Documentos/oposiciones/tema-01.pdf"))
    assert abreviada == "…/oposiciones/tema-01.pdf"
    assert "David" not in abreviada
    assert "Users" not in abreviada


def test_abbreviate_con_una_raiz_suelta() -> None:
    assert abbreviate(Path("C:/")) == "…"


def test_redact_paths_quita_las_rutas_de_un_error_real() -> None:
    """Regresión: un `PermissionError` publicaba la carpeta del usuario en `jobs.error_message`."""
    error = PermissionError(13, "Permission denied", r"C:\Users\David\Documentos\secreto.pdf")

    limpio = redact_paths(str(error))

    assert "David" not in limpio
    assert "C:" not in limpio
    assert "…/secreto.pdf" in limpio


def test_redact_paths_cubre_unc_y_varias_rutas() -> None:
    texto = r"no se pudo copiar \\servidor\recurso\privado.docx ni D:\material\tema.docx"

    limpio = redact_paths(texto)

    assert "servidor" not in limpio
    assert "D:" not in limpio
    assert "…/privado.docx" in limpio
    assert "…/tema.docx" in limpio


def test_redact_paths_deja_intacto_lo_que_no_es_una_ruta() -> None:
    assert redact_paths("no hay espacio en el disco") == "no hay espacio en el disco"


def test_safe_message_no_publica_la_ruta_del_fichero(tmp_path: Path) -> None:
    """El mensaje que se guarda y se publica por la API tampoco lleva la ruta.

    Se construyen los errores como los produce Windows de verdad (`PermissionError` con la ruta
    completa en el texto), que es justo lo que llegaba a `jobs.error_message`.
    """
    privado = tmp_path / "Documentos-de-David" / "secreto.pdf"

    mensaje = _safe_message(
        PermissionError(13, "Permission denied", str(privado).replace("/", "\\"))
    )

    assert str(tmp_path) not in mensaje
    assert "David" not in mensaje
    assert "…/secreto.pdf" in mensaje


def test_safe_message_acota_la_longitud() -> None:
    mensaje = _safe_message(RuntimeError("x" * 500))
    assert len(mensaje) == 201
    assert mensaje.endswith("…")


def test_relative_display_no_incluye_la_raiz(tmp_path: Path) -> None:
    dentro = tmp_path / "apuntes" / "ley.md"
    assert relative_display(tmp_path, dentro) == "apuntes/ley.md"
    fuera = tmp_path.parent / "otra" / "x.md"
    assert str(tmp_path) not in relative_display(tmp_path, fuera)


def test_resolve_within_bloquea_lo_que_sale_de_la_raiz(tmp_path: Path) -> None:
    root = tmp_path / "datos"
    root.mkdir()
    with pytest.raises(PathOutsideRootError):
        resolve_within(root, tmp_path / "fuera.txt")
    assert is_within(root, root / "dentro.txt")


def test_safe_display_name_quita_separadores_y_reservados() -> None:
    traversal = safe_display_name("../../etc/passwd")
    assert "/" not in traversal
    assert "\\" not in traversal
    assert traversal.endswith("etc_passwd")
    assert safe_display_name("CON") == "_CON"
    assert safe_display_name("   ") == "sin-nombre"
