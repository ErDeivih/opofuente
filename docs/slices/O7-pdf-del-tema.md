# O7 · PDF del tema completo

Estado: **implementado con la puerta unitaria verde y una puerta pendiente**. El renderizador deja de
estar «sin probar»: `test_topic_pdf_render.py` ejecuta PyMuPDF de verdad, y el bucle de `Story` tiene
ahora una guarda de terminación con su prueba. La descarga ya se puede pedir desde la pantalla del
tema. `9df85043f3a0` (`gates.ps1`, ESLint/tsc/build) sigue **sin ejecutar en este worktree** —se rechaza
aquí—, así que el cambio de la web **no está verificado** por ninguna puerta.

## Qué he construido

- Guarda de terminación del maquetador, `apps/api/opofuente/infrastructure/topic_pdf.py`: el bucle de
  `Story.place` deja de ser `while True` y pasa a `_maquetar_cuerpo(story, writer, cuerpo)`, que corta
  al llegar a `MAX_PAGINAS = 200` y lanza `CuerpoDemasiadoLargoError` (un `RuntimeError`). Los dos
  colaboradores entran por `Protocol` (`_Historia`, `_Escritor`), que es lo que permite probar el corte
  con dobles en vez de generar 200 páginas de PDF.
- Pruebas reales del renderizador, `apps/api/tests/unit/test_topic_pdf_render.py`: 10 pruebas que
  abren el PDF con PyMuPDF y comprueban texto extraído (título, cabecera, estado, pie «página 1 de 1»,
  cuerpo), el aviso de borrador, los metadatos del documento, el reparto en varias páginas con su
  «página i de total», un documento sin capítulos, un título con emoji y CJK, el orden de los capítulos
  y la guarda: con un `Story` que no termina nunca se lanza `CuerpoDemasiadoLargoError` exactamente
  después de `MAX_PAGINAS` intentos.
- Descarga desde la pantalla, `apps/web/src/features/student/DescargarPdf.tsx`: botón «Descargar el
  tema en PDF» en la cabecera del tema (solo si hay apuntes), con su aviso de estado y su error.
  Pide el PDF por `apiFetchBinary` —nuevo en `apps/web/src/api/client.ts`, hermano binario de
  `apiFetch`: misma base, mismas credenciales, mismos `ApiError`/`ApiUnavailableError`— y lo entrega al
  navegador con el nombre que manda el servidor.
- `filenameFromDisposition` en el cliente (forma `filename*=UTF-8''…` y `filename="…"`) y
  `Content-Disposition` añadido a `expose_headers` de CORS en `apps/api/opofuente/main.py`: sin eso el
  navegador no dejaba leer la cabecera y el nombre saneado del servidor no se podía usar.
- Reparto único del tema en capítulos: `apps/api/opofuente/application/topic_reading.py`.
  `read_by_chapters` ordena los apartados por el programa oficial y conserva el número global de cada
  uno. Lo comparten la pantalla de lectura y el PDF para que no puedan contar el tema de dos formas.
- Documento de exportación puro: `apps/api/opofuente/application/topic_pdf.py`.
  - `TopicPdfSection`, `TopicPdfChapter` y `TopicPdfDocument` con la cabecera de procedencia.
  - `markdown_to_html`, que interpreta el mismo subconjunto que `notesMarkdownParser.ts` (títulos,
    listas, tablas, citas, negrita, cursiva y código), escapa el HTML antes de dar formato y elimina
    las marcas `<!-- revisar: … -->`.
  - `build_topic_pdf_html`, con el aviso de borrador y los capítulos ordenados por posición.
  - `topic_pdf_filename`, que reduce código y título a ASCII, sin rutas, y recorta títulos largos.
- Renderizador PyMuPDF: `apps/api/opofuente/infrastructure/topic_pdf.py`.
  Maqueta con `Story`, compone el PDF en un `BytesIO`, estampa cabecera y pie en cada página
  (procedencia, estado y «página N de M»), añade metadatos y devuelve los bytes. No escribe disco.
- `texto_para_pdf` en `apps/api/opofuente/application/topic_pdf.py`: la cabecera y el pie se dibujan
  con la fuente base `helv`, que solo codifica Latin-1. La función conserva las letras acentuadas y
  sustituye lo que esa fuente no puede representar (guion largo, puntos suspensivos, comillas
  tipográficas, viñeta, espacios finos…) por su equivalente visible antes de medir y estampar, para
  que el ancho del texto alineado a la derecha coincida con lo que se dibuja.
