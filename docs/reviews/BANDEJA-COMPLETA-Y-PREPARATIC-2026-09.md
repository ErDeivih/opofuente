# La bandeja, contada entera, y el material de PreparaTIC mapeado (30-09-2026)

Segunda pasada de la tarde. Aquí van los números y cómo se han obtenido, con los dos caminos que se
probaron y **fallaron** escritos también, para que la próxima ronda no los repita.

## 1. ¿Está todo lo de las bandejas dentro de la aplicación?

Se hizo un auditor (`_oficial/auditoria_de_la_bandeja.py`) que recorre las carpetas de material y, para cada
fichero, mira si existe un artefacto con su nombre y su tamaño. **La primera versión contaba 589 ficheros
sin llegar y estaba mal**: buscaba el nombre sólo en `original_name`, y la aplicación guarda ahí a veces el
nombre saneado del trozo (por ejemplo `-boe-leyes-consolidadas-ley-9-2017-contratos-xml-txt-c64377.txt`).
Corregido, busca el nombre en los **tres** sitios donde la aplicación lo escribe (`original_name`,
`display_location`, `source_path_display`) y, para lo que sigue sin reconocerse, **calcula la huella
sha256** y la compara con los artefactos. Resultado:

| | ficheros legibles en la bandeja | dentro de la aplicación | sin llegar |
| --- | --- | --- | --- |
| `F:\OpoFuente\TAI` | 5.938 | **5.679 (95,6 %)** | 259 |
| `F:\OpoFuente\GUARDIA-CIVIL` | 325 | 236 (72,6 %) | 89 |
| `F:\OpoFuente\AMPLIACION` | 33 | 0 | 33 |

De esos **381** que no llegaron por nombre, el recuento por decisión (`_oficial/decidir_lo_que_falta.py`):

| decisión | ficheros | qué son |
| --- | --- | --- |
| **ya está** | 161 | volcados de texto que se convirtieron a legible y **sí entraron** (ver §2) |
| apuntes de ampliación propios | 58 | notas de ampliación por tema; su texto ya está en los apuntes de la aplicación |
| basura | 45 | bloqueos temporales de Office (`~$…`), que no son material |
| informe mío | 38 | `CATALOGO` de TAI y de Guardia Civil (25) y notas de ampliación de Guardia Civil (13) |
| vista derivada | 53 | `.xml.txt` cuyo `.xml` ya está dentro **y con texto** (17) y `.xlsx` cuyo original ya está dentro (36) |
| OCR propio | 20 | texto que generé yo; el escaneo original sigue en la bandeja |
| otros | 6 | 4 páginas descargadas sin plantilla aprovechable y 2 ficheros de datos intermedios |
| | **381** | |

**No queda nada que ingerir: 0 ficheros.** El informe de la bandeja está en
`F:\OpoFuente\CATALOGO\auditoria-bandeja.json` y el plan, con la decisión de cada uno, en
`plan-de-ingesta.json`.

Nota honesta sobre el recuento de Guardia Civil: el 72,6 % es bajo porque buena parte de lo que hay en
`GUARDIA-CIVIL` son **mis propios productos** (`CATALOGO`, `OCR`) y notas de ampliación cuyo contenido ya
está dentro por otra vía; el material de estudio propiamente dicho está dentro.

## 2. Lo que se encontró de verdad: 197 documentos dentro pero **mudos**

El hallazgo que sí valía la pena. Comprobado contra la base, uno por uno:

| extensión | cuántos | qué pasa |
| --- | --- | --- |
| `.epub` de PreparaTIC | 122 | están en la biblioteca y su texto extraído es **de 0 caracteres**: la aplicación no sabe leerlos |
| hojas de cálculo `.xlsx` | 67 | igual: están, y mudas |
| presentaciones `.pptx` / `.odt` | 8 | igual |

El único texto que existía de todo eso eran **volcados que ya había hecho yo** (`.epub.txt`, `.xlsx.txt`,
`.pptx.txt`) y que nunca llegaron a la aplicación. Son **6.225.446 caracteres (6,1 MB) de texto invisible**:
temas de PreparaTIC, glosarios, listas de comandos, comparativas.

Se convirtieron con `_oficial/volcados_a_texto_legible.py` a `F:\OpoFuente\EN-TEXTO-LEGIBLE`, haciendo bien
las dos cosas que están medidas:

1. **bloques de 800 caracteres**: los volcados traen párrafos enormes (uno de **417.296** caracteres) y la
   aplicación guarda como mucho 1.200 caracteres por tramo. Ingeridos tal cual sobreviviría el **28,7 %**;
   reagrupados, sobrevive el **97,9 %**;
