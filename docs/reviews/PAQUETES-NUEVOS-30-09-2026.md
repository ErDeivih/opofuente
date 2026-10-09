# Los paquetes nuevos de la bandeja (30-09-2026)

Llegaron **13 paquetes nuevos** a `F:\OpoFuente\zips` (111 MB comprimidos): el temario actualizado de 2026, el
de 2025, cuestionarios, bases de datos de preguntas y de prácticas, un PDF de 1.600 preguntas de la Constitución
y unas correcciones de apuntes. Esto es qué es cada cosa, dónde se ha puesto y qué ha salido de ahí.

## Qué era y dónde ha ido

| paquete | qué trae | dónde va |
| --- | --- | --- |
| `BLOQUE 1..4.7z` y `1. TAI_2026.7z` | **temario actualizado 2026**, un documento por bloque (docx y pdf) | biblioteca |
| `1. TAI TEMARIO ACTUALIZADO 2025.7z` | temario de 2025 por bloques y con los temas por separado (74 ficheros) | biblioteca |
| `2. Html_Preguntas_Examenes_2025.7z` | `Pool_Preguntas_TAI.html`: **760 preguntas** por bloque en un array de JavaScript | banco de preguntas |
| `3. Html_Preguntas_Temario.rar` | 21 cuestionarios por tema, pero con las definiciones en JavaScript: **215 definiciones** | biblioteca (convertidas a texto) |
| `3. RecursosNuevos_2026 (Por revisar).7z` | `Preguntas_Examenes_2026.db`: **540 preguntas** de convocatorias con bloque, tema y respuesta | banco de preguntas |
| `4. Tai_BBDD_2025.7z` | `Tai_BBDD_2025.db`: **868 preguntas** con bloque y respuesta | banco de preguntas |
| `5. BBDD_Practicas.rar` | `colegio1.db`, `Poke.db`: bases de datos para practicar SQL | biblioteca (volcadas a `.sql`) |
| `1600_preguntas_constitucion_espanola_1.pdf` | **1.641 preguntas** de la Constitución **con su plantilla al final** | banco de preguntas |
| `Apuntes_Correciones.docx` | correcciones de los apuntes | biblioteca |

## Lo que ha salido de ahí, medido

Preguntas sacadas de los paquetes (`preguntas_de_los_paquetes_nuevos.py`):

| fuente | con respuesta y opciones | nuevas para el banco |
| --- | --- | --- |
| `Tai_BBDD_2025.db` | 868 | **826** |
| `Preguntas_Examenes_2026.db` | 540 | **209** |
| `Pool_Preguntas_TAI.html` | 760 | **33** |
| `1600_preguntas_constitucion_espanola_1.pdf` | 1.639 | **1.544** (medido aparte) |

Y el banco, antes y después:

| | antes | después |
| --- | --- | --- |
| preguntas | 2.399 | **5.359** |
| con cita | 2.396 | **5.348** |
| con tema | 1.116 | **3.901** |
| sin opciones | 0 | 0 |
| documentos en la biblioteca | 3.101 | **3.201** |
| versiones aceptadas | 3.113 | **3.213** |

Las preguntas nuevas **no** se han echado a un cajón: se han escrito en textos limpios, se han ingerido y se han
importado con `import-document`, así que **cada una tiene su cita** (de qué documento sale) y su **respuesta**. Y
traen su **bloque** del programa, que es un dato de la fuente, no una suposición: 3.901 de las 5.359 quedan
enlazadas a un nodo (1.544 de ellas al tema I.1, porque todas son de la Constitución).

Los cuatro conjuntos nuevos son, por tamaño: `1600_preguntas_constitucion_espanola_1` (**1.547**),
`Tai_BBDD_2025` (**839**), `Preguntas_Examenes_2026` (**540**) y `Pool_Preguntas_TAI` (34). Con el resto de TAI
(27 conjuntos) el banco de la oposición queda en **5.118 preguntas**.

## Dos fallos de lectura que hubo que arreglar, con su medida

El PDF de la Constitución destapó dos cosas del lector de claves y preguntas, las dos del mismo tipo: un tope de
cifras que no se había visto antes.

