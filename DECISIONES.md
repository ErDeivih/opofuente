# Decisiones tomadas sin preguntar (Nivel 2)

Registro del [protocolo de autonomía](../../EspacioCodigo/_flujo-dsh/PROTOCOLO-AUTONOMIA.md):
decisiones que el agente toma solo, con su motivo, para que David las revise cuando quiera. Las de
Nivel 1 (refactor, pruebas, docs) no se registran aquí. Lo que cambia el alcance, borra datos o toca
credenciales **no** está aquí: se pregunta.

Las decisiones de modelo de datos de esta sesión están desarrolladas en
[`ESPECIFICACION.md`](ESPECIFICACION.md) §5–§6 y en
[`docs/decisions/ADR-018`](docs/decisions/ADR-018-temario-comun-y-convocatorias-que-lo-referencian.md).
Aquí queda el resumen con el motivo y la reversión.

---

## D-001 — El temario común se modela con versiones, no con una fila editable

- **Fecha:** 2026-11-04 · **Nivel:** 2 · **Estado:** aplicada a la propuesta (no implementada)
- **Decisión:** `curricula` + `curriculum_versions` + `curriculum_nodes`; una versión `active` por
  temario, y una versión `active` no se edita: se publica la siguiente.
- **Motivo:** una convocatoria referencia una **versión concreta**. Si el temario común crece (el
  «tema 41» de la fuente), las convocatorias ya publicadas no deben cambiar solas: se actualiza su
  referencia cuando se decida. Es el patrón que el producto ya usa con `convocation_versions` y evita
  perder trazabilidad.
- **Alternativa descartada:** una sola fila de temario editada en sitio (rompe la historia y la
  estabilidad de lo ya publicado).
- **Reversión:** el `downgrade` de `0021` elimina las tablas y restaura `convocation_version_id`.

## D-002 — El programa publicado de cada convocatoria se conserva como evidencia

- **Fecha:** 2026-11-04 · **Nivel:** 2 · **Estado:** aplicada a la propuesta
- **Decisión:** cada convocatoria que publica temario conserva su árbol de nodos en una
  `curriculum_versions` de tipo `published`, con sus `id` intactos y una referencia `role='official'`.
- **Motivo:** las bases son la prueba de lo que la convocatoria pide. Borrarlas o sustituirlas por el
  temario común perdería la cita y la cobertura ya calculada; además, borrar datos es Nivel 3 y no
  hace falta. Con `id` intactos, `curriculum_mappings` y `learning_errors` siguen siendo válidos.
- **Alternativa descartada:** borrar los programas publicados y quedarse solo con el común (destructivo
  e irreversible).
- **Reversión:** el `downgrade` reconstruye `convocation_version_id` desde las refs `official`.

## D-003 — Los temas añadidos entran en el temario común, no en la convocatoria

- **Fecha:** 2026-11-04 · **Nivel:** 2 · **Estado:** aplicada a la propuesta
- **Decisión:** un tema que una convocatoria añade se incorpora al temario común con
  `origin_kind='enrichment'` y `origin_convocation_version_id` (procedencia); nunca se copia como
  tema propio de la convocatoria.
- **Motivo:** la decisión del propietario es que las convocatorias **referencian** el temario y no lo
  copian; la fuente lo dice igual («lo añades aquí como tema 41»). Guardar la procedencia mantiene la
  trazabilidad sin duplicar.
- **Alternativa descartada:** tabla de temas por convocatoria (reintroduce la copia que se prohíbe).
- **Reversión:** los nodos `enrichment` se pueden despublicar en una versión nueva; borrar un nodo con
  material está bloqueado por FK (ADR-007).

## D-004 — Una sola migración `0021`, reversible, y el contenido por fixture

- **Fecha:** 2026-11-04 · **Nivel:** 2 · **Estado:** aplicada a la propuesta
- **Decisión:** una migración de esquema y datos (`0021_temario_comun_y_referencias`) con `downgrade`
  completo; el contenido del temario común (5 bloques, 40 temas) entra por fixture con procedencia y
  siembra idempotente, igual que los perfiles oficiales (ADR-006).
- **Motivo:** SQLite no altera restricciones sin recrear la tabla, así que la migración tiene que ser
  una unidad probada de subida y bajada; y una migración no debe contener 40 títulos que nadie puede
  revisar ni verificar contra la fuente. Las puertas ya prueban migración desde cero, siembra
  idempotente y fixtures contra fuentes: el temario entra en las mismas puertas.
- **Alternativa descartada:** partir en dos migraciones (expandir/contratar) sin ventaja real en un
  producto local de un solo usuario, y meter los 40 temas en la migración.
- **Reversión:** `alembic downgrade 0020`; copia previa de la base antes de tocar datos reales.

## D-005 — El temario común v1 es el de `temario-c1.md` (5 bloques, 40 temas)

- **Fecha:** 2026-11-04 · **Nivel:** 2 · **Estado:** aplicada a la propuesta, revisable (§7 O1)
- **Decisión:** la versión 1 del temario común se siembra desde
  `F:\aprendizaje\empleo-informatica\minicerebro\temario-c1.md` (5 bloques, 40 temas, sha256
  `50d8fa7f…dcea`); el programa del TAI 2025 (4 bloques, 33 temas, ANEXO V del BOE) queda como
  programa **publicado** de su convocatoria, unido al común por `curriculum_equivalences`.
- **Motivo:** la fuente que la especificación ya llama «el temario único» es ese fichero, construido
  desde bases reales de 2026 y del TAI. El ANEXO V es el programa de **una** convocatoria; usarlo como
  temario del producto dejaría fuera régimen local, haciendas locales y seguridad que las C1 piden.
- **Alternativa descartada:** tomar los 33 temas del TAI como temario común (no cubre lo que las bases
  de 2026 piden y perdería la fuente ya trabajada).
- **Reversión:** cambiar el fixture y publicar otra versión; el modelo no cambia. Está marcada como
  revisable en `ESPECIFICACION.md` §7 (O1).
