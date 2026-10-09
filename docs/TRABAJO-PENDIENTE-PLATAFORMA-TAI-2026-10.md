# Trabajo pendiente: plataforma TAI de preguntas y apuntes

**Para:** DeepSeek · **De:** Claude · **7 oct 2026** · **Base:** `main = e05afa5`

Este es **el documento de trabajo**: todo lo que queda, en orden, con qué ficheros tocar y cuándo está hecho. Los anteriores (`REDISENO-ALUMNO-TAI-Y-PANEL-ADMIN`, `RESPUESTAS-F0-Y-ARRANQUE-F1`, `CAMINO-A-APP-DESPLEGABLE`) siguen siendo la referencia del *porqué*; si algo choca, manda este.

**El objetivo** es una plataforma de estudio de TAI con dos pilares iguales de importantes:
1. **Preguntas**: tests por tema y bloque, simulacros con la estructura real, exámenes oficiales, repaso de fallos y progreso.
2. **Apuntes**: unos apuntes buenos y completos de los 33 temas, **redactados a partir del material que ya hay en la base** (cada tema tiene entre 6 y 70 documentos asignados: normativa, documentación técnica oficial, apuntes personales y otros) y revisados por el propietario antes de publicarse.

---

## Parte A. Reglas de trabajo (obligatorias)

1. **Una fase por sesión, en este orden.** No se empieza otra cosa hasta cerrar la fase en curso. Si una fase no cabe en una sesión, se parte **por pantallas o por endpoints**, pero cada sesión termina con algo que **el alumno ve** funcionando.
2. **No se pospone una fase porque obligue a cambiar pruebas.** Actualizar las pruebas afectadas es parte de la fase.
3. **Una rama por fase**, con la prueba que falla antes y pasa después; puertas en verde antes de fusionar. Si una puerta falla por tiempo, se repite **una vez**; si vuelve a fallar, se investiga como regresión propia.
4. **Cada entrega incluye:** capturas de `npm run screens` de las pantallas tocadas (escritorio y móvil), el `report.md` y la lista de criterios de aceptación de la fase marcados uno a uno. Yo reviso las capturas (DeepSeek no puede ver imágenes).
5. **Nada de texto explicativo en pantalla** para el alumno: si una pantalla necesita un párrafo para entenderse, está mal diseñada.
6. **Componentes**: siempre los de `src/ui/`. Si falta uno, se añade a `src/ui/` y a `/admin/ui`, no se hace a mano en la página.

---

## Parte B. Las fases

### Fase 0 — Cierre de lo abierto (media sesión)

| # | Tarea | Hecho cuando |
|---|---|---|
| 0.1 | Repetir la puerta 18. Si `library.spec.ts` y `questions.spec.ts` vuelven a fallar, encontrar la causa en `e05afa5` y arreglarla | dos pasadas seguidas sin esos dos fallos |
| 0.2 | El **botón deshabilitado** sigue viéndose azul claro en la captura de `/admin/ui` (el informe decía que no). Comprobar qué regla CSS gana (probablemente `.button-primary:disabled` del CSS antiguo con más especificidad que `.ui-button`) | en la captura se ve gris, hundido y con borde discontinuo |
| 0.3 | Revisión (puerta 18 roja por 30–35 s): medir con el Performance de Playwright qué tarda tras cargar; casi seguro es pintar miles de filas. **Paginar** (50 por página) la lista de propuestas | la prueba de accesibilidad de Revisión pasa con su límite actual |

### Fase 1 — Dos zonas (una sesión)

**Menos trabajo del que parece:** las pruebas E2E entran casi siempre con `page.goto('/bandeja')`, `'/preguntas'`, etc. (54 entradas). Si las rutas viejas **redirigen** a las nuevas, esas pruebas siguen funcionando sin tocarlas. Solo hay que cambiar las que hacen clic en el menú por su rótulo.

