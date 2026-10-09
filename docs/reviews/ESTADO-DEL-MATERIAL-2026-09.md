# Estado del material de TAI y de Guardia Civil, y por dónde sigue (30-09-2026)

Resumen de lo verificado contra la aplicación en estas rondas, y la lista de lo que queda con su base medida. Va
aquí para que la siguiente ronda no tenga que deducirlo de los informes largos.

## Lo que está hecho y comprobado

| | TAI | Guardia Civil |
| --- | --- | --- |
| preguntas en el banco | **11.292** (8.570 con tema · 11.234 con clave · 11.250 con cita) | **240** (todas con clave) |
| conjuntos de preguntas | 105 (74 son los mazos de la comunidad) | 2 (examen oficial 2026, modelos A y B) |
| temas con material | **33 de 33** | **25 de 25** |
| temas sin ninguna pregunta | **0** | 1 (tema 25, Lengua Española: su examen no lo pregunta, medido) |
| apuntes dentro de la aplicación | **37 de 37** (102 partes, 97 % del texto, todas mapeadas a su nodo) | **25 de 25** (98,2 % del texto, todas mapeadas) |
| material (fragmentos mapeados) | 4.473 por tema + los apuntes | **4.314** |

Informes con las mediciones: `MAZOS-DE-ANKI-2026-09.md`, `GUARDIA-CIVIL-MATERIAL-2026-09.md`,
`APUNTES-DE-TAI-EN-LA-APP-2026-09.md`.

## Actualización (30-09-2026, al final de la serie de clasificación)

| | TAI y Guardia Civil, hoy |
| --- | --- |
| preguntas en el banco | **16.984** |
| con clave | **16.504** |
| con cita | **16.489** |
| con tema (nodo del programa) | **11.419** (5.565 sin tema) |
| conjuntos | 233 |
| temas sin ninguna pregunta | **0** |
| tema con menos preguntas | **70** (IV.3) |
| apuntes dentro de la aplicación | **37 de 37** (102 partes, 97 % del texto) |
| fuentes de internet mapeadas a su tema | **28** (MDN, W3C, BOE, Pro Git, ENS, PostgreSQL) |
| búsqueda de la aplicación | **445-697 ms**, con resultados |

## Última hora (30-09-2026, cierre de la tarde)

Lo de esta última pasada está en **`BANDEJA-COMPLETA-Y-PREPARATIC-2026-09.md`**, con sus mediciones. Resumen:

- **La bandeja está contada entera y no queda nada por ingerir** (0 ficheros). El auditor encuentra **5.679 de
  5.938** ficheros de `TAI` dentro de la aplicación (95,6 %); el resto son mis informes, vistas derivadas de
  documentos que ya están dentro, bloqueos de Office y mi propio OCR. Ojo al dato: la primera versión del
  auditor **contaba 589 ficheros perdidos y estaba mal** (buscaba el nombre sólo en un campo); corregido,
  busca en los tres y además compara huellas.
- **197 documentos estaban dentro pero mudos**, con 0 caracteres de texto: 122 `.epub` de PreparaTIC, 67 hojas
  de cálculo y 8 presentaciones. Su único texto eran volcados míos que nunca llegaron: **6,1 MB invisibles**.
  Convertidos con la receta medida (bloques de 800 caracteres: sin ella sobreviviría el 28,7 % del texto, con
  ella el **97,9 %**) e ingeridos **165 de 165**, cero sin extraer.
- **El defecto del sniffing de 4.096 bytes se ha cobrado tres ficheros más** (esta vez de más de 4.096 bytes,
  que el relleno anterior no cubría) y ya está cerrado en el conversor.
- **PreparaTIC mapeado a los temas de TAI**: 133 temas de PreparaTIC catalogados, **85 con correspondencia**
  (49 directas y 36 relacionadas) y **48 fuera del temario de TAI a propósito**. **303 documentos mapeados, 0
  fallos**. El camino por contenido se probó y **se descartó con la medición delante** (derecho administrativo
  acababa en «protección de datos»).
