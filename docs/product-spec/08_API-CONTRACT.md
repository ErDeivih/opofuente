# OpoFuente — contrato HTTP API v1

## 1. Convenciones

- Base: `/api/v1`.
- JSON UTF-8, snake_case.
- Fechas ISO-8601 UTC.
- IDs UUID string.
- Errores RFC 9457 `application/problem+json` con `type`, `title`, `status`, `detail`, `instance`,
  `code`, `correlation_id`, `field_errors` opcional.
- Paginación: `limit` (1–100) y cursor opaco donde el orden puede cambiar; offset solo en tablas
  administrativas estables.
- Escrituras peligrosas admiten `Idempotency-Key`.
- Concurrencia: `version`/ETag en recursos revisables; conflicto HTTP 409.
- API local sin login en MVP, pero valida `Origin` y solo escucha en loopback.

## 2. Sistema

```text
GET  /health/live
GET  /health/ready
GET  /capabilities
GET  /settings
PATCH /settings
GET  /diagnostics/export
```

`capabilities` indica OCR/vector/embedding/LLM configurado y degradaciones, nunca secretos.

## 3. Oposiciones

```text
GET  /oppositions
GET  /oppositions/{id}
POST /oppositions/{id}/activate
GET  /oppositions/{id}/convocations
GET  /convocations/{id}
GET  /convocations/{id}/curriculum
GET  /curriculum-nodes/{id}
GET  /curriculum-nodes/{id}/coverage
```

Los perfiles oficiales se siembran por migración/fixture versionado. El MVP no ofrece editor libre de
reglas de examen.

## 4. Inventario e ingestión

```text
POST /inventories
GET  /inventories/{id}
POST /inventories/{id}/confirm-import
POST /ingestion-batches/files          multipart, límites estrictos
POST /ingestion-batches/paste
POST /ingestion-batches/url
GET  /ingestion-batches
GET  /ingestion-batches/{id}
POST /ingestion-batches/{id}/cancel
POST /ingestion-batches/{id}/retry
GET  /ingestion-batches/{id}/items
GET  /ingestion-batches/{id}/issues
GET  /ingestion-batches/{id}/report
```

Crear inventario recibe ruta local solo desde loopback y resuelve/valida en backend. La respuesta de
importación devuelve job ID.

## 5. Trabajos y eventos

```text
GET  /jobs
GET  /jobs/{id}
POST /jobs/{id}/cancel
GET  /events                         Server-Sent Events
```

Eventos: `job.updated`, `batch.updated`, `review.count_changed`, `source.changed`. SSE es mejora P1;
polling con backoff es fallback obligatorio.

## 6. Revisión y clasificación

```text
GET  /classification-proposals
GET  /classification-proposals/{id}
POST /classification-proposals/{id}/accept
POST /classification-proposals/{id}/reject
POST /classification-proposals/bulk-decision
POST /classification-decisions/{id}/undo
GET  /review-groups
```

Bulk request incluye IDs explícitos, decisión, overrides, versión esperada y nota. Respuesta lista
éxitos/conflictos; no es todo-o-nada si algunos recursos cambiaron, pero cada ítem es transaccional.

## 7. Biblioteca

```text
GET  /documents
POST /documents
GET  /documents/{id}
PATCH /documents/{id}
GET  /documents/{id}/versions
POST /documents/{id}/versions/{version_id}/accept
POST /documents/{id}/versions/{version_id}/mark-supersedes
GET  /document-versions/{id}
GET  /document-versions/{id}/content
GET  /document-versions/{id}/original
GET  /document-versions/{id}/sections
GET  /document-versions/{id}/mappings
POST /document-versions/{id}/mappings
DELETE /curriculum-mappings/{id}
GET  /duplicate-clusters
POST /duplicate-clusters/{id}/resolve
```

`original` soporta Range y `Content-Disposition: inline` solo para MIME seguros; resto attachment.

## 8. Búsqueda y RAG

```text
POST /search
POST /rag/queries
GET  /rag/queries/{id}
GET  /rag/queries/{id}/retrieval
GET  /evidence-spans/{id}
```

Request de búsqueda: texto, opposition/convocation, curriculum IDs, authority, version mode, fecha,
document IDs, strategy (`lexical|hybrid`).

Request RAG añade estilo (`brief|teach|compare`) y `allow_private_sources`. No permite activar fuentes
obsoletas implícitamente. Response sigue el esquema de `05_RAG-EVIDENCE-AND-EVALUATION.md`.

## 9. Preguntas y claves

```text
GET  /question-sets
POST /question-sets
GET  /question-sets/{id}
GET  /question-sets/{id}/questions
POST /question-sets/{id}/parse
GET  /questions
GET  /questions/{id}
PATCH /questions/{id}
POST /questions/{id}/local-corrections
GET  /questions/{id}/evidence
POST /questions/{id}/report-issue
GET  /question-sets/{id}/answer-keys
POST /question-sets/{id}/answer-keys/{key_id}/activate
POST /answer-keys/{id}/mark-supersedes
```

No devolver claves/explicaciones en payload de pregunta de una sesión no corregida.

## 10. Estudio

```text
POST /study-sessions
GET  /study-sessions/{id}
POST /study-sessions/{id}/start
GET  /study-sessions/{id}/current-question
POST /study-sessions/{id}/answers
POST /study-sessions/{id}/navigate
POST /study-sessions/{id}/finish
GET  /study-sessions/{id}/result
GET  /study-sessions/{id}/review
POST /attempts/{id}/error-classification
GET  /reviews/due
POST /reviews/{id}/complete
POST /reviews/{id}/snooze
```

El servidor calcula puntuación. Request de respuesta incluye question ID, option keys, elapsed ms y
client sequence; el servidor comprueba que pertenece a la sesión y es la versión congelada.

## 11. Cambios y exportación

```text
GET  /change-sets
GET  /change-sets/{id}
POST /change-sets/{id}/confirm
GET  /change-sets/{id}/affected
POST /exports/markdown
POST /exports/anki-csv
POST /backups
GET  /backups
POST /backups/{id}/verify
POST /restore/validate
POST /restore/execute
```

Restaurar exige seleccionar backup validado, previsualización y creación automática de backup previo.

## 12. Seguridad del contrato

- CORS solo origen local configurado.
- protección CSRF/origin incluso sin login;
- límites por endpoint y tamaño;
- nombres de archivo solo para display;
- URLs y rutas nunca se pasan a shell;
- errores no exponen rutas completas, prompts, claves o contenido privado;
- `DELETE` material no se añade hasta diseñar retención/referencias; el MVP ofrece archivar.

## 13. Generación del cliente

OpenAPI es fuente de verdad. CI genera tipos TypeScript y falla si hay diff sin registrar. Los tests de
contrato comprueban ejemplos de error, paginación y ausencia de solución en sesiones activas.

