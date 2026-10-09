# El banco de preguntas: copias, citas y opciones cortadas (29-09-2026)

Trabajo sobre el banco privado de TAI: 1.845 preguntas repartidas en 21 conjuntos que se metieron con un
importador automático. Tres defectos, los tres **medidos**, y los tres arreglados. Las cifras son de la base
de la aplicación antes y después, leídas con `_oficial/estado_del_banco.py` y `_oficial/preguntas_sin_cita.py`.

| | antes | después |
| --- | --- | --- |
| preguntas en el banco | 2.526 | **2.399** |
| con cita | 2.500 | **2.396** |
| **sin cita** | 26 | **3** |
| sin ninguna opción | 27 | **0** |
| sin clave | 61 | **11** |
| con tema asignado | 673 | 673 |
| banco privado de TAI | 1.845 preguntas en 21 conjuntos | **1.718 en 19 conjuntos, 1.716 con cita** |
| exámenes oficiales de TAI | 440 preguntas, 440 con cita | 440 preguntas, **440 con cita** |
| Guardia Civil (oficial) | 241 preguntas, 240 con cita | 241 preguntas, **240 con cita** |

Y la comprobación que más dice: comparando el banco con **el texto que se ingirió**, pregunta a pregunta y
opción a opción (`_oficial/comprobar_banco_contra_textos.py`) salen **1.710 de 1.716 iguales** (99,65 %). Las
6 diferencias están identificadas y son del origen, no del banco (abajo).

## Causa 1 · El tope de 500 fragmentos (las 393 preguntas sin cita)

De un `.txt`, la aplicación saca **un fragmento por párrafo** (bloque separado por una línea en blanco) y
**deja de partir en 500** (`apps/api/opofuente/infrastructure/extractors/text_files.py`,
`MAX_BLOCK_SECTIONS`). Lo que sobra no tiene fragmento, y una pregunta sin fragmento **no puede citarse**
porque `import_from_document` lee el texto reconstruido a partir de los fragmentos
(`apps/api/opofuente/application/question_service.py`, `_texto_de_la_version`).

Medido: la versión de 323.507 caracteres tenía 500 fragmentos y cubría el 56,3 % del texto. En el conjunto de
la cosecha, **393 preguntas de 872** entraban sin cita (las creaba el CSV, no el documento).

**Arreglo**: el texto se parte en trozos de 200 preguntas y cada trozo va como documento propio al **mismo**
conjunto. Ningún documento llega a 500 párrafos (los nuevos tienen 210-214) y todas las preguntas tienen
fragmento del que citarse.

## Causa 2 · Mi regla de «son la misma pregunta» no era la de la aplicación

La aplicación no duplica una pregunta si su **huella** coincide
(`apps/api/opofuente/domain/questions.py`, `question_fingerprint`): enunciado normalizado y **juego de
opciones sin orden**. Mi criba de copias usaba enunciado recortado a 90 caracteres, opciones en orden y
letra. Con esa regla, **36 filas** que la aplicación consideraba la misma pregunta le llegaban como nuevas: el
documento no las creaba y el CSV las metía **sin cita** (8 de ellas se veían una a una).

**Arreglo**: la criba usa **la huella de la propia aplicación**, importándola de su código
(`from opofuente.domain.questions import question_fingerprint`), no una reimplementación parecida. Efecto
medido: el fichero de la cosecha pasa de 880 filas a **827**, que es exactamente lo que la aplicación crea.

También se corrigió una idea **falsa** que yo había dejado escrita en el script: creí que rechazaba la
segunda pregunta con el mismo enunciado dentro de una importación y repartí los enunciados entre partes. Era
otra cosa (la huella), y repartirlos no arreglaba nada y desordenaba las preguntas: está deshecho.

## Causa 3 · El texto de un fragmento se corta en 1.200 caracteres (opciones a medias)

`apps/api/opofuente/infrastructure/document_repository.py` tiene `MAX_EVIDENCE_CHARS = 1200`: el texto de un
fragmento se recorta a 1.200 caracteres. Como el importador **reconstruye** el texto con los fragmentos, una
pregunta cuyo bloque pasaba de 1.200 caracteres llegaba al banco con la última opción cortada. Se vio
comparando preguntas gemelas: la citada tenía `…que tenga como objetivo o consecuencia a` y la que entró por
CSV tenía la opción entera.

Medido en los textos de la cosecha: 3, 2, 2 y 2 bloques por cada 200 preguntas pasaban del tope (el mayor,
1.579 caracteres).

**Arreglo**: cuando un bloque pasa de 1.000 caracteres, el enunciado y cada opción van en **párrafos
distintos**, así que ningún fragmento se acerca al tope. Que el analizador sigue leyendo la pregunta entera se
comprobó **con su analizador**, no con una idea: `_oficial/probar_parrafos_en_pregunta.py` prueba las tres
formas (normal, línea en blanco tras el enunciado, línea en blanco entre todas las opciones) y las tres
devuelven 2 preguntas con 4 opciones y los mismos 352 caracteres en cada opción.

