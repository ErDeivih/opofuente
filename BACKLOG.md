# Backlog — OpoFuente, temario común de informática C1

Regla del [protocolo](../../EspacioCodigo/_flujo-dsh/PROTOCOLO-AUTONOMIA.md): **nunca menos de 5
tareas listas**. Cada sesión: comprobar estado → elegir la de más valor → ejecutar → pasar puertas →
commit y push → actualizar este fichero. Una tarea bloqueada no para la sesión: se marca y se sigue
con la siguiente.

Estado de partida (2026-11-04, sesión 2): la propuesta de modelo está escrita en
[`ESPECIFICACION.md`](ESPECIFICACION.md) §5–§6, con su ADR-018 en propuesta. **Nada implementado**, a
propósito: el encargo pedía escribirla antes de codificar.

## Lista

| ID | Tarea | Nivel | Estado | Depende de |
|---|---|---|---|---|
| [B-001](#b-001) | Modelos + migración `0021_temario_comun_y_referencias` | 2 | lista (sujeta a revisión del documento) | — |
| [B-002](#b-002) | Fixture del temario común v1, generador y siembra idempotente | 2 | lista | B-001 |
| [B-003](#b-003) | Equivalencias TAI publicado → común y re-atribución del banco | 2 | lista | B-002 |
| [B-004](#b-004) | API y contrato del temario común y de las particularidades | 2 | lista | B-002 |
| [B-005](#b-005) | Interfaz: índice del temario, ficha de tema y avance | 2 | lista | B-004 |
| [B-006](#b-006) | Importar las convocatorias C1 de `c1.txt` como referencias | 2 | lista | B-004 |
| [B-007](#b-007) | Entrega del slice `docs/slices/S13.md` | 1 | lista | B-005 |
| [B-008](#b-008) | Poner al día `docs/product-spec/03_DATA-MODEL.md` y el índice de ADR | 1 | lista | B-001 |
| [B-009](#b-009) | Investigación encomendada: cómo organizan el temario las academias C1 | 1 | lista | — |

## Detalle

### B-001

**Modelos y migración `0021_temario_comun_y_referencias`.** Cinco tablas nuevas (`curricula`,
`curriculum_versions`, `convocation_curriculum_refs`, `convocation_curriculum_adjustments`,
`curriculum_equivalences`), `curriculum_nodes` cambia de dueño (`convocation_version_id` →
`curriculum_version_id`, unicidad `(curriculum_version_id, path)`) y backfill no destructivo, según
`ESPECIFICACION.md` §5–§6.

- **Ficheros:** `apps/api/opofuente/infrastructure/db_models.py`,
  `apps/api/alembic/versions/0021_temario_comun_y_referencias.py`,
  `apps/api/tests/integration/test_migrations_0021.py`.
- **Criterio de cierre:** `alembic upgrade head` desde vacío y desde copia de la base viva (`0004`);
  `downgrade 0020` + `upgrade head` sin error; 235 nodos antes = 235 después; 0 nodos sin versión;
  `PRAGMA foreign_key_check` vacío; ninguna convocatoria sin su ref `official`; pruebas verdes.
- **Nota:** si la revisión del documento cambia el modelo, se ajusta aquí antes de codificar (el
  ADR-018 seguiría en propuesta hasta ratificarse).

### B-002

**Fixture del temario común v1** desde `F:\aprendizaje\empleo-informatica\minicerebro\temario-c1.md`
(5 bloques, 40 temas), generador con verificación de sha256 y siembra idempotente en la puerta que ya
existe.

- **Ficheros:** `fixtures/curricula/informatica-c1.v1.json`,
  `apps/api/opofuente/tools/build_curriculum_fixtures.py`,
  `apps/api/opofuente/tools/seed_profiles.py` (o `seed_curricula.py`), `scripts/gates.ps1` (sin pasos
  nuevos si se engancha a la siembra existente), pruebas de siembra.
- **Criterio de cierre:** siembra dos veces sin cambios (`--check` en verde); 5 bloques / 40 temas /
  45 nodos con `path` `I.1`…`V.40`; la ref `primary` de `tai-age-2025` al temario común queda creada
  con su cita; `build_curriculum_fixtures --check` no detecta diferencias.

### B-003

**Equivalencias nodo publicado → nodo común y re-atribución.** Propuesta de las 33→40 equivalencias,
revisión humana de las dudosas y re-apuntado de `curriculum_mappings` y `learning_errors` al nodo
común, con informe por fila.

- **Ficheros:** migración de datos o herramienta `tools/remap_curriculum.py` (con inverso probado),
  `fixtures/curricula/tai-age-2025.equivalences.json`, pruebas.
- **Criterio de cierre:** ninguna pregunta pierde su tema (informe con antes/después); las
  equivalencias `proposed` no se aplican solas; re-ejecutar no duplica; el inverso devuelve el banco a
  los nodos publicados y una prueba lo comprueba.

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
  permiso; `ai-design-check` o la lista de diez de las recetas; ojos frescos de un subagente sin
  historial.

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
`13_DECISIONS-AND-OPEN-QUESTIONS.md` (preguntas O1–O4 de `ESPECIFICACION.md` §7) y el índice de ADR
(ratificar ADR-018 cuando David la apruebe).

### B-009

**Investigación encomendada** (AGENTE.md): cómo organizan el temario las academias de informática C1
y los portales de oposiciones, y qué se repite en todas las convocatorias. Termina en
`INVESTIGACION.md` con lo mirado (enlace o captura), lo que hace la competencia, lo que nos falta y
**una propuesta concreta** de tarea Nivel 1 o 2. Si la propuesta cambia el alcance, es Nivel 3: se
pregunta.

## Fuentes para generar tareas nuevas

1. **Competencia**: EstudiaTAI, OpositaTest, Adams, OposiciónInformática, OposTIC, Typed AI.
2. **Huecos de la especificación**: pantallas prometidas sin implementar, estados sin cubrir, casos
   límite de las convocatorias (sin temario publicado, temario con anexos, plazas reservadas).
3. **Deuda técnica**: `docs/DEBT.md` (27 entradas, varias abiertas: DEBT-003, DEBT-014, DEBT-016,
   DEBT-018, DEBT-020, DEBT-021, DEBT-022, DEBT-023, DEBT-027).
