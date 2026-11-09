# Revisión de interfaz — OpoFuente (noviembre de 2026)

**Qué es este documento.** Informe de revisión de la interfaz web de OpoFuente a partir del
inventario de pantallas y de las capturas del 9/11/2026. No es una auditoría técnica ni una propuesta
de rediseño completo: son **diez problemas concretos**, ordenados por gravedad, cada uno con la
captura que lo demuestra, qué está mal (con la medida cuando existe), por qué le importa a un
opositor y un arreglo propuesto. Al final, una sección de lo que ya está bien y el anexo de capturas.

| Dato | Valor |
|---|---|
| Fecha de la revisión | **9/11/2026** (Europe/Madrid) |
| Repositorio | `F:\Proyectos\opofuente` |
| Commit de referencia | **`72a634b`** (HEAD del 9/11/2026) |
| Código de la web capturada | `c5d6f93` — el commit de código inmediatamente anterior; `72a634b` no toca nada fuera de `docs/` y `ESTADO-AGENTE.md`, así que la interfaz capturada es la de este árbol |
| Capturas | **64 PNG fullPage** en [`docs/capturas/revision-2026-11/`](capturas/revision-2026-11/): 20 pantallas × 2 anchos + 20 estados vacíos + 4 estados de apoyo |
| Anchos | **1280×900** (escritorio) y **390×844** (móvil) |
| Datos de las capturas | **sintéticos** (corpus de la suite E2E); los textos de la interfaz son reales |
| Fuentes | [`INVENTARIO-PANTALLAS-2026-11.md`](interfaz/INVENTARIO-PANTALLAS-2026-11.md), [`TEXTOS-PANTALLAS-2026-11.md`](interfaz/TEXTOS-PANTALLAS-2026-11.md) y las 64 capturas |

**Escala de severidad.** *Bloqueante*: impide terminar la tarea principal de la pantalla. *Alta*:
fricción grave en una pantalla de uso diario o en la primera impresión. *Media*: cuesta tiempo o
comprensión, pero hay rodeo. *Baja*: pulido; no impide hacer nada.

---

## Resumen del inventario: las 20 pantallas

Cada entrada de la columna «Capturas» se lee como `<nombre>-1280.png` y `<nombre>-390.png`; las
marcas `+cargando`, `+error` y `+vacío` son capturas adicionales (estados de apoyo o estados vacíos).
El detalle de cada pantalla, sus textos y sus medidas están en el
[inventario completo](interfaz/INVENTARIO-PANTALLAS-2026-11.md).

| # | Pantalla | Ruta | Para qué está | Capturas |
|---|---|---|---|---|
| 1 | Inicio | `/` | Portada: siguiente tarea, repaso vencido, sesión a medias, pendientes de decisión y estado del programa | `inicio` + `+cargando`, `+error`, `+vacío` |
| 2 | Bandeja | `/bandeja` | Entrada de material: inventariar carpeta, copiar ficheros, pegar texto, traer URL; historial de lotes | `bandeja` + `+vacío` |
| 3 | Temario | `/temario` | Índice del temario común, búsqueda y avance por bloque | `temario` + `+vacío` |
| 4 | Programa | `/programa` | Árbol oficial de la convocatoria activa y reglas del examen | `programa` |
| 5 | Biblioteca | `/biblioteca` | Documentos con versión activa, derechos, procedencia y colecciones | `biblioteca` + `+vacío` |
| 6 | Ficha de documento | `/biblioteca?documento=<id>` | Cabecera de versión/derechos y cinco pestañas de trabajo (Lector por defecto) | `biblioteca-documento` |
| 7 | Documento, «Versiones y diff» | `/biblioteca?documento=<id>` (pestaña) | Comparar dos versiones sin fusionar nada | `biblioteca-documento-versiones` |
| 8 | Preguntas | `/preguntas` | Banco de preguntas: importar, revisar, plantillas de corrección | `preguntas` + `+vacío` |
| 9 | Banco con conjunto y pregunta | `/preguntas?conjunto=<id>&pregunta=<id>` | Trabajar un conjunto de 85 preguntas y la ficha de una pregunta | `preguntas-conjunto` |
| 10 | Plantillas del banco | `/preguntas` (pestaña «Plantillas») | Ver y activar la plantilla de corrección del conjunto | `preguntas-plantillas` |
| 11 | Estudiar | `/estudiar` | Preparar la sesión, correrla y leer el resultado; historial de sesiones | `estudiar` + `+vacío` |
| 12 | Errores | `/errores` | Cola de repaso y cuaderno de conceptos fallados; exportación | `errores` + `+vacío` |
| 13 | Cambios | `/cambios` | Comparar versiones nuevas y decir qué depende de lo cambiado | `cambios` + `+vacío` |
| 14 | Revisión | `/revision` | Decidir las propuestas de clasificación (eje, valor, confianza, cobertura) | `revision` + `+vacío` |
| 15 | Buscar y preguntar | `/buscar?q=plazo` | Búsqueda literal en el corpus y respuesta extractiva con citas | `buscar` |
| 16 | Ajustes | `/ajustes` | Datos y disco, capacidades, privacidad, copias, índice, diagnóstico y límites | `ajustes` + `+vacío` |
| 17 | 404 | `/seccion-que-no-existe` | Explicar que la dirección no existe y volver | `no-encontrada` |
| 18 | Ficha de tema | `/temario/<nodeId>` | Apuntes, material, preguntas y convocatorias de un tema | `temario-tema` |
| 19 | Ficha de tema con convocatoria | `/temario/<nodeId>?convocatoria=<id>` | Particularidades del tema en una convocatoria concreta | `temario-tema-convocatoria` |
| 20 | Práctica libre del bloque | `/temario/<nodeId>/practicar` | Repasar las preguntas aceptadas de un bloque, sin montar examen | `temario-tema-practicar` |

