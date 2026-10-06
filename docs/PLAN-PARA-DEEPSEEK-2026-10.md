# OpoFuente — lo que falta para estudiar rápido y bien (plan para DeepSeek, 5 de octubre de 2026)

Escrito por Claude tras usar la aplicación **con los datos reales del propietario** (Chrome sobre
`http://127.0.0.1:5173`, API en `8765`, `main = 41e5319`) y recorrer las 11 pantallas también con
datos sintéticos, en escritorio (1280 px) y en móvil (390 px). Cada punto dice **qué se ve**, **por
qué importa para estudiar**, **dónde está en el código**, **qué hacer** y **cómo comprobarlo**.

El objetivo no es añadir funciones: casi todo lo que pide la especificación ya existe (S00–S13 y
S12.x entregados, 18 de 18 puertas en verde). Lo que falta es que **estudiar sea rápido, sin
errores y sin pensar en la herramienta**. La medida de éxito de este plan:

> **Desde abrir la aplicación hasta estar contestando preguntas de un tema: 2 clics y menos de
> 5 segundos.** Contestar una pregunta y pasar a la siguiente: **una tecla**. Ninguna pantalla con
> texto técnico, fechas en bruto o recuentos de miles que nadie va a revisar.

---

## 0. Reglas de trabajo (las de siempre, recordadas)

1. **Una rama por bloque** desde `main`, con su prueba que **falla antes** del arreglo y pasa
   después. `./scripts/gates.ps1` 18/18 antes de fusionar. Nada de desactivar reglas ni de `skip`.
2. **Los datos del propietario** (`F:\OpoFuente\datos`) se tocan solo por la API o con copia de
   seguridad previa (`POST /backups` o `bd_snapshot.py`). Para probar pantallas, usa `.e2e-data` o
   una copia.
3. **Medir antes y después** y dejarlo escrito en `docs/reviews/` (como hasta ahora).
4. Al terminar cada bloque, **recorre a mano** el camino de §8 en el navegador.
5. Si un punto pide una decisión del propietario (§7), **no la tomes**: pregunta.

---

## 1. P0 — Errores que hoy rompen el estudio (hacer primero, en este orden)

### P0.1 El cronómetro va 2 horas adelantado y un examen oficial nace sin tiempo — **HECHO (e510f97)**

> **Revisado por Claude el 5 de octubre**: el tipo `UtcDateTime` es correcto (escribe en UTC sin
> zona, como antes; lee con UTC) y las rutas de estudio y de dossier sirven las fechas con zona
> (`...Z`). Queda un cabo: `infrastructure/dossier_repository.py` y `domain/dossier.py` (`_momento`)
> y `classification_repository.py` (`_fecha`) leen fechas con SQL directo y `fromisoformat`, que no
> pasa por el tipo nuevo y devuelve fechas **sin zona**. Hoy no rompe nada (medido), pero pásalas
> por `infrastructure/db.py → as_utc()` para que no se mezclen con fechas con zona. **Pendiente**:
> el recorrido visual del cronómetro en el navegador (§8, pasos 2 y 5), que hará Claude en cuanto
> Chrome esté conectado.


- **Se ve**: al empezar una práctica, el reloj marca `2:00:03`; a los 20 s, `2:00:24`. Una sesión
  antigua mostraba `94:53:57 · queda 00:00`. En un **examen oficial** de 120 min el tiempo empieza
  en 2 h: nace agotado.
- **Causa**: la API devuelve las fechas **sin zona horaria** (`"2026-10-05T10:43:52.793645"`, que es
  UTC) y el navegador las interpreta como hora local (Madrid, UTC+2).
  `apps/web/src/features/study/labels.ts → elapsedSeconds()` hace `Date.parse(startedAt)`.
  El origen es el backend: las columnas `DateTime(timezone=True)` de SQLite pierden la zona al leer.
- **Qué hacer**: que **toda** fecha que sirve la API lleve zona (`...Z` o `+00:00`). Lo correcto es
  arreglarlo en el backend, en un solo sitio: un tipo de columna/serializador que devuelva
  `datetime` *aware* en UTC (p. ej. un `TypeDecorator` que añada `tzinfo=UTC` al leer, o un
  serializador Pydantic común en `api/`). No parchear solo el front.
