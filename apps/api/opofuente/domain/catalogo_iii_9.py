"""El catálogo de materias de III.9 (repositorios, metodologías, pruebas y control de versiones).

III.9 es un tema **técnico**: lo que lo estructura son sus seis epígrafes —los repositorios, la
generación de código y documentación, las metodologías de desarrollo, las pruebas, los programas
para
control de versiones y las plataformas de desarrollo colaborativo— y dentro de cada uno el índice va
por **asunto**, como en IV.7, IV.2 y II.4. Este catálogo los abre en trece apartados porque las
preguntas del tema se agrupan así de verdad:

- los repositorios y la configuración, en uno: qué es un repositorio y cómo se organiza, la gestión
  de la configuración, las líneas base, los elementos de configuración y la actualización;
- la generación de código y la documentación, en uno: la generación automática y las herramientas
  CASE, los tipos de documentación y los estándares para escribirla;
- las metodologías, en **cuatro**, porque es con diferencia el bloque más grande del banco (MÉTRICA
  v3 sola aparece en la mitad de los enunciados del tema): los **procesos y los participantes** de
  MÉTRICA v3, sus **técnicas y sus diagramas** (el flujo de datos, la estructura, la transición de
  estados y la planificación), los **modelos de ciclo de vida** (cascada, espiral, prototipos,
  incremental y el resto) y las **metodologías ágiles** (Scrum, Kanban y la programación extrema);
- el mantenimiento y la estimación, en dos: los **tipos de mantenimiento** y la gestión del cambio,
y
  la **planificación y la estimación** del proyecto (puntos de función, Delphi, Gantt y PERT) con la
  calidad del software;
- las pruebas, en dos: los **tipos y los niveles** (unitaria, de integración, de sistema, de
  aceptación, de regresión y las de caja blanca y negra) y las **técnicas y la calidad** (el diseño
  de los casos, la cobertura y los modelos de calidad);
- el control de versiones, en dos: los **programas y sus comandos** (Git por delante de todo, y
  después Subversion, CVS y Mercurial) y las **licencias del software** (el software libre, el
  copyleft y las licencias de las herramientas);
- las plataformas colaborativas, en uno: las forjas y los servicios de alojamiento, el trabajo
  colaborativo, la integración continua y la entrega continua.

Tres decisiones de redacción de los patrones, dichas donde se leen:

- las **herramientas y sus comandos** van con su nombre y con `\\b` (`\\bgit\\b`, `\\bsvn\\b`,
  `\\bcommit\\b`, `\\bpush\\b`): el tema se pregunta mucho por el comando exacto, y sin la frontera
  `git` casa dentro de otras palabras;
- **MÉTRICA v3** se escribe en el material de cinco maneras (`métrica`, `metrica`, `MÉTRICA v3`,
  `métrica versión 3`, `métrica3`), así que el patrón cubre la palabra normalizada (`metrica`) y el
  número suelto;
- **«prueba» va con sus dos sentidos**: la prueba del software (el banco de pruebas, probar) y la
  prueba como sinónimo de examen, que aparece en el enunciado de otras preguntas del mismo banco.
  Los
  patrones piden el contexto (`prueba(s)? (de|del|unitaria|de caja|de integracion)`), no la palabra
  suelta.

Las preguntas que no se sitúan ni por su enunciado ni por el texto de sus hechos **no** acaban en un
cajón: van a la bandeja del propietario con su motivo (`Motivo.SIN_MATERIA_EN_EL_INDICE`).
"""

from __future__ import annotations

from opofuente.domain.topic_index import Materia

#: La metodología que el banco cita en la mitad de sus enunciados, como la deja el texto
# normalizado.
_METRICA = r"metrica|\bm[eé]trica\b|\bmetricav3\b|metrica ?v? ?3|metrica version 3|\bmv3\b"

