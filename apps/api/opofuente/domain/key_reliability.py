"""Si la clave de un conjunto se puede fiar, y por que no.

El problema que resuelve este modulo lo midio el propietario, no el codigo: **hay bancos con la
respuesta correcta mal guardada**, y el alumno ya esta practicando con ellos. Comparando la letra
que dan los apuntes con la clave de cada pregunta y agrupando por conjunto de origen, la media
global era del 10 % —normal, porque los apuntes se equivocan—, pero **14 conjuntos pasaban del
30 %**, y en un conjunto de 18 preguntas eso no es que los apuntes se equivoquen: es que la clave
esta mal.

De ahi las tres palabras que se guardan en `question_sets.key_reliability`:

- **`fiable`**: la discrepancia medida esta por debajo del 15 %, o el conjunto **no se puede medir**
  (menos de `MINIMO_COMPROBADAS` preguntas con letra y clave). Un conjunto que no se ha podido medir
  no se cuarentena nunca: seria castigar por lo que no se sabe.
- **`dudosa`** (del 15 % al 30 %): entra en los tests, con la marca **«clave en revision»**.
- **`no_fiable`** (mas del 30 %): **no entra** en tests, simulacros ni repasos, y **no cuenta** en
  el
  denominador de cobertura de los apuntes.

Las dos fronteras son las del documento que manda en el objetivo
  (`AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO
§1`) y son **estrictas arriba**: «por encima del 30 %» es `>`, asi que un 30,0 % exacto es `dudosa`.
Se escribe aqui, en una constante con nombre, y no repartido por los sitios que deciden.

Todo lo de este modulo es puro: no sabe de SQL, ni de ficheros, ni de modelos. La medida se calcula
desde las filas que le den y se puede probar sin base de datos.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

#: Cuantas preguntas con letra y clave hacen falta para poder medir un conjunto. Por debajo de esto
#: la discrepancia es ruido: 2 de 3 son un 67 % que no dice nada de la clave.
MINIMO_COMPROBADAS = 15

#: Por encima de esta discrepancia, el conjunto queda en cuarentena.
UMBRAL_NO_FIABLE = 0.30

#: A partir de esta discrepancia (y hasta `UMBRAL_NO_FIABLE`), el conjunto entra marcado.
UMBRAL_DUDOSA = 0.15

#: Lo que se le ensena al alumno cuando la clave de su pregunta esta en revision. Es un texto y
#: no un booleano: el alumno tiene que poder entender por que se le avisa.
MARCA_EN_REVISION = "clave en revisión"

#: El actor con el que se auditan los cambios de fiabilidad. Uno solo, para que la auditoria diga
#: siempre quien los hizo: la puerta de datos del final de cada tema.
ACTOR = "f19:puerta-de-claves"

#: Las letras de una pregunta de cuatro opciones. Se usa para probar permutaciones (una opcion de
#: mas o de menos): el alfabeto es cerrado y probarlo entero es barato.
LETRAS = ("a", "b", "c", "d")


class KeyReliability(StrEnum):
    """Cuanto se puede fiar uno de la clave de un conjunto. Es vocabulario cerrado: la base lo
    impone con un `CHECK`."""

    FIABLE = "fiable"
    DUDOSA = "dudosa"
    NO_FIABLE = "no_fiable"

    @property
    def entra_en_los_tests(self) -> bool:
        """¿Sus preguntas pueden entrar en un test, un simulacro o un repaso? Las dudosas si."""
        return self is not KeyReliability.NO_FIABLE

    @property
    def se_marca_al_alumno(self) -> bool:
        """¿Hay que ensenarle la marca «clave en revision» cuando responda una de sus preguntas?"""
        return self is KeyReliability.DUDOSA


def letras_de_clave(crudo: str | None) -> tuple[str, ...]:
    """Las letras de la clave, guardadas como JSON (`["a","c"]`) o como texto suelto.

    `answer_key_entries.correct_option_keys_json` es JSON en todo lo que escribe el proyecto, pero
    lo que llega de una importacion vieja puede venir como `a` o `a,c`. Se aceptan las dos formas
    porque **comparar mal la clave seria justo el defecto que este modulo mide**.
    """
    if crudo is None:
        return ()
    texto = crudo.strip()
    if not texto:
        return ()
    if texto.startswith("["):
        try:
            datos = json.loads(texto)
        except json.JSONDecodeError:
            datos = None
        if isinstance(datos, list):
            return tuple(str(valor).strip().lower() for valor in datos if str(valor).strip())
    return tuple(parte.strip().lower() for parte in re.split(r"[,\s]+", texto) if parte.strip())


def normalizar_letra(letra: str | None) -> str:
    """La letra tal como se compara: sin espacios, sin punto y en minuscula."""
    return (letra or "").strip().strip(".").lower()


def discrepante(letra: str | None, letras_de_la_clave: Sequence[str]) -> bool:
    """¿La letra de los apuntes contradice la clave? Solo se pregunta con las dos cosas puestas."""
    propia = normalizar_letra(letra)
    if not propia or not letras_de_la_clave:
        return False
    return propia not in {normalizar_letra(otra) for otra in letras_de_la_clave}


def veredicto(comprobadas: int, discrepantes: int) -> KeyReliability:
    """El veredicto de un conjunto a partir de su medida.

    Con menos de `MINIMO_COMPROBADAS` no se opina: el conjunto queda `fiable` porque **no se ha
    podido medir**, y eso es distinto de haberlo medido bien.
    """
    if comprobadas < MINIMO_COMPROBADAS:
        return KeyReliability.FIABLE
    proporcion = discrepantes / comprobadas
    if proporcion > UMBRAL_NO_FIABLE:
        return KeyReliability.NO_FIABLE
    if proporcion >= UMBRAL_DUDOSA:
        return KeyReliability.DUDOSA
    return KeyReliability.FIABLE


@dataclass(frozen=True, slots=True)
class AnclaMedible:
    """Una fila de `question_note_anchors` con lo justo para medir: la letra y la clave.

    `expected_letters` es la clave **tal como la leyó el motor de apuntes al comprobar la pregunta**
        (la activa o la de borrador de su conjunto en ese momento), no la clave de hoy: es
      exactamente el
    dato con el que se decidió que la letra no cuadraba.
    """

    set_id: str
    set_title: str
    question_version_id: str
    answer_letter: str | None
    expected_letters: str | None

    @property
    def medible(self) -> bool:
        """¿Se puede comparar? Hace falta letra de los apuntes **y** una clave con letras.

        Una clave vacía (`'[]'`, `''`, `null`) no es una clave que discuta: es una pregunta **sin
                clave**, y contarla como discrepancia cambiaría el veredicto de su conjunto por un
          motivo que
        no es el suyo.
        """
        return bool(normalizar_letra(self.answer_letter)) and bool(
            letras_de_clave(self.expected_letters)
        )

    @property
    def discrepa(self) -> bool:
        return discrepante(self.answer_letter, letras_de_clave(self.expected_letters))


@dataclass(frozen=True, slots=True)
class MedidaDeConjunto:
    """La discrepancia apuntes -> clave de **un** conjunto, con sus dos numeros."""

    set_id: str
    set_title: str
    comprobadas: int
    discrepantes: int

    @property
    def discrepancia(self) -> float:
        return 0.0 if not self.comprobadas else self.discrepantes / self.comprobadas

    @property
    def veredicto(self) -> KeyReliability:
        return veredicto(self.comprobadas, self.discrepantes)

    @property
    def medible(self) -> bool:
        return self.comprobadas >= MINIMO_COMPROBADAS

    def linea(self) -> str:
        if not self.medible:
            return (
                f"{self.set_title}: sin medir ({self.comprobadas} comprobada(s), "
                f"mínimo {MINIMO_COMPROBADAS}) · fiable por defecto"
            )
        return (
            f"{self.set_title}: {self.discrepantes}/{self.comprobadas} = "
            f"{100 * self.discrepancia:.1f} % · {self.veredicto.value}"
        )


def medir_conjuntos(anclas: Iterable[AnclaMedible]) -> tuple[MedidaDeConjunto, ...]:
    """La discrepancia por conjunto de origen, con una pregunta contada **una** vez.

    **La unidad es la pregunta y el conjunto de origen es `question_versions.question_set_id`** (su
    nombre legible, `question_sets.title`). No hay ninguna pregunta sin conjunto: el campo es
    obligatorio en la base.

    Tres reglas, y las tres se han tenido que demostrar contra una medición distinta:

    1. **Una pregunta cuenta una vez**, aunque tenga ancla en dos temas. Contarla dos veces infla el
       denominador sin añadir información (en la base real solo 4 preguntas de 6.307 tienen ancla en
       más de un tema, así que la diferencia es pequeña, pero la unidad correcta es la pregunta: el
       documento pide «mínimo 15 preguntas comprobadas»).
        2. **Una ancla sin clave (`expected_letters` vacío o `'[]'`) no cuenta**: no es una
      discrepancia,
       es una pregunta **sin clave** con la que comparar (`key_status = 'ninguna'`), que es otro
              defecto y va a la bandeja con su categoría. Medirla como discrepancia diría que la
         clave de un
       conjunto es mala cuando el conjunto no tiene clave, y subiría a `no_fiable` conjuntos que no
       lo son.
    3. **Si alguna de las anclas de una pregunta discrepa, la pregunta discrepa.** Es la variante
       conservadora: no se tira la evidencia de un tema porque otro tema haya salido bien.
    """
    por_pregunta: dict[str, list[AnclaMedible]] = {}
    for ancla in anclas:
        if not ancla.medible:
            continue
        por_pregunta.setdefault(ancla.question_version_id, []).append(ancla)

    acumulado: dict[str, list[int]] = {}
    titulos: dict[str, str] = {}
    for suyas in por_pregunta.values():
        primera = suyas[0]
        titulos.setdefault(primera.set_id, primera.set_title)
        numeros = acumulado.setdefault(primera.set_id, [0, 0])
        numeros[0] += 1
        if any(ancla.discrepa for ancla in suyas):
            numeros[1] += 1

    medidas = [
        MedidaDeConjunto(
            set_id=set_id,
            set_title=titulos.get(set_id, ""),
            comprobadas=numeros[0],
            discrepantes=numeros[1],
        )
        for set_id, numeros in acumulado.items()
    ]
    medidas.sort(key=lambda medida: (-medida.discrepancia, -medida.comprobadas, medida.set_title))
    return tuple(medidas)


def probar_desplazamientos(
    anclas: Sequence[tuple[int, str]],
    claves_por_posicion: Mapping[int, str],
    *,
    actual: MedidaDeConjunto,
) -> tuple[Desplazamiento, ...]:
    """Prueba si la clave de un conjunto está **corrida** en vez de equivocada.

    Es el paso barato del §1: antes de dar por mal una clave, se comprueba si la extracción del
    material se fue una pregunta o una opción. Se prueban dos cosas:

    - **la pregunta**: la letra de la clave de la posición `p + k`, con `k` de -2 a +2, contra la
      letra que dan los apuntes en `p`;
    - **la opción**: la letra de la clave de la posición `p`, girada en el alfabeto (una opción de
      más o de menos).

    `anclas` son pares `(posición de la pregunta, letra que dan los apuntes)` y
    `claves_por_posicion` la clave **de cada posición**, en la misma línea base que la lectura de
    hoy: la letra que el motor de apuntes leyó al comprobar esa pregunta, que es lo que `actual`
    mide. Mezclar dos líneas base —la del ancla para «hoy» y la de la plantilla de hoy para las
    alternativas— hace que la tabla no se pueda comparar consigo misma, y una tabla así se puede
    leer al revés sin que nada avise. `actual` se usa solo para **comprobar** que la línea base
    cuadra: si no cuadra, se devuelve la lectura de hoy sola y se dice, en vez de enseñar una
    comparación que no es de lo mismo.

    Medido en la base real, con la línea base cuadrada: **ningún conjunto de los que no son fiables
    baja del 10 %**, y las rotaciones de opciones se quedan en el **nivel del azar** (el 25 % de
    cuatro opciones). Sus claves no están corridas: están mal en muchos sitios, y el paso siguiente
    es la clave derivada.

    `Desplazamiento.discrepantes` es el **numerador de lo que no cuadra**, así que cuanto más bajo
    mejor, y `explica_la_discrepancia` es lo que hay que mirar para decidir: dice si la alternativa
    baja del 10 %. La fila de hoy no puede explicarse a sí misma: se excluye a propósito.
    """
    hoy_comparables = 0
    hoy_iguales = 0
    for posicion, letra in anclas:
        letra_de_la_clave = claves_por_posicion.get(posicion)
        if not letra_de_la_clave:
            continue
        hoy_comparables += 1
        if normalizar_letra(letra) == normalizar_letra(letra_de_la_clave):
            hoy_iguales += 1
    if (hoy_comparables, hoy_comparables - hoy_iguales) != (
        actual.comprobadas,
        actual.discrepantes,
    ):
        # La línea base no es la misma que la de `actual`: no se compara nada, porque una tabla con
        # dos orígenes distintos es la que se puede leer al revés.
        return (
            Desplazamiento(
                descripcion="lectura de hoy (línea base sin cuadrar: no se prueban alternativas)",
                comprobadas=actual.comprobadas,
                discrepantes=actual.discrepantes,
                es_alternativa=False,
            ),
        )

    lecturas = [
        Desplazamiento(
            descripcion="lectura de hoy (la clave en su sitio)",
            comprobadas=actual.comprobadas,
            discrepantes=actual.discrepantes,
            es_alternativa=False,
        )
    ]
    for salto in (-2, -1, 1, 2):
        comparables = 0
        iguales = 0
        for posicion, letra in anclas:
            letra_de_la_clave = claves_por_posicion.get(posicion + salto)
            if not letra_de_la_clave:
                continue
            comparables += 1
            if normalizar_letra(letra) == normalizar_letra(letra_de_la_clave):
                iguales += 1
        if comparables:
            lecturas.append(
                Desplazamiento(
                    descripcion=f"la clave, {salto:+d} pregunta(s)",
                    comprobadas=comparables,
                    discrepantes=comparables - iguales,
                )
            )
    for giro in (1, 2, 3):
        comparables = 0
        iguales = 0
        for posicion, letra in anclas:
            letra_de_la_clave = claves_por_posicion.get(posicion)
            if not letra_de_la_clave:
                continue
            comparables += 1
            if normalizar_letra(letra) == _girar(letra_de_la_clave, giro):
                iguales += 1
        if comparables:
            lecturas.append(
                Desplazamiento(
                    descripcion=f"las opciones, {giro} puesto(s)",
                    comprobadas=comparables,
                    discrepantes=comparables - iguales,
                )
            )
    return tuple(lecturas)


def _girar(letra: str, puestos: int) -> str:
    """La letra, `puestos` más adelante en el alfabeto de cuatro opciones."""
    limpia = normalizar_letra(letra)
    if limpia not in LETRAS:
        return limpia
    return LETRAS[(LETRAS.index(limpia) + puestos) % len(LETRAS)]


@dataclass(frozen=True, slots=True)
class Desplazamiento:
    """Lo que se ha probado para saber si una clave esta **corrida** en vez de equivocada.

    `salto_de_preguntas` mueve la clave una o dos posiciones; `giro_de_opciones` rota el alfabeto
    (una opcion de mas o de menos). Si alguno de los dos baja la discrepancia por debajo del 10 %,
    la clave no esta mal: esta desplazada, y volver a extraerla del original la arregla.

    `es_alternativa` distingue la fila de **hoy** de las que se prueban. No es un adorno: la lectura
    de hoy **no puede explicarse a si misma** —si hoy ya coincidiera, no habria discrepancia que
    explicar—, y sin esta bandera la fila de hoy de un conjunto con pocas anclas movibles se marcaba
    como «lo explica», que es una contradiccion en la propia tabla.
    """

    descripcion: str
    comprobadas: int
    discrepantes: int
    es_alternativa: bool = True

    @property
    def discrepancia(self) -> float:
        return 0.0 if not self.comprobadas else self.discrepantes / self.comprobadas

    @property
    def explica_la_discrepancia(self) -> bool:
        """¿Es una alternativa que baja del 10 %, con muestra bastante? La fila de hoy no."""
        return (
            self.es_alternativa
            and self.comprobadas >= MINIMO_COMPROBADAS
            and self.discrepancia < 0.10
        )


__all__ = [
    "ACTOR",
    "LETRAS",
    "MARCA_EN_REVISION",
    "MINIMO_COMPROBADAS",
    "UMBRAL_DUDOSA",
    "UMBRAL_NO_FIABLE",
    "AnclaMedible",
    "Desplazamiento",
    "KeyReliability",
    "MedidaDeConjunto",
    "discrepante",
    "letras_de_clave",
    "medir_conjuntos",
    "normalizar_letra",
    "probar_desplazamientos",
    "veredicto",
]