Tareas:
1. `src/app/navigation.ts` → dos listas: `STUDENT_NAV` (Inicio `/`, Temario `/temario`, Tests `/tests`, Simulacros `/simulacros`, Exámenes `/examenes`, Fallos `/fallos`, Progreso `/progreso`) y `ADMIN_NAV` (Resumen `/admin`, Temario `/admin/temario`, Apuntes `/admin/apuntes`, Preguntas `/admin/preguntas`, Importar `/admin/importar`, Biblioteca `/admin/biblioteca`, Revisión `/admin/revision`, Cambios `/admin/cambios`, Errores de importación `/admin/errores`, Buscar en fuentes `/admin/buscar`, Ajustes `/admin/ajustes`, Componentes `/admin/ui`).
2. `AppShell.tsx` → `StudentShell.tsx` y `AdminShell.tsx`.
   - **Alumno**: cabecera con el nombre de la app y la barra de 7 entradas; en móvil (< 720 px), barra inferior fija con 5 (Inicio, Temario, Tests, Fallos, Progreso) y el resto dentro de Tests. **Sin** buscador de corpus, **sin** estado del worker/IA, **sin** selector de oposición, **sin** contadores de bandeja/errores/cambios, **sin** el pie "Aplicación local de un solo usuario…". Enlace discreto "Administrar" en el pie.
   - **Admin**: todo lo que hay hoy en la cabecera y el menú lateral, más la franja fija "Modo administración · sin contraseña: solo en este ordenador" y un enlace "Ver como alumno".
3. `routes.tsx`: rutas nuevas; las pantallas actuales se montan bajo `/admin/...`. **Redirecciones** (`<Navigate replace>`): `/bandeja`→`/admin/importar`, `/biblioteca`→`/admin/biblioteca`, `/preguntas`→`/admin/preguntas`, `/revision`→`/admin/revision`, `/cambios`→`/admin/cambios`, `/errores`→`/admin/errores`, `/buscar`→`/admin/buscar` (conservando `?q=`), `/ajustes`→`/admin/ajustes`, `/programa`→`/temario`, `/estudiar`→`/tests`.
4. Mientras no existan F3–F5, las rutas de alumno nuevas pintan un `EmptyState` honesto ("Pronto: aquí podrás…") **dentro** del `StudentShell`, y `/tests` monta la pantalla de estudio actual para que se pueda seguir estudiando.
5. E2E: un helper `tests/e2e/rutas.ts` con las rutas nuevas; cambiar las pruebas que pulsan el menú; añadir `zones.spec.ts`: cada ruta vieja redirige, la barra del alumno tiene exactamente 7 entradas, y en `/` no aparece "Bandeja", "Biblioteca", "Worker" ni el selector de oposición.
6. `npm run screens`: añadir las rutas nuevas.

**Hecho cuando:** ninguna ruta vieja da 404; el detector de palabras no salta en `/` por el marco (sí puede saltar por el contenido de pantallas antiguas aún montadas); puertas verdes; capturas.

### Fase 2 — API del alumno (una sesión)

Módulo aislado `apps/api/opofuente/student/` (router, servicio, esquemas). **No importa** nada de `ingestion`, `extractors`, `classifiers`, `search`, `dossier` ni rutas de fichero; una prueba lo comprueba recorriendo los imports del módulo.

1. **Configuración**: `OPOFUENTE_STUDENT_OPPOSITION=tai-age` (por defecto) y `OPOFUENTE_PUBLIC_MODE=0`.
2. **Migración Alembic**:
   - `question_sets.distribution` (`personal` | `public`, por defecto `personal`; los `official_exam` del INAP → `public`).
   - `user_id` (texto, por defecto `'local'`) en `study_sessions`, `attempts`, `learning_errors`, `review_items`. Hoy siempre vale `'local'`; es la costura para las cuentas de la fase de despliegue.
   - `session_questions.flagged` (dudosa) si no existe.
