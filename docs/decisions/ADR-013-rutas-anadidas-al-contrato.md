# ADR-013 — Rutas añadidas al contrato de la API

**Estado:** propuesto (pendiente de ratificación del propietario)
**Fecha:** 19 de septiembre de 2026
**Contexto de la decisión:** cierre de cada slice, recogido aquí en la revisión de S00–S11.

## Contexto

`08_API-CONTRACT.md` fija las rutas de la API **por sección**, y cada slice implementa las suyas. Al
construir la interfaz y las pruebas aparecieron rutas que el contrato no lista pero que el producto
necesita para no hacer algo peor: por ejemplo, listar las sesiones de estudio abiertas, o comparar dos
versiones de un documento. En todos los casos la alternativa era peor que la ruta:

- **no tenerla** dejaba la pantalla sin datos que sí existen (una sesión en marcha invisible, una lista
  de decisiones que no se puede recorrer);
- **deducirla en el cliente** habría puesto lógica de negocio en el navegador, contra la arquitectura
  del proyecto;
- **meterla en una ruta existente** habría cambiado el significado de una ruta ya documentada.

Cada slice las declaró en su ficha y en el propio código (`summary` de la ruta), así que no son rutas
escondidas: son rutas **fuera del contrato y señaladas**. Lo que faltaba era una decisión única que las
recogiera, porque estaban repartidas en siete documentos y se leían como «pendiente de ratificación»
siete veces, sin una lista que se pudiera aprobar de una vez.

En la revisión del cierre de deuda (19 de septiembre de 2026) aparecieron **cuatro rutas más que no
estaban en esta tabla**: las tres de colecciones que S05 dio por entregadas y declaró en la prosa de su
ficha, y el filtro por colección de la biblioteca. Faltaban aquí, que es donde hay que mirarlas: si esta
tabla es el registro único, una ruta añadida que no esté en ella es exactamente la ruta escondida que
esta decisión existe para evitar.

## Decisión

Se mantienen las rutas añadidas, todas bajo `/api/v1`, con esta tabla como registro único. Ratificarlas
significa aceptar que el contrato tiene una lista adicional a la que él mismo fija; rechazar alguna
significa retirarla y asumir la consecuencia escrita en la última columna.

