"""El catálogo de materias de IV.1 (administración del sistema operativo y software de base).

IV.1 es un tema **técnico** y su banco lo dice sin género de dudas: de sus 229 grupos de
preguntas, 145 no traen epígrafe y casi todos empiezan por «¿qué comando…?», «¿qué directorio…?» o
«¿qué versión…?». Lo que estructura el tema no es un asunto suelto sino el **trabajo del
administrador**, así que el índice va **por asunto**, como en IV.7, III.5, III.9 y IV.8, y este
catálogo lo abre en nueve apartados:

- el **oficio del administrador** en uno: qué hace, de qué responde, las herramientas con las que
  gobierna un parque (la gestión de la configuración) y las imágenes y el despliegue de software;
- los **usuarios, los grupos y los permisos** en uno: crear y borrar cuentas, los grupos, la
  contraseña, el `home` y la `shell`, la propiedad de los ficheros, los permisos y `root`;
- los **ficheros y el trabajo en la shell** en uno: la jerarquía de directorios y para qué es cada
  uno, ver y buscar texto en un fichero, copiar, mover, renombrar y enlazar, comprimir, la
  redirección, la tubería y el historial;
- los **procesos, los servicios y el arranque** en uno: los procesos y las señales, `systemd`, los
  niveles de ejecución, el gestor de arranque y el firmware, el apagado, la planificación de tareas
  y los comandos que informan del estado de la máquina (hardware, kernel, versión y memoria);
- los **discos, los sistemas de ficheros y los volúmenes** en uno: `ext2/3/4` y `XFS`, formatear,
  comprobar la integridad, montar, `fstab`, la swap, las particiones, LVM, RAID y las cuotas;
- el **software de base: paquetes, versiones y actualización** en uno: `apt`/`dpkg`, `rpm`, `yum`,
  `pacman`, los repositorios y la caché, instalar y desinstalar, y las versiones **con nombre** de
  Debian y macOS, que el banco pregunta una a una;
- la **administración de Windows** en uno: PowerShell y `cmd`, las directivas de grupo y de
  seguridad, el registro, los servicios de Windows y el escritorio remoto;
- la **red del sistema** en uno: la configuración del equipo (interfaces, rutas, `resolv.conf`),
  la hora (`NTP`), el acceso remoto y el fichero de `log`;
- y el **mantenimiento y la reparación** en uno (el epígrafe IV.1.2): los tipos de mantenimiento,
  `sfc /scannow`, la relación de confianza con el dominio y la pantalla azul.

Cuatro decisiones de los patrones, dichas donde se leen:

- **nada de patrones de relleno.** «fichero», «comando», «sistema» o «servidor» salen en media
  asignatura, así que no son patrones propios: van en los **débiles**, que solo deciden cuando
  ninguna materia ha casado. Sin esa regla, «¿Cómo se formatea un dispositivo a ext2?» acabaría en
  el apartado de la shell por decir «fichero» antes que `ext2`;
- **los comandos se piden por lo que hacen, no por su nombre.** El banco pregunta «¿qué comando
  muestra la versión del kernel?», no «¿para qué sirve `uname`?». Por eso el apartado del estado de
  la máquina se reconoce por el **objeto** que se consulta (`versión del kernel`, `nombre del host`,
  `memoria disponible`) y no por la fórmula «¿qué comando…?», que encabezaría medio tema;
- **`¿qué directorio…?` sí es un patrón propio**, y no contradice lo anterior: esa fórmula aparece
  19 veces y **siempre** pregunta por la jerarquía de directorios de Linux;
- y las **versiones con nombre** (`Hamm`, `Woody`, `Bookworm`, las de macOS) se piden con
  (`nombre|versión`) + (`recibe|corresponde`), que es como están escritas todas, en vez de con
  `\\bdebian\\b` a secas: con esa, «En Debian 8.7, ¿cuál es la ruta del fichero de log…?» acabaría
  hablando de versiones en lugar de `log`.

Lo que el banco trae de **otro tema** —el `ERS` y los tipos de mantenimiento de Métrica v3, que son
de III.9; la desnormalización y ANSI/SPARC, que son de III.1; la caché L1, que es de II.1; el
servicio ITSM y el CAU, que son de IV.5, y Exchange y Kubernetes, que son de IV.3— **no** se lava
dentro de un apartado que no existe: va a la bandeja del propietario con su motivo
(`Motivo.SIN_MATERIA_EN_EL_INDICE`), que es lo que manda el índice.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Las versiones **con nombre**: el banco pregunta «¿qué versión recibe el nombre de "Hamm"?»,
#: «¿cuál es el nombre de la versión 15 de Mac?» y «¿qué versión se corresponde con "Wheezy"?».
#: Se piden por la fórmula que usan todas y no por `debian`/`mac` sueltos, que salen en preguntas
#: de otras materias (la ruta del `log`, la resolución de nombres).
_VERSIONES_CON_NOMBRE = (
    r"\b(nombre|version)\s+(recibe|corresponde|se corresponde)|nombre de la version|"
    r"denomina la version|distribucion linux|version \d+ de (mac|macos|os x)|"
    r"ultima version de debian|version de mac\b"
)

#: El trabajo del administrador: el banco pregunta por sus funciones y por las herramientas con las
#: que se gobierna un parque (`Ansible`, `Salt`, las imágenes y el despliegue).
_EL_OFICIO = (
    r"administrador(es)? de(l)? (sistema|sistemas)|\bfunciones del administrador|"
    r"responsabilidad(es)? de(l| un) (administrador|tecnico)|tareas (del|de un) administrador|"
    r"no es (una )?funcion del administrador|perfil profesional"
)

#: Los usuarios, los grupos y los permisos. La contraseña se pide **con usuario delante**: suelta
#: aparece en preguntas de Windows que van al apartado de Windows.
_USUARIOS = (
    r"crear un usuario|anadir un usuario|afiadir un usuario|borrar un usuario|"
    r"eliminar(i?a)? al usuario|usuario (llamado|denominado)|cuentas? de usuario|"
    r"perfil de usuario|\bhome_dir\b|directorio principal|shell que usara|"
    r"\buseradd\b|\badduser\b|\busermod\b|\buserdel\b|\bgroupadd\b|\bgroupdel\b|"
    r"\bpasswd\b|cambiar la contrasena|contrasena de un usuario"
)

#: La jerarquía de directorios del sistema: 19 preguntas del banco empiezan por «¿qué directorio…?».
_DIRECTORIOS = (
    r"que directorio|directorio(s)? (se utiliza|de (inicio|trabajo|raiz|usuario|log|arranque|"
    r"dispositivos))|jerarquia de directorios|sistema de archivos de linux"
)

#: El estado de la máquina: lo que el banco consulta con un comando (hardware, kernel, versión y
#: memoria). Se reconoce por el **objeto** de la consulta y no por «¿qué comando…?».
_ESTADO_DE_LA_MAQUINA = (
    r"(muestra|mostrar|muestre) (los componentes hardware|la informacion del procesador|"
    r"el nombre del host|la arquitectura de la maquina|el tiempo que el sistema lleva iniciado|"
    r"la version del kernel|el nombre del kernel|"
    r"la version de (la distribucion|rhel|debian|ubuntu)|"
    r"el nombre (del|de la) (sistema operativo|distribucion)|"
    r"el nombre en codigo de la distribucion|la descripcion de la distribucion|"
    r"toda la informacion)|"
    r"nombre de la maquina|version del kernel|memoria (disponible|libre|del sistema)|"
    r"consulta de parametros"
)

MATERIAS: tuple[Materia, ...] = (
    # --- IV.1.1 Administración del sistema operativo y software de base -------------------------
    Materia(
        key="el-oficio-de-administrador",
        epigraph_code="IV.1.1",
        title="El oficio de administrador: funciones y gestión del parque",
        resumen=(
            "Qué hace un administrador de sistemas y de qué responde, el perfil profesional con el "
            "que se corresponde cada tarea, y las herramientas con las que se gobierna un parque "
            "entero: la gestión de la configuración automatizada (Ansible, Salt, Puppet, Vagrant), "
            "el inventariado de equipos y software, las imágenes maestras y el despliegue de "
            "aplicaciones corporativas."
        ),
        patrones=(
            _EL_OFICIO,
            r"\bansible\b|\bsalt\b|\bpuppet\b|\bchef\b|\bvagrant\b|terraform|"
            r"gestion de la configuracion|configuracion automatizada|automatizar la configuracion|"
            r"herramienta(s)? de automatizacion|gestionar la configuracion",
            r"imagen (de (un )?equipo|maestra)|clonar (un )?equipo|"
            r"despliegue de (software|aplicaciones)|distribuir en entorno|"
            r"paquete de software de usuario|aplicaciones corporativas|inventariado|"
            r"inventario de (equipos|software)|parque (informatico|de equipos)",
        ),
        patrones_debiles=(r"administrador(es)?", r"automatizacion", r"configuracion"),
        prioridad=60,
    ),
    Materia(
        key="usuarios-grupos-y-permisos",
        epigraph_code="IV.1.1",
        title="Los usuarios, los grupos y los permisos",
        resumen=(
            "Quién puede hacer qué: crear, modificar y borrar usuarios y grupos, el directorio "
            "principal y la shell de cada cuenta, la contraseña, los privilegios de `root` y "
            "`sudo`, la propiedad de los ficheros, los permisos (incluidos los de todos los "
            "usuarios) y las cuotas de disco por usuario."
        ),
        patrones=(
            _USUARIOS,
            r"\bchmod\b|\bchown\b|\bchgrp\b|\bumask\b|\bsetfacl\b|\bgetfacl\b|permisos de|"
            r"propiedad de un usuario|propietario de los ficheros|"
            r"modificables por todos los usuarios|evitar que .* pueda borrar|"
            r"privilegios de root|\bsudo\b|perteneciente al grupo|pertenezca al grupo|"
            r"grupo de usuarios|miembro(s)? del grupo",
            r"\buid\b|\bgid\b|identificador de usuario",
        ),
        patrones_debiles=(r"usuario(s)?", r"grupo(s)?", r"permiso(s)?"),
        prioridad=30,
    ),
    Materia(
        key="ficheros-y-trabajo-en-la-shell",
        epigraph_code="IV.1.1",
        title="Los ficheros, los directorios y el trabajo en la shell",
        resumen=(
            "El trabajo del día a día en la consola: para qué es cada directorio del sistema, ver "
            "y buscar texto dentro de un fichero, copiar, mover, renombrar y enlazar, comprimir y "
            "empaquetar, sincronizar carpetas, la redirección y la tubería, el historial de "
            "comandos y las variables de entorno."
        ),
        patrones=(
            _DIRECTORIOS,
            r"primeras \d+ (filas|lineas)|ultimas \d+ lineas|\bhead\b|\btail\b|\bcat\b|\bmore\b|"
            r"\bless\b|\bwc\b|lista de palabras|\bgrep\b|\bfind\b|\bwhich\b|\bwhereis\b|"
            r"\blocate\b|\bman\b|ubicacion del binario|ruta completa de un comando|"
            r"manuales del comando",
            r"renombrar|renombraria|copiar (una carpeta|un fichero|ficheros)|mover un fichero|"
            r"\bcp\b|\bmv\b|\brm\b|\bmkdir\b|enlace simbolico|enlace duro|\bln\b|"
            r"\btar\b|\bgzip\b|\bgunzip\b|\bbzip2\b|\bzip\b|comprimir|descomprimir|empaquetar|"
            r"backup del directorio|crear un backup|copia de seguridad del directorio",
            r"sincronizar|rsync|redireccion(es)?|tuberia|\bpipeline\b|\becho\b|"
            r"historial de comandos|repetir el ultimo comando|shell bash|"
            r"interprete de comandos|variable(s)? de entorno|\bpath\b",
        ),
        patrones_debiles=(r"fichero(s)?", r"archivo(s)?", r"directorio(s)?"),
        prioridad=55,
    ),
    Materia(
        key="procesos-servicios-y-arranque",
        epigraph_code="IV.1.1",
        title="Los procesos, los servicios y el arranque del sistema",
        resumen=(
            "Lo que está pasando en la máquina: los procesos y su estado, las señales y cómo se "
            "termina un proceso, el identificador de proceso, `systemd` y los servicios, los "
            "niveles de ejecución y el gestor de arranque con el firmware, el apagado y el "
            "reinicio, la planificación de tareas, la cola de impresión y los límites del sistema; "
            "y los comandos que informan del estado de la máquina (hardware, kernel, versión y "
            "memoria)."
        ),
        patrones=(
            r"\bproceso(s)?\b.*(ejecucion|estado|listar|matar|local)|listar.*procesos|"
            r"procesos en ejecucion|id de proceso|\bpid\b|senal(es)?\b|"
            r"finalizacion ordenada de un proceso|\bkill\b|\bkillall\b|\bsigterm\b|\bsigkill\b|"
            r"\bsighup\b",
            r"\bsystemd\b|\bsystemctl\b|activar el servicio|servicio httpd|parar un servicio|"
            r"arrancar un servicio|\bdaemon\b|demonio(s)?|ejecuciones periodicas|\bcron\b|"
            r"\bcrontab\b|planificar.*(tarea|apagado|ejecucion)|tarea(s)? programada(s)?|"
            r"cola de impresion|maximo permitido de ficheros abiertos|\bulimit\b",
            r"\brunlevel\b|nivel(es)? de ejecucion|\binit\b|arranque del sistema|"
            r"gestor de arranque|\bgrub\b|\bbios\b|\buefi\b|"
            r"programa incorporado en un microprocesador|firmware|\bshutdown\b|apagar el sistema|"
            r"apagado del sistema|reiniciar el sistema|\breboot\b|\bhalt\b|\bwho\b",
            _ESTADO_DE_LA_MAQUINA,
            r"\blscpu\b|\blshw\b|\bdmesg\b|\buname\b|\bfree\b|\bvmstat\b|\biostat\b|\bmpstat\b|"
            r"\buptime\b",
        ),
        patrones_debiles=(r"comando(s)?", r"servicio(s)?", r"sistema"),
        prioridad=35,
    ),
    Materia(
        key="discos-sistemas-de-ficheros-y-volumenes",
        epigraph_code="IV.1.1",
        title="Los discos, los sistemas de ficheros y los volúmenes",
        resumen=(
            "El almacenamiento de la máquina: los sistemas de ficheros (`ext2`, `ext3`, `ext4` y "
            "`XFS`), formatear y crear un sistema de ficheros, comprobar su integridad y "
            "repararlo, montar y desmontar con `fstab`, la memoria de intercambio, las "
            "particiones, los volúmenes lógicos y el RAID, el uso del disco y las cuotas."
        ),
        patrones=(
            r"\bext ?[234]\b|\bxfs\b|\breiserfs\b|\bbtrfs\b|\bnfs\b|\bfsck\b|\be2fsck\b|"
            r"formatear|formatea un|crear un sistema (de ficheros|ext|linux)|\bmkfs\b|"
            r"comprobar la integridad|comprueba la integridad|integridad de un sistema de ficheros",
            r"punto de montaje|montar (un|el)|\bmount\b|\bumount\b|sistemas? de ficheros|"
            r"se montaran en el arranque|\bfstab\b|listar los sistemas de ficheros",
            r"\bswap\b|\bmkswap\b|\bswapon\b|memoria de intercambio|ficheros swap",
            r"particion(es)?|\blvm\b|volumen logico|grupo de volumenes|\braid\b|\bmdadm\b|"
            r"capacidad neta de almacenamiento|\bdd if\b|\bdd of\b|uso de disco|\bdf\b|\bdu\b|"
            r"espacio (libre|disponible)",
            r"cuota(s)? de disco|limite de cuota|disco duro|capacidad del disco",
        ),
        patrones_debiles=(r"disco(s)?", r"almacenamiento", r"capacidad"),
        prioridad=25,
    ),
    Materia(
        key="paquetes-versiones-y-actualizacion",
        epigraph_code="IV.1.1",
        title="El software de base: paquetes, versiones y actualización",
        resumen=(
            "El software instalado y cómo se cambia: los gestores de paquetes (`apt` y `dpkg`, "
            "`rpm`, `yum` y `dnf`, `pacman`), los repositorios y la caché, instalar, listar, "
            "consultar y desinstalar —con o sin su configuración—, saber si algo está instalado, y "
            "las versiones con nombre de Debian y macOS."
        ),
        patrones=(
            r"\bapt\b|\bdpkg\b|\baptitude\b|\brpm\b|\byum\b|\bdnf\b|\bzypper\b|pacman|"
            r"gestor de paquetes|repositorio(s)? de (paquetes|software)|"
            r"paquete(s)? (instalado|disponible)|instalar un paquete|lista(r)? los paquetes|"
            r"desinstalar|eliminar un paquete|eliminando su fichero de configuracion|"
            r"cache de paquetes|esta instalado el paquete|ha sido instalado|no tiene instalado|"
            r"instalaciones y desinstalaciones de software|activar el modulo|a2enmod|"
            r"informacion (sobre|acerca del) dicho paquete|informacion acerca del paquete",
            _VERSIONES_CON_NOMBRE,
            r"actualizar( todos)? los paquetes|ultima version|actualizacion (de software|software)|"
            r"actualice el servidor|actualizar el servidor|ultimo software disponible|"
            r"mantener actualizado|windows installer|software instalado|listado del software",
        ),
        patrones_debiles=(r"paquete(s)?", r"version(es)?", r"instalar"),
        prioridad=20,
    ),
    Materia(
        key="administracion-de-windows",
        epigraph_code="IV.1.1",
        title="La administración de Windows: herramientas, directivas y PowerShell",
        resumen=(
            "El puesto Windows: los `cmdlet` de PowerShell y los comandos del intérprete `cmd`, "
            "las directivas de grupo y de seguridad (GPO, `secpol`, `rsop`), el registro, las "
            "cuentas locales y los perfiles, los servicios de Windows, la gestión de dispositivos "
            "móviles, el escritorio remoto y las herramientas administrativas del sistema."
        ),
        patrones=(
            r"powershell|cmdlet|simbolo del sistema|interprete de comandos cmd|"
            r"caracteristicas de windows",
            r"directivas de (grupo|seguridad)|\bgpo\b|\bsecpol\b|\brsop\b|gpupdate|gpresult|"
            r"editor del registro|registro de windows|regedit|politica de grupo|directorio activo",
            r"\bwindows\b|servicio de windows|\bmdm\b|gestion de dispositivos moviles|"
            r"proyecto honolulu|windows admin center|escritorio remoto|\brdp\b|"
            r"cuentas de usuario que pertenecen al grupo administradores",
        ),
        patrones_debiles=(r"microsoft", r"escritorio", r"puesto cliente"),
        prioridad=40,
    ),
    Materia(
        key="la-red-del-sistema",
        epigraph_code="IV.1.1",
        title="La red del sistema: interfaz, nombres, hora y acceso remoto",
        resumen=(
            "La red del propio equipo: la interfaz y su dirección, la resolución de nombres y el "
            "fichero `resolv.conf`, las rutas y la puerta de enlace, la sincronización de la hora "
            "con NTP, el servidor de SSH, los puertos en escucha, el fichero de `log` del sistema "
            "y el encendido remoto."
        ),
        patrones=(
            r"resolv conf|fichero(d)? de dns|servidor(es)? de dns|servidores del grr|"
            r"configurar el dns|cache dns|\betc hosts\b|resolucion de nombres",
            r"ifconfig|\bip (a|addr|address)\b|interfaz de red|obtener la ip|ip del servidor|"
            r"direccion ip del servidor",
            r"ruta persistente|anadir una ruta|\bip route\b|\broute\b|puerta de enlace|"
            r"gateway.*firewall",
            r"\bntp\b|sincronizacion horaria|sincronizar.*hora|servidores? de hora",
            r"\bssh\b|\bscp\b|\bsftp\b|servidor de ssh|escuchando por el puerto|"
            r"puerto(s)? de escucha|fichero de log|\bvar log\b|mensajes como el siguiente|"
            r"registro de sucesos|encender.*remotamente|wake on lan|\bwol\b",
        ),
        patrones_debiles=(r"red(es)?", r"servidor(es)?", r"puerto(s)?"),
        prioridad=65,
    ),
    # --- IV.1.2 Actualización, mantenimiento y reparación del sistema operativo -----------------
    Materia(
        key="mantenimiento-y-reparacion",
        epigraph_code="IV.1.2",
        title="El mantenimiento del sistema y su reparación",
        resumen=(
            "Mantener y arreglar: los tipos de mantenimiento (preventivo, correctivo, perfectivo, "
            "adaptativo y evolutivo) y las tareas que caben en cada uno, la reparación de los "
            "ficheros del sistema (`sfc /scannow`), la relación de confianza de la estación con el "
            "dominio, la pantalla azul y la restauración del sistema."
        ),
        patrones=(
            r"mantenimiento (preventivo|correctivo|perfectivo|adaptativo|evolutivo|del sistema|"
            r"y reparacion)|tipos? de mantenimiento|mantenimiento (de|del) (software|sistemas)|"
            r"tarea(s)? de mantenimiento|actividades? de mantenimiento|"
            r"esencial para el mantenimiento|encuadrar dentro del mantenimiento",
            r"\bsfc\b|scannow|reparar (el|un|la) (sistema|fichero|instalacion|sistema operativo)|"
            r"reparacion (del|de un) sistema|restauracion del sistema|punto de restauracion|"
            r"revertir una actualizacion|reparar el arranque",
            r"relacion de confianza|volver a unir al dominio|rejoin|pantalla azul|\bbsod\b|"
            r"\bchkdsk\b",
            r"actualizacion del sistema operativo|mantener actualizado el sistema",
        ),
        patrones_debiles=(r"mantenimiento", r"reparacion", r"incidencia"),
        prioridad=20,
    ),
)

#: El orden del índice: primero el oficio y las cuentas, después el trabajo diario (ficheros,
#: procesos, discos), luego el software y su actualización, después las dos caras de un puesto
#: (Windows y su red) y, al final, el mantenimiento y la reparación, que es lo que se hace cuando
#: algo ya no funciona.
ORDEN: tuple[str, ...] = (
    "el-oficio-de-administrador",
    "usuarios-grupos-y-permisos",
    "ficheros-y-trabajo-en-la-shell",
    "procesos-servicios-y-arranque",
    "discos-sistemas-de-ficheros-y-volumenes",
    "paquetes-versiones-y-actualizacion",
    "administracion-de-windows",
    "la-red-del-sistema",
    "mantenimiento-y-reparacion",
)

__all__ = ["MATERIAS", "ORDEN"]