Además de las 20 pantallas se capturaron **10 estados vacíos** con un directorio recién migrado
(`-vacio`, 1280 y 390), **carga y error** de Inicio y Preguntas (`inicio-cargando` 1078 px,
`inicio-error` 1782 px, `preguntas-cargando` y `preguntas-error`), y el 404. «Temario vacío» no es un
vacío real: la siembra de perfiles deja el temario de 40 temas.

---

## Los 10 problemas

### 1. Revisión: la tabla desborda y deja «Aceptar / Rechazar» fuera de la pantalla

- **Severidad: bloqueante**
- **Pantalla y ruta:** Revisión · `/revision`
- **Captura:** [`revision-1280.png`](capturas/revision-2026-11/revision-1280.png) (PNG de **1635×15443**)
  y [`revision-390.png`](capturas/revision-2026-11/revision-390.png) (**390×29644**)
- **Qué está mal:**
  - `document.scrollWidth = 1635` frente a `clientWidth = 1280`: **357 elementos** salen por la
    derecha y la celda que contiene los botones de decisión termina en x=1635, **fuera del
    viewport**. La captura fullPage mide por eso 1635 px de ancho; es una de las dos únicas
    pantallas que desbordan a 1280.
  - La página mide **15443 px** (unas 17 pantallas de 900 px) y tiene **164 botones**. Apila cinco
    trabajos distintos: el aviso «Esto son propuestas, no hechos», «Cola de revisión» (9 grupos),
    «Clasificación de este material», «Propuestas» (**51 filas**) y «Cobertura del programa» (árbol
    de 33 temas).
  - La tabla de 51 propuestas no pagina ni filtra por eje o estado, y **cada fila lleva un
    `select` con los 33 temas del programa** (51 × 33 opciones): de ahí el tamaño y la densidad.
- **Por qué importa a un opositor:** es la pantalla donde las propuestas se convierten en decisiones.
  Sin decidir, el material no entra en ningún tema y el diagnóstico no reparte preguntas: el propio
  Inicio lo dice («6 catalogada(s) por tema. Quedan 126 sin tema»). Si la acción principal está fuera
  de la pantalla y no hay progreso visible (51 filas), el lote se abandona.
- **Arreglo propuesto:** (1) envolver la tabla en un contenedor con `overflow-x: auto` para que la
  página **nunca** desborde; (2) sacar el `select` de 33 opciones del flujo de la tabla y sustituirlo
  por un panel «Corregir el tema» con buscador de nodos; (3) agrupar por eje con colapso, paginar o
  virtualizar y dejar la barra de acciones del lote *sticky*; (4) mover «Cobertura del programa» y
  «Clasificación de este material» a pestañas. Aceptación: la primera propuesta decidible cabe en
  900 px y no hace falta scroll horizontal.

### 2. Inicio: la portada no elige la tarea de hoy y acaba siendo un panel de estado

- **Severidad: alta**
- **Pantalla y ruta:** Inicio · `/`
- **Captura:** [`inicio-1280.png`](capturas/revision-2026-11/inicio-1280.png) (1280×3564),
  [`inicio-390.png`](capturas/revision-2026-11/inicio-390.png) (390×5824) y
  [`inicio-vacio-1280.png`](capturas/revision-2026-11/inicio-vacio-1280.png) (2692 px)
- **Qué está mal:**
  - Trece encabezados en una sola página (contando el H1) y **cinco llamadas a la acción** en el
    primer tramo: «Ir al repaso de errores», «Ver la bandeja», «Revisar propuestas», «Ver los
    cambios» y «Ver la biblioteca». La barra lateral añade encima los contadores 18 · 4 · 2, que
    repiten las mismas cuentas.
  - «¿Listo para estudiar?» vive dentro de la tarjeta «Estado del programa», compitiendo con la
    tarea del día, y en la captura con datos anuncia «faltan 2 cosas» con tres pasos y sus enlaces.
  - Los bloques de soporte cierran la portada: «Estado del sistema» (`journal_mode=wal`, `bm25`,
    `DEBT-014`), una tabla de **7 capacidades**, **4 párrafos** de «Degradaciones declaradas» y
    «Almacenamiento». En la captura vacía son además 2692 px y repiten lo mismo.
