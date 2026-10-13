"""El catálogo de materias de III.1 (modelado de datos, modelo relacional y normalización).

III.1 es un tema **técnico**: lo que lo estructura son sus seis epígrafes —el modelado de datos y
sus
metodologías, las entidades, los atributos y las relaciones, el diseño de bases de datos, el diseño
lógico y físico, el modelo lógico relacional y la normalización— y dentro de cada uno el índice va
por
**asunto**, como en IV.7, IV.2 y II.4. Este catálogo los abre en **nueve** apartados:

- el modelado de datos, en dos: los **conceptos y las metodologías** (los niveles conceptual,
lógico y
  físico, los modelos de datos —el jerárquico, el de red, el relacional y el PLEX—, la metodología
  MÉTRICA v3 y sus diagramas de flujo de datos, y los esquemas del almacén de datos con el esquema
  en
  estrella, el copo de nieve y el OLAP frente al OLTP) y la **arquitectura de tres niveles** con la
  independencia de datos;
- las entidades, los atributos y las relaciones, en dos: el **modelo entidad-relación** (la entidad
y
  sus tipos y ocurrencias, la entidad débil, los atributos y su dominio, la relación y su grado, la
  cardinalidad y la razón de cardinalidad, la participación y la dependencia, y su representación
  gráfica) y el **modelo entidad-relación extendido** de MÉTRICA v3 (la superentidad y la
  subentidad,
  el supertipo y los subtipos, la especialización y la generalización, las jerarquías disjuntas y
  solapadas, la entidad asociativa y la agregación, y las reglas del modelo);
- el diseño, en dos: el **diseño de bases de datos** (sus fases, el paso del modelo conceptual al
  lógico, la transformación de las entidades y de las relaciones uno a uno, uno a varios y varios a
  varios en tablas, los atributos multivaluados, las relaciones redundantes y la desnormalización)
  y el
  **modelo lógico relacional** (la relación y sus propiedades, las tuplas, los atributos y el
  dominio,
  el grado y la cardinalidad, las claves —superclave, candidata, primaria, alternativa y ajena—, la
  integridad de entidad y la integridad referencial, los valores nulos, los índices y las vistas);
- el **álgebra relacional**, en uno: las operaciones fundamentales y las derivadas, la reunión y sus
  variantes, la composición de operaciones y el cálculo relacional;
- la **normalización**, en uno: la dependencia funcional, las formas normales de la primera a la
quinta
  y la de Boyce-Codd, las dependencias multivaluadas y de reunión, la descomposición sin pérdida y
  sus
  propiedades.

Tres decisiones de redacción de los patrones, dichas donde se leen:

- **`relacion` y `modelo` no son patrones propios de nadie**: aparecen en casi todos los enunciados
del
  tema, así que viven en los `patrones_debiles` del apartado del modelo relacional. Lo particular
  gana a
  lo general, que es la regla de todos los catálogos del proyecto;
- las **siglas van con `\\b`** (`\\bdfd\\b`, `\\bfnbc\\b`, `\\bansi\\b`, `\\bolap\\b`): sin la
frontera,
  `ansi` casa dentro de otra palabra y el reparto se llena de falsos positivos;
- **este tema no pregunta SQL ni transacciones** (medido sobre su banco: ni una pregunta de `SQL`,
  disparadores, transacciones o ACID), así que no hay apartado para ellos: los lenguajes de
  interrogación tienen su propio tema (III.3) y poner aquí un apartado vacío sería escribir un
  apunte
  que nadie va a leer.

Las preguntas que no se sitúan ni por su enunciado ni por el texto de sus hechos **no** acaban en un
cajón: van a la bandeja del propietario con su motivo (`Motivo.SIN_MATERIA_EN_EL_INDICE`).
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: El modelo extendido y su metodología, que el banco cita en una cuarta parte de sus enunciados.
_METRICA = r"metrica|\bmv3\b|metodologia metrica"
#: La sigla del diagrama de flujo de datos, con su frontera.
_DFD = r"\bdfd\b|diagrama(s)? de flujo de datos|flujo de datos"

MATERIAS: tuple[Materia, ...] = (
    # --- III.1.1 Modelado de datos, metodologías y reglas ----------------------------------------
    Materia(
        key="modelado-de-datos-y-metodologias",
        epigraph_code="III.1.1",
        title="El modelado de datos, sus niveles y sus metodologías",
        resumen=(
            "Qué es modelar los datos y con qué: los niveles del modelado (conceptual, lógico y "
            "físico) y en qué se diferencian, los modelos de datos (el jerárquico, el de red, el "
            "relacional y el orientado a objetos) y el modelo PLEX, las metodologías de desarrollo "
            "y "
            "MÉTRICA v3, los diagramas de flujo de datos y sus reglas de construcción, y el "
            "almacén de "
            "datos: los esquemas en estrella y en copo de nieve, el data mart, los hechos y las "
            "dimensiones, y el OLAP frente al OLTP."
        ),
        patrones=(
            _METRICA,
            _DFD,
            r"esquema(s)? (en )?(estrella|copo de nieve|constelacion)|"
            r"data ?mart|data ?warehouse|almacen de datos|\bolap\b|\bolt[pf]\b",
            r"modelo(s)? de datos|\bplex\b|modelo (jerarquico|en red|relacional|"
            r"orientado a objetos|conceptual|logico|fisico)",
            r"niveles? (de|del) (modelado|abstraccion|ansi)|"
            r"modelo conceptual.*modelo (logico|fisico)|"
            r"diferencia.*modelos? de datos? (logicos?|fisicos?|conceptuales?)",
            r"metodologia(s)? (de|para el) (desarrollo|diseno)|"
            r"fases? del (desarrollo|diseno) de (una )?base de datos",
        ),
        patrones_debiles=(r"modelo", r"metodologia", r"esquema"),
        prioridad=60,
    ),
    Materia(
        key="ansi-sparc-y-niveles",
        epigraph_code="III.1.4",
        title="La arquitectura de tres niveles y la independencia de datos",
        resumen=(
            "Cómo se organiza una base de datos por dentro: la arquitectura ANSI/X3/SPARC y sus "
            "tres "
            "niveles (el interno, el conceptual y el externo), el esquema y las vistas de cada "
            "nivel, "
            "la independencia de los datos (la lógica y la física), el diccionario de datos y el "
            "catálogo, y el diseño lógico y el físico como pasos separados."
        ),
        patrones=(
            r"ansi ?/? ?x3 ?/? ?sparc|\bansi\b|\bsparc\b|arquitectura de (tres|3) niveles",
            r"nivel(es)? (interno|conceptual|externo)|"
            r"independencia de (los )?datos|independencia (logica|fisica)",
            r"esquema(s)? (conceptual|interno|externo)|diccionario de datos|"
            r"catalogo (de datos)?",
            r"diseno (logico|fisico)|nivel fisico.*nivel logico",
        ),
        patrones_debiles=(r"nivel", r"esquema"),
        prioridad=41,
    ),
    # --- III.1.2 Entidades, atributos y relaciones ----------------------------------------------
    Materia(
        key="entidades-atributos-y-relaciones",
        epigraph_code="III.1.2",
        title="El modelo entidad-relación: entidades, atributos y relaciones",
        resumen=(
            "El modelo entidad-relación: la entidad, sus tipos y sus ocurrencias, la entidad débil "
            "y la "
            "fuerte, el atributo (simple y compuesto, monovaluado y multivaluado, derivado, y su "
            "dominio), el identificador y la clave, la relación y su grado (unaria, binaria y "
            "ternaria), "
            "la cardinalidad y la razón de cardinalidad, la participación total y parcial, la "
            "dependencia y la existencia, la superclave y las claves candidata, primaria y ajena, "
            "y la "
            "representación gráfica de cada elemento (el rectángulo, la elipse, el rombo y la "
            "línea)."
        ),
        patrones=(
            r"entidad(es)?( debil| fuerte| asociativa| superentidad)?|"
            r"tipo(s)? de entidad|ocurrencia(s)?",
            r"atributo(s)?|dominio de un atributo|atributo(s)? multivaluad|"
            r"atributo(s)? compuest|atributo(s)? derivad",
            r"cardinalidad|razon de cardinalidad|participacion (total|parcial)|"
            r"grado (de la|de una) relacion|relacion (unaria|binaria|ternaria)|grado 3",
            r"superclave|clave (candidata|primaria|alternativa|ajena|foranea)|\bprimary key\b|"
            r"clave principal",
            r"diagrama entidad ?/? ?relacion|modelo e ?/? ?r|"
            r"elipse|rectangulo|rombo|circulo o elipse",
            r"relacion(es)? (uno a uno|uno a varios|varios a varios|1 ?: ?n|n ?: ?m)|"
            r"jerarquia disjunta|especializacion",
        ),
        patrones_debiles=(r"entidad", r"atributo", r"cardinalidad"),
        prioridad=42,
    ),
    Materia(
        key="modelo-er-extendido",
        epigraph_code="III.1.2",
        title="El modelo entidad-relación extendido de MÉTRICA v3",
        resumen=(
            "El modelo entidad-relación extendido tal como lo recoge MÉTRICA v3: la superentidad y "
            "la "
            "subentidad, el supertipo y los subtipos, la especialización y la generalización, las "
            "jerarquías (disjunta y solapada, total y parcial), la herencia de atributos y de "
            "relaciones, la agregación y la entidad asociativa, los atributos de la relación, y "
            "las "
            "reglas que tienen que cumplir las entidades, las relaciones y los atributos del "
            "modelo."
        ),
        patrones=(
            r"(modelo )?entidad ?/? ?relacion extendid|\bmer extendido\b|e ?/? ?r extendido",
            r"superentidad|subentidad|supertipo|subtipo(s)?|superclase|subclase",
            r"especializacion|generalizacion|jerarquia(s)? (disjunta|solapada|total|parcial|"
            r"de especializacion)|herencia de atributos",
            r"agregacion|entidad asociativa|atributos? de la relacion",
            r"reglas? (que|del modelo)|no se caracteriza por|no es una regla",
        ),
        patrones_debiles=(r"extendido", r"supertipo", r"jerarquia"),
        prioridad=43,
    ),
    # --- III.1.3 y III.1.4 Diseño -----------------------------------------------------------------
    Materia(
        key="diseno-de-bases-de-datos",
        epigraph_code="III.1.3",
        title="El diseño de bases de datos y el paso al modelo relacional",
        resumen=(
            "El proceso de diseño: la recogida y el análisis de requisitos, el diseño conceptual, "
            "el "
            "lógico y el físico, la primera fase del modelo conceptual, el paso del modelo "
            "entidad-relación al relacional, la transformación de las entidades en tablas y de las "
            "relaciones uno a uno, uno a varios y varios a varios, el tratamiento de los atributos "
            "multivaluados y de las relaciones redundantes, la desnormalización como decisión de "
            "rendimiento y la elección de los índices."
        ),
        patrones=(
            r"diseno (de|conceptual|logico|fisico) (la |una )?base de datos|"
            r"fases? (de|del) (diseno|construccion)",
            r"paso del modelo|transformacion (de|al) modelo|"
            r"pasar (del|al) modelo (conceptual|relacional|logico)",
            r"primera fase|recogida de (requisitos|informacion)|analisis de requisitos",
            r"(que|como) (ocurre|se refleja|se transforma) (con|en) (los|las) "
            r"(atributos? multivaluad|relaciones?)",
            r"relaciones? redundante|desnormaliz|denormaliz|"
            r"eleccion de (un )?indice|diseno fisico",
        ),
        patrones_debiles=(r"diseno", r"transformacion", r"fase"),
        prioridad=44,
    ),
    # --- III.1.5 El modelo lógico relacional -----------------------------------------------------
    Materia(
        key="modelo-relacional",
        epigraph_code="III.1.5",
        title="El modelo lógico relacional y su integridad",
        resumen=(
            "El modelo relacional: la relación y sus propiedades, las tuplas y los atributos, el "
            "grado "
            "de la relación y su cardinalidad, la extensión y la intensión, el esquema y la "
            "instancia, "
            "los valores nulos, la integridad de entidad y la integridad referencial y lo que "
            "establecen, las claves en el modelo lógico, los índices y las vistas."
        ),
        patrones=(
            r"modelo (logico )?relacional|base de datos relacional|"
            r"sistemas? de bases de datos relacionales",
            r"integridad (referencial|de entidad)|regla de integridad|"
            r"clave ajena|clave foranea|\bforeign key\b",
            r"una relacion se caracteriza|propiedades de (una|la) relacion|"
            r"extension de una relacion|intension|instancia de la relacion",
            r"grado de (una|la) relacion|numero de (tuplas|atributos)|"
            r"valores? nul[oa]s?|\bnull\b",
            r"tabla(s)? (del modelo|relacional)|esquema relacional",
            r"indice(s)? (de|sobre) (la |una )?tabla|\bvista(s)?\b|indice (unico|agrupado)",
        ),
        patrones_debiles=(r"relacional", r"relacion", r"tabla"),
        prioridad=45,
    ),
    Materia(
        key="algebra-relacional",
        epigraph_code="III.1.5",
        title="El álgebra relacional y el cálculo relacional",
        resumen=(
            "Las operaciones con las que se consulta un modelo relacional: las operaciones "
            "fundamentales (la selección o restricción, la proyección, el producto cartesiano, la "
            "unión "
            "y la diferencia) y las derivadas (la intersección, la reunión o join y sus variantes, "
            "la "
            "división y la reunión externa), la composición de operaciones, la renombración, y el "
            "cálculo relacional de tuplas y de dominios."
        ),
        patrones=(
            r"algebra relacional|operacion(es)? (fundamental|derivad|del algebra)",
            r"seleccion|proyeccion|producto cartesiano|reunion|\bjoin\b|"
            r"interseccion|diferencia|division|reunion (natural|externa|interna)|\btheta\b",
            r"calculo relacional|calculo de (tuplas|dominios)|"
            r"lenguaje(s)? de consulta formal",
            r"composicion de operaciones|renombra|"
            r"operador(es)? (de|del) algebra",
        ),
        patrones_debiles=(r"algebra", r"operacion", r"join"),
        prioridad=46,
    ),
    Materia(
        key="normalizacion",
        epigraph_code="III.1.6",
        title="La normalización y las formas normales",
        resumen=(
            "La normalización como técnica de diseño: la dependencia funcional y sus tipos "
            "(parcial y "
            "transitiva), la primera forma normal, la segunda, la tercera, la forma normal de "
            "Boyce-Codd, la cuarta y la quinta, las dependencias multivaluadas y de reunión, la "
            "descomposición sin pérdida de información, y qué se gana y qué se pierde al "
            "normalizar."
        ),
        patrones=(
            r"normalizacion|forma(s)? normal(es)?|\b1fn\b|\b2fn\b|\b3fn\b|\bfnbc\b|\bbcnf\b|"
            r"\b4fn\b|\b5fn\b",
            r"dependencia(s)? funcional(es)?|dependencia (parcial|transitiva|multivaluada)|"
            r"dependencia de reunion",
            r"descomposicion (sin perdida|de relaciones)|perdida de informacion",
            r"se dice que (esta|se encuentra) en|para que (una relacion )?este en|"
            r"requiere para que una relacion este",
            r"primera forma normal|segunda forma normal|tercera forma normal",
        ),
        patrones_debiles=(r"normal", r"dependencia", r"forma"),
        prioridad=47,
    ),
)

#: El orden en que se **enseña** el índice: primero el modelado y sus metodologías, después la
#: arquitectura de niveles, después el modelo entidad-relación y su versión extendida, después el
#: diseño y el paso al relacional, después el modelo relacional con su álgebra y por último la
#: normalización, que es el orden de los seis epígrafes del tema.
ORDEN: tuple[str, ...] = (
    "modelado-de-datos-y-metodologias",
    "ansi-sparc-y-niveles",
    "entidades-atributos-y-relaciones",
    "modelo-er-extendido",
    "diseno-de-bases-de-datos",
    "modelo-relacional",
    "algebra-relacional",
    "normalizacion",
)

__all__ = ["MATERIAS", "ORDEN"]