**Arreglo 2 (limpieza)**: además se amplió la limpieza del texto con las formas de pie de página que
quedaban, contadas sobre los textos ingeridos (7.501 líneas de opción, 50 con restos): `2019 – GSI - PI`
(26), `Modelo: 1` (22), `2024 - TAI-L – MODELO A` (11), `Página 9 de 20` (4) y
`PLANTILLA DEFINITIVA DE RESPUESTAS…` (3). Las que empiezan por un año y una sigla, por `Página N de M`, por
`Modelo: N` o por `PLANTILLA DEFINITIVA` no pueden ser una opción de verdad: se cortan siempre. `MODELO A`
en minúsculas sí puede ser una opción («el modelo A de la Constitución»), así que ese se corta solo detrás de
un cierre de frase.

## Causa 4 · Preguntas que no se pueden contestar

**27 preguntas** del banco no tenían ninguna opción: salen de PDF en los que las opciones eran imágenes o no
se pudieron extraer. Una pregunta sin opciones ocupa sitio y no se puede estudiar. Ahora se dejan fuera al
importar **y se dice cuántas** (51 filas en la cosecha, 42 en las parejas): filtrar en silencio sería el otro
error.

## Lo que queda abierto (medido, no supuesto)

- **3 preguntas sin cita** en todo el banco: una en el examen oficial de Guardia Civil (modelo A) y dos en
  conjuntos de TAI. Las tres son de un enunciado que **ya está citado** en su conjunto y con opciones
  distintas; entran por CSV porque la aplicación no crea una segunda pregunta con la misma huella. Están con
  su clave; lo que no tienen es cita.
- **6 diferencias** entre el banco y el texto ingerido, todas por opciones **vacías** en el fichero de origen
  (la aplicación descarta la opción vacía y el texto mantiene el hueco).
- **Los conjuntos de examen oficial de TAI** (ingreso libre y promoción interna 2025, 440 preguntas) **no se
  han rehecho**: su origen, `BANCO-oficial\\tai-*.jsonl`, tiene extracciones sucias en algunas filas (una
  opción se traga la frase siguiente). Compararlos contra los ficheros del banco privado da 8 avisos de
  «truncada» que son **falsos**: el banco está limpio y el fichero sucio. Arreglar esas filas es trabajo de
  extracción, no de importación.
- **`_copias` llegó a 43 GB y llenó el disco F:** (`database or disk is full` al copiar). `bd_snapshot.py`
  hacía una copia de 600 MB en **cada** consulta. Ahora poda: conserva una copia por nombre y **seis en
  total** (podar solo por nombre dejaba 20 copias y 10 GB, porque cada script usa el suyo). Estado tras
  limpiar: **8 copias y 3,57 GB**, con **39,8 GB libres** en F:.
- **La biblioteca** queda en 3.082 documentos y 3.094 versiones aceptadas; el banco, en 25 conjuntos
  (19 privados de TAI, 4 de examen oficial de TAI y 2 de Guardia Civil) y 2.399 preguntas.
- Las **27 preguntas sin opciones** se han quitado del banco, pero siguen en los `.jsonl` de origen: si algún
  día se rehace la extracción con OCR de esas páginas, se recuperan.

## Cómo se reproduce

```powershell
# 1. textos limpios (no aplica nada)
python respuestas_verificadas_a_la_app.py --cosecha --solo-textos
python respuestas_verificadas_a_la_app.py --parejas  --solo-textos
python respuestas_verificadas_a_la_app.py            --solo-textos
# 2. ingerir la carpeta y esperar
python ingerir_carpeta.py "F:\OpoFuente\TAI\internet\respuestas-verificadas"
python esperar_lote.py --ultimo
# 3. deshacer los conjuntos viejos y volver a meterlos
python deshacer_conjuntos.py --prefijo "TAI ·" --aplicar
python respuestas_verificadas_a_la_app.py --cosecha --aplicar --refrescar
python respuestas_verificadas_a_la_app.py --parejas  --aplicar
python respuestas_verificadas_a_la_app.py            --aplicar
# 4. comprobar
python estado_del_banco.py
python preguntas_sin_cita.py --todos
python comprobar_banco_contra_textos.py
```

## Ficheros

- `_oficial/respuestas_verificadas_a_la_app.py`: trocea en partes, usa la huella de la aplicación, deja fuera
  las preguntas sin dos opciones y avisa si una parte se acerca al tope de fragmentos.
- `_oficial/limpieza_texto.py`: limpieza del enunciado y las opciones (pies de página medidos y palabras
  cortadas por el salto de línea, conservando el guion de una bandera `--all- databases`).
- `_oficial/deshacer_conjuntos.py`, `_oficial/deshacer_conjunto.py`: deshacer conjuntos, con una sola copia
  de seguridad para todos.
- `_oficial/preguntas_sin_cita.py`, `_oficial/por_que_sin_cita.py`, `_oficial/comparar_gemelas.py`,
  `_oficial/comprobar_banco_contra_textos.py`, `_oficial/comprobar_opciones_completas.py`,
  `_oficial/medir_cortes_de_fragmentos.py`, `_oficial/medir_restos_en_textos.py`,
  `_oficial/medir_preguntas_sin_opciones.py`, `_oficial/probar_parrafos_en_pregunta.py`: las medidas y las
  comprobaciones.
- `_oficial/bd_snapshot.py`: copia coherente de la base que además **poda**.