- **Por qué importa a un opositor:** la portada promete «La siguiente tarea de hoy…», pero no la
  protege: obliga a decidir entre cinco acciones y a atravesar información de soporte para llegar a
  lo que importa. La entrada diaria debería ser «haz esto», no un cuadro de mando.
- **Arreglo propuesto:** una única acción primaria derivada de «Siguiente tarea»; «Acciones
  necesarias» como lista compacta (las 3 primeras + «ver las 4»), sin botón propio por línea; mover
  «Estado del sistema», «Capacidades», «Degradaciones declaradas» y «Almacenamiento» a Ajustes o a
  una pantalla «Estado»; deduplicar los contadores de la barra lateral; reservar «¿Listo para
  estudiar?» para el primer uso (vacío), no para el uso diario.

### 3. La interfaz habla en jerga de implementación: UUID, hashes, fechas ISO, enums en inglés y plural mecánico

- **Severidad: alta**
- **Pantalla y ruta:** varias; sobre todo Cambios `/cambios`, Biblioteca `/biblioteca`, Buscar
  `/buscar?q=plazo`, Revisión `/revision`, Ajustes `/ajustes`, Inicio `/` y Estudiar `/estudiar`
- **Captura:** [`cambios-1280.png`](capturas/revision-2026-11/cambios-1280.png),
  [`biblioteca-1280.png`](capturas/revision-2026-11/biblioteca-1280.png),
  [`biblioteca-documento-versiones-1280.png`](capturas/revision-2026-11/biblioteca-documento-versiones-1280.png),
  [`buscar-1280.png`](capturas/revision-2026-11/buscar-1280.png),
  [`ajustes-1280.png`](capturas/revision-2026-11/ajustes-1280.png) e
  [`inicio-1280.png`](capturas/revision-2026-11/inicio-1280.png)
- **Qué está mal:**
  - **Versiones identificadas por UUID.** En Cambios, la lista principal se lee «Apuntes sinteticos
    E2E-08 mw8f42ou: `ebd7e72b-c552-43be-8478-5a77abb7d121` → `7ff4f5a2-89eb-4776-a951-92fb7a59b108`»;
    en Biblioteca, la columna «VERSIÓN ACTIVA» es otro UUID y cada versión muestra
    `hash: fa2a60dc…` (SHA-256 de 64 caracteres, que además no rompe línea y estira la tabla hasta
    504 px a 390).
  - **Estados del servidor en inglés** dentro de frases en español: «la versión está en estado
    «superseded»», la insignia «accepted», y en Revisión el sujeto mezcla etiqueta y código:
    «Solo uso privado `private_use_only`», «Apuntes personales `personal_notes`».
  - **Fechas sin localizar:** `2026-11-08T22:43:07.294168` (Inicio, Estudiar, Plantillas),
    `2026-11-08 22:42:45` (Ajustes), `2025-12-22` (Inicio), `2026-11-08` (Cambios).
  - **Referencias internas a la vista:** «(ADR-017)» en Inicio, «(07_UI-UX §12)» en Revisión,
    «(07_UI-UX §3, §5)» en el Inicio vacío; en Ajustes, «esquema 0023_block_practice», «ordenada por
    bm25», «lease 60 s», «DEBT-014».
  - **Copy mecánico:** «4 pregunta(s) vencida(s)», «18 aviso(s) y error(es)», «1 cambiada(s) · 0
    nueva(s)», «6 fallo(s) acumulado(s)»; y concordancias sueltas como «1 plantillas del conjunto»,
    «1 pendientes» (Estudiar), «1 versiones» (Biblioteca), «recuperación lexical» (Buscar, por
    «léxica»).
- **Por qué importa a un opositor:** tiene que distinguir **qué versión de sus apuntes está
  estudiando** y no puede: dos UUID no se leen ni se memorizan, y no dicen cuál es más nueva. Los
  códigos en inglés y las fechas con microsegundos hacen dudar de si la aplicación está terminada.
  Las referencias a ADR, § de especificación y DEBT son pistas de que la pantalla está escrita para
  el equipo, no para quien se examina.
- **Arreglo propuesto:** un componente de versión legible («v2 · 7 nov 2026», con el UUID solo si se
  pide); traducir los enums en el límite de la vista (`superseded` → «sustituida», `accepted` →
  «aceptada», `private_use_only` → «solo uso privado», `curriculum` → «temario»); fechas y horas con
  `Intl.DateTimeFormat('es-ES')`; plurales con `Intl.PluralRules`; sacar ADR/DEBT/§ de la interfaz
  de uso; dejar el detalle técnico en Ajustes → «Diagnóstico». El patrón ya existe: «texto extraído»
  sí está traducido.

### 4. Bandeja: cuatro formas de entrada a la vez, la principal es escribir una ruta absoluta y los controles nativos salen en inglés

