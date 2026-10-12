"""El catálogo de materias de I.8 (acceso electrónico, procedimiento electrónico, ENS, ENI y NTI).

I.8 es un tema **normativo**, así que su índice sigue la estructura de las normas que lo componen y
no un reparto por ocurrencias. Las normas del tema son la Ley 39/2015 (procedimiento administrativo
común), la Ley 40/2015 (régimen jurídico del sector público), la Ley 11/2007 (acceso electrónico de
los ciudadanos, que sigue cayendo aunque esté derogada en su mayor parte), el Real Decreto 203/2021
(reglamento de actuación y funcionamiento del sector público por medios electrónicos), el Real
Decreto 311/2022 y el Real Decreto 3/2010 (Esquema Nacional de Seguridad), el Real Decreto 4/2010
(Esquema Nacional de Interoperabilidad) y las Normas Técnicas de Interoperabilidad que desarrollan
este último.

Los cuatro epígrafes oficiales del tema son el acceso electrónico, la gestión electrónica de los
procedimientos, el ENS y la ENI y las NTI, y este catálogo los abre en los apartados que las
preguntas piden de verdad:

- el acceso electrónico, en cuatro: el **derecho a relacionarse** y quién está obligado, la **sede
  electrónica y los canales**, la **identificación y la firma** de los interesados y la
  **administración electrónica** como competencia (ámbito, órganos y gobernanza);
- la gestión electrónica de los procedimientos, en seis: los **registros** (el registro electrónico
  general, el de apoderamientos y el de funcionarios habilitados), las **notificaciones**, el
  **documento y el expediente electrónico**, la **tramitación del procedimiento**, los **interesados
  y la representación** y la **actuación administrativa automatizada**;
- el ENS y la ENI, en cuatro: el **Esquema Nacional de Seguridad**, el **Esquema Nacional de
  Interoperabilidad**, la **reutilización de la información** y los **servicios comunes y
  compartidos** (los que hacen posible lo anterior);
- las NTI, en cuatro: las del **documento y el expediente**, las de **firma y sellos**, las de
  **datos, metadatos y comunicaciones** y las de **políticas y catálogo de estándares**.

Tres decisiones de redacción de los patrones, dichas donde se leen:

- las citas de una norma van **con su número** (`ley 39 2015`, `rd 311 2022`), porque el texto
  normalizado deja el número separado por espacios y una pregunta que dice «la Ley 39/2015» no dice
  nada más de su materia: sin la cita, cien preguntas del tema se quedarían sin apartado;
- los conceptos que aparecen en **las dos normas** (interesado, notificación, registro) van a su
  apartado de asunto y no al de la ley que los regula: eso es lo que hace que un apartado de la NTI
  se distinga del procedimiento que la aplica;
- la sigla va con `\\b` y **con** su nombre desarrollado (`\\bens\\b` y «esquema nacional de
  seguridad»), porque la mitad de los enunciados escribe la sigla y la otra mitad el nombre, y
  también al revés: `\\beni\\b`, `\\bnti\\b`, `\\bsir\\b`, `\\bcs v\\b`.

Las preguntas que no se sitúan ni por su enunciado ni por el texto de sus hechos **no** acaban en un
cajón: van a la bandeja del propietario con su motivo (`Motivo.SIN_MATERIA_EN_EL_INDICE`).
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Las citas de las normas del tema, como las deja el texto normalizado («ley 39 2015»).
_LEY_39 = r"ley\s?39\s?/?\s?2015|\b39\s?/\s?2015\b|\blpac\b"
_LEY_40 = r"ley\s?40\s?/?\s?2015|\b40\s?/\s?2015\b|\blrjsp\b"
_LEY_11 = r"ley\s?11\s?/?\s?2007|\b11\s?/\s?2007\b|\blaecsp\b"
_RD_203 = r"real decreto\s?203\s?/?\s?2021|\brd\s?203\s?/\s?2021\b|decreto\s?203\s?/\s?2021"
#: El ENS, por su nombre, por su sigla y por **sus dos** reales decretos (el vigente y el anterior).
_ENS = (
    r"esquema nacional de seguridad|\bens\b|\brd\s?311\s?/\s?2022\b|"
    r"real decreto\s?311\s?/\s?2022|\brd\s?3\s?/\s?2010\b|real decreto\s?3\s?/\s?2010"
)
#: La ENI, por su nombre, por su sigla y por su real decreto.
_ENI = (
    r"esquema nacional de interoperabilidad|\beni\b|\brd\s?4\s?/\s?2010\b|"
    r"real decreto\s?4\s?/\s?2010"
)

MATERIAS: tuple[Materia, ...] = (
    # --- I.8.1 Acceso electrónico de los ciudadanos a los servicios públicos ----------------------
    Materia(
        key="derecho-a-relacionarse",
        epigraph_code="I.8.1",
        title="El derecho a relacionarse electrónicamente y quién está obligado",
        resumen=(
            "El derecho de los ciudadanos a relacionarse con las administraciones por medios "
            "electrónicos y su régimen: los sujetos que pueden ejercerlo y los "
            "colectivos que están "
            "obligados a hacerlo (las personas jurídicas, las entidades sin personalidad, los que "
            "ejercen actividad profesional colegiada, los representantes y los "
            "empleados públicos), "
            "la elección del canal, la asistencia en el uso de medios electrónicos, la lengua, la "
            "gratuidad del acceso y la igualdad, la accesibilidad y los derechos de los ciudadanos "
            "en la Ley 11/2007 y en la Ley 39/2015."
        ),
        patrones=(
            _LEY_11,
            r"derecho(s)? (de los ciudadanos|a relacionarse|de acceso)",
            r"relacionarse (con|por medios|electronicamente)",
            r"obligad[oa]s? a (relacionarse|utilizar|usar) (por|los) medios electronicos|"
            r"quedan obligad",
            r"personas? juridicas?|entidades? sin personalidad",
            r"colegiad[oa]|profesionales? (colegiad|para los que)",
            r"asistencia (al ciudadano|en el uso)|oficina de asistencia|asistencia en materia",
            r"lengua(s)? (oficial|cooficial)|castellano",
            r"accesibilidad|discapacidad|igualdad de (acceso|genero)",
            r"(no )?estaran obligad|obligatoriedad de relacionarse",
        ),
        patrones_debiles=(r"ciudadano(s)?", r"derecho", r"relacionarse"),
        prioridad=20,
    ),
    Materia(
        key="sede-y-canales",
        epigraph_code="I.8.1",
        title="La sede electrónica, los canales y los puntos de acceso",
        resumen=(
            "Dónde se atiende al ciudadano por vía electrónica: la sede electrónica "
            "(su creación, su "
            "titularidad, su dirección, su responsabilidad y su contenido), el portal "
            "de internet y "
            "su diferencia con la sede, el Punto de Acceso General, las oficinas de asistencia en "
            "materia de registros, los canales de acceso (presencial, telefónico y "
            "electrónico), la "
            "cita previa, el tablón edictal y los servicios de atención e información al ciudadano."
        ),
        patrones=(
            r"\bsede(s)? electronica(s)?\b",
            r"punto de acceso general|\bpag\b|\b060\b|oficina de asistencia",
            r"portal de internet|sede (central|asociada)|subsede",
            r"canal(es)? (de acceso|electronico|presencial|telefonico)|atencion (al ciudadano|"
            r"telefonica)",
            r"cita previa|tablon edictal|oficina(s)? de registro",
            r"sellos? (de|electronico de) la sede|sede electronica.*(creacion|titular|responsab)",
            r"informacion (y atencion |al ciudadano|general)",
            r"directorio de (servicios|unidades)|\bcarpeta ciudadana\b|mi carpeta",
        ),
        patrones_debiles=(r"sede", r"portal", r"oficina"),
        prioridad=21,
    ),
    Materia(
        key="identificacion-y-firma",
        epigraph_code="I.8.1",
        title="La identificación y la firma electrónica de los interesados",
        resumen=(
            "Cómo se acredita quién actúa y cómo firma: los sistemas de identificación de los "
            "interesados (certificado electrónico cualificado, sello electrónico, DNI electrónico, "
            "Cl@ve y los sistemas de clave concertada), los sistemas de firma admitidos, la firma "
            "electrónica avanzada y cualificada, el sello de órgano y el sello de "
            "empleado público, "
            "el código seguro de verificación (CSV) y su uso para comprobar copias, la firma del "
            "interesado en el procedimiento y el régimen de la firma electrónica en la normativa "
            "de desarrollo."
        ),
        patrones=(
            r"sistema(s)? de (identificacion|firma)( electronica)?",
            r"firma(s)? electronica(s)?|firmar electronicamente|firmado electronicamente",
            r"sello(s)? electronico(s)?|sello de organo|sello de empleado",
            r"certificado(s)? (electronico|digital|cualificad|de firma|de empleado)",
            r"\bdni(e)?\b|documento nacional de identidad electronico|tarjeta soporte|chip",
            r"reglamento eidas|\beidas\b|910\s?/\s?2014|cartera(s)? europea(s)? de identidad|"
            r"identidad digital|servicios? de confianza",
            r"clave concertada|\bcl@ve\b|clave permanente|clave pin",
            r"codigo seguro de verificacion|\bcsv\b",
            r"identificacion (de los interesados|y firma|electronica)",
            r"prestador(es)? de servicios de confianza|confianza cualificad",
        ),
        patrones_debiles=(r"firma", r"certificado", r"identificacion"),
        prioridad=22,
    ),
    Materia(
        key="administracion-electronica-y-gobernanza",
        epigraph_code="I.8.1",
        title="La administración electrónica: ámbito, órganos y gobernanza",
        resumen=(
            "El marco general de la administración electrónica: el ámbito de aplicación de las "
            "leyes, los principios de actuación, el órgano competente para cada actuación, la "
            "atribución de competencias a los órganos y unidades, la estrategia y el gobierno de "
            "las tecnologías de la información (la comisión de estrategia TIC y los órganos de "
            "coordinación), los convenios y los planes, la cooperación entre administraciones y la "
            "gestión del cambio."
        ),
        patrones=(
            _LEY_40,
            _RD_203,
            r"forman parte del sector publico|sector publico (institucional|estatal|autonomico)",
            r"ambito de aplicacion de (la|las) ley",
            r"gobierno de las tecnologias|estrategia(s)? (tic|tecnologica)|comision de estrategia",
            r"cooperacion (entre|inter)administrativa|convenio(s)? (de|para) (la|el) "
            r"(administracion|"
            r"sede)",
            r"competencia(s)? (de los organos|digital)|atribucion de competencias",
            r"principios? (de actuacion|generales de la administracion electronica)|"
            r"principio(s)? organizativ",
            r"administracion electronica(?! de)|transformacion digital|digitalizacion de la "
            r"administracion",
            r"plan(es)? de (digitalizacion|gobierno)|agenda digital",
            r"espana digital|estrategia (nacional|de impulso)|inteligencia artificial|"
            r"tecnologia 5g|\b5g\b",
        ),
        patrones_debiles=(r"administracion", r"competencia", r"organo"),
        prioridad=23,
    ),
    # --- I.8.2 La gestión electrónica de los procedimientos administrativos -----------------------
    Materia(
        key="registros",
        epigraph_code="I.8.2",
        title="Los registros: electrónico general, de apoderamientos y de funcionarios habilitados",
        resumen=(
            "Dónde y cómo se presentan las solicitudes: el registro electrónico general y su "
            "funcionamiento (asientos, fecha y hora, número de asiento, días "
            "inhábiles y cómputo de "
            "plazos), el registro de apoderamientos (su contenido, la representación "
            "apud acta y su "
            "inscripción), el registro de funcionarios habilitados y el registro electrónico de "
            "empleados públicos habilitados, los documentos que se pueden presentar y los que no, "
            "la subsanación de la presentación y el justificante de presentación."
        ),
        patrones=(
            r"registro(s)? electronico(s)?( general)?|registro general",
            r"registro de apoderamientos|apud acta|registro de (funcionarios|empleados publicos) "
            r"habilitad",
            r"presentacion (de solicitudes|de documentos|de escritos|electronica)",
            r"asiento(s)? (de|en el) registro|numero de asiento|anotacion(es)? de registro",
            r"justificante(s)? de (presentacion|registro)",
            r"fecha y hora (de presentacion|oficial)|calendario de dias inhabiles|dias inhábiles",
            r"documento(s) que (se|deben) (pueden )?presentar|no se admitira(n)? "
            r"(por|en el) registro",
        ),
        patrones_debiles=(r"registro", r"presentacion", r"solicitud"),
        prioridad=24,
    ),
    Materia(
        key="notificaciones",
        epigraph_code="I.8.2",
        title="Las notificaciones electrónicas y su práctica",
        resumen=(
            "Cómo llega el acto al interesado: la práctica de las notificaciones por medios "
            "electrónicos, la notificación en la sede y en la dirección electrónica habilitada, el "
            "aviso de cortesía y su valor, la notificación por comparecencia cuando "
            "no se accede al "
            "contenido, el rechazo de la notificación y sus efectos, la notificación por edictos y "
            "la publicación en el boletín o en el tablón, la notificación defectuosa y su "
            "subsanación, y el régimen de la notificación en papel."
        ),
        patrones=(
            r"notificacion(es)?( electronica(s)?)?",
            r"practica de (la|las) notificacion",
            r"comparecencia|no accede(d|r)? al contenido|notificacion por (edictos|comparecencia)",
            r"aviso(s)? (de cortesia|de notificacion)|direccion electronica habilitada|\bdeh\b",
            r"notificacion (rechazad|defectuos|fallid|infructuos)",
            r"publicacion (en el boletin|en el tablon|edictal)|tablon de edictos",
            r"efectos de la notificacion|se entendera (notificad|rechazad)",
            r"ley\s?39\s?/?\s?2015.*notificac|notificac.*articulo\s?4[0-9]",
        ),
        patrones_debiles=(r"notificar", r"notificacion", r"aviso"),
        prioridad=25,
    ),
    Materia(
        key="documento-y-expediente",
        epigraph_code="I.8.2",
        title="El documento y el expediente electrónico, las copias y el archivo",
        resumen=(
            "Qué es un documento administrativo electrónico y cómo se conserva: sus requisitos "
            "(contenido, autor, firma, metadatos y formato), la validez y la eficacia "
            "de las copias "
            "auténticas, la digitalización de documentos en papel y su valor probatorio, el "
            "expediente electrónico (su índice, su foliado y su puesta a disposición), el archivo "
            "electrónico único y la conservación de los documentos, y la copia y el traslado de "
            "documentos."
        ),
        patrones=(
            r"documento(s)? (administrativo(s)? )?electronic",
            r"copia(s)? (autentica(s)?|electronic)|copias? (simples?|de documentos)",
            r"digitalizacion (de|del) documento|digitalizar",
            r"expediente(s)? electronic|indice electronic|foliado",
            r"archivo electronic|conservacion de (los )?documento|archivo(s)? de documentos",
            r"metadatos|formato(s)? (de documento|abierto)|contenido minimo",
            r"validez (y eficacia )?de (las )?copias|eficacia de las copias",
            r"documento (valid|nulo|invalido)|firma del documento",
            r"\bodf\b|open document format|formato(s)? de (documento|archivo) abierto(s)?",
        ),
        patrones_debiles=(r"documento", r"expediente", r"copia"),
        prioridad=26,
    ),
    Materia(
        key="tramitacion-del-procedimiento",
        epigraph_code="I.8.2",
        title="La tramitación electrónica del procedimiento administrativo",
        resumen=(
            "El procedimiento administrativo hecho por medios electrónicos: su ámbito y sus fases "
            "(iniciación, ordenación, instrucción, finalización y ejecución), los actos de "
            "instrucción y los informes, la resolución y su notificación, el silencio "
            "administrativo, la tramitación simplificada, la acumulación de procedimientos, la "
            "caducidad y la terminación, los recursos administrativos presentados por vía "
            "electrónica y los plazos del procedimiento en la Ley 39/2015."
        ),
        patrones=(
            _LEY_39,
            r"quedan derogadas|disposicion(es)? derogatoria|derogad[oa]s? (expresamente|por)",
            r"acto(s)? administrativo(s)?|motivacion (del acto|de los actos)|deber de motivar",
            r"a los efectos de (esta|la presente) ley|terminos que en ella se emplean|"
            r"definiciones de la ley",
            r"\btramit",
            r"procedimiento(s)? administrativo(s)?( comun)?",
            r"tramitacion (electronica|simplificada|del procedimiento)",
            r"(iniciacion|ordenacion|instruccion|finalizacion|ejecucion) del procedimiento",
            r"recurso(s)? (de alzada|de reposicion|extraordinario de revision)|revision de oficio",
            r"resolucion (expresa|presunta)|silencio administrativo|silencio (positivo|negativo)",
            r"caducidad del procedimiento|terminacion del procedimiento",
            r"plazo(s)? (maximo|de resoluci|del procedimiento)|computo de plazos",
        ),
        patrones_debiles=(r"procedimiento", r"tramitacion", r"plazo"),
        prioridad=27,
    ),
    Materia(
        key="interesados-y-representacion",
        epigraph_code="I.8.2",
        title="Los interesados, la capacidad y la representación",
        resumen=(
            "Quién es parte en el procedimiento y quién puede actuar por él: el concepto de "
            "interesado y los que tienen la consideración de tal, la capacidad de obrar y su "
            "acreditación, la representación y sus formas, el apoderamiento apud acta, la "
            "representación mancomunada o solidaria, los registros de apoderamientos y su "
            "inscripción, y la identificación de los interesados en el procedimiento."
        ),
        patrones=(
            r"interesad[oa]s? (en el procedimiento|se considera|son los)",
            r"concepto de interesado|quien (tiene|tienen) la consideracion de interesad",
            r"capacidad de obrar",
            r"representacion(?! grafica)|representante(s)? del interesad",
            r"apud acta|poder(es)? de representacion|apoderamiento",
            r"actuacion por (medio de )?representante|acreditar la representacion",
            r"legitimacion|accion(es)? (publica|de interesado)",
        ),
        patrones_debiles=(r"interesado", r"representacion", r"apoderamiento"),
        prioridad=28,
    ),
    Materia(
        key="actuacion-automatizada-y-servicios",
        epigraph_code="I.8.2",
        title="La actuación administrativa automatizada y los catálogos de servicios",
        resumen=(
            "Las administraciones que actúan por sí mismas: la actuación administrativa "
            "automatizada, su régimen y la firma por sello de órgano, los sistemas de "
            "información y "
            "las aplicaciones, el catálogo de servicios y el de procedimientos, la carta de "
            "servicios y la calidad, la reingeniería de procesos, las declaraciones responsables y "
            "las comunicaciones previas presentadas electrónicamente."
        ),
        patrones=(
            r"actuacion administrativa automatizada|administracion automatizada",
            r"catalogo(s)? de (servicios|procedimientos)|carta(s)? de servicios",
            r"declaracion(es)? responsable(s)?|comunicacion(es)? previa(s)?",
            r"calidad de los servicios|evaluacion de (la calidad|los servicios)|carta de "
            r"compromisos",
            r"sistema(s)? de informacion|aplicacion(es)? informatica",
            r"simplificacion administrativa|reduccion de cargas|reingenieria",
        ),
        patrones_debiles=(r"servicio", r"automatizada"),
        prioridad=29,
    ),
    # --- I.8.3 Esquema Nacional de Seguridad y de Interoperabilidad -------------------------------
    Materia(
        key="ens",
        epigraph_code="I.8.3",
        title="El Esquema Nacional de Seguridad",
        resumen=(
            "El Esquema Nacional de Seguridad: su objeto y su ámbito, los principios básicos y los "
            "requisitos mínimos, las dimensiones de seguridad y los niveles, la categorización del "
            "sistema (categoría básica, media y alta), las medidas de seguridad y su selección, la "
            "auditoría de la seguridad y la declaración de conformidad, los roles (responsable de "
            "seguridad, de servicio y de sistema), la respuesta a incidentes, la criptología y el "
            "uso de productos cualificados, y el Real Decreto 311/2022 y el anterior Real Decreto "
            "3/2010."
        ),
        patrones=(
            _ENS,
            r"categor(ia|izacion) (de la|del) (informacion|sistema)|categorias? "
            r"(basica|media|alta)"
            r"dimension(es)? de (la )?seguridad|medida(s)? de seguridad|principio(s)? basico(s)? "
            r"de (la )?seguridad",
            r"requisitos? minimos de seguridad|nivel(es)? de seguridad",
            r"auditoria (de|en materia de) seguridad|declaracion de conformidad|certificacion de "
            r"conformidad",
            r"responsable(s)? de (la )?(seguridad|servicio|sistema)|comite de seguridad",
            r"incidente(s)? de seguridad|gestion de incidentes|respuesta a incidentes",
            r"criptologia|criptografia cualificad|producto(s)? cualificad",
            r"analisis de riesgos|gestion de riesgos|principio de seguridad",
            r"\b(op|mp) [a-z]{2,4} [0-9]|\bmp sw\b|\bop exp\b|responsable de la informacion",
        ),
        patrones_debiles=(r"seguridad", r"medida", r"\bens\b"),
        prioridad=30,
    ),
    Materia(
        key="eni",
        epigraph_code="I.8.3",
        title="El Esquema Nacional de Interoperabilidad",
        resumen=(
            "El Esquema Nacional de Interoperabilidad: su objeto y su ámbito, los principios "
            "(entre ellos la sostenibilidad, el uso de estándares abiertos y la no supeditación "
            "tecnológica), las tres dimensiones de la interoperabilidad (organizativa, semántica y "
            "técnica), la interoperabilidad europea (el marco europeo y el EIF), el catálogo de "
            "estándares y su actualización, la reutilización de sistemas y aplicaciones, la "
            "transferencia de tecnología y el Real Decreto 4/2010."
        ),
        patrones=(
            _ENI,
            r"dimension(es)? de (la )?interoperabilidad|interoperabilidad (organizativa|semantica|"
            r"tecnica)",
            r"principio(s)? de (la )?interoperabilidad|supeditacion tecnologica|"
            r"estandares? abiertos?|uso de estandares",
            r"catalogo de estandares|marco europeo de interoperabilidad|\beif\b",
            r"interoperabilidad (entre|de las) administracion",
            r"sostenibilidad (de los|de las) (sistemas|aplicacion)|reutilizacion de (sistemas|"
            r"aplicaciones|software)",
            r"transferencia de tecnologia|declaracion de "
            r"(interoperabilidad|conformidad en materia)",
        ),
        patrones_debiles=(r"interoperabilidad", r"estandar", r"esquema"),
        prioridad=31,
    ),
    Materia(
        key="reutilizacion-de-la-informacion",
        epigraph_code="I.8.3",
        title="La reutilización de la información y los datos abiertos",
        resumen=(
            "Abrir los datos que ya tienen las administraciones: la reutilización de documentos y "
            "de información del sector público (la Ley 37/2007 y su ámbito), las modalidades de "
            "reutilización, las condiciones y las licencias, la prohibición de "
            "derechos exclusivos, "
            "los formatos y la puesta a disposición, los catálogos y portales de datos abiertos, y "
            "la política de gestión de documentos y de datos."
        ),
        patrones=(
            r"reutilizacion (de (la )?(informacion|documentos|datos)|de la informacion del sector)",
            r"datos abiertos|open data|portal de datos",
            r"licencia(s)? (de reutilizacion|de datos)|condiciones de reutilizacion",
            r"derechos? exclusivos|acuerdo(s)? exclusiv",
            r"ley\s?37\s?/?\s?2007|\b37\s?/\s?2007\b",
            r"puesta a disposicion (de la informacion|de los datos)|formato(s)? (reutilizable|"
            r"legible por maquina)",
            r"politica(s)? de (gestion de documentos|datos|informacion)|gobierno del dato",
        ),
        patrones_debiles=(r"reutilizacion", r"datos", r"abiertos"),
        prioridad=32,
    ),
    Materia(
        key="servicios-comunes-y-compartidos",
        epigraph_code="I.8.3",
        title="Los servicios comunes y compartidos",
        resumen=(
            "Las piezas que sostienen la administración electrónica: los servicios comunes y los "
            "servicios compartidos, los sistemas de información comunes (el Sistema de Información "
            "Administrativa, el Sistema de Interconexión de Registros, la Plataforma de "
            "Intermediación de Datos y el servicio de verificación de datos), la red SARA y las "
            "redes de comunicación, la Carpeta Ciudadana, la Plataforma de Contratación, la sede "
            "electrónica compartida y los nodos de interoperabilidad."
        ),
        patrones=(
            r"servicio(s)? (comun(es)?|compartid[oa]s?)|infraestructura(s)? comun(es)?",
            r"sistema(s)? de informacion (comun|administrativa)|\bsia\b",
            r"sistema de interconexion de registros|\bsir\b|\bgeiser\b",
            r"plataforma de intermediacion|\bscsp\b|verificacion de datos|intermediacion de datos",
            r"red\s?sara|\bsara\b|red(es)? de comunicacion(es)? de las administracion",
            r"carpeta ciudadana|plataforma de contratacion|\bplace\b|\bface\b",
            r"nodo(s)? de interoperabilidad|punto(s)? de acceso",
            r"servicio(s)? de (soporte|alojamiento)|centro(s)? de datos|nube (privada|publica) "
            r"de la administracion",
        ),
        patrones_debiles=(r"comun(es)?", r"compartid", r"plataforma"),
        prioridad=33,
    ),
    # --- I.8.4 Normas técnicas de Interoperabilidad -----------------------------------------------
    Materia(
        key="nti-documento-y-expediente",
        epigraph_code="I.8.4",
        title="Las NTI del documento, la digitalización y el expediente",
        resumen=(
            "Las normas técnicas de interoperabilidad que dicen cómo es un documento: la NTI de "
            "Documento electrónico (sus componentes, sus metadatos mínimos obligatorios y sus "
            "condiciones), la NTI de Digitalización de documentos (los requisitos del "
            "proceso y los "
            "formatos de imagen), la NTI de Copia auténtica, la NTI de Expediente electrónico (su "
            "estructura, su índice y los servicios de remisión) y la NTI de Política de gestión de "
            "documentos electrónicos."
        ),
        patrones=(
            r"norma(s)? tecnica(s)? de interoperabilidad|\bnti\b",
            r"nti de (documento|digitalizacion|copia|expediente|politica de gestion)",
            r"documento electronico.*(metadatos|componente|estructura)|metadatos minimos",
            r"digitalizacion.*(requisitos|formato|resolucion|imagen)",
            r"copia autentica.*(nti|norma)|valor probatorio de la copia",
            r"expediente electronic.*(estructura|indice|servicio de remision)",
            r"politica de gestion de documentos electronicos|conservacion.*documento",
        ),
        patrones_debiles=(r"\bnti\b", r"digitalizacion", r"metadatos"),
        prioridad=34,
    ),
    Materia(
        key="nti-firma-y-sellos",
        epigraph_code="I.8.4",
        title="Las NTI de firma electrónica, certificados y sellos",
        resumen=(
            "Las normas técnicas que dicen cómo se firma: la NTI de Firma electrónica y de "
            "certificados (los formatos de firma, la validación y las políticas de firma), la NTI "
            "de Sello electrónico y de sello de órgano, la NTI de Protocolos de firma y la NTI del "
            "Catálogo de estándares en lo que toca a la firma, junto con las condiciones de uso de "
            "los certificados y la verificación de la firma."
        ),
        patrones=(
            r"nti (de|del) (firma|sello|certificad|protocolo)",
            r"policitica(s)? de firma|politica de firma electronica",
            r"formato(s)? de firma|\bxades\b|\bcades\b|\bpes\b|firma (longeva|de larga duracion)",
            r"validacion de (la )?firma|verificacion de (la )?firma|validez de la firma",
            r"sello(s)? (de organo|electronico|de empleado publico)",
            r"certificado(s)? (de empleado publico|de sello|de componente|de sede)",
            r"prestador(es)? de (servicios de )?certificacion|autoridad de certificacion",
        ),
        patrones_debiles=(r"firma", r"sello", r"certificado"),
        prioridad=35,
    ),
    Materia(
        key="nti-datos-y-comunicaciones",
        epigraph_code="I.8.4",
        title="Las NTI de datos, metadatos y comunicaciones",
        resumen=(
            "Las normas técnicas que dicen cómo se intercambian los datos: la NTI de Modelo de "
            "datos (el modelo de datos de las administraciones y su publicación), la NTI de "
            "Catálogo de estándares, la NTI de Protocolos de comunicación (los protocolos de "
            "transporte y de intercambio), la NTI de Comunicación de datos entre "
            "administraciones y "
            "la NTI de Reutilización de recursos, con los esquemas y los formatos de intercambio."
        ),
        patrones=(
            r"nti (de|del) (modelo|modelos|dato|comunicacion|protocolo|catalogo|reutilizacion|"
            r"intercambio)",
            r"modelo(s)? de datos?.*(administracion|comun|publish)|publicacion de modelos de datos",
            r"esquema(s)? de (datos|intercambio)|formato(s)? de intercambio",
            r"protocolo(s)? de (comunicacion|transporte|intercambio)|\bsobre\b.*xml",
            r"comunicacion de datos entre administraciones|intercambio de datos",
            r"catalogo de estandares|relacion de estandares",
        ),
        patrones_debiles=(r"modelo de datos", r"protocolo", r"intercambio"),
        prioridad=36,
    ),
    Materia(
        key="nti-politicas-y-gobierno",
        epigraph_code="I.8.4",
        title="Las políticas de interoperabilidad y el gobierno de las NTI",
        resumen=(
            "Quién decide y con qué reglas se aprueban las normas del esquema: la política de "
            "firma y de certificados, la política de seguridad de la información, la política de "
            "gestión de documentos, los órganos competentes para aprobar las normas técnicas de "
            "interoperabilidad (la Comisión de estrategia TIC y el Comité técnico de "
            "interoperabilidad), su publicación y su mantenimiento, y la declaración de "
            "conformidad con el esquema."
        ),
        patrones=(
            r"politica(s)? (de|nacional de) (firma|seguridad|interoperabilidad|gestion de "
            r"documentos|informacion)",
            r"comite tecnico de interoperabilidad|comision (sectorial|de estrategia|tecnica)",
            r"aprobacion de (las )?normas? tecnicas|elaboracion de (las )?nti",
            r"resolucion de la secretaria|orden (ministerial|de desarrollo)|instruccion tecnica",
            r"declaracion de conformidad|esquema nacional.*conformidad",
            r"mantenimiento de (las )?normas|actualizacion de (las )?nti|version de la nti",
        ),
        patrones_debiles=(r"politica", r"comite", r"conformidad"),
        prioridad=37,
    ),
)

#: El orden en que se **enseña** el índice: primero quién puede relacionarse y por dónde (el acceso
#: electrónico), después cómo se sustancia el procedimiento (los registros, las notificaciones, el
#: documento), después los dos esquemas que lo sostienen (la seguridad y la interoperabilidad y lo
#: que se construye encima: los servicios comunes), y por último las normas técnicas que desarrollan
#: la interoperabilidad —que es el orden del título del tema y el orden en que se estudia—.
ORDEN: tuple[str, ...] = (
    "derecho-a-relacionarse",
    "sede-y-canales",
    "identificacion-y-firma",
    "administracion-electronica-y-gobernanza",
    "registros",
    "notificaciones",
    "documento-y-expediente",
    "tramitacion-del-procedimiento",
    "interesados-y-representacion",
    "actuacion-automatizada-y-servicios",
    "ens",
    "eni",
    "reutilizacion-de-la-informacion",
    "servicios-comunes-y-compartidos",
    "nti-documento-y-expediente",
    "nti-firma-y-sellos",
    "nti-datos-y-comunicaciones",
    "nti-politicas-y-gobierno",
)

__all__ = ["MATERIAS", "ORDEN"]
