"""El catálogo de materias de III.3 (lenguajes de interrogación, ANSI SQL, procedimientos
almacenados y disparadores).

III.3 es el tema **técnico** más homogéneo del bloque III: de sus 181 grupos de preguntas, **103 no
traen epígrafe** y el resto se reparte entre los cuatro epígrafes oficiales —el lenguaje de
interrogación (5 grupos), el estándar ANSI SQL (67), los procedimientos almacenados (3) y los
eventos y disparadores (3)—. El banco entero habla de SQL, así que el índice va **por asunto dentro
de SQL**, que es lo que hace que un tema de una sola materia se pueda estudiar y redactar por
partes.

Once apartados:

- **el lenguaje de interrogación y sus lenguajes** en uno (III.3.1): qué es un lenguaje de
  interrogación, qué facilidades da el lenguaje de definición de datos, a qué se llama recuperar,
  insertar, eliminar y modificar, el cálculo relacional y para qué sirve un sistema gestor;
- **el álgebra relacional** aparte (III.3.1): las operaciones y cuáles son unarias, y los comandos
  de formato de informes de SQL*Plus;
- **las sentencias de definición de datos** en uno (III.3.2): CREATE, ALTER, DROP y TRUNCATE, qué
  permite ALTER TABLE, cómo se crea una tabla, un esquema o un dominio y qué pasa al borrar un
  dominio con CASCADE;
- **la consulta SELECT y sus filtros** en uno (III.3.2), que es el bloque más grande: la cláusula
  WHERE y el predicado LIKE, BETWEEN, CASE, DISTINCT, ORDER BY y su criterio de ordenación, las
  subconsultas y la secuencia correcta de las cláusulas;
- **las funciones de agregación y la agrupación** (III.3.2): GROUP BY y HAVING, la función COUNT y
  las demás de agregado, y qué pasa al mezclar una función de agregación con la lista de selección;
- **las combinaciones de tablas** (III.3.2): JOIN interior, externo, natural y cruzado, la
  auto-combinación, el producto cartesiano y UNION;
- **modificar los datos y las transacciones** (III.3.2): INSERT, UPDATE y DELETE frente a TRUNCATE,
  COMMIT, ROLLBACK y los puntos de recuperación, y los niveles de aislamiento con las lecturas
  sucias;
- **las restricciones de integridad y las claves** (III.3.2): PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT
  NULL, CHECK y DEFAULT, la integridad referencial y qué ocurre al borrar o actualizar una clave
  referenciada;
- **el control de acceso y los privilegios** (III.3.2): GRANT y REVOKE, a qué familia de lenguajes
  pertenecen, cómo se dan permisos sobre una columna y qué significa cada lenguaje;
- **las vistas, los índices y los tipos de datos** (III.3.2): crear y borrar vistas, los índices y
  los que no admiten duplicados, los tipos de datos numéricos, de cadena y de fecha y el tamaño por
  defecto de un VARCHAR en SQL-92;
- y **el estándar, la sintaxis y las versiones de SQL** (III.3.2): qué significa la sigla, quién lo
  escogió como estándar en 1986, en qué año lo desarrolló IBM, qué versión introdujo las
  expresiones regulares, las consultas recursivas y los disparadores, y la sintaxis de SQL Server y
  Transact-SQL con sus comentarios y sus parámetros de salida;
- los **procedimientos almacenados** (III.3.3): por qué es buena práctica manejar transacciones
  dentro, por qué son más eficientes que lanzar consultas desde la aplicación, las excepciones no
  manejadas en PL/SQL, los parámetros de entrada y de salida y cómo se crean, modifican y ejecutan;
- y los **disparadores y los eventos** (III.3.4): qué es un disparador, qué significa FOR EACH ROW,
  cuándo se dispara —antes o después del evento— y qué operaciones no tienen sentido dentro.

Cuatro decisiones de los patrones, dichas donde se leen:

- **«sentencia», «tabla», «cláusula» y «SQL» están en los débiles**, no como patrón propio: salen en
  casi todos los enunciados del tema, así que si contaran igual que los demás, el apartado que
  primero los mencionara se llevaría media asignatura. Deciden solo cuando ninguna materia ha casado
  con sus patrones propios;
- **las restricciones se piden por su nombre inglés y por su nombre español** —`constraint`,
  `restricciones de integridad`, `clave primaria`, `clave ajena`, `foranea`—: el banco usa las dos
  formas y las dos significan lo mismo aquí;
- **el disparador se pide como `trigger` y como `disparador`**, y `FOR EACH ROW` se busca literal
  porque es lo que distingue la pregunta de fila de la de sentencia;
- y **lo que es de otro tema no se lava**, y aquí hay bastante: el estándar **ANSI/TIA-942-B** de la
  zona de un CPD y el TIER de un CPD son de **IV.2**; el formato de imagen **JPG** y el sistema de
  ficheros de un CD-ROM son de **II.3**; y el **cable de par trenzado** con su estándar de extremos
  es de **IV.10**. Son 12 de las 201 preguntas con clave utilizable y van a la bandeja del
  propietario con su motivo (`Motivo.SIN_MATERIA_EN_EL_INDICE`). Crearles un apartado aquí sería
  exactamente lo que no se hace: lavar preguntas de otra materia dentro de un tema que no las tiene.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Qué es un lenguaje de interrogación y qué familia es cada uno.
_EL_LENGUAJE = (
    r"lenguaje(s)? (de interrogacion|de consulta)",
    r"a que (se )?le? denomina.*(interrogacion|consulta)",
    r"que es un lenguaje de (interrogacion|consulta)",
    r"sistema gestor de base de datos|\bsgbd\b",
    r"facilidades|serie de facilidades",
    r"al lenguaje que interactua",
    r"recuperar,? insertar,? eliminar y modificar",
    r"bases de datos relacionales",
    r"\bcrud\b",
)

#: El álgebra y el cálculo relacional, y los informes de SQL*Plus.
_ALGEBRA_RELACIONAL = (
    r"algebra relacional|calculo relacional",
    r"operacion(es)? unaria",
    r"\bunaria\b|\bbinaria\b.*(operacion|algebra)",
    r"sql ?plus|formatos de informes",
    r"operador(es)? (de|del) algebra",
)

#: Las sentencias que definen objetos: DDL.
_DEFINIR_OBJETOS = (
    r"\balter table\b|\balter\b",
    r"\bdrop\b|\bcreate\b|\btruncate\b",
    r"crear (una|un) (tabla|esquema|dominio|indice|vista|base de datos|procedimiento)",
    r"sentencia de (creacion|definicion)",
    r"componente logico de control",
    r"eliminar un indice|crear un dominio|borrar un dominio|cascade",
    r"anadir una nueva columna",
)

#: La consulta SELECT, sus filtros y su orden.
_LA_CONSULTA = (
    r"\bselect\b|\bwhere\b|\bfrom\b",
    r"clausula(s)? (where|order by|distinct|having|group by)",
    r"\border by\b|\bgroup by\b|\bhaving\b|\bdistinct\b",
    r"criterio de ordenacion|ordenar los registros|orden de las filas",
    r"predicado (between|like|in)|\bbetween\b|\blike\b",
    r"subconsulta",
    r"sentencia correcta de consulta|consulta en sql|en la consulta",
    r"secuencia de parametros en el orden correcto",
    r"operador case|la funcion del operador case|\bcase\b",
    r"comodin",
    r"filtro|filtrar (filas|grupos)",
)

#: Las funciones de agregación y la agrupación.
_AGREGACION = (
    r"funcion(es)? de agregacion|de agregado|agregacion",
    r"\bcount\b|\bavg\b|\bsum\b|\bmax\b|\bmin\b",
    r"grupo de agregacion",
    r"agrupar filas|agrupar por",
)

#: Las combinaciones de tablas.
_COMBINACIONES = (
    r"\bjoin\b|\bunion\b",
    r"combinacion de (tablas|una tabla)",
    r"combinar dos tablas|combinacion de una tabla consigo misma",
    r"producto cartesiano|\bcross join\b|\bnatural join\b|left join|right join|full join",
    r"tablas relacionadas",
)

#: Modificar los datos y las transacciones.
_DATOS_Y_TRANSACCIONES = (
    r"modificar datos existentes|insertar datos|anadir un nuevo registro",
    r"\binsert\b|\bupdate\b|\bdelete\b|\bcommit\b|\brollback\b|\bsavepoint\b",
    r"deshacer una transaccion|confirmar los cambios|punto de recuperacion",
    r"nivel de aislamiento|lecturas sucias|autocommit|transaccion(es)?",
    r"eliminar (el contenido|los datos|todos los registros|todos los datos)",
)

#: Las restricciones de integridad y las claves.
_RESTRICCIONES = (
    r"constraint|restriccion(es)? de integridad|restriccion de columna",
    r"clave (primaria|ajena|foranea|candidata)",
    r"primary key|foreign key|\bunique\b|\bcheck\b|not null|valor por defecto|\bdefault\b",
    r"integridad referencial",
    r"no puede tener valores nulos",
    r"no permite valores duplicados",
)

#: Los privilegios y el control de acceso.
_PRIVILEGIOS = (
    r"\bgrant\b|\brevoke\b",
    r"privilegios|permisos de select|controlar el acceso a los datos",
    r"\bdcl\b",
    r"otorgar privilegios|retirar privilegios|dar permisos",
    r"usuario de la bd|se le asigne permisos",
)

#: Las vistas, los índices y los esquemas.
_VISTAS_E_INDICES = (
    r"\bvista\b|\bview\b|\bdrop view\b",
    r"tabla virtual",
    r"\bindice(s)?\b|\bindex\b",
    r"crear un esquema|esquema de la base de datos",
    r"todos los objetos creados en el mismo",
)

#: Los tipos de datos y la sintaxis concreta.
_TIPOS_Y_SINTAXIS = (
    r"tipo(s)? de dato(s)?",
    r"\bvarchar\b|\bchar\b|\binteger\b|\bnumeric\b|\bdate\b|\bnumber\b|\bfloat\b|\bdecimal\b",
    r"tamano por defecto",
    r"cadena(s)? de caracteres|numeros enteros",
    r"almacenar fechas",
    r"sintaxis|sintacticamente correcta|comentarios en una linea",
    r"transact|sql server|\bmysql\b|\bpostgresql\b|\boracle\b|\bmariadb\b",
    r"lenguaje de procedimiento",
    r"to_char|to_date|to_number|funcion(es)? de conversion|mascara de formato",
)

#: El estándar, su historia y sus versiones.
_EL_ESTANDAR = (
    r"ansi sql|ansi ?/? ?iso ?sql|ansi iso sql|\biso ?9075\b",
    r"sql ?92|sql ?99|sql ?3\b|sql ?: ?1999|sql ?2016",
    r"estandar (ansi|iso) sql|estandar sql",
    r"que significa sql|que version de sql|ano fue desarrollado|que organizacion escogio",
    r"parte del (lenguaje )?sql|pertenece al (lenguaje )?sql",
    r"se cataloga dentro del lenguaje sql",
    r"categorias? de sentencias",
    r"\bddl\b|\bdml\b|\bdcl\b",
    r"que lenguaje se usa para crear",
    r"lenguajes? de definicion de datos",
)

#: Los procedimientos almacenados.
_PROCEDIMIENTOS = (
    r"procedimiento(s)? almacenado",
    r"pl ?/? ?sql|\bplsql\b",
    r"parametro(s)? (de salida|de entrada)|palabra clave.*parametro",
    r"excepcion no manejada|manejar transacciones dentro",
    r"desde el punto de vista del rendimiento",
)

#: Los disparadores y los eventos.
_DISPARADORES = (
    r"\btrigger(s)?\b|disparador(es)?",
    r"\bfor each row\b|\bevento(s)?\b",
    r"antes del evento|despues del evento|\bbefore\b|\bafter\b",
)

MATERIAS: tuple[Materia, ...] = (
    # --- III.3.1 Lenguajes de interrogación de bases de datos -----------------------------------
    Materia(
        key="el-lenguaje-de-interrogacion-y-sus-familias",
        epigraph_code="III.3.1",
        title="El lenguaje de interrogación y las familias de sentencias",
        resumen=(
            "Qué es un lenguaje de interrogación y para qué sirve: las facilidades que da el "
            "lenguaje de definición de datos, a qué se llama recuperar, insertar, eliminar y "
            "modificar la información, el papel del sistema gestor y el término CRUD."
        ),
        patrones=_EL_LENGUAJE,
        patrones_debiles=(r"lenguaje", r"interrogacion"),
        prioridad=35,
    ),
    Materia(
        key="el-algebra-y-el-calculo-relacional",
        epigraph_code="III.3.1",
        title="El álgebra y el cálculo relacional, y los informes de SQL*Plus",
        resumen=(
            "La base formal de las consultas: el cálculo relacional como lenguaje de "
            "interrogación,"
            "las operaciones del álgebra relacional y cuáles son unarias, y los comandos con los "
            "que SQL*Plus da formato a los informes."
        ),
        patrones=_ALGEBRA_RELACIONAL,
        patrones_debiles=(r"relacional",),
        prioridad=20,
    ),
    # --- III.3.2 Estándar ANSI SQL --------------------------------------------------------------
    Materia(
        key="las-sentencias-de-definicion-de-objetos",
        epigraph_code="III.3.2",
        title="Las sentencias de definición de objetos (DDL)",
        resumen=(
            "Crear, cambiar y borrar lo que hay dentro de la base: qué permite ALTER TABLE, cómo "
            "se"
            "crea una tabla, un esquema, un dominio o un índice, qué hace DROP y TRUNCATE, y qué "
            "ocurre con las referencias a un dominio al borrarlo con CASCADE."
        ),
        patrones=_DEFINIR_OBJETOS,
        patrones_debiles=(r"tabla(s)?", r"esquema", r"eliminar"),
        prioridad=30,
    ),
    Materia(
        key="la-consulta-select-sus-clausulas-y-sus-filtros",
        epigraph_code="III.3.2",
        title="La consulta SELECT, sus cláusulas y sus filtros",
        resumen=(
            "El corazón de SQL: la sentencia SELECT con sus cláusulas y el orden en que aparecen, "
            "el filtro WHERE, los predicados LIKE, BETWEEN y CASE, la eliminación de duplicados, "
            "el criterio de ordenación y las subconsultas."
        ),
        patrones=_LA_CONSULTA,
        patrones_debiles=(r"consulta", r"sentencia", r"select"),
        prioridad=40,
    ),
    Materia(
        key="las-funciones-de-agregacion-y-la-agrupacion",
        epigraph_code="III.3.2",
        title="Las funciones de agregación y la agrupación de filas",
        resumen=(
            "Resumir muchas filas en una: qué funciones de agregado admite el estándar, qué hace "
            "COUNT, para qué sirven GROUP BY y HAVING y qué ocurre cuando en la lista de selección "
            "se mezcla una función de agregación con columnas."
        ),
        patrones=_AGREGACION,
        patrones_debiles=(r"agregacion", r"fila(s)?"),
        prioridad=15,
    ),
    Materia(
        key="las-combinaciones-de-tablas",
        epigraph_code="III.3.2",
        title="Las combinaciones de tablas",
        resumen=(
            "Consultar varias tablas a la vez: la combinación interna y las externas, la natural y "
            "la cruzada, qué devuelve cada una, la combinación de una tabla consigo misma, el "
            "producto cartesiano y la unión de dos consultas."
        ),
        patrones=_COMBINACIONES,
        patrones_debiles=(r"combinacion", r"tablas"),
        prioridad=15,
    ),
    Materia(
        key="modificar-los-datos-y-las-transacciones",
        epigraph_code="III.3.2",
        title="Modificar los datos y las transacciones",
        resumen=(
            "Cambiar lo que hay guardado, y poder deshacerlo: INSERT, UPDATE y DELETE frente a "
            "TRUNCATE, el COMMIT y el ROLLBACK, los puntos de recuperación y los niveles de "
            "aislamiento con las lecturas sucias."
        ),
        patrones=_DATOS_Y_TRANSACCIONES,
        patrones_debiles=(r"modificar", r"transaccion", r"eliminar"),
        prioridad=25,
    ),
    Materia(
        key="las-restricciones-de-integridad-y-las-claves",
        epigraph_code="III.3.2",
        title="Las restricciones de integridad y las claves",
        resumen=(
            "Las reglas que la base hace cumplir sola: la clave primaria y la ajena, la unicidad, "
            "el no nulo, el valor por defecto y las comprobaciones, la integridad referencial y "
            "qué"
            "ocurre al borrar o actualizar una fila referenciada."
        ),
        patrones=_RESTRICCIONES,
        patrones_debiles=(r"integridad", r"clave"),
        prioridad=20,
    ),
    Materia(
        key="los-privilegios-y-el-control-de-acceso",
        epigraph_code="III.3.2",
        title="Los privilegios y el control de acceso a los datos",
        resumen=(
            "Quién puede hacer qué: GRANT y REVOKE, a qué familia de sentencias pertenecen, cómo "
            "se"
            "concede permiso para actualizar una sola columna sin poder dar de alta empleados, y "
            "qué lenguaje controla el acceso a los datos."
        ),
        patrones=_PRIVILEGIOS,
        patrones_debiles=(r"privilegios", r"permisos", r"usuario"),
        prioridad=20,
    ),
    Materia(
        key="las-vistas-los-indices-y-los-esquemas",
        epigraph_code="III.3.2",
        title="Las vistas, los índices y los esquemas",
        resumen=(
            "Lo que se ve y lo que acelera: qué es una vista y cómo se crea y se borra, la vista "
            "como tabla virtual, los índices y cuál no admite valores duplicados, y el esquema de "
            "la base de datos con su propietario."
        ),
        patrones=_VISTAS_E_INDICES,
        patrones_debiles=(r"vista", r"indice"),
        prioridad=25,
    ),
    Materia(
        key="los-tipos-de-datos-y-la-sintaxis",
        epigraph_code="III.3.2",
        title="Los tipos de datos y la sintaxis concreta",
        resumen=(
            "Con qué se declara cada columna y cómo se escribe: los tipos de datos numéricos, de "
            "cadena y de fecha del estándar y su tamaño por defecto, y la sintaxis concreta de SQL "
            "Server, MySQL, PostgreSQL y Oracle (Transact-SQL, comentarios y parámetros)."
        ),
        patrones=_TIPOS_Y_SINTAXIS,
        patrones_debiles=(r"sintaxis", r"tipo"),
        prioridad=45,
    ),
    Materia(
        key="el-estandar-sql-su-historia-y-sus-versiones",
        epigraph_code="III.3.2",
        title="El estándar SQL, su historia y sus versiones",
        resumen=(
            "De dónde viene y qué dice el estándar: qué significa la sigla, quién lo escogió como "
            "lenguaje estándar en 1986 y en qué año lo desarrolló IBM, qué versiones hay (SQL-92, "
            "SQL:1999) y cuál introdujo las expresiones regulares, las consultas recursivas y los "
            "disparadores, y a qué familia —DDL, DML o DCL— pertenece cada sentencia."
        ),
        patrones=_EL_ESTANDAR,
        patrones_debiles=(r"sql",),
        prioridad=50,
    ),
    # --- III.3.3 Procedimientos almacenados -----------------------------------------------------
    Materia(
        key="los-procedimientos-almacenados",
        epigraph_code="III.3.3",
        title="Los procedimientos almacenados",
        resumen=(
            "El código que vive dentro de la base: por qué es buena práctica manejar las "
            "transacciones dentro del procedimiento, por qué es más eficiente que lanzar consultas "
            "desde la aplicación, qué pasa con una excepción no manejada en PL/SQL, los parámetros "
            "de entrada y de salida y cómo se crean, modifican y ejecutan."
        ),
        patrones=_PROCEDIMIENTOS,
        patrones_debiles=(r"procedimiento", r"almacenado"),
        prioridad=10,
    ),
    # --- III.3.4 Eventos y disparadores ---------------------------------------------------------
    Materia(
        key="los-disparadores-y-los-eventos",
        epigraph_code="III.3.4",
        title="Los disparadores y los eventos",
        resumen=(
            "Lo que se ejecuta solo cuando algo pasa: qué es un disparador y qué es un evento, "
            "cuándo se dispara —antes o después del cambio, y por cada fila o por sentencia—, y "
            "qué"
            "operaciones no tienen sentido dentro de uno."
        ),
        patrones=_DISPARADORES,
        patrones_debiles=(r"evento",),
        prioridad=10,
    ),
)

#: El orden del índice: primero qué es el lenguaje y su base formal, después las sentencias —las
#: que definen objetos, la consulta, los resúmenes, las combinaciones, los cambios y las
#: transacciones, las restricciones y los privilegios—, luego lo que se ve y cómo se declara, y al
#: final el estándar con su historia y el código que vive dentro de la base.
ORDEN: tuple[str, ...] = (
    "el-lenguaje-de-interrogacion-y-sus-familias",
    "el-algebra-y-el-calculo-relacional",
    "el-estandar-sql-su-historia-y-sus-versiones",
    "los-tipos-de-datos-y-la-sintaxis",
    "las-sentencias-de-definicion-de-objetos",
    "la-consulta-select-sus-clausulas-y-sus-filtros",
    "las-funciones-de-agregacion-y-la-agrupacion",
    "las-combinaciones-de-tablas",
    "modificar-los-datos-y-las-transacciones",
    "las-restricciones-de-integridad-y-las-claves",
    "las-vistas-los-indices-y-los-esquemas",
    "los-privilegios-y-el-control-de-acceso",
    "los-procedimientos-almacenados",
    "los-disparadores-y-los-eventos",
)

__all__ = ["MATERIAS", "ORDEN"]
