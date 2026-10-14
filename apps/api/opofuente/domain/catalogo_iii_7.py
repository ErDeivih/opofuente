"""El catálogo de materias de III.7: aplicaciones web, HTML, XML, navegadores y script.

III.7 es un tema **técnico** de la web: lo que lo estructura son sus cinco epígrafes —las
aplicaciones web, el desarrollo front-end y en servidor, los lenguajes de marcado, los
navegadores y los lenguajes de programación web, y los lenguajes de script— y dentro de cada uno
el índice va **por asunto**, como en IV.7, III.5, III.9 y IV.2. Este catálogo los abre en doce
apartados:

- las **aplicaciones web y los gestores de contenido** en uno: qué es una aplicación web, los
  gestores de contenido, el posicionamiento y los buscadores, la web 2.0 y los mashups;
- la **arquitectura de una aplicación web** en uno: las capas y el modelo de tres capas, el
  cliente/servidor web, los servidores web y de aplicaciones y la intranet;
- el **desarrollo front-end** en uno: el diseño adaptativo y multidispositivo, el DOM, los
  frameworks de cliente, la accesibilidad web y la validación en el navegador;
- el **desarrollo web en servidor** en uno: los servlets y JSP, ASP.NET y Razor, el contenedor web
  y lo que se ejecuta en el servidor;
- el **desarrollo multiplataforma y multidispositivo** en uno: las aplicaciones móviles, sus
  plataformas y las herramientas para escribir una sola vez y desplegar en varias;
- los **servicios web** en uno: SOAP, WSDL, UDDI, REST, WS-Security y SAML, que es lo que hace
  hablarse a las aplicaciones web entre ellas;
- el **HTML y las hojas de estilo** en uno: las etiquetas y sus atributos, los formularios, las
  tablas, los marcos, el DOCTYPE, y el CSS con sus selectores;
- el **XML y sus derivaciones** en uno: el documento bien formado y su validación (DTD y esquema),
  el XPath y el XSLT, los procesadores, la web semántica (RDF y OWL), el VoiceXML y el WebDAV;
- los **navegadores** en uno: las versiones y los motores, las extensiones y la seguridad del
  navegador;
- el **JavaScript y el AJAX** en uno: el lenguaje del cliente, jQuery, JSON, las peticiones sin
  recargar la página y los entornos de ejecución del lenguaje;
- los **lenguajes de script** en uno: PHP (sus funciones, sus etiquetas y sus inclusiones) y los
  guiones del sistema (PowerShell y el shell).

Tres decisiones de los patrones, dichas donde se leen:

- **«aplicación web» y «servidor» van en los patrones débiles**, no en los propios: son las palabras
  que aparecen hablando de media asignatura, y con ellas como patrón propio cualquier pregunta que
  las mencione acabaría en el primer apartado aunque hablara de otra cosa;
- **«cookie» no es un patrón de los navegadores**: el banco tiene una pregunta de PHP sobre
  `setcookie()` y otra del navegador sobre el atributo que la protege de JavaScript. El patrón pide
  el contexto (`httponly`, «atributo de seguridad»), no la palabra suelta;
- **lo que es de otro tema no se lava**: el banco de III.7 trae preguntas de MySQL y del modelo
  relacional (que son de III.3 y III.4), de `iptables` y del correo (IV.3 y IV.9), de la firma
  electrónica y de la FNMT (I.6), de la archivística (III.8) y de textos legales que no son de este
  tema. Ninguna acaba en un cajón: van a la bandeja del propietario con su motivo
  (`Motivo.SIN_MATERIA_EN_EL_INDICE`), que es lo que manda el índice.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Las herramientas y las plataformas del desarrollo móvil que el banco nombra.
_PLATAFORMAS_MOVILES = (
    r"xamarin|cordova|phonegap|ionic|flutter|react native|\bmaui\b|appcelerator|"
    r"android studio|\bxcode\b|swift|kotlin"
)

#: Las siglas y los nombres de los servicios web de la familia SOAP y REST.
_SERVICIOS_WEB = (
    r"servicios? web|web services|\bsoap\b|\bwsdl\b|\buddi\b|\bwsil\b|\brest\b|restful|"
    r"ws- ?security|xml ?signature|\bsaml\b|arquitectura orientada a servicios|\bsoa\b|"
    r"\besb\b|bus de servicios"
)

#: Las funciones y las palabras propias de PHP, que es lo que el apartado de script pregunta.
_PHP = (
    r"\bphp\b|php ?[4578]|setcookie|array_shift|\bpcntl_exec\b|\bchr\b|\bexec\(\)|"
    r"include\(\)|require\(\)|etiqueta de comienzo de un fichero php"
)

MATERIAS: tuple[Materia, ...] = (
    # --- III.7.1 Aplicaciones web -----------------------------------------------------------------
    Materia(
        key="aplicaciones-web-y-cms",
        epigraph_code="III.7.1",
        title="Las aplicaciones web y los gestores de contenido",
        resumen=(
            "Qué es una aplicación web y con qué se publica: los gestores de contenido (y cuál "
            "usa cada lenguaje), la publicación y la distribución de la información, el "
            "posicionamiento en los buscadores y los enlaces entrantes, la web 2.0, las redes "
            "sociales y los mashups."
        ),
        patrones=(
            r"gestor(es)? de conten|\bcms\b|content management|wordpress|joomla|drupal|typo3|"
            r"prestashop|magento|plone",
            r"posicionamiento (web|en buscadores|natural)|\bseo\b|backlink|enlaces? (externos|"
            r"entrantes)|buscadores",
            r"mashup|web ?2 ?0|redes sociales|contenido generado por el usuario",
            r"sitio web|portal(es)? web|web corporativa|publicacion (web|de contenidos)|"
            r"gestion de contenidos",
        ),
        patrones_debiles=(r"aplicacion(es)? web", r"contenido(s)?", r"web"),
        prioridad=65,
    ),
    Materia(
        key="arquitectura-de-aplicaciones-web",
        epigraph_code="III.7.1",
        title="La arquitectura de una aplicación web",
        resumen=(
            "Cómo se organiza una aplicación web: las capas y el modelo de tres capas, la relación "
            "entre el cliente y el servidor, los servidores web y de aplicaciones (Apache, IIS y "
            "compañía) y lo que se sirve dentro de una intranet."
        ),
        patrones=(
            r"tres capas|3 capas|n ?capas|multicapa|arquitectura (de|en) capas|modelo de capas|"
            r"capa (de|del) (datos|presentacion|negocio|logica|servicios|aplicacion)",
            r"servidor(es)? (web|de aplicaciones|apache)|apache ?2|\bhttpd\b|\bnginx\b|\biis\b|"
            r"intranet|servidor de la subred",
            r"cliente ?servidor|peticiones? al servidor|se sirve|servir paginas|"
            r"directivas? (de|del) (apache|servidor)",
            r"balanceo|servidor de ficheros|despliegue de la aplicacion",
        ),
        patrones_debiles=(r"arquitectura", r"servidor(es)?", r"capa(s)?"),
        prioridad=75,
    ),
    # --- III.7.2 Desarrollo web front-end y en servidor, multiplataforma y multidispositivo -------
    Materia(
        key="desarrollo-front-end",
        epigraph_code="III.7.2",
        title="El desarrollo front-end: diseño adaptativo, DOM y accesibilidad",
        resumen=(
            "Lo que se ejecuta y se ve en el cliente: el diseño adaptativo y multidispositivo, el "
            "DOM y el árbol del documento, los frameworks de cliente, las plantillas, los "
            "formularios y la validación en el navegador, la accesibilidad web y el favicon."
        ),
        patrones=(
            r"front ?end|diseno (web|responsive|adaptativo)|responsive|diseno adaptativo|"
            r"multidispositivo|experiencia de usuario",
            r"\bdom\b|document object model|arbol de nodos|modelo de objetos del documento",
            r"framework.*(front|cliente|css|javascript)|bootstrap|angular|react|\bvue\b|"
            r"backbone|ember",
            r"favicon|plantilla(s)? web|pagina maestra|rejilla|\bgrid\b|layout",
            r"accesibilidad web|pautas de accesibilidad|\bwcag\b|paginas? accesibles|"
            r"diseno universal|lectores? de pantalla",
            r"validacion de datos de entrada|lado del cliente|en el navegador del usuario",
        ),
        patrones_debiles=(r"diseno", r"interfaz", r"cliente", r"usuario"),
        prioridad=70,
    ),
    Materia(
        key="desarrollo-web-en-servidor",
        epigraph_code="III.7.2",
        title="El desarrollo web en el servidor: servlets, JSP y ASP.NET",
        resumen=(
            "Lo que se ejecuta en el servidor: los servlets y su ciclo de vida, las páginas JSP y "
            "sus directivas y etiquetas, ASP y ASP.NET con Razor, el contenedor web, el patrón MVC "
            "aplicado a las aplicaciones web y la seguridad del propio desarrollo web (las "
            "recomendaciones de OWASP y la prevención de la inyección de código y del XSS)."
        ),
        patrones=(
            r"servlet|contenedor web|ciclo de vida de un servlet",
            r"\bjsp\b|jakarta server pages|javaserver pages|paginas? jsp|jsp:usebean",
            r"asp ?net|\basp\b|razor|paginas? maestras? en asp|webforms|mvc en asp|\bwebmatrix\b",
            r"lado (del )?servidor|en el servidor|script del servidor|\bcgi\b|modulo del servidor",
            r"framework.*(servidor|aplicaciones web)|\bmvc\b.*web|modelo vista controlador",
            r"\bowasp\b|\bxss\b|\bcsrf\b|inyeccion (de codigo|sql)|vulnerabilidad(es)?|"
            r"prevenir ataques",
        ),
        patrones_debiles=(r"servidor", r"aplicacion(es)? web", r"pagina(s)?"),
        prioridad=45,
    ),
    Materia(
        key="multiplataforma-y-multidispositivo",
        epigraph_code="III.7.2",
        title="El desarrollo multiplataforma y multidispositivo",
        resumen=(
            "Cómo se escribe una vez y se despliega en varios sitios: las aplicaciones móviles y "
            "sus plataformas (iOS y Android), las herramientas multiplataforma, el acceso desde "
            "teléfonos y PDA y las tecnologías de la web móvil."
        ),
        patrones=(
            r"multiplataforma|multidispositivo|aplicaciones? moviles?|apps? moviles?|"
            r"desarrollo de apps|desarrollo movil|aplicacion(es)? nativas?|hibridas?",
            r"\bios\b|android|iphone|ipad|smartphone|\bpda\b|tablet|telefonos? moviles?",
            _PLATAFORMAS_MOVILES,
            r"\bwap\b|web movil|moviles? wap|sincronizacion de datos entre equipos",
        ),
        patrones_debiles=(r"movil(es)?", r"dispositivo(s)?", r"plataforma(s)?"),
        prioridad=40,
    ),
    Materia(
        key="servicios-web",
        epigraph_code="III.7.2",
        title="Los servicios web y su interoperabilidad",
        resumen=(
            "Cómo se hablan las aplicaciones entre ellas: los servicios web y sus estándares "
            "(SOAP, WSDL y UDDI), el estilo REST, la seguridad de los mensajes (WS-Security y la "
            "firma XML), SAML y el intercambio de datos en JSON."
        ),
        patrones=(
            _SERVICIOS_WEB,
            r"interoperabilidad (entre|de) (aplicaciones|sistemas)|mensajes? (b2b|electronicos)|"
            r"descripcion de la interfaz de servicios",
            r"pasarela de servicios|intermediario.*servicios",
        ),
        patrones_debiles=(r"servicio(s)?", r"interoperabilidad", r"estandar(es)?"),
        prioridad=30,
    ),
    # --- III.7.3 Lenguajes: HTML, XML y sus derivaciones ------------------------------------------
    Materia(
        key="html-y-css",
        epigraph_code="III.7.3",
        title="El HTML y las hojas de estilo",
        resumen=(
            "El lenguaje de las páginas: las etiquetas de HTML y de HTML5 (las que llegan y las "
            "que se retiran), sus atributos, los formularios, las tablas, las listas, los marcos "
            "y las anclas, la declaración de tipo de documento y las hojas de estilo en cascada "
            "con sus selectores."
        ),
        patrones=(
            r"\bhtml\b|html ?[45]|xhtml|doctype|etiquetas? html|marcos?|frameset|iframe|"
            r"\bbody\b|\bhead\b",
            r"hojas? de estilo|\bcss\b|css ?[23]|selector(es)?|estilos?",
            r"cellpadding|atributos? (de|del|html)|anclas?|hipervinculo|vinculos? internos",
            r"lista(s)? (de|numerada|de definiciones)|tabla(s)? html|formulario html|"
            r"cuerpo de un documento html|comentario en html",
            r"entidades? html|caracteres? especiales|letra .* acentuada",
            r"paginas? web|documento html|contenido de una pagina",
        ),
        patrones_debiles=(r"etiqueta(s)?", r"documento", r"pagina(s)?", r"lenguaje(s)?"),
        prioridad=35,
    ),
    Materia(
        key="xml-y-sus-derivaciones",
        epigraph_code="III.7.3",
        title="El XML y sus derivaciones",
        resumen=(
            "El lenguaje de los datos: el documento XML bien formado y su validación (el DTD y el "
            "esquema), el XPath y el XSLT, los procesadores y sus modelos, la web semántica (RDF, "
            "OWL y sus lenguajes de consulta), el VoiceXML, el WebDAV y los demás derivados."
        ),
        patrones=(
            r"\bxml\b|\bxsd\b|\bdtd\b|xml schema|\bxpath\b|\bxslt\b|\bxsl\b|\bxlink\b|"
            r"namespaces?|\bcdata\b|bien formado|documento validador|procesador de documento",
            r"\bparser\b|\bsax\b|\bstax\b|modelo que procesa el documento",
            r"\brdf\b|\bowl\b|ontologias?|web semantica|sparql|\brdfs\b",
            r"voicexml|\bvxml\b|\bpls\b|\bssml\b|sintesis de voz|\bprompt\b",
            r"\bwebdav\b|propfind|proppatch|rfc ?4918",
            r"\bsvg\b|\bmathml\b|\bsmil\b|\bead\b|\beac\b",
        ),
        patrones_debiles=(r"esquema", r"derivad", r"consulta"),
        prioridad=25,
    ),
    # --- III.7.4 Navegadores y lenguajes de programación web --------------------------------------
    Materia(
        key="navegadores",
        epigraph_code="III.7.4",
        title="Los navegadores web",
        resumen=(
            "El programa con el que se ve la web: sus versiones y sus motores, las extensiones y "
            "los complementos, el almacenamiento y las cookies, la configuración de seguridad y la "
            "gestión de certificados desde el navegador."
        ),
        patrones=(
            r"navegador(es)?|internet explorer|\bedge\b|firefox|\bchrome\b|safari|\bopera\b|"
            r"extensiones? (del|para|de los) navegador|complementos? (del|para) (el )?navegador",
            r"version de internet explorer|navegador por defecto|"
            r"motores? de (renderizado|navegador)",
            r"httponly|modo incognito|almacenamiento local|seguridad (de|en) (los )?navegadores|"
            r"atributo de seguridad de las cookies",
            r"certificados? de usuario instalados|herramientas de desarrollo del navegador",
        ),
        patrones_debiles=(r"navegador(es)?", r"seguridad", r"version(es)?"),
        prioridad=15,
    ),
    Materia(
        key="javascript-y-ajax",
        epigraph_code="III.7.4",
        title="El JavaScript y el AJAX",
        resumen=(
            "El lenguaje de programación del cliente y lo que hace posible: el propio JavaScript y "
            "sus sentencias, jQuery y los demás marcos de cliente, AJAX y las peticiones sin "
            "recargar la página, el JSON como formato de intercambio y los entornos de ejecución "
            "del lenguaje."
        ),
        patrones=(
            r"\bjavascript\b|ecmascript|jquery|\bajax\b|xmlhttprequest|"
            r"asynchronous javascript|\bjson\b|\bmean\b|node ?js|\bv8\b|nashorn",
            r"lenguaje de (script|programacion) (del|en el) (lado )?(cliente|navegador)|"
            r"script en el cliente|scripts? en el navegador",
            r"console ?\.? ?log|===|setinterval|fetch\(|\bdocument\)|"
            r"objeto usado para recibir informacion",
            r"framework de pruebas para javascript|sentencia condicional en javascript",
        ),
        patrones_debiles=(r"javascript", r"script", r"cliente", r"datos"),
        prioridad=20,
    ),
    # --- III.7.5 Lenguajes de script -----------------------------------------------------------
    Materia(
        key="lenguajes-de-script",
        epigraph_code="III.7.5",
        title="Los lenguajes de script",
        resumen=(
            "Los lenguajes que se ejecutan sin compilar: PHP y sus funciones, sus etiquetas y sus "
            "inclusiones, y los guiones del sistema (PowerShell y sus cmdlets, el shell y sus "
            "guiones)."
        ),
        patrones=(
            _PHP,
            r"powershell|cmdlet|alias de otro cmdlet|\bbash\b|shell ?script|lenguaje de script|"
            r"scripts? (del|de) sistema",
            r"funcion(es)? (que|para) (realiza|realizar|borrar|devolver)|labor inversa",
        ),
        patrones_debiles=(r"script", r"funcion(es)?", r"lenguaje(s)?"),
        prioridad=20,
    ),
)

#: El orden del índice: primero la aplicación web y su arquitectura, después el desarrollo (cliente,
#: servidor, móvil y servicios), luego los lenguajes de marcado, y al final los navegadores, el
#: JavaScript y los lenguajes de script, que es como se estudia el tema.
ORDEN: tuple[str, ...] = (
    "aplicaciones-web-y-cms",
    "arquitectura-de-aplicaciones-web",
    "desarrollo-front-end",
    "desarrollo-web-en-servidor",
    "multiplataforma-y-multidispositivo",
    "servicios-web",
    "html-y-css",
    "xml-y-sus-derivaciones",
    "navegadores",
    "javascript-y-ajax",
    "lenguajes-de-script",
)

__all__ = ["MATERIAS", "ORDEN"]