| Ruta | Slice | Por qué existe | Qué se pierde si se retira |
|---|---|---|---|
| `POST /classification-runs` | S04 | Lanzar el motor determinista sobre el corpus y seguir su avance; sin ella, clasificar no se puede pedir desde la interfaz. Desde DEBT-024 (S12.6) responde **202 con el trabajo encolado**, no con el informe: el informe viaja en el paso del trabajo al terminar | la pantalla de Revisión no puede pedir una clasificación nueva |
| `GET /documents/{id}/diff` | S05 | Comparar dos versiones del mismo documento y decir qué sección cambió | la pestaña «Versiones y diff» se queda sin diff |
| `GET /collections` y `POST /collections` | S05 | Listar y crear colecciones: agrupar material sin duplicarlo (`03_DATA-MODEL` §«colección») | la Biblioteca pierde las colecciones y, con ellas, el filtro por colección |
| `POST /collections/{id}/items` | S05 | Meter un sujeto en una colección: una versión, un artefacto, una representación, una sección o una evidencia | ninguna colección podría tener nada dentro, así que la superficie entera sobra |
| `GET /study-sessions` | S07 | Listar las sesiones (en marcha y terminadas) de una oposición | no se puede retomar una sesión sin recordar su id |
| `POST /study-sessions/{id}/recalculate` | S08 | Recalcular con una clave corregida y conservar el resultado anterior | una clave mal importada cambiaría notas a escondidas o no se podría corregir |
| Cinco rutas de §8 (búsqueda y RAG) | S09 | El contrato de §8 fija el comportamiento; la interfaz necesita además leer una consulta guardada con su recuperación completa | la vista «Preguntar» no podría auditar de dónde salió una afirmación |
| Seis rutas | S10 | Cola de errores, conceptos, exportación y su historial | la pantalla de Errores no tendría con qué trabajar |
| Cinco rutas | S11 | Cambios pendientes, confirmar, descartar, derivados y su resolución | la pantalla de Cambios no existiría como tal |
| `POST /question-sets/{id}/recalculate-sessions` | DEBT-013 | Recalcular **en bloque** las sesiones terminadas de un conjunto, con informe por sesión; el recálculo de una sola sesión (S08) obligaba a repetirlo una vez por sesión y las olvidadas se quedaban con la puntuación vieja | corregir una clave mal importada vuelve a ser un trabajo manual sesión a sesión, y las que nadie recuerde quedan mal para siempre |
| `GET /question-sets/{id}/outdated-sessions` | DEBT-013 | Cuántas sesiones terminadas no están corregidas con la plantilla **activa**: es lo que permite avisar al activar una clave nueva en lugar de descubrirlo sesión a sesión | activar una clave corregida no cambia ninguna nota y no se notaría en ninguna pantalla |
| `DELETE /collections/{id}/items` | DEBT-017 | Quitar un miembro de una colección sin borrar el sujeto; ninguna sección del contrato lista las colecciones, y sin esta ruta una colección se puede llenar y no vaciar | el error de agrupar algo se vuelve permanente |
| `GET /documents?collection_id=…` | DEBT-017 | Filtrar la biblioteca por colección con el criterio resuelto en el **servidor**, porque un miembro puede ser cualquiera de los cinco tipos de sujeto | el filtro habría que deducirlo en el navegador —o traerse la biblioteca entera—, contra la arquitectura del proyecto |
| `POST /question-sets/{id}/import-document` | DEBT-010 | Importar las preguntas de una versión de documento creando la cita de cada una; el camino del contrato §9 solo tiene texto, CSV, JSON y plantilla, y sin esta ruta una pregunta nacida de un documento no puede enseñar de dónde salió | la ficha no puede abrir la cita que sostiene el enunciado, y adivinar la sección en el navegador sería peor |
| `GET /study-sessions/{id}/diagnostic` | DEBT-012 | La lectura por temas de un diagnóstico: lo contestado en la muestra y su intervalo del 95 %. Va aparte del resultado porque el resultado dice la puntuación directa de la muestra —que no es una nota— y esta lectura dice por dónde está el hueco | el diagnóstico enseñaría una puntuación sin la incertidumbre que la hace legible, que es justo lo que 06_QUESTIONS §5 prohíbe |
| `GET /oppositions/{id}/readiness` | S12.6 | Responder «¿puedo estudiar ya con lo que he soltado?» por oposición: material por papel, preguntas por tema y claves activas, con lo que falta dicho en palabras. Se calcula con recuentos agregados en el servidor para que Inicio no tenga que traerse el corpus entero para contar | Inicio vuelve a no poder decir si falta algo, y el propietario tiene que deducirlo mirando cuatro pantallas |
| `GET /pending-actions` | S12.6 | Lo que sigue esperando una decisión humana —incidencias de importación, propuestas de clasificación, cambios de fuente y material sin aceptar—, con su cifra y la pantalla donde se resuelve. Es la otra mitad de la misma pregunta: la aplicación hace lo demás sola (ADR-017) | la lista de tareas del propietario habría que componerla en el navegador juntando cuatro listados, o no existir |
| `GET /questions/{id}/explanations` | S12.7 | Leer la explicación de la pregunta entera y la de **cada opción** (07_UI-UX §7). El modelo las guardaba desde S06 y no había forma de verlas: la ficha solo podía decir cuántas había | la explicación por opción que pide el editor estructurado no se podría leer, y el trabajo de explicar el material se quedaría invisible |
| `POST /questions/{id}/explanations` | S12.7 | Escribir (o sustituir) la explicación de un hueco: la identidad es `(pregunta, opción)`, así que el mismo sitio se corrige en lugar de acumular versiones | el editor no podría explicar nada sin crear una versión nueva de la pregunta con motivo, que es otra cosa |
| `POST /convocations/{id}/activate` | S12.2 | Elegir con qué convocatoria trabaja la aplicación cuando una oposición tiene más de una publicada (Celador: acceso libre de 2022 y estabilización). `POST /oppositions/{id}/activate` no sirve: la elección no es de oposición sino de convocatoria, y solo una puede ser la vigente por el índice único parcial | la segunda convocatoria quedaría sembrada e invisible: Programa, Estudio, Repaso y Banco resuelven su convocatoria con `active_convocation` de la oposición activa, y no habría forma de cambiar de una a otra |
| `POST /ingestion-batches/{id}/pause` y `…/resume` | DEBT-027 §4 | Pausar un lote no es cancelarlo: `07_UI-UX` §4 pide las dos cosas y hasta ahora solo existía cancelar. Pausar deja el lote donde está —lo copiado sigue copiado— y reanudar lo devuelve a la cola. El lote y su trabajo tienen un estado nuevo (`paused`), y el índice de idempotencia se recrea para que un trabajo en pausa siga ocupando su clave | o se ofrece un botón de pausa que en realidad cancela —pérdida irreversible de trabajo ya hecho— o se puede «pausar» sin que nadie pare el trabajo, que es una etiqueta que miente |
| `GET /curriculum-nodes/{id}/dossier` | S13 (ADR-019) | Lo que el corpus dice de un tema, citado: pasajes con su documento, versión y página, más lo que **no** tiene declarado como huecos. La cobertura dice *cuánto* material tiene un tema; esto dice *qué dice* | el tema sigue siendo un número en la interfaz, que es justo lo que el propietario pidió cambiar: el material se lee por fichero y el tema no se puede leer |
| `POST /curriculum-nodes/{id}/dossier/versions` | S13 (ADR-019) | Archiva la lectura actual del tema para poder compararla con la de después («esto es lo que sabía y esto lo que sé»). Es un `POST` a propósito: leer un dossier no escribe, y un `GET` con efectos no se puede reintentar sin pensar | cada fuente nueva reescribiría el pasado: no habría forma de ver qué aportó el material que llegó ayer |
| `GET /curriculum-nodes/{id}/dossier/versions` y `…/{version_id}` | S13 (ADR-019) | Listar las versiones guardadas y leer una anterior **tal como se leyó** (el contenido se guarda entero, no una referencia) | la historia archivada existiría y no se podría consultar, que es como no tenerla |