3. **Orden numérico del temario**: bloque por número romano, tema por número (`IV.10` después de `IV.9`). Una función en el dominio con su prueba.
4. **Códigos legibles**: `I-1`, `IV-10` ↔ id del nodo.
5. Endpoints (todos `GET` salvo indicación), esquemas propios, **sin** `evidence`, `source_*`, títulos de conjunto, rutas ni UUID de documento:
   - `/api/v1/student/overview` — test a medias, fallos vencidos, % por bloque, últimos 5 tests.
   - `/api/v1/student/syllabus` — bloques → temas: código, título, epígrafes (§Fase 6.2), nº de preguntas, % acierto, ¿hay apuntes publicados?
   - `/api/v1/student/topics/{codigo}` — cabecera, progreso del tema.
   - `/api/v1/student/topics/{codigo}/notes` — los apuntes publicados (Fase 6). Hasta entonces, 404 con `{"status":"en_preparacion"}`.
   - `POST /api/v1/student/tests` — `{nodes: string[], count: 10|25|50|100, filter: "all"|"unseen"|"failed"|"flagged", feedback: "immediate"|"at_end", timed: bool}`. Internamente `practice` **multi‑tema** (hoy solo admite uno: ampliar el servicio de estudio). Un bloque = todos sus temas.
   - `GET /api/v1/student/sessions/{id}/question`, `POST …/answer`, `POST …/flag`, `POST …/navigate`, `POST …/finish`, `GET …/result` — envoltorios de los actuales con `StudentQuestionView` (enunciado, opciones A‑D, estado, y tras corregir: correcta, explicación publicada si la hay, enlace al tema).
   - `/api/v1/student/progress` — por bloque y tema, historial, evolución de simulacros.
6. Pruebas: (a) con datos de Celador y Guardia Civil sembrados, ninguna respuesta de `/student/*` los contiene; (b) ninguna respuesta contiene las claves prohibidas (`evidence`, `source_document_version_id`, `path`, `question_set_title`…) ni valores de `palabrasProhibidas` de tipo dato; (c) con `PUBLIC_MODE=1` solo salen preguntas de conjuntos `public`.
7. Contrato OpenAPI y tipos regenerados.

**Hecho cuando:** los endpoints responden con los datos reales en < 300 ms (medido en el informe) y las pruebas pasan.

### Fase 3 — Inicio, Temario, Tema y Progreso (una o dos sesiones)

Especificación de pantallas: `REDISENO…` §3.1, §3.2, §3.3 (sin la pestaña de apuntes aún: se rellena en la Fase 6) y §3.9. Todo con `src/ui/`. Contenido (enunciados, títulos de tema) dentro de `data-contenido`.

**Hecho cuando:** desde `/` se llega a un tema y se empieza su test en 2 clics; capturas a 390 y 1280; axe 0; detector de palabras 0 en estas rutas.

### Fase 4 — Hacer tests (una o dos sesiones)

`REDISENO…` §3.4 (configurador), §3.5 (pantalla de test: teclado A‑D/1‑4, Enter, ←/→, M; mapa de preguntas; "Esta pregunta está mal") y §3.10 (resultado con penalización, desglose por tema, "Repetir falladas"). La pantalla de estudio actual (`/estudiar`) se retira cuando esta funcione.

**Hecho cuando:** de Inicio a la primera pregunta de un test de 10 en ≤ 3 clics; un test completo solo con teclado (prueba E2E); responder < 200 ms.

### Fase 5 — Simulacros, exámenes oficiales y fallos (una sesión)

`REDISENO…` §3.6–§3.8, leyendo `exam_parts`/`exam_rules` de la convocatoria (80 + 20 de supuesto III o IV, 120 min, −1/3, 25/50 por parte, nota 0‑100 marcada "estimada"). Simulacro corto de 40 preguntas y 48 min.

**Hecho cuando:** se completa un simulacro con elección de supuesto y el resultado dice si se supera cada parte.

---

### Fase 6 — Apuntes (el segundo pilar; varias sesiones)

#### 6.1 Modelo y pantallas (una sesión)

