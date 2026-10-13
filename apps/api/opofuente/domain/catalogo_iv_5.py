"""El catálogo de materias de IV.5 (seguridad de los sistemas de información).

IV.5 es un tema **técnico**, así que su índice va por **asunto** dentro de sus nueve epígrafes
oficiales, como en IV.7, IV.2 y II.4. Sus epígrafes son los conceptos de seguridad, la seguridad
física, la seguridad lógica, las amenazas y vulnerabilidades, las técnicas criptográficas y los
protocolos seguros, los mecanismos de firma digital, la infraestructura física del CPD, los sistemas
de gestión de incidencias y el control remoto de puestos; este catálogo los abre en quince apartados
porque las preguntas del tema se agrupan así de verdad:

- los conceptos, en cinco: las **dimensiones y los servicios** de seguridad (confidencialidad,
  integridad, disponibilidad, autenticación, no repudio y trazabilidad), las **normas y
  metodologías**
  (la familia ISO/IEC 27000, MAGERIT, el ENS y las guías CCN-STIC), el **análisis y la gestión de
  riesgos** (activos, amenazas, vulnerabilidades, impacto, riesgo, salvaguardas, planes de
  contingencia y continuidad), el **gobierno de la seguridad** (la política y el plan de seguridad,
  el comité y los responsables) y el **Esquema Nacional de Seguridad** (categorización, medidas,
  auditoría y conformidad);
- la seguridad física, en uno: el control de acceso físico, la protección del entorno y los sistemas
  de detección y extinción;
- la seguridad lógica, en uno: la autenticación y el control de acceso lógico, los cortafuegos, los
  sistemas de detección y prevención de intrusiones, el antimalware, el cifrado del puesto y el
  control de la red;
- las amenazas, en uno: el **software malicioso** y los **ataques** (denegación de servicio,
  interceptación, suplantación, ingeniería social, APT) y la **vulnerabilidad** como defecto que los
  habilita;
- la criptografía, en cuatro: la **criptografía** (simétrica y asimétrica, algoritmos, modos y
  gestión de claves), el **resumen y la integridad** (las funciones hash), la **firma digital y los
  certificados** (la infraestructura de clave pública, el certificado X.509 y su revocación, el
  sellado de tiempo) y los **protocolos seguros** (IPsec, TLS, SSH, Kerberos, el correo seguro y los
  protocolos de autenticación);
- la infraestructura del CPD, en uno: el acondicionamiento y el equipamiento (los niveles TIER y la
  norma ANSI/TIA-942, la disponibilidad, la climatización, la alimentación y el Green CPD);
- la gestión de incidencias, en uno: el servicio de atención, los acuerdos de nivel de servicio, la
  gestión de incidencias y problemas, los indicadores y los equipos de respuesta;
- el control remoto, en uno: el escritorio remoto y sus protocolos.

Tres decisiones de redacción de los patrones, dichas donde se leen:

- las **herramientas del CCN-CERT** —que el banco pregunta por decenas, casi siempre con la misma
  fórmula «¿qué herramienta…?»— van a un apartado propio y **no** al de las normas: lo que se
  aprende ahí es qué hace cada herramienta, y mezclarlo con el ENS obligaría a estudiar un catálogo
  dentro de un esquema;
- los **nombres de los ataques y del software malicioso** van con su nombre en inglés y en español
  cuando el material usa los dos (`ransomware` y «secuestro de datos», `phishing` y «suplantación»),
  porque el enunciado de una pregunta usa uno y el de la siguiente, el otro;
- las siglas van con `\\b` (`\\bens\\b`, `\\brsa\\b`, `\\bsha\\b`, `\\brdp\\b`, `\\bitil\\b`): sin
la
  frontera, `des` casa dentro de `desarrollo` y `ens` dentro de `enseñanza`, que es exactamente lo
  que llenaba de falsos positivos el reparto del primer piloto.

Las preguntas que no se sitúan ni por su enunciado ni por el texto de sus hechos **no** acaban en un
cajón: van a la bandeja del propietario con su motivo (`Motivo.SIN_MATERIA_EN_EL_INDICE`). Por eso
este catálogo, como el de IV.7 y el de II.4, **no tiene cajones**.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Las normas y metodologías del tema, como las deja el texto normalizado.
_ISO_27000 = r"\biso\b.{0,20}2700[0-9]|2700[0-9]|iso iec 2700[0-9]"
_MAGERIT = r"magerit"
_ENS = r"\bens\b|esquema nacional de seguridad"
_CCN = r"\bccn\b|ccn ?-? ?cert|ccn ?-? ?stic|\bstic\b"

MATERIAS: tuple[Materia, ...] = (
    # --- IV.5.1 Conceptos de seguridad de los sistemas de información ----------------------------
    Materia(
        key="conceptos-y-dimensiones",
        epigraph_code="IV.5.1",
        title="Las dimensiones y los servicios de la seguridad de la información",
        resumen=(
            "Qué se protege y con qué propiedades: los atributos esenciales de la seguridad de la "
            "información (confidencialidad, integridad y disponibilidad, con la autenticidad, el "
            "no "
            "repudio y la trazabilidad), las dimensiones de seguridad de los datos y los servicios "
            "(la integridad de los datos, la integridad del servicio, la disponibilidad, la "
            "confidencialidad y la autenticidad), los servicios de seguridad (autenticación, "
            "control "
            "de acceso, confidencialidad, integridad, no repudio y disponibilidad), los protocolos "
            "y "
            "procesos de autenticación, autorización y contabilidad (AAA) y la seguridad de la "
            "información como disciplina."
        ),
        patrones=(
            r"dimensiones? de seguridad|dimensione?s de la seguridad",
            r"(confidencialidad|integridad|disponibilidad|autenticidad|no repudio|trazabilidad)",
            r"atributos? (esenciales|de la seguridad)",
            r"servicios? de seguridad( de la informacion)?",
            r"protocolos? aaa|autenticacion, autorizacion y contabilidad",
            r"seguridad de (la informacion|los sistemas de informacion)|seguridad informatica",
            r"principio(s)? de seguridad|qu[eé] principio de seguridad",
            r"elementos? de la seguridad|proceso de la administracion de la seguridad",
            r"seguridad (activa|pasiva)|prevencion, deteccion y recuperacion",
            r"garantizar (la|las) (confidencialidad|integridad|disponibilidad)",
        ),
        patrones_debiles=(r"seguridad", r"informacion", r"proteccion"),
        prioridad=60,
    ),
    Materia(
        key="normas-y-metodologias",
        epigraph_code="IV.5.1",
        title="Las normas y metodologías de seguridad (ISO, MAGERIT, ENS y CCN-STIC)",
        resumen=(
            "El marco de referencia: la familia de normas ISO/IEC 27000 (el sistema de gestión de "
            "la "
            "seguridad de la información, el código de práctica, la gestión de riesgos y la "
            "certificación), la norma ISO 31000 de gestión de riesgos, la metodología MAGERIT y "
            "sus "
            "libros, el Esquema Nacional de Seguridad y sus guías CCN-STIC, las normas de "
            "continuidad "
            "del negocio, la arquitectura de seguridad y los estándares internacionales de "
            "seguridad "
            "aplicables a los sistemas de información."
        ),
        patrones=(
            _ISO_27000,
            _MAGERIT,
            r"\biso\b ?/? ?iec\b|organizacion internacional para la estandarizacion|"
            r"\biec\b|comision electrotenica",
            r"\biso\b ?/? ?31000|gestion de riesgos iso|norma internacional para la gestion de "
            r"riesgos",
            r"arquitectura de seguridad 081|arquitectura 081",
            r"normas? de (seguridad|continuidad|referencia)|estandares? de seguridad",
            r"(certificacion|acreditacion).{0,30}(iso|27001)|iso 27001.*certific",
            r"familia de normas|codigo de practica|sgs?i|sistemas? de gestion de la seguridad",
        ),
        patrones_debiles=(r"norma", r"estandar", r"iso", r"metodologia"),
        prioridad=40,
    ),
    Materia(
        key="analisis-y-gestion-de-riesgos",
        epigraph_code="IV.5.1",
        title="El análisis y la gestión de riesgos y los planes de contingencia",
        resumen=(
            "Cómo se decide qué proteger y cuánto: el análisis de riesgos y su metodología MAGERIT "
            "(los activos, las amenazas, las vulnerabilidades, el impacto, el riesgo, la "
            "probabilidad "
            "y la estimación), los tipos de impacto y de riesgo, las salvaguardas como medida que "
            "reduce el riesgo, la gestión y el tratamiento del riesgo (evitar, reducir, compartir "
            "y "
            "asumir), el plan de seguridad y su ejecución, el plan de contingencia y de "
            "continuidad, "
            "y la auditoría de la seguridad."
        ),
        patrones=(
            _MAGERIT,
            r"analisis de riesgos|gestion de riesgos|gestion del riesgo|gesti[oó]n de los riesgos",
            r"\briesgos?\b|nivel de riesgo|matriz de riesgo|apetito de riesgo",
            r"activos? (esenciales|de (la )?informacion)|\bactivos?\b",
            r"amenaza(s)?( a la seguridad)?|vulnerabilidad(es)?",
            r"impacto|probabilidad|estimacion del (riesgo|grado)",
            r"salvaguardas?|medida(s)? de (mitigacion|proteccion)|mitigar el riesgo",
            r"plan de (seguridad|contingencia|continuidad)|plan de recuperacion|"
            r"recuperacion ante desastres|\bdrp\b|\bbcp\b",
            r"analisis de impacto|continuidad del negocio",
            r"auditoria(s)? de (seguridad|los sistemas|cumplimiento)|sera auditada",
            r"metodologia(s)? (de analisis|de gestion)|tecnicas? (de analisis|magerit)",
        ),
        patrones_debiles=(r"riesgo", r"amenaza", r"auditoria", r"contingencia"),
        prioridad=41,
    ),
    Materia(
        key="gobierno-de-la-seguridad",
        epigraph_code="IV.5.1",
        title="El gobierno de la seguridad: política, comité y responsables",
        resumen=(
            "Quién decide y quién responde de la seguridad: la política de seguridad y su "
            "contenido, "
            "el plan de seguridad y su elaboración, el comité de seguridad y sus funciones, los "
            "responsables y sus papeles (el responsable de la seguridad, el responsable del "
            "sistema, "
            "el responsable de la información y el responsable del servicio), la estructura de la "
            "función de seguridad, la formación y la concienciación de los usuarios, y el régimen "
            "de "
            "obligaciones y responsabilidades como parte del Esquema Nacional de Seguridad."
        ),
        patrones=(
            r"politica de seguridad",
            r"comite de seguridad|secretario del comite",
            r"responsable(s)? de(l)? (la )?(seguridad|sistema|informacion|servicio)|"
            r"responsables? de seguridad",
            r"funciones del responsable|responsable del sistema tiene",
            r"organizacion de la seguridad|estructura de la seguridad|"
            r"funcion de (la )?seguridad",
            r"formacion (de los usuarios|y concienciacion)|concienciacion|sensibilizacion",
            r"regimen de obligaciones|responsabilidades de los usuarios",
            r"plan director de seguridad|estrategia de seguridad",
            r"administrador(es)? del sistema|funciones del administrador",
        ),
        patrones_debiles=(r"politica", r"comite", r"responsable"),
        prioridad=42,
    ),
    Materia(
        key="ens-y-conformidad",
        epigraph_code="IV.5.1",
        title="El Esquema Nacional de Seguridad: categorización, medidas y auditoría",
        resumen=(
            "El cumplimiento del Esquema Nacional de Seguridad: la categorización de los sistemas "
            "(las "
            "categorías básica, media y alta y las dimensiones de seguridad), las medidas de "
            "seguridad "
            "de sus anexos y su selección, la declaración de conformidad y las responsabilidades, "
            "la "
            "auditoría de conformidad y su periodicidad, el informe de estado de seguridad y el "
            "seguimiento de las medidas, y las guías y publicaciones del CCN-CERT y del CCN-STIC "
            "que "
            "lo desarrollan."
        ),
        patrones=(
            _ENS,
            _CCN,
            r"categorizacion de(l)? (los )?sistemas?|categoria (de seguridad )?(basica|media|alta)|"
            r"sistema de categoria (basica|media|alta)",
            r"conformidad (con el ens|del ens)|declaracion de conformidad|"
            r"informe de estado de seguridad",
            r"medidas? de seguridad (del anexo|del ens)|anexo(s)? (i|ii|iii)? ?del ens",
            r"auditoria de cumplimiento|conformidad ens|ens/stic",
            r"guia(s)? (ccn|stic|de seguridad)|publicaciones del ccn",
            r"ambito de aplicacion del ens|entidades del ambito",
        ),
        patrones_debiles=(r"conformidad", r"categorizacion"),
        prioridad=43,
    ),
    # --- IV.5.2 Seguridad física -----------------------------------------------------------------
    Materia(
        key="seguridad-fisica",
        epigraph_code="IV.5.2",
        title="La seguridad física",
        resumen=(
            "La protección del entorno donde viven los sistemas: el control de acceso físico y sus "
            "métodos (tarjetas, biometría, vigilancia y guardias), la protección contra el fuego y "
            "la "
            "detección y extinción, la protección contra el agua y las inundaciones, la protección "
            "contra las perturbaciones eléctricas y el ruido, el control de la temperatura y la "
            "humedad, y la seguridad del personal y de las instalaciones."
        ),
        patrones=(
            r"seguridad fisica",
            r"control de acceso (fisico|al (cpd|centro))|acceso fisico|biometric",
            r"(sistema|sistemas) de (deteccion|extincion) (de incendios|de fuego)|"
            r"extintores?|deteccion de incendios|rociadores|halon",
            r"proteccion contra (el fuego|el agua|las inundaciones|el ruido)|"
            r"inundacion|humedad|temperatura",
            r"vigilancia|guardias? de seguridad|circuito cerrado de television|\bcctv\b",
            r"perturbacion(es)? electrica|puesta a tierra|apantallamiento",
            r"seguridad (del personal|de las personas)|acceso de personas",
        ),
        patrones_debiles=(r"fisica", r"incendio", r"acceso"),
        prioridad=44,
    ),
    # --- IV.5.3 Seguridad lógica -----------------------------------------------------------------
    Materia(
        key="seguridad-logica",
        epigraph_code="IV.5.3",
        title="La seguridad lógica: autenticación, cortafuegos y detección",
        resumen=(
            "La protección del sistema por dentro: la identificación y la autenticación "
            "(contraseñas y "
            "su gestión, el doble factor y los factores de autenticación, la autenticación mutua y "
            "el "
            "inicio de sesión único), la autorización y el control de acceso lógico, los "
            "cortafuegos y "
            "las reglas de filtrado, los sistemas de detección y prevención de intrusiones (IDS, "
            "IPS y "
            "HIDS), el antimalware y su actualización, el cifrado del disco y de los soportes, el "
            "control de acceso a la red y de los dispositivos, la prevención de fugas de "
            "información y "
            "el registro de la actividad."
        ),
        patrones=(
            r"seguridad logica",
            r"autenticacion (de usuarios|multifactor|multi ?-? ?factor)|\bmfa\b|doble factor|"
            r"dos factores",
            r"contrasen(a|as)|clave(s)? de (acceso|usuario)|politica de contrasenas|"
            r"caducidad de (la|las) contrasena",
            r"inicio de sesion unico|single sign ?-? ?on|\bsso\b",
            r"cortafuegos|firewall|iptables|reglas de filtrado|proxy",
            r"deteccion de intrusiones|\bids\b|\bips\b|\bhids\b|\bnids\b|prevencion de intrusiones",
            r"antivirus|antimalware|proteccion (del|contra el) malware",
            r"control de acceso (logico|a la red)|\bnac\b|byod|segmentacion de la red",
            r"prevencion de (fugas|perdida) de (informacion|datos)|\bdlp\b",
            r"cifrado (del|de) (disco|los soportes)|bitlocker|cifrado de la informacion",
            r"registro(s)? (de actividad|de auditoria|de accesos)|\blog\b",
            r"mecanismos? para proteger (un|el) sistema",
        ),
        patrones_debiles=(r"autenticacion", r"cortafuegos", r"contrasena", r"acceso"),
        prioridad=45,
    ),
    # --- IV.5.4 Amenazas y vulnerabilidades ------------------------------------------------------
    Materia(
        key="amenazas-y-vulnerabilidades",
        epigraph_code="IV.5.4",
        title="Las amenazas, los ataques y las vulnerabilidades",
        resumen=(
            "Qué puede salir mal y cómo lo intentan: el software malicioso y sus familias (virus, "
            "gusanos, troyanos, rootkits, spyware, adware, ransomware y keyloggers), los ataques "
            "(denegación de servicio y su versión distribuida, la interceptación y el "
            "intermediario, "
            "la suplantación y el enmascaramiento, la fuerza bruta y el barrido de claves, la "
            "inyección, el desbordamiento de búfer, el ping de la muerte, el ataque smurf y las "
            "botnets), la ingeniería social y el fraude (phishing, spear phishing, vishing y "
            "pretexting), las amenazas persistentes avanzadas, y la vulnerabilidad y el error "
            "humano "
            "como lo que las habilita."
        ),
        patrones=(
            r"amenazas? y vulnerabilidades|amenazas? a la seguridad",
            r"software malicioso|codigo malicioso|malware|virus|gusano|troyano|rootkit|spyware|"
            r"adware|keylogger",
            r"software espia|grayware|greyware|accion delictiva|fines lucrativos",
            r"ransomware|secuestro de datos|criptovirus|piden un dinero|desencriptar|"
            r"se han encriptado",
            r"inyeccion (de )?sql|sql injection|\bexploit\b|desbordamiento de (bufer|buffer)",
            r"servidor de comando y control|comando y control|\bc ?y ?c\b",
            r"denegacion de servicio|\bdos\b|\bddos\b|saturar un sistema|"
            r"multitud de sistemas atacan",
            r"ataque(s)? (de|por|smurf|informatico|dirigido)|\bsmurf\b|ping de la muerte|"
            r"barrido (del espacio )?de claves|fuerza bruta",
            r"intermediario|man in the middle|\bmitm\b|interceptar mensajes",
            r"suplantacion de (identidad|identidad digital)|enmascaramiento|spoofing",
            r"ingenieria social|phishing|spear ?-? ?phishing|vishing|pretexting|"
            r"correos? falsos|mensajes? falsos",
            r"amenaza(s)? persistente(s)? avanzada(s)|\bapt\b|botnet|red (zombi|de bots)|"
            r"dispositivos infectados",
            r"honeypot|trampa|sistemas deliberadamente vulnerables",
            r"vulnerabilidad(es)?|defecto o debilidad|error(es)? humano|malas practicas",
        ),
        patrones_debiles=(r"ataque", r"malicioso", r"vulnerabilidad"),
        prioridad=46,
    ),
    # --- IV.5.5 Técnicas criptográficas y protocolos seguros --------------------------------------
    Materia(
        key="criptografia",
        epigraph_code="IV.5.5",
        title="La criptografía: algoritmos de clave simétrica y asimétrica",
        resumen=(
            "Cómo se cifra: la criptografía de clave simétrica y sus algoritmos (DES y sus modos "
            "de "
            "operación, triple DES, IDEA, RC y AES o Rijndael), la criptografía de clave pública o "
            "asimétrica y sus algoritmos (RSA, Diffie-Hellman, DSA y ElGamal), el uso de cada "
            "clave "
            "para cifrar y para descifrar, las ventajas y los inconvenientes de cada familia, la "
            "longitud de las claves y su gestión, el criptoanálisis y los ataques a los "
            "criptosistemas."
        ),
        patrones=(
            r"criptografia|criptografico|criptosistema",
            r"cifrado (simetrico|asimetrico)|clave(s)? (simetrica|asimetrica|publica|privada)|"
            r"criptografia (de clave publica|asimetrica|simetrica)",
            r"\bdes\b|triple des|3des|\baes\b|rijndael|\bidea\b|\brc[245]\b|\bblowfish\b",
            r"\brsa\b|diffie ?-? ?hellman|\bdsa\b|elgamal|curva eliptica|\becdsa\b|"
            r"kerckhoff",
            r"algoritmo(s)? de (cifrado|encriptacion|clave)|metodo(s)? de cifrado|"
            r"cifrado en bloque|modos? de (operacion|funcionamiento)",
            r"clave privada rsa|crear una clave|gestion de claves|intercambio de claves",
            r"criptoanalisis|romper el cifrado|espacio de claves",
            r"eficiencia de los metodos criptograficos|metodo mas eficiente para securizar",
        ),
        patrones_debiles=(r"cifrado", r"clave", r"criptografia", r"algoritmo"),
        prioridad=47,
    ),
    Materia(
        key="resumen-y-hash",
        epigraph_code="IV.5.5",
        title="Las funciones hash y el resumen de un mensaje",
        resumen=(
            "La huella del mensaje: qué es una función hash o de resumen y sus propiedades "
            "(unidireccional, de tamaño fijo, resistente a colisiones y efecto avalancha), los "
            "algoritmos de resumen (MD5, la familia SHA, SHA-1, SHA-256 y SHA-512, RIPEMD), para "
            "qué "
            "sirve el resumen (comprobar la integridad y la autenticidad de un fichero descargado, "
            "la "
            "firma y el almacenamiento de contraseñas) y los ataques a las funciones de resumen."
        ),
        patrones=(
            r"funcion(es)? (de )?hash|hashe?o|\bhashing\b|hash de comprobacion",
            r"resumen( de(l)? mensaje| digital)|huella digital|digest",
            r"\bmd5\b|\bsha\b|sha ?-? ?(1|2|256|512)|ripemd",
            r"tamano fijo|longitud de hash|resumen de tamano",
            r"integ?ridad (de un fichero|del mensaje|de los datos)|no ha sido alterada|"
            r"comprobar la integridad",
            r"colision(es)?|unidireccional|efecto avalancha",
        ),
        patrones_debiles=(r"hash", r"resumen", r"integridad"),
        prioridad=48,
    ),
    Materia(
        key="firma-digital-y-certificados",
        epigraph_code="IV.5.6",
        title="La firma digital, los certificados y la infraestructura de clave pública",
        resumen=(
            "Cómo se prueba quién ha firmado y que no ha cambiado: la firma digital y los "
            "servicios "
            "que da (autenticidad, integridad y no repudio), el proceso de firma y de verificación "
            "y "
            "qué clave se usa en cada paso, el certificado digital y su estructura conforme al "
            "estándar X.509, la autoridad de certificación y la infraestructura de clave pública "
            "(PKI), los servicios que presta (registro, emisión, validación y revocación), la "
            "revocación y su consulta (listas de revocación y OCSP) y el sellado de tiempo."
        ),
        patrones=(
            r"firma (digital|electronica)|firmar (digitalmente|un mensaje|electronicamente)",
            r"certificado(s)? (digital|electronico|de clave publica|de firma)|x ?509|509",
            r"infraestructura de clave publica|\bpki\b|autoridad de certificacion|"
            r"\bca\b (de|raiz)|entidad emisora",
            r"revocacion|lista(s)? de revocacion|\bcrl\b|\bocsp\b|revocado",
            r"sellado de tiempo|time ?-? ?stamping|marca de tiempo",
            r"no repudio|previene el repudio",
            r"\bber\b|basic encoding rules|estructura de un certificado",
            r"prestador(es)? de servicios de confianza|servicios de certificacion",
        ),
        patrones_debiles=(r"firma", r"certificado", r"pki"),
        prioridad=49,
    ),
    Materia(
        key="protocolos-seguros",
        epigraph_code="IV.5.5",
        title="Los protocolos seguros de red y de correo",
        resumen=(
            "Los protocolos que protegen las comunicaciones: la seguridad en la capa de red (IPsec "
            "y "
            "sus cabeceras AH y ESP, la asociación de seguridad y el intercambio de claves IKE), "
            "la "
            "seguridad en el transporte (TLS y su predecesor SSL, HTTPS y los protocolos de correo "
            "seguro S/MIME y PGP), la seguridad en la sesión y el acceso remoto (SSH, Kerberos y "
            "los "
            "protocolos de autenticación RADIUS y TACACS+), la seguridad de las redes inalámbricas "
            "(WEP, WPA y WPA2) y los protocolos y estándares de seguridad de internet."
        ),
        patrones=(
            r"protocolo(s)? (seguro|de seguridad|relacionado con la seguridad|de autenticacion|"
            r"de gestion de claves)",
            r"\bipsec\b|\bah\b|\besp\b|\bike\b|asociacion de seguridad|"
            r"cabecera del protocolo ah",
            r"\btls\b|\bssl\b|\bhttps\b|seguridad en la capa de transporte",
            r"\bssh\b|\bkerberos\b|\bs ?/ ?mime\b|\bpgp\b|\bset\b|\bldap\b|\bradius\b|"
            r"\btacacs\b|\bftps\b|\bsftp\b|cifrado implicito",
            r"\bwep\b|\bwpa\b|\bwpa2\b|red(es)? inalambrica(s)?.*seguridad|"
            r"seguridad (de|en) (las )?redes? inalambricas?",
            r"proporciona (capacidad de hacer )?seguras las comunicaciones|securizar las "
            r"comunicaciones",
            r"protocolo que proporciona servicios de autenticacion, autorizacion y contabilidad",
            r"estandares de seguridad para internet",
        ),
        patrones_debiles=(r"protocolo", r"ipsec", r"tls"),
        prioridad=50,
    ),
    # --- IV.5.7 Infraestructura física de un CPD --------------------------------------------------
    Materia(
        key="cpd-infraestructura",
        epigraph_code="IV.5.7",
        title="La infraestructura física del CPD: TIER, disponibilidad y eficiencia",
        resumen=(
            "El centro de proceso de datos como instalación: la norma ANSI/TIA-942 y sus áreas y "
            "sistemas, la clasificación por niveles TIER y la disponibilidad que da cada uno, el "
            "acondicionamiento (espacio, suelo técnico, cableado estructurado, el armario o rack y "
            "la "
            "unidad U), la climatización (las unidades CRAC y el free cooling), la alimentación "
            "(el "
            "sistema de alimentación ininterrumpida, los cuadros eléctricos y los grupos "
            "electrógenos), la eficiencia energética y el Green CPD con el indicador PUE, la "
            "infraestructura convergente y la ubicación del CPD de respaldo."
        ),
        patrones=(
            r"\bcpd\b|centro de (proceso|procesamiento) de datos|centro de calculo",
            r"tia ?-? ?942|ansi ?-? ?tia|ansi ?-? ?eia|eia ?/? ?tia",
            r"\btier\b|niveles? (tier|de disponibilidad)|grado de disponibilidad",
            r"\bpue\b|power usage effectiveness|green cpd|eficiencia (energetica|del cpd)|"
            r"free cooling|consumo energetico",
            r"sistema de alimentacion ininterrumpida|\bsai\b|\bsat\b|\bups\b|"
            r"cuadros electricos|interruptores diferenciales|grupo electrogeno",
            r"climatizacion|refrigeracion|unidades? crac|aire acondicionado|"
            r"temperatura y la humedad",
            r"armario|rack|unidad de rack|\bu\b|suelo tecnico|cableado estructurado",
            r"infraestructura (convergente|de soporte)|\bci\b",
            r"limpieza (de las cabezas|mensual)|mantenimiento (preventivo|correctivo) del cpd",
        ),
        patrones_debiles=(r"cpd", r"centro de datos", r"disponibilidad"),
        prioridad=51,
    ),
    # --- IV.5.8 Sistemas de gestión de incidencias -----------------------------------------------
    Materia(
        key="gestion-de-incidencias",
        epigraph_code="IV.5.8",
        title="La gestión de incidencias y el servicio de atención al usuario",
        resumen=(
            "Cómo se atiende y se resuelve lo que falla: el centro de atención a usuarios y sus "
            "funciones, la gestión de incidencias, de peticiones, de problemas y de cambios, el "
            "acuerdo de nivel de servicio y sus indicadores, la priorización por impacto y "
            "urgencia, "
            "el escalado funcional y jerárquico, las métricas de disponibilidad y de fiabilidad "
            "(MTBF, MTTR y tiempo de actividad), el catálogo de servicios y los marcos de "
            "referencia "
            "de gestión de servicios (ITIL y su sistema de valor), las herramientas de gestión de "
            "incidencias y los equipos de respuesta a incidentes de seguridad."
        ),
        patrones=(
            r"gestion de (incidencias|incidentes|problemas|cambios|peticiones|servicios)",
            r"\bitil\b|sistema de valor del servicio|\bsvs\b|marco de referencia de servicios",
            r"acuerdo de nivel de servicio|\bsla\b|nivel de servicio acordado",
            r"centro de atencion (al usuario|a usuarios)|\bcau\b|service desk|"
            r"gestor de atencion al usuario",
            r"escalado (funcional|jerarquico)|priorizar las incidencias|impacto y urgencia",
            r"\bmtbf\b|\bmttr\b|tiempo medio (entre fallos|de reparacion|para reparar)|"
            r"tiempo promedio|tiempo de disponibilidad|\buptime\b",
            r"\bcsirt\b|equipo de respuesta|respuesta a incidentes",
            r"incidencia(s)?( informatica| de seguridad)?\b|qu[eé] es un incidente",
            r"ticketing|herramienta de gestion de incidentes|open source para la gestion",
        ),
        patrones_debiles=(r"incidencia", r"servicio", r"usuario"),
        prioridad=52,
    ),
    # --- IV.5.9 Control remoto de puestos de usuario ---------------------------------------------
    Materia(
        key="control-remoto",
        epigraph_code="IV.5.9",
        title="El control remoto de puestos de usuario",
        resumen=(
            "El acceso al puesto desde otro sitio: el protocolo de escritorio remoto RDP y su "
            "puerto "
            "de escucha, las posibilidades y los límites de una conexión RDP, los servidores de "
            "terminales y las conexiones de escritorio remoto, las alternativas (VNC, Telnet y los "
            "asistentes de acceso remoto) y los problemas de seguridad propios del control remoto."
        ),
        patrones=(
            r"control remoto de puestos|escritorio remoto|acceso remoto|puesto remoto",
            r"\brdp\b|remote desktop protocol|protocolo rdp",
            r"\bvnc\b|virtual network computing|servidor(es)? de terminales|"
            r"terminal server|\brdesktop\b",
            r"conexion (rdp|remota)|\b3389\b|puerto de escucha del servidor",
            r"asistencia remota|controlar remotamente (el|un) (puesto|equipo)",
        ),
        patrones_debiles=(r"remoto", r"rdp", r"escritorio"),
        prioridad=53,
    ),
    # --- Las herramientas del CCN, que el banco pregunta por decenas ------------------------------
    Materia(
        key="herramientas-de-ciberseguridad",
        epigraph_code="IV.5.1",
        title="Las herramientas y las soluciones de ciberseguridad",
        resumen=(
            "El catálogo de herramientas con el que se opera: las soluciones y herramientas del "
            "CCN-CERT para la Administración (la defensa frente a ataques avanzados, la vigilancia "
            "y "
            "el análisis de amenazas, el intercambio de información de ciberamenazas, la gestión "
            "federada de tickets, la auditoría continua y el análisis de conformidad, la detección "
            "de "
            "malware, el borrado seguro y la formación), las herramientas de gestión de la "
            "seguridad "
            "(gestión de eventos e información, control de acceso a la red y automatización de "
            "dispositivos de red) y las plataformas de concienciación y de retos de ciberseguridad."
        ),
        patrones=(
            r"herramienta(s)? (del|de|para) (el )?ccn|solucion(es)? (de ciberseguridad )?del ccn|"
            r"soluciones? del ccn ?-? ?cert",
            r"herramienta(s)? (de|para) (la )?(gestion|analisis|deteccion|visualizacion|borrado|"
            r"compartir|coordinar)",
            r"analiza y gestiona los riesgos de seguridad de los sistemas de informacion|"
            r"comprobaci[oó]n de conocimientos en seguridad|desaf[ií]os de criptografia",
            r"simulador(es)? de (tecnicas|situaciones)|centro de vacunacion",
            r"gestion federada de tickets|intercambio de informacion de ciberamenazas|"
            r"defensa de ataques avanzados|visibilidad y control sobre la red",
            r"clasificacion com[uú]n de incidentes|conformidad tecnica del ens",
            r"mapas y gr[aá]ficas|tiempo real el estado de ciberseguridad",
        ),
        patrones_debiles=(
            r"herramienta",
            r"solucion",
            r"plataforma",
        ),
        prioridad=55,
    ),
)

#: El orden en que se **enseña** el índice: primero los conceptos (qué se protege, con qué normas,
# con
#: qué método de riesgo, quién decide y qué exige el ENS), después los tres bloques clásicos del
# tema
#: (la seguridad física, la lógica y las amenazas), después la criptografía en sus cuatro partes (el
#: cifrado, el resumen, la firma y los protocolos), después la instalación (el CPD) y por último la
#: operación (las incidencias, el control remoto y las herramientas con las que se hace), que es el
#: orden del título del tema.
ORDEN: tuple[str, ...] = (
    "conceptos-y-dimensiones",
    "normas-y-metodologias",
    "analisis-y-gestion-de-riesgos",
    "gobierno-de-la-seguridad",
    "ens-y-conformidad",
    "seguridad-fisica",
    "seguridad-logica",
    "amenazas-y-vulnerabilidades",
    "criptografia",
    "resumen-y-hash",
    "firma-digital-y-certificados",
    "protocolos-seguros",
    "cpd-infraestructura",
    "gestion-de-incidencias",
    "control-remoto",
    "herramientas-de-ciberseguridad",
)

__all__ = ["MATERIAS", "ORDEN"]
