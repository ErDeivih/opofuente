"""El catálogo de materias de IV.8 (Internet: arquitectura, evolución, servicios y HTTP/SSL).

IV.8 es un tema **técnico** de Internet y lo que lo estructura son sus cuatro epígrafes —la
arquitectura de red, el origen y la evolución, los principales servicios y los protocolos HTTP,
HTTPS y SSL/TLS— y dentro de cada uno el índice va **por asunto**, como en IV.7, III.5 y III.9. Este
catálogo los abre en ocho apartados:

- la **arquitectura de Internet** en uno: qué es la red de redes, el modelo TCP/IP y sus capas, la
  conmutación de paquetes, los proveedores de servicios y las redes internas de una organización;
- el **direccionamiento** en uno: las direcciones IP y sus versiones, las máscaras y las subredes,
  la traducción de direcciones, y quién reparte las direcciones y los nombres en el mundo;
- el **origen y la evolución** en uno (el epígrafe IV.8.2): de ARPANET a la web, quién la inventó,
  el consorcio que la estandariza, la web 2.0 y el Internet de las cosas;
- el **sistema de nombres de dominio** en uno, que es el servicio que más pregunta el banco: la
  resolución, los tipos de registro, los servidores y las consultas, los ficheros de zona, la
  sintaxis de un nombre de dominio y las extensiones de seguridad;
- los **demás servicios** en uno: el correo electrónico, la transferencia de ficheros, el acceso
  remoto y los puertos de escucha de cada uno, los proxies y el Internet de las cosas;
- la **voz y el vídeo sobre IP** en uno: los códecs, las recomendaciones de la ITU-T, la
  videoconferencia y la calidad de la conversación (porque el banco le dedica un bloque propio);
- el **protocolo HTTP** en uno: los métodos, los mensajes y, sobre todo, los códigos de estado
  (1xx a 5xx), las versiones y sus RFC;
- el **HTTPS y el TLS/SSL** en uno: el establecimiento de la sesión, los certificados, el cifrado y
  sus tipos, las suites y las versiones del protocolo, y su configuración en el servidor.

Dos decisiones de los patrones, dichas donde se leen:

- **los códigos de estado no se enumeran uno a uno**: el banco los pregunta por su nombre en inglés
  («Misdirected Request», «Reset Content», «Already Reported») y por su clase («¿qué clase indica
  un error del cliente?»). El patrón pide el contexto (`codigo(s) (de estado|de respuesta)`,
  `\b[1-5]xx\b` y los nombres propios que se repiten), no la palabra «código» suelta, que aparece
  en media asignatura;
- **«internet» y «protocolo» van en los patrones débiles**, y las direcciones IP se piden por su
  forma (`ipv4`, `ipv6`, `mascara`, `subred`): son las palabras que salen hablando de cualquier cosa
  del tema, y con ellas como patrón propio el primer apartado se llevaría las preguntas de DNS y de
  HTTP.

Lo que el banco trae de **otro tema** —la seguridad perimetral y los cortafuegos, que son de IV.9;
el correo como servicio administrativo, que es de IV.3; y las preguntas de sistemas operativos—
**no** se lava dentro de un apartado que no existe: va a la bandeja del propietario con su motivo
(`Motivo.SIN_MATERIA_EN_EL_INDICE`), que es lo que manda el índice.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Los códigos de estado de HTTP que el banco pregunta **por su nombre**: no se enumeran todos, solo
#: los que se repiten y los que no llevan la palabra «código» en el enunciado.
_CODIGOS_HTTP = (
    r"misdirected request|use proxy|reset content|already reported|not extended|loop detected|"
    r"unavailable for legal reasons|proxy authentication required|too many requests|"
    r"request timeout|bad request|not found|multi ?status|network connect timeout|"
    r"http version not supported|processing|created|no content|unauthorized|forbidden|"
    r"internal server error|service unavailable|gateway timeout|bad gateway|continue|"
    r"\b[1-5]xx\b"
)

#: Los tipos de registro de un fichero de zona DNS que el banco nombra por su sigla.
_REGISTROS_DNS = (
    r"registro(s)? (dns|de (tipo|recurso|zona))|\bcname\b|\bsoa\b|\bmx\b|\bns\b|\btxt\b|\baaaa?\b|"
    r"\bptr\b|\bsrv\b|\bdnssec\b|\brrsig\b|\bdnskey\b"
)

MATERIAS: tuple[Materia, ...] = (
    # --- IV.8.1 Internet: arquitectura de red --------------------------------------------------
    Materia(
        key="arquitectura-de-internet",
        epigraph_code="IV.8.1",
        title="La arquitectura de Internet: la red de redes y el modelo TCP/IP",
        resumen=(
            "Qué es Internet y cómo está montada: la red de redes y su arquitectura, el modelo "
            "TCP/IP y la misión de sus capas, la conmutación de paquetes y el encaminamiento, "
            "los proveedores de servicios de Internet, las redes internas de una organización "
            "(intranet, extranet y redes privadas) y el ancho de banda."
        ),
        patrones=(
            r"arquitectura de (internet|red)|red de redes|modelo tcp ?/? ?ip|"
            r"capa de (internet|red|transporte|aplicacion|acceso a la red) del modelo|"
            r"mision principal de la capa",
            r"conmutacion de paquetes|encaminamiento|enrutamiento|red(es)? de conmutacion|"
            r"conmutacion de circuitos",
            r"proveedor(es)? de servicios? de internet|\bisp\b|operador(es)? de telecomunicaciones",
            r"red interna|intranet|extranet|red privada|red corporativa|red perimetral|"
            r"red de area (local|amplia|metropolitana)|topologia",
            r"ancho de banda|caudal|tasa de transferencia|latencia",
        ),
        patrones_debiles=(r"internet", r"red(es)?", r"arquitectura"),
        prioridad=70,
    ),
    Materia(
        key="direccionamiento-y-nombres-de-alto-nivel",
        epigraph_code="IV.8.1",
        title="El direccionamiento IP y quién lo reparte",
        resumen=(
            "Las direcciones con las que se habla en Internet: las direcciones IPv4 e IPv6, sus "
            "clases y rangos, la máscara de subred y las subredes, la traducción de direcciones de "
            "red, la asignación dinámica de direcciones, y las organizaciones que reparten las "
            "direcciones y los nombres de dominio en el mundo."
        ),
        patrones=(
            r"ipv ?4|ipv ?6|direccion(es)? ip|mascara de subred|mascara|\bsubred(es)?\b|"
            r"\bcidr\b|clase [abc] de direcciones|rango de direcciones",
            r"traduccion de direcciones|\bnat\b|\bpat\b|direccion(es)? privada|"
            r"\bdhcp\b|asignacion (dinamica|automatica) de direcciones",
            r"\bicann\b|\biana\b|\brir\b|\bnic\b|organismo.*(asignar|responsable)|"
            r"asignar direcciones ip|funciones de gestion del sistema de nombres",
            r"direccion(es)? de (red|difusion|broadcast)|puerta de enlace|mascara",
        ),
        patrones_debiles=(r"direccion(es)?", r"ip\b"),
        prioridad=40,
    ),
    # --- IV.8.2 Origen, evolución y estado actual ----------------------------------------------
    Materia(
        key="origen-y-evolucion-de-internet",
        epigraph_code="IV.8.2",
        title="El origen y la evolución de Internet y de la web",
        resumen=(
            "De dónde viene todo esto: ARPANET y los orígenes de la red, la aparición de la web y "
            "quiénes la crearon, el consorcio que la estandariza, la evolución hasta hoy (la web "
            "2.0, las redes sociales, la web semántica) y el Internet de las cosas."
        ),
        patrones=(
            r"\barpanet\b|origen de internet|historia de internet|evolucion de internet|"
            r"padre de la web|quien (creo|invento) la web|tim berners|\bw3c\b|"
            r"consorcio (de la web|www)",
            r"web ?2 ?0|web semantica|redes sociales|navegador(es)? web",
            r"internet de las cosas|internet of things|\biot\b|dispositivos? conectados?",
            r"estado actual de internet|penetracion de internet|usuarios de internet",
        ),
        patrones_debiles=(r"internet", r"web\b", r"evolucion"),
        prioridad=75,
    ),
    # --- IV.8.3 Principales servicios ----------------------------------------------------------
    Materia(
        key="dns",
        epigraph_code="IV.8.3",
        title="El sistema de nombres de dominio (DNS)",
        resumen=(
            "El servicio que traduce nombres a direcciones: la resolución de nombres y los tipos "
            "de consulta, los servidores de nombres y su jerarquía, los tipos de registro de un "
            "fichero de zona (A, AAAA, CNAME, MX, NS, SOA, TXT, PTR y los de la extensión de "
            "seguridad), la sintaxis de un nombre de dominio y los comandos para diagnosticarlo."
        ),
        patrones=(
            r"\bdns\b|sistema de nombres de dominio|servidor(es)? de nombres|"
            r"resolucion de nombres|fichero de zona|zona dns|consulta(s)? (dns|al servidor de "
            r"nombres)|flag \baa\b|servidor de nombres",
            _REGISTROS_DNS,
            r"nombre(s)? de dominio|dominio(s)? de (primer|segundo) nivel|sintaxis de un nombre|"
            r"\bdominio\b.*(normas|sintaxis)|subdominio",
            r"\bnslookup\b|\bdig\b|\bnamed\b|diagnosticar el estado del servicio de nombres|"
            r"traduccion de nombres",
        ),
        patrones_debiles=(r"nombre(s)?", r"dominio(s)?", r"resolucion"),
        prioridad=20,
    ),
    Materia(
        key="servicios-de-internet",
        epigraph_code="IV.8.3",
        title="Los principales servicios de Internet",
        resumen=(
            "Los servicios que se usan sobre la red y sus puertos: el correo electrónico y sus "
            "protocolos, la transferencia de ficheros, el acceso remoto (Telnet y SSH), los "
            "servidores de aplicaciones y los proxies, y los puertos de escucha de cada servicio."
        ),
        patrones=(
            r"correo electronico|servidor de correo|\bsmtp\b|\bpop3?\b|\bimap\b|"
            r"protocolo.*(correo|mensajeria)",
            r"\bftp\b|\bsftp\b|transferencia de (ficheros|archivos)|servidor de ficheros",
            r"\btelnet\b|\bssh\b|acceso remoto|terminal virtual|escritorio remoto",
            r"puerto(s)? (de escucha|estandar|de aplicacion|por defecto)|"
            r"que puerto|numero de puerto|puerto en el que escucha",
            r"\bproxy\b|servidor(es)? proxy|servidor de aplicaciones web|"
            r"biblioteca de objetos|servicio de directorio(?! universal)",
            r"servicio(s)? de internet|principales servicios",
        ),
        patrones_debiles=(r"servicio(s)?", r"protocolo(s)?", r"puerto(s)?"),
        prioridad=35,
        #: La tabla de puertos de los servicios vive **aquí y solo aquí**: marcarla es lo que hace
        #: que `--limpiar-forma` la parta por familias (correo, ficheros, acceso remoto, web) y le
        #: quite las notas que solo dicen lo que un puerto **no** es. Sin la marca, la puerta de
        #: forma la da por no partida y el tema no se publica.
        tabla_unica=True,
    ),
    Materia(
        key="voz-y-video-sobre-ip",
        epigraph_code="IV.8.3",
        title="La voz y el vídeo sobre IP",
        resumen=(
            "La conversación por la red: la voz sobre IP y sus protocolos, los códecs de voz y las "
            "recomendaciones de la ITU-T, la videoconferencia sobre redes IP y las técnicas para "
            "medir la calidad de la conversación."
        ),
        patrones=(
            r"voz sobre ip|\bvoip\b|\bvoz\b.*\bip\b|telefonia (sobre )?ip|"
            r"codec(s)?|codificacion de voz|cs ?acelp|\bg\.?7\d\d\b|\bg\.?1\d\d\b|\bitu\b|"
            r"\bitu-t\b",
            r"videoconferencia|videollamada|\bh\.?32[0-9]\b|\bsip\b|\brtp\b|\brtcp\b|\bsdp\b|"
            r"\bmegaco\b|\bh\.?248\b",
            r"calidad de (la )?(conversacion|voz|servicio)|\bmos\b|\bjitter\b|\beco\b|"
            r"retardo|perdida de paquetes",
        ),
        patrones_debiles=(r"voz\b", r"video\b", r"calidad"),
        prioridad=25,
    ),
    # --- IV.8.4 Protocolos HTTP, HTTPS y SSL/TLS -----------------------------------------------
    Materia(
        key="http-y-sus-codigos",
        epigraph_code="IV.8.4",
        title="El protocolo HTTP y sus códigos de estado",
        resumen=(
            "El protocolo de la web: los métodos y los mensajes de petición y respuesta, las "
            "clases de códigos de estado (1xx informativos, 2xx de éxito, 3xx de redirección, 4xx "
            "de error del cliente y 5xx de error del servidor) con sus nombres, y las versiones "
            "del protocolo y sus RFC."
        ),
        patrones=(
            _CODIGOS_HTTP,
            r"protocolo http|\bhttp\b(?!s)|peticion(es)? http|respuesta http|metodos? http|"
            r"mensaje(?:s)? (http|de peticion|de respuesta)|cabeceras? http",
            r"http ?/? ?2|spdy|\brfc ?2616\b|\brfc ?7230\b|hipertexto",
            r"codigo(s)? (de estado|de respuesta)|clase de codigos|error por parte del cliente|"
            r"significado del conjunto de codigos",
        ),
        patrones_debiles=(r"http", r"codigo(s)?", r"respuesta"),
        prioridad=30,
    ),
    Materia(
        key="https-y-tls",
        epigraph_code="IV.8.4",
        title="El HTTPS y el TLS/SSL",
        resumen=(
            "La web cifrada: qué es SSL y qué es TLS y qué protegen, el establecimiento de la "
            "sesión y sus mensajes, los certificados que hacen falta, los tipos de cifrado "
            "(simétrico y asimétrico) y las suites, las versiones del protocolo y su "
            "configuración en el servidor."
        ),
        patrones=(
            r"\bssl\b|secure sockets? layer|\btls\b|transport layer security|\bhttps\b|"
            r"capa de sockets? segura",
            r"certificado(s)? (digital|ssl|tls|de servidor|de cliente)|autoridad de certificacion|"
            r"infraestructura de clave publica|\bpki\b|clave publica|clave privada",
            r"cifrado (simetrico|asimetrico|de tipo|de clave)|\bcifrado\b|encriptacion|"
            r"handshake|negociacion de parametros|suite de cifrado|\bhmac\b|sha ?256",
            r"acceso al servidor web.*https|puerto estandar de https|mod_ssl|"
            r"certificados en apache|sesion ssl (expire|en la cache)",
        ),
        patrones_debiles=(r"seguridad", r"cifrado", r"certificado(s)?"),
        prioridad=22,
    ),
)

#: El orden del índice: primero la arquitectura y el direccionamiento, después de dónde viene, luego
#: los servicios y, al final, los dos protocolos de la web, que es como se estudia el tema.
ORDEN: tuple[str, ...] = (
    "arquitectura-de-internet",
    "direccionamiento-y-nombres-de-alto-nivel",
    "origen-y-evolucion-de-internet",
    "dns",
    "servicios-de-internet",
    "voz-y-video-sobre-ip",
    "http-y-sus-codigos",
    "https-y-tls",
)

__all__ = ["MATERIAS", "ORDEN"]
