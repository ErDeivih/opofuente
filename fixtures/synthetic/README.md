# Fixtures sintéticos

Material **creado para pruebas**, nunca material comercial ni contenido privado del usuario
(10_TEST-PLAN §2, `AGENTS.md`: «Fixtures sintéticos; nada privado/comercial en git»).

En S00 esta carpeta está vacía a propósito: todavía no existe ingestión que probar. Cada fixture
se añade en el slice que lo necesita:

| Fixture | Slice | Uso |
|---|---|---|
| PDF nativo multipágina, PDF escaneado pequeño, DOCX con títulos y tablas | S03 | extractores |
| CSV de preguntas válido y con filas defectuosas | S06 | importador |
| HTML con scripts y texto que intenta inyectar instrucciones | S03 | seguridad |
| ZIP seguro, ZIP con traversal y ZIP con ratio de expansión abusivo | S03 | seguridad |
| Dos archivos idénticos con nombres distintos; dos revisiones casi iguales | S02/S04 | duplicados |
| Cuestionarios sintéticos modelo A/B y claves v1/v2 | S08 | claves versionadas |

## Material de S02 (inventario y copia)

La bandeja de S02 **sí** necesita una carpeta con material. No se versiona como ficheros binarios:
las pruebas la crean en un directorio temporal con contenido propio y la borran al terminar. Así no
entra en git nada que parezca material de estudio real, y el caso cubierto es exactamente el que
describe el plan de pruebas:

| Elemento | Dónde se crea | Qué prueba |
|---|---|---|
| `tema-01.pdf` y `tema-01-copia.pdf` (byte a byte iguales) | `tests/integration/test_import.py`, `tests/e2e/tray.spec.ts` | un solo artefacto con dos orígenes |
| `notas.txt` | ídem | copia normal |
| `.oculto.txt`, `~$temporal.docx`, `programa.exe` | ídem | omisión declarada (oculto, temporal, ejecutable) |
| `node_modules/` | ídem | directorio ignorado |
| `enlace-fuera` (junction a una carpeta de fuera) | ídem | no se sigue un enlace que sale de la raíz |
| `secreto.txt` fuera de la carpeta | ídem | el material de fuera no se copia ni se inventaría |

Nada de esto apunta jamás a una carpeta real del usuario: la raíz la elige el propio test.

## Material de S03 (extracción, contenedores y entradas directas)

Tampoco se versionan binarios aquí. Los documentos se **generan** en cada prueba
(`apps/api/tests/synthetic_documents.py`) para que el contenido se lea en el propio test y no haya
binarios opacos en git: un PDF de verdad (PyMuPDF), un DOCX (python-docx) y sus variantes maliciosas,
HTML con scripts, CSV, JSON, texto en Windows-1252, PNG, ZIP (stdlib `zipfile`) y un falso XLSX.

| Fixture | Dónde se genera | Qué prueba |
|---|---|---|
| PDF nativo de varias páginas (con relleno propio) | `synthetic_documents.build_text_pdf` | extracción por páginas, secciones y calidad |
| PDF «escaneado» (imágenes, sin capa de texto) | `build_scanned_pdf` | candidato a OCR: `ocr_pending`, nunca texto inventado |
| PDF con cabecera y pie repetidos en todas las páginas | `build_pdf_with_repeated_header` | aviso `repeated_header` y calidad |
| DOCX con títulos, listas y tabla | `build_docx` | estructura de secciones |
| DOCX con `DOCTYPE` y entidad externa | `build_docx_with_doctype` | DEBT-004: no se resuelven entidades ni ficheros locales |
| DOCX bomba (XML enorme comprimido) | `build_bomb_docx` | límites del contenedor |
| HTML con `script`, `iframe`, `nav`, `footer` y una inyección de prompt | `build_html` | nada de contenido activo; el texto hostil entra como texto |
| CSV válido y con fila defectuosa, JSON válido y roto, texto en cp1252 | `build_csv`, `build_json`, `build_json_broken`, `build_cp1252_text` | extractores de texto y aviso de codificación |
| PNG pequeño | `build_png` | metadatos de imagen (dimensiones), sin texto inventado |
| ZIP con miembros, ZIP con `../traversal`, ZIP anidado, falso XLSX, `MZ` ejecutable | `build_zip`, `build_spreadsheet_like`, `build_executable_bytes` | expansión controlada, DEBT-008 y rechazos por seguridad |

En el E2E (`apps/web/tests/e2e/tray.spec.ts`) el PDF y el ZIP se construyen con dos funciones del
propio test —`buildPdf` (con su tabla `xref` y sus desplazamientos reales: un PDF falso haría que la
prueba midiera el andamio y no la aplicación) y `buildZip` (ZIP sin comprimir, con CRC-32 calculado a
mano para no añadir dependencias)—. El material vive en el directorio temporal del sistema y se borra
al terminar.

Reglas:

- nada de material con derechos de terceros;
- ningún fichero con datos personales reales;
- los documentos sintéticos se generan a partir de texto propio y se versionan aquí;
- si un test necesita una fuente oficial, se guarda URL, fecha, derechos y hash, o se prueba con
  metadatos en lugar de descargar.
