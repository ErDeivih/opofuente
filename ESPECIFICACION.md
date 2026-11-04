# Especificación — OpoFuente, oposiciones de informática C1

Estado: **propuesta de modelo de datos escrita** (2026-11-04). La implementación **no ha empezado**
y no empieza hasta que David revise §5 y §6. Lo que aquí aparece como «decidido» ya no se vuelve a
preguntar; lo que se puede implementar sin esperar está marcado como Nivel 1/2 y anotado en
`DECISIONES.md`. Lo único que sigue abierto para David está en §7.

## 0. Qué cambia esta revisión

| Antes (versión anterior, mismo día) | Ahora |
|---|---|
| «El modelo de datos es lo primero que hay que decidir»: cinco preguntas pendientes | Las cinco están respondidas en §5, con el porqué de cada una y las alternativas descartadas |
| No había leído el esquema real | §4 recoge el modelo **medido**: tablas, columnas, restricciones y datos de la base viva |
| No había plan de migración | §6 tiene la migración `0021` paso a paso, con `downgrade` completo y verificación |
| No se sabía qué piezas del producto actual se pueden romper | §8 cuantifica el impacto: 18 módulos, 28 ficheros de prueba, 16 de interfaz y el contrato OpenAPI |

## 1. Qué es y qué no es

**Es**: una plataforma de temario para **oposiciones de informática de España de cualquier
administración** — ayuntamientos, diputaciones, comunidades, sanidad, Estado. Grupo **C1** (y su
escalón C2 si comparte temario).

**No es**: celador, Guardia Civil ni ninguna oposición que no sea de informática. Ese material existe
en la base heredada y **no se borra**, pero no entra en el producto.

## 2. El problema real que resuelve

Las distintas oposiciones C1 de informática **no comparten temario entre sí**. Cada convocatoria
publica el suyo. La solución no es copiar uno: es **un temario general basado en el de TAI**,
enriquecido con lo que aparece en las demás, y que cada convocatoria **referencie** con sus
particularidades.

Las fuentes de contenido ya están trabajadas en:

```
F:\aprendizaje\empleo-informatica\
```