- Caso de uso `StudentService.pdf(codigo)`: resuelve oposición, tema, bloque y apuntes; si no hay
  ningún capítulo lanza `NotFoundError` (404) en vez de fabricar un PDF vacío. Devuelve
  `StudentTopicPdf(filename, content)`.
- Ruta `GET /api/v1/student/topics/{codigo}/pdf` en `apps/api/opofuente/api/routes/student.py`.
  Responde `application/pdf` con `Content-Disposition: attachment; filename="…"` y
  `Cache-Control: private, no-store`.
- Contrato actualizado a mano en `packages/contracts/openapi.json` y
  `packages/contracts/src/openapi.d.ts` con la operación
  `student_topic_pdf_api_v1_student_topics__codigo__pdf_get`.
- Pruebas nuevas en `apps/api/tests/unit/test_topic_pdf.py` y en
  `apps/api/tests/integration/test_student_notes_api.py` (descarga real, borrador y 404 sin
  apuntes).

## Cómo fluye la información

1. La ruta pide `service.pdf(codigo)`; el servicio resuelve la oposición configurada y busca el tema
   por su código legible.
2. `notes_for_node` trae los apartados y `read_by_chapters` los reparte en los epígrafes oficiales,
   en orden de programa, con su número global.
3. El servicio compone un `TopicPdfDocument` inmutable: oposición, bloque, tema, fechas, estado y
   capítulos. No conoce PyMuPDF.
4. `render_topic_pdf` convierte el documento a HTML, lo maqueta, sella cabecera y pie y devuelve los
   bytes en memoria.
5. La ruta entrega esos bytes como descarga; el nombre del archivo ya viene saneado del servidor.
6. En la web, `DescargarPdf` pide esa misma ruta por `apiFetchBinary` con las credenciales de la
   instalación, recibe el `Blob` y el nombre de `Content-Disposition`, y lo entrega al navegador con un
   `objectURL` temporal que se libera en el turno siguiente.

## Ficheros y migraciones

- `apps/api/opofuente/application/topic_reading.py` (nuevo).
- `apps/api/opofuente/application/topic_pdf.py` (nuevo).
- `apps/api/opofuente/infrastructure/topic_pdf.py` (nuevo).
- `apps/api/opofuente/application/student_service.py` (lectura por capítulos y exportación).
- `apps/api/opofuente/application/student_models.py` (`StudentTopicPdf`).
- `apps/api/opofuente/api/routes/student.py` (ruta PDF y docstring del módulo).
- `apps/api/tests/unit/test_topic_pdf.py` (nuevo).
- `apps/api/tests/unit/test_topic_pdf_render.py` (nuevo: el renderizador y la guarda de terminación).
- `apps/web/src/api/client.ts` (`apiFetchBinary` y `filenameFromDisposition`).
- `apps/web/src/api/studentStudy.ts` (`downloadStudentTopicPdf`).
- `apps/web/src/features/student/DescargarPdf.tsx` (nuevo).
- `apps/web/src/pages/student/TopicNotesPage.tsx` (botón en la cabecera del tema).
- `apps/api/opofuente/main.py` (`Content-Disposition` en `expose_headers` de CORS).
- `apps/api/tests/integration/test_student_notes_api.py` (pruebas del PDF).
- `packages/contracts/openapi.json` y `packages/contracts/src/openapi.d.ts`.
- Sin migración: el PDF se compone desde datos existentes y no persiste nada.

## Patrones y decisiones aplicadas

- **Aplicación pura e infraestructura aparte**: la composición del documento y el markdown no
  importan PyMuPDF; el renderizador es el único que conoce la librería, igual que el resto de
  integraciones.
- **Un solo reparto**: `read_by_chapters` sustituye la lógica que solo existía para la pantalla, para
  que PDF y web no puedan divergir en orden ni en numeración.
- **Nada de archivos temporales**: `DocumentWriter` sobre `io.BytesIO`; el PDF viaja en la respuesta
  y no queda copia en disco ni en la base de datos.