- **Severidad: alta**
- **Pantalla y ruta:** Bandeja · `/bandeja`
- **Captura:** [`bandeja-1280.png`](capturas/revision-2026-11/bandeja-1280.png) (1280×2236) y
  [`bandeja-390.png`](capturas/revision-2026-11/bandeja-390.png) (390×3993)
- **Qué está mal:**
  - La acción primaria, «Entrada», pide «Carpeta a inventariar (ruta absoluta)» con un campo que
    muestra `F:\EspacioCodigo\material-para-probar`; el arrastre y «O elige una carpeta» están
    **debajo**, en «Otras formas de entrada».
  - Conviven cuatro mecanismos con el mismo peso visual (inventariar ruta, soltar ficheros/carpetas,
    texto pegado, URL) y **27 botones** en la página.
  - Los controles nativos de fichero aparecen **en inglés** en mitad de una interfaz en español:
    «Choose Files · No file chosen», dos veces.
  - El propio copy se contradice: «Las tres formas de entrada del MVP están aquí: inventariar una
    carpeta, copiar ficheros sueltos, pegar texto y traer una URL» — dice tres y enumera cuatro.
  - «Lotes recientes» (el historial) queda por debajo de la primera pantalla de 900 px: la página
    mide 2236 px. El placeholder de la ruta y los lotes sintéticos
    (`…/opofuente-e2e-HI7Z5Q/material-sintetico`) añaden ruido técnico a la primera impresión.
- **Por qué importa a un opositor:** la Bandeja es lo primero que ve alguien con material pendiente,
  y le pide lo más difícil (teclear una ruta de Windows) antes de ofrecerle lo más fácil (arrastrar).
  El inglés de los controles nativos rompe el idioma justo en la acción clave, y cuatro caminos sin
  jerarquía no dicen cuál es «el camino».
- **Arreglo propuesto:** una única zona primaria grande («Arrastra aquí tus apuntes o elige una
  carpeta», con selector de carpeta vía `webkitdirectory`); la ruta manual, plegada en «Opciones
  avanzadas»; texto y URL como pestañas o enlaces secundarios, no como bloques equivalentes; botón
  propio en español que oculte el `input type=file` del sistema; corregir el copy «tres/cuatro».
  Objetivo medible: en 1280×900 deben caber título, zona de arrastre y «Lotes recientes».

### 5. En móvil, Revisión son 35 pantallas y el aviso se come la primera

- **Severidad: alta**
- **Pantalla y ruta:** Revisión · `/revision` a 390 (con corroboración en Preguntas y Programa)
- **Captura:** [`revision-390.png`](capturas/revision-2026-11/revision-390.png) (390×29644),
  [`revision-1280.png`](capturas/revision-2026-11/revision-1280.png),
  [`preguntas-conjunto-390.png`](capturas/revision-2026-11/preguntas-conjunto-390.png) (20942) y
  [`programa-390.png`](capturas/revision-2026-11/programa-390.png) (11647)
- **Qué está mal:**
  - La página mide **29644 px** a 390, es decir unas **35 pantallas de 844 px**. El aviso «Esto son
    propuestas, no hechos» ocupa **~600 px** (medido en el inventario) y la «Cola de revisión» no
    aparece hasta pasado más de un scroll completo.
  - Las 51 propuestas se convierten en tarjetas apiladas, con los mismos 164 botones y la misma
    cobertura del programa detrás; las tablas pasan a bloques por debajo de 640 px (lo que evita el
    scroll horizontal a costa de alargar la página).
  - El patrón se repite en las pantallas de trabajo: Preguntas llega a **20942 px** y Programa a
    **11647 px** a 390.
- **Por qué importa a un opositor:** mucha preparación se hace con el móvil en ratos sueltos. Una
  pantalla de 35 pantallas de alto no se recorre: la primera decisión está a más de un scroll y no
  hay un punto de retorno: el usuario no sabe cuánto le queda.
- **Arreglo propuesto:** para móvil, el aviso como resumen de una línea + «más información»
  (`details/summary` o hoja inferior); tarjetas de propuesta paginadas (10 por página) con barra de
  acciones *sticky* abajo; plegar «Cobertura del programa» y «Clasificación de este material». El
  mismo patrón de paginación para Preguntas y Programa. Objetivo: primera decisión en ≤2 pantallas
  de móvil.

### 6. Preguntas: 85 filas sin paginar y la ficha de la pregunta abierta, al final de la tabla

- **Severidad: media**
- **Pantalla y ruta:** Preguntas · `/preguntas` (conjunto abierto)
- **Captura:** [`preguntas-conjunto-1280.png`](capturas/revision-2026-11/preguntas-conjunto-1280.png)
  (1280×6496), [`preguntas-conjunto-390.png`](capturas/revision-2026-11/preguntas-conjunto-390.png)
  (390×20942) y [`preguntas-1280.png`](capturas/revision-2026-11/preguntas-1280.png) (4 preguntas)