2. **corte limpio en el byte 4.096**: ver §3.

Salieron 165 ficheros (36 eran repetidos por contenido y se descartaron). Ingeridos: **165 de 165, cero sin
extraer, 5.766.146 caracteres de texto**. Después se promocionaron y se aceptaron sus versiones: **168
documentos nuevos**, y la biblioteca quedó en 4.107 artefactos con texto (con el rehacer de los apuntes de §4,
el estado final es **4.217 versiones aceptadas** de **4.146 documentos**).

## 3. El defecto del sniffing se cobró tres ficheros más, y ya está cerrado

El detector de formato de la aplicación lee **4.096 bytes**. Si el corte parte un carácter acentuado (los
bytes `0x8D`, `0x8F`, `0x90` y `0x9D` no existen en cp1252), el `.txt` se guarda como «conservado sin
extraer» y no se lee. El relleno ASCII que se usaba **sólo cubría los ficheros de menos de 4.096 bytes**: en
esta pasada se cayeron tres que pasaban de ahí (`PreparaTIC_31_056 - Resumen`, `PreparaTIC_31_126 - Tema`,
`Preparatic_29_005 - Resumen`).

Arreglado en `volcados_a_texto_legible.asegurar_que_parece_texto`: si el byte 4.096 parte un carácter, se
meten los espacios necesarios **al principio de esa línea** —no en medio de la palabra— para que el carácter
empiece justo en 4.096. Comprobado: de los 165 ficheros sólo cambiaron esos 3, y al reingerir el lote salió
**165 copiados, 0 sin extraer**.

Esto sigue siendo un defecto de la aplicación, no del material: cualquier `.txt` con acentos que llegue por
otra vía se seguirá perdiendo. Está en la lista de defectos reproducidos (`ESTADO-DEL-MATERIAL-2026-09.md`).

## 4. PreparaTIC → temas de TAI

Se catalogaron los **133 temas de PreparaTIC** (cuerpo superior TIC) leyendo los nombres de sus carpetas,
pero **sólo** las que son hijas de una carpeta llamada `PUBLICADOS`: cogiendo cualquier carpeta que empiece
por tres dígitos entraban ficheros y árboles ajenos («002 Aspectos importantes.pdf») y el matcher decidía
sobre basura.

**Dos caminos probados y descartados, con la medición delante:**

- **por el contenido del documento**: se probó y sale mal. El vocabulario tira hacia los temas que tienen más
  material; el tema 8 («LPAC, LRJSP, RDAD», derecho administrativo) acababa en **I.7 protección de datos**, el
  3 (organización territorial) en **IV.7 modelo TCP/IP** y el 117 (Industria 4.0) también en IV.7. Descartado.
- **por el título a secas** con el emparejador de la aplicación: decide 52 de 133, y algunas mal (Métrica v3 →
  «lenguajes de interrogación», que es SQL; diseño de software → «modelado de datos»).

**Lo que se hizo**: escribir la correspondencia leyendo los dos temarios, tema por tema, marcando si es
**directa** (el tema de PreparaTIC es ese tema de TAI) o **relacionada** (material que ayuda a estudiarlo).
Y dejar **fuera a propósito** lo que el temario de TAI no pide:

| | temas de PreparaTIC |
| --- | --- |
| correspondencia **directa** | 49 |
| correspondencia **relacionada** | 36 |
| **fuera del temario de TAI** (economía, presupuestos, liderazgo, gestión de proyectos, ITIL/COBIT, inteligencia artificial, SIG, CATV…) | 48 |

La decisión por términos se conservó como **comprobación independiente**: coinciden 16 de 42 comparables, y
en los desacuerdos la tabla tiene razón leyendo los títulos (Métrica v3 → III.9 metodologías, no III.3 SQL;
virtualización → IV.2, no IV.1; análisis de riesgos → IV.5 seguridad, no IV.6 comunicaciones; E-R y clases →
III.1 modelado de datos, no II.3 estructuras de datos).

**Aplicado**: **303 mapeos creados, 0 fallos** (178 de temas directos y 125 de relacionados).
Temas de TAI que **no tienen ningún tema de PreparaTIC**: I.2, I.3, I.5, II.3, III.2, III.3 y IV.4 — esos
siete dependen de su propio material y de sus apuntes.

### Lo que cambió en cada tema (medido, en tres pasos)