- ~~**Efecto en tres pasos** (antes → tras mapear PreparaTIC → tras rehacer los apuntes con ese material)~~:
  **estos números están mal y quedan tachados**. Contaban cada documento dos veces (el mapeo es polimórfico y
  la consulta unía las tres vías con un `or`); el factor va de ×1,00 a ×1,80 según el tema. Los buenos están en
  `APUNTES-SIN-REPETIDOS-2026-09.md`: III.9 **1.930**, III.7 **1.773**, I.9 **1.408**, I.4 **2.090**, IV.6
  **1.434**, IV.9 **1.406**, IV.10 **1.214**, III.8 **1.241**, I.6 **4.928**, IV.5 **6.977**, I.1 **9.076**,
  I.7 **10.720**. Lo que sí sigue valiendo: los **33 de 33** temas con material y ninguno por debajo de 50
  fragmentos (el más flojo es III.4, con **1.033**), y los 33 apuntes rehechos, con los anteriores en
  `APUNTES-anteriores\2026-09-30-1951`.
- **La guarda del corte de 4.096 bytes se ha llevado al módulo común** (`limpieza_texto.asegurar_corte_limpio`),
  porque se cobró otra víctima: una parte del apunte de 4.4 (90.691 bytes) se quedó sin extraer. Rehecha con la
  guarda, las **111 de 111** partes entraron y quedaron mapeadas.
- **Biblioteca**: **4.217 versiones aceptadas** de **4.146 documentos** (4.107 artefactos con texto antes de
  rehacer los apuntes), tras promocionar y aceptar 168 documentos nuevos.
- **Dossier comprobado por API**: III.9 devuelve **54 fuentes y 1.817 pasajes** (con sus 3 partes de apunte
  dentro), IV.5 34 y I.1 25. El material mapeado llega al dossier.

## Cierre del 30-09-2026 (madrugada): apuntes sin repetidos y de una sola generación

Está entero en **`APUNTES-SIN-REPETIDOS-2026-09.md`**. Resumen:

- **Corregido un número que publiqué mal**: los fragmentos por tema estaban contados **dos veces** (mapeo
  polimórfico: 10.340 asignaciones por `representation` y 10.355 por `artifact`, casi el mismo conjunto). Los 33
  temas sumaban 177.288 y son **129.099**. Arreglado en el mapa y en el armador de apuntes.
- **Los apuntes tenían 1.088 fragmentos repetidos palabra por palabra (12,8 %)**, 787 de ellos repitiendo el
  mismo documento — la firma del error anterior. Quitados con renumera­ción y **traducción de las referencias
  del resumen** (`([35], [37])`), comprobando la invariante antes de escribir: los dos primeros intentos se
  negaron a escribir y por eso no rompieron nada. **8.421 → 7.333 fragmentos.**
- **Dos generaciones de apuntes vivían a la vez** en la aplicación (102 partes de las 13:17 y 111 de las
  18:03), las dos aceptadas y mapeadas. La aplicación **rechaza con 409** sustituir versiones de documentos
  distintos, así que se hizo por la vía correcta: `POST /documents` **con `document_id`** añade una versión al
  mismo documento. **101 partes al día, 0 fallos, 101 versiones mapeadas**, y las generaciones viejas quedan sin
  mapear. Aviso: `accept` contesta 409 «ya está aceptada» porque la promoción acepta sola.
- **Resto que no se puede limpiar desde fuera**: las generaciones viejas siguen en la biblioteca y en la
  búsqueda (sin mapear), porque **no hay ruta para retirar un documento**. Es defecto de código.
- **195 preguntas más con su tema**, con un diccionario de términos elegido sobre una partición de
  entrenamiento y medido en **validación** (97,2 % de precisión) y en **prueba** (95,7 %). El primer intento dio
  94,7 % en prueba y **el programa se negó a aplicar nada** en vez de bajar el listón.

## Cierre del 01-10-2026: Guardia Civil, una sola generación y el Código 599 entero

