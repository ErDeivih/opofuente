"""La tabla de puertos: sus familias, sus notas y las confusiones que de verdad se caen.

El propietario levantó dos defectos en la tabla de puertos de IV.7, y los dos son el mismo: la tabla
se escribió como una lista de 47 filas con la columna de notas llena de «no es X» —«6000 X11 — No es
DynamoDB», «3000 Grafana — No es MySQL»—, que salen de las **opciones falsas de una pregunta** y no
de una confusión que tenga un alumno. Y son 47 filas seguidas: demasiado larga para memorizarla.

Aquí se arreglan las dos cosas, y se arreglan **sin volver a pedirle nada al modelo**:

1. **la tabla se parte por familias** (`FAMILIAS`): servicios de red, correo, bases de datos y
   escritorio remoto y otros. Se reescribe la misma tabla, la misma información, en una tabla por
   familia, ordenada por número de puerto;
2. **las notas explican el puerto**; lo que solo dice lo que el puerto **no** es se retira, y los
   pares que se confunden de verdad —mismo servicio con y sin cifrar, cliente y servidor, control y
   datos, números parecidos o el mismo número en otro transporte— se recogen al final, en
   «Confusiones que caen».

Lo que no es una confusión real **se va**, que es lo que pidió el propietario. Es una decisión de
contenido tomada una vez y aplicada a todos los temas: la misma que se le da al redactor en las
instrucciones, y la misma que comprueba la puerta.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from opofuente.domain.rag import normalise

#: Título del bloque final de confusiones. Es una sección de verdad, no una nota al pie.
TITULO_CONFUSIONES = "Confusiones que caen"


@dataclass(frozen=True, slots=True)
class FamiliaDePuertos:
    """Una familia de la tabla: su título y los puertos que le tocan.

    Los puertos son un dato del temario, no una heurística: la familia de una fila es la de su
    primer puerto, y un puerto que no esté en ninguna lista cae en «Otros servicios». Así la tabla
    se parte igual siempre y se puede revisar de un vistazo.
    """

    key: str
    title: str
    resumen: str
    puertos: frozenset[int] = frozenset()


#: Las familias, en el orden en que se enseñan. La última recoge lo que no es de las otras.
FAMILIAS: tuple[FamiliaDePuertos, ...] = (
    FamiliaDePuertos(
        key="servicios-de-red",
        title="Servicios de red",
        resumen="Los servicios básicos de Internet y del sistema: ficheros, acceso, nombres, web, "
        "gestión y los clásicos de la red local.",
        puertos=frozenset(
            {
                20,
                21,
                22,
                23,
                53,
                67,
                68,
                69,
                80,
                88,
                111,
                123,
                137,
                138,
                139,
                161,
                162,
                443,
                445,
                546,
                547,
                860,
                989,
                990,
                3260,
            }
        ),
    ),
    FamiliaDePuertos(
        key="correo",
        title="Correo",
        resumen="El envío (SMTP y submission) y la recogida (POP3 e IMAP), cada uno con su versión "
        "cifrada.",
        puertos=frozenset({25, 110, 143, 465, 587, 993, 995, 2525}),
    ),
    FamiliaDePuertos(
        key="bases-de-datos",
        title="Bases de datos",
        resumen="Los gestores relacionales, los de documentos y los almacenes en memoria.",
        puertos=frozenset(
            {
                1433,
                1521,
                1527,
                3306,
                5432,
                6379,
                7000,
                7001,
                7473,
                7474,
                7687,
                8000,
                9042,
                9160,
                27017,
            }
        ),
    ),
    FamiliaDePuertos(
        key="escritorio-remoto",
        title="Escritorio remoto y otros",
        resumen="El acceso gráfico a otro equipo y los servicios que no son de las familias "
        "anteriores.",
        puertos=frozenset({3000, 3389, 5200, 5900, 5901, 5902, 5938, 5990, 6000}),
    ),
    FamiliaDePuertos(
        key="otros-servicios",
        title="Otros servicios",
        resumen="Lo que no es de ninguna de las familias anteriores: se lista igual, y no se "
        "inventa una familia para dos puertos.",
    ),
)

#: La familia que recoge lo que no está en ninguna lista. Es la última declarada.
FAMILIA_POR_DEFECTO = FAMILIAS[-1].key

#: Una fila de tabla de markdown.
_FILA = re.compile(r"^\s*\|.*\|\s*$")
#: La línea de separación de la tabla.
_SEPARADOR = re.compile(r"^\s*\|?[\s:|-]*-[\s:|-]*\|?\s*$")
#: Un encabezado de markdown, para saber a qué familia pertenece la tabla que viene debajo.
_ENCABEZADO = re.compile(r"^\s*#{2,6}\s+(.*\S)\s*$")
#: El número de puerto al principio del texto de una celda: `20/TCP`, `137, 138 y 139`, `547/UDP`.
_PUERTO = re.compile(r"\b(\d{1,5})\b")
#: La cabecera de una tabla de puertos: la columna del número.
_CABECERA_PUERTO = re.compile(r"puerto", re.IGNORECASE)
#: Una negación que descarta **otro** servicio: «no es Telnet», «no a FTPS», «no el 990». También
#: al principio de la celda, que es como están la mitad de las notas que se retiran («No es POP3»).
_NEGACION = re.compile(
    r"(?P<cola>(?:^|,\s*|\s+)(?:y\s+)?(?:no|ni)\s+"
    r"(?:es|son|a|al|el|en\s+el|se\s+corresponde|corresponde|pertenece|usa|usan|negocia)\b.*)$",
    re.IGNORECASE,
)
#: El sufijo que marca «cifrado» en el nombre de un servicio: FTPS es FTP, POP3S es POP3…
_SUFIJO_CIFRADO = re.compile(r"(s|tls|ssl)$")

LETRAS = re.compile(r"[^0-9a-z]+")


def familia_de(puerto: int) -> str:
    """La clave de la familia de un puerto, o la familia por defecto si no está en ninguna lista."""
    for familia in FAMILIAS:
        if puerto in familia.puertos:
            return familia.key
    return FAMILIA_POR_DEFECTO


def titulo_de_familia(clave: str) -> str:
    return next((familia.title for familia in FAMILIAS if familia.key == clave), clave)


def familia_de_un_titulo(titulo: str) -> str:
    """Qué familia nombra un encabezado. Cadena vacía si no nombra ninguna.

    Se compara contra el título de cada familia sobre el texto normalizado: un encabezado que dice
    «Servicios de red (FTP, SSH, HTTP…)» nombra la familia de servicios de red.
    """
    limpio = normalise(titulo)
    for familia in FAMILIAS:
        if normalise(familia.title) in limpio:
            return familia.key
    return ""


@dataclass(frozen=True, slots=True)
class FilaDePuertos:
    """Una fila de la tabla: su número de puerto (el primero), su servicio y su nota."""

    puerto: int
    puerto_texto: str
    servicio: str
    nota: str

    @property
    def familia(self) -> str:
        return familia_de(self.puerto)


@dataclass(frozen=True, slots=True)
class TablaDePuertos:
    """Una tabla de puertos localizada en un texto, con las líneas que ocupa."""

    desde: int
    hasta: int
    titulo: str
    filas: tuple[FilaDePuertos, ...]


@dataclass(frozen=True, slots=True)
class LimpiezaDePuertos:
    """Lo que se ha hecho con la tabla: el texto nuevo y la cuenta de lo que se ha ido.

    `confusiones` son los pares que se han llevado al bloque final por ser confusiones de verdad;
    `descartadas`, las notas que solo decían lo que el puerto **no** es y que se han ido. Los dos
    números se enseñan: un arreglo que no se puede contar no se puede revisar.
    """

    texto: str
    tablas: int
    filas: int
    notas_retiradas: int
    confusiones: tuple[str, ...] = ()
    descartadas: tuple[str, ...] = ()
    transformada: bool = True

    @property
    def cambio(self) -> bool:
        return self.notas_retiradas > 0 or len(self.confusiones) > 0 or self.tablas > 1


def _celdas(linea: str) -> list[str]:
    return [celda.strip() for celda in linea.strip().strip("|").split("|")]


def es_cabecera_de_puertos(celdas: list[str]) -> bool:
    """¿Esta fila es la cabecera de una tabla de puertos? Lo dice su primera columna."""
    return bool(celdas) and bool(_CABECERA_PUERTO.search(celdas[0]))


def tablas_de_puertos(texto: str) -> tuple[TablaDePuertos, ...]:
    """Las tablas de puertos del texto, con sus filas.

    Una tabla de puertos es una tabla de markdown cuya primera columna se llama «puerto…» y tiene
    fila de separación. Lo que no se puede leer como puerto **no** se inventa: la tabla se da por no
    transformable.
    """
    lineas = texto.split("\n")
    tablas: list[TablaDePuertos] = []
    indice = 0
    while indice < len(lineas):
        if not _FILA.match(lineas[indice]):
            indice += 1
            continue
        inicio = indice
        while indice < len(lineas) and _FILA.match(lineas[indice]):
            indice += 1
        bloque = lineas[inicio:indice]
        if len(bloque) < 3 or not _SEPARADOR.match(bloque[1]):
            continue
        celdas = _celdas(bloque[0])
        if not es_cabecera_de_puertos(celdas):
            continue
        filas: list[FilaDePuertos] = []
        for linea in bloque[2:]:
            suyas = _celdas(linea)
            if len(suyas) < 2:
                filas = []
                break
            numero = _PUERTO.search(suyas[0])
            if numero is None:
                filas = []
                break
            filas.append(
                FilaDePuertos(
                    puerto=int(numero.group(1)),
                    puerto_texto=suyas[0],
                    servicio=suyas[1],
                    nota=suyas[2] if len(suyas) > 2 else "",
                )
            )
        if not filas:
            continue
        tablas.append(
            TablaDePuertos(
                desde=inicio,
                hasta=indice,
                titulo=_titulo_anterior(lineas, inicio),
                filas=tuple(filas),
            )
        )
    return tuple(tablas)


def _titulo_anterior(lineas: list[str], desde: int) -> str:
    """El encabezado que manda sobre una tabla: el último `###` por encima de ella."""
    for posicion in range(desde - 1, -1, -1):
        if not lineas[posicion].strip():
            continue
        casado = _ENCABEZADO.match(lineas[posicion])
        if casado is not None:
            return casado.group(1).strip()
        # Cualquier otra línea con texto corta la búsqueda: el encabezado tiene que estar pegado.
        return ""
    return ""


#: Palabras que dicen el **papel** del puerto y no su servicio: dos puertos que solo comparten
#: «servidor», «conexión» o «TLS» no se confunden por eso.
_PALABRAS_DE_PAPEL = frozenset(
    {
        "servidor",
        "servidores",
        "cliente",
        "clientes",
        "servicio",
        "servicios",
        "puerto",
        "puertos",
        "conexion",
        "conexiones",
        "sobre",
        "canal",
        "con",
        "sin",
        "tls",
        "ssl",
        "cifrado",
        "cifrada",
        "implicito",
        "explicita",
        "explicito",
        "alternativo",
        "oficial",
        "primera",
        "adicionales",
        "base",
        "de",
        "del",
        "la",
        "el",
        "los",
        "las",
        "y",
        "e",
        "o",
        "u",
        "en",
        "para",
        "por",
        "un",
        "una",
        "al",
        "se",
        "su",
        "sus",
        "que",
    }
)


def clave_de_servicio(nombre: str) -> frozenset[str]:
    """Las dos primeras palabras significativas de un servicio, con el plural doblado.

    Es lo que hace comparables «SMTP» y «SMTPS, SMTP sobre SSL/TLS…» (los dos son `smtp`) y lo que
    deja fuera un «HTTPS» que aparece al final del nombre de otro servicio: no es de lo que habla.
    """
    palabras = [
        palabra
        for palabra in LETRAS.split(normalise(nombre))
        if len(palabra) >= 3 and palabra not in _PALABRAS_DE_PAPEL
    ]
    dobladas = [
        palabra[:-1] if palabra.endswith("s") and len(palabra) > 3 else palabra
        for palabra in palabras
    ]
    return frozenset(dobladas[:2])


def es_confusion_real(puerto: int, otro_puerto: int, uno: str, otro: str) -> bool:
    """¿Este par se confunde de verdad? Solo los casos que pidió el propietario.

    1. **el mismo servicio con y sin cifrar**: FTP y FTPS, SMTP y SMTPS, POP3 y POP3S, IMAP e
       IMAPS (el plural se dobla: `https` es `http`, `smtps` es `smtp`);
    2. **el mismo servicio con otro papel**: cliente y servidor (DHCP 67/68, DHCPv6 546/547) y
       control y datos (FTP 20/21, FTPS 989/990), emparejando el papel cuando los dos lo dicen;
    3. **números parecidos** del mismo servicio (546 y 547, 989 y 990, 7473 y 7474).

    Cualquier otra cosa —Oracle frente a MySQL, VNC frente a TeamViewer, X11 frente a DynamoDB, 110
    frente a 111— no es una confusión de estudio: es el distractor de una pregunta, y se va.
    """
    clave_uno = clave_de_servicio(uno)
    clave_otro = clave_de_servicio(otro)
    if not clave_uno or not clave_otro:
        return False
    if normalise(uno).strip() == normalise(otro).strip():
        return True
    if not (clave_uno & clave_otro):
        return False
    # Cuando los dos hablan del mismo servicio y dicen su papel, el papel importa: el 20 es el canal
    # de datos de FTP y el 21 el de control (esos dos **sí** se confunden, y son consecutivos), pero
    # el 20 no se confunde con el 990, que es el control de FTPS y está a setecientos números.
    if _papel(uno) in ("datos", "control") and _papel(otro) in ("datos", "control"):
        if _papel(uno) == _papel(otro):
            return True
        return abs(puerto - otro_puerto) <= 2
    return True


def _papel(nombre: str) -> str:
    limpio = normalise(nombre)
    for papel in ("datos", "control", "cliente", "servidor"):
        if papel in limpio:
            return papel
    return ""


#: Tope de líneas de «Confusiones que caen»: una lista de cuarenta pares no se memoriza.
MAX_CONFUSIONES = 24


def confusiones_de_la_tabla(filas: Sequence[FilaDePuertos]) -> tuple[str, ...]:
    """Los pares de la propia tabla que se confunden de verdad, en orden de número de puerto.

    No es una lista inventada: sale de las filas que ya están escritas. Es el sitio de memoria que
    pidió el propietario, separado de la tabla para que la tabla pueda explicar cada puerto sin
    ruido.
    """
    lineas: list[str] = []
    ordenadas = sorted(filas, key=lambda fila: fila.puerto)
    for posicion, una in enumerate(ordenadas):
        for otra in ordenadas[posicion + 1 :]:
            if una.puerto == otra.puerto:
                continue
            if not es_confusion_real(una.puerto, otra.puerto, una.servicio, otra.servicio):
                continue
            lineas.append(f"**{una.puerto} {una.servicio}** y **{otra.puerto} {otra.servicio}**")
            if len(lineas) >= MAX_CONFUSIONES:
                return tuple(dict.fromkeys(lineas))
    return tuple(dict.fromkeys(lineas))


def _limpiar_nota(nota: str, fila: FilaDePuertos) -> tuple[str, str | None]:
    """La nota sin las negaciones de otros servicios. Devuelve `(nota_limpia, descartado)`.

    Se corta la **cola** negativa de cada trozo separado por `;` y se quedan las afirmaciones que
    explican el puerto. Si al cortar no queda nada que explique el puerto (ni una cifra ni una
    palabra del propio servicio), el trozo se va entero: «Sus puertos por defecto no son el 5990 ni
    el 5200» no dice nada de TeamViewer, dice lo que no es.
    """
    descartados: list[str] = []
    trozos: list[str] = []
    for trozo in nota.split(";"):
        casado = _NEGACION.search(trozo)
        if casado is None:
            trozos.append(trozo.strip())
            continue
        cola = casado.group("cola").strip()
        cabeza = trozo[: casado.start()].strip()
        descartados.append(cola.strip(" ,;."))
        if _explica(cabeza, fila):
            trozos.append(cabeza)
    limpia = "; ".join(trozo for trozo in trozos if trozo).strip(" ;,")
    unicos = "; ".join(dict.fromkeys(descartados))
    return limpia, (unicos or None)


def _explica(cabeza: str, fila: FilaDePuertos) -> bool:
    """¿Lo que queda explica el puerto? Una cifra o una palabra de su propio servicio, sí."""
    if len(cabeza.split()) < 3:
        return False
    if _PUERTO.search(cabeza) is not None:
        return True
    suyas = {palabra for palabra in LETRAS.split(normalise(fila.servicio)) if len(palabra) > 3}
    return any(palabra in normalise(cabeza) for palabra in suyas)


def _servicios_de(cola: str) -> tuple[str, ...]:
    """Los nombres de servicio que se descartan en una cola negativa, para juzgar la confusión."""
    limpio = re.sub(
        r"^(?:,\s*|\s+)?(?:y\s+)?(?:no|ni)\s+"
        r"(?:es|son|a|al|el|en\s+el|se\s+corresponde|corresponde|pertenece|usa|usan|negocia)\s*",
        "",
        cola.strip(),
        flags=re.IGNORECASE,
    )
    limpio = re.sub(r"\b(?:ni|y)\b", ",", limpio, flags=re.IGNORECASE)
    limpio = re.sub(r"\((?:[^)]*)\)", "", limpio)
    return tuple(
        trozo.strip(" ,.;")
        for trozo in limpio.split(",")
        if len(trozo.strip(" ,.;")) > 2 and _PUERTO.search(trozo) is None
    )


def limpiar_tabla_de_puertos(texto: str) -> LimpiezaDePuertos:
    """Parte la tabla de puertos por familias y le quita las notas que no explican nada.

    Es una reescritura **de forma**: los mismos puertos, los mismos servicios y las mismas notas, en
    una tabla por familia y ordenados por número. Lo único que se va es lo que solo decía lo que el
    puerto no es, y los pares que se confunden de verdad se recogen al final, en «Confusiones que
    caen».
    """
    tablas = tablas_de_puertos(texto)
    if not tablas:
        return LimpiezaDePuertos(texto=texto, tablas=0, filas=0, notas_retiradas=0)

    filas: list[FilaDePuertos] = []
    retiradas = 0
    confusiones: list[str] = []
    descartadas: list[str] = []
    for tabla in tablas:
        for fila in tabla.filas:
            limpia, descartado = _limpiar_nota(fila.nota, fila)
            if descartado:
                retiradas += 1
                for nombre in _servicios_de(descartado):
                    otro_puerto = _puerto_mencionado(descartado)
                    if otro_puerto is not None and es_confusion_real(
                        fila.puerto, otro_puerto, fila.servicio, nombre
                    ):
                        confusiones.append(
                            f"**{fila.puerto} {fila.servicio}** frente a {nombre} "
                            f"({otro_puerto}): se confunden por el número."
                        )
                    else:
                        aviso = f"{fila.puerto} {fila.servicio}: {descartado}"
                        if aviso not in descartadas:
                            descartadas.append(aviso)
            filas.append(FilaDePuertos(fila.puerto, fila.puerto_texto, fila.servicio, limpia))

    por_familia: dict[str, list[FilaDePuertos]] = {}
    for fila in filas:
        por_familia.setdefault(fila.familia, []).append(fila)

    # Las confusiones que caen salen de la propia tabla (las filas que ya están escritas) y, si una
    # nota retirada nombraba un par que de verdad se confunde, también. Nunca de un distractor.
    unicas = tuple(dict.fromkeys((*confusiones, *confusiones_de_la_tabla(filas))))

    bloques: list[str] = []
    for familia in FAMILIAS:
        suyas = por_familia.get(familia.key)
        if not suyas:
            continue
        bloques.append(f"#### {familia.title}\n")
        bloques.append("| Puerto / transporte | Servicio | Notas |")
        bloques.append("|---|---|---|")
        for fila in sorted(suyas, key=lambda fila: fila.puerto):
            bloques.append(f"| {fila.puerto_texto} | {fila.servicio} | {fila.nota or '—'} |")
        bloques.append("")
    if unicas:
        bloques.append(f"#### {TITULO_CONFUSIONES}\n")
        bloques.extend(f"- {confusion}" for confusion in unicas)

    lineas = texto.split("\n")
    fuera = _fuera_lo_viejo(lineas, tablas)
    principio = tablas[0].desde
    # Se inserta donde estaba la primera tabla, con lo que ya se ha borrado por delante.
    desplazamiento = sum(1 for indice in fuera if indice < principio)
    nuevas = [linea for indice, linea in enumerate(lineas) if indice not in fuera]
    posicion = principio - desplazamiento
    final = [*nuevas[:posicion], *bloques, *nuevas[posicion:]]
    return LimpiezaDePuertos(
        texto="\n".join(final),
        tablas=len(tablas),
        filas=len(filas),
        notas_retiradas=retiradas,
        confusiones=unicas,
        descartadas=tuple(descartadas),
    )


def _fuera_lo_viejo(lineas: list[str], tablas: Sequence[TablaDePuertos]) -> frozenset[int]:
    """Lo que hay que borrar antes de volver a escribir el bloque: las tablas y **lo que las
    titula**.

    Es lo que hace la limpieza repetible, y no es un detalle: en la primera versión se le pidió al
    modelo que partiera él la tabla por familias y que añadiera su bloque de confusiones, así que el
    texto traía sus propios encabezados (`#### Servicios de red`, `#### Confusiones que caen`) y el
    motor añadía los suyos. El tema acababa con el mismo encabezado dos y tres veces, y la
    comprobación de encabezados repetidos —con razón— lo decía. Aquí se borran:
    las filas de las tablas de puertos, los encabezados que nombran una familia, el encabezado de
    «Confusiones que caen» y su lista. La prosa del apartado no se toca.
    """
    fuera: set[int] = set()
    for tabla in tablas:
        fuera.update(range(tabla.desde, tabla.hasta))
    indice = 0
    while indice < len(lineas):
        casado = _ENCABEZADO.match(lineas[indice])
        if casado is not None and (
            familia_de_un_titulo(casado.group(1)) or _es_el_titulo_de_confusiones(casado.group(1))
        ):
            # El encabezado y, si es el de las confusiones, su lista entera.
            fuera.add(indice)
            if _es_el_titulo_de_confusiones(casado.group(1)):
                siguiente = indice + 1
                while siguiente < len(lineas):
                    limpia = lineas[siguiente].strip()
                    if not limpia or limpia.startswith(("-", "*")):
                        fuera.add(siguiente)
                        siguiente += 1
                        continue
                    break
        indice += 1
    return frozenset(fuera)


def _es_el_titulo_de_confusiones(titulo: str) -> bool:
    return normalise(TITULO_CONFUSIONES) in normalise(titulo)


def _puerto_mencionado(texto: str) -> int | None:
    """El primer número de la cola negativa, si lo hay: es el puerto con el que se confunde."""
    casado = _PUERTO.search(texto)
    return None if casado is None else int(casado.group(1))


def notas_sin_sentido(texto: str) -> tuple[str, ...]:
    """Las notas de tabla que solo dicen lo que un puerto **no** es. La puerta exige cero.

    Es la comprobación del defecto del propietario: «6000 X11 — No es DynamoDB» viene de una opción
    falsa de una pregunta, no de una confusión de estudio, y en la tabla no pinta nada.
    """
    malas: list[str] = []
    for tabla in tablas_de_puertos(texto):
        for fila in tabla.filas:
            if _NEGACION.search(fila.nota) is not None:
                malas.append(
                    f"{tabla.titulo or 'tabla'}: {fila.puerto} {fila.servicio} → {fila.nota}"
                )
    return tuple(malas)


def familias_de_la_tabla(texto: str) -> tuple[str, ...]:
    """Las familias que la tabla de puertos tiene declaradas, en el orden en que se enseñan.

    Una tabla sin encabezado de familia cuenta como una sola familia vacía: la puerta lo lee como
    «la tabla no está partida» y lo dice.
    """
    familias: list[str] = []
    for tabla in tablas_de_puertos(texto):
        clave = familia_de_un_titulo(tabla.titulo) or ""
        if clave not in familias:
            familias.append(clave)
    return tuple(familias)


def puertos_repetidos(texto: str) -> tuple[int, ...]:
    """Puertos que salen en dos tablas distintas: partir la tabla no puede duplicar una fila."""
    vistos: dict[int, int] = {}
    for tabla in tablas_de_puertos(texto):
        for fila in tabla.filas:
            vistos[fila.puerto] = vistos.get(fila.puerto, 0) + 1
    return tuple(sorted(puerto for puerto, veces in vistos.items() if veces > 1))


def familias_para_el_prompt() -> str:
    """Las familias tal como se le dicen al redactor: los puertos que van en cada una.

    Se le pide **una sola tabla**, con todos los puertos y ordenada por número: partirla por
    familias y poner los encabezados lo hace el motor (`limpiar_tabla_de_puertos`), que lo hace
    igual siempre. Pedirle al modelo que la parta él fue un error de la primera versión: escribía
    sus propios encabezados de familia y el motor añadía los suyos, así que el tema acababa con
    «Servicios de red» dos veces y la comprobación de encabezados repetidos —con razón— lo decía.
    """
    lineas = [
        "Si el apartado es la tabla de puertos, escribe **una sola tabla** con todos los puertos, "
        "ordenada de menor a mayor, con las columnas «Puerto / transporte», «Servicio» y «Notas». "
        "**No** la partas por familias ni pongas encabezados de familia: el motor la parte "
        "después, siempre igual. Los puertos que van en cada familia son estos:"
    ]
    for familia in FAMILIAS:
        ejemplos = ", ".join(str(puerto) for puerto in sorted(familia.puertos)[:12])
        lineas.append(f"  - «{familia.title}»: {familia.resumen} (por ejemplo {ejemplos}…)")
    lineas.append(
        "La columna de notas **explica el puerto** (qué hace, en qué transporte va, de qué "
        "depende). No escribas en la tabla lo que un puerto **no** es: los distractores de una "
        "pregunta no son confusiones de estudio. Si un par se confunde de verdad —el mismo "
        "servicio con y sin cifrar (FTP y FTPS, POP3 y POP3S), cliente y servidor (DHCP 67/68, "
        "DHCPv6 546/547), control y datos (FTP 20/21, FTPS 989/990) o números parecidos—, recógelo "
        "al final en un bloque «Confusiones que caen» con una línea por par."
    )
    return "\n".join(lineas)


__all__ = [
    "FAMILIAS",
    "FAMILIA_POR_DEFECTO",
    "MAX_CONFUSIONES",
    "TITULO_CONFUSIONES",
    "FamiliaDePuertos",
    "FilaDePuertos",
    "LimpiezaDePuertos",
    "TablaDePuertos",
    "confusiones_de_la_tabla",
    "es_confusion_real",
    "familia_de",
    "familia_de_un_titulo",
    "familias_de_la_tabla",
    "familias_para_el_prompt",
    "limpiar_tabla_de_puertos",
    "notas_sin_sentido",
    "puertos_repetidos",
    "tablas_de_puertos",
    "titulo_de_familia",
]
