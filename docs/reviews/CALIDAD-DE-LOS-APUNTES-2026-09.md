# Calidad de los apuntes por tema: la medida que faltaba (28 de septiembre de 2026)

**Qué se pregunta:** los 33 apuntes están hechos con la regla trozo-a-nodo, que coloca cada fragmento en el
tema cuyo título oficial más se parece al texto. ¿Cuántos fragmentos están **de verdad** en su tema?

**Por qué hacía falta medirlo otra vez:** las dos medidas que había no servían para esto.

| Medida | Qué dio | Por qué no vale |
|---|---|---|
| La del principio (`RESULTADO-LAYA-TAI`, con el troceador de pruebas) | **86,7 % de acierto de bloque** y **53,8 % de tema** | Se hizo con otro troceador y sobre una muestra distinta |
| El acuerdo con el **vocabulario de cada tema** (28-sep) | **85,8 %** de coincidencia | Es **circular**: el vocabulario se construyó con esos mismos fragmentos, así que tiende a darles la razón |

**La única medida que no se engaña a sí misma es leerlos.** Se sacaron **20 fragmentos al azar** (semilla
fija, `auditar_fragmentos.py`) de los que entran a los apuntes, con su tema y su ajuste, y se miraron uno a
uno contra el título oficial del tema.

## Lo que salió

| Veredicto | Fragmentos | Ejemplo |
|---|---|---|
| **Del tema, claro** | 12 de 20 (60 %) | «Dependencia funcional: X → Y…» en 3.1 Modelado de datos |
| **Dudoso** (relacionado, pero el título no lo pide) | 3 de 20 (15 %) | El Defensor del Pueblo en 1.2 Cortes Generales |
| **De otro tema, claro** | 4 de 20 (20 %) | «Funcionarios interinos…» (TREBEP) en 1.3 El Gobierno; «E/S programada, interrupciones» en 3.2 Lenguajes de programación; «tratados internacionales» en 1.6 Firma electrónica; «Active Directory» en 4.3 Correo electrónico |

Los errores **no son aleatorios**: caen en el **tema vecino del mismo bloque** (1.3 por 1.4, 4.3 por 4.4,
2.1 por 2.2) o en el bloque contiguo. Es lo que se ve leyendo: el 1.7 (protección de datos) contiene
fragmentos de los artículos 30 a 33 de la Constitución y de la Ley de Igualdad, porque el documento del que
salen, «Bloque 1 Actualizado 2026», cubre el bloque entero y sus trozos comparten palabras con varios
títulos («derechos», «obligaciones», «garantía», «digitales»).

**Con 20 fragmentos el margen de error es amplio** (±20 puntos con un 95 % de confianza): lo que se puede
afirmar es «del orden del 60 %, no del 90 %», no un decimal.

## El ajuste no separa: subir el umbral no arregla esto

Los cuatro fragmentos de otro tema tenían ajustes de **0,285, 0,295, 0,379 y 0,524** — el de 0,524 es más
alto que la mayoría de los buenos. Se comprobó también que **ningún** fragmento de los apuntes se apoya
solo en palabras que aparecen en muchos títulos (0 de 2.547), así que ni contar palabras ni mirar su rareza
los distingue. **Subir el umbral quitaría material bueno sin quitar los errores.**

## Qué se probó para arreglarlo, y qué salió

Se probaron **cuatro** caminos en dos sesiones, y los cuatro se midieron. Tres no sirven y se dicen:

| Intento | Cobertura / efecto medido | Resultado |
|---|---|---|
| **La carpeta del material como etiqueta** («BLOQUE 4\07 El modelo TCPIP…») | Solo **10 documentos y 19 fragmentos (el 1 %)** | No sirve: casi todo el material son documentos de **bloque entero** («Resumen de Hellcito», «Bloque 2 y 4», «Bloque 1 Actualizado 2026») que no están en una carpeta de tema |
| **El tema que el propio material declara** dentro del texto («BLOQUE III TEMA 4: ANSI-SQL») | **28 fragmentos de 2.547 (el 1 %)** | Tampoco; y en los 21 emparejables la regla coincidía con lo declarado el **52,4 %** de las veces |
| **El hilo del documento**: un trozo que cae en un tema distinto al de sus vecinos se va con ellos | Se activó **154 veces** en todo el material; cambió **6 de los 2.436** fragmentos que entran en los apuntes (0,25 %) | **Revertido.** Los errores **no vienen sueltos**: vienen en tandas (una sección entera de un documento de bloque colocada en el tema vecino), y el hilo local no ve eso |
| **Cortar cada documento por sus propios rótulos** («TEMA 7. Ley Orgánica 3/2018…») | 57 documentos de 251 traen rótulos; **332 fragmentos** comprobados contra el rótulo que los precede | **No se construye, y por una razón medida**: solo el **34,6 %** están en el tema que anuncia su rótulo… y al mirar tres casos con lupa aparece el motivo: en un documento de bloque los rótulos son **leyes y artículos** que se suceden (una página, tres leyes de tres temas distintos), así que ni el rótulo ni la regla aciertan siempre, y ninguno de los dos puede mandar sobre el otro |

**La conclusión que sí cambia el producto:** con documentos que mezclan temas en la misma página, la unidad
fiable es el **bloque**, no el tema. De ahí los **4 apuntes de bloque** nuevos (ver abajo).

## Qué se ha hecho con esa conclusión

- **Cuatro apuntes de bloque** (`APUNTES\BLOQUE 1 … BLOQUE 4`): todo el material del bloque, con sus temas
  en orden y **cada fragmento numerado con su procedencia**. Suma los mismos 2.304 fragmentos que los 33
  apuntes de tema (nada se duplica ni se pierde) y **no depende de la frontera entre temas vecinos**, que
  es lo que falla.
- **Cada apunte de bloque lo dice en su cabecera**: por qué existe, con los números (bloque 86,7 %, tema
  35-60 %), y para qué sirve cada lectura.
- **`COMO-ESTUDIAR.md`** explica cuál usar: el de bloque para fiabilidad, el de tema para el detalle (con
  sus apartados y su «Compruébate»).

## Qué queda por probar (y cómo se mediría)

1. **Reordenar por el vocabulario del tema, restringido al bloque.** La técnica ya está medida en el banco
   de preguntas: preguntando al vocabulario del tema, con un margen de 0,08, acierta el 90 % frente a las
   preguntas que sí tenían tema por el título. Aquí serviría para **reordenar** los fragmentos dentro del
   bloque. Ojo: usar ese vocabulario para medirse a sí mismo es **circular** — hay que auditarlo a mano.
2. **Medir cada intento con la misma auditoría**: 20 fragmentos al azar, a mano, y el recuento publicado.

Lo que **no** se hace: dar por bueno el 85,8 % del vocabulario. Era circular, y decirlo es parte del
trabajo.