- **Qué está mal:**
  - El banco anuncia «1–85 de 85 preguntas del conjunto» y las pinta **todas de una tirada**: 6496 px
    a 1280 y 20942 px a 390. No hay paginación ni filtro por texto (solo «Estado», «Origen» y la
    casilla «solo reservas»).
  - Cada fila acumula una caja con borde para el enunciado y tres insignias (origen, clave, estado):
    85 filas producen un patrón de rectángulos repetidos que compite con la lectura.
  - La ficha de la pregunta seleccionada («Pregunta 1», «Composición», «Corrección local», «Reportar
    una incidencia») se renderiza **debajo de la tabla**, después de la fila 85: para editar la
    pregunta que acabas de pulsar hay que atravesar el banco entero.
  - El selector «Conjunto abierto» lista 14 conjuntos con nombres generados por la suite
    («Practica E2E 1794177785174-455876 · banco privado»), sin búsqueda ni agrupación.
- **Por qué importa a un opositor:** revisar o corregir una pregunta concreta —la tarea de esta
  pantalla— exige recorrer 85 filas primero y 85 después para volver a la ficha. Es tiempo de estudio
  convertido en desplazamiento.
- **Arreglo propuesto:** paginar (25 por página) o virtualizar la tabla y añadir búsqueda por texto;
  abrir la ficha en un panel lateral o llevar el foco/scroll a ella al seleccionar una fila; una sola
  caja por fila y columnas con ancho mínimo; en el selector de conjunto, agrupar o filtrar. Objetivo:
  el alto de la pantalla no debe depender del número de preguntas.

### 7. Estados vacíos: explican el camino pero tres no llevan a él

- **Severidad: media**
- **Pantalla y ruta:** Biblioteca `/biblioteca`, Cambios `/cambios`, Errores `/errores` (y contraste
  con Inicio y Bandeja)
- **Captura:** [`biblioteca-vacio-1280.png`](capturas/revision-2026-11/biblioteca-vacio-1280.png)
  (915 px), [`cambios-vacio-1280.png`](capturas/revision-2026-11/cambios-vacio-1280.png) (900 px),
  [`errores-vacio-1280.png`](capturas/revision-2026-11/errores-vacio-1280.png) (900 px) y
  [`inicio-vacio-1280.png`](capturas/revision-2026-11/inicio-vacio-1280.png) (2692 px)
- **Qué está mal:**
  - **Biblioteca:** «Todavía no hay ningún documento / Un documento nace al promocionar material ya
    copiado: la biblioteca no crea obras. Copia el material en la Bandeja y promociónalo: aparecerá
    aquí con su versión.» Explica el camino, pero **no hay ningún enlace** a la Bandeja.
  - **Cambios:** «No hay ninguna versión nueva pendiente de revisar. Un cambio aparece cuando
    promocionas una segunda versión de un documento que ya tenía una aceptada…». Tampoco enlaza a la
    Biblioteca, que es donde se produce.
  - **Errores:** «No hay ningún repaso todavía: se crean solos al fallar una pregunta en una
    sesión.» y «…si quieres repasar antes de que toque, puedes declarar el resultado de un repaso
    hecho fuera.» Sin enlace a Estudiar, donde se falla la pregunta que llena la cola.
  - El contraste lo marca el propio producto: `preguntas-vacio` despliega «Crear un conjunto» en la
    misma pantalla y `inicio-vacio` ofrece «Ir a la bandeja» / «Ir al banco». Ese patrón no se ha
    aplicado en las tres pantallas de arriba.
- **Por qué importa a un opositor:** en el primer uso no hay material y no hay mapa. Los estados
  vacíos son la única documentación que se lee en ese momento; decirle «copia el material en la
  Bandeja» sin un botón le obliga a buscar la sección a mano y confirma la sensación de que la
  aplicación no arranca.
- **Arreglo propuesto:** un componente único de estado vacío con título + por qué está vacío + **una
  acción primaria** («Ir a la Bandeja», «Abrir la Biblioteca», «Preparar una sesión») + enlace
  secundario opcional. Mantener la explicación actual, que es buena; solo falta el botón.

### 8. Práctica libre del bloque: el texto promete «sin reservas ni tiempo» y el formulario los pide

- **Severidad: media**
- **Pantalla y ruta:** Práctica libre del bloque · `/temario/<nodeId>/practicar`
- **Captura:** [`temario-tema-practicar-1280.png`](capturas/revision-2026-11/temario-tema-practicar-1280.png)
  (1280×900) y
  [`temario-tema-practicar-390.png`](capturas/revision-2026-11/temario-tema-practicar-390.png)
  (390×1339)
- **Qué está mal:**
  - El texto dice: «Puedes abrirlas en su ficha o empezar una práctica del bloque: **sin reservas ni
    tiempo** y con la corrección de la convocatoria.» Debajo, el formulario ofrece **«Reservas»**
    (Ninguna / 1 / 2) y **«Tiempo máximo»** (Sin tiempo / 15 / 30 / 60 minutos).
  - La rejilla del formulario está rota a 1280: la etiqueta «Reservas» queda al final de la primera
    fila, y su desplegable («Ninguna») cae al principio de la segunda, separado de su etiqueta;
    «Cuántas preguntas» ocupa casi todo el ancho. No hay botón de reinicio.
  - El inventario documenta la causa: el control «Reservas» se añadió en el último commit y el copy
    no se actualizó.
