# Inventario de pantallas y capturas — revisión de interfaz (2026-11)

Documento de trabajo para que **un revisor externo (Claude / GPT / Codex)** juzgue la interfaz de
OpoFuente sin tener que arrancar la aplicación. Recoge **qué pantallas hay**, **qué textos y estados
enseñan**, **64 capturas** a dos anchos y **los tres problemas de diseño más claros** que se ven hoy,
con su evidencia y su arreglo propuesto.

El volcado literal del texto visible de cada pantalla está en el anexo
[`TEXTOS-PANTALLAS-2026-11.md`](./TEXTOS-PANTALLAS-2026-11.md); este documento lo resume y lo juzga.

---

## Metadatos

| Dato | Valor |
|---|---|
| Fecha de captura | **2026-11-09** (Europe/Madrid) |
| Repositorio | `F:\Proyectos\opofuente` |
| Commit | **`c5d6f93`** (`git rev-parse --short HEAD`) |
| Web servida | build de producción local: `apps/web/dist` con `vite preview` en `http://127.0.0.1:4173` |
| API | FastAPI en `http://127.0.0.1:8765` |
| Datos de las capturas «con datos» | **sintéticos**: directorio `.e2e-data` generado por la suite E2E (4 documentos, 14 conjuntos de preguntas, 11 sesiones, 21 intentos, 2 errores de aprendizaje, 3 conjuntos de cambios, 56 propuestas de clasificación) |
| Datos de las capturas «vacías» | directorio **temporal fuera del repositorio** (`%TEMP%\opofuente-capturas-vacio`), recién migrado y sembrado solo con perfiles |
| Herramienta | Node **v24.19.0** + Playwright **1.63.0** (Chromium que instala Playwright) |
| Anchos | **1280×900** y **390×844** (móvil), `deviceScaleFactor: 1`, `locale: es-ES`, tema claro |
| Formato de imagen | PNG **fullPage** (alto completo de la página, no solo la primera pantalla) |
| Capturas | **64 PNG**: 44 con datos (20 pantallas × 2 anchos + 4 estados de apoyo) y 20 de estados vacíos (10 pantallas × 2 anchos) |
| Script de captura | [`capturar.mjs`](./capturar.mjs) · generador del anexo: [`generar-textos.mjs`](./generar-textos.mjs) |
| Directorio de imágenes | [`docs/capturas/revision-2026-11/`](../capturas/revision-2026-11/) |

