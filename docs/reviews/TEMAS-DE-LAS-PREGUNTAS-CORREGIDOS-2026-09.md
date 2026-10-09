# Temas de las preguntas: dos errores corregidos y una vía nueva medida (30-09-2026)

La tarde cerró con 8.759 preguntas enlazadas a un tema de TAI y 5.565 con ningún mapeo, y con la conclusión de
que las vías léxicas estaban agotadas. Esta pasada ha mirado los **datos** en vez de las señales del texto, y ha
encontrado tres cosas: una vía que funciona (validada), dos etiquetas mal puestas a escala y una tabla de reglas
con un término en el tema equivocado.

## 1. La vía nueva: el tema del **conjunto**

Un conjunto de preguntas es una unidad coherente: los 233 conjuntos del banco son mazos, cuestionarios o
exámenes, y cada uno suele ser de un solo tema. Si 20 de sus 25 preguntas ya están en el tema 4, las otras 5
casi seguro también.

Lo importante es que **se puede comprobar sin creérselo**: se esconde el tema de cada pregunta etiquetada, se
predice con las demás de su conjunto y se cuenta. Medido (`_oficial/tema_por_el_conjunto.py`):

| | |
| --- | --- |
| casos probados | 6.078 |
| aciertos | **6.062** |
| **precisión** | **99,7 %** |
| regla | tema ganador con ≥80 % de las etiquetadas y ≥5 etiquetadas en el conjunto |

Fallos, 16, y dónde: «TAI · Normativa» (5), «TAI · TEST B1» (3), «1600-Preguntas-Constitución» (3+2),
«TPJULICEIV-V.15P1» (2) y «Derechos digitales» (1) — todos conjuntos que juntan material de varios temas.

**Ganancia real: 215 preguntas** (2,6 % de las que no tenían tema). Es poco porque los conjuntos son de todo o
nada: los grandes sin etiquetar son precisamente los heterogéneos. Pero es gratis y está medido al 99,7 %.

## 2. Error de escala: 119 preguntas del Tribunal Constitucional en el tema equivocado

Salió al medir la precisión de las reglas estrechas contra las preguntas ya etiquetadas: la regla de I.2 fallaba
668 veces, y 605 de esos fallos eran preguntas puestas en **I.1**. Mirando por qué, la tabla de reglas metía
«tribunal constitucional» entre los términos de **I.1**, y el temario de TAI pone «El Tribunal Constitucional:
composición y atribuciones» en **I.2**, junto a las Cortes Generales y el Defensor del Pueblo.

Corregido con `_oficial/corregir_el_tribunal_constitucional.py`, y con un detalle que importa: se busca por el
**enunciado**, no por las opciones. Medido en las dos formas: buscando en enunciado y opciones salían 231
candidatas, pero leyendo la muestra había preguntas de la Corona que sólo mencionan el Tribunal Constitucional
en una opción. Buscando sólo en el enunciado salen **119**, y las 12 leídas son todas del Tribunal
Constitucional (su composición, su nombramiento, su mandato, el recurso de amparo):

- **119 mapeos retirados** por `DELETE /curriculum-mappings/{id}` (queda auditado) y **119 puestos en I.2**;
- **18 más** que nombraban el Tribunal Constitucional y no tenían tema: ganancia neta;
- **0 fallos**.

## 3. Error de escala: 216 preguntas de las Cortes en I.1

De los mismos 668 fallos, **216** eran preguntas cuyo enunciado habla de las Cortes Generales, el Congreso, el
Senado, la Diputación Permanente o el Defensor del Pueblo, y estaban en I.1 (que es «derechos y deberes
fundamentales» y «la Corona»).

No se movieron a ciegas: se descartan las que además nombran la Corona, la sucesión o los derechos
fundamentales (**12** — el temario sí pone ahí «El Rey, al ser proclamado ante las Cortes Generales, prestará
juramento de…»), y las que nombran el Gobierno o los ministros (**24** — las relaciones Gobierno-Cortes son
**I.3**). De las que quedan se leyeron **20 al azar**, y las 20 son material de I.2:

    · ¿Cuántos Senadores elige una Comunidad Autónoma por el simple hecho de serlo?
    · ¿Cuál de las siguientes no es una Comisión legislativa permanente del Congreso de los Diputados?
    · Una de las siguientes actuaciones no puede ser ejercitada por la Diputación Permanente:
    · El Defensor del Pueblo es, según la Constitución:

**216 movidas** (216 retiradas, 216 puestas), **0 fallos**. Matiz dicho en voz alta: unas pocas hablan de la
cuestión de confianza o de la disolución de las Cámaras, que son relaciones Gobierno-Cortes vistas desde el
Congreso; se mueven igual porque su sujeto es la Cámara, y dejarlas en I.1 era peor.

## 4. Las reglas estrechas, donde ya había bloque

2.420 preguntas tenían **bloque** (`I`, `II`, `III`, `IV`) y ningún tema: entraron por el CSV de un mazo o un
examen con el bloque puesto. Las reglas estrechas se habían aplicado sólo a las que no tenían **nada**, así que
se quedaron fuera.

