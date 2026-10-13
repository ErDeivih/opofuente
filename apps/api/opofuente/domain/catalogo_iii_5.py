"""El catálogo de materias de III.5 (arquitectura Java EE/Jakarta EE y plataforma .NET).

III.5 es un tema **técnico** de dos plataformas: lo que lo estructura son sus tres epígrafes —la
arquitectura, los componentes, la persistencia y la seguridad; las características, los elementos,
los lenguajes y las funciones de los dos entornos; y el desarrollo de interfaces— y dentro de cada
uno el índice va **por asunto**, como en IV.7, III.9, IV.2 y II.4. Este catálogo los abre en diez
apartados porque el banco se agrupa así de verdad:

- la **plataforma Jakarta EE** en uno: qué es y de dónde viene (Java EE, el JCP, el working group),
  sus versiones y sus JSR, sus servidores de aplicaciones y sus contenedores, y sus componentes
  (EJB, servlets, beans empresariales), que es lo que más se pregunta del tema;
- la **persistencia** en uno: JPA y sus anotaciones, el `EntityManager`, los ORM, JDBC y sus
  drivers, y la capa de acceso a datos;
- los **servicios y la seguridad** en uno: las siglas que el banco pregunta una a una (JMS, JTA,
  JNDI, JAAS, JACC, JASPIC, JSSE, SASL, JAX-WS, JAX-RS, JAXP, JAXB, SAAJ, JSON-P, JSON-B, JSTL…),
  la mensajería, las transacciones, la concurrencia y la autenticación y la autorización;
- la **plataforma .NET** en uno: el CLR y el código intermedio, los ensamblados y la BCL, los
  runtimes y sus versiones, NuGet y los proveedores de datos;
- el **lenguaje Java** en uno: la herencia, los modificadores y la visibilidad, las excepciones,
  las cadenas y los bucles (el banco pregunta mucho por código suelto de Java);
- el **entorno de ejecución y las herramientas de Java** en uno: JVM, JRE, JDK, el compilador, Maven
  y Ant, los IDE, la documentación y las bibliotecas (Jena, Lucene, generación de PDF);
- los **frameworks y los servicios de Java** en uno: Spring (Framework, MVC y Boot), los servlets,
  JSP y Jakarta Faces, las pruebas (JUnit y xUnit) y los motores de plantillas;
- los **lenguajes y las funciones de .NET** en uno: C# y Visual Basic, LINQ, Entity Framework y
  ADO.NET, WCF y las bibliotecas del ecosistema (NLog, PostSharp, NUnit, AutoMapper, MEF);
- la **arquitectura en capas y los empaquetados** en uno: presentación, negocio, acceso a datos y
  persistencia, qué es una capa y qué es un contenedor, y los formatos JAR, WAR y EAR;
- el **desarrollo de interfaces** en uno, que es el epígrafe III.5.3, hoy sin ninguna pregunta
  clasificada: WPF y Windows Forms, XAML, Silverlight, Blazor y .NET MAUI.

Cuatro decisiones de los patrones, dichas donde se leen:

- **`.NET` se escribe `\\bnet\\b`**: la normalización del proyecto quita los signos, así que «.NET»
  llega al patrón como la palabra `net` (`normalise` de `rag.py`). Con la frontera de palabra no
  casa dentro de «internet» ni de «netbeans», que son de Java;
- **las siglas de los servicios van una a una** y no con «siglas»: veintidós grupos del banco
  empiezan igual («¿Qué significan las siglas X en JavaEE?»), y un patrón sobre la palabra «siglas»
  se llevaría también las preguntas de siglas de .NET y de la propia arquitectura;
- **C, C++ y las preguntas de otros lenguajes no tienen apartado**: el banco trae una docena de
  preguntas de C y C++ (`printf`, `const`, inicializadores, herencia) que son de III.2 —lenguajes de
  programación— y no de aquí. No se lavan dentro de un apartado que no existe: van a la bandeja del
  propietario con su motivo;
- **lo mismo con ITIL, SAX, la web semántica y los «niveles» genéricos**: lo que no casa con
  ninguna materia del tema **no** acaba en un cajón. Se cuenta, se dice con su texto y va a la
  bandeja del propietario (`Motivo.SIN_MATERIA_EN_EL_INDICE`), que es lo que manda el índice.

Y una nota para el que lea el informe: la **tercera** materia de la familia Jakarta (los servicios y
las siglas) tiene la prioridad más baja de la plataforma Java a propósito, porque comparte el patrón
`java ee` con la materia de la arquitectura y hay que decidir por lo que la pregunta **nombra** —la
sigla— y no por la mención genérica a la plataforma.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Las siglas de los servicios de Jakarta EE, una a una: es lo que el banco pregunta de verdad
#: («¿Qué significan las siglas JMS en JavaEE?»). Con la palabra «siglas» a secas se llevarían
#: también las de .NET y las de la arquitectura, que son de otras materias.
_SIGLAS_JAKARTA = (
    r"\bjms\b|\bjta\b|\bjndi\b|\bjaas\b|\bjacc\b|\bjaspic\b|\bjsse\b|\bsasl\b|\bjaf\b|\bjaxr\b|"
    r"\bjax ?ws\b|\bjax ?rs\b|\bjax ?rpc\b|\bjaxp\b|\bjaxb\b|\bsaaj\b|\bjson ?p\b|\bjson ?b\b|"
    r"\bjstl\b|\bgss ?api\b|\bidl\b|\brmi\b|\biiop\b|\bjrmp\b|\bjms\b|\bjta\b|\bjaspic\b"
)

#: Los servidores de aplicaciones y las implementaciones que el banco nombra.
_SERVIDORES_JAKARTA = (
    r"glassfish|payara|wildfly|jboss|websphere|web ?logic|open ?liberty|apache tomcat|\btomcat\b"
)

#: Los lenguajes y las tecnologías del ecosistema .NET que el banco nombra por su nombre propio.
_TERMINOS_DOTNET = (
    r"\bc#\b|\bxaml\b|\blinq\b|entity framework|ado ?net|nhibernate|fluent ?nhibernate|"
    r"fluent ?validation|\bwcf\b|\bwwf\b|\bmef\b|managed extensibility|postsharp|automapper|nlog|"
    r"log4net|\bnunit\b|nuget|\bbcl\b|base class library|\bclr\b|clrver|\bmsil\b|\bcil\b|"
    r"codigo intermedio|visual basic|\bvb\b|\bblazor\b|webassembly|\bmono\b|\bmaui\b|\bml ?net\b|"
    r"silverlight|webmatrix|\buwp\b|windows forms|\bwpf\b|windows presentation foundation|"
    r"\bwwf\b|universal windows platform|visual studio"
)

MATERIAS: tuple[Materia, ...] = (
    # --- III.5.1 Arquitectura Java EE/Jakarta EE y plataforma .NET --------------------------------
    Materia(
        key="jakarta-ee-arquitectura",
        epigraph_code="III.5.1",
        title="La plataforma Jakarta EE: arquitectura, versiones, servidores y componentes",
        resumen=(
            "Qué es Java EE y qué es Jakarta EE, de dónde viene y quién lo gobierna (el JCP, el "
            "Jakarta EE Working Group), sus versiones y sus JSR, qué perfiles tiene (web, "
            "completo, MicroProfile), sus servidores de aplicaciones y sus contenedores, sus "
            "componentes (los EJB y los beans empresariales, los servlets, los módulos web) y la "
            "arquitectura en niveles de la plataforma."
        ),
        patrones=(
            r"jakarta ?ee|java ?ee|java enterprise edition|\bjee\b|\bj2ee\b",
            r"servidor(es)? de aplicaciones",
            r"\bejb\b|enterprise javabeans|beans? empresariales?",
            r"\bjcp\b|java community process|jakarta ee working group|working group",
            _SERVIDORES_JAKARTA,
            r"jsr ?\d|java specification request|\bjsr\b",
            r"arquitectura de (capas|niveles) de java|diseno de la plataforma",
            r"perfil (web|completo)|\bweb profile\b|\bfull profile\b|especificaciones? (de|existe|"
            r"debe cumplir) (jakarta|java)",
            r"que es (jakarta|java ?ee|jakarta ?ee)|version actual de jakarta|"
            r"objetivo principal de la arquitectura java",
        ),
        patrones_debiles=(r"plataforma", r"especificacion(es)?"),
        prioridad=60,
    ),
    Materia(
        key="jakarta-persistencia",
        epigraph_code="III.5.1",
        title="La persistencia en Jakarta EE: JPA, los ORM y JDBC",
        resumen=(
            "Cómo se guardan los datos en Jakarta EE: la especificación Jakarta Persistence "
            "(JPA) y sus anotaciones (entidad, tabla, columna, clave primaria, relaciones y "
            "estrategias de generación de valores), el EntityManager, los marcos de mapeo "
            "objeto-relacional (Hibernate y compañía), JDBC y sus drivers (el tipo 4 y el "
            "`ojdbc8.jar`), y la capa de acceso a datos y de persistencia."
        ),
        patrones=(
            r"persistencia|jakarta persistence|\bjpa\b|persistence api",
            r"\bentity ?manager\b|\borm\b|hibernate|eclipselink|mybatis|\bjdo\b|toplink",
            r"\bjdbc\b|ojdbc|driver(es)? (de|tipo|jdbc)",
            r"anotacion(es)? .*(entity|tabla|columna|clave primaria|relacion|persistir|"
            r"generacion de valores)",
            r"persistir en (jakarta|java)|capa de (acceso a datos|persistencia)",
            r"(uno|muchos) a (uno|muchos)|relacion de (uno|muchos)",
        ),
        patrones_debiles=(r"base de datos relacional", r"anotacion", r"origen de datos"),
        prioridad=30,
    ),
    Materia(
        key="jakarta-servicios-y-seguridad",
        epigraph_code="III.5.1",
        title="Los servicios y la seguridad de Jakarta EE",
        resumen=(
            "Los servicios de la plataforma Jakarta EE y sus siglas (mensajería, transacciones, "
            "directorio, XML, JSON, correo, conectores), la concurrencia y el procesamiento por "
            "lotes de los componentes, y la seguridad: la autenticación y la autorización de las "
            "aplicaciones."
        ),
        patrones=(
            _SIGLAS_JAKARTA,
            r"mensajeria|autenticacion|autorizacion|seguridad de la plataforma",
            r"concurrencia de los componentes|procesamiento por lotes|\bbatch\b|"
            r"transaccion(es)? (gestionadas|de la aplicacion|distribuidas)",
            r"servicios? (web|de la plataforma|de nombres)|descubrimiento de servicios",
            r"\bwsil\b|\bwsdl\b|\bsoap\b|\buddi\b|servicios web restful|\bws-",
            r"servlet|servlets",
        ),
        patrones_debiles=(r"siglas", r"\bapi\b", r"servicio(s)?"),
        prioridad=20,
    ),
    Materia(
        key="dotnet-plataforma",
        epigraph_code="III.5.1",
        title="La plataforma .NET: el CLR, los ensamblados y los runtimes",
        resumen=(
            "Qué es la plataforma .NET y cómo se ejecuta: el Common Language Runtime y la "
            "compilación del código intermedio, los ensamblados y la Base Class Library, los "
            "lenguajes que admite y los tipos comunes, sus implementaciones y runtimes (.NET "
            "Framework, .NET Core y sus versiones, Mono, UWP, .NET Standard, .NET MAUI), NuGet y "
            "los proveedores de datos."
        ),
        patrones=(
            _TERMINOS_DOTNET,
            r"\bnet\b",
            r"proveedores? de datos|codigo intermedio|compilar el codigo",
        ),
        patrones_debiles=(r"plataforma", r"framework", r"runtime", r"ensamblado"),
        prioridad=50,
    ),
    # --- III.5.2 Características, elementos, lenguajes y funciones en ambos entornos --------------
    Materia(
        key="java-lenguaje",
        epigraph_code="III.5.2",
        title="El lenguaje Java: clases, modificadores, excepciones y código",
        resumen=(
            "El lenguaje Java por dentro: las clases y la herencia (y cómo se impide), los "
            "modificadores y la visibilidad de métodos y atributos, las excepciones y las palabras "
            "reservadas, los tipos y sus conversiones, las cadenas y los bucles, y la lectura del "
            "código suelto que el banco pone en el enunciado."
        ),
        patrones=(
            r"en java\b|del lenguaje java|en el lenguaje java|de java\b",
            r"excepcion(es)?( de java| en java)?|palabra (reservada|da se utiliza en java)",
            r"herencia en java|modificador(es)?( final| abstract| native| static)?|"
            r"visibilidad (de|en) (metodos|atributos|clases)",
            r"codigo (java|valido en java)|siguiente codigo en java|variable elegido|"
            r"variable sencillo",
            r"tipo superior a un tipo inferior|polimorfismo|sobrecarga|sobrescritura",
            r"impedir que se pueda heredar|palabra reservada se utiliza en java",
        ),
        patrones_debiles=(
            r"\bjava\b",
            r"clase(s)?",
            r"variable",
            r"bucle|while|for\b",
            r"\barray\b|arrays?",
            r"\bstring\b|cadena(s)? de texto",
            r"int\b|\bvoid\b|\bprivate\b|\bstatic\b|\bpublic\b",
        ),
        prioridad=70,
    ),
    Materia(
        key="java-entorno-y-herramientas",
        epigraph_code="III.5.2",
        title="El entorno de ejecución y las herramientas de Java",
        resumen=(
            "Dónde y con qué se ejecuta (y se construye) Java: la máquina virtual y el entorno de "
            "ejecución (JVM, JRE, JDK, el compilador y la compilación justo a tiempo), las "
            "herramientas de construcción y de dependencias (Maven, Ant, Ivy), los entornos de "
            "desarrollo, la documentación del código y las bibliotecas de Java (la web semántica, "
            "los motores de búsqueda de texto y la generación de documentos)."
        ),
        patrones=(
            r"\bjvm\b|\bjre\b|\bjd ?k\b|maquina virtual|maquina virtual de java|"
            r"just in time|\bjit\b|bytecode|codigo maquina.*java|compilador.*java",
            r"maven|\bant\b|\bivy\b|gradle|gestion y construccion de proyectos|"
            r"herramienta de apache|construir y desplegar aplicaciones java|"
            r"gestion de dependencias",
            r"javadoc|documentacion (html )?a partir del codigo|"
            r"documentacion html a partir del codigo fuente",
            r"biblioteca de apache|motor de busqueda de texto|\bjena\b|\blucene\b|"
            r"web semantica en java|generar archivos? pdf|"
            r"api de java para el procesamiento",
            r"entorno integrado de desarrollo|\bide\b|netbeans|intellij",
            r"java web start|\bjnlp\b|java card|java embedded",
            r"lenguaje java (esta|es) (interpretado|compilado)|"
            r"intermediario entre el sistema operativo",
        ),
        patrones_debiles=(r"herramienta(s)?", r"biblioteca(s)?", r"entorno"),
        prioridad=45,
    ),
    Materia(
        key="frameworks-y-servicios-java",
        epigraph_code="III.5.2",
        title="Los frameworks y las pruebas del lado servidor en Java",
        resumen=(
            "Con qué se construye una aplicación Java del lado servidor: los servlets, JSP y "
            "Jakarta Faces (y sus etiquetas y directivas), Spring (Framework, MVC, Boot y sus "
            "subproyectos), los demás frameworks web y de microservicios, los motores de "
            "plantillas, el patrón MVC y las pruebas (JUnit, xUnit y las de rendimiento)."
        ),
        patrones=(
            r"spring|\bspring ?boot\b",
            r"servlet",
            r"\bjsp\b|jakarta faces|\bjsf\b|facelets|struts|tapestry|wicket|grails|groovy|vaadin|"
            r"javaserver faces",
            r"junit|\bxunit\b|\btestng\b|pruebas? (unitarias|de (estres|rendimiento|carga|"
            r"integracion))",
            r"motor de plantillas|thymeleaf|velocity|freemarker|jade",
            r"microprofile|patron de diseno mvc|\bmvc\b",
            r"frameworks? (java|de apache|web|para)|framework.*aplicaciones web",
            r"servicios web restful|jersey|\bcxf\b|\baxis\b|restful",
            r"jee? ?7|java ee 7",
        ),
        patrones_debiles=(r"framework(s)?", r"servicios? web", r"aplicaciones? web"),
        prioridad=35,
    ),
    Materia(
        key="dotnet-lenguajes-y-funciones",
        epigraph_code="III.5.2",
        title="Los lenguajes y las funciones de la plataforma .NET",
        resumen=(
            "Con qué se programa en .NET y qué trae: los lenguajes (C# y Visual Basic) y sus "
            "características (los arrays, las excepciones, la opcionalidad de tipos), el acceso a "
            "datos (ADO.NET, Entity Framework y los proveedores), los servicios y las herramientas "
            "(WCF, MEF y los marcos de extensibilidad), las bibliotecas de registro (NLog y "
            "log4Net) y las de pruebas (NUnit)."
        ),
        patrones=(
            r"\bc#\b|visual basic|\bvb\b",
            r"\blinq\b|entity framework|ado ?net|nhibernate|fluent ?(nhibernate|validation)",
            r"\bwcf\b|\bmef\b|managed extensibility|\bwwf\b|windows workflow",
            r"nlog|log4net|postsharp|automapper|\bnunit\b",
            r"asp ?net|razor|\bblazor\b|webmatrix|lenguajes? (de programacion )?(que ofrece|"
            r"soportados|del)",
            r"\.?net\b.*(lenguajes|funciones|biblioteca|herramienta|implementaciones)",
        ),
        patrones_debiles=(r"\bnet\b", r"lenguaje(s)?", r"biblioteca(s)?", r"herramienta(s)?"),
        prioridad=40,
    ),
    Materia(
        key="componentes-y-capas",
        epigraph_code="III.5.2",
        title="La arquitectura en capas y los empaquetados",
        resumen=(
            "Cómo se organiza una aplicación por dentro: qué es una capa y en cuáles se divide "
            "(presentación o cliente, negocio o lógica, acceso a datos y persistencia), qué "
            "función tiene cada nivel, qué es un contenedor, y los empaquetados y descriptores "
            "de despliegue (JAR, WAR y EAR)."
        ),
        patrones=(
            r"capa (de |del )?(negocio|presentacion|acceso a datos|datos|persistencia|logica|"
            r"servicios|cliente)|capas? (de una|en que se divide|del servidor)|varias capas|"
            r"n-?capas|multicapa|tres capas|3 capas",
            r"que es una capa|nivel de cliente|funcion realiza el nivel|"
            r"que tecnologia (no )?(existe|pertenece) en la capa",
            r"empaquetad|\bwar\b|\bjar\b|\bear\b|descriptor de despliegue",
            r"que es un contenedor|contenedor(es)? (de aplicaciones|web|ejb)",
            r"\bitil\b|gestion de servicios",
        ),
        patrones_debiles=(r"capa(s)?", r"nivel(es)?", r"componente(s)?"),
        prioridad=55,
    ),
    # --- III.5.3 Desarrollo de interfaces ---------------------------------------------------------
    Materia(
        key="interfaces-de-usuario",
        epigraph_code="III.5.3",
        title="El desarrollo de interfaces de usuario",
        resumen=(
            "Con qué se construye la interfaz: Windows Presentation Foundation y Windows Forms, el "
            "lenguaje de marcado XAML, Silverlight, Blazor y las plataformas de interfaz web y "
            "multiplataforma de los dos entornos."
        ),
        patrones=(
            r"\bwpf\b|windows presentation foundation|windows forms|silverlight|\bxaml\b|\bmaui\b|"
            r"interfaz(es)? de usuario|\bunity\b|aplicaciones? de escritorio",
            r"plataforma .*interfaces de usuario web interactivas|"
            r"aplicaciones moviles y de escritorio nativas",
        ),
        patrones_debiles=(r"interfaz(es)?", r"presentacion", r"escritorio"),
        prioridad=25,
    ),
)

#: El orden del índice: primero la plataforma Jakarta, después .NET y la arquitectura; luego los
#: lenguajes y las herramientas de los dos entornos; y al final las interfaces (III.5.3), que es
#: como se estudia el tema.
ORDEN: tuple[str, ...] = (
    "jakarta-ee-arquitectura",
    "jakarta-persistencia",
    "jakarta-servicios-y-seguridad",
    "dotnet-plataforma",
    "java-lenguaje",
    "java-entorno-y-herramientas",
    "frameworks-y-servicios-java",
    "dotnet-lenguajes-y-funciones",
    "componentes-y-capas",
    "interfaces-de-usuario",
)

__all__ = ["MATERIAS", "ORDEN"]
