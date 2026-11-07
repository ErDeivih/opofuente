# OpoFuente — modelo de dominio y datos

## 1. Reglas generales

- UUID como clave pública; enteros internos solo si mejoran FTS.
- Todos los timestamps en UTC.
- Texto original y texto normalizado se almacenan separados.
- `created_at`, `updated_at` y, cuando proceda, `deleted_at`.
- Enumeraciones validadas en dominio y `CHECK` en SQLite.
- JSON solo para payloads variables no consultados; relaciones importantes son tablas.
- No usar cascadas destructivas desde oposición a documentos compartidos.

## 2. Oposiciones y convocatorias

### `oppositions`

`id`, `code` único (`tai-age`, `gc-cabos-guardias`), `name`, `description`, `active`.

### `convocation_versions`

`id`, `opposition_id`, `code`, `title`, `official_url`, `published_at`, `exam_date`, `status`,
`source_document_version_id`, `supersedes_id`, `created_at`.

Estados: `draft`, `active`, `superseded`, `archived`. Solo una activa por oposición.

## 2 bis. Temario común versionado (S13)

La decisión es de ADR-018: **un solo temario común** y convocatorias que lo **referencian**, sin
copiar sus nodos. El programa publicado de cada convocatoria se conserva como evidencia, pero el
alumno estudia el común.

### `curricula`

`id`, `code` único (`informatica-c1`), `kind` (`common` / `published`), `name`, `group_code`,
`family`, `created_at`, `updated_at`.

- `common`: el temario único que estudian las convocatorias de informática C1.
- `published`: el programa publicado de una convocatoria concreta, conservado tal cual (B-001). No se
  copia al común: se enlaza con una referencia.

### `curriculum_versions`

`id`, `curriculum_id`, `version_no`, `code` único, `title`, `status` (`draft` / `active` /
`superseded`), `source_reference`, `created_at`.

Una versión **activa no se edita** (I9): un cambio de contenido es otra versión. La v1 se publica
desde un fixture con huella sha256 y solo si los recuentos coinciden (5 bloques / 40 temas / 45
nodos).

### `curriculum_nodes`

Árbol por `parent_id`: bloque, tema y epígrafe. Campos: `id`, `curriculum_version_id`, `parent_id`,
`node_type`, `official_code`, `title`, `description` (los apuntes de la ficha), `position`, `path`,
`depth`, `origin_kind`, `origin_convocation_version_id`.

`UNIQUE(curriculum_version_id, path)`. El `path` materializado acelera la lectura, pero la identidad
del nodo pertenece a **su versión**; una convocatoria no tiene nodos propios, tiene una referencia.

### `convocation_curriculum_refs`

`id`, `convocation_version_id`, `curriculum_version_id`, `role`, `source_reference`, `created_at`.

Papeles: `primary` (el temario que estudia), `official` (el programa publicado de esa convocatoria)
y `complementary` (temario adicional). Una convocatoria tiene como mucho una referencia `primary`.
La convocatoria **referencia** la versión y su cita; no la copia.

### `convocation_curriculum_adjustments`

`id`, `ref_id`, `curriculum_node_id`, `kind` (`omitted` / `renamed` / `renumbered` / `weighted`),
`official_code_override`, `title_override`, `weight`, `evidence_quote`, `created_at`.

`UNIQUE(ref_id, curriculum_node_id, kind)`. Se aplican **al componer** el temario efectivo de esa
convocatoria: `omitted` excluye el nodo y su subárbol; `renamed` y `renumbered` solo cambian lo que
se muestra; `weighted` no toca el árbol y se usará en simulacros. Borrar el ajuste devuelve el
temario completo sin tocar la versión.

### `curriculum_equivalences`

`id`, `source_node_id` (nodo del programa publicado), `target_node_id` (nodo del común),
`relation_type` (`equivalent` / `subset` / `superset` / `partial`), `confidence`, `status`
(`proposed` / `accepted` / `rejected`), `evidence_note`, `created_at`, `decided_at`.

`UNIQUE(source_node_id, target_node_id)`. Solo las `accepted` se aplican al material; una equivalencia
no implica automáticamente el mismo nivel ni preguntas intercambiables.

### `curriculum_study_marks`

`id`, `curriculum_node_id` único, `marked_at`, `note`.

Marca local del alumno (una por nodo). La FK es `CASCADE`: un nodo sin material se puede borrar y su
marca se va con él. El **avance** por bloque y total se calcula al leer a partir de las marcas y de la
actividad real (preguntas mapeadas y fallos); no se guarda ningún porcentaje.

