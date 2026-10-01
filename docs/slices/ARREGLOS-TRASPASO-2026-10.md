# Arreglos del traspaso de material (octubre de 2026)

Rama `arreglos-traspaso-material`, desde `main` (906b760). Atiende los defectos de la §4 y el
rendimiento de la §5.2 de `docs/TRASPASO-DE-MATERIAL-A-CLAUDE.md` (escrito por el agente de material).
No toca la rama `fase0-reconciliacion-artefacto-representacion` ni el trabajo sin guardar del otro
agente (pantalla de promoción en `apps/web`).

## Qué he construido

| § | Defecto | Arreglo |
| --- | --- | --- |
| 4.1 | Cada sección daba **una** evidencia recortada a 1.200 caracteres; además se leían solo los primeros 400.000 caracteres de la representación. Se guardaba el 36,7 % del texto extraído. | `domain/evidence.py` trocea cada sección en evidencias de ≤1.200 (corte preferente en párrafo, línea, frase, espacio), con offsets exactos. El texto que no cae en ninguna sección también se cita. Se lee la representación entera. |
| — | **Nuevo, no estaba en el traspaso**: un `.txt` con más de 500 párrafos (`MAX_BLOCK_SECTIONS`) perdía todo lo que venía después. | Lo cubre la regla del texto fuera de secciones. |
| 4.2 | El detector lee 4.096 bytes; si el corte parte un carácter UTF-8 y el bloque tiene un byte que Windows-1252 no define, un `.txt` legible se declaraba binario. | `detect_format` acepta un carácter partido **al final** (decodificador incremental UTF-8); cualquier otro byte inválido sigue siendo binario. |
| 4.3 | En un `.md` cada sección era solo la línea del encabezado: el cuerpo no se citaba. | La sección llega hasta el siguiente encabezado; el preámbulo es su propio tramo; un `#` dentro de un bloque de código no es encabezado; sin encabezados, se trocea por bloques. |
| 4.5 | `POST /question-sets/{id}/parse` con `kind=answer_key` daba 500 (IntegrityError). Causa: la misma pregunta dos veces en una plantilla, por un número repetido o por dos preguntas en la misma posición. En el segundo caso, además, la clave caía en silencio en cualquiera de las dos. | Número repetido → aviso `key_position_repeated`, vale la primera. Posición con varias preguntas → aviso `key_position_ambiguous`, no se aplica. `save_key` rechaza repetidas como invariante (409/422), no 500. |
| 4.6 | Barajas de Anki modernas (esquema 18): `notetypes.config` es protobuf y los nombres de campo salían como «campo 1». | Se leen de la tabla `fields`; el JSON queda para colecciones antiguas. |
| 4.7 | No había forma de retirar material obsoleto. | `POST /documents/{id}/versions/{vid}/withdraw` (motivo obligatorio), `.../reinstate` (vuelve a candidata) y `POST /documents/{id}/withdraw` (archiva todas las versiones vivas). Nada se borra; todo queda auditado. El corpus ya excluía `withdrawn`. |
| 4.8 | «344 filas → 110 temas» por CSV. | **No reproducible**: 344 filas sintéticas (comas, comillas, `;`, saltos de línea, reimportando preguntas existentes) asignan las 344 al tema correcto. Lo que sí faltaba: el informe no decía cuántos temas aplicó la columna (`mapped_to_topics` es la catalogación automática y daba 0). Campo nuevo `topics_from_column`. |
| 5.2 | Búsqueda 1,5-5,7 s con 700.277 fragmentos. | Ver abajo. |

### Búsqueda

Medido sobre una copia íntegra de `F:\OpoFuente\datos\opofuente.sqlite3` (01-10-2026, 700.277
fragmentos, `quick_check` ok), en Linux:

- `corpus_revision` hacía `count(*)` y dos `max()` sin índice en **cada** búsqueda: 0,61 s. Ahora:
  último `rowid` + recuento de versiones por estado: 0,0001 s.