- Tabla `topic_notes`: `id, curriculum_node_id, version_no, body_markdown, status (draft|published|archived), origin (manual|generated|mixed), generation_json` (modelo, plantilla, fecha, fuentes usadas, resultado de las comprobaciones), `note` (motivo), `created_at`, `published_at`. Editar crea versión; el alumno ve la última publicada.
- Endpoints admin: `GET/POST /api/v1/admin/topics/{codigo}/notes`, `GET …/notes/{version_id}`, `POST …/notes/{version_id}/publish`, `POST …/notes/{version_id}/restore`, `GET …/notes/diff?from=&to=`.
- **Admin `/admin/apuntes`**: tabla de los 33 temas con estado (sin apuntes · borrador · publicado), fecha, % de comprobaciones superadas. **`/admin/apuntes/:codigo`**: editor Markdown con vista previa a la izquierda; a la derecha, el **material del tema** (el dossier actual, con buscador y filtro por tipo de documento) para consultar y citar. Botones: Guardar borrador, Publicar, Historial (diff), Restaurar.
- **Alumno, pestaña Apuntes** del tema: lectura limpia con índice lateral (en móvil, desplegable arriba), ancho máximo 70 caracteres, tablas con scroll horizontal en móvil, marca "leído" por sección, botón "Test de este tema" al final. Sin nombres de fuente, sin versiones.
- Requisito previo: **la segunda mitad de P0.4** (el material de un tema grande debe cargar en < 3 s y paginado), porque es la columna derecha del editor.

#### 6.2 Cómo son unos buenos apuntes de TAI (la plantilla)

Cada tema sigue **la misma estructura**, para que el alumno sepa dónde está todo:

1. **Encabezado**: bloque, número y título oficial completo.
2. **Mapa del tema**: los epígrafes del título oficial como índice. El título oficial ya los trae separados por puntos: «La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. …» → un epígrafe por frase. **Cada epígrafe oficial es una sección**; ninguno se queda sin desarrollar.
3. **Desarrollo por epígrafe**: explicación clara en frases cortas, definiciones en negrita, listas cuando hay enumeraciones, **tablas comparativas** cuando hay conceptos parecidos (p. ej. TCP vs UDP, niveles RAID, tipos de recurso administrativo).
4. **Normativa clave** (temas de bloque I y los técnicos con norma: ENS, ENI, LOPDGDD, accesibilidad…): los artículos que caen, **citados literalmente** de la norma (los textos legales se pueden reproducir) con su número de artículo.
5. **Lo que más cae**: los 5–10 conceptos que más aparecen en las preguntas asignadas al tema (se calcula, ver 6.3), con una línea cada uno.
6. **Trampas típicas**: las confusiones que provocan las preguntas con más fallos del tema (plazos, órganos, cifras, siglas).
7. **Resumen en 10 puntos** para repasar el día antes.
8. **Autoevaluación**: botón al test del tema.

Longitud orientativa: 2.500–6.000 palabras por tema según su peso (número de preguntas asignadas). Español claro, segunda persona, sin relleno.

#### 6.3 Generación de borradores a partir del material (dos sesiones)

Hay material de sobra; lo que falta es convertirlo en apuntes. Se hace con un **generador en el taller** que produce **borradores** (`status = draft`, `origin = generated`) que el propietario revisa y publica. Nunca publica solo.

**Proveedor de IA:** la app ya admite `OPOFUENTE_LLM_PROVIDER=openai_compatible` con `OPOFUENTE_LLM_BASE_URL`, `OPOFUENTE_LLM_MODEL` y `OPOFUENTE_LLM_API_KEY` (`config.py`). La API de DeepSeek es compatible con OpenAI, así que basta configurarla. La clave la pone el propietario; si no la hay, el generador se puede lanzar igual en modo "preparar" (ver más abajo) y DeepSeek, como agente, redacta a partir de los ficheros que genera.

**Pasos del generador** (`opofuente notes generate --topic IV-7 [--section 3] [--prepare-only]`, y un botón "Generar borrador" en `/admin/apuntes/:codigo`):

