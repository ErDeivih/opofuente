# Apuntes completos: escritos a partir de las preguntas y comprobados con ellas

**Para:** DeepSeek · **De:** Claude · **7 oct 2026** · **Base:** `main = 3ebe0dd`
**Sustituye** a los apartados 6.2 y 6.3 de `TRABAJO-PENDIENTE-PLATAFORMA-TAI-2026-10.md`. El resto de ese documento sigue valiendo.

## 0. Qué pide el propietario y qué cambia

1. **Apuntes mucho más completos.** La base es muy grande y no tiene sentido sacar temas cortos. El límite de 2.500–6.000 palabras por tema que puse **se elimina**: la extensión la decide el contenido.
2. **Con los apuntes se tienen que poder contestar todas las preguntas.** El 85 % sobre las oficiales que puse **se sustituye** por: **cada pregunta del tema se contesta con los apuntes**, o queda señalada con un motivo que el propietario revisa (clave dudosa, ley derogada, fuera de temario).

Por eso los apuntes **ya no se miden por palabras sino por preguntas cubiertas**, y se construyen al revés: primero se saca de las preguntas todo lo que el alumno tiene que saber y luego se redacta para que esté todo.

---

## 1. De dónde partimos (medido sobre la copia de los datos reales)

| Dato | Valor |
|---|---|
| Preguntas de TAI | **16.743** |
| Enunciados distintos (quitando repetidas entre bancos) | **13.327** |
| Preguntas asignadas a un tema | 9.342 |
| **Preguntas sin tema** | **7.401 (44 %)** |
| Preguntas distintas por tema (asignadas) | de 59 (IV.3) a **1.865 (I.1)**; el bloque II tiene solo 80–86 por tema, sospechosamente pocas |
| Material asignado por tema | entre 6 y 70 documentos, y miles de pasajes (I.7: 15.331) |
| Preguntas con la correcta en estado `conflicting` o `incomplete` | 10 |

**Consecuencia:** antes de escribir nada hay que **asignar a un tema las 7.401 que no lo tienen**, porque son preguntas que los apuntes también tienen que cubrir. Las cifras bajas del bloque II indican que ahí está la mayoría de las sin asignar.

---

## 2. El proceso (siete pasos)

### Paso A. Todas las preguntas en su tema y su epígrafe

1. **Agrupar repetidas**: normalizar el enunciado (sin acentos ni puntuación) más las opciones; las iguales forman un grupo y se trabajan una vez. Guardar el grupo (`question_group_id`) para no volver a calcularlo. Si dos preguntas iguales tienen **correctas distintas**, el grupo se marca como conflicto.
2. **Asignar tema** a cada grupo sin tema: primero el clasificador que ya existe; si la confianza es baja, el modelo de lenguaje con el temario oficial completo (bloques, temas y epígrafes) en las instrucciones, devolviendo tema, epígrafe y confianza.
3. **Asignar epígrafe** a todas (también a las que ya tenían tema). Los epígrafes salen del título oficial, que los separa por puntos (I.1: «La Constitución Española de 1978. Derechos y deberes fundamentales. Su garantía y suspensión. El Tribunal Constitucional. …»).
4. **Revisión del propietario solo de lo dudoso**: confianza baja y preguntas que el modelo marca como "fuera del temario". Pantalla de lote en `/admin/preguntas?revisar_tema=1` con teclas (aceptar, cambiar tema, fuera de temario).

**Hecho cuando:** el 100 % de los grupos tiene tema y epígrafe, o está marcado "fuera del temario" por el propietario.

### Paso B. Inventario de hechos: lo que hay que saber

Para cada grupo de preguntas con correcta válida, el modelo escribe **de 1 a 3 hechos**: frases afirmativas, autónomas y comprobables que, sabidas, permiten acertar la pregunta.

> Pregunta: «¿Qué artículo de la Constitución reconoce el derecho de petición?» Correcta: «El 29».
> Hecho: «El derecho de petición, individual y colectivo, por escrito, se reconoce en el artículo 29 de la Constitución.»

Si la pregunta se basa en descartar opciones, añadir el hecho que descarta la trampa más tentadora («El artículo 23 regula la participación en asuntos públicos, no la petición»).

- Se trabaja por lotes (≈ 20 preguntas por llamada).
- Los hechos repetidos o casi iguales se fusionan, conservando de qué preguntas salen.
- Cada hecho queda guardado con: tema, epígrafe, preguntas de origen, y si es **normativo** (cita un artículo) o **técnico**.
- El resultado es la tabla `topic_facts` y un informe por tema: número de hechos por epígrafe. Es la **medida de lo que tienen que contener los apuntes**.

### Paso C. Esquema detallado del tema

Antes de redactar, un esquema por tema: **epígrafes oficiales → apartados → subapartados**, construido a partir de:
- los grupos de hechos de cada epígrafe (qué conceptos aparecen);
- los títulos de los apuntes personales y de la documentación asignada al tema;
- en los temas normativos, la estructura de la propia norma (títulos, capítulos y artículos que caen).

Cada subapartado lleva la lista de hechos que tiene que contener. **Ningún hecho se queda sin subapartado.**

