# Lo que ha hecho DeepSeek en esta sesión, para Claude (7 de octubre de 2026)

Resumen de todas las rondas de trabajo, agrupado por bloques y con los números que los sostienen. Todo lo
que dice «en `main`» está en `main` y pasó las 18 puertas. El propietario pidió este resumen para
pasártelo; al final están las decisiones abiertas y lo que queda.

## Dónde está el repositorio

- `main` = **`47c1399`** («F2: la capa del alumno (/api/v1/student), owner_id y modo publico»).
- `opofuente-main` sigue con **41 ficheros sin guardar** tuyos, intactos: no he tocado ni uno.
- Árboles de trabajo vivos: `opofuente-arreglos` (puertas), `opofuente-alumno` (ruta de temas),
  `opofuente-f2` (F2). Las ramas ya fusionadas son `fechas-con-zona`, `sesiones-y-aviso-api`,
  `f0-capturas-y-privacidad`, `f1-zonas`, `f2-mapa-preguntas`, `f2-alumno-base`, `f2-api-alumno`.
- Las claves de API (Stitch y DeepSeek) **no han entrado en ningún repositorio**; puedes revocarlas.

## Bloque 1 — Zona horaria (`e510f97`)

El cronómetro de una práctica empezaba en `2:00:03` y un examen de 120 minutos nacía agotado. Causa
medida: SQLite no guarda la zona, la API servía `2026-10-05T10:43:52.793645` y el navegador lo tomaba
por hora de Madrid. Arreglado en la base, en un solo sitio: un tipo de columna `UtcDateTime` en las **79**
columnas de fecha, que al leer devuelve la fecha con UTC y al escribir normaliza. En la web,
`elapsedSeconds` toma por UTC cualquier fecha sin zona. **Antes/después**: la sesión en marcha arrancada
a las 10:43:52Z contaba 4.999 s reales en vez de 12.199.

## Bloque 2 — Sesiones y aviso de API caída (`a19d13a`)

- La lista de sesiones no decía de qué era cada una (cinco exámenes oficiales eran cinco filas iguales
  porque solo llevaba la etiqueta de la clave, que llega a listar 21 plantillas). Ahora cada sesión
  **congela una etiqueta de contexto** («TAI ingreso libre 2025 · modelo A…»).
- **`DELETE /study-sessions/{id}`**: borra si no tiene respuestas, abandona si las tiene (nunca borra
  historial con respuestas). Auditado. Se descartaron las 5 sesiones de prueba del propietario con copia
  de seguridad previa.
- **Un solo aviso** cuando la API no responde, en vez de ocho «Failed to fetch» en inglés.
- Fechas legibles en la interfaz (`lib/fechas.ts`).

## Bloque 3 — Los apuntes por tema (el dossier) (`e5ce278`)

Medido por dentro: de los 99 s del tema II.1 y 53,6 s del I.1, **todo era la consulta** (el cálculo en
Python eran 0,16 s). La consulta unía los tramos con los mapeos mediante un `OR` de cinco condiciones y
eso impedía usar los índices: SQLite comparaba cada tramo con las 39.242 filas de mapeos. Ahora son tres
lecturas con índice y el emparejamiento en memoria. **I.1: 53,6 → 2,01 s. II.1: 51,6 → 1,99 s.** Lo
sostiene una prueba que compara las dos consultas (mismos tramos, mismos estados, mismo orden), porque el
dossier se archiva y un tramo de más cambiaría la huella de contenido.

## Bloque 4 — Diseño: capturas, v0 y Stitch (`7f5b889`, `ef45b16`, `3ebe0dd`)

- **`npm run screens`**: recorre las rutas a 1280×800 y 390×844, guarda PNG en `artifacts/screens/` y
  escribe un informe con tiempos, errores de consola, violaciones de axe y **palabras prohibidas**.
- **El detector de palabras**, corregido tras tu revisión: dos listas (`DATOS_PROHIBIDOS` en toda la
  pantalla; `LENGUAJE_INTERNO` solo fuera de los contenedores `data-contenido`), palabras completas con
  límites Unicode (con `\b` «sas» contaba dentro de «casas») y sin distinguir acentos. 11 pruebas.
- **`frame-ancestors` fuera de la meta**: las 24 capturas salen ya con **0 errores de consola**.
- **v0, una sola llamada** (chat `fNfFdZDmTgJ`): prototipo del alumno con el concepto de la hoja de
  respuestas, **21 capturas**. Dos correcciones al guion: la clave necesita el prefijo **`v1:`** (sin él,
  401) y el campo es **`message`**, no `initialMessage`.
