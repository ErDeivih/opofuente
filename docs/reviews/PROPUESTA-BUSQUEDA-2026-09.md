# La búsqueda tarda un segundo: de dónde sale y qué hacer (septiembre 2026)

La búsqueda es la puerta principal de la aplicación: cuando alguien estudia, escribe una pregunta y espera
material. Hoy esa espera es de **un segundo de mediana y 2,5 segundos en el p95**, medido con **56 preguntas
reales de los exámenes oficiales** sobre el corpus cargado (3.000 documentos, más de 100.000 pasajes
citables). Esto desglosa ese segundo con medidas y propone por dónde empezar.

Antes de esto yo había escrito —en los informes de DEBT-014— que la búsqueda respondía «en decenas de
milisegundos» y que, por tanto, un índice de vectores solo podría comprar calidad. **Era falso**: la medida
manda, y cambia la conclusión.

## 1. Lo medido

### El tiempo de la API

| | |
| --- | --- |
| consultas medidas | 56 (preguntas reales, TAI y Guardia Civil) |
| latencia mediana | **1.027 ms** |
| latencia p95 | **2.466 ms** |
| consultas con algún resultado | 56 de 56 |

**Actualización (29-09)**: repetida sobre el corpus de hoy (**3.101 documentos y 187.283 fragmentos**, que es
más material que cuando se midió), con cuatro consultas repetidas cinco veces cada una
(`medir_latencia_de_busqueda.py`): **mediana 802 ms · p95 1.106 ms · máxima 1.164 ms**. La latencia no ha
empeorado al crecer el corpus, que es lo que se quería saber antes de decidir sobre el índice.

### De qué depende

La misma búsqueda con una palabra, con tres y con la pregunta entera:

| consulta | mediana | p95 |
| --- | --- | --- |
| una palabra | 460 ms | 742 ms |
| tres palabras | 592 ms | 845 ms |
| pregunta entera | 1.003 ms | 2.342 ms |

Hay un **suelo de medio segundo** y un coste que crece con el número de términos.

### Qué parte está en la consulta y cuál en el resto

La aplicación construye la expresión léxica uniendo **todos** los términos con `OR` y con **prefijo**
(`"palabra"*`), así que una pregunta de veinte palabras son veinte exploraciones de prefijo que después se
fusionan. Ejecutando la **misma consulta** sobre una copia de la base y cambiando solo la expresión:

| variante | mediana | p95 | acuerdo de los 5 primeros |
| --- | --- | --- | --- |
| **la de hoy** (OR + prefijo, todos los términos) | 286 ms | 934 ms | — |
| sin prefijo | 237 ms | 521 ms | 85,3 % |
| seis términos con prefijo | 99 ms | 228 ms | 82,7 % |
| seis términos sin prefijo | 83 ms | 207 ms | 84,0 % |
| **seis términos con `AND` y prefijo** | **4 ms** | **8 ms** | 84,0 % |
| solo el índice, sin los `JOIN` | 79 ms | 484 ms | 100 % |

Tres cosas que dicen estos números:

1. **El prefijo y el `OR` son el grueso del coste.** Con `AND` sobre seis términos, la misma consulta pasa de
   286 ms a **4 ms**: setenta veces menos, y el 84 % de las cinco primeras respuestas sigue siendo el mismo.
2. **Los `JOIN` no son el problema**: sin ellos la consulta baja a 79 ms, sí, pero siguen siendo 79 ms; el
   cuello está en cómo se busca, no en cómo se junta.
3. **La API tarda 1.027 ms y la consulta 286 ms**: hay unos **700 ms que se van en el servicio** —resolver el
   ámbito del programa, la revisión del corpus, armar la vista de cada resultado—. No he medido cuál de esas
   tres cosas se los lleva: **habría que instrumentarlo**, y no voy a decir cuál es por intuición.

## 2. La calidad: la búsqueda devuelve el examen, no la norma

La velocidad es solo la mitad del problema. Se midió **si la búsqueda encuentra el documento donde está la
respuesta**, con verdad de referencia conocida de antemano: las preguntas oficiales de TAI que **nombran su
norma** («conforme al artículo 21 de la Ley 50/1997…») y el documento de esa norma, que está en la biblioteca
porque se descargó del BOE. 26 preguntas cumplen eso.