El propietario puede ver el esquema de los temas piloto antes de que se redacten: cuesta poco y evita reescribir un tema entero.

### Paso D. Redacción por subapartado

Una llamada por subapartado, con:
- **todos los hechos asignados** a ese subapartado: es obligatorio que todos aparezcan, integrados en el texto, en tablas o en listas, no como una lista suelta pegada al final;
- el **material** del tema para ese subapartado, por orden de fiabilidad: normativa y documentación técnica oficial; luego apuntes personales; luego el resto;
- en los temas normativos, el **texto literal** de los artículos que caen (los textos legales se pueden citar).

Reglas de redacción (en la plantilla de instrucciones versionada):
1. Explicar, no solo enumerar: qué es, para qué sirve, cómo se relaciona con lo anterior, y el ejemplo cuando ayude.
2. Mantener **todas** las cifras, plazos, mayorías, órganos, siglas, puertos, versiones de norma y números de artículo que aparezcan en los hechos o en la norma.
3. Tablas comparativas cuando haya conceptos que se confunden.
4. Con palabras propias; cita literal solo de normativa; nunca más de 20 palabras seguidas de otro documento.
5. **Nada inventado.** En especial, **ninguna afirmación sobre exámenes** («ha caído en 4 de las últimas 5 convocatorias») salvo que la calcule la aplicación con datos reales. Las pantallas de Stitch traían frases así inventadas: no pueden llegar a los apuntes.
6. Si falta material para un hecho, se escribe igualmente a partir del hecho y la norma, y el párrafo se marca `<!-- revisar: sin material de apoyo -->` para el propietario.
7. Cada párrafo lleva un ancla estable (`{#iv-7-3-2-p4}`) para enlazarlo desde las preguntas.

**Extensión:** la que salga. Como orientación, con estos números un tema con 1.865 preguntas distintas (I.1) dará unos apuntes muy largos y uno con 60 (IV.3), unos más cortos. Los temas largos se dividen en **capítulos** en la interfaz (§4).

**Partes fijas de cada tema**, además del desarrollo:
- **Esquema inicial** de una página.
- **Siglas y términos** del tema (glosario).
- **Datos que caen**: tabla con todas las cifras, plazos, mayorías, puertos, etc. del tema, cada uno enlazado al párrafo donde se explica.
- **Trampas típicas**: a partir de las opciones incorrectas que más eligen los alumnos (cuando haya intentos) y de los hechos "que descartan".
- **Resumen para el último repaso.**

### Paso E. Comprobación pregunta a pregunta

Para **cada** grupo de preguntas del tema:
1. Se le da al modelo **solo** el texto de los apuntes (el subapartado donde están sus hechos y los vecinos) y la pregunta con sus opciones.
2. Debe responder la letra **y copiar la frase exacta de los apuntes** que la justifica. Si no la encuentra, responde «NO ESTÁ».
3. Se comprueba **mecánicamente** que la frase copiada existe en los apuntes (comparación de texto, no el criterio del modelo). Si no existe, cuenta como «NO ESTÁ». Esto evita que el modelo conteste con lo que ya sabe.
4. Resultado de cada pregunta:
   - **Cubierta**: letra correcta y frase verificada → se guarda el enlace pregunta → párrafo (`question_note_anchors`). Es lo que usa "Ver en apuntes" para llevar al párrafo exacto.
   - **Hueco**: «NO ESTÁ» o letra incorrecta con la clave clara → se redacta un **añadido** para ese subapartado con el hecho que falta y se vuelve a comprobar. Máximo dos vueltas.
   - **Pregunta dudosa**: tras dos vueltas sigue fallando, o el modelo señala que la clave contradice la norma o el material, o la norma ha cambiado → **incidencia de pregunta** en el panel (`/admin/preguntas?incidencias=1`) con el motivo y el párrafo de los apuntes que la contradice.

**Meta por tema: 100 % de grupos cubiertos o con incidencia.** El informe de cada tema dice: cubiertas, huecos resueltos, incidencias abiertas, por epígrafe.

Se repite automáticamente cuando: entran preguntas nuevas al tema (solo esas), cambia la correcta de una pregunta, o el propietario edita un párrafo enlazado a preguntas (solo las enlazadas a ese párrafo).

### Paso F. Revisión del propietario, centrada en lo que importa

Nadie puede leer a fondo decenas de miles de palabras por tema antes de publicar. La revisión se concentra en:
- las **incidencias** de preguntas;
- los párrafos marcados «revisar: sin material de apoyo»;
- los párrafos con **copia literal** de material no normativo;
- una **muestra** aleatoria de 10 párrafos por tema, para juzgar el tono y la calidad.

Con eso resuelto se publica; el resto se corrige al estudiar con el botón «Esto está mal» en los apuntes, que también existe para el alumno.

### Paso G. Mantener

- Panel `/admin/apuntes`: por tema, preguntas cubiertas, incidencias, fecha de la última comprobación y si el material ha cambiado desde entonces.
- La comprobación del paso E entra en las puertas como **prueba de datos** (no de código): un comando `opofuente notes verify --all` que falla si algún tema publicado baja del 100 %.

