# Los apuntes, sin repetidos y de una sola generación (30-09-2026, noche)

Tres cosas, las tres con medición delante: un número que yo había publicado mal, un montón de texto repetido
dentro de los apuntes y dos generaciones enteras de apuntes viviendo a la vez dentro de la aplicación.

## 1. Corrijo un número que publiqué mal: los fragmentos por tema estaban contados dos veces

Al medir por qué los apuntes tenían fragmentos repetidos apareció la causa, y afectaba también al mapa de
temas. El mapeo al programa en la aplicación es **polimórfico**: una misma asignación se puede guardar contra
la `document_version`, contra su `representation` o contra su `artifact`. Y la consulta que usaban mis
programas unía las tres vías con un `or`, así que **cada documento aparecía dos veces**.

Medido: **10.340 asignaciones por `representation` y 10.355 por `artifact`**, casi el mismo conjunto. Sumando
por fila, los 33 temas daban **177.288 fragmentos**; contando cada versión una sola vez son **129.099**. El
factor va de ×1,00 a ×1,80 según el tema, porque sólo se duplican los documentos mapeados por dos vías.

Arreglado en `mapa_de_material_por_tema.py` (cuenta cada pareja nodo–versión una vez) y en
`anadir_material_de_la_biblioteca_a_los_apuntes.py` (que era el que metía los fragmentos repetidos en los
apuntes). **Los números de fragmentos por tema que publiqué antes están inflados y estos son los buenos**:

| tema | publicado (mal) | real |
| --- | --- | --- |
| I.1 | 18.380 | **9.076** |
| I.7 | 22.211 | **10.720** |
| I.5 | 9.654 | **4.552** |
| III.9 | 2.832 | **1.930** |
| IV.5 | 7.740 | **6.977** |
| IV.9 | 2.171 | **1.406** |

Lo que **no** cambia, porque no dependía de ese error: los temas son 33 de 33 con material, ninguno por debajo
de 50 fragmentos y ninguno sin preguntas. El más flojo sigue siendo el mismo tipo de tema (III.4, con **1.033**
fragmentos, donde antes decía 1.662).

## 2. Los apuntes tenían 1.088 fragmentos repetidos palabra por palabra

Medido con `medir_lo_que_se_repite_en_los_apuntes.py`, sobre los 37 apuntes y sus 8.421 fragmentos:

- **1.074** repetidos palabra por palabra (**12,8 %**), y de esos grupos **787 repetían el mismo documento**,
  que es la firma del error de la consulta polimórfica del §1;
- **488** fragmentos más (5,8 %) en parejas que se parecen mucho sin ser iguales (Jaccard ≥ 0,70 sobre grupos
  de 8 palabras). Ésos **no se han tocado**: son textos distintos que cuentan lo mismo, y decidir cuál sobra
  es un juicio, no una regla.

Quitados con `quitar_lo_repetido_de_los_apuntes.py`. Lo delicado no es borrar, es que **el resumen del apunte
cita los fragmentos por su número** (`([35], [37])`): al quitar uno hay que renumerar y traducir las
referencias, apuntando las que citaban un fragmento borrado al que se conservó (el texto es el mismo, así que
la afirmación sigue apoyada en lo mismo). El programa **comprueba una invariante antes de escribir**: toda
referencia tiene que apuntar a un fragmento que existe y con el mismo texto. Los dos primeros intentos se
negaron a escribir (29 y luego 9 apuntes), y por eso no rompieron nada:

- el primero tradujo las marcas `**[67]**` como si fueran referencias y las renumeró dos veces;
- el segundo comparaba el texto en crudo, y hay fragmentos cuyo propio texto lleva dentro un `[n]`, así que
  cambiaban a propósito al traducir. Ahora se comparan quitando las referencias de los dos lados.

Resultado: **8.421 → 7.333 fragmentos** (1.088 fuera) y la medición queda en **3 repetidos** (0,0 %).

## 3. Dos generaciones de apuntes dentro de la aplicación