Se aplican ahora con dos guardas (`_oficial/reglas_estrechas_en_las_que_ya_tienen_bloque.py`): el tema tiene que
estar **dentro del bloque que la pregunta ya declara**, y cada regla pasa antes por las preguntas que ya tienen
otro tema para medir su precisión. La medición descartó cuatro reglas por imprecisas:

| regla | acierta | falla | precisión | dónde falla |
| --- | --- | --- | --- | --- |
| III.8 | 81 | 3 | **96,4 %** | III.7 |
| I.1 | 91 | 3 | **96,8 %** | I.7 |
| I.7 | 374 | 19 | **95,2 %** | I.6 |
| I.4 | 368 | 24 | **93,9 %** | I.7 |
| IV.9 | 163 | 15 | **91,6 %** | IV.4 |
| I.8 | 364 | 41 | 89,9 % | III.7 |
| I.9 | 27 | 4 | 87,1 % | III.7 |
| III.9 | 70 | 15 | 82,4 % | IV.2 |
| I.5 / I.6 | 306 / 180 | 82 / 61 | 78,9 % / 74,7 % | **descartadas** |
| IV.6 / II.1 | 152 / 47 | 66 / 21 | 69,7 % / 69,1 % | **descartadas** |
| I.2 | 602 | 528 | 53,3 % | I.1 — es el síntoma del §2 y §3 |

**164 temas puestos, 0 fallos**, y **55 descartadas** porque la regla caía en otro bloque (una regla de IV.9 no
puede mover al bloque II una pregunta que ya dice que es del II).

## 5. Guardia Civil: cerrado

**241 de 241** preguntas con su tema. Quedaba una, la 13 del modelo A (Ley Orgánica para la igualdad efectiva de
mujeres y hombres), que es del tema **2** (IGUALDAD EFECTIVA DE MUJERES Y HOMBRES): puesta. El tema 25 (Lengua
Española) sigue con **0 preguntas** y no es un fallo: el examen de 2026 no pregunta esa materia.

## 6. Por qué las 5.349 que quedan sin mapeo no tienen tema

Contarlas no sirve para decidir; saber de qué están hechas, sí (`_oficial/por_que_una_pregunta_no_tiene_tema.py`):

| causa | preguntas | qué es |
| --- | --- | --- |
| **material heterogéneo** | 2.997 (56,0 %) | documentos que juntan preguntas de muchos sitios («BLOQUE GENERAL::TESTS GENERALS», «Doc adicional», «baquedano», «Material adicional», «Test por temas»). El documento no decide y hay que ir pregunta a pregunta: **esto es lo que necesita DEBT-014** |
| **documento identificado, sin tema declarado** | 1.341 (25,1 %) | exámenes y simulacros de TAI cuyo nombre sí dice qué son (Tai_BBDD_2025, SIMULACRO_TAI_ABRIL26, Supuesto Base de Datos…) pero no de qué tema |
| **fuera del alcance** | 959 (17,9 %) | exámenes de otras administraciones y otros cuerpos que ya están en el banco: Ayuntamiento de Madrid, Universidad de Sevilla, Xunta de Galicia, Parlamento de La Rioja, Concello de Pontevedra, Ajuntament de Barcelona, GSI, cuerpo facultativo. El propietario dejó esos organismos fuera del objetivo, así que **no se les pone tema de TAI**: ponerlo sería afirmar que una pregunta de la Xunta es del temario de TAI |
| **sin documento de origen** | 53 (1,0 %) | casos sueltos (la sección no está en la base) |

Dos vías más probadas y **descartadas con la medición delante**, para que no se repitan:

- **la cita de la pregunta** (`question_evidence` → documento mapeado): 0 de 8.010. Las citas del banco
  apuntan a documentos que son **bancos de preguntas**, no material de estudio, y ninguno está mapeado.
- **el nombre del documento** pasado por la regla de texto: 97,9 % de acierto sobre las 141 preguntas ya
  etiquetadas donde decide, pero sólo decide **10** de las que no tienen tema (0,1 %). Esta vía ya se había
  usado para cinco temas y no le queda nada que rascar.

## 7. Dónde queda el banco

| | preguntas |
| --- | --- |
| en total | **16.984** |
| **con tema de TAI** | **9.156** (182 además con bloque) |
| sólo con bloque de TAI | 2.238 |
| con tema de Guardia Civil | 241 |
| sin ningún mapeo | 5.349 |

La base al cerrar: 16.984 preguntas · 4.146 documentos · 4.217 versiones aceptadas · **33.212 mapeos** · 329.654
fragmentos · 0 trabajos en cola.

Y el reparto por tema cambia donde tenía que cambiar: **I.1 pasa de 2.317 a 1.988** preguntas e **I.2 de 296 a
821**. No es que haya más preguntas: es que 335 estaban contadas en el tema equivocado. Los dos temas con menos
preguntas siguen siendo IV.3 (70) y II.2 (83), y los dos con más, I.1 (1.988) e I.2 (821) frente a III.2 (77) y
II.4 (94).

## 8. Lo que sigue necesitando una decisión

**DEBT-014** (embeddings o modelo local). Las 2.997 preguntas de documentos heterogéneos y las 1.341 de
documentos identificados sin tema declarado no se pueden repartir con señales léxicas: está medido por cinco
vías. Las otras 959 están fuera del alcance a propósito.