| Fichero | Qué es |
|---|---|
| `minicerebro\temario-c1.md` (143 líneas, sha256 `50d8fa7f…dcea`) | **el temario único**: 5 bloques y 40 temas, construido desde bases reales de 2026 y del TAI del Estado |
| `fuentes\oposicionesinformatica\c1.txt` | 10 convocatorias de informática C1 con su enlace |
| `fuentes\sacyl\C1 Tecnico Especialista en Informatica\` | convocatorias y plantillas de examen reales de Ávila, León, Palencia, Salamanca, Soria, Valladolid y Zamora |
| `minicerebro\convocatorias.csv` | inventario de 23 convocatorias con administración, grupo, plazo y enlace |
| `alertas\` | vigía de nuevas oposiciones de informática |

Datos que esas fuentes ya dejan escritos y que el producto debe respetar:

- Las C1 que publican temario tienen **unos 40 temas**.
- Materias que **se repiten en todas**: régimen local, redes, sistemas operativos y servidores,
  copias de seguridad y continuidad.
- **Formato típico del examen**: test de **50 preguntas** (a veces 40–90), penalización de **1/3 o
  1/4** por error, **más un supuesto práctico**; **5 sobre 10** en cada parte.

## 3. Lo que ya está decidido

| Fecha | Decisión | Quien |
|---|---|---|
| 2026-11-04 | **Un solo temario común** para todas las convocatorias de informática C1, **basado en el de TAI**. Las convocatorias lo **referencian**; el temario **no se copia** por convocatoria. | David (encargo) |
| 2026-11-04 | La fuente de contenido es `F:\aprendizaje\empleo-informatica\`. El banco de 53,7 GB de `E:` **no** es la fuente de este producto. | David (encargo) |
| 2026-11-04 | Se trabaja solo en la rama `rescate/fase0-2026-10-26` de este worktree. `main` vive en `F:\temp-opofuente\opofuente-restaurado` y **no se toca** desde aquí. No se abren ramas. | David (encargo) |

## 4. El modelo de datos actual (leído del código y de la base, no supuesto)

### 4.1 Qué hay hoy

El repositorio contiene el producto anterior completo: banco de preguntas, sesiones de estudio,
documentos y RAG. El eje del temario son **las tablas de `S01`** (`apps/api/opofuente/
infrastructure/db_models.py`, migración `0002_profiles_and_curriculum`, ADR-005):

| Tabla | Papel | Columnas que importan aquí |
|---|---|---|
| `oppositions` | el cuerpo u oposición (`tai-age`, `gc-cabos-guardias`) | `id`, `code` único, `name`, `active` |
| `convocation_versions` | una convocatoria concreta (`tai-age-2025`) | `id`, `opposition_id`, `code` único, `title`, `official_url`, `published_at`, `status`, `supersedes_id` |
| `curriculum_nodes` | **el programa, colgado de la convocatoria** | `id`, **`convocation_version_id` NOT NULL**, `parent_id`, `node_type` (`block`/`topic`/`epigraph`), `official_code`, `title`, `description`, `position`, `path`, `depth` |
| `exam_parts` | partes del examen, de la convocatoria | umbrales, formato, penalización, tiempo, `evidence_quote` |
| `exam_rules` | reglas transversales, de la convocatoria | `code`, `kind`, `value_text`, `description`, `evidence_quote` |

Las restricciones reales de `curriculum_nodes` hoy (volcado del DDL en una base migrada a `head`):

```sql
CONSTRAINT uq_curriculum_path UNIQUE (convocation_version_id, path),
CONSTRAINT ck_node_type CHECK (node_type IN ('block', 'topic', 'epigraph')),
FOREIGN KEY(convocation_version_id) REFERENCES convocation_versions (id) ON DELETE CASCADE,
FOREIGN KEY(parent_id) REFERENCES curriculum_nodes (id) ON DELETE CASCADE
```

Es decir: **la identidad de un tema es `(convocatoria, ruta)`**. El temario es una copia por
convocatoria.

### 4.2 Quién apunta a un nodo (lo que no se puede romper)

Solo dos sitios guardan `curriculum_node_id`:

| Dónde | Restricción | Qué se pierde si el nodo desaparece |
|---|---|---|
| `curriculum_mappings.curriculum_node_id` | `ON DELETE RESTRICT` | la clasificación de documentos, secciones, citas y preguntas contra el temario; la cobertura |
| `learning_errors.curriculum_node_id` (opcional) | `SET NULL` | el tema al que el alumno atribuyó un fallo |

**Los `id` de los nodos son el eje de todo el banco de preguntas y del progreso.** Cualquier modelo
nuevo tiene que conservarlos.

### 4.3 Qué no existe todavía

- **`curriculum_equivalences`**: `03_DATA-MODEL.md` §2 la define, pero **no se creó**. ADR-005 lo
  decidió a propósito: «con una sola convocatoria por oposición no hay ningún par de nodos que
  relacionar; se crea en el slice que la use». Ese slice es este (§5.7).
- `convocation_versions.source_document_version_id`: también diferida; sigue sin existir.
- El programa común: no existe. Solo hay programas publicados por convocatoria.

### 4.4 Medida de la base viva (para dimensionar la migración)

`data/opofuente.sqlite3` está en la revisión `0004` (antigua; la cabeza del código es `0020`):

| Tabla | Filas |
|---|---|
| `oppositions` | 2 (`tai-age` activa, `gc-cabos-guardias` inactiva) |
| `convocation_versions` | 2 (`tai-age-2025`, `gc-cabos-guardias-2026`) |
| `curriculum_nodes` | **235** = 37 de TAI (4 bloques, 33 temas) + 198 de Guardia Civil |
| `exam_parts` | 10 |
| `exam_rules` | 19 |

La migración tiene que funcionar con esas 235 filas y con cualquier base posterior que ya esté en
`0020`. No depende del directorio de datos ni del banco de `E:`.

### 4.5 Por qué el modelo actual no sirve para el producto decidido

| Problema | Consecuencia concreta |
|---|---|
| El temario cuelga de la convocatoria | 40 temas × 50 convocatorias = 2.000 nodos, y cada corrección hay que repetirla 50 veces |
| La pregunta se clasifica contra el nodo de **una** convocatoria | la misma pregunta no aparece al estudiar otra convocatoria |
| El progreso se mide por nodo de convocatoria | el avance no se puede compartir entre convocatorias |
| «En qué convocatorias aparece este tema» | **no es consultable**: no hay relación entre programas, solo copias |
| Enriquecer el temario | obliga a re-sembrar el árbol de cada convocatoria y a resolver la retirada de nodos a mano |

### 4.6 Qué del modelo actual se conserva (y por qué)

| Pieza | Se conserva porque |
|---|---|
| `id` de nodo como clave estable | lo referencian las preguntas y los fallos (§4.2) |
| El programa **publicado** por cada convocatoria | es la evidencia de las bases; no se puede borrar ni sustituir por el común |
| `exam_parts` y `exam_rules` por convocatoria | el formato del examen **sí** cambia por convocatoria (50 preguntas vs 80+20, penalización 1/3 vs 1/4) |
| Siembra idempotente por `path` y retirada bloqueada por material | ADR-007 y DEBT-005 ya resolvieron que un nodo con material no se borra |
| `evidence_quote` obligatoria en partes, reglas y mapeos | el producto no inventa cifras ni citas |

## 5. Modelo propuesto: un temario común, convocatorias que lo referencian

### 5.1 Vista de conjunto

```text
TEMARIO COMÚN (lo que se estudia)          CONVOCATORIA (lo que se convoca)
─────────────────────────────             ──────────────────────────────
curricula (kind='common')                 oppositions
   │                                          │
   └── curriculum_versions (v1, v2…)          └── convocation_versions
          │                                        │   │
          └── curriculum_nodes ──┐                 │   ├── exam_parts
                                 │                 │   └── exam_rules
                                 │                 │
                                 ├─ convocation_curriculum_refs ◄──┘
                                 │      (role: primary | official | complementary)
                                 │
                                 ├─ convocation_curriculum_adjustments
                                 │      (omitted | weighted | renumbered | renamed)
                                 │
                                 └─ curriculum_equivalences
                                        (nodo publicado ◄─► nodo común)

PROGRAMA PUBLICADO (la evidencia)
─────────────────────────────────
curricula (kind='published')  ← una por convocatoria que publica temario
   └── curriculum_versions
          └── curriculum_nodes  ← los 235 nodos actuales, mismo id, sin copiar
```

Lectura en una frase: **el temario común es uno**, vive en `curricula`/`curriculum_versions` y lo
estudian todas; **cada convocatoria publica su programa** y ese programa se conserva como evidencia
en una versión de tipo `published`; entre ambos hay **referencia** (qué temario estudia esa
convocatoria) y **particularidades** (qué omite, qué pondera, cómo renumera). Nada se copia.

### 5.2 `curricula` — la identidad del temario

| Columna | Tipo | Regla |
|---|---|---|
| `id` | `VARCHAR(36)` | PK (UUID) |
| `code` | `VARCHAR(64)` | **único**; `informatica-c1` para el común, `<convocatoria>-programa` para un publicado |
| `kind` | `VARCHAR(16)` | `CHECK IN ('common','published')` |
| `name` | `TEXT` | nombre legible |
| `description` | `TEXT` | opcional |
| `group_code` | `VARCHAR(8)` | opcional: `C1` (el grupo al que sirve el temario) |
| `family` | `VARCHAR(32)` | opcional: `informatica` |
| `created_at`, `updated_at` | `DATETIME` | UTC |

Hoy hay exactamente **dos tipos de fila**: una `common` (`informatica-c1`) y una `published` por cada
convocatoria que publica programa. El tipo `published` no es un adorno: es lo que permite **no borrar**
los programas heredados (Guardia Civil incluida) y seguir enseñándolos en administración como
evidencia, sin que entren en la aplicación del alumno.

### 5.3 `curriculum_versions` — las ediciones del temario

| Columna | Tipo | Regla |
|---|---|---|
| `id` | `VARCHAR(36)` | PK |
| `curriculum_id` | `VARCHAR(36)` | FK → `curricula.id` `ON DELETE RESTRICT` |
| `version_no` | `INTEGER` | `>= 1`; `UNIQUE(curriculum_id, version_no)` |
| `code` | `VARCHAR(64)` | **único**; `informatica-c1-v1`, `informatica-c1-v2`… |
| `title` | `TEXT` | título de la edición |
| `status` | `VARCHAR(16)` | `CHECK IN ('draft','active','superseded','archived')` |
| `source_reference` | `TEXT` | de dónde sale esta edición (documento y ancla) |
| `supersedes_id` | `VARCHAR(36)` | FK a sí misma `ON DELETE SET NULL` |
| `created_at`, `updated_at` | `DATETIME` | UTC |

Índice único parcial, igual que en `opposition`/`convocation_versions`:

```sql
CREATE UNIQUE INDEX uq_curriculum_version_single_active
    ON curriculum_versions(curriculum_id) WHERE status = 'active';
