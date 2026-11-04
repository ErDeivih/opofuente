# Decisiones tomadas sin preguntar (Nivel 2)

Registro del [protocolo de autonomía](../../EspacioCodigo/_flujo-dsh/PROTOCOLO-AUTONOMIA.md):
decisiones que el agente toma solo, con su motivo, para que David las revise cuando quiera. Las de
Nivel 1 (refactor, pruebas, docs) no se registran aquí. Lo que cambia el alcance, borra datos o toca
credenciales **no** está aquí: se pregunta.

Las decisiones de modelo de datos de esta sesión están desarrolladas en
[`ESPECIFICACION.md`](ESPECIFICACION.md) §5–§6 y en
[`docs/decisions/ADR-018`](docs/decisions/ADR-018-temario-comun-y-convocatorias-que-lo-referencian.md).
Aquí queda el resumen con el motivo y la reversión.

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

## D-006 — B-001 incluye adaptar todo el código que resolvía el programa por convocatoria

- **Fecha:** 2026-11-04 · **Nivel:** 2 · **Estado:** aplicada
- **Decisión:** además de los modelos SQLAlchemy y la migración `0021`, esta tarea actualiza los
  repositorios que resolvían nodos por `convocation_version_id` (perfiles, clasificación, cobertura,
  búsqueda, readiness y preguntas) y las pruebas que insertaban nodos con esa columna.
- **Motivo:** cambiar el dueño del nodo sin adaptar a sus lectores deja la suite en rojo
  (`no such column: convocation_version_id`) y, peor, deja el producto sin poder leer su propio
  programa. `ESPECIFICACION.md` §8 ya cuantificaba ese impacto; hacerlo ahora es la parte de la
  tarea 1 de §6.9 que la puerta de pruebas exige, no un cambio de alcance.
- **Criterio aplicado:** se conserva el comportamiento actual del contrato: `/convocations/{id}/curriculum`
  sigue devolviendo el **programa publicado** de la convocatoria y `packages/contracts/openapi.json`
  no cambia. El temario común y sus rutas son B-002/B-004.
- **Alternativa descartada:** partir la migración en dos (expandir/contratar) para no tocar
  repositorios todavía; contradice §6.1 (una sola migración) y habría dejado el esquema a medias.
- **Reversión:** `alembic downgrade 0020` y `git revert` del cambio de repositorios; van juntos.

## D-007 — La siembra crea el envoltorio publicado de cada convocatoria

- **Fecha:** 2026-11-04 · **Nivel:** 2 · **Estado:** aplicada
- **Decisión:** `SqlAlchemyProfileRepository._sync_curriculum` crea, antes que los nodos y de forma
  idempotente, la `curricula` `published` (`<convocation>-programa`), su versión `active`
  (`<convocation>-programa-v1`) y la `convocation_curriculum_refs` con `role='official'` y la cita
  de la convocatoria.
- **Motivo:** una instalación nueva migra **y después siembra**. La migración solo puede rellenar el
  envoltorio de los datos que ya existían; si la siembra no lo hiciera, una base nueva tendría nodos
  colgando de versiones que nunca se crean. Los códigos son los de la migración para que, sobre una
  base migrada, la siembra reutilice el envoltorio en vez de duplicarlo o chocar con el índice que
  solo permite una versión activa por temario.
- **Alternativa descartada:** crear el envoltorio en `seed_profiles.py`; no cubriría la siembra de
  las pruebas ni la del servicio, y habría dos formas de sembrar.
- **Reversión:** las filas nuevas son de esta funcionalidad; el `downgrade` de `0021` las elimina.

## D-008 — Un nodo del temario común todavía no tiene ficha (404 en `/curriculum-nodes/{id}`)

- **Fecha:** 2026-11-04 · **Nivel:** 2 · **Estado:** aplicada, temporal
- **Decisión:** `get_node` resuelve la convocatoria por la referencia `official` de la versión del
  nodo. Si el nodo es del temario común (no tiene programa publicado) devuelve «no existe».
- **Motivo:** `NodeDetail` exige datos de la convocatoria (código, título, URL, fecha) y un nodo
  común no los tiene. Inventar una convocatoria o devolver campos vacíos sería mentir en el
  contrato. La ficha del nodo común, con «en qué convocatorias aparece», es la tarea B-004; hasta
  entonces no existen nodos comunes sembrados (B-002 es quien los pone).
- **Reversión:** B-004 sustituye este retorno por la ficha del temario común y sus pruebas.

## D-009 — Borrar una convocatoria ya no borra su programa publicado

- **Fecha:** 2026-11-04 · **Nivel:** 2 · **Estado:** aplicada (documentada como limitación)
- **Decisión:** el programa publicado es una **versión de temario**, no una parte de la
  convocatoria. Al borrar la convocatoria se van con ella sus `exam_parts`, `exam_rules` y sus
  referencias (`ON DELETE CASCADE`), pero el temario publicado y sus nodos **se conservan**, con sus
  `id`, porque son la evidencia de lo publicado y el eje de `curriculum_mappings`.
- **Motivo:** conservar los `id` es lo que mantiene vivos la clasificación y los fallos del usuario
  (§4.2), y borrar datos es Nivel 3. La API actual no ofrece borrar convocatorias, así que no hay
  un flujo de producto que quede roto; la prueba de integración se actualizó a la nueva semántica.
