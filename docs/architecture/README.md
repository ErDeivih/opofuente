# Arquitectura — notas de implementación

La arquitectura **vigente** es
[`docs/product-spec/02_ARCHITECTURE.md`](../product-spec/02_ARCHITECTURE.md). Este directorio
contiene solo notas de cómo se ha materializado, sin contradecirla.

> `docs/product-spec/` es una copia literal del paquete de especificación. Dos de sus enlaces
> (`00_START-HERE.md` y `09_SECURITY-PRIVACY-AND-RIGHTS.md`) apuntan a documentos de investigación
> que viven en el repositorio original (`../ideas/opposition-study-rag/…`), no en este. No se han
> reescrito para no alterar la copia; los hechos y reglas de derechos que citan siguen aplicando.

## Forma del sistema

```text
Navegador (127.0.0.1:5173 dev / 4173 preview)
   |
   v
React SPA  --HTTP/JSON-->  FastAPI (127.0.0.1:8765)
                              |-- SQLite + FTS5
                              |-- almacén de artefactos por SHA-256   (S02)
                              |-- Qdrant local                        (S09)
                              |-- worker persistido                   (S02)
                              |-- adaptadores OCR / LLM / embeddings   (S03/S09)
```

## Capas del backend

| Capa | Ruta | Puede importar |
|---|---|---|
| Domain | `apps/api/opofuente/domain/` | solo biblioteca estándar |
| Application | `apps/api/opofuente/application/` | dominio y puertos propios |
| Infrastructure | `apps/api/opofuente/infrastructure/` | application, domain, SQLAlchemy, Alembic |
| API | `apps/api/opofuente/api/` | application, domain, FastAPI |
| Arranque | `apps/api/opofuente/main.py` | todo lo anterior (composición explícita) |
| Worker | `apps/api/opofuente/workers/` | application, domain, infrastructure (S02) |

El dominio no conoce FastAPI, SQLAlchemy, Qdrant ni el sistema de archivos.

## Decisiones de S00 que condicionan lo siguiente

1. **Estado en `app.state`, no en singletons.** `create_app(settings)` permite levantar una
   aplicación completa contra un directorio temporal; es lo que usan las pruebas y el E2E. En S01
   las dependencias de sesión deben seguir este patrón (`request.app.state.session_factory`).
2. **OpenAPI es la fuente de verdad.** `packages/contracts/openapi.json` se genera desde FastAPI y
   `packages/contracts/src/openapi.d.ts` se deriva de él. Un cambio de contrato que no se regenere
   rompe la puerta de contrato y el typecheck del frontend.
3. **Cadena de middlewares ASGI puros**, de dentro hacia fuera: CORS → cabeceras de seguridad →
   comprobación de Origin → identificador de correlación. Se evita `BaseHTTPMiddleware` para no
   romper SSE cuando llegue S09.
4. **Capacidades honestas.** `CapabilityStatus` distingue `enabled` (comprobado), `disabled`,
   `unavailable`, `configured_unverified` y `planned`. La UI no puede mostrar como operativo lo que
   no lo está.
5. **Logs con lista blanca de campos.** El formateador descarta cualquier `extra` no declarado en
   `SAFE_EXTRA_KEYS`, de modo que un descuido al registrar no filtra contenido.
6. **El esquema de los errores se publica con su media type real.** FastAPI documenta el modelo de
   una respuesta adicional bajo el media type de la ruta (`application/json`), pero OpoFuente sirve
   todos los errores como `application/problem+json` (RFC 9457). `api/openapi.py` mueve el `$ref`
   ya generado por FastAPI al media type real, sin escribir nombres de componente a mano; la
   prueba de contrato comprueba el esquema **y** el cuerpo servido. Como consecuencia, cada ruta
   documenta también su 500 (`ProblemDetail`), que es el tipo base del problema que usa el cliente.

## Deuda técnica

La deuda obligatoria, con su slice y su criterio de cierre, está en
[`docs/DEBT.md`](../DEBT.md). No se implementa fuera del slice indicado.