El otro hallazgo: cada vez que se rehacían los apuntes y se volvían a ingerir, la aplicación creaba
**documentos nuevos con el mismo título** en vez de una versión nueva. Y no se puede arreglar después:
`mark-supersedes` contesta **409 «Solo se sustituyen versiones del mismo documento»**. Así que había la
generación de las 13:17 (102 partes), la de las 18:03 (111 partes) y la de ahora, todas aceptadas y mapeadas a
la vez: el tema enseñaba las tres.

La ruta correcta existe y no la estaba usando: `POST /documents` **con `document_id`**, que la propia API
documenta como «Promociona un artefacto a documento (o le añade una versión)». Emparejar cada parte tuvo su
miga: **las partes de un apunte comparten título** (el número de parte no está en el título), así que el título
no dice a qué documento pertenece cada fichero. Se sigue la cadena **nombre de fichero → artefacto → versión →
documento**, que sí es fiable porque cada parte entra con el mismo nombre en todas las generaciones.

Primero intenté emparejar por título y el plan salió mal (36 documentos destino para 101 partes, y 555
«generaciones anteriores»); cambiado a la cadena, salen **101 partes y 101 documentos destino distintos**.

Resultado (`apuntes_al_dia_en_la_app.py` + `dejar_los_apuntes_mapeados.py`):

- **101 partes al día, 0 fallos**;
- **101 versiones de apunte mapeadas** (las de ahora) y **17 mapeos retirados** de versiones que ya no son las
  que se estudian — además de los 240 que retiró la primera pasada;
- aviso para el que venga: `accept` **devuelve 409 «No se puede aceptar una versión accepted»** porque la
  promoción acepta sola. Contarlo como fallo dio **56 falsos negativos** en el primer intento.

**Queda un resto que no se puede limpiar desde fuera**: las generaciones anteriores siguen en la biblioteca y
en la búsqueda (sin mapear, así que no salen en el dossier ni en el mapa de temas), porque **la aplicación no
tiene ruta para retirar un documento**. Es un defecto de código, no de material: hace falta un
«archivar/retirar documento» o que `mark-supersedes` admita documentos distintos con el mismo título.

## 4. De paso: 195 preguntas más con su tema, medido con partición de tres

Las reglas estrechas se escribieron a mano y cubren 13 de los 33 temas. Se hizo al revés
(`terminos_por_tema_medidos.py`): se usan las 9.153 preguntas que **ya** tienen tema como patrón, se eligen los
términos que aparecen ≥8 veces y ≥95 % de ellas en un solo tema, y se mide sobre preguntas que no se usaron
para elegirlas. **Tres particiones, no dos**: entrenamiento (elegir términos), validación (elegir el punto de
corte) y prueba (el número que se publica), porque elegir el corte mirando el mismo conjunto con el que luego
se informa maquilla el resultado.

| punto de corte | validación: precisión | cobertura |
| --- | --- | --- |
| 1 término | 93,5 % | 20,5 % |
| **2 términos** (el elegido) | **97,2 %** | 9,2 % |
| 3 términos | 97,0 % | 5,7 % |

Con el corte elegido en validación, el diccionario se rehace con entrenamiento **y** validación (847 términos,
24 temas) y se mide en prueba: **95,7 % de precisión** (225 de 235), por encima del 95 % que exigí **antes** de
mirar. El primer intento dio 94,7 % en prueba y el programa **se negó a aplicar nada**: en vez de bajar el
listón, se mejoró el método (rehacer el diccionario con la validación incluida). Aplicado: **195 preguntas**.

## 5. Dónde queda todo

| | |
| --- | --- |
| preguntas en el banco | **16.984** |
| con tema de TAI | **9.342** (antes 9.156 en esta misma ronda) |
| apuntes dentro de la aplicación | **101 partes**, una sola generación mapeada, sin repetidos |
| fragmentos de los apuntes | **7.333** (eran 8.421) |
| temas | **33 de 33** con material, ninguno por debajo de 1.000 fragmentos |
| base | 4.146 documentos · 4.217 versiones aceptadas · 33.287 mapeos · 343.633 fragmentos · 0 en cola |

Comprobado: la búsqueda responde en ~1 s y devuelve el apunte de III.9; el dossier de III.9 trae **54 fuentes y
1.817 pasajes**, con sus **3 partes de apunte** dentro (450, 450 y 267 tramos), y el de IV.5, 34 fuentes.
