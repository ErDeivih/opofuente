"""El intento acotado de OCR de los cuestionarios de 2018 (remate, punto 7, decisión 3).

**Qué se prueba, lo que manda el documento**: **400 ppp, enderezado, binarizado, `--psm 4` y
cortar las dos columnas antes del OCR si las hay.** Se cuenta cuántas preguntas numeradas
salen y se compara con la plantilla. **Si no llega a 95 de 100, quedan fuera y no se insiste.**

**Sólo con `pymupdf`, que es lo que hay en el entorno**: no hay Pillow ni numpy, y añadirlos
para medir habría sido cambiar el proyecto para hacer una prueba.

- **400 ppp**: `get_pixmap(dpi=400)`.
- **Binarizado**: se pide en **escala de grises** (`csGRAY`); Tesseract binariza con Otsu de
  todas formas, y sin Pillow no hay un Otsu propio que valga la pena.
- **Enderezado**: `page.set_rotation` y **se elige el ángulo por resultado** —el que saca más
  números de pregunta en la primera página—, no por una estimación que no se puede comprobar.
- **Columnas**: se renderiza **por mitades con `clip`** cuando la página las tiene; si no,
  entera. **Cortar una página de una columna por la mitad partiría cada pregunta en dos.**

**No importa nada y no escribe en la base**: mide y dice la cifra.

**Uso**:

```
uv run python medir-ocr-2018.py
```
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

import pymupdf

FUENTES = Path(r"F:\OpoFuente\fuentes\inap-tai")
TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
TESSDATA = Path(r"F:\OpoFuente\ocr\tessdata")

#: Los cuestionarios y cuántas preguntas tiene su plantilla.
CASOS = {
    "TAI-2018-libre-cuestionario-1.pdf": 100,
    "TAI-2018-libre-cuestionario-2.pdf": 100,
    "TAI-2018-pi-cuestionario-unico.pdf": 100,
}

#: El número de pregunta al principio de una línea: `1.`, `12.`, `7.-`.
_NUMERO = re.compile(r"^\s*(\d{1,3})\s*[.\-)]\s")

#: Los ángulos que se prueban: pocos y pequeños —un escaneo torcido no gira treinta grados—.
_ANGULOS = (-2, -1, 0, 1, 2)


def _ocr(pagina: pymupdf.Page, recorte: pymupdf.Rect | None, carpeta: Path) -> str:
    pixeles = pagina.get_pixmap(dpi=400, clip=recorte, colorspace=pymupdf.csGRAY)
    ruta = carpeta / "recorte.png"
    pixeles.save(ruta)
    # **La misma excepción que usa el OCR del proyecto** (`ocr.py`): el comando se construye
    # con rutas de configuración, no con nada que venga de fuera.
    resultado = subprocess.run(  # noqa: S603 - comando construido con rutas de configuración
        [
            str(TESSERACT),
            str(ruta),
            "stdout",
            "-l",
            "spa",
            "--psm",
            "4",
            "--tessdata-dir",
            str(TESSDATA),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    return resultado.stdout


def _numeros(texto: str) -> set[int]:
    """Los números de pregunta que el OCR ha puesto al principio de una línea."""
    vistos: set[int] = set()
    for linea in texto.splitlines():
        encontrado = _NUMERO.match(linea)
        if encontrado:
            numero = int(encontrado.group(1))
            if 1 <= numero <= 120:
                vistos.add(numero)
    return vistos


def _dos_columnas(pagina: pymupdf.Page, carpeta: Path) -> bool:
    """¿La página va a dos columnas? **Se decide mirando si el centro está vacío.**

    Se OCRiza la franja central estrecha: si **no sale ningún número de pregunta**, el centro
    es un hueco de separación y la página es a dos columnas. Una de una columna tiene texto
    cruzando el centro, y ahí sí aparecen números.
    """
    ancho, alto = pagina.rect.width, pagina.rect.height
    centro = pymupdf.Rect(ancho * 0.44, 0, ancho * 0.56, alto)
    return not _numeros(_ocr(pagina, centro, carpeta))


def main() -> int:
    total = 0
    for nombre, esperadas in CASOS.items():
        ruta = FUENTES / nombre
        if not ruta.is_file():
            print(f"  {nombre}: no está")
            continue
        documento = pymupdf.open(ruta)
        vistos: set[int] = set()
        with tempfile.TemporaryDirectory(prefix="ocr-2018-") as carpeta_base:
            carpeta = Path(carpeta_base)

            # **El ángulo se elige por resultado**, en la primera página: el que más números saca.
            primera = documento.load_page(0)
            mejor_angulo, mejor_cuenta = 0, -1
            for angulo in _ANGULOS:
                primera.set_rotation(angulo)
                cuenta = len(_numeros(_ocr(primera, None, carpeta)))
                if cuenta > mejor_cuenta:
                    mejor_angulo, mejor_cuenta = angulo, cuenta
            print(f"  {nombre}: enderezado a {mejor_angulo} ({mejor_cuenta} en la 1)")

            for numero in range(documento.page_count):
                pagina = documento.load_page(numero)
                pagina.set_rotation(mejor_angulo)
                if _dos_columnas(pagina, carpeta):
                    ancho = pagina.rect.width
                    izquierda = pymupdf.Rect(0, 0, ancho * 0.52, pagina.rect.height)
                    derecha = pymupdf.Rect(ancho * 0.48, 0, ancho, pagina.rect.height)
                    vistos |= _numeros(_ocr(pagina, izquierda, carpeta))
                    vistos |= _numeros(_ocr(pagina, derecha, carpeta))
                else:
                    vistos |= _numeros(_ocr(pagina, None, carpeta))
        documento.close()
        encontradas = len([n for n in vistos if 1 <= n <= esperadas])
        total += encontradas
        print(f"  {nombre}: {encontradas} de {esperadas}")
    print(f"  total: {total} de {sum(CASOS.values())}")
    print("  QUEDAN FUERA" if total < 95 else "  LLEGAN AL LISTON")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
