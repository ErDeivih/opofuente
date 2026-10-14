"""El catálogo de materias de I.4 (El EBEP, la Ley 19/2013 de transparencia y la Agenda 2030).

I.4 es un tema **normativo**: el índice sigue la estructura de las normas que mezcla. Sus tres
epígrafes oficiales son el texto refundido del Estatuto Básico del Empleado Público, la Ley 19/2013
de transparencia y buen gobierno y la Agenda 2030, así que:

- el **EBEP** (Real Decreto Legislativo 5/2015) se abre por sus partes, que es como pregunta el
  banco: qué es y a quién se aplica (`ebep-estructura-y-personal`), la selección y la pérdida de la
  condición de funcionario (`ebep-seleccion`), la carrera y la provisión de puestos
  (`ebep-carrera-y-provision`), las situaciones administrativas (`ebep-situaciones`), los derechos,
  los deberes y las retribuciones (`ebep-derechos-deberes-y-retribuciones`), el régimen
  disciplinario (`ebep-regimen-disciplinario`) y las incompatibilidades
  (`ebep-incompatibilidades`);
- la **Ley 19/2013** se abre por sus tres títulos más su órgano de control: la publicidad activa
  (`transparencia-publicidad-activa`), el derecho de acceso (`transparencia-derecho-de-acceso`), el
  buen gobierno y su régimen sancionador (`transparencia-buen-gobierno`) y el Consejo de
  Transparencia y Buen Gobierno (`consejo-de-transparencia`);
- la **Agenda 2030** va en un apartado (`agenda-2030-y-ods`), y los planes de Gobierno Abierto —que
  no son ninguna de las tres normas pero caen en este tema— en otro (`gobierno-abierto`).

**Y dos materias que están aquí porque sus preguntas se clasificaron con estas**, no porque el
título del tema las nombre: `administracion-electronica` (sede electrónica, CSV, registro, Ley
39/2015 y Real Decreto-ley 6/2023) y el cajón `i-4-otros`, que recoge lo que no es de ninguna de las
anteriores —incluidas las preguntas de otros temas que el clasificador dejó aquí— para que ninguna
se quede sin un apartado donde estudiarla. La medición está hecha: de los 546 grupos del tema, 331
traen epígrafe propio y 215 no.

Dos decisiones de redacción de los patrones, dichas donde se leen:

- los artículos van **por número** (`_ARTS_EBEP` y `_ARTS_LEY19`), porque media oposición pregunta
  «el artículo 18 del TREBEP» y sin el número esa pregunta no dice de qué habla;
- las siglas van **con su nombre desarrollado** (`\\btrebep\\b` y «estatuto basico del empleado
  publico»; `\\bctbg\\b` y «consejo de transparencia y buen gobierno»), porque el banco usa las dos
  formas y un patrón que solo acepte una deja fuera la mitad de las preguntas.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Las siglas del Estatuto, por sus dos nombres. El banco escribe `TREBEP`, `EBEP` y el nombre
#: entero, a veces en la misma pregunta.
_EBEP = (
    r"\btrebep\b|\bebep\b|estatuto basico del empleado publico|estatuto basico del empleo publico"
)

#: La Ley 19/2013, por sus dos nombres.
_LEY19 = r"ley 19 2013|ley 19 12013|ley 19 20013|transparencia"

#: Los artículos del TREBEP por bloque, como alternancia de números. Van con un `\d` opcional detrás
#: para que casen tanto «artículo 18» como «artículo 18.1» (que se normaliza a `articulo 18 1`).
_ARTS_EBEP = {
    # Título I: objeto, ámbito y clases de personal (1 a 13).
    "estructura": r"(articulos?|arts?) (1|2|3|4|5|6|7|8|9|1[0-3])\b",
    # Título II: nacimiento y extinción de la relación de servicio (14 a 24).
    "seleccion": r"(articulos?|arts?) (1[4-9]|2[0-4])\b",
    # Título III: carrera y provisión (14 a 24 y 74 a 84).
    "carrera": r"(articulos?|arts?) (7[4-9]|8[0-4])\b",
    # Título VI: situaciones administrativas (85 a 92).
    "situaciones": r"(articulos?|arts?) (8[5-9]|9[0-2])\b",
    # Título VII: régimen disciplinario (93 a 98).
    "disciplinario": r"(articulos?|arts?) (9[3-8])\b",
    # Título III, derechos y deberes y Título V: retribuciones (14 a 15, 22 a 30, 47 a 53).
    "derechos": r"(articulos?|arts?) (2[5-9]|30|4[7-9]|5[0-3])\b",
}

#: Los artículos de la Ley 19/2013, por título: el II es la publicidad activa (5 a 12), el III el
#: derecho de acceso (12 a 24) y el II, capítulo III, con el Título II bis, el buen gobierno (25 a
#: 32).
_ARTS_LEY19 = {
    "publicidad": r"(articulos?|arts?) (5|6|7|8|9|1[0-2])\b",
    "acceso": r"(articulos?|arts?) (1[3-9]|2[0-4])\b",
    "buen-gobierno": r"(articulos?|arts?) (2[5-9]|3[0-2])\b",
}

MATERIAS: tuple[Materia, ...] = (
    # --- I.4.1 El texto refundido del Estatuto Básico del Empleado Público ------------------------
    Materia(
        key="ebep-estructura-y-personal",
        epigraph_code="I.4.1",
        title="El EBEP: qué es, a quién se aplica y qué clases de empleado público hay",
        resumen=(
            "El Real Decreto Legislativo 5/2015 y su texto refundido: objeto y ámbito de "
            "aplicación "
            "(las Administraciones y entidades a las que se aplica y a las que no), los principios "
            "y "
            "el carácter supletorio de sus disposiciones, las competencias de cada Administración "
            "y "
            "las clases de empleado público —funcionario de carrera, funcionario interino, "
            "personal "
            "laboral, personal eventual y personal directivo—, los grupos y subgrupos de "
            "clasificación (A1, A2, B, C1 y C2) y la relación de servicio."
        ),
        patrones=(
            _EBEP,
            r"real decreto legislativo 5 2015|rdl 5 2015",
            r"texto refundido de la ley del estatuto",
            r"empleado(s)? publico(s)?|empleado(s)? publica(s)?",
            r"clases de (empleado|personal)|personal al servicio",
            r"personal (laboral|eventual|directivo|funcionario|interino)",
            r"funcionario(s)? de carrera|funcionari[oa]s? interin[oa]s?",
            r"ambito de aplicacion|se aplica(ra)? (directamente|al personal)",
            r"subgrupo(s)? (a1|a2|b|c1|c2)|grupo(s)? de clasificacion",
            r"relacion de servicio|nombramiento legal",
            r"funciones publicas necesarias|habilitacion de caracter nacional|corporaciones "
            r"locales",
            r"toma de posesion|cese",
            r"articulo 2 (del trebep|1)",
            _ARTS_EBEP["estructura"],
        ),
        patrones_debiles=(r"empleado publico", r"estatuto", r"personal"),
        prioridad=10,
    ),
    Materia(
        key="ebep-seleccion",
        epigraph_code="I.4.1",
        title="La selección y la pérdida de la condición de funcionario",
        resumen=(
            "Los procesos selectivos y sus principios (publicidad, igualdad, mérito y capacidad), "
            "los órganos de selección, la oferta de empleo público, los sistemas selectivos "
            "(oposición y concurso-oposición), los requisitos de acceso, las medidas de "
            "discriminación positiva, la adquisición y la pérdida de la condición de funcionario "
            "(renuncia, jubilación, separación del servicio, inhabilitación y pena principal o "
            "accesoria) y el personal directivo."
        ),
        patrones=(
            r"proceso(s)? selectivo(s)?|sistema(s)? selectivo(s)?",
            r"seleccion( de personal| de los funcionarios)?",
            r"oferta de empleo publico|convocatoria(s)? de (pruebas|plazas)",
            r"concurso.?oposicion|\boposicion\b",
            r"organo(s)? de seleccion|tribunal(es)? de seleccion",
            r"requisito(s)? (general|de acceso)|nacionalidad.*acceso",
            r"perdida de la condicion de funcionario|adquisicion de la condicion",
            r"\brenuncia\b|jubilacion|inhabilitacion|separacion del servicio",
            r"personal directivo|directivo profesional",
            r"discapacidad|medidas de (accion positiva|discriminacion)",
            r"causas de (la )?(perdida|extincion)",
            _ARTS_EBEP["seleccion"],
        ),
        patrones_debiles=(r"seleccion", r"convocatoria", r"condicion de funcionario"),
        prioridad=11,
    ),
    Materia(
        key="ebep-carrera-y-provision",
        epigraph_code="I.4.1",
        title="La carrera profesional, la promoción interna y la provisión de puestos",
        resumen=(
            "Los instrumentos que ordenan la vida profesional del funcionario: la carrera "
            "profesional (horizontal y vertical), la promoción interna y su antigüedad, la "
            "formación, la evaluación del desempeño, la provisión de puestos de trabajo (concurso "
            "y "
            "libre designación), las comisiones de servicio, la movilidad entre Administraciones, "
            "las agrupaciones de puestos y el teletrabajo."
        ),
        patrones=(
            r"carrera (profesional|horizontal|vertical)",
            r"promocion interna|ascenso",
            r"evaluacion del desempeno|evaluacion del rendimiento",
            r"provision de puestos|provicion de puestos",
            r"concurso (de (meritos|traslados)|general|especifico)",
            r"libre designacion",
            r"comision(es)? de (servicios?|servicio)",
            r"movilidad|adscripcion (provisional|definitiva)",
            r"grado|escalon|categoria",
            r"teletrabajo|trabajo a distancia",
            r"formacion (del personal|continua)|plan de formacion",
            r"detectar las necesidades|planificacion (de recursos humanos|estrategica)",
        ),
        patrones_debiles=(r"carrera", r"promocion", r"puesto de trabajo"),
        prioridad=12,
    ),
    Materia(
        key="ebep-situaciones",
        epigraph_code="I.4.1",
        title="Las situaciones administrativas",
        resumen=(
            "Las situaciones en que puede hallarse un funcionario de carrera: servicio activo, "
            "servicios especiales (miembros del Gobierno, altos cargos, liberados sindicales…), "
            "servicio en otras Administraciones públicas, expectativa de destino, excedencia "
            "(voluntaria, por interés particular, por agrupación familiar, por cuidado de hijos o "
            "familiares y por razón de violencia de género), suspensión de funciones y sus efectos "
            "sobre el puesto, el tiempo de servicio y las retribuciones."
        ),
        patrones=(
            r"situacion(es)? administrativa(s)?",
            r"servicio activo",
            r"servicios especiales",
            r"servicio en otras administraciones|servicio en otra administracion",
            r"excedencia (voluntaria|forzosa|por interes particular|por agrupacion familiar|por "
            r"cuidado|por razon de violencia)",
            r"excedencia(s)?",
            r"suspension (de funciones|firme)",
            r"expectativa de destino",
            r"violencia de genero.*excedencia|excedencia.*violencia de genero",
            r"pase a la situacion|seran declarados en situacion",
            _ARTS_EBEP["situaciones"],
        ),
        patrones_debiles=(r"excedencia", r"situacion", r"suspension"),
        prioridad=13,
    ),
    Materia(
        key="ebep-derechos-deberes-y-retribuciones",
        epigraph_code="I.4.1",
        title="Derechos, deberes, principios éticos y retribuciones",
        resumen=(
            "Los derechos individuales y colectivos de los empleados públicos, los deberes y los "
            "principios éticos (artículo 53) y de conducta (artículo 54), el código de conducta, "
            "las retribuciones de los funcionarios (básicas —sueldo y trienios— y complementarias "
            "—destino, específico y productividad—) y las del personal laboral, la jornada, los "
            "permisos (por nacimiento, cuidado de familiares, conciliación), las vacaciones y la "
            "evaluación."
        ),
        patrones=(
            r"derechos? (individuales?|colectivos?|de los empleados)",
            r"deber(es)? (de los empleados|publicos)?|codigo de conducta",
            r"principios? (eticos?|de conducta)",
            r"retribuciones? (basicas?|complementarias?|del personal|de los funcionarios)",
            r"sueldo|trienios|complemento (de destino|especifico|de productividad)",
            r"pagas extraordinarias|indemnizacion(es)? por (razon del servicio|residencia)",
            r"complementos? salariales?|salario base",
            r"jornada (de trabajo|general)|horario",
            r"permisos? (por|para)|vacaciones anuales|conciliacion",
            r"nacimiento|maternidad|paternidad|lactancia|fallecimiento",
            r"reduccion de jornada|excedencia.*hijos",
            r"formacion.*derecho|derecho a la formacion",
            r"articulo 14 del trebep|articulo 15 del trebep",
            _ARTS_EBEP["derechos"],
        ),
        patrones_debiles=(r"derecho", r"retribucion", r"permiso"),
        prioridad=14,
    ),
    Materia(
        key="ebep-regimen-disciplinario",
        epigraph_code="I.4.1",
        title="El régimen disciplinario: faltas, sanciones y su prescripción",
        resumen=(
            "La responsabilidad disciplinaria del empleado público: las faltas leves, graves y muy "
            "graves (con el catálogo de cada una), las sanciones que les corresponden, el "
            "procedimiento disciplinario y sus garantías, la prescripción de las faltas y de las "
            "sanciones, el demérito, la separación del servicio y el «registro de sanciones»."
        ),
        patrones=(
            r"regimen disciplinario|responsabilidad disciplinaria",
            r"falta(s)? (leve|leves|grave|graves|muy grave|muy graves|disciplinaria)",
            r"sancion(es)?( disciplinaria)?",
            r"prescripcion de (las )?(faltas|sanciones)|plazo de prescripcion",
            r"procedimiento disciplinario",
            r"demerito",
            r"separacion del servicio",
            r"ausencia injustificada|abandono del servicio",
            r"infraccion(es)? disciplinaria",
            _ARTS_EBEP["disciplinario"],
        ),
        patrones_debiles=(r"falta", r"sancion", r"disciplinario"),
        prioridad=15,
    ),
    Materia(
        key="ebep-incompatibilidades",
        epigraph_code="I.4.1",
        title="El régimen de incompatibilidades",
        resumen=(
            "El régimen de incompatibilidades del personal al servicio de las Administraciones: "
            "qué "
            "actividades públicas y privadas pueden compatibilizarse, los principios de la Ley "
            "53/1984, la dedicación exclusiva, el reconocimiento de compatibilidad, las "
            "incompatibilidades por pertenencia a órganos, la percepción de dos pagas y las "
            "indemnizaciones por cese."
        ),
        patrones=(
            r"incompatibilidad(es)?",
            r"ley 53 1984|ley de incompatibilidades",
            r"actividades? (publicas?|privadas?)",
            r"reconocimiento de compatibilidad",
            r"dedicacion (exclusiva|a tiempo completo)",
            r"compatibilizar|compatibilidad (para|del puesto)",
            r"dos pagas|segunda actividad",
            r"pertenencia a (organos|consejos)",
        ),
        patrones_debiles=(r"incompatibilidad", r"compatibilidad"),
        prioridad=16,
    ),
    Materia(
        key="administracion-electronica",
        epigraph_code="I.4.1",
        title="La administración electrónica que cae en este tema: sedes, registros y documentos",
        resumen=(
            "La sede electrónica y su contenido mínimo, el registro electrónico y las "
            "notificaciones, "
            "el código seguro de verificación (CSV) y el catálogo de documentos, las copias "
            "electrónicas, la Ley 39/2015 y la Ley 40/2015, el Real Decreto-ley 6/2023 y los "
            "prestadores de servicios electrónicos de confianza. Va aquí porque las preguntas de "
            "administración electrónica que cita este tema se clasificaron con las de función "
            "pública."
        ),
        patrones=(
            r"sede(s)? electronica(s)?|sede judicial electronica",
            r"codigo seguro de verificacion|\bcsv\b",
            r"registro(s)? electronico(s)?",
            r"notificacion(es)? electronica(s)?|practica de la notificacion",
            r"ley 39 2015|ley 40 2015|ley 39 20015",
            r"real decreto ley 6 2023|real decreto-ley 6 2023",
            r"prestadores? de servicios electronicos de confianza",
            r"certificado(s)? electronico(s)?|firma electronica",
            r"documento(s)? electronico(s)?|copias? electronicas?",
            r"firma del titular|sellado de tiempo",
            r"punto de acceso general|portal de internet",
        ),
        patrones_debiles=(r"sede electronica", r"electronico", r"registro"),
        prioridad=20,
    ),
    # --- I.4.2 La Ley 19/2013, de transparencia, acceso y buen gobierno --------------------------
    Materia(
        key="transparencia-publicidad-activa",
        epigraph_code="I.4.2",
        title="La publicidad activa y el Portal de Transparencia",
        resumen=(
            "El Título II de la Ley 19/2013: la obligación de publicar de oficio la información "
            "institucional, organizativa y de planificación, la información de relevancia "
            "jurídica, "
            "la información económica, presupuestaria y estadística, los principios técnicos de la "
            "publicidad (accesibilidad, interoperabilidad, calidad y reutilización), el Portal de "
            "la "
            "Transparencia y el plazo de publicación."
        ),
        patrones=(
            r"publicidad activa",
            r"portal de (la )?transparencia",
            r"publicar(an)? de oficio|obligaciones de publicidad",
            r"informacion (institucional|organizativa|economica|presupuestaria|estadistica|"
            r"de relevancia juridica)",
            r"principios? tecnicos? de la (publicidad|informacion)",
            r"reutilizacion de la informacion",
            r"contenido minimo.*portal",
            r"ordenanza de transparencia",
            r"publicacion del codigo de las aplicaciones",
            _ARTS_LEY19["publicidad"],
        ),
        patrones_debiles=(r"publicidad", r"portal", r"publicar"),
        prioridad=10,
    ),
    Materia(
        key="transparencia-derecho-de-acceso",
        epigraph_code="I.4.2",
        title="El derecho de acceso a la información pública",
        resumen=(
            "El Título III de la Ley 19/2013: quién puede solicitar y cómo, las causas de "
            "inadmisión a trámite, los límites del derecho, la protección de los datos personales "
            "y "
            "de los especialmente protegidos, la audiencia a los terceros afectados, la resolución "
            "(plazo, ampliación y notificación), el acceso parcial, la reclamación y el silencio, "
            "y "
            "la información sujeta a publicidad activa."
        ),
        patrones=(
            r"derecho de acceso( a la informacion)?",
            r"solicitud(es)? de acceso|solicitante",
            r"se inadmitiran a tramite|inadmi(sion|tir)",
            r"limites? (del derecho|al derecho)|podra ser limitado",
            r"datos (personales|especialmente protegidos)",
            r"tercero(s)? (afectado|identificado)",
            r"resolucion en la que se conceda o deniegue",
            r"acceso parcial|informacion de caracter auxiliar",
            r"reclamacion ante el consejo de transparencia",
            r"plazo (de un mes|para (notificar|resolver))",
            r"ampliacion del plazo|silencio",
            _ARTS_LEY19["acceso"],
        ),
        patrones_debiles=(r"acceso", r"solicitud", r"informacion publica"),
        prioridad=11,
    ),
    Materia(
        key="transparencia-buen-gobierno",
        epigraph_code="I.4.2",
        title="El buen gobierno y su régimen sancionador",
        resumen=(
            "El Título II, capítulo III, de la Ley 19/2013 y su Título II bis: los principios de "
            "buen gobierno y la obligación de abstenerse, los altos cargos y su régimen, el "
            "ejercicio "
            "del alto cargo sometido a los principios de eficacia y austeridad, las infracciones y "
            "sanciones (muy graves y graves), su prescripción, la competencia para imponerlas y el "
            "procedimiento."
        ),
        patrones=(
            r"buen gobierno",
            r"altos? cargos?",
            r"principios? (de buen gobierno|informadores|eticos?)",
            r"infraccion(es)? (muy grave|grave|leve|disciplinaria)",
            r"sancion(es)?|competencia para la imposicion de sanciones",
            r"prescripcion de las infracciones",
            r"abstencion|ejercicio del alto cargo",
            r"responsabilidad.*(alto cargo|buen gobierno)",
            _ARTS_LEY19["buen-gobierno"],
        ),
        patrones_debiles=(r"buen gobierno", r"alto cargo", r"sancion"),
        prioridad=12,
    ),
    Materia(
        key="consejo-de-transparencia",
        epigraph_code="I.4.2",
        title="El Consejo de Transparencia y Buen Gobierno",
        resumen=(
            "El Consejo de Transparencia y Buen Gobierno: su naturaleza y personalidad jurídica, "
            "su "
            "composición (el Presidente —nombramiento y mandato—, el Consejo y la Comisión de "
            "Transparencia y Buen Gobierno), los vocales y quién no es miembro, sus funciones "
            "(resolver las reclamaciones, evaluar, informar y proponer), su Estatuto, su "
            "estructura "
            "orgánica y su personal."
        ),
        patrones=(
            r"consejo de transparencia|\bctbg\b",
            r"comision de transparencia y buen gobierno",
            r"presidente del consejo de transparencia",
            r"miembro(s)? de la comision",
            r"estructura organica.*consejo",
            r"estatuto del consejo de transparencia",
            r"personalidad juridica propia|plena capacidad de obrar",
            r"funciones? del consejo de transparencia",
        ),
        patrones_debiles=(r"consejo de transparencia", r"transparencia"),
        prioridad=13,
    ),
    Materia(
        key="gobierno-abierto",
        epigraph_code="I.4.2",
        title="El Gobierno Abierto y sus planes de acción",
        resumen=(
            "El Gobierno Abierto: qué es y en qué pilares se sustenta (transparencia, "
            "participación "
            "y colaboración), sus principios informadores, los planes de acción (el IV Plan de "
            "Gobierno Abierto y sus ejes), el Foro de Gobierno Abierto, la Alianza para el "
            "Gobierno "
            "Abierto y el mecanismo de evaluación de los compromisos."
        ),
        patrones=(
            r"gobierno abierto",
            r"plan(es)? de (accion )?(de )?gobierno abierto|iv plan",
            r"pilares? (del gobierno abierto|de la alianza)",
            r"foro de gobierno abierto",
            r"alianza para el gobierno abierto|\bogp\b|open government",
            r"compromisos?.*gobierno abierto",
            r"mecanismo de evaluacion.*avance|informe de autoevaluacion",
        ),
        patrones_debiles=(r"gobierno abierto", r"participacion"),
        prioridad=14,
    ),
    # --- I.4.3 La Agenda 2030 y los Objetivos de Desarrollo Sostenible ---------------------------
    Materia(
        key="agenda-2030-y-ods",
        epigraph_code="I.4.3",
        title="La Agenda 2030 y los Objetivos de Desarrollo Sostenible",
        resumen=(
            "La Agenda 2030 sobre Desarrollo Sostenible: quién y cuándo la aprobó, cuántos "
            "objetivos "
            "y metas tiene (17 y 169), en qué fecha entraron en vigor, el contenido de cada ODS "
            "(incluido a qué se refiere el ODS 4, 9, 10 y 14), su estructura de gobernanza y sus "
            "áreas de vital importancia, el mecanismo de examen, y la Agenda España 2030 con sus "
            "ejes (incluidos los transversales)."
        ),
        patrones=(
            r"agenda 2030",
            r"objetivos? de desarrollo sostenible|\bods\b",
            r"\bods [0-9]+\b",
            r"desarrollo sostenible",
            r"agenda espana 2030|estrategia de desarrollo sostenible",
            r"metas? de la agenda|17 objetivos",
            r"naciones unidas.*2030|asamblea general.*2030",
            r"areas? de vital importancia|las \bp\b\b",
            r"examen(es)? (nacional(es)?|voluntario)|foro politico de alto nivel",
        ),
        patrones_debiles=(r"2030", r"sostenible", r"objetivo"),
        prioridad=10,
    ),
    Materia(
        key="i-4-otros",
        epigraph_code="I.4.1",
        title="Otras cuestiones que caen en este tema",
        resumen=(
            "Lo que cae en las preguntas de este tema y no es de ninguna de las materias "
            "anteriores "
            "(por ejemplo, preguntas de informática o de otras normas que el clasificador dejó "
            "aquí): "
            "se recoge en vez de perderlo, para que ninguna pregunta se quede sin un apartado "
            "donde "
            "estudiarla."
        ),
        patrones=(),
        prioridad=29,
    ),
)

#: El orden en que se **enseña** el índice: el del título del tema (el Estatuto, la Ley 19/2013 y
#: la Agenda 2030). Dentro del Estatuto se estudia primero qué es y a quién se aplica, después cómo
#: se entra y cómo se sale, luego la carrera y las situaciones, y al final los derechos, el régimen
#: disciplinario y las incompatibilidades.
ORDEN: tuple[str, ...] = (
    "ebep-estructura-y-personal",
    "ebep-seleccion",
    "ebep-carrera-y-provision",
    "ebep-situaciones",
    "ebep-derechos-deberes-y-retribuciones",
    "ebep-regimen-disciplinario",
    "ebep-incompatibilidades",
    "administracion-electronica",
    "transparencia-publicidad-activa",
    "transparencia-derecho-de-acceso",
    "transparencia-buen-gobierno",
    "consejo-de-transparencia",
    "gobierno-abierto",
    "agenda-2030-y-ods",
    "i-4-otros",
)

__all__ = ["MATERIAS", "ORDEN"]