- **Comprobar**:
  - prueba de contrato: todas las fechas de `GET /study-sessions/{id}` terminan en `Z`/`+00:00`;
  - prueba de componente: `elapsedSeconds` con `"…Z"` y hora local Madrid da segundos reales;
  - a mano: empezar una práctica → el reloj marca `0:00` y avanza; empezar un examen oficial TAI →
    quedan `120:00`.
- **Ojo**: revisa también cualquier comparación de fechas en el backend (límites de tiempo,
  repasos vencidos, «hoy» del Inicio) para que todas usen UTC *aware*.

### P0.2 La búsqueda dice mal en qué coincide (y lo de «or»)

- **Se ve**: buscar `derecho de supresión` → cada resultado dice «coincide en: derecho, **or**»; la
  palabra `supresión` **nunca** aparece como coincidencia aunque esté en el texto.
- **Causa** (dos fallos en el mismo sitio):
  1. `infrastructure/search_repository.py → search()` calcula los términos con
     `significant_terms(expression)` sobre la **expresión FTS** (`"derecho"* OR "supresion"*`), no
     sobre la consulta: de ahí sale «or».
  2. Compara el término **sin tildes** (`supresion`) con el texto **con tildes**
     (`" ".join(text.lower().split())`), así que una palabra con tilde nunca coincide.
- **Qué hacer**: pasar los términos de la **consulta original** (`significant_terms(request.query)`)
  y comparar contra `normalise(texto)` (la misma normalización que el índice, `domain/rag.py`).
  Revisa de paso que el cálculo de «respaldada / parcial / insuficiente» de *Preguntar* use la
  misma normalización (si no, una respuesta buena sale «parcial» por una tilde).
- **Comprobar**: prueba unitaria con `derecho de supresión` contra `Artículo 17. Derecho de
  supresión` → coincide en `derecho, supresion`; ningún término `or`/`and`.

### P0.3 El Programa no suma bien: un bloque tiene menos preguntas que uno de sus temas

- **Se ve**: Bloque I «preguntas: 452»; su tema 1 «preguntas: 2006».
- **Causa probable**: el recuento del bloque cuenta solo lo mapeado **directamente al bloque**, no
  lo de sus temas (y además hay que contar cada pregunta **una vez**: el mapeo es polimórfico, ver
  §4.4.1 del traspaso).
- **Qué hacer**: el número del bloque = preguntas **distintas** del bloque **y** de su subárbol. Lo
  mismo para «dominio» y «repaso» del bloque.
- **Comprobar**: prueba de integración con un bloque con 2 temas y preguntas repetidas entre ellos.

### P0.4 El panel de un tema se queda en «Leyendo el tema…» — **medido: 99 s, súbelo de prioridad**

> **Medido por Claude el 5 de octubre** con una copia de la base real y el código de `main`:
> `GET /curriculum-nodes/{II.1}/dossier` (un tema **pequeño**) tarda **99 s** la primera vez y
> **21 s** la segunda, y responde **1,16 MB** de JSON. Guardar una versión (`POST …/dossier/versions`)
> tarda 21 s. Con temas grandes (I.1, I.7) será peor. Es lo más lento de toda la aplicación y está
> en el camino de estudiar (Programa → tema). Va justo después de P0.5/P0.6.

- **Se ve**: en Programa, al pulsar I.7 (protección de datos), el apartado del tema sigue en
  «Leyendo el tema…» pasados 12 s (el dossier de un tema con ~20.000 fragmentos).
- **Qué hacer**: medir `GET /curriculum-nodes/{id}/dossier` (o la ruta que use) con la base real;
  objetivo **< 1 s**. Opciones: servir primero un resumen (número de fuentes, fragmentos, enlaces) y
  paginar los fragmentos; o cachear el dossier por `corpus_revision` (ya existe y ahora es barata).
  No bloquear el resto del panel mientras carga.
