"""El catálogo de materias de III.8 (accesibilidad, diseño universal, usabilidad y seguridad en el
desarrollo de los sistemas).

III.8 es un tema **técnico y normativo a la vez**, y su banco lo enseña: de sus **147 grupos de
preguntas, 124 no traen epígrafe** (el 84 %, el banco más descolgado de la serie) y hablan de dos
cosas que el temario junta en un solo tema:

- la **accesibilidad y la usabilidad**: las pautas WCAG en sus versiones 2.0, 2.1 y 2.2 con sus
  principios, sus pautas, sus criterios de conformidad y sus niveles; WAI-ARIA y los atributos del
  marcado; los lectores de pantalla y las herramientas de evaluación; los principios de Nielsen y la
  definición de usabilidad de la ISO; el diseño universal y sus siete principios; y el **Real
  Decreto
  1112/2018** con las normas UNE y AENOR que lo acompañan;
- y los **conceptos de seguridad en el desarrollo**: OWASP y la inyección, el análisis estático del
  código, la validación de la entrada, las consultas preparadas, el control de acceso roto, la
  falsificación de peticiones, la autenticación y la biometría, y la disponibilidad.

Diez apartados, en el orden en que se estudia:

- **la accesibilidad y el diseño universal** (III.8.1): qué es que un sitio pueda usarlo todo el
  mundo, el diseño para todos y sus siete principios —quién los formuló y cuál busca minimizar los
  riesgos de las acciones involuntarias—, el diseño de productos para el rango más amplio de
  personas
  y situaciones, y las barreras de accesibilidad;
- **las pautas WCAG: principios, pautas, criterios y niveles** (III.8.1), que es el bloque más
grande
  del tema: los cuatro principios —perceptible, operable, comprensible y robusto—, cuántas pautas
  tiene cada versión, los niveles A, AA y AAA y a cuál pertenece cada criterio de conformidad
  (abreviaturas, contraste del contenido no textual, tres destellos, titulado de páginas, idioma,
  orientación), la pauta que pertenece a cada principio, las técnicas esenciales, la versión de las
  pautas 2.2 y la guía para aplicar WCAG a las tecnologías que no son web;
- **WAI-ARIA y las técnicas de accesibilidad** (III.8.1): qué es la WAI, qué significa ARIA y qué es
  verdad sobre ella, los valores válidos del atributo `role`, el atributo que describe la función de
  cada elemento visual, el que anuncia que un menú está desplegado, la estructura del contenido
  principal para los lectores de pantalla, el texto equivalente de una imagen y qué recomiendan las
  normas para los enlaces de hipertexto;
- **la usabilidad, sus principios y su evaluación** (III.8.1): qué es la usabilidad y cómo la define
  la ISO, los diez principios de Jakob Nielsen y cuál no lo es, las siglas UI y UX, la ley de Fitt,
  el
  diseño de prototipos de pantalla, la evaluación con expertos y las normas de ergonomía de la
  interacción persona-sistema;
- **las herramientas de evaluación y los lectores de pantalla** (III.8.1): los lectores de pantalla
  que vienen con Windows, con iOS y con Android y los de código abierto, las herramientas que
  evalúan
  la accesibilidad —TAW, 3AWS y compañía— y cuáles **no** son de evaluación, y el conjunto de pautas
  y componentes de diseño de interfaz de Google;
- **la normativa española de accesibilidad** (III.8.1): el **Real Decreto 1112/2018** —su ámbito de
  aplicación, los principios de su artículo 4, la carga desproporcionada del 7, el plazo de
  respuesta
  del 10 y el contenido de la declaración de accesibilidad del 15—, las obligaciones de fecha para
  las
  aplicaciones móviles del sector público, la norma **UNE 139803:2012** y la norma de AENOR sobre
  accesibilidad del equipo físico;
- **el desarrollo seguro de aplicaciones** (III.8.4): los conceptos de seguridad en el desarrollo y
  cuál no lo es, la técnica que analiza el código fuente de forma estática antes de producción,
  OWASP
  y el fallo que ocurre cuando datos no confiables llegan a un intérprete, la validación de la
  entrada
  y la que **no** se recomienda, las consultas preparadas y qué previenen, el control de la subida
  de
  ficheros, y el análisis de seguridad a lo largo del ciclo de vida con la inteligencia artificial;
- **las vulnerabilidades y los ataques a las aplicaciones** (III.8.4): el control de acceso roto que
  deja leer la incidencia de otra comisaría, la falsificación de peticiones en la que el navegador
  de
  la víctima hace la acción, y la vulnerabilidad de dos procesos que cambian a la vez un recurso
  compartido;
- **la autenticación, la biometría y el control de acceso** (III.8.3): los esquemas de autenticación
  de usuarios, qué es un captcha, los rasgos biométricos y cuál no cumple la distintividad, la tasa
  de
  falsos positivos y el portal cautivo;
- y **la disponibilidad, la confidencialidad y la integridad** (III.8.3): qué significa que un
sistema
  tenga alta disponibilidad, y los principios sobre los que se sostiene la información.

Cuatro decisiones de los patrones, dichas donde se leen:

- **la lección de III.3, II.3 y II.2, aplicada desde el principio**: en este banco «accesibilidad»,
  «web», «usuario», «herramienta» y «seguridad» salen en casi todos los enunciados y **no son
  patrones propios de ninguna materia**; los que se usan como débiles son los que no pueden llevarse
  nada de otro apartado. Lo que distingue una pregunta de otra es **la sigla y el número** —`WCAG ?2
  ?2` frente a `RD ?1112`, `aria` frente a `nielsen`— y por eso los patrones miran la sigla;
- **el Real Decreto 1112/2018 se pide por su número** (`1112`), no por «real decreto»: hay otras
  normas en el banco que también son reales decretos, y pedirlo por el número deja su apartado
  limpio;
- **la lección de II.3, aplicada**: los títulos de los diez apartados **no comparten las tres
primeras
  palabras entre tres de ellos**, y se comprueba antes de correr;
- y **lo que es de otro tema no se lava**, y aquí hay tres casos medidos: la pregunta del **Portal
de
  la Transparencia** (artículo 11 de la Ley 19/2013) y la del **personal directivo** (artículo 14
  del
  TREBEP) son de **I.4**, y la de los **once principios generales de la Ley 11/2007** es de
  **I.8.1**.
  Son **5 de las 167 preguntas con clave utilizable** y van a la bandeja del propietario con su
  motivo
  (`Motivo.SIN_MATERIA_EN_EL_INDICE`) en vez de a un apartado inventado.
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: Qué es la accesibilidad y qué el diseño universal.
_ACCESIBILIDAD = (
    r"accesibilidad|accesible(s)?",
    r"diseno (universal|para todos)|diseno de productos|diseno centrado",
    r"disenar productos|rango mas amplio de personas",
    r"siete principios|principios del diseno universal|que institucion formulo",
    r"barrera(s)? de accesibilidad|barreras?",
    r"independientemente de sus habilidades|discapacidad(es)?",
    r"percibir,? entender,? navegar e interactuar",
    r"caracteristica de una web NO se ajusta",
)

#: Las pautas WCAG.
_WCAG = (
    r"\bwcag\b|web content accessibility guidelines",
    r"pautas? de accesibilidad|directrices de accesibilidad|tecnicas esenciales",
    r"principio(s)? (perceptible|operable|comprensible|robusto)|perceptible|operable|comprensible",
    r"criterio(s)? de conformidad|nivel(es)? (a|aa|aaa)\b",
    r"abreviaturas|tres destellos|contraste de contenido|titulado de paginas|idioma de la pagina",
    r"orientacion|entrada de datos asistida|tiempo suficiente|legible|maximizar la compatibilidad",
    r"ataques? epilepticos|destellos",
    r"cuantas pautas se definen|cuantas? directrices|se estructura",
    r"tecnologias de la informacion y comunicaciones no web|\bwcag2ict\b",
    r"a quien NO se dirige|se compone de",
)

#: WAI-ARIA y las técnicas de marcado.
_ARIA = (
    r"\bwai\b|\baria\b|wai ?-? ?aria",
    r"\brole\b|atributo(s)? (que|de) (describir|utilizar)|aria ?-? ?expanded",
    r"texto equivalente|texto alternativo|\balt\b|placeholder|<label>|etiqueta",
    r"enlaces? de hipertexto|enlace o link",
    r"estructura del contenido principal|lectores de pantalla informen",
    r"que significa aria|sobre wai ?-? ?aria",
)

#: La usabilidad y sus principios.
_USABILIDAD = (
    r"usabilidad|\bux\b|\bui\b|experiencia de usuario",
    r"nielsen|jakob|diez principios|10 principios|principios? clave",
    r"ley de fitt|\bfitt\b|prototipo(s)?|diseno de interface|interfaz de usuario",
    r"eficacia,? eficiencia y satisfaccion",
    r"norma iso.*usabilidad|iso ?9241|ergonomia de la interaccion|interaccion persona ?-? ?sistema",
    r"evaluadores? expertos|inspeccionan o examinan",
    r"estandares? de documentacion|relacionado con la usabilidad",
)

#: Las herramientas y los lectores de pantalla.
_HERRAMIENTAS = (
    r"lector(es)? de pantalla|\bjaws\b|\bnvda\b|narrador|voiceover|talkback|\borca\b",
    r"herramienta(s)? (de|para) (evaluar|evaluacion|probar)|evaluacion automatica",
    r"\btaw\b|3 ?aws|wave|\baxe\b|examinator",
    r"material design|perteneciente a google|respalda(n)? las mejores practicas",
    r"aplicacion de codigo abierto|exploracion de componentes graficos",
    r"aplicacion JAWS|aplicacion 3AWS",
)

#: La normativa española de accesibilidad.
_NORMATIVA = (
    r"1112 ?/? ?2018|real decreto 1112|rd 1112",
    r"une ?139803|aenor|norma une|norma espanola|norma de aenor",
    r"declaracion de accesibilidad|carga desproporcionada",
    r"sector publico|administraciones publicas deberan ser accesibles|fecha.*accesibles",
    r"exactitud de toda la informacion|revisar la.*declaracion",
    r"mecanismos de comunicacion|solicitudes de informacion accesible y quejas",
    r"estandares? (de jure|de facto)|comite con estatus legal|avalados por un gobierno",
)

#: El desarrollo seguro de aplicaciones.
_DESARROLLO_SEGURO = (
    r"desarrollo seguro|seguridad en el desarrollo|principios? de seguridad",
    r"analisis estatico|\bsast\b|analisis del codigo fuente|antes de que se implemente",
    r"\bowasp\b|inyeccion|interprete como parte de un comando",
    r"validacion de (los )?datos de entrada|validacion de la entrada|consultas preparadas",
    r"subir ficheros|\bexe\b|control de seguridad.*mitigar|adjuntar fotografias",
    r"ciclo de vida del desarrollo|analisis de seguridad|inteligencia artificial",
    r"para el desarrollo seguro de aplicaciones web se recomienda",
)

#: Las vulnerabilidades y los ataques.
_VULNERABILIDADES = (
    r"vulnerabilidad(es)?|vulnerable",
    r"control de acceso|comisaria|incidencia solicitada|pertenece a la comisaria",
    r"falsificacion de peticiones|\bcsrf\b|fuerza al navegador",
    r"condiciones? de carrera|dos procesos|recurso compartido",
    r"robo de sesion|\bxss\b|inyeccion de codigo",
)

#: La autenticación, la biometría y el control de acceso.
_AUTENTICACION = (
    r"autenticacion|esquemas? de autenticacion|doble factor|\bmfa\b",
    r"captcha|capcha",
    r"biometr|huella|reconocimiento facial|iris|distintividad|tasa de falsos positivos",
    r"portal cautivo|control de acceso a la red",
)

#: La disponibilidad, la confidencialidad y la integridad.
_DISPONIBILIDAD = (
    r"alta disponibilidad|\bha\b|disponibilidad",
    r"confidencialidad|integridad de la informacion|\bcia\b",
    r"disponibilidad de la informacion|puestos? de usuario final",
)

MATERIAS: tuple[Materia, ...] = (
    # --- III.8.1 Accesibilidad, diseño universal y usabilidad -----------------------------------
    Materia(
        key="la-accesibilidad-y-el-diseno-universal",
        epigraph_code="III.8.1",
        title="La accesibilidad y el diseño universal",
        resumen=(
            "Que lo pueda usar todo el mundo: qué es la accesibilidad, el diseño para todos y sus "
            "siete principios —quién los formuló y cuál minimiza los riesgos de las acciones "
            "involuntarias—, el diseño de productos para el rango más amplio de personas y "
            "situaciones, y las barreras de accesibilidad que se encuentran de verdad."
        ),
        patrones=_ACCESIBILIDAD,
        prioridad=60,
    ),
    Materia(
        key="las-pautas-wcag-sus-principios-y-sus-niveles",
        epigraph_code="III.8.1",
        title="Las pautas WCAG: principios, pautas, criterios y niveles",
        resumen=(
            "El estándar de la accesibilidad web: los cuatro principios —perceptible, operable, "
            "comprensible y robusto—, cuántas pautas tiene cada versión, los niveles A, AA y AAA y "
            "a"
            "cuál pertenece cada criterio de conformidad (abreviaturas, contraste del contenido no "
            "textual, tres destellos, titulado de páginas, idioma, orientación), la pauta que "
            "pertenece a cada principio, las técnicas esenciales y la guía para las tecnologías "
            "que"
            "no son web."
        ),
        patrones=_WCAG,
        prioridad=15,
    ),
    Materia(
        key="wai-aria-y-las-tecnicas-de-accesibilidad",
        epigraph_code="III.8.1",
        title="WAI-ARIA y las técnicas de accesibilidad en el marcado",
        resumen=(
            "Lo que se escribe en el código para que lo entienda un lector de pantalla: qué es la "
            "WAI, qué significa ARIA, los valores válidos del atributo `role`, el atributo que "
            "describe la función de cada elemento visual, el que anuncia que un menú está "
            "desplegado,"
            "el texto equivalente de una imagen y qué recomiendan las normas para los enlaces de "
            "hipertexto."
        ),
        patrones=_ARIA,
        prioridad=20,
    ),
    Materia(
        key="la-usabilidad-sus-principios-y-su-evaluacion",
        epigraph_code="III.8.1",
        title="La usabilidad, sus principios y su evaluación",
        resumen=(
            "Que además sea fácil: qué es la usabilidad y cómo la define la ISO, los diez "
            "principios"
            "de Jakob Nielsen y cuál no lo es, las siglas UI y UX, la ley de Fitt, el diseño de "
            "prototipos de pantalla, la evaluación con expertos y las normas de ergonomía de la "
            "interacción persona-sistema."
        ),
        patrones=_USABILIDAD,
        prioridad=25,
    ),
    Materia(
        key="las-herramientas-de-evaluacion-y-los-lectores-de-pantalla",
        epigraph_code="III.8.1",
        title="Las herramientas de evaluación y los lectores de pantalla",
        resumen=(
            "Con qué se comprueba y con qué se lee: los lectores de pantalla que vienen con "
            "Windows,"
            "con iOS y con Android y los de código abierto, las herramientas que evalúan la "
            "accesibilidad —TAW, 3AWS y compañía— y cuáles **no** lo son, y el conjunto de pautas "
            "y"
            "componentes de diseño de interfaz de Google."
        ),
        patrones=_HERRAMIENTAS,
        prioridad=20,
    ),
    Materia(
        key="la-normativa-espanola-de-accesibilidad",
        epigraph_code="III.8.1",
        title="La normativa española de accesibilidad: el Real Decreto 1112/2018 y las normas UNE",
        resumen=(
            "Lo que obliga la ley: el ámbito de aplicación del Real Decreto 1112/2018, los "
            "principios de su artículo 4, la carga desproporcionada del 7, el plazo de respuesta "
            "del"
            "10 y el contenido de la declaración de accesibilidad del 15, las fechas de obligación "
            "de"
            "las aplicaciones móviles del sector público, y las normas UNE 139803:2012 y de AENOR."
        ),
        patrones=_NORMATIVA,
        prioridad=10,
    ),
    # --- III.8.4 Conceptos de seguridad en el desarrollo de los sistemas ------------------------
    Materia(
        key="el-desarrollo-seguro-de-aplicaciones",
        epigraph_code="III.8.4",
        title="El desarrollo seguro de aplicaciones y el análisis de seguridad",
        resumen=(
            "Escribir para que no se rompa: los conceptos de seguridad en el desarrollo de "
            "sistemas,"
            "el análisis estático del código fuente antes de producción, OWASP y el fallo que "
            "ocurre"
            "cuando datos no confiables llegan a un intérprete, la validación de la entrada y la "
            "que"
            "no se recomienda, las consultas preparadas, el control de la subida de ficheros y el "
            "análisis a lo largo del ciclo de vida."
        ),
        patrones=_DESARROLLO_SEGURO,
        prioridad=25,
    ),
    Materia(
        key="las-vulnerabilidades-y-los-ataques-a-las-aplicaciones",
        epigraph_code="III.8.4",
        title="Las vulnerabilidades y los ataques a las aplicaciones web",
        resumen=(
            "Por dónde entra el atacante: el control de acceso roto que deja leer la incidencia de "
            "otra comisaría, la falsificación de peticiones en la que el navegador de la víctima "
            "hace"
            "la acción, y la vulnerabilidad de dos procesos que cambian a la vez un recurso "
            "compartido."
        ),
        patrones=_VULNERABILIDADES,
        prioridad=20,
    ),
    # --- III.8.3 Confidencialidad y disponibilidad en puestos de usuario final ------------------
    Materia(
        key="la-autenticacion-la-biometria-y-el-control-de-acceso",
        epigraph_code="III.8.3",
        title="La autenticación, la biometría y el control de acceso",
        resumen=(
            "Quién eres y cómo lo demuestras: los esquemas de autenticación de usuarios, qué es un "
            "captcha, los rasgos biométricos y cuál no cumple la distintividad, la tasa de falsos "
            "positivos y el portal cautivo."
        ),
        patrones=_AUTENTICACION,
        prioridad=25,
    ),
    Materia(
        key="la-disponibilidad-la-confidencialidad-y-la-integridad",
        epigraph_code="III.8.3",
        title="La disponibilidad, la confidencialidad y la integridad de la información",
        resumen=(
            "Lo que se protege: qué significa que un sistema tenga alta disponibilidad, y la "
            "confidencialidad, la integridad y la disponibilidad como los tres principios sobre "
            "los"
            "que se sostiene la información en el puesto del usuario final."
        ),
        patrones=_DISPONIBILIDAD,
        prioridad=35,
    ),
)

#: El orden del índice: primero la accesibilidad —qué es, el estándar WCAG, lo que se escribe en el
#: marcado, la usabilidad, las herramientas y la normativa española— y después la seguridad del
#: desarrollo, que es la otra mitad del enunciado del tema.
ORDEN: tuple[str, ...] = (
    "la-accesibilidad-y-el-diseno-universal",
    "las-pautas-wcag-sus-principios-y-sus-niveles",
    "wai-aria-y-las-tecnicas-de-accesibilidad",
    "la-usabilidad-sus-principios-y-su-evaluacion",
    "las-herramientas-de-evaluacion-y-los-lectores-de-pantalla",
    "la-normativa-espanola-de-accesibilidad",
    "el-desarrollo-seguro-de-aplicaciones",
    "las-vulnerabilidades-y-los-ataques-a-las-aplicaciones",
    "la-autenticacion-la-biometria-y-el-control-de-acceso",
    "la-disponibilidad-la-confidencialidad-y-la-integridad",
)

__all__ = ["MATERIAS", "ORDEN"]