```

**Por qué versiones y no una fila que se edita.** La convocatoria referencia una **versión concreta**:
cuando el temario común crezca (el «tema 41» de `temario-c1.md`), se publica una versión nueva sin
cambiar lo que estudia una convocatoria ya publicada hasta que su referencia se actualice. Es el
mismo patrón que ya usa el producto con `convocation_versions.supersedes_id`; no se inventa nada.

**Reglas de negocio** (servicio + prueba, no solo SQL):

1. Una versión `active` **no se edita**: se crea la siguiente y se marca la anterior `superseded`.
2. Solo una versión `active` por temario (lo garantiza el índice parcial).
3. Una referencia `primary` **solo puede apuntar a una versión `active`** (invariante de servicio;
   SQLite puede reforzarlo con un trigger, se decide en la implementación).
4. Contenido vacío no se publica: una versión `active` tiene al menos un bloque y un tema (prueba).
   Por eso la migración crea la v1 del temario común en `draft` y **la publica la siembra** cuando los
   40 temas están dentro (§6.7).

### 5.4 `curriculum_nodes` — la tabla actual cambia de dueño, no de forma

Se **conserva la tabla** y los `id`; cambia la clave foránea que la ata:

| Columna | Cambio |
|---|---|
| `convocation_version_id` | **se elimina** |
| `curriculum_version_id` | **nueva**, `VARCHAR(36)` NOT NULL, FK → `curriculum_versions.id` `ON DELETE CASCADE` |
| `origin_kind` | **nueva**, `VARCHAR(16)` NOT NULL default `base`, `CHECK IN ('base','enrichment')` |
| `origin_convocation_version_id` | **nueva**, `VARCHAR(36)` NULL, FK → `convocation_versions.id` `ON DELETE SET NULL` |
| `parent_id`, `node_type`, `official_code`, `title`, `description`, `position`, `path`, `depth` | sin cambios |

Restricción de unicidad, renombrada para que diga la verdad:

```sql
CONSTRAINT uq_curriculum_node_path UNIQUE (curriculum_version_id, path)
```

**Procedencia del enriquecimiento.** Un tema que entra al temario común porque una convocatoria lo
pedía lleva `origin_kind='enrichment'` y `origin_convocation_version_id` apuntando a la convocatoria
que lo motivó. Eso es trazabilidad, no una copia: el tema es **uno** y lo estudian todas. Los temas
que están en la base TAI llevan `origin_kind='base'` y `origin_convocation_version_id=NULL`.

**Estructura de la v1 del temario común** (`temario-c1.md`): 5 bloques (`I`–`V`), 40 temas numerados
`1`–`40` con `path` `I.1`…`V.40`; `node_type` `block`/`topic`; sin epígrafes en la v1 (el nivel
`epigraph` sigue permitido y no se usa).

### 5.5 `convocation_curriculum_refs` — la convocatoria referencia el temario

| Columna | Tipo | Regla |
|---|---|---|
| `id` | `VARCHAR(36)` | PK |
| `convocation_version_id` | `VARCHAR(36)` | FK → `convocation_versions.id` `ON DELETE CASCADE` |
| `curriculum_version_id` | `VARCHAR(36)` | FK → `curriculum_versions.id` `ON DELETE RESTRICT` |
| `role` | `VARCHAR(16)` | `CHECK IN ('primary','official','complementary')` |
| `source_reference` | `TEXT` | cita de las bases: «Anexo V, apartado 3. Programa» |
| `created_at`, `updated_at` | `DATETIME` | UTC |

```sql
CONSTRAINT uq_convocation_curriculum_ref UNIQUE (convocation_version_id, curriculum_version_id);
CREATE UNIQUE INDEX uq_convocation_primary_ref
    ON convocation_curriculum_refs(convocation_version_id) WHERE role = 'primary';
CREATE UNIQUE INDEX uq_convocation_official_ref
    ON convocation_curriculum_refs(convocation_version_id) WHERE role = 'official';
