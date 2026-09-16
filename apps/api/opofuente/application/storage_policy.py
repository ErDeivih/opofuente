"""Política común de contenido antes de guardar en el almacén (04_INGESTION §2, 09_SECURITY §3).

Un mismo fichero puede llegar por cuatro vías —subida desde el navegador, descarga por URL, copia
desde una carpeta y miembro de un ZIP— y la regla de qué se admite es la misma en las cuatro: ni
ejecutables ni bibliotecas, se llamen como se llamen y digan lo que digan los bytes. Este módulo es
el único sitio donde se decide, para que ninguna vía se quede sin comprobar (antes solo lo hacía la
subida, así que un PE descargado por URL o un `.exe` renombrado en una carpeta sí llegaban al
almacén).

El texto pegado no pasa por aquí: lo escribe OpoFuente, no llega de fuera y no hay firma que
inspeccionar.
"""

from __future__ import annotations

from pathlib import Path

from opofuente.domain.formats import storage_refusal
from opofuente.infrastructure.extractors.base import read_head
from opofuente.infrastructure.safe_paths import safe_display_name


def refusal_message(
    *, name: str, head: bytes | None = None, path: Path | None = None
) -> str | None:
    """Motivo por el que este contenido no se admite, ya redactado, o `None` si se admite.

    `head` son los primeros bytes ya leídos (si se tienen) y `path` un fichero del que leerlos. Con
    los dos a `None` la comprobación es solo por el nombre, que es lo que interesa antes de escribir
    nada en disco.
    """
    datos = head or b""
    if not datos and path is not None:
        try:
            datos = read_head(path)
        except OSError:
            # Si no se puede leer la cabecera, la comprobación por nombre sigue en pie y la copia
            # fallará más adelante con su propio error.
            datos = b""
    motivo = storage_refusal(name=name, head=datos)
    if motivo is None:
        return None
    return f"el fichero {safe_display_name(name)!r} no se admite: {motivo}"


__all__ = ["refusal_message"]