- **Por qué importa a un opositor:** aquí se decide cómo será la sesión (con reservas o sin ellas,
  con reloj o sin él) y el texto de la propia pantalla dice lo contrario de lo que ofrecen los
  controles. En un producto que vive de reglas de examen, una contradicción así hace desconfiar del
  resto del cálculo.
- **Arreglo propuesto:** actualizar el copy («con reservas y tiempo opcionales, y la corrección de la
  convocatoria»); poner los tres campos en una rejilla de columnas iguales con etiquetas encima de
  cada control (una columna por debajo de 640 px); añadir «Restablecer» y una línea de resumen («Todas
  las preguntas · sin reservas · sin tiempo») antes del botón.

### 9. Errores: ruidosos cuando falla todo y mudos cuando falla un dato

- **Severidad: media**
- **Pantalla y ruta:** Inicio `/` con la API caída; Inicio y Programa con el dominio estimado no
  disponible
- **Captura:** [`inicio-error-1280.png`](capturas/revision-2026-11/inicio-error-1280.png) (1782 px),
  [`inicio-1280.png`](capturas/revision-2026-11/inicio-1280.png) y
  [`programa-1280.png`](capturas/revision-2026-11/programa-1280.png)
- **Qué está mal:**
  - Con la API caída, Inicio no muestra *un* error sino **ocho**: «No se pudo leer la cola de
    repaso», «No se pudieron cargar las sesiones», «No se pudo leer lo que espera tu decisión», «No
    se pudieron cargar los perfiles», «No se pudo leer la actividad reciente», «No se pudo comprobar
    el estado», «No se pudieron consultar las capacidades» y «No se pudo leer la configuración».
    Cinco llevan «Reintentar» y tres no; el texto «La API no responde o la base de datos no está
    migrada» se repite tres veces. La página resultante mide 1782 px.
  - Al revés, un fallo **parcial** es invisible: Inicio y Programa prometen «Dominio estimado por
    tema (07_UI-UX §3, §5)» y `GET /api/v1/reviews/mastery` responde **404** (tres respuestas 404
    registradas entre las capturas de Inicio y Programa); la pantalla simplemente **omite el dato sin
    ningún aviso**.
- **Por qué importa a un opositor:** cuando algo se rompe, es el peor momento para interpretar ocho
  mensajes y decidir cuál reintentar; lo que hay que hacer es una sola cosa, con un único diagnóstico
  legible. Y el fallo silencioso es peor: el «dominio estimado por tema» nunca aparece y el opositor
  puede creer que no tiene progreso cuando en realidad la consulta está rota.
- **Arreglo propuesto:** un estado de error agregado por pantalla (banda superior «No se pudo conectar
  con la aplicación» + un «Reintentar» que reintenta todo + detalle técnico plegado) y un componente
  de error por bloque con reintento compartido; copy en lenguaje de usuario, con enlace a Ajustes →
  Diagnóstico. Para el dominio: mover la ruta estática `/api/v1/reviews/mastery` por encima de
  `/api/v1/reviews/{review_id}` (las líneas 253 y 297 de `apps/api/opofuente/api/routes/reviews.py`),
  añadir prueba de contrato y, mientras tanto, mostrar «dominio no disponible» explícito en vez de
  omitir el bloque.

### 10. El buscador global de la cabecera no se anuncia ni se envía

- **Severidad: baja**
- **Pantalla y ruta:** cabecera de todas las pantallas; se juzga con Inicio (`/`) y Buscar
  (`/buscar?q=plazo`)
- **Captura:** [`inicio-1280.png`](capturas/revision-2026-11/inicio-1280.png),
  [`inicio-390.png`](capturas/revision-2026-11/inicio-390.png) y
  [`buscar-1280.png`](capturas/revision-2026-11/buscar-1280.png)
- **Qué está mal:** la cabecera tiene la etiqueta «Buscar en el corpus» y un campo **vacío**, sin
  placeholder, sin icono y sin botón. No se ve cómo se envía: se deduce que con Enter. A 390, la
  etiqueta y el campo se apilan y el campo ocupa una fila entera sin ninguna afordancia; en la
  captura de `/buscar?q=plazo` se ve que funciona, pero solo porque la URL ya trae la consulta.
- **Por qué importa a un opositor:** buscar en todo el material es una de las funciones centrales del
  producto y la única entrada permanente está escondida como un campo anónimo. Quien no prueba a
  pulsar Enter puede concluir que la aplicación no tiene búsqueda.