- **Limitación conocida:** si algún día se borra una convocatoria, su programa publicado queda como
  evidencia huérfana (sin referencia que lo alcance) y, además, la baja de `0021` ya no puede devolver
  esos nodos a ninguna convocatoria: el `downgrade` fallará con «nodos sin programa publicado» aunque
  no haya temario común sembrado. Habrá que decidir entonces si el borrado archiva el programa, lo
  borra en cascada explícita o se bloquea; queda anotado en `BACKLOG.md` (B-010).
- **Reversión:** el `downgrade` devuelve los nodos a su convocatoria desde la referencia `official`.

## D-010 — La siembra no reactiva versiones publicadas ni re-apunta referencias `official`

- **Fecha:** 2026-11-04 · **Nivel:** 2 · **Estado:** aplicada
- **Decisión:** al sembrar el programa publicado, si la versión `<conv>-programa-v1` existe pero no
  está `active` (fue sustituida por una v2), o si la referencia `official` de la convocatoria apunta a
  otra versión, la siembra **falla en voz alta** y no escribe: no pone la v1 `active` de nuevo ni
  cambia a qué versión apunta la referencia.
- **Motivo:** revivir una v1 `superseded` choca con `uq_curriculum_version_single_active` (el índice
  único parcial de I1) y, si la v2 estuviera en borrador, la resucitaría en silencio. Re-apuntar una
  referencia `official` es decidir qué bases constan como publicadas: es publicación, no siembra, y
  hacerlo de forma implícita rompería la trazabilidad que el producto exige. Falla antes de escribir
  y el mensaje dice qué hay que hacer (publicar la edición que toque).
- **Alternativa descartada:** dejar que la siembra «converja» la versión y la referencia al fixture
  (dos verdades sobre qué edición está vigente y riesgo de `IntegrityError` a medias).
- **Reversión:** el `downgrade` no se ve afectado; revertir es volver a permitir la reactivación.

## D-011 — La fuente del temario común entra por manifiesto y huella, no por una ruta fija

- **Fecha:** 2026-11-04 · **Nivel:** 2 · **Estado:** aplicada (B-002)
- **Decisión:** `fixtures/curricula/manifest.json` declara la fuente del temario común (`id`,
  `document`, `sha256`, `local_path` relativa al repositorio), y el generador la busca por este orden:
  `--source <ruta>`, variable `OPOFUENTE_TEMARIO_C1`, o `data/sources/temario-c1.md` (ignorada por
  git). Antes de leerla comprueba su `sha256`; si no coincide, no genera nada.
- **Motivo:** la fuente vive fuera del repositorio, en el espacio de contenido de `ESPECIFICACION.md`
  §2, y una ruta absoluta del equipo no debe quedar a fuego en el código (se rompe en otra máquina y
  no es trazable). El patrón es el mismo que ya usan los perfiles oficiales (ADR-006): manifiesto con
  huella + generador + `--check` en la puerta. El fixture queda rastreable hasta el documento.
- **Alternativa descartada:** escribir el JSON a mano (nadie podría verificar de dónde sale cada
  tema) o embeber la ruta `F:\…` en el código (se rompe fuera de este equipo).
- **Reversión:** cambiar el manifiesto y el `local_path`; el formato del fixture no cambia.

## D-012 — La v1 se publica solo con el recuento del contrato, y una versión activa no se edita

- **Fecha:** 2026-11-04 · **Nivel:** 2 · **Estado:** aplicada (B-002)
- **Decisión:** la siembra del común sincroniza los nodos de su edición y solo pone `active` cuando
  el recuento real es exactamente 5 bloques / 40 temas / 45 nodos (`ESPECIFICACION.md` §6.7). Si la
  edición ya está `active`, cualquier diferencia con el fixture **falla en voz alta** en lugar de
  reescribirla (I9). Un fixture incompleto se siembra en `draft` y no se publica.
- **Motivo:** publicar es afirmar que el temario está completo; y una convocatoria no puede ver
  cambiar el temario que estudia sin una edición nueva. El error temprano evita dos verdades y un
  `IntegrityError` del índice parcial de versión activa a mitad de la siembra.
- **Alternativa descartada:** publicar si el fixture «parece completo» (el propio fixture incompleto
  es coherente consigo mismo y pasaría esa comprobación).
- **Reversión:** volver a permitir ediciones sobre `active`; el `downgrade` de `0021` no cambia.

## D-013 — Las referencias del fixture se crean o confirman, no se re-apuntan solas

- **Fecha:** 2026-11-04 · **Nivel:** 2 · **Estado:** aplicada (B-002)
- **Decisión:** la siembra del común crea la referencia `primary` que declara el fixture (TAI 2025 →
  temario común, con la cita «ANEXO V, apartado 3») o actualiza su cita; si ya existe y apunta a
  **otra** versión, falla y no la re-apunta. Tampoco duplica una referencia al mismo par con otro
  papel.
- **Motivo:** qué edición estudia una convocatoria es una decisión de producto (O1), no un efecto de
  sembrar un fixture. Cambiarla en silencio dejaría a la convocatoria estudiando otra edición sin que
  nadie lo haya decidido; la cita, en cambio, sí debe converger con la fuente.
- **Alternativa descartada:** re-apuntar la referencia al valor del fixture (mismo problema que D-010
  con las `official`: dos verdades sobre la edición vigente).
- **Reversión:** el `downgrade` de `0021` borra las referencias del común; volver a sembrar las crea.