## Notas de S01 (perfiles y programa)

- **Tablas nuevas:** `oppositions`, `convocation_versions`, `curriculum_nodes`, `exam_parts` y
  `exam_rules` (ver [ADR-005](../decisions/ADR-005-modelo-de-perfiles-y-reglas-de-examen.md)). La
  restricción de «una sola convocatoria activa por oposición» y la de «una sola oposición activa»
  son **índices únicos parciales de SQLite**, no validaciones del código.
- **Identidad del programa:** `(convocation_version_id, path)`. `official_code` guarda la numeración
  publicada y, donde la convocatoria no numera (los subniveles del temario de GC), la secuencia
  dentro del padre; por eso no es único.
- **Procedencia:** cada parte y cada regla guardan `evidence_quote`, la cita literal de la fuente
  oficial; la herramienta que construye los fixtures comprueba que la cita existe en el documento
  descargado (hash verificado) antes de escribir nada
  ([ADR-006](../decisions/ADR-006-fixtures-desde-fuentes-oficiales.md)).
- **Sin datos inventados:** lo que la convocatoria no publica se queda `NULL` en la base y se
  devuelve `null` en la API. En TAI, `options_per_question` es nulo porque el anexo V no dice
  cuántas alternativas tiene cada pregunta. La cobertura documental se declara `null` hasta S05.
- **Siembra idempotente por CLI** (`opofuente.tools.seed_profiles`), no en el arranque: crear datos
  como efecto secundario de arrancar el servidor esconde cambios.

## Notas de S02 (artefactos, inventario y lotes)

- **Almacén por contenido.** `data/artifacts/sha256/ab/cd/<hash>` (02_ARCHITECTURE §5). El
  `storage_key` guardado en la base es `sha256/ab/cd/<hash>`, relativo a `DataPaths.artifacts`
  (que es `data/artifacts`): la ruta final es la documentada, sin segmentos repetidos. La escritura
  es `<uuid>.part` en `data/tmp` + `fsync` + `os.replace`, de modo que un artefacto nunca aparece a
  medias.
- **Un artefacto, varios orígenes.** `source_artifacts.sha256` es único y `artifact_origins` guarda
  cada sitio donde se ha visto el contenido (`UNIQUE(artifact_id, display_location)`). Dos ficheros
  idénticos con nombres distintos son **un** artefacto y **dos** orígenes.
- **Dos fases.** El inventario (`kind=inventory`, `mode=read_only`) solo lee y describe; la
  importación (`kind=import`, `mode=copy`) copia lo que el usuario confirma. `ingestion_batches.source_root`
  guarda la ruta real **en local** y no se publica nunca por la API (solo `source_path_display`).
- **Cola persistida con lease.** `jobs` (02_ARCHITECTURE §6) con `lease_owner`, `lease_expires_at`,
  `attempts`, `max_attempts` e índice único **parcial** `uq_jobs_idempotency_alive`. El worker es una
  tarea de asyncio del proceso (`workers/job_worker.py`), ejecuta los manejadores en un hilo y
  recupera al arrancar los trabajos cuyo lease venció.
- **Cancelación cooperativa.** El manejador comprueba `cancelled()` entre unidades y lanza
  `JobCancelledError`; el worker lo cierra como `cancelled`. Un trabajo con cancelación pedida y sin
  empezar **también** se reclama: tiene que pasar por el worker para cerrar el lote con su informe.
- **Capacidades comprobadas de verdad.** `IngestionCapabilityProvider` escribe en el directorio de
  artefactos y pregunta a `WorkerLiveness` si la tarea está corriendo; hasta que arranca de verdad,
  la capacidad se declara `unavailable`, no `enabled`.
- **Rutas seguras.** `infrastructure/safe_paths.py` concentra `is_within`, `resolve_within`,
  `safe_display_name` y las rutas abreviadas: ni la copia ni el informe pueden salirse de la raíz
  elegida ni publicar la ruta real del usuario.
