"""Emparejar cada **fragmento** de texto con el nodo del programa del que habla (paso 1 de S14).

Por qué existe este módulo, y por qué no es un clasificador de documentos:

La aplicación clasifica el material **entero** —un PDF es «temario», un examen es «examen»— y ahí se
queda.
Pero un temario de treinta páginas **no pertenece a un tema**: contiene decenas de fragmentos, y
cada uno sí
pertenece a algo. `04_INGESTION-AND-CLASSIFICATION §7` ya pedía «recuperar nodos candidatos por
coincidencia
de títulos/entidades» antes de llamar a ningún modelo. Lo que se ha medido en el material real del
propietario es que ese paso, hecho **por fragmentos** y contra los **títulos oficiales**, coloca
bien el
bloque en el **93,8 %** de los documentos y el tema exacto en el **61,5 %**, sin ningún modelo, sin
etiquetas y sin entrenar nada. La misma tarea pedida al documento entero daba el 18,5 % (el azar es
25 %).

La regla no decide: propone. Y no fuerza: si un fragmento no comparte palabras distintivas
suficientes con
ningún título, **no se propone nada**, que es un resultado válido y explícito (`04 §7`:
`unassigned`).

Por qué cuenta palabras en vez de usar un modelo: porque un título oficial dice lo que el tema
trata, y las
palabras que **distinguen** unos títulos de otros (una que aparece en un solo título pesa mucho; una
que
aparece en diez, poco) son exactamente la señal que hace falta. Es determinista, se puede explicar
señal a
señal —como el motor de clasificación que ya existe— y no cuesta nada.

Lo que **no** hace: no decide el tema de un documento (eso es sumar sus fragmentos, y es de la capa
de
aplicación), no escribe nada, no toca la base de datos y no llama a la red.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass

#: Palabras que no distinguen un tema de otro: aparecen en cualquier texto de la oposición y en casi
#: todos
#: los títulos. Se excluyen antes de comparar, y también los conectores y los nombres de la propia
#: estructura («tema», «bloque», «epígrafe»), que están en todos los títulos por igual.
PALABRAS_SIN_VALOR: frozenset[str] = frozenset(
    {
        "de",
        "del",
        "la",
        "las",
        "el",
        "los",
        "un",
        "una",
        "unos",
        "unas",
        "y",
        "o",
        "u",
        "e",
        "en",
        "con",
        "sin",
        "para",
        "por",
        "que",
        "al",
        "a",
        "su",
        "sus",
        "se",
        "le",
        "les",
        "lo",
        "como",
        "mas",
        "menos",
        "sobre",
        "entre",
        "segun",
        "contra",
        "ni",
        "tan",
        "todo",
        "toda",
        "todos",
        "todas",
        "este",
        "esta",
        "estos",
        "estas",
        "es",
        "son",
        "ser",
        "fue",
        "han",
        "ha",
        "hay",
        "otro",
        "otra",
        "otros",
        "otras",
        "cual",
        "cuales",
        "cuando",
        "donde",
        "quien",
        "quienes",
        "articulo",
        "capitulo",
        "tema",
        "temas",
        "bloque",
        "bloques",
        "apartado",
        "epigrafe",
        "epigrafes",
        "pagina",
        "indice",
        "contenido",
        "introduccion",
        "general",
        "generales",
        "basica",
        "basicas",
        "basico",
        "basicos",
    }
)

#: Longitudes del troceado, heredadas de la medición (`05_RAG §3` pide trocear por unidad con
#: sentido):
#: por debajo del mínimo el trozo es un encabezado o un pie, y por encima el trozo mezcla temas.
MINIMO_CARACTERES_TROZO = 250
MAXIMO_CARACTERES_TROZO = 1_400

#: Umbral medido sobre el material real: por debajo, el trozo se queda sin asignar. No se baja para
#: que
#: «haya más propuestas»: una propuesta floja es una decisión que alguien tiene que deshacer.
UMBRAL_POR_DEFECTO = 0.25

#: Cuántas alternativas se guardan junto a la elegida, para que la revisión tenga sentido
#: (`Proposal` ya
#: guarda las suyas: esto es lo mismo, en el vocabulario de este módulo).
MAXIMO_ALTERNATIVAS = 3


@dataclass(frozen=True, slots=True)
class NodoPrograma:
    """Un nodo del programa al que se puede asignar un fragmento.

    `path` es la ruta oficial («I.3», «IV.10») y es lo que ordena y desempata: dos nodos con la
    misma
    puntuación se resuelven por ruta, nunca por el orden en que hayan llegado, para que el resultado
    sea
    el mismo en dos ejecuciones y en dos máquinas.
    """

    node_id: str
    path: str
    title: str

    def __post_init__(self) -> None:
        if not self.node_id:
            raise ValueError("Un nodo del programa necesita identificador")
        if not self.path:
            raise ValueError("Un nodo del programa necesita ruta")


@dataclass(frozen=True, slots=True)
class Coincidencia:
    """El nodo que mejor encaja con un fragmento, con su puntuación y sus alternativas."""

    nodo: NodoPrograma
    puntuacion: float
    alternativas: tuple[tuple[NodoPrograma, float], ...] = ()

    @property
    def es_floja(self) -> bool:
        """¿Está la puntuación justo en el límite? Sirve para pedir revisión en vez de decidir."""
        return self.puntuacion < UMBRAL_POR_DEFECTO * 1.5


def normalizar(texto: str) -> str:
    """Texto en minúsculas, sin acentos y sin signos: solo letras, números y espacios simples.

    Los acentos se quitan porque el material real llega de todas las formas: texto nativo del PDF,
    OCR,
    copiado y pegado de una web. «Constitución» y «Constitucion» son la misma palabra, y comparar
    sin
    normalizar perdería coincidencias por un detalle de codificación.
    """
    sin_acentos = "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(caracter) != "Mn"
    )
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", sin_acentos)).strip()


def raiz(palabra: str) -> str:
    """Recorte de sufijos para que «administrativo» y «administrativa» cuenten como la misma
    palabra.

    Es un recorte tosco a propósito: un lematizador de verdad traería una dependencia y un
    diccionario
    para un problema que aquí se resuelve comparando títulos oficiales. Se documenta como lo que es.
    """
    for sufijo in ("ciones", "cion", "mente", "dades", "dad", "es", "os", "as", "a", "o", "s"):
        if len(palabra) > 6 and palabra.endswith(sufijo):
            return palabra[: -len(sufijo)]
    return palabra


def palabras(texto: str) -> tuple[str, ...]:
    """Las palabras que cuentan de un texto: sin acentos, sin las vacías y sin las de cuatro letras
    o menos."""
    return tuple(
        raiz(palabra)
        for palabra in re.findall(r"[a-z0-9]{4,}", normalizar(texto))
        if palabra not in PALABRAS_SIN_VALOR
    )


def fragmentar(
    texto: str,
    *,
    minimo: int = MINIMO_CARACTERES_TROZO,
    maximo: int = MAXIMO_CARACTERES_TROZO,
) -> tuple[str, ...]:
    """Trocea un texto en unidades con sentido, agrupando párrafos hasta el tamaño objetivo.

    No se corta por número fijo de caracteres porque un tema se reconoce por lo que dice un párrafo
    entero, no por una ventana arbitraria.

    Dos reglas que se aprendieron escribiendo esto, y las dos importan:

    - **Un párrafo más largo que el máximo se parte, nunca se recorta**: recortarlo perdería texto,
    y
      perder texto de un temario no es una decisión de formato, es perder material.
    - **Un bloque corto suelto se descarta** (un pie, un número de página, un encabezado), pero el
      **resto** de un párrafo partido se conserva aunque quede por debajo del mínimo: una cola de
      200
      caracteres es contenido, no una migaja.
    """
    if minimo <= 0 or maximo < minimo:
        raise ValueError("Los límites del troceado no tienen sentido")
    bloques = [bloque.strip() for bloque in re.split(r"\n\s*\n", texto) if bloque.strip()]
    piezas: list[tuple[str, bool]] = []
    for bloque in bloques:
        if len(bloque) <= maximo:
            piezas.append((bloque, False))
        else:
            piezas.extend((bloque[i : i + maximo], True) for i in range(0, len(bloque), maximo))

    trozos: list[str] = []
    actual = ""
    tiene_resto = False
    for pieza, es_resto in piezas:
        if len(actual) + len(pieza) + 2 <= maximo:
            actual = f"{actual}\n\n{pieza}" if actual else pieza
            tiene_resto = tiene_resto or es_resto
            continue
        if actual and (len(actual) >= minimo or tiene_resto):
            trozos.append(actual)
        actual, tiene_resto = pieza, es_resto
    if actual and (len(actual) >= minimo or tiene_resto):
        trozos.append(actual)
    return tuple(trozos)


class EmparejadorDeTemas:
    """Compara fragmentos con los títulos de un programa y propone el nodo que mejor encaja.

    Se construye una vez por programa (con los nodos de la convocatoria activa) y se reutiliza: el
    peso de
    cada palabra se calcula sobre el conjunto de títulos, así que construir el emparejador es lo que
    fija
    la referencia. Si cambia el programa, se construye otro.
    """

    def __init__(self, nodos: Sequence[NodoPrograma]) -> None:
        if not nodos:
            raise ValueError("Sin nodos del programa no hay nada con lo que comparar")
        self._nodos: tuple[NodoPrograma, ...] = tuple(sorted(nodos, key=lambda nodo: nodo.path))
        raices_por_nodo = tuple(frozenset(palabras(nodo.title)) for nodo in self._nodos)

        # Una palabra que aparece en un solo título es la que distingue; una que aparece en diez, no
        # distingue nada. El peso es 1 entre el número de títulos en los que aparece.
        apariciones: dict[str, int] = {}
        for raices in raices_por_nodo:
            for raiz_ in raices:
                apariciones[raiz_] = apariciones.get(raiz_, 0) + 1
        self._peso: dict[str, float] = {
            raiz_: 1.0 / cuantos for raiz_, cuantos in apariciones.items()
        }

        # La puntuación se normaliza por el peso total del título: así un título largo y detallado
        # no gana
        # sólo por ser largo, que es la trampa más fácil de este método. El precio de esta
        # normalización es
        # el contrario y hay que decirlo: un título muy largo **diluye** la puntuación de un
        # fragmento que
        # sólo comparte una o dos de sus palabras, así que ese fragmento se queda sin asignar. Se
        # acepta a
        # propósito —el error cae del lado conservador, que es el que no crea decisiones que
        # deshacer— y
        # está medido: es la fórmula con la que se obtuvo el 93,8 % de bloque en el material real.
        self._total: tuple[float, ...] = tuple(
            sum(self._peso[raiz_] for raiz_ in raices) for raices in raices_por_nodo
        )
        self._raices = raices_por_nodo

    @property
    def nodos(self) -> tuple[NodoPrograma, ...]:
        """Los nodos con los que compara, ordenados por ruta."""
        return self._nodos

    def puntuar(self, fragmento: str) -> tuple[tuple[NodoPrograma, float], ...]:
        """Todos los nodos con su puntuación, de mejor a peor y con el desempate fijo por ruta."""
        raices = set(palabras(fragmento))
        puntuaciones = [
            (
                nodo,
                (sum(self._peso[raiz_] for raiz_ in raices & propias) / total) if total else 0.0,
            )
            for nodo, propias, total in zip(self._nodos, self._raices, self._total, strict=True)
        ]
        puntuaciones.sort(key=lambda par: (-par[1], par[0].path))
        return tuple(puntuaciones)

    def emparejar(self, fragmento: str, *, umbral: float | None = None) -> Coincidencia | None:
        """El nodo que mejor encaja, o `None` si ninguno llega al umbral.

        Devolver `None` no es un fallo: es la respuesta correcta para un fragmento que no habla de
        ningún
        tema del programa (una portada, un índice, un caso práctico de examen). Forzarlo sería peor
        que no
        proponer nada, porque crearía una decisión que alguien tendría que deshacer.
        """
        limite = UMBRAL_POR_DEFECTO if umbral is None else umbral
        if not 0.0 <= limite <= 1.0:
            raise ValueError("El umbral debe estar entre 0 y 1")
        puntuaciones = self.puntuar(fragmento)
        mejor, puntuacion = puntuaciones[0]
        if puntuacion < limite:
            return None
        alternativas = tuple(
            (nodo, valor)
            for nodo, valor in puntuaciones[1 : MAXIMO_ALTERNATIVAS + 1]
            if valor >= limite
        )
        return Coincidencia(nodo=mejor, puntuacion=round(puntuacion, 6), alternativas=alternativas)
