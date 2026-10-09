# El texto que estaba extraído pero no se podía leer: 123 millones de caracteres (01-10-2026)

El hallazgo más grande de la sesión, y el más tonto de explicar: **la aplicación extraía el texto y luego lo
tiraba**. De 4.281 versiones aceptadas, **2.199 guardaban menos del 90 % de su texto extraído**; en total se
extrajeron **195.127.818 caracteres y se guardaban 71.685.330**. Faltaban **123 millones de caracteres**, el
**63 %** de todo el material.

## 1. La causa, medida

Un tramo de evidencia se guarda **recortado a 1.200 caracteres**. Un documento largo con pocos cortes de sección
produce pocos tramos, así que casi todo el texto se queda fuera. El caso que lo destapó fue el Código 599 de
Guardia Civil: **2.000.000 de caracteres extraídos, 118.084 guardados** (el 5,9 %), en 100 tramos.

Los diez que más perdían:

| documento | extraído | guardado | % |
| --- | --- | --- | --- |
| ley-9-2017-contratos.txt | 2.000.000 | 107.058 | 5,4 % |
| BOE-031 Código de Contratos | 2.000.000 | 107.326 | 5,4 % |
| 2025 Diccionario conceptos AE | 2.000.000 | 116.501 | 5,8 % |
| BOE-173 Código de Ciberseguridad | 2.000.000 | 127.200 | 6,4 % |
| AndroidNotesForProfessionals.pdf | 2.000.000 | 166.037 | 8,3 % |
| JavaNotesForProfessionals.pdf | 1.911.670 | 168.591 | 8,8 % |
| Seguridad en UNIX y redes.pdf | 1.588.386 | 125.748 | 7,9 % |
| PythonNotesForProfessionals.pdf | 1.430.581 | 191.311 | 13,4 % |
| LPIC 2ª edición | 1.300.990 | 245.002 | 18,8 % |
| Exámenes TAI · Test GSI (v2024).pdf | 1.040.506 | — | — |

## 2. La recuperación

El texto **no había que volver a extraerlo**: está en `datos\extracted\<representación>\texto.txt`. Lo que
faltaba era cortarlo en trozos que quepan antes de ingerirlo — la receta que ya está medida tres veces en esta
sesión (apuntes de Guardia Civil, apuntes de TAI y Código 599). Con
`recuperar_el_texto_que_no_cabe.py`:

| | |
| --- | --- |
| documentos que perdían 300.000 caracteres o más | **78** (63.118.030 caracteres invisibles) |
| partes escritas (bloques de 800, partes de ≤380.000) | **247** ficheros, 72,2 MB |
| corte de 4.096 bytes | comprobado en los 247: **ninguno partido** |
| ingeridos | **247 de 247**, cero sin extraer |
| promocionados como versión nueva del mismo documento | **247**, 0 fallos |
| mapeos heredados de la versión vieja | **871** |

El Código 599 se dejó fuera **a propósito**: sus 48 normas ya están dentro con **5.408.807 caracteres** del texto
del PDF, más que los 2.000.000 que la aplicación extrajo de él, así que volver a ingerir esa versión habría
añadido una copia peor al lado de las buenas.

## 3. Dos fallos míos, encontrados y arreglados

Los dos se vieron midiendo, no suponiendo:

1. **las partes de un mismo documento se pisaron entre ellas.** Se promocionaron todas como versiones del mismo
   documento, cada una marcando que sustituía a la anterior, así que **sólo la última quedó aceptada**. Y de
   `sustituida` no se vuelve: la aplicación contesta **409 «No se puede aceptar una versión «superseded»»**. En
   `JavaNotesForProfessionals.pdf` se ve: cinco partes de 475 tramos y sólo la quinta viva. Arreglado con
   `separar_las_partes_del_texto_recuperado.py`, que hace lo que ya hacían los apuntes: **cada parte es un
   documento propio**, con una cabecera que cambia el contenido para que la aplicación le dé un artefacto nuevo
   (sin eso devuelve el mismo, cuya versión está sustituida). **169 partes separadas, 0 fallos**, y **590 mapeos**
   heredados después.
2. **dos documentos con el mismo nombre de fichero se pisaban en silencio** al escribirlos: se planearon 247
   ficheros y en disco aparecieron **238**. Ahora el nombre lleva sufijo cuando ya existe.

También hubo que arreglar la **herencia de mapeos**: se hacía sólo por la vía `document_version` y en esta
biblioteca la mayoría del material está mapeado como `artifact` o `representation`, así que de 247 ficheros sólo
7 heredaron sus nodos y el texto recuperado no aparecía en ningún tema. Mirando las **tres vías**: 871 mapeos.

## 4. Lo que ha cambiado, medido