`antes` = el mapa de las 18:28; `+PreparaTIC` = después de mapear los 303 documentos; `+apuntes` = después de
rehacer los 33 apuntes con el material nuevo (`_oficial/anadir_material_de_la_biblioteca_a_los_apuntes.py
--rehacer --aplicar`, que añadió hasta 150 fragmentos por apunte y guardó los anteriores en
`APUNTES-anteriores\2026-09-30-1951`).

| tema | antes | +PreparaTIC | +apuntes | documentos |
| --- | --- | --- | --- | --- |
| III.9 repositorios y metodologías | 1.164 | 1.599 | **2.832** | 10 → **56** |
| III.7 aplicaciones web | 1.347 | 1.507 | **2.520** | 20 → **39** |
| I.9 instrumentos de acceso | 1.421 | 1.652 | **2.511** | 7 → **15** |
| I.4 empleo público y transparencia | 1.586 | 1.825 | **2.756** | 11 → **24** |
| IV.2 bases de datos y virtualización | 1.100 | 1.237 | **2.219** | 6 → **21** |
| IV.6 comunicaciones | 1.006 | 1.288 | **2.207** | 5 → **25** |
| IV.9 seguridad en redes | 1.042 | 1.191 | **2.171** | 5 → **16** |
| IV.10 redes locales | 1.054 | 1.179 | **2.066** | 12 → **20** |
| III.8 accesibilidad | 977 | 1.160 | **1.870** | 6 → **16** |
| II.2 periféricos | 994 | 1.014 | **1.668** | 4 → **9** |
| I.6 sociedad de la información | 7.548 | 8.427 | **9.507** | 42 → **75** |
| I.8 acceso electrónico | 4.221 | 4.880 | **5.918** | 25 → **57** |
| IV.5 seguridad de sistemas | 6.200 | 6.763 | **7.740** | 16 → **42** |

Estado del mapa: **33 de 33 temas con material**, **ninguno por debajo de 50 fragmentos** y **ninguno sin
preguntas**. El tema más flojo pasa de 994 fragmentos (II.2, con 4 documentos) a **1.668** con 9 documentos. Las
111 partes de los apuntes entraron **todas** (antes 110 de 111: una parte se quedó fuera por el corte de 4.096
bytes, y es lo que motivó llevar la guarda al módulo común) y las 111 quedaron mapeadas a su nodo. El mapa
completo, con preguntas y claves por tema, lo imprime `_oficial/mapa_de_material_por_tema.py`.

## 5. Comprobado de punta a punta

- **Búsqueda**: encuentra el material nuevo por su contenido. «paradigma orientado a objetos ABAP» trae
  `Nombrespropiosrecopilacion (texto).txt`, que es una de las hojas de cálculo que estaban mudas.
- **Dossier de tema** (`GET /curriculum-nodes/{id}/dossier`): III.9 devuelve **53 fuentes**, IV.5 **33** y IV.6
  **22**, con los documentos de PreparaTIC dentro de las de IV.6. El material mapeado llega al dossier.
- **Tiempos**: las búsquedas responden en **619–1.077 ms** con el corpus de hoy.
- **Aviso de un falso positivo mío, para que no se repita**: durante esta ronda llegué a ver un error 400 al
  buscar con tildes. **No es un defecto de la aplicación**: era mi propio cliente de PowerShell mandando el
  cuerpo en Latin-1. Mandando el JSON en UTF-8, «constitución española», «métricas de estimación» y
  «compresión de datos» responden bien. Queda escrito aquí porque la conclusión contraria habría sido falsa.

## 6. Lo que sigue abierto

1. **5.565 preguntas del banco sin tema** (el banco tiene 16.984): las cuatro vías léxicas están agotadas y
   medidas; hace falta la decisión **DEBT-014** (embeddings o modelo local), que es del propietario.
2. **`crudo-docx.jsonl`**: 2.164 preguntas con opciones y **0 con clave**. Siguen fuera del banco.
3. **Exámenes de Guardia Civil 2021-2025**: legibles (137-158 preguntas) pero sin plantilla fiable.
4. **Defectos de la aplicación reproducidos** (merecen arreglo en el código, no caso por caso): el sniffing de
   4.096 bytes —que se ha vuelto a cobrar tres ficheros—, los nombres de campo protobuf de las barajas
   modernas, el `.md` que se extrae sólo por sus encabezados, y el **500** de
   `POST /question-sets/{id}/parse` con `kind=answer_key` en 11 de 24 conjuntos.
5. **Material de PreparaTIC fuera del temario de TAI** (48 temas): está en la biblioteca y se puede
   consultar, pero **a propósito no está asignado a ningún tema de TAI**.
