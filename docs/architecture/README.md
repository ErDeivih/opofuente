# Arquitectura — notas de implementación

La arquitectura **vigente** es
[`docs/product-spec/02_ARCHITECTURE.md`](../product-spec/02_ARCHITECTURE.md). Este directorio
contiene solo notas de cómo se ha materializado, sin contradecirla.

> `docs/product-spec/` es una copia literal del paquete de especificación. Dos de sus enlaces
> (`00_START-HERE.md` y `09_SECURITY-PRIVACY-AND-RIGHTS.md`) apuntan a documentos de investigación
> que viven en el repositorio original (`../ideas/opposition-study-rag/…`), no en este. No se han
> reescrito para no alterar la copia; los hechos y reglas de derechos que citan siguen aplicando.
>
> **Corrección sincronizada con el documento maestro** (15/09/2026, autorizada por el propietario):
> en `04_INGESTION-AND-CLASSIFICATION.md §3` la frase sobre formatos no extraíbles metía los
> ejecutables en `unsupported_preserved`, contradiciendo a §2, que pide omitirlos. El texto se
> corrigió aquí **y en el maestro** (`proptech-access-control/docs/opofuente/…`): ahora dice que los
> ejecutables se omiten por seguridad y que Office con macros, audio, vídeo, EPUB y PPTX se conservan
> sin ejecutar. Los dos ficheros son idénticos (mismo `sha256`), así que **no** es una desviación de
> la copia: es una corrección en origen. El resto del paquete sigue siendo copia literal.

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

## Notas de S03 (extractores, representaciones y entradas directas)

- **El formato lo decide el contenido.** `infrastructure/extractors/base.py::detect_format` mira los
  primeros bytes (magic bytes) y solo usa la extensión como señal secundaria: un `.pdf` que no es un
  PDF se trata por lo que es. Consecuencia práctica: la lista de lo que no se extrae se decide por
  familia detectada (`PRESERVED_FAMILIES`) **y** por sufijo (`PRESERVED_SUFFIXES`), porque un XLSX es
  un ZIP y no se quiere confundir con un contenedor expandible.
- **El ZIP no es un documento.** `plan()` devuelve `expand_zip` y el servicio lo expande en entradas
  propias del lote (`expanded`), de modo que el informe sigue contando entradas y no archivos
  internos. Un ZIP **dentro** de otro no se expande: se conserva (`unsupported_preserved`) según
  `max_zip_depth`, medido sobre la ruta persistida (`paquete.zip/inner.zip` → 2).
- **Representación = texto de un artefacto.** `extracted_representations` guarda metadatos (extractor
  y versión, tipo, calidad, avisos, secciones, `ocr_candidate`, `format_version`) y apunta al texto,
  que vive en `data/extracted/<id>/texto.txt` con su `estructura.json`. La clave lógica es
  `(artefacto, extractor, versión, tipo)`: volver a extraer no duplica y **otra versión sí crea otra**
  fila, que es lo que permitirá reprocesar cuando mejore un extractor.
- **Estados de entrada nuevos.** `ingestion_items` gana `extracted`, `unsupported_preserved`,
  `expanded` y `ocr_pending` (migración `0006`). «Terminado» significa siempre «no queda nada por
  hacer»: al acabar la copia, si queda algo por extraer, el lote vuelve a `queued` con un trabajo
  `extract_artifact` y solo entonces se cierra.
- **`unsupported_preserved` tiene su propio término en la ecuación** (`BALANCE_TERMS`,
  `preserved_unsupported`): conservar sin extraer no es copiar texto, y esconderlo dentro de `copied`
  habría hecho que el informe contara como leído algo que no se ha leído (DEBT-008).
- **Módulos de seguridad con una responsabilidad cada uno.**
  `infrastructure/safe_xml.py` (lxml endurecido: sin DTD, sin entidades, sin red, con tope de bytes),
  `infrastructure/safe_zip.py` (nombres, tamaños, ratio y profundidad **antes** de escribir nada) y
  `infrastructure/url_guard.py` (esquema, resolución DNS, listas negras de redes y conexión fijada a
  la IP comprobada). Los tres tienen pruebas negativas propias (`tests/unit/test_safe_inputs.py`).
- **El texto se lee por trozos.** `GET /representations/{id}/text` sirve slices con `offset`/`limit` y
  avisos; el modelo de lectura es `TextSlice` y el lector de la interfaz amplía solo si el usuario lo
  pide. Un documento largo no bloquea la pantalla ni la API.