- **Sin apuntes no hay PDF**: 404 explícito en vez de un archivo vacío que parecería una avería.
- **Nombre saneado en servidor**: ASCII, sin separadores de ruta y con recorte; el cliente no decide
  el nombre que se escribe.

## Seguridad y privacidad

- El HTML del apunte se escapa antes de aplicar negrita, cursiva o código; las marcas internas de
  revisión no se exportan.
- La ruta no acepta rutas de archivo ni contenido: solo el código del tema, que se resuelve contra
  el currículo autorizado.
- No se escribe en `OPOFUENTE_DATA_DIR` ni fuera de él; no hay secretos, credenciales ni datos
  personales en el flujo.
- `Cache-Control: private, no-store` evita que un PDF con estado de borrador quede cacheado por
  intermediarios.

## Puertas ejecutadas y resultado

- `validar({"project":"opofuente","gate":"648dc9aeae21"})` sobre `tree_hash`
  `7524217a9b01b677a711a28daa595ef6752d4ddd6ae0eab4e07d8679f4f86c64` → **verde**: 1101 pasan, 3 se
  omiten, 0 fallan (50,6 s; evidencia
  `ff39cf35e24bc94caf16054480d03fade2dc2cfc876f46d848bab9e06e4e78af`). Es la segunda pasada verde
  seguida: la anterior fue sobre `692d9579…` con evidencia `0964b89d…`, mismo resultado.
- `tree_hash` de la candidata medida: `7524217a9b01b677a711a28daa595ef6752d4ddd6ae0eab4e07d8679f4f86c64`.
  Las dos cifras de este apartado se escribieron **después** de esa ejecución, así que el árbol final
  difiere solo por este documento; no se volvió a lanzar la puerta por un cambio de redacción.
- La puerta `9df85043f3a0` (`gates.ps1`: ESLint, `tsc`, build, integración, E2E) **no se ejecutó**:
  `validar` la rechaza en un worktree propio y dura decenas de minutos. Por eso la parte de web de este
  slice (botón de descarga, `apiFetchBinary`, `filenameFromDisposition`) **no tiene ninguna puerta
  verde** y no hay ni typecheck ni lint de esos ficheros ejecutados aquí.
- No se ejecutaron `ruff`, `mypy`, `npm run contracts:check` ni `export-openapi --check`. El contrato y
  los tipos se editaron a mano imitando el formato del generador, y **eso no es evidencia de que
  coincidan byte a byte**.
- La puerta de contrato, cuando pueda correr, **fallará además por trabajo ajeno**: el WIP de
  `apps/api/opofuente/api/routes/plan.py` añade `/plan/calendario` y cambia esquemas sin regenerar
  `packages/contracts/openapi.json`. Este slice no toca ese WIP para no mezclar árboles.

### Historial (revisión anterior, se conserva)

- `validar` sobre `tree_hash` `2b7d9a6215eaefd1535170271acf705fe5ece01a220d16e9d10c9cb01ad6a072`:
  1083 pasan, 8 fallan, 3 se omiten (evidencia
  `db1888bc82fd24dc921c2a1618d3a75c6e3a535d5290ef5ba907825a9c48b432`); las 8 fallas eran de
  `test_safe_inputs.py`, `test_safe_paths.py` y `test_study_plan.py`, ajenas a este slice.
- Reparado el bloqueo de manifiestos que impedía construir la imagen del sandbox: `npm ci` rechazaba
  `"@opofuente/contracts": "workspace:*"` en `apps/web/package.json`; ahora declara `^0.0.0`, que es lo
  que `package-lock.json` ya resolvía, y `@playwright/test@1.63.0` consta en la entrada raíz del lock.

## Prueba manual

1. Con la API en marcha y un tema con apuntes (por ejemplo `IV.1`), pedir
   `GET /api/v1/student/topics/IV.1/pdf`.
2. Comprobar que la respuesta es `application/pdf`, que el nombre descargado empieza por
   `tema-iv-1-` y que el archivo abre en un lector.
3. Verificar en el documento el título del tema, la oposición y el bloque, la fecha, el estado, el
   pie «página 1 de N» y que aparecen todos los epígrafes.
4. Pedir un tema sin apuntes (`IV.10`) y comprobar el 404.
5. Sin archivar versión (tema en borrador), comprobar el aviso del pie «BORRADOR - no oficial» (el
   guion es ASCII porque la fuente base del PDF no dibuja el guion largo) y el texto «pendiente de
   revisión» en la cabecera.
