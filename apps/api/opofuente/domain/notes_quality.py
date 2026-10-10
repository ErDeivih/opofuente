"""Las comprobaciones de forma de los apuntes, automáticas, antes de dar un tema por bueno.

Existen porque los tres pilotos salieron **escritos a trozos**: cada apartado era la redacción de un
lote de preguntas puesto detrás de otro. La cobertura era buena (89 % de las preguntas contestadas
contra su clave) y los apuntes no se podían estudiar: siete apartados seguidos explicando el modelo
OSI, la tabla de puertos diez veces, marcas internas a la vista y tablas a las que les faltaba el
nombre de una columna. Este módulo es la medida de eso, y no juzga el contenido: cuenta lo que se
ve.

Las cinco comprobaciones son las del informe del propietario (`REVISION-APUNTES-PILOTO-Y-RAMAS`):

1. **encabezados repetidos**: dentro del tema, dos encabezados iguales o casi iguales son el mismo
   apartado escrito dos veces; y, en el mismo sitio, **misma cabecera**, que es el otro defecto de
   los pilotos: muchos apartados **distintos** con el título empezando igual (19 «Protocolos TCP/IP:
   …»), que es lo que se ve cuando un epígrafe se parte en trozos y cada trozo se titula por su
   cuenta;
2. **marcas internas**: `[fact 23]`, `fact 5`, `<!-- fuentes …` y compañía son andamios, no apuntes;
3. **tablas sin cabecera**: toda tabla con su fila de cabecera y **todas** sus columnas con nombre
   (una fila con más celdas que la cabecera enseña una columna que nadie ha titulado);
4. **párrafos repetidos**: el porcentaje de párrafos que se parecen a otro anterior, por trigramas,
   como se midió en la revisión;
5. **densidad**: palabras del tema frente a `40 x hechos distintos`. Es el síntoma, no la cura: con
   el esquema bien hecho los mismos hechos ocupan una fracción.

Todo lo que devuelve son **cuentas y sitios**, para que se pueda arreglar sin volver a leer el tema
entero. El umbral de cada comprobación es una constante de este módulo y se dice en el informe.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from opofuente.domain.puertos import (
    familias_de_la_tabla,
    notas_sin_sentido,
    puertos_repetidos,
    tablas_de_puertos,
)
from opofuente.domain.rag import normalise
from opofuente.domain.topic_notes import MAX_PALABRAS_POR_HECHO, Hecho

#: Dos encabezados se consideran el mismo si, normalizados, se parecen más que esto.
SIMILITUD_ENCABEZADO = 0.8

#: Dos párrafos son «casi iguales» por encima de este parecido de trigramas.
SIMILITUD_PARRAFO = 0.6

#: Tope de párrafos casi repetidos de otro: el 5 % del informe del propietario.
MAX_PARRAFOS_REPETIDOS = 0.05

#: Palabras del tema por hecho distinto. El tope de densidad del informe (40). Se importa del
#: dominio de los apuntes —y no se repite aquí— porque el redactor lo necesita **antes** de
#: escribir: dos constantes con el mismo valor acabarían diciendo cosas distintas.

#: Un párrafo de menos de estas palabras no cuenta para la repetición: «Sí.» y «Ver arriba.» se
#: parecen a cualquier cosa y no dicen nada de la redacción.
MINIMO_PALABRAS_PARRAFO = 12

#: Palabras de la cabecera de un título que tienen que coincidir para hablar de «misma cabecera»
#: (19 apartados titulados «Protocolos TCP/IP: …»).
PALABRAS_DE_CABECERA = 3

#: Apartados que tienen que compartir cabecera para que sea un hallazgo y no una casualidad.
MINIMO_MISMA_CABECERA = 3

#: Los códigos de hallazgo. Son vocabulario cerrado: el informe los cuenta y la prueba los usa.
ENCABEZADOS_REPETIDOS = "encabezados_repetidos"
CABECERAS_REPETIDAS = "cabeceras_repetidas"
MARCAS_INTERNAS = "marcas_internas"
TABLAS_SIN_CABECERA = "tablas_sin_cabecera"
PARRAFOS_REPETIDOS = "parrafos_repetidos"
DENSIDAD = "densidad"
#: Las dos comprobaciones que pidió el propietario sobre la tabla de puertos: las notas que solo
#: dicen lo que un puerto **no** es salen de la tabla, y la tabla se parte por familias.
NOTAS_DE_PUERTOS = "notas_de_puertos"
FAMILIAS_DE_PUERTOS = "tablas_puertos_sin_familias"

#: Lo que no puede quedar a la vista en el texto de los apuntes. `[fact 23]` es el que se coló en
#: IV.7; el resto son las variantes con las que el mismo andamio aparece (`[hecho 3]`, `[fuente 7]`,
#: el comentario de fuentes sin cerrar). «fact» solo cuenta con número detrás: «factor» y «factura»
#: son palabras normales de un temario. Es **una** expresión y no varias: dos patrones que casan el
#: mismo trozo contarían la misma marca dos veces (`[fact 26]` y `fact 26`), y la cuenta tiene que
#: poder compararse con la del propietario.
_MARCA = re.compile(
    r"\[\s*(?:facts?|hechos?|fuentes?)\s*#?\s*\d+\s*\]"
    r"|\bfacts?\s*#\s*\d+"
    r"|\bfacts?\s+\d+\b"
    r"|(?:&lt;|<!--)\s*fuentes?",
    re.IGNORECASE,
)

#: Un encabezado de markdown: de `#` a `######` al principio de la línea.
_ENCABEZADO = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")

#: Una línea de tabla de markdown (empieza y acaba por barra, o solo empieza).
_FILA_TABLA = re.compile(r"^\s*\|.*$")

#: La línea de separación de una tabla: `| --- | :---: |`.
_SEPARADOR_TABLA = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")

#: Un párrafo, separado por línea en blanco. Las tablas y las listas también son bloques: se limpian
#: al contarlos, porque lo que se compara es lo que se lee.
_VINETA = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_MAYUSCULAS_MARKDOWN = re.compile(r"[*_`>#]+")


class ApartadoDeApuntes(Protocol):
    """Lo que una comprobación necesita de un apartado: dónde está y qué dice.

    Es un protocolo y no el tipo del dominio porque lo cumplen los dos: el apartado que se escribe
    (`NoteSection`) y el que se publica dentro del tema (`SectionNotes`). Medir el tema guardado y
    el que se acaba de escribir tiene que dar lo mismo.
    """

    @property
    def key(self) -> str: ...

    @property
    def title(self) -> str: ...

    @property
    def anchor(self) -> str: ...

    @property
    def body_markdown(self) -> str: ...


@dataclass(frozen=True, slots=True)
class Hallazgo:
    """Una comprobación que no pasa, con su cuenta y dónde está, para poder ir a arreglarla."""

    codigo: str
    cuenta: int
    detalle: str
    donde: tuple[str, ...] = ()

    def line(self) -> str:
        sitios = "" if not self.donde else f" · en {', '.join(self.donde[:5])}"
        if len(self.donde) > 5:
            sitios += f" y {len(self.donde) - 5} más"
        return f"{self.detalle}{sitios}"


@dataclass(frozen=True, slots=True)
class RevisionApuntes:
    """Lo que miden las comprobaciones sobre un tema entero. Sin hallazgos, el tema pasa."""

    apartados: int
    palabras: int
    hechos: int
    parrafos: int
    parrafos_repetidos: int
    hallazgos: tuple[Hallazgo, ...] = ()

    @property
    def limite_palabras(self) -> int:
        """El tope de extensión según los datos que tiene el tema: `40 x hechos distintos`."""
        return MAX_PALABRAS_POR_HECHO * max(self.hechos, 1)

    @property
    def porcentaje_repetidos(self) -> float:
        return 0.0 if not self.parrafos else self.parrafos_repetidos / self.parrafos

    @property
    def pasa(self) -> bool:
        return not self.hallazgos

    def lines(self) -> tuple[str, ...]:
        """El informe de la revisión: primero si pasa, después el detalle de lo que no pasa."""
        cabecera = (
            f"    revision de forma: {'PASA' if self.pasa else 'NO PASA'} · "
            f"{self.apartados} apartado(s) · {self.palabras} palabra(s) de {self.limite_palabras} "
            f"({MAX_PALABRAS_POR_HECHO} x {self.hechos} hecho(s)) · "
            f"parrafos repetidos {100.0 * self.porcentaje_repetidos:.1f} % "
            f"(tope {100 * MAX_PARRAFOS_REPETIDOS:.0f} %)"
        )
        return (cabecera, *(f"      · {hallazgo.line()}" for hallazgo in self.hallazgos))


# --- la medida de fondo ---------------------------------------------------------------------------


def trigramas(texto: str) -> frozenset[str]:
    """Los trigramas de caracteres del texto normalizado: la medida de parecido que se usa aquí."""
    limpio = re.sub(r"\s+", " ", normalise(texto)).strip()
    if len(limpio) < 3:
        return frozenset({limpio}) if limpio else frozenset()
    return frozenset(limpio[indice : indice + 3] for indice in range(len(limpio) - 2))


def parecido(uno: str, otro: str) -> float:
    """Parecido de dos textos por trigramas (Jaccard). 1.0 es el mismo texto; 0.0, nada en común."""
    suyos, ajenos = trigramas(uno), trigramas(otro)
    if not suyos or not ajenos:
        return 0.0
    return len(suyos & ajenos) / len(suyos | ajenos)


def _sin_marcas_de_markdown(linea: str) -> str:
    return _MAYUSCULAS_MARKDOWN.sub(" ", _VINETA.sub("", linea)).strip()


def _normalizado(texto: str) -> str:
    return re.sub(r"\s+", " ", normalise(texto)).strip()


def _encabezados_del_apartado(apartado: ApartadoDeApuntes) -> tuple[tuple[str, str], ...]:
    """Los encabezados del texto del apartado, sin la primera vez que se titula a sí mismo.

    Un apartado empieza por su propio título: eso no es repetirlo. La **segunda** vez que aparece sí
    se cuenta, porque es el apartado repitiéndose dentro de sí mismo.

    La comparación es la **misma** que la de los repetidos (igual o parecido ≥
    `SIMILITUD_ENCABEZADO`), y no la igualdad exacta: el redactor titula casi siempre con el mismo
    texto que se le dio, pero a veces lo parafrasea un poco («DHCP y **la** configuración
    automática»), y con la igualdad exacta ese saludo al lector contaba como un encabezado repetido
    —dos apartados de IV.7 salían por esto— mientras que la segunda aparición de verdad se sigue
    contando en los dos casos.
    """
    propio = _normalizado(apartado.title)
    salida: list[tuple[str, str]] = []
    visto_el_suyo = False
    for _, titulo in encabezados(apartado.body_markdown):
        limpio = _normalizado(titulo)
        if not visto_el_suyo and (
            limpio == propio or parecido(limpio, propio) >= SIMILITUD_ENCABEZADO
        ):
            visto_el_suyo = True
            continue
        salida.append((apartado.key, titulo))
    return tuple(salida)


def encabezados(texto: str) -> tuple[tuple[int, str], ...]:
    """Los encabezados de markdown del texto, en orden, con su nivel. ``##`` cuenta; un renglón
    suelto en negrita no."""
    encontrados: list[tuple[int, str]] = []
    for linea in texto.splitlines():
        casado = _ENCABEZADO.match(linea)
        if casado is not None:
            encontrados.append((len(casado.group(1)), casado.group(2).strip()))
    return tuple(encontrados)


def parrafos(texto: str) -> tuple[str, ...]:
    """Los párrafos del texto tal como se leen: sin viñetas, sin barras de tabla y sin encabezados.

    Las líneas de una tabla se juntan en un solo bloque (una tabla se lee como una tabla) y se
    quitan las barras: si no, dos tablas de puertos se parecerían por la forma y no por lo que
    dicen.
    """
    bloques: list[list[str]] = []
    actual: list[str] = []
    for linea in texto.splitlines():
        if not linea.strip():
            if actual:
                bloques.append(actual)
                actual = []
            continue
        actual.append(linea)
    if actual:
        bloques.append(actual)

    resultado: list[str] = []
    for bloque in bloques:
        lineas = [
            _sin_marcas_de_markdown(linea) for linea in bloque if _ENCABEZADO.match(linea) is None
        ]
        limpio = " ".join(parte for parte in lineas if parte).strip()
        if limpio:
            resultado.append(limpio)
    return tuple(resultado)


@dataclass(frozen=True, slots=True)
class TablaRota:
    """Una tabla que no se puede leer: dice cuál y por qué."""

    donde: str
    fila: int
    motivo: str


def tablas_rotas(donde: str, texto: str) -> tuple[TablaRota, ...]:
    """Las tablas de markdown del texto que no tienen cabecera utilizable.

    Tres casos, y los tres se ven en los pilotos:

    - un bloque de filas con barras **sin** la línea de separación: no es una tabla, es una fila
      suelta con barras (el lector la ve como texto con tuberías);
    - una cabecera con una celda **sin nombre** (una columna que nadie ha titulado);
    - una fila de datos con **más celdas** que la cabecera: esa columna de más es, literalmente, la
      respuesta que se coló como tercera columna (`| 137 | NetBIOS Name Service | NTP |`).
    """
    rotas: list[TablaRota] = []
    lineas = texto.splitlines()
    indice = 0
    while indice < len(lineas):
        if not _FILA_TABLA.match(lineas[indice]):
            indice += 1
            continue
        inicio = indice
        while indice < len(lineas) and _FILA_TABLA.match(lineas[indice]):
            indice += 1
        bloque = lineas[inicio:indice]
        numero = inicio + 1
        if len(bloque) < 2 or not _SEPARADOR_TABLA.match(bloque[1]) or "|" not in bloque[1]:
            rotas.append(
                TablaRota(donde, numero, "tabla sin fila de cabecera (no hay línea de separación)")
            )
            continue
        cabecera = _celdas(bloque[0])
        vacias = [posicion + 1 for posicion, celda in enumerate(cabecera) if not celda]
        if vacias:
            rotas.append(
                TablaRota(
                    donde,
                    numero,
                    f"columna(s) sin nombre en la cabecera: {', '.join(str(v) for v in vacias)}",
                )
            )
        for desplazamiento, fila in enumerate(bloque[2:], start=2):
            celdas = _celdas(fila)
            if len(celdas) != len(cabecera):
                rotas.append(
                    TablaRota(
                        donde,
                        numero + desplazamiento,
                        f"fila con {len(celdas)} celda(s) y una cabecera de {len(cabecera)} "
                        "columna(s)",
                    )
                )
    return tuple(rotas)


def _celdas(linea: str) -> list[str]:
    return [celda.strip() for celda in linea.strip().strip("|").split("|")]


def marcas_internas(texto: str) -> tuple[str, ...]:
    """Las marcas de andamio que se han quedado a la vista en el texto, tal cual aparecen."""
    return tuple(casado.group(0) for casado in _MARCA.finditer(texto))


def limpiar_andamios(texto: str) -> str:
    """El texto de los apuntes sin las marcas de andamio que el redactor copia de su encargo.

    El redactor recibe los hechos numerados (`1. [tecnico] …`) y a veces cita ese número dentro del
    texto (`… no disponen de dicha tabla. [[Hecho 36]] La ruta por defecto …`). Ese número no es
    parte de los apuntes: es la referencia al encargo, y en el texto del opositor es basura. Se
    quitan **las marcas**, nunca el contenido, y se deja el hueco con un solo espacio para que la
    frase quede legible.

    Va aquí, junto a la comprobación que las cuenta (`marcas_internas`), porque son la misma cosa
    vista desde los dos lados: lo que se mide y lo que se arregla tienen que ser la misma expresión.
    """
    sin_marcas = _MARCA.sub(" ", texto)
    # El redactor envuelve la marca en sus propios corchetes (`[[Hecho 36]]`): al quitar la marca
    # queda `[ ]`, que tampoco se lee y se retira con ella.
    sin_marcas = re.sub(r"\[\s*\]", "", sin_marcas)
    # El hueco que deja la marca no puede quedar como dos espacios ni como un espacio antes de un
    # signo: se aprieta el texto, sin tocar los saltos de línea (son los que separan los párrafos).
    lineas = [
        re.sub(r"[ \t]{2,}", " ", re.sub(r"[ \t]+([.,;:)])", r"\1", linea))
        for linea in sin_marcas.split("\n")
    ]
    return "\n".join(lineas)


def hechos_distintos(hechos: Sequence[Hecho]) -> int:
    """Cuántos hechos distintos tiene el tema, por su texto normalizado.

    Es el divisor del tope de extensión: dos hechos escritos con otras palabras son uno, y contar
    dos veces el mismo hecho es lo que hace que un tema de 150.000 palabras parezca justificado.
    """
    return len({re.sub(r"\s+", " ", normalise(hecho.text)).strip() for hecho in hechos})


# --- la revisión de un tema -----------------------------------------------------------------------


def revisar_apuntes(
    apartados: Sequence[ApartadoDeApuntes],
    hechos: Sequence[Hecho] = (),
) -> RevisionApuntes:
    """Mide el tema entero con las cinco comprobaciones y devuelve lo que no pasa.

    Las comprobaciones de forma (encabezados, marcas, tablas y repetición) miran el texto **de todo
    el tema**, no apartado a apartado: el defecto de los pilotos era justo ese, el mismo contenido
    repartido en apartados distintos. La de densidad mira el tema completo contra sus hechos.
    """
    hallazgos: list[Hallazgo] = []

    titulos: list[tuple[str, str]] = []
    todos: list[str] = []
    for apartado in apartados:
        todos.append(apartado.body_markdown)
        # El título del apartado repetido como encabezado **de su propio texto** no es un apartado
        # escrito dos veces: es cómo se titula. Se perdona **una vez**; a partir de la segunda sí
        # cuenta, porque ahí ya se está repitiendo el apartado dentro de sí mismo.
        titulos.extend(_encabezados_del_apartado(apartado))
    # El título del apartado es un encabezado más: el esquema lo pone él y se repite en el tema.
    titulos.extend((apartado.anchor, apartado.title) for apartado in apartados)
    texto = "\n\n".join(todos)

    repetidos = _titulos_repetidos(titulos)
    if repetidos:
        hallazgos.append(
            Hallazgo(
                ENCABEZADOS_REPETIDOS,
                len(repetidos),
                f"{len(repetidos)} encabezado(s) repetidos o casi iguales dentro del tema "
                f"(mismo título, o parecido ≥ {SIMILITUD_ENCABEZADO:g})",
                tuple(f"{clave}: «{titulo}»" for clave, titulo in repetidos),
            )
        )

    # El otro defecto de los pilotos, y el que no caza el anterior: no es el mismo encabezado, son
    # muchos apartados distintos con la misma cabecera (IV.7.2 tenía 19 titulados «Protocolos
    # TCP/IP: …»). Cada uno con su texto, así que comparar títulos no los ve: lo que se ve es que un
    # epígrafe se ha partido en trozos y cada trozo se ha titulado por su cuenta.
    cabeceras = _misma_cabecera(apartados)
    if cabeceras:
        hallazgos.append(
            Hallazgo(
                CABECERAS_REPETIDAS,
                sum(len(claves) for claves, _ in cabeceras),
                f"{len(cabeceras)} cabecera(s) compartidas por {MINIMO_MISMA_CABECERA} o más "
                f"apartados del tema (las {PALABRAS_DE_CABECERA} primeras palabras del título)",
                tuple(
                    f"«{' '.join(cabecera)}» en {', '.join(claves[:4])}"
                    for claves, cabecera in cabeceras
                ),
            )
        )

    marcas = marcas_internas(texto)
    if marcas:
        hallazgos.append(
            Hallazgo(
                MARCAS_INTERNAS,
                len(marcas),
                f"{len(marcas)} marca(s) interna(s) a la vista en el texto",
                tuple(dict.fromkeys(marcas)),
            )
        )

    rotas = [
        rota
        for apartado in apartados
        for rota in tablas_rotas(apartado.key, apartado.body_markdown)
    ]
    if rotas:
        hallazgos.append(
            Hallazgo(
                TABLAS_SIN_CABECERA,
                len(rotas),
                f"{len(rotas)} tabla(s) sin cabecera utilizable",
                tuple(f"{rota.donde}:{rota.fila} {rota.motivo}" for rota in rotas),
            )
        )

    # La tabla de puertos, que es una comprobación de contenido y no de forma: el propietario
    # levantó los dos defectos que mide esto. Se aplica a cualquier tema que tenga una tabla con
    # una columna de puerto, no solo a IV.7: la comprobación es del texto, no del tema.
    for apartado in apartados:
        tablas = tablas_de_puertos(apartado.body_markdown)
        if not tablas:
            continue
        malas = notas_sin_sentido(apartado.body_markdown)
        if malas:
            hallazgos.append(
                Hallazgo(
                    NOTAS_DE_PUERTOS,
                    len(malas),
                    f"{len(malas)} nota(s) de la tabla de puertos solo dicen lo que un puerto "
                    "**no** es: vienen de los distractores de una pregunta, no de una confusión "
                    "de estudio (la columna de notas explica el puerto)",
                    tuple(malas[:8]),
                )
            )
        familias = familias_de_la_tabla(apartado.body_markdown)
        repetidos_en_tablas = puertos_repetidos(apartado.body_markdown)
        if len(tablas) < 2 or "" in familias or repetidos_en_tablas:
            hallazgos.append(
                Hallazgo(
                    FAMILIAS_DE_PUERTOS,
                    max(1, len(repetidos_en_tablas)),
                    f"la tabla de puertos de {apartado.key} no está partida por familias: "
                    f"{len(tablas)} tabla(s), familias reconocidas {familias or 'ninguna'}, "
                    f"{len(repetidos_en_tablas)} puerto(s) repetidos entre tablas",
                    tuple(f"{apartado.key}:{puerto}" for puerto in repetidos_en_tablas[:8]),
                )
            )

    bloques = parrafos(texto)
    comparables = [bloque for bloque in bloques if len(bloque.split()) >= MINIMO_PALABRAS_PARRAFO]
    repetidos_parrafos = _parrafos_repetidos(comparables)
    porcentaje = 0.0 if not bloques else repetidos_parrafos / len(bloques)
    if porcentaje > MAX_PARRAFOS_REPETIDOS:
        hallazgos.append(
            Hallazgo(
                PARRAFOS_REPETIDOS,
                repetidos_parrafos,
                f"{100 * porcentaje:.1f} % de los párrafos se parecen a otro anterior "
                f"(tope {100 * MAX_PARRAFOS_REPETIDOS:.0f} %, parecido ≥ {SIMILITUD_PARRAFO:g})",
            )
        )

    palabras = len(texto.split())
    distintos = hechos_distintos(hechos)
    limite = MAX_PALABRAS_POR_HECHO * max(distintos, 1)
    if hechos and palabras > limite:
        hallazgos.append(
            Hallazgo(
                DENSIDAD,
                palabras - limite,
                f"{palabras} palabra(s) para {distintos} hecho(s) distintos: el tope es "
                f"{MAX_PALABRAS_POR_HECHO} x {distintos} = {limite}",
            )
        )

    return RevisionApuntes(
        apartados=len(apartados),
        palabras=palabras,
        hechos=distintos,
        parrafos=len(bloques),
        parrafos_repetidos=repetidos_parrafos,
        hallazgos=tuple(hallazgos),
    )


def _titulos_repetidos(titulos: Sequence[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
    """Los encabezados que ya habían salido antes, normalizados iguales o casi iguales.

    Se compara cada uno con los anteriores y se devuelve el repetido con su sitio. Un tema con
    veinte encabezados iguales devuelve veinte filas (una por repetido), que es la cuenta que el
    propietario quiere ver.
    """
    vistos: list[str] = []
    repetidos: list[tuple[str, str]] = []
    for clave, titulo in titulos:
        limpio = _normalizado(titulo)
        if not limpio:
            continue
        if any(
            anterior == limpio or parecido(anterior, limpio) >= SIMILITUD_ENCABEZADO
            for anterior in vistos
        ):
            repetidos.append((clave, titulo))
            continue
        vistos.append(limpio)
    return tuple(repetidos)


def _misma_cabecera(
    apartados: Sequence[ApartadoDeApuntes],
) -> tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]:
    """Los grupos de apartados cuyos títulos empiezan por las mismas palabras.

    Devuelve `(claves, cabecera)` por cada grupo de `MINIMO_MISMA_CABECERA` o más apartados, en
    orden de aparición. Es la comprobación del epígrafe partido en trozos: IV.7.2 tenía 19 apartados
    titulados «Protocolos TCP/IP: …», y cada uno era un lote de hechos con su texto.
    """
    grupos: dict[tuple[str, ...], list[str]] = {}
    for apartado in apartados:
        palabras = _palabras_del_titulo(apartado.title)
        if len(palabras) < PALABRAS_DE_CABECERA:
            continue
        grupos.setdefault(tuple(palabras[:PALABRAS_DE_CABECERA]), []).append(apartado.key)
    return tuple(
        (tuple(claves), cabecera)
        for cabecera, claves in grupos.items()
        if len(claves) >= MINIMO_MISMA_CABECERA
    )


def _palabras_del_titulo(titulo: str) -> list[str]:
    return [palabra for palabra in re.split(r"[^0-9a-z/]+", normalise(titulo)) if palabra]


def _parrafos_repetidos(bloques: Sequence[str]) -> int:
    """Cuántos párrafos se parecen a alguno de los anteriores.

    El tema grande ronda los dos mil párrafos y comparar todos con todos son cuatro millones de
    intersecciones de conjuntos de trigramas. Con un índice de trigrama → párrafos solo se cuentan
    los que comparten alguno, y antes de calcular el parecido se descarta lo que no puede llegar al
    umbral: hacen falta al menos `SIMILITUD_PARRAFO` veces el mayor de los dos conjuntos.
    """
    repetidos = 0
    guardados: list[frozenset[str]] = []
    indice: dict[str, list[int]] = {}
    for bloque in bloques:
        suyos = trigramas(bloque)
        if not suyos:
            continue
        compartidos: dict[int, int] = {}
        for trigrama in suyos:
            for anterior in indice.get(trigrama, ()):
                compartidos[anterior] = compartidos.get(anterior, 0) + 1
        repetido = False
        for anterior, comunes in compartidos.items():
            ajenos = guardados[anterior]
            if comunes < SIMILITUD_PARRAFO * max(len(suyos), len(ajenos)):
                continue
            if comunes / len(suyos | ajenos) >= SIMILITUD_PARRAFO:
                repetido = True
                break
        if repetido:
            repetidos += 1
            continue
        posicion = len(guardados)
        guardados.append(suyos)
        for trigrama in suyos:
            indice.setdefault(trigrama, []).append(posicion)
    return repetidos


__all__ = [
    "CABECERAS_REPETIDAS",
    "DENSIDAD",
    "ENCABEZADOS_REPETIDOS",
    "MARCAS_INTERNAS",
    "MAX_PALABRAS_POR_HECHO",
    "MAX_PARRAFOS_REPETIDOS",
    "MINIMO_MISMA_CABECERA",
    "MINIMO_PALABRAS_PARRAFO",
    "PALABRAS_DE_CABECERA",
    "PARRAFOS_REPETIDOS",
    "SIMILITUD_ENCABEZADO",
    "SIMILITUD_PARRAFO",
    "TABLAS_SIN_CABECERA",
    "ApartadoDeApuntes",
    "Hallazgo",
    "RevisionApuntes",
    "TablaRota",
    "encabezados",
    "hechos_distintos",
    "limpiar_andamios",
    "marcas_internas",
    "parecido",
    "parrafos",
    "revisar_apuntes",
    "tablas_rotas",
    "trigramas",
]