1. **Recoger el material del tema**: los tramos del dossier del tema, ordenados por fiabilidad: `law_or_regulation` y `official_technical` primero; después `personal_notes`; después el resto. Quitar duplicados (los tramos casi iguales de documentos distintos).
2. **Repartir por epígrafe**: asignar cada tramo al epígrafe más parecido (búsqueda de términos del epígrafe en el tramo con el índice FTS que ya existe; si hay embeddings configurados, por similitud). Límite de material por epígrafe para no saturar al modelo (p. ej. 12.000 palabras, los mejores primero).
3. **Calcular "lo que más cae" y "trampas"**: de las preguntas asignadas al tema, los términos más frecuentes en enunciados y respuestas correctas, y las preguntas con más fallos en `attempts`/`learning_errors`.
4. **Redactar por epígrafe** (una llamada por epígrafe, no el tema entero de golpe), con una plantilla de instrucciones versionada en `apps/api/opofuente/notes/prompts/` que exige:
   - redactar **con palabras propias**, en español, siguiendo la estructura de 6.2;
   - citar literalmente **solo** de documentos de normativa, con su artículo;
   - no copiar más de 20 palabras seguidas de ningún otro documento;
   - no inventar: si el material no cubre algo del epígrafe, escribir `> [FALTA MATERIAL: …]` para que el propietario lo vea;
   - marcar cada párrafo con referencias ocultas `<!-- fuentes: span:<id>, span:<id> -->` (el alumno no las ve; el editor sí, para comprobar).
5. **Ensamblar** las secciones con el encabezado, "lo que más cae", "trampas" y el resumen (una última llamada que resume el texto ya generado).
6. **Comprobaciones automáticas** (se guardan en `generation_json` y se enseñan en el editor):
   - **Cobertura**: todos los epígrafes oficiales tienen sección y ninguna está vacía.
   - **Copia literal**: secuencias de 12 palabras compartidas con tramos que **no** son normativa → se resaltan los párrafos que las tengan. Umbral para aprobar: 0 párrafos marcados.
   - **Suficiencia**: de las preguntas oficiales y públicas del tema, cuántas se pueden responder con lo que dicen los apuntes (comprobación con el modelo: "¿con este texto se puede elegir la correcta?, responde la letra"). Se informa el %; objetivo ≥ 85 %. Las que no, se listan como "huecos" con su enunciado.
   - **Huecos de material**: lista de los `[FALTA MATERIAL]`.
   - **Longitud** dentro del rango del tema.
7. **Modo `--prepare-only`**: en vez de llamar al modelo, escribe en `artifacts/notes/<codigo>/` un fichero por epígrafe con el material, las instrucciones y las preguntas del tema. Sirve para que DeepSeek redacte como agente si no hay clave de API, y para depurar.

**Piloto antes de hacer los 33:** generar **tres temas** de naturaleza distinta —**I.1** (Constitución: normativo), **II.4** (Sistemas operativos: técnico) y **IV.7** (TCP/IP y OSI: técnico con tablas)—, pasar las comprobaciones, y **parar** para que el propietario y yo los leamos. Se ajusta la plantilla de instrucciones según lo que salga y **solo entonces** se lanza el resto.

**Hecho cuando** (por tema): borrador con 100 % de cobertura de epígrafes, 0 párrafos con copia literal no normativa, suficiencia ≥ 85 % o huecos listados, y publicado por el propietario.

#### 6.4 Revisión cómoda para el propietario (una sesión)

Revisar 33 temas tiene que ser rápido:
- En el editor, cada sección con su estado (pendiente · revisada) y botones **Regenerar esta sección** (con una indicación opcional: "más corto", "añade tabla de X") y **Marcar revisada**.
- Los avisos de las comprobaciones, clicables, llevan al párrafo.
- Pasando el ratón por un párrafo, el material del que sale aparece resaltado en la columna derecha.
- "Publicar" solo se activa con todas las secciones revisadas.

#### 6.5 Después de publicar

- **Apuntes → preguntas**: al fallar una pregunta, "Ver en apuntes" abre la sección del epígrafe al que pertenece (asignación pregunta→epígrafe por el mismo método de 6.2 paso 2; guardarla).
- **Preguntas → apuntes**: al final de cada sección, "Practicar este epígrafe" (test de 10 de las preguntas asignadas a esa sección).
- Cuando cambie el material de un tema (nueva versión de una ley), el tema aparece en `/admin/apuntes` como "material cambiado desde la publicación".

---

### Fase 7 — Panel de preguntas (una o dos sesiones)