- **Arreglo propuesto:** placeholder («Busca en tus apuntes…»), icono de lupa y botón/Enter visible,
  `aria-label` en el campo, ancho completo con acción a la vista en móvil; al enviar, conservar el
  comportamiento actual (llevar a `/buscar?q=`).

---

## Qué está bien

- **Estados vacíos cuidados en su mayoría.** Casi todos dicen **por qué** están vacíos y **qué
  hacer**: «Todavía no hay lotes / Cuando inventaríes una carpeta aparecerá aquí, con su informe»
  (Bandeja), «Todavía no hay ningún conjunto de preguntas. Se crea aquí debajo…» (Preguntas, que
  despliega el formulario en la misma pantalla), «Elige un conjunto…» y «Haz un diagnóstico»
  (Estudiar), o la explicación de que los repasos «se crean solos al fallar una pregunta» (Errores).
  El Inicio vacío es, de hecho, un asistente de primeros pasos con «Ir a la bandeja» e «Ir al banco».
  El problema es que tres de ellos no enlazan a la acción (problema 7), no el texto.
- **Accesibilidad sin violaciones automatizables en las puertas.** La suite E2E incluye análisis axe
  y las entregas de los slices registran «axe sin violaciones» (S01, S02 y S03 para Inicio, Programa
  y Bandeja; S13 para el temario y la práctica libre). Esta pasada de capturas **no volvió a
  ejecutar axe**, así que aquí no se afirma nada más allá de lo que ya está registrado en
  [`docs/slices/`](slices/). Tampoco hubo `pageerror` (excepciones de React sin capturar) en ninguna
  pantalla, y el único error de consola común es la CSP `frame-ancestors` puesta en `<meta>`, que el
  navegador ignora: ruido, no rotura.
- **Responsive contenido.** De las 20 pantallas, 18 no desbordan a 1280 y todas salvo la tabla de
  versiones tampoco a 390: por debajo de 640 px las tablas pasan a bloques. Los dos únicos desbordes
  son los de Revisión y «Versiones y diff» (el segundo por los UUID y hashes que no rompen línea), y
  ambos están documentados aquí.
- **Navegación sin enlaces muertos.** Las 65 rutas internas distintas recogidas responden 200 y las
  56 entidades referenciadas por la dirección (nodos, documentos, conjuntos, preguntas,
  convocatorias) también. El 404 es sobrio y correcto.
- **Estados de carga y error existen de verdad.** Inicio muestra 8 mensajes de espera y Preguntas 1
  («Cargando los conjuntos…»); no son pantallas en blanco con un spinner. El problema es de
  agregación (problema 9), no de ausencia de estados.

---

## Estado de corrección (sesión del 9/11/2026, tarde)

Lo corregido en el árbol después de esta revisión. No cambia el diagnóstico: los problemas 2, 4, 5 y 6
siguen abiertos y son los que más valor tienen.

| # | Estado | Qué se cambió |
|---|---|---|
| 1 | **corregido el síntoma principal** | Las tablas anchas van en `.table-wrap` (la tarjeta desplaza en horizontal, la página ya no desborda) y la columna «Decisión» es `position: sticky` a la derecha: Aceptar/Rechazar deja de quedar fuera de la vista. La densidad (51 filas, `select` de 33 temas) sigue pendiente. |
| 2 | pendiente | Inicio sigue siendo un panel de operaciones; el rediseño de portada es una tarea propia. |
| 3 | pendiente | UUID, fechas ISO y enums en inglés siguen en pantalla; falta el componente de versión legible y la localización de fechas. |
| 4 | pendiente | Bandeja sigue pidiendo la ruta absoluta como acción principal. |
| 5 | pendiente | El aviso largo de Revisión en móvil no se colapsa; el `.table-wrap` no reduce sus 29.644 px. |
| 6 | pendiente | La tabla de 85 preguntas sigue sin paginar ni filtrar por texto. |
| 7 | **corregido** | Los vacíos de Biblioteca, Cambios y Errores enlazan a Bandeja, Biblioteca y Estudiar. |
| 8 | **corregido** | El texto de la práctica ya no promete «sin reservas ni tiempo»: dice que se eligen cantidad, reservas y tiempo. |
| 9 | **corregido el bug** | `/reviews/mastery` se declara antes de `/reviews/{review_id}` y tiene prueba de regresión; el dominio estimado vuelve a llegar a Inicio y Programa. El botón «Reintentar» en los 3 errores sin él sigue pendiente. |
| 10 | **corregido** | El buscador de la cabecera tiene placeholder («Busca un tema, una ley, un concepto…») y botón «Buscar». |

Puertas de esta corrección: `tsc`, `eslint`, 219 pruebas web, 53 E2E y la suite de backend en verde
(ver el resumen de la sesión). Las capturas de este documento son anteriores a los cambios: se
conservan como evidencia del estado revisado, no como estado actual.

> **Efecto secundario detectado al corregir el 9:** con `/reviews/mastery` respondiendo, la insignia
> de dominio por nodo desbordaba **Programa a 390 px** (459 px de ancho). Se corrigió en
> `.tree__label` (`flex-wrap: wrap`) y `.tree__title` (`min-width: 0; overflow-wrap: anywhere`), y la
> prueba E2E de responsive de Programa vuelve a verde.