Las rutas concretas de S09, S10 y S11 están enumeradas en las fichas de sus slices
(`docs/slices/S09.md`, `S10.md`, `S11.md`), cada una con lo que aporta; esta tabla no las repite una a
una para no duplicar lo que ya está escrito donde se decidió.

## Consecuencias

- **El contrato deja de ser la lista completa de rutas.** Quien lea `08_API-CONTRACT.md` y compare con
  el OpenAPI verá diferencias, y esta es la lista que las explica. Las alternativas eran peores: o
  rutas escondidas, o un producto al que le falta lo que ya tiene.
- **Las rutas añadidas siguen el mismo contrato de errores** (`ProblemDetail` con `code` y
  `correlation_id`), la misma comprobación de `Origin` en escrituras y la misma validación de esquema
  que las rutas del contrato: no hay dos calidades de API.
- **El OpenAPI es la verdad ejecutable.** Estas rutas están en `packages/contracts/openapi.json` con su
  esquema y sus respuestas de error, así que un cliente generado las ve; lo que no están es en el
  documento §8/§10/§11 escrito a mano.
- **Si el propietario retira una**, la retirada es un cambio de producto y va con su slice: no se
  dejan rutas a medias ni pantallas que las llamen.

## Alternativas descartadas

1. **Ampliar `08_API-CONTRACT.md`.** Se descartó porque ese documento es el contrato **de partida** y
   reescribirlo borraría la trazabilidad de qué se pidió y qué se añadió después. La lista de añadidos
   tiene que ser un añadido, no una edición del original.
2. **No añadirlas y forzar el producto a lo que hay.** Se descartó porque en cada caso la consecuencia
   es una pantalla que no puede hacer su trabajo, o peor: deducir en el cliente lo que decide el
   servidor.
3. **Añadirlas en silencio.** Se descartó desde el primer slice: cada una se declara en su ficha y en el
   `summary` de la ruta, y ahora también aquí.