Está entero en **`GUARDIA-CIVIL-UNA-GENERACION-Y-EL-CODIGO-599-2026-09.md`**. Resumen:

- **Tres generaciones del mismo apunte de Guardia Civil**, las tres aceptadas y mapeadas: la primera tenía **17
  tramos** (el 10 % del texto, porque venía de leer el `.md` por sus encabezados) y la vigente **162**. Aquí sí
  sirve `mark-supersedes` (son versiones del mismo documento, no documentos distintos como en TAI).
  **71 versiones retiradas y 59 mapeos quitados en 40 documentos** (25 apuntes, 9 fuentes y 6 exámenes).
- **El mapa de Guardia Civil medía otra cosa**: sólo los mapeos `document_version`, y allí el material está
  mapeado contra **epígrafes** (7.421) y bloques (2.085). Los temas salían con 36-264 fragmentos cuando su
  dossier devuelve cientos de fuentes. Arreglado con las tres vías del mapeo y agregando el **subárbol por
  unión** (no sumando: un documento mapeado en dos niveles del mismo tema se contaba dos veces, como pasó con el
  tema 10, de 71.045 a 53.362). Ahora: **25 de 25 temas con material y 288.087 fragmentos** agregados.
- **El Código 599 estaba dentro con el 2 % de su texto**: de 2.000.000 de caracteres extraídos, la aplicación
  guardó **118.084** en 100 tramos (los tramos se recortan a 1.200). Partido **una norma por documento** con
  `partir_el_codigo_599.py`: **48 normas, 5.408.807 caracteres**, ingeridos **50 de 50** sin incidencias.
- **Epígrafes del temario de Guardia Civil sin material: 55 → 34**, atando cada epígrafe a su norma (cita del
  epígrafe o de sus antecesores, nombre del documento, o la frase del epígrafe en el texto). Los 34 que quedan
  son subdivisiones internas de normas ya mapeadas en su bloque: el límite es que la aplicación mapea por
  documento, no por sección.

## Cierre del 01-10-2026: el texto que estaba extraído y no se podía leer

Está entero en **`TEXTO-EXTRAIDO-QUE-NO-SE-PODIA-LEER-2026-09.md`**. Es el hallazgo más grande de la sesión:

- **De 4.281 versiones, 2.199 guardaban menos del 90 % de su texto.** En total: **195.127.818 caracteres
  extraídos y 71.685.330 guardados** (36,7 %). Faltaban **123 millones de caracteres**, el 63 % del material.
  La causa: un tramo de evidencia se guarda recortado a **1.200 caracteres**, así que un documento largo con
  pocos cortes de sección pierde casi todo (el Código 599: 2.000.000 extraídos, **118.084 guardados**).
- **El texto no había que volver a extraerlo**: está en `datos\extracted\<representación>\texto.txt`. Se cortó
  en bloques de 800 y partes de ≤380.000 caracteres: **78 documentos, 247 ficheros, 72,2 MB**, ingeridos
  **247 de 247** y promocionados como versión nueva del mismo documento, con **871 mapeos heredados**.
- **Resultado**: el texto guardado pasa de **71,7 a 256,6 millones de caracteres (36,7 % → 97,4 %)**; los
  documentos que pierden más de 10.000 caracteres pasan de miles a **1** (el Código 599, a propósito); los
  tramos citables, de **381.874 a 700.277**; y los documentos, de 4.281 a **4.477**.
- **Se hizo por tramos**, bajando el umbral con el mismo procedimiento: 300.000+ (78 documentos), 50.000+ (357),
  20.000+ (373) y 10.000+ (353) → **1.365 ficheros ingeridos y 5.546 mapeos heredados, 0 fallos**.
- **En los temas**: I.7 protección de datos 12.018 → **20.265**; II.4 sistemas operativos 8.596 → **10.023**;
  III.1 modelado de datos 7.155 → **8.341**; IV.7 TCP/IP 3.261 → **5.305**; I.6 sociedad de la información 4.928
  → **6.128**; I.4 empleo público 3.301 → **3.835**; III.5 Java EE y .NET 3.339 → **3.980**.
