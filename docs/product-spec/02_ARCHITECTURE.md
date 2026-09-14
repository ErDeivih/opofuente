# OpoFuente — arquitectura técnica

## 1. Forma del sistema

Monorepo independiente con backend y frontend separados, ejecutados localmente:

```text
Browser en localhost
      |
      v
React SPA ----HTTP/JSON----> FastAPI (127.0.0.1)
                               |-- SQLite + FTS5
                               |-- almacén de artefactos
                               |-- Qdrant local
                               |-- worker persistido
                               |-- adaptadores OCR / LLM / embeddings
```

No usar Electron en el MVP. Una PWA local evita empaquetado temprano. El backend abre el navegador al
arrancar en distribución posterior; durante desarrollo se usan procesos separados.

## 2. Estructura obligatoria del nuevo repositorio

```text
opofuente/
  AGENTS.md
  README.md
  pyproject.toml
  uv.lock
  package.json
  package-lock.json
  .env.example
  .gitignore
  docs/
    architecture/
    decisions/
    slices/
  apps/
    api/
      opofuente/
        main.py
        config.py
        api/
        domain/
        application/
        infrastructure/
        workers/
      tests/
    web/
      src/
        app/
        pages/
        features/
        components/
        api/
        styles/
      tests/
  packages/
    contracts/
  scripts/
  fixtures/
    synthetic/
  data/                 # gitignored
```

El frontend no importa código Python. `packages/contracts` contiene OpenAPI generado y tipos
TypeScript derivados; la fuente de verdad del contrato es FastAPI/OpenAPI.

## 3. Capas backend

### Domain

Entidades, value objects, estados y reglas puras. No importa FastAPI, SQLAlchemy, Qdrant, proveedores
LLM ni sistema de archivos.

### Application

Casos de uso y puertos: importar lote, aceptar propuesta, crear sesión, contestar, buscar, responder,
versionar y exportar. Gestiona transacciones mediante `UnitOfWork`.

### Infrastructure

SQLAlchemy, repositorios, almacenamiento por hash, parsers, OCR, FTS5, Qdrant y proveedores externos.
Cada integración implementa un puerto del dominio/aplicación.

### API

Rutas, DTO, validación, códigos HTTP y streaming de eventos. No contiene reglas de puntuación ni
clasificación.

### Worker

Consume trabajos persistidos con bloqueo/lease. Es idempotente: reintentar no duplica documentos,
preguntas o vectores.

## 4. Frontend

Organización por funcionalidad. Las páginas componen features; no acceden directamente a `fetch`.
TanStack Query gestiona estado remoto. El estado visual local puede usar React; no añadir Redux en el
MVP.

Componentes transversales:

- `SourceBadge`, `ConfidenceBadge`, `VersionBadge`;
- `EvidenceCitation`;
- `JobProgress`;
- `BulkReviewTable`;
- `EmptyState`, `ErrorState`, `ConfirmDialog`;
- `QuestionCard`, `AnswerReview`;
- `CurriculumTree` y `CoverageCell`.

## 5. Persistencia

### SQLite

- `PRAGMA foreign_keys=ON` en toda conexión.
- WAL para lectura concurrente.
- migraciones Alembic obligatorias.
- transacciones cortas; no mantener una transacción durante OCR/LLM.
- soft delete solo donde el historial lo exige; artefactos se recuentan por referencias.

### FTS5

Índice de texto derivado y reconstruible. Guardar IDs de fragmento y texto normalizado. Las tablas FTS
no son fuente de verdad ni reciben escrituras directas desde rutas.

### Qdrant local

Colección versionada por modelo de embedding y dimensión. El punto contiene `evidence_span_id` y filtros
de oposición, convocatoria, fuente, idioma, estado y vigencia. Si cambia el modelo se crea/reconstruye
otra colección; nunca mezclar vectores incompatibles.

### Archivos

```text
data/
  artifacts/sha256/ab/cd/<hash>
  extracted/<representation-id>/...
  qdrant/
  exports/
  backups/
  tmp/
  opofuente.sqlite3
```

Las escrituras usan archivo temporal, `fsync` cuando proceda y renombrado atómico. Comprobar que la
ruta resuelta permanece dentro de `data`. Los nombres originales son metadatos, nunca rutas de destino.

## 6. Trabajos

Estados: `queued`, `leased`, `running`, `succeeded`, `failed`, `cancel_requested`, `cancelled`.

Campos mínimos: tipo, payload validado, progreso, paso, intentos, error seguro, timestamps, lease y
clave de idempotencia. Al arrancar, trabajos con lease expirado vuelven a cola. Cancelar se comprueba
entre páginas/unidades y nunca deja registros a medias.

Tipos iniciales:

- `inventory_source`;
- `ingest_batch`;
- `extract_artifact`;
- `classify_document`;
- `parse_question_set`;
- `build_fts`;
- `embed_spans`;
- `diff_versions`;
- `invalidate_derivatives`;
- `export_backup`.

## 7. Integraciones y puertos

```python
ArtifactStore
DocumentExtractor
OcrEngine
ClassificationEngine
EmbeddingProvider
VectorIndex
Reranker
LanguageModel
WebSourceFetcher
Clock
IdGenerator
```

Proporcionar implementaciones `disabled`/`noop` cuando una función opcional no está configurada. La
aplicación debe importar, buscar por FTS y estudiar preguntas sin LLM, OCR ni vectorial.

## 8. Configuración

Prioridad: valores seguros -> fichero local -> variables de entorno. Nunca guardar claves desde el
frontend en `localStorage`. El backend expone capacidad/configuración sanitizada, no secretos.

Variables previstas:

```text
OPOFUENTE_DATA_DIR
OPOFUENTE_HOST=127.0.0.1
OPOFUENTE_PORT=8765
OPOFUENTE_LOG_LEVEL=INFO
OPOFUENTE_LLM_PROVIDER=disabled|openai_compatible|ollama
OPOFUENTE_LLM_BASE_URL
OPOFUENTE_LLM_MODEL
OPOFUENTE_LLM_API_KEY
OPOFUENTE_EMBEDDING_PROVIDER=local|openai_compatible|disabled
OPOFUENTE_EMBEDDING_MODEL
OPOFUENTE_TESSERACT_PATH
```

## 9. Observabilidad local

Logs JSON rotativos sin contenido de documentos, preguntas privadas, prompts completos ni claves.
Cada petición y trabajo tiene correlation ID. Pantalla de diagnóstico exporta versiones, capacidades y
errores sanitizados. No integrar Sentry ni telemetría remota.

## 10. Decisiones de rendimiento

- hash y copia por streaming;
- extracción página a página;
- lotes pequeños para embeddings;
- paginación por cursor o `limit/offset` estable en UI local;
- virtualizar tablas grandes;
- no cargar blobs por API; servirlos mediante endpoint con rangos y disposición segura;
- caché de consulta basada en versión de corpus y parámetros, no solo texto de pregunta.

## 11. Desarrollo y calidad

- Python: Ruff, mypy estricto sobre código de producción, pytest.
- TypeScript: `strict`, ESLint, Vitest, Testing Library, Playwright.
- OpenAPI generado y comprobado contra tipos frontend.
- Pre-commit opcional; CI obligatorio aunque el despliegue sea local.
- Nunca relajar las herramientas para hacer pasar un slice.