- **Comprobar**: medición antes/después en `docs/reviews/`; el panel enseña algo útil en < 1 s.

### P0.5 Sesiones de prueba que ensucian Estudiar e Inicio

- **Se ve**: 5 sesiones «sin empezar» (4 de examen oficial de 85 y una práctica de 176) creadas
  durante las pruebas; «Continuar estudiando» del Inicio apunta a una de ellas. La lista no dice
  **de qué examen** es cada sesión (cinco filas iguales «examen oficial · sin empezar · 0 de 85»).
  Además, el nombre accesible del botón dice «Abrir la sesión **empezada** el …» en sesiones sin
  empezar, y fechas en bruto.
- **Qué hacer**:
  1. Función **«Descartar sesión»** (solo sin respuestas, o archivar si tiene respuestas; nunca
     borrar historial con respuestas). Ruta + botón + auditoría.
  2. En la lista de sesiones: **nombre del conjunto/tema**, modo, progreso y fecha legible.
  3. Descartar las 5 de prueba del propietario (por la API, con copia previa). La práctica de 176
     que empezó Claude al probar (1 respuesta) también se puede descartar.
- **Comprobar**: prueba de la ruta; a mano, Inicio → «Continuar estudiando» apunta a algo real.

### P0.6 Si la API no está arrancada, ocho errores técnicos en inglés

- **Se ve**: cada tarjeta dice «Failed to fetch» y un «Reintentar».
- **Qué hacer**: un **aviso único arriba**: «La aplicación no responde. Arráncala con
  `scripts\api.ps1` (o `scripts\dev.ps1`) y pulsa Reintentar». Detectar `TypeError` de `fetch` en
  `apps/web/src/api/client.ts` y lanzarlo como un error propio («sin conexión con la API»).
- **Comprobar**: prueba de componente con `fetch` que falla; a mano, parar la API.

---

## 2. P1 — Estudiar rápido (lo que más velocidad de estudio da)

### P1.1 Empezar a estudiar en 2 clics: «Practicar este tema» y modos con nombre humano

- **Se ve**: para practicar hay que ir a Estudiar → «Preparar otra sesión» → elegir entre **~100
  conjuntos** con nombres de rutas de Windows (`TAI · internet\descargas\drive-download-2026…`),
  muchos de 1–2 preguntas y muchos **sin clave** (no se pueden corregir). La práctica **por tema**
  (que existe en la API: `curriculum_node_id`, S13) **no se ofrece en la pantalla**, y el panel de un
  tema en Programa **no tiene ningún botón** (ni practicar, ni ver preguntas, ni abrir apuntes).
- **Qué hacer**:
  1. **Programa → cada tema**: botones **«Practicar 20 preguntas»**, **«Ver sus preguntas»**,
     **«Leer sus apuntes»**. El primero crea la práctica por tema y lleva directo a la pregunta 1.
  2. **Estudiar → pantalla inicial con 4 tarjetas grandes**:
     *Repasar mis fallos (N vencidos)* · *Practicar un tema* (selector de los 33 temas con su nº de
     preguntas corregibles) · *Examen oficial* (solo los que tienen clave activa, por nombre:
     «TAI libre 2025 · modelo A») · *Simulacro mixto* (de todo el banco con clave, por partes de la
     convocatoria).
  3. El selector de «conjunto» actual pasa a **«Avanzado»**, filtrado: solo con clave activa y con
     ≥ 10 preguntas, con **nombre legible** (título del documento, no la ruta; la ruta como texto
     secundario).
- **Comprobar**: E2E nueva «desde Inicio a contestar una pregunta de I.7 en 2 clics»; medir tiempo.

### P1.2 La pantalla de pregunta: legible, una sola vez y con teclado

- **Se ve**:
  - el enunciado sale en **letra monoespaciada dentro de un recuadro** (parece código);
  - las opciones salen **dos veces**: una lista `A … B …` y debajo los radios `A) … B) …`;
  - para avanzar hay que pulsar **Responder** y luego **Siguiente**;
  - la cabecera de la sesión ocupa media pantalla: «Clave con la que se corrige» lista **21
    plantillas** en un párrafo; «Cómo se compuso esta sesión» con texto técnico y «..» doble.
