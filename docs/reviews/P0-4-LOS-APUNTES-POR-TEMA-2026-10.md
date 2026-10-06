# P0.4 — Los apuntes por tema: de 53,6 s a 2,0 s (5 de octubre de 2026)

Bloque 3 del plan `PLAN-PARA-DEEPSEEK-2026-10.md`, primera mitad. Rama `apuntes-por-tema-rapidos`,
sacada de `sesiones-antiguas-con-nombre` (el arreglo de Claude para las sesiones sin etiqueta).

## Lo que se veía

Abrir un tema en el Programa construye sus apuntes con las citas del material (el «dossier»). Para
el tema II.1, la primera vez tardaba **99 s** y devolvía **1,16 MB** (medido por Claude); guardar una
versión, otros **21 s**. Medido otra vez con más temas, el peor caso era mucho peor: el bloque que
contiene toda la oposición, **14,3 s** y **58,8 MB** de datos.

## Dónde se iba el tiempo, medido por dentro

Antes de tocar nada se midió cada parte del camino real, sobre los datos del propietario:

| paso | I.1 | II.1 |
| --- | --- | --- |
| **consulta de los tramos** | **53,6 s** | **51,6 s** |
| `build_dossier` (Python) | 0,16 s | 0,06 s |
| `dossier_document` + JSON | 0,03 s | 0,01 s |
| esquema Pydantic + serializar la respuesta | 0,15 s | 0,02 s |
| tamaño de la respuesta | 2,43 MB | 1,16 MB |

Todo el tiempo estaba en **una consulta**. El cálculo y la serialización eran ruido.

## La causa

La consulta unía `evidence_spans` con `curriculum_mappings` mediante un `OR` de cinco condiciones —el
material puede estar asignado por su artefacto, su representación, la versión del documento, una
sección o una cita—, y ese `OR` **impedía usar los índices**: SQLite comparaba cada tramo del tema con
las **39.242** filas de mapeos (el tema I.1 tiene 9.915 tramos).

## El arreglo

Tres lecturas, cada una con su índice, y el emparejamiento de estados en memoria:

1. **los mapeos del ámbito**, por `ix_mapping_node` (2.064 filas en I.1, 129 en II.1);
2. **los artefactos y las representaciones, traducidos a sus versiones**: un mapeo de artefacto
   alcanza a todas las versiones de ese artefacto, y `document_versions` tiene 5.927 filas con
   `artifact_id` indexado. `representation_id` **no** tiene índice, y dejarlo en la consulta grande
   costaba 2,6 s por tema (medido: 8.145 tramos de I.1);
3. **los tramos** por versión (`ix_evidence_version`), sección (`ix_evidence_section`) o cita (su
   clave), con los estados de mapeo emparejados en Python en lugar de `group_concat(DISTINCT …)`.

El resultado es **el mismo**: la prueba
`test_los_tramos_del_tema_son_los_mismos_con_las_dos_consultas` compara, para dos nodos, los tramos de
la consulta nueva con los de la única de antes —mismos identificadores, mismos estados de mapeo, mismo
orden—. Esa prueba es la que sostiene el cambio: el dossier de un tema se archiva como versión, y un
tramo de más o de menos cambia la huella de contenido y con ella el historial.

## Antes y después (datos del propietario)

| nodo | antes | ahora | tramos |
| --- | --- | --- | --- |
| tema I.1 | 53,6 s | **2,01 s** | 9.915 |
| tema II.1 | 51,6 s | **1,99 s** | 2.510 |
| bloque I (toda la oposición) | — | 14,3 s + 4,9 s de cálculo | 119.667 |

Y por HTTP, contra la API en marcha (que es lo que vive la pantalla):

| | antes | ahora |
| --- | --- | --- |
| II.1, primera llamada con la caché del sistema **fría** | 99 s | 63,3 s |
| II.1, con la caché caliente | 21 s | **3,9 s** |
| II.1, segunda llamada | 21 s | **2,8 s** |
| I.7 (tema grande, 12,2 MB) | — | 9,3 s la primera, 7,0 s después |
| guardar una versión (II.1) | 21 s | **3,6 s** |
| listar las versiones guardadas | — | 0,01 s |

La diferencia entre la primera llamada con la caché fría (63 s) y con la caché caliente (3,9 s) es del
**sistema de ficheros**, no de la aplicación: se comprobó reiniciando la API —proceso nuevo, misma
caché del sistema— y la primera llamada tardó 3,94 s.

## Lo que queda de P0.4

Dos cosas, y las dos son lo otro que pedía el plan:

1. **El bloque sigue siendo el caso gordo**: 19 s y **58,8 MB** de datos, porque su ámbito es la
   oposición entera (119.667 tramos, 728 fuentes). Hace falta la respuesta con **resumen** (cuántas
   fuentes y cuántos pasajes, y los primeros) y los fragmentos **paginados**, en vez de devolver 59 MB
   de golpe al navegador.
2. **La primera lectura con la caché fría** (63 s para un tema) es del disco, no de la consulta, pero
   se nota igual al abrir la aplicación. Se arregla con la **caché por revisión del corpus** que pedía
   el plan: si el corpus no ha cambiado, el dossier del tema se sirve ya construido.