- La consulta cruzaba cada coincidencia con su versión y documento antes de ordenar («datos» → 217.107
  coincidencias). Ahora el índice ordena por `bm25` en una ventana (`max(400, limit·40)`) y solo esa
  ventana se cruza; si los filtros la dejan corta, se repite sin ventana. **Resultado idéntico.**

| consulta | antes | después |
| --- | --- | --- |
| artículo 24 protección de datos derechos | 2,30 s | 0,25 s |
| modelo entidad relación | 1,23 s | 0,11 s |
| sistema operativo planificación de procesos | 1,23 s | 0,12 s |
| ley 39/2015 plazos | 1,22 s | 0,12 s |
| silencio administrativo | 0,71 s | 0,03 s |
| cortafuegos perimetral | 0,56 s | 0,01 s |

Comparación de identidad: 10 consultas × 3 filtros (sin filtro, por oposición, `limit` 25) → los mismos
fragmentos en el mismo orden con el código anterior y con este. Total 27,3 s → 2,9 s.

## Cómo fluye la información

Extracción (`extractors/*`) → representación con secciones → promoción (`document_repository._derive_structure`)
→ `evidence_cuts` por sección + `uncovered_ranges` para el resto → evidencias ordenadas por posición →
disparador FTS5 → búsqueda (`search_repository.search`, ventana + reintento).

## Ficheros y migraciones

Sin migraciones. Nuevos: `domain/evidence.py`, `tests/unit/test_evidence_domain.py`. Cambiados:
`document_repository.py`, `extractors/base.py`, `extractors/text_files.py`, `extractors/anki.py`,
`question_service.py`, `question_repository.py`, `question_models.py`, `library_service.py`,
`domain/documents.py` (`WITHDRAWABLE_FROM`), `api/routes/library.py`, `api/library_schemas.py`,
`api/routes/questions.py`, `api/question_schemas.py`, `search_repository.py`, `opofuente_testing/synthetic_documents.py`
(colección Anki con config protobuf), contrato OpenAPI y tipos regenerados, un dato de prueba de la web.

## Patrones y decisiones aplicadas

- Lo ambiguo se informa, no se adivina (plantilla con posición compartida).
- La elegibilidad sigue en el dominio (`corpus_eligible`); la ventana de la búsqueda no la adelanta.
- Retirar es reversible y auditado; no hay borrado.

## Seguridad y privacidad

Sin cambios de superficie salvo tres rutas de escritura bajo las mismas cabeceras y comprobaciones de
origen que el resto de `/documents`. La copia de la base usada para medir estaba fuera del repositorio.

## Puertas ejecutadas y resultado

En Linux (la máquina de trabajo no es el Windows del propietario), por tandas:

- `ruff format` / `ruff check`: limpio.
- `mypy`: 1 error preexistente y solo de Linux (`st_file_attributes`, atributo de Windows).
- `pytest` unitarias + contrato + integración (las 47): todo pasa salvo **7 preexistentes de Linux**
  (6 de `test_safe_paths`/`test_safe_inputs` y `test_import::…agotan_los_intentos`: la limpieza de rutas
  solo reconoce rutas de Windows). Las 7 fallan igual en `main` sin estos cambios.
- `export_openapi --check` y `contracts:check`: sincronizados.
- Web: `typecheck`, `lint` y `vitest` (225 pruebas): verde.
- **No ejecutado**: E2E (Playwright) ni `gates.ps1` en Windows. Hay que pasar `./scripts/gates.ps1`
  en el equipo del propietario antes de fusionar.

## Prueba manual

1. Pegar o ingerir un `.md` con encabezados y cuerpo largo → promocionar → `GET /document-versions/{id}/evidence`:
   el cuerpo aparece troceado en evidencias de ≤1.200.
2. `POST /documents/{id}/withdraw {"reason": "…"}` → la búsqueda deja de devolverlo; `reinstate` + `accept` lo devuelven.

## Limitaciones conocidas

