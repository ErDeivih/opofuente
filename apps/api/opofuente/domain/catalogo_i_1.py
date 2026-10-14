"""El catálogo de materias de I.1 (La Constitución Española de 1978).

I.1 es un tema **normativo**: el índice sigue la estructura de la norma. Los cuatro epígrafes
oficiales son La Constitución, los derechos y deberes, su garantía y suspensión, y La Corona, así
que:

- lo que la Constitución dice de sus propios caracteres, de los principios del Título Preliminar y
de
  los **órganos** que crea (Cortes, Gobierno, Poder Judicial, Tribunal Constitucional, organización
  territorial y economía) va a `I.1.1`, que es el epígrafe de la Constitución entera;
- los derechos y los deberes, por capítulos y secciones del Título I, a `I.1.2`;
- las garantías (art. 53), el Defensor del Pueblo (art. 54) y la suspensión (art. 55, con los
estados
  de alarma, excepción y sitio del art. 116), a `I.1.3`;
- la Corona (Título II, arts. 56 a 65), a `I.1.4`.

Dos decisiones de redacción de los patrones, dichas donde se leen:

- los artículos van **por número** (`_ARTS`) y no solo por institución: media oposición pregunta «el
  artículo 127.1», y sin ellos esa pregunta no dice de qué habla;
- las palabras que en el texto real aparecen escritas de dos maneras van con las **dos** formas
  (`autonómicas`/`autónomas`, `enseñanza`/`educación`). La normalización del proyecto quita los
  acentos, así que un patrón escrito con la variante que no está deja sin materia a todas las
  preguntas que usen la otra —pasó con «Comunidades Autónomas», que se quedaba fuera por un patrón
  que solo aceptaba «autonómicas»—.

Las preguntas que no se sitúan ni por su enunciado ni por el texto de sus hechos **no** acaban en un
cajón: van a la bandeja del propietario con su motivo (`Motivo.SIN_MATERIA_EN_EL_INDICE`).
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Los artículos de un título, como alternancia de números. Sirve para las preguntas que citan el
#: artículo y no la institución. Hay que aceptar `art` además de `articulo`: media oposición escribe
#: «art. 57 CE», y en el texto normalizado eso es `art 57`.
#:
#: Las cifras van con un `\d` opcional detrás del número **y** sin él, para que casen tanto
#: «artículo 127» como «artículo 127.1» (que se normaliza a `articulo 127 1`): el `\b` de después
#: del número ya los separa, pero el patrón tiene que reconocer el número entero y no la primera
#: cifra (`12` no es `127`).
_ARTS = {
    "preliminar": r"(articulos?|arts?) (1|2|3|4|5|6|7|8|9)\b",
    "t1": r"(articulos?|arts?) (1[0-9]|2[0-9]|3[0-9]|4[0-9]|5[0-5])\b",
    "corona": r"(articulos?|arts?) (5[6-9]|6[0-5])\b",
    "cortes": r"(articulos?|arts?) (6[6-9]|7[0-9]|8[0-9]|9[0-6])\b",
    "gobierno": r"(articulos?|arts?) (9[7-9]|10[0-7])\b",
    "relaciones": r"(articulos?|arts?) (10[8-9]|11[0-6])\b",
    "judicial": r"(articulos?|arts?) (11[7-9]|12[0-7])\b",
    "economia": r"(articulos?|arts?) (12[8-9]|13[0-6])\b",
    "territorial": r"(articulos?|arts?) (13[7-9]|14[0-9]|15[0-8])\b",
    "constitucional": r"(articulos?|arts?) (15[9]|16[0-5])\b",
    "reforma": r"(articulos?|arts?) (16[6-9])\b",
}

#: Las dos maneras de nombrar lo autonómico en el texto real: `autonómico`/`autonómica` (lo que
#: escribe la norma) y `autónomo`/`autónoma` (lo que escriben los enunciados). Un patrón que solo
#: acepte una de las dos deja fuera la mitad de las preguntas.
_AUTONOMICO = r"autonomic[oa]s?|autonom[oa]s?"

MATERIAS: tuple[Materia, ...] = (
    # --- I.1.1 La Constitución Española de 1978 ------------------------------------------------
    Materia(
        key="constitucion-caracteres",
        epigraph_code="I.1.1",
        title="La Constitución de 1978: caracteres, estructura, reforma y Tribunal Constitucional",
        resumen=(
            "Qué es la Constitución, cuándo se aprobó y entró en vigor, sus caracteres (norma "
            "suprema, rígida, escrita, consensuada), su estructura por títulos, los valores "
            "superiores del ordenamiento y los principios de la seguridad jurídica, el"
            "procedimiento "
            "de reforma de los artículos 166 a 169 y el Tribunal Constitucional como intérprete "
            "supremo (arts. 159 a 165)."
        ),
        patrones=(
            r"constitucion (espanola )?de 1978",
            r"\b1978\b",
            r"norma (suprema|fundamental)",
            r"caracter(es)? de la constitucion",
            r"estructura de la constitucion",
            r"revision constitucional",
            r"reforma (de la |agravada|ordinaria|constitucional)",
            r"poder constituyente",
            r"cortes constituyentes",
            r"referendum",
            r"disposiciones? (transitorias?|adicionales?|derogatorias?|final)",
            r"tribunal constitucional",
            r"recurso de inconstitucionalidad",
            r"cuestion de inconstitucionalidad",
            r"conflicto(s)? (de competencia|entre organos)",
            r"magistrado(s)? del tribunal constitucional",
            r"titulo x\b",
            r"disposicion adicional primera",
            r"valores superiores",
            r"seguridad juridica",
            r"publicidad de las normas",
            r"pluralismo politico",
            r"irretroactividad",
            r"potestad reglamentaria",
            r"(un )?reglamento(s)? (ilegal|es ilegal|no es ilegal|administrativos?)",
            r"norma(s)? (comunitaria|de la union|europea)",
            _ARTS["reforma"],
            _ARTS["constitucional"],
        ),
        patrones_debiles=(r"constitucion", r"reforma", r"titulo ix"),
        prioridad=10,
    ),
    Materia(
        key="titulo-preliminar",
        epigraph_code="I.1.1",
        title="Título Preliminar: los principios constitucionales (arts. 1 a 9)",
        resumen=(
            "Los principios del Título Preliminar: el Estado social y democrático de Derecho, la "
            "soberanía nacional, la forma política del Estado (la monarquía parlamentaria), la"
            "unidad "
            "y la autonomía, el castellano y las demás lenguas, la bandera, la capital, los"
            "partidos "
            "y sindicatos, las Fuerzas Armadas y los principios de legalidad y jerarquía normativa."
        ),
        patrones=(
            r"titulo preliminar",
            r"estado social y democratico",
            r"soberania nacional",
            r"monarquia parlamentaria",
            r"forma politica del estado",
            r"lengua(s)? (oficial|espanola|propias)",
            r"\bcastellano\b",
            r"bandera de espana",
            r"capital (del estado|de espana)",
            r"partidos? politicos?",
            r"sindicatos?",
            r"fuerzas armadas",
            r"jerarquia normativa",
            r"legalidad",
            r"irretroactividad",
            r"pluralismo politico",
            r"principios? (de la constitucion|constitucionales)",
            _ARTS["preliminar"],
        ),
        patrones_debiles=(r"principios", r"poderes publicos"),
        prioridad=11,
    ),
    Materia(
        key="cortes-generales",
        epigraph_code="I.1.1",
        title="Las Cortes Generales: composición y funciones (arts. 66 a 96)",
        resumen=(
            "El Congreso y el Senado: composición, elección, mandato, el estatuto de los "
            "parlamentarios, la elaboración de las leyes, los tratados internacionales, el Tribunal"
            ""
            "de Cuentas y las relaciones entre las dos Cámaras."
        ),
        patrones=(
            r"cortes generales",
            r"\bcongreso\b",
            r"\bsenado\b",
            r"camaras?",
            r"diputados?",
            r"senadores?",
            r"mesa del (congreso|senado)",
            r"junta de portavoces",
            r"grupos? parlamentarios?",
            r"diputacion permanente",
            r"comisiones? (legislativas|del congreso|del senado)",
            r"iniciativa legislativa",
            r"proposicion de ley",
            r"proyecto de ley",
            r"veto",
            r"tribunal de cuentas",
            r"tratados? (internacionales?|y convenios)",
            r"leyes organicas?",
            r"delegacion legislativa",
            r"estado de (alarma|excepcion|sitio)",
            r"investidura",
            r"cuestion de confianza",
            r"mocion de censura",
            r"mociones? alternativas?",
            r"representar al pueblo",
            r"reuniones? de parlamentarios",
            r"regimen electoral",
            r"ley electoral",
            r"sistema electoral",
            r"acuerdos? (adoptados|de la camara)",
            r"renovacion por terceras partes",
            r"disolucion de (las camaras|congreso|senado)",
            r"decreto de (la )?disolucion",
            r"juntas? electorales?",
            r"consentimiento del estado.*tratados",
            r"titulo iii\b",
            _ARTS["cortes"],
        ),
        patrones_debiles=(r"ley", r"camara", r"presupuestos"),
        prioridad=12,
    ),
    Materia(
        key="gobierno-y-administracion",
        epigraph_code="I.1.1",
        title="El Gobierno y la Administración (arts. 97 a 107)",
        resumen=(
            "El Gobierno: composición, nombramiento y cese del Presidente y de los ministros, sus "
            "funciones, la Administración pública y los principios de actuación, y el Consejo de "
            "Estado."
        ),
        patrones=(
            r"\bgobierno\b",
            r"presidente del gobierno",
            r"consejo de ministros",
            r"ministros?",
            r"vicepresidente",
            r"administracion(es)? (publicas?|general del estado)",
            r"consejo de estado",
            r"delegado del gobierno",
            r"subdelegado",
            r"cee",
            r"secretario(s)? general(es)?",
            r"subsecretario",
            r"direcciones? generales?",
            r"organos? superiores?",
            r"titulo iv\b",
            _ARTS["gobierno"],
        ),
        patrones_debiles=(r"gobierno", r"administracion", r"ministerio"),
        prioridad=13,
    ),
    Materia(
        key="relaciones-gobierno-cortes",
        epigraph_code="I.1.1",
        title="Relaciones entre el Gobierno y las Cortes (arts. 108 a 116)",
        resumen=(
            "La responsabilidad política del Gobierno ante el Congreso: la cuestión de confianza,"
            "la "
            "moción de censura, las interpelaciones y preguntas, y los estados de alarma, excepción"
            "y "
            "sitio."
        ),
        patrones=(
            r"mocion de censura",
            r"cuestion de confianza",
            r"responsabilidad politica",
            r"interpelacion",
            r"preguntas? (al gobierno|orales|escritas)",
            r"estado de (alarma|excepcion|sitio)",
            r"estados? de (alarma|excepcion|sitio)",
            r"declaracion del estado",
            r"decreto de (la )?disolucion",
            r"titulo v\b",
            _ARTS["relaciones"],
        ),
        patrones_debiles=(r"gobierno.*cortes",),
        prioridad=14,
    ),
    Materia(
        key="poder-judicial",
        epigraph_code="I.1.1",
        title="El Poder Judicial (arts. 117 a 127)",
        resumen=(
            "La justicia como poder del Estado: los principios de la jurisdicción, la independencia"
            ""
            "de los jueces y magistrados, el Consejo General del Poder Judicial, el Ministerio "
            "Fiscal, el jurado y la policía judicial."
        ),
        patrones=(
            r"poder judicial",
            r"consejo general del poder judicial",
            r"\bcgpj\b",
            r"jueces? y magistrados?",
            r"magistraturas?",
            r"ministerio fiscal",
            r"fiscal general del estado",
            r"tribunal supremo",
            r"jurisdiccion",
            r"independencia (de los jueces|judicial)",
            r"jurado",
            r"policia judicial",
            r"audiencia nacional",
            r"tribunales? superiores? de justicia",
            r"la justicia emana",
            r"emana la justicia",
            r"administracion de justicia",
            r"juzgados? y tribunales?",
            r"asociacion profesional de (jueces|la carrera judicial)",
            _ARTS["judicial"],
        ),
        patrones_debiles=(r"judicial", r"tribunal"),
        prioridad=15,
    ),
    Materia(
        key="economia-y-hacienda",
        epigraph_code="I.1.1",
        title="Economía y Hacienda (arts. 128 a 136)",
        resumen=(
            "La riqueza del país y su subordinación al interés general, la iniciativa pública en la"
            ""
            "economía, la potestad tributaria, los Presupuestos Generales del Estado, el patrimonio"
            ""
            "del Estado y el Tribunal de Cuentas."
        ),
        patrones=(
            r"hacienda( )?publica",
            r"potestad tributaria",
            r"tributos?",
            r"presupuestos generales del estado",
            r"deuda publica",
            r"patrimonio (del estado|nacional)",
            r"dominio publico",
            r"iniciativa (publica|privada) en la economia",
            r"planificacion economica",
            r"politica economica",
            r"modelo (economico|de )?",
            r"plusvalias?",
            r"accion urbanistica",
            _ARTS["economia"],
        ),
        patrones_debiles=(r"economia", r"presupuesto"),
        prioridad=16,
    ),
    Materia(
        key="organizacion-territorial",
        epigraph_code="I.1.1",
        title="La organización territorial del Estado (arts. 137 a 158)",
        resumen=(
            "Municipios, provincias y comunidades autónomas: la autonomía local, el acceso a la "
            "autonomía, los estatutos, las competencias del Estado y de las comunidades, la "
            "solidaridad, el fondo de compensación y los derechos históricos de los territorios "
            "forales."
        ),
        patrones=(
            rf"comunidades? ({_AUTONOMICO})",
            rf"\b{_AUTONOMICO}\b",
            r"organizacion territorial",
            r"estado (autonomico|de las autonomias)",
            r"estatutos? de autonomia",
            r"municipios?",
            r"provincias?",
            r"ayuntamiento",
            r"diputaciones? provinciales?",
            r"competencias? (del estado|autonomicas?|exclusivas?)",
            r"solidaridad (interterritorial|entre)",
            r"fondo de compensacion",
            r"islas? (baleares|canarias)",
            r"ceuta y melilla",
            r"convenios? (o acuerdos) entre comunidades",
            r"principio de solidaridad",
            r"regimen local",
            r"entidad(es)? local(es)?",
            r"territorios? forales?",
            r"derechos historicos",
            r"nivel minimo en la prestacion",
            r"titulo viii\b",
            _ARTS["territorial"],
        ),
        patrones_debiles=(r"autonomic", r"territorial"),
        prioridad=17,
    ),
    # --- I.1.2 Derechos y deberes fundamentales ------------------------------------------------
    Materia(
        key="derechos-igualdad-nacionalidad",
        epigraph_code="I.1.2",
        title="Dignidad, igualdad y nacionalidad (arts. 10 a 14)",
        resumen=(
            "La dignidad de la persona y el libre desarrollo de la personalidad, los derechos "
            "inherentes, la interpretación conforme a los tratados, la mayoría de edad, la igualdad"
            ""
            "ante la ley y la nacionalidad y la extranjería."
        ),
        patrones=(
            r"dignidad de la persona",
            r"libre desarrollo de la personalidad",
            r"igualdad ante la ley",
            r"articulo 14",
            r"mayoria de edad",
            r"nacionalidad",
            r"extranjeros?",
            r"extranjeria",
            r"derechos? inviolables",
            r"declaracion universal de los derechos humanos",
            r"tratados? y acuerdos internacionales.*derechos",
        ),
        patrones_debiles=(r"dignidad", r"igualdad"),
        prioridad=20,
    ),
    Materia(
        key="derechos-seccion-primera",
        epigraph_code="I.1.2",
        title="Derechos fundamentales y libertades públicas (arts. 15 a 29)",
        resumen=(
            "La Sección 1.ª del capítulo II: el derecho a la vida y a la integridad, la libertad "
            "ideológica y religiosa, la libertad y la seguridad, la intimidad y el secreto de las "
            "comunicaciones, la libertad de residencia y circulación, la libertad de expresión e "
            "información, el derecho de reunión y manifestación, el de asociación, el de "
            "participación política, el de petición, la tutela judicial, la legalidad penal, el"
            "honor "
            "y la educación."
        ),
        patrones=(
            r"derechos? fundamentales?",
            r"libertades? publicas?",
            r"seccion 1",
            r"derecho a la vida",
            r"integridad (fisica|moral)",
            r"tratos? inhumanos?",
            r"pena de muerte",
            r"tortura",
            r"libertad (ideologica|religiosa|de cultos)",
            r"libertad y seguridad",
            r"intimidad",
            r"secreto de las comunicaciones",
            r"libertad de (expresion|informacion|residencia|circulacion)",
            r"derecho de reunion",
            r"manifestacion",
            r"derecho de asociacion",
            r"\basociaciones?\b",
            r"participacion (politica|en los asuntos publicos)",
            r"derecho de peticion",
            r"tutela judicial efectiva",
            r"legalidad penal",
            r"no constituya delito",
            r"sanciones? (administrativas?|privativas?)",
            r"honor.*intimidad.*propia imagen",
            r"derecho a la educacion",
            r"ensenanza",
            r"obligatoria y gratuita",
            r"libertad de catedra",
            r"detencion preventiva",
            r"\bhabeas corpus\b",
            r"asilo",
            r"domicilio",
            r"inviolabilidad del domicilio",
            r"religion( estatal)?",
            r"libertad de conciencia",
            r"flagrante delito",
            r"entrada en el domicilio",
            r"creacion de centros docentes",
        ),
        patrones_debiles=(r"derecho", r"libertad", r"libertades", r"titulo i"),
        prioridad=21,
    ),
    Materia(
        key="derechos-deberes-seccion-segunda",
        epigraph_code="I.1.2",
        title="Derechos y deberes de los ciudadanos (arts. 30 a 38)",
        resumen=(
            "La Sección 2.ª del capítulo II: la defensa de España, el sistema tributario, el "
            "matrimonio, la propiedad privada y la herencia, la libertad de empresa, el derecho al "
            "trabajo, la negociación colectiva, la libertad sindical y el derecho de huelga."
        ),
        patrones=(
            r"seccion 2",
            r"derechos? y deberes? de los ciudadanos",
            r"defensa de espana",
            r"sistema tributario",
            r"matrimonio",
            r"propiedad privada",
            r"herencia",
            r"libertad de empresa",
            r"economia de mercado",
            r"derecho al trabajo",
            r"negociacion colectiva",
            r"libertad sindical",
            r"derecho de huelga",
            r"conflicto colectivo",
            r"colegios profesionales",
            r"obligaciones militares",
            r"servicio militar",
            r"objecion de conciencia",
            r"prestacion social sustitutoria",
            r"grave riesgo.*catastrofe",
        ),
        patrones_debiles=(r"deberes", r"trabajo"),
        prioridad=22,
    ),
    Materia(
        key="principios-rectores",
        epigraph_code="I.1.2",
        title="Principios rectores de la política social y económica (arts. 39 a 52)",
        resumen=(
            "El capítulo III del Título I: la protección de la familia y de los hijos, la Seguridad"
            ""
            "Social, la salud, el acceso a la cultura, el medio ambiente, la vivienda, la juventud,"
            ""
            "los minusválidos, los consumidores, las organizaciones profesionales y la tercera"
            "edad."
        ),
        patrones=(
            r"principios? rectores",
            r"politica social y economica",
            r"proteccion (de la familia|a la familia|de los hijos)",
            r"seguridad social",
            r"proteccion de la salud",
            r"acceso a la cultura",
            r"medio ambiente",
            r"vivienda",
            r"juventud",
            r"disminuidos?",
            r"minusvalidos?",
            r"consumidores? y usuarios?",
            r"organizaciones? profesionales?",
            r"tercera edad",
            r"patrimonio historico",
            r"pleno empleo",
        ),
        patrones_debiles=(r"proteccion", r"social"),
        prioridad=23,
    ),
    # --- I.1.3 Su garantía y suspensión --------------------------------------------------------
    Materia(
        key="garantias-y-defensor",
        epigraph_code="I.1.3",
        title="La garantía de las libertades: art. 53 y el Defensor del Pueblo",
        resumen=(
            "Cómo se protegen los derechos: la reserva de ley, el recurso de amparo ante el"
            "Tribunal "
            "Constitucional, el procedimiento preferente y sumario, los principios del capítulo III"
            "y "
            "el Defensor del Pueblo como alto comisionado de las Cortes."
        ),
        patrones=(
            r"garantia(s)? de (las libertades|los derechos)",
            r"articulo 53",
            r"recurso de amparo",
            r"tutela de (las libertades|los derechos)",
            r"procedimiento (preferente|sumario)",
            r"defensor del pueblo",
            r"alto comisionado de las cortes",
            r"reserva de ley",
            r"contenido esencial",
        ),
        patrones_debiles=(r"garantia", r"amparo", r"defensor"),
        prioridad=30,
    ),
    Materia(
        key="suspension-de-derechos",
        epigraph_code="I.1.3",
        title="La suspensión de los derechos y los estados excepcionales",
        resumen=(
            "Art. 55: qué derechos pueden suspenderse, en qué supuestos (bandas armadas o elementos"
            ""
            "terroristas), la suspensión general durante los estados de alarma, excepción y sitio,"
            "y "
            "el control de la declaración."
        ),
        patrones=(
            r"suspension (de|general de) (los )?derechos",
            r"articulo 55",
            r"bandas? armadas?",
            r"elementos? terroristas?",
            r"suspension individual",
            r"estado de excepcion",
            r"estado de sitio",
            r"ley organica 4 1981",
            r"derechos? (suspendidos?|suspendibles)",
        ),
        patrones_debiles=(r"suspension", r"excepcional"),
        prioridad=31,
    ),
    # --- I.1.4 La Corona ----------------------------------------------------------------------
    Materia(
        key="corona",
        epigraph_code="I.1.4",
        title="La Corona: el Rey y sus funciones (arts. 56 a 65)",
        resumen=(
            "El Rey como Jefe del Estado y símbolo de su unidad: sus funciones, la sucesión y la "
            "regencia, la tutela del Rey menor, el refrendo de sus actos, la Casa de Su Majestad,"
            "la "
            "dotación, la Familia Real y el título de Príncipe de Asturias."
        ),
        patrones=(
            r"\bcorona\b",
            r"\brey\b|\breina\b",
            r"jefe del estado",
            r"familia real",
            r"registro civil",
            r"casa de su majestad",
            r"sucesion (a la corona|al trono|en el trono)",
            r"regencia",
            r"tutela del rey",
            r"refrendo",
            r"principe de asturias",
            r"heredero de la corona",
            r"abdicacion",
            r"proclamacion",
            r"inviolabilidad del rey",
            r"consorte",
            r"indultos?",
            r"infantes?",
            r"hijos? del rey",
            r"tratamiento.*(infantes?|rey|reina|principe)",
            r"titulos?.*tratamientos?.*honores?",
            r"orden(es)? (civil|del merito)",
            _ARTS["corona"],
        ),
        patrones_debiles=(r"monarquia", r"jefe del estado", r"titulo ii"),
        prioridad=40,
    ),
)

#: El orden en que se **enseña** el índice: el de la norma (Título Preliminar, Título I por
#: capítulos, la garantía, la suspensión y la Corona), no el de reparto.
ORDEN: tuple[str, ...] = (
    "constitucion-caracteres",
    "titulo-preliminar",
    "cortes-generales",
    "gobierno-y-administracion",
    "relaciones-gobierno-cortes",
    "poder-judicial",
    "economia-y-hacienda",
    "organizacion-territorial",
    "derechos-igualdad-nacionalidad",
    "derechos-seccion-primera",
    "derechos-deberes-seccion-segunda",
    "principios-rectores",
    "garantias-y-defensor",
    "suspension-de-derechos",
    "corona",
)

__all__ = ["MATERIAS", "ORDEN"]