`REDISENO…` §4.3 y §4.4: tabla con filtros (sin tema, sin correcta, reportadas, en conflicto), ficha editable (enunciado, opciones, **correcta**, explicación, tema, activa), crear pregunta en un conjunto `admin_bank` (`distribution = public`), acciones en lote, reportes del alumno. Endpoints de §4.4 en `/api/v1/admin/...`, todo en una transacción y con `audit_events`.

**Hecho cuando:** cambiar la correcta en admin se refleja en el siguiente test del alumno y en los resultados afectados (ofreciendo recalcular).

### Fase 8 — Explicaciones de las preguntas (una o dos sesiones)

Mismo generador que los apuntes, por pregunta: explicación de 2–5 frases de por qué la correcta lo es y por qué no las otras, **basada en los apuntes publicados del tema** (y en la norma si es de bloque I), con la misma comprobación de copia literal. Revisión en lote en `/admin/preguntas?sin_explicacion=1`: lista con la explicación propuesta, teclas **A** (aprobar), **E** (editar), **R** (regenerar), **S** (saltar). Primero las **440 oficiales**; luego por tema.

Las 11.315 explicaciones que hay hoy vienen de material privado: se quedan como `origin = private` y **solo** se muestran con `PUBLIC_MODE=0`.

**Hecho cuando:** el 100 % de las preguntas oficiales tiene explicación aprobada.

### Fase 9 — Panel de temario (media sesión)

`REDISENO…` §4.1: crear, renombrar, reordenar y archivar temas y bloques; un tema nuevo aparece en el temario del alumno y admite preguntas y apuntes.

### Fase 10 — Más preguntas legales: exámenes INAP anteriores (sesión de contenido)

El INAP publica cuestionarios y plantillas de convocatorias anteriores de TAI. El propietario los descarga (DeepSeek no tiene red para eso) a una carpeta; el taller ya importa examen + plantilla. Tareas: importar todos, clasificar sus preguntas por tema con la clasificación existente, revisar los conflictos en el panel, `distribution = public`. Objetivo: ≥ 40 preguntas públicas por tema.

### Fase 11 — Palabras prohibidas bloqueantes

El detector entra en las puertas para todas las rutas de alumno. Puertas 18/18.

### Fase 12 en adelante — Despliegue

Según `CAMINO-A-APP-DESPLEGABLE-2026-10.md` §7 (paquete de contenido, Postgres + cuentas, CI, legal, beta cerrada). Empieza **después** de que el propietario haya estudiado con la Fase 1–9 en local y esté contento.

---

## Parte C. Cuándo es "plataforma de preguntas y apuntes" v1

- [ ] Zona alumno sin rastro de la herramienta interna (detector a 0).
- [ ] Tests por tema, bloque y mixtos; simulacro real; exámenes oficiales; repaso de fallos; progreso.
- [ ] **33/33 temas con apuntes publicados**, todos con cobertura completa de epígrafes.
- [ ] Explicación en el 100 % de las preguntas oficiales.
- [ ] Panel admin para corregir preguntas, correctas, apuntes y temas sin tocar la base.
- [ ] Todo usable en el móvil y con teclado.

## Parte D. Lo que decide el propietario

1. **Clave de API para el generador** (DeepSeek API u otra compatible con OpenAI). Sin ella, los apuntes se redactan en modo `--prepare-only` con DeepSeek como agente, más lento.
2. Leer y dar el visto bueno a los **tres temas piloto** antes de generar el resto.
3. Revisar y publicar cada tema (la Fase 6.4 está pensada para que sean minutos, no horas).
4. Descargar los exámenes INAP anteriores para la Fase 10.

## Parte E. Orden y tamaño

| Sesión aprox. | Fase |
|---|---|
| 1 | 0 + 1 |
| 2 | 2 |
| 3–4 | 3 |
| 5–6 | 4 |
| 7 | 5 |
| 8 | 6.1 (+ segunda mitad de P0.4) |
| 9–10 | 6.3 + piloto de 3 temas → **parar para revisión** |
| 11 | 6.4 |
| 12–14 | resto de temas (generar, comprobar) mientras el propietario revisa |
| 15–16 | 7 |
| 17–18 | 8 |
| 19 | 9 + 11 |
| — | 10 cuando el propietario tenga los PDFs |