| | buscando en todo el corpus | dejando fuera exámenes y bancos |
| --- | --- | --- |
| la norma aparece entre los resultados | 12 de 26 | **14 de 26** |
| aparece en los **cinco primeros** | **0** de 26 | **10** de 26 |
| MRR (media de 1/puesto) | **0,083** | **0,216** |
| consultas cuyo primer resultado es un examen | **26** de 26 | 4 de 26 |

Lo que estaba pasando es fácil de entender: el **enunciado de la pregunta está en el examen**, que también
está en la biblioteca, así que el examen gana siempre por coincidencia literal. Quien estudia escribe su
pregunta y recibe… la pregunta. La norma que la responde queda enterrada.

Y el arreglo medido es baratísimo: **dejar fuera 39 documentos de 3.016** (los de tipo examen, banco de
preguntas, plantilla y caso práctico) lleva la norma que se busca del puesto «nunca en los cinco primeros» a
**10 de 26 en el top 5**. Sin dependencias nuevas y sin tocar el motor de búsqueda: es un filtro de corpus,
que la aplicación ya sabe aplicar (`document_ids`, `document_type`).

Queda margen: en 12 de 26 consultas la norma **no aparece** en veinte resultados. Ahí sí hay algo que comprar
—con vectores o con una consulta mejor—, pero primero lo barato.

## 3. Qué propongo, en este orden

1. **Modo estudio: dejar fuera el material de examen.** 39 documentos de 3.016, sin dependencias nuevas, y la
   norma buscada pasa de 0 a 10 veces en los cinco primeros puestos. Es el mejor cambio por esfuerzo de todo
   el informe.
2. **Cambiar la expresión** (lo segundo más barato): buscar primero con `AND` sobre los términos más
   significativos y **caer a `OR`** si esa búsqueda no devuelve nada. La consulta baja de 286 ms a **4 ms** y
   mantiene el 84 % de los cinco primeros resultados.
3. **Medir los 700 ms del servicio** antes de tocarlos: una instrumentación sencilla (cronometrar la
   resolución de ámbito, la revisión y el armado de la vista) dice dónde está. No se ha mirado.
4. **Vectores después**, si con lo anterior la norma sigue sin aparecer en las 12 consultas donde no sale. Con
   los números actuales **sí saldría a cuenta** (incrustar la consulta, decenas de ms; búsqueda por fuerza
   bruta, 1,76 ms), con dos condiciones: la pasada inicial **por tandas** —empezando por los fragmentos de los
   apuntes y los exámenes, no por los 124.000 de golpe, que son unas 20 horas de CPU— y mantenerlos al día.
5. **El modelo de lenguaje, lo último**, y solo para tareas concretas (corregir la respuesta a una pregunta
   con la evidencia delante). Su coste real no es generar (~70 tokens/s) sino preparar la evidencia: unos 15
   segundos hasta la primera palabra con 4.000 token, así que el expediente tiene que caber en 1.500-2.000.

## 4. Lo que sigue faltando para cerrar DEBT-014 con un número

Una prueba de calidad **más ancha**: las 26 consultas con verdad de referencia son pocas y todas del bloque
jurídico. Habría que repetirla con preguntas técnicas (donde la respuesta está en un apunte, no en una norma)
y con más volumen, y con eso el número —MRR— diría si los vectores hacen falta de verdad.

## 5. Cómo se ha medido (para poder repetirlo)

- `_oficial/medir_busqueda.py`: 56 preguntas reales contra la API, latencia y número de resultados.
- `_oficial/medir_coste_busqueda.py`: la misma búsqueda con una, tres y todas las palabras.
- `_oficial/medir_variantes_fts.py`: la consulta de la aplicación sobre una **copia** de la base, cambiando
  solo la expresión, y midiendo además el **acuerdo** de los cinco primeros resultados (una variante que
  tarda la mitad pero devuelve otra cosa no sirve).
- `_oficial/medir_calidad_busqueda.py`: 26 preguntas con **verdad de referencia** (su norma, que está en la
  biblioteca), midiendo puesto, MRR y cuántas veces lo primero que sale es un examen; con `--sin-examenes`
  repite la medida excluyendo el material de examen.
- Informes: `F:\OpoFuente\CATALOGO\medida-busqueda.md`, `coste-busqueda.md`, `variantes-fts.md` y
  `calidad-busqueda.md`.