MATERIAS: tuple[Materia, ...] = (
    # --- III.9.1 Repositorios: estructura y actualización ----------------------------------------
    Materia(
        key="repositorios-y-configuracion",
        epigraph_code="III.9.1",
        title="Los repositorios y la gestión de la configuración",
        resumen=(
            "Dónde vive el software y cómo se guarda: el repositorio y su estructura, el "
            "repositorio de"
            " metadatos y el de objetos, la gestión de la configuración del software, los "
            "elementos de"
            " configuración y su identificación, las líneas base, el control de cambios y de "
            "versiones"
            " como disciplina, la biblioteca de software, la actualización del repositorio y la"
            " integridad de lo guardado."
        ),
        patrones=(
            r"repositorio(s)?( de (metadatos|objetos|software))?|"
            r"estructura del repositorio",
            r"gestion de (la )?configuracion|\bsccm\b|elementos? de configuracion|"
            r"linea(s)? base",
            r"biblioteca de software|almacen( de|amiento de) (software|codigo)",
            r"actualizacion del repositorio|actualizar el repositorio",
            r"control de cambios|gestion de cambios|peticion de cambio",
        ),
        patrones_debiles=(r"repositorio", r"configuracion"),
        prioridad=60,
    ),
    # --- III.9.2 Generación de código y documentación --------------------------------------------
    Materia(
        key="generacion-de-codigo-y-documentacion",
        epigraph_code="III.9.2",
        title="La generación de código y la documentación del software",
        resumen=(
            "Cómo se escribe (y se escribe solo) el software y cómo se documenta: la generación"
            " automática de código, las herramientas CASE y los generadores a partir del modelo, la"
            " reutilización, la documentación del software y sus tipos (la técnica y la de "
            "usuario, la"
            " documentación del proyecto y la de explotación), su contenido y su mantenimiento, las"
            " etiquetas de documentación y los estándares para documentar, y la documentación que "
            "pide"
            " una metodología."
        ),
        patrones=(
            r"generacion (automatica )?de codigo|generador(es)? de codigo|"
            r"herramientas? case|\bcase\b|ingenieria de software asistida",
            r"documentacion (del|de) (software|los sistemas|un proyecto)|"
            r"documentacion tecnica|manual(es)? (de|del) (usuario|explotacion|sistema)",
            r"estandar(es)? (de|para la|relacionado con la) documentacion|"
            r"etiqueta(s)? de documentacion|javadoc|doxygen",
            r"reutilizacion (de codigo|del software)|componentes? reutilizables",
            r"documentar|documentacion clara y coherente",
        ),
        patrones_debiles=(r"documentacion", r"codigo"),
        prioridad=40,
    ),
    # --- III.9.3 Metodologías de desarrollo ------------------------------------------------------
    Materia(
        key="metrica-procesos-y-participantes",
        epigraph_code="III.9.3",
        title="MÉTRICA v3: los procesos, las actividades y los participantes",
        resumen=(
            "La metodología MÉTRICA v3 por dentro: su estructura principal y sus procesos (la"
            " planificación del sistema de información, el estudio de viabilidad, el análisis, el"
            " diseño, la construcción, la implantación y la aceptación, y el mantenimiento), las"
            " interfaces y su gestión, las actividades y las tareas de cada proceso, los productos "
            "y"
            " los entregables, los participantes y los perfiles (el comité de dirección, el jefe de"
            " proyecto, los analistas, los usuarios expertos y los consultores), y el ciclo de "
            "vida y"
            " el mantenimiento que la metodología define."
        ),
        patrones=(
            _METRICA,
            r"(procesos|estructura principal|actividades|tareas) de (la metodologia "
            r")?(metrica|mv3)",
            r"participantes?|perfiles? (de|del) (analista|usuario)|usuario experto|"
            r"jefe de proyecto|comite de direccion",
            r"planificacion del sistema de informacion|\bps i\b|\bevs\b|\basi\b|\bdsi\b|"
            r"\bcsi\b|\bias\b",
            r"estudio de viabilidad|analisis del sistema de informacion|"
            r"diseno del sistema de informacion",
            r"producto(s)? (final|de entrada|de salida)|entregable(s)?",
            r"interfaz(es)? de (gestion|proyecto)|interfaces de metrica",
        ),
        patrones_debiles=(r"metrica", r"proceso", r"actividad", r"participante"),
        prioridad=41,
    ),
    Materia(
        key="metrica-tecnicas-y-diagramas",
        epigraph_code="III.9.3",
        title="Las técnicas y los diagramas de MÉTRICA v3",
        resumen=(
            "Las técnicas que MÉTRICA v3 usa para analizar y diseñar: el diagrama de flujo de "
            "datos y"
            " sus elementos y reglas de construcción, el diagrama de estructura y sus tipos de "
            "módulos,"
            " el diagrama de transición de estados, el modelo entidad-relación, y las técnicas de"
            " planificación y de estimación (el diagrama de Gantt, el PERT, el camino crítico y los"
            " hitos)."
        ),
        patrones=(
            r"diagrama(s)? de flujo de datos|\bdfd\b|\bdfds\b|flujo de datos",
            r"diagrama(s)? de estructura|\bde\b ?\(|diagramas? de estructura",
            r"diagrama(s)? de transicion de estados|\bdte\b|transicion de estados",
            r"diagrama(s)? de (gantt|pert)|camino critico|hitos?",
            r"modelo entidad ?-? ?relacion|\bmer\b|entidad-relacion",
            r"tecnica(s)? (de|del) (analisis|diseno|metrica)|"
            r"reglas de (construccion|comprobacion)",
        ),
        patrones_debiles=(r"diagrama", r"tecnica"),
        prioridad=42,
    ),
    Materia(
        key="ciclos-de-vida",
        epigraph_code="III.9.3",
        title="Los modelos de ciclo de vida del software",
        resumen=(
            "Cómo se organiza el proyecto en el tiempo: el ciclo de vida del software y sus fases, "
            "el"
            " modelo en cascada y sus caracteristicas, el modelo en espiral y la gestión de "
            "riesgos, el"
            " modelo de prototipos y el evolutivo, el modelo incremental e iterativo, el modelo en "
            "V y"
            " el RAD, la ingeniería de requisitos y la toma de requisitos, y la elección del modelo"
            " según el proyecto."
        ),
        patrones=(
            r"ciclo de vida|modelo(s)? (de ciclo de vida|en (cascada|espiral|v))",
            r"cascada|espiral|prototip(o|os)|incremental|iterativ|evolutiv|"
            r"\brad\b|modelo en v",
            r"fases? (del|de) (desarrollo|proyecto|analisis|diseno)|"
            r"analisis, diseno",
            r"ingenieria de requisitos|toma de requisitos|requisitos? (funcionales|no funcionales)|"
            r"especificacion de requisitos",
            r"gestion de riesgos? del proyecto|analisis de riesgos del proyecto",
        ),
        patrones_debiles=(r"ciclo", r"cascada", r"requisito"),
        prioridad=43,
    ),
    Materia(
        key="metodologias-agiles",
        epigraph_code="III.9.3",
        title="Las metodologías ágiles y el desarrollo iterativo",
        resumen=(
            "El desarrollo ágil: el manifiesto ágil y sus valores, Scrum (los roles, el product "
            "owner,"
            " el scrum master, el equipo, los artefactos, la pila de producto y la de sprint, el "
            "sprint"
            " y sus reuniones y la definición de terminado), Kanban y su tablero, la programación"
            " extrema y sus prácticas, Lean, el desarrollo dirigido por pruebas y la integración"
            " continua como práctica, y los marcos de escalado y las métricas ágiles."
        ),
        patrones=(
            r"\bagil(es)?\b|manifiesto agil|desarrollo agil|metodologia(s)? agiles?",
            r"\bscrum\b|sprint|product owner|scrum master|pila de (producto|sprint)|"
            r"\bbacklog\b",
            r"\bkanban\b|tablero kanban|limite de trabajo en curso",
            r"programacion extrema|\bxp\b|practicas? de la programacion extrema|"
            r"desarrollo dirigido por pruebas|\btdd\b",
            r"\blean\b|desarrollo esbelto|desperdicio",
            r"integracion continua|entrega continua|\bci\b ?/? ?\bcd\b|\bdevops\b",
        ),
        patrones_debiles=(r"agil", r"scrum", r"iteracion", r"sprint"),
        prioridad=44,
    ),
    Materia(
        key="mantenimiento-del-software",
        epigraph_code="III.9.3",
        title="El mantenimiento del software y su evolución",
        resumen=(
            "Lo que pasa después de entregar: los tipos de mantenimiento (correctivo, adaptativo,"
            " perfectivo, evolutivo y preventivo), el mantenimiento correctivo y el adaptativo y "
            "qué"
            " activa cada uno, la evolución del software y la ley de Lehman, la reingeniería y la"
            " ingeniería inversa, la migración y la retirada del sistema, la gestión del cambio y "
            "las"
            " peticiones de cambio, y el coste del mantenimiento."
        ),
        patrones=(
            r"mantenimiento (correctivo|adaptativo|perfectivo|evolutivo|preventivo)|"
            r"tipos? de mantenimiento|el mantenimiento (se ocupa|de) ",
            r"evolucion del software|ley(es)? de (lehman|belady)|mantenimiento del software",
            r"reingenieria|ingenieria inversa|ingenieria (del|de) software",
            r"migracion (de|del) (sistema|aplicacion)|retirada del sistema|"
            r"obsolescencia",
            r"coste (del|de) mantenimiento|estimacion del mantenimiento",
        ),
        patrones_debiles=(r"mantenimiento", r"evolucion"),
        prioridad=45,
    ),
    Materia(
        key="planificacion-y-estimacion",
        epigraph_code="III.9.3",
        title="La planificación, la estimación y la calidad del proyecto",
        resumen=(
            "Cuánto cuesta y cuánto tarda: la planificación del proyecto, la estimación del "
            "esfuerzo y"
            " del tamaño (los puntos de función, el COCOMO, el juicio de expertos y el método "
            "Delphi y"
            " el método de aproximación por analogía), la descomposición del trabajo, la "
            "planificación"
            " temporal y las técnicas de revisión, el equipo y la organización del proyecto, los"
            " riesgos, y la calidad del software y su aseguramiento."
        ),
        patrones=(
            r"estimacion (del|de) (esfuerzo|tamano|coste|proyecto)|puntos? de funcion|"
            r"\bcocomo\b|metodo delphi|juicio de expertos|analogia",
            r"planificacion (del|de) (proyecto|trabajo)|plan de proyecto|"
            r"descomposicion (del trabajo|de tareas)|\bedt\b|\bwbs\b",
            r"calidad del software|aseguramiento de la calidad|\bsqa\b|"
            r"norma(s)? iso 2500[0-9]|\biso 9126\b|modelo de calidad",
            r"equipo de (trabajo|proyecto)|organizacion del equipo|roles del equipo",
            r"riesgos? del proyecto|gestion de riesgos del proyecto",
        ),
        patrones_debiles=(r"estimacion", r"planificacion", r"calidad"),
        prioridad=46,
    ),
    # --- III.9.4 Pruebas -------------------------------------------------------------------------
    Materia(
        key="pruebas-tipos-y-niveles",
        epigraph_code="III.9.4",
        title="Las pruebas del software: tipos y niveles",
        resumen=(
            "Qué se prueba y en qué orden: la verificación y la validación, las pruebas unitarias "
            "o de"
            " unidad, las de integración y sus estrategias (ascendente, descendente y sándwich), "
            "las de"
            " sistema y las de aceptación, las de regresión y las de humo, las pruebas alfa y "
            "beta, las"
            " de caja blanca, caja negra y caja gris, las pruebas estáticas y dinámicas, y los "
            "objetos"
            " y el propósito de cada nivel."
        ),
        patrones=(
            r"prueba(s)? (unitaria|de unidad|de integracion|de sistema|de aceptacion|de regresion|"
            r"de humo|alfa|beta|funcionales?)",
            r"tipo(s)? de prueba|niveles? de prueba|pruebas? del software|"
            r"probar el software",
            r"caja (blanca|negra|gris)|pruebas? de caja",
            r"integracion (ascendente|descendente|sandwich)|estrategia(s)? de integracion|"
            r"prueba de integracion",
            r"verificacion y validacion|\bv ?& ?v\b|verificar y validar",
            r"prueba(s)? (estatica|dinamica)|revision(es)? (de codigo|tecnica)",
        ),
        patrones_debiles=(r"prueba", r"integracion", r"caja"),
        prioridad=47,
    ),
    Materia(
        key="pruebas-tecnicas-y-calidad",
        epigraph_code="III.9.4",
        title="Las técnicas de prueba y la calidad del software",
        resumen=(
            "Cómo se diseñan los casos y cómo se mide lo probado: las técnicas de diseño de casos"
            " (particiones de equivalencia, análisis de valores límite, tablas de decisión, "
            "transición"
            " de estados y pruebas basadas en la experiencia), la cobertura y sus criterios (de"
            " sentencias, de decisiones y de caminos), las herramientas y la automatización de "
            "pruebas,"
            " las pruebas de rendimiento, de carga y de estrés, las de seguridad y de usabilidad, "
            "y los"
            " modelos y las métricas de calidad."
        ),
        patrones=(
            r"tecnicas? de (prueba|diseno de casos)|diseno de casos de prueba|"
            r"particiones? de equivalencia|valores? limite|tabla(s)? de decision",
            r"cobertura (de codigo|de sentencias|de decisiones|de caminos)|"
            r"criterios? de cobertura",
            r"herramienta(s)? de (prueba|testing)|automatizacion de (las )?pruebas|"
            r"junit|selenium",
            r"pruebas? de (rendimiento|carga|estres|seguridad|usabilidad|accesibilidad)|"
            r"prueba de esfuerzo",
            r"metricas? de calidad|indicadores? de calidad|"
            r"comprobar el correcto funcionamiento",
        ),
        patrones_debiles=(r"cobertura", r"tecnica de prueba", r"calidad"),
        prioridad=48,
    ),
    # --- III.9.5 Programas para control de versiones ---------------------------------------------
    Materia(
        key="control-de-versiones",
        epigraph_code="III.9.5",
        title="Los programas de control de versiones y sus comandos",
        resumen=(
            "Las herramientas que guardan el histórico: el control de versiones centralizado y el"
            " distribuido, Git y sus comandos y conceptos (el repositorio local y el remoto, la "
            "copia de"
            " trabajo, el área de preparación, el commit, la rama y su creación y cambio, la "
            "fusión y"
            " sus conflictos, el rebase, el remoto y el push y el pull, el fetch, el stash, la"
            " etiqueta y el historial), Subversion, CVS y Mercurial, y las ventajas e "
            "inconvenientes de"
            " cada uno."
        ),
        patrones=(
            r"control de versiones|\bcvs\b|\bsvn\b|subversion|mercurial|\bgit\b",
            r"\bcommit(s)?\b|\bpush\b|\bpull\b|\bfetch\b|\bmerge\b|\brebase\b|\bclone\b|"
            r"\bcheckout\b|\bstash\b|\bbranch\b|repositorio remoto|rama(s)?",
            r"comando(s)? de git|git (init|add|commit|push|pull|fetch|merge|log|status|tag)",
            r"programa(s)? (para|de) control de versiones|herramienta de control de versiones",
            r"conflicto(s)? (de|en la) (fusion|merge)|resolver el conflicto",
            r"versionado|historial de cambios|revertir (un )?cambio",
        ),
        patrones_debiles=(r"git", r"version", r"comando", r"repositorio"),
        prioridad=49,
    ),
    Materia(
        key="licencias-de-software",
        epigraph_code="III.9.5",
        title="El software libre y las licencias",
        resumen=(
            "Con qué condiciones se distribuye el software: el software libre y sus libertades"
            " esenciales, el código abierto y sus criterios, el copyleft y su diferencia con las"
            " licencias permisivas, las licencias GPL y sus versiones, la LGPL, la AGPL, la BSD, "
            "la MIT,"
            " la Apache y la Mozilla, el software de dominio público y el propietario, y la "
            "licencia de"
            " las herramientas que el tema estudia."
        ),
        patrones=(
            r"licencia(s)?( de software| libre| gpl)?|copyleft|"
            r"\bgpl\b|\blgpl\b|\bagpl\b|\bbsd\b|\bmit\b|apache|mozilla|\bepl\b",
            r"software libre|libertades? (esenciales|del software)|codigo abierto|"
            r"open source|\bfoss\b",
            r"dominio publico|licencia propietaria|software propietario",
            r"distribuir (el|un) software|bajo (que|qué) licencia",
        ),
        patrones_debiles=(r"licencia", r"libre"),
        prioridad=50,
    ),
    # --- III.9.6 Plataformas de desarrollo colaborativo de software -------------------------------
    Materia(
        key="plataformas-colaborativas",
        epigraph_code="III.9.6",
        title="Las plataformas de desarrollo colaborativo",
        resumen=(
            "Dónde trabaja el equipo: las forjas y las plataformas de alojamiento de repositorios"
            " (GitHub, GitLab, Bitbucket y las instalaciones propias), el trabajo colaborativo y "
            "sus"
            " herramientas (la wiki, el sistema de seguimiento de incidencias, las peticiones de"
            " incorporación de cambios y la revisión de código), la integración y la entrega "
            "continua y"
            " sus servidores, los flujos de trabajo y las ramas de larga duración, y las "
            "herramientas"
            " de gestión del proyecto compartido."
        ),
        patrones=(
            r"plataforma(s)? (de|para el) desarrollo colaborativo|"
            r"desarrollo colaborativo|trabajo colaborativo",
            r"github|gitlab|bitbucket|forja(s)?|sourceforge",
            r"wiki|incidencia(s)?|seguimiento de (incidencias|tareas)|"
            r"peticion(es)? de incorporacion|pull request|merge request",
            r"integracion continua|entrega continua|servidor de integracion|jenkins|"
            r"\bci\b ?/? ?\bcd\b",
            r"revision de codigo|pair programming|programacion en pareja",
            r"flujo de trabajo|git ?flow|ramas? de larga duracion",
        ),
        patrones_debiles=(r"plataforma", r"colaborativo", r"github"),
        prioridad=51,
    ),
)

#: El orden en que se **enseña** el índice: el repositorio (dónde vive el software), la generación
# y la
#: documentación, las metodologías (que es el bloque mayor: MÉTRICA, sus técnicas, los ciclos de
# vida y
#: lo ágil, y después el mantenimiento y la estimación), las pruebas, el control de versiones con
# las
#: licencias, y por último las plataformas colaborativas. Es el orden de los seis epígrafes del
# tema.
ORDEN: tuple[str, ...] = (
    "repositorios-y-configuracion",
    "generacion-de-codigo-y-documentacion",
    "metrica-procesos-y-participantes",
    "metrica-tecnicas-y-diagramas",
    "ciclos-de-vida",
    "metodologias-agiles",
    "mantenimiento-del-software",
    "planificacion-y-estimacion",
    "pruebas-tipos-y-niveles",
    "pruebas-tecnicas-y-calidad",
    "control-de-versiones",
    "licencias-de-software",
    "plataformas-colaborativas",
)

__all__ = ["MATERIAS", "ORDEN"]
