"""El catálogo de materias de IV.10 (redes locales, tipología, técnicas de transmisión, métodos de
acceso y dispositivos de interconexión).

IV.10 es un tema **técnico** y su banco es el más desequilibrado de la serie: de sus 185 grupos de
preguntas, **126 no traen epígrafe** (el 68 %) y son casi todos de lo mismo —la familia de normas
IEEE 802, Ethernet, la VLAN, el Wi-Fi, el cableado y los dispositivos de la red local—, mientras que
los cinco epígrafes oficiales son un esqueleto de 18, 4, 3, 7 y 27 grupos. Por eso el índice va
**por
asunto**, como en IV.7, IV.9, III.3 y II.3, y el enunciado es el que decide.

Doce apartados, en el orden en que se estudia:

- las **normas IEEE 802 y sus grupos de trabajo** en uno (IV.10.1): qué norma cubre qué —el 802.1
  para el enlace, el 802.2 para el control lógico, el 802.3 para Ethernet, el 802.4 para el testigo
  en bus, el 802.5 para el testigo en anillo, el 802.11 para la red inalámbrica, el 802.12, el
  802.15
  para la red personal, el 802.16 para la metropolitana y el 802.22 para la regional—, la relación
  de
  la familia con el modelo OSI y a qué nombre comercial equivale cada versión;
- las **bandas y las velocidades del Wi-Fi** aparte (IV.10.1), porque es el bloque más repetido del
  banco: qué versión trabaja en 2,4, 5, 6 o 60 GHz, cuál llega a 11, 54, 600 Mb/s o varios Gb/s, y
  cuál introduce MIMO, WPA3, la calidad de servicio, el roaming, la gestión de la malla o la
  protección de las tramas de gestión;
- **Ethernet y sus velocidades** (IV.10.1): el estándar 802.3 y su velocidad máxima, las variantes
  de 10, 100 y 1000 Mb/s y de 10, 40 y 100 Gb/s, la fibra y el par trenzado, el tamaño mínimo de
  trama, el campo de redundancia cíclica, el tamaño del campo de datos y la dirección MAC con sus 48
  bits;
- las **VLAN** (IV.10.1): qué son y qué caracteriza a una red de área local virtual, los tipos de
  VLAN por asignación de puertos, la etiqueta de identificador y su tamaño, el máximo de
  identificadores útiles y el protocolo que las define;
- el **Spanning Tree y los bucles** (IV.10.1): para qué sirve el protocolo de árbol de expansión,
sus
  versiones rápida y múltiple, el protocolo de agregación de enlaces, sus estados, sus unidades de
  datos y qué pasa con los caminos redundantes entre conmutadores;
- las **topologías de red** (IV.10.2): la topología en bus, en anillo y en estrella con su punto
  central, la malla, el enlace punto a punto entre equipos vecinos, la topología física y la lógica,
  y cuál tolera el fallo de un equipo;
- el **cableado y los medios de transmisión** (IV.10.3): el par trenzado y sus categorías, la
  frecuencia y la distancia que exige cada velocidad, el cable cruzado y los hilos que se cruzan, el
  estándar de los extremos, la fibra, el cableado estructurado y qué indican las letras de cada
  variante de Ethernet;
- los **métodos de acceso al medio** (IV.10.4): CSMA/CD y CSMA/CA, el acceso por contienda, el paso
  de testigo y la arquitectura en anillo con testigo, el método que solo se usa en las redes de bus
  y el que emplea Gigabit Ethernet;
- los **dispositivos de interconexión** (IV.10.5): qué es cada uno —el repetidor, el concentrador,
el
  puente, el conmutador y el encaminador—, en qué capa del modelo OSI trabaja cada uno, cuál
  segmenta los dominios de colisión pero mantiene uno solo de difusión, la tabla de puenteo y la
  dirección canónica del puente, qué conecta cada uno y la alimentación a través del cable de red;
- la **conmutación y el trabajo del conmutador** (IV.10.5): las técnicas de conmutación de un
  conmutador, la diferencia entre un conmutador y un concentrador, y entre uno de capa 2 y otro de
  capa 3;
- el **encaminamiento y las tablas de encaminamiento** (IV.10.5), que es una decisión de este
  catálogo y se explica abajo: los protocolos de encaminamiento interior y exterior, el
  encaminamiento por vector de distancia, por estado de enlace y por vector de camino, el límite de
  saltos de RIPv2, quién usa tablas de encaminamiento y los algoritmos que emplean los
  encaminadores;
- y los **equipos terminales de datos de la red local** (IV.10.1): las estaciones, los equipos
  terminales y el direccionamiento de difusión de la red.

Cinco decisiones de los patrones, dichas donde se leen:

- **`IEEE` es lo que casi todo el banco comparte, así que no puede decidir por sí solo.** Está en
los
  **débiles** de la primera materia y solo entra cuando ninguna otra ha casado con sus patrones
  propios: sin esa regla, las decenas de preguntas de la familia 802 se las llevaría todas el primer
  apartado por citar la norma;
- **las bandas y las velocidades se buscan como cifras** (`2 4 ?ghz`, `5 ?ghz`, `60 ?ghz`, `11
  mb/s`, `54 mb/s`, `600 mb/s`), porque son lo único que distingue unas versiones del Wi-Fi de otras
  en un banco donde decenas de enunciados empiezan igual;
- **el encaminamiento se queda dentro del tema, y se dice por qué**: este banco pregunta por los
  protocolos de encaminamiento y por las tablas de encaminamiento en el contexto de los equipos de
  interconexión, que es literalmente el epígrafe `IV.10.5` («Dispositivos de interconexión»), y un
  encaminador es un dispositivo de interconexión. Mandarlos fuera dejaría sin apartado a un bloque
  entero de preguntas del tema; se les da el suyo, explícito, en vez de repartirlos por los demás;
- **la tabla de puertos no existe en este tema**, así que ninguna materia lleva la marca
  `tabla_unica`: aquí los números que se memorizan son las categorías de cable, los identificadores
  de VLAN y los tamaños de trama, y no hay una tabla única que pueda duplicarse —que es lo que
  rompió la forma de IV.9 en la tanda anterior—;
- y **lo que es de otro tema no se lava**: la pregunta por los **semáforos** de los sistemas
  operativos es de **II.4** y la definición de **proxy** en el contexto informático es de **IV.9**.
  Dos de las 180 preguntas con clave utilizable, y van a la bandeja del propietario con su motivo
  (`Motivo.SIN_MATERIA_EN_EL_INDICE`).
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: La familia IEEE 802 y qué cubre cada grupo de trabajo.
_NORMAS_IEEE = (
    r"norma(s)? (del ieee|desarrolladas por el ieee|desarrollada por el ieee)",
    r"normal(es)? (desarrolladas|desarrollada) por el ieee",
    r"grupo(s)? de estandares 802|familia ieee 802|estandares? 802",
    r"relacion existente entre el grupo de estandares 802",
    r"que norma del ieee|que estandar (del ieee|ieee) "
    r"(permite|define|normaliza|se ocupa|corresponde)",
    r"a que (estandar|nombre) (del )?ieee|a que estandar ieee corresponde",
    r"802 ?\.? ?(1|2|3|4|5|6|7|9|10|12|14|15|16|17|18|19|20|21|22|23|24)\b",
    r"802 ?15 ?4|802 ?12|802 ?16|802 ?22|802 ?21|802 ?19|802 ?17",
    r"token bus|token ring|paso de testigo",
    r"control de enlace logico|\bllc\b|subnivel mac|\bmac\b",
    r"quien asigna identificadores numericos correlativos",
    r"wpan|wman|wran|wlan|\bwimax\b|wimax ?2|wimax movil|wimax fijo|wimedia|wirelessman",
    r"visible light communication|vehicle-to-x|v2x|wireless access for the vehicular",
    r"100g ?-? ?epon|macsec|media ?-? ?independent handover|wireless network management",
    r"mesh|mallad|autenticacion en redes lan|control de acceso a la red basado en puertos",
)
#: Las bandas y las velocidades del Wi-Fi: el bloque más repetido del banco.
_WIFI = (
    r"wi ?-? ?fi|wifi ?[4-7]\b|\bwlan\b",
    r"2 ?[,.]?4 ?ghz|5 ?ghz|6 ?ghz|60 ?ghz|54 mhz|790 ?mhz|900 ?mhz|5 ?ghz",
    r"\bmimo\b|multiple mimo|antenas mimo|introduce mimo",
    r"\bwpa ?[23]\b|\bwep\b|wifi enhanced security|management frame protection|\bmfp\b",
    r"calidad de servicio.*(ap|cliente)|qos en la comunicacion",
    r"punto(s)? de acceso|roaming|itinerancia|redes? mallad",
    r"wireless gigabit alliance|banda(s)? sin licencia|internet de las cosas|\biot\b",
    r"zigbee|halow|wifi halow|bluetooth|infrarrojos",
    r"priorizacion de las tramas de gestion|asignacion dinamica de canales",
    r"normativa japonesa|paises que tienen restricciones sobre el uso de las frecuencias",
)

#: Ethernet, sus velocidades y su trama.
_ETHERNET = (
    r"ethernet|\b802 ?3\b",
    r"10 ?gigabit|gigabit ethernet|100 ?gigabit|\b10g\b|\b100g\b|2 ?5 y 5 gigabit",
    r"10base ?t|100base ?(t4|f|fx|t1|t)\b|1000base ?t1",
    r"direccion(es)? mac|una mac\b|la mac\b",
    r"trama (ethernet|de ethernet|basica ethernet|vlan)|tamano de trama|payload",
    r"codigo de redundancia ciclica|\bcrc\b",
    r"campo ethertype|ethertype para ipv6",
    r"ethernet conmutada|direccion mac de difusion|broadcast",
    r"estandar ethernet|\b802 ?3\b",
)

#: Las VLAN.
_VLAN = (
    r"\bvlan\b|vlan(es)?|802 ?1q|virtual local area network",
    r"identificador(es)? de vlan|vlan id|\bvid\b",
    r"etiqueta de vlan|tramas ethernet incorporen la etiqueta",
    r"que protocolo define las vlan",
)

#: El Spanning Tree, los bucles y la agregación de enlaces.
_SPANNING_TREE = (
    r"spanning tree|\bstp\b|\brstp\b|\bmstp\b|\bspb\b|arbol de expansion",
    r"802 ?1 ?d|802 ?1 ?w|802 ?1 ?s|802 ?1 ?aq",
    r"protocolo(s)? .*estandarizado por|estandarizado por",
    r"bucles|topologia logica de nivel 2|caminos redundantes",
    r"link aggregation|agregacion de enlaces|\blacp\b|802 ?3 ?ad",
    r"unidades? de datos del protocolo|protocol data unit|\bbpdu\b",
)

#: Las topologías.
_TOPOLOGIAS = (
    r"topologia(s)?",
    r"topologia en (bus|anillo|estrella|malla|arbol)",
    r"enlace punto a punto|punto a punto directo",
    r"punto central|se conectan todos los equipos",
    r"equipos terminal(es)? de datos|\bdte\b",
    r"tipo de red nos estamos refiriendo|si falla uno de ellos",
    r"rotura de un enlace|topologia fisica",
)

#: El cableado y los medios de transmisión.
_CABLEADO = (
    r"par trenzado|\butp\b|\bstp\b|cable(s)? (cruzado|de red|utp|coaxial)",
    r"categoria(s)? (de cable|de cable utp|cable)|\bcat ?[5-8]\b|clase e",
    r"ansi eia tia|eia tia 568|t568|extremos del cable|hilos que se cruzan",
    r"cableado estructurado|fibra optica|medio(s)? de transmision|medios? fisicos",
    r"frecuencia de hasta|mhz|distancia maxima de \d+ metros",
    r"que indican la letra|letras que se han subrayado",
    r"paquete de \d+ kbytes se transmite|velocidad de transmision",
    r"conectar con un cable",
)

#: Los métodos de acceso al medio.
_METODOS_DE_ACCESO = (
    r"csma ?/? ?(cd|ca)|acceso al medio|control de acceso al medio",
    r"paso de testigo|token passing|testigo",
    r"contienda|persistente|escucha por contienda",
    r"metodo(s)? de control de acceso|solo se usa con redes de bus",
    r"arquitectura de red desarrollada por ibm",
    r"campos que configuran la trama",
)

#: Los dispositivos de interconexión y las capas en que trabajan.
_DISPOSITIVOS = (
    r"dispositivo(s)? de interconexion|interconexion de redes",
    r"\bhub\b|concentrador|repetidor|\bswitch\b|conmutador|conmutadores|\bbridge\b|puente|brouter|pasarela|encaminador",
    r"que conectan los routers|que es un switch|que es un puente",
    r"capa del modelo osi (opera|trabaja)|en que capa (del modelo osi )?opera",
    r"dominios? de (colision|difusion)",
    r"tabla de puenteo|direccion canonica de un puente",
    r"power over ethernet|\bpoe\b",
    r"conectar redes que utilizan protocolos de red distintos",
    r"que dispositivo trabaja en la capa 1",
)

#: La conmutación y el trabajo del conmutador.
_CONMUTACION = (
    r"tecnica(s)? de conmutacion|conmutacion (de|por)",
    r"diferencia (ente|entre) un switch y un hub|switch y un hub",
    r"switches? de capa 2 y switches? de capa 3|switch de capa 3 y un router",
)

#: El encaminamiento y las tablas de encaminamiento.
_ENCAMINAMIENTO = (
    r"encaminamiento|enrutamiento|routing",
    r"\brip ?v?2?\b|\bospf\b|\bbgp\b|\beigrp\b|\bigrp\b|\bis-?is\b",
    r"vector ?-? ?distancia|vector de distancia|estado de (los )?enlaces|"
    r"path-vector|vector de camino",
    r"tablas? de encaminamiento",
    r"protocolo de encaminamiento (interno|externo|basado)",
    r"limite maximo de saltos|saltos para que una ruta",
    r"algoritmos? de encaminamiento",
    r"cada router",
)

#: Los equipos terminales y las estaciones de la red local.
_EQUIPOS = (
    r"equipos? terminal(es)?|estacion(es)? de trabajo",
    r"comunicacion entre dos dispositivos en una lan",
    r"red de area local|\blan\b",
)

MATERIAS: tuple[Materia, ...] = (
    # --- IV.10.1 Redes locales ------------------------------------------------------------------
    Materia(
        key="las-normas-ieee-802-y-sus-grupos-de-trabajo",
        epigraph_code="IV.10.1",
        title="Las normas IEEE 802 y sus grupos de trabajo",
        resumen=(
            "El mapa de la familia: qué cubre cada grupo de trabajo —el enlace, el control lógico, "
            "Ethernet, el testigo en bus y en anillo, la red inalámbrica, la red personal, la "
            "metropolitana y la regional—, cómo se relaciona la familia con el modelo OSI de ISO, "
            "a"
            "qué nombre comercial equivale cada versión y quién asigna los identificadores "
            "numéricos de cada capa."
        ),
        patrones=_NORMAS_IEEE,
        patrones_debiles=(r"ieee", r"802"),
        prioridad=50,
    ),
    Materia(
        key="las-bandas-y-las-velocidades-del-wifi",
        epigraph_code="IV.10.1",
        title="Las bandas y las velocidades del Wi-Fi",
        resumen=(
            "Qué versión es cada una y en qué banda trabaja: 2,4, 5, 6 y 60 GHz, las capacidades "
            "de"
            "11, 54, 600 Mb/s y de varios Gb/s, y qué versión introduce las antenas MIMO, WPA3, la "
            "calidad de servicio, el roaming, la malla, la protección de las tramas de gestión y "
            "la"
            "asignación dinámica de canales."
        ),
        patrones=_WIFI,
        patrones_debiles=(r"wifi", r"inalambric"),
        prioridad=20,
    ),
    Materia(
        key="ethernet-sus-velocidades-y-su-trama",
        epigraph_code="IV.10.1",
        title="Ethernet, sus velocidades y su trama",
        resumen=(
            "El estándar de la red local cableada: el 802.3 y su velocidad máxima, las variantes "
            "de"
            "10, 100 y 1000 Mb/s y de 10, 40 y 100 Gb/s sobre fibra y sobre par trenzado, el "
            "tamaño"
            "mínimo de trama, el campo de redundancia cíclica, el tamaño del campo de datos, el "
            "EtherType y la dirección MAC con sus 48 bits."
        ),
        patrones=_ETHERNET,
        patrones_debiles=(r"ethernet",),
        prioridad=25,
    ),
    Materia(
        key="las-vlan",
        epigraph_code="IV.10.1",
        title="Las VLAN",
        resumen=(
            "Segmentar la red local sin cambiar el cable: qué es una VLAN y qué la caracteriza, "
            "los"
            "tipos por asignación de puertos, la etiqueta con el identificador de VLAN y su "
            "tamaño,"
            "el máximo de identificadores útiles y el protocolo que las define."
        ),
        patrones=_VLAN,
        patrones_debiles=(r"vlan",),
        prioridad=15,
    ),
    Materia(
        key="el-spanning-tree-y-los-bucles",
        epigraph_code="IV.10.1",
        title="El Spanning Tree, los bucles y la agregación de enlaces",
        resumen=(
            "Que no haya bucles: para qué sirve el protocolo de árbol de expansión, sus versiones "
            "rápida, múltiple y por puentes, el protocolo de agregación de enlaces y su norma, los "
            "estados del protocolo, sus unidades de datos y qué se hace con los caminos "
            "redundantes"
            "entre conmutadores."
        ),
        patrones=_SPANNING_TREE,
        patrones_debiles=(r"spanning",),
        prioridad=15,
    ),
    Materia(
        key="los-equipos-terminales-de-la-red-local",
        epigraph_code="IV.10.1",
        title="Los equipos terminales y las estaciones de la red local",
        resumen=(
            "Quién está conectado: los equipos terminales de datos, las estaciones de trabajo y la "
            "comunicación entre dos dispositivos dentro de la misma red de área local."
        ),
        patrones=_EQUIPOS,
        patrones_debiles=(r"equipos",),
        prioridad=80,
    ),
    # --- IV.10.2 Tipología ----------------------------------------------------------------------
    Materia(
        key="las-topologias-de-red",
        epigraph_code="IV.10.2",
        title="Las topologías de red",
        resumen=(
            "Cómo se dibuja la red: la topología en bus, la de anillo, la de estrella con su punto "
            "central, la malla y el árbol, el enlace punto a punto directo entre equipos vecinos "
            "que"
            "operan en un solo sentido, la topología física frente a la lógica y cuál sigue "
            "funcionando cuando falla uno de sus equipos."
        ),
        patrones=_TOPOLOGIAS,
        patrones_debiles=(r"topologia",),
        prioridad=20,
    ),
    # --- IV.10.3 Técnicas de transmisión --------------------------------------------------------
    Materia(
        key="el-cableado-y-los-medios-de-transmision",
        epigraph_code="IV.10.3",
        title="El cableado y los medios de transmisión",
        resumen=(
            "El medio por el que viaja la señal: el par trenzado y sus categorías, la frecuencia y "
            "la distancia máxima de cada velocidad, el cable cruzado y los hilos que se cruzan, el "
            "estándar que define los extremos, la fibra óptica, el cableado estructurado y qué "
            "indican las letras de cada variante de Ethernet."
        ),
        patrones=_CABLEADO,
        patrones_debiles=(r"cable", r"cableado"),
        prioridad=20,
    ),
    # --- IV.10.4 Métodos de acceso --------------------------------------------------------------
    Materia(
        key="los-metodos-de-acceso-al-medio",
        epigraph_code="IV.10.4",
        title="Los métodos de acceso al medio",
        resumen=(
            "Quién habla y cuándo: CSMA/CD y CSMA/CA, el acceso por contienda con escucha, el paso "
            "de testigo y la arquitectura en anillo con testigo, el método que solo se usa en las "
            "redes de bus, el CSMA un persistente y el método que emplea Gigabit Ethernet."
        ),
        patrones=_METODOS_DE_ACCESO,
        patrones_debiles=(r"acceso al medio", r"csma"),
        prioridad=15,
    ),
    # --- IV.10.5 Dispositivos de interconexión --------------------------------------------------
    Materia(
        key="los-dispositivos-de-interconexion",
        epigraph_code="IV.10.5",
        title="Los dispositivos de interconexión y las capas en que trabajan",
        resumen=(
            "Los aparatos de la red local: el repetidor, el concentrador, el puente, el "
            "conmutador,"
            "el encaminador y el encaminador-puente, en qué capa del modelo OSI trabaja cada uno, "
            "cuál segmenta los dominios de colisión pero mantiene uno solo de difusión, la tabla "
            "de"
            "puenteo y la dirección canónica del puente, y la alimentación a través del cable de "
            "red."
        ),
        patrones=_DISPOSITIVOS,
        patrones_debiles=(r"dispositivo", r"switch"),
        prioridad=30,
    ),
    Materia(
        key="la-conmutacion-y-el-trabajo-del-conmutador",
        epigraph_code="IV.10.5",
        title="La conmutación y el trabajo del conmutador",
        resumen=(
            "Cómo decide un conmutador: sus técnicas de conmutación, la diferencia entre un "
            "conmutador y un concentrador, y entre uno de capa 2 y otro de capa 3 frente a un "
            "encaminador."
        ),
        patrones=_CONMUTACION,
        patrones_debiles=(r"conmutacion",),
        prioridad=25,
    ),
    Materia(
        key="el-encaminamiento-y-las-tablas-de-encaminamiento",
        epigraph_code="IV.10.5",
        title="El encaminamiento y las tablas de encaminamiento",
        resumen=(
            "Cómo encuentran el camino los equipos de interconexión: los protocolos de "
            "encaminamiento interior y exterior, el encaminamiento por vector de distancia, por "
            "estado de enlace y por vector de camino, el límite de saltos de RIPv2, quién usa "
            "tablas de encaminamiento y qué hace cada encaminador."
        ),
        patrones=_ENCAMINAMIENTO,
        patrones_debiles=(r"encaminamiento", r"enrutamiento"),
        prioridad=35,
    ),
)

#: El orden del índice: primero qué es la red local por dentro —las normas, el Wi-Fi, Ethernet, la
#: VLAN, el árbol de expansión y los equipos—, después cómo se dibuja, por dónde viaja la señal y
#: cómo se reparte el turno de palabra, y al final los aparatos que la unen, con el encaminamiento
#: como última pieza.
ORDEN: tuple[str, ...] = (
    "las-normas-ieee-802-y-sus-grupos-de-trabajo",
    "las-bandas-y-las-velocidades-del-wifi",
    "ethernet-sus-velocidades-y-su-trama",
    "las-vlan",
    "el-spanning-tree-y-los-bucles",
    "los-equipos-terminales-de-la-red-local",
    "las-topologias-de-red",
    "el-cableado-y-los-medios-de-transmision",
    "los-metodos-de-acceso-al-medio",
    "los-dispositivos-de-interconexion",
    "la-conmutacion-y-el-trabajo-del-conmutador",
    "el-encaminamiento-y-las-tablas-de-encaminamiento",
)

__all__ = ["MATERIAS", "ORDEN"]
