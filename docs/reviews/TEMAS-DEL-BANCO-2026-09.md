# El banco, enlazado a su tema (29-09-2026)

El banco de la aplicación tenía **2.399 preguntas** y solo **673 con tema**: las 1.726 del banco privado de TAI
no estaban enlazadas a ningún nodo del programa, así que no se podía estudiar por temas ni saber qué queda
flojo. Esto es lo que se ha hecho, con las medidas delante.

## Resultado

| | antes | después |
| --- | --- | --- |
| preguntas con tema | 673 (28,1 %) | **1.116 (46,5 %)** |
| preguntas sin tema | 1.726 | **1.283** |
| con cita | 2.396 | 2.396 |
| sin clave | 11 | 11 |
| preguntas nuevas creadas al enlazar | — | **0** |

Nada más se movió: enlazar un tema **no toca** la cita, la clave ni el enunciado, y eso se comprobó después
(2.396 con cita y 11 sin clave, igual que antes).

## Las señales, medidas antes de usarlas

La referencia es independiente del método que se mide: el tema de las **142 preguntas de examen oficial**
que lo tienen por **el orden del examen** (`bloques_por_vecinos.py`, que acertó el 100 % sobre 120 anclas),
no por su texto. Contra ella (`medir_metodos_contra_oficiales.py`):

| método | acierta |
| --- | --- |
| por el texto, **dos o más palabras** del título oficial | **96,2 %** (127 de 132) |
| por el texto, una sola palabra (*enlace flojo*) | muestra de 10: no decide nada |
| por el vocabulario del tema (TF-IDF sobre los fragmentos del tema, margen ≥ 0,08) | 66,7 % (16 de 24) |
| por el **bloque** (I, II, III, IV) cuando el tema no se puede decidir | 23,5 % → descartado |

Y dos señales más que se probaron y **no** se usaron, con su número:

- la **norma que cita la pregunta**, buscada en el vocabulario de cada tema: acuerdo del 20 % sobre 30
  preguntas (los fragmentos de un tema no siempre nombran la norma que tratan);
- la misma norma, buscada en los **apuntes** del tema (donde sí se nombran): acierta 4 de 4, pero solo
  **decide en 4 de 142** preguntas y en el banco privado resuelve 19. No compensa.

## Qué se enlazó y qué no

Se enlazan **443** preguntas del banco privado:

- **393 por el texto** con dos o más palabras del título (el método del 96,2 %);
- **50 heredadas** de un examen oficial: la misma pregunta, con la misma huella, ya tenía tema allí. Eso es un
  dato, no una decisión.

Se dejan **sin tema 1.275** y se dice por qué, sin esconderlo:

- **634** con enlace flojo (una sola palabra del título). Ejemplo de por qué se dejan: «La Ley 56/2007, de
  Medidas de Impulso de la Sociedad de la Información» cae en el tema de las bases de datos;
- **559** sin ninguna señal de texto;
- **82** que solo decidía el vocabulario del tema, con el 66,7 % medido. **Poner el tema mal es peor que no
  ponerlo**, porque el banco se estudia por temas: una pregunta de otra cosa en el tema que estás estudiando
  es peor que una pregunta sin clasificar.

Los tres grupos están en `F:\OpoFuente\BANCO\por-tema-de-la-app\SIN-TEMA.md`, una a una.

## Cómo se enlazó, sin reimportar nada

La importación por CSV de la aplicación reconoce cada pregunta por su **huella** (enunciado normalizado y
juego de opciones sin orden) y, cuando ya está, no la crea: solo le aplica la columna `topic`, que es la ruta
del nodo (`I.1`, `III.9`…). Así que se manda un CSV por conjunto con las mismas preguntas y su tema.

Dos guardas, las dos por un defecto que ya había pasado:

1. solo se mandan filas cuya huella está **ya** en ese conjunto (comprobado contra una copia coherente de la
   base): una fila que no encajara crearía una pregunta **sin cita**;
2. **no** se manda la columna `correct`: el tema se añade, las claves no se tocan.

Resultado de todas las peticiones (una por conjunto y tramo): **creadas 0** en todas.

## El banco por tema, escrito

`F:\OpoFuente\BANCO\por-tema-de-la-app\` (regenerable con `banco_por_tema_de_la_app.py`, leído de la base de
la aplicación, que es donde vive el banco):

- `TAI\`: **876 preguntas en 34 nodos** del programa; de los 33 temas, solo 3 no tienen ninguna pregunta;
- `GUARDIA-CIVIL\`: **240 preguntas en 24 nodos**; de sus 25 temas, 1 sin ninguna;
- un fichero por tema con el enunciado, las opciones, **la respuesta marcada**, de qué conjunto sale y de qué
  documento está citada;
- `LEEME.md` por convocatoria con el recuento, y `SIN-TEMA.md` con las que faltan.

Las dos convocatorias van separadas a propósito: cada oposición numera sus temas a su manera y un índice
común no significaría nada.

## Cómo se reproduce

```powershell
python medir_metodos_contra_oficiales.py          # el acierto de cada método contra la referencia
python medir_norma_en_apuntes.py                  # la señal de la norma, medida
python medir_bloque_cuando_no_hay_tema.py         # el bloque como plan B, medido
python temas_del_banco_en_la_app.py               # informe de lo que se enlazaría
python temas_del_banco_en_la_app.py --aplicar     # lo enlaza
python cobertura_de_temas.py                      # cuánto queda con tema y cuánto sin
python banco_por_tema_de_la_app.py                # escribe el banco por tema desde la aplicación
```

## Qué queda

- **1.283 preguntas sin tema.** Ninguno de los métodos medidos llega al listón en ellas. Es candidato claro
  para lo que decida el ADR de DEBT-014: un clasificador por **embeddings** (similitud pregunta ↔ temario)
  es justo lo que falta aquí, y ahora hay una referencia medida (el tema de los exámenes oficiales por orden)
  para evaluarlo sin discutir.
- La herencia desde exámenes oficiales solo cubrió **50** preguntas: el banco privado y los exámenes
  oficiales casi no comparten preguntas literales.

## Un intento más, también medido (29-09)

Se probó una cuarta señal, más de fondo que las anteriores: **a qué tema pertenece el material al que se
parece la pregunta** (`medir_tema_por_el_corpus.py`). Para cada pregunta se pide a la **búsqueda de la
aplicación** sus cinco mejores fragmentos, se descartan los que son material de examen o banco de preguntas
(una pregunta se parece a otra pregunta, y eso no dice de qué tema habla) y se vota el tema del documento del
que sale cada fragmento.

Medido contra la misma referencia independiente:

| | resultado |
| --- | --- |
| decide | **10 de 142** |
| acierta | 6 de 10 (**60 %**) |

No sirve: decide en muy pocas y, cuando decide, acierta menos que el vocabulario del tema. La causa está a la
vista en los números: solo 485 representaciones de TAI tienen mapeo a un **tema** (el resto del material está
mapeado a **bloque**), así que la mayoría de los aciertos de búsqueda no dan ningún tema con el que votar.

Queda escrito para no repetirlo: **no** se usa para las 1.283.

De paso quedó medida la latencia real de la búsqueda con el corpus de hoy (187.283 fragmentos):
**mediana 802 ms y p95 1.106 ms** por consulta, que es el número que le hace falta al ADR de DEBT-014 cuando
compare alternativas.
