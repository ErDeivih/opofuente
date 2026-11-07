# Backlog — OpoFuente, temario común de informática C1

Regla del [protocolo](../../EspacioCodigo/_flujo-dsh/PROTOCOLO-AUTONOMIA.md): **nunca menos de 5
tareas listas**. Cada sesión: comprobar estado → elegir la de más valor → ejecutar → pasar puertas →
commit y push → actualizar este fichero. Una tarea bloqueada no para la sesión: se marca y se sigue
con la siguiente.

Estado de partida (2026-11-04, sesión 2): la propuesta de modelo está escrita en
[`ESPECIFICACION.md`](ESPECIFICACION.md) §5–§6, con su ADR-018 en propuesta. **Nada implementado**, a
propósito: el encargo pedía escribirla antes de codificar.

Estado (sesión 3, 2026-11-04): David aprobó §5, §6 y O1–O4 tal cual; **B-001 y B-002 están hechas**
(modelos, migración `0021` con `downgrade`, temario común v1 con su generador y siembra idempotente).
La siguiente es B-003.

## Lista

| ID | Tarea | Nivel | Estado | Depende de |
|---|---|---|---|---|
| [B-001](#b-001) | Modelos + migración `0021_temario_comun_y_referencias` | 2 | **hecha** (2026-11-04) | — |
| [B-002](#b-002) | Fixture del temario común v1, generador y siembra idempotente | 2 | **hecha** (2026-11-04) | B-001 |
| [B-003](#b-003) | Equivalencias TAI publicado → común y re-atribución del banco | 2 | **hecha** (2026-11-05) | B-002 |
| [B-004](#b-004) | API y contrato del temario común y de las particularidades | 2 | **hecha** (2026-11-05) | B-002 |
| [B-005](#b-005) | Interfaz: índice del temario, ficha de tema y avance | 2 | **hecha** (2026-11-05) | B-004 |
| [B-006](#b-006) | Importar las convocatorias C1 de `c1.txt` y del inventario como referencias | 2 | **hecha** (2026-11-05) | B-004 |
| [B-007](#b-007) | Entrega del slice `docs/slices/S13.md` | 1 | **hecha** (2026-11-07) | B-005 |
| [B-008](#b-008) | Poner al día `docs/product-spec/03_DATA-MODEL.md` y el índice de ADR | 1 | **hecha** (2026-11-07) | B-001 |
| [B-009](#b-009) | Investigación encomendada: cómo organizan el temario las academias C1 | 1 | lista | — |
| [B-010](#b-010) | Decidir la bajada de `0021` después de sembrar el temario común | 2 | lista | B-002 |
| [B-011](#b-011) | Estabilizar las pruebas de API que compiten con el worker de fondo | 1 | lista | — |
| [B-012](#b-012) | Acotar por versión la resolución de nodo por `path` en clasificación | 2 | lista | B-004 |
| [B-013](#b-013) | Contenido de la ficha de tema: preguntas del banco y material del tema | 2 | **hecha** (2026-11-06) | B-005 |
| [B-014](#b-014) | Apuntes del temario común: separar título y descripción en la v1 | 2 | **hecha** (2026-11-06) | B-002 |
| [B-015](#b-015) | Revisión visual del temario en móvil y PC y textos §8 | 2 | **hecha** (2026-11-06) | B-005 |
| [B-016](#b-016) | Enlazar la ficha del tema con biblioteca, banco y bases oficiales | 2 | **hecha** (2026-11-07) | B-013 |

## Detalle

### B-001

**HECHA (2026-11-04).** Modelos y migración `0021_temario_comun_y_referencias`. Cinco tablas nuevas (`curricula`,
`curriculum_versions`, `convocation_curriculum_refs`, `convocation_curriculum_adjustments`,
`curriculum_equivalences`), `curriculum_nodes` cambia de dueño (`convocation_version_id` →
`curriculum_version_id`, unicidad `(curriculum_version_id, path)`) y backfill no destructivo, según
`ESPECIFICACION.md` §5–§6.

- **Entregado:** `db_models.py` (cinco modelos y el nodo nuevo), migración `0021` con `downgrade`
  y `PRAGMA foreign_key_check` dentro de la propia migración, `test_migrations_0021.py` (15 pruebas,
  incluida la subida desde `0004` y la supervivencia de un mapeo con material), adaptación de
  `profile_repository`, `classification_repository`, `document_coverage`, `search_repository`,
  `readiness_repository`, `question_repository` y de las pruebas que insertaban nodos con el dueño
  viejo; helper `curriculum_lookup` con la resolución convocatoria → ref `official` → versión → nodos,
  y `opofuente_testing/programs.py` para las pruebas que siembran programas con SQL crudo.
- **Evidencia ejecutada:** suite completa en verde; `alembic upgrade head` desde vacío y sobre
  **copia** de la base viva (`0004` → `0021`): 235 nodos antes y después, 0 sin versión,
  2 referencias `official`, `PRAGMA foreign_key_check` vacío; `downgrade 0020` devuelve 198 + 37
  nodos a sus convocatorias y borra las cinco tablas; volver a subir funciona. Siembra idempotente
  sobre base vacía y sobre copia migrada (`--check` en verde, sin duplicar programas). Contrato
  OpenAPI sin cambios. Decisiones D-006 a D-010 en `DECISIONES.md`; ADR-018 ratificada.
- **Puertas:** 1–16 en verde sobre el árbol final (`./scripts/gates.ps1 -SkipE2e`: formato, lint,
  mypy, eslint, typecheck, unitarias, integración, contrato, Vitest, OpenAPI, builds, migración desde
  vacío, verificación sqlite3 y siembra idempotente). La **17** (`build_profile_fixtures --check`) no
  es ejecutable en este worktree: `data/sources` no tiene las fuentes oficiales y las descargadas hoy
  con `fetch-sources.ps1` ya no coinciden con el manifiesto de octubre (5 documentos). Es un requisito
  previo del entorno, no del cambio: no se tocan fixtures ni manifiesto. La **18** (E2E) no se ejecuta
  y no se declara ejecutada. Queda anotado como deuda de entorno en `docs/DEBT.md` (DEBT-028).
- **Criterio de cierre:** cumplido en esquema, datos, contrato y suite; puerta 17 pendiente de
  fuentes oficiales.

### B-002

**HECHA (2026-11-04).** Fixture del temario común v1 desde `temario-c1.md` (5 bloques, 40 temas),
generador con verificación de sha256 y siembra idempotente en la puerta que ya existe.

- **Entregado:** `fixtures/curricula/informatica-c1.v1.json` (45 nodos, rutas `I.1`…`V.40`,
  `official_code` 1–40, cita por bloque y `referenced_by` con la `primary` del TAI);
  `fixtures/curricula/manifest.json` con la huella de la fuente;
  `apps/api/opofuente/tools/build_curriculum_fixtures.py` (genera, `--check` y verifica sha256);
  dominio `opofuente/domain/curricula.py`, cargador `infrastructure/curriculum_fixture_loader.py`,
  repositorio `infrastructure/curriculum_repository.py` y servicio
  `application/curriculum_service.py`; `tools/seed_profiles.py` siembra ahora perfil + temario y
  `--check` cubre los dos; la puerta 17 ejecuta también `build_curriculum_fixtures --check`.
- **Pruebas:** `test_temario_comun.py` (7 pruebas: forma del fixture, idempotencia explícita,
  recuentos y rutas en la base, `primary` del TAI con su cita, un temario incompleto no se publica, una
  versión activa no se edita, un solo común) y `tests/unit/test_build_curriculum_fixtures.py`
  (5 pruebas herméticas del parser y la verificación por hash).
- **Evidencia ejecutada:** suite completa **988 pruebas en verde** (las 976 previas + 12 nuevas);
  sobre una base recién migrada, primera siembra publica el temario (5/40/45, ref `primary` con
  «ANEXO V, apartado 3», `PRAGMA foreign_key_check` vacío) y la segunda pasada con `--check` termina
  con **0 creadas, 0 actualizadas, 0 fallos**; `build_curriculum_fixtures --check` verde contra la
  fuente real (sha256 `50d8fa7f…dcea`). Puertas 1–16 en verde; en la 17 el fixture del temario queda
  sincronizado y es la verificación de los **perfiles** la que sigue bloqueada por las fuentes
  oficiales descargadas (DEBT-028, previo). E2E no ejecutada.
- **Decisiones:** D-011 (fuente por manifiesto y huella), D-012 (publicar solo con el recuento y no
  editar una versión activa), D-013 (referencias se confirman, no se re-apuntan).
- **Criterio de cierre:** cumplido.

### B-003

**HECHA (2026-11-05).** Equivalencias nodo publicado → nodo común y re-atribución. Propuesta de las
33→40 equivalencias, revisión humana de las dudosas y re-apuntado de `curriculum_mappings` y
`learning_errors` al nodo común, con informe por fila.

- **Entregado:** `fixtures/curricula/tai-age-2025.equivalences.json` (33 filas: 20 `accepted` y 13
  `proposed`, con relación, confianza y motivo); dominio `opofuente/domain/equivalences.py`; cargador
  y repositorio (`infrastructure/equivalence_fixture_loader.py`, `remap_repository.py`); modelos del
  informe (`application/remap_models.py`); herramienta `tools/remap_curriculum.py` con `--check`,
  `--apply` (copia previa de la base + `informe.json`) y `--inverse <informe>`.
- **Pruebas:** `test_equivalencias.py` (5 pruebas: plan sin escribir, solo se mueve lo aceptado, lo
  dudoso se queda, conflicto de unicidad informado, idempotencia, inverso completo) y
  `tests/unit/test_remap_curriculum.py` (4: cobertura de los 33 temas, 20/13 por estado, copia previa
  y fallo sin base).
- **Evidencia ejecutada:** `--check` calcula el plan sin escribir; `--apply` crea 33 equivalencias
  (20 con `decided_at`), mueve 2 mapeos y 1 fallo, informa 1 conflicto y deja 1 mapeo dudoso en su
  sitio; segunda pasada = 0 cambios; `--inverse` con el informe de la ejecución devuelve el material
  y retira las 33 equivalencias; `PRAGMA foreign_key_check` vacío. Informe por fila con ids y
  antes/después en `data/backups/remap-curriculum-<marca>/informe.json`.
- **Decisiones:** D-014 (solo se aplican las aceptadas), D-015 (copia previa, informe por fila e
  inverso), D-016 (se re-apuntan mapeos y fallos; las propuestas no se reescriben).
- **Queda para B-012:** la clasificación de material nuevo resuelve el nodo por `path` sin acotar la
  versión; no afecta a esta re-atribución (va por `id`) pero sí a lo que se clasifique después.
- **Criterio de cierre:** cumplido.

### B-004

**HECHA (2026-11-05).** API y contrato del temario común: rutas `/curricula`,
`/curricula/{code}`, `/curricula/{code}/versions`, `/curricula/{code}/progress`,
`/convocations/{id}/temario`, `/convocations/{id}/references`, ficha de nodo con `appears_in` y
particularidades, y marca de estudiado (`POST/DELETE /curriculum-nodes/{id}/studied`).
`/convocations/{id}/curriculum` sigue devolviendo el programa **publicado**.

- **Entregado:** migración `0022_study_marks`; modelos de lectura
  (`application/curriculum_models.py`), repositorio (`infrastructure/curriculum_read_repository.py`),
  servicio (`application/curriculum_read_service.py`), router (`api/routes/temario.py`), DTO
  (`api/temario_schemas.py`), cableado en `main.py`/`deps.py`; contrato OpenAPI y tipos TS
  regenerados.
- **Pruebas:** `test_temario_api.py` (7: índice, particularidades, referencias, ficha con
  `appears_in`, nodo publicado, marca y avance, 404), `test_migrations_0022.py` (3) y contrato
  (23 en verde, con las rutas nuevas incluidas).
- **Evidencia ejecutada:** `ruff`, `mypy` y las pruebas anteriores en verde; contrato sincronizado;
  el temario efectivo aplica `omitted` (y su subárbol), `renamed` y `renumbered`; una convocatoria
  sin `primary` responde 404. Decisiones D-017, D-018 y D-019.
- **Criterio de cierre:** cumplido.

### B-005

**HECHA (2026-11-05).** Interfaz del alumno: índice del temario común (5 bloques, búsqueda que
perdona tildes, marca de estudiado), ficha de tema con apuntes y «en qué convocatorias aparece», y
avance por bloque y total. Sin nombres de fuentes, rutas de Windows ni versiones en la zona del
alumno.

- **Entregado:** `pages/TemarioPage.tsx` y `pages/TemarioNodePage.tsx`; `features/temario/`
  (`search.ts`, `labels.ts`, `TemarioTree.tsx`, `ProgressPanel.tsx`); `api/temario.ts` y los hooks de
  `api/queries.ts`; sección «Temario» en `app/navigation.ts` y rutas en `app/routes.tsx`; estilos en
  `styles/global.css`; `ProgramPage` adaptado al contrato nuevo (procedencia bajo `convocation`) y
  limpio de textos de desarrollador (§8).
- **Pruebas:** `tests/unit/temario.test.tsx` (10: árbol 5/40, búsqueda sin tildes, sin resultados,
  avance total/por bloque/qué queda, estados vacío y error, ficha con convocatorias, navegación
  anterior/siguiente, particularidades con `?convocatoria=`, marcar/retirar, apuntes vacíos) y ajuste
  de `program.test.tsx`/`shell.test.tsx`. Vitest: **17 ficheros, 207 pruebas**.
- **Evidencia ejecutada:** `npm run typecheck:web`, `npm run lint:web`, `npm run test:web` y
  `npm run build:web` en verde; `export_openapi --check` y `contracts:check` verdes; suite backend
  completa **1008 pruebas** en verde. Puertas 1–16 en verde (`./scripts/gates.ps1 -SkipE2e`: 508
  unitarias + 477 integración + 23 contrato, 207 de componentes, contrato, builds, migración desde
  vacío a `0022` y siembra idempotente). La 17 deja el temario común sincronizado y solo falla por
  las fuentes oficiales de los perfiles (DEBT-028, previo); la 18 (E2E) no se ejecuta.
- **DOCTRINA-CALIDAD §8 aplicada:** fuera los textos de desarrollador y las explicaciones de cómo se
  calcula (dominio, avance, cobertura); solo lo que el alumno necesita para decidir o actuar.
- **Decisiones:** D-020.
- **Criterio de cierre:** cumplido (estados vacío/cargando/error; teclado y foco visibles; 400 px sin
  scroll horizontal por el diseño existente; E2E no ejecutada).

### B-006

**HECHA (2026-11-05).** Importar convocatorias de informática C1 de `c1.txt` (10) y del inventario
`convocatorias.csv` (las filas de grupo C1 con enlace oficial) como convocatorias que **referencian**
el temario común, sin copiarlo.

- **Entregado:** `domain/convocatorias_c1.py`, `infrastructure/convocatorias_fixture_loader.py`,
  `infrastructure/convocatorias_repository.py`, `application/convocatorias_service.py`, fixture
  `fixtures/curricula/convocatorias-c1.json` generado por
  `tools/build_c1_convocatorias_fixtures.py`, dos fuentes nuevas en el manifiesto (con sha256 y fecha
  de observación), siembra en `tools/seed_profiles.py` y puerta 17. `AppearanceSchema` añade
  `convocation_status` y la ficha marca «Por confirmar» (contrato y tipos regenerados).
- **Datos:** 12 convocatorias C1 (10 del agregador en `draft`, 2 del inventario en `archived`) bajo
  la oposición inactiva `informatica-c1`, cada una con su ref `primary` a `informatica-c1-v1` y su
  cita; 21 filas del inventario descartadas con motivo escrito (A1/A2/bolsas/portales y el TAI 2025,
  que ya estaba sembrado). No se inventan fechas: si la fuente no la publica se usa la de
  observación y se dice.
- **Pruebas:** unitarias del generador (criterio de importación, descartes, fixture real) e
  integración de la siembra (12 + 2 estados, refs a la versión activa, TAI sin duplicar,
  idempotencia, ficha con estados). Contrato regenerado.
- **Evidencia ejecutada:** puertas 1–16 en verde (511 unitarias + 480 integración + 23 contrato =
  **1014 backend**, 207 Vitest, contrato, builds, migración desde vacío a `0022` y doble siembra
  idempotente con las 12 convocatorias). En la 17 pasan el temario común y las convocatorias C1; solo
  falla la verificación de fuentes oficiales de los perfiles (DEBT-028, previo). E2E no ejecutada.
- **Decisiones:** D-021 y D-022.
- **Criterio de cierre:** cumplido; `build_c1_convocatorias_fixtures --check` sincronizado.

### B-007

**HECHA (2026-11-07).** Entrega del slice S13 en `docs/slices/S13.md`, con las diez secciones que
exige `AGENTS.md` y sin declarar pruebas que no se hayan ejecutado.

- **Contenido:** qué se construyó (B-001…B-016), flujo de la información, ficheros y migraciones
  (`0021`/`0022`), patrones y decisiones (D-001…D-026, ADR-018), seguridad y privacidad, puertas
  ejecutadas con sus cifras reales, prueba manual (Playwright a 400/1280 px), limitaciones conocidas,
  qué se rompe si se cambia cada pieza y qué criticaría un revisor senior.
- **Honestidad:** E2E no ejecutada, DEBT-028 abierta (puerta 17 de perfiles), B-012 pendiente,
  actualización de versión no construida y ficha vacía sin mapeos reales.
- **Criterio de cierre:** cumplido.

### B-008

**HECHA (2026-11-07).** Documentación al día con el modelo del temario común.

- **Entregado:** `docs/product-spec/03_DATA-MODEL.md` §2 reescrito (curricula, versiones, nodos por
  versión, refs con papeles, ajustes, equivalencias, marcas de estudio y su relación con
  `curriculum_mappings`); `13_DECISIONS-AND-OPEN-QUESTIONS.md` registra las decisiones D015–D017
  (O1/O2: temario único referenciado; O3: re-atribución con equivalencias aceptadas; O4:
  convocatorias C1 como tarea propia con confianza explícita); `docs/decisions/README.md` marca
  ADR-018 como ratificada e implementada, y el encabezado de ADR-018 refleja el alcance real de S13.
- **Criterio de cierre:** cumplido.

### B-009

**Investigación encomendada** (AGENTE.md): cómo organizan el temario las academias de informática C1
y los portales de oposiciones, y qué se repite en todas las convocatorias. Termina en
`INVESTIGACION.md` con lo mirado (enlace o captura), lo que hace la competencia, lo que nos falta y
**una propuesta concreta** de tarea Nivel 1 o 2. Si la propuesta cambia el alcance, es Nivel 3: se
pregunta.

### B-010

**Decidir qué hace el `downgrade` de `0021` cuando ya hay temario común sembrado.** Hoy la bajada
falla a propósito si algún nodo no tiene programa publicado al que volver (`ESPECIFICACION.md` §6.5,
paso 3). Eso cubre dos casos: los 40 temas del común en cuanto B-002 los siembre, y los nodos de un
programa publicado cuya convocatoria se haya borrado (la referencia `official` cascadea y el programa
queda huérfano; ver D-009).

- **Opciones:** (a) descartar los nodos comunes (y bloquear si tienen material asignado); (b) dejar
  de ofrecer la bajada una vez publicado el común; (c) separar la bajada del contenido con una
  migración previa que archive el temario común.
- **Criterio de cierre:** la opción elegida documentada en §6.5 y en la prueba
  `test_migrations_0021`, con la bajada ejecutada en el caso que toque. Es Nivel 2 si no borra datos
  con material; si la opción elegida los descarta, es Nivel 3 y se pregunta.
- **Depende de:** B-002.

### B-011

**Estabilizar las pruebas de API que compiten con el worker de fondo.** Las pruebas con
`seeded_client` construyen la aplicación con la configuración de producción (`worker_enabled=True`)
y además ejecutan trabajos a mano con `run_one_job`; con la máquina cargada, el worker puede
adelantarse y dejar un trabajo a medias (visto en `test_library_api`: una versión se promocionó antes
de su extracción y el diff salió vacío). Se ha añadido una espera determinista en `_pegar`; queda
revisar el resto de pruebas que usan el patrón y, si procede, usar `api_only_client` o desactivar el
worker en los fixtures que controlan la cola.

- **Criterio de cierre:** ejecutar la suite de integración varias veces con carga externa y sin ella
  sin fallos intermitentes; ninguna prueba depende del orden en que dos consumidores reclaman la cola.

### B-012

**Acotar por versión la resolución de nodo por `path` en clasificación.** `classification_repository`
resuelve un nodo candidato con `WHERE path = :valor LIMIT 1` (aceptar una propuesta de eje `topic`) y
etiqueta valores por `path` (`_value_labels`). Hoy ya es ambiguo entre el TAI, Guardia Civil y
Celador; con el temario común sembrado, un `I.1` puede resolver al nodo publicado o al común sin
criterio. Afecta al material que se clasifique **después** de B-003; la re-atribución hecha en B-003 va
por `id` y no le afecta.

- **Ficheros:** `apps/api/opofuente/infrastructure/classification_repository.py` (resolución de nodo y
  etiquetas).
- **Criterio de cierre:** la resolución y el etiquetado reciben el ámbito de versión (convocatoria o
  común) y no eligen entre versiones distintas; prueba con el mismo `path` en dos versiones.
- **Depende de:** B-004 (es quien decide qué árbol enseña la API).

### B-013

**HECHA (2026-11-06).** La ficha de tema enseña su **contenido**, no solo sus datos: las preguntas
del banco catalogadas en el tema y el material de la biblioteca que apunta a él.

- **Entregado:** rutas de lectura `GET /curriculum-nodes/{id}/questions` (preguntas sin clave, solo
  mapeos aceptados y versiones no sustituidas) y `GET /curriculum-nodes/{id}/materials` (documento,
  sección o cita aceptados, con su cita y su cobertura). Vistas y DTO en `curriculum_models.py` /
  `temario_schemas.py`, lectura en `curriculum_read_repository.py`, servicio y router; en la web,
  hooks `useTemarioNodeQuestions` / `useTemarioNodeMaterials` y las tarjetas «Material del tema» y
  «Preguntas» de la ficha. Contrato y tipos regenerados.
- **Pruebas:** `test_temario_contenido_api.py` (3: solo aceptadas y sin clave; material con sección y
  cita; 404) y 3 pruebas Vitest de la ficha (preguntas con tipo y reserva, material con cita, estado
  vacío). Vitest **17 ficheros / 210 pruebas**.
- **Evidencia ejecutada:** puertas 1–16 en verde (511 unitarias + 483 integración + 23 contrato =
  **1017 backend**, 210 Vitest, contrato, builds, migración desde vacío a `0022`, doble siembra). En
  la 17 pasan el temario común y las convocatorias C1; solo falla la verificación de fuentes
  oficiales de los perfiles (DEBT-028, previo). E2E no ejecutada.
- **Decisión:** D-023.
- **Criterio de cierre:** cumplido; la ficha sigue sin enseñar la clave.

### B-014

**HECHA (2026-11-06).** La ficha de cada tema ya tiene **apuntes**: el generador separa el título del
tema de su descripción.

- **Entregado:** `build_curriculum_fixtures.py` separa por el primer «: » y guarda el resto en
  `description`; fixture `informatica-c1.v1.json` regenerado (5 bloques / 40 temas / 45 nodos, mismas
  rutas y códigos); la ficha enseña título corto y apuntes reales, y la búsqueda del temario mejora
  al no arrastrar la descripción en el título.
- **Pruebas:** `test_cada_tema_tiene_titulo_y_apuntes_separados` (40 temas con descripción; I.1 con
  su título y sus apuntes) y la ficha de API comprueba que llega `description`; el resto de pruebas
  del temario y de equivalencias siguen verdes.
- **Evidencia ejecutada:** puertas 1–16 en verde (511 unitarias + 484 integración + 23 contrato =
  **1018 backend**, 210 Vitest, contrato, builds, migración desde vacío a `0022`, doble siembra con
  los apuntes nuevos). En la 17 pasan el temario común y las convocatorias C1; solo falla la
  verificación de fuentes oficiales de los perfiles (DEBT-028, previo). E2E no ejecutada.
- **Decisión:** D-024 (corrección de representación antes de que la v1 esté en una base duradera;
  I9 sigue impidiendo reescribir una versión ya activa).
- **Criterio de cierre:** cumplido; `build_curriculum_fixtures --check` sincronizado.

### B-015

**HECHA (2026-11-06).** Revisión visual real del temario y la ficha a 400 px y 1280 px, y limpieza de
textos según `DOCTRINA-CALIDAD.md` §8.

- **Revisado:** seis vistas con Playwright sobre una base temporal sembrada (temario, convocatorias C1,
  preguntas, material y marcas): `/temario` y ficha del tema en escritorio y móvil, y ficha con
  `?convocatoria=`. Sin desbordes horizontales (`scrollWidth == innerWidth` en 400 y 1280) ni
  solapamientos; sin errores de consola (solo el aviso de CSP del propio Vite).
- **Cambios:** fuera el pie con la descripción del producto y el estado interno del worker/IA de la
  cabecera (§8); fuera las etiquetas «BLOQUE/TEMA» del árbol; la ficha agrupa las convocatorias `draft`
  en un desplegable con una nota de procedencia (sin repetir la cita en 10 filas) y solo enlaza a
  «Ver particularidades» cuando hay algo que ver; el material se agrupa por obra.
- **Pruebas:** 2 pruebas nuevas (agrupación de `draft` y ausencia de pie/indicadores) y ajuste de la
  prueba de material; Vitest **17 ficheros / 212 pruebas**.
- **Decisión:** D-025.
- **Evidencia:** capturas revisadas con la aplicación en marcha (API 8765 y web 4173, ambos cerrados
  al terminar); puertas 1–16 en verde (511 unitarias + 484 integración + 23 contrato = **1018
  backend**, 212 Vitest, contrato, builds, migración y doble siembra). En la 17 pasan el temario
  común y las convocatorias C1; solo falla la verificación de fuentes oficiales de los perfiles
  (DEBT-028, previo). E2E no ejecutada.

### B-016

**HECHA (2026-11-07).** La ficha de tema ya no es un callejón: apuntes, preguntas y convocatorias
llevan a su sitio.

- **Entregado:** `AppearanceSchema` incluye `official_url` (bases oficiales o anuncio del listado) y
  la ficha enlaza cada convocatoria («Bases oficiales» para confirmadas, «Ver el anuncio» para las
  `draft`); el material abre la biblioteca en su documento (`/biblioteca?documento=<id>`); cada
  pregunta abre el banco con su conjunto y su pregunta (`/preguntas?conjunto=<id>&pregunta=<id>`), y
  `QuestionsPage` acepta ese estado inicial. Contrato y tipos regenerados.
- **Pruebas:** API comprueba que la apariencia trae el enlace; Vitest: enlaces de bases, de
  biblioteca y de banco, y apertura del banco por enlace directo (deep link). **17 ficheros / 213
  pruebas**.
- **Revisión visual:** ficha a 400 y 1280 px con API+web temporales (sin desbordes ni errores de
  consola); servidores y temporales cerrados al terminar. **No se dejan servidores ni navegadores
  abiertos.**
- **Evidencia:** puertas 1–16 en verde (511 unitarias + 484 integración + 23 contrato = **1018
  backend**, 213 Vitest, contrato, builds, migración y doble siembra). En la 17 pasan el temario
  común y las convocatorias C1; solo falla la verificación de fuentes oficiales de los perfiles
  (DEBT-028, previo). E2E no ejecutada.
- **Decisión:** D-026.
- **Criterio de cierre:** cumplido.

## Fuentes para generar tareas nuevas

1. **Competencia**: EstudiaTAI, OpositaTest, Adams, OposiciónInformática, OposTIC, Typed AI.
2. **Huecos de la especificación**: pantallas prometidas sin implementar, estados sin cubrir, casos
   límite de las convocatorias (sin temario publicado, temario con anexos, plazas reservadas).
3. **Deuda técnica**: `docs/DEBT.md` (27 entradas, varias abiertas: DEBT-003, DEBT-014, DEBT-016,
   DEBT-018, DEBT-020, DEBT-021, DEBT-022, DEBT-023, DEBT-027).
