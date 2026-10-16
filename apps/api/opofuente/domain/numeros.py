"""Las cifras que la API **escribe en prosa**: en español, con coma y sin ceros de más (§2.2).

Por qué existe este módulo, y no vale con `decimal_text`: son **dos cosas distintas**, y
confundirlas fue el defecto.

- `decimal_text` es el **decimal que viaja en el contrato** (punto y cuatro cifras, `0.3333`): es un
  dato para leer, no una cifra para mirar, y su formato es de máquina.
- Esto es lo que se lee **dentro de una frase** —«es 0,33 sobre 50», «un intervalo que va de 0,34 a
  1,00»—, y en una frase la cifra va como la escribe quien la lee: **con coma**.

La pantalla se unificó en `apps/web/src/lib/numeros.ts` (un solo módulo para los siete sitios que
pintan un número), y **la frase que compone el servidor se quedó fuera**. El resultado se midió el
16-oct-2026 y es el peor de los sitios posibles: en la **misma fila** de la tabla del diagnóstico
convivían `0,34 - 1,00` (la columna, la pinta la pantalla) y `0.3424 a 1.0` (la nota de esa fila).

Tres reglas, las mismas que en el módulo del frontend:

1. **una nota** —lo que se puntúa— con coma y **siempre** dos decimales: `12,50`, `0,00`, `-0,33`;
2. **una escala** —el máximo, el mínimo, un umbral publicado— va igual pero **sin ceros de más**:
   `50`, `25`, `25,5`. Es la cifra que publica la convocatoria y no se le añade precisión;
3. **un porcentaje** sin decimales de relleno donde no hacen falta y con ellos donde sí (la
   cobertura, que se compara contra el listón del 90 %).

Y una cosa que **no** se toca aquí: los identificadores y los códigos (`IV.1`, `50 preguntas`, una
versión, un tamaño en KB) **no son notas ni magnitudes de una nota**, y no pasan por este módulo.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

__all__ = ["escala", "nota", "porcentaje"]

#: Lo que se admite como cifra: una fracción exacta (como se calcula la puntuación) o un número.
Cifra = Fraction | int | float | Decimal


def _exacto(valor: Cifra) -> Decimal:
    """El valor como `Decimal`, sin pasar por coma flotante cuando no hace falta.

    Una puntuación se calcula con `Fraction` (un tercio no es un decimal), así que se convierte
    dividiendo numerador entre denominador; un número que ya viene de fuera (un umbral de la
    convocatoria) se lee **de su texto** y no de su binario, que es lo que evita que un 25,5 se
    convierta en 25,499999999999996.
    """
    if isinstance(valor, Fraction):
        return Decimal(valor.numerator) / Decimal(valor.denominator)
    if isinstance(valor, Decimal):
        return valor
    return Decimal(str(valor))


def _con_coma(texto: str) -> str:
    return texto.replace(".", ",")


def nota(valor: Cifra, *, decimales: int = 2) -> str:
    """Una nota: coma y **siempre** `decimales` cifras. `0,33`, `12,50`, `-0,33`."""
    exponente = Decimal(1).scaleb(-decimales)
    return _con_coma(str(_exacto(valor).quantize(exponente, rounding=ROUND_HALF_UP)))


def escala(valor: Cifra, *, decimales: int = 2) -> str:
    """Un máximo o un mínimo: los mismos decimales, **sin ceros de más**. `50`, `25`, `25,5`."""
    texto = nota(valor, decimales=decimales)
    if "," in texto:
        texto = texto.rstrip("0").rstrip(",")
    return texto


def porcentaje(proporcion: float, *, decimales: int = 1) -> str:
    """Un porcentaje a partir de una **proporción** (0-1): `0.902 → 90,2 %`."""
    return f"{nota(proporcion * 100, decimales=decimales)} %"
