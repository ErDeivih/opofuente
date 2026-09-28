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

## Qué haría falta para arreglarlo (y cómo se mediría)

1. **Usar la organización del propio propietario como señal.** El material trae carpetas con el tema en el
   nombre («BLOQUE 4\07 El modelo TCP/IP…», «BLOQUE 1\T4_Trebep-Transparencia-Agenda 2030»): eso es una
   etiqueta puesta por una persona y vale más que cualquier parecido de palabras. Un documento que vive en
   una carpeta de un tema se coloca ahí **entero**, y solo sus trozos dudosos se reparten por la regla.
2. **Reordenar por el vocabulario del tema, restringido al bloque.** La técnica ya está medida en el banco
   de preguntas: preguntando al vocabulario del tema, con un margen de 0,08, acierta el 90 % frente a las
   preguntas que sí tenían tema por el título. Aquí serviría para **reordenar** los fragmentos del bloque,
   no para traerlos de otro.
3. **Medir cada intento con la misma auditoría**: 20 fragmentos al azar, a mano, y el recuento publicado.

Lo que **no** se hace: dar por bueno el 85,8 % del vocabulario. Era circular, y decirlo es parte del
trabajo.