> **Aviso sobre el build.** El `dist/` que había en el repositorio se construyó a las 23:41 del
> 2026-11-08 y el último commit (`c5d6f93`) modificó después `TemarioBlockPracticePage.tsx` (23:44).
> Para que las capturas correspondan al código del commit, **se reconstruyó el frontend con
> `npm run build:web` antes de capturar** (Vite 8.3.0; aviso de chunk > 500 kB: `index-CJob_VGQ.js`,
> 585,76 kB). `dist/` está en `.gitignore`, así que reconstruirlo no ensucia el diff.
>
> **Las capturas no escriben datos de la aplicación.** Todo el recorrido es de lectura: navegar,
> abrir pestañas y forzar estados de carga/error con intercepción de red en el navegador; no se pulsó
> ninguna acción que guarde, confirme o borre. La única acción que escribe (el botón «Preguntar» del
> RAG) **no** se capturó a propósito (ver
> [Qué no se pudo capturar](#qué-no-se-pudo-capturar-y-por-qué)).

---

## Cómo se regeneran las capturas (comandos exactos)

Un bloque cada vez y sin dejar dos API escuchando en el mismo puerto.

```powershell
# --- Bloque 1: capturas con datos sintéticos -----------------------------------------
# Terminal A: API sobre el directorio de la suite (nunca el directorio real)
$env:OPOFUENTE_DATA_DIR = 'F:\Proyectos\opofuente\.e2e-data'
uv run python -m uvicorn opofuente.main:app --host 127.0.0.1 --port 8765

# Terminal B: web de producción local (reconstruir si dist/ no está al día)
npm run build:web
npm run preview --workspace @opofuente/web -- --port 4173 --strictPort

# Terminal C: capturas
node docs/interfaz/capturar.mjs --modo=datos

# --- Bloque 2: estados vacíos (parar antes la API del bloque 1) -----------------------
$tmp = Join-Path $env:TEMP 'opofuente-capturas-vacio'
if (Test-Path $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force }   # solo si es esa ruta
New-Item -ItemType Directory -Path $tmp | Out-Null
$env:OPOFUENTE_DATA_DIR = $tmp
uv run alembic upgrade head
uv run python -m opofuente.tools.seed_profiles
uv run python -m uvicorn opofuente.main:app --host 127.0.0.1 --port 8765

# (el preview de 4173 sigue sirviendo; no depende del directorio de datos)
node docs/interfaz/capturar.mjs --modo=vacio

# --- Bloque 3: anexo de textos y limpieza --------------------------------------------
node docs/interfaz/generar-textos.mjs
# Parar uvicorn y `npm run preview`; comprobar que no queda nada escuchando:
Get-NetTCPConnection -State Listen -LocalPort 8765,4173 -ErrorAction SilentlyContinue
# Borrar el directorio temporal de estados vacíos
Remove-Item -LiteralPath (Join-Path $env:TEMP 'opofuente-capturas-vacio') -Recurse -Force
```

`capturar.mjs` resuelve **los ids reales por la API** antes de navegar (`/api/v1/documents`,
`/api/v1/mappings`, `/api/v1/question-sets`, `/api/v1/curricula`, `/api/v1/curriculum-nodes/…`) y
guarda un informe técnico por modo en `docs/interfaz/.captura-datos.json` y
`docs/interfaz/.captura-vacio.json` (insumo de `generar-textos.mjs`).

---

## Método y alcance

- **Recorrido completo del producto** con datos: las 10 secciones de la barra lateral, la ficha de
  tema, la práctica de bloque, la ficha de documento (dos pestañas), banco de preguntas (con
  conjunto y pregunta abiertos, y pestaña de plantillas), búsqueda con consulta, y el 404.
- **Cada pantalla a dos anchos**, porque el producto declara adaptación a móvil (hay reglas
  `@media (max-width: 640px)` y `1024px`): 1280 (escritorio) y 390 (móvil).
- **Estados de apoyo** (solo 1280): `inicio-cargando`, `inicio-error`, `preguntas-cargando`,
  `preguntas-error`, obtenidos retrasando 2,5 s o forzando un 500 en las respuestas de la API.
- **Estados vacíos** con un directorio recién migrado: 10 pantallas × 2 anchos (sufijo `-vacio`).
- Se registran por pantalla: título, H1, encabezados, pestañas, texto visible, enlaces, botones,
  avisos, estados (`vacío/cargando/error`), errores de consola, respuestas HTTP ≥ 400, desborde
  horizontal (y qué elementos se salen) y alto total de la página.
- **No** se modificó código de la aplicación, ni specs E2E, ni datos reales. El único efecto fuera
  de `docs/` fue reconstruir `apps/web/dist` (artefacto ignorado por git), explicado arriba.

---

## Tabla inventario

Alto = alto real de la página (`scrollHeight`) medido al asentar cada pantalla; el PNG puede diferir
en unos píxeles y, si la página **desborda**, la captura fullPage es más ancha que el viewport (es el
caso de `revision-1280.png`, de 1635 px de ancho, y de `biblioteca-documento-versiones-*`). «Desborde»
= `scrollWidth` mayor que el ancho del viewport (aparición de barra horizontal). Las capturas se
nombran `<pantalla>-1280.png` / `<pantalla>-390.png`; las vacías, `<pantalla>-vacio-1280.png` etc.

| # | Pantalla | Ruta | Para qué está | Qué datos muestra con el corpus sintético | Estados vistos | Acciones y enlaces principales | Alto (1280/390) | Capturas |
|---|---|---|---|---|---|---|---|---|
| 1 | **Inicio** | `/` | Decir qué toca hoy: repaso vencido, sesión a medias, lo que espera decisión y estado del programa | 4 repasos vencidos de 19; sesión en marcha (práctica 1/2); 18 avisos de importación, 9 clasificaciones, 2 cambios, 1 material sin aceptar; oposición TAI AGE y convocatoria `tai-age-2025`; 4 perfiles | cargado; **carga** y **error** capturados; vacío en `-vacio` | Ir al repaso de errores · Ver la bandeja · Revisar propuestas · Ver los cambios · Ver la biblioteca · enlaces a Programa/Estudiar | 3564 / 5824 | `inicio-1280`, `inicio-390`, `inicio-cargando-1280`, `inicio-error-1280`, `inicio-vacio-*` |
| 2 | **Bandeja** | `/bandeja` | Entrada de material: inventariar carpeta, copiar ficheros, pegar texto, traer URL; historial de lotes | Lote `import`/`inventory` recientes con 3 y 6 entradas y estado «terminado» | cargado; vacío en `-vacio` | Revisar la clasificación del material · Inventariar (solo lectura) · soltar ficheros · Guardar el texto · Descargar y copiar · Ver lote | 2237 / 3994 | `bandeja-1280`, `bandeja-390`, `bandeja-vacio-*` |
| 3 | **Temario** | `/temario` | Índice del temario común que se estudia, con búsqueda y avance | 5 bloques · 40 temas · 0 de 40 estudiados · «Qué queda» por bloque | cargado; en vacío **no** está vacío (la siembra de perfiles trae el temario) | Buscar un tema · abrir cualquier tema · «Practicar este bloque» (5 enlaces) | 2555 / 3496 | `temario-1280`, `temario-390`, `temario-vacio-*` |
| 4 | **Programa** | `/programa` | Árbol oficial de la convocatoria activa y reglas del examen | TAI AGE: 4 bloques / 33 temas con títulos oficiales largos; el dominio por nodo **no** se ve (la petición falla, ver §Comprobaciones) | cargado | Desplegar/plegar bloques · seleccionar nodo (detalle) · enlaces a bases oficiales | 4733 / 11647 | `programa-1280`, `programa-390` |
| 5 | **Biblioteca** | `/biblioteca` | Documentos con su versión activa, derechos, procedencia y colecciones | 4 documentos (notas personales y programas), 2 versiones cada uno, «derechos restringidos» en los 4, 1 colección con 0 miembros | cargado; vacío en `-vacio` | Filtrar por tipo/ámbito/derechos · Limpiar filtros · crear colección · Abrir la ficha | 1554 / 2848 | `biblioteca-1280`, `biblioteca-390`, `biblioteca-vacio-*` |
| 6 | **Ficha de documento** | `/biblioteca?documento=<id>` | Cabecera de versión/derechos + cinco pestañas de trabajo (Lector, Estructura, Asignaciones, Versiones y diff, Metadatos) | «Apuntes sinteticos E2E-08 mw8f42ou»: versión activa `7ff4f5a2-…`, sin autoridad, derechos no constan (restringidos), 3 secciones · 3 evidencias | cargado; aviso de derechos restringidos | Volver a la lista · cambiar pestaña · Marcar sustitución… · Abrir el fichero original · Añadir a colección | 2964 / 5058 | `biblioteca-documento-1280`, `-390` |
| 7 | **Documento, pestaña «Versiones y diff»** | `/biblioteca?documento=<id>` (pestaña) | Comparar dos versiones sin fusionar nada | Tabla de 2 versiones identificadas por **UUID** y **hash SHA-256**, diff de 3 secciones (1 cambiada, 2 iguales) | cargado; **desborde horizontal** | Marcar sustitución… · elegir versión anterior/nueva · leer diff | 3219 / 5903 | `biblioteca-documento-versiones-1280`, `-390` |
| 8 | **Preguntas** | `/preguntas` | Banco de preguntas: importar, revisar, plantillas de corrección | Conjunto por defecto (4 preguntas), 14 conjuntos en el selector, badges «borrador» y «con clave activa» | cargado; vacío en `-vacio` | Elegir conjunto · crear conjunto · pestañas Preguntas/Importar/Plantillas · filtros · abrir pregunta | 903 / 1949 | `preguntas-1280`, `preguntas-390`, `preguntas-vacio-*` |
| 9 | **Banco con conjunto y pregunta** | `/preguntas?conjunto=<id>&pregunta=<id>` | Trabajar un conjunto grande y la ficha de una pregunta | Examen de 85 preguntas (5 reservas), tabla de 85 filas, pregunta abierta con opciones y clave | cargado | Navegar tabla · filtros Estado/Origen · solo reservas · editar/corregir/reportar | 6496 / 20942 | `preguntas-conjunto-1280`, `-390` |
| 10 | **Plantillas del banco** | `/preguntas` (pestaña «Plantillas») | Ver y activar la plantilla de corrección del conjunto | 1 plantilla `v1` activa, 4 preguntas con desenlace, aprobada `2026-11-08T22:43:05.872587`, 0 sesiones desactualizadas | cargado | Activar plantilla · marcar sustitución · recalcular sesiones | 900 / 1250 | `preguntas-plantillas-1280`, `-390` |
| 11 | **Estudiar** | `/estudiar` | Preparar sesión, correrla y ver el resultado | Sesión en marcha (práctica 1 de 2, tiempo agotado), pregunta 2 con «Tu respuesta», historial de sesiones | cargado; preparación en vacío | Preparar otra sesión · responder · navegar · terminar · historial | 1962 / 3919 | `estudiar-1280`, `estudiar-390`, `estudiar-vacio-*` |
| 12 | **Errores** | `/errores` | Cola de repaso y cuaderno de conceptos fallados | 4 de 19 vencidos · 6 fallos acumulados; dos repasos con su pregunta, opciones y «toca hoy» | cargado; vacío en `-vacio` | Repasar en una sesión (4) · Repasado y sabido/fallado · Aplazar 3 días · exportar Anki/Markdown | 1651 / 2589 | `errores-1280`, `errores-390`, `errores-vacio-*` |
| 13 | **Cambios** | `/cambios` | Comparar versiones nuevas y decir qué depende de lo cambiado | 3 cambios (2 propuestos, 1 confirmado); diff de secciones de «Apuntes sinteticos E2E-08» | cargado; vacío en `-vacio` | Seleccionar cambio · confirmar · descartar · revisar derivados | 1462 / 2703 | `cambios-1280`, `cambios-390`, `cambios-vacio-*` |
| 14 | **Revisión** | `/revision` | Decidir las propuestas de clasificación (ejes, valores, confianza, cobertura) | 9 grupos con 51 propuestas pendientes; 357 elementos desbordan a la derecha; clasificación «sin clasificar» del material | cargado; vacío en `-vacio` | Buscar propuestas ahora · marcar grupos · Aceptar/Rechazar · Corregir el tema · deshacer · cobertura del programa | **15443 / 29644** | `revision-1280`, `revision-390`, `revision-vacio-*` |
| 15 | **Buscar y preguntar** | `/buscar?q=plazo` | Búsqueda literal en el corpus y respuesta extractiva con citas | 4 fragmentos, 2 documentos «fuera del corpus» por estar sustituidos, citas con su sección | cargado (resultados); **no** se capturó `Preguntar` (escribe) | Buscar · elegir versión · estilo de respuesta · Preguntar · Abrir en la Biblioteca | 1418 / 2209 | `buscar-1280`, `buscar-390` |
| 16 | **Ajustes** | `/ajustes` | Datos y disco, uso, capacidades reales, privacidad, copias, índice, diagnóstico, límites | Ruta y base de datos, 182,3 KB usados, tabla de capacidades (FTS5 operativo, LLM/embeddings desactivados), copia `20261108-224245-fd6cd3`, índice completo (18 fragmentos), contadores del diagnóstico | cargado; vacío en `-vacio` | Hacer copia · Verificar · Previsualizar restauración · Rehacer el índice · Preparar diagnóstico · purgas | 3333 / 5502 | `ajustes-1280`, `ajustes-390`, `ajustes-vacio-*` |
| 17 | **404** | `/seccion-que-no-existe` | Explicar que la dirección no existe y volver | — | error de ruta | Volver a Inicio | 900 / 844 | `no-encontrada-1280`, `-390` |
| 18 | **Ficha de tema** | `/temario/<nodeId>` | Apuntes, material, preguntas y convocatorias de un tema | Nodo I.1 de TAI AGE: sin apuntes propios, 1 documento, 2 preguntas, 13 convocatorias (10 por confirmar) | cargado; vacío parcial («Este tema aún no tiene apuntes») | Marcar como estudiado · Ver material · Ver en el banco · siguiente/anterior tema | 1357 / 1977 | `temario-tema-1280`, `-390` |
| 19 | **Ficha de tema con convocatoria** | `/temario/<nodeId>?convocatoria=<id>` | Particularidades del tema en una convocatoria concreta | Tema «La Constitución Española de 1978» del temario común, «13 convocatorias», sección «En esta convocatoria» | cargado | Cambiar de convocatoria · Ver particularidades · Bases oficiales | 1309 / 1980 | `temario-tema-convocatoria-1280`, `-390` |
| 20 | **Práctica libre del bloque** | `/temario/<nodeId>/practicar` | Repasar todas las preguntas aceptadas de un bloque, sin montar examen | 2 preguntas del bloque, formulario «cuántas / reservas / tiempo» y arranque de práctica | cargado | Empezar la práctica del bloque · Repasar en el banco | 900 / 1261 | `temario-tema-practicar-1280`, `-390` |
| — | **Carga** | `/` y `/preguntas` | Cómo se ve mientras la API no contesta | 8 y 1 mensajes «Cargando…» | cargando | — | 1078 / 900 | `inicio-cargando-1280`, `preguntas-cargando-1280` |
| — | **Error** | `/` y `/preguntas` | Cómo se ve con la API caída (500 en todo) | Inicio: 5 bloques de error y 3 vacíos; Preguntas: 1 error con «Reintentar» | error | Reintentar | 1782 / 900 | `inicio-error-1280`, `preguntas-error-1280` |

---

## Las pantallas, una a una

Se citan las capturas de 1280; las de 390 están en el mismo directorio con el sufijo `-390`. El
texto literal de cada una está en el [anexo de textos](./TEXTOS-PANTALLAS-2026-11.md).

### 1. Inicio (`/`)

- **Textos**: H1 «Inicio». Lead: «La siguiente tarea de hoy: el repaso vencido manda; si no hay nada
  vencido, se continúa la sesión que quedó a medias.» Bloques: «Siguiente tarea», «Continuar
  estudiando», «Acciones necesarias» («La aplicación ya ha hecho lo que puede hacer sola. Esto es lo
  que no puede decidir por ti (ADR-017)…»), «Estado del programa», «¿Listo para estudiar?»,
  «Actividad reciente», «Últimos lotes», «Últimas sesiones», «Estado del sistema», «Capacidades»,
  «Degradaciones declaradas», «Almacenamiento». Botón principal: «Ir al repaso de errores».
- **Qué se puede hacer**: saltar al repaso, a la bandeja, a las propuestas de clasificación, a los
  cambios y a la biblioteca; ver la última sesión y el estado real del programa; enlaces a
  Programa/Estudiar.
- **Qué falta o chirría**: la fecha de la sesión en marcha aparece como
  `2026-11-08T22:43:07.294168` (ISO con microsegundos); los recuentos usan plural mecánico
  («4 pregunta(s) vencida(s)»); el «Estado del sistema» del final vuelca jerga de implementación
  (`journal_mode=wal`, `bm25`, `DEBT-014`) en una portada; la tarjeta «Estado del programa» promete
  dominio estimado pero la petición de dominio falla (404 silencioso, ver §Comprobaciones).
- **Capturas**: [`inicio-1280.png`](../capturas/revision-2026-11/inicio-1280.png) ·
  [`inicio-390.png`](../capturas/revision-2026-11/inicio-390.png) ·
  [`inicio-cargando-1280.png`](../capturas/revision-2026-11/inicio-cargando-1280.png) ·
  [`inicio-error-1280.png`](../capturas/revision-2026-11/inicio-error-1280.png)

### 2. Bandeja (`/bandeja`)

- **Textos**: H1 «Bandeja». Lead: «OpoFuente copia: nunca mueve, renombra ni borra tus originales.
  Primero inventaría la carpeta en modo lectura y solo después copia lo que confirmes.» Bloques:
  «Entrada» (etiqueta «Carpeta a inventariar (ruta absoluta)», botón «Inventariar (solo lectura)»),
  «Otras formas de entrada» (ficheros/carpetas, «Texto pegado», «Desde una URL»), «Vista previa del
  inventario», «Importación», «Entradas del lote», «Incidencias del lote», «Texto extraído», «Lotes
  recientes».
- **Qué se puede hacer**: inventariar una carpeta, soltar ficheros o carpetas, elegir carpeta, pegar
  texto, descargar una URL y revisar los lotes recientes.
- **Qué falta o chirría**: la acción primaria pide **escribir una ruta absoluta a mano** mientras la
  misma pantalla ya ofrece «O elige una carpeta»; los controles nativos de fichero salen en inglés
  («Choose Files / No file chosen») en una interfaz en español; cuatro mecanismos de entrada con el
  mismo peso compiten en una sola página (27 botones); conviven el placeholder
  `F:\EspacioCodigo\material-para-probar` y el texto del lote
  `…/opofuente-e2e-HI7Z5Q/material-sintetico`.
- **Capturas**: [`bandeja-1280.png`](../capturas/revision-2026-11/bandeja-1280.png) ·
  [`bandeja-390.png`](../capturas/revision-2026-11/bandeja-390.png)

### 3. Temario (`/temario`)

- **Textos**: H1 «Temario»; lead «5 bloques · 40 temas»; tarjeta «Temas» con «Buscar un tema»;
  árbol de bloques (I–V) y temas (1–40); panel «Avance» («0 de 40 temas estudiados», «Por bloque»,
  «Qué queda», «Practicar este bloque»).
- **Qué se puede hacer**: buscar con tolerancia a tildes, abrir un tema, marcar avance, lanzar la
  práctica de un bloque.
- **Qué falta o chirría**: el buscador es un campo ancho sin resultados sugeridos hasta teclear;
  «Qué queda» ordena los bloques por cantidad restante (I, III, IV, V, II), no por orden oficial,
  lo que desconcierta al leer; el temario se ve, pero los 40 temas están «0 de 40» porque el corpus
  sintético no tiene material asignado a ellos (es un estado de datos, no de interfaz).
- **Capturas**: [`temario-1280.png`](../capturas/revision-2026-11/temario-1280.png) ·
  [`temario-390.png`](../capturas/revision-2026-11/temario-390.png)

### 4. Programa (`/programa`)

- **Textos**: H1 «Programa»; lead «Cuerpo de Técnicos Auxiliares de Informática de la Administración
  del Estado · 4 bloques, 33 temas»; tarjeta «Temario oficial» con el árbol y las etiquetas «bloque»
  / «tema».
- **Qué se puede hacer**: desplegar bloques, seleccionar un nodo (panel «Nodo seleccionado»),
  consultar la cobertura y el dominio por nodo.
- **Qué falta o chirría**: es la página más larga de la navegación de estudio (4733 px a 1280,
  11647 a 390) y el detalle del nodo aparece al seleccionarlo, no en la captura; el dominio por nodo
  no se muestra porque `GET /api/v1/reviews/mastery` devuelve 404 (ver §Comprobaciones); los títulos
  oficiales ocupan varias líneas y a 390 hacen la lista muy difícil de escanear.
- **Capturas**: [`programa-1280.png`](../capturas/revision-2026-11/programa-1280.png) ·
  [`programa-390.png`](../capturas/revision-2026-11/programa-390.png)

### 5. Biblioteca (`/biblioteca`)

- **Textos**: H1 «Biblioteca». Lead: «Tus documentos con sus versiones, sus derechos y su
  procedencia…». Tarjetas «Filtros» (tipo documental, ámbito, derechos, «Limpiar filtros»),
  «Colecciones», «Documentos». Nota técnica visible: «…porque la API todavía no filtra por derechos:
  el recuento que se ve es el de esta pantalla, no el de toda la biblioteca.»
- **Qué se puede hacer**: filtrar, crear colecciones, abrir la ficha de un documento.
- **Qué falta o chirría**: la explicación de la limitación del filtro es lenguaje de
  implementación («la API todavía no filtra»); la columna «VERSIÓN ACTIVA» enseña un UUID; los
  AVISOS repiten por fila «no constan derechos: se tratan como desconocidos y restringidos»; la
  última columna de la fila abierta dice «Abrir la ficha abierta ahora».
- **Capturas**: [`biblioteca-1280.png`](../capturas/revision-2026-11/biblioteca-1280.png) ·
  [`biblioteca-390.png`](../capturas/revision-2026-11/biblioteca-390.png)

### 6. Ficha de documento (`/biblioteca?documento=<id>`)

- **Textos**: H2 con el título del documento; ficha con «Versión activa», «Autoridad», «Ámbito»,
  «Vigencia», «Procedencia», «Derechos»; aviso «Derechos restringidos: no se puede compartir»;
  pestañas «Lector · Estructura · Asignaciones · Versiones y diff · Metadatos».
- **Qué se puede hacer**: leer las secciones, citar, resumir una sección, revisar versiones, asignar
  al programa, cambiar metadatos, añadir a una colección.
- **Qué falta o chirría**: los valores de versión, artefacto y hash son UUID/SHA-256 crudos; la
  separación «Lector / Estructura» puede solaparse (el lector ya enseña secciones); el aviso de
  derechos restringidos se repite en cabecera y en cada fila de la pestaña de versiones.
- **Capturas**: [`biblioteca-documento-1280.png`](../capturas/revision-2026-11/biblioteca-documento-1280.png) ·
  [`biblioteca-documento-390.png`](../capturas/revision-2026-11/biblioteca-documento-390.png) ·
  [`biblioteca-documento-versiones-1280.png`](../capturas/revision-2026-11/biblioteca-documento-versiones-1280.png) ·
  [`biblioteca-documento-versiones-390.png`](../capturas/revision-2026-11/biblioteca-documento-versiones-390.png)

### 7. Preguntas (`/preguntas`)

- **Textos**: H1 «Preguntas». Lead: «El banco de preguntas de una oposición…». Tarjeta «Conjunto»
  (selector «Conjunto abierto», recuentos «85 preguntas (0 incompletas · 5 reservas) · 1 plantilla»,
  badges «borrador» y «con clave activa», despliegue «Crear un conjunto»); tarjeta «Banco» con
  pestañas «Preguntas», «Importar», «Plantillas», filtros «Estado» y «Origen», casilla «solo
  reservas» y tabla «N° · ENUNCIADO · ORIGEN · TIPO · CLAVE · ESTADO».
- **Qué se puede hacer**: crear conjuntos, importar (CSV/JSON/documento), activar plantillas,
  filtrar, abrir una pregunta, editarla, corregirla, reportar incidencias.
- **Qué falta o chirría**: la tabla no pagina (85 filas = 6496 px, 20942 px a 390) y cada celda va
  dentro de una caja con borde, lo que produce un patrón de rectángulos repetidos que compite con la
  lectura; la columna CLAVE enseña «clave: a» incluso con la respuesta visible (para un banco de
  práctica, no de examen, es correcto, pero el ojo lo lee como spoiler).
- **Capturas**: [`preguntas-1280.png`](../capturas/revision-2026-11/preguntas-1280.png) ·
  [`preguntas-conjunto-1280.png`](../capturas/revision-2026-11/preguntas-conjunto-1280.png) ·
  [`preguntas-390.png`](../capturas/revision-2026-11/preguntas-390.png) ·
  [`preguntas-conjunto-390.png`](../capturas/revision-2026-11/preguntas-conjunto-390.png) ·
  [`preguntas-plantillas-1280.png`](../capturas/revision-2026-11/preguntas-plantillas-1280.png)

### 8. Estudiar (`/estudiar`)

- **Textos**: H1 «Estudiar». Lead: «Practicar y examinarse con el banco de preguntas…». Con sesión
  abierta: «Tienes una sesión en marcha (práctica, en marcha): se retoma donde estaba… y empezó el
  `2026-11-08T22:43:07.294168`»; tarjeta «Sesión en marcha» (Modo, Clave, Progreso, Tiempo),
  pregunta con opciones, «Tu respuesta», y al final la tabla «Sesiones» (modo, estado, respondidas,
  fecha, «Abrir»). Sin sesión: «Preparar la sesión» con modo, parte, conjunto, cuántas, corrección,
  barajar y «Empezar», más «¿No sabes por dónde empezar? Haz un diagnóstico».
- **Qué se puede hacer**: preparar una sesión (práctica / examen oficial / simulacro / diagnóstico),
  responder, navegar, terminar, leer el resultado y retomar sesiones del historial.
- **Qué falta o chirría**: fechas ISO con microsegundos; «1 de 2 respondidas · 1 pendientes»
  (concordancia); el cronómetro «18:30:02 · queda 00:00» con el aviso «Se ha agotado el tiempo…»
  deja una sesión viva en un estado raro; la letra de los enunciados es monoespaciada, lo que da
  aspecto de consola a un texto de estudio.
- **Capturas**: [`estudiar-1280.png`](../capturas/revision-2026-11/estudiar-1280.png) ·
  [`estudiar-390.png`](../capturas/revision-2026-11/estudiar-390.png) ·
  [`estudiar-vacio-1280.png`](../capturas/revision-2026-11/estudiar-vacio-1280.png)

### 9. Errores (`/errores`)

- **Textos**: H1 «Errores»; lead «Lo que fallaste y cuándo toca repasarlo…». Tarjeta «Repaso»
  («4 de 19 vencidos · 6 fallo(s) acumulado(s)»), pestañas «Hoy» / «Conceptos», botón «Repasar en
  una sesión (4)», y una entrada por repaso con su pregunta, sus opciones y tres botones
  («Repasado y sabido», «Repasado y fallado», «Aplazar 3 días»). Al final «Exportar» (Anki CSV,
  Markdown/Obsidian) con la explicación de qué lleva el fichero.
- **Qué se puede hacer**: repasar el vencido en una sesión, declarar el resultado de un repaso hecho
  fuera, aplazar, exportar el banco, ver conceptos.
- **Qué falta o chirría**: los mismos dos párrafos explicativos se repiten **debajo de cada
  entrada** («Declarar el resultado es para lo que repases fuera de aquí…», «un fallo entra en la
  cola de hoy mismo»), lo que hace la lista larga y repetitiva; «primer repaso · 1 fallo(s) ·
  private» mezcla español e inglés; el resumen duplica la cuenta («4 de 19 vencidos » y «4 de 19»).
- **Capturas**: [`errores-1280.png`](../capturas/revision-2026-11/errores-1280.png) ·
  [`errores-390.png`](../capturas/revision-2026-11/errores-390.png)

### 10. Cambios (`/cambios`)

- **Textos**: H1 «Cambios». Lead: «Cuando llega una versión nueva de un material, OpoFuente compara
  las dos…». «Propuestas y cambios» con una fila por cambio: título del documento,
  `uuid-anterior → uuid-nuevo`, badge de estado («propuesto, sin aplicar», «confirmado») y resumen
  «1 cambiada(s) · 0 nueva(s) · 0 quitada(s) · 2 sin cambios · 0 derivado(s) afectado(s), 0 por
  revisar». «Qué ha cambiado» con la tabla «SECCIÓN · QUÉ LE PASÓ · ANTES · DESPUÉS». «Resúmenes del
  material» con su explicación.
- **Qué se puede hacer**: elegir un cambio, leer el diff sección a sección, confirmar o descartar,
  revisar resúmenes afectados.
- **Qué falta o chirría**: los identificadores de versión son UUID, así que la lista principal de la
  pantalla se lee como `…: ebd7e72b-… → 7ff4f5a2-…`; las fechas son `2026-11-08`; las etiquetas
  «sección 1 / sección 2» no dicen nada del contenido; el plural mecánico «(s)» aparece cuatro veces
  en una sola línea.
- **Capturas**: [`cambios-1280.png`](../capturas/revision-2026-11/cambios-1280.png) ·
  [`cambios-390.png`](../capturas/revision-2026-11/cambios-390.png)

### 11. Revisión (`/revision`)

- **Textos**: H1 «Revisión». Lead: «Revisa lo que la aplicación propone sobre tu material: qué eje,
  qué valor, con qué confianza y con qué evidencia…». Aviso destacado «Esto son propuestas, no
  hechos» (con «(07_UI-UX §12)» al final), «Cola de revisión» («Buscar propuestas ahora», «9 grupos
  con 51 propuestas pendientes…», tabla «GRUPO · SUJETO · EJE · PROPUESTAS · CONFIANZA · AVISO»),
  «Clasificación de este material» («Lo que consta de este material, eje por eje»), «Propuestas»
  (tabla de 51 filas con «Aceptar / Rechazar / Corregir el tema»), «Decisiones de esta sesión» y
  «Cobertura del programa» (árbol completo).
- **Qué se puede hacer**: lanzar una pasada de clasificación, elegir grupos, aceptar/rechazar/
  corregir propuestas, deshacer decisiones de la sesión y mirar la cobertura del programa.
- **Qué falta o chirría**: **es el problema nº 1** (ver más abajo): 15443 px de alto, 164 botones,
  tabla que desborda a 1635 px de ancho y deja los botones de decisión fuera del viewport a 1280.
  Además, la columna SUJETO mezcla etiqueta y código interno («Solo uso privado
  `private_use_only`», «Temario o programa `curriculum`»).
- **Capturas**: [`revision-1280.png`](../capturas/revision-2026-11/revision-1280.png) ·
  [`revision-390.png`](../capturas/revision-2026-11/revision-390.png) ·
  [`revision-vacio-1280.png`](../capturas/revision-2026-11/revision-vacio-1280.png)

### 12. Buscar y preguntar (`/buscar?q=plazo`)

- **Textos**: H1 «Buscar y preguntar». Tarjeta «Búsqueda» («Qué buscas», «Versiones: solo lo
  vigente», botón «Buscar»; «Respuesta: breve», botón «Preguntar», casilla «Incluir mi material
  privado»); «Resultados» («4 fragmentos · solo versiones vigentes · recuperación lexical · corpus
  18-2026-11-08 22:42:44.669074-4»); aviso «Lo que esta búsqueda no puede hacer» («sin proveedor de
  embeddings: la búsqueda ha sido solo léxica (FTS5)»); «Fuera del corpus» («la versión está en
  estado «superseded»»); lista de resultados con badge «accepted», cita y «Abrir en la Biblioteca».
- **Qué se puede hacer**: buscar, incluir histórico, pedir una respuesta extractiva, abrir la cita en
  la biblioteca.
- **Qué falta o chirría**: «recuperación lexical» es un anglicismo/errata («léxica»); el resumen de
  resultados incluye un identificador de corpus con fecha; los estados del servidor salen en inglés
  dentro de comillas españolas («superseded»); el aviso técnico (FTS5) es correcto pero está en el
  camino de lectura.
- **Capturas**: [`buscar-1280.png`](../capturas/revision-2026-11/buscar-1280.png) ·
  [`buscar-390.png`](../capturas/revision-2026-11/buscar-390.png)

### 13. Ajustes (`/ajustes`)

- **Textos**: H1 «Ajustes». Lead: «Todo lo que la aplicación hace con tus datos, dicho sin
  adornos…». Diez bloques: «Datos y disco», «Uso del almacén», «Qué se puede retirar», «Capacidades
  instaladas», «Privacidad: a dónde sale tu contenido», «Copia y restauración», «Índice de
  búsqueda», «Exportación», «Diagnóstico y registros saneados», «Límites en vigor».
- **Qué se puede hacer**: crear copia, verificarla, previsualizar restauración, rehacer el índice,
  preparar el diagnóstico en texto, purgar material con confirmación.
- **Qué falta o chirría**: es la pantalla más técnica: enseña la ruta de datos absoluta, «esquema
  0023_block_practice», «registro WARNING», «bm25», «lease 60 s», «DEBT-014» y una tabla de
  contadores (`artifacts: 16`, `evidence_spans: 18`…). Es honesto y útil para soporte, pero no está
  separado de la configuración cotidiana: 3333 px (5502 a 390) sin índice ni pestañas.
- **Capturas**: [`ajustes-1280.png`](../capturas/revision-2026-11/ajustes-1280.png) ·
  [`ajustes-390.png`](../capturas/revision-2026-11/ajustes-390.png)

### 14. 404 (`/seccion-que-no-existe`)

- **Textos**: H1 «Página no encontrada»; «La dirección solicitada no corresponde a ninguna sección de
  OpoFuente.»; enlace «Volver a Inicio».
- **Qué falta o chirría**: cumple y es sobrio; no sugiere buscar en el corpus ni volver a la pantalla
  anterior (solo a Inicio).
- **Capturas**: [`no-encontrada-1280.png`](../capturas/revision-2026-11/no-encontrada-1280.png) ·
  [`no-encontrada-390.png`](../capturas/revision-2026-11/no-encontrada-390.png)

### 15. Ficha de tema (`/temario/<nodeId>`)

- **Textos**: migas «Temario › Organización del Estado y Administración electrónica»; H1 con el
  título oficial completo del tema; lead «I.1 · Resolución de 18 de diciembre de 2025, de la
  Secretaría de Estado de Función Pública…». Bloques «Apuntes» (aquí «Este tema aún no tiene
  apuntes / Cuando haya texto para este tema aparecerá aquí»), «Material del tema», botón «Marcar
  como estudiado», «Preguntas» («2 preguntas en el banco»), «En qué convocatorias aparece» (13, con
  «Por confirmar» en las 10 en borrador) y navegación «Siguiente».
- **Qué se puede hacer**: leer apuntes y material, marcar/retirar la marca de estudiado, abrir una
  pregunta en el banco, ver en qué convocatorias aparece y saltar al tema siguiente/anterior.
- **Qué falta o chirría**: el H1 es un título oficial de dos líneas y el lead repite otra
  convocatoria entera; el «Material del tema» reduce un documento a su título y a la etiqueta
  «Documento»; todo el bloque «En qué convocatorias aparece» es una lista larga de convocatorias en
  borrador («Por confirmar»), que domina la ficha.
- **Capturas**: [`temario-tema-1280.png`](../capturas/revision-2026-11/temario-tema-1280.png) ·
  [`temario-tema-390.png`](../capturas/revision-2026-11/temario-tema-390.png) ·
  [`temario-tema-convocatoria-1280.png`](../capturas/revision-2026-11/temario-tema-convocatoria-1280.png) ·
  [`temario-tema-convocatoria-390.png`](../capturas/revision-2026-11/temario-tema-convocatoria-390.png)

### 16. Práctica libre del bloque (`/temario/<nodeId>/practicar`)

- **Textos**: migas con el tema; H1 «Práctica libre del bloque»; lead «Preguntas aceptadas del banco
  catalogadas en los temas de este bloque. Puedes abrirlas en su ficha o empezar una práctica del
  bloque: **sin reservas ni tiempo** y con la corrección de la convocatoria.»; formulario «Cuántas
  preguntas / Reservas / Tiempo máximo»; botón «Empezar la práctica del bloque»; listado con «2
  preguntas» y «Repasar en el banco».
- **Qué se puede hacer**: elegir cantidad, reservas y tiempo, empezar una sesión de bloque o abrir
  una pregunta en el banco.
- **Qué falta o chirría**: **el texto dice «sin reservas ni tiempo» y el formulario ofrece reservas y
  tiempo** (el control «Reservas» se añadió en el último commit y el copy no se actualizó); el
  formulario tiene tres selects en fila sin botón de reinicio.
- **Capturas**: [`temario-tema-practicar-1280.png`](../capturas/revision-2026-11/temario-tema-practicar-1280.png) ·
  [`temario-tema-practicar-390.png`](../capturas/revision-2026-11/temario-tema-practicar-390.png)

---

## Estados vacíos

Directorio temporal recién migrado y sembrado (`alembic upgrade head` + `seed_profiles`): sin
material, sin preguntas, sin sesiones, sin propuestas y sin cambios. Lo único poblado son los
perfiles: 4 oposiciones, 4 temarios y el temario común de 40 temas. Sufijo `-vacio`.

| Pantalla | Qué dice literalmente sin datos | ¿Ofrece acción útil? | Captura |
|---|---|---|---|
| `/` Inicio | «Nada vencido y ninguna sesión a medias. Lo siguiente es practicar: una sesión de práctica sobre el banco que tengas, o un examen oficial si el material está completo.» · «Sin sesiones de estudio / No hay ninguna sesión previa que continuar. Se empieza desde la sección Estudiar…» · «Nada esperando tu decisión…» · «¿Listo para estudiar? **faltan 3 cosas**» con tres pasos («Material por papel: todavía nada», «Preguntas por tema: todavía nada», «Claves activas: todavía nada») y su enlace | **Sí**: cada paso lleva a la bandeja, al banco o al programa; el Inicio vacío es, de hecho, un asistente de primeros pasos. Pero son **2692 px** con todo el estado del sistema y jerga técnica al final | [`inicio-vacio-1280.png`](../capturas/revision-2026-11/inicio-vacio-1280.png) |
| `/bandeja` | «Todavía no hay lotes / Cuando inventaríes una carpeta aparecerá aquí, con su informe.» | Sí: el formulario de entrada sigue arriba | [`bandeja-vacio-1280.png`](../capturas/revision-2026-11/bandeja-vacio-1280.png) |
| `/temario` | **No está vacío**: la siembra de perfiles deja el temario común (5 bloques · 40 temas, «0 de 40 estudiados»). Útil como comprobación de que el temario no depende del material | — (no es un estado vacío real) | [`temario-vacio-1280.png`](../capturas/revision-2026-11/temario-vacio-1280.png) |
| `/biblioteca` | «Todavía no hay colecciones. Crea una para agrupar material.» · «Todavía no hay ningún documento / Un documento nace al promocionar material ya copiado: la biblioteca no crea obras. Copia el material en la Bandeja y promociónalo: aparecerá aquí con su versión.» | Explica el camino (Bandeja → promocionar) pero **sin ningún enlace**: hay que ir a la Bandeja a mano | [`biblioteca-vacio-1280.png`](../capturas/revision-2026-11/biblioteca-vacio-1280.png) |
| `/preguntas` | «Todavía no hay ningún conjunto de preguntas. Se crea aquí debajo: un examen oficial, un banco privado, práctica o un lote generado.» + «▶ Crear un conjunto»; en el banco: «Elige o crea un conjunto para trabajar con sus preguntas.» | **Sí**: despliega el formulario de creación en la misma pantalla | [`preguntas-vacio-1280.png`](../capturas/revision-2026-11/preguntas-vacio-1280.png) |
| `/estudiar` | Enseña el formulario «Preparar la sesión» completo con «Elige un conjunto…» y el enlace «¿No sabes por dónde empezar? Haz un diagnóstico» | **Sí**: es el estado más resuelto; el formulario es el contenido | [`estudiar-vacio-1280.png`](../capturas/revision-2026-11/estudiar-vacio-1280.png) |
| `/errores` | «No hay ningún repaso todavía: se crean solos al fallar una pregunta en una sesión.» · «No hay nada vencido. La cola se llena sola cuando fallas una pregunta en una sesión; si quieres repasar antes de que toque, puedes declarar el resultado de un repaso hecho fuera.» + panel de exportación | Sí: explica el origen de la cola y deja exportar; no hay enlace directo a Estudiar | [`errores-vacio-1280.png`](../capturas/revision-2026-11/errores-vacio-1280.png) |
| `/cambios` | «No hay ninguna versión nueva pendiente de revisar. Un cambio aparece cuando promocionas una segunda versión de un documento que ya tenía una aceptada…» | Parcial: explica el mecanismo, pero no enlaza a la Biblioteca para hacerlo | [`cambios-vacio-1280.png`](../capturas/revision-2026-11/cambios-vacio-1280.png) |
| `/ajustes` | Sin datos: todo a 0 («Total 0 B · recuperable 0 B») y las capacidades declaradas; el diagnóstico y las copias siguen operativos | Sí: las acciones de mantenimiento funcionan sin corpus | [`ajustes-vacio-1280.png`](../capturas/revision-2026-11/ajustes-vacio-1280.png) |
| `/revision` | «No hay propuestas pendientes que agrupar. Cuando el motor proponga algo lo verás aquí…» · «No hay ninguna propuesta esperando tu decisión…» y la cobertura del programa con el árbol | Parcial: ofrece «Buscar propuestas ahora», pero sin corpus no hay nada que proponer | [`revision-vacio-1280.png`](../capturas/revision-2026-11/revision-vacio-1280.png) |

**Valoración de conjunto**: los estados vacíos están cuidados —casi todos dicen **por qué** están
vacíos y **qué hacer**—, pero el de Inicio es desproporcionado (2692 px, con la tabla de capacidades
y las degradaciones declaradas al final) y el de Cambios no enlaza a donde se produce el cambio.

---

## Los tres problemas de diseño más claros

Ordenados de más a menos grave. Son observaciones de producto y de interfaz, no de código: cada una
tiene su captura y su arreglo.

### 1. Revisión no deja revisar: 15.000 px, cuatro tareas apiladas y la decisión fuera de pantalla

**Evidencia**:
[`revision-1280.png`](../capturas/revision-2026-11/revision-1280.png) (15443 px de alto; captura
completa) y [`revision-390.png`](../capturas/revision-2026-11/revision-390.png) (29644 px). Medido en
la captura de 1280: `document.scrollWidth = 1635` frente a `clientWidth = 1280`; **357 elementos**
salen por la derecha, y la celda que contiene los botones de decisión termina en x=1635, es decir
**fuera del viewport**. La pantalla tiene 164 botones y apila cinco bloques distintos: aviso,
«Cola de revisión» (grupos), «Clasificación de este material» (ejes), «Propuestas» (tabla de 51
filas) y «Cobertura del programa» (árbol completo de 33 temas).

**Por qué es un problema**: es la pantalla donde el usuario convierte propuestas en decisiones, y sin
embargo:
- la acción principal («Aceptar / Rechazar / Corregir el tema») queda **a la derecha del viewport**:
  hay que hacer scroll horizontal para decidir, algo que nadie descubre y que en un portátil de
  1280 px ocurre siempre;
- 51 propuestas en una sola tabla sin paginación, filtro por eje ni estado, con un `select` de 33
  temas por fila: el usuario no sabe dónde está ni cuánto le queda;
- cuatro trabajos distintos (lote por grupos, clasificación de un material, propuestas sueltas,
  cobertura del programa) comparten página, así que la jerarquía desaparece: todo parece igual de
  importante.

**Qué lo arreglaría** (en orden):
1. Envolver la tabla en un contenedor con `overflow-x: auto` (o, mejor, quitar del flujo de la tabla
   el `select` de 33 opciones: sustituirlo por un botón «Corregir el tema» que abra un buscador de
   nodos en un panel) para que la página **nunca** desborde a 1280.
2. Paginar o agrupar por eje con colapso («Autoridad (10) · Derechos (6) · Tipo de documento (10) ·
   Tema del programa (24)»), con la barra de acciones del lote **sticky** arriba o abajo.
3. Separar «Cobertura del programa» y «Clasificación de este material» a una pestaña o a un panel de
   detalle: no son parte de la cola de decisión.
4. Medir el objetivo: la primera propuesta decidible debe caber en la primera pantalla a 1280×900 y
   la acción no debe exigir scroll horizontal.

### 2. La interfaz habla en jerga de implementación: UUID, hashes, códigos en inglés y fechas ISO

**Evidencia**:
- [`cambios-1280.png`](../capturas/revision-2026-11/cambios-1280.png): la lista principal identifica
  cada cambio con dos UUID —
  «Apuntes sinteticos E2E-08 mw8f42ou: `ebd7e72b-c552-43be-8478-5a77abb7d121` →
  `7ff4f5a2-89eb-4776-a951-92fb7a59b108`».
- [`biblioteca-1280.png`](../capturas/revision-2026-11/biblioteca-1280.png) y
  [`biblioteca-documento-versiones-1280.png`](../capturas/revision-2026-11/biblioteca-documento-versiones-1280.png):
  la columna «VERSIÓN ACTIVA» es un UUID y cada versión muestra `hash: fa2a60dc…`.
- [`revision-1280.png`](../capturas/revision-2026-11/revision-1280.png): la columna SUJETO mezcla
  texto y código interno («Solo uso privado `private_use_only`», «Temario o programa `curriculum`»,
  «Apuntes personales `personal_notes`»).
- [`buscar-1280.png`](../capturas/revision-2026-11/buscar-1280.png): «la versión está en estado
  «superseded»», badge «accepted», «recuperación lexical», y un resumen con
  `corpus 18-2026-11-08 22:42:44.669074-4`.
- [`ajustes-1280.png`](../capturas/revision-2026-11/ajustes-1280.png): «esquema
  0023_block_practice», «ordenada por bm25», «lease 60 s», «DEBT-014», tabla de contadores.
- Fechas: `2026-11-08T22:43:07.294168` (Inicio, Estudiar, Plantillas), `2026-11-08 22:42:45`
  (Ajustes), `2025-12-22` (Inicio), `2026-11-08` (Cambios) — ninguna está localizada.
- Referencias internas en pantalla: «(ADR-017)» en Inicio, «(07_UI-UX §12)» en Revisión,
  «(07_UI-UX §3, §5)» en el Inicio vacío.

**Por qué es un problema**: el usuario tiene que distinguir versiones de su propio material y no
puede: dos UUID no se leen, no se memorizan y no dicen «qué versión es más nueva». Los códigos en
inglés dentro de frases en español hacen dudar de si la interfaz está sin terminar. Las fechas ISO
con microsegundos parecen un volcado de base de datos. Y las referencias a documentos internos
(ADR, § de la especificación, DEBT) son pistas de que la pantalla está escrita para el equipo, no
para quien estudia.

**Qué lo arreglaría**:
1. Un componente de versión legible: «v2 · 7 nov 2026» (y en detalle, el UUID solo si se pide).
2. Traducir los enums en el límite de la vista: `private_use_only` → «solo uso privado»,
   `curriculum` → «temario», `superseded` → «sustituida», `accepted` → «aceptada»;
   `texto extraído` ya está traducido, así que el patrón existe.
3. Localizar fechas con `Intl.DateTimeFormat('es-ES')` (y horas sin microsegundos).
4. Colapsar el detalle técnico en Ajustes → «Diagnóstico»; fuera de ahí, nada de DEBT/ADR/§.
5. Revisar el copy que narra limitaciones de implementación («la API todavía no filtra por
   derechos»): decir «el filtro de derechos se aplica a lo ya cargado» sin la excusa técnica.

### 3. Bandeja: cuatro formas de entrar a la vez y la principal es escribir una ruta absoluta

**Evidencia**: [`bandeja-1280.png`](../capturas/revision-2026-11/bandeja-1280.png) (2237 px, 27
botones) y [`bandeja-390.png`](../capturas/revision-2026-11/bandeja-390.png) (3994 px). La primera
tarjeta, «Entrada», pide «Carpeta a inventariar (ruta absoluta)» con un `input` que muestra
`F:\EspacioCodigo\material-para-probar` y el botón «Inventariar (solo lectura)». Justo debajo,
«Otras formas de entrada» ofrece soltar ficheros/carpetas, elegir carpeta, pegar texto y traer una
URL. Los controles nativos de fichero aparecen en inglés: «Choose Files · No file chosen».

**Por qué es un problema**: la pantalla de entrada es la primera que ve alguien con material
pendiente, y le pide lo más difícil (teclear una ruta de Windows) mientras ofrece lo más fácil
(arrastrar) en un segundo bloque. Cuatro mecanismos con el mismo peso visual no dan una jerarquía:
el usuario no sabe cuál es «el camino». Además, el inglés de los controles nativos rompe el idioma de
toda la aplicación justo en la acción clave.

**Qué lo arreglaría**:
1. Una única zona primaria grande: «Arrastra aquí tus apuntes o elige una carpeta», con selector de
   carpeta nativo (`webkitdirectory`) como acción real; la ruta de texto queda como opción avanzada
   plegada.
2. Las otras entradas (texto pegado, URL) como pestañas o enlaces secundarios, no como bloques de
   igual tamaño.
3. Sustituir los `input type=file` nativos por un botón propio en español y ocultar el control del
   sistema (o, como mínimo, un texto guía en español que los acompañe).
4. Medir el objetivo: en la primera pantalla a 1280×900 deben caber el título, la zona de arrastre y
   el historial reciente; hoy la primera pantalla no llega a «Lotes recientes».

---

## Otros hallazgos (menores, pero se ven)

- **Plural mecánico «(s)» en toda la aplicación**: «4 pregunta(s) vencida(s)», «18 aviso(s) y
  error(es)», «9 decisión(es)», «1 cambiada(s) · 0 nueva(s)», «6 fallo(s) acumulado(s)». Es el
  defecto de copy más repetido. Hay además concordancias sueltas: «1 plantillas del conjunto»
  (Plantillas), «1 pendientes» (Estudiar), «recuperación lexical» (Buscar), «1 versiones» (Biblioteca).
- **Avisos que se comen la primera pantalla en móvil**: en
  [`revision-390.png`](../capturas/revision-2026-11/revision-390.png) el aviso «Esto son propuestas,
  no hechos» ocupa ~600 px: la cola de revisión no aparece hasta pasado más de un scroll completo.
  Lo mismo, en menor medida, con el lead de tres líneas de Cambios y el de Estudiar.
- **Buscador global sin afordancia**: en la cabecera hay una etiqueta «Buscar en el corpus» junto a
  un campo vacío sin placeholder, sin icono y sin botón; a 390 el campo ocupa una fila entera y no se
  sabe cómo se envía (Enter, se deduce). Ver
  [`inicio-390.png`](../capturas/revision-2026-11/inicio-390.png).
- **«¿Qué queda?» desordenado**: en Temario, la lista «Qué queda» sale I, III, IV, V, II (ordenada
  por cantidad restante), no en orden oficial I–V.
- **Copy que contradice al formulario**: la práctica libre dice «sin reservas ni tiempo» y ofrece
  Reservas y Tiempo máximo (ver pantalla 16).
- **Aviso repetido por fila**: en Errores, cada entrada repite los dos mismos párrafos explicativos.

---

## Comprobaciones técnicas

### Errores de consola por pantalla

Se registró cada mensaje de consola de tipo `error` y cada `pageerror` durante la carga y el
asentamiento de la pantalla (1280 y 390). Resultado:

| Grupo de pantallas | Errores de consola |
|---|---|
| Las 20 pantallas con datos y las 10 vacías | **1**: `The Content Security Policy directive 'frame-ancestors' is ignored when delivered via a <meta> element.` — la CSP está puesta en `index.html` (ver `apps/web/index.html`), y `frame-ancestors` **no es válido por `<meta>`**: el navegador lo ignora y avisa. Inocuo, pero ensucia la consola en todas las páginas; se quita de la meta y se deja para la cabecera del servidor (o se elimina, porque `frame-ancestors 'none'` por meta nunca se aplica). |
| **Inicio** y **Programa** | **4**: la anterior + **3 respuestas 404** de `/api/v1/reviews/mastery` (una sin `opposition_id` y dos con él). El cuerpo del 404 es `{"detail":"No existe repaso con ese identificador."}`, lo que delata el problema: la ruta **`/api/v1/reviews/{review_id}` está declarada antes que `/api/v1/reviews/mastery`** en `apps/api/opofuente/api/routes/reviews.py` (líneas 253 y 297), así que FastAPI toma «mastery» como un id de repaso. Consecuencia visible: el «dominio estimado por tema» de Inicio y de Programa no se enseña y **no hay ningún aviso**: la pantalla simplemente omite ese dato. Arreglo: mover la ruta estática de `mastery` por encima de la dinámica `{review_id}` (y añadir una prueba de contrato). |
| Capturas de estado (cargando/error) | 0: son interceptaciones del navegador, no se registran errores de consola. |

No hubo `pageerror` (excepciones no capturadas de React) en ninguna pantalla.

### Desbordes horizontales (`scrollWidth` frente al ancho del viewport)

| Pantalla | Ancho de ventana | `scrollWidth` | Elementos que se salen | Consecuencia |
|---|---|---|---|---|
| **Revisión** (`/revision`) a 1280 | 1280 | **1635** | 357 elementos sin recorte; la tabla mide 1292 px y su celda de decisión termina en 1635 | Barra horizontal y botones «Aceptar / Rechazar» fuera de pantalla. La captura fullPage mide, por eso, 1635 px de ancho |
| **Biblioteca → Versiones y diff** a 1280 | 1280 | **1443** | 15 elementos; la tabla de versiones mide 1100 px y empieza en x=343 | Barra horizontal; la columna «Acciones» queda a la derecha. Captura de 1443 px de ancho |
| **Biblioteca → Versiones y diff** a 390 | 390 | **504** | No hay caja más ancha que 390, pero **sí hay texto que no rompe**: identificadores como `ebd7e72b-c552-43be-8478-5a77abb7d121` y hashes SHA-256 de 64 caracteres estiran la línea hasta 504 px | Barra horizontal también en móvil (captura de 504 px de ancho) |
| Resto de pantallas (todas) a 1280 | 1280 | 1280 | — | Sin desborde |
| Resto de pantallas (todas) a 390 | 390 | 390 | — | Sin desborde: por debajo de 640 px las tablas pasan a bloques (`@media (max-width: 640px)`), lo que evita el scroll horizontal de tabla a costa de alargar la página (Revisión: 29644 px) |

La causa es común: `.table { width: 100% }` sin contenedor con `overflow-x`, celdas cuyo contenido
mínimo (un `select` de 33 opciones, una fila de botones, un UUID sin puntos de corte) exige más ancho
que la tarjeta, y ningún `overflow-wrap: anywhere` en las celdas de tabla (sí existe en `.facts dd` y
otros textos). Solo se mitiga por debajo de 640 px convirtiendo la tabla en bloques, y aun así los
identificadores largos siguen estirando la línea.

> **Nota de método**: el medidor automático de `capturar.mjs` anotó «sin desborde» en
> `biblioteca-documento-versiones-390` porque el diff de versiones terminó de renderizarse **después**
> de que la página pareciera asentada; el PNG (504 px) delató el desborde real. La medición fiable es
> la del ancho del PNG fullPage. En las pantallas grandes no hay esta ambigüedad: la medición y el
> ancho del PNG coinciden (1635 y 1443).

### Enlaces

- **65 rutas internas distintas** recogidas de las pantallas con datos: **todas responden 200**.
  El 100 % se resuelve porque el `preview` de Vite sirve el `index.html` para cualquier ruta (la SPA
  nunca da 404 HTTP); por eso, además del código HTTP, se comprobó que la ruta case con
  `apps/web/src/app/routes.tsx`.
- **56 entidades referenciadas por la dirección** comprobadas contra la API (nodos de temario,
  documentos, conjuntos, preguntas y convocatorias de `?convocatoria=`): **todas 200**. No hay
  enlaces a fichas de entidades borradas.
- **14 enlaces externos** (no se descargan; solo se enumeran): 13 a portales de convocatorias
  (`oposicionesinformatica.com`, `saludcastillayleon.es`, `boe.es`) y 1 a la API local para abrir el
  fichero original (`/api/v1/document-versions/<id>/original`).
- **Lo que no se puede detectar así**: enlaces que lleven a una pantalla con un estado de error o a
  una pestaña que no exista en la siguiente versión. En esta pasada no apareció ninguno.

### Qué no se pudo capturar y por qué

| No capturado | Motivo |
|---|---|
| Estado de **respuesta del RAG** (botón «Preguntar» de `/buscar`) | La acción **escribe** una consulta en el corpus; toda la sesión de captura fue de solo lectura para no tocar los datos de la suite. El estado de resultados (búsqueda literal) sí está capturado. |
| Pestañas **Estructura, Asignaciones y Metadatos** de la ficha de documento | Se capturaron Lector (por defecto) y Versiones y diff; las otras tres quedan fuera del alcance mínimo y no se añadieron para no inflar el paquete (se pueden añadir con un `preparar` en `capturar.mjs`). |
| Pestaña **Importar** de Preguntas y pestaña **Conceptos** de Errores | Mismo criterio: el estado por defecto de cada pantalla ya está capturado; el encargo pedía las pantallas y los estados vacíos, no todas las pestañas. |
| **Modales y confirmaciones** (purga en Ajustes, «Marcar sustitución…» en Biblioteca) | Son acciones que escriben o abren un `confirm` del navegador; se dejaron fuera por la misma regla de solo lectura. |
| **Tema oscuro** | La aplicación declara `color-scheme: light` en `global.css` (aunque `index.html` anuncia `light dark`): no hay tema oscuro que capturar. |
| **Vista de resultado de examen** (puntuación por partes) | La sesión disponible en el corpus sintético es de práctica en marcha; el resultado de un simulacro ya terminado existe en el historial, pero abrirlo desde `Estudiar` habría requerido navegar el historial con clics que esta pasada no hizo. La pantalla de resultado queda pendiente de una segunda pasada. |

---

## Paquete para revisión externa

### Qué enviar y en qué orden

Máximo recomendado: **12 capturas** para una primera lectura de 20-30 minutos. Todas están en
`docs/capturas/revision-2026-11/`.

1. `inicio-1280.png` — la portada con trabajo pendiente (primera impresión).
2. `inicio-vacio-1280.png` — la portada de un usuario nuevo (primer uso).
3. `bandeja-1280.png` — la entrada de material.
4. `biblioteca-1280.png` + `biblioteca-documento-versiones-1280.png` — la biblioteca y el diff.
5. `preguntas-conjunto-1280.png` — el banco de 85 preguntas (densidad de tabla).
6. `estudiar-1280.png` — una sesión en marcha.
7. `errores-1280.png` — la cola de repaso.
8. `revision-1280.png` — la pantalla de decisión (problema nº 1).
9. `cambios-1280.png` — el diff de versiones (problema nº 2).
10. `ajustes-1280.png` — la pantalla técnica.
11. `inicio-390.png`, `revision-390.png` y `temario-390.png` — el comportamiento móvil.

Si el revisor solo puede mirar una: **`revision-1280.png`** (con la advertencia de que es la peor
pantalla). Si puede mirar tres: Inicio, Revisión y Bandeja.

### Preguntas concretas para el revisor externo

1. **Jerarquía**: en Inicio hay cuatro llamadas a la acción compitiendo («repaso», «bandeja»,
   «propuestas», «cambios»). ¿Cuál debería ser la única acción primaria de la portada y qué habría
   que quitar de ella?
2. **Revisión**: ¿cómo rediseñarías una pantalla que debe resolver 51 propuestas de clasificación con
   cuatro ejes distintos? ¿Tabla con filtros y lote, cola una-a-una, o agrupación por eje con
   colapso? ¿Qué harías para que la decisión no exija scroll horizontal?
3. **Lenguaje**: los identificadores de versión son UUID y hay códigos en inglés
   (`private_use_only`, `superseded`, `accepted`). ¿Qué convención de nombres y fechas propondrías
   para que un opositor distinga «la versión que estudia» de «la anterior»?
4. **Onboarding**: compara `inicio-vacio-1280.png` con `inicio-1280.png`. ¿El primer uso se entiende
   en 30 segundos? ¿Qué sobra del «Estado del sistema» en la portada?
5. **Entrada de material**: en Bandeja, ¿cuál debería ser el camino principal y qué hacer con las
   otras tres formas de entrada? ¿Cómo se resuelve el inglés de los controles nativos de fichero?
6. **Móvil**: en `revision-390.png` el aviso ocupa la primera pantalla. ¿Qué patrón usarías para
   avisos largos en móvil (resumen + «más información», hoja inferior, banner)?
7. **Estados vacíos**: de los ocho capturados, ¿cuáles cumplen «dice por qué está vacío y qué hacer»
   y cuáles son solo texto?
8. **Densidad**: ¿qué tres elementos quitarías de la aplicación para que se lea mejor sin perder
   información? (Candidatos: la tabla de capacidades de Inicio, la explicación repetida por fila en
   Errores, el desplegable de 33 temas de Revisión).

### Prompt sugerido (una página)

```text
Eres revisor de producto y diseño de interfaces. Te paso el inventario de pantallas y capturas de
OpoFuente, una aplicación local (Windows, un solo usuario) para preparar oposiciones: importa
material propio, lo clasifica por temas con propuestas que el usuario confirma, y permite estudiar
con preguntas y repasar errores. Es local-first: los datos no salen del ordenador.

Contexto que debes dar por bueno:
- Las capturas con datos usan un corpus SINTÉTICO de pruebas: títulos como «Apuntes sinteticos
  E2E-08 mw8f42ou», textos sin tildes y UUID visibles son datos de prueba, no decisiones de diseño.
- Los textos de la interfaz (etiquetas, avisos, botones, estados vacíos) sí son reales.
- Capturas fullPage a 1280×900 y 390×844, tema claro.

Tarea:
1. Lee el inventario y mira las capturas en el orden que se indica.
2. Evalúa: (a) jerarquía y foco por pantalla; (b) densidad y legibilidad, sobre todo en tablas
   largas; (c) claridad del lenguaje para un opositor no técnico; (d) coherencia entre estados
   (cargando, vacío, error); (e) comportamiento en móvil.
3. Contrasta los tres problemas que ya hemos detectado (Revisión, jerga interna, Bandeja) y di si
   estás de acuerdo, si hay otro más grave que se nos ha pasado, y qué arreglarías primero.
4. Entrega: 5 recomendaciones priorizadas, cada una con pantalla, problema, arreglo concreto y
   esfuerzo estimado (bajo/medio/alto). Señala lo que NO cambiarías.
No propongas funcionalidad nueva que no exista en las capturas: evalúa lo que hay.
```

---

## Anexo de textos

El volcado literal del `innerText` visible por pantalla (con datos y en vacío, incluidos los estados
de carga y error) está en **[`TEXTOS-PANTALLAS-2026-11.md`](./TEXTOS-PANTALLAS-2026-11.md)**, generado
desde los JSON de captura con `node docs/interfaz/generar-textos.mjs`. Se cita aquí para que el
revisor externo pueda juzgar el copy sin abrir las imágenes.

---

## Anexo: ficheros de captura

Los 64 PNG del directorio [`docs/capturas/revision-2026-11/`](../capturas/revision-2026-11/). Tamaño = píxeles reales del PNG (ancho × alto); el alto es el de la página completa. Las capturas
marcadas con un ancho mayor que su viewport son la prueba visual del desborde horizontal.

| Fichero | Tamaño (px) | Peso |
|---|---|---|
| `ajustes-1280.png` | 1280×3333 | 244 KB |
| `ajustes-390.png` | 390×5502 | 221 KB |
| `ajustes-vacio-1280.png` | 1280×3192 | 230 KB |
| `ajustes-vacio-390.png` | 390×5293 | 212 KB |
| `bandeja-1280.png` | 1280×2236 | 200 KB |
| `bandeja-390.png` | 390×3993 | 191 KB |
| `bandeja-vacio-1280.png` | 1280×1466 | 95 KB |
| `bandeja-vacio-390.png` | 390×2202 | 85 KB |
| `biblioteca-1280.png` | 1280×1554 | 157 KB |
| `biblioteca-390.png` | 390×2848 | 138 KB |
| `biblioteca-documento-1280.png` | 1280×2964 | 262 KB |
| `biblioteca-documento-390.png` | 390×5058 | 239 KB |
| `biblioteca-documento-versiones-1280.png` | 1443×3219 | 320 KB |
| `biblioteca-documento-versiones-390.png` | 504×5903 | 308 KB |
| `biblioteca-vacio-1280.png` | 1280×915 | 69 KB |
| `biblioteca-vacio-390.png` | 390×1558 | 66 KB |
| `buscar-1280.png` | 1280×1418 | 125 KB |
| `buscar-390.png` | 390×2209 | 116 KB |
| `cambios-1280.png` | 1280×1462 | 140 KB |
| `cambios-390.png` | 390×2703 | 133 KB |
| `cambios-vacio-1280.png` | 1280×900 | 50 KB |
| `cambios-vacio-390.png` | 390×1022 | 43 KB |
| `errores-1280.png` | 1280×1651 | 129 KB |
| `errores-390.png` | 390×2589 | 121 KB |
| `errores-vacio-1280.png` | 1280×900 | 54 KB |
| `errores-vacio-390.png` | 390×1177 | 48 KB |
| `estudiar-1280.png` | 1280×1962 | 130 KB |
| `estudiar-390.png` | 390×3919 | 125 KB |
| `estudiar-vacio-1280.png` | 1280×900 | 54 KB |
| `estudiar-vacio-390.png` | 390×1084 | 49 KB |
| `inicio-1280.png` | 1280×3564 | 289 KB |
| `inicio-390.png` | 390×5824 | 271 KB |
| `inicio-cargando-1280.png` | 1280×1078 | 50 KB |
| `inicio-error-1280.png` | 1280×1782 | 98 KB |
| `inicio-vacio-1280.png` | 1280×2692 | 225 KB |
| `inicio-vacio-390.png` | 390×4691 | 211 KB |
| `no-encontrada-1280.png` | 1280×900 | 28 KB |
| `no-encontrada-390.png` | 390×844 | 23 KB |
| `preguntas-1280.png` | 1280×903 | 83 KB |
| `preguntas-390.png` | 390×1949 | 79 KB |
| `preguntas-cargando-1280.png` | 1280×900 | 35 KB |
| `preguntas-conjunto-1280.png` | 1280×6496 | 744 KB |
| `preguntas-conjunto-390.png` | 390×20942 | 779 KB |
| `preguntas-error-1280.png` | 1280×900 | 40 KB |
| `preguntas-plantillas-1280.png` | 1280×900 | 58 KB |
| `preguntas-plantillas-390.png` | 390×1250 | 51 KB |
| `preguntas-vacio-1280.png` | 1280×900 | 39 KB |
| `preguntas-vacio-390.png` | 390×909 | 34 KB |
| `programa-1280.png` | 1280×4733 | 456 KB |
| `programa-390.png` | 390×11647 | 475 KB |
| `revision-1280.png` | 1635×15443 | 1404 KB |
| `revision-390.png` | 390×29644 | 1299 KB |
| `revision-vacio-1280.png` | 1280×3508 | 319 KB |
| `revision-vacio-390.png` | 390×9210 | 342 KB |
| `temario-1280.png` | 1280×2555 | 151 KB |
| `temario-390.png` | 390×3496 | 141 KB |
| `temario-tema-1280.png` | 1280×1357 | 98 KB |
| `temario-tema-390.png` | 390×1977 | 91 KB |
| `temario-tema-convocatoria-1280.png` | 1280×1309 | 108 KB |
| `temario-tema-convocatoria-390.png` | 390×1980 | 101 KB |
| `temario-tema-practicar-1280.png` | 1280×900 | 63 KB |
| `temario-tema-practicar-390.png` | 390×1339 | 57 KB |
| `temario-vacio-1280.png` | 1280×2555 | 149 KB |
| `temario-vacio-390.png` | 390×3496 | 139 KB |

## Limitaciones conocidas de esta pasada

- **Datos sintéticos**: los títulos, los enunciados y las fechas de contenido son de la suite E2E.
  El corpus no tiene material asignado a los 40 temas del temario común, así que la ficha de tema y
  el avance del temario salen con estados que en datos reales serían distintos.
- **Una sola pasada y un solo día**: no se capturó el resultado de examen ni el estado de respuesta
  del RAG (ver tabla anterior). El informe técnico por pantalla está en
  `docs/interfaz/.captura-datos.json` y `docs/interfaz/.captura-vacio.json` (no se versionan como
  entregable; se regeneran con el script).
- **El `dist/` se reconstruyó** para que las capturas correspondieran al commit `c5d6f93`; si el
  revisor compara con una build anterior, `temario-tema-practicar` puede diferir (el control
  «Reservas» es nuevo).
- **No hay tema oscuro** que capturar: la aplicación declara solo `color-scheme: light`.
