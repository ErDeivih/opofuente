# La lectura de los apuntes, medida (F35 · punto 1 del §3)

**Base:** `main = c4a7d8d` · rama `f35-lectura` · **datos:** copia verificada de la base real
(`F:\temp-opofuente\f35-datos`, SHA-256 `622aaa6f…`, la real intacta).

Todo lo que sigue está **medido** sobre esa copia: la mitad con el código de antes (`main`) y la otra
mitad con el de esta rama. La real no se ha tocado.

## 1. Las tres cifras que pidió el encargo

| Cifra | Antes | Después |
|---|---|---|
| **Altura de la página del tema** a 1280 px | IV.7 **110.427 px** · I.1 **314.402 px** | IV.7 **20.433 px** (capítulo IV.7.1) · I.1 **118.982 px** (capítulo I.1.1) |
| **Ancho de la columna de texto** a 1280 px | **370 px** | **647 px** (68 caracteres) |
| **`scrollY` al pulsar «Ver en apuntes»** | **0** — el párrafo, a 10.288 px | **6.640** — el párrafo, arriba y a la vista |

Y la misma cifra del enlace con un apartado del **segundo** capítulo (`#apartado-puertos`, el caso que
obliga a abrir el capítulo que lo contiene), a 1280 y a 390:

| «Ver en apuntes» de `puertos` | Antes | Después |
|---|---|---|
| `scrollY` a 1280 px | **0** — el párrafo, a **87.623 px** | **34.971** — el párrafo, a 0 px |
| `scrollY` a 390 px | **0** — el párrafo, a **102.528 px** | **61.022** — el párrafo, a 0 px |

## 2. El índice, que era lo que más molestaba al estudiar

| | Antes (IV.7 / I.1) | Después |
|---|---|---|
| Alto del índice a 1280 px | **1.415 / 1.405 px** | **610 / 752 px** |
| ¿Cabe en la ventana (800 px)? | no | sí |
| ¿Tiene su propio scroll? | no (`sticky`, sin `overflow`) | sí — 446 px de recorrido en I.1 |
| ¿Se puede pulsar el último apartado? | **no** (el 20.º de 25 y el 20.º de 21, fuera de la ventana) | sí: se recorren sus 16 entradas |

## 3. Las tablas

| | Antes | Después |
|---|---|---|
| Ancho de las tablas | forzado al de la columna (370 px) | el suyo (`max-content`) |
| Palabras partidas | sí («Aplic\|ación», «Trans\|porte») | **no** (`overflow-wrap: normal`, `word-break: normal`) |
| Tablas que se desplazan a 1280 px | 0 (cabían a costa de partir las palabras) | IV.7 **7 de 12** · I.1 **37 de 42** |

El ancho natural de estas tablas, medido: mediana de **919 px** en IV.7 y **1.205 px** en I.1, máximo
**3.295 px**. Es decir: **no caben** — cabían rompiendo las palabras.

## 4. Lo que comprueba la prueba, no el ojo

`apps/web/tests/screens/lectura.spec.ts` (seis casos: IV.7, I.1 y el ancla × 1280 y 390) exige, en
cada captura:

- **0 violaciones de axe** (etiquetas `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`, `wcag22aa`);
- **0 errores de consola**;
- la altura menor que la del antes, el índice que cabe en la ventana, la columna ≥ 600 px, las celdas
  sin `overflow-wrap: anywhere`, las tablas que se desplazan, el recuento **plegado** hasta que se
  abre, y el ancla que abre su capítulo y deja el párrafo a la vista.

Las cifras de esta corrida, tal cual salen de la prueba, están en `artifacts/lectura/medidas.json`;
las de antes, en `artifacts/lectura/antes/medidas-probe.json` y `…/medidas-ver-en-apuntes.json`. Los
PNG (antes y después, a 1280 y 390) están en `artifacts/lectura/antes/` y `artifacts/lectura/despues/`
y **no se rastrean**: son artefactos generados, como los de `artifacts/screens/`.

**La nota al margen cae debajo del párrafo a todas las anchuras**, y no es una preferencia: el lienzo
del alumno está limitado a **1080 px** por el diseño, y dentro de él caben el índice (208), los huecos,
el relleno de la tarjeta y **o** el texto con sus 68 caracteres **o** la columna de la nota. Medido a
**1600 px** con las tres columnas: el texto se quedaba en **582 px (61 caracteres)** en vez de 647.
Como lo que el propietario pidió es que el texto tenga un ancho de lectura cómodo, manda el texto. Lo
comprueba la prueba de `tests/screens/lectura.spec.ts` a 1600 px.

## 5. Lo que NO mejora, dicho por su nombre

**El capítulo más grande de I.1 sigue midiendo 118.982 px.** El tema de la Constitución tiene **cuatro
epígrafes oficiales** y sus 21 apartados están repartidos así:

| Capítulo | Apartados | Caracteres | Alto medido a 1280 px |
|---|---|---|---|
| I.1.1 «La Constitución Española de 1978.» | **12** | 247.505 | **118.982** |
| I.1.2 «Derechos y deberes fundamentales.» | 5 | 70.167 | — |
| I.1.3 «Su garantía y suspensión.» | 2 | 17.932 | — |
| I.1.4 «La Corona: funciones constitucionales del Rey.» | 2 | 37.725 | — |

Es decir: **I.1.1 se lleva 12 de los 21 apartados (el 66 % del texto)** porque el programa oficial da
a ese tema cuatro epígrafes y nada más. Paginar por epígrafes es lo que el propietario pidió y es lo
que se ha hecho; el capítulo que queda gordo es el que el programa define como gordo. Si esa página
sigue siendo incómoda, lo que hay que revisar es **la granularidad de los epígrafes de I.1**, no la
paginación.

Los otros temas quedan repartidos de forma mucho más razonable: IV.7 son dos capítulos (6 y 19
apartados) y su página de entrada baja de 110.427 a 20.433 px.
