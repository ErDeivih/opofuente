"""El catálogo de materias de IV.6 (comunicaciones, medios de transmisión y redes).

IV.6 es un tema **técnico**: lo que lo estructura son sus siete epígrafes —las comunicaciones, los
medios de transmisión, los modos de comunicación, los equipos terminales y de interconexión, las
redes
de comunicaciones, las redes de conmutación y de difusión y las comunicaciones móviles e
inalámbricas— y dentro de cada uno el índice va por **asunto**, como en IV.7, IV.2 y II.4. Este
catálogo los abre en **dieciséis** apartados porque las preguntas del tema se agrupan así de verdad:

- las comunicaciones, en tres: los **conceptos de la transmisión** (la señal analógica y digital, el
  ancho de banda, la velocidad, la modulación y la codificación, la atenuación, el ruido, los
  errores y
  la paridad), los **organismos y los estándares** (la UIT y sus series, el IEEE, la ISO/IEC y la
  ANSI/TIA) y la **voz y el vídeo sobre IP** (los protocolos de señalización, los códecs y la
  calidad
  de servicio);
- los medios de transmisión, en cuatro: el **cableado de cobre** (los pares trenzados, sus
categorías y
  clases, el apantallamiento y la diafonía), la **fibra óptica** (monomodo y multimodo, OM1 a OM4,
  las
  ventanas de longitud de onda y los conectores), el **cableado estructurado** (sus subsistemas, los
  armarios y las normas que lo regulan) y los **medios inalámbricos y el satélite** (los
  radioenlaces,
  las órbitas, el PLC y las líneas de transmisión);
- los modos de comunicación, en tres: los **modos** (simplex, semidúplex y dúplex; serie y paralelo;
  síncrono y asíncrono; banda base y banda ancha), la **multiplexación** (por división de
  frecuencia,
  de tiempo, de código y de longitud de onda) y la **conmutación** (de circuitos, de mensajes y de
  paquetes);
- los equipos, en uno: los **equipos terminales y de interconexión** (el DTE y el DCE, el módem, el
  repetidor, el concentrador, el conmutador, el encaminador, la pasarela y el punto de acceso) y los
  protocolos de redundancia y de encaminamiento;
- las redes de comunicaciones, en uno: las **tecnologías de acceso** (la familia xDSL, la fibra
hasta
  el hogar, el cable, el PLC y el DSLAM);
- las redes de conmutación y de difusión, en uno: las **redes de área extensa** (Frame Relay, ATM,
  RDSI y MPLS, con sus campos, sus celdas y sus circuitos virtuales);
- las comunicaciones móviles e inalámbricas, en tres: la **telefonía móvil** (las generaciones, GSM,
  UMTS, LTE y 5G, con sus bandas y su handover), las **redes inalámbricas** (IEEE 802.11 y sus
  versiones, las bandas de 2,4, 5 y 6 GHz, la seguridad WEP/WPA/WPA2/WPA3, Bluetooth y NFC) y las
  **radiocomunicaciones profesionales** (TETRA y su modo DMO, DECT y la movilidad IP).

Tres decisiones de redacción de los patrones, dichas donde se leen:

- las **categorías del cableado y las versiones del WiFi** se escriben de muchas maneras en el
material
  (`CAT6`, `cat 6`, `categoría 6`, `clase E`, `Wi-Fi 6`, `802.11ax`, `WiFi6`), así que los patrones
  cubren las tres formas y el número suelto;
- las **siglas van con `\\b`** (`\\batm\\b`, `\\brdsi\\b`, `\\bmpls\\b`, `\\bgsm\\b`, `\\blte\\b`,
  `\\bqos\\b`): sin la frontera, `atm` casa dentro de `atmosfera` y `lt` de cualquier palabra, y el
  reparto se llena de falsos positivos;
- **`red` y `comunicaciones` no son patrones propios de nadie**: aparecen en la mitad de los
  enunciados del tema, así que viven en los `patrones_debiles` del apartado de conceptos. Lo
  particular
  gana a lo general, que es la regla de todos los catálogos del proyecto.

Las preguntas que no se sitúan ni por su enunciado ni por el texto de sus hechos **no** acaban en un
cajón: van a la bandeja del propietario con su motivo (`Motivo.SIN_MATERIA_EN_EL_INDICE`). Por eso
este
catálogo, como el de IV.6 y el de II.4, **no tiene cajones**.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Los organismos y las normas que el material cita, como los deja el texto normalizado.
_UIT = (
    r"\buit\b|\bitu\b|union internacional de telecomunicaciones|"
    r"recomendacion(es)? (de la )?(uit|itu)|"
    r"serie [gqxv] de la (uit|itu)"
)
#: El IEEE **por su nombre**, sin los números de sus grupos de trabajo: `802 ?11` es del WiFi y del
#: cableado, no de quién normaliza, y con el número suelto el apartado de organismos se llevaba
#: media asignatura por citar la norma al principio del enunciado.
_IEEE = r"\bieee\b|instituto de ingenieros electricos y electronicos"
_ISO_11801 = r"iso ?/? ?iec ?11801|iso ?11801|ansi ?/? ?tia ?568|tia ?568|en ?50173"

MATERIAS: tuple[Materia, ...] = (
    # --- IV.6.1 Comunicaciones -------------------------------------------------------------------
    Materia(
        key="conceptos-de-transmision",
        epigraph_code="IV.6.1",
        title="Los conceptos de la transmisión: señal, ancho de banda y errores",
        resumen=(
            "Lo que se mide y lo que se degrada al transmitir: la señal analógica y la digital, la "
            "amplitud, la frecuencia, el periodo, la fase y el ciclo de trabajo, la velocidad de "
            "transmisión y el ancho de banda, la capacidad del canal, la modulación y la "
            "codificación, "
            "la atenuación, la distorsión, el ruido y la diafonía, la detección y la corrección de "
            "errores (el bit de paridad, la paridad par e impar y las tramas de comprobación) y la "
            "eficiencia del enlace."
        ),
        patrones=(
            r"ancho de banda|velocidad de (transmision|bajada|subida)|\bbps\b|gbps|mbps|kbps",
            r"(señal|senal) (digital|analogica)|periodo|frecuencia|ciclo de trabajo|"
            r"ancho del impulso",
            r"modulacion|codificacion|demodulacion",
            r"bit de paridad|paridad (par|impar)|deteccion de errores|correccion de errores|"
            r"trama de comprobacion|\bcrc\b",
            r"atenuacion|distorsion|ruido|diafonia|crosstalk|interferencia",
            r"capacidad del canal|teorema de (nyquist|shannon)|relacion señal ruido",
            r"transmision (de datos|serie|paralela)|velocidad de transmision de datos",
        ),
        patrones_debiles=(r"transmision", r"señal", r"senal", r"datos"),
        prioridad=60,
    ),
    Materia(
        key="organismos-y-estandares",
        epigraph_code="IV.6.1",
        title="Los organismos y los estándares de las telecomunicaciones",
        resumen=(
            "Quién regula y quién normaliza: la Unión Internacional de Telecomunicaciones y sus "
            "series "
            "de recomendaciones (la G, la Q, la V y la X), el Instituto de Ingenieros Eléctricos y "
            "Electrónicos y sus grupos de trabajo, la Organización Internacional de Normalización "
            "y la "
            "Comisión Electrotécnica Internacional, la ANSI y la TIA, el ETSI y el resto de "
            "organismos "
            "de normalización de las telecomunicaciones, y el papel de cada uno."
        ),
        patrones=(
            r"organismo(s)? (de normalizacion|internacional|especializado)|"
            r"que organismo|cual de los siguientes organismos|"
            r"responsible for international|signaling and interface standards|"
            r"organizacion de las naciones unidas|encargad[oa] de regular las telecomunicaciones",
            r"estandar(es)? (de|para) (la )?(telecomunicacion|señalizacion|comunicacion)|"
            r"norma(s)? (de|para) (el cableado|las telecomunicaciones)",
            r"recomendacion(es)? (de la )?(uit|itu)|serie [gqxv] de la (uit|itu)|"
            r"que recomendacion",
            r"quien (regula|normaliza|aprueba|define) (los|las) (estandares|normas|"
            r"recomendaciones)",
            r"comision electrotenica internacional|"
            r"organizacion internacional para la estandarizacion",
            r"responsable de (los estandares|la normalizacion|la señalizacion)|"
            r"estandares? internacionales? de (señalizacion|interfaz)",
        ),
        patrones_debiles=(
            _UIT,
            _IEEE,
            _ISO_11801,
            r"estandar",
            r"organismo",
            r"norma",
            r"ieee",
            r"uit",
        ),
        prioridad=41,
    ),
    Materia(
        key="voz-y-video-sobre-ip",
        epigraph_code="IV.6.1",
        title="La voz y el vídeo sobre IP y la calidad de servicio",
        resumen=(
            "La telefonía y la videoconferencia por la red de datos: la voz sobre IP y sus "
            "protocolos "
            "(SIP, H.323 y su guardián o gatekeeper, RTP y MGCP), los códecs de voz y sus "
            "velocidades "
            "(G.711, G.722, G.726, G.729 y el resto de la serie G), la calidad de servicio (la "
            "latencia, "
            "el jitter, la pérdida de paquetes y el eco), las arquitecturas de VoIP y su "
            "señalización, "
            "y la traducción de direcciones para el establecimiento de la llamada."
        ),
        patrones=(
            r"voz sobre ip|\bvoip\b|telefonia ip|telefonia sobre ip|ip ?-? ?telephony",
            r"\bsip\b|h ?\.? ?323|gatekeeper|\brtp\b|\bmgcp\b|\bskinny\b|\bsccp\b",
            r"codec(s)?|codificacion de voz|g ?\.? ?7[0-9]{2}|g ?\.? ?726|g ?\.? ?729|"
            r"modulacion por impulsos codificados diferencial",
            r"calidad de servicio|\bqos\b|latencia|jitter|perdida de paquetes|eco",
            r"videoconferencia|videollamada|video sobre ip|multimedia",
            r"\bnat\b|travesia de nat|stun|\bturn\b|puerto publico asociado",
        ),
        patrones_debiles=(r"voz", r"video", r"qos"),
        prioridad=42,
    ),
    # --- IV.6.2 Medios de transmisión ------------------------------------------------------------
    Materia(
        key="cableado-de-cobre",
        epigraph_code="IV.6.2",
        title="El cableado de cobre: pares trenzados, categorías y apantallamiento",
        resumen=(
            "El medio guiado de cobre: el par trenzado y su trenzado, el cable no apantallado "
            "(UTP) y "
            "los apantallados (STP, FTP y S/FTP), las categorías y las clases del cableado (la 5e, "
            "la 6, "
            "la 6a, la 7, la 7a y la 8, y las clases D a I) con su frecuencia y su ancho de banda, "
            "el "
            "cable coaxial, los conectores, la diafonía y cómo se atenúa, el apantallamiento y la "
            "relación entre categoría, velocidad y distancia."
        ),
        patrones=(
            _ISO_11801,
            r"par(es)? trenzad|par trenzado|twisted pair",
            r"\butp\b|\bstp\b|\bftp\b|\bs ?/? ?ftp\b|apantallamiento|apantallad",
            r"categorias? ?(5|5e|6|6a|7|7a|8)|cat ?\.? ?(5|6|7|8)|clase [a-i] ?\b|"
            r"cableado de cobre|coaxial|\brj ?45\b|conector",
            r"diafonia|crosstalk|induccion|corrientes? en otros pares",
            r"(500|250|600|1000) ?mhz|frecuencia de (operacion|500)|"
            r"ancho de banda de(l)? cable",
            r"cable(s)? (de pares|trenzado|apantallado|de cobre)",
        ),
        patrones_debiles=(r"cable", r"cobre", r"pares"),
        prioridad=43,
    ),
    Materia(
        key="fibra-optica",
        epigraph_code="IV.6.2",
        title="La fibra óptica: monomodo, multimodo y sus ventanas",
        resumen=(
            "El medio guiado de vidrio: la fibra monomodo y la multimodo, sus tipos y sus clases "
            "(OM1, "
            "OM2, OM3, OM4 y OM5; OS1 y OS2), el núcleo y el revestimiento y su relación, las "
            "ventanas "
            "de longitud de onda y las longitudes apropiadas para cada fibra, la atenuación y la "
            "dispersión, los conectores y los transceptores, la fibra frente al cobre y las "
            "distancias "
            "que se alcanzan con cada medio."
        ),
        patrones=(
            r"fibra(s)? (optica|multimodo|monomodo)|\bom[1-5]\b|\bos[12]\b",
            r"monomodo|multimodo|nucleo.*revestimiento|revestimiento",
            r"longitud(es)? de onda|nanometro|nm\b|1550|1310|850",
            r"atenuacion|dispersion|dispers[ií]on cromatica",
            r"\bftth\b|fibra hasta el hogar|fibra hasta el (domicilio|edificio)|\bpon\b|"
            r"\bgpon\b|\bwdm\b",
            r"significa om|que significa om|\bom[1-5]\b|"
            r"conector(es)? (de fibra|optic)|\bsfp\b|\bgbic\b|transceptor|"
            r"\bfddi\b|10 ?gbps",
        ),
        patrones_debiles=(r"fibra", r"optica", r"optico"),
        prioridad=44,
    ),
    Materia(
        key="cableado-estructurado",
        epigraph_code="IV.6.2",
        title="El cableado estructurado y sus subsistemas",
        resumen=(
            "Cómo se organiza el cableado de un edificio: los elementos funcionales y los "
            "subsistemas "
            "del cableado estructurado (la acometida, el distribuidor de edificio y de planta, el "
            "cableado horizontal, el cableado vertical o troncal y el área de trabajo), de dónde "
            "parte "
            "el cableado horizontal, los armarios y los bastidores y la unidad de rack, los "
            "paneles de "
            "parcheo, las rosetas y los latiguillos, la certificación del enlace y del canal y las "
            "normas que lo regulan."
        ),
        patrones=(
            r"cableado estructurado|subsistema(s)? de cableado|"
            r"elementos? funcionales? (basicos)? de un sistema de cableado",
            r"cableado (horizontal|vertical|troncal|de (la )?acometida)|"
            r"distribuidor de (edificio|planta)|area de trabajo",
            r"armario(s)? (de comunicaciones|de cableado|rack)|bastidor|rack|"
            r"panel(es)? de parcheo|patch panel|roseta(s)?|latiguillo",
            r"certificacion (del|de) (enlace|canal)|categoria del enlace|"
            r"clase (d|e|f) ?\b",
            r"canalizacion|bandeja|suelo tecnico|registro(s)? de (cableado|comunicaciones)",
        ),
        patrones_debiles=(r"cableado", r"estructurado", r"rack"),
        prioridad=45,
    ),
    Materia(
        key="medios-inalambricos-y-satelite",
        epigraph_code="IV.6.2",
        title="Los medios no guiados: radioenlaces, satélite y PLC",
        resumen=(
            "La transmisión sin cables y por la red eléctrica: los radioenlaces punto a punto y "
            "multipunto, las microondas y las frecuencias que usan, los sistemas de transmisión "
            "por "
            "satélite y sus órbitas (geoestacionaria, media y baja), el retardo y la cobertura de "
            "cada "
            "una, el infrarrojo y la luz visible, la tecnología PLC y BPL sobre la red eléctrica y "
            "sus "
            "estándares, y las líneas de transmisión y sus equipos terminales."
        ),
        patrones=(
            r"radioenlace(s)?|microondas|enlace(s)? (por )?radio|"
            r"comunicacion(es)? (por|via) (radio|satelite)",
            r"satelite(s)?|orbita (geoestacionaria|baja|media)|\bgeo\b|\bleo\b|\bmeo\b|"
            r"estacion terrena|transpondedor",
            r"\bplc\b|\bbpl\b|power line|red electrica.*(datos|comunicacion)|"
            r"broadband over power line",
            r"infrarroj|ondas? de luz|linea de (vision|vista)|no estan en linea directa de vision",
            r"linea(s)? de transmision|equipo terminal de (linea|datos)|\bdte\b|\bdce\b",
        ),
        patrones_debiles=(r"satelite", r"radio", r"inalambrico"),
        prioridad=46,
    ),
    # --- IV.6.3 Modos de comunicación ------------------------------------------------------------
    Materia(
        key="modos-de-comunicacion",
        epigraph_code="IV.6.3",
        title="Los modos de comunicación y de transmisión",
        resumen=(
            "Cómo hablan los dos extremos: la transmisión simplex, semidúplex y dúplex, la "
            "transmisión "
            "en serie y en paralelo y sus ventajas, la transmisión síncrona y la asíncrona, la "
            "transmisión en banda base y en banda ancha, la transmisión analógica y la digital, la "
            "difusión y la comunicación punto a punto y multipunto, y los sentidos de la "
            "transmisión."
        ),
        patrones=(
            r"simplex|semi ?-? ?duplex|half ?-? ?duplex|full ?-? ?duplex|"
            r"\bduplex\b|unidireccional|bidireccional",
            r"transmision (en )?(serie|paralelo)|serie frente a paralelo|"
            r"comunicacion (serie|paralela)",
            r"(transmision )?(sincrona|asincrona)|sincronia|caracteres? de (inicio|fin)|"
            r"start ?/? ?stop",
            r"banda base|banda ancha|broadband",
            r"punto a punto|multipunto|difusion|broadcast|unidifusion|multidifusion",
            r"modos? de (comunicacion|transmision)|sentido de la (transmision|comunicacion)",
        ),
        patrones_debiles=(r"simplex", r"duplex", r"serie", r"modo"),
        prioridad=47,
    ),
    Materia(
        key="multiplexacion",
        epigraph_code="IV.6.3",
        title="La multiplexación y la compartición del medio",
        resumen=(
            "Cómo se comparte un medio entre varias comunicaciones: la multiplexación por división "
            "de "
            "frecuencia, por división de tiempo (síncrona y estadística), por división de código y "
            "por "
            "división de longitud de onda, la multiplexación inversa, el acceso múltiple al medio "
            "y las "
            "técnicas de acceso (CSMA, CSMA/CD, CSMA/CA, TDMA, FDMA y CDMA), y su relación con la "
            "conmutación de paquetes."
        ),
        patrones=(
            r"multiplexacion|multiplex(ar|or|acion)|multiplexad",
            r"division de (frecuencia|tiempo|codigo|longitud de onda)|"
            r"\bfdm\b|\btdm\b|\bcdm[ae]?\b|\bwdm\b|\bdwdm\b",
            r"acceso (multiple )?al medio|\bcsma\b|\btdma\b|\bfdma\b|\bcdma\b|"
            r"deteccion de (portadora|colisiones)",
            r"comparticion del medio|canal compartido|ancho de banda compartido",
            r"multiplexacion (estadistica|inversa|por division)",
        ),
        patrones_debiles=(r"multiplexacion", r"division", r"canal"),
        prioridad=48,
    ),
    Materia(
        key="conmutacion",
        epigraph_code="IV.6.3",
        title="La conmutación de circuitos, de mensajes y de paquetes",
        resumen=(
            "Cómo se encamina lo que se transmite: la conmutación de circuitos y sus tres fases "
            "(establecimiento, transferencia y liberación), la conmutación de mensajes, la "
            "conmutación "
            "de paquetes y sus dos modos (el datagrama y el circuito virtual), las ventajas e "
            "inconvenientes de cada una, el retardo y la congestión, la teoría de colas y las "
            "disciplinas de servicio, y la conmutación de etiquetas."
        ),
        patrones=(
            r"conmutacion de (circuitos|mensajes|paquetes|etiquetas)|"
            r"conmutacion (de|por) (circuitos|paquetes)",
            r"circuito(s)? virtual(es)?|datagrama(s)?|"
            r"establecimiento, (la )?transferencia y (la )?liberacion",
            r"congestion|saturacion|teoria de colas|disciplina de cola|\brss\b|"
            r"politica de (encolamiento|descarte)",
            r"conmutad[oa]r|conmutacion (de nivel|por division)",
            r"red(es)? de (conmutacion|difusion)",
        ),
        patrones_debiles=(r"conmutacion", r"paquete", r"circuito"),
        prioridad=49,
    ),
    # --- IV.6.4 Equipos terminales y de interconexión ---------------------------------------------
    Materia(
        key="equipos-de-interconexion",
        epigraph_code="IV.6.4",
        title="Los equipos terminales y los de interconexión y conmutación",
        resumen=(
            "Los aparatos que hay en los extremos y en medio: el equipo terminal de datos y el de "
            "circuito de datos, el módem, la tarjeta de red, el repetidor, el concentrador o hub, "
            "el "
            "conmutador o switch y sus dominios, el puente, el encaminador o router, el "
            "cortafuegos, la "
            "pasarela, el punto de acceso y el balanceador de carga, y los protocolos de "
            "redundancia y "
            "de encaminamiento que se configuran en ellos."
        ),
        patrones=(
            r"equipo(s)? (terminal|de interconexion|de conmutacion)|\bdte\b|\bdce\b",
            r"modem|tarjeta de red|\bnic\b|repetidor|concentrador|\bhub\b|"
            r"conmutador|\bswitch(es)?\b|puente|\bbridge\b",
            r"encaminador|router(s)?|pasarela|gateway|punto de acceso|\bap\b|"
            r"balanceo de carga|balanceador",
            r"protocolo(s)? de (redundancia|encaminamiento)|"
            r"\bhsrp\b|\bvrp\b|\bvrrp\b|\bcarp\b|protocolo propietario de cisco|"
            r"\bospf\b|\bbgp\b|\beigrp\b|\brip\b|estado de enlace",
            r"dominio de (colision|difusion)|segmentacion de la red",
        ),
        patrones_debiles=(r"equipo", r"router", r"conmutador"),
        prioridad=50,
    ),
    # --- IV.6.5 Redes de comunicaciones ----------------------------------------------------------
    Materia(
        key="tecnologias-de-acceso",
        epigraph_code="IV.6.5",
        title="Las tecnologías de acceso y las redes de comunicaciones",
        resumen=(
            "Cómo se llega desde el domicilio a la red del operador: la familia xDSL (ADSL y "
            "ADSL2+, "
            "HDSL, SDSL y VDSL y VDSL2) con sus velocidades y sus estándares, el microfiltro y el "
            "repartidor, el DSLAM y la red de agregación, la fibra hasta el hogar y el cable "
            "módem, el "
            "acceso por radio, las redes de acceso fijas y móviles, el protocolo MPLS y sus "
            "elementos, "
            "y la clasificación de las redes por su extensión."
        ),
        patrones=(
            r"\badsl\b|adsl2|adsl2\+|xdsl|\bdsl\b|\bhdsl\b|\bsdsl\b|\bvdsl\b|"
            r"linea de abonado digital",
            r"microfiltro|filtro (adsl|de linea)|repartidor|\bdslam\b|"
            r"multiplexor de acceso",
            r"red de (acceso|agregacion|transporte)|tecnologia(s)? de acceso|"
            r"acceso (cablead[oa]|fijo|movil|por radio)",
            r"\bmpls\b|multiprotocol label switching|\bldp\b|\bler\b|\blsr\b|"
            r"conmutacion de etiquetas multiprotocolo|tunel mpls",
            r"\bethernet\b|10 ?base ?-? ?[0-9]+|"
            r"\bftth\b|cable ?-? ?modem|\bhfc\b|fibra hasta el hogar|"
            r"red(es)? (de area local|metropolitana|de area extensa)|\blan\b|\bman\b|\bwan\b",
        ),
        patrones_debiles=(r"acceso", r"adsl", r"red"),
        prioridad=51,
    ),
    # --- IV.6.6 Redes de conmutación y de difusión -----------------------------------------------
    Materia(
        key="redes-de-area-extensa",
        epigraph_code="IV.6.6",
        title="Las redes de área extensa: Frame Relay, ATM y RDSI",
        resumen=(
            "Las tecnologías de red pública de datos: Frame Relay (los campos de su trama, los "
            "bits de "
            "congestión FECN, BECN y DECN, y los parámetros CIR, Bc, Be y EIR), el modo de "
            "transferencia "
            "asíncrona o ATM (la célula y su tamaño, las clases de servicio CBR, VBR, ABR y UBR, "
            "los "
            "circuitos virtuales permanentes y conmutados y el modelo de referencia), la Red "
            "Digital de "
            "Servicios Integrados (el acceso básico y el primario, los canales B, D y H y sus "
            "velocidades), la red pública de datos X.25 y el primer protocolo estándar de red "
            "pública, "
            "y la interconexión de equipos terminales con la red."
        ),
        patrones=(
            r"frame relay|\bfr\b|fecn|becn|decn|\bcir\b|\bbc\b|\bbe\b|\beir\b|"
            r"commited (information|burst)",
            r"\batm\b|modo de transferencia asincrona|celdas?|\bcbr\b|\bvbr\b|\babr\b|"
            r"\bubr\b|atm forum|circuito virtual (permanente|conmutado)|\bpvc\b|\bsvc\b",
            r"\brdsi\b|red digital de servicios integrados|acceso (basico|primario)|"
            r"canal(es)? (b|d|h) ?(11|12|0)?\b|interfaz usuario ?-? ?red",
            r"\bx ?\.? ?25\b|red(es)? publica(s)? de datos|\bpspdn\b|"
            r"primer protocolo estandar de la red de datos",
            r"red(es)? de area extensa|\bwan\b|linea dedicada|conexion punto a punto",
        ),
        patrones_debiles=(r"frame relay", r"atm", r"rdsi", r"extensa"),
        prioridad=52,
    ),
    # --- IV.6.7 Comunicaciones móviles e inalámbricas --------------------------------------------
    Materia(
        key="telefonia-movil",
        epigraph_code="IV.6.7",
        title="La telefonía móvil: de GSM al 5G",
        resumen=(
            "Las generaciones de la telefonía móvil y lo que trajo cada una: la primera generación "
            "analógica y el comienzo de la digital, GSM y sus bases de datos y su señalización, "
            "GPRS, "
            "UMTS y su acceso W-CDMA, LTE y su red de acceso con OFDMA, el 4G y su banda ancha "
            "móvil, el "
            "5G y la segmentación de red, las bandas de frecuencia y el dividendo digital, la "
            "conmutación entre celdas y el itinerario, y los servicios móviles de banda ancha."
        ),
        patrones=(
            r"telefonia movil|comunicaciones? moviles?|red(es)? moviles?|"
            r"generacion(es)? (de|del) (telefonia|movil|tecnologia)|"
            r"\b[1-5]g\b|\bgsm\b|\bgprs\b|\bumts\b|\blte\b|\bhsdpa\b|\bedge\b",
            r"\bw ?-? ?cdma\b|\bofdma\b|\bsc ?-? ?fdma\b|\bnetwork slicing\b|"
            r"segmentacion de red",
            r"dividendo digital|banda(s)? de frecuencia.*(4g|5g|movil)|"
            r"banda de (700|800|900|1800|2100|2600|3500) ?mhz",
            r"handover|traspaso entre celdas|itinerancia|roaming|"
            r"estacion base|\bbts\b|\bhlr\b|\bvlr\b",
            r"telefono movil|dispositivo movil|red de acceso.*(lte|movil)|"
            r"banda ancha movil|\bmbwa\b",
        ),
        patrones_debiles=(r"movil", r"telefonia", r"generacion"),
        prioridad=53,
    ),
    Materia(
        key="redes-inalambricas",
        epigraph_code="IV.6.7",
        title="Las redes inalámbricas: WiFi, Bluetooth y NFC",
        resumen=(
            "Las redes locales sin cables: el estándar IEEE 802.11 y sus versiones y enmiendas, "
            "con los "
            "nombres comerciales de cada una y las bandas de 2,4, 5 y 6 GHz, las topologías "
            "inalámbricas "
            "(la red básica, la extendida y la red ad hoc o independiente), el punto de acceso y "
            "el "
            "conjunto de servicios, la seguridad de la red inalámbrica (WEP, WPA, WPA2, WPA3, WPS, "
            "el "
            "SSID y la clave precompartida) y sus vulnerabilidades, el Bluetooth y sus versiones, "
            "el NFC "
            "y su frecuencia, y las redes de sensores."
        ),
        patrones=(
            _IEEE,
            r"\bwifi\b|wi ?-? ?fi|\bwlan\b|red(es)? (local )?inalambrica(s)?|"
            r"redes? de area local inalambrica",
            r"wi ?-? ?fi ?(4|5|6|6e|7)|802 ?11 ?(a|b|g|n|ac|ax|be)",
            r"\bssid\b|\bpsk\b|\bwep\b|\bwpa ?2?\b|\bwpa3\b|wifi protected setup|\bwps\b|"
            r"band steering|red(es)? (oculta|abierta)",
            r"bluetooth|\bble\b|nfc|near field|zigbee|z ?-? ?wave|"
            r"\brfid\b|antenas?|punto de acceso inalambrico",
            r"topologia(s)? (de red )?inalambrica|red (ad hoc|independiente|de infraestructura)|"
            r"\bbss\b|\bess\b|\bibss\b",
            r"\bwimax\b|wirelessman|sin (necesidad de )?emparejamiento|"
            r"comunicacion(es)? sin contacto|"
            r"6 ?ghz|2 ?[,.]?4 ?ghz|5 ?ghz|banda(s)? (de|del) (wifi|inalambrica)",
        ),
        patrones_debiles=(r"wifi", r"inalambrica", r"bluetooth", r"802"),
        prioridad=54,
    ),
    Materia(
        key="radiocomunicaciones-profesionales",
        epigraph_code="IV.6.7",
        title="Las radiocomunicaciones profesionales: TETRA, DECT y la movilidad IP",
        resumen=(
            "Los sistemas de radio para servicios y colectivos: el TETRA y sus características (el "
            "modo "
            "directo DMO y su utilidad para las emergencias, el acceso al medio, la asignación de "
            "canales y su normativa), el DECT y su cifrado, los sistemas privados de telefonía "
            "móvil "
            "para un colectivo limitado, los servicios de emergencia y su coordinación, y la "
            "movilidad "
            "en IP con sus agentes."
        ),
        patrones=(
            r"\btetra\b|terrestrial trunked radio|radio(comunicacion)?(es)? profesionales?|"
            r"red privada de telefonia movil",
            r"\bdect\b|dect standard cipher|\bdsc\b|telefono inalambrico domestico",
            r"modo (dmo|directo)|\bdmo\b|servicios? de emergencia|"
            r"colectivo limitado",
            r"movilidad ip|agente (base|local|extranjero)|home agent|foreign agent|"
            r"mobile ip",
            r"radio(comunicacion)? (troncal|movil profesional)|\bpmr\b|"
            r"\bp25\b|\bapco\b",
        ),
        patrones_debiles=(r"tetra", r"dect", r"emergencia"),
        prioridad=55,
    ),
)

#: El orden en que se **enseña** el índice: primero los conceptos y los organismos (qué se
# transmite, con
#: qué norma y con qué calidad), después los medios (el cobre, la fibra, el cableado y el aire),
# después
#: los modos y la conmutación, después los equipos, después las redes de acceso y las de área
# extensa, y
#: por último las móviles y las inalámbricas, que es el orden del título del tema.
ORDEN: tuple[str, ...] = (
    "conceptos-de-transmision",
    "organismos-y-estandares",
    "voz-y-video-sobre-ip",
    "cableado-de-cobre",
    "fibra-optica",
    "cableado-estructurado",
    "medios-inalambricos-y-satelite",
    "modos-de-comunicacion",
    "multiplexacion",
    "conmutacion",
    "equipos-de-interconexion",
    "tecnologias-de-acceso",
    "redes-de-area-extensa",
    "telefonia-movil",
    "redes-inalambricas",
    "radiocomunicaciones-profesionales",
)

__all__ = ["MATERIAS", "ORDEN"]
