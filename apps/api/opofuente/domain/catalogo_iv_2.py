"""El catálogo de materias de IV.2 (Administración de bases de datos, almacenamiento, backup y
virtualización).

IV.2 es un tema **técnico**: no lo estructura una norma, lo estructuran las cinco materias de su
título, y dentro de cada una el índice va por **asunto**, como en IV.7. Sus cinco epígrafes
oficiales son la administración de bases de datos, el almacenamiento, las políticas de backup, el
backup de sistemas físicos y virtuales y la virtualización; este catálogo los abre en doce apartados
porque las preguntas del tema se agrupan así de verdad:

- la administración de bases de datos, en tres apartados: los **SGBD relacionales** (Oracle, MySQL,
  PostgreSQL, SQL Server…), las **NoSQL** por familia (clave-valor, documental, columnar, grafos,
  multimodelo) y la **administración** de la base (cuentas y privilegios, procesos de Oracle,
  ficheros de configuración, copia lógica de datos);
- el almacenamiento, en tres: los **niveles RAID** (paridad, stripping, mirroring, capacidades y
  número mínimo de discos), el **almacenamiento en red** (DAS, NAS, SAN, iSCSI, Fibre Channel, AoE y
  el reparto en bloque o en fichero) y el **almacenamiento avanzado** (thin provisioning,
  deduplicación, snapshots, hiperconvergencia y soportes);
- el backup, en dos: las **políticas** (tipos de copia, ventana, retención, la regla 3-2-1, RPO/RTO
  y el catálogo) y las **herramientas y modos** (backup lógico y físico, en caliente y en frío,
  sintético, a nivel de hipervisor);
- el backup de sistemas físicos y virtuales, en uno: lo que cambia cuando lo que se copia es una
  **máquina virtual** o un contenedor, y cómo se restaura;
- la virtualización, en tres: los **hipervisores** (tipo 1 y tipo 2, virtualización completa,
  paravirtualización y asistida por hardware, y los productos de cada fabricante), los **puestos de
  usuario (VDI)** y los **contenedores y su orquestación** (Docker, Kubernetes, OpenShift, las nubes
  gestionadas y el registro de imágenes).

Tres decisiones de redacción de los patrones, dichas donde se leen:

- `raid` va **el primero** de su epígrafe y con prioridad baja porque `raid` aparece en casi todas
  las preguntas de RAID y, sin eso, un hecho que compara «RAID 5 con NAS» acabaría en el
  almacenamiento en red por mencionar antes el NAS. Es la misma regla que en IV.7: el particular
  gana a lo general;
- las siglas van con `\\b` y **con** su significado desarrollado (`\\bsan\\b` y «storage area
  network»), porque media oposición escribe la sigla y la otra media el nombre;
- las palabras que el texto real escribe de dos maneras van con las **dos**: `hipervisor`/
  `hypervisor`, `backup`/`copia de seguridad`, `stripping`/`striping` (el material del tema escribe
  «stripping», que no es la forma inglesa correcta pero es la que está en los enunciados).

Las preguntas que no se sitúan ni por su enunciado ni por el texto de sus hechos **no** acaban en un
cajón: van a la bandeja del propietario con su motivo (`Motivo.SIN_MATERIA_EN_EL_INDICE`). Por eso
este catálogo, como el de I.1, **no tiene cajones**: con trece apartados que cubren el tema
entero, un cajón solo escondería una pregunta mal situada.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Las palabras con las que el texto real nombra lo mismo de dos maneras. Un patrón que solo acepte
#: una deja fuera la mitad de las preguntas.
_HIPERVISOR = r"hipervisor(es)?|hypervisor(es)?|\bvmm\b"

#: La copia de seguridad, por sus dos nombres. El material del tema usa los dos indistintamente.
_COPIA = r"\bbackups?\b|copias? de (seguridad|respaldo)|copias? de seguridad"

MATERIAS: tuple[Materia, ...] = (
    # --- IV.2.1 Administración de bases de datos -------------------------------------------------
    Materia(
        key="bbdd-relacionales",
        epigraph_code="IV.2.1",
        title="Las bases de datos relacionales: productos y objetos",
        resumen=(
            "Los sistemas gestores de bases de datos relacionales y sus productos: Oracle, MySQL y "
            "MariaDB, PostgreSQL, SQL Server, SQLite, DB2, MaxDB, Apache Derby y las bases de "
            "datos "
            "en la nube. Y los objetos con los que se organizan: tablas, vistas, índices, "
            "tablespaces, esquemas, segmentos y extensiones."
        ),
        patrones=(
            r"base(s)? de datos relacional(es)?",
            r"\brelacional(es)?\b",
            r"\boracle\b",
            r"\bmysql\b|\bmariadb\b",
            r"\bpostgres(ql)?\b|\bpostgres\b|\bpsql\b|\bpg_",
            r"sql server|\btransact",
            r"\bsqlite\b",
            r"\bdb2\b|\bmaxdb\b|\bderby\b",
            r"\bsql\b",
            r"lenguaje(s)? de (consulta|interrogacion)|\bansi sql\b",
            r"\btablespace(s)?\b",
            r"\bvista(s)?\b|\bview(s)?\b",
            r"\btrigger(s)?\b|\bprocedimiento(s)? almacenado",
            r"indice(s)? (de la tabla|unico|primario)",
            r"\besquema(s)?\b|\bsegmento(s)?\b|\bextension(es)?\b",
            r"integridad referencial|clave primaria|clave ajena",
            r"normalizacion|formas normales",
            r"amazon (rds|aurora)|azure sql|base de datos en la nube",
            r"gestion de bases de datos|administracion de bases de datos",
        ),
        patrones_debiles=(r"base de datos", r"tabla", r"consulta"),
        prioridad=20,
    ),
    Materia(
        key="bbdd-nosql",
        epigraph_code="IV.2.1",
        title="Las bases de datos NoSQL y las orientadas a objetos",
        resumen=(
            "Las bases de datos NoSQL y su familia: clave-valor (Redis, Memcached, DynamoDB, "
            "SimpleDB, Aerospike), documentales (MongoDB, CouchDB, HBase), columnares (Cassandra, "
            "Bigtable, HBase), de grafos (Neo4j, FlockDB, AllegroGraph) y multimodelo (Azure "
            "Cosmos "
            "DB, OrientDB). Y las orientadas a objetos y de objetos (Db4o, ObjectDB, Gemstone, "
            "Matisse, ZODB, Zope)."
        ),
        patrones=(
            r"\bnosql\b",
            r"clave.?valor|key.?value",
            r"documental(es)?|orientad[ao]s? a documentos",
            r"columnar(es)?|por columnas",
            r"\bgrafos?\b|\bgraph\b",
            r"multimodelo",
            r"\bmongodb\b|\bcouchdb\b|\bhbase\b|\bcassandra\b|\bbigtable\b",
            r"\bredis\b|\bmemcached\b|\bdynamodb\b|\bsimpledb\b|\baerospike\b",
            r"\bneo4j\b|\bflockdb\b|\ballegrograph\b",
            r"cosmos db|\borientdb\b",
            r"orientad[ao]s? a objetos|\boodb\b|\bdb4o\b|\bobjectdb\b|\bgemstone\b|\bmatisse\b|"
            r"\bzodb\b|\bzope\b",
            r"mongodb|couchdb",
            r"teorema de cap|\bcap\b.*consistencia|consistencia eventual",
        ),
        patrones_debiles=(r"nosql", r"documentos", r"objetos"),
        prioridad=21,
    ),
    Materia(
        key="bbdd-administracion",
        epigraph_code="IV.2.1",
        title="Administración del gestor: cuentas, procesos y copia lógica de datos",
        resumen=(
            "La administración del gestor por dentro: las cuentas y privilegios (SYS, SYSTEM, "
            "SYSDBA, "
            "SYSOPER, SYSBACKUP, SYSRAC, SYSKM, y el control de privilegios en MySQL), los "
            "procesos "
            "de Oracle (PMON, SMON, PMAN, MMON, MMNL, CKPT, LGWR, DBW, ARCn, RECO, LREG), los "
            "ficheros de configuración (listener.ora, sqlnet.ora, tnsnames.ora), las sentencias de "
            "administración (AUDIT, ANALYZE, SET ROLE, SET TRANSACTION, CALL, EXPLAIN), las "
            "herramientas de exportación e importación lógica (expdp/impdp, pg_dump/pg_restore, "
            "mysqldump) y las métricas del sistema."
        ),
        patrones=(
            r"\bsysdba\b|\bsysoper\b|\bsysbackup\b|\bsysrac\b|\bsyskm\b",
            # La memoria del gestor (SGA, PGA, UGA) y sus procesos auxiliares (FBDA) son la
            # estructura interna de Oracle: ahí es donde se estudian, no en el relacional de tablas.
            r"\bsga\b|\bpga\b|\buga\b|\bfbda\b",
            r"estructura (logica|fisica|de memoria)",
            r"administrador(es)? de bases de datos|\bdba\b",
            r"cuentas? (de |especial )?(sys|system|usuario)|usuario(s)? por defecto",
            r"privilegios?|grant\b|\brevoke\b|\bset role\b",
            r"proceso(s)? (de |del )?oracle|proceso(s)? en segundo plano",
            r"\bpmon\b|\bsmon\b|\bpman\b|\bmm[onl]{2}\b|\bckpt\b|\blgwr\b|\bdbw",
            r"\barcn\b|\breco\b|\blreg\b|\bckpt\b",
            # El punto de los nombres de fichero desaparece al normalizar («sqlnet.ora» se lee
            # «sqlnet ora»), así que el patrón tiene que aceptarlo con punto y **con hueco**.
            r"listener(\.|\s)?ora|sqlnet(\.|\s)?ora|tnsnames(\.|\s)?ora|\blistener\b",
            r"\baudit\b|\banalyze\b|\bexplain\b|set transaction|\bcall\b",
            r"expdp|impdp|\bexp\b|\bimp\b|pg_dump|pg_restore|mysqldump|mysqladmin|sqlplus",
            r"copia de seguridad logica|exportacion(es)? de datos|importacion(es)? de datos",
            r"servicios? (de |del )?(base de datos|gestor)|escucha|puerto 3306|puerto 1521|"
            r"puerto 5432|puerto 1433",
            r"\bmtbf\b|\bmttr\b|disponibilidad(es)?|alta disponibilidad",
            r"replicacion(es)?( de bases de datos)?|cluster de base de datos",
            r"instancia(s)? de base de datos",
        ),
        patrones_debiles=(r"usuario", r"comando", r"sentencia", r"servidor"),
        prioridad=22,
    ),
    # --- IV.2.2 Sistemas de almacenamiento y su virtualización -----------------------------------
    Materia(
        key="raid",
        epigraph_code="IV.2.2",
        title="Los niveles RAID: paridad, stripping y mirroring",
        resumen=(
            "Qué es RAID y qué niveles hay: RAID 0 (stripping), RAID 1 (mirroring), RAID 2, RAID "
            "3, "
            "RAID 4, RAID 5 y RAID 6 (paridad dedicada o distribuida), los niveles anidados (0+1, "
            "1+0, 5+0, 5+1, 10, 100) y las variantes 5E y 6E. El número mínimo de discos de cada "
            "nivel, su capacidad útil y su fórmula, la tolerancia a fallos, RAID por hardware y "
            "por software, JBOD y el disco de reserva (standby spare)."
        ),
        patrones=(
            r"\braid\b",
            r"\bjbod\b",
            # `stripping` es la forma que escriben los enunciados; `striping` es la correcta en
            # inglés y también aparece. Las dos, o media asignatura se queda sin materia.
            r"\bstrip(?:p)?ing\b|\bmirroring\b|\bdisk mirroring\b",
            r"paridad(es)?|\bxor\b",
            r"tolerancia a fallos( de discos)?|redundancia de discos",
            r"nivel(es)? de raid|raid anidado(s)?",
            r"discos? (minimo|minimos|necesarios|requiere)",
            r"capacidad (total|util|neta|aprovechable)",
            r"standby spare|disco de reserva|hot spare",
            r"controladora? raid|tarjeta raid|raid por hardware|raid por software",
            r"\bmdadm\b",
        ),
        patrones_debiles=(r"disco", r"discos"),
        prioridad=10,
    ),
    Materia(
        key="almacenamiento-en-red",
        epigraph_code="IV.2.2",
        title="El almacenamiento en red: DAS, NAS, SAN e iSCSI",
        resumen=(
            "Dónde vive el almacenamiento y cómo se accede: DAS (conexión directa), NAS "
            "(almacenamiento en red, a nivel de fichero, SMB/CIFS y NFS, Samba) y SAN (red "
            "dedicada, "
            "a nivel de bloque), con sus protocolos y variantes (Fibre Channel, FCP, FC-AL, FC-SW, "
            "FCIP, FCoE, FC-NVMe, iSCSI, iSNS, AoE), sus componentes (HBA, switches FC, WWN, "
            "zoning, "
            "LUN masking, port binding, cabina y sus caras front-end y back-end) y sus topologías."
        ),
        patrones=(
            r"\bdas\b|direct attached|conexion directa",
            r"\bnas\b|network attached|network attached storage",
            r"\bsan\b|storage area network",
            r"\biscsi\b|\bisns\b|\baoe\b|ata over ethernet",
            r"fibre channel|\bfc\b|\bfcp\b|\bfc-al\b|\bfc-sw\b|\bfcip\b|\bfcoe\b|\bfc-nvme\b",
            r"\bhba\b|host bus adapter|tarjeta.*fibre channel",
            r"\bwwn\b|world wide name",
            r"\bzoning\b|zona(s)? de la san",
            r"lun masking|\blun\b",
            r"port binding|port_binding",
            r"cabina(s)? de discos|front.?end|back.?end",
            r"\bsamba\b|\bcifs\b|\bsmb\b|\bnfs\b",
            r"red (de area )?(de )?almacenamiento|red dedicada|lan.*almacenamiento",
            r"almacenamiento a nivel de (bloque|fichero|archivo)",
            r"\bsds\b|software defined storage|definido por software",
            r"topolog[ií]a(s)? de (red )?san|switches? fc|fabric",
            r"escalabilidad de (san|nas)|conmutad(a|o)s? de almacenamiento",
            # La arquitectura SCSI por dentro (iniciador, destino y su adaptador) y la cara de
            # gestión de la cabina: es donde se estudian, con el resto del almacenamiento en red.
            r"iniciador|destino scsi|\btarget\b|\bcna\b|sendtargets",
            r"controladora de (la|una) cabina|controladora de discos|controladora(es)? del? "
            r"almacenamiento",
            r"\blvm\b|volume group|volumen(es)? logic(o|os)",
            r"lustre|gluster|\bceph\b|sistema de archivos distribuido",
            r"\bsdn\b|red definida por software",
        ),
        patrones_debiles=(r"almacenamiento", r"red", r"bloque", r"fichero"),
        prioridad=11,
    ),
    Materia(
        key="almacenamiento-avanzado",
        epigraph_code="IV.2.2",
        title="Almacenamiento avanzado: thin provisioning, snapshots e hiperconvergencia",
        resumen=(
            "Las técnicas que se montan encima del almacenamiento: el thin provisioning o "
            "aprovisionamiento fino, la deduplicación (y dónde se hace), la compresión, los "
            "snapshots y su diferencia con una copia de seguridad, la replicación, el "
            "almacenamiento "
            "en caché y en niveles, la hiperconvergencia (HCI) y sus nodos, la consolidación y los "
            "soportes (disco, SSD y cinta) para cada uso."
        ),
        patrones=(
            r"thin provision|aprovisionamiento (fino|thin)",
            r"deduplicacion|dedupe",
            r"\bsnapshot(s)?\b|instantanea(s)?",
            r"hiperconvergente|hiperconvergencia|\bhci\b",
            r"replicacion( de datos| sincrona| asincrona)?|espejo remoto",
            r"cinta(s)? magnetica|cinta lto|almacenamiento (a largo plazo|de archivo)|archivado",
            r"\bssd\b|unidad de estado solido|flash",
            r"almacenamiento en (niveles|cache)|tiering",
            r"consolidacion del almacenamiento|virtualizacion del almacenamiento",
            r"pool de recursos|pool de almacenamiento|\bpool\b",
            r"\bsoftware defined\b|definido por software",
            r"presupuesto de capacidad|sobreaprovisionamiento",
        ),
        patrones_debiles=(r"almacenamiento", r"capacidad", r"copia"),
        prioridad=12,
    ),
    # --- IV.2.3 Políticas, sistemas y procedimientos de backup -----------------------------------
    Materia(
        key="backup-politicas",
        epigraph_code="IV.2.3",
        title="La política de copias: tipos, ventana, retención y objetivos",
        resumen=(
            "Cómo se planifica el backup: los tipos de copia (completa, incremental, diferencial y "
            "sintética), la ventana de backup, la frecuencia y el bit de modificado, la retención "
            "y "
            "su política, la regla 3-2-1, dónde se guarda una copia crítica, los objetivos RPO y "
            "RTO "
            "y las métricas MTBF y MTTR, el catálogo de backup, el cliente y el servidor de backup "
            "y "
            "las buenas prácticas y errores habituales."
        ),
        patrones=(
            _COPIA,
            r"\bbackup\b",
            r"copia (completa|incremental|diferencial|sintetica)",
            r"\bincremental(es)?\b|\bdiferencial(es)?\b|backup sintetico",
            r"ventana de (backup|copia)",
            r"retencion de copias|politicas? de retencion|\bretention\b",
            r"regla 3.?2.?1|3 2 1",
            r"\brpo\b|\brto\b|\bmtbf\b|\bmttr\b",
            r"catalogo de backup|bit de modificado",
            r"planificacion de (las )?copias|frecuencia de las copias",
            r"objetivo(s)? de (la copia|recuperacion)|punto de recuperacion",
            r"cliente de backup|servidor de backup|software de backup",
            r"practica(s)? (basica|correcta)|buena(s)? practica(s)?",
            r"almacenamiento (fuera|externo)|cinta.*backup|nube publica.*backup",
            r"prueba(s)? de (restauracion|recuperacion)",
            # La continuidad del negocio: las preguntas que definen RPO y RTO sin nombrarlos.
            r"recuperacion ante desastres|disaster recovery|plan de contingencia|continuidad del "
            r"negocio",
            r"tiempo maximo|tiempo de inactividad|nivel de servicio|punto en el tiempo",
            r"entre cpd|centros? de (datos|proceso de datos).*(comunicacion|replica)",
            r"spectrum protect|tivoli|\bvss\b|volume shadow",
        ),
        patrones_debiles=(r"copia", r"backup", r"restauracion"),
        prioridad=10,
    ),
    Materia(
        key="backup-herramientas-y-modos",
        epigraph_code="IV.2.3",
        title="Modos y herramientas de copia: en caliente, en frío y a nivel de bloque",
        resumen=(
            "Cómo se hace la copia: en caliente (hot) y en frío (cold), con la base abierta o "
            "cerrada y el mecanismo que garantiza la consistencia, el backup lógico frente al "
            "físico "
            "y a nivel de bloque, la deduplicación aplicada a la copia, el snapshot como origen de "
            "la copia, la restauración (restore) y sus formas (granular, completa) y el backup "
            "sintético."
        ),
        patrones=(
            r"backup en (caliente|frio)|hot backup|cold backup",
            r"\brestore\b|restauracion(es)? (granular|completa|de datos)?",
            r"recuperacion (de datos|tras un fallo)|procedimiento de recuperacion",
            r"backup (logico|fisico)|copia logica|copia fisica",
            r"a nivel de (bloque|fichero)",
            r"deduplicacion.*(backup|copia)|compresion.*(backup|copia)",
            r"backup sintetico|synthetic",
            r"consistencia.*(backup|copia)|en caliente.*consistencia",
            r"snapshot(s)? (de la copia|para la copia)|backup basado en snapshot",
            r"copia incremental.*restauracion|restauracion.*incremental",
            r"verificacion de (la copia|las copias)|integridad de la copia",
        ),
        patrones_debiles=(r"copia", r"backup", r"restaurar"),
        prioridad=11,
    ),
    # --- IV.2.4 Backup de sistemas físicos y virtuales -------------------------------------------
    Materia(
        key="backup-fisico-y-virtual",
        epigraph_code="IV.2.4",
        title="El backup de sistemas físicos y de sistemas virtuales",
        resumen=(
            "Lo que cambia cuando lo que se copia es una máquina virtual o un contenedor: el "
            "backup "
            "a nivel de hipervisor, sin apagar la máquina y con snapshot, la ventaja del backup de "
            "sistemas virtuales, el backup de instancias en la nube y la restauración de una "
            "máquina "
            "entera o de un fichero concreto. La replicación y su relación con la copia: por qué "
            "una "
            "no sustituye a la otra."
        ),
        patrones=(
            r"backup (de|en) (maquinas? virtuales?|sistemas? virtuales?|entornos? virtual)",
            r"backup a nivel de hipervisor|a nivel de hipervisor",
            r"maquina(s)? virtual(es)?.*(copia|backup|respaldo)",
            r"backup (de|en) la nube|instancias? (cloud|en la nube)|azure.*ec2|ec2.*azure",
            r"replicacion( de vm| de maquinas virtuales)?|replica",
            r"replicacion.*(sustituye|no sustituye|backup)|backup.*replicacion",
            r"sin apagar( la maquina)?|en caliente.*maquina virtual",
            r"restauracion( de una maquina| completa del sistema)",
            r"backup de contenedores|contenedores?.*(copia|backup)",
        ),
        patrones_debiles=(r"maquina virtual", r"backup", r"copia"),
        prioridad=10,
    ),
    # --- IV.2.5 Virtualización de sistemas y de puestos de usuario -------------------------------
    Materia(
        key="virtualizacion-hipervisores",
        epigraph_code="IV.2.5",
        title="La virtualización de sistemas y los hipervisores",
        resumen=(
            "Qué es virtualizar y qué se virtualiza: el hipervisor o VMM, de tipo 1 (nativo o "
            "bare-metal) y de tipo 2 (hosted), la virtualización completa, la paravirtualización, "
            "la "
            "asistida por hardware (HVM) y la de aplicaciones; el aislamiento, el pool de "
            "recursos, "
            "la migración en vivo y el paging o ballooning de memoria. Y los productos de cada "
            "fabricante: VMware (ESXi, vSphere, Workstation, Fusion), Hyper-V, Xen y XenServer, "
            "KVM "
            "y Red Hat Virtualization, Proxmox, Oracle VM VirtualBox, IBM PowerVM y las "
            "plataformas "
            "de nube."
        ),
        patrones=(
            _HIPERVISOR,
            r"tipo (1|2|uno|dos)\b.*(nativo|hosted)?|bare.?metal|hosted",
            r"virtualizacion (completa|asistida|nativa|de hardware|de aplicaciones|de servidores)",
            r"paravirtualizacion|\bhvm\b|asistida por hardware",
            r"\bvmware\b|\besxi\b|\bvsphere\b|\bworkstation\b|\bhorizon\b",
            r"\bhyper-?v\b|\bxen\b|\bxenserver\b|\bcitrix\b",
            r"\bkvm\b|\bqemu\b|red hat virtualization|\brhv\b",
            r"\bproxmox\b|virtualbox|\bpower ?vm\b|\bibm power\b",
            r"aislamiento.*(virtual|maquina)|\bisolation\b",
            r"migracion en vivo|live migration",
            r"paging|ballooning|memoria de la maquina virtual",
            r"maquina(s)? virtual(es)?|\bvm\b",
            r"\bnfv\b|virtualizacion de funciones de red",
            r"consolidacion de servidores|ratio de consolidacion",
            r"windows server|\besxi\b|ovf\b|\bova\b|formato (abierto )?de (virtualizacion|maquina)",
        ),
        patrones_debiles=(_HIPERVISOR, r"virtualizacion", r"virtual"),
        prioridad=10,
    ),
    Materia(
        key="vdi",
        epigraph_code="IV.2.5",
        title="La virtualización de puestos de usuario (VDI)",
        resumen=(
            "La infraestructura de escritorio virtual (VDI): sus componentes, el broker de "
            "conexiones, el escritorio persistente y el no persistente, la virtualización de "
            "aplicaciones y de presentación, y los productos (VMware Horizon, Citrix, Microsoft)."
        ),
        patrones=(
            r"\bvdi\b|virtual desktop infrastructure",
            r"escritorio(s)? virtual(es)?|puesto(s)? de (usuario|trabajo) virtual",
            r"broker de conexiones|connection broker",
            r"persistente.*no persistente|no persistente.*persistente",
            r"virtualizacion de (aplicaciones|presentacion|puestos)",
            r"\bhorizon\b|\bxendesktop\b|\bxenapp\b",
            r"escritorio remoto|\brds\b|\bts\b.*escritorio",
            r"escritorio(s)? (persistente|no persistente)",
        ),
        patrones_debiles=(r"escritorio", r"usuario"),
        prioridad=11,
    ),
    Materia(
        key="computacion-en-la-nube",
        epigraph_code="IV.2.5",
        title="La computación en la nube",
        resumen=(
            "La definición de computación en la nube del NIST y sus piezas: las cinco "
            "características esenciales, los tres modelos de servicio (IaaS, PaaS y SaaS), los "
            "modelos de despliegue (pública, privada, híbrida y comunitaria), el pago por uso y la "
            "elasticidad, las nubes de software libre y el uso de la nube en la recuperación ante "
            "desastres. Va aquí porque es la plataforma sobre la que se virtualiza y donde caen "
            "sus "
            "preguntas, que no tienen epígrafe propio en el temario."
        ),
        patrones=(
            r"computacion en la nube|cloud computing|\bcloud\b|en la nube",
            r"\bnist\b",
            r"\biaas\b|\bpaas\b|\bsaas\b|infraestructura como servicio|plataforma como servicio|"
            r"software como servicio",
            r"nube (publica|privada|hibrida|comunitaria)|modelo(s)? de despliegue",
            r"caracteristicas esenciales.*nube|elasticidad|pago por uso",
            r"nube de software libre|openstack|openshift.*nube|cloud de software libre",
            r"servicios? en la nube|proveedor(es)? de nube",
        ),
        patrones_debiles=(r"nube", r"cloud", r"servicio"),
        prioridad=13,
    ),
    Materia(
        key="contenedores-y-orquestacion",
        epigraph_code="IV.2.5",
        title="Contenedores y orquestación: Docker, Kubernetes y OpenShift",
        resumen=(
            "La virtualización ligera por contenedores y su orquestación: Docker y sus comandos, "
            "imágenes y registros (Docker Hub), Podman; Kubernetes y sus objetos (pod, namespace, "
            "volumen persistente, etcd, la unidad más pequeña), Helm, los servicios gestionados "
            "(AKS, EKS, GKE, Amazon ECS), OpenShift y OKD, la malla de servicios (Istio, Envoy) y "
            "dónde se guardan las imágenes."
        ),
        patrones=(
            r"\bdocker\b|\bpodman\b|contenedor(es)?",
            r"\bkubernetes\b|\bk8s\b",
            r"\bopenshift\b|\bokd\b",
            r"\bhelm\b",
            r"\bpod(s)?\b|\bnamespace(s)?\b|\betcd\b",
            r"volumen(es)? persistente(s)?|\bpv\b|\bpvc\b",
            r"\baks\b|\beks\b|\bgke\b|amazon ecs|servicio(s)? de kubernetes administrado",
            r"registro(s)? (de imagenes|de contenedores)|docker hub|repositorio de imagenes",
            r"\bistio\b|\benvoy\b|service mesh|malla de servicios",
            r"imagen(es)? de contenedor|dockerfile",
            r"orquestacion( de contenedores)?",
        ),
        patrones_debiles=(r"contenedor", r"imagen", r"cluster"),
        prioridad=12,
    ),
)

#: El orden en que se **enseña** el índice: primero la base de datos (su administración y sus
#: productos), después el almacenamiento donde vive, después cómo se copia y, por último, lo que se
#: virtualiza —que es el orden del título del tema y el orden en que se estudia—.
ORDEN: tuple[str, ...] = (
    "bbdd-relacionales",
    "bbdd-nosql",
    "bbdd-administracion",
    "raid",
    "almacenamiento-en-red",
    "almacenamiento-avanzado",
    "backup-politicas",
    "backup-herramientas-y-modos",
    "backup-fisico-y-virtual",
    "virtualizacion-hipervisores",
    "vdi",
    "contenedores-y-orquestacion",
    "computacion-en-la-nube",
)

__all__ = ["MATERIAS", "ORDEN"]