- **Dos fallos propios, encontrados midiendo**: las partes de un mismo documento se pisaron entre ellas (cada
  una sustituía a la anterior, así que sólo la última quedaba viva, y de `sustituida` no se vuelve: **409**);
  arreglado haciendo **cada parte un documento propio** (169 partes en el primer tramo, 33+1+1 en los demás).
  Y dos ficheros con el mismo nombre se pisaban al escribirlos (247 planeados, 238 en disco).
- **Lo que queda de esa pérdida**: el **2,6 %** (6.958.888 caracteres), en 337 documentos que pierden entre
  5.000 y 20.000 y varios miles que pierden menos de 5.000. Mismo procedimiento con otro umbral.






Cómo se han puesto los temas, todo medido antes de escribirlo: **reglas de término exclusivo** (III.7 282, IV.9 136,
IV.6 122, III.8 66, III.9 55, II.1 42), **reglas de norma** para el bloque I (I.2 98, I.4 83, I.5 91, I.6 105,
I.7 196, I.8 200, I.9 9, I.1 30), la vía medida anterior (110) y las del importador de mazos y cuestionarios
(805). Todo escrito **de uno en uno**: con lotes de 344 filas la aplicación solo aplicó 110 temas (desalineación),
y buscando la pregunta por su enunciado literal solo se encontraba un tercio — se busca por **huella**.

**Lo que no se puede hacer con señales léxicas, medido por cinco vías:** las preguntas sin tema. Texto fuerte:
decide 0. Vocabulario del tema: ~68 % (por debajo del umbral). Nombre del fichero y del documento: 39 % el
primero y **10 preguntas** el segundo. Cita de la pregunta a un documento mapeado: **0 de 8.010** (las citas del
banco apuntan a bancos de preguntas, no a material). Y el clasificador de la aplicación **no clasifica
preguntas**. Para las que quedan hace falta **DEBT-014** (embeddings o modelo local): decisión del propietario.

## Cierre del 30-09-2026 (noche): temas del banco corregidos

Lo de esta última pasada está en **`TEMAS-DE-LAS-PREGUNTAS-CORREGIDOS-2026-09.md`**. Resumen:

| | preguntas |
| --- | --- |
| en total | **16.984** |
| **con tema de TAI** | **9.342** (antes 8.759) |
| sólo con bloque de TAI | 2.238 |
| con tema de Guardia Civil | **241 de 241** (cerrado) |
| sin ningún mapeo | 5.349 |

- **Vía nueva, validada al 99,7 %**: el tema del **conjunto** de la pregunta. Se comprueba escondiendo el tema
  de 6.078 preguntas etiquetadas y prediciéndolo con las demás de su conjunto: **6.062 aciertos**. Ganancia
  real 215 preguntas (poca, porque los conjuntos son de todo o nada).
- **Dos errores de etiquetado a escala, corregidos**: **119 preguntas del Tribunal Constitucional** estaban en
  I.1 y el temario lo pone en **I.2** (la tabla de reglas tenía el término en el tema equivocado), y **216
  preguntas de las Cortes, el Congreso, el Senado y el Defensor del Pueblo** también estaban en I.1. Las dos se
  corrigieron retirando el mapeo por `DELETE` (queda auditado) y poniendo el bueno; 20 leídas al azar para
  comprobarlo. **Efecto: I.1 pasa de 2.317 a 1.988 preguntas e I.2 de 296 a 821** — no hay más preguntas, es
  que 335 estaban contadas en el tema equivocado.
- **164 preguntas más** con tema a partir de las que ya tenían bloque, usando las reglas estrechas restringidas
  al bloque declarado y descartando las cuatro reglas que la medición dejó por debajo del 80 % de precisión.
- **Las 5.349 sin mapeo, contadas por causa**: 2.997 de documentos heterogéneos, 1.341 de documentos
  identificados sin tema declarado, 959 **fuera del alcance** (otras administraciones y otros cuerpos, que el
  propietario dejó fuera) y 53 sin documento de origen.