- **Las representaciones se deduplican por artefacto y muestran sus rutas.** Si el lote trae el mismo
  contenido dos veces (`tema.pdf` y su copia), hay **una** representación con sus dos rutas: el lector
  no repite el mismo texto como si fueran documentos distintos.
- **La configuración de límites es real, no decorativa.** Cada ajuste nuevo de S03
  (`max_representation_chars`, `max_pdf_pages`, `max_zip_*`, `url_*`, `max_paste_bytes` y, tras la
  corrección, `max_text_bytes`, `max_json_bytes` y `max_image_bytes`) se usa en el código y está
  documentado en `.env.example`; los que no tenían uso se retiraron.

## Corrección de S03 (15/09/2026, tras la revisión del propietario)

Trece bloqueos, todos con prueba de regresión. Los que cambian la forma del sistema:

- **`domain/formats.py`**: la política de formatos (qué se rechaza, qué se conserva y qué firmas de
  ejecutable se reconocen) sale del registro de extractores y pasa al dominio, para que la copia y
  las entradas directas puedan rechazar un binario **antes** de guardarlo sin depender de
  infraestructura.
- **`ingestion_items` gana tres columnas** (migración `0007`): `container_depth` (profundidad de
  contenedor, dato persistido con el que se decide si un ZIP anidado se expande),
  `origin_type`/`origin_display` (procedencia **de esa entrada**, no del artefacto) y
  `representation_id` (enlace explícito entrada → representación). Sin el enlace, la lista de un lote
  unía por artefacto y enseñaba el texto producido en otro lote: el mismo contenido entrado como
  fichero deja `native_text` y entrado como texto pegado, `plain_text`.
- **El nombre original viaja a los extractores** (`plan(path, name=…)`): en el almacén el fichero se
  llama como su hash, así que la extensión con la que se aplica la política sale de la entrada.
- **La profundidad de contenedor sustituye al conteo de sufijos** (`nested_container_refusal`): un
  `paquete.zip/inner.bin` reconocido por contenido ya no se expande otra vez.
- **Lectura acotada por extractor** (`read_bounded`): el texto, el HTML y el CSV se leen hasta
  `max_text_bytes` (y avisan si hay más), el JSON que no cabe en `max_json_bytes` se declara en lugar
  de cargarse en memoria, y las imágenes se miden **leyendo su cabecera**, sin decodificarlas.
- **Las secciones se ajustan al texto final** (`clamp_sections`): invariante
  `0 ≤ char_start ≤ char_end ≤ char_count`, comprobada en `sections_are_consistent`.
- **Stubs locales de PyMuPDF** (`apps/api/typestubs/pymupdf/__init__.pyi`, en `mypy_path`): mypy
  estricto comprueba las llamadas a PyMuPDF **sin** apagar `disallow_untyped_calls` en ningún módulo
  (el paquete publica `py.typed` pero sin anotaciones).
- **`opofuente_testing`**: los constructores de documentos sintéticos y los dobles de prueba pasan a
  un paquete tipado y comprobado con mypy; `apps/api/tests` sale del `pythonpath`.

## Segunda corrección de S03 (15/09/2026)

Once defectos más, con dos cambios de forma:

- **Una sola puerta antes del almacén**: `application/storage_policy.py` decide qué contenido se
  admite (sufijo y firma) y la usan **todas** las vías de entrada —subida, descarga por URL, copia
  desde carpeta y miembros de ZIP—, antes de crear el lote y de copiar. El texto pegado queda fuera:
  lo escribe OpoFuente.
- **`item_representations`** (migración `0008`): la relación entrada→representación pasa de una clave
  ajena singular a una tabla de asociación con unicidad por pareja, para que el texto nativo, el OCR
  y las versiones de extractor convivan enlazados a la misma entrada. `ingestion_items.representation_id`
  desaparece.
- **Procedencia honesta**: la migración `0007` solo rellena el tipo de origen cuando no hay ambigüedad
  (un único origen registrado); con varios, queda `NULL` («no consta») en lugar de inventarse uno. La
  procedencia que ve el usuario sale de `origin_display` (URL saneada, título pegado), no de la ruta.
- **Escritura atómica** de `texto.txt` + `estructura.json` (temporal, `fsync`, `os.replace`) y
  **corte de lectura en frontera de carácter** (nunca dentro de un carácter UTF-8).
- **Los tramos se miden sobre texto normalizado**: cada extractor normaliza su pieza antes de
  calcular offsets (`_piece`), porque NFC puede acortarla.
- **`copied_bytes` mide presencia física** (`artifact_id IS NOT NULL`), no el resultado del
  procesamiento.
