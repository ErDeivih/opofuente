# La bandeja: qué faltaba de los zip, y qué se ha hecho con ello (29-09-2026)

La bandeja tiene **12 zip, 14,5 GB**. Cuatro estaban inventariados (`CATALOGO\pack-extraido.json`), pero los
cinco del 29-09 (material de Preparatic) y el tercero de PreparaTAI AGE **no tenían índice**. Y de esos cinco
no se sabía qué había dentro ni si estaba ya en la aplicación.

## Lo que se midió antes de copiar nada

`ver_dentro_de_los_zip.py` (lee el índice del zip, no descomprime) y `medir_cobertura_de_los_zip.py` (compara
el nombre de cada fichero con lo que la aplicación ya conoce, sin acentos y sin el prefijo «Copia de» que pone
el navegador):

| zip | documentos | ya en la aplicación |
| --- | --- | --- |
| drive-download-…-001 | 417 | 91 % |
| drive-download-…-002 | 312 | 94 % |
| drive-download-…-003 | 133 | 84 % |
| drive-download-…-004 | 1 | 100 % |
| PreparaTAI AGE (3 zip, 5,5 GB) | 861 | 91 % |
| PUBLICADOS (Preparatic) | 1.174 | **94 %** |
| RELEASE (Preparatic) | 327 | 88 % |
| PUBLICAR PACK 3 ANALISIS P31 | 317 | 93 % |
| INFORMES | 22 | 64 % |
| SUPUESTOS | 25 | 68 % |

Es decir: el material de Preparatic de los zip del 29-09 **ya estaba casi todo** en la biblioteca. Lo que
faltaba eran ficheros sueltos: PDF, DOCX, XLSX, PPTX, EPUB, apkg y algún .doc.

## Lo que se hizo

De todos esos, la aplicación solo sabe extraer texto de **PDF y DOCX** (XLSX, PPTX y EPUB no tienen extractor:
se guardarían sin texto, DEBT-008). Así que se descomprimieron **solo PDF y DOCX que faltaban**
(`extraer_lo_que_falta.py`), con dos cuidados:

- se salta lo que ya está (por nombre, sin acentos y sin «Copia de»);
- se salta lo repetido **entre** zip por `sha256` — los tres zip de PreparaTAI AGE traen los mismos ficheros
  que las descargas de Drive, y sin esto se habrían copiado dos veces (70 ficheros repetidos detectados).

Resultado: **133 documentos, 398 MB**, descomprimidos en `F:\OpoFuente\TAI\internet\lo-que-faltaba\`. Los zip
no se han tocado.

Al importarlos, la aplicación avisó de lo que no puede leer: 20 PDF **sin texto nativo** (quedan pendientes de
OCR, que no se ha ejecutado), 4 formatos sin extractor, 1 fichero vacío y 3 fallos (uno por contenido
peligroso, `UnsafeContentError`).

## El resultado, medido por contenido y no por nombre

`medir_lo_nuevo_por_contenido.py` compara el `sha256` de los 133 ficheros con los artefactos de la aplicación
y, además, mira si el artefacto tiene **documento** —que es lo que se puede leer, buscar y citar—:

| | ficheros |
| --- | --- |
| ya estaban legibles en la biblioteca | 68 |
| **el fichero estaba guardado pero sin documento: ahora se puede leer** | **65** |
| material con contenido nuevo | 0 |

Es decir: la descompresión no trajo contenido nuevo (la aplicación guarda por `sha256`, así que el mismo PDF
con dos nombres es un solo artefacto), pero sí **rescató 65 documentos que estaban en el almacén sin ficha**.
La biblioteca pasa de **3.082 documentos y 3.094 versiones aceptadas** a **3.101 y 3.113**.

Ese es el número honesto: por nombre «faltaban 133», por contenido eran 65 documentos sin usar.

## Y una comprobación que evita un trabajo inútil

El material nuevo **ya está clasificado**: 67 de las 68 representaciones con texto tienen propuestas de
clasificación (solo falta una, `Soluciones - Subnetting - 2017-2022.pdf`).

Quedan **12.286 propuestas pendientes** de decisión en toda la biblioteca (dato en `ver_propuestas.py`), y sus
confianzas están medidas (`medir_confianza_de_propuestas.py`):

| eje | pendientes | ≥0,90 | 0,80-0,89 | 0,60-0,79 | 0,40-0,59 | <0,40 |
| --- | --- | --- | --- | --- | --- | --- |
| authority | 1.584 | 362 | 154 | 688 | 380 | 0 |
| document_type | 1.598 | 0 | 0 | 994 | 604 | 0 |
| topic | 8.812 | 466 | 44 | 2.010 | 2.324 | 3.968 |
| rights | 196 | 0 | 0 | 196 | 0 | 0 |
| opposition | 96 | 0 | 0 | 0 | 96 | 0 |

**No se han aceptado en bloque, y es una decisión medida**: el dossier de un tema ya usa los mapeos
`provisional` (en `dossier_repository` la condición es `status <> 'rejected'`), así que aceptarlas no añadiría
nada que la aplicación no esté usando ya; y aceptar es aprobar (ADR-009). La cola queda como cola de revisión,
con sus bandas de confianza a la vista.

## Cómo se reproduce

```powershell
python ver_dentro_de_los_zip.py                 # qué hay dentro de cada zip, sin descomprimir
python medir_cobertura_de_los_zip.py            # qué de eso está ya en la aplicación
python extraer_lo_que_falta.py                  # informe de lo que falta (PDF y DOCX)
python extraer_lo_que_falta.py --aplicar        # lo descomprime
python ingerir_carpeta.py "F:\OpoFuente\TAI\internet\lo-que-faltaba"
python rellenar_biblioteca.py                   # promociona y acepta las versiones
python medir_lo_nuevo_por_contenido.py          # qué era material nuevo de verdad
python ver_propuestas.py                        # la cola de clasificación, por eje y estado
```

## Qué queda de la bandeja

- **20 PDF escaneados** de lo recién importado, sin texto nativo: pendientes de OCR (el pipeline de OCR existe
  y está medido en `docs/reviews/OCR-*.md`).
- **XLSX, PPTX, EPUB y .doc** que faltan: no tienen extractor en la aplicación. Meterlos sería guardarlos sin
  poder leerlos; convertirlos es un paso aparte (`convertir_no_soportados.py` existe y está medido).
- La cola de **12.286 propuestas** de clasificación, con sus bandas de confianza, esperando revisión.