- **Qué hacer**:
  1. Enunciado en la tipografía normal, grande y con buen interlineado.
  2. Opciones **una sola vez**, como **botones grandes clicables** (toda la fila), con su letra.
  3. **Teclado**: `A`–`D` (o `1`–`4`) eligen, `Enter` responde, `→`/`Enter` pasa a la siguiente,
     `B` deja en blanco, `←` anterior. Mostrar la ayuda de teclas discretamente.
  4. En práctica con «corrección al responder»: tras corregir, **un `Enter` avanza**.
  5. Barra de progreso fina (`12 / 20`) y reloj pequeño arriba; la lista de claves y la
     composición, plegadas en «Detalles de la sesión».
- **Comprobar**: prueba de componente de los atajos; E2E «responder 5 preguntas solo con teclado».

### P1.3 Que la corrección enseñe algo: explicación y la fuente de verdad

- **Se ve**: tras acertar/fallar, «Evidencia que la sostiene» muestra **la propia pregunta**
  («stem · sección 3» con el enunciado y las opciones): no es evidencia, es el sitio de donde salió.
  No hay explicación de **por qué** la C es la buena.
- **Qué hacer**:
  1. Separar y rotular: **«De dónde sale esta pregunta»** (la cita actual, plegada) y **«Lo que
     dice la norma / tus apuntes»**.
  2. Para lo segundo: si la pregunta tiene explicación guardada (CSV/JSON/Anki la traen), enseñarla
     primero. Si no, **buscar en el corpus** con el enunciado + la opción correcta (la búsqueda ya
     existe y ahora tarda 0,01–0,25 s) y enseñar el **mejor fragmento de una norma o apunte**
     (no de otro banco de preguntas), con enlace «Abrir en la Biblioteca». Marcarlo como
     «fragmento relacionado (búsqueda)», no como evidencia aceptada.
  3. Al fallar: mostrar tu respuesta tachada y la correcta resaltada, y **«Añadido a tus
     repasos»** (la cola de errores ya existe).
- **Comprobar**: E2E: fallar una pregunta de protección de datos → se ve un artículo de la LOPDGDD
  o del RGPD y el aviso de repaso.

### P1.4 Al terminar: nota útil y siguiente paso

- **Qué hacer**: pantalla de resultado con **nota con las reglas de la convocatoria** (TAI: −1/3 por
  error, en blanco no penaliza, mínimo 25/50 por parte; ya están en el perfil), aciertos/fallos/
  blancos, **fallos por tema** y tres botones: *Repasar estos fallos ahora* · *Practicar el tema más
  flojo* · *Volver al Inicio*.
- **Comprobar**: prueba de servicio de la nota con un caso TAI conocido (p. ej. 60 aciertos, 15
  fallos, 5 blancos en la primera parte → nota directa y si supera el 25/50).

### P1.5 El Inicio, para estudiar (no para administrar)

- **Se ve**: el Inicio mezcla estudio con administración: «557 pendientes», «12.286 propuestas»,
  «1.446 cambios», capacidades técnicas (FTS5, SQLite, SHA-256), almacenamiento, «ADR-017»…
- **Qué hacer**: arriba **una sola tarjeta de acción**: «Hoy: repasar N fallos» o «Seguir con I.7
  (12/20)» o «Empieza por un tema» → un botón. Debajo, **progreso por bloque** (preguntas
  contestadas, % de acierto, temas sin tocar). Todo lo técnico (estado del sistema, capacidades,
  almacenamiento) a **Ajustes**. Los pendientes de administración, en **una línea** con enlace
  («Hay tareas de mantenimiento: ver»), no como alarma.
- **Comprobar**: la pantalla de Inicio cabe en 1 pantalla de portátil (≤ 900 px de alto) con datos
  reales.

### P1.6 Repaso espaciado de verdad

- La cola de errores existe («2 repasos vencidos»). Asegurar que: (1) cada fallo entra en la cola,
  (2) el Inicio lo propone primero, (3) una sesión de repaso se lanza con **un clic** y (4) acertar
  en el repaso alarga el intervalo y fallar lo acorta (comprobar los intervalos en
  `domain/review.py`). Añadir a la E2E.