- **Sin exclusiones de Ruff nuevas**: los ayudantes de prueba generan sus PNG con `zlib`/`struct`, así
  que el stub de PyMuPDF no necesita constantes con nombre propio y el `per-file-ignore` de N816 se
  retiró.

## Tercera corrección de S03 (16/09/2026)

Cuatro defectos:

- **`read_bounded` conserva el bloque entero** cuando ya decodifica como UTF-8 y solo retrocede ante
  una secuencia incompleta **al final** (antes perdía un byte aunque el corte fuera válido).
- **CSV y JSON no colapsan espacios** (`_piece_literal`: solo `normalise_text`); HTML y DOCX mantienen
  el colapso, que ahí es presentación. Lo pide la regla del dominio: los datos no se reformatean.
- **`0009_repair_item_origin`**: una migración ya aplicada no se vuelve a ejecutar, así que corregir
  el fichero de `0007` no reparaba las bases que la habían ejecutado. La 0009 limpia la procedencia
  inventada cuando el artefacto tiene varios orígenes y recupera el tipo cuando es inequívoco; su
  `downgrade` no hace nada a propósito (no se reconstruye un dato inventado).
- **El texto pegado escribe su temporal antes de crear el lote**, así que un fallo de disco no deja un
  lote en `queued` sin nada que lo cierre.

## Cuarta corrección de S03 (16/09/2026)

- **`0010_recover_item_origin`**: la 0009 limpiaba de más (borraba el tipo de origen de **todas** las
  entradas de un artefacto con varios orígenes, incluidas las que constan). Como una migración ya
  aplicada no se reejecuta, la reparación va en una migración posterior: recupera el tipo cuando la
  procedencia visible de la entrada (`origin_display`) coincide exactamente con la de un origen del
  artefacto (`display_location`), y deja «no consta» cuando no coincide. La 0009 **no** se reescribe.
- **El recorte por bytes se decide por el motivo del error** (`unexpected end of data`), no por su
  posición: solo se retrocede ante una secuencia UTF-8 truncada al final. Un `0xFF` o una continuación
  inválida se entregan tal cual (recortar perdería contenido sin arreglar la decodificación).

## Quinta corrección de S03 (16/09/2026)

- **`0011_origin_identity_by_channel`**: la identidad de un origen es
  `(artifact_id, origin_type, display_location)`, no `(artifact_id, display_location)`. El mismo
  contenido que entra como fichero y como texto pegado con la **misma** etiqueta (`tema.txt` los dos)
  son dos orígenes: con la restricción vieja el segundo reutilizaba la fila del primero y su canal se
  perdía. `register_artifact` consulta el origen incluyendo el canal, y el `origin_type` pasa a `NULL`
  («no consta») cuando varias entradas comparten artefacto y etiqueta y ya no hay forma de saber qué
  canal trajo cada una: la recuperación de datos no adivina. La 0010 **no** se reescribe; el
  `downgrade` de la 0011 retira los orígenes duplicados por etiqueta y restaura la restricción
  anterior.
- **El corte por bytes mira lo que viene después del límite** (`LOOKAHEAD_BYTES`): un `0xC3` final en
  un fichero Windows-1252 no es una secuencia UTF-8 partida, es un `Ã`, y solo se retrocede cuando los
  bytes siguientes **completan** la secuencia. Así el límite mide bytes del fichero y el extractor
  declara `cp1252` en lugar de perder un carácter en silencio.

## Sexta corrección de S03 (16/09/2026)

- **La comprobación del corte pide solo los bytes que le faltan a la secuencia que cruza el límite**:
  la longitud se deduce del byte inicial (`_utf8_length`) en vez de tomar lo que cabe en una secuencia
  (`4 - len(parcial)`). Con `é` partido seguido inmediatamente de `€` o de un emoji, la versión
  anterior incluía el byte inicial del siguiente carácter, fallaba la decodificación y leía como
  CP-1252 un fichero UTF-8, con una `Ã` inventada al final.
- **El `downgrade` de `0011` no deja canales huérfanos**: conserva un origen por pareja
  `(artefacto, etiqueta)` —el de `id` menor en orden binario, criterio determinista y **no** temporal,
  porque el esquema no guarda la fecha de creación del origen— y después deja sin canal toda entrada
  cuya procedencia no esté respaldada por un origen existente con el mismo artefacto, etiqueta y canal.
  Antes, la entrada que había llegado como texto pegado conservaba `origin_type = 'paste'` con su
  origen ya borrado.
