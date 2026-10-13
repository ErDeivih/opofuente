"""El catálogo de materias de I.7 (protección de datos personales y derechos digitales).

I.7 es un tema **normativo**, así que su índice sigue la estructura de las normas que lo componen y
no un reparto por ocurrencias. Las normas del tema son el **Reglamento (UE) 2016/679** (RGPD), la
**Ley Orgánica 3/2018** (LOPDGDD), de protección de datos personales y garantía de los derechos
digitales, y —todavía con un peso grande en el banco— el **régimen anterior**: la Ley Orgánica
15/1999 (LOPD) y su reglamento de desarrollo, el Real Decreto 1720/2007, más el Real Decreto
994/1999 de medidas de seguridad. La mayoría de las preguntas del tema pregunta por **una** de esas
cuatro cosas, y el índice las separa para que el alumno estudie el régimen que le van a preguntar.

Los dos epígrafes oficiales del tema son «la protección de datos personales y su régimen jurídico:
principios, derechos y obligaciones» (I.7.1) y «derechos digitales» (I.7.2), y este catálogo los
abre
en los apartados que las preguntas piden de verdad:

- I.7.1, en **dieciséis**: el marco normativo y el ámbito de aplicación, los **principios** del
  tratamiento, la **base jurídica y el consentimiento**, las **categorías especiales de datos**, el
  **deber de información**, los **derechos del interesado**, el **responsable y el encargado**, el
  **Registro General y la inscripción de ficheros**, la **seguridad del tratamiento** (con los
  niveles del RD 1720/2007), las **violaciones de seguridad**, la **evaluación de impacto**, el
  **delegado de protección de datos**, las **transferencias internacionales**, las **autoridades de
  control** (la AEPD, las autonómicas y el Comité Europeo), los **códigos tipo y la certificación**
  y
  las **infracciones y sanciones**;
- I.7.2, en **tres**: los **derechos digitales** del título X de la LOPDGDD, los derechos digitales
  **en el ámbito laboral** (desconexión, intimidad frente a dispositivos, videovigilancia y
  geolocalización) y la **Carta de Derechos Digitales** con los derechos ante la inteligencia
  artificial y las carteras europeas de identidad.

Cinco decisiones de redacción de los patrones, dichas donde se leen:

- las citas de una norma van **con su número** y **con su sigla** (`ley organica 3 2018`,
`\blopdgdd\b`,
  `\brgpd\b`, `1720 2007`), porque el texto normalizado deja el número separado por espacios y
  porque
  la mitad de los enunciados escribe la sigla y la otra mitad el nombre desarrollado; sin las dos,
  un
  tercio del banco se quedaría sin apartado;
- **lo genérico va en `patrones_debiles`, nunca en los propios**. El reparto mira primero los
  patrones propios de todas las materias y solo si **ninguno** casa prueba los débiles, así que
  `datos personales`, `responsable del tratamiento` y `proteccion de datos` —que aparecen en media
  asignatura— no pueden robarle una pregunta a su apartado. Es la misma regla que en II.4: lo
  particular gana a lo general;
- el **régimen anterior (LOPD 15/1999 y RD 1720/2007) y el vigente (RGPD y LOPDGDD) comparten
  apartados por asunto**, no por norma: una pregunta sobre el derecho de acceso de la LOPD y otra
  sobre el derecho de acceso del RGPD se estudian juntas, porque lo que se aprende es el derecho. Lo
  que sí es apartado propio es lo que solo existe en un régimen: los **niveles de seguridad y el
  documento de seguridad** del RD 1720/2007, el **documento de seguridad** y las medidas por nivel,
  y
  el **Registro General y la inscripción de ficheros** de la LOPD;
- `normativa-y-ambito` es el **apartado de recogida del tema**, y por eso sus patrones son débiles:
  recoge lo que habla de datos personales y no ha casado con ningún apartado concreto (definiciones,
  ámbito material y territorial, exclusiones). No es un cajón —no hay cajones en este catálogo—: lo
  que no casa con **nada** va a la bandeja del propietario con su motivo
  (`Motivo.SIN_MATERIA_EN_EL_INDICE`);
- la distinción entre **`datos-especialmente-protegidos`** (qué datos son de categoría especial y
  cuándo se pueden tratar) y **`base-juridica-y-consentimiento`** (qué legitima el tratamiento) se
  hace por lo que el enunciado **nombra primero**: los dos hablan del artículo 9, y separarlos por
  la
  primera palabra que casa es lo que hace que el alumno encuentre el dato donde lo busca.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Las citas de las normas del tema, como las deja el texto normalizado («ley organica 3 2018»).
_RGPD = r"\brgpd\b|reglamento ue 2016 679|2016 679|directiva 2016 680"
_LOPDGDD = (
    r"\blopdgdd\b|ley organica 3 2018|ley 3 2018 de|"
    r"proteccion de datos personales y garantia de los derechos digitales"
)
_LOPD = r"\blopd\b|ley organica 15 1999|ley 15 1999|\b15 1999\b"
_RD_1720 = (
    r"\brd ?1720 ?2007\b|rdlopd|real decreto 1720 2007|\b1720 2007\b|"
    r"\brd ?994 ?1999\b|real decreto 994 1999|\b994 1999\b"
)
#: Las cuatro normas juntas: para los apartados que existen en todos los regímenes.
_NORMAS = rf"{_RGPD}|{_LOPDGDD}|{_LOPD}|{_RD_1720}"

MATERIAS: tuple[Materia, ...] = (
    # --- I.7.1 Protección de datos personales: principios, derechos y obligaciones ---------------
    Materia(
        key="normativa-y-ambito",
        epigraph_code="I.7.1",
        title="El marco normativo, el ámbito de aplicación y las definiciones",
        resumen=(
            "Qué normas rigen la protección de datos y a qué se aplican: el Reglamento (UE) "
            "2016/679, la Ley Orgánica 3/2018 y —como régimen anterior que el banco sigue "
            "preguntando— la Ley Orgánica 15/1999 y su reglamento, el Real Decreto 1720/2007; el "
            "objeto y el ámbito material y territorial de cada una, los tratamientos y los "
            "ficheros "
            "excluidos, la aplicación a los responsables no establecidos en la Unión, y las "
            "definiciones legales: datos personales, interesado, tratamiento, fichero, responsable "
            "y "
            "encargado, tercero, destinatario, disociación, seudonimización, establecimiento "
            "principal, categorías de datos y consentimiento del afectado."
        ),
        patrones=(
            _RD_1720,
            r"ambito (de aplicacion|material|territorial)",
            r"(no )?sera de aplicacion|quedan? fuera( asimismo)? del ambito|excluid[oa]s? del "
            r"(reglamento|ambito)|ficheros? o tratamientos? excluid",
            r"definicion(es)? (legal|de la ley)|se entendera por|se considera(ra)? (que )?(forman "
            r"parte|datos personales)",
            r"establecimiento principal|responsable no establecido|no establecido en la union",
            r"disociacion|seudonimizacion|anonimizacion",
            r"a los efectos de (la|esta) (ley|ley organica|reglamento)|a los efectos previstos",
            r"objeto de (la|esta) (ley|ley organica)|objeto del reglamento|tiene por objeto",
            r"fuentes? accesibles? al publico|censo promocional",
            r"articulo 2 1 del real decreto legislativo|ley de ordenacion de la cartografia",
            r"cualquier informacion concerniente a personas fisicas",
            r"personas? fisicas? identificad|identificables",
        ),
        patrones_debiles=(
            _RGPD,
            _LOPDGDD,
            _LOPD,
            r"datos personales|datos de caracter personal|dades personals",
            r"proteccion de datos|proteccio de dades",
            r"tratamiento de datos|tratamientos? de datos",
            r"\bficheros?\b",
            r"\bdatos\b",
        ),
        prioridad=60,
    ),
    Materia(
        key="principios-del-tratamiento",
        epigraph_code="I.7.1",
        title="Los principios del tratamiento y la protección desde el diseño",
        resumen=(
            "Los principios que tiene que cumplir todo tratamiento: licitud, lealtad y "
            "transparencia; "
            "limitación de la finalidad; minimización de los datos; exactitud; limitación del "
            "plazo de "
            "conservación; integridad y confidencialidad, y responsabilidad proactiva. Con ellos, "
            "la "
            "protección de datos desde el diseño y por defecto, la calidad de los datos, la "
            "proporcionalidad y la licitud del tratamiento cuando los datos se recogen para fines "
            "determinados, explícitos y legítimos."
        ),
        patrones=(
            r"principios? (de|relativos? al|del) (el )?tratamiento",
            r"principios? de (la )?proteccion de datos|principios? (del|de la) (rgpd|reglamento)",
            r"licitud|lealtad|transparencia del tratamiento",
            r"minimizacion|limitacion de la finalidad|limitacion del plazo",
            r"exactitud de los datos|datos (inexactos?|exactos? y)|(seran|seran? )?exactos",
            r"proteccion de datos desde el diseno|desde el diseno y por defecto|por defecto",
            r"responsabilidad proactiva|enfoque de riesgo|responsabilidad del responsable",
            r"conservacion|plazo de conservacion|se conservaran|conservarse durante",
            r"(datos personales )?seran (recogidos|tratados) con fines|fines determinados",
            r"integridad y confidencialidad|confidencialidad de los datos",
        ),
        patrones_debiles=(r"principio", r"finalidad", r"exactitud"),
        prioridad=22,
    ),
    Materia(
        key="base-juridica-y-consentimiento",
        epigraph_code="I.7.1",
        title="La base jurídica del tratamiento y el consentimiento",
        resumen=(
            "Qué legitima tratar datos personales: las bases jurídicas del artículo 6 del RGPD, "
            "las "
            "excepciones al consentimiento de la Ley Orgánica 15/1999, el consentimiento del "
            "interesado (sus condiciones, su carácter inequívoco, su prueba, su revocación y los "
            "supuestos en que no hace falta), el consentimiento de los menores de edad y la "
            "prohibición de recabar datos por medios engañosos o fraudulentos."
        ),
        patrones=(
            r"\bconsentimiento\b|consentir|prestar(a)? (su )?consentimiento",
            r"revocacion del consentimiento|revocar (el|su) consentimiento",
            r"base(s)? (juridica|del tratamiento|legitimadora)|legitimacion (del|para el) "
            r"tratamiento",
            r"articulo 6 (del|de el) (reglamento|rgpd)|art 6 (del|de el) reglamento",
            r"(sin (el|su) )?consentimiento (del|de el|expreso|inequivoco)",
            r"menor(es)? de edad|mayor(es)? de (14|14 anos|catorce)|14 anos|consentimiento.*menor",
            r"medios? (enganosa|fraudulenta)|forma enganosa y fraudulenta",
            r"interes(es)? (vital|publico|legitimo)|mision de interes publico",
            r"ejecucion de un contrato|obligacion legal del responsable",
        ),
        patrones_debiles=(r"consentimiento", r"legitimacion", r"autorizacion"),
        prioridad=20,
    ),
    Materia(
        key="datos-especialmente-protegidos",
        epigraph_code="I.7.1",
        title="Las categorías especiales de datos y los datos especialmente protegidos",
        resumen=(
            "Qué datos son de categoría especial y cuándo se pueden tratar: los datos que revelen "
            "el "
            "origen racial o étnico, las opiniones políticas, las convicciones religiosas o "
            "filosóficas y la afiliación sindical, los datos genéticos y biométricos, los "
            "relativos a "
            "la salud y a la vida sexual o la orientación sexual, los datos de condenas e "
            "infracciones penales y los datos de los menores; el régimen de excepciones del "
            "artículo "
            "9 del RGPD y el de los datos especialmente protegidos de la Ley Orgánica 15/1999, con "
            "las sanciones específicas de crear ficheros con ellos."
        ),
        patrones=(
            r"categorias? especiales?|datos? (de )?categorias? especiales?",
            r"datos? (especialmente|particularmente) protegidos?",
            r"origen racial|etnic[oa]|datos? etnicos?",
            r"ideologia|opiniones? politicas?|convicciones? religiosas?|religion|creencias?",
            r"afiliacion sindical|sindicato|sindical",
            r"vida sexual|orientacion sexual",
            r"datos? (relativos? a la|de) salud|datos? sanitarios?|historial clinico",
            r"biometric|dactiloscop|imagenes? faciales?|reconocimiento facial",
            r"genetic|datos? geneticos?",
            r"condenas?|infracciones? penales?|datos? penales?",
            r"datos? de (los )?(menores?|ninos)|menor de edad.*datos",
            r"prohibicion (del|de) tratamiento|tratamiento (prohibido|de estos datos)",
        ),
        patrones_debiles=(r"salud", r"religio", r"violencia de genero"),
        prioridad=21,
    ),
    Materia(
        key="deber-de-informacion",
        epigraph_code="I.7.1",
        title="El deber de información al interesado",
        resumen=(
            "La información que hay que dar a quien se le piden sus datos: dónde y cuándo hay que "
            "informar, la información básica y la adicional, el contenido mínimo de la "
            "información, "
            "la información por capas o en dos niveles, lo que se informa cuando los datos se "
            "obtienen del propio interesado y lo que se informa cuando no se han obtenido de él, "
            "la "
            "información en la recogida de datos de la Ley Orgánica 15/1999 y la dirección "
            "electrónica para acceder al resto de la información."
        ),
        patrones=(
            r"deber(es)? de informacion|derecho de informacion|obligacion de informar",
            r"informacion (basica|adicional|indicada|que debera facilitarse|que hay que facilitar)",
            r"informacion (a la que se refiere|contemplada en|senalada en|del apartado)",
            r"(deberan?|debera|han de) ser (previamente )?informad",
            r"informados? de (modo|forma) (expreso|preciso)",
            r"facilitar(a)? (al interesado )?(toda )?la informacion|proporcionar(a)? "
            r".{0,30}informacion",
            r"no (se )?hayan? (sido )?obtenidos? (del|de un|de el) (interesado|afectado)",
            r"cuando los datos personales no (se )?hayan obtenido",
            r"capas? de informacion|informacion por capas|primer nivel de informacion",
            r"direccion electronica u otro medio",
            r"informacion (en la recogida|al interesado|relativa a sus actuaciones)",
        ),
        patrones_debiles=(r"informacion", r"informar", r"informado"),
        prioridad=23,
    ),
    Materia(
        key="derechos-del-interesado",
        epigraph_code="I.7.1",
        title="Los derechos del interesado y su ejercicio",
        resumen=(
            "Los derechos que puede ejercer quien es titular de los datos y cómo se ejercen: el "
            "acceso, la rectificación, la supresión y el derecho al olvido, la limitación del "
            "tratamiento, la portabilidad, la oposición, el derecho a no ser objeto de decisiones "
            "individuales automatizadas y la elaboración de perfiles; las reglas comunes de "
            "ejercicio (forma, plazo de contestación, gratuidad, prueba de identidad, "
            "representación "
            "y ejercicio por terceros), los límites y las suspensiones, la tutela de derechos ante "
            "la "
            "autoridad de control y los derechos ARCO del régimen anterior."
        ),
        patrones=(
            r"derecho(s)? de (acceso|rectificacion|cancelacion|supresion|limitacion|portabilidad|"
            r"oposicion|actualizacion)",
            r"derecho(s)? (al olvido|de oposicion|de acceso|de rectificacion|de supresion|"
            r"de limitacion|de portabilidad|de actualizacion)",
            r"derechos? (de los interesados?|del interesado|de las personas|de los ciudadanos)",
            r"\barco\b|acceso, rectificacion, cancelacion y oposicion",
            r"ejercicio de (los |sus )?derechos|ejercitar(a|an)? (los|sus|el) derechos?|"
            r"podran ser ejercitad|seran ejercidos",
            r"tutela de (los )?derechos|reclamacion ante la agencia|solicitud de tutela",
            r"plazo (maximo )?(en que|para) (debe|dictar|resolver|contestar|atender).{0,40}"
            r"(derecho|solicitud|resolucion expresa)",
            r"portabilidad|formato estructurado|lectura mecanica|transmitirlos a otro responsable",
            r"derecho a recibir los datos|derecho a obtener sin dilacion",
            r"procedimiento de (oposicion|acceso|rectificacion|cancelacion)|"
            r"oposicion, acceso, rectificacion|oposicion, acceso, rectificacion o cancelacion",
            r"no se aplicara si la decision|cuando la decision (se base|este basada)",
            r"decision(es)? individual(es)? automatizad|elaboracion de perfiles|perfilado",
            r"no ser objeto de (una )?decision",
            r"supresion de los datos|derecho a obtener sin dilacion",
        ),
        patrones_debiles=(r"derecho", r"interesado", r"afectado"),
        prioridad=24,
    ),
    Materia(
        key="responsable-y-encargado",
        epigraph_code="I.7.1",
        title="El responsable y el encargado del tratamiento",
        resumen=(
            "Quién responde de qué: el responsable del tratamiento y el encargado, sus deberes "
            "respectivos, el contrato o acto jurídico del encargo y su contenido, la elección del "
            "encargado, los corresponsables y el representante; las obligaciones de los "
            "responsables "
            "y encargados del sector público (los contratos con terceros que tratan datos, los "
            "deberes de confidencialidad y secreto profesional), el registro de las actividades de "
            "tratamiento del responsable y del encargado, y los códigos de conducta que los "
            "vinculan."
        ),
        patrones=(
            r"contrato (de|del|con el) encargado|instrumento juridico|encargo del tratamiento",
            r"\bencargad[oa]s? (del|de) tratamiento|encargado(s)? y (el )?responsable",
            r"corresponsables?|responsables? conjuntos?",
            r"representante (del|de el) (responsable|encargado)",
            r"registro de (las )?actividades de tratamiento|registro de (los )?tratamientos",
            r"(prestacion de )?servicios? por parte de terceros|contratos? del sector "
            r"publico.*datos",
            r"deber(es)? de (confidencialidad|secreto)|secreto profesional",
            r"quien (decida|determine) (sobre )?(la finalidad|el contenido y uso)",
            r"eleccion de (un )?encargado|garantias (suficientes|adecuadas) del encargado",
            r"obligaciones? del responsable|funciones del responsable|obligaciones del encargado",
        ),
        patrones_debiles=(r"responsable", r"encargado", r"tercero"),
        prioridad=26,
    ),
    Materia(
        key="registro-e-inscripcion-de-ficheros",
        epigraph_code="I.7.1",
        title="El Registro General de Protección de Datos y la inscripción de ficheros",
        resumen=(
            "El registro público de los ficheros y su régimen: el Registro General de Protección "
            "de "
            "Datos y su contenido, la obligación de notificar e inscribir los ficheros y los "
            "tratamientos, quién tiene que inscribirlos y qué datos se inscriben, la creación de "
            "ficheros de titularidad pública y privada, la cancelación y la supresión de la "
            "inscripción, el Registro Central de ficheros y el régimen de inscripción después del "
            "Reglamento europeo."
        ),
        patrones=(
            r"registro general de proteccion de datos|registro central",
            r"inscripcion de (los )?ficheros|inscripcion en el registro|inscribir(se)? (los|en "
            r"el) ",
            r"notificacion (e inscripcion|de ficheros)|notificar (la creacion|los ficheros)",
            r"creacion de ficheros|creacion de tratamientos",
            r"ficheros? de titularidad (publica|privada)",
            r"(sigue siendo obligatoria|es obligatoria) la inscripcion",
            r"cancelacion (de la )?inscripcion|suprimir la inscripcion",
            r"datos relativos a los ficheros que sean necesarios para el ejercicio",
        ),
        patrones_debiles=(r"inscripcion", r"registro"),
        prioridad=28,
    ),
    Materia(
        key="seguridad-del-tratamiento",
        epigraph_code="I.7.1",
        title="La seguridad del tratamiento y las medidas de seguridad por niveles",
        resumen=(
            "Cómo se protegen los datos por dentro: la seguridad del tratamiento del artículo 32 "
            "del "
            "RGPD (medidas técnicas y organizativas, seudonimización, cifrado y evaluación del "
            "riesgo) y las medidas de seguridad del Real Decreto 1720/2007 con sus tres niveles "
            "—básico, medio y alto—, el documento de seguridad y su contenido, las auditorías, el "
            "registro de accesos, la gestión de soportes y copias, las claves de combinación y los "
            "códigos de control, los ficheros con datos de salud y los de las entidades "
            "financieras y "
            "de la Seguridad Social, y el bloqueo de los datos."
        ),
        patrones=(
            r"medidas? de seguridad|nivel(es)? de seguridad|de nivel (basico|medio|alto)",
            r"documento de seguridad",
            r"seguridad (de los datos|del tratamiento|de la informacion)",
            r"auditoria(s)?( de seguridad)?|auditoria (interna|externa|bienal)",
            r"registro de accesos|registro de (los )?accesos",
            r"claves? de combinacion|codigos? de control|central de alarmas|cajas fuertes",
            r"cifrad|en claro|ininteligible|criptograf",
            r"medidas? tecnicas y organizativas|seudonimizacion y el cifrado",
            r"entidades financieras|entidades gestoras y servicios comunes de la seguridad social",
            r"bloqueo de (los )?datos|bloquear los datos",
            r"copias? de (respaldo|seguridad)|soportes? (de|que contengan)",
            r"ficheros? automatizados|tratamientos? automatizados",
        ),
        patrones_debiles=(r"seguridad", r"medida", r"nivel"),
        prioridad=30,
    ),
    Materia(
        key="violaciones-de-seguridad",
        epigraph_code="I.7.1",
        title="Las violaciones de la seguridad de los datos",
        resumen=(
            "Qué es una violación de la seguridad de los datos personales y qué hay que hacer "
            "cuando "
            "ocurre: la diferencia entre incidente y violación de seguridad, la notificación a la "
            "autoridad de control y su plazo, la comunicación al interesado cuando entraña un alto "
            "riesgo, el contenido de la notificación, el registro de las violaciones y las "
            "excepciones a la hora de notificar."
        ),
        patrones=(
            r"violacion(es)? de (la )?seguridad",
            r"incidente(s)? de seguridad",
            r"notificacion de (una )?violacion|comunicar(a|an)? .{0,30}violacion",
            r"brecha de seguridad|fuga de (datos|informacion)",
            r"alto riesgo para los derechos",
            r"registro de (las )?violaciones",
            r"violacion de los datos personales",
            r"la notificacion contemplada en el apartado|contenido de la notificacion",
            r"violacio de seguretat|incident de seguretat",
        ),
        patrones_debiles=(r"violacion", r"incidente"),
        prioridad=31,
    ),
    Materia(
        key="evaluacion-de-impacto",
        epigraph_code="I.7.1",
        title="La evaluación de impacto y la consulta previa",
        resumen=(
            "Cuándo hay que analizar de antemano el riesgo de un tratamiento: la evaluación de "
            "impacto relativa a la protección de datos y los supuestos en que es obligatoria, su "
            "contenido y su metodología, las listas de tratamientos que la exigen, la consulta "
            "previa a la autoridad de control, la evaluación de riesgo y su revisión, y las "
            "herramientas de la Agencia para evaluar el riesgo."
        ),
        patrones=(
            r"evaluacion de impacto|\beipd\b",
            r"consulta previa a la autoridad",
            r"listas? de (los )?tratamientos?|lista de tratamientos que requieren",
            r"evaluacion de(l)? riesgo|analisis de riesgo|gestion de riesgos",
            r"tratamientos? (de alto riesgo|que entrañen un alto riesgo)",
            r"revisar(a|an)? la evaluacion|cuando se revise",
        ),
        patrones_debiles=(r"evaluacion", r"riesgo"),
        prioridad=32,
    ),
    Materia(
        key="delegado-de-proteccion-de-datos",
        epigraph_code="I.7.1",
        title="El delegado de protección de datos",
        resumen=(
            "La figura del delegado de protección de datos: quién está obligado a designarlo y los "
            "supuestos del artículo 37 del RGPD, los supuestos del artículo 34 de la Ley Orgánica "
            "3/2018, la comunicación de la designación y el cese a la Agencia y su plazo, su "
            "posición y su independencia, los medios y recursos que se le deben dar, sus funciones "
            "y "
            "sus deberes (informar, asesorar, supervisar, cooperar con la autoridad y ser el punto "
            "de "
            "contacto), y su intervención en la evaluación de impacto."
        ),
        patrones=(
            r"delegad[oa]s? de proteccion de datos|\bdpd\b",
            r"designacion de (un )?delegado|nombrar(a|an)? (a )?un delegado|no tiene la obligacion "
            r"de "
            r"nombrar",
            r"comunicar(a|an)? a la agencia .{0,40}(nombramientos|designaciones|ceses)",
            r"funciones del delegado|posicion del delegado|independencia del delegado",
            r"delegado de prevencion",
        ),
        patrones_debiles=(r"delegado", r"designacion"),
        prioridad=33,
    ),
    Materia(
        key="transferencias-internacionales",
        epigraph_code="I.7.1",
        title="Las transferencias internacionales de datos",
        resumen=(
            "La salida de los datos fuera del Espacio Económico Europeo: el principio general y "
            "las "
            "tres vías (las decisiones de adecuación, las garantías adecuadas y las normas "
            "corporativas vinculantes), las excepciones para casos concretos, la autorización de "
            "la "
            "Agencia, el contenido de las normas corporativas vinculantes, la suspensión del "
            "procedimiento y las transferencias ulteriores a terceros países."
        ),
        patrones=(
            r"transferencia(s)? internacional(es)?",
            r"decision(es)? de adecuacion|nivel de proteccion adecuado|pais(es)? (adecuad|tercer)",
            r"normas? corporativas vinculantes|\bbcr\b",
            r"garantias adecuadas|garantias (de|para la) transferencia",
            r"transfieran? (los )?datos a (un|otro) (estado|pais)|a un tercer pais|"
            r"a otro estado que no pertenezca a la union",
            r"organizacion(es)? internacional(es)?",
            r"transferencias ulteriores|excepciones? (para casos concretos|a la transferencia)",
        ),
        patrones_debiles=(r"transferencia", r"pais tercero", r"internacional"),
        prioridad=34,
    ),
    Materia(
        key="autoridades-de-control",
        epigraph_code="I.7.1",
        title="Las autoridades de control: la Agencia, las autonómicas y el Comité Europeo",
        resumen=(
            "Quién vigila el cumplimiento: la Agencia Española de Protección de Datos (su "
            "naturaleza "
            "y su régimen jurídico, su presidencia y su nombramiento, el Consejo Consultivo y sus "
            "miembros, su dependencia y su relación con el Gobierno, sus bienes y medios "
            "económicos, "
            "sus funciones y sus potestades de investigación, correctivas, de autorización y "
            "consultivas), las autoridades autonómicas y el registro de las mismas, el Comité "
            "Europeo "
            "de Protección de Datos, el mecanismo de coherencia y la cooperación entre "
            "autoridades, y "
            "los procedimientos de la Agencia."
        ),
        patrones=(
            r"\baepd\b|agencia (espanola )?de proteccion de datos",
            r"autoridad(es)? de (control|proteccion de datos)( autonomas?)?",
            r"comite europeo de proteccion de datos|comite europeo|mecanismo de coherencia",
            r"consejo consultivo|miembros? del consejo",
            r"president[ae] (de la agencia|de la autoridad|de la aepd)|director de la agencia",
            r"el presidente desempenara|presidente desempen|funciones del presidente",
            r"(potestades?|poderes?) (de (investigacion|autorizacion)|correctiv|consultiv)",
            r"cooperacion entre autoridades|autoridad de control (competente|interesada|requerida)",
            r"asistencia mutua|procedimiento (de|sancionador) de la agencia",
            r"(dependencia|adscripcion|se relaciona).{0,40}(ministerio|gobierno|cortes)",
            r"bienes y medios economicos",
        ),
        patrones_debiles=(r"agencia", r"autoridad", r"comite"),
        prioridad=35,
    ),
    Materia(
        key="codigos-tipo-y-certificacion",
        epigraph_code="I.7.1",
        title="Los códigos tipo, los códigos de conducta y la certificación",
        resumen=(
            "Los instrumentos de autorregulación y de acreditación: los códigos de conducta y su "
            "contenido, los códigos tipo del régimen anterior (su contenido mínimo, su inscripción "
            "y "
            "su adhesión, las entidades promotoras y los compromisos que pueden contener), la "
            "certificación en materia de protección de datos, los sellos y las marcas de "
            "certificación, los organismos de certificación y su acreditación, y las entidades "
            "adheridas y supletoriamente obligadas."
        ),
        patrones=(
            r"codigos? (tipo|de conducta|deontologico)",
            r"certificacion|sello(s)? (de|en materia de) (proteccion de datos|certificacion)|"
            r"marca de certificacion",
            r"organismo(s)? de certificacion|entidad(es)? certificadora",
            r"organismo(s)? de supervision|organismos? de supervision designados",
            r"acreditacion de (los )?organismos",
            r"adhesion|entidades? adheridas?|entidades? promotoras?",
            r"mecanismos? de certificacion",
        ),
        patrones_debiles=(r"codigo", r"certificacion", r"acreditacion"),
        prioridad=36,
    ),
    Materia(
        key="infracciones-y-sanciones",
        epigraph_code="I.7.1",
        title="Las infracciones, las sanciones y el procedimiento sancionador",
        resumen=(
            "Qué pasa cuando se incumple: las infracciones muy graves, graves y leves de la Ley "
            "Orgánica 15/1999 y de la Ley Orgánica 3/2018, con sus supuestos y su tipificación; "
            "las "
            "sanciones y las multas administrativas del RGPD con sus cuantías y sus tramos, el "
            "régimen de las administraciones públicas (el procedimiento de infracción y el "
            "apercibimiento), la prescripción de infracciones y sanciones y sus plazos, el "
            "procedimiento sancionador y sus reglas, y la valoración del comportamiento de los "
            "ciudadanos."
        ),
        patrones=(
            r"infraccion(es)? (muy grave|grave|leve)|infracciones? y sanciones",
            r"muy graves?|graves? y leves|sera(n)? constitutiv[oa]s? de (infraccion|falta)",
            r"se considera(n)? (como )?infraccion|constituye (una )?infraccion|es constitutiva de",
            r"sancion(es)?|multas? administrativas?|cuantia de (la )?multa|importe de la sancion",
            r"prescripcion (de )?(las )?(infracciones|sanciones)|prescriben",
            r"procedimiento sancionador|expediente sancionador|acuerdo de inicio",
            r"regimen sancionador|potestad sancionadora",
            r"20 000 000|10 000 000|4 % del volumen|2 % del volumen",
            r"apercibimiento|sancion a las administraciones publicas",
            r"(infraccion|sancion) (muy grave|grave|leve) (prescrib|.*(anos|anos))",
        ),
        patrones_debiles=(r"infraccion", r"sancion", r"multa", r"grave"),
        prioridad=37,
    ),
    # --- I.7.2 Derechos digitales -----------------------------------------------------------------
    Materia(
        key="derechos-digitales",
        epigraph_code="I.7.2",
        title="Los derechos digitales del título X de la LOPDGDD",
        resumen=(
            "El catálogo de derechos digitales de la Ley Orgánica 3/2018 y lo que garantiza cada "
            "uno: "
            "la neutralidad de internet y el acceso universal, la seguridad digital, la educación "
            "digital, la protección de los menores en internet, el derecho a la identidad digital, "
            "el "
            "derecho al testamento digital y los datos de las personas fallecidas, el derecho al "
            "olvido y a la supresión en las redes y los servicios de internet, la libertad de "
            "expresión y el derecho a la información en internet, el derecho de acceso a los datos "
            "propios y la portabilidad, la intimidad y el uso de la identidad en las redes "
            "sociales."
        ),
        patrones=(
            r"derechos? digital(es)?",
            r"titulo x( de la ley| de la lopdgdd)?",
            r"neutralidad (de|en) (la )?internet|acceso universal (a internet|a la red)",
            r"educacion digital|seguridad digital|alfabetizacion digital",
            r"proteccion de (los )?menores (en internet|en la red)",
            r"identidad digital|carteras? europeas? de identidad digital",
            r"testamento digital|datos? de (las )?personas fallecidas|persona fallecida|"
            r"datos de (los )?fallecidos",
            r"derecho al olvido|olvido digital|supresion en (las )?(redes|internet|servicios)",
            r"libertad de expresion|derecho a la informacion en internet",
            r"redes sociales|servicios? de (la sociedad de la informacion|intermediacion)",
            r"discapacidad.*accesibilidad digital|accesibilidad (universal|digital)",
        ),
        patrones_debiles=(r"digital(es)?", r"internet", r"redes"),
        prioridad=25,
    ),
    Materia(
        key="derechos-digitales-laborales",
        epigraph_code="I.7.2",
        title="Los derechos digitales en el ámbito laboral",
        resumen=(
            "Los derechos digitales de quien trabaja, en el sector público y en el privado: el "
            "derecho a la desconexión digital y su regulación en la negociación colectiva, el "
            "derecho "
            "a la intimidad frente al uso de dispositivos digitales en el ámbito laboral, el "
            "derecho "
            "a la intimidad frente a la videovigilancia y a la grabación de sonidos, el derecho a "
            "la "
            "intimidad ante los sistemas de geolocalización, la utilización de las cámaras para el "
            "control de los trabajadores, la capacidad de los empleadores y la información previa "
            "al "
            "uso de esos medios."
        ),
        patrones=(
            r"desconexion digital|derecho a la desconexion",
            r"dispositivos? digitales? (en el ambito laboral|de los empleados)|"
            r"intimidad (frente|ante|y uso de)",
            r"videovigilancia|videocamara|camaras? (de|o) videocamaras?|grabacion de sonidos",
            r"geolocalizacion|dispositivos? de geolocalizacion",
            r"ambito laboral|relacion laboral|poder de direccion|negociacion colectiva",
            r"control de (los )?(trabajadores|empleados)|poder de direccion",
            r"teletrabajo|entornos digitales y el teletrabajo",
            r"delegat d empresa|comite de empresa",
        ),
        patrones_debiles=(r"laboral", r"trabajador", r"empleado", r"empleador"),
        prioridad=26,
    ),
    Materia(
        key="carta-de-derechos-digitales",
        epigraph_code="I.7.2",
        title="La Carta de Derechos Digitales y los derechos ante la inteligencia artificial",
        resumen=(
            "La Carta de Derechos Digitales y los derechos que reconoce: los derechos de los "
            "usuarios "
            "ante la inteligencia artificial, la transparencia y la explicabilidad de los "
            "sistemas, "
            "los derechos ante las decisiones automatizadas, la no discriminación y la equidad, el "
            "desarrollo y el ciclo de vida de los sistemas de inteligencia artificial, y los "
            "principios y valores del entorno digital que la Carta declara."
        ),
        patrones=(
            r"carta de derechos digitales",
            r"inteligencia artificial|\bia\b|sistemas? de (ia|inteligencia artificial)",
            r"decisiones? automatizadas?|algoritm",
            r"explicabilidad|transparencia algoritmica|sistema de ia",
            r"xxv|articulo xxv",
        ),
        patrones_debiles=(r"carta", r"algoritmo"),
        prioridad=27,
    ),
)

#: El orden en que se **enseña** el índice: primero el marco y los principios (qué es y qué rige el
#: tratamiento), después cómo se legitima y qué datos son especiales, después los derechos del
#: interesado y quién responde, después las garantías y la seguridad (el registro, las medidas, las
#: violaciones y la evaluación), después las relaciones con terceros y con las autoridades (las
#: transferencias, las autoridades de control, los códigos y la certificación), después el régimen
#: sancionador, y por último los derechos digitales —que son el segundo epígrafe del tema y se
#: estudian al final, como en el programa—.
ORDEN: tuple[str, ...] = (
    "normativa-y-ambito",
    "principios-del-tratamiento",
    "base-juridica-y-consentimiento",
    "datos-especialmente-protegidos",
    "deber-de-informacion",
    "derechos-del-interesado",
    "responsable-y-encargado",
    "registro-e-inscripcion-de-ficheros",
    "seguridad-del-tratamiento",
    "violaciones-de-seguridad",
    "evaluacion-de-impacto",
    "delegado-de-proteccion-de-datos",
    "transferencias-internacionales",
    "autoridades-de-control",
    "codigos-tipo-y-certificacion",
    "infracciones-y-sanciones",
    "derechos-digitales",
    "derechos-digitales-laborales",
    "carta-de-derechos-digitales",
)

__all__ = ["MATERIAS", "ORDEN"]
