# ADR-005 — Modelo de perfiles: convocatorias, programa y reglas de examen

- **Estado:** propuesta (requiere revisión del propietario en la revisión de S01)
- **Fecha:** 14 de septiembre de 2026
- **Ámbito:** modelo de datos de S01
- **Motivo:** `03_DATA-MODEL.md` §2 define `oppositions`, `convocation_versions` y
  `curriculum_nodes`, y `11_IMPLEMENTATION-SLICES.md` (S01) exige «reglas de examen validadas», pero
  **el modelo de datos no nombra ninguna tabla para las partes del examen ni para sus reglas**. Hay
  que decidirlo antes de escribir la migración.

## Contexto

Los perfiles oficiales verificados en S01 tienen esta forma (procedente de las fuentes oficiales,
ver `fixtures/profiles/manifest.json`):

- **TAI 2025:** un ejercicio único de dos partes (80 + 5 preguntas; un supuesto de 20 + 5), 120
  minutos, penalización de un tercio por error, cada parte 0–50 con mínimo 25, y la calificación
  oficial pendiente del baremo que publique la Comisión Permanente de Selección.
- **Guardia Civil 2026:** un bloque teórico-práctico de 140 minutos con cuatro pruebas (ortografía y
  gramática apto/no apto con umbral de seis errores; conocimientos 0–100 mínimo 50; inglés 0–20
  mínimo 8), una prueba psicotécnica con aptitudes (80 preguntas, 55 minutos, 0–30 mínimo 12) y una
  fórmula `Px = (Y/T)·(A − E/(N−1))` con `Y`, `T` y `N` por prueba.

Es decir: hay **agrupaciones** (bloques de pruebas), **partes** con reglas numéricas y **reglas**
transversales (fórmulas, penalizaciones, desempates, condiciones de calificación).

## Opciones

| Opción | A favor | En contra |
|---|---|---|
| Guardar el perfil como JSON validado en `convocation_versions.exam_profile_json` | no añade tablas; el perfil se lee siempre entero | `03_DATA-MODEL.md` §1 dice «JSON solo para payloads variables no consultados»; S07/S08 tendrán que consultar umbrales y partes; sin `CHECK` ni unicidad |
| **Dos tablas: `exam_parts` y `exam_rules`** | consultable, con restricciones reales, auditable con la cita de la fuente | añade dos tablas que el modelo de datos no nombra (esta ADR) |
| Una tabla por nivel (bloques, partes, reglas) | máxima normalización | tres tablas nuevas para datos que siempre se leen juntos y que no crecen |

## Decisión

Dos tablas nuevas, más las tres del modelo ya definido:

```text
oppositions            (id, code único, name, description, active)
convocation_versions   (id, opposition_id, code único, title, official_url, published_at,
                        exam_date, status, supersedes_id, created_at, updated_at)
curriculum_nodes       (id, convocation_version_id, parent_id, node_type, official_code,
                        title, description, position, path, depth)
exam_parts             (id, convocation_version_id, parent_id, code, name, kind, format,
                        position, ordinary_items, reserve_items, options_per_question,
                        score_min, score_max, pass_score, wrong_penalty_fraction,
                        fail_if_errors_gte, time_minutes, structure_note, notes, evidence_quote)
exam_rules             (id, convocation_version_id, code, kind, value_text, description,
                        evidence_quote)
```

- `exam_parts.kind` es `group` o `test`. Las agrupaciones son filas con `kind='group'` y las
  pruebas cuelgan de ellas por `parent_id` (por ejemplo, el bloque teórico-práctico de 140 minutos
  agrupa ortografía, gramática, conocimientos e inglés). `format` es
  `single_choice | multi_mark_error | psychotechnical` o nulo en las agrupaciones.
- Todo valor numérico admite `NULL`: **no se inventa** lo que la convocatoria no publica. En TAI,
  `options_per_question` queda nulo porque el anexo V no dice cuántas alternativas tiene cada
  pregunta (solo que hay una correcta y que el error descuenta un tercio). La interfaz debe mostrar
  «no consta en la convocatoria», no un número supuesto.
- Cada parte y cada regla guardan `evidence_quote`: la cita literal de la fuente oficial. La
  herramienta que construye los fixtures **comprueba que esa cita existe** en el documento
  descargado (hash verificado); una cifra sin cita no puede entrar.
- Restricciones reales: `UNIQUE(convocation_version_id, code)` en partes y reglas,
  `UNIQUE(convocation_version_id, path)` y `UNIQUE(convocation_version_id, official_code)` en el
  programa, e **índice único parcial** que impide más de una convocatoria `active` por oposición y
  más de una oposición activa.

## Se decide también NO crear en S01

| Elemento del modelo | Por qué no ahora |
|---|---|
| `curriculum_equivalences` | Con una sola convocatoria por oposición no hay ningún par de nodos que relacionar: sería una tabla vacía y sin pruebas. Se crea en el slice que la use (equivalencias entre convocatorias). |
| `convocation_versions.source_document_version_id` | Apunta a `document_versions`, que llega en S05. Una columna sin su clave foránea real sería una restricción falsa. Se añade con la tabla que referencia. |

## Consecuencias

- S07 y S08 podrán calcular con umbrales consultables, y toda cifra será trazable a su cita oficial.
- La interfaz de S01 puede mostrar las reglas con su procedencia, en lugar de una descripción
  inventada.
- Coste: dos tablas que el modelo de datos no nombraba. Si el propietario prefiere el JSON validado,
  hay que rehacer la migración `0002` antes de seguir.

## Reversión

Las tablas se crean en una sola migración (`0002_profiles_and_curriculum`) con su `downgrade`
completo y probado. Volver al JSON implica migrar los datos a una columna y eliminar las dos tablas.
