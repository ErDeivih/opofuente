# La cola de revisión de la clasificación (8-oct-2026) y lo que quedó bloqueado

## Lo que está hecho y verificado

**`c902f10` — la maquinaria de clasificación** (en `main`): la ruta por lotes
`POST /api/v1/questions/topics/bulk`, que **no es un segundo camino de escritura** (cada fila entra por el
mismo `assign_topic` que la ruta individual: mismo `UNIQUE`, mismo evento `question.mapped`, y hay una
prueba que lo compara **campo a campo contra la base**); el comando
`uv run python -m opofuente.tools.clasificar_preguntas`; el **fuera de temario** en su propia tabla
(`0028`, con motivo validado, sin código ni posición: imposible confundirlo con un tema, excluido de
simulacros y exámenes oficiales) y los **umbrales** (≥0,75 se asigna; 0,5–0,75 a la cola; <0,5 no se
escribe) puestos con la calidad medida delante.

**`9bc32ac` — la pantalla de la cola** (rama `f5-pantalla-revision`, **18/18 puertas**, 24:40, 60 E2E):
la lista de propuestas con el enunciado, el tema y epígrafe propuestos, **la confianza y el motivo que dio
la IA**, todo con **teclado** (aceptar, cambiar, marcar fuera de temario, saltar) y aceptación en lote; la
**agrupación por pregunta** (una tarjeta por pregunta: aceptar un tema retira los demás, así no se pueden
dejar dos temas aceptados por descuido); y la **guarda de corrida** (dos arranques sobre la misma base: el
segundo se niega; la marca se suelta aunque la primera falle).

Además, en esa rama, la **guarda del panel** quedó mejor que estaba: las dos pruebas E2E del panel ya no
llevan una lista escrita a mano de sus secciones, sino que **derivan de `ADMIN_NAV_ITEMS` y
`ROUTE_REDIRECTS`** y exigen que cada dirección enseñe una pantalla de verdad con título propio y distinto.
Si mañana alguien añade una entrada al menú sin su ruta, sigue fallando.

## La fusión de `9bc32ac` está bloqueada, y a propósito

`git merge --ff-only` **aborta** porque Claude tiene **45 ficheros sin guardar** en `opofuente-main` y uno
de ellos —`apps/web/src/api/queries.ts`— también lo toca nuestro commit:

| | qué añade |
|---|---|
| Nuestra fusión (F5) | +57 líneas: imports de `./topicReview` y las claves de la cola de revisión |
| Claude (sin guardar) | +69 líneas: la promoción de artefactos en lote (`PromoteArtifactsInput`) |

Son **dos cosas distintas en zonas distintas y las dos solo añaden**. Cuando Claude commitee, la fusión
será automática. **No se ha forzado**: mover la referencia de `main` sin tocar el árbol dejaría el fichero
con la versión antigua y las 57 líneas nuevas desaparecerían en silencio al siguiente guardado.

## Cifras medidas en la base (no en el informe del comando)

| | antes | después |
|---|---|---|
| Preguntas sin ningún mapeo | 5.249 | **3.460** (−1.789: exactamente las que tocó la máquina) |
| Mapeos | 12.487 | **16.068** (+3.581: 2.196 aceptados y **1.385 a la cola**) |
| Fuera de temario | 0 | **9** (4 enunciados rotos + 5 de otra administración) |
| Auditoría | — | los 3.581 con **exactamente un** `question.mapped`; estado y confianza coinciden en los 3.581 |

## Dos cosas que hay que resolver, y las dos las decide el propietario

1. **4 preguntas con dos temas y 9 con más de un epígrafe**, salidas de **dos corridas solapadas** sobre
   los datos reales (una de ellas, del banco «astrocuestion», anterior a la mía y que yo creí hecha sobre
   una copia). Los identificadores están en el informe del agente. La pantalla las agrupa por pregunta y
   el propietario las despacha viéndolas; **no se ha tocado ninguna fila a mano**.
2. **21 preguntas con más de un tema `accepted`**, y **19 no las escribió el clasificador** (actor
   `local`: catalogación heredada y migraciones anteriores; entre ellas el examen oficial del INAP de 2025
   con I.3 + II.3, el mismo número en dos bloques). Una pregunta en dos temas cuenta en los dos y ensucia
   el progreso. Encargado como **segundo commit** de la misma pantalla: una sección que las liste **con el
   actor de cada mapeo** y permita dejar uno solo, sin arreglarlas en masa por nuestra cuenta.

## Coste medido

**0,3466 $** por los primeros bancos (82 llamadas, 558.670 tokens de entrada y 437.959 de salida):
**0,00021 $ por pregunta**, no los 0,0000366 $ del piloto de apuntes —allí el prompt era pequeño; aquí
lleva los 33 temas y los 134 epígrafes en cada llamada—. La estimación de 0,63 $ para las 17.183
**queda corregida a ≈3,6 $**.