- **Lo ya guardado no cambia.** Las evidencias se crean al promocionar; el material de antes conserva
  lo que tenía (el 97,4 % ya se recuperó con el apaño). No hay herramienta para regenerar evidencias de
  versiones existentes: las preguntas citan evidencias por id (`ON DELETE RESTRICT`) y rehacerlas
  rompería esas citas.
- El tope `max_representation_chars` (2.000.000) sigue: un documento más largo se trunca al extraer.
  Es configuración, no un defecto.
- §4.4.2 (`mark-supersedes` solo dentro del mismo documento) y §4.4.3 (de `superseded` no se vuelve)
  siguen igual: son reglas de diseño; retirar cubre el caso práctico.
- El título que sanea `31/1995` a `31-1995` (§4.8) no se ha tocado: viene del saneado de nombres de
  fichero.
- El índice FTS5 indexa `id` (UUID), `text` **y** `normalized_text` (el mismo texto dos veces).
  Quitarlo reduciría el índice, pero exige migración y reconstrucción; no se ha hecho.

## Qué se rompe si cambias X

- Si `evidence_cuts` deja de garantizar ≤`MAX_EVIDENCE_CHARS`, `_evidence` lanza invariante.
- Si quitas el reintento sin ventana de `search`, un filtro restrictivo esconde resultados (lo caza
  `test_la_ventana_del_indice_no_esconde_lo_que_responde_tras_los_filtros`).
- `corpus_revision` ya no cuenta fragmentos: si algún día se borran fragmentos sin tocar versiones,
  la revisión no cambiaría.

## Qué criticaría un revisor senior

- Promocionar un PDF de 2.000 páginas crea ahora miles de evidencias en una transacción: más lento y
  más índice que antes (es el precio de no perder el texto).
- Las evidencias de texto fuera de sección no cuelgan de ninguna sección (`section_id` nulo): un mapeo
  de **sección** no las alcanza.
- La ventana de búsqueda es una constante sin medir en el Windows del propietario.

## Segunda tanda (1 de octubre, tarde): lo que destaparon las puertas y las claves

| origen | defecto | arreglo |
| --- | --- | --- |
| puertas en Windows | `review.spec.ts:186` fallaba siempre (también en `main`): dos motores proponen el mismo tema para el mismo material y sus botones tenían el mismo nombre accesible. | El nombre accesible de cada acción lleva valor y confianza («… · Tema del programa: 4.1, 100 %»). Prueba E2E verde en Linux. |
| puertas en Windows | `gates.ps1` imprimió OK en las puertas 17 y 18 con sus comandos fallando. No reproducido. | `Invoke-OpoFuenteStep` lee el código global, trata excepciones como fallo y escribe el código en cada OK; `gates.ps1` empieza comprobando que el intérprete detecta un `exit 3`. Probado con PowerShell 7. |
| informe de claves | Una pregunta sin entrada en la clave activa entraba en la práctica por tema y se corregía como «excluida». | Práctica por tema y diagnóstico eligen solo lo que la clave activa corrige; la práctica cuenta lo que deja fuera. Los exámenes no cambian. |
| informe de claves | No había ruta para enlazar la plantilla oficial a una clave existente. | `POST /question-sets/{id}/answer-keys/{kid}/source`: compara plantilla y clave pregunta a pregunta (una discrepancia → 409; <95 % confirmado → 409); `null` desenlaza salvo la activa de un examen oficial. Auditado. |
| informe de claves | La alineación por número daba «100 %» con 93 líneas sobre 135 preguntas que reiniciaban la numeración, y solo miraba las 200 primeras. | `key_alignment` (dominio): una línea cuenta solo si su número es de una sola pregunta; la nota es lo peor entre encajar y cubrir. |

**Para el propietario**: con la alineación nueva, un conjunto con secciones que numeran desde 1 ya
no recibe una plantilla por número (antes la recibía mal). Las claves de TAI 2025 que se activaron a
mano el 1 de octubre se comprobaron por enunciado contra el fichero oficial, así que no les afecta.
