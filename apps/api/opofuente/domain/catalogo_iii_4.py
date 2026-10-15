"""El catálogo de materias de III.4 (diseño y programación orientada a objetos, patrones y UML).

III.4 llegó a esta tanda **con el banco arreglado**: el §5.2 del orden nuevo mandaba reclasificar a
III.2 las preguntas que no eran de este tema —y se hizo por la ruta auditada, con su antes y su
después
medidos en `DECISIONES` F28d—. De las **434** preguntas que colgaban de III.4, **92** se fueron a
III.2
como decisión y **67** quedaron allí como propuesta en la cola; **275 se quedaron**, y con ellas el
tema
tiene hoy **248 grupos** (los grupos agrupan por firma, así que varias preguntas iguales son un solo
trabajo). Lo que queda es **coherente**: orientación a objetos, patrones de diseño y UML.

De sus **248 grupos, 160 no traen epígrafe** (el 65 %) y los cuatro oficiales son un esqueleto de
8, 33,
0 y 47 grupos. Por eso el índice va **por asunto**, como en los demás temas de la serie.

Catorce apartados, en el orden en que se estudia:

- **las fases del análisis y del diseño orientado a objetos** (III.4.1): qué se hace en la fase de
  análisis y qué **no**, y las tareas de cada una;
- **la calidad del diseño, la cohesión y el acoplamiento** (III.4.1): los indicadores de que un
diseño
  tiene poca calidad, qué busca un diseño de buena calidad estructural, la cohesión y el
  acoplamiento, y
  los principios básicos del diseño orientado a objetos —y cuál **no** lo es—, con SOLID;
- **los objetos, las clases y sus relaciones** (III.4.2): qué es un objeto y qué una clase, en qué
se
  diferencian, la agrupación lógica de objetos con la misma estructura y comportamiento, las
  relaciones
  entre clases —«un libro tiene capítulos», la jerárquica entre un todo y sus partes según METRICA,
  la
  semántica y la de subsistema cliente-proveedor—, la estructura de datos abstracta con sus
  operaciones
  y el mecanismo de crear clases complejas agregando objetos de clases que ya existen;
- **la herencia y el polimorfismo** (III.4.2): qué se hereda, lo que heredan dos subclases de una
  superclase común, la herencia múltiple en Java, el nivel de acceso que solo alcanzan la clase, sus
  subclases y su paquete, `this` y `super`, y el concepto que describe que al llamar a un método
  sobrescrito se ejecute la versión de la subclase;
- **la sobrecarga de métodos y de operadores** (III.4.2): definir varios métodos con el mismo
nombre y
  distintos parámetros y cómo se llama esa propiedad, para qué sirve la sobrecarga de operadores,
  cuáles
  **no** se pueden sobrecargar en C++ y qué pasa cuando se define dos veces una función con distinto
  número de parámetros;
- **la encapsulación y los niveles de acceso** (III.4.2): la ocultación del estado y sus otros
nombres,
  qué implica declarar un atributo `private`, la clase raíz de la jerarquía de Java y las interfaces
  frente a las clases, las palabras `new` y `final`, el constructor y el destructor en C++ y la
  recolección de basura;
- **los lenguajes orientados a objetos y sus reglas** (III.4.2): qué lenguajes son y cuáles **no**,
  afirmaciones correctas e incorrectas sobre Java y sobre C++, las *applets*, Swift, la genericidad
  o el
  polimorfismo paramétrico, y los lenguajes orientados a objetos puros;
- **qué es un patrón de diseño y cuáles son sus familias** (III.4.4): qué es un patrón y qué no, la
  clasificación de GoF y sus tres familias, a cuál pertenece cada patrón conocido, las afirmaciones
  ciertas sobre patrones, y GRASP con la ventaja de usarlo y el principio «no hables con extraños»;
- **los patrones creacionales** (III.4.4): Singleton —que asegura una única instancia y su ejemplo
  clásico—, el que encapsula la creación delegando en una subclase, el que define una interfaz para
  crear **familias** de objetos sin decir sus clases concretas, Builder y cuándo es útil, y
  Prototype
  para crear copiando una instancia;
- **los patrones de comportamiento** (III.4.4): Observer —la dependencia uno a muchos y cuándo es
  útil—, Strategy, el que cambia el comportamiento de un objeto cuando cambia su estado interno,
  Mediator y cómo se comunican sus objetos, Iterator —el acceso secuencial a una colección—, el que
  se
  usa cuando un comportamiento solo tiene sentido en algunas clases de la jerarquía, e Interpreter
  con
  su gramática;
- **los patrones estructurales** (III.4.4): el que desacopla una abstracción de su implementación,
  Composite y las jerarquías parte-todo, el que añade funcionalidades envolviendo el objeto en otro,
  Proxy como sustituto que controla el acceso, y cuál de los conocidos es estructural;
- **el lenguaje de modelado unificado: qué es y qué norma lo define** (III.4.4): qué significan las
  siglas y qué no, la norma ISO/IEC 19505-1, la versión actual y las afirmaciones correctas e
  incorrectas sobre él;
- **los diagramas de estructura de UML** (III.4.4): cuáles son de estructura y cuál **no**, el de
clases
  y qué significa el signo menos delante de un método, el de componentes, el de despliegue —el que
  muestra las particiones físicas—, el de objetos y el de paquetes;
- y **los diagramas de comportamiento de UML** (III.4.4): cuáles son de interacción y cuál **no**,
el de
  actividad con sus transiciones y la de reunión, el de casos de uso y cómo se relacionan, y el
  diagrama
  que muestra una instantánea del sistema en un momento dado.

Cuatro decisiones de los patrones y de los apartados, dichas donde se leen:

- **este tema ya no tiene material de otro**: las preguntas de lenguaje de programación general
  —tipado, operadores, estructuras de control, recursividad— **se fueron a III.2** por la ruta
  auditada
  y **están dichas con su antes y su después**; lo que queda aquí lo reclama el catálogo sin lavar
  nada;
- **la lección de la serie, aplicada desde el principio**: «clase», «objeto», «método» y «diseño»
salen
  en casi todos los enunciados y **no son patrones propios de una sola materia**; lo que distingue
  una
  pregunta de otra es **el nombre del patrón y el del diagrama** (`singleton`, `observer`, `proxy`,
  `casos de uso`, `despliegue`), y por eso los patrones miran eso;
- **la lección de II.3, aplicada**: los títulos de los catorce apartados **no comparten las tres
  primeras palabras entre tres de ellos**, y se comprueba con una cuenta antes de correr;
- y **lo que es de otro tema no se lava**: lo que no cuenta patrones ni diagramas ni orientación a
  objetos **ya se fue a III.2**, y las 67 propuestas que quedaron en su cola esperan la decisión del
  propietario y **no cuentan** en el diagnóstico mientras estén así.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Las fases del análisis y del diseño.
_FASES = (
    r"fase de analisis|analisis y diseno|analisis orientado a objetos",
    r"tareas? (no )?forma(n)? parte|actividades realizadas durante",
)

#: La calidad del diseño, cohesión y acoplamiento.
_CALIDAD = (
    r"cohesion|acoplamiento",
    r"calidad (del|de un) diseno|escasa calidad|calidad estructural|indicadores?",
    r"principio(s)? (basico|basicos) de dise|no es un principio basico",
    r"objetivo de un diseno de software|software con una buena calidad",
    r"principio solid|solid es un acronimo|unica razon para cambiar",
    r"liskov|inversion de dependencia|abierto ?-? ?cerrado|segregacion de interfaces",
    r"varios metodos diferentes para abrir",
)

#: Los objetos, las clases y sus relaciones.
_OBJETOS = (
    r"que es un objeto|un objeto\b|clase y objeto|diferencia.*clase.*objeto",
    r"agrupacion logica de objetos|misma estructura y el mismo comportamiento",
    r"un libro tiene capitulos|relacion.*(tiene|parte|todo)|totalidad",
    r"estructura de datos abstracta|tipo abstracto de datos|\btad\b",
    r"agregando objetos de clases ya existentes|clases complejas agregando",
    r"relacion semantica|subsistema cliente ?-? ?proveedor|metrica",
    r"generalizacion entre clases|asociacion entre clases",
    r"los objetos se caracterizan|clases en poo|clases? abstracta",
)

#: La herencia y el polimorfismo.
_HERENCIA = (
    r"herencia|hereda|heredan|subclase|superclase|clase base|clase derivada",
    r"polimorfismo",
    r"palabras? (das )?this y super|\bthis\b|\bsuper\b",
    r"sobreescrit|version sobreescrita|se ejecuta la version",
    r"que permite la herencia|propiedad.*asuma como propios",
    r"nivel de acceso.*metodo|protected",
)

#: La sobrecarga.
_SOBRECARGA = (
    r"sobrecarga",
    r"multiples? metodos con el mismo nombre|mismo nombre.*diferentes? (parametros|signaturas)",
    r"distinto numero de parametros|distintos parametros|por duplicado una funcion",
    r"diferentes versiones del mismo metodo",
    r"operador(es)? no se puede sobrecargar",
    r"define.*diferentes versiones del mismo metodo|mismo nombre pero",
)

#: La encapsulación y los niveles de acceso.
_ENCAPSULACION = (
    r"encapsulaci|ocultacion del estado|ocultacion de los datos",
    r"atributo private|definimos una variable con la clausula protected|niveles? de acceso",
    r"clase raiz|jerarquia de clases|todas las clases en java",
    r"palabra clave new|new en java|constructor\b|destructor",
    r"recoleccion de basura|garbage collector|eliminar los objetos no usados",
    r"interfaz(es)? java|diferencia.*clases e interfaces",
    r"\bgetter\b|\bsetter\b|modificar el valor de un atributo",
)

#: Los lenguajes orientados a objetos.
_LENGUAJES_OO = (
    r"lenguaje(s)? .*orientado(s)? a objetos|no es orientado a objetos",
    r"\bjava\b|\bc\+\+\b|\bc#\b|\bswift\b|kotlin",
    r"applets?|aseveraciones es falsa",
    r"genericidad|polimorfismo parametrico|funciones genericas",
    r"lenguajes? orientados? a objetos? puros?",
    r"afirmacion incorrecta,? con respecto al lenguaje c\+\+",
    r"que representa este fragmento de codigo|fragmento de codigo en swift",
)

#: Qué es un patrón y sus familias.
_PATRONES = (
    r"\bpatron(es)?( de diseno)?\b|patrones de diseno de software",
    r"gof|gang of four|clasificacion de los patrones",
    r"grasp|no hables con extranos|experto en informacion",
    r"creacional(es)?|estructural(es)?|de comportamiento",
    r"afirmaciones? (con respecto a|sobre) los patrones",
    r"que es un patron de diseno",
)

#: Los patrones creacionales.
_CREACIONALES = (
    r"singleton|unica instancia|punto de acceso global",
    r"factory ?method|encapsula la creacion|delega la instancia a una subclase",
    r"abstract factory|familias de objetos relacionados|producir familias de objetos",
    r"\bbuilder\b|constructor paso a paso|especialmente util cuando",
    r"\bprototype\b|copiando una instancia existente|nuevo objeto copiando",
    r"copiar objetos existentes",
)

#: Los patrones de comportamiento.
_COMPORTAMIENTO = (
    r"observer|uno a muchos|dependencia uno a muchos|notificados y actualizados",
    r"\bstrategy\b|en el patron strategy",
    r"\bstate\b|alterar su comportamiento cuando su estado interno cambia",
    r"\bmediator\b|los objetos se comunican",
    r"\biterator\b|acceso secuencial a los elementos",
    r"\binterpreter\b|evaluar sentencias|definiendo una gramatica",
    r"un comportamiento solo tenga sentido en algunas clases|template ?method",
    r"cadena de responsabilidad|memento|visitor",
    r"mecanismo de suscripcion|separar algoritmos de los objetos",
    r"familia de algoritmos",
)

#: Los patrones estructurales.
_ESTRUCTURALES = (
    r"desacopla una abstraccion de su implementacion|\bbridge\b|puente",
    r"\bcomposite\b|jerarquia.*parte ?-? ?todo|todo-parte",
    r"\bdecorator\b|decorador|colocando estos objetos dentro de objetos encapsuladores",
    r"\bproxy\b|sustituto o representante|controlar el acceso al mismo",
    r"interfaz simplificada a una biblioteca|convertir la interfaz de una clase",
    r"estructuras de arbol|dos jerarquias separadas|abstraccion e implementacion",
    r"compartiendo las partes comunes del estado",
    r"colaboracion entre objetos con interfaces incompatibles",
    r"\badapter\b|adaptador|\bfacade\b|fachada|\bflyweight\b|peso ligero",
    r"cual de los siguientes es un patron de diseno estructural",
    r"anadir funcionalidades a objetos colocando",
)

#: Qué es UML.
_UML_QUE_ES = (
    r"\buml\b|lenguaje de modelado unificado",
    r"iso ?/? ?iec ?19505|norma iso.*19505",
    r"version actual de uml|uml ?v?\.? ?2\.?5",
    r"que significa uml",
    r"no se corresponde con el lenguaje uml",
)

#: Los diagramas de estructura.
_DIAGRAMAS_ESTRUCTURA = (
    r"diagrama(s)? de estructura",
    r"diagrama de clases|signo menos|precedido de",
    r"diagrama de componentes|componentes indique la respuesta incorrecta",
    r"diagrama de despliegue|particiones fisicas|disposicion de las particiones",
    r"diagrama de objetos",
    r"diagrama de paquetes",
)

#: Los diagramas de comportamiento.
_DIAGRAMAS_COMPORTAMIENTO = (
    r"diagramas? de interaccion|diagramas? de comportamiento",
    r"no es un diagrama de interaccion",
    r"transicion de reunion|flujos entrantes se sincronicen|transicion",
    r"casos de uso",
    r"diagrama de actividad|maquina de estado|diagrama de estados",
    r"instantanea del sistema en un",
)

#: Las ventajas, los inconvenientes y las características de la orientación a objetos.
_VENTAJAS = (
    r"ventaja(s)? .*(poo|orientad[ao] a objetos)|una ventaja de la orientacion",
    r"no se considera una ventaja|no es una ventaja",
    r"caracteristica(s)? (fundamental|clave).*(poo|orientad[ao] a objetos)",
    r"no es una caracteristica (de la programacion orientada|fundamental)",
    r"reutilizacion,? en relacion con la orientacion|se consigue mediante",
    r"respuesta incorrecta ?\(?poo\)?",
)

MATERIAS: tuple[Materia, ...] = (
    # --- III.4.1 Diseño y programación orientada a objetos ---------------------------------------
    Materia(
        key="las-fases-del-analisis-y-del-diseno-orientado-a-objetos",
        epigraph_code="III.4.1",
        title="Las fases del análisis y del diseño orientado a objetos",
        resumen=(
            "Qué se hace en cada fase: las actividades del análisis orientado a objetos y cuál "
            "**no**"
            "forma parte de ellas, y qué corresponde al diseño."
        ),
        patrones=_FASES,
        prioridad=40,
    ),
    Materia(
        key="la-calidad-del-diseno-la-cohesion-y-el-acoplamiento",
        epigraph_code="III.4.1",
        title="La calidad del diseño, la cohesión y el acoplamiento",
        resumen=(
            "Cuándo un diseño es bueno: los indicadores de que tiene poca calidad, qué busca un "
            "diseño"
            "de buena calidad estructural, la cohesión y el acoplamiento, y los principios básicos "
            "del"
            "diseño orientado a objetos —y cuál **no** lo es—, con SOLID."
        ),
        patrones=_CALIDAD,
        prioridad=30,
    ),
    # --- III.4.2 Elementos y componentes software -------------------------------------------------
    Materia(
        key="los-objetos-las-clases-y-sus-relaciones",
        epigraph_code="III.4.2",
        title="Los objetos, las clases y sus relaciones",
        resumen=(
            "Las piezas y cómo se enlazan: qué es un objeto y qué una clase y en qué se "
            "diferencian, la"
            "agrupación lógica de objetos con la misma estructura y comportamiento, las relaciones "
            "entre"
            "clases —«un libro tiene capítulos», la jerárquica entre un todo y sus partes de "
            "METRICA, la"
            "semántica y la de subsistema cliente-proveedor—, la estructura de datos abstracta con "
            "sus"
            "operaciones y el mecanismo de crear clases complejas agregando objetos ya existentes."
        ),
        patrones=_OBJETOS,
        prioridad=30,
    ),
    Materia(
        key="la-herencia-y-el-polimorfismo",
        epigraph_code="III.4.2",
        title="La herencia y el polimorfismo",
        resumen=(
            "Heredar y comportarse como el padre: qué se hereda, lo que heredan dos subclases de "
            "una"
            "superclase común, la herencia múltiple en Java, el nivel de acceso que solo alcanzan "
            "la"
            "clase, sus subclases y su paquete, `this` y `super`, y el concepto que describe que "
            "al"
            "llamar a un método sobrescrito se ejecute la versión de la subclase."
        ),
        patrones=_HERENCIA,
        prioridad=20,
    ),
    Materia(
        key="la-sobrecarga-de-metodos-y-de-operadores",
        epigraph_code="III.4.2",
        title="La sobrecarga de métodos y de operadores",
        resumen=(
            "El mismo nombre, distintos parámetros: definir varios métodos con un mismo nombre y "
            "parámetros distintos y cómo se llama esa propiedad, para qué sirve la sobrecarga de "
            "operadores, cuáles **no** se pueden sobrecargar en C++ y qué pasa cuando se define "
            "dos"
            "veces una función con distinto número de parámetros."
        ),
        patrones=_SOBRECARGA,
        prioridad=25,
    ),
    Materia(
        key="la-encapsulacion-y-los-niveles-de-acceso",
        epigraph_code="III.4.2",
        title="La encapsulación y los niveles de acceso",
        resumen=(
            "Esconder el estado: la ocultación del estado y sus otros nombres, qué implica un "
            "atributo"
            "`private`, la clase raíz de la jerarquía de Java y las interfaces frente a las "
            "clases, las"
            "palabras `new` y `final`, el constructor y el destructor en C++ y la recolección de "
            "basura."
        ),
        patrones=_ENCAPSULACION,
        prioridad=25,
    ),
    Materia(
        key="los-lenguajes-orientados-a-objetos-y-sus-reglas",
        epigraph_code="III.4.2",
        title="Los lenguajes orientados a objetos y sus reglas",
        resumen=(
            "Qué lenguajes lo son y cuáles **no**, las afirmaciones correctas e incorrectas sobre "
            "Java y"
            "sobre C++, las *applets*, Swift, la genericidad o polimorfismo paramétrico y los "
            "lenguajes"
            "orientados a objetos puros."
        ),
        patrones=_LENGUAJES_OO,
        prioridad=35,
    ),
    Materia(
        key="las-ventajas-y-los-inconvenientes-de-la-orientacion",
        epigraph_code="III.4.3",
        title="Las ventajas y los inconvenientes de la orientación a objetos",
        resumen=(
            "Lo que se gana y lo que se paga: las ventajas de la orientación a objetos y la que"
            " **no** lo es, la reutilización y cómo se consigue, las características"
            " fundamentales y las claves —y la que **no** es ninguna de las dos—, y los"
            " inconvenientes."
        ),
        patrones=_VENTAJAS,
        prioridad=40,
    ),
    # --- III.4.4 Patrones y UML ------------------------------------------------------------------
    Materia(
        key="que-es-un-patron-de-diseno-y-sus-familias",
        epigraph_code="III.4.4",
        title="Qué es un patrón de diseño y cuáles son sus familias",
        resumen=(
            "El catálogo de soluciones que ya funcionan: qué es un patrón de diseño, la "
            "clasificación de"
            "GoF y sus tres familias, a cuál pertenece cada patrón conocido, las afirmaciones "
            "ciertas"
            "sobre patrones y GRASP con la ventaja de usarlo y el principio «no hables con "
            "extraños»."
        ),
        patrones=_PATRONES,
        prioridad=30,
    ),
    Materia(
        key="los-patrones-creacionales",
        epigraph_code="III.4.4",
        title="Los patrones creacionales: Singleton, Factory, Builder y Prototype",
        resumen=(
            "Los que resuelven **cómo se crea**: Singleton, que asegura una única instancia y su "
            "ejemplo"
            "clásico; el que encapsula la creación delegando en una subclase; el que define una "
            "interfaz"
            "para crear familias de objetos sin decir sus clases concretas; Builder y cuándo es "
            "útil; y"
            "Prototype, que crea copiando una instancia."
        ),
        patrones=_CREACIONALES,
        prioridad=20,
    ),
    Materia(
        key="los-patrones-de-comportamiento",
        epigraph_code="III.4.4",
        title="Los patrones de comportamiento: Observer, Strategy, State e Iterator",
        resumen=(
            "Los que reparten **quién hace qué y cuándo**: Observer y su dependencia uno a muchos, "
            "Strategy, el que cambia el comportamiento cuando cambia el estado interno, Mediator y "
            "cómo"
            "se comunican sus objetos, Iterator y el acceso secuencial a una colección, el que se "
            "usa"
            "cuando un comportamiento solo tiene sentido en algunas clases de la jerarquía, e "
            "Interpreter con su gramática."
        ),
        patrones=_COMPORTAMIENTO,
        prioridad=20,
    ),
    Materia(
        key="los-patrones-estructurales",
        epigraph_code="III.4.4",
        title="Los patrones estructurales: Bridge, Composite, Decorator y Proxy",
        resumen=(
            "Los que resuelven **cómo se componen**: el que desacopla una abstracción de su "
            "implementación, Composite y las jerarquías parte-todo, el que añade funcionalidades "
            "envolviendo el objeto en otro, Proxy como sustituto que controla el acceso, y cuál de "
            "los"
            "conocidos es estructural."
        ),
        patrones=_ESTRUCTURALES,
        prioridad=20,
    ),
    Materia(
        key="el-lenguaje-de-modelado-unificado-y-su-norma",
        epigraph_code="III.4.4",
        title="El lenguaje de modelado unificado: qué es y qué norma lo define",
        resumen=(
            "El idioma de los planos del software: qué significan las siglas y qué no, la norma "
            "ISO/IEC 19505-1, la versión actual y las afirmaciones correctas e incorrectas sobre "
            "él."
        ),
        patrones=_UML_QUE_ES,
        prioridad=15,
    ),
    Materia(
        key="los-diagramas-de-estructura-de-uml",
        epigraph_code="III.4.4",
        title="Los diagramas de estructura de UML",
        resumen=(
            "Lo que no cambia con el tiempo: cuáles son diagramas de estructura y cuál **no**, el "
            "de"
            "clases y qué significa el signo menos delante de un método, el de componentes, el de "
            "despliegue —el que muestra las particiones físicas—, el de objetos y el de paquetes."
        ),
        patrones=_DIAGRAMAS_ESTRUCTURA,
        prioridad=15,
    ),
    Materia(
        key="los-diagramas-de-comportamiento-de-uml",
        epigraph_code="III.4.4",
        title="Los diagramas de comportamiento de UML",
        resumen=(
            "Lo que pasa con el tiempo: cuáles son diagramas de interacción y cuál **no**, el de "
            "actividad con sus transiciones y la de reunión, el de casos de uso y cómo se "
            "relacionan, y"
            "el que muestra una instantánea del sistema en un momento dado."
        ),
        patrones=_DIAGRAMAS_COMPORTAMIENTO,
        prioridad=15,
    ),
)

#: El orden del índice: primero el diseño —sus fases y su calidad—, después las piezas de la
#: orientación a objetos —objetos y clases, herencia, sobrecarga, encapsulación y los lenguajes— y,
#: al final, lo que más se pregunta: los patrones de diseño y los diagramas de UML.
ORDEN: tuple[str, ...] = (
    "las-fases-del-analisis-y-del-diseno-orientado-a-objetos",
    "la-calidad-del-diseno-la-cohesion-y-el-acoplamiento",
    "los-objetos-las-clases-y-sus-relaciones",
    "la-herencia-y-el-polimorfismo",
    "la-sobrecarga-de-metodos-y-de-operadores",
    "la-encapsulacion-y-los-niveles-de-acceso",
    "los-lenguajes-orientados-a-objetos-y-sus-reglas",
    "las-ventajas-y-los-inconvenientes-de-la-orientacion",
    "que-es-un-patron-de-diseno-y-sus-familias",
    "los-patrones-creacionales",
    "los-patrones-de-comportamiento",
    "los-patrones-estructurales",
    "el-lenguaje-de-modelado-unificado-y-su-norma",
    "los-diagramas-de-estructura-de-uml",
    "los-diagramas-de-comportamiento-de-uml",
)

__all__ = ["MATERIAS", "ORDEN"]
