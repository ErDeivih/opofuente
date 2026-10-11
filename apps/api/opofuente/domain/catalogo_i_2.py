"""El catálogo de materias de I.2 (Las Cortes Generales, el Tribunal Constitucional y el Defensor
del Pueblo).

I.2 es un tema **normativo**: el índice sigue la estructura de la norma. Sus tres epígrafes
oficiales son las Cortes Generales, el Tribunal Constitucional y el Defensor del Pueblo, así que:

- lo que la Constitución dice de las Cámaras (Título III, arts. 66 a 96) va a `I.2.1`, repartido por
  lo que cada hecho **afirma**: cómo se componen (`cortes-composicion`), cómo se organizan y
  funcionan (`cortes-organizacion`), qué les toca (`cortes-funciones`) y cómo hacen las leyes
  (`cortes-procedimiento-legislativo`);
- el Tribunal Constitucional (arts. 159 a 165 y su Ley Orgánica 2/1979) va a `I.2.2`;
- el Defensor del Pueblo (art. 54 y la Ley Orgánica 3/1981) va a `I.2.3`.

**Y una decisión de contenido que se dice donde se lee**: cuando este tema se clasificó, a sus
preguntas cayeron también preguntas de otras partes de la Constitución (la Corona, el Gobierno, los
derechos, la organización territorial, el Poder Judicial y la Ley 19/2013 de transparencia) —se
midió sobre las 685 preguntas del tema y son del orden de una de cada tres—. Como el alumno estudia
por temas y esas preguntas **caen en este bloque**, tienen su apartado propio (`corona`,
`gobierno-y-administracion`, `derechos-y-garantias`, `organizacion-territorial-y-justicia` y
`transparencia`) y **no** un cajón de «otros»: un cajón mezclaría el régimen de la moción de censura
con el de la sucesión a la Corona, que es justo lo que el §2.1.1 prohíbe. Lo que no case con nada sí
acaba en el cajón de su epígrafe, que existe precisamente para eso.

Dos decisiones de redacción de los patrones, las mismas que en I.1 y por el mismo motivo:

- los artículos van **por número** (`_ARTS`) y no solo por institución: media oposición pregunta «el
  artículo 159 de la Constitución», y sin el número esa pregunta no dice de qué habla;
- las palabras que en el texto real aparecen escritas de dos maneras van con las **dos** formas
  (`autonómico`/`autónomo`, `reglamento`/`reglamentos`). La normalización del proyecto quita los
  acentos, así que un patrón escrito con la variante que no está deja sin materia a todas las
  preguntas que usen la otra.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Los artículos de la Constitución, por bloque, como alternancia de números. Es lo que sitúa las
#: preguntas que citan el artículo y no la institución. Hay que aceptar `art` además de `articulo`:
#: media oposición escribe «art. 159 CE», y en el texto normalizado eso es `art 159`.
#:
#: Las cifras van con un `\d` opcional detrás del número **y** sin él, para que casen tanto
#: «artículo 159» como «artículo 159.1» (que se normaliza a `articulo 159 1`).
_ARTS = {
    # Título II, la Corona (56 a 65).
    "corona": r"(articulos?|arts?) (5[6-9]|6[0-5])\b",
    # Título III, las Cortes Generales (66 a 96).
    "cortes": r"(articulos?|arts?) (6[6-9]|7[0-9]|8[0-9]|9[0-6])\b",
    # Título IV, el Gobierno y la Administración (97 a 107).
    "gobierno": r"(articulos?|arts?) (9[7-9]|10[0-7])\b",
    # Título V, las relaciones entre el Gobierno y las Cortes (108 a 116).
    "relaciones": r"(articulos?|arts?) (10[8-9]|11[0-6])\b",
    # Título VI, el Poder Judicial (117 a 127).
    "judicial": r"(articulos?|arts?) (11[7-9]|12[0-7])\b",
    # Título VIII, la organización territorial (137 a 158).
    "territorial": r"(articulos?|arts?) (13[7-9]|14[0-9]|15[0-8])\b",
    # Título IX, el Tribunal Constitucional (159 a 165) y Título X, la reforma (166 a 169).
    "constitucional": r"(articulos?|arts?) (159|16[0-5])\b",
    "reforma": r"(articulos?|arts?) (16[6-9])\b",
}

#: Las dos maneras de nombrar lo autonómico en el texto real: `autonómico`/`autonómica` (lo que
#: escribe la norma) y `autónomo`/`autónoma` (lo que escriben los enunciados). Un patrón que solo
#: acepte una de las dos deja fuera la mitad de las preguntas.
_AUTONOMICO = r"autonomic[oa]s?|autonom[oa]s?"

#: Las dos maneras de nombrar al Parlamento y a sus miembros: la norma escribe «Cámaras» y
#: «Diputados», y media oposición escribe «Cámara baja», «Congreso» o «Senado» indistintamente.
_CAMARAS = r"\bcamaras?\b|\bcongreso\b|\bsenado\b|\bcortes\b"

MATERIAS: tuple[Materia, ...] = (
    # --- I.2.1 Las Cortes Generales ------------------------------------------------------------
    Materia(
        key="cortes-composicion",
        epigraph_code="I.2.1",
        title="Qué son las Cortes Generales y cómo se componen",
        resumen=(
            "Las Cortes Generales como órgano de representación del pueblo español: su carácter "
            "bicameral, la composición del Congreso (número de diputados, circunscripción, sistema "
            "electoral proporcional) y del Senado (senadores por provincia, por las islas y por "
            "las "
            "Comunidades Autónomas). El mandato de los parlamentarios, su elección por sufragio, "
            "el "
            "estatuto del parlamentario (inviolabilidad, inmunidad, incompatibilidades y "
            "prerrogativas) y el régimen electoral."
        ),
        patrones=(
            _CAMARAS,
            r"cortes generales",
            r"diputados?",
            # Ojo con el plural: `senadores?` casa «senadore» y «senadores», **no** «senador».
            # Medido en el ensayo del reparto: dejaba fuera «Corresponderá un Senador a».
            r"senador(es)?\b",
            r"camara (alta|baja)",
            r"representacion (del pueblo|territorial|popular)",
            r"dos camaras|bicameral",
            r"circunscripcion",
            r"sufragio",
            r"sistema electoral|regimen electoral|ley electoral",
            r"juntas? electorales?",
            r"se compone de|se componen de|cuantos diputados|cuantos senadores",
            r"elegibles? por cada",
            r"inviolabilidad",
            r"inmunidad",
            r"incompatibilidades?",
            r"prerrogativas?",
            r"fuero",
            r"juramento o promesa",
            r"mandato (de los|del|parlamentario)",
            r"renovacion (del congreso|de las camaras|por mitades)",
            r"titulo iii\b",
            r"haciendas? locales?",
            r"riqueza del pais",
            r"referendum",
            r"\bceuta\b|\bmelilla\b",
            _ARTS["cortes"],
        ),
        patrones_debiles=(r"eleccion", r"voto", r"escanos", r"pueblo"),
        prioridad=10,
    ),
    Materia(
        key="cortes-organizacion",
        epigraph_code="I.2.1",
        title="Organización y funcionamiento de las Cámaras",
        resumen=(
            "Cómo funcionan las Cámaras por dentro: el Pleno y las Comisiones, la Mesa y la Junta "
            "de "
            "Portavoces, los Grupos Parlamentarios, los Presidentes de las Cámaras, las sesiones "
            "(ordinarias, extraordinarias y conjuntas), el quórum y las mayorías, la publicidad de "
            "las sesiones, los Reglamentos de las Cámaras, la Diputación Permanente y la "
            "disolución "
            "de las Cámaras."
        ),
        patrones=(
            r"\bpleno\b|\bplenos\b",
            r"comisiones? (legislativas|permanentes|no legislativas|de investigacion|mixtas|del "
            r"congreso|del senado)",
            r"mesa del (congreso|senado)|la mesa\b",
            r"junta de portavoces",
            r"grupos? parlamentarios?",
            r"presidente (del congreso|del senado|de la camara)",
            r"sesiones? (ordinarias?|extraordinarias?|conjuntas?|del pleno)",
            r"periodo de sesiones|periodos de sesiones",
            r"quorum",
            r"mayoria (absoluta|simple|de tres quintos|de dos tercios|cualificada)",
            r"reglamento (del congreso|del senado|de las camaras|de la camara)",
            r"diputacion permanente",
            r"diputaciones permanentes",
            r"disolucion (de las camaras|anticipada|del congreso|del senado)",
            r"decreto de (la )?disolucion",
            r"convocatoria extraordinaria",
            r"expirado el mandato",
            r"funcionaran en pleno",
            r"publicidad de las sesiones|sesiones seran publicas",
            r"orden del dia",
            r"comparecencia",
            _ARTS["cortes"],
        ),
        patrones_debiles=(r"sesion", r"comision", r"pleno"),
        prioridad=11,
    ),
    Materia(
        key="cortes-funciones",
        epigraph_code="I.2.1",
        title="Las atribuciones de las Cortes Generales",
        resumen=(
            "Lo que las Cortes hacen: la potestad legislativa, la aprobación de los presupuestos, "
            "el "
            "control de la acción del Gobierno (interpelaciones, preguntas, comisiones de "
            "investigación), la autorización de tratados internacionales, la declaración de los "
            "estados de alarma, excepción y sitio, el nombramiento de los órganos que les "
            "corresponden (Tribunal Constitucional, Defensor del Pueblo, vocales del Consejo "
            "General "
            "del Poder Judicial) y las demás atribuciones del artículo 66."
        ),
        patrones=(
            r"atribuciones? de las cortes|funciones? de las cortes",
            r"potestad legislativa",
            r"control (de la accion|del gobierno|politico)",
            r"interpelacion",
            r"preguntas? (al gobierno|orales|escritas|de los diputados)",
            r"comision de investigacion",
            r"presupuestos generales del estado",
            r"tratados?",
            r"consentimiento del estado",
            r"autorizacion (previa )?de las cortes",
            r"estados? de (alarma|excepcion|sitio)",
            r"declaracion del estado",
            r"no es funcion de las cortes|no es atribucion",
            r"nombramiento de los miembros del tribunal constitucional",
            r"defensor del pueblo es elegido|propuesta de defensor",
            r"consejo general del poder judicial.*cortes",
            r"leyes? de (bases|delegacion|autorizacion)",
            r"no puede en ningun caso",
            _ARTS["cortes"],
            _ARTS["relaciones"],
        ),
        patrones_debiles=(r"control", r"presupuesto", r"autoriza"),
        prioridad=12,
    ),
    Materia(
        key="cortes-procedimiento-legislativo",
        epigraph_code="I.2.1",
        title="La elaboración de las leyes y la reforma de la Constitución",
        resumen=(
            "El procedimiento legislativo: la iniciativa legislativa (proyectos del Gobierno, "
            "proposiciones de ley, iniciativa popular), la tramitación en el Congreso y en el "
            "Senado, las enmiendas, el veto o la enmienda del Senado y su superación por el "
            "Congreso, la sanción y promulgación por el Rey, los supuestos de tramitación especial "
            "(leyes orgánicas, de bases y de delegación legislativa), el decreto-ley y el "
            "decreto legislativo, y los dos procedimientos de reforma constitucional de los "
            "artículos 167 y 168."
        ),
        patrones=(
            r"iniciativa legislativa",
            r"proyecto de ley|proposiciones? de ley",
            r"tramitacion",
            r"enmiendas?",
            r"\bveto\b",
            r"rechazo por el senado",
            r"promulgacion|sancion(ados?|arse)? por el rey|sancion real",
            r"leyes? organicas?",
            r"delegacion legislativa|leyes? de delegacion|leyes? de bases",
            r"decreto ley|decretos? leyes|real decreto ley",
            r"decreto legislativo|texto refundido|texto articulado",
            r"legislacion delegada",
            r"reforma de la constitucion|revision constitucional",
            r"procedimiento de reforma",
            r"disolucion.*reforma",
            r"ley de presupuestos",
            r"plazo de que dispone el senado|plazo de dos meses|plazo de veinte dias",
            r"urgencia|tramitacion urgente",
            _ARTS["cortes"],
            _ARTS["reforma"],
        ),
        patrones_debiles=(r"ley", r"enmienda", r"procedimiento"),
        prioridad=13,
    ),
    Materia(
        key="corona",
        epigraph_code="I.2.1",
        title="La Corona: el Rey, la sucesión y la Regencia",
        resumen=(
            "El Rey como Jefe del Estado: su posición arbitral y moderadora, la sucesión a la "
            "Corona "
            "y las Cortes, la Regencia y la tutela del Rey menor, el juramento, el refrendo de sus "
            "actos y las funciones que le atribuye el artículo 62. Va aquí porque este tema recoge "
            "las preguntas sobre la Corona que se clasificaron con las de las Cámaras."
        ),
        patrones=(
            r"\brey\b|\breina\b",
            r"\bcorona\b",
            r"regencia|\bregente",
            r"principe (heredero|de asturias)",
            r"heredero|sucesion (a la corona|al trono)|linea de sucesion",
            r"jefe del estado",
            r"abdicacion|renuncia.*corona",
            r"tutela del rey|tutela del monarca",
            r"consorte",
            r"refrendo|refrendar",
            r"funciones del rey|corresponde al rey",
            r"juramento.*rey|prestaran el mismo juramento",
            r"inviolable.*rey|no esta sujeto a responsabilidad",
            r"casa real|patrimonio del estado.*rey",
            r"mando supremo de las fuerzas armadas",
            _ARTS["corona"],
        ),
        patrones_debiles=(r"monarquia", r"jefe"),
        prioridad=20,
    ),
    Materia(
        key="gobierno-y-administracion",
        epigraph_code="I.2.1",
        title="El Gobierno, la Administración y el empleo público",
        resumen=(
            "El Gobierno: composición, nombramiento y cese del Presidente y de los ministros, sus "
            "funciones y su relación con las Cámaras (la investidura, la cuestión de confianza y "
            "la "
            "moción de censura), la responsabilidad criminal de los miembros del Gobierno, los "
            "principios de actuación de la Administración (artículo 103), el Consejo de Estado y "
            "el "
            "empleo público."
        ),
        patrones=(
            r"presidente del gobierno",
            r"\bgobierno\b",
            r"consejo de ministros",
            r"ministros?|vicepresidente",
            r"mocion de censura|mociones? de censura|mociones alternativas",
            r"cuestion de confianza|investidura",
            r"otorgamiento de la confianza",
            r"nombramiento del presidente",
            r"propuesta del candidato",
            r"cese del gobierno|dimision",
            r"responsabilidad criminal.*(ministro|presidente|diputados)",
            r"responsabilidad criminal",
            r"potestad reglamentaria",
            r"titulo iv\b",
            r"consejo de seguridad nacional",
            r"personal funcionario|funcionarios? (de carrera|publicos?)",
            r"jubilacion",
            r"principios? de (actuacion|la actuacion)",
            r"administracion(es)? (publicas?|general del estado)",
            r"consejo de estado",
            r"delegado del gobierno|subdelegado",
            r"empleo publico|funcion publica|personal al servicio",
            r"ley 50 1997|ley del gobierno",
            r"ley 40 2015|ley 39 2015",
            r"organizacion (y funcionamiento )?del sector publico",
            r"acoso sexual",
            _ARTS["gobierno"],
            _ARTS["relaciones"],
        ),
        patrones_debiles=(r"gobierno", r"administracion", r"ministerio"),
        prioridad=21,
    ),
    Materia(
        key="derechos-y-garantias",
        epigraph_code="I.2.1",
        title="Los derechos, sus garantías y la tutela judicial",
        resumen=(
            "Los derechos y libertades que aparecen en las preguntas de este tema: la igualdad "
            "ante "
            "la ley, el derecho de reunión, la tutela judicial efectiva, los derechos que son "
            "susceptibles de recurso de amparo según el artículo 53.2, la indemnización por "
            "funcionamiento anormal de los servicios públicos, la Seguridad Social, los principios "
            "rectores de la política social y económica (la riqueza del país, la creación de "
            "centros docentes, los trabajadores españoles en el extranjero), los símbolos del "
            "Estado y las Fuerzas y Cuerpos de Seguridad. Es también donde se recoge lo que el "
            "Título Preliminar dice de los poderes públicos."
        ),
        patrones=(
            r"derecho de (reunion|asociacion|manifestacion|huelga|peticion)",
            r"igualdad de los (espanoles|ciudadanos)",
            r"tutela (judicial )?efectiva",
            r"articulo 53|art 53",
            r"recurso de amparo.*derecho|derechos.*recurso de amparo",
            r"no se encuentra protegido por el recurso de amparo",
            r"indemnizacion.*(estado|funcionamiento)",
            r"funcionamiento anormal",
            r"seguridad social",
            r"fuerzas y cuerpos de seguridad",
            r"policia|guardia civil",
            r"hacienda publica|tributos",
            r"los poderes publicos|corresponde a los podes publicos",
            r"riqueza del pais",
            r"creacion de centros docentes",
            r"trabajadores espanoles en el extranjero",
            r"bandera de espana|símbolos? del estado",
            r"la ley.*segun la constitucion",
            r"administracion.*sometida a la ley",
            r"proteccion de la salud|consumidores|medio ambiente",
            r"derecho a la (vida|libertad|intimidad|educacion|trabajo)",
            r"libertad de (expresion|informacion|catedra|religion)",
            r"libertad personal|detencion",
            r"participacion (politica|en los asuntos publicos)",
        ),
        patrones_debiles=(r"derecho", r"libertad", r"tutela", r"poderes publicos"),
        prioridad=22,
    ),
    Materia(
        key="organizacion-territorial-y-justicia",
        epigraph_code="I.2.1",
        title="La organización territorial del Estado y el Poder Judicial",
        resumen=(
            "El Estado de las Autonomías: las Comunidades Autónomas, sus Estatutos, las "
            "competencias del Estado y de las Comunidades, la solidaridad interterritorial, las "
            "provincias, los municipios y la autonomía local. Y el Poder Judicial: los principios "
            "de la justicia, el Consejo General del Poder Judicial, el Tribunal Supremo, el "
            "Ministerio Fiscal y la policía judicial."
        ),
        patrones=(
            _AUTONOMICO,
            r"comunidades? autonomas?",
            r"estatutos? de autonomia",
            r"\bestatutos?\b",
            r"nacionalidades? y regiones",
            r"provincias?|municipios?|entidades? locales",
            r"autonomia local|regimen local",
            r"solidaridad (interterritorial|entre)",
            r"fondo de compensacion",
            r"transferencias? y delegaciones?",
            r"competencias? (exclusivas?|concurrentes|compartidas)",
            r"convenio de (conferencia sectorial|colaboracion)",
            r"poder judicial",
            r"consejo general del poder judicial",
            r"vocales?",
            r"tribunal supremo",
            r"ministerio fiscal|fiscales?",
            r"jueces? y magistrados?",
            r"policia judicial",
            r"justicia (gratuita|como poder)",
            r"unidad jurisdiccional|independencia judicial",
            _ARTS["judicial"],
            _ARTS["territorial"],
        ),
        patrones_debiles=(r"territorio", r"justicia", r"competencia"),
        prioridad=23,
    ),
    Materia(
        key="transparencia",
        epigraph_code="I.2.1",
        title="La transparencia y el buen gobierno (Ley 19/2013)",
        resumen=(
            "La Ley 19/2013, de transparencia, acceso a la información pública y buen gobierno: la "
            "publicidad activa, el derecho de acceso a la información, el Consejo de Transparencia "
            "y "
            "Buen Gobierno y el régimen de infracciones. Va aquí porque las preguntas de "
            "transparencia que cita este tema se clasificaron con las de las Cámaras."
        ),
        patrones=(
            r"ley 19 2013",
            r"transparencia",
            r"buen gobierno",
            r"publicidad activa",
            r"acceso a la informacion publica",
            r"consejo de transparencia",
            r"portal de la transparencia",
            r"reutilizacion de la informacion",
            r"informacion publica",
            r"gobierno abierto",
            r"datos abiertos",
            r"rendicion de cuentas",
        ),
        patrones_debiles=(r"transparencia", r"informacion"),
        prioridad=24,
    ),
    Materia(
        key="cortes-otros",
        epigraph_code="I.2.1",
        title="Otras cuestiones que caen en este tema",
        resumen=(
            "Lo que cae en las preguntas de este tema y no es de ninguna de las materias "
            "anteriores: "
            "se recoge aquí en vez de perderlo, para que ninguna pregunta se quede sin un apartado "
            "donde estudiarla."
        ),
        patrones=(),
        prioridad=29,
    ),
    # --- I.2.2 El Tribunal Constitucional ------------------------------------------------------
    Materia(
        key="tc-naturaleza-y-composicion",
        epigraph_code="I.2.2",
        title="El Tribunal Constitucional: naturaleza, composición y magistrados",
        resumen=(
            "El Tribunal Constitucional como intérprete supremo de la Constitución: su naturaleza "
            "y "
            "jurisdicción, su independencia, la composición de sus doce magistrados y quién los "
            "propone (Congreso, Senado, Gobierno y Consejo General del Poder Judicial), el "
            "nombramiento por el Rey, el mandato de nueve años y su renovación por terceras "
            "partes, "
            "el estatuto de sus magistrados (inamovilidad, incompatibilidades), el Presidente y el "
            "Vicepresidente y su sede."
        ),
        patrones=(
            r"tribunal constitucional",
            r"\blotc\b",
            r"ley organica 2 1979",
            r"magistrados? (del tribunal constitucional|del tc)",
            r"se compone de.*(miembros|magistrados)|doce miembros",
            r"designados? por periodos|nueve anos",
            r"nombrados? por el rey",
            r"propone el congreso|propone el senado|propone el gobierno|consejo general del poder "
            r"judicial.*propone",
            r"presidente del tribunal constitucional",
            r"vicepresidente del tribunal constitucional",
            r"interprete supremo",
            r"jurisdiccion en todo el territorio",
            r"inamovilidad.*magistrados",
            r"sede del tribunal constitucional",
            r"pleno|sala(s)? (primera|segunda)|secciones del tribunal",
            _ARTS["constitucional"],
        ),
        patrones_debiles=(r"tribunal constitucional", r"magistrado"),
        prioridad=10,
    ),
    Materia(
        key="tc-atribuciones",
        epigraph_code="I.2.2",
        title="Lo que conoce el Tribunal Constitucional: recursos y conflictos",
        resumen=(
            "Las competencias del Tribunal Constitucional: el recurso de inconstitucionalidad y la "
            "cuestión de inconstitucionalidad, el recurso de amparo y quién puede interponerlo, "
            "los "
            "conflictos entre el Estado y las Comunidades Autónomas y entre órganos "
            "constitucionales, los conflictos en defensa de la autonomía local, el control previo "
            "de "
            "los tratados internacionales y las demás atribuciones del artículo 161."
        ),
        patrones=(
            r"recurso de inconstitucionalidad",
            r"cuestion de inconstitucionalidad",
            r"cuesti[oó]n(es)? de inconstitucionalidad",
            r"recurso de amparo",
            r"\bamparo\b",
            r"legitimacion para (interponer|acudir)",
            r"puede interponer|no puede interponer",
            r"conflictos? (de competencia|de atribuciones|entre)",
            r"conflicto en defensa de la autonomia local",
            r"control previo.*tratados",
            r"tratados? internacionales.*constitucional",
            r"autocuesti[oó]n",
            r"tribunal constitucional entendera|es competente para conocer",
            r"recurso previo",
            r"impugnacion.*comunidad",
            _ARTS["constitucional"],
        ),
        patrones_debiles=(r"inconstitucionalidad", r"amparo", r"conflicto"),
        prioridad=11,
    ),
    Materia(
        key="tc-sentencias-y-efectos",
        epigraph_code="I.2.2",
        title="Las sentencias del Tribunal Constitucional y sus efectos",
        resumen=(
            "Qué produce una sentencia del Tribunal Constitucional: su valor de cosa juzgada, su "
            "eficacia frente a todos, los efectos de la declaración de inconstitucionalidad de una "
            "ley (nulidad y sus límites), los votos particulares, la ejecución de sus "
            "resoluciones, "
            "el recurso de amparo como vía previa y la reforma constitucional."
        ),
        patrones=(
            r"sentencias? del tribunal constitucional",
            r"contra las sentencias del tribunal constitucional",
            r"valor de cosa juzgada",
            r"efectos? de la (declaracion de inconstitucionalidad|sentencia)",
            r"declaracion de inconstitucionalidad",
            r"nulidad de (la ley|los preceptos)",
            r"votos particulares",
            r"ejecucion de (las )?(resoluciones|sentencias)",
            r"publicacion en el boletin oficial",
            r"reforma constitucional.*tribunal",
            r"control previo de inconstitucionalidad",
            r"no cabe recurso|no se puede interponer",
            _ARTS["constitucional"],
            _ARTS["reforma"],
        ),
        patrones_debiles=(r"sentencia", r"efectos"),
        prioridad=12,
    ),
    Materia(
        key="tc-otros",
        epigraph_code="I.2.2",
        title="Otras cuestiones del Tribunal Constitucional que caen en este tema",
        resumen=(
            "Lo que cae en las preguntas de este epígrafe y no es de ninguna de las materias "
            "anteriores."
        ),
        patrones=(),
        prioridad=19,
    ),
    # --- I.2.3 El Defensor del Pueblo ---------------------------------------------------------
    Materia(
        key="defensor-del-pueblo",
        epigraph_code="I.2.3",
        title="El Defensor del Pueblo",
        resumen=(
            "El Defensor del Pueblo como alto comisionado de las Cortes Generales: su elección por "
            "el Congreso y el Senado, el mandato de cinco años, sus competencias (supervisión de "
            "la "
            "Administración, las quejas de los ciudadanos y su plazo, la facultad de interponer el "
            "recurso de amparo y de promover el de inconstitucionalidad), sus informes y las "
            "figuras análogas autonómicas (Ley Orgánica 3/1981)."
        ),
        patrones=(
            r"defensor del pueblo",
            r"ley organica 3 1981",
            r"\bqueja\b|\bquejas\b",
            r"alto comisionado",
            r"supervisar.*administracion|supervision de la administracion",
            r"informe anual.*cortes",
            r"podra dirigirse al defensor",
            r"plazo.*queja",
            r"responsabilidad (civil|penal).*defensor",
            r"defensor del pueblo.*elegido|elegido por.*cortes",
            r"adjunto(s)? del defensor",
        ),
        patrones_debiles=(r"defensor", r"queja"),
        prioridad=10,
    ),
    Materia(
        key="defensor-otros",
        epigraph_code="I.2.3",
        title="Otras cuestiones que caen en el epígrafe del Defensor del Pueblo",
        resumen=(
            "Lo que cae en las preguntas de este epígrafe y no es de la materia del Defensor del "
            "Pueblo."
        ),
        patrones=(),
        prioridad=11,
    ),
)

#: El orden en que se **enseña** el índice: el de la norma (las Cámaras, el Tribunal Constitucional
#: y el Defensor del Pueblo), no el de reparto. Dentro de las Cámaras se estudia primero qué son y
#: cómo se componen, después cómo funcionan, después qué les toca y, por último, cómo hacen las
#: leyes; lo que cae de otros títulos de la Constitución va al final, para no partir la lectura del
#: Título III.
ORDEN: tuple[str, ...] = (
    "cortes-composicion",
    "cortes-organizacion",
    "cortes-funciones",
    "cortes-procedimiento-legislativo",
    "tc-naturaleza-y-composicion",
    "tc-atribuciones",
    "tc-sentencias-y-efectos",
    "defensor-del-pueblo",
    "corona",
    "gobierno-y-administracion",
    "derechos-y-garantias",
    "organizacion-territorial-y-justicia",
    "transparencia",
    "cortes-otros",
    "tc-otros",
    "defensor-otros",
)

__all__ = ["MATERIAS", "ORDEN"]
