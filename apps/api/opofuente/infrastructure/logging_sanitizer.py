"""Saneado de una línea de registro (09_SECURITY §9 y §12).

Los logs ya se escriben con lista blanca de campos (`JsonFormatter`), así que hoy ninguna línea
lleva
contenido de documentos ni claves. Este módulo existe para lo que **no** puede garantizar el
formateador: una línea que venga de otra fuente (una excepción serializada, una línea escrita a
mano,
un mensaje de una biblioteca) y que se enseñe al usuario en el diagnóstico. Antes de salir de la
aplicación se pasa por aquí.

Qué se hace con una línea:

1. **se redactan los valores con pinta de secreto** (`api_key`, `token`, `password`,
`authorization`…),
   conservando la clave para que se vea que había algo y que se ha quitado;
2. **se abrevian las rutas absolutas** de Windows y POSIX: una ruta de disco publica el nombre del
   usuario, y en un informe que se pega en una incidencia eso no tiene por qué ir;
3. **se recorta** la longitud, porque un diagnóstico no es un volcado.

Lo que este módulo **no** hace es adivinar contenido: no puede saber si una frase es una pregunta
privada. Por eso el registro se escribe sin contenido y esta es la segunda red, no la primera.
"""

from __future__ import annotations

import re

#: Etiquetas cuyo valor es un secreto. Se conserva la etiqueta y se sustituye el valor.
_SECRET_KEYS = (
    "api[_-]?key",
    "apikey",
    "authorization",
    "bearer",
    "clave",
    "password",
    "passwd",
    "secret",
    "token",
)

#: `clave=valor`, `clave: valor`, `"clave": "valor"`. El valor puede ir entre comillas o suelto.
_SECRET_PATTERN = re.compile(
    r"""(?i)\b(""" + "|".join(_SECRET_KEYS) + r""")\b("?\s*[:=]\s*)("?)([^\s",;]{1,200})\3""",
)

#: Rutas absolutas de Windows (`F:\...`) y POSIX (`/home/...`, `/Users/...`) dentro de un texto.
_WINDOWS_PATH = re.compile(r"\b[A-Za-z]:\\[^\s\"']*")
_POSIX_PATH = re.compile(r"(?<![\w./])/(?:home|Users|root|var|tmp|opt|mnt)/[^\s\"']*")

#: Longitud máxima de una línea saneada. Más que esto no aporta y llena el informe.
MAX_LINE = 500

REDACTED = "[redactado]"


def redact_secrets(text: str) -> str:
    """Sustituye el valor de cualquier etiqueta sensible por una marca, conservando la etiqueta."""

    def _sustituir(encontrado: re.Match[str]) -> str:
        comilla = encontrado.group(3)
        return f"{encontrado.group(1)}{encontrado.group(2)}{comilla}{REDACTED}{comilla}"

    return _SECRET_PATTERN.sub(_sustituir, text)


def redact_paths(text: str) -> str:
    """Abrevia rutas absolutas: se conserva la forma y se descarta de dónde cuelgan."""
    sin_windows = _WINDOWS_PATH.sub(lambda m: "…\\" + _ultimo_componente(m.group(0), "\\"), text)
    return _POSIX_PATH.sub(lambda m: "…/" + _ultimo_componente(m.group(0), "/"), sin_windows)


def _ultimo_componente(ruta: str, separador: str) -> str:
    partes = [parte for parte in ruta.split(separador) if parte]
    return partes[-1] if partes else "…"


def sanitize_line(line: str) -> str:
    """Sanea una línea entera: secretos, rutas y longitud. Es lo que se enseña en el diagnóstico."""
    limpia = redact_paths(redact_secrets(line)).replace("\r", " ").replace("\n", " ").strip()
    if len(limpia) > MAX_LINE:
        return limpia[: MAX_LINE - 1] + "…"
    return limpia


__all__ = ["MAX_LINE", "REDACTED", "redact_paths", "redact_secrets", "sanitize_line"]