---

## 3. P1 — Datos que hoy impiden estudiar parte del temario (tu línea de trabajo)

1. **Guardia Civil 2026**: separar conocimientos e idioma, añadir las 6 reservas, enlazar la
   plantilla con la ruta `/source` y activar (el mismo tratamiento que TAI 2025).
2. **Claves a medias de 20 conjuntos (7.876 preguntas)** con numeración absoluta.
3. **79 conjuntos sin clave activa**: activar los que se puedan comprobar; archivar los de 1–2
   preguntas sin clave que solo ensucian el selector (o fusionarlos por origen).
4. **Tema I.1**: «1.824 se quedaron fuera por no tener plantilla activa» al practicar el tema 1:
   es la mayor bolsa de preguntas que no se pueden practicar.
5. **5.249 preguntas sin tema** y **3.071 documentos sin asignar** al programa.
6. **Nombres de conjuntos**: renombrar los que llevan la ruta de Windows como título
   (`TAI · internet\descargas\…`) a un título humano (documento + año/organismo).

---

## 4. P2 — Quitar el ruido que tapa lo importante

### P2.1 Revisión: 12.286 propuestas, cada una por duplicado

- **Se ve**: cada grupo sale **dos veces** (sujeto «material» = artefacto y «texto extraído» =
  representación) con la misma propuesta. 12.286 propuestas no las revisa nadie a mano. La tabla
  de propuestas mide 1.457 px en una pantalla de 1.280 (se sale) y la página 30.000 px (53.000 en
  móvil).
- **Qué hacer**:
  1. **En el motor de clasificación**: proponer **una vez por material** (por la representación o por
     el artefacto, no por los dos); al decidir una, la otra se resuelve igual. Migración de datos
     que fusione las duplicadas pendientes (con copia previa).
  2. **Revisión en bloque por confianza**: «Aceptar todas las de confianza alta en ejes no
     críticos» (tipo documental, tema) con resumen previo y deshacer. Autoridad y derechos siguen
     pidiendo confirmación (regla del producto).
  3. Tabla que quepa: columnas Evidencia/Alternativas plegables; paginación (50 por página).

### P2.2 Cambios: 1.446 «sin confirmar»

- Coinciden con las **1.446 versiones sustituidas** de las reingestas de material (apuntes,
  texto recuperado). No son cambios de normativa que haya que estudiar: son reorganización del
  propio material.
- **Qué hacer**: (1) que una sustitución hecha **por quien ingiere** (mismo origen, misma mano) se
  registre como confirmada; (2) acción en bloque «confirmar los cambios de mis propias
  reingestas»; (3) dejar en «Cambios» solo lo que de verdad afecta al estudio (una norma nueva que
  deja obsoletas preguntas o apuntes).

### P2.3 Bandeja: 557 avisos de importación

- Agruparlos por causa (formato no soportado, escaneado sin OCR, duplicado…) con «Descartar este
  grupo» y explicar en una línea qué significa cada causa. Que el contador del menú cuente
  **grupos sin decidir**, no avisos sueltos.

---

## 5. P2 — Pulido de diseño (rápido y visible)

1. **Programa**: las etiquetas de cada tema dejan al título una columna de ~130 px y el título se
   parte palabra a palabra (la página mide 10.925 px en escritorio y 16.878 en móvil). Poner las
   etiquetas **debajo** del título (flex-wrap) o en una columna fija estrecha; título a ancho
   completo. Mostrar una **barra de progreso** por tema (contestadas / corregibles, acierto).
2. **Fechas legibles** en toda la web: un único `formatDate()` (`5 oct 2026, 12:43`, y «hace
   3 días» en listas). Hoy salen en bruto en Inicio, Estudiar, Sesiones y Actividad.
3. **Jerga interna fuera de la interfaz**: «ADR-017», «07_UI-UX §3, §5», «(07_UI-UX §12)», claves
   como `blank_answer_penalty`, `private_use_only`, `curriculum`, «stem», la revisión del corpus
   `700753-2026-10-02…-accepted4481.superseded1446`. Todo con su etiqueta en español o fuera.