```

Los tres papeles, y qué significa cada uno:

| `role` | Qué dice | Obligatorio |
|---|---|---|
| `primary` | **el temario común que se estudia** para esta convocatoria | sí, para que la convocatoria sea «estudiable» |
| `official` | el programa que **publica** la convocatoria (evidencia, `curricula.kind='published'`) | solo si publica temario |
| `complementary` | otro temario que también aplica (p. ej. un específico de la administración) | no |

Una convocatoria sin ref `primary` **existe** (Guardia Civil, Celador) pero **no es estudiable** en la
aplicación nueva: no hay que borrarla ni mentir; simplemente no aparece en la zona del alumno.

### 5.6 `convocation_curriculum_adjustments` — las particularidades, sin copiar el tema

| Columna | Tipo | Regla |
|---|---|---|
| `id` | `VARCHAR(36)` | PK |
| `ref_id` | `VARCHAR(36)` | FK → `convocation_curriculum_refs.id` `ON DELETE CASCADE` |
| `curriculum_node_id` | `VARCHAR(36)` | FK → `curriculum_nodes.id` `ON DELETE RESTRICT` |
| `kind` | `VARCHAR(16)` | `CHECK IN ('omitted','weighted','renumbered','renamed')` |
| `weight` | `REAL` | NULL salvo `weighted`; `>= 0` (proporción de preguntas del examen) |
| `official_code_override` | `VARCHAR(32)` | NULL salvo `renumbered` |
| `title_override` | `TEXT` | NULL salvo `renamed` |
| `evidence_quote` | `TEXT` | **NOT NULL**: cita literal de las bases |
| `created_at`, `updated_at` | `DATETIME` | UTC |

```sql
CONSTRAINT uq_adjustment_identity UNIQUE (ref_id, curriculum_node_id, kind);
CONSTRAINT ck_adjustment_weight   CHECK (kind <> 'weighted'   OR weight IS NOT NULL);
CONSTRAINT ck_adjustment_code     CHECK (kind <> 'renumbered' OR official_code_override IS NOT NULL);
CONSTRAINT ck_adjustment_title    CHECK (kind <> 'renamed'    OR title_override IS NOT NULL);
CONSTRAINT ck_adjustment_evidence CHECK (length(evidence_quote) > 0);
```

Qué significa cada tipo:

| `kind` | Significado | Ejemplo real |
|---|---|---|
| `omitted` | esta convocatoria **no** incluye ese tema | una convocatoria que no pide «régimen local» |
| `weighted` | ese bloque o tema **pesa** de una forma concreta en el examen | bloque III con el 40 % de las preguntas |
| `renumbered` | la convocatoria lo numera distinto | su «tema 3» es nuestro «tema 7» |
| `renamed` | la convocatoria lo titula distinto | «Administración electrónica» vs «Sede electrónica» |

Reglas:

1. **La omisión se hereda**: si se omite un bloque, se consideran omitidos sus temas, sin filas
   duplicadas.
2. Un ajuste **no cambia el temario común**: solo cómo lo ve esa convocatoria. El tema sigue en el
   común y lo estudian las demás.
3. Un ajuste siempre lleva su cita: no se inventa que una convocatoria omite algo.
4. `weighted` sobre un bloque no impide `weighted` sobre sus temas; el cálculo del simulacro usa el
   nivel más específico (regla del servicio, con prueba).

### 5.7 `curriculum_equivalences` — tender el puente entre lo publicado y lo común

Se crea ahora porque **ya tiene uso real** (la condición que puso ADR-005): los 37 nodos publicados
del TAI tienen preguntas mapeadas y el temario común tiene 40 temas; para que las preguntas aparezcan
bajo el tema común hay que decir qué nodo publicado corresponde a qué nodo común.

| Columna | Tipo | Regla |
|---|---|---|
| `id` | `VARCHAR(36)` | PK |
| `source_node_id` | `VARCHAR(36)` | FK → `curriculum_nodes.id` `ON DELETE RESTRICT`; nodo **publicado** |
| `target_node_id` | `VARCHAR(36)` | FK → `curriculum_nodes.id` `ON DELETE RESTRICT`; nodo **común** |
| `relation` | `VARCHAR(16)` | `CHECK IN ('equivalent','subset','superset','partial')` |
| `confidence` | `REAL` | `0..1` |
| `status` | `VARCHAR(16)` | `CHECK IN ('proposed','accepted','rejected')` |
| `evidence_note` | `TEXT` | por qué se propone (título, cita) |
| `created_at`, `decided_at` | `DATETIME` | `decided_at` obligatorio si `accepted` |

```sql
CONSTRAINT ck_equivalence_distinct CHECK (source_node_id <> target_node_id);
CONSTRAINT uq_equivalence_pair UNIQUE (source_node_id, target_node_id);
CONSTRAINT ck_equivalence_decided CHECK (status <> 'accepted' OR decided_at IS NOT NULL);
```

Usos (los tres, no uno):

1. **Re-atribuir el banco**: `curriculum_mappings` de preguntas y `learning_errors` se re-apuntan del
   nodo publicado al común aceptado. Las equivalencias `proposed` **no** se aplican solas.
2. **Cobertura**: qué porcentaje del temario común está cubierto por material de cada programa
   publicado.
3. **Enriquecimiento**: cuando una convocatoria nueva publica un tema que no está en el común, la
   equivalencia contra el programa publicado existente es la prueba de que es nuevo, y el tema entra
   con `origin_kind='enrichment'`.

### 5.8 Invariantes que el modelo hace cumplir

| # | Invariante | Cómo |
|---|---|---|
| I1 | El temario común es **uno solo** con versiones | `curricula` con `kind='common'` y `code='informatica-c1'`; una versión `active` (índice parcial) |
| I2 | **No hay copia del temario común** por convocatoria | no existe FK de nodo a convocatoria; las particularidades son filas de ajuste |
| I3 | Una convocatoria a lo sumo tiene **un** temario común de estudio | índice único parcial `role='primary'` |
| I4 | Nodo publicado ≠ nodo común, pero ambos viven en la misma tabla | `curriculum_version_id` + `curricula.kind`; la equivalencia cruza los dos mundos |
| I5 | Un tema con material **no** se puede retirar | FK `curriculum_mappings ON DELETE RESTRICT` (se conserva) |
| I6 | Un tema **nunca** se borra al borrar la convocatoria que lo motivó | `origin_convocation_version_id ON DELETE SET NULL` |
| I7 | La numeración del temario común es estable por versión; renumerar = versión nueva | `UNIQUE(curriculum_version_id, path)`; `official_code` no es única (ADR-005 sigue vigente) |
| I8 | Todo ajuste tiene cita oficial | `evidence_quote` NOT NULL + CHECK de longitud |
| I9 | Una versión `active` no se edita | regla de servicio + prueba |

### 5.9 Las consultas que el producto necesita, y que el modelo hace fáciles

**«En qué convocatorias aparece este tema»** (pantalla de ficha de tema):

```sql
SELECT conv.code, conv.title
FROM convocation_curriculum_refs r
JOIN convocation_versions conv ON conv.id = r.convocation_version_id
WHERE r.role IN ('primary', 'complementary')
  AND r.curriculum_version_id IN (
      SELECT id FROM curriculum_versions WHERE curriculum_id = :informatica_c1
  )
  AND NOT EXISTS (
      SELECT 1 FROM convocation_curriculum_adjustments a
      WHERE a.ref_id = r.id
        AND a.kind = 'omitted'
        AND a.curriculum_node_id IN (:nodo, :sus_bloques_ancestros)
  )
