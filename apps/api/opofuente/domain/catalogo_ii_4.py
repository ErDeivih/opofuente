"""El catálogo de materias de II.4 (sistemas operativos, Windows, Unix y Linux, y móviles).

II.4 es un tema **técnico**: no lo estructura una norma, lo estructuran los cinco epígrafes de su
título, y dentro de cada uno el índice va por **asunto**, como en IV.7 y en IV.2. Sus cinco
epígrafes oficiales son el concepto de sistema operativo, sus características y elementos
constitutivos, Windows, Unix y Linux, y los sistemas operativos móviles; este catálogo los abre en
dieciséis apartados porque las preguntas del tema se agrupan así de verdad:

- el concepto de sistema operativo, en uno: qué es, qué funciones tiene, cómo se clasifica
  (monotarea, multitarea, multiusuario, tiempo compartido, tiempo real), cómo se estructura por
  dentro (monolítico, por capas, microkernel, cliente-servidor), las llamadas al sistema y los
  modos de ejecución, y el arranque;
- las características y elementos constitutivos, en cuatro: los **procesos** (estados, PCB, hilos,
  cambio de contexto y planificación), la **concurrencia** (secciones críticas, exclusión mutua,
  semáforos, monitores y el interbloqueo), la **memoria** (paginación, segmentación, memoria
  virtual, algoritmos de reemplazo y thrashing) y la **entrada/salida** (interrupciones, DMA,
  buffers, spooling, controladores y planificación del disco);
- Windows, en cinco: las **versiones y ediciones** (cliente y servidor, requisitos y novedades), la
  **administración** (directorio activo, cuentas y grupos, directivas de grupo y el registro), los
  **comandos y herramientas** (cmd, PowerShell, MMC y las utilidades de diagnóstico), el
  **almacenamiento y los permisos** (NTFS, FAT, compartición, cuotas y discos) y la **arquitectura y
  el arranque** (HAL, servicios, BIOS/UEFI, BCD y el administrador de tareas);
- Unix y Linux, en cinco: los **comandos y el shell** (tuberías, redirecciones, variables,
  editores y scripting), los **permisos y los usuarios** (modos, chmod, umask, SUID, passwd, sudo),
  el **sistema de ficheros** (jerarquía, inodos, enlaces, montaje, tipos de sistema de ficheros y
  NFS/SMB), el **arranque y los procesos** (GRUB, init y systemd, niveles, demonios, señales y el
  ciclo de vida del proceso) y las **distribuciones y la familia** (GNU, la historia, los gestores
  de paquetes, el software libre y macOS);
- los sistemas operativos móviles, en dos: **Android** (versiones, capas, máquina virtual y
  aplicaciones) y **los demás** (iOS, Apple, Symbian y el resto de plataformas).

Tres decisiones de redacción de los patrones, dichas donde se leen:

- `so-concepto-y-funciones` va con la prioridad **más alta** (se mira al final) y sus patrones son
  los del concepto, no los de cualquier cosa que se ejecute en un ordenador: «sistema operativo» y
  «sistema operativo» aparecen en el 60 % de los enunciados del tema. Sin eso, media asignatura
  acabaría en el apartado del concepto. Es la misma regla que en IV.2: lo particular gana a lo
  general;
- las palabras que el material escribe de dos maneras van con las **dos**: `hilo`/`thread`,
  `planificacion`/`scheduling`, `paginacion`/`paging`, `nucleo`/`kernel`, `directorio`/`carpeta`,
  `fichero`/`archivo`, `contrasena`/`clave`, y `stripping`/`striping` no aparece aquí pero sí el
  «formateo» que el material escribe «formateo»;
- las siglas van con `\\b` (`\\bgpo\\b`, `\\bntfs\\b`, `\\bfhs\\b`, `\\bpid\\b`): sin la frontera,
  `gpo` casa dentro de otra palabra y el reparto se llena de falsos positivos.

Las preguntas que no se sitúan ni por su enunciado ni por el texto de sus hechos **no** acaban en un
cajón: van a la bandeja del propietario con su motivo (`Motivo.SIN_MATERIA_EN_EL_INDICE`). Por eso
este catálogo, como el de IV.2 y el de I.1, **no tiene cajones**.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

MATERIAS: tuple[Materia, ...] = (
    # --- II.4.1 Sistemas operativos ---------------------------------------------------------------
    Materia(
        key="so-concepto-y-funciones",
        epigraph_code="II.4.1",
        title="Qué es un sistema operativo, qué hace y cómo se estructura",
        resumen=(
            "El sistema operativo como concepto: sus funciones (gestión de procesos, "
            "de memoria, de "
            "ficheros y de dispositivos, y la interfaz con el usuario), sus tipos y "
            "su clasificación "
            "(monotarea y multitarea, monousuario y multiusuario, por lotes, tiempo compartido y "
            "tiempo real, multiproceso y distribuido), su estructura interna "
            "(monolítica, por capas, "
            "microkernel, cliente-servidor y máquina virtual) y su interfaz con los programas: las "
            "llamadas al sistema, el modo usuario y el modo núcleo, las "
            "interrupciones y el arranque. "
            "Incluye el procesamiento por lotes y su lenguaje de control de trabajos (JCL)."
        ),
        patrones=(
            r"\bjcl\b|job control|control de (trabajos|tareas)",
            r"llamada(s)? al sistema|\bsyscall(s)?\b|system call",
            r"modo (usuario|nucleo|supervisor|kernel)|\bmodo privilegiado\b|modos? de "
            r"funcionamiento"
            r"monolitic[oa]|microkernel|micro.?nucleo|por capas|\bcliente.servidor\b",
            r"estructura de un sistema operativo|estructura interna",
            r"maquina virtual|\bvm\b(?!ware)",
            r"multiprogramacion|monoprogramacion|multitarea|monotarea|multiusuario|monousuario|"
            r"multiprocesamiento",
            r"tiempo compartido|tiempo real|\bmultiproceso\b|multiprocesador",
            r"distribuid[oa]s?",
            r"funcion(es)? (de|del|principal) (un )?sistema operativo",
            r"no es (un|una) sistema operativo|no es un sistema operativo",
            r"clasificacion de los sistemas operativos|tipos de sistemas operativos",
            r"interfaz (de|con el) usuario|\bcli\b|\bgui\b|interprete de (comandos|ordenes)",
            r"arranque del sistema|proceso de arranque|bios|\buefi\b|\bmbr\b|gestor de arranque",
            r"\bfirmware\b|\bpost\b",
            r"software (de base|del sistema)|software de sistema",
            r"\bmultics\b|\bunix\b como|evolucion de los sistemas operativos|historia de los",
        ),
        patrones_debiles=(r"sistema operativo", r"ordenador", r"programa"),
        prioridad=60,
    ),
    # --- II.4.2 Características y elementos constitutivos -----------------------------------------
    Materia(
        key="gestion-de-procesos",
        epigraph_code="II.4.2",
        title="Los procesos: estados, hilos y planificación",
        resumen=(
            "El proceso como unidad de trabajo: qué es, en qué se diferencia de un programa, sus "
            "estados (nuevo, listo, en ejecución, bloqueado y terminado) y su ciclo de vida, el "
            "bloque de control de proceso (PCB) y el cambio de contexto. Los hilos o hebras y su "
            "comparación con los procesos. Y la planificación de la CPU: los criterios, los "
            "algoritmos (FCFS o FIFO, SJF, el más corto primero, Round Robin y sus variantes, por "
            "prioridades y por colas multinivel) y la diferencia entre planificación apropiativa y "
            "no apropiativa."
        ),
        patrones=(
            r"\bpcb\b|bloque de control de(l)? proceso",
            r"cambio de contexto",
            r"\bhilo(s)?\b|\bhebra(s)?\b|\bthread(s)?\b",
            r"planificacion (de|del) (la )?(cpu|procesador|procesos)|planificador|\bscheduler\b|"
            r"\bscheduling\b|panificacion",
            r"round.?robin|\bfcfs\b|\bsjf\b|\bsrt\b|\bsrr\b|\bhrrn\b|el mas corto primero|"
            r"multinivel|multilevel",
            r"apropiativ|no apropiativ|expropiativ",
            r"quantum|rodaja de tiempo|time.?slice",
            r"estado(s)? de(l| un) proceso|en ejecucion|listo para ejecutar|bloqueado|"
            r"\bsleeping\b|\bwaiting\b|\bzombie\b",
            r"transicion(es)? de estado",
            r"concurrencia de procesos|proceso(s)? (ligero|pesado)",
            r"cola(s)? de (listos|preparados|espera)|dispatching|despachador",
            r"prioridad(es)? de(l| los) proceso",
        ),
        patrones_debiles=(r"proceso", r"cpu", r"planificacion"),
        prioridad=20,
    ),
    Materia(
        key="concurrencia-y-interbloqueo",
        epigraph_code="II.4.2",
        title="La concurrencia: exclusión mutua, semáforos e interbloqueo",
        resumen=(
            "Ejecutar varias cosas a la vez sin que se estropeen: la sección crítica y sus "
            "condiciones, la exclusión mutua y los mecanismos que la consiguen (el algoritmo de "
            "Dekker, Peterson, el test-and-set, los semáforos y los monitores), los problemas "
            "clásicos (productor-consumidor, lectores-escritores y el barbero) y la comunicación "
            "entre procesos por paso de mensajes. Y el interbloqueo o deadlock: sus cuatro "
            "condiciones, la prevención, la evitación (el algoritmo del banquero), la "
            "detección y la "
            "recuperación, junto con la inanición o starvation."
        ),
        patrones=(
            r"seccion(es)? critic",
            r"exclusion mutua|mutex|\bsemaforo(s)?\b|semaphore|\bmonitor(es)?\b(?! de)",
            r"interbloqueo|deadlock|\babrazo mortal\b|starvation|inanicion",
            r"productor.{0,3}consumidor|lectores.{0,3}escritores|barbero",
            r"algoritmo de (dekker|peterson|lamport)|test.and.set|\bcsp\b",
            r"paso de mensajes|buzon(es)?|cola de mensajes|comunicacion entre procesos|\bipc\b",
            r"\bespera activa\b|busy waiting|\bspinlock\b",
            r"condiciones? de (coffman|el interbloqueo)|grafo de asignacion",
            r"algoritmo del banquero|estado seguro|evitacion del interbloqueo",
            r"barrera(s)? de sincronizacion|region critica",
            r"\bsocket(s)?\b",
        ),
        patrones_debiles=(r"concurrencia", r"sincronizacion", r"procesos concurrentes"),
        prioridad=18,
    ),
    Materia(
        key="gestion-de-memoria",
        epigraph_code="II.4.2",
        title="La memoria: paginación, segmentación y memoria virtual",
        resumen=(
            "Cómo se reparte la memoria: la dirección lógica y la física, la unidad de gestión de "
            "memoria (MMU), la memoria virtual y el intercambio (swapping), las técnicas de "
            "asignación (particiones fijas y variables, first-fit, best-fit y worst-fit, "
            "compactación) y la memoria paginada y segmentada. Las tablas de páginas "
            "y de segmentos, "
            "los marcos, los fallos de página y los algoritmos de reemplazo (FIFO, "
            "óptimo, LRU y sus "
            "variantes por contador y por pila, el reloj y NFU), la hiperpaginación o "
            "thrashing y la "
            "memoria caché y asociativa."
        ),
        patrones=(
            r"memoria virtual",
            r"paginacion|paginad[oa]|\bpaging\b|\bmarco(s)? de pagina|pagina(s)? virtual",
            r"segmentacion|\bsegmento(s)?\b",
            r"tabla(s)? de pagina|tabla de segmento|\btlb\b|memoria asociativa",
            r"fallo(s)? de pagina|page fault|hiperpaginacion|thrashing|trashing",
            r"reemplazo de pagina|reemplazo de marco|\blru\b|\bfifo\b|opc?tim[oa] de reemplazo|"
            r"algoritmo de reemplazo|\bnfu\b|algoritmo del reloj|segunda oportunidad",
            r"memoria (principal|fisica|real|central)|memoria fisica|memoria logica",
            r"direccion(es)? (fisica|logica|virtual)|espacio de direccionamiento",
            r"\bmmu\b|unidad de gestion de memoria",
            r"first.?fit|best.?fit|worst.?fit|primer hueco|mejor hueco|peor hueco",
            r"particion(es)? (de memoria|fija|variable)|compactacion|fragmentacion",
            r"\bswap\b|swapping|intercambio de memoria",
            r"memoria cache|\bcache\b|memoria intermedia",
        ),
        patrones_debiles=(r"memoria", r"pagina", r"direccion"),
        prioridad=19,
    ),
    Materia(
        key="gestion-de-e-s-y-discos",
        epigraph_code="II.4.2",
        title="La entrada/salida: interrupciones, controladores y discos",
        resumen=(
            "Cómo habla el sistema operativo con los dispositivos: las técnicas de entrada/salida "
            "(por programa o consulta, por interrupciones y por acceso directo a "
            "memoria o DMA), las "
            "interrupciones y sus tipos, los controladores o drivers, el almacenamiento intermedio "
            "(buffers y caché de disco) y la impresión en espera (spooling). Y los "
            "discos: sectores, "
            "cilindros y pistas, el tiempo de acceso (búsqueda, latencia y transferencia) y los "
            "algoritmos de planificación del disco (FCFS, SSTF, SCAN, C-SCAN y LOOK)."
        ),
        patrones=(
            r"entrada(s)?.{0,3}salida|entrada salida|\be ?/? ?s\b",
            r"interrupcion(es)?|\birq\b",
            r"acceso directo a memoria|\bdma\b",
            r"\bdriver(s)?\b|controlador(es)? de dispositivo|manejador(es)? de dispositivo",
            r"\bbuffer(s)?\b|spooling|\bspool\b|almacenamiento intermedio",
            r"disco(s)? (duro|magnetico)|unidad de disco|\bhdd\b|\bssd\b",
            r"sector(es)?|\bcilindro(s)?\b|\bpista(s)?\b|tiempo de (busqueda|acceso|latencia)",
            r"planificacion del (disco|brazo)|\bsstf\b|\bscan\b|\bc.?scan\b|\blook\b|"
            r"elevator|ascensor",
            r"dispositivo(s)? de (entrada|salida|almacenamiento)|periferico(s)?",
            r"gestion de dispositivos|gestor de dispositivos",
            r"\bps2\b|\busb\b|\bsata\b|\bnvme\b|tarjeta de red",
        ),
        patrones_debiles=(r"dispositivo", r"disco", r"entrada y salida"),
        prioridad=22,
    ),
    # --- II.4.3 Sistemas Windows ------------------------------------------------------------------
    Materia(
        key="windows-versiones-y-ediciones",
        epigraph_code="II.4.3",
        title="Windows: versiones, ediciones y requisitos",
        resumen=(
            "Las versiones y las ediciones de Windows: la familia de cliente (3.x, 95, 98, Me, NT, "
            "2000, XP, Vista, 7, 8, 8.1, 10 y 11) y la de servidor (NT Server, 2000, 2003, 2008, "
            "2012, 2016, 2019 y 2022), las ediciones de cada una (Home, Pro, Professional, "
            "Enterprise, Ultimate, Datacenter y Web), el canal de servicio (LTSC y las "
            "actualizaciones), los requisitos de hardware, el ciclo de vida y el soporte, y qué "
            "añade o quita cada versión."
        ),
        patrones=(
            r"windows\s?(3|95|98|me|nt|2000|xp|vista|7|8|8\.?1|10|11)\b",
            r"windows server\s?(20\d\d|2003|2008|2012|2016|2019|2022)",
            r"windows server(?!\s?20)",
            r"edicion(es)? (home|pro|professional|enterprise|ultimate|datacenter|basica|starter)|"
            r"\bhome edition\b|\bultimate\b",
            r"canal (de servicio|semi.?anual)|ltsc|\bltsb\b|\blts\b",
            r"requisitos (de hardware|del sistema|minimos)|requisitos de windows",
            r"ciclo de vida|fin de soporte|service pack|\bsp\d\b",
            r"actualizacion(es)? de windows|windows update",
            r"\bwindows\b.*\b(version|edicion|novedad)",
        ),
        patrones_debiles=(r"\bwindows\b.*\b(version|edicion)", r"edicion(es)?", r"novedades"),
        prioridad=26,
    ),
    Materia(
        key="windows-directorio-activo-y-politicas",
        epigraph_code="II.4.3",
        title="Windows: directorio activo, cuentas y directivas",
        resumen=(
            "La administración de Windows en red: el directorio activo (AD y AD DS), el dominio y "
            "el bosque, el controlador de dominio y el catálogo global, las unidades "
            "organizativas, "
            "la autenticación (Kerberos, NTLM y LDAP) y la confianza entre dominios. "
            "Las cuentas de "
            "usuario y los grupos (locales, globales y universales), los perfiles y los perfiles "
            "móviles, las directivas de grupo (GPO) y su orden de aplicación, las directivas de "
            "seguridad y las plantillas administrativas."
        ),
        patrones=(
            r"directorio activo|active directory|\bad ds\b|\bad\b(?!minist)",
            r"controlador(es)? de dominio|\bdc\b|dominio(s)? de "
            r"windows|\bbosque\b|arbol de dominios",
            r"unidad(es)? organizativa(s)?|\bou(s)?\b",
            r"\bkerberos\b|\bntlm\b|\bldap\b|autenticacion de windows",
            r"directiva(s)? de grupo|\bgpo(s)?\b|plantilla(s)? administrativa(s)?",
            r"directiva(s)? de seguridad|politica(s)? de (seguridad|contrasena|clave)|"
            r"politica(s)? de grupo",
            r"cuenta(s)? de (usuario|equipo)|grupo(s)? (local|global|universal)|"
            r"grupo(s)? de (seguridad|trabajo)",
            r"perfil(es)? (de usuario|movil|obligatorio)|carpeta(s)? particular",
            r"permisos (ntfs|de archivo|efectivos)|herencia de permisos|\bacl\b",
            r"inicio de sesion|\blogon\b|\bcuota(s)? de disco",
            r"servidor(es)? de (archivos|impresion)|\bimpresora(s)? compartida",
            r"\bapplocker\b|directiva(s)? de restriccion de aplicaciones",
        ),
        patrones_debiles=(r"usuario", r"grupo", r"cuenta"),
        prioridad=24,
    ),
    Materia(
        key="windows-comandos-y-herramientas",
        epigraph_code="II.4.3",
        title="Windows: la consola, PowerShell y las herramientas de diagnóstico",
        resumen=(
            "La caja de herramientas de Windows: el intérprete de comandos (cmd) y sus órdenes "
            "(dir, cd, md, copy, xcopy, robocopy, del, type, net, ipconfig, ping, tracert, "
            "tasklist, taskkill, sc, reg, chkdsk, format, diskpart y attrib), PowerShell y sus "
            "cmdlets, la consola de administración (MMC) y sus complementos, el "
            "editor del registro "
            "(regedit) y las utilidades de diagnóstico y reparación (sfc /scannow, el comprobador "
            "de archivos del sistema, msconfig, la restauración del sistema y el monitor de "
            "rendimiento)."
        ),
        patrones=(
            r"powershell|\bps1\b|cmdlet(s)?|invoke.expression",
            r"\bcmd\b|simbolo del sistema|interprete de comandos|linea de comandos",
            r"\bregedit\b|editor del registro|entrada(s)? del registro|\bregistro de windows\b|"
            r"\bhkey\b|clave(s)? de registro",
            r"\bmmc\b|consola de administracion|complemento(s)? de consola",
            r"sfc|scannow|comprobador de archivos|chkdsk|comprobacion de disco",
            r"msconfig|restauracion del sistema|punto de restauracion|modo seguro",
            r"monitor de rendimiento|administrador de tareas|visor de eventos|"
            r"programador de tareas",
            r"\brobocopy\b|\bxcopy\b|\bipconfig\b|\bnetstat\b|\btasklist\b|\btaskkill\b|"
            r"\bdiskpart\b",
            r"\battrib\b|\bcacls\b|\bicacls\b|\btakeown\b|\bnet use\b|\bnet share\b",
            r"panel de control|herramientas administrativas|configuracion del sistema",
        ),
        patrones_debiles=(r"comando", r"herramienta", r"consola"),
        prioridad=25,
    ),
    Materia(
        key="windows-almacenamiento-y-ficheros",
        epigraph_code="II.4.3",
        title="Windows: NTFS, discos y sistemas de ficheros",
        resumen=(
            "Cómo guarda los datos Windows: los sistemas de ficheros (FAT, FAT32, exFAT y NTFS) y "
            "sus diferencias, el formateo, las particiones (primarias, extendidas y lógicas), el "
            "arranque MBR y GPT, los volúmenes y los volúmenes dinámicos, los discos básicos y "
            "dinámicos, la desfragmentación, la compresión y el cifrado (EFS y BitLocker), la "
            "compartición de carpetas y los recursos compartidos, los puntos de montaje y las "
            "copias de seguridad y su restauración."
        ),
        patrones=(
            r"\bntfs\b|\bfat\b|\bfat32\b|\bexfat\b",
            r"tabla de asignacion de archivos|sistema de (ficheros|archivos) de windows",
            r"formateo|formatear (un|el) disco|formato (rapido|completo)",
            r"particion(es)? (primaria|extendida|logica)|volumen(es)? (dinamico|simple|"
            r"distribuido|seccionado)|disco(s)? (basico|dinamico)",
            r"\bgpt\b|tabla de particiones|\bmbr\b.*particion",
            r"desfragmentacion|desfragmentar|\bbitlocker\b|\befs\b|cifrado de disco",
            r"recursos? compartidos?|carpeta(s)? compartida|compartir (una|la) carpeta",
            r"copia(s)? de seguridad de windows|imagen del sistema|historial de archivos",
            r"punto(s)? de montaje|\bchkdsk\b.*(disco|volumen)",
            r"espacio (libre|en disco)|cuota(s)? de disco",
            r"\btxf\b|ntfs transaccional",
        ),
        patrones_debiles=(r"disco", r"fichero", r"archivo", r"volumen"),
        prioridad=23,
    ),
    Materia(
        key="windows-arquitectura-y-servicios",
        epigraph_code="II.4.3",
        title="Windows: arquitectura, servicios y sesiones",
        resumen=(
            "Windows por dentro: su arquitectura por capas (el núcleo o kernel, la capa de "
            "abstracción del hardware o HAL, los subsistemas de entorno y las bibliotecas de "
            "enlace dinámico), el modo usuario y el modo núcleo, el registro como base de "
            "configuración, los servicios y su consola, los procesos y su administración, el "
            "administrador de tareas y el arranque del sistema (BIOS y UEFI, el gestor de arranque "
            "de Windows, el almacén de datos de arranque o BCD y las opciones avanzadas)."
        ),
        patrones=(
            r"\bhal\b|capa de abstraccion del hardware",
            r"arquitectura de windows|subsistema(s)? de (entorno|windows)|"
            r"biblioteca(s)? de enlace dinamico|\bdll\b",
            r"servicio(s)? de windows|consola de servicios|administrador de servicios|"
            r"services ?\.? ?msc",
            r"almacen de datos de arranque|\bbcd\b|bootmgr|gestor de arranque de windows|"
            r"\bwinload\b|\bntldr\b",
            r"administrador de tareas|\btaskmgr\b",
            r"\bwmi\b|instrumental de administracion de windows",
            r"sesion(es)? de (usuario|windows)|cierre de sesion|\bwinlogon\b",
            r"nucleo de windows|kernel de windows|\bntoskrnl\b",
            r"modo kernel|modo usuario.*windows|terminal server|\brdp\b|escritorio remoto",
        ),
        patrones_debiles=(r"windows", r"servicio"),
        prioridad=27,
    ),
    # --- II.4.4 Sistemas Unix y Linux -------------------------------------------------------------
    Materia(
        key="unix-comandos-y-shell",
        epigraph_code="II.4.4",
        title="El shell y los comandos de Unix y Linux",
        resumen=(
            "El intérprete de órdenes y lo que se hace con él: los shells (sh, bash, csh, ksh y "
            "zsh), las variables de entorno y de shell, las comillas y los comodines, la "
            "redirección de la entrada y la salida y las tuberías, los filtros y los comandos de "
            "uso corriente (ls, cd, pwd, cat, more, less, head, tail, cp, mv, rm, mkdir, find, "
            "grep, sed, awk, sort, uniq, wc, cut, tr, tar, gzip, dd, echo, date, man, which, ps, "
            "kill, nohup y at), los editores (vi y nano) y la programación de guiones "
            "o scripts con "
            "sus estructuras de control."
        ),
        patrones=(
            r"\bshell\b|\bbash\b|\bcsh\b|\bksh\b|\bzsh\b|\bsh\b",
            r"variable(s)? de (entorno|shell)|export|\bpath\b",
            r"redireccion(es)?|tuberia(s)?|\bpipe\b|comodin(es)?|\bstdin\b|\bstdout\b|"
            r"\bstderr\b",
            r"\bgrep\b|\bsed\b|\bawk\b|\bsort\b|\buniq\b|\bwc\b|\bcut\b|\btr\b|\bdiff\b|"
            r"\bpaste\b|\bcomm\b",
            r"\bcat\b|\bmore\b|\bless\b|\bhead\b|\btail\b|\becho\b|\btee\b",
            r"\bls\b|\bcd\b|\bpwd\b|\bcp\b|\bmv\b|\brm\b|\bmkdir\b|\brmdir\b|\btouch\b|"
            r"variable(es)? (de unix|de linux|especiales)",
            r"\bfind\b|\blocate\b|\bwhich\b|\bwhereis\b|\bman\b|\bapropos\b",
            r"\bchmod\b|\bchown\b|\bchgrp\b|\bumask\b",
            r"\bfork\b|\bexec\b|\bnohup\b|\bat\b|\bcron\b|\bcrontab\b",
            r"\bvim?\b|\bnano\b|\bemacs\b|editor de texto",
            r"\btar\b|\bgzip\b|\bzip\b|\bunzip\b|\bbzip2\b|\bdd\b|compresion de ficheros",
            r"guion(es)?|\bscript(s)?\b|programacion de shell|estructura(s)? de control",
            r"comando(s)? de (linux|unix)|orden(es)? de (linux|unix)|"
            r"que (hace|realiza|devuelve) (el|la) (comando|orden|siguiente)",
            r"ejecuta(ndo)? (el|la) (comando|orden)|linea de ordenes de linux",
        ),
        patrones_debiles=(r"comando", r"orden", r"shell"),
        prioridad=30,
    ),
    Materia(
        key="unix-permisos-y-usuarios",
        epigraph_code="II.4.4",
        title="Usuarios, grupos y permisos en Unix y Linux",
        resumen=(
            "Quién puede hacer qué: las cuentas de usuario y los grupos, el usuario root y el "
            "superusuario, los ficheros de cuentas (/etc/passwd, /etc/shadow y /etc/group), el "
            "cambio de usuario (su y sudo), los permisos de lectura, escritura y ejecución para el "
            "propietario, el grupo y el resto, la notación simbólica y la octal de chmod, la "
            "máscara umask, los permisos especiales (SUID, SGID y el bit pegajoso o sticky), la "
            "propiedad de los ficheros con chown y el control de acceso por listas (ACL)."
        ),
        patrones=(
            r"permiso(s)? (de|del|para) (fichero|archivo|directorio|usuario)|permisos de acceso",
            r"\bchmod\b|\bchown\b|\bchgrp\b|\bumask\b|\bsticky\b|\bsuid\b|\bsgid\b",
            r"propietario del fichero|propietario de un fichero|usuario propietario",
            r"\broot\b|superusuario|\bsudo\b|\bwheel\b",
            r"etc.passwd|etc.shadow|etc.group|fichero(s)? de (cuentas|contrasenas)",
            r"contrasena(s)? (de usuario|en linux|de root)|cifrado de contrasenas",
            r"cuenta(s)? de usuario en (linux|unix)|usuario(s)? y grupo(s)?",
            r"grupo(s)? (de usuarios|primario|secundario)|pertenencia a grupos",
            r"listas de control de acceso|\bacl\b.*(linux|unix)|permisos extendidos",
            r"notacion (simbolica|octal)|permisos (rwx|en octal)",
            r"lectura escritura y ejecucion|\brwx\b|drwx",
        ),
        patrones_debiles=(r"permiso", r"usuario", r"propietario"),
        prioridad=28,
    ),
    Materia(
        key="unix-sistema-de-ficheros",
        epigraph_code="II.4.4",
        title="El sistema de ficheros y el almacenamiento en Unix y Linux",
        resumen=(
            "Cómo se organizan los datos: la jerarquía de directorios y su estándar (la raíz y sus "
            "directorios /bin, /sbin, /etc, /dev, /proc, /var, /home, /usr, /lib y /tmp), los "
            "inodos y la estructura del sistema de ficheros, los enlaces duros y simbólicos, el "
            "montaje y el fichero /etc/fstab, los tipos de sistema de ficheros (ext2, ext3, ext4, "
            "XFS, ReiserFS, Btrfs, JFS y los de red), la gestión de discos y particiones "
            "(fdisk, mkfs, df, du, fsck y LVM) y la compartición por red (NFS, Samba y CIFS)."
        ),
        patrones=(
            r"inodo(s)?|\binode\b",
            r"enlace(s)? (duro(s)?|simbolico(s)?)|\bln\b|symlink",
            r"jerarquia de (directorios|ficheros)|\bfhs\b|estandar de jerarquia|"
            r"directorio(s)? raiz|estructura de directorios",
            r"etc.fstab|punto(s)? de montaje|\bmount\b|\bumount\b",
            r"\bext[234]\b|\bxfs\b|\breiser\b|\bbtrfs\b|\bjfs\b|sistema de ficheros (de red|"
            r"journaling)|journaling",
            r"\bnfs\b|\bsamba\b|\bcifs\b|\bsmb\b|comparticion de ficheros en red",
            r"\bfdisk\b|\bmkfs\b|\bfsck\b|\bdf\b|\bdu\b|\blvm\b|volumen(es)? logico(s)?",
            r"directorio(s)? (etc|bin|var|home|usr|dev|proc|tmp|lib|sbin|mnt|opt)",
            r"cuota(s)? de disco|espacio en disco.*linux|uso de disco",
            r"fichero(s)? (de dispositivo|especial)|dev.sda|dev.hda",
            r"\bparticion(es)?\b|organizacion de las particiones",
        ),
        patrones_debiles=(r"directorio", r"fichero", r"archivo", r"sistema de ficheros"),
        prioridad=29,
    ),
    Materia(
        key="unix-arranque-y-procesos",
        epigraph_code="II.4.4",
        title="Arranque, procesos y servicios de Unix y Linux",
        resumen=(
            "Cómo arranca y cómo se ejecuta: el arranque (BIOS o UEFI, el gestor de arranque GRUB "
            "o LILO, el núcleo, init y systemd, los niveles de ejecución o runlevels y los "
            "guiones de arranque), los demonios y los servicios, la gestión de procesos (el "
            "identificador o PID y el PPID, fork y exec, los estados, los procesos en segundo "
            "plano y en primer plano, los procesos zombie y huérfanos, las señales y kill, y los "
            "comandos ps, top, jobs, bg y fg) y el planificador del núcleo."
        ),
        patrones=(
            r"\bgrub\b|\blilo\b|gestor de arranque|niveles? de ejecucion|runlevel|\binit\b|"
            r"systemd|\bsystemctl\b|arranque de linux",
            r"demonio(s)?|\bdaemon(es)?\b|servicio(s)? de linux|servicio(s)? del sistema",
            r"\bpid\b|\bppid\b|identificador de proceso",
            r"\bfork\b|\bexec\b|\bwait\b|proceso(s)? (zombie|huerfano|huerfanos)|"
            r"proceso(s)? en segundo plano|segundo plano",
            r"senal(es)? (de linux|al proceso)|\bkill\b|\bsigkill\b|\bsigterm\b|\bsighup\b|"
            r"\bsigint\b",
            r"\bps\b aux|\btop\b|\bjobs\b|\bbg\b|\bfg\b|\bpgrep\b|\bpkill\b|\bnice\b|"
            r"\brenice\b",
            r"planificador (de linux|del nucleo)|cfs|completely fair|prioridad(es)? de proceso",
            r"nucleo de linux|kernel de linux|\bkernel\b|\bnucleo\b|modulo(s)? del nucleo|"
            r"monolitico.*linux",
            r"apagado del sistema|reinicio del sistema|halt|shutdown|runlevel",
        ),
        patrones_debiles=(r"proceso", r"arranque", r"servicio"),
        prioridad=31,
    ),
    Materia(
        key="unix-familia-y-distribuciones",
        epigraph_code="II.4.4",
        title="La familia de Unix y Linux: distribuciones y paquetes",
        resumen=(
            "De dónde viene y con qué se instala: la historia de Unix (System V y BSD), el "
            "proyecto GNU y el software libre y de código abierto, las licencias (GPL), las "
            "distribuciones (Debian, Ubuntu, Red Hat, Fedora, CentOS, SUSE, Slackware, Arch y "
            "Mint) y sus familias, los gestores de paquetes (dpkg y apt frente a rpm, yum y dnf), "
            "los entornos de escritorio (GNOME y KDE), las diferencias entre Unix, Linux y macOS, "
            "y las herramientas de virtualización propias de Linux."
        ),
        patrones=(
            r"distribucion(es)? (de linux|linux)|\bdebian\b|\bubuntu\b|\bred hat\b|\bfedora\b|"
            r"\bcentos\b|\bsuse\b|\bslackware\b|\barch\b|\bmint\b|\bgentoo\b",
            r"\bgnu\b|software libre|open source|codigo abierto|\bgpl\b|licencia(s)? (de "
            r"software|gpl)",
            r"gestor(es)? de paquetes|\bdpkg\b|\bapt\b|\baptitude\b|\brpm\b|\byum\b|\bdnf\b|"
            r"\bsnap\b|\bflatpak\b",
            r"repositorio(s)? de paquetes|instalar (un )?paquete",
            r"entorno(s)? de escritorio|\bgnome\b|\bkde\b|\bxfce\b|\bunity\b",
            r"historia de unix|\bsystem v\b|\bbsd\b|\bposix\b|estandar posix",
            r"\bmacos\b|\bmac os\b|apple|\btahoe\b|\bsequoia\b|\bventura\b|\bmonterey\b",
            r"\bminix\b|\blinux torvalds\b|familia de sistemas operativos",
            r"software (propietario|privativo)|free software foundation|\bfsf\b",
        ),
        patrones_debiles=(r"distribucion(es)?", r"licencia", r"paquete(s)?", r"unix y linux"),
        prioridad=32,
    ),
    # --- II.4.5 Sistemas operativos para dispositivos móviles -------------------------------------
    Materia(
        key="moviles-android",
        epigraph_code="II.4.5",
        title="Android: versiones, capas y aplicaciones",
        resumen=(
            "El sistema operativo de Google: su historia y sus versiones, su arquitectura por "
            "capas (el núcleo de Linux, la capa de abstracción del hardware, las bibliotecas "
            "nativas, el entorno de ejecución con la máquina virtual Dalvik y ART, el marco de "
            "aplicaciones y las aplicaciones), el desarrollo de aplicaciones (Android Studio, el "
            "lenguaje Java o Kotlin y el fichero APK), el almacenamiento, los permisos y las "
            "notificaciones, y Google Play como tienda de aplicaciones."
        ),
        patrones=(
            r"\bandroid\b",
            r"\bdalvik\b|\bart\b.*android|android runtime",
            r"\bapk\b|google play|play store|tienda de aplicaciones",
            r"\bkotlin\b|\bjava\b.*android|android studio|\bgradle\b",
            r"notificacion(es)? (push|de android)|\bnotification\b",
            r"aplicacion(es)? (nativa(s)?|movil(es)?)|app movil|aplicaciones moviles",
            r"capa(s)? (de abstraccion|de android)|arquitectura de android",
            r"\bapi\b.*android|nivel de api|\bsdk\b.*android",
        ),
        patrones_debiles=(r"aplicacion", r"movil", r"dispositivo"),
        prioridad=34,
    ),
    Materia(
        key="moviles-otros-sistemas",
        epigraph_code="II.4.5",
        title="Los demás sistemas operativos móviles: iOS y otros",
        resumen=(
            "Los otros sistemas operativos de dispositivos móviles: iOS y sus versiones, el "
            "ecosistema de Apple (iPhone, iPad y iPadOS), su arquitectura y su tienda de "
            "aplicaciones, la seguridad y el sandboxing de las aplicaciones, y las plataformas que "
            "han quedado atrás o conviven con ellas (Symbian, Windows Phone y Windows Mobile, "
            "BlackBerry, webOS, Firefox OS, Tizen, HarmonyOS y los sistemas para tabletas y "
            "relojes)."
        ),
        patrones=(
            r"\bios\b|\bipados\b|\biphone\b|\bipad\b|\bapple\b|\bapp store\b",
            r"\bsymbian\b|\bblackberry\b|\bwebos\b|\bfirefox os\b|\btizen\b|\bharmonyos\b|"
            r"\bwindows phone\b|\bwindows mobile\b",
            r"\bsandbox\b|aislamiento de aplicaciones",
            r"dispositivo(s)? movil(es)?|telefono(s)? (inteligente(s)?|movil(es)?)|"
            r"\bsmartphone(s)?\b|\btableta(s)?\b|\bwearable(s)?\b",
            r"sistema(s)? operativo(s)? (para|de) (moviles|dispositivos moviles)|"
            r"sistemas operativos moviles",
            r"asistente(s)? de voz|google now|siri|android auto|carplay",
        ),
        patrones_debiles=(r"movil", r"moviles", r"tableta"),
        prioridad=35,
    ),
)

#: El orden en que se **enseña** el índice: primero el concepto de sistema operativo, después sus
#: elementos constitutivos (procesos, concurrencia, memoria y entrada/salida), después los dos
#: sistemas que el título nombra uno detrás del otro (Windows y Unix/Linux) y, por último, los
#: móviles —que es el orden del título del tema y el orden en que se estudia—. Dentro de Windows y
#: de Unix, el orden es el de la administración de fuera hacia dentro: qué versiones hay, cómo se
#: administra, con qué herramientas, dónde se guardan los datos y cómo funciona por dentro.
ORDEN: tuple[str, ...] = (
    "so-concepto-y-funciones",
    "gestion-de-procesos",
    "concurrencia-y-interbloqueo",
    "gestion-de-memoria",
    "gestion-de-e-s-y-discos",
    "windows-versiones-y-ediciones",
    "windows-directorio-activo-y-politicas",
    "windows-comandos-y-herramientas",
    "windows-almacenamiento-y-ficheros",
    "windows-arquitectura-y-servicios",
    "unix-comandos-y-shell",
    "unix-permisos-y-usuarios",
    "unix-sistema-de-ficheros",
    "unix-arranque-y-procesos",
    "unix-familia-y-distribuciones",
    "moviles-android",
    "moviles-otros-sistemas",
)

__all__ = ["MATERIAS", "ORDEN"]
