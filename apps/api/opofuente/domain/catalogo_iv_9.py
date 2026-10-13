"""El catálogo de materias de IV.9 (seguridad en redes, perímetro, acceso remoto, VPN y puesto).

IV.9 es un tema **técnico** de seguridad y su banco lo confirma: de sus 222 grupos de preguntas,
191 no traen epígrafe y hablan de cortafuegos, de VPN, de IDS, de puertos y de antivirus. Los cinco
epígrafes oficiales del temario son el esqueleto —seguridad de la red, seguridad perimetral, acceso
remoto, VPN y puesto del usuario— y dentro de cada uno el índice va **por asunto**, como en IV.7,
III.5, III.9, IV.8 y IV.1. Este catálogo los abre en ocho apartados:

- la **seguridad de la red y sus ataques** en uno (IV.9.1): qué protege la seguridad de la red, la
  tipología de las medidas, los ataques que sufre (ARP *spoofing*, escuchas, análisis con
  escáneres), la seguridad inalámbrica (WEP frente a WPA) y el control de acceso a la red (AAA,
  RADIUS, 802.1X y el segundo factor);
- la **detección y la prevención de intrusos** en uno (IV.9.1): los IDS y los IPS y sus tipos, qué
  hace y qué no hace cada uno, las herramientas (Snort, Snorby, Suricata) y los señuelos;
- los **cortafuegos y su filtrado** en uno (IV.9.2), que es el bloque más grande del banco: los
  tipos (filtrado de paquetes, *stateful*, proxy, nivel de aplicación, DPI, UTM), la capa en la que
  actúan, qué protegen y qué no, las reglas y los comandos (`iptables`, el cortafuegos de Windows) y
  las arquitecturas de cortafuegos;
- la **DMZ y la arquitectura perimetral** en uno (IV.9.2): la seguridad perimetral, la zona
  desmilitarizada, el proxy directo y el inverso, el filtrado de contenido web y el anti-spoofing;
- los **puertos que se abren en el cortafuegos** en uno (IV.9.2), que es la tabla única del tema:
  qué puerto por defecto usa cada servicio que hay que dejar pasar;
- el **acceso remoto seguro** en uno (IV.9.3): el acceso remoto y sus protocolos (SSH, RDP, VNC), el
  escritorio virtual y el VDI, el teletrabajo y el control remoto de puestos;
- las **redes privadas virtuales** en uno (IV.9.4): qué son, los tipos por nivel, los protocolos
  (IPsec con AH, ESP e IKE, L2TP, PPTP, OpenVPN), el túnel y sus modos, la asociación de seguridad y
  el *split tunneling*;
- y la **seguridad en el puesto del usuario** en uno (IV.9.5): las categorías de servicios que
  protegen el puesto (antivirus, antispam, control de aplicaciones), la lucha contra el *malware* y
  el *phishing*, el cifrado del disco, la seguridad del correo, las guías y herramientas del
  CCN-CERT y el bastionado.

Cuatro decisiones de los patrones, dichas donde se leen:

- **la palabra que sale en todo el tema no vale como patrón propio.** «seguridad», «red»,
  «protocolo» y «puerto» están en los **débiles**, que solo deciden cuando ninguna materia ha
  casado. Sin esa regla, «Seguridad en el puesto del usuario» se llevaría media asignatura por
  decir «seguridad» en la primera línea;
- **`\\bips\\b` y `\\bids\\b` se aceptan como siglas**, y se dice por qué: en este banco «IPs» en
  plural no aparece —se escribe «direcciones IP»—, así que la sigla no se confunde con la dirección;
- **la tabla de puertos vive en un solo apartado, y se aprendió corrigiendo**: el redactor escribió
  una segunda tabla de puertos dentro del acceso remoto, y un tema **no puede tener dos** —cada una
  recibe los encabezados de familia («Servicios de red», «Confusiones que caen») y la puerta de
  encabezados repetidos, que mira el tema entero, los cuenta dos veces—. Sus cuatro filas que no
  estaban en la del cortafuegos (23 Telnet, 69 TFTP, 3389 RDP y 5900 VNC) se movieron allí
  **literalmente**, sin inventar ninguna, y el resto de la tabla se quitó;
- **AH y ESP se piden con `protocolo` delante**, porque `\\bah\\b` y `\\besp\\b` sueltos casan con
  cualquier palabra corta del enunciado;
- y **lo que es de otro tema no se lava**: el PoE, las VLAN, los dispositivos de la capa 2 y el
  direccionamiento IPv6 son de IV.10; el `RAID 6` y el TIA-942, de IV.2 y IV.5; los principios del
  ENS y la gestión de incidencias, de I.8 y IV.5; el `heartbleed` y las técnicas criptográficas, de
  IV.5, y el `RFC 2142` y Exchange, de IV.3. Todo eso va a la bandeja del propietario con su motivo
  (`Motivo.SIN_MATERIA_EN_EL_INDICE`), que es lo que manda el índice.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: AH y ESP son dos protocolos de IPsec y se piden **con la palabra `protocolo` delante**: sueltos,
#: `\\bah\\b` y `\\besp\\b` casan con cualquier palabra corta del enunciado.
_AH_Y_ESP = r"protocolo (ah|esp)\b|\b(ah|esp)\b en ipsec|en relacion con el protocolo (ah|esp)"

#: La seguridad inalámbrica y los ataques a la red: el bloque propio de IV.9.1.
_ATAQUES_Y_REDES = (
    r"\bwpa\b|\bwep\b|\bwpa ?[23]\b|802 11i|eavesdropping|redes? inalambrica(s)?|"
    r"seguridad de la red de (una|la) organizacion|mecanismos de seguridad en redes|"
    r"protocolo disenado para aportar seguridad|suplantacion de direcciones|"
    r"arp spoofing|ataque arp|"
    r"\bnmap\b|escaner de (puertos|vulnerabilidades)|analisis de vulnerabilidades|"
    r"captura de (paquetes|trafico)|analizador de (trafico|protocolos)|sniffer|"
    r"tipologia de las medidas de seguridad|medida organizativa|"
    r"es una medida (organizativa|preventiva|reactiva)|"
    r"cual de estas medidas o sistemas de seguridad es reactiva"
)

#: El control de acceso a la red: AAA, 802.1X, el segundo factor y la biometría.
_CONTROL_DE_ACCESO = (
    r"protocolos? aaa|autenticacion,? autorizacion|\bradius\b|\btacacs\b|802 1x|"
    r"servidor de autenticacion|factor(es)? de autenticacion|doble factor|"
    r"autenticacion multifactor|\bmfa\b|se denomina a este tipo de validacion|"
    r"tecnicas? biometricas?|control de acceso fisico|"
    r"hosts? allow|hosts? deny|acceso a hosts concretos"
)

#: Los puertos que hay que dejar pasar: se piden por el puerto, no por el servicio.
_LOS_PUERTOS = (
    r"puerto (por defecto|estandar|de escucha|utilizado por|que utiliza)|"
    r"que puerto|puerto(s)? (seguros|por defecto|estandar(es)?)|"
    r"puerto(s)? .*(abrir|abiertos|abrirse|utiliza|escucha)|"
    r"indique el puerto|indique cual es el puerto|cual es el puerto|"
    r"puertos? estandares? deberian tener abiertos"
)

MATERIAS: tuple[Materia, ...] = (
    # --- IV.9.1 Seguridad y protección en redes de comunicaciones -------------------------------
    Materia(
        key="la-seguridad-de-la-red-y-sus-ataques",
        epigraph_code="IV.9.1",
        title="La seguridad de la red: medidas, ataques y control de acceso",
        resumen=(
            "Qué protege la seguridad de una red y con qué: la tipología de las medidas "
            "(organizativas, preventivas y reactivas), los ataques que sufre (la suplantación de "
            "direcciones ARP, las escuchas y el análisis con escáneres), la seguridad inalámbrica "
            "(WEP frente a WPA), y el control de acceso a la red: los protocolos AAA, RADIUS, "
            "802.1X, el segundo factor y la biometría."
        ),
        patrones=(
            _ATAQUES_Y_REDES,
            _CONTROL_DE_ACCESO,
        ),
        patrones_debiles=(r"seguridad", r"ataque(s)?", r"red(es)?"),
        prioridad=45,
    ),
    Materia(
        key="deteccion-y-prevencion-de-intrusos",
        epigraph_code="IV.9.1",
        title="La detección y la prevención de intrusos",
        resumen=(
            "Vigilar la red y cortar lo que entra: los sistemas de detección (IDS) y de prevención "
            "(IPS) de intrusos, sus tipos (de red y de host, por firmas y por anomalías), qué hace "
            "y qué no hace cada uno, la diferencia entre los dos, las herramientas (Snort, Snorby, "
            "Suricata) y los señuelos que se dejan atacar a propósito."
        ),
        patrones=(
            r"\bids\b|\bips\b|deteccion de intrus|prevencion de intrus|intrusion detection|"
            r"intrusion prevention|sistema de deteccion de intrusos|detectores de intrusos|"
            r"herramientas? ids|\bsnort\b|\bsnorby\b|\bsuricata\b|"
            r"honeypot|honeynet|sistema trampa|senuelo|"
            r"sistema fisico o virtual que integra una red de herramientas y hosts|"
            r"deteccion por (firmas|anomalias)|comportamiento anomalo|"
            r"\bsiem\b|correlacion de eventos|monitorizacion de (la )?seguridad",
        ),
        patrones_debiles=(r"intrus", r"deteccion", r"monitorizacion"),
        prioridad=25,
    ),
    # --- IV.9.2 Seguridad perimetral ------------------------------------------------------------
    Materia(
        key="cortafuegos-y-su-filtrado",
        epigraph_code="IV.9.2",
        title="Los cortafuegos y su filtrado",
        resumen=(
            "La barrera de la red: qué es un cortafuegos, los tipos que hay (filtrado de paquetes, "
            "con estado, proxy, de nivel de aplicación, con inspección profunda y los unificados), "
            "en qué capa actúan, qué protegen y qué no, sus funciones y características, las "
            "reglas y los comandos con los que se configuran (iptables, el cortafuegos de "
            "Windows) y las arquitecturas de cortafuegos (host bastión, screening)."
        ),
        patrones=(
            r"cortafuegos?|firewall|\biptables\b|\bfirewalld\b|\bnftables\b|"
            r"filtrado de paquetes|packet filtering|"
            r"habilitar el firewall|reglas? (del|de) firewall|regla al firewall|"
            r"modulo de seguridad para filtrar|"
            r"que hardware necesita|"
            r"gestion unificada de amenazas|\butm\b|"
            r"\bdpi\b|deep packet inspection|stateful|stateless|"
            r"arquitectura de cortafuegos|host bastion|"
            r"que protege un cortafuegos|contra que protege|"
            r"funcionalidad(es)? de los cortafuegos|caracteristica(s)? de (un )?cortafuegos|"
            r"que no (es|le aplica) a los cortafuegos",
        ),
        patrones_debiles=(r"filtrado", r"bloquear", r"reglas"),
        prioridad=30,
    ),
    Materia(
        key="la-dmz-y-la-arquitectura-perimetral",
        epigraph_code="IV.9.2",
        title="La DMZ y la arquitectura perimetral",
        resumen=(
            "Cómo se ordena el perímetro: la seguridad perimetral y su finalidad, la zona "
            "desmilitarizada (DMZ) y en qué zona va cada servicio, el proxy directo y el inverso, "
            "el filtrado del contenido web por categorías, el anti-spoofing y los rangos de "
            "direcciones que se filtran en la frontera."
        ),
        patrones=(
            r"seguridad perimetral|red perimetral|perimetro de red|"
            r"\bdmz\b|zona desmilitarizada|demilitarized zone|"
            r"proxy inverso|\bproxy\b|\bproxies\b|"
            r"zona publica|zona interna|"
            r"arquitectura de red segura|diseno de una arquitectura de red|"
            r"configuracion perimetral|aislar los servidores|"
            r"filtrado web|categorias de contenido|"
            r"anti ?spoofing|securitzar|"
            r"que rangos de direcciones ipv4 filtraria|"
            r"sitios? web en funcion de sus categorias",
        ),
        patrones_debiles=(r"perimetral", r"zona", r"arquitectura"),
        prioridad=40,
    ),
    Materia(
        key="los-puertos-que-se-abren-en-el-cortafuegos",
        epigraph_code="IV.9.2",
        title="Los puertos que se abren en el cortafuegos",
        resumen=(
            "La tabla de puertos del tema: qué puerto y qué transporte usa por defecto cada "
            "servicio al que hay que dejar pasar —bases de datos, correo y sus versiones cifradas, "
            "acceso remoto, web, inventariado y las herramientas de gestión— para poder escribir "
            "la regla del cortafuegos."
        ),
        patrones=(_LOS_PUERTOS,),
        patrones_debiles=(r"puerto(s)?",),
        prioridad=10,
        #: La tabla de puertos vive **aquí y solo aquí**: marcarla es lo que hace que el motor la
        #: parta por familias (bases de datos, correo, acceso remoto, web, gestión) y le quite las
        #: notas que solo dicen lo que un puerto **no** es. Sin la marca, la puerta de forma la da
        #: por no partida y el tema no se publica.
        tabla_unica=True,
    ),
    # --- IV.9.3 Acceso remoto seguro a redes ----------------------------------------------------
    Materia(
        key="acceso-remoto-seguro",
        epigraph_code="IV.9.3",
        title="El acceso remoto seguro a la red",
        resumen=(
            "Entrar en la red desde fuera: el acceso remoto y sus protocolos (SSH y SCP, RDP y el "
            "escritorio remoto, VNC y sus desventajas), el escritorio virtual y el VDI con sus "
            "protocolos de acceso, el teletrabajo y sus recomendaciones de seguridad, la "
            "validación del que entra y el control remoto de los puestos."
        ),
        patrones=(
            r"acceso remoto|\brdp\b|escritorio remoto|terminal server|"
            r"\bvdi\b|escritorio virtual|virtual desktop|virtualizacion del escritorio|"
            r"\bvnc\b|virtual network computing|"
            r"\bssh\b|\bscp\b|conexiones ssh|\btelnet\b|"
            r"teletrabajo|trabajadores moviles|acceso telematico|pdas? con telefono|"
            r"herramienta.*acceso remoto|control remoto de puestos",
        ),
        patrones_debiles=(r"remoto", r"escritorio"),
        prioridad=35,
    ),
    # --- IV.9.4 Redes privadas virtuales (VPN) --------------------------------------------------
    Materia(
        key="vpn-y-sus-protocolos",
        epigraph_code="IV.9.4",
        title="Las redes privadas virtuales (VPN) y sus protocolos",
        resumen=(
            "El túnel por el que se entra a la red interna: qué es una VPN y para qué sirve, sus "
            "tipos por nivel (de enlace, de red y de transporte, con SSL/TLS o con IPsec), los "
            "protocolos (IPsec con AH, ESP e IKE, L2TP, PPTP, OpenVPN), el modo túnel y el de "
            "transporte, la asociación de seguridad, el reparto del tráfico y la dirección que "
            "recibe el cliente."
        ),
        patrones=(
            r"\bvpn\b|\brpv\b|red(es)? privada(s)? virtual(es)?|virtual private network|"
            r"\bipsec\b|" + _AH_Y_ESP + r"|"
            r"\bike\b|asociacion(es)? de seguridad|"
            r"\bl2tp\b|\bpptp\b|openvpn|\bwireguard\b|"
            r"tunel(es)?|tunneling|modo tunel|split tunneling|"
            r"que protocolo.*(vpn|tunel)|protocolo de tunneling|"
            r"confidencialidad.*vpn|cifrado de la vpn|"
            r"que tipo de direccion ip recibe.*tunel|unir dos sedes",
        ),
        patrones_debiles=(r"tunel", r"cifrado", r"protocolo"),
        prioridad=20,
    ),
    # --- IV.9.5 Seguridad en el puesto del usuario ----------------------------------------------
    Materia(
        key="seguridad-en-el-puesto-del-usuario",
        epigraph_code="IV.9.5",
        title="La seguridad en el puesto del usuario",
        resumen=(
            "El último metro: las categorías de servicios que protegen el puesto (antivirus, "
            "antispam, control de aplicaciones, filtrado), la lucha contra el malware y el "
            "phishing, el cifrado del disco del equipo, la seguridad del correo (la falsificación "
            "de remitentes), las guías y herramientas del CCN-CERT, el aislamiento de lo que se "
            "ejecuta y el bastionado del puesto."
        ),
        patrones=(
            r"puesto de (trabajo|usuario)|proteccion del puesto|puesto (cliente|de usuario final)|"
            r"seguridad en el puesto|"
            r"antivirus|antimalware|antispam|anti spam|"
            r"control de aplicaciones|lista blanca|lista negra de aplicaciones|"
            r"malware|gusano|troyano|spyware|ransomware|phishing|smishing|vishing|"
            r"seguridad.*correo|correo electronico.*(seguridad|proteccion)|"
            r"falsificacion de direcciones en el envio de correo|"
            r"ccn cert|ccn stic|guia(s)? del ccn|"
            r"cifrado.*(disco|almacenamiento)|filevault|bitlocker|"
            r"medidas? de seguridad para combatir el malware|"
            r"proteger un equipo informatico|"
            r"espacio virtual limitado|sandbox|entorno controlado|"
            r"securizar|bastionado|hardening|secpol|"
            r"milloren la seguretat|us del correu|\bcorreu\b",
        ),
        patrones_debiles=(r"puesto", r"usuario final", r"malware"),
        prioridad=35,
    ),
)

#: El orden del índice: primero cómo es la red y cómo se la vigila, después el perímetro (los
#: cortafuegos, la DMZ y los puertos que hay que abrir), luego cómo se entra desde fuera (el acceso
#: remoto y su túnel) y, al final, el puesto del usuario, que es donde acaba todo.
ORDEN: tuple[str, ...] = (
    "la-seguridad-de-la-red-y-sus-ataques",
    "deteccion-y-prevencion-de-intrusos",
    "cortafuegos-y-su-filtrado",
    "la-dmz-y-la-arquitectura-perimetral",
    "los-puertos-que-se-abren-en-el-cortafuegos",
    "acceso-remoto-seguro",
    "vpn-y-sus-protocolos",
    "seguridad-en-el-puesto-del-usuario",
)

__all__ = ["MATERIAS", "ORDEN"]