El material se sigue asignando a nodos con `curriculum_mappings` (§9), que es `RESTRICT`: un nodo con
material asignado no se retira sin decidir antes qué pasa con ese material (ADR-007).

## 3. Ingestión y archivos

### `ingestion_batches`

`id`, `kind`, `source_path_display`, `mode`, `status`, contadores, `started_at`, `finished_at`,
`manifest_hash`, `error_summary`.

### `ingestion_items`

Una entrada encontrada: `id`, `batch_id`, `relative_path`, `original_name`, `size_bytes`, `mtime`,
`media_type`, `artifact_id`, `status`, `issue_count`. No guardar una ruta absoluta sensible en logs.

### `source_artifacts`

`id`, `sha256` único, `size_bytes`, `media_type`, `storage_key`, `first_seen_at`, `quarantine_status`.
El mismo artefacto puede aparecer en varios lotes/rutas.

### `artifact_origins`

`artifact_id`, `origin_type` (`file`, `url`, `paste`, `generated`), ubicación mostrable, fecha de
acceso y metadatos de descarga. URLs conservan final URL y cadena limitada de redirecciones.

### `extracted_representations`

`id`, `artifact_id`, `extractor_name`, `extractor_version`, `kind`, `language`, `status`, `quality`,
`text_storage_key`, `page_count`, `warnings_json`, `created_at`.

Una nueva versión del extractor crea otra representación; no sobrescribe.

### `import_issues`

`id`, `batch_id`, `item_id`, `code`, `severity`, `safe_message`, `details_json`, `resolved_at`,
`resolution`.

## 4. Documentos y versiones

### `logical_documents`

Representa la obra: `id`, `canonical_title`, `document_type`, `authority_tier`, `owner_scope`,
`canonical_identifier`, `created_at`.

`owner_scope`: `public`, `private_user`, `generated`. Un documento privado nunca se promueve a público
por clasificación automática.

### `document_versions`

`id`, `logical_document_id`, `artifact_id`, `representation_id`, `version_label`, `published_at`,
`valid_from`, `valid_to`, `retrieved_at`, `language`, `status`, `supersedes_id`, `rights_status_id`,
`official_url`, `content_hash`, `approved_at`, `approved_by`.

Estados: `candidate`, `accepted`, `outdated`, `superseded`, `withdrawn`, `rejected`.

### `rights_statuses`

`id`, `code`, `license_name`, `license_url`, `attribution`, `commercial_reuse`, `sharing`, `notes`,
`review_status`. Desconocido es un valor explícito y conservador.

### `document_sections`

Árbol estructural: página, título, capítulo, artículo, disposición, sección técnica. `id`,
`document_version_id`, `parent_id`, `section_type`, `label`, `title`, `position`, `page_start`,
`page_end`, offsets y estructura adicional limitada.

### `evidence_spans`

Unidad recuperable: `id`, `document_version_id`, `section_id`, `ordinal`, `text`, `normalized_text`,
offsets, páginas, `token_count`, `quality`, `citation_label`, `index_status`.

## 5. Clasificación y cobertura

### `classification_proposals`

`id`, `subject_type`, `subject_id`, `axis`, `proposed_value`, `confidence`, `alternatives_json`,
`evidence_json`, `engine_name`, `engine_version`, `status`, `decided_at`, `decision_note`.

Estados: `pending`, `accepted`, `rejected`, `superseded`, `auto_applied_provisional`.

### `curriculum_mappings`

`id`, `curriculum_node_id`, `subject_type`, `subject_id`, `coverage_type`, `depth`, `confidence`,
`status`, `source_proposal_id`, `approved_at`.

Puede mapear documento, sección, evidencia o pregunta. Cobertura se calcula; no se almacena como un
número editable.

### `collections` y `collection_items`

Organización personal virtual. Un ítem puede estar en varias colecciones sin duplicar bytes.

## 6. Preguntas y respuestas

### `question_sets`

`id`, `title`, `opposition_id`, `convocation_version_id`, `set_type`, `model_code`, `held_at`,
`source_document_version_id`, `status`.

Tipos: `official_exam`, `private_bank`, `practice`, `generated_batch`.

### `question_versions`

`id`, `question_set_id`, `stable_key`, `version_no`, `stem`, `question_type`, `position`, `is_reserve`,
`status`, `origin_type`, `source_section_id`, `supersedes_id`, `created_at`.