6. En la web (`scripts\dev.ps1`), abrir `/temario/IV.1`: bajo la cabecera del tema debe estar el botón
   «Descargar el tema en PDF». Pulsarlo y comprobar que se descarga un fichero cuyo nombre empieza por
   `tema-iv-1-` (lo pone el servidor, vía `Content-Disposition`) y que el aviso pasa por
   «Preparando el PDF…» y luego «Descargando «…»».
7. Con la API parada, pulsar el botón: tiene que salir el aviso de que la aplicación no responde, no un
   error genérico en inglés.
8. Un tema sin apuntes (`IV.10`) no debe enseñar el botón.

## Limitaciones conocidas

- **La parte de web no está verificada por ninguna puerta**: `gates.ps1` (ESLint, `tsc`, build) es la
  que la cubriría y no se ejecuta en este worktree. El botón y `apiFetchBinary` están escritos
  siguiendo los patrones del resto de la aplicación, pero **no hay typecheck, lint ni prueba unitaria**
  de ellos: `apps/web/tests/unit/**` no es escribible desde este encargo.
- La guarda `MAX_PAGINAS = 200` es un tope de seguridad, no una comprobación de que un temario quepa:
  un tema de más de 200 páginas **falla** con `CuerpoDemasiadoLargoError` (500) en vez de generar un
  PDF enorme. Hoy el temario más largo cabe de sobra, pero el límite es arbitrario y no se ha medido
  el tamaño real del peor caso.
- El contrato OpenAPI y `openapi.d.ts` se editaron a mano; `contracts:check` y
  `export-openapi --check` siguen pendientes y pueden detectar diferencias de formato u orden.
- PyMuPDF con la fuente `helv` no puede representar todos los caracteres tipográficos; la cabecera y
  el pie pasan por `texto_para_pdf` (guion largo → `-`, puntos suspensivos → `...`). El **cuerpo** lo
  maqueta `Story` con sus propias fuentes: no está cubierto por esa sustitución (sí hay prueba de que
  un título con emoji y CJK no rompe el render, pero no de que se imprima completo).
- Los capítulos se ordenan por `position`; si dos capítulos compartieran posición, el orden sería el
  de entrada.

## Qué se rompe si cambias X

- Si cambias `read_by_chapters` sin actualizar la pantalla, el PDF y `GET .../notes` pueden mostrar
  capítulos u orden distintos.
- Si cambias el markdown del PDF sin tocar `notesMarkdownParser.ts`, el texto impreso y el de la web
  dejarán de contar lo mismo.
- Si quitas el 404 de «sin apuntes», volverá el PDF vacío que este slice evita.
- Si cambias el nombre de la operación o la descripción de la ruta, habrá que regenerar
  `openapi.json` y `openapi.d.ts`; la edición manual actual quedaría desfasada.
- Si devuelves el PDF escribiendo un archivo temporal, incumples la regla de no persistir contenido
  derivado y abres la puerta a residuos con datos del alumno.

## Qué criticaría un revisor senior

- Que la mitad del slice que se ve (el botón de la web) llegue **sin typecheck, sin lint y sin prueba**,
  y que el revisor tenga que confiar en que `apiFetchBinary` compila.
- Que la guarda de terminación se pruebe solo con dobles y no con un caso real que llegue al tope: el
  camino `CuerpoDemasiadoLargoError` nunca se ha producido con un PDF de verdad.
- Que se añada `Content-Disposition` a `expose_headers` sin una prueba de que el navegador lo lee y sin
  comprobar que ninguna otra respuesta se vea afectada.
- Que el contrato se haya editado a mano en vez de generarlo, con riesgo de que `contracts:check`
  falle por un espacio o una línea de JSDoc.
- Que el aviso de borrador dependa de `state == "draft"` y no de una comprobación de estados
  desconocidos; hoy un estado nuevo se imprimiría tal cual, sin aviso.
- Que el pie y la cabecera usen `insert_text` con una fuente base: ya se sustituyen los caracteres
  fuera de Latin-1, pero el cuerpo lo maqueta `Story` con fuentes propias y sigue sin prueba que un
  temario con comillas tipográficas o símbolos raros se imprima completo.
