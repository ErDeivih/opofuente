"""Tipos de la parte de PyMuPDF que usa OpoFuente.

PyMuPDF publica `py.typed` pero **sin anotaciones**: para mypy estricto, `pymupdf.open(...)`,
`document.load_page(...)` o `pixmap.set_rect(...)` son llamadas a funciones sin tipos
(`no-untyped-call`). La salida fácil era apagar esa comprobación en los módulos afectados
(`disallow_untyped_calls = false`), y eso es relajar la puerta de calidad: el día que un extractor
llamara a PyMuPDF con un argumento equivocado, mypy no diría nada.

En su lugar se declara aquí **lo que el proyecto usa de verdad**, con su firma real. Este directorio
está en `mypy_path` (`pyproject.toml`), así que mypy ve estos tipos y en ejecución se importa el
PyMuPDF real. Si algún día se usa una función que no está declarada, mypy lo dirá: es exactamente lo
que se quiere.
"""

from __future__ import annotations

from collections.abc import Iterator
from os import PathLike
from typing import IO, Any

__version__: str

class FileDataError(RuntimeError): ...
class EmptyFileError(FileDataError): ...

class Colorspace:
    name: str
    n: int

class Rect:
    x0: float
    y0: float
    x1: float
    y1: float
    width: float
    height: float
    def __init__(self, *args: float) -> None: ...

class IRect:
    x0: int
    y0: int
    x1: int
    y1: int
    width: int
    height: int
    def __init__(self, *args: int) -> None: ...

class Point:
    x: float
    y: float
    def __init__(self, x: float = ..., y: float = ...) -> None: ...

class Matrix:
    def __init__(self, *args: float) -> None: ...

class Pixmap:
    width: int
    height: int
    n: int
    alpha: int
    colorspace: Colorspace
    irect: IRect
    samples: bytes
    def __init__(
        self,
        *args: Any,
        colorspace: Colorspace = ...,
        alpha: bool = ...,
        source: Any = ...,
    ) -> None: ...
    # El segundo parámetro se llama `colorspace` en la biblioteca real, pero acepta un color suelto
    # (`(255, 0, 0)`) además de un espacio de color con nombre: la firma lo refleja.
    def set_rect(
        self,
        irect: IRect,
        colorspace: Colorspace | tuple[int, ...] | tuple[float, ...],
        alpha: int = ...,
    ) -> None: ...
    def tobytes(self, output: str = ..., *args: Any) -> bytes: ...
    def save(self, filename: str | PathLike[str], *args: Any, **kwargs: Any) -> None: ...

class Page:
    number: int
    rect: Rect
    def get_text(self, option: str = ..., *args: Any, **kwargs: Any) -> str: ...
    def get_pixmap(self, *args: Any, **kwargs: Any) -> Pixmap: ...
    def insert_text(
        self,
        point: Point | tuple[float, float],
        text: str,
        *,
        fontsize: float = ...,
        fontname: str = ...,
        **kwargs: Any,
    ) -> int: ...
    def insert_image(
        self,
        rect: Rect,
        *,
        stream: bytes | None = ...,
        filename: str | None = ...,
        **kwargs: Any,
    ) -> None: ...

class Document:
    page_count: int
    metadata: dict[str, str] | None
    is_pdf: bool
    def __init__(
        self,
        filename: str | PathLike[str] | bytes | None = ...,
        stream: bytes | None = ...,
        filetype: str | None = ...,
        **kwargs: Any,
    ) -> None: ...
    def load_page(self, page_id: int) -> Page: ...
    def new_page(self, *args: Any, **kwargs: Any) -> Page: ...
    def close(self) -> None: ...
    def save(
        self,
        filename: str | PathLike[str] | IO[bytes],
        *args: Any,
        **kwargs: Any,
    ) -> None: ...
    def __iter__(self) -> Iterator[Page]: ...
    def __len__(self) -> int: ...
    def __getitem__(self, item: int) -> Page: ...
    def __enter__(self) -> Document: ...
    def __exit__(self, *args: object) -> None: ...

def open(
    filename: str | PathLike[str] | bytes | None = ...,
    *args: Any,
    **kwargs: Any,
) -> Document: ...
def new_document(*args: Any, **kwargs: Any) -> Document: ...
