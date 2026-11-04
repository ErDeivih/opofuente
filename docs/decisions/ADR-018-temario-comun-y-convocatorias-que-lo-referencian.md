# ADR-018 — Temario común único y convocatorias que lo referencian

- **Estado:** propuesta (4 de noviembre de 2026), **pendiente de ratificación por el propietario**.
  No se implementa hasta que se ratifique; el modelo completo, con columnas, restricciones y
  migración paso a paso, está en [`ESPECIFICACION.md`](../../ESPECIFICACION.md) §5 y §6.
- **Fecha:** 4 de noviembre de 2026
- **Ámbito:** modelo de datos del temario; sustituye el papel de `curriculum_nodes` de ADR-005
- **Motivo:** decisión ya tomada por el propietario (2026-11-04): **un solo temario común** para todas
  las convocatorias de informática C1, basado en el de TAI, que las convocatorias **referencian**. El
  modelo actual guarda el programa **dentro de cada convocatoria**, así que el producto no puede
  representar esa decisión sin copiar 40 temas por convocatoria.

## Contexto

El esquema heredado (`0002_profiles_and_curriculum`, ADR-005) tiene:

```text
convocation_versions 1 ─── N curriculum_nodes     UNIQUE(convocation_version_id, path)
```

Cada convocatoria tiene su copia del temario. Con dos convocatorias hay 235 nodos (37 de TAI, 198 de
Guardia Civil). Con las 10 convocatorias C1 de informática que ya están inventariadas en
`F:\aprendizaje\empleo-informatica`, serían ~760 nodos, y con el catálogo completo, más de 2.000; cada
corrección de un título habría que repetirla en todas. Además, las preguntas se clasifican contra el
nodo de **una** convocatoria (`curriculum_mappings.curriculum_node_id`, `ON DELETE RESTRICT`) y los
fallos del alumno también (`learning_errors.curriculum_node_id`): el banco y el progreso no se pueden
compartir entre convocatorias.

Datos que condicionan la decisión:

- `docs/product-spec/03_DATA-MODEL.md` §2 define `curriculum_equivalences` y dice que la identidad de
  un nodo **pertenece a una convocatoria**, con las equivalencias aparte. Ese diseño asumía varias
  oposiciones con temarios distintos; el producto decidido va en la dirección contraria.
- ADR-005 difirió `curriculum_equivalences` con una condición explícita: «se crea en el slice que la
  use». Este es ese slice: sin equivalencias no se pueden re-atribuir las preguntas del TAI al
  temario común.
- La fuente de contenido ya construida (`minicerebro/temario-c1.md`, 5 bloques y 40 temas) es el
  temario común; el programa del TAI (4 bloques y 33 temas, ANEXO V del BOE) es el **programa
  publicado** de una convocatoria concreta, no el temario del producto.
- Los `id` de nodo son el eje de `curriculum_mappings` y `learning_errors`: no se pueden cambiar.

## Opciones

| Opción | A favor | En contra |
|---|---|---|
| **A. Temario común versionado + convocatorias que lo referencian** (`curricula`, `curriculum_versions`, nodos dentro, `convocation_curriculum_refs`, `convocation_curriculum_adjustments`) | una sola copia de cada tema; el programa publicado se conserva como evidencia; particularidades con cita; el banco y el progreso se comparten; crecer es publicar versión | cinco tablas nuevas y una migración que recrea `curriculum_nodes` |
| B. Etiqueta N:M `tema ↔ convocatoria` sobre los nodos actuales | menos tablas; los nodos no se mueven | no guarda el programa publicado como evidencia; sin ponderación ni renumeración con cita; sin historia: el temario de una convocatoria vieja cambia si cambia el común; sigue habiendo copias |
| C. Copiar el temario por convocatoria (estado actual) | cero cambios | 40 × 50 nodos; correcciones redundantes; banco y progreso no compartidos; «en qué convocatorias aparece» no consultable |
| D. Una sola tabla `curricula` sin versiones | una tabla menos | una convocatoria publicada vería cambiar su temario sin aviso; se pierde la trazabilidad que el resto del producto exige |

## Decisión

**Opción A.** El temario común es **uno** (`curricula.kind='common'`, `code='informatica-c1'`) con
versiones (`curriculum_versions`), y las convocatorias lo referencian
(`convocation_curriculum_refs.role` = `primary` | `official` | `complementary`). Lo que una
convocatoria publica se conserva como **programa publicado** en una versión de tipo `published` —una
por convocatoria, con sus nodos y sus `id`— y no se borra. Las particularidades (omite, pondera,
renumera, renombra) son filas de `convocation_curriculum_adjustments`, con cita oficial obligatoria.
Los temas que entran al común por una convocatoria llevan procedencia (`origin_kind='enrichment'`,
`origin_convocation_version_id`). `curriculum_equivalences` une nodo publicado con nodo común y es
lo que permite re-atribuir el banco de preguntas y los fallos.

## Relación con decisiones anteriores

| Decisión previa | Qué pasa con ella aquí |
|---|---|
| ADR-005 (modelo de perfiles) | se sustituye **el papel** de `curriculum_nodes` (deja de colgar de la convocatoria); `exam_parts` y `exam_rules` siguen como ADR-005 los dejó. `curriculum_equivalences`, que ADR-005 difirió «al slice que la use», se crea aquí |
| ADR-007 y DEBT-005 (nodo con material asignado) | se mantiene intacta su política: la retirada de un nodo con `curriculum_mappings` está bloqueada por `ON DELETE RESTRICT` y la siembra informa el conflicto. ADR-007 aplazó como «decisión de modelo mayor, propia de cuando el temario se reorganice de verdad» el versionado de nodos; **esta es esa reorganización**. También rechazó la reasignación automática: por eso las equivalencias `proposed` no se aplican solas y la re-atribución exige `status='accepted'` |
| DEBT-003 (temario de Guardia Civil privado) | este cambio **no publica** ese temario: sus nodos se quedan en la base y en su fixture, y no se exponen a la zona del alumno porque esa convocatoria no tiene ref `primary` (§6.4) |

## Consecuencias

- `curriculum_nodes` cambia de dueño: `convocation_version_id` sale, `curriculum_version_id` entra
  (NOT NULL, `ON DELETE CASCADE`), y la unicidad pasa a `(curriculum_version_id, path)`. Los `id` no
  cambian: `curriculum_mappings` y `learning_errors` siguen vivos.
- Una migración `0021_temario_comun_y_referencias` (reversible, con `downgrade` probado) crea las
  tablas nuevas y rellena: cada convocatoria con nodos recibe su versión `published` y su ref
  `official`. El temario común nace **vacío** y lo llena un fixture con procedencia + siembra
  idempotente, no la migración.
- `exam_parts` y `exam_rules` **siguen** en la convocatoria: el formato del examen sí cambia.
- Guardia Civil y Celador **no se borran**: se migran como programas publicados sin ref `primary`, así
  que no entran en la aplicación del alumno.
- El `downgrade` restaura `convocation_version_id` desde la ref `official`; se lleva por delante el
  temario común (datos de esta funcionalidad). La re-atribución del banco es una tarea aparte, con su
  inverso probado, posterior a la migración.

## Reversión

1. `alembic downgrade 0020` (probado en `test_migrations_0021` y en `test_migrations_downgrade`).
2. Restaurar la copia previa de la base si el `downgrade` no fuese suficiente: es la vía preferida
   para datos reales y está documentada en `docs/OPERACION.md` §3.
3. El contenido del temario común no se pierde con el `downgrade` si se conserva su fixture, que es la
   fuente de verdad de la siembra.
