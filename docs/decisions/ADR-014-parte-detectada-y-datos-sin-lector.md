# ADR-014 — Dónde vive lo que el importador lee y no puede guardar

**Estado:** aceptado (20 de septiembre de 2026)
**Contexto de la decisión:** cierre de DEBT-010 (importar preguntas desde un documento).

## Contexto

DEBT-010 dejó tres cosas abiertas al cerrar S06, y las tres son la misma pregunta con tres caras:
**qué se hace con lo que el importador lee y el modelo no tiene dónde guardar**.

| Lo que se lee | Dónde estaba el problema |
|---|---|
| La **sección** del documento del que salió la pregunta | `question_versions.source_section_id` existía en el modelo desde S05 y **nadie lo rellenaba**: la ficha no podía abrir la cita que sostiene el enunciado porque no había cita |
| La **parte del examen** («Parte 2», «Primera parte») | el parser la detecta (`parts_detected`) y se perdía al guardar: no hay ninguna columna ni tabla que ligue una pregunta con `exam_parts` |
| Las columnas `tags` y `source` del CSV (y `section`, `reference`, `image`, `id` del JSON) | el asistente las lee y el informe declara que no se guardan (`ignored_columns`) |

La deuda pedía **decidir** dónde vive cada cosa, o dejar de prometer que se guarda. Esta es la decisión.

## Decisión

**1. La sección de origen se guarda, y se llena al importar desde un documento.**
`question_versions.source_section_id` (ya en `03_DATA-MODEL` §`question_versions`, ya en la base, ya en
el contrato) se rellena con la sección de la que salió el enunciado, y la cita
(`question_evidence`, papel `stem`) apunta al **fragmento** concreto. Se deduce de la lectura, no de una
suposición: el texto de la versión se reconstruye desde sus fragmentos conservando la estructura de
líneas, y como el parser devuelve la línea donde empieza cada enunciado, la cita es exactamente el
fragmento del que se leyó.

**2. La cita de una pregunta importada nace `accepted`, no `proposed`.**
No es una propuesta de un clasificador: es de dónde se leyó el texto. Se acepta sola porque es un hecho
comprobable —el enunciado está en ese fragmento— y porque pedir una confirmación por cada cita
convertiría la importación de un temario en una cola de doscientas decisiones sin nada que decidir.

**3. Solo se importa de una versión **aceptada**.**
Un documento puede tener una versión candidata y otra aceptada. Las preguntas se importan de la
aceptada: una candidata no es la versión buena —es la regla de la Biblioteca—, y una cita que apunta a
una versión candidata es una cita a material que nadie ha aceptado. La pantalla lo dice y deja el botón
deshabilitado mientras la versión no esté aceptada, con lo que hay que hacer.

**4. La parte del examen NO se guarda por pregunta, y se declara.**
El modelo no tiene dónde (`03_DATA-MODEL` no liga preguntas a `exam_parts`; `session_questions` guarda
la parte de la **composición** de una sesión, que es otra cosa: la decide quien monta el examen, no el
material). Emparejar el rótulo que trae el documento («2», «IV») con los códigos de `exam_parts` de la
convocatoria exigiría adivinar, y guardar el rótulo suelto sería un dato sin lector: ninguna pantalla ni
cálculo lo usa hoy. Por eso el rótulo se **declara en el informe** (`parts_detected`) con la frase que
dice que no se guarda —igual que `tags` y `source`—, en lugar de perderse en silencio.

Lo que haría falta para guardarlo: una tabla de enlace pregunta↔`exam_parts` con estado
`proposed`/`accepted` **y** una pantalla donde confirmar el emparejamiento, porque el rótulo del
material no es un código de la convocatoria. Eso es una decisión de producto (¿se compone el examen por
parte desde el banco?) que hoy no existe: la composición pide N preguntas del conjunto para una parte,
sin mirar la parte de cada pregunta.

**5. `tags` y `source` (CSV) y `section`, `reference`, `image`, `id` (JSON) siguen leyéndose y
declarándose, sin guardarse.**
`04_INGESTION` §10 los lista como columnas mapeables, así que el asistente los sigue aceptando y el
informe sigue diciendo que no se guardan (`ignored_columns`). Lo que cambia con esta decisión es que ya
no es un «todavía»: **es el destino final**. Ninguna pantalla, filtro ni exportación consume etiquetas
libres por pregunta, y la procedencia ya no es un texto suelto: es la cita, con su documento, su versión,
su sección y su página. Quitar `tags` y `source` del mapeo contradiría §10 sin ganar nada; guardarlos
sería coleccionar datos que nadie lee.

## Consecuencias

- **La ficha de pregunta puede enseñar el original al lado** (07_UI-UX §7) y abrirlo en su página: la
  cita lleva un enlace a `GET /document-versions/{id}/original#page=N`. Sin cita, la pantalla sigue
  diciendo que no hay documento de origen en lugar de enseñar un hueco.
- **Volver a importar el mismo documento repara las citas** sin duplicar nada: la pregunta ya estaba
  (idempotente por huella) y el enlace se crea si no existía.
- **El informe gana dos cifras**: `evidence_links` (citas creadas de verdad) y `parts_detected`. Una
  importación que no enlaza nada porque la versión no tiene texto extraído lo dice con su incidencia,
  no con un «hecho» vacío.
- **Un dato que no se guarda tiene que estar escrito aquí.** Si algún día se guarda la parte o las
  etiquetas, se cambia esta decisión y su motivo queda a la vista.

## Alternativas descartadas

1. **Guardar el rótulo de parte tal cual en `question_versions`.** Se descartó por dato sin lector: la
   composición no lo mira, y un rótulo suelto («2») sin su convocatoria al lado se lee como un código
   que no es. Guardar mal es peor que declarar bien.
2. **Resolver el rótulo contra `exam_parts` al importar.** Se descartó por adivinar: «Parte 2» no es
   `practical`, y el material real usa rótulos que no coinciden con los códigos del perfil.
3. **Guardar `tags` y `source` en dos columnas nuevas.** Se descartó porque no hay quien los lea: sería
   una migración para llenar una tabla que ninguna pantalla consulta, y la procedencia ya está resuelta
   con la cita.
4. **Importar de cualquier versión, no solo la aceptada.** Se descartó porque contradice la regla de la
   Biblioteca (una candidata no es la versión buena) y deja citas apuntando a material sin aceptar.
5. **Crear la evidencia como `proposed` y confirmarla a mano.** Se descartó porque no hay nada que
   decidir: el enunciado se leyó de ese fragmento, y una cola de confirmaciones por cada pregunta de un
   temario es trabajo inventado.