---

## Anexo: qué captura enseña cada problema

| # | Problema | Severidad | Captura(s) | Pantalla y ruta |
|---|---|---|---|---|
| 1 | Revisión desborda y esconde la decisión | bloqueante | `revision-1280.png` (1635×15443), `revision-390.png` | Revisión · `/revision` |
| 2 | Inicio sin foco de portada | alta | `inicio-1280.png`, `inicio-390.png`, `inicio-vacio-1280.png` | Inicio · `/` |
| 3 | Jerga, UUID, fechas ISO y plural mecánico | alta | `cambios-1280.png`, `biblioteca-1280.png`, `biblioteca-documento-versiones-1280.png`, `buscar-1280.png`, `ajustes-1280.png`, `inicio-1280.png` | Cambios, Biblioteca, Buscar, Revisión, Ajustes, Inicio, Estudiar |
| 4 | Bandeja: ruta absoluta, 27 botones y controles en inglés | alta | `bandeja-1280.png`, `bandeja-390.png` | Bandeja · `/bandeja` |
| 5 | Revisión móvil: 29644 px y aviso de ~600 px | alta | `revision-390.png`, `preguntas-conjunto-390.png`, `programa-390.png` | Revisión a 390 (y Preguntas/Programa a 390) |
| 6 | 85 filas sin paginar y ficha al final | media | `preguntas-conjunto-1280.png`, `preguntas-conjunto-390.png`, `preguntas-1280.png` | Preguntas · `/preguntas?conjunto=…` |
| 7 | Vacíos que explican el camino pero no enlazan | media | `biblioteca-vacio-1280.png`, `cambios-vacio-1280.png`, `errores-vacio-1280.png`, `inicio-vacio-1280.png` | Biblioteca, Cambios, Errores (y contraste con Inicio) |
| 8 | Copy «sin reservas ni tiempo» contra un formulario con reservas y tiempo | media | `temario-tema-practicar-1280.png`, `temario-tema-practicar-390.png` | Práctica libre del bloque · `/temario/<nodeId>/practicar` |
| 9 | Ocho errores a la vez y un fallo silencioso | media | `inicio-error-1280.png`, `inicio-1280.png`, `programa-1280.png` | Inicio · `/` y Programa · `/programa` |
| 10 | Buscador global sin afordancia | baja | `inicio-1280.png`, `inicio-390.png`, `buscar-1280.png` | Cabecera de todas las pantallas |

Todas las capturas están en [`docs/capturas/revision-2026-11/`](capturas/revision-2026-11/); los
nombres de la tabla se refieren a ese directorio.

### Nota metodológica y límites

- **Capturas fullPage.** Los PNG son la página completa, no solo la primera pantalla: su alto es el
  `scrollHeight` y, cuando hay desborde, su **ancho es mayor que el viewport** (1635 px en
  `revision-1280.png`, 1443 en `biblioteca-documento-versiones-1280.png` y 504 en su versión de 390).
  Las medidas de `scrollWidth`, elementos que se salen y número de botones se tomaron en la pasada
  del inventario; este informe no las ha vuelto a medir.
- **Datos sintéticos.** El corpus «con datos» es el de la suite E2E (títulos como «Apuntes sinteticos
  E2E-08 mw8f42ou», nombres generados y UUID visibles). Los textos de interfaz (etiquetas, avisos,
  botones, estados vacíos) sí son reales y se citan del [anexo de textos](interfaz/TEXTOS-PANTALLAS-2026-11.md).
  Por eso no se juzgan los nombres ni las fechas de contenido, solo cómo los presenta la interfaz.
- **Sin tema oscuro.** La aplicación declara `color-scheme: light` (aunque `index.html` anuncia
  `light dark`): no hay tema oscuro que capturar ni que valorar.
- **Sin re-ejecución.** No se arrancó la aplicación, no se capturó de nuevo y no se tocó código,
  tests ni capturas para escribir este informe; todo sale de las fuentes citadas. Por la misma razón
  no se re-ejecutó axe ni se repitieron las comprobaciones de consola/HTTP.
- **Lo que no se capturó y queda fuera del juicio.** El estado de respuesta del RAG («Preguntar» no se
  pulsó porque escribe), la vista de resultado de un examen terminado, y las pestañas «Estructura»,
  «Asignaciones» y «Metadatos» de la ficha de documento, «Importar» de Preguntas y «Conceptos» de
  Errores. Tampoco modales ni confirmaciones. Una segunda pasada puede cubrirlos; los problemas de
  este informe no dependen de ellos.
- **Un dato de corpus que no es de interfaz.** El temario de las capturas muestra «0 de 40 temas
  estudiados» porque el corpus sintético no tiene material asignado a esos 40 temas; es un estado de
  datos, no un defecto de diseño, y no se cuenta entre los diez problemas.