## Por dónde sigue, con la base medida

1. **III.7 (aplicaciones web): 289 preguntas y 2.520 fragmentos.** Ya no es el tema más flojo en material (lo era
   con 880 y hoy tiene 39 documentos). Lo que sigue flojo de verdad es la **cola de preguntas**: IV.3 (70), IV.4
   (74), III.2 (79), II.2 (83), II.3 (91) y II.1 (93) están por debajo de 100, frente a I.1 con 1.988. El banco
   creció por donde había material, no por donde el temario reparte el peso.
2. **La cola del material** (números corregidos, sin el doble recuento): III.4 (1.033 fragmentos), II.2 (1.107),
   IV.10 (1.214), III.8 (1.241), IV.2 (1.264) y IV.3 (1.390). Ninguno por debajo de 1.000 ni sin nada: el suelo
   que había antes (5 temas por debajo de 50 y 2 a cero) está resuelto, y los **33 de 33** temas tienen material.
3. **La cola del banco**: IV.3 (70), IV.4 (74), III.2 (79), II.2 (83), II.3 (91), II.1 (93), II.4 (94), II.5 (98).
   Los dos con más son I.1 (1.988) e I.2 (821), y ahí está la corrección del cierre de la noche: I.1 tenía 2.317
   porque 335 preguntas que son de I.2 estaban contadas en él.
4. **Guardia Civil 2021-2025**: exámenes legibles (137-158 preguntas) pero **sin clave**: plantillas oficiales
   escaneadas, copias de academias como imagen y OCR con 12-80 números sin leer (medido). Se quedan como material.
5. **Defectos de la aplicación encontrados y reproducidos** (merecen arreglo en el código, no caso por caso):
   - los nombres de campo de las barajas modernas se pierden (`notetypes.config` es **protobuf**, no JSON; los
     nombres están en la tabla `fields`): 4 documentos y 1.851 fragmentos con «campo 1: …»;
   - el **sniffing de 4.096 bytes** clasifica como binario un `.txt` legible si el corte parte un carácter: se ha
     cobrado **ocho** ficheros en esta sesión (2 textos de mazo, 2 partes de apunte, 1 fuente del BOE y **3
     volcados de PreparaTIC** de más de 4.096 bytes, que el relleno anterior no cubría). El relleno ASCII y el
     corte limpio ya se aplican antes de ingerir en todas las tuberías nuevas;
   - un **`.md`** se extrae por sus encabezados y guarda el título como texto del tramo: un apunte de 80 KB quedaba
     en 447 caracteres (0,7 %);
   - **`POST /question-sets/{id}/parse` con `kind=answer_key` devuelve 500** en **11 de 24 conjuntos** y funciona
     en los otros 13, de forma **determinista** (se reintentó con la máquina ociosa y fallan igual). No es por
     posiciones repetidas: los dos grupos las tienen (los que fallan, de 2 a 202; los que funcionan, de 1 a 268).
     Reproducción guardada: cuerpos de error y `set_id` en `F:\OpoFuente\CATALOGO\anuladas-por-no-ser-preguntas.json`
     y en `_oficial\anular-aplicado2.txt`. Efecto: 113 entradas que son texto de norma (no preguntas) siguen sin
     poder anularse; 26 sí quedaron anuladas.
6. **DEBT-014** (embeddings o LLM local): sigue sin decidir, y es decisión del propietario. La búsqueda léxica
   actual responde en 619-1.077 ms con el corpus de hoy.
7. **Los 197 documentos que estaban mudos** (`.epub`, `.xlsx`, `.pptx`) siguen siéndolo **en su formato original**:
   su texto se ha metido convirtiéndolo a `.txt`, pero la aplicación continúa sin saber leerlos. Arreglarlo es un
   defecto de código, no de material: merece la pena porque hay 122 `.epub` de PreparaTIC y 67 hojas de cálculo.
8. **Los 48 temas de PreparaTIC fuera del temario de TAI** están en la biblioteca y se pueden consultar, pero a
   propósito **no están asignados a ningún tema de TAI**.