4. **Plurales**: «pregunta(s)», «pendiente(s)», «(1 puntos)» → usar la función de concordancia que
   ya existe en `apps/web/src/features/review/labels.ts` (y llevarla a un módulo común).
5. **Móvil**: Bandeja y Programa se desplazan en horizontal (405 y 401 px en 390); Revisión, ver P2.1.
6. **Reglas del examen** (panel del tema): dejar visible el resumen («120 min · 80+5 y 20+5 ·
   −1/3 por error · mínimo 25/50 por parte») y plegar el detalle con las citas.

---

## 6. Lo que ya está bien (no tocar sin motivo)

- La corrección por el servidor con la clave congelada, las reservas y la penalización.
- La búsqueda (0,01–0,25 s con 700.277 fragmentos) y sus citas abribles.
- La alineación de plantillas (en orden, «d MODIFICADA», enlace `/source` comprobado).
- Las puertas (18/18) y la regla de medir antes de afirmar.

---

## 7. Decisiones del propietario (preguntar, no decidir)

- **DEBT-014**: búsqueda por significado / modelo local (desbloquearía temas para las 5.249 sin tema
  y respuestas explicadas). Con P1.3 se puede vivir sin ello de momento.
- **DEBT-023**: que una tarjeta de Anki sea pregunta (su reverso como respuesta).
- **DEBT-028**: saber si un proceso selectivo está abierto.
- **DEBT-018**: la revisión humana sobre material real.
- Si aceptar en bloque las propuestas de confianza alta (P2.1.2) y confirmar en bloque los cambios
  de reingesta (P2.2).

---

## 8. Recorrido de aceptación (hacer a mano en el navegador al final de cada bloque)

Con los datos reales (o una copia) y la API y la web arrancadas:

1. Abrir `http://127.0.0.1:5173/` → el Inicio cabe en una pantalla y dice qué hacer hoy.
2. Programa → I.7 → «Practicar 20 preguntas» → en < 5 s estás en la pregunta 1. El reloj marca
   `0:00`.
3. Contestar 5 preguntas **solo con el teclado**. Fallar una a propósito → ves la correcta, una
   explicación o un artículo de la LOPDGDD/RGPD y «Añadido a tus repasos».
4. Terminar → nota con las reglas TAI, fallos por tema, «Repasar estos fallos ahora».
5. Estudiar → «Examen oficial» → «TAI libre 2025 · modelo A» → quedan `120:00`; 80+5 primera parte en
   orden del cuadernillo.
6. Buscar «derecho de supresión» → el primer resultado es un artículo (RGPD art. 17 o LOPDGDD art.
   15) y «coincide en: derecho, supresion».
7. Parar la API → un solo aviso claro con cómo arrancarla.
8. Repetir 1–4 en móvil (390 px) sin desplazamiento horizontal.

Deja el resultado de este recorrido (capturas y tiempos) en
`docs/reviews/RECORRIDO-DE-ESTUDIO-<fecha>.md`.

---

## 9. Orden recomendado

| # | Bloque | Por qué primero |
| --- | --- | --- |
| 1 | ~~P0.1 zona horaria~~ (hecho, e510f97) | rompía los exámenes oficiales |
| 2 | P0.5 + P0.6 | limpia lo que ve el propietario al abrir |
| 3 | P0.4 dossier (99 s) | bloquea abrir un tema |
| 4 | P1.1 + P1.2 | es donde se gana la velocidad de estudio |
| 5 | P1.3 + P1.4 | es donde se gana la calidad de estudio |
| 6 | P0.2, P0.3 | búsqueda y Programa fiables |
| 7 | §3 datos (GC, claves, I.1) | más preguntas corregibles |
| 8 | P1.5 + P1.6 | el Inicio que guía cada día |
| 9 | P2 (ruido) y §5 (pulido) | quitar lo que distrae |

Cuando termines un bloque, fusiona y pasa al siguiente; no acumules ramas.
