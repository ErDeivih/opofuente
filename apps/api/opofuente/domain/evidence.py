"""Cómo se trocea el texto de una versión en evidencias citables: reglas puras, sin base de datos.

Una evidencia es un fragmento citable, no el documento entero, así que tiene un tope de longitud.
Hasta octubre de 2026 cada sección producía **una** evidencia recortada a ese tope, y todo lo que
pasaba de él se perdía: una página de PDF de 3.000 caracteres dejaba 1.200 y un bloque de texto de
50.000 dejaba los mismos 1.200. Medido sobre el material real, se guardaba el 36,7 % del texto
extraído (docs/reviews/TEXTO-EXTRAIDO-QUE-NO-SE-PODIA-LEER-2026-09.md).

Las reglas que se cumplen ahora:

- **Nada del texto extraído se queda fuera**: una sección larga se parte en varias evidencias, y el
  texto que no cae en ninguna sección (el cuerpo de un Markdown, lo que queda tras el tope de
  secciones de un `.txt`) se cubre con evidencias propias.
- **Ninguna evidencia pasa del tope** y los cortes caen, por este orden de preferencia, en un salto
  de párrafo, un salto de línea, un final de frase o un espacio. Solo si no hay nada de eso en la
  ventana se corta a pelo.
- **Los offsets son exactos**: `texto[char_start:char_end]` es literalmente la evidencia, sin
  espacios al principio ni al final.
"""

from __future__ import annotations

from collections.abc import Iterable

#: Tope duro de una evidencia, en caracteres.
MAX_EVIDENCE_CHARS = 1200

#: Longitud a la que se intenta cortar: deja margen para alargar el corte hasta un buen límite.
TARGET_EVIDENCE_CHARS = 1000

#: Separadores preferidos, del mejor al peor. El corte se hace **después** del separador.
_SEPARADORES: tuple[str, ...] = ("\n\n", "\n", ". ", "; ", ", ", " ")


def _sin_blancos(texto: str, inicio: int, fin: int) -> tuple[int, int]:
    """Estrecha `[inicio, fin)` hasta que no empiece ni termine en blanco."""
    while inicio < fin and texto[inicio].isspace():
        inicio += 1
    while fin > inicio and texto[fin - 1].isspace():
        fin -= 1
    return inicio, fin


def _mejor_corte(texto: str, inicio: int, limite: int, minimo: int) -> int:
    """Posición de corte en `(minimo, limite]`: el mejor separador más a la derecha."""
    for separador in _SEPARADORES:
        posicion = texto.rfind(separador, minimo, limite)
        if posicion != -1:
            return posicion + len(separador)
    return limite


def evidence_cuts(
    texto: str,
    inicio: int,
    fin: int,
    *,
    max_chars: int = MAX_EVIDENCE_CHARS,
    target_chars: int = TARGET_EVIDENCE_CHARS,
) -> tuple[tuple[int, int], ...]:
    """Parte `texto[inicio:fin]` en tramos de como mucho `max_chars`, sin blancos en los bordes.

    Devuelve offsets **absolutos** sobre `texto`. Un tramo vacío o solo de blancos no produce nada.
    """
    if max_chars < 1 or target_chars < 1 or target_chars > max_chars:
        raise ValueError("max_chars y target_chars deben ser positivos y target_chars ≤ max_chars")
    inicio = max(inicio, 0)
    fin = min(fin, len(texto))
    cortes: list[tuple[int, int]] = []
    actual, fin = _sin_blancos(texto, inicio, fin)
    while actual < fin:
        if fin - actual <= max_chars:
            cortes.append((actual, fin))
            break
        # Se busca el mejor separador entre la mitad del objetivo y el tope: así ningún tramo
        # queda ridículamente corto por culpa de un salto de línea temprano.
        limite = actual + max_chars
        minimo = actual + target_chars // 2
        corte = _mejor_corte(texto, actual, min(limite, actual + target_chars), minimo)
        if corte == min(limite, actual + target_chars):
            # Nada antes del objetivo: se mira hasta el tope duro antes de cortar a pelo.
            corte = _mejor_corte(texto, actual, limite, minimo)
        tramo = _sin_blancos(texto, actual, corte)
        if tramo[0] < tramo[1]:
            cortes.append(tramo)
        actual, _ = _sin_blancos(texto, corte, fin)
    return tuple(cortes)


def uncovered_ranges(
    longitud: int, rangos: Iterable[tuple[int, int]]
) -> tuple[tuple[int, int], ...]:
    """Huecos de `[0, longitud)` que no cubre ningún rango. Los rangos pueden solaparse."""
    huecos: list[tuple[int, int]] = []
    cursor = 0
    for inicio, fin in sorted((max(a, 0), min(b, longitud)) for a, b in rangos):
        if fin <= inicio:
            continue
        if inicio > cursor:
            huecos.append((cursor, inicio))
        cursor = max(cursor, fin)
    if cursor < longitud:
        huecos.append((cursor, longitud))
    return tuple(huecos)