1. **El número de pregunta puede tener cuatro cifras.** El PDF numera hasta 1.641 y el lector solo aceptaba tres:
   leía **1.003 preguntas** de 1.641 y las 638 de cuatro cifras se perdían. Arreglado en
   `buscar_respuestas_marcadas.py`: ahora lee **1.642** de 1.641 (una de más, por una línea que se confunde con
   un enunciado) y solo quedan 2 sin responder de las 1.641.
2. **La línea de la clave puede llevar más de un separador.** La plantilla de ese PDF escribe `1613.- D` (punto
   **y** guion) y el lector admitía uno solo: **0 tablas de clave**. Arreglado en `cosechar_claves_propias.py`:
   ahora lee **1.641 respuestas** en una tabla.

El reparto de respuestas del PDF (A 426, B 429, C 387, D 397) es el de una plantilla de verdad, no el de una
columna mal leída.

## Lo que se ha dejado fuera, y por qué

- **`users_Register`**, la tabla del pool con **usuarios y contraseñas de otras personas**: no se ha copiado a
  ninguna parte, ni al banco ni a ningún volcado. La base se conserva como material, pero esa tabla no se lee.
- Las tablas de preguntas de las bases de datos **no** se vuelcan a texto: sus preguntas ya están en el banco,
  que es su sitio; volcarlas otra vez sería duplicar.
- 19 enunciados del PDF de la Constitución que eran un número de sección suelto (el enunciado real se había
  quedado en la pregunta anterior): fuera, porque con eso por delante no se pueden estudiar.
- Los ficheros temporales de Word (`~WRL*.tmp`, `~$…docx`) que vienen dentro de los paquetes: no son material.

## Los cuestionarios por tema: convertidos a texto, no metidos a medias

Los 21 HTML por tema (comandos de Linux, puertos, diagramas UML, amenazas, HTTP, MPLS…) tienen su contenido en
un objeto de JavaScript, así que el extractor de HTML de la aplicación solo veía la cáscara de la página
(medido: **1 fragmento de 12 caracteres**). Se han convertido a texto —**215 definiciones**— y ahora están en la
biblioteca como cualquier otro documento. Lo mismo con las **bases de datos de prácticas**: se han volcado a
`.sql` (28 KB entre las dos) porque un `.db` no se puede leer desde la aplicación.

## Cómo se reproduce

```powershell
python extraer_paquetes_nuevos.py --aplicar                 # descomprime los 13 paquetes
python preguntas_de_los_paquetes_nuevos.py --escribir       # bases de datos y HTML → jsonl
python preguntas_de_la_constitucion.py --escribir           # el PDF de 1.600 preguntas → jsonl
python respuestas_verificadas_a_la_app.py --nuevas --solo-textos
python respuestas_verificadas_a_la_app.py --nuevas --aplicar --refrescar
python respuestas_verificadas_a_la_app.py --nuevas --nuevas-fichero "F:\OpoFuente\BANCO\preguntas-1600-constitucion.jsonl" --solo-textos
python respuestas_verificadas_a_la_app.py --nuevas --nuevas-fichero "F:\OpoFuente\BANCO\preguntas-1600-constitucion.jsonl" --aplicar
python convertir_practicas_y_glosarios.py --aplicar          # .db → .sql y HTML → .txt
python ingerir_carpeta.py "F:\OpoFuente\TAI\internet\practicas-y-glosarios"
python rellenar_biblioteca.py                               # promociona y acepta las versiones
python banco_por_tema_de_la_app.py                          # el banco por tema, otra vez
```

## Qué queda de estos paquetes

- Los **cinco `.db`** siguen en la biblioteca como material conservado sin texto (no hay extractor de SQLite):
  su contenido útil ya está convertido o en el banco.
- Los **cuestionarios por tema** convertidos son definiciones sueltas (5 a 66 por fichero): sirven para buscar y
  para repasar, no para preguntar. Donde de verdad aportan es en los apuntes del tema, y ahí queda trabajo por
  hacer: enlazarlos con el tema al que pertenecen.
- El **temario 2026** ya está en la biblioteca (3.653 fragmentos entre los cuatro bloques): es el material sobre
  el que conviene rehacer los apuntes por tema, porque es la versión actualizada.