---

## 3. Modelo de datos (añadir a lo del 6.1)

- `question_groups` (id, firma normalizada) y `question_versions.question_group_id`.
- `question_topic_assignments` o ampliar `curriculum_mappings` con `epigraph_index` y `confidence`.
- `topic_facts` (id, curriculum_node_id, epigraph_index, subsection_key, text, kind `normative|technical`, source_question_group_ids, created_at, status).
- `topic_note_sections` (topic_note_id, subsection_key, anchor, body_markdown, status `pending|reviewed`) — para regenerar y revisar por partes.
- `question_note_anchors` (question_group_id, topic_note_id, anchor, quoted_sentence, result `covered|gap|doubtful`, checked_at).
- `question_issues` reutiliza `question_issue_reports` con `origin = notes_check`.

---

## 4. Lectura de apuntes largos (pantalla del alumno)

Con temas largos, la pantalla de apuntes tiene que ayudar a moverse:
- **Capítulos** = epígrafes oficiales; un capítulo por pantalla, con "Anterior / Siguiente".
- **Índice** a la izquierda con apartados y subapartados, y una marca de leído por apartado.
- **Buscador** dentro del tema.
- **Modo repaso**: solo esquema, tablas, «Datos que caen», trampas y resumen.
- Al final de cada apartado: **«Practicar este apartado»** (test con las preguntas enlazadas a sus párrafos).
- Desde cualquier pregunta corregida: **«Ver en apuntes»** abre el párrafo exacto, resaltado.
- Las notas al margen («Esto cae») salen de los hechos con más preguntas detrás, **nunca** de frases inventadas.

---

## 5. Qué hace falta para hacerlo y cuánto trabajo es

**Imprescindible: una clave de API de un modelo** (`OPOFUENTE_LLM_PROVIDER=openai_compatible`; la API de DeepSeek vale). Con este volumen, redactar a mano como agente no es viable: hablamos de miles de llamadas. Cuenta aproximada de llamadas (no de dinero: el propietario debe mirar los precios vigentes de la API que elija):
- Paso A (clasificar sin tema): ≈ 7.401 / 20 ≈ **370**.
- Paso B (hechos): ≈ 13.327 / 20 ≈ **670**.
- Paso D (redactar): ≈ 33 temas × 20–60 subapartados ≈ **1.000–2.000**.
- Paso E (comprobar): ≈ **670 por vuelta**, dos o tres vueltas.

El generador debe: ir por lotes, **guardar cada resultado en cuanto llega** (si se corta, se reanuda donde iba), limitar las llamadas por minuto y anotar los tokens gastados en el informe.

## 6. Orden

| # | Qué | Hecho cuando |
|---|---|---|
| 1 | Paso A completo (grupos, tema y epígrafe para todas) + pantalla de revisión de dudosas | 100 % con tema/epígrafe o fuera de temario |
| 2 | Pasos B–E en **tres temas piloto**: **IV.7** (234 preguntas, técnico), **I.6** (139, mixto) e **I.1** (1.865, el más grande y normativo) | informe con 100 % cubiertas o incidencia; **parar** para que el propietario y yo leamos los tres |
| 3 | Ajustar instrucciones según la lectura del piloto | — |
| 4 | Resto de temas, por bloques, con el informe de cada uno | 33/33 al 100 % cubiertas o incidencia |
| 5 | Pantalla de lectura del §4 y "Ver en apuntes" al párrafo | recorrido E2E: fallar una pregunta → ver el párrafo exacto |
| 6 | Revisión del propietario (paso F) y publicación | 33/33 publicados |

Esto es trabajo de servidor y por lotes: **puede ir en paralelo** a las fases de pantallas (Fase 1–5). Recomendación: una sesión de pantallas, una de apuntes, alternando, para que no se pare ninguna de las dos.

---

## 7. Revisión de las capturas de v0 y Stitch

El diseño va bien. Me quedo con:
- **Test en curso de v0**: la hoja de respuestas a la derecha con la casilla fallada en rojo y la correcta en verde funciona exactamente como queríamos. Es la referencia para el test.
- **Apuntes de Stitch**: tres columnas (índice, texto en serif, notas «Esto cae» al margen). Es la referencia para los apuntes, más el §4 de este documento.
- **Los apuntes de v0 son demasiado cortos y estrechos**: sirven para el estilo, no para el contenido.

A corregir al construir:
1. Las notas al margen de Stitch afirman cosas como «ha aparecido en 4 de las últimas 5 convocatorias (OEP 2019, 2020, 2022 y 2023)». **Es inventado.** Esa línea solo puede salir si la calcula la aplicación con los exámenes que tiene.
2. En los apuntes de v0, el índice va dentro de un recuadro con borde negro que pesa demasiado: índice sin recuadro, con la sección actual en azul.
3. El botón «Test de este tema» de v0 usa la tipografía serif de los apuntes: los botones van siempre en Atkinson.
4. La explicación tras corregir (v0) va bien en verde suave cuando aciertas o fallas, pero el título «Respuesta correcta: C. TCP» repite lo que ya marca la opción: basta con la explicación y «Ver en apuntes».
