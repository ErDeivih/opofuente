# ADR-016 — Anki y Markdown entran como material, y con qué se lee una baraja

**Estado:** aceptada (22 de septiembre de 2026)
**Contexto de la decisión:** el propietario pidió que la aplicación acepte «todo» lo que tiene —
barajas de Anki, apuntes en Markdown, temarios, exámenes, plantillas, supuestos y anotaciones— y que
lo clasifique y lo deje listo para estudiar sin que él actúe.

## Contexto

Leer una baraja de Anki no estaba resuelto y no era una extensión trivial. Un `.apkg`/`.colpkg` es un
**contenedor ZIP** con una **base de datos SQLite** dentro y la media numerada:

- desde Anki 2.1.50 la colección (`collection.anki21`, y `collection.anki21b` en versiones nuevas) va
  comprimida con **zstd**; las versiones anteriores guardaban `collection.anki2` como SQLite a pelo;
- las tarjetas están en `notes.flds`, con los campos separados por `\x1f`, y los nombres de esos
  campos en `notetypes` (o, antes de 2.1.28, en el JSON de la tabla `col`);
- los mazos cuelgan de `decks` (o del JSON de `col`).

Si el contenedor se tratara como cualquier ZIP —que es lo que hacía la aplicación: `.zip` se expande—
entrarían como entradas sueltas la colección (un SQLite que el extractor de texto no puede leer) y
las imágenes del mazo, y **las tarjetas se perderían**. Es exactamente el fallo silencioso que hay que
evitar.

En Markdown, en cambio, la extracción ya existía (los encabezados son secciones), pero el **importador
de preguntas** no leía un cuestionario escrito así: la clave suele ir en negrita (`**Respuesta
correcta: b**`) y las opciones como viñetas (`- a) …`), y ninguna de las dos formas encajaba con los
patrones del parser. El resultado era un cuestionario con «opciones huérfanas» y sin clave, declarado
como incidencia pero inservible para estudiar.

## Decisión

**1. Una baraja de Anki se lee como baraja, con su propio extractor y su propia familia.**

Se reconoce por el **contenido** (¿hay una colección dentro?), no por la extensión, y no se expande
como ZIP. Se lee la colección con `sqlite3` en **solo lectura**, se sacan de ella las notas, los
mazos y los nombres de campo, y se escribe **un tramo por tarjeta** con los nombres de campo que usa
la propia baraja (`Anverso: …`, `Reverso: …`, o los que sean): no se inventa cuál es la pregunta y
cuál la respuesta.

**2. Entra `zstandard` como dependencia, y se dice por qué.**

Sin leer zstd no se puede abrir una baraja exportada por un Anki de los últimos años, que es la
mayoría. `zstandard` es BSD-3-Clause (compatible con el uso local del proyecto, DEBT-003) y es la
única dependencia nueva de este slice. La descompresión está **acotada** por el mismo límite de
tamaño que el resto del material: una colección no puede llenar la memoria.

**3. La media de la baraja no se extrae, y se avisa.**

Las imágenes y el audio de un mazo no se convierten en artefactos ni se analizan. La representación
lleva el aviso `media_not_extracted` y el recuento en su informe: callarlo sería hacer creer que la
baraja entró entera.

**4. Una tarjeta **no** se convierte en una pregunta corregible, y se dice por qué.**

El modelo tiene el tipo `free_text_reference` y **no tiene dónde guardar la respuesta de referencia**.
Una tarjeta de Anki es exactamente un enunciado con su respuesta, así que convertirla en pregunta
perdería el reverso —lo único que la hace útil— o lo guardaría en un sitio que no existe. Entra, por
tanto, como **material estudiable y citable** (una tarjeta, un tramo, una cita), y se clasifica como
`flashcards`. Convertirlas en preguntas es una decisión de modelo (dónde vive la respuesta de
referencia) con su contrato y su interfaz: queda en DEBT-023, no se improvisa aquí.

**5. El adorno de Markdown no es contenido.**

Antes de leer una línea como enunciado, opción, clave o cabecera, se le quitan los adornos que son
cómo se escribe y no qué se dice: encabezados (`##`), citas (`>`), viñetas (`- `) y las marcas de
énfasis fuerte (`**`, `__`). Un **encabezado** de Markdown se entiende como estructura (encabeza lo
que viene debajo), no como texto suelto. Lo que **no** se toca: las palabras, ni el énfasis simple
(`*diez* días`), porque un guion bajo separa palabras y un asterisco puede ser una nota.

**6. La señal del tipo documental para una baraja es su extensión, y es fuerte.**

`\.apkg` y `\.colpkg` valen 0,8 en el clasificador: además de la extensión, el extractor comprueba
que dentro hay una colección de verdad, así que la señal no se apoya solo en el nombre. Las señales
nuevas del vocabulario del propietario (`preguntas tipo test`, `supuesto práctico`, `cuestionario`,
`anotaciones`) llevan su peso y su cita, y **ninguna decide sola salvo las que no pueden aparecer por
casualidad**: la política de qué se aplica sin preguntar se decide en S12.4, no cue a cue.

## Consecuencias

- Una carpeta con barajas, apuntes en Markdown y exámenes entra **entera y de una vez**, sin expandir
  las barajas en basura y sin dejar las tarjetas fuera.
- El cuestionario en Markdown entra con sus opciones y su clave: la misma frase que antes producía
  «opciones huérfanas» ahora produce preguntas completas con su cita.
- Sigue sin haber **preguntas** de una baraja (DEBT-023) y sigue sin extraerse la **media**.
- La aplicación gana una dependencia; el lockfile y la puerta 11 (build) la verifican.

## Reversión

Quitar el extractor es quitar su familia del registro y su rama de `_zip_family`: el `.apkg` volvería
a expandirse como ZIP (que es el comportamiento anterior, con pérdida de tarjetas), así que la
reversión sensata es marcarlo como `unsupported_preserved`. Lo leído no se pierde: las
representaciones ya extraídas quedan guardadas con su extractor (`anki_apkg@1`) y siguen siendo
legibles y citables.