Tipos de pregunta iniciales: `single_choice`, `multi_mark_error`, `true_false`, `free_text_reference`.
Solo `single_choice` y `multi_mark_error` necesitan experiencia completa en el MVP.

### `option_versions`

`id`, `question_version_id`, `stable_key`, `label`, `text`, `position`. La posición y la clave estable
son distintas para poder relacionar modelos A/B con opciones reordenadas.

### `answer_key_versions`

`id`, `question_set_id`, `source_document_version_id`, `version_no`, `status`, `supersedes_id`,
`published_at`, `approved_at`.

### `answer_key_entries`

`answer_key_version_id`, `question_version_id`, `outcome`, `correct_option_keys_json`, `notes`.
`outcome`: `keyed`, `annulled`, `unanswered`, `conflicting`.

### `question_evidence`

`question_version_id`, `evidence_span_id`, `role` (`stem`, `correct`, `distractor`, `explanation`),
`claim`, `status`.

### `question_explanations`

Versionadas por pregunta y opción: texto, origen, estado de verificación y modelo/prompt si fue
generado.

## 7. Sesiones y aprendizaje

### `study_sessions`

`id`, `opposition_id`, `convocation_version_id`, `mode`, `configuration_json`, `status`, timestamps y
resultado agregado. La configuración se congela al iniciar.

### `session_questions`

Orden y versión exacta de pregunta, clave aplicable al inicio, sección/parte y temporización.

### `attempts`

Respuesta del usuario, `is_correct`, puntos, duración, confianza declarada, resultado anterior si hubo
recalculo y timestamps. No se sobrescribe tras una clave nueva: se añade una evaluación revisada.

### `attempt_evaluations`

`attempt_id`, `answer_key_version_id`, `outcome`, `score`, `evaluated_at`, `supersedes_id`, `reason`.

### `learning_errors`

`id`, `attempt_id`, `curriculum_node_id`, `concept_label`, `cause`, `user_note`, `status`, recurrencia.
Causas: `knowledge`, `confusion`, `reading`, `time`, `calculation`, `ambiguous`, `other`.

### `review_items`

`id`, vínculo a error/pregunta/tarjeta, estabilidad/dificultad si se adopta FSRS, `due_at`, historial y
estado. La primera versión puede usar intervalos deterministas; cualquier cambio de algoritmo debe
versionarse.

## 8. RAG, derivados y cambios

### `rag_queries`

Pregunta, filtros, corpus revision, proveedor/modelo, configuración y métricas. El texto puede ser
privado; no se incluye en logs operativos.

### `retrieval_hits`

`query_id`, `evidence_span_id`, scores léxico/vectorial/rerank, posición y si entró en contexto.

### `generated_answers` y `answer_claims`

Respuesta versionada, estado (`supported`, `partial`, `insufficient`, `failed`) y afirmaciones. Cada
claim se relaciona con evidencias mediante `claim_evidence`.

### `derived_artifacts`

Resumen, explicación, tarjeta o pregunta generada. Guarda generador, prompt template version, modelo,
entradas exactas, estado de revisión y `needs_review`.

### `dependency_edges`

Grafo dirigido `from_type/from_id -> to_type/to_id` para invalidar derivados cuando cambia una
evidencia. Las aristas se crean durante generación/importación, no se infieren después.

### `change_sets`

Versiones anterior/nueva, diff por sección, estado de revisión y efecto. `affected_derivatives` lista
el resultado del recorrido de dependencias.

## 9. Auditoría y trabajos

### `audit_events`

Acciones que alteran autoridad, clasificación, respuesta o versión: actor local, acción, objeto,
antes/después sanitizado, timestamp y correlation ID. No registrar contenido completo.

### `jobs`

Definidos en arquitectura. Payload con referencia a entidades, no blobs.

## 10. Invariantes

1. Un `SourceArtifact.sha256` identifica exactamente unos bytes.
2. Un artefacto aceptado nunca cambia de bytes.
3. Una pregunta oficial necesita documento de origen oficial; una etiqueta no basta.
4. Una clave oficial necesita una plantilla oficial enlazada y aprobada.
5. Solo una versión de clave puede estar activa por set/modelo, pero las anteriores permanecen.
6. Un intento conserva pregunta y configuración tal como se presentaron.
7. Recalcular crea evaluación nueva.
8. Un contenido generado nunca es autoridad A/B.
9. Todo claim mostrado como respaldado tiene al menos una evidencia aceptada y vigente para el filtro.
10. Borrar un lote no borra un artefacto compartido mientras queden referencias.

