"""El catálogo de materias de II.2 (periféricos, impresión, almacenamiento y visualización).

II.2 es un tema **técnico** de hardware y su banco lo dice con una claridad poco habitual: de sus
**175 grupos de preguntas, 87 no traen epígrafe** (el 50 %) y hablan todos de lo mismo —velocidades
de
USB, Thunderbolt, FireWire, HDMI, DVI y DisplayPort, impresoras y su cola, discos y RAID, monitores
y
escáneres—, mientras que los cuatro epígrafes oficiales son un esqueleto de 26, 10, 28 y 24 grupos.
Por eso el índice va **por asunto** y el enunciado es el que decide, como en IV.7, IV.9, II.1,
III.3 y
IV.10.

Dieciséis apartados, en el orden en que se estudia:

- el **bus USB y sus versiones** (II.2.1), que es el bloque más repetido del banco: las versiones
  (1.0, 1.1, 2.0, 3.0, 3.1, 3.2 y 4), sus nombres comerciales —SuperSpeed, USB 3.1 Gen 1—, los
  modificadores Gen 1x1, Gen 1x2, Gen 2x1 y Gen 2x2, las velocidades, el número de cables y de
  pines,
  el conector tipo C y su simetría, y el USB *on-the-go*;
- **Thunderbolt, FireWire y los puertos de vídeo** (II.2.1): las cinco generaciones de Thunderbolt
con
  su conector —el de Apple en las dos primeras, el tipo C después—, el bus FireWire con sus normas
  IEEE 1394 y sus velocidades de 400, 800, s1600 y s3200, y los puertos de vídeo HDMI, DisplayPort y
  DVI con sus versiones, sus pines y sus tipos;
- los **puertos serie y paralelo** (II.2.1): RS-232C, el puerto paralelo y su configuración en la
BIOS
  cuando consume un canal de acceso directo a memoria, el interfaz serie, y el adaptador de bus de
  host;
- el **bus de expansión y sus carriles** (II.2.1): PCI Express, cuántos carriles admite y qué
velocidad
  alcanza, y qué puerto se usa para conectar una tarjeta gráfica a la placa base;
- la **administración de los periféricos** (II.2.1): qué son los controladores que vienen con una
  tarjeta de red y qué hay que hacer para conectar un equipo a la red de área local, la
  configuración
  del puerto y la administración de los dispositivos móviles;
- los **periféricos de entrada y de salida** (II.2.1): qué se considera periférico de entrada y qué
de
  salida, y las distribuciones de teclado QWERTY y DVORAK;
- los **tipos de impresora y sus mecanismos** (II.2.2): la clasificación por mecanismo de impresión
  —impacto, matricial, inyección, láser, térmica y de sublimación—, los cabezales piezoeléctricos,
  la
  impresora de tickets, la impresión 3D y sus tecnologías y la impresión GDI o basada en host;
- la **impresión en red y la cola de trabajos** (II.2.2): los protocolos de impresión en red, cómo
se
  comparte una impresora conectada a un equipo y por qué deja de imprimir a todos, cómo se configura
  en Windows una impresora conectada directamente a la red, y las órdenes para continuar o borrar
  los
  trabajos en pausa, también en Linux;
- los **discos magnéticos y su estructura** (II.2.3): el sector, la pista, el cilindro y el clúster
y
  su orden de tamaño, el tiempo de latencia y el retardo de acceso, la organización física y la
  lógica,
  la partición activa, y la familia de discos magnéticos y extraíbles;
- los **discos de estado sólido y las memorias flash** (II.2.3): qué son las memorias flash, la
  arquitectura 3D NAND frente a la de celdas planas, el TRIM, el NVMe y las velocidades de lectura y
  escritura;
- los **niveles RAID** (II.2.3): qué es cada nivel, cuántos discos necesita como mínimo cada uno,
cuál
  no tiene tolerancia a fallos, en cuáles se reparte la paridad entre todos los discos, la capacidad
  útil y el nivel que emplea códigos de Hamming;
- el **almacenamiento óptico y la jerarquía** (II.2.3): los discos ópticos y sus novedades, y las
  jerarquías de almacenamiento ordenadas de más rápido a menos rápido acceso;
- las **interfaces de disco** (II.2.3): SATA y su cable de datos, SAS y sus velocidades, y el
sistema
  de almacenamiento que accede a nivel de bloque;
- los **monitores, sus paneles y sus tecnologías** (II.2.4): LCD, OLED, LED, plasma y las
tecnologías
  que no existen, los tipos de panel, el tamaño de punto, el refresco y la diferencia entre una
  resolución progresiva y una entrelazada;
- las **resoluciones, la memoria de vídeo y los espacios de color** (II.2.4): 640x480, 1280x720,
Full
  HD y 8K, los bits por píxel y la memoria de vídeo que hace falta para una resolución con color
  verdadero, y los espacios de color que existen y los que no;
- los **escáneres y la digitalización** (II.2.4): las partes de un escáner y cuál determina la
  resolución óptica, la resolución interpolada, los estándares y controladores de escaneo, los tipos
  —el de gran formato para estudios de diseño y el que copia libros valiosos sin dañarlos—, el
  reconocimiento óptico de caracteres, los formatos de los ficheros escaneados y el tamaño que
  ocupan;
- y la **realidad virtual, la aumentada y las pantallas táctiles** (II.2.4): qué es cada una, los
  anáglifos, el sistema estéreo activo de la realidad inmersiva, el lápiz óptico y las tecnologías
  de
  las pantallas táctiles.

Cuatro decisiones de los patrones, dichas donde se leen:

- **la lección de III.3 y II.3, aplicada desde el principio**: en este banco «velocidad»,
«estándar»,
  «puerto» y «dispositivo» salen en casi todos los enunciados, así que **no son patrones propios de
  ninguna materia** y de los débiles solo se usan los que no pueden llevarse nada de otro apartado.
  Aquí lo que distingue una pregunta de otra es **la cifra** —3.0 frente a 2.0, 400 frente a 800,
  1080p
  frente a 1080i— y por eso los patrones miran las cifras;
- **`\\bus\\b` no se usa suelto**: el banco lo dice para FireWire («el bus FireWire es lo mismo que
  el…»), para PCIe y para USB, así que FireWire se pide por su nombre y por su norma (`1394`) y el
  bus
  de expansión por `pci ?e`, que es de lo que habla su pregunta;
- **la lección de II.3, aplicada**: los títulos de los dieciséis apartados **no comparten las tres
  primeras palabras entre tres de ellos** —la puerta de *misma cabecera* mira el tema entero y exige
  que no haya tres que empiecen igual—, y se comprueba antes de correr, que es gratis;
- y **lo que es de otro tema no se lava**: las dos preguntas de la **NTI de Digitalización de
  documentos** («componentes digitales de un documento electrónico» e «imágenes electrónicas
  definidas
  en la NTI») son de **I.8.4**, Normas técnicas de Interoperabilidad, y van a la bandeja del
  propietario con su motivo (`Motivo.SIN_MATERIA_EN_EL_INDICE`) en vez de a un apartado de este
  tema.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: El bus USB: versiones, velocidades, cables, conectores y OTG.
_USB = (
    r"\busb\b",
    r"usb ?(1|2|3|4)( ?\.?\d)?\b|usb ?3 ?[12]|usb ?4",
    r"gen ?[12] ?x ?[12]|superspeed",
    r"tipo ?c|type ?c|conector(es)? usb|pines tiene un conector usb",
    r"on ?-? ?the ?-? ?go|\botg\b",
    r"cuantos cables utiliza|simetric",
)

#: Thunderbolt, FireWire y los puertos de vídeo.
_VIDEO_Y_BUSES = (
    r"thunderbol",
    r"firewire|firewire ?(400|800)|s ?1600|s ?3200|1394",
    r"\bhdmi\b|displayport|display ?port",
    r"\bdvi\b|dvi ?-? ?[aid]\b",
    r"puerto(s)? de video|senal de video",
    r"creado por el fabricante apple|conector usado para carga y datos",
    r"unificar la transferencia de datos",
)

#: Los puertos serie y paralelo.
_SERIE_Y_PARALELO = (
    r"rs ?-? ?232|rs ?232c|interfaz serie|comunicacion en serie",
    r"puerto paralelo|\bparalelo\b|\bepp\b|\becp\b|canal de acceso directo a memoria",
    r"\bhba\b|host bus adapter|adaptador de bus de host",
    r"audio solamente|solo audio",
)

#: El bus de expansión y sus carriles.
_EXPANSION = (
    r"\bpci ?e\b|\bpcie\b|pci express",
    r"carriles|tarjeta grafica a la placa|carril",
    r"bus de expansion|ranura de expansion",
)

#: La administración de los periféricos.
_ADMINISTRACION = (
    r"driver(s)?|controlador(es)? de (la tarjeta|dispositivo)|los drivers",
    r"configurar un equipo|conectarlo a la red de area local|tarjeta de red a instalar",
    r"configuracion de un puerto|configura en windows una impresora",
    r"\bmdm\b|dispositivos moviles|administracion de dispositivos",
    r"administrar los perifericos",
)

#: Los periféricos de entrada y de salida.
_ENTRADA_Y_SALIDA = (
    r"periferico(s)? de (entrada|salida)|perifericos de entrada y salida",
    r"no es un dispositivo de salida|se consideran perifericos",
    r"teclado(s)?|qwerty|dvorak|distribucion de teclado",
    r"raton|escanner de codigos|lector de",
)

#: Los tipos de impresora y sus mecanismos.
_IMPRESORAS = (
    r"impresora(s)? (de|por|termica|matricial|laser|inyeccion)|tipo(s)? de impresora",
    r"mecanismo(s)? de impresion|clasificamos por su mecanismo",
    r"impresora de impacto|impacto|matricial|piezo ?electrica|cabezales",
    r"sublimacion|tinta|toner|laser|termica|tickets?",
    r"impresion 3d|tecnologia de impresion|\bfdm\b",
    r"\bgdi\b|graphics device interface|basada en host",
    r"no constituye un tipo de impresora|no es uno de ellos",
    r"impresion mas economica|coste por pagina|mas economica",
)

#: La impresión en red y la cola de trabajos.
_IMPRESION_EN_RED = (
    r"impresion en red|protocolos de impresion|impresora compartida|compartir una impresora",
    r"cola de impresion|trabajos pendientes|trabajos en pausa|impresora ?\d|se ha quedado en pausa",
    r"imprimir en (linux|windows)|comando.*(cola|impresion)",
    r"conectada directamente a la red|impresora en red",
)

#: Los discos magnéticos y su estructura.
_DISCOS_MAGNETICOS = (
    r"\bsector\b|\bpista\b|\bcilindro\b|\bcluster\b|clusters?",
    r"disco(s)? (duro|magnetico|zip|jaz|extraible)|unidad(es)? de disco",
    r"latencia|tiempo de acceso|retardo|posiciona sobre la pista",
    r"particion activa|organizacion (interna|fisica|logica) de los discos",
    r"respecto al almacenamiento en disco",
    r"jerarquia de almacenamiento|de mayor a menor tamano|mas rapido acceso",
    r"estructura fisica de un disco|estructura logica de un disco",
)

#: Los discos de estado sólido y las memorias flash.
_SOLIDOS = (
    r"\bssd\b|solid state drive|discos? de estado solido|unidades? ssd",
    r"memorias? flash|\bflash\b|\bnand\b|3d nand|celdas planas",
    r"\btrim\b|\bnvme\b",
    r"almacenamiento de datos volatil|no volatil",
    r"velocidades de lectura y escritura|cache de escritura",
)

#: Los niveles RAID.
_RAID = (
    r"\braid\b|raid ?(0|1|2|3|4|5|6|10|50|60)\b",
    r"paridad|tolerancia a fallos|espejo|stripping|mirroring",
    r"codigos? de hamming|hamming",
    r"array de discos|discos? son necesarios como minimo",
)

#: El almacenamiento óptico.
_OPTICO = (
    r"optico(s)?|\bcd\b|\bdvd\b|blu ?-? ?ray",
    r"almacenamiento masivo|disco optico",
    r"\bcinta\b|almacenamiento (en|por) cinta",
)

#: Las interfaces de disco.
_INTERFACES_DISCO = (
    r"\bsata\b|sata ?(2|3)|serial ?ata",
    r"\bsas\b|sas ?-? ?3|-sas\b|scsi",
    r"nivel de bloque|acceso a nivel de bloque",
    r"bus serie|16 ?gbps|interfaz que permite trabajar",
    r"medio de almacenamiento tiene mayor velocidad|componentes? de almacenamiento ofrece",
    r"\bhdd\b|disco duro mecanico|discos? mecanicos",
)

#: Los monitores y sus tecnologías.
_MONITORES = (
    r"monitor(es)?|pantalla(s)?",
    r"\blcd\b|\boled\b|\bled\b|plasma|\bcrt\b|\btft\b|\bips\b|\bva\b",
    r"panel de una pantalla|tecnologia de monitor no existe",
    r"siglas no corresponde a un tipo de monitor",
    r"dot ?pitch|tamano de punto|refresco|60 ?hz",
    r"1080 ?(p|i)\b|progresiv|entrelazad",
    r"pantalla tactil|pantallas tactiles",
)

#: Las resoluciones, la memoria de vídeo y los espacios de color.
_RESOLUCIONES = (
    r"resolucion(es)? (de|grafica|estandar|full|8k)|full ?hd|\b4k\b|\b8k\b|\buhd\b",
    r"\d{3,4} ?x ?\d{3,4}",
    r"memoria de video|color verdadero|true color",
    r"espacio(s)? de color|espacios? cromatico|cymk|cmyk|\brgb\b",
    r"bits utilizados para definir cada pixel|bits por pixel|\bpixel",
    r"redimension|tamano de las imagenes|imagenes que se publican",
    r"tamano de (la )?imagen digitalizada|tamano mayor para un mismo fichero",
)

#: Los escáneres y la digitalización.
_ESCANERES = (
    r"escaner(es)?|digitaliza|digitalizacion|escaneo",
    r"resolucion (optica|interpolada)|componente de un escaner|elemento basico de un escaner",
    r"\bocr\b|reconocimiento optico de caracteres",
    r"gran formato|estudios de diseno grafico|libros o documentos que.*no se les quiere deteriorar",
    r"formatos? de (salida|los ficheros escaneados)|ficheros generados mediante un escaner",
    r"lapiz optico",
)

#: La realidad virtual, la aumentada y el 3D.
_REALIDAD = (
    r"realidad (aumentada|virtual)|virtual inmersiva|realidad (mixta)",
    r"anaglifos?|estereo|\b3d\b|tres dimensiones",
    r"reconocimiento de pulso acustico",
)

MATERIAS: tuple[Materia, ...] = (
    # --- II.2.1 Periféricos: conectividad y administración ---------------------------------------
    Materia(
        key="el-bus-usb-sus-versiones-y-sus-conectores",
        epigraph_code="II.2.1",
        title="El bus USB: versiones, velocidades y conectores",
        resumen=(
            "El puerto de siempre: las versiones 1.0, 1.1, 2.0, 3.0, 3.1, 3.2 y 4 con su velocidad "
            "y"
            "su nombre comercial (SuperSpeed, USB 3.1 Gen 1), los modificadores Gen 1x1, Gen 1x2, "
            "Gen 2x1 y Gen 2x2, cuántos cables y cuántos pines tiene cada conector, el tipo C y su "
            "simetría, y el USB on-the-go."
        ),
        patrones=_USB,
        prioridad=30,
    ),
    Materia(
        key="thunderbolt-firewire-y-los-puertos-de-video",
        epigraph_code="II.2.1",
        title="Thunderbolt, FireWire y los puertos de vídeo (HDMI, DisplayPort y DVI)",
        resumen=(
            "Los puertos que llevan datos y vídeo: las cinco generaciones de Thunderbolt con su "
            "conector y su velocidad, el bus FireWire con sus normas IEEE 1394 y sus velocidades "
            "de"
            "400, 800, s1600 y s3200, y los puertos HDMI, DisplayPort y DVI con sus versiones, sus "
            "pines y sus tipos."
        ),
        patrones=_VIDEO_Y_BUSES,
        prioridad=25,
    ),
    Materia(
        key="los-puertos-serie-y-paralelo",
        epigraph_code="II.2.1",
        title="Los puertos serie y paralelo, y el adaptador de bus de host",
        resumen=(
            "Los puertos clásicos: el RS-232C y el interfaz serie, el puerto paralelo y su "
            "configuración en la BIOS cuando consume un canal de acceso directo a memoria, el "
            "adaptador de bus de host y los conectores que solo llevan audio."
        ),
        patrones=_SERIE_Y_PARALELO,
        prioridad=30,
    ),
    Materia(
        key="el-bus-de-expansion-y-sus-carriles",
        epigraph_code="II.2.1",
        title="El bus de expansión y sus carriles",
        resumen=(
            "Cómo se conectan las tarjetas por dentro: PCI Express, cuántos carriles admite y qué "
            "velocidad alcanza, y qué puerto se usa para conectar una tarjeta gráfica a la placa "
            "base."
        ),
        patrones=_EXPANSION,
        prioridad=35,
    ),
    Materia(
        key="la-administracion-de-los-perifericos",
        epigraph_code="II.2.1",
        title="La administración de los periféricos: controladores y configuración",
        resumen=(
            "Poner un periférico a funcionar: qué son los controladores que vienen con una tarjeta "
            "de red y qué hay que hacer para conectar el equipo a la red de área local, la "
            "configuración del puerto, y la administración de los dispositivos móviles."
        ),
        patrones=_ADMINISTRACION,
        prioridad=40,
    ),
    Materia(
        key="los-perifericos-de-entrada-y-de-salida",
        epigraph_code="II.2.1",
        title="Los periféricos de entrada y de salida",
        resumen=(
            "Qué es cada cosa: qué se considera periférico de entrada y qué de salida, y las "
            "distribuciones de teclado QWERTY y DVORAK."
        ),
        patrones=_ENTRADA_Y_SALIDA,
        prioridad=45,
    ),
    # --- II.2.2 Elementos de impresión ----------------------------------------------------------
    Materia(
        key="los-tipos-de-impresora-y-sus-mecanismos",
        epigraph_code="II.2.2",
        title="Los tipos de impresora y sus mecanismos",
        resumen=(
            "Cómo imprime cada una: la clasificación por mecanismo —impacto, matricial, inyección, "
            "láser, térmica y sublimación—, los cabezales piezoeléctricos, la impresora de "
            "tickets,"
            "la impresión 3D y sus tecnologías, y la impresión GDI o basada en host."
        ),
        patrones=_IMPRESORAS,
        prioridad=25,
    ),
    Materia(
        key="la-impresion-en-red-y-la-cola-de-trabajos",
        epigraph_code="II.2.2",
        title="La impresión en red y la cola de trabajos",
        resumen=(
            "Compartir la impresora y desatascarla: los protocolos de impresión en red, por qué "
            "una"
            "impresora compartida deja de imprimir para todos, cómo se configura en Windows una "
            "impresora conectada directamente a la red, y las órdenes para continuar o borrar los "
            "trabajos en pausa, también en Linux."
        ),
        patrones=_IMPRESION_EN_RED,
        prioridad=20,
    ),
    # --- II.2.3 Elementos de almacenamiento -----------------------------------------------------
    Materia(
        key="los-discos-magneticos-y-su-estructura",
        epigraph_code="II.2.3",
        title="Los discos magnéticos y su estructura física y lógica",
        resumen=(
            "El disco de toda la vida: el sector, la pista, el cilindro y el clúster y su orden de "
            "tamaño, el tiempo de latencia y el retardo de acceso, la organización física y la "
            "lógica, la partición activa, y la familia de discos magnéticos y extraíbles."
        ),
        patrones=_DISCOS_MAGNETICOS,
        prioridad=30,
    ),
    Materia(
        key="los-discos-de-estado-solido-y-las-memorias-flash",
        epigraph_code="II.2.3",
        title="Los discos de estado sólido y las memorias flash",
        resumen=(
            "El almacenamiento sin partes móviles: qué son las memorias flash, la arquitectura 3D "
            "NAND frente a la de celdas planas, el TRIM, el NVMe, y qué almacenamiento es volátil "
            "y"
            "cuál no."
        ),
        patrones=_SOLIDOS,
        prioridad=25,
    ),
    Materia(
        key="los-niveles-raid",
        epigraph_code="II.2.3",
        title="Los niveles RAID y la tolerancia a fallos",
        resumen=(
            "Juntar discos: qué es cada nivel RAID, cuántos discos necesita como mínimo cada uno, "
            "cuál no tiene tolerancia a fallos, en cuáles se reparte la paridad entre todos los "
            "discos físicos, la capacidad útil de un RAID 5 y el nivel que emplea códigos de "
            "Hamming."
        ),
        patrones=_RAID,
        prioridad=15,
    ),
    Materia(
        key="el-almacenamiento-optico-y-la-jerarquia",
        epigraph_code="II.2.3",
        title="El almacenamiento óptico y la jerarquía de almacenamiento",
        resumen=(
            "Los discos que se leen con luz: el CD, el DVD y el Blu-ray, los discos ópticos de "
            "almacenamiento masivo, la cinta, y las jerarquías de almacenamiento ordenadas de más "
            "rápido a menos rápido acceso."
        ),
        patrones=_OPTICO,
        prioridad=30,
    ),
    Materia(
        key="las-interfaces-de-disco-sata-sas-y-bloque",
        epigraph_code="II.2.3",
        title="Las interfaces de disco: SATA, SAS y el acceso a nivel de bloque",
        resumen=(
            "Cómo se enchufa el disco: SATA y su cable de datos, qué velocidad ofrece SATA 3.0, "
            "las"
            "velocidades de SAS, y el sistema de almacenamiento que accede a nivel de bloque de "
            "bits."
        ),
        patrones=_INTERFACES_DISCO,
        prioridad=35,
    ),
    # --- II.2.4 Elementos de visualización y digitalización -------------------------------------
    Materia(
        key="los-monitores-sus-paneles-y-sus-tecnologias",
        epigraph_code="II.2.4",
        title="Los monitores, sus paneles y sus tecnologías",
        resumen=(
            "La pantalla: LCD, OLED, LED, plasma y las tecnologías que no existen, los tipos de "
            "panel, el tamaño de punto, el refresco, la diferencia entre una resolución progresiva "
            "y"
            "una entrelazada, y las tecnologías de las pantallas táctiles."
        ),
        patrones=_MONITORES,
        prioridad=25,
    ),
    Materia(
        key="las-resoluciones-la-memoria-de-video-y-el-color",
        epigraph_code="II.2.4",
        title="Las resoluciones, la memoria de vídeo y los espacios de color",
        resumen=(
            "Cuánto se ve y con cuántos colores: 640x480, 1280x720, Full HD, 4K y 8K UHD, los bits "
            "por píxel, la memoria de vídeo que hace falta para una resolución con color "
            "verdadero,"
            "y los espacios de color que existen y los que no."
        ),
        patrones=_RESOLUCIONES,
        prioridad=20,
    ),
    Materia(
        key="los-escaneres-y-la-digitalizacion",
        epigraph_code="II.2.4",
        title="Los escáneres y el proceso de digitalización",
        resumen=(
            "Pasar el papel a bits: las partes de un escáner y cuál determina la resolución "
            "óptica,"
            "la resolución interpolada, los estándares y controladores de escaneo, el escáner de "
            "gran formato y el que copia libros valiosos sin dañarlos, el reconocimiento óptico de "
            "caracteres, los formatos de los ficheros escaneados y el tamaño que ocupan, y el "
            "lápiz"
            "óptico."
        ),
        patrones=_ESCANERES,
        prioridad=25,
    ),
    Materia(
        key="la-realidad-virtual-aumentada-y-el-3d",
        epigraph_code="II.2.4",
        title="La realidad virtual, la aumentada y el 3D",
        resumen=(
            "Ver lo que no está: qué es la realidad aumentada y la virtual inmersiva, el sistema "
            "estéreo activo, los anáglifos y las tecnologías de representación en tres dimensiones."
        ),
        patrones=_REALIDAD,
        prioridad=30,
    ),
)

#: El orden del índice: primero cómo se conecta un periférico —USB, los puertos de vídeo, los
#: serie y paralelo, el bus de expansión, su administración y qué es de entrada y qué de salida—,
#: después lo que imprime, luego lo que guarda y, al final, lo que se ve y se digitaliza.
ORDEN: tuple[str, ...] = (
    "el-bus-usb-sus-versiones-y-sus-conectores",
    "thunderbolt-firewire-y-los-puertos-de-video",
    "los-puertos-serie-y-paralelo",
    "el-bus-de-expansion-y-sus-carriles",
    "la-administracion-de-los-perifericos",
    "los-perifericos-de-entrada-y-de-salida",
    "los-tipos-de-impresora-y-sus-mecanismos",
    "la-impresion-en-red-y-la-cola-de-trabajos",
    "los-discos-magneticos-y-su-estructura",
    "los-discos-de-estado-solido-y-las-memorias-flash",
    "los-niveles-raid",
    "el-almacenamiento-optico-y-la-jerarquia",
    "las-interfaces-de-disco-sata-sas-y-bloque",
    "los-monitores-sus-paneles-y-sus-tecnologias",
    "las-resoluciones-la-memoria-de-video-y-el-color",
    "los-escaneres-y-la-digitalizacion",
    "la-realidad-virtual-aumentada-y-el-3d",
)

__all__ = ["MATERIAS", "ORDEN"]
