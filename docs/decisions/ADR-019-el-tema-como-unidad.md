# ADR-019 — La unidad del producto es el tema, no el fichero

**Estado:** propuesta (23 de septiembre de 2026), decidida por el codificador por delegación expresa
del propietario.
**Contexto de la decisión:** indicación del propietario del 23 de septiembre de 2026.

## Contexto

Hasta hoy la aplicación trata el **fichero** como unidad de trabajo: se importa, se lee, se clasifica
(¿a qué tema pertenece?) y se revisa la propuesta. El tema aparece al final, como un destino: una
cobertura, un dominio, un recuento de preguntas.

El propietario ha dicho que eso no es lo que quiere:

> «no clasifiques el pdf en sí o el archivo, sino que lea la info y use esa info para nutrir cada tema, y
> después mostrar ese tema en una versión que ha construido el sistema en base a toda la info que ha
> obtenido de las fuentes, que a medida que añado fuentes esa información se mejore, como un
> NotebookLM pero sin límite de ficheros».

Dos cosas se piden, y conviene separarlas porque no cuestan lo mismo:

1. **El tema como unidad de lectura**: lo que se abre no es un PDF, es «el Tema 7» con todo lo que el
   corpus dice de él, venga de donde venga.
2. **Una versión construida por el sistema** de ese tema, que **mejora** según se añaden fuentes.

## Decisión

**La unidad del producto es el nodo del programa (el tema).** El fichero pasa a ser una fuente: se
importa, se lee y se cita, pero lo que el usuario abre, estudia y ve crecer es el tema.

Se construye, por cada nodo, un **dossier del tema**: la reunión de todo lo que el corpus dice de él,
y se sirve con `GET /curriculum-nodes/{id}/dossier`. Un dossier contiene:

- **los pasajes citados** que sostienen el tema, agrupados por fuente (documento, versión, sección,
  página), sin repetir el mismo texto dos veces y en orden estable;
- **la procedencia de cada pasaje**: de qué fichero, de qué versión y de qué página salió;
- **los huecos**: qué partes del tema no tienen ningún pasaje, y qué temas del programa no tienen nada
  todavía (esto es la lista de trabajo de quien sube material);
- **cuándo se construyó y con qué fuentes**, para poder ver la diferencia cuando entra material nuevo.

Y se define qué pasa cuando entra una fuente nueva: **el dossier se rehace**, y el anterior no se
pierde —queda como versión— para poder comparar «qué sabía de este tema antes y qué sé ahora». Eso es
lo que significa «que se mejore a medida que añado fuentes» sin que nadie lo pida a mano.

## Lo que esta decisión NO promete (todavía)

**El dossier es un dossier de citas, no un texto redactado.** Escribir el tema «con palabras» es
redacción, y la redacción necesita un modelo de lenguaje. Hoy no hay proveedor, y el propietario ha
decidido que no se conecte ninguno **de momento** (a futuro, un modelo local y, si hace falta, la API
de DeepSeek).

Así que:

- **Ahora**: el tema se enseña como lo que las fuentes dicen, con sus citas, ordenado y sin repetir; la
  estructura, los huecos y las preguntas sí son del sistema. Nada de prosa inventada: no hay ninguna
  frase que no esté en una fuente.
- **Cuando haya modelo** (ADR-020 decidirá cuál y con qué garantías): el mismo dossier es la entrada
  para redactar el tema, y la redacción conserva las citas —cada afirmación con su pasaje— y se guarda
  como **derivado**, con su versión y su fecha, para poder rehacerla cuando llegue material nuevo. La
  invariante de citas de `05_RAG` §6 (`assert_grounded`) es la que manda: si una afirmación central no
  tiene evidencia entregada, la respuesta no se marca como sostenida.

Se deja escrito aquí para que nadie lea «versión construida por el sistema» como «texto que se escribe
solo» antes de que exista el modelo.

## Consecuencias

- **El pipeline de importación no cambia**: sigue copiando, extrayendo y clasificando. Lo que cambia es
  para qué sirve la clasificación: deja de ser una cola de decisiones sobre ficheros y pasa a ser el
  índice con el que se construye cada tema.
- **La pantalla de Revisión no desaparece**: sigue siendo donde una persona confirma a qué tema va cada
  cosa. Lo que ya no tiene sentido es revisar «por documento»: se revisa **contra el tema**, viendo el
  tema crecer.
- **El coste de revisión baja de importancia relativa**: si el dossier se construye con mapeos
  provisionales y se marca lo provisional como provisional, la revisión deja de ser un peaje para
  empezar a estudiar (es lo que pidió DEBT-018 y lo que decide su criterio 3).
- **Sin límite de ficheros no significa sin límites**: la aplicación es local, así que no hay cuotas de
  subida, pero sí hay límites de ingeniería por fichero y por lote (512 MiB por fichero, 50 000
  entradas por lote, 2 000 páginas de PDF, 2 000 entradas de ZIP, 2 MB de texto por representación).
  Se declaran en Ajustes, como el resto de límites, y se miden con el corpus del propietario.
- **La búsqueda sigue siendo léxica** hasta que haya embeddings (ADR-012): un dossier se construye con
  mapeos aceptados o provisionales, y la búsqueda por tema no depende de vectores.

## Alternativas descartadas

1. **Seguir con el fichero como unidad y añadir un «resumen por tema» encima.** Es lo que ya hay
   (cobertura y dominio por nodo) y es exactamente lo que el propietario ha dicho que no quiere: un
   número por tema en lugar de contenido por tema.
2. **Redactar los temas ya, con texto generado a mano por el codificador.** Sería prosa que no está en
   ninguna fuente y que nadie puede verificar contra el material: la aplicación dejaría de ser un
   espejo de las fuentes. Descartado.
3. **Esperar al modelo para construir el dossier.** El dossier es lo que hace falta *para* que el modelo
   sirva de algo: sin la reunión de pasajes por tema, la redacción tendría que buscar el material cada
   vez (o inventarlo). Se construye ahora, y el modelo llegará a un trabajo ya hecho.
