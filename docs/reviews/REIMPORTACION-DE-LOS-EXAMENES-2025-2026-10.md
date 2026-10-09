# Los exámenes de TAI 2025 reimportados, y el orden de la composición (octubre 2026)

Veredicto en una línea: los cuatro exámenes oficiales de TAI 2025 están **reimportados con la
estructura real de su cuadernillo** —numeración por secciones, reservas como las imprime el papel y la
letra de la plantilla oficial enlazada— y, al hacerlo, salió un defecto que no era de los datos: **la
composición de una sesión ordenaba por posición**, así que con la numeración por secciones mezclaba la
parte primera con los supuestos prácticos. Está arreglado y con prueba.

## 1. El lector: «d MODIFICADA» (rama `plantilla-modificada`)

La puerta que faltaba del lector era real y su efecto se midió sobre la plantilla oficial de promoción
interna: el lector devolvía **84 líneas de 85** y la respuesta 7 de la primera parte (`d MODIFICADA`,
que la Comisión cambió tras las alegaciones) se perdía. Con el arreglo:

```
líneas leídas: 85   ·   posición 7 · letra ('d',) · nota 'respuesta modificada'
```

Puertas: **18 de 18 en verde en 23:08 minutos** en Windows (E2E dentro del guion, 54 de 54), fusionada
(`main` = `6f73f17`).

## 2. La reimportación, paso a paso

El texto con el que se importaron estos exámenes **renumeraba las preguntas del 1 al 135** y no marcaba
ninguna reserva: de ahí que las posiciones no tuvieran repetidos (y la comparación en orden no se
pudiera aplicar) y que las reservas vinieran de otra fuente. Lo que se hizo:

1. **Releer los cuadernillos del INAP** desde sus PDF, página a página, conservando su estructura:
   `PRIMERA PARTE` + `Preguntas de reserva` + `SUPUESTO I` + `Preguntas de reserva` + `SUPUESTO II` +
   `Preguntas de reserva`. Validado con el analizador de la propia aplicación:

   | examen | preguntas | reservas | posiciones repetidas | 4 opciones | incidencias |
   | --- | --- | --- | --- | --- | --- |
   | libre A / B | 135 | 15 | 55 | 135 | 0 |
   | promoción A / B | 85 | 11 | 35 | 85 | 0 |

2. **Ingerir** los cuatro textos y aceptarlos (4 versiones nuevas), y **montar los conjuntos nuevos**
   importando el documento: cada pregunta entra con su **cita** al papel (135/135/85/85) y con la
   numeración y las reservas del cuadernillo.
3. **Importar la clave desde la plantilla oficial** con su texto completo (`kind=answer_key` y la
   versión de la plantilla): el resultado es la prueba de que la comparación en orden funciona —
   **135, 135, 85 y 85 entradas y 0 sin pareja** en los cuatro— y la clave queda **con la plantilla
   enlazada** en la misma llamada.
4. **Activar** las cuatro claves.
5. **Archivar los conjuntos viejos y retirarles la clave activa** (dos campos de la base: la API no
   tiene ruta para ninguna de las dos cosas). No se borró nada: la historia y las sesiones de estudio
   que había siguen intactas.

Estado de los cuatro conjuntos nuevos:

| conjunto | preguntas | reservas | con tema | entradas de la clave | plantilla enlazada |
| --- | --- | --- | --- | --- | --- |
| TAI libre 2025 A | 135 | 15 | 135 | 135 | ✓ |
| TAI libre 2025 B | 135 | 15 | 135 | 135 | ✓ |
| TAI promoción 2025 A | 85 | 11 | 85 | 85 | ✓ |
| TAI promoción 2025 B | 85 | 11 | 85 | 85 | ✓ |

## 3. Dos huecos de la aplicación que salieron por el camino

1. **La columna `topic` de una importación solo se aplica a las preguntas que esa llamada crea.** Si
   las preguntas ya existen (las creó antes el `import-document`), la columna se lee y **no se aplica a
   nada**: el informe dice `existing: 135 · topics_from_column: 0` y no hay ninguna incidencia que lo
   explique. Los temas se han heredado con un script que inserta el mapeo con la misma forma que
   `map_question_to_node` (440 mapeos, 0 sin pareja), pero la aplicación debería decirlo o aplicarlo.
2. **La composición de una sesión ordenaba por posición** (arreglado en §4).

Y una corrección de lo que yo mismo había escrito: el texto de la plantilla **no está cortado**. Lo que
está cortado es la **cita**: la versión de la plantilla tiene un solo fragmento de **1.198** caracteres
(el tope del recorte), mientras el texto extraído tiene los 135 renglones completos. Por eso la clave
sale completa (se importa del texto de la plantilla, no del fragmento) y lo que faltaba era la cita.

## 4. La composición va en el orden del documento (rama `composicion-en-orden-documento`)

Medido con la API contra los datos reales, después de reimportar: al montar el examen oficial de la
primera parte (80 + 5), la sesión salía así:

```
sesión 1 · pregunta nº 1 · En la Constitución Española de 1978…
sesión 2 · pregunta nº 1 · Se desea garantizar en la base de datos que el campo DNI…
sesión 3 · pregunta nº 1 · Se le asigna la gestión de la red interna 10.30.16.0/20…
sesión 4 · pregunta nº 2 · Indique cuál de los siguientes principios…
```

Es decir: parte primera nº 1, supuesto I nº 1, supuesto II nº 1, parte primera nº 2… La causa:
`all_questions` ordenaba por `(position, stable_key, id)` y en un examen que numera desde 1 en cada
sección las posiciones se repiten. El arreglo: **ordenar por `questions_in_document_order`** (el orden
en que se leyó el material), que es el mismo orden que usa la alineación en orden. En un conjunto sin
posiciones repetidas los dos órdenes coinciden, así que no cambia nada para los demás.

Con prueba: un cuestionario de dos secciones que numeran desde 1 se compone `3 de la primera parte + 2
del supuesto + la reserva al final`; la prueba **falla con el código anterior** y pasa con el nuevo.

## 5. Lo que queda

1. **Guardia Civil 2026**: sus conjuntos mezclan conocimientos e idioma con números repetidos y les
   faltan las 6 reservas (101-105 y la de idioma). Es el mismo trabajo de reimportación que se acaba de
   hacer con TAI, y ahora la composición ya sabe ordenar por el documento (su caso es el mismo: dos
   secciones que numeran desde 1).
2. **Rehacer las claves a medias** de los 20 conjuntos flojos (7.876 preguntas hoy sin corregir).
3. Los dos huecos de §3.1 y el recorte de la cita (§3).

## 6. Cómo se reproduce

```
$py = "F:\temp-opofuente\opofuente-main\.venv\Scripts\python.exe"
$of = "F:\EspacioCodigo\proptech-access-control\docs\opofuente\_oficial"

& $py "$of\preparar_los_examenes_oficiales_de_tai_2025.py" --escribir   # relee los cuadernillos
& $py "$of\reimportar_los_examenes_oficiales_de_tai_2025.py"            # informe de la reimportación
& $py "$of\reimportar_los_examenes_oficiales_de_tai_2025.py" --aplicar
& $py "$of\heredar_los_temas_de_los_examenes_reimportados.py" --aplicar
& $py "$of\probar_el_examen_reimportado.py"                             # composición del examen
& $py "$of\comprobar_las_reservas_contra_el_cuadernillo.py"             # reservas frente al papel
```
