# El banco de preguntas de la aplicación: por qué estaba a cero y cómo se llena (septiembre 2026)

La biblioteca tiene miles de documentos aceptados y cientos de miles de fragmentos citables, y sin
embargo la pantalla de preguntas estaba en **cero**. No era una pantalla vacía por falta de material:
eran **dos eslabones** que nadie había cerrado. Esto cuenta los dos, con lo que se midió, con lo que se
corrigió de lo que yo mismo había dicho mal, y con lo que queda sin comprobar.

**Resultado**: el banco queda con las **440 preguntas de los cuatro exámenes oficiales de 2025**, cada
una **con su cita**, con sus opciones, 258 con tema y 436 con la clave oficial (las 4 sin clave están
anuladas o no llevan respuesta en la plantilla definitiva).

## 1. El diagnóstico, medido

`GET /api/v1/questions?limit=1` → `total: 0`. En la base: `question_sets = 0`, `question_versions = 0`,
`answer_key_versions = 0`, `option_versions = 0`.

La importación automática de preguntas existe y está probada (S12.5/S12.6, ADR-013): se dispara al
aceptar una versión (`library.py:380` → `auto.after_version_accepted`). Pero para llegar al final
necesita dos cosas que **no había**:

| lo que necesita | dónde lo mira | lo que había |
| --- | --- | --- |
| tipo documental aceptado del artefacto | `auto_study_service._document_type` → `accepted_classification` | **0 propuestas aceptadas** (todas en `pending` o `auto_applied_provisional`) |
| asignación aceptada de la versión a un nodo del programa | `auto_study_service._opposition_of` → `mapeo.status == "accepted"` | **0 mapeos aceptados** (10.355 provisionales, de artefacto y representación) |

Con eso, cada aceptación de versión respondía lo mismo: «el material no está clasificado: no se sabe si
trae preguntas». Y es coherente con el diseño: **aceptar es aprobar** (ADR-009) y nadie había aprobado
la clasificación. El relleno de la biblioteca aceptó versiones, no propuestas de clasificación.

Consecuencia práctica: **la clasificación se hizo (38.220 propuestas) y se aplicó de forma provisional,
pero no se aprobó nunca**, así que ninguna ruta que dependa de lo aceptado —el banco de preguntas, el
catálogo por tema de cada pregunta— podía funcionar.

## 2. El segundo obstáculo: el texto que llega al analizador

Con el material en la biblioteca, se probó el camino directo (`import-document`) sobre el
**Cuestionario TAI-P-ModeloB.pdf** (examen oficial del INAP, promoción interna, 85 preguntas).
Resultado: **27 preguntas creadas de 85 y sin opciones**.

La primera explicación que escribí aquí —«el analizador no entiende la maquetación del PDF oficial»— era
**falsa**. Se comprobó pasando el analizador de la aplicación, a mano, por los mismos ficheros:

| texto | preguntas que lee el analizador |
| --- | --- |
| `tai-pi-2025-modeloB.txt` (limpio) | **85** |
| `Cuestionario TAI-P-ModeloB.pdf` | — (el analizador no ve el PDF) |

El analizador no es el problema. Lo que pasa es que `import_from_document` no lee la representación
entera: **reconstruye el texto con los fragmentos** (`evidence_spans`), que son a la vez las citas. Y los
fragmentos del PDF cubren muy poco de su propio texto:

| documento | caracteres de la representación | fragmentos | caracteres cubiertos | cobertura |
| --- | --- | --- | --- | --- |
| Cuestionario TAI-L-ModeloA.pdf | 63.314 | 14 | 16.769 | **26,5 %** |
| Cuestionario TAI-P-ModeloA.pdf | 40.125 | 11 | 13.176 | **32,8 %** |
| Cuestionario TAI-L-ModeloB.pdf | 63.330 | 14 | 16.768 | **26,5 %** |
| Cuestionario TAI-P-ModeloB.pdf | 40.102 | 11 | 13.174 | **32,9 %** |
| `tai-libre-2025-modeloA.txt` (limpio) | 56.714 | 143 | 56.424 | **99,5 %** |
| `tai-pi-2025-modeloB.txt` (limpio) | 35.342 | 93 | 35.152 | **99,5 %** |

