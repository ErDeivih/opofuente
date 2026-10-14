"""El catálogo de materias de IV.4 (administración de redes de área local, gestión de usuarios y de
dispositivos, y monitorización y control de tráfico).

IV.4 es el tema de **administrar** una red, no el de diseñarla: de sus **153 grupos de preguntas,
73 no
traen epígrafe** (el 48 %) y el banco se reparte en los cuatro asuntos que el enunciado del tema ya
nombra:

- **la administración de la LAN**: las funciones de gestión —contabilidad, configuración, fallos,
  prestaciones y seguridad—, las áreas del modelo de gestión, el despliegue de plantillas de
  configuración y las topologías de la red de área local, incluida la inalámbrica;
- **la gestión de usuarios**, que es el bloque más grande después de la monitorización: las cuentas
y
  los grupos en Linux con sus ficheros (`/etc/passwd`, `/etc/shadow`, `/etc/gshadow`), las cuentas
  en
  Windows y en PowerShell, el directorio activo y LDAP, las contraseñas y su caducidad, y el acceso
  remoto;
- **la gestión de dispositivos**: MDM, MAM y BYOD, los modelos de propiedad del dispositivo, y los
  protocolos y las herramientas de gestión de activos;
- y **la monitorización y el control del tráfico**, que es el corazón del tema (45 grupos solo en su
  epígrafe oficial y más de la mitad del banco sin epígrafe): el protocolo SNMP con sus componentes,
  sus operaciones y sus versiones, las herramientas de monitorización —Nagios, Zabbix, RMON—, y la
  captura y el análisis del tráfico.

Catorce apartados, en el orden en que se estudia:

- **la administración de la red y sus áreas de gestión** (IV.4.1): qué es la función de
contabilidad y
  qué las demás áreas del modelo de gestión, las áreas que define el modelo OSI, la estructura de la
  información de gestión, y el despliegue de plantillas de configuración sobre máquinas clonadas;
- **las topologías de red de área local y los medios inalámbricos** (IV.4.1): la topología en bus y
su
  afirmación falsa, la que enlaza punto a punto los equipos terminales de datos en un solo sentido,
  la
  red *scatternet* y el protocolo inalámbrico de 5 GHz y 7 Gbps;
- **la red en Linux: interfaces, rutas y comandos** (IV.4.1): mostrar la tabla de rutas y listar las
  rutas existentes, poner una interfaz en modo promiscuo, bajar la interfaz de un servidor con
  agregación de enlaces que no ha conmutado, y desplegar las plantillas de red de las máquinas
  clonadas;
- **la red en Windows: IP, DNS y tabla de rutas** (IV.4.1): ver, liberar y renovar la dirección,
vaciar
  la caché de resolución de nombres, obtener la dirección física de un equipo remoto, conocer la
  dirección asignada automáticamente y mostrar la tabla de enrutamiento;
- **la segmentación de la red y el cortafuegos perimetral** (IV.4.1): qué es un cortafuegos, qué
  tráfico hay que bloquear siempre entre una zona desmilitarizada y la red interna, y para qué se
  usan
  los segmentos de red;
- **las cuentas y los grupos en Linux** (IV.4.2): crear y modificar usuarios y grupos con sus
comandos,
  el grupo primario y los secundarios, bloquear una cuenta, mover el directorio del usuario, los
  campos
  de `/etc/passwd` y de `/etc/shadow` —y cuál no está—, el campo `inactive`, el fichero con las
  contraseñas cifradas, el comando que verifica su integridad y el que modifica la caducidad;
- **las cuentas en Windows y en PowerShell, y las directivas de grupo** (IV.4.2): el comando de
  PowerShell que muestra el identificador de seguridad de un usuario, el que añade un usuario a un
  grupo, el que lista los miembros de un grupo y el que da información detallada de un usuario
  local,
  cambiar la contraseña, conocer los grupos del sistema y qué comando muestra la información de las
  directivas de grupo;
- **el directorio activo, LDAP y las búsquedas en el directorio** (IV.4.3): qué es LDAP y qué un
  fichero LDIF, las ventajas —y la que **no** lo es— de los directorios LDAP para autenticar
  usuarios,
  qué permite un dominio de Windows, las afirmaciones correctas e incorrectas sobre el directorio
  activo, y los comandos para buscar en él;
- **las contraseñas, las políticas de seguridad y el acceso remoto** (IV.4.2): en qué fichero se
cambia
  el número máximo de días de una contraseña en un servidor Debian, qué se define primero al aplicar
  políticas de seguridad por directivas de grupo, la gestión de las contraseñas locales de los
  equipos
  unidos al dominio, restringir por SSH el acceso a un grupo y añadir un usuario a un grupo del
  sistema;
- **la gestión de dispositivos móviles: MDM, MAM y BYOD** (IV.4.3): qué significan las siglas, las
  características que **no** son de una herramienta de gestión de móviles, las soluciones que sí lo
  son,
  cómo se llama el modelo en el que el dispositivo es de la organización y se entrega solo para el
  trabajo, y por qué una directiva de grupo no se aplica a un equipo;
- **los protocolos y las herramientas de gestión de activos** (IV.4.3): qué protocolo está
orientado a
  la gestión de los dispositivos de una red y cuál de los acrónimos **no** corresponde a un
  protocolo
  de gestión, y qué funciones debe tener una herramienta de gestión de activos;
- **el protocolo SNMP: componentes, operaciones y versiones** (IV.4.4), que es el bloque más
repetido
  del banco: para qué sirve y en qué capa vive, qué es la MIB y qué rama contiene el grupo `icmp`,
  qué
  es una unidad de datos de protocolo, las comunidades por defecto y la línea que las cambia, los
  puertos y su relación con UDP, las operaciones —la que recupera tablas grandes y la que notifica
  un
  evento no solicitado—, y las versiones 1, 2c, 2u y 3 con el modelo de seguridad de usuario de la
  RFC 3414 y la mejora principal que introduce;
- **la monitorización de la red: Nagios, Zabbix y RMON** (IV.4.4): qué permite Nagios además de
SNMP y
  qué comando comprueba su configuración, qué protocolo emplea RMON y a qué extiende RMON 2, cómo se
  reinicia el agente de Zabbix, qué sistemas de monitorización existen y cuáles **no** son
  herramientas
  de monitorización, y qué herramienta protege un portátil robado;
- y **la captura del tráfico y la comprobación de puertos** (IV.4.4): la sentencia que captura el
  tráfico de una interfaz y lo guarda en un fichero, qué muestra el comando de estadísticas de
  conexión, cómo saber si un servidor está escuchando por un puerto —con `telnet`, con las
  herramientas
  de sockets o con un analizador— y qué es el *jitter* en la calidad de servicio.

Cinco decisiones de los patrones y de los apartados, dichas donde se leen:

- **la lección de III.3, II.3, II.2 y II.5, aplicada desde el principio**: en este banco «comando»,
  «permite», «sistema», «usuario», «red», «Windows», «Linux» y «siguiente» salen en casi todos los
  enunciados —«comando» aparece 22 veces y «permite» 15— y **ninguno es patrón propio de una
  materia**;
  si contaran, cualquier pregunta caería en el primer apartado que los nombrara. Lo que distingue
  una
  pregunta de otra es **la orden concreta, la sigla o el fichero** (`usermod`, `ipconfig`, `chage`,
  `/etc/shadow`, `snmp`, `mib`, `rmon`, `gpo`, `mdm`), y por eso los patrones miran eso;
- **`puerto` no se usa suelto**: sale en las preguntas de SNMP, en las de SSH y en las de
  comprobación de puertos abiertos. Se pide por su forma —`puerto` seguido de su número, `puertos
  abiertos`, `esta escuchando`— y no por la palabra sola;
- **la lección de II.3, aplicada**: los títulos de los catorce apartados **no comparten las tres
  primeras palabras entre tres de ellos**, y se comprueba con una cuenta antes de correr;
- **el cortafuegos se queda y el ataque no**: las preguntas del **cortafuegos** y de la **zona
  desmilitarizada** son de segmentación de la red de área local —qué tráfico hay que bloquear entre
  la
  zona expuesta y la red interna— y se quedan en su apartado; el **ataque de denegación de servicio
  distribuido** es de **IV.9** y se va a la bandeja;
- y **lo que es de otro tema no se lava**, con su cuenta: el **ataque de denegación distribuida**
es de
  **IV.9**; las **funciones de la capa de transporte** son del modelo de referencia (**IV.7**); los
  **sistemas de almacenamiento SAN y NAS** son de administración de almacenamiento (**IV.2**); y la
  pregunta de la **Ley 7/1985 reguladora de las bases de régimen local** es de **otro bloque**
  —derecho
  administrativo—, no de este tema. Son **4 de las 150 preguntas con clave utilizable** y van a la
  bandeja del propietario con su motivo (`Motivo.SIN_MATERIA_EN_EL_INDICE`) en vez de a un apartado
  inventado.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: La administración de la red y sus áreas de gestión.
_ADMINISTRACION_LAN = (
    r"administracion de (redes|la red)|funcion de contabilidad|contabilidad",
    r"\bfcaps\b|areas? de (la )?gestion|areas que define",
    r"modelo de gestion (de red )?(osi|tcp)|gestion de redes según",
    r"prestaciones|fallos|plantillas con la configuracion de red",
    r"path correcto|maquinas clonadas|carecen de interfaz de usuario",
    r"estructura de la informacion de gestion",
)

#: Las topologías y los medios inalámbricos.
_TOPOLOGIAS = (
    r"topologia(s)?|topologia en bus|anillo|estrella|malla",
    r"punto a punto|equipos? terminal de datos|\bdte\b|un solo sentido",
    r"scatternet|piconet|bluetooth",
    r"inalambric|wifi|wi ?-? ?fi|802 ?\.? ?11|5 ?ghz|banda de los 5",
    r"red de area local inalambrica|\bwlan\b",
)

#: La red en Linux.
_LINUX_RED = (
    r"tabla de rutas|listar las rutas|ruta anterior|anadir una ruta",
    r"\bifconfig\b|\bethtool\b|modo promiscuo|interfaz de red|interfaz eth|\beth\d\b",
    r"bonding|agregacion de enlaces|bajar la interfaz|bajaria la interfaz",
    r"\bip (a|addr|route|link)\b|\bnetplan\b|\brhel\b",
    r"interfaz 0 del servidor|conmutado de manera automatica",
    r"\bping\b|paquetes a la maquina",
)

#: La red en Windows.
_WINDOWS_RED = (
    r"\bipconfig\b|liberar las direcciones|renovar las direcciones",
    r"obtencion automatica de direcciones ip",
    r"cache dns|vaciar la cache|renovar las direcciones ip",
    r"memoria cache|cache de la resolucion",
    r"direcciones mac de un equipo remoto|\barp\b|\bnslookup\b|nombre de dominio a partir",
    r"tabla de enrutamiento del equipo",
    r"cmd\b|simbolo del sistema|en las redes de windows",
)

#: La segmentación y el cortafuegos.
_SEGMENTACION = (
    r"cortafuegos|firewall",
    r"\bdmz\b|zona desmilitarizada|red perimetral",
    r"trafico que generalmente siempre hay que bloquear",
    r"segmentos de red|para gestionar diferentes segmentos",
    r"\bvlan\b|redes? locales? virtuales",
)

#: Las cuentas y los grupos en Linux.
_USUARIOS_LINUX = (
    r"usermod|useradd|adduser|groupmod|groupadd|deluser|userdel",
    r"\bchage\b|caducidad de la contrasena|caducidad de las contrasenas|pass_max_days",
    r"etc ?passwd|etc ?shadow|etc ?gshadow|login ?defs",
    r"\bpwck\b|\bgrpck\b|verificar la integridad de la informacion almacenada",
    r"\bgid\b|\buid\b|grupo primario|grupos secundarios|bloquearle la cuenta",
    r"campo inactive|directorio del usuario|mover el directorio",
    r"ultimo cambio de contrasena|cuando se ha realizado el ultimo cambio",
    r"grupos a los que pertenece un usuario|contrasenas encriptadas de los usuarios",
)

#: Las cuentas en Windows y PowerShell.
_USUARIOS_WINDOWS = (
    r"powershell",
    r"get-aduser|get-adgroup|get-adcomputer|new-aduser|add-adgroupmember|get-localuser",
    r"\bsid\b|identificador de seguridad|valor de sid",
    r"net user|net localgroup|net group|cuentas de usuario que pertenecen",
    r"\bgpo\b|directivas de grupo|politicas de grupo|directiva de grupo",
    r"cambiar la contrasena del usuario|contrasena del usuario generico",
    r"grupos del sistema|informacion detallada sobre este usuario",
    r"ver mas informacion sobre este usuario",
)

#: LDAP y el directorio.
_LDAP = (
    r"\bldap\b|ldif|directorios ldap|openldap",
    r"directorio activo|active directory",
    r"dominio de windows|un dominio permite",
    r"busquedas en el directorio activo|buscar en el directorio",
    r"directorio de usuarios",
)

#: Las contraseñas, las políticas y el acceso remoto.
_CONTRASENAS = (
    r"\bssh\b|acceso remoto|conectarnos a la maquina remota",
    r"politicas de seguridad al grupo de usuarios|definir primero",
    r"contrasenas de la cuenta local|cuenta local de los equipos unidos al dominio",
    r"pertenecen a un grupo llamado|anadiria este usuario a dicho grupo|usuarios_ssh",
    r"anadir el usuario.*al grupo|unir un usuario a un grupo",
)

#: La gestión de dispositivos móviles.
_MDM = (
    r"\bmdm\b|mobile device management|gestion de dispositivos moviles|gestion de moviles",
    r"\bmam\b|mobile application management",
    r"\bbyod\b|bring your own device",
    r"\bcope\b|propiedad de (la|una) organizacion",
    r"robo o extravio|parque de equipos portatiles",
    r"soluciones? mdm|herramienta de gestion de moviles|una solucion para evaluar",
)

#: Los protocolos y las herramientas de gestión.
_GESTION_DISPOSITIVOS = (
    r"protocolo(s)? (de|orientado a la|orientado a) gestion",
    r"gestion de (los )?dispositivos de una red",
    r"acronimos? no (se )?corresponde|no se corresponde con un protocolo de gestion",
    r"herramienta de gestion de activos|funciones que debe tener una herramienta",
    r"administrar los dispositivos de tu red|administrar dispositivos de una red",
    r"protocolo de gestion de red|relacionado con la gestion de redes",
)

#: SNMP.
_SNMP = (
    r"\bsnmp\b|snmp ?v?[123]|snmpv3|snmpv2",
    r"\bmib\b|management information base|rama de la mib|grupo icmp",
    r"protocol data unit|\bpdu\b|unidad de datos de protocolo",
    r"comunidad(es)? (snmp|por defecto)|valores de comunidad|comunidad public",
    r"\busm\b|user-based security model|rfc ?3414|modelo de seguridad de usuario",
    r"\btrap\b|notificar un evento|no solicitados por el administrador",
    r"getbulk|datos voluminosos de una tabla",
    r"agente(s)? snmp|gestor snmp|tres componentes|snmp tiene",
    r"protocolo simple de administracion de redes",
)

#: La monitorización y sus herramientas.
_MONITORIZACION = (
    r"nagios|\bzabbix\b|\bcacti\b|\bmrtg\b|pandora|observium|icinga",
    r"\brmon\b|monitoreo remoto|rmon ?2",
    r"monitorizacion|monitorizar|monitoreo|sistema de monitorizacion",
    r"herramienta de monitorizacion|monitorizacion de instalaciones",
    r"no es una herramienta de monitorizacion|no esta pensada para la monitorizacion",
    r"reiniciaria el agente|comprobar que este servicio esta configurado",
)

#: La captura del tráfico y los puertos.
_TRAFICO = (
    r"tcpdump|wireshark|analizador de trafico|captura del trafico",
    r"netstat|conexiones y estadisticas|estadisticas y conexiones",
    r"estadisticas de red|que puertos tiene abiertos",
    r"puertos? abiertos|esta escuchando|escuchando por el puerto|comprobar si el puerto",
    r"telnet|nmap|comprobar usando el comando telnet",
    r"si llega al puerto|pruebe en linux si llega|comprobar que la comunicacion",
    r"jitter|\bqos\b|calidad de servicio",
)

#: Los comandos de administración del sistema.
_ADMIN_SISTEMA = (
    r"usuarios conectados|nombres de los usuarios conectados",
    r"procesos en ejecucion|informacion de usuarios conectados",
    r"conectar la sesion actual|sesion en una maquina remota",
    r"terminar (con )?un proceso.*maquina remota|terminar un proceso en una",
    r"ultimo reinicio|fecha y hora del ultimo reinicio",
)

MATERIAS: tuple[Materia, ...] = (
    # --- IV.4.1 Administración de redes de área local -------------------------------------------
    Materia(
        key="la-administracion-de-la-red-y-sus-areas-de-gestion",
        epigraph_code="IV.4.1",
        title="La administración de la red y sus áreas de gestión",
        resumen=(
            "Qué se administra y con qué modelo: la función de contabilidad y las demás áreas de "
            "gestión —prestaciones, fallos, configuración y seguridad—, las áreas que define el "
            "modelo"
            "de gestión del modelo OSI, la estructura de la información de gestión, y el "
            "despliegue de"
            "plantillas de configuración sobre máquinas clonadas."
        ),
        patrones=_ADMINISTRACION_LAN,
        prioridad=45,
    ),
    Materia(
        key="las-topologias-de-la-lan-y-los-medios-inalambricos",
        epigraph_code="IV.4.1",
        title="Las topologías de red de área local y los medios inalámbricos",
        resumen=(
            "Cómo se conectan los equipos: la topología en bus y su afirmación falsa, la que "
            "enlaza"
            "punto a punto los equipos terminales de datos que operan en un solo sentido, la red "
            "*scatternet*, y el protocolo inalámbrico de 5 GHz que alcanza 7 Gbps."
        ),
        patrones=_TOPOLOGIAS,
        prioridad=35,
    ),
    Materia(
        key="la-red-en-linux-interfaces-rutas-y-comandos",
        epigraph_code="IV.4.1",
        title="La red en Linux: interfaces, rutas y comandos",
        resumen=(
            "Configurar la red desde la consola de Linux: mostrar la tabla de rutas y listar las "
            "rutas"
            "existentes, poner una interfaz en modo promiscuo, bajar la interfaz de un servidor "
            "con"
            "agregación de enlaces que no ha conmutado, y desplegar las plantillas de red de las "
            "máquinas clonadas."
        ),
        patrones=_LINUX_RED,
        prioridad=25,
    ),
    Materia(
        key="la-red-en-windows-ip-dns-y-tabla-de-rutas",
        epigraph_code="IV.4.1",
        title="La red en Windows: IP, DNS y tabla de rutas",
        resumen=(
            "Configurar la red desde la consola de Windows: ver, liberar y renovar la dirección, "
            "vaciar la caché de resolución de nombres, obtener la dirección física de un equipo "
            "remoto, conocer la dirección asignada automáticamente y mostrar la tabla de "
            "enrutamiento."
        ),
        patrones=_WINDOWS_RED,
        prioridad=25,
    ),
    Materia(
        key="la-segmentacion-de-la-red-y-el-cortafuegos",
        epigraph_code="IV.4.1",
        title="La segmentación de la red y el cortafuegos perimetral",
        resumen=(
            "Separar la red para protegerla: qué es un cortafuegos, qué tráfico hay que bloquear "
            "siempre entre una zona desmilitarizada y la red interna, y para qué se usan los "
            "segmentos"
            "de red."
        ),
        patrones=_SEGMENTACION,
        prioridad=30,
    ),
    # --- IV.4.2 Gestión de usuarios -------------------------------------------------------------
    Materia(
        key="las-cuentas-y-los-grupos-en-linux",
        epigraph_code="IV.4.2",
        title="Las cuentas y los grupos en Linux",
        resumen=(
            "Crear, modificar y bloquear cuentas: los comandos de usuarios y grupos, el grupo "
            "primario"
            "y los secundarios, mover el directorio del usuario, los campos de `/etc/passwd` y de "
            "`/etc/shadow` —y cuál no está—, el campo `inactive`, el fichero con las contraseñas "
            "cifradas, el comando que verifica su integridad y el que modifica la caducidad."
        ),
        patrones=_USUARIOS_LINUX,
        prioridad=20,
    ),
    Materia(
        key="las-cuentas-en-windows-powershell-y-las-directivas",
        epigraph_code="IV.4.2",
        title="Las cuentas en Windows y en PowerShell, y las directivas de grupo",
        resumen=(
            "Gestionar cuentas en Windows: el comando de PowerShell que muestra el identificador "
            "de"
            "seguridad de un usuario, el que añade un usuario a un grupo, el que lista los "
            "miembros de"
            "un grupo y el que da información detallada de un usuario local, cambiar la "
            "contraseña,"
            "conocer los grupos del sistema y qué comando muestra la información de las directivas "
            "de"
            "grupo."
        ),
        patrones=_USUARIOS_WINDOWS,
        prioridad=20,
    ),
    Materia(
        key="el-directorio-activo-ldap-y-las-busquedas",
        epigraph_code="IV.4.3",
        title="El directorio activo, LDAP y las búsquedas en el directorio",
        resumen=(
            "El directorio donde viven las cuentas: qué es LDAP y qué un fichero LDIF, las "
            "ventajas"
            "—y la que **no** lo es— de los directorios LDAP para autenticar usuarios, qué permite "
            "un"
            "dominio de Windows, las afirmaciones correctas e incorrectas sobre el directorio "
            "activo y"
            "los comandos para buscar en él."
        ),
        patrones=_LDAP,
        prioridad=15,
    ),
    Materia(
        key="las-contrasenas-las-politicas-y-el-acceso-remoto",
        epigraph_code="IV.4.2",
        title="Las contraseñas, las políticas de seguridad y el acceso remoto",
        resumen=(
            "Que la contraseña caduque y que solo entre quien deba: en qué fichero se cambia el "
            "número"
            "máximo de días de una contraseña en un servidor Debian, qué se define primero al "
            "aplicar"
            "políticas de seguridad por directivas de grupo, la gestión de las contraseñas locales "
            "de"
            "los equipos unidos al dominio, restringir por SSH el acceso a un grupo y añadir un "
            "usuario"
            "a un grupo del sistema."
        ),
        patrones=_CONTRASENAS,
        prioridad=30,
    ),
    # --- IV.4.3 Gestión de dispositivos ---------------------------------------------------------
    Materia(
        key="la-gestion-de-dispositivos-moviles-mdm",
        epigraph_code="IV.4.3",
        title="La gestión de dispositivos móviles: MDM, MAM y BYOD",
        resumen=(
            "Los móviles dentro de la organización: qué significan MDM, MAM y BYOD, las "
            "características"
            "que **no** son de una herramienta de gestión de móviles, las soluciones que sí lo "
            "son, cómo"
            "se llama el modelo en el que el dispositivo es de la organización y se entrega solo "
            "para"
            "el trabajo, y por qué una directiva de grupo no se aplica a un equipo."
        ),
        patrones=_MDM,
        prioridad=15,
    ),
    Materia(
        key="los-protocolos-y-las-herramientas-de-gestion-de-activos",
        epigraph_code="IV.4.3",
        title="Los protocolos y las herramientas de gestión de activos",
        resumen=(
            "Con qué se gobiernan los dispositivos: qué protocolo está orientado a la gestión de "
            "los"
            "dispositivos de una red y cuál de los acrónimos **no** corresponde a un protocolo de "
            "gestión, y qué funciones debe tener una herramienta de gestión de activos."
        ),
        patrones=_GESTION_DISPOSITIVOS,
        prioridad=25,
    ),
    Materia(
        key="los-comandos-de-administracion-del-sistema",
        epigraph_code="IV.4.2",
        title="Los comandos de administración del sistema: sesiones y procesos",
        resumen=(
            "Las órdenes del día a día del administrador: quién está conectado y con qué procesos, "
            "cómo se abre una sesión en una máquina remota, cómo se termina un proceso que corre "
            "en otro equipo y cómo se averigua la fecha y la hora del último reinicio."
        ),
        patrones=_ADMIN_SISTEMA,
        prioridad=40,
    ),
    # --- IV.4.4 Monitorización y control de tráfico ---------------------------------------------
    Materia(
        key="el-protocolo-snmp-sus-componentes-y-sus-versiones",
        epigraph_code="IV.4.4",
        title="El protocolo SNMP: componentes, operaciones y versiones",
        resumen=(
            "El protocolo de gestión por excelencia: para qué sirve y en qué capa vive, qué es la "
            "MIB y"
            "qué rama contiene el grupo `icmp`, qué es una unidad de datos de protocolo, las "
            "comunidades por defecto y la línea que las cambia, los puertos y su relación con UDP, "
            "las"
            "operaciones —la que recupera tablas grandes y la que notifica un evento no "
            "solicitado—, y"
            "las versiones 1, 2c, 2u y 3 con el modelo de seguridad de usuario de la RFC 3414 y la "
            "mejora principal que introduce."
        ),
        patrones=_SNMP,
        prioridad=10,
    ),
    Materia(
        key="la-monitorizacion-de-la-red-nagios-zabbix-y-rmon",
        epigraph_code="IV.4.4",
        title="La monitorización de la red: Nagios, Zabbix y RMON",
        resumen=(
            "Con qué se vigila la red: qué permite Nagios además de SNMP y qué comando comprueba "
            "su"
            "configuración, qué protocolo emplea RMON y a qué extiende RMON 2, cómo se reinicia el "
            "agente de Zabbix, qué sistemas de monitorización existen y cuáles **no** son "
            "herramientas"
            "de monitorización, y qué herramienta protege un portátil robado."
        ),
        patrones=_MONITORIZACION,
        prioridad=15,
    ),
    Materia(
        key="la-captura-del-trafico-y-la-comprobacion-de-puertos",
        epigraph_code="IV.4.4",
        title="La captura del tráfico y la comprobación de puertos",
        resumen=(
            "Mirar lo que pasa por la red: la sentencia que captura el tráfico de una interfaz y "
            "lo"
            "guarda en un fichero, qué muestra el comando de estadísticas de conexión, cómo saber "
            "si un"
            "servidor está escuchando por un puerto —con `telnet`, con las herramientas de sockets "
            "o"
            "con un analizador— y qué es el *jitter* en la calidad de servicio."
        ),
        patrones=_TRAFICO,
        prioridad=20,
    ),
)

#: El orden del índice: primero administrar la red —sus áreas, sus topologías, los comandos de Linux
#: y de Windows y la segmentación—, después las personas —cuentas en Linux, cuentas en Windows, el
#: directorio y las contraseñas—, luego los dispositivos —móviles y activos— y, al final, lo que más
#: se pregunta: SNMP, la monitorización y la captura del tráfico.
ORDEN: tuple[str, ...] = (
    "la-administracion-de-la-red-y-sus-areas-de-gestion",
    "las-topologias-de-la-lan-y-los-medios-inalambricos",
    "la-red-en-linux-interfaces-rutas-y-comandos",
    "la-red-en-windows-ip-dns-y-tabla-de-rutas",
    "la-segmentacion-de-la-red-y-el-cortafuegos",
    "las-cuentas-y-los-grupos-en-linux",
    "las-cuentas-en-windows-powershell-y-las-directivas",
    "el-directorio-activo-ldap-y-las-busquedas",
    "las-contrasenas-las-politicas-y-el-acceso-remoto",
    "los-comandos-de-administracion-del-sistema",
    "la-gestion-de-dispositivos-moviles-mdm",
    "los-protocolos-y-las-herramientas-de-gestion-de-activos",
    "el-protocolo-snmp-sus-componentes-y-sus-versiones",
    "la-monitorizacion-de-la-red-nagios-zabbix-y-rmon",
    "la-captura-del-trafico-y-la-comprobacion-de-puertos",
)

__all__ = ["MATERIAS", "ORDEN"]