- **Stitch**: 13 pantallas (11 del alumno + 2 de administración) con la dirección nueva, comprobado sobre
  el HTML (crema y azul viejos: 0 apariciones; papel nuevo y Atkinson: presentes). Hallazgos: la
  `downloadUrl` es una **miniatura de 512 px** (la grande pide `=s2560`/`=w1280`), y
  `apply_design_system` **no cambia los colores por sí solo**. Todo en `artifacts/design/`.

## Bloque 5 — F1: las dos zonas (`8e10083`)

La aplicación por fin tiene **zona de alumno** (7 secciones: Inicio, Temario, Tests, Simulacros,
Exámenes, Fallos, Progreso) y **panel** (11), con el marco elegido **por la dirección** (rutas
envolventes), las **diez direcciones viejas redirigidas conservando consulta y ancla** (si no,
`/biblioteca?documento=…` perdía la ficha) y las seis secciones nuevas con `ComingSoonPage` que saca
título y frase del propio mapa de navegación. De la portada del alumno se fueron los contadores de
bandeja/revisión, las acciones pendientes de revisión, la actividad de lotes y **el estado del sistema,
que enseñaba la ruta del directorio de datos**.

**Verificado por mí** con una corrida propia completa: 18/18 en 28:37, 257 unitarias web, 57 E2E, 503 de
integración. Comprobé además con el buscador que la zona del alumno no contiene vocabulario interno (las
dos únicas apariciones son comentarios que explican lo retirado).

## Bloque 6 — Ruta para asignar tema a una pregunta (`ceb04a5`, `d0d6dfb`)

No existía **ninguna** forma por HTTP de decir a qué tema pertenece una pregunta; la vez que se escribió
directo en la base (los 440 mapeos del 2-oct) quedó **sin auditoría** (los otros 12.047 sí la tienen).
Ahora hay `POST`/`GET`/`DELETE /questions/{id}/topics`, idempotente (`200` con `created: true|false`),
**409 con motivo** si el destino no es un tema, y **actor identificable** (`local` o
`llm:deepseek-flash`). El chequeo «solo temas» vive en el servicio, no en el método compartido, para **no
cambiar el comportamiento de la catalogación automática S12.6**. La carrera del `UNIQUE` se cierra
releyendo: sin 500, con un solo evento de auditoría. La prueba sabe fallar (comprobado desactivando el
`except`).

## Bloque 7 — Orden numérico de los temas y `distribution` (`73bb451`, `fd0f7de`, `1212871`)

- **El orden**: `IV.10` salía detrás de `IV.1`. Arreglado **en SQL** (`curriculum_order.py`: bloque →
  tema → epígrafe, texto no numérico al final) y usado por el programa, la cobertura y los temas de una
  pregunta. Medido: antes `['IV.1','IV.10','IV.2']`, después `['IV.1','IV.2','IV.10']`. Dato: en la base
  `position` y orden numérico coincidían en los 62 grupos, así que el síntoma estaba en los listados
  planos (TAI y **cuatro de Guardia Civil** con `1.1.10` tras `1.1.1`).
- **`distribution`** (`personal` | `public`) con dos migraciones separadas y **aplicadas a los datos
  reales** (con copia de seguridad de 2,47 GB antes): **4 públicos** —los cuatro exámenes del INAP— y
  **229 personales**, con 17.424 preguntas y 575 claves intactas. Ojo: hay **ocho** filas con esos cuatro
  títulos porque el importador corrió dos veces; la migración marca solo las cuatro activas.
- **Y un arreglo que era culpa mía**: al poner el `globalSetup` que limpia `.e2e-data` en cada corrida
  destapé que `program.spec.ts` se apoyaba en preguntas que crean los specs que corren **después**. Ahora
  esa prueba **se crea sus propios datos** usando la ruta de asignar tema. Se revisaron las 13 specs: no
  hay más dependencias de orden.

## Bloque 8 — F2: la capa del alumno (`47c1399`)

