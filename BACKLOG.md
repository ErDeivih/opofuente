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
| [B-004](#b-004) | API y contrato del temario común y de las particularidades | 2 | lista | B-002 |
| [B-005](#b-005) | Interfaz: índice del temario, ficha de tema y avance | 2 | lista | B-004 |
| [B-006](#b-006) | Importar las convocatorias C1 de `c1.txt` como referencias | 2 | lista | B-004 |
| [B-007](#b-007) | Entrega del slice `docs/slices/S13.md` | 1 | lista | B-005 |
| [B-008](#b-008) | Poner al día `docs/product-spec/03_DATA-MODEL.md` y el índice de ADR | 1 | lista | B-001 |
| [B-009](#b-009) | Investigación encomendada: cómo organizan el temario las academias C1 | 1 | lista | — |
| [B-010](#b-010) | Decidir la bajada de `0021` después de sembrar el temario común | 2 | lista | B-002 |
| [B-011](#b-011) | Estabilizar las pruebas de API que compiten con el worker de fondo | 1 | lista | — |
| [B-012](#b-012) | Acotar por versión la resolución de nodo por `path` en clasificación | 2 | lista | B-004 |

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

**API y contrato.** Rutas del temario común (`/curricula`, `/curricula/{code}/versions`,
`/convocations/{id}/temario`, `/convocation/{id}/references`), campos `appears_in` y particularidades
en la ficha de nodo; `export_openapi` y tipos TS regenerados. `/convocations/{id}/curriculum` sigue
devolviendo el programa **publicado** para no romper lo que ya llama.

- **Ficheros:** `api/routes/profiles.py`, `api/profiles_schemas.py`,
  `application/profiles_service.py`, `read_models.py`, `infrastructure/profile_repository.py`,
  `packages/contracts/openapi.json`, `packages/contracts/src/openapi.d.ts`.
- **Criterio de cierre:** pruebas de contrato y de integración verdes; `export-openapi -Check` y
  `npm run contracts:check` en verde; una convocatoria sin ref `primary` no aparece como estudiable.

### B-005

**Interfaz del alumno y de administración.** Índice del temario común (5 bloques, búsqueda que perdona
tildes, marca de estudiado), ficha de tema con «en qué convocatorias aparece», avance por bloque y
total. Sin nombres de fuentes, rutas de Windows ni versiones en la zona del alumno.

- **Ficheros:** `apps/web/src/pages/ProgramPage.tsx`, `apps/web/src/features/profiles/*`,
  `apps/web/src/features/study/*`, pruebas de interfaz.
- **Criterio de cierre:** checklist de `ESPECIFICACION.md` §9 con estados vacío/cargando/error/sin
  permiso; **sin textos de desarrollador ni explicaciones de cómo se calcula nada**
  (`DOCTRINA-CALIDAD.md` §8: la app no habla de tokens, endpoints, «últimas temporadas» ni fórmulas);
  `ai-design-check` o la lista de diez de las recetas; ojos frescos de un subagente sin historial.

### B-006

**Importar convocatorias C1** de `fuentes\oposicionesinformatica\c1.txt` (10) y
`minicerebro\convocatorias.csv` (23) como convocatorias con su ref `primary` al temario común y su
cita de bases. Sin copiar temario: solo referencia y particularidades cuando las bases las digan.

- **Criterio de cierre:** cada convocatoria importada tiene `official_url` y `source_reference`; las
  que no publican temario no inventan particularidades; prueba de idempotencia.

### B-007

**Entrega del slice** con el formato obligatorio de `AGENTS.md`
(`docs/slices/S13.md`): qué se construyó, cómo fluye la información, ficheros y migraciones,
patrones, seguridad, puertas ejecutadas, prueba manual, limitaciones, qué se rompe si cambias X, qué
criticaría un revisor senior. Sin declarar pruebas no ejecutadas.

### B-008

**Documentación al día:** `docs/product-spec/03_DATA-MODEL.md` §2 (sustituir el modelo
convocatoria→nodos por el de temario común + refs, y `curriculum_equivalences` creada),
`13_DECISIONS-AND-OPEN-QUESTIONS.md` (preguntas O1–O4 de `ESPECIFICACION.md` §7) y el índice de ADR.
ADR-018 ya está ratificada en esta sesión (aprobación de David registrada en `ESPECIFICACION.md`);
queda enlazarla en el índice y reflejar O1–O4.

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

## Fuentes para generar tareas nuevas

1. **Competencia**: EstudiaTAI, OpositaTest, Adams, OposiciónInformática, OposTIC, Typed AI.
2. **Huecos de la especificación**: pantallas prometidas sin implementar, estados sin cubrir, casos
   límite de las convocatorias (sin temario publicado, temario con anexos, plazas reservadas).
3. **Deuda técnica**: `docs/DEBT.md` (27 entradas, varias abiertas: DEBT-003, DEBT-014, DEBT-016,
   DEBT-018, DEBT-020, DEBT-021, DEBT-022, DEBT-023, DEBT-027).
