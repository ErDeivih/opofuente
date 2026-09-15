"""Ayudantes compartidos por las pruebas de OpoFuente (no forma parte de la aplicación).

Antes vivían dentro de `apps/api/tests` y esa carpeta tenía que estar en `pythonpath` para que las
pruebas de unitarias y las de integración compartieran los constructores de documentos sintéticos.
Eso hacía que `pythonpath` incluyera una carpeta de pruebas (lo que puede tapar importaciones mal
escritas) y que el paquete no se comprobara con mypy estricto.

Ahora es un paquete normal, importable desde `apps/api` (que ya está en `pythonpath`), tipado y
comprobado como el resto del código:

- `synthetic_documents`: construye los documentos de prueba (PDF, DOCX, HTML, CSV, JSON, ZIP…);
- `jobs`: reloj fijo, ejecución de trabajo falsa y ejecución del worker real sobre la app de prueba.
"""

from __future__ import annotations

__all__ = ["jobs", "synthetic_documents"]