`/api/v1/student/overview`, `/syllabus`, `/topics/{codigo}` (acepta `IV.10` y `IV-10`, **ningún UUID**) y
`/progress`. **Esquemas propios sin campos prohibidos**: no se filtra al final, no hay dónde poner una
evidencia, un conjunto, una clave, una versión o una ruta. Lo demuestra una prueba que recorre **las 7
respuestas** con TAI **y Celador** sembrados y falla si una clave o un valor contiene lo que no debe
(incluidos los identificadores sembrados), exigiendo además 33 temas y progreso real: sin datos, «no hay
fugas» no demostraría nada. **`owner_id`** en las cinco tablas del progreso con migración de ida y vuelta,
y el listado de sesiones filtrando por dueño. Y las dos variables en el servidor
(`OPOFUENTE_STUDENT_OPPOSITION`, `OPOFUENTE_PUBLIC_MODE`), con prueba del modo público.

**Verificado en vivo por mí** contra los datos reales: `overview` (4 bloques, 3 repasos vencidos),
`syllabus` con `I.1, I.2, I.3, I.4` y **IV.1 antes de IV.10 = True**, base en revisión `0027_owner_id`.

## Tres trampas de operación de las puertas (documentadas)

1. **Nunca** `gates.ps1` dentro de una tubería (`… 2>&1 | Tee-Object`): el stderr de `uv` se vuelve error
   terminante y la puerta 11 falla con código −1 sin estar rota.
2. El registro con `Start-Process -RedirectStandardOutput`, **nunca con `>`**: los `OK:` van por
   `Write-Host` y `>` no los captura (perdí una corrida por esto).
3. Un árbol de trabajo nuevo **no trae `data\sources`** (ignorado por git) y la puerta 17 falla con
   «faltan fuentes locales» pareciendo un fallo del código.

## Dos fallos míos, dichos

- Apliqué un arreglo del botón desactivado que **nunca llegó al fichero** (la edición falló y no la
  repetí) y lo anuncié como hecho. Lo cazaste tú en la captura. Ya está: el color de cada variante solo se
  aplica con `:not(:disabled)`.
- Llamé «pre-existente y del producto» al fallo de la puerta 18 cuando en realidad eran los **datos
  acumulados de la propia suite** (649 ficheros, 148 MB) y, después, una dependencia de orden.

## Decisiones abiertas

**Del propietario:**
1. Las **≈2.100 preguntas que son de otras administraciones** (Pontevedra, Zaragoza, Barcelona, Murcia,
   Asturias… importadas al banco de TAI): ¿se marcan «fuera de temario» —en bloque por conjunto de origen,
   que es gratis— o se les fuerza un tema?
2. ¿El resultado de la clasificación se guarda con la ruta nueva (ya implementada) o con un guion?

**De diseño, para ti:**
3. `POST /student/tests` y `/student/mock-exams` quedaron fuera a propósito: componer **varios bloques** o
   el **simulacro 80+20 con elección de bloque III/IV** exige que `StudyService` sepa hacerlo (hoy compone
   por conjunto o por un tema, y del simulacro coge la parte entera de un solo conjunto). Hacerlo en la
   capa del alumno duplicaría el congelado de clave/reservas/penalización. **Es decisión sobre
   `StudyService`.**
4. **El epígrafe no existe para TAI**: los 125 nodos `epigraph` de la base son todos de Celador. El plan
   A.3 no es ejecutable tal cual; los 134 epígrafes ya están derivados del título oficial en
   `temario-tai.json` y hay que decidir dónde se guardan.
5. `owner_id` no llega a `review_items`/`review_events` (índice único por pregunta): es trabajo de las
   cuentas.

## Lo que queda

1. Portar a `src/ui` las pantallas aprobadas (Stitch para escritorio y el editor de apuntes; v0 para
   móvil), con sus capturas en `npm run screens`.
2. El panel de administración: temario (crear, renombrar, reordenar, archivar), apuntes con versiones y
   publicar, preguntas con su correcta y explicaciones, e informes de preguntas erróneas.
3. Los exámenes anteriores del INAP, importados con sus claves.
4. El paso A de los apuntes (**0,0036 $** gastados en el piloto; el paso completo, menos de 1 $), los tres
   temas piloto (IV.7, I.6 e I.1) y los 33.

## Documentos que dejé escritos

`docs/reviews/`: `P0-4-LOS-APUNTES-POR-TEMA-2026-10.md`, `F1-LAS-DOS-ZONAS-2026-10.md` (con las tres
trampas de las puertas), `F2-PLAN-DE-EJECUCION-2026-10.md`, `PASO-A-APUNTES-LO-QUE-HAY-QUE-DECIDIR-2026-10.md`,
`F0-CAPTURAS-Y-PALABRAS-PROHIBIDAS-2026-10.md`, `PUERTA-18-EN-ROJO-POR-LA-REVISION-2026-10.md`.
