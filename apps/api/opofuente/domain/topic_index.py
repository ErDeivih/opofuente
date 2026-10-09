"""El índice de un tema por materias: los apartados que tendrá, en orden, **antes** de redactar.

El esquema de los pilotos salió de los lotes: un apartado por cada trozo de cuarenta hechos, en el
orden en que se pidieron. De ahí los **19 apartados «Protocolos TCP/IP: …»** de IV.7.2 (cada uno
con su tabla de puertos, distinta de las demás) y los **7 del modelo OSI** de IV.7.1. El contenido
era el mismo; lo que faltaba era la estructura.

Esto es lo contrario: un catálogo de **materias** por epígrafe, en el orden en que se estudia, y un
reparto **determinista** de los hechos y las preguntas que ya están en la base a la materia que les
toca. No llama a nadie: clasifica por las palabras del propio texto, con el vocabulario del tema,
así que el índice se puede calcular, leer y discutir antes de escribir una sola línea (que es lo
que se pidió: ver el esquema antes de redactar).

Cinco reglas, y las cinco se ven en el resultado:

1. **cada hecho y cada pregunta van a una sola materia**: la que los menciona antes (y, a igualdad,
   la de `prioridad` más baja). Se mira primero entre las materias del epígrafe del hecho y, si en
   el suyo no casa con ninguna, en el catálogo entero: hay hechos a los que el modelo puso el
   epígrafe que no era (9 en IV.7), y su contenido manda. Esos se cuentan y se dicen;
2. **el reparto mira primero lo particular**: un hecho que habla de DNS *y* del puerto 53 es un
   hecho de DNS, no de la tabla de puertos. Por eso cada materia tiene su `prioridad` de reparto,
   aparte del orden en que se enseña el índice;
3. **nada se queda sin apartado**: cada epígrafe tiene su cajón («Otros contenidos…»), donde caen
   los hechos que no son de ninguna de sus materias ni de las del otro epígrafe. En IV.7 son 22:
   preguntas de otros bloques (integridad referencial, diagramas de flujo de datos, Métrica v3, el
   registro de Windows, normativa) que se clasificaron en este tema. Se enseñan, no se esconden;
4. **la tabla de puertos tiene un solo sitio**: la materia de puertos es la única marcada con
   `tabla_unica`, y su apartado es donde vive esa tabla;
5. **el índice va en el orden oficial**: primero los epígrafes del temario y, dentro de cada uno,
   las materias en el orden en que se estudian. Ese orden está escrito aparte, en una lista de
   claves (`_ORDEN_IV7`), y es distinto del de reparto: si no lo fuera, la tabla de puertos se
   llevaría las preguntas de DNS.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from opofuente.domain.rag import normalise
from opofuente.domain.topic_notes import Hecho, QuestionGroup

#: Prioridad de reparto por defecto: se mira después de las materias con prioridad propia.
PRIORIDAD_POR_DEFECTO = 100


@dataclass(frozen=True, slots=True)
class Materia:
    """Un apartado del índice: su materia, en qué epígrafe vive y qué le toca.

    `patrones` son expresiones regulares sobre el texto **normalizado** (sin acentos, sin signos, en
    minúsculas), que es la normalización con la que se compara todo en el proyecto. `resumen` es la
    línea que se le enseña al propietario: qué entra en este apartado.

    Una materia **sin patrones** es el cajón de su epígrafe: recoge lo que no ha casado con ninguna
    otra. Cada epígrafe del catálogo tiene que tener el suyo, y solo uno.
    """

    key: str
    epigraph_code: str
    title: str
    resumen: str
    patrones: tuple[str, ...] = ()
    #: Orden de **reparto** (no el del índice): más bajo, se mira antes. Sirve para que lo
    #: particular gane a lo general (DNS antes que la tabla de puertos) sin cambiar el orden en que
    #: se enseña.
    prioridad: int = PRIORIDAD_POR_DEFECTO
    #: Si es la materia donde vive una tabla que no puede estar en dos sitios (la de puertos).
    tabla_unica: bool = False

    @property
    def es_cajon(self) -> bool:
        """¿Es el cajón del epígrafe (lo que no es de ninguna materia)?"""
        return not self.patrones


@dataclass(frozen=True, slots=True)
class RepartoMateria:
    """Lo que le ha tocado a una materia: sus hechos y los grupos de preguntas de su materia."""

    materia: Materia
    hechos: tuple[Hecho, ...]
    grupos: tuple[QuestionGroup, ...]

    @property
    def preguntas(self) -> int:
        return sum(len(grupo.questions) for grupo in self.grupos)

    def lineas(self) -> tuple[str, ...]:
        """El apartado del índice: una línea con su cuenta y otra con lo que entra."""
        marcas = " · una sola tabla en todo el tema" if self.materia.tabla_unica else ""
        return (
            f"    {self.materia.key} · {self.materia.title} — {len(self.hechos)} hecho(s), "
            f"{len(self.grupos)} grupo(s) de preguntas ({self.preguntas} pregunta(s){marcas})",
            f"        {self.materia.resumen}",
        )


@dataclass(frozen=True, slots=True)
class IndiceDelTema:
    """El índice completo: el tema, sus epígrafes y el reparto de hechos y preguntas."""

    topic_code: str
    topic_title: str
    epigraphs: tuple[tuple[str, str], ...]
    reparto: tuple[RepartoMateria, ...] = ()
    #: Hechos que han caído en el cajón de su epígrafe (no son de ninguna de sus materias).
    sin_materia: tuple[Hecho, ...] = field(default=())
    #: Hechos que se han ido a una materia del **otro** epígrafe porque es donde se estudian: el
    #: modelo les puso el epígrafe que no era, y eso es lo que hay que revisar.
    fuera_de_su_epigrafe: tuple[Hecho, ...] = field(default=())

    @property
    def hechos(self) -> int:
        return sum(len(apartado.hechos) for apartado in self.reparto)

    @property
    def grupos(self) -> int:
        return sum(len(apartado.grupos) for apartado in self.reparto)

    @property
    def preguntas(self) -> int:
        return sum(apartado.preguntas for apartado in self.reparto)

    @property
    def apartados(self) -> int:
        return len(self.reparto)

    @property
    def materias_de_la_tabla(self) -> tuple[Materia, ...]:
        return tuple(apartado.materia for apartado in self.reparto if apartado.materia.tabla_unica)

    def lines(self) -> tuple[str, ...]:
        """El índice en texto: es lo que se enseña y se discute antes de redactar."""
        lineas = [
            f"Índice por materias de [{self.topic_code}] {self.topic_title}",
            f"    {self.apartados} apartado(s) · {self.hechos} hecho(s) · {self.preguntas} "
            f"pregunta(s) en {self.grupos} grupo(s) · {len(self.epigraphs)} epígrafe(s) oficiales",
        ]
        actual = ""
        for apartado in self.reparto:
            if apartado.materia.epigraph_code != actual:
                actual = apartado.materia.epigraph_code
                titulo = dict(self.epigraphs).get(actual, "")
                lineas.append(f"  {actual} — {titulo}")
            lineas.extend(apartado.lineas())
        if self.sin_materia:
            lineas.append(
                f"    AVISO: {len(self.sin_materia)} hecho(s) caen en «Otros contenidos»: no son "
                "de ninguna materia del tema (preguntas de otros bloques que se clasificaron aquí) "
                "y se revisan antes de redactar"
            )
        if self.fuera_de_su_epigrafe:
            lineas.append(
                f"      · {len(self.fuera_de_su_epigrafe)} hecho(s) más van a una materia del otro "
                "epígrafe porque es donde se estudian: el epígrafe que traían era el que no era"
            )
        return tuple(lineas)


def _mejor_materia(limpio: str, candidatas: Sequence[Materia]) -> Materia | None:
    """La materia que menciona el texto **antes** (y, a igualdad, la de prioridad más baja).

    Es lo que hace que «DHCP es un protocolo … el servidor DNS» sea un hecho de DHCP y no de DNS: un
    hecho habla de su materia primero y de las demás después, para compararlas. Sin esa regla,
    cualquier mención de un distractor se llevaría el hecho.
    """
    mejor: tuple[int, int, Materia] | None = None
    for materia in sorted(candidatas, key=lambda materia: materia.prioridad):
        if not materia.patrones:
            continue
        posiciones = [
            casado.start()
            for patron in materia.patrones
            if (casado := re.search(patron, limpio)) is not None
        ]
        if not posiciones:
            continue
        candidato = (min(posiciones), materia.prioridad, materia)
        if mejor is None or candidato[:2] < mejor[:2]:
            mejor = candidato
    return None if mejor is None else mejor[2]


def materia_de(texto: str, epigraph_code: str | None, materias: Sequence[Materia]) -> Materia:
    """A qué materia va un texto.

    Se busca primero entre las materias **de su epígrafe** (un hecho de IV.7.1 se queda en IV.7.1)
    y, si en el suyo no casa con ninguna, se busca en el catálogo entero: hay hechos a los que el
    modelo puso el epígrafe que no era (9 en IV.7: capas de OSI etiquetadas como IV.7.2), y su
    contenido manda, porque su sitio es donde se estudia. Esos se cuentan aparte y se dicen. Lo que
    no casa con nada —preguntas de otros bloques— cae en el cajón de su epígrafe.
    """
    suyas = tuple(materia for materia in materias if materia.epigraph_code == epigraph_code)
    limpio = normalise(texto)
    encontrada = _mejor_materia(limpio, suyas) if suyas else None
    if encontrada is None:
        encontrada = _mejor_materia(limpio, tuple(m for m in materias if not m.es_cajon))
    if encontrada is not None:
        return encontrada
    return next(
        (materia for materia in suyas if materia.es_cajon),
        next(materia for materia in materias if materia.es_cajon),
    )


def _texto_de_grupo(grupo: QuestionGroup) -> str:
    """De un grupo de preguntas se clasifica el **enunciado**: las opciones traen los distractores
    (NTP, DNS, 137) y clasificar por ellos mandaría la pregunta a la materia del distractor."""
    return grupo.representative.stem


def repartir_hechos(hechos: Sequence[Hecho], materias: Sequence[Materia]) -> dict[str, list[Hecho]]:
    """Los hechos de cada materia, por su clave. Los cajones se llevan lo que no casa con nada."""
    por_clave: dict[str, list[Hecho]] = {materia.key: [] for materia in materias}
    for hecho in hechos:
        por_clave[materia_de(hecho.text, hecho.epigraph_code, materias).key].append(hecho)
    return por_clave


def repartir_grupos(
    grupos: Sequence[QuestionGroup], materias: Sequence[Materia]
) -> dict[str, list[QuestionGroup]]:
    """Los grupos de preguntas de cada materia, por su clave."""
    por_clave: dict[str, list[QuestionGroup]] = {materia.key: [] for materia in materias}
    for grupo in grupos:
        epigrafe = grupo.epigraph_code or grupo.representative.epigraph_code
        por_clave[materia_de(_texto_de_grupo(grupo), epigrafe, materias).key].append(grupo)
    return por_clave


def validar_catalogo(topic_code: str, materias: Sequence[Materia]) -> None:
    """Un catálogo mal formado se dice antes de repartir nada, no se descubre en el resultado.

    Dos invariantes: cada epígrafe con materias tiene **un solo** cajón, y el cajón no tiene
    patrones (si los tuviera, dejaría de recoger lo que no casa con nada).
    """
    por_epigrafe: dict[str, list[Materia]] = {}
    for materia in materias:
        por_epigrafe.setdefault(materia.epigraph_code, []).append(materia)
    claves = [materia.key for materia in materias]
    if len(set(claves)) != len(claves):
        raise ValueError(f"el catálogo de {topic_code} tiene claves de materia repetidas")
    for epigrafe, suyas in por_epigrafe.items():
        cajones = [materia for materia in suyas if materia.es_cajon]
        if len(cajones) != 1:
            raise ValueError(
                f"el epígrafe {epigrafe} de {topic_code} tiene {len(cajones)} cajones y tiene que "
                "tener exactamente uno"
            )


def indice_de(
    *,
    topic_code: str,
    topic_title: str,
    epigraphs: Sequence[tuple[str, str]],
    hechos: Sequence[Hecho] = (),
    grupos: Sequence[QuestionGroup] = (),
) -> IndiceDelTema:
    """El índice del tema con el catálogo de sus epígrafes. Falla si el tema no tiene catálogo.

    Un catálogo de materias es una decisión de contenido: inventarlo a medias para un tema que no se
    ha definido sería escribir apuntes a ciegas. Los temas sin catálogo se dicen, no se inventan.
    """
    materias = catalogo(topic_code)
    if materias is None:
        raise KeyError(topic_code)
    validar_catalogo(topic_code, materias)
    conocidos = {codigo for codigo, _ in epigraphs}
    for materia in materias:
        if materia.epigraph_code not in conocidos:
            raise ValueError(
                f"la materia «{materia.key}» apunta al epígrafe {materia.epigraph_code}, que no "
                f"está en el temario de {topic_code}"
            )
    por_materia_hechos = repartir_hechos(hechos, materias)
    por_materia_grupos = repartir_grupos(grupos, materias)
    reparto = tuple(
        RepartoMateria(
            materia=materia,
            hechos=tuple(por_materia_hechos[materia.key]),
            grupos=tuple(por_materia_grupos[materia.key]),
        )
        for materia in materias
    )
    sin_materia = tuple(
        hecho for apartado in reparto if apartado.materia.es_cajon for hecho in apartado.hechos
    )
    return IndiceDelTema(
        topic_code=topic_code,
        topic_title=topic_title,
        epigraphs=tuple(epigraphs),
        reparto=reparto,
        sin_materia=sin_materia,
        fuera_de_su_epigrafe=tuple(
            hecho
            for apartado in reparto
            if not apartado.materia.es_cajon
            for hecho in apartado.hechos
            if hecho.epigraph_code != apartado.materia.epigraph_code
        ),
    )


# --- el catálogo de IV.7 --------------------------------------------------------------------------

#: IV.7, por epígrafes y **en el orden en que se estudia** (el que se enseña). El orden del reparto
#: es otro y va en `prioridad`: un hecho que habla de POP3 y del puerto 110 es un hecho de correo,
#: no de la tabla de puertos, así que los protocolos se reparten antes que la tabla de puertos.
_MATERIAS_IV7: tuple[Materia, ...] = (
    # --- IV.7.1: el modelo de referencia y la arquitectura
    Materia(
        key="tcpip-arquitectura",
        epigraph_code="IV.7.1",
        title="La arquitectura TCP/IP: capas, protocolos y su comparación con OSI",
        resumen=(
            "Qué es TCP/IP como familia de protocolos, sus cuatro capas (acceso a la red, "
            "internet, transporte y aplicación), qué protocolos van en cada una, protocolos de "
            "usuario y de soporte, y la correspondencia capa a capa con el modelo OSI."
        ),
        patrones=(
            r"tcp ip",
            r"\barquitectura\b",
            r"capa de internet",
            r"acceso a la red",
            r"protocolos? de (usuario|soporte)",
            r"\benrutable\b",
            r"familia de protocolos",
            r"\bcuatro capas\b",
            r"\bconectividad extremo a extremo\b",
        ),
        prioridad=10,
    ),
    Materia(
        key="osi-modelo",
        epigraph_code="IV.7.1",
        title="El modelo OSI de ISO: las siete capas y sus unidades de datos",
        resumen=(
            "El modelo de referencia de ISO: qué es un sistema abierto, el orden y la función de "
            "las siete capas (física, enlace, red, transporte, sesión, presentación y aplicación), "
            "las subcapas LLC y MAC, la PDU de cada nivel (bit, trama, paquete, segmento), el "
            "encapsulado y los dispositivos que operan en cada capa."
        ),
        patrones=(
            r"\bosi\b",
            r"\biso\b",
            r"sistema abierto",
            r"\bsubcapa",
            r"\bllc\b",
            r"\bmac\b",
            r"\bpdu\b",
            r"\btramas?\b",
            r"\bsegmentos?\b",
            r"\bpaquetes?\b",
            r"capa (1|2|3|4|5|6|7|fisica|enlace|de enlace|red|transporte|sesion|presentacion|"
            r"aplicacion)",
            r"nivel (1|2|3|4|5|6|7|fisico|de enlace|red|transporte|sesion|presentacion|aplicacion)",
            r"\bpresentacion\b",
            r"\bsesion\b",
            r"\bencapsul",
            r"\binteroperabilidad\b",
            r"\bcapas?\b",
        ),
        prioridad=20,
    ),
    Materia(
        key="conceptos-del-modelo",
        epigraph_code="IV.7.1",
        title="Servicio, protocolo, interfaz y comunicación entre capas",
        resumen=(
            "El vocabulario del modelo: qué es un servicio y una primitiva, qué es un protocolo, "
            "la interfaz entre capas adyacentes, la comunicación vertical y horizontal (virtual), "
            "la multiplexación y las técnicas de nivel de enlace (piggybacking)."
        ),
        patrones=(
            r"\bservicios?\b",
            r"\bprotocolos?\b",
            r"\binterfaz(es)?\b",
            r"\bprimitivas?\b",
            r"\bpiggyback",
            r"\bmultiplexa",
            r"modos? de transmision",
            r"\bduplex\b",
            r"\bcheckpoints?\b",
            r"\bpuntos de (verificacion|sincronizacion)\b",
            r"\bmodular\b",
        ),
        prioridad=90,
    ),
    # --- IV.7.2: los protocolos
    Materia(
        key="ipv6",
        epigraph_code="IV.7.2",
        title="IPv6: direcciones, cabecera y convivencia con IPv4",
        resumen=(
            "El direccionamiento de 128 bits y su notación, los tipos de dirección (global "
            "unicast, link-local, ULA fc00::/7, multicast, loopback ::1, no especificada), la "
            "cabecera fija de 40 bytes y sus campos (flow label, traffic class, hop limit), los "
            "jumbogramas, la MTU mínima de 1280 y los mecanismos de transición."
        ),
        patrones=(
            r"\bipv6\b",
            # El enunciado de una pregunta llega con erratas de OCR («1Pv6»): sin esto, la pregunta
            # del campo Clase de Tráfico caía en el cajón de revisión.
            r"\bpv6\b",
            r"\bff0[0-9]",
            r"\bfc00\b|\bfd00\b",
            r"\bula\b",
            r"jumbograma",
            r"flow label|etiqueta de flujo",
            r"hop limit",
            r"neighbor (solicitation|advertisement)",
            r"solicited node",
            r"cabeceras? de extension",
            r"eui 64",
            r"traffic class",
        ),
        prioridad=10,
    ),
    Materia(
        key="arp",
        epigraph_code="IV.7.2",
        title="ARP y RARP: la dirección física",
        resumen=(
            "Cómo se pasa de una dirección IP a la dirección MAC dentro de la red local (ARP), la "
            "resolución inversa (RARP) y las direcciones físicas y de difusión."
        ),
        patrones=(r"\barp\b", r"\brarp\b", r"direccion fisica", r"direcciones? mac"),
        prioridad=11,
    ),
    Materia(
        key="icmp",
        epigraph_code="IV.7.2",
        title="ICMP: los mensajes de control y error",
        resumen=(
            "Qué es ICMP (y ICMPv6), en qué capa vive, sus mensajes de error (destino "
            "inalcanzable, tiempo excedido, redirección) y su relación con el TTL y con las "
            "herramientas de diagnóstico."
        ),
        patrones=(
            r"\bicmp",
            r"time exceeded",
            r"destino inalcanzable",
            r"destination unreachable",
        ),
        prioridad=12,
    ),
    Materia(
        key="dns",
        epigraph_code="IV.7.2",
        title="DNS: nombres de dominio",
        resumen=(
            "La base de datos distribuida y jerárquica de nombres, los tipos de registro (A, AAAA, "
            "NS, MX, CNAME, SOA, PTR, TXT), el 53/UDP y 53/TCP, la resolución directa e inversa y "
            "las consultas."
        ),
        patrones=(
            r"\bdns\b",
            r"nombres? de dominio",
            r"registros? (a|aaaa|ns|mx|cname|soa|ptr|txt|srv)\b",
            r"\bnslookup\b",
            r"resolucion (de nombres|inversa|directa)",
            r"transferencias? de zona",
        ),
        prioridad=13,
    ),
    Materia(
        key="dhcp",
        epigraph_code="IV.7.2",
        title="DHCP y la configuración automática",
        resumen=(
            "La asignación dinámica de direcciones (DHCP, sus puertos 67-68/UDP, BOOTP), la "
            "configuración manual frente a la automática y lo que pasa cuando no hay servidor."
        ),
        patrones=(
            r"\bdhcp\b",
            r"\bbootp\b",
            r"asignacion (dinamica|automatica) de direcciones",
            r"direccionamiento (estatico|dinamico)",
            r"\bconcesion\b",
        ),
        prioridad=14,
    ),
    Materia(
        key="web",
        epigraph_code="IV.7.2",
        title="HTTP y HTTPS",
        resumen=(
            "El protocolo de transferencia de hipertexto, sus métodos y códigos, el 80/TCP y el "
            "443/TCP con TLS, y HTTP/2 y HTTP/3 como versiones."
        ),
        patrones=(r"\bhttp", r"\bhipertexto\b", r"\bweb\b"),
        prioridad=15,
    ),
    Materia(
        key="correo",
        epigraph_code="IV.7.2",
        title="Correo electrónico: SMTP, POP3, IMAP y sus versiones seguras",
        resumen=(
            "El envío (SMTP en el 25 y submission en el 587), la recogida (POP3 en el 110 y 995, "
            "IMAP4 en el 143 y 993), el formato de los mensajes y los protocolos con cifrado."
        ),
        patrones=(
            r"\bsmtp\b",
            r"\bpop3\b|\bpop2\b",
            r"\bimap",
            r"\bcorreo\b",
            r"\bqmtp\b",
            r"\bsubmission\b",
        ),
        prioridad=16,
    ),
    Materia(
        key="ficheros",
        epigraph_code="IV.7.2",
        title="Transferencia de ficheros: FTP, FTPS, SFTP y TFTP",
        resumen=(
            "FTP y sus dos conexiones (20 y 21/TCP), TFTP sobre 69/UDP, SFTP sobre SSH (22/TCP) y "
            "FTPS: en qué se diferencian y cuál va cifrado."
        ),
        patrones=(
            r"\bftp\b",
            r"\bftps\b",
            r"\bsftp\b",
            r"\btftp\b",
            r"transferencia de ficheros",
            r"\bscp\b",
        ),
        prioridad=17,
    ),
    Materia(
        key="gestion",
        epigraph_code="IV.7.2",
        title="Gestión de red: SNMP, directorio y acceso remoto",
        resumen=(
            "SNMP y sus versiones (v1, v2c, v3 con seguridad), la MIB y las PDU, los puertos 161 y "
            "162, el acceso a servicios de directorio (LDAP) y el acceso remoto (Telnet y SSH)."
        ),
        patrones=(
            r"\bsnmp",
            r"\bmib\b",
            r"gestion de red",
            r"\bmonitorizacion\b",
            r"\bldap\b",
            r"\btelnet\b",
            r"\bssh\b",
            r"\brdp\b",
            r"gestion osi",
        ),
        prioridad=18,
    ),
    Materia(
        key="subredes",
        epigraph_code="IV.7.2",
        title="Subredes, máscaras y CIDR",
        resumen=(
            "La máscara de subred y el prefijo (/24, /27, /29…), el cálculo de la dirección de red "
            "(AND bit a bit), la de difusión, el rango de direcciones utilizables, CIDR, VLSM y el "
            "reparto en subredes del mismo tamaño."
        ),
        patrones=(
            r"subred",
            r"subnet",
            r"\bmascaras?\b",
            r"\bprefijo",
            r"\bcidr\b",
            r"\bvlsm\b",
            r"direccion de red",
            r"direccion de difusion",
            r"\bbroadcast\b",
            r"direcciones? (utiles|validas)",
            r"hosts? (utilizables|disponibles|validas)",
            r"and bit a bit",
            r"bits? (de hosts?|para hosts?)",
            r"bloques de \d+",
            r"\bhosts?\b",
        ),
        prioridad=20,
    ),
    Materia(
        key="direcciones-especiales",
        epigraph_code="IV.7.2",
        title="Direcciones privadas, reservadas y NAT",
        resumen=(
            "Los rangos privados de la RFC 1918, las direcciones reservadas (loopback 127.0.0.0/8, "
            "0.0.0.0, APIPA 169.254.0.0/16, multicast 224.0.0.0/4, clase E), el direccionamiento "
            "público y privado y la traducción de direcciones (NAT)."
        ),
        patrones=(
            r"\bprivad",
            r"rfc 1918",
            r"\bloopback\b",
            r"\bapipa\b",
            r"169 254",
            r"multidifusion|\bmulticast\b",
            r"clase [de]\b",
            r"\bnat\b",
            r"\bpublica",
            r"reservad",
            r"127 0 0",
            r"no asignable",
        ),
        prioridad=21,
    ),
    Materia(
        key="tcp",
        epigraph_code="IV.7.2",
        title="TCP: conexión, fiabilidad y cabecera",
        resumen=(
            "El protocolo orientado a conexión: el saludo de tres vías (SYN, SYN-ACK, ACK), los "
            "acuses y las retransmisiones, el control de flujo y de congestión, la cabecera (20 a "
            "60 bytes) y sus campos (puertos, número de secuencia, flags, ventana)."
        ),
        patrones=(
            r"\btcp\b",
            r"orientado a conexion",
            r"\bsyn\b",
            r"\backs?\b",
            r"ventana (de |de congestion|congestion)",
            r"retransmis",
            r"control de flujo",
            r"control de congestion",
        ),
        prioridad=25,
    ),
    Materia(
        key="udp",
        epigraph_code="IV.7.2",
        title="UDP: datagramas sin conexión",
        resumen=(
            "El protocolo no orientado a conexión: qué no garantiza (entrega, orden, duplicados), "
            "su cabecera de 8 bytes y para qué se usa frente a TCP."
        ),
        patrones=(r"\budp\b", r"no orientado a conexion", r"\bdatagramas?\b"),
        prioridad=26,
    ),
    Materia(
        key="encaminamiento",
        epigraph_code="IV.7.2",
        title="Encaminamiento: rutas, protocolos y puerta de enlace",
        resumen=(
            "El encaminamiento de paquetes y la tabla de rutas, la puerta de enlace por defecto, "
            "los protocolos de encaminamiento (RIP, OSPF, BGP) y su clasificación, el TTL y el "
            "número de saltos, y la alta disponibilidad de la puerta de enlace (VRRP, HSRP)."
        ),
        patrones=(
            r"encaminamiento|enrutamiento|\brouting\b",
            r"\brutas?\b",
            r"\brouters?\b",
            r"\bospf",
            # «RIPng» es RIP: sin quitar el límite de palabra, la pregunta de RIPng se quedaba sin
            # materia y caía en el cajón de revisión.
            r"\brip",
            r"\bbgp",
            r"\bttl\b",
            r"\bsaltos?\b",
            r"puerta de enlace",
            r"\bvrrp\b|\bhsrp\b",
            r"\bgateway\b",
            r"tabla de (rutas|encaminamiento)",
        ),
        prioridad=30,
    ),
    Materia(
        key="herramientas",
        epigraph_code="IV.7.2",
        title="Herramientas de diagnóstico y configuración",
        resumen=(
            "Con qué se mira la red desde el equipo: ping, traceroute/tracert, netstat, ipconfig e "
            "ifconfig, arp, y los ficheros de configuración de red del sistema operativo."
        ),
        patrones=(
            r"\bping\b",
            r"trace(route|rt)",
            r"\bnetstat\b",
            r"\bipconfig\b|\bifconfig\b",
            r"herramientas? de (diagnostico|red)",
            r"etc (fstab|hosts|netplan|sysconfig|resolv)",
            r"path mtu|camino mtu",
            r"depuracion de windows",
        ),
        # Se reparte **antes** que subredes: un hecho que habla de `ipconfig` o de `/etc/hosts`
        # es un hecho de herramientas, aunque mencione la máscara o los hosts de la red.
        prioridad=19,
    ),
    Materia(
        key="puertos",
        epigraph_code="IV.7.2",
        title="Puertos bien conocidos (una sola tabla)",
        resumen=(
            "Qué es un puerto, los rangos de la IANA (bien conocidos, registrados y dinámicos), "
            "los pares puerto-servicio que se confunden y **la tabla de puertos del tema, aquí y "
            "solo aquí**: el resto de apartados la enlazan."
        ),
        patrones=(r"\bpuertos?\b", r"well known", r"\biana\b", r"\bsockets?\b"),
        prioridad=40,
        tabla_unica=True,
    ),
    Materia(
        key="direccionamiento-ipv4",
        epigraph_code="IV.7.2",
        title="Direccionamiento IPv4: clases, cabecera y fragmentación",
        resumen=(
            "La dirección IPv4 y sus clases (A, B, C, D y E), la notación decimal y binaria, la "
            "cabecera IPv4 (IHL, ToS, identificación, offset, checksum, protocolo) y la "
            "fragmentación, la MTU y el MSS."
        ),
        patrones=(
            r"\bipv4\b",
            r"direcciones? ip\b",
            r"primer octeto",
            r"\boctetos?\b",
            r"cabecera ip",
            r"\bihl\b",
            r"\btos\b",
            r"total length",
            r"suma de verificacion",
            r"\bchecksum\b",
            r"campo (tos|ihl|identificacion|offset|desplazamiento)",
            r"fragmentacion|fragmentos?",
            r"\bmtu\b|\bmss\b",
            # «¿A qué clase pertenece la red 172.17.8.0/21?»: el enunciado nombra la clase y no la
            # dirección, así que sin este patrón la pregunta se quedaba sin materia.
            r"\bclase\b",
            r"bits? mas significativos",
            r"\bip\b",
        ),
        prioridad=50,
    ),
    Materia(
        key="otros-protocolos",
        epigraph_code="IV.7.2",
        title="Otros protocolos y servicios de aplicación del tema",
        resumen=(
            "Protocolos TCP/IP que aparecen en las preguntas del tema y no son de las materias "
            "anteriores: NTP (hora), IPP (impresión), RSVP (reservas), Kerberos y RADIUS "
            "(autenticación), CoAP (dispositivos limitados), los protocolos heredados (IPX/SPX, "
            "NetBEUI/NetBIOS) y los que se confunden con ellos. **Propuesta**: si no convence, "
            "estos hechos se reparten entre la materia de puertos y el cajón de revisión."
        ),
        patrones=(
            r"\bntp\b",
            r"\bipp\b",
            r"\brsvp\b",
            r"\bkerberos\b",
            r"\bradius\b",
            r"\bcoap\b",
            r"\bipx\b",
            r"\bspx\b",
            r"netbeui|netbios",
            r"\bwhois\b",
            r"\bx11\b",
            r"\bsdp\b",
            r"\bsap\b",
            r"\bcmip\b",
            r"\blpd\b",
            r"\bgopher\b",
            r"\bsntp\b",
        ),
        prioridad=45,
    ),
    Materia(
        key="otros-iv-7-1",
        epigraph_code="IV.7.1",
        title="Otros contenidos de IV.7.1 (revisar)",
        resumen=(
            "Hechos del epígrafe que no son de ninguna de sus materias. Se revisan antes de "
            "redactar: si son de otro bloque, la pregunta está mal clasificada."
        ),
        prioridad=PRIORIDAD_POR_DEFECTO,
    ),
    Materia(
        key="otros",
        epigraph_code="IV.7.2",
        title="Otros contenidos de IV.7.2 (revisar)",
        resumen=(
            "Hechos que están en el tema pero no son de ninguna de sus materias: preguntas de "
            "otros bloques (bases de datos, diagramas de flujo de datos, Métrica v3, normativa) "
            "que se clasificaron aquí. Se revisan antes de redactar; no se escriben como si "
            "fueran TCP/IP."
        ),
        prioridad=PRIORIDAD_POR_DEFECTO,
    ),
)

#: El orden en que se **enseña** el índice de IV.7: el del temario, que es el del propietario. Las
#: materias se declaran agrupadas por epígrafe para poder leerlas; este es el orden del índice, y es
#: una decisión aparte del orden de reparto (`prioridad`), que mira primero lo particular.
_ORDEN_IV7 = (
    "tcpip-arquitectura",
    "osi-modelo",
    "conceptos-del-modelo",
    "otros-iv-7-1",
    "direccionamiento-ipv4",
    "subredes",
    "direcciones-especiales",
    "ipv6",
    "arp",
    "icmp",
    "encaminamiento",
    "tcp",
    "udp",
    "puertos",
    "dns",
    "dhcp",
    "web",
    "correo",
    "ficheros",
    "gestion",
    "herramientas",
    "otros-protocolos",
    "otros",
)


def _en_orden_de_estudio(materias: Sequence[Materia], orden: Sequence[str]) -> tuple[Materia, ...]:
    """Las materias en el orden del índice. Falla si el orden no cubre el catálogo entero.

    Un orden escrito a mano se desincroniza en cuanto alguien añade una materia: mejor que falle al
    cargar que quedarse una materia fuera del índice sin que nadie lo vea.
    """
    por_clave = {materia.key: materia for materia in materias}
    if set(orden) != set(por_clave):
        faltan = sorted(set(por_clave) - set(orden))
        sobran = sorted(set(orden) - set(por_clave))
        raise ValueError(
            f"el orden del índice no cuadra con el catálogo (faltan {faltan}, sobran {sobran})"
        )
    return tuple(por_clave[clave] for clave in orden)


#: Los catálogos definidos. Un tema sin catálogo no tiene índice: se dice, no se inventa.
_CATALOGOS: dict[str, tuple[Materia, ...]] = {
    "IV.7": _en_orden_de_estudio(_MATERIAS_IV7, _ORDEN_IV7),
}


def catalogo(topic_code: str) -> tuple[Materia, ...] | None:
    """El catálogo de materias de un tema, o `None` si todavía no está definido."""
    return _CATALOGOS.get(topic_code)


__all__ = [
    "PRIORIDAD_POR_DEFECTO",
    "IndiceDelTema",
    "Materia",
    "RepartoMateria",
    "catalogo",
    "indice_de",
    "materia_de",
    "repartir_grupos",
    "repartir_hechos",
    "validar_catalogo",
]
