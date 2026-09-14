"""OpoFuente — backend local.

Aplicación local-first para organizar y estudiar material de oposiciones (TAI y Guardia
Civil). Especificación: `docs/product-spec`.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("opofuente")
except PackageNotFoundError:  # copia de trabajo sin instalar el paquete
    __version__ = "0.0.0+source"

__all__ = ["__version__"]