ORDER BY conv.published_at DESC;
```

**Temario efectivo de una convocatoria** (lo que se estudia, con sus particularidades):
ref `primary` → versión → árbol de nodos, aplicando `renamed`/`renumbered` en presentación y
`omitted` para excluir. `weighted` se usa al componer simulacros.

**Progreso**:
- por tema y por bloque: agregación de `attempts`/`learning_errors` sobre **nodos comunes**;
- por convocatoria: los nodos de la versión referenciada que no están omitidos; el porcentaje se
  calcula, no se guarda (igual que la cobertura hoy).

### 5.10 Lo que **no** cambia

| Pieza | Estado |
|---|---|
| `oppositions`, `convocation_versions` | sin cambios de esquema |
| `exam_parts`, `exam_rules` | sin cambios: siguen colgando de la convocatoria (formato y penalización son suyos) |
| `question_sets`, `question_versions`, `option_versions`, claves, evidencias, explicaciones | sin cambios de esquema: siguen apuntando a nodos por `curriculum_mappings` |
| `study_sessions`, `attempts`, `learning_errors`, `review_items` | sin cambios de esquema; la sesión sigue perteneciendo a una convocatoria (para sus reglas), pero el contenido se mide en nodos comunes |
| `document_versions`, `document_sections`, `evidence_spans`, RAG | sin cambios; `curriculum_mappings` sigue siendo el puente |
| Siembra idempotente por `path`, retirada bloqueada por material, citas obligatorias | se conservan |

### 5.11 Alternativas descartadas (y por qué)

| Alternativa | Por qué no |
|---|---|
| **Etiqueta N:M `tema ↔ convocatoria` sin versiones** (lo que sugería la duda original «¿un tema puede pertenecer a varias convocatorias?») | no guarda el programa publicado como evidencia, no permite ponderación ni renumeración con cita, y no da historia: si el temario cambia, la convocatoria vieja cambia con él |
| **Copiar el temario por convocatoria** (estado actual) | 40 × 50 = 2.000 nodos; cada corrección se repite 50 veces; el banco de preguntas no se comparte |
| **Tabla única `curricula` sin versiones** | una convocatoria ya publicada vería cambiar su temario sin aviso; se pierde la trazabilidad que el producto exige en todo lo demás |
| **Clave natural del tema por título** | los títulos se reformulan entre convocatorias; fue exactamente el fallo que ADR-005 documentó con `official_code` |
| **Tabla aparte para los temas añadidos** | reintroduce la copia por convocatoria que la decisión prohíbe; el enriquecimiento va al común con procedencia (§5.4) |
| **Guardar el avance de forma agregada y editable** | la cobertura y el avance ya se calculan en el producto actual; guardarlos es tener dos verdades |

## 6. Migraciones necesarias

### 6.1 Estrategia

- **Una migración de esquema y datos**: `0021_temario_comun_y_referencias`, `down_revision =
  "0020_changes_and_derivatives"` (cabeza actual comprobada con `alembic heads`).
- **Rol único y reversible**: crea lo nuevo, rellena, aprieta y elimina lo viejo. Su `downgrade` deja
  la base exactamente en `0020` (lo prueba `apps/api/tests/integration/test_migrations_downgrade.py`).
- **El contenido del temario común no va en la migración**: va en un fixture con procedencia +
  siembra idempotente (§6.7), igual que los perfiles oficiales (ADR-006). Una migración no debe
  inventar 40 títulos.
- La base viva está en `0004`; la cadena completa (`0005`…`0021`) se aplica igual. Antes de migrar
  datos reales: copia de `opofuente.sqlite3` (y su `-wal`/`-shm`) con la aplicación parada, como dice
  `docs/OPERACION.md` §3.

### 6.2 Pasos exactos

**A. Crear la estructura** (cinco tablas nuevas + tres índices parciales):

1. `curricula` — único en `code`; `CHECK` de `kind`.
2. `curriculum_versions` — FK `curriculum_id` RESTRICT, FK `supersedes_id` SET NULL, único
   `(curriculum_id, version_no)`, único `code`, `CHECK` de `status`; índice parcial
   `uq_curriculum_version_single_active`.
3. `convocation_curriculum_refs` — FKs CASCADE/RESTRICT, único `(convocation, version)`, índice
   parcial `primary` y `official`, `CHECK` de `role`.
4. `convocation_curriculum_adjustments` — FKs CASCADE/RESTRICT, único
   `(ref_id, curriculum_node_id, kind)`, `CHECK` de `kind` y de coherencia de columnas.
5. `curriculum_equivalences` — dos FK RESTRICT a `curriculum_nodes`, `CHECK` de `relation`,
   `status`, `confidence` y `decided_at`.

**B. Abrir `curriculum_nodes` en caliente**: `op.add_column("curriculum_version_id", nullable=True)`
y `origin_kind` NOT NULL con `server_default='base'`, `origin_convocation_version_id` nullable.
La columna nueva queda **sin FK todavía**: la FK y el NOT NULL entran en el paso D, cuando ya no hay
ningún NULL.

**C. Rellenar (datos, determinista, sin inventar nada)**:

1. Por cada `convocation_versions` que tenga nodos:
   - `curricula` nueva: `code = <convocation.code> || '-programa'`, `kind='published'`,
     `name = convocation.title`;
   - `curriculum_versions`: `version_no=1`, `code = <code> || '-v1'`, `status='active'`,
     `title = convocation.title`, `source_reference = convocation.source_reference`;
   - `UPDATE curriculum_nodes SET curriculum_version_id = <esa versión> WHERE
     convocation_version_id = <esa convocatoria>`;
   - `convocation_curriculum_refs` nueva con `role='official'` y
     `source_reference = convocation.source_reference`.
2. Crear el temario común **vacío y en borrador**: `curricula(code='informatica-c1', kind='common',
   group_code='C1', family='informatica', name='Temario común de informática C1')` y su
   `curriculum_versions(v1, status='draft', source_reference='minicerebro/temario-c1.md, sha256
   50d8fa7f…dcea')`. **Sin nodos**: los pone el fixture y **la siembra es la que publica** la versión
   (`draft` → `active`) cuando el recuento cuadra (§6.7). La migración no decide qué convocatorias son
   de informática C1: la ref `primary` del TAI también la crea la siembra, porque es una decisión de
   producto, no de esquema.
3. Comprobación dura antes de seguir: `SELECT count(*) FROM curriculum_nodes WHERE
   curriculum_version_id IS NULL` **debe ser 0**; si no, la migración falla ruidosamente.

**D. Cerrar (reconstrucción de la tabla, porque SQLite no altera restricciones)**:

`op.batch_alter_table("curriculum_nodes", recreate="always", naming_convention=…)`:

- `curriculum_version_id` → NOT NULL con FK `ON DELETE CASCADE` (nombre `fk_curriculum_node_version`);
- `UNIQUE(curriculum_version_id, path)` con nombre `uq_curriculum_node_path`;
- índice `ix_curriculum_node_version` sobre `curriculum_version_id`;
- **antes de quitar la columna vieja**, `drop_index("ix_curriculum_convocation")` y
  `drop_constraint("uq_curriculum_path", type_="unique")` (si se quita la columna antes, sus índices
  se quedan apuntando a algo que no existe);
- `drop_column("convocation_version_id")`;
- se mantienen `ix_curriculum_parent`, `parent_id`, `ck_node_type`, `ck_node_depth`,
  `ck_node_position` y las dos propiedades nuevas (`origin_kind`, `origin_convocation_version_id`).

**E. Fuera de la migración**: fixture + siembra del contenido (§6.7) y, en una tarea aparte,
equivalencias y re-atribución del banco (§5.7).

### 6.3 Reglas del relleno que importan

1. **No se inventa ningún dato**: los programas publicados conservan su título, su código, su
   referencia y sus nodos; el común nace vacío hasta que se siembra del temario fuente.
2. **Los `id` de los nodos no cambian**: es lo que mantiene vivos `curriculum_mappings` y
   `learning_errors` (§4.2).
3. **Ninguna convocatoria pierde su programa**: cada una que publicaba temario recibe su versión
   `published` y su ref `official`.
4. **Ninguna fila se borra** en el camino de subida. La única eliminación es la columna
   `convocation_version_id` de `curriculum_nodes`, cuyo contenido ya vive en la ref `official`.

### 6.4 Qué pasa con Guardia Civil y Celador (material fuera de alcance)

- **No se borran.** Se migran como cualquier otra convocatoria: programa `published` + ref
  `official`.
- **No son estudiables** en la aplicación nueva porque **no tienen ref `primary`** al temario común.
  La zona del alumno filtra por ref `primary`; la administración los sigue viendo como evidencia.
- No se les asigna ningún tema común a mano: si algún día se decidiera, sería un enlace explícito con
  cita, no una invención de la migración.

### 6.5 `downgrade` de `0021`

1. Reconstruir `curriculum_nodes` con `convocation_version_id` nullable + FK nombrada.
2. Rellenarla desde `convocation_curriculum_refs` con `role='official'` →
   `curriculum_versions` → nodos (`UPDATE … SET convocation_version_id = r.convocation_version_id`).
3. Comprobar que no queda ningún NULL; si queda, **fallar**: significa que un nodo no tenía programa
   publicado y no se puede devolver a una convocatoria sin inventarla.
4. Volver a `NOT NULL`, recrear `uq_curriculum_path` e `ix_curriculum_convocation` y, **antes** de
   quitar la columna nueva, quitar su FK (`fk_curriculum_node_version`), su índice
   (`ix_curriculum_node_version`) y su unicidad (`uq_curriculum_node_path`); después, `drop_column`
   de `curriculum_version_id`, `origin_kind` y `origin_convocation_version_id`.
5. Borrar en orden inverso: `curriculum_equivalences`, `convocation_curriculum_adjustments`,
   `convocation_curriculum_refs`, `curriculum_versions`, `curricula`.

Consecuencia honesta: **el `downgrade` se lleva por delante el temario común y sus referencias** (son
datos de esta funcionalidad). No puede deshacer la re-atribución de preguntas: esa operación va en su
propia tarea, con su informe y su inverso probado (§5.7), y solo puede ejecutarse **después** de que
`0021` esté estable.

### 6.6 Notas de SQLite (lo que ya dolió en este repositorio)

- `ALTER TABLE` en SQLite **no** añade ni quita restricciones: el paso D es una **recreación**
  (`batch_alter_table(recreate="always")`), como en `0006` y `0007`.
- Las FK actuales de `curriculum_nodes` **no tienen nombre**; la recreación exige que lo tengan
  (lo documenta `0007`). Hay que pasar `naming_convention` al batch, no confiar en la reflexión.
- `PRAGMA foreign_keys=ON` está activo en toda conexión (`db.py`); la recreación se hace con las
  claves desactivadas por Alembic y se comprueba al final con `PRAGMA foreign_key_check`.
- La base usa WAL: la copia previa incluye `-wal` y `-shm`, no solo el `.sqlite3`.

### 6.7 Fixture y siembra del contenido (fuera de la migración, mismo contrato que los perfiles)

| Pieza | Dónde | Qué |
|---|---|---|
| Fixture | `fixtures/curricula/informatica-c1.v1.json` | 5 bloques, 40 temas, `path`, `official_code`, `title`, `source_reference` por bloque; `referenced_by: [{convocation_code: 'tai-age-2025', role: 'primary', source_reference: 'ANEXO V, apartado 3'}]` |
| Generador | `apps/api/opofuente/tools/build_curriculum_fixtures.py` | construye el fixture desde `temario-c1.md` con su sha256 y comprueba que los 40 temas están (como `build_profile_fixtures.py` con los perfiles) |
| Siembra | ampliar `apps/api/opofuente/tools/seed_profiles.py` con el temario común (mismo `--check`) | idempotente por `path`; pone los 40 temas en la versión `draft`, **la publica (`active`) solo si el recuento cuadra** (5 bloques / 40 temas / 45 nodos), crea la ref `primary` del TAI con su cita y falla en `--check` si hay cambios pendientes |
| Puerta | `scripts/gates.ps1` pasos 15–17 | ya ejecuta siembra + `--check` + fixtures contra fuentes: el temario entra en la misma puerta |

Por qué así: el contenido tiene procedencia y se verifica contra la fuente (ADR-006), y la migración
no se convierte en un almacén de títulos que nadie puede revisar.

### 6.8 Verificación de la migración (antes de declararla hecha)

| Comprobación | Criterio |
|---|---|
| Subir desde vacío | `alembic upgrade head` en directorio temporal (paso 13 de las puertas) |
| Subir desde `0004` (la base viva) | sobre **copia**, no sobre la viva; termina en `0021` |
| Bajar y volver a subir | `upgrade head → downgrade 0020 → upgrade head` sin error y con los mismos recuentos |
| Recuentos antes/después | 235 nodos antes = 235 nodos después; **cada** convocatoria con nodos tiene su ref `official` (2 en la base viva, 3 con los fixtures actuales); 0 nodos sin versión; 0 filas huérfanas |
| Integridad | `PRAGMA foreign_key_check` vacío |
| Prueba nueva | `test_migrations_0021.py` (patrón de `test_migrations_0012.py`): estructura, backfill, NOT NULL, `downgrade` restaurando `convocation_version_id` |
| Siembra posterior | el temario común queda `active` con 5 bloques / 40 temas / 45 nodos y el TAI con ref `primary`; `--check` en verde |
| Copia previa | fichero `.sqlite3` + `-wal` + `-shm` guardados y verificados antes de tocar la base real |

### 6.9 Orden de implementación (cuando David apruebe)

1. Modelos SQLAlchemy + migración `0021` + `test_migrations_0021` + `downgrade` (Nivel 2).
2. Fixture del temario + generador + siembra + puertas (Nivel 2).
3. Equivalencias TAI publicado → común y re-atribución del banco, con informe por fila (Nivel 2).
4. API y contrato: rutas del temario común, particularidades y «aparece en» (Nivel 2).
5. Interfaz: índice del temario común, ficha de tema con convocatorias, avance (Nivel 2).

Cada paso es reversible y deja las pruebas en verde; ninguno toca la base viva sin copia previa.

## 7. Lo que sigue abierto para David (no bloquea el modelo)

El modelo de §5 es el mismo tanto si el temario canónico tiene 33 temas como si tiene 40: lo único
que cambia es el fixture. Por eso se puede implementar la migración sin esperar estas respuestas.
Recomendación por defecto, que se aplica si no se dice lo contrario:

| # | Pregunta | Recomendación |
|---|---|---|
| O1 | ¿El temario común v1 es el de `temario-c1.md` (**5 bloques, 40 temas**) y el TAI 2025 queda como programa publicado + equivalencias? | **Sí.** Es la fuente que la especificación ya llama «el temario único» y la que las bases reales de 2026 piden |
| O2 | ¿La zona del alumno enseña **solo** el temario común y el programa publicado se queda en administración? | **Sí.** Es lo que pide el rediseño (alumno ve temario, no fuentes) y evita dos verdades |
| O3 | ¿Se re-atribuyen al común las preguntas y los fallos ya existentes, o se dejan bajo el programa publicado? | **Re-atribuir** con equivalencias aceptadas, con informe por fila y copia previa; lo dudoso se queda como está y se revisa |
| O4 | ¿Las convocatorias nuevas de `c1.txt` se importan en esta tanda? | **No todavía**: primero el temario común; las convocatorias son su propia tarea |

## 8. Impacto en el código, el contrato y la interfaz (medido)

| Zona | Ficheros | Qué cambia |
|---|---|---|
| Modelos | `infrastructure/db_models.py` (9 referencias a `convocation_version_id`) | `CurriculumNodeRecord` cambia de FK; cinco tablas nuevas |
| Repositorio de perfiles | `infrastructure/profile_repository.py` (13 referencias) | `_sync_curriculum` siembra por versión de temario; `get_curriculum` deja de ser «nodos de la convocatoria» |
| Clasificación y cobertura | `classification_repository.py` (3), `document_coverage.py` (1) | las consultas cruzan `curriculum_version_id` en lugar de `convocation_version_id` |
| Otros repositorios | `question_repository.py` (5), `study_repository.py` (3), `search_repository.py` (3), `readiness_repository.py` (1) | filtros por nodo/tema, sin cambio semántico |
| Servicios | `study_service.py` (9), `question_service.py` (4), `auto_study_service.py` (1) | la sesión sigue en su convocatoria; el contenido se resuelve contra el temario común |
| Dominio | `domain/profiles.py`, `domain/questions.py` | `Profile` gana el temario referenciado |
| API y contrato | `api/routes/profiles.py`, `classification.py`, `library.py`, `reviews.py`, `search.py`; `packages/contracts/openapi.json` + `src/openapi.d.ts` | rutas nuevas y campos nuevos; `/convocations/{id}/curriculum` se mantiene devolviendo el **programa publicado** para no romper lo que ya llama |
| Interfaz | 16 ficheros (`CurriculumTree.tsx`, `ProgramPage.tsx`, `features/study/*`, `api/profiles.ts`…) | el árbol pasa a ser el común; la ficha de tema gana «en qué convocatorias aparece» |
| Pruebas | 28 ficheros tocan el temario | todas se actualizan; las que cuentan nodos por convocatoria cambian de pregunta a «nodos de la versión»; nuevas: `test_migrations_0021`, `test_temario_comun`, `test_equivalencias`, y contrato de las rutas nuevas |
| Puertas | `scripts/gates.ps1` | sin pasos nuevos: la siembra, `--check`, fixtures contra fuentes y migración desde cero ya existen |

## 9. Pantallas de esta tanda

### 1. Índice del temario común (`/temario`)
- [ ] Árbol bloque → tema, en el orden oficial del temario común (5 bloques, 40 temas)
- [ ] Búsqueda que **perdona tildes**
- [ ] Marca visible de lo estudiado (nodo común)
- [ ] Nada de nombres de fuentes, rutas de Windows ni versiones

### 2. Ficha de tema
- [ ] Texto del tema y apuntes, si existen
- [ ] **En qué convocatorias aparece** (según §5.9; esto es lo que hace útil el temario único)
- [ ] Particularidades de la convocatoria cuando se llega desde una (omitido, renumerado, renombrado)
- [ ] Navegación anterior / siguiente
- [ ] Marcar como estudiado, con fecha

### 3. Avance
- [ ] Por bloque y total, sobre nodos comunes
- [ ] Qué queda, ordenado por lo que falta

### 4. Convocatorias (solo lectura)
- [ ] Lista con administración, año y grupo
- [ ] Ficha con sus bases y sus particularidades de temario
- [ ] «Estudiar con el temario común» (lo que crea la referencia si no existe, con su cita)

## 10. Estados obligatorios

- [ ] Vacío · [ ] Cargando · [ ] Error · [ ] Sin permiso

## 11. Fuera de alcance de esta tanda

- **Test y simulacros con penalización**: no todavía, aunque el formato ya está documentado.
- **Supuesto práctico**: no.
- **Ciclo del alumno** (resultado, repaso, fallos): no.
- **Cualquier oposición que no sea de informática**.
- **El banco de 53,7 GB**: no es la fuente de este producto. La fuente es `F:\aprendizaje\empleo-informatica\`.
- **Importar las 10 convocatorias de `c1.txt`**: tarea propia, después del temario común.
- **Implementar §6 sin revisión de este documento**: no se empieza hasta que David lo apruebe.

## 12. Qué no se toca

- **`main`**: está en `F:\temp-opofuente\opofuente-restaurado`. Desde este worktree no se toca.
- **Las 85 ramas locales**: no se abre ni se borra ninguna.
- **El banco de `E:\`** (53,7 GB, junction): no es fuente del producto, no se lee para este modelo.
- **Guardia Civil y Celador**: sus datos se conservan migrados como programas publicados (§6.4); no se
  borran.
- **Secretos**: nada de `.env`, credenciales ni datos del propietario en git. Los fixtures son
  sintéticos o citas de fuentes públicas.

## 13. Riesgos

| Riesgo | Mitigación |
|---|---|
| **El banco de preguntas no aparece** bajo el temario común hasta re-atribuirlo | es la tarea 3 de §6.9 y el criterio de O3; sin ella, la ficha de tema del común está vacía de preguntas |
| **Dos verdades**: programa publicado y temario común | la zona del alumno enseña solo el común; el publicado es evidencia de administración (O2) |
| **El temario de 40 temas no coincide 1:1 con los 33 del TAI** | equivalencias con `relation` (`equivalent`/`subset`/`superset`/`partial`) y revisión humana; lo dudoso no se aplica |
| **Migración SQLite a medias** | una sola migración transaccional, recreación con `batch`, `downgrade` probado, copia previa verificada y recuentos antes/después |
| **Un nodo con material bloquea una retirada** | se conserva de serie (FK RESTRICT, ADR-007); la siembra informa el conflicto en vez de forzarlo |
| **La base viva está en `0004`** | la cadena completa se prueba desde vacío **y** desde copia de la viva antes de tocar nada |
| **85 ramas y dos worktrees** | solo se trabaja en `rescate/fase0-2026-10-26` de este worktree; nada de `main` |
| **Crecimiento del temario común** | versiones: crece una versión nueva y cada convocatoria se actualiza cuando se decide, no sola |

## 14. Puertas antes de dar una pantalla o una migración por buena

1. `uv run pytest` en verde (unitarias, integración y contrato).
2. Migración desde vacío, desde `0004` (copia) y `downgrade` + `upgrade` sin error.
3. `alembic check` sin diferencias entre modelos y esquema; `PRAGMA foreign_key_check` vacío.
4. Siembra idempotente (`--check`) y fixtures contra las fuentes (`build_*_fixtures --check`).
5. Contrato: `export_openapi --check` y `npm run contracts:check` en verde.
6. `ai-design-check` o la lista de diez de las recetas, para interfaz.
7. Ojos frescos: subagente sin historial con este fichero y una captura.

## Aprobación de David (2026-11-04)

Aprobado **tal cual**, sin cambios:

- **§5** — modelo de datos: temario común versionado y convocatorias que lo referencian.
- **§6** — migración `0021` con su downgrade.
- **O1** sí: el temario común v1 es `temario-c1.md` (5 bloques, 40 temas) y el TAI 2025 queda como programa publicado con equivalencias.
- **O2** sí: el alumno ve solo el temario común; el programa publicado queda en administración.
- **O3** re-atribuir: las preguntas y fallos existentes se re-apuntan al común con equivalencias aceptadas, informe por fila y copia previa.
- **O4** no todavía: primero el temario común; las convocatorias nuevas son su propia tarea.

La siguiente sesión empieza por **B-001**. No hay que esperar nada más.

