"""El catálogo de materias de II.5 (sistemas de gestión de bases de datos relacionales, orientados a
objetos y NoSQL).

II.5 tiene **un solo epígrafe oficial con contenido** —«Sistemas de gestión de bases de datos
relacionales, orientados a objetos y NoSQL: características y componentes», con 55 grupos— y **88 de
sus 143 grupos no traen epígrafe** (el 62 %). Así que aquí no hay esqueleto del temario que reparta
nada: **el asunto lo pone entero el enunciado**, que es el caso extremo de la regla de siempre (el
índice va por asunto dentro de cada epígrafe; cuando el epígrafe es uno, el asunto manda solo).

Once apartados, en el orden en que se estudia:

- **qué es un sistema gestor de bases de datos y qué funciones cumple**: la definición, las
funciones
  mínimas para asegurar la base, los componentes principales —y cuál no lo es—, el componente que
  interactúa con el hardware, los componentes de proceso y qué es lo que un SGBD **no** debe hacer;
- **la arquitectura ANSI/SPARC y sus tres niveles**: el externo, el conceptual y el interno, cuál
  corresponde a cada definición, las transformaciones entre niveles, la independencia de los datos y
  en qué nivel se crean las vistas;
- **las doce reglas de Codd y la independencia de los datos**: cuáles son, cuál **no** lo es, la
regla
  2, la del tratamiento sistemático de los valores nulos, la de independencia de integridad y la de
  la accesibilidad unívoca por nombre de tabla, columna y clave;
- **las transacciones, las propiedades ACID y el bloqueo mortal**: qué significan atomicidad,
  consistencia, aislamiento y durabilidad, el punto de integridad, los niveles de aislamiento del
  estándar y en cuál aparecen las lecturas sucias, cuándo se liberan los registros y qué es un
  interbloqueo;
- **el modelo relacional y los gestores relacionales**: la tabla y la relación, la unidad de
  información asociada a un dominio, qué gestor es relacional y cuál no, el motor InnoDB, el gestor
  relacional de la nube compatible con MySQL y PostgreSQL, y qué hacer cuando la escalabilidad en
  lecturas se queda corta;
- **los gestores concretos: Oracle, Access y SQL Server por dentro**: los elementos de Oracle, su
  estructura física, el espacio de tablas y los segmentos, la instancia y sus procesos, la vista
  materializada y sus alternativas, el lenguaje de procedimiento que se guarda compilado, cuándo
  conviene Access frente a una hoja de cálculo, qué es el servicio de aprendizaje automático de SQL
  Server y los puertos por defecto de los gestores;
- **el acceso a los datos: ODBC, JPA y los marcos de persistencia**: qué es ODBC y qué no es un
  sistema de acceso a datos, las herramientas de Oracle para acceder a sus bases, Jakarta
  Persistence y JPA, y Entity Framework;
- **las bases NoSQL y sus cuatro tipos de almacenamiento**: qué es NoSQL, sus ventajas y sus
  características, el principio BASE frente a ACID, el teorema CAP, los tipos de almacenamiento
  —clave-valor, orientado a columnas, orientado a documentos y orientado a grafos—, cuál **no** es
  NoSQL, y Cassandra, MongoDB, Redis y Neo4j con sus orígenes;
- **el procesamiento analítico y los cubos OLAP**: qué arquitecturas se usan en un almacén de datos
  y qué términos son de los cubos multidimensionales y cuál no;
- **las bases orientadas a objetos y el identificador único**: qué caracteriza a un gestor orientado
  a objetos, las características **obligatorias** del manifiesto de Malcolm Atkinson y cuál no lo
  es,
  el identificador de objeto único (OID), los constructores de tipo de colección, el lenguaje OQL y
  cuál de los gestores es orientado a objetos;
- y **los conceptos de la orientación a objetos que usa el modelo**: la clase, el polimorfismo, la
  sobrecarga de métodos, la ocultación del estado o encapsulación, la generalización entre clases y
  los lenguajes orientados a objetos puros.

Cuatro decisiones de los patrones y de los apartados, dichas donde se leen:

- **este banco es el que más vocabulario comparte de la serie**, y por eso «datos», «base»,
«sistema»
  y «siguiente» **no son patrones propios de ninguna materia**: si contaran, cualquier enunciado
  caería
  en el primer apartado que los nombrara. Lo que distingue una pregunta de otra es **la sigla y el
  nombre propio** —`ansi ?/? ?sparc`, `codd`, `acid`, `nosql`, `mongodb`, `oracle`— y por eso los
  patrones miran eso;
- **la lección de II.3 y III.8, aplicada**: los títulos de los once apartados **no comparten las
tres
  primeras palabras entre tres de ellos**, y se comprueba antes de correr;
- **los conceptos de la orientación a objetos se quedan, y se dice por qué**: media docena de
preguntas
  del banco son de polimorfismo, sobrecarga, encapsulación y generalización, que son de programación
  orientada a objetos y no de gestores. Están aquí porque **el modelo de datos orientado a objetos
  se
  construye con ese vocabulario** —el OID, las colecciones, la herencia de tipos— y porque es el
  banco
  del propio tema el que las pregunta; se les da **un apartado explícito** en vez de repartirlas por
  los demás, que es lo que sería lavarlas;
- y **lo que es de otro tema no se lava**: el **hipervisor** es de IV.2, **SCRUM** es de las
  metodologías del bloque III, el **mecanismo de Docker para persistir datos** es de IV.1, **Spring
  Boot** es de III.5 y las **características del lenguaje C#** son de III.2. Son **5 de las 155
  preguntas con clave utilizable** y van a la bandeja del propietario con su motivo
  (`Motivo.SIN_MATERIA_EN_EL_INDICE`), más dos enunciados sin sujeto.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Qué es un SGBD y qué funciones cumple.
_QUE_ES = (
    r"\bsgbd\b|sistema(s)? (de )?gestion de bases? de datos|gestor de bases? de datos",
    r"funciones minimas|asegurar la base de datos|no debe",
    r"componente(s)? (principal|de proceso|de un sistema|\s*de un sgbd)",
    r"se encarga de interactuar con el hardware|gestionar el almacenamiento fisico",
    r"\bcrud\b|que significa crud|independencia de los datos|ventajas? de (un|los) sgbd",
    r"que es un sistema gestor|caracteristicas y componentes",
)

#: La arquitectura ANSI/SPARC.
_ANSI_SPARC = (
    r"ansi ?/? ?(x ?3 ?/? ?)?sparc|ansi.?sparc|x3.?sparc",
    r"nivel(es)? de abstraccion|tres niveles|nivel (externo|conceptual|interno|fisico)",
    r"transformaciones? entre los niveles|independencia (de los datos|logica|fisica)",
    r"representacion abstracta de la estructura de almacenamiento",
    r"creacion de vistas|que y como son almacenados",
)

#: Las reglas de Codd.
_CODD = (
    r"\bcodd\b|reglas? de codd|doce reglas",
    r"tratamiento sistematico de los valores nulos|valores nulos.*regla",
    r"independencia de integridad|regla 2 de codd|regla 1[0-2]",
    r"accesible de manera univoca|nombre de tabla,? un nombre de columna",
    r"sirven para|las reglas de codd sirven",
)

#: Las transacciones y ACID.
_TRANSACCIONES = (
    r"\bacid\b|atomicidad|atomic|consistencia|durabilidad|aislamiento",
    r"transaccion(es)?",
    r"nivel de aislamiento|lectura comprometida|read committed|lecturas sucias",
    r"punto de integridad|savepoint|fallo de sentencia|recuperar el normal funcionamiento",
    r"deadlock|bloqueo mortal|interbloqueo",
    r"se liberan|registros intervinientes",
    r"propiedades de las transacciones|pueden ser completados todos o deshechos todos",
)

#: El modelo relacional y los gestores relacionales.
_RELACIONAL = (
    r"modelo relacional|base(s)? de datos relacional(es)?|sgbd relacional|\brdbms\b",
    r"base de datos local en una aplicacion|moviles android",
    r"gestor(es)? de bases? de datos relacional",
    r"sistema(s)? de gestion de bases? de datos relacional",
    r"no se clasifica como un sgbd relacional|no es un sgbd relacional|cu[aá]l no se clasifica",
    r"tablas que permiten establecer relaciones",
    r"unidad de informacion que esta asociada a un dominio",
    r"innodb|myisam|motor de almacenamiento",
    r"creada para la nube|compatible con mysql y postgresql",
    r"escalabilidad en lecturas|consultas complejas|replicas de lectura",
)

#: Los gestores concretos.
_GESTORES = (
    r"\boracle\b|sql ?plus|pl ?/? ?sql|tablespace|segmentos? de oracle",
    r"estructura fisica esta compuesta|estructura fisica de oracle|instancia de oracle",
    r"\baccess\b|en lugar de excel",
    r"sql server|machine learning services|\bmssql\b",
    r"puertos? por defecto que usan diferentes gestores",
    r"elementos de un sgbd|esta formado por los siguientes elementos",
    r"estructura de memoria y procesos|conjunto compartido de estructuras",
)

#: El acceso a los datos y los ORM.
_ACCESO_A_DATOS = (
    r"\bodbc\b|\bjdbc\b|\boledb\b|ado ?\.? ?net",
    r"sistema(s)? de acceso a (bases? de )?datos|protocolos? de acceso a datos",
    r"herramienta.*(de|para el) acceso a sus bases|desarrollada por oracle para el acceso",
    r"jpa|java persistence|\bjakarta\b|persistence api",
    r"entity framework|marco(s)? de persistencia|\borm\b",
    r"vista materializada|vistas materializadas",
)

#: NoSQL.
_NOSQL = (
    r"\bnosql\b|not only sql|no relacional(es)?",
    r"clave ?-? ?valor|orientad(a|o)s? a (columnas?|documentos?|grafos?)|documental",
    r"cassandra|mongodb|redis|neo4j|hbase|memcache|\bmemcached\b|couchdb|elasticsearch",
    r"serie(s)? temporales?|\btimeseries\b|influxdb",
    r"teorema de cap|principio base|principio.*comun en las bases de datos nosql",
    r"proyecto de la fundacion apache|quien desarrollo inicialmente",
    r"cuando no se recomiendan|no es una ventaja de.*nosql",
    r"caracteristicas de las bases de datos nosql",
)

#: El procesamiento analítico y los cubos OLAP.
_OLAP = (
    r"\bolap\b|cubos? multidimensional|almacen de datos|data warehouse|\bdwh\b",
    r"arquitectura(s)? utilizada(s)? en data warehouse|procesamiento analitico",
    r"mineria de datos|business intelligence|\betl\b",
)

#: Las bases de datos orientadas a objetos.
_ORIENTADAS_A_OBJETOS = (
    r"orientad(a|o)s? a objetos|sgbdoo|sgdboo|\boodbms\b",
    r"identificador de objeto|\boid\b",
    r"constructor(es)? de tipo de coleccion|tipos? de coleccion",
    r"manifiesto|malcolm atkinson|caracteristicas obligatorias",
    r"\boql\b|lenguaje de consulta de objetos",
    r"es un sistema de bases de datos orientado a objetos|gestor.*orientado a objetos",
)

#: Los conceptos de la orientación a objetos.
_ORIENTACION_A_OBJETOS = (
    r"polimorfismo|sobrecarga|overload|mismo nombre pero (funcionalidad|distintos argumentos)",
    r"encapsulacion|ocultacion del estado|datos miembro|metodos definidos para dicho objeto",
    r"generalizacion entre clases|herencia entre clases|\bclase\b|instancia de una clase",
    r"lenguajes? orientados? a objetos? puros?|paradigma de la programacion orientada a objetos",
    r"diseno orientado a objetos|analisis y diseno orientado a objetos",
)

MATERIAS: tuple[Materia, ...] = (
    Materia(
        key="que-es-un-sgbd-y-que-funciones-cumple",
        epigraph_code="II.5.1",
        title="Qué es un sistema gestor de bases de datos y qué funciones cumple",
        resumen=(
            "La definición y el reparto de tareas: las funciones mínimas para asegurar la base de "
            "datos, los componentes principales —y cuál no lo es—, el que interactúa con el "
            "hardware"
            "y gestiona el almacenamiento físico, los componentes de proceso, qué es lo que un "
            "SGBD"
            "no debe hacer y qué significan las siglas CRUD."
        ),
        patrones=_QUE_ES,
        prioridad=55,
    ),
    Materia(
        key="la-arquitectura-ansi-sparc-y-sus-tres-niveles",
        epigraph_code="II.5.1",
        title="La arquitectura ANSI/SPARC y sus tres niveles de abstracción",
        resumen=(
            "Los tres pisos del gestor: el nivel externo, el conceptual y el interno, cuál "
            "corresponde a cada definición, las transformaciones entre niveles, la independencia "
            "de"
            "los datos y en qué nivel se crean las vistas."
        ),
        patrones=_ANSI_SPARC,
        prioridad=10,
    ),
    Materia(
        key="las-doce-reglas-de-codd-y-la-independencia",
        epigraph_code="II.5.1",
        title="Las doce reglas de Codd y la independencia de los datos",
        resumen=(
            "El contrato de un gestor relacional: cuáles son las doce reglas, cuál no lo es, la "
            "regla"
            "2, la del tratamiento sistemático de los valores nulos, la de independencia de "
            "integridad, y la que exige que todo dato sea accesible de forma unívoca por el nombre "
            "de la tabla, el de la columna y el valor de la clave primaria."
        ),
        patrones=_CODD,
        prioridad=10,
    ),
    Materia(
        key="las-transacciones-las-propiedades-acid-y-el-bloqueo",
        epigraph_code="II.5.1",
        title="Las transacciones, las propiedades ACID y el bloqueo mortal",
        resumen=(
            "Lo que tiene que cumplir una transacción: qué significan atomicidad, consistencia, "
            "aislamiento y durabilidad, el punto de integridad, los niveles de aislamiento del "
            "estándar y en cuál aparecen las lecturas sucias, cuándo se liberan los registros "
            "intervinientes y qué es un interbloqueo o bloqueo mortal."
        ),
        patrones=_TRANSACCIONES,
        prioridad=15,
    ),
    Materia(
        key="el-modelo-relacional-y-los-gestores-relacionales",
        epigraph_code="II.5.1",
        title="El modelo relacional y los gestores relacionales",
        resumen=(
            "La tabla y la relación: la unidad de información que toma sus valores de un dominio, "
            "qué"
            "gestor es relacional y cuál no, el motor de almacenamiento InnoDB, el gestor "
            "relacional"
            "de la nube compatible con MySQL y PostgreSQL, y qué hacer cuando la escalabilidad en "
            "lecturas se queda corta."
        ),
        patrones=_RELACIONAL,
        prioridad=30,
    ),
    Materia(
        key="los-gestores-concretos-oracle-access-y-sql-server",
        epigraph_code="II.5.1",
        title="Los gestores concretos: Oracle, Access y SQL Server por dentro",
        resumen=(
            "Los productos que salen en el examen: los elementos de Oracle, su estructura física, "
            "el"
            "espacio de tablas y los segmentos, la instancia con sus procesos y su memoria "
            "compartida, la vista materializada y sus alternativas, el lenguaje de procedimiento "
            "que"
            "se guarda compilado, cuándo conviene Access frente a una hoja de cálculo, qué es el "
            "servicio de aprendizaje automático de SQL Server y los puertos por defecto de los "
            "gestores."
        ),
        patrones=_GESTORES,
        prioridad=20,
    ),
    Materia(
        key="el-acceso-a-los-datos-odbc-jpa-y-los-marcos",
        epigraph_code="II.5.1",
        title="El acceso a los datos: ODBC, JPA y los marcos de persistencia",
        resumen=(
            "Cómo habla la aplicación con la base: qué es ODBC y qué no es un sistema de acceso a "
            "datos, las herramientas de Oracle para acceder a sus bases, Jakarta Persistence y "
            "JPA,"
            "Entity Framework, y las alternativas a las vistas materializadas."
        ),
        patrones=_ACCESO_A_DATOS,
        prioridad=25,
    ),
    Materia(
        key="las-bases-nosql-y-sus-cuatro-tipos",
        epigraph_code="II.5.1",
        title="Las bases NoSQL y sus cuatro tipos de almacenamiento",
        resumen=(
            "Lo que no es una tabla: qué es NoSQL, sus ventajas y sus características, el "
            "principio"
            "BASE frente a ACID, el teorema CAP, los cuatro tipos de almacenamiento —clave-valor, "
            "columnas, documentos y grafos—, cuál **no** es NoSQL, y Cassandra, MongoDB, Redis y "
            "Neo4j con sus orígenes."
        ),
        patrones=_NOSQL,
        prioridad=15,
    ),
    Materia(
        key="el-procesamiento-analitico-y-los-cubos-olap",
        epigraph_code="II.5.1",
        title="El procesamiento analítico y los cubos OLAP",
        resumen=(
            "La base para analizar, no para operar: qué arquitecturas se usan en un almacén de "
            "datos,"
            "qué términos son de los cubos multidimensionales y cuál no, y las siglas de la "
            "minería"
            "de datos y del gobierno del dato."
        ),
        patrones=_OLAP,
        prioridad=25,
    ),
    Materia(
        key="las-bases-orientadas-a-objetos-y-el-identificador",
        epigraph_code="II.5.1",
        title="Las bases de datos orientadas a objetos y el identificador único",
        resumen=(
            "Cuando la base guarda objetos y no filas: qué caracteriza a un gestor orientado a "
            "objetos, las características **obligatorias** del manifiesto de Malcolm Atkinson y "
            "cuál"
            "no lo es, el identificador de objeto único, los constructores de tipo de colección, "
            "el"
            "lenguaje OQL y cuál de los gestores es orientado a objetos."
        ),
        patrones=_ORIENTADAS_A_OBJETOS,
        prioridad=15,
    ),
    Materia(
        key="los-conceptos-de-la-orientacion-a-objetos",
        epigraph_code="II.5.1",
        title="Los conceptos de la orientación a objetos que usa el modelo",
        resumen=(
            "El vocabulario con el que se describe el modelo de objetos: la clase y la instancia, "
            "el"
            "polimorfismo, la sobrecarga de métodos con el mismo nombre y distintos argumentos, la "
            "ocultación del estado o encapsulación, la generalización entre clases y los lenguajes "
            "orientados a objetos puros."
        ),
        patrones=_ORIENTACION_A_OBJETOS,
        prioridad=35,
    ),
)

#: El orden del índice: primero el gestor —qué es, su arquitectura de tres niveles, las reglas de
#: Codd, las transacciones y el modelo relacional—, después los productos concretos y cómo accede
#: la aplicación a los datos, luego lo que no es relacional —NoSQL, analítico y objetos— y, al
#: final, el vocabulario de la orientación a objetos que ese modelo necesita.
ORDEN: tuple[str, ...] = (
    "que-es-un-sgbd-y-que-funciones-cumple",
    "la-arquitectura-ansi-sparc-y-sus-tres-niveles",
    "las-doce-reglas-de-codd-y-la-independencia",
    "las-transacciones-las-propiedades-acid-y-el-bloqueo",
    "el-modelo-relacional-y-los-gestores-relacionales",
    "los-gestores-concretos-oracle-access-y-sql-server",
    "el-acceso-a-los-datos-odbc-jpa-y-los-marcos",
    "las-bases-nosql-y-sus-cuatro-tipos",
    "el-procesamiento-analitico-y-los-cubos-olap",
    "las-bases-orientadas-a-objetos-y-el-identificador",
    "los-conceptos-de-la-orientacion-a-objetos",
)

__all__ = ["MATERIAS", "ORDEN"]