Es decir: al analizador le llega **un tercio** del examen, así que lee un tercio de las preguntas, y las
que lee a medias entran sin sus opciones. Y no es un problema del importador de preguntas: **lo que no
está en un fragmento tampoco se puede citar**, así que ese tercio de texto era, además, invisible para la
búsqueda y el dossier.

**Lo que se hace con eso**: generar una versión en **texto limpio** de cada cuestionario (mismo contenido,
una opción por línea, `[R]` para las de reserva y «Modelo: A/B»), que da un 99,5 % de cobertura. El texto
limpio se deja en `F:\OpoFuente\TAI\internet\examenes-para-la-app\`, se ingiere como cualquier otro
material y entra como **versión nueva del mismo documento** (`document_id` en la promoción), no como un
documento duplicado.

Dos reglas del formato que costaron una vuelta cada una, y conviene no volver a olvidarlas, porque el
analizador no las perdona:

- la marca de reserva va **en la línea numerada** (`81. [R] …`), que es donde el analizador la busca; en
  una línea suelta delante acaba **pegada al final de la última opción de la pregunta anterior**, y esa
  pregunta deja de coincidir con su fila del CSV (pasó: 15 preguntas duplicadas en cada examen de libre,
  11 en cada uno de promoción interna);
- **ninguna línea suelta** entre una pregunta y la siguiente: cualquier texto en medio se añade a la
  última opción leída.

## 3. Cómo se llena, sin inventar nada

Las dos rutas que hacen falta, y por qué hacen falta las dos:

1. **`POST /question-sets/{id}/import-document`** con la versión del texto limpio: crea las preguntas
   **con su cita** (`source_section_id` y su fragmento de evidencia). No pone tema: el tema de una
   pregunta se hereda del documento entero, y un examen oficial cubre los 33 temas del programa, así que
   asignarle un nodo sería etiquetar mal 32 de cada 33 preguntas.
2. **`POST /question-sets/{id}/parse` con `kind: csv`** y el mismo examen en CSV con la columna `topic`:
   la aplicación reconoce cada pregunta por su huella, **no la duplica**, y le pone el tema; además
   guarda la **clave oficial** de la pregunta. El CSV solo no valdría (las preguntas quedarían sin cita);
   el documento solo tampoco (sin tema y sin clave).

Los temas del CSV salen del banco de fuera (`BANCO-oficial/por-tema.jsonl`, 440 preguntas de los cuatro
exámenes oficiales de 2025): **142 con tema concreto** (`I.1`…`IV.10`, la misma referencia que usa el
programa de la aplicación) y **116 más con solo el bloque** (`I`…`IV`). El resto no lleva tema: no se
inventa. Las **2 preguntas anuladas** por el tribunal entran **sin clave**, con el motivo escrito en su
`source`.

## 4. Lo que está pendiente de aprobación y sigue pendiente a propósito

- **Activar la clave.** El CSV deja la clave guardada en **borrador**; activarla es aprobar (ADR-009) y
  se hace con un clic en la pantalla de preguntas. Hasta entonces la aplicación no corrige con ella.
- **Aceptar la clasificación de más material.** De las propuestas de `document_type` pendientes, el motor
  reparte etiquetas que **no se sostienen**: propone `practical_case` para sesiones y apuntes
  (`ESTAILI*.pdf`, sesiones de PreparaTIC, `Leeme PRIMERO.txt`) y `answer_key` para libros (`LPIC 2º
  edición`, `LPIC-2 Linux_Castellano`) y para test sin clave. Aceptarlas en bloque con la firma de una
  persona sería meter ruido con aspecto de decisión humana. Por eso se aceptaron **solo** los ocho
  ficheros oficiales, uno a uno, con el nombre y el contenido comprobados.

## 5. Defectos y rarezas de la API encontrados por el camino

Cada uno está comprobado con una respuesta real del servidor:

1. **`convocation_version_id` pide el identificador, no el código, y el error sale como 500.**
   Con `"tai-age-2025"` (el código) la API responde 500 con `IntegrityError: FOREIGN KEY constraint
   failed` sobre `question_sets`. Un valor que no existe debería ser 400/404 con el motivo, no un error
   interno.
2. **Dos escritores a la vez tumban la escritura.** Con el relleno de la biblioteca y otra escritura en
   paralelo, `POST /documents` devolvió 500 con `sqlite3.OperationalError: database is locked`. La causa
   es `PRAGMA busy_timeout=5000` (`infrastructure/db.py:57`): cinco segundos no bastan cuando hay miles
   de inserciones con FTS. La petición se pierde; el cliente solo ve 500.
3. **El origen de las preguntas importadas es siempre `private`.** `import_from_text`, `import_from_csv`
   e `import_from_document` tienen `origin_type: Origin = Origin.PRIVATE` y las rutas lo pasan explícito
   (`questions.py`). No hay forma, por API, de que las preguntas de un **examen oficial** queden marcadas
   como `official`, aunque el documento del que salen esté clasificado como examen oficial.
4. **El mapeo de CSV anuncia columnas que no se guardan.** `CsvColumnMapping` declara `source` y `tags`
   entre las columnas del mapeo, pero al leer las filas solo se consumen `stem`, opciones, `correct`,
   `explanation`, `topic` y `reserve`, y `QuestionSchema` no tiene dónde guardar `source`. Es
   precisamente la columna que resolvería la cita sin pasar por `import-document`.
5. **Un solo trabajador, y una cola larga lo bloquea todo.** Con una tanda de clasificación de 5.434
   elementos corriendo durante horas, la ingesta de cuatro ficheros se quedó en `queued` sin límite ni
   aviso. No hay prioridad, ni estimación, ni forma de saltar la cola.
6. **La clasificación de tipo documental no es fiable a escala.** Es el mismo problema ya medido en el
   eje de tema (86,7 % a nivel de bloque, ~60 % a nivel de tema): en `document_type` la etiqueta se
   reparte por palabras del texto y confunde una sesión con un caso práctico y un libro con una plantilla.
7. **No hay forma de deshacer un conjunto de preguntas.** La aplicación conserva la historia a propósito,
   pero un importador automático se equivoca, y no hay ruta para retirar un conjunto creado por error: la
   única salida es tocar la base. En este trabajo se hizo así —sobre el conjunto de prueba creado minutos
   antes, con copia de seguridad y sin sesiones de estudio detrás— y quedó al descubierto un detalle del
   modelo: los mapeos al programa de una pregunta se guardan con `subject_type = 'question_version'`, y
   si se borran las preguntas y no esos mapeos quedan **50 enlaces a preguntas inexistentes** que la
   cobertura del programa seguiría contando.

## 6. Una advertencia sobre cómo se midió esto

Las cifras de esta revisión se leyeron primero con una copia hecha con `shutil.copy2`, que **no vale**:
la aplicación usa SQLite en modo WAL, así que esa copia deja fuera lo confirmado recientemente y
devuelve un estado viejo sin avisar. Llegó a mostrar 112 preguntas de un conjunto que ya se había
borrado. Lo que se lee aquí está medido con la **API de copia de SQLite** (`Connection.backup`), que sí
es coherente. Copiar una base SQLite a mano y sacar conclusiones de ella es un error fácil de cometer y
silencioso.

## 7. Lo que se puede comprobar y lo que no

- **Comprobado, con respuesta real del servidor o de la base**: los conteos previos, la ruta del código
  que decide la importación automática, la cobertura de fragmentos de cada documento, el número de
  preguntas que lee el analizador en cada texto, el 500 por clave ajena, el 500 por bloqueo de base, el
  valor por defecto del origen de las preguntas y las columnas del mapeo de CSV.
- **Comprobado, ya ejecutado**: el banco de preguntas queda en **440 preguntas**, que son exactamente las
  cuatro pruebas oficiales (135 + 135 + 85 + 85); **440 con cita**, 440 con sus cuatro opciones,
  **258 asignadas a un tema** del programa (142 a un tema concreto y 116 a su bloque) y **436 con la
  clave oficial**. Las **4 sin clave** no son un fallo: dos están anuladas por el tribunal (la plantilla
  dice «ANULADA») y otras dos no llevan respuesta en la plantilla definitiva. **No se ha inventado
  ninguna clave.** La clave queda **guardada y en borrador** en cada conjunto: activarla es aprobar
  (ADR-009) y es un clic en la pantalla de preguntas.
- **No comprobado**: que el dueño estudie con esto. No hay ninguna sesión de estudio todavía, así que el
  diagnóstico por temas y la corrección con la clave activa están sin usar de verdad.