| | antes | después |
| --- | --- | --- |
| texto extraído que la aplicación guarda | 71.685.330 (36,7 %) | **203.157.081 (76,3 %)** |
| documentos que pierden más de 300.000 caracteres | 79 | **1** |
| tramos citables | 381.874 | **559.645** |
| documentos | 4.281 | 4.446 |

Y en los temas, donde se nota de verdad (fragmentos):

| tema | antes | después |
| --- | --- | --- |
| II.4 sistemas operativos | 5.740 | **8.596** |
| III.1 modelado de datos | 5.727 | **7.155** |
| III.5 Java EE y .NET | 1.911 | **3.339** |
| IV.7 TCP/IP y OSI | 2.785 | **3.261** |
| IV.8 Internet | 1.476 | **2.428** |
| III.2 lenguajes de programación | 1.578 | **2.054** |
| I.7 protección de datos | 11.066 | **12.018** |
| I.4 empleo público | 2.349 | **3.301** |

Los **33 de 33** temas siguen con material, ninguno por debajo de 1.000 fragmentos (el más flojo, III.4, con
1.033) y ninguno sin preguntas.

## 5. La recuperación, por tramos: hasta el 97,4 %

El primer tramo fue el de los documentos que perdían 300.000 caracteres o más. Como quedaba cola, se fue
bajando el umbral con el mismo procedimiento (y con las dos correcciones del §3 ya dentro: partes como
documentos propios y herencia de mapeos por las tres vías):

| tramo | documentos | ficheros | caracteres recuperados | mapeos heredados | fallos |
| --- | --- | --- | --- | --- | --- |
| 300.000 o más | 78 | 247 | 63.118.030 | 871 | 0 |
| 50.000 o más | 357 | 390 | 39.256.181 | 1.457 | 0 |
| 20.000 o más | 373 | 374 | 12.126.589 | 1.572 | 0 |
| 10.000 o más | 353 | 354 | 5.145.259 | 1.646 | 0 |
| **total** | — | **1.365** | **119.646.059** | **5.546** | **0** |

| | al empezar | al terminar |
| --- | --- | --- |
| texto extraído que la aplicación guarda | 71.685.330 (**36,7 %**) | **256.633.482 (97,4 %)** |
| tramos citables | 381.874 | **700.277** |
| documentos | 4.281 | **4.477** |
| documentos que pierden más de 10.000 caracteres | — | **1** (el Código 599, a propósito) |

### Lo que ha cambiado en cada tema

| tema | antes | después | | tema | antes | después |
| --- | --- | --- | --- | --- | --- | --- |
| I.1 | 9.076 | **9.712** | | III.1 | 7.155 | **8.341** |
| I.2 | 1.864 | **2.057** | | III.2 | 2.054 | **2.152** |
| I.3 | 2.310 | **2.628** | | III.3 | 3.170 | **3.395** |
| I.4 | 3.301 | **3.835** | | III.4 | 1.033 | **1.055** |
| I.5 | 4.552 | **5.378** | | III.5 | 3.339 | **3.980** |
| I.6 | 4.928 | **6.128** | | III.7 | 1.645 | **1.740** |
| I.7 | 12.018 | **20.265** | | III.8 | 1.123 | **1.208** |
| I.8 | 3.142 | **3.992** | | III.9 | 1.882 | **2.124** |
| II.1 | 1.569 | **2.297** | | IV.1 | 3.080 | **3.495** |
| II.2 | 1.107 | **1.126** | | IV.2 | 1.264 | **1.473** |
| II.3 | 3.191 | **3.451** | | IV.4 | 2.032 | **2.361** |
| II.4 | 8.596 | **10.023** | | IV.5 | 6.977 | **7.586** |
| II.5 | 1.900 | **2.514** | | IV.7 | 3.261 | **5.305** |
| | | | | IV.8 | 2.428 | **2.487** |

Los **33 de 33** temas con material, ninguno por debajo de 1.000 fragmentos (el más flojo, III.4, con 1.055) y
ninguno sin preguntas.

## 6. Lo que queda de esa pérdida

**Dos coma seis por ciento** (6.958.888 caracteres), repartido entre 337 documentos que pierden entre 5.000 y
20.000 caracteres cada uno y varios miles que pierden menos de 5.000. No hay ningún documento al que le falte
una parte importante de su texto: el único que quedaba por encima de 10.000 era el Código 599, y se dejó a
propósito porque sus 48 normas ya están dentro con más texto del que la aplicación extrajo de él.

Bajarlo más es el mismo procedimiento con otro umbral (5.000 en vez de 10.000): unos 700 ficheros más para
recuperar 4,3 millones de caracteres. Queda apuntado.

