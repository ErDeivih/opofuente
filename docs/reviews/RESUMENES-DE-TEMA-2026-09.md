# Los resúmenes de tema: qué son, cómo se han comprobado y qué les falta (septiembre 2026)

Los apuntes de tema de `F:\OpoFuente\APUNTES` llevan, arriba del todo, un **resumen escrito para leer de
corrido**: un texto en español que explica el tema y **apoya cada afirmación en los fragmentos** que van
debajo (el número entre corchetes que precede a cada fragmento). Este documento deja constancia de qué son,
**cómo se ha comprobado que no inventan nada** y qué queda sin cubrir. Están todos: **33 de 33**.

## Qué hay

| | |
|---|---|
| Resúmenes escritos | **33** (uno por tema) |
| Texto total | **774 KB**, media **23,5 KB** por tema (mínimo 8,2 KB en el 1.4; máximo 52 KB en el 1.6) |
| Citas a fragmento | **1.473**, todas a fragmentos que existen en su apunte |
| Dónde viven | en `F:\OpoFuente\RESUMENES\<tema>.md`, **fuera de los apuntes** |

Vivir fuera es a propósito: `apuntes_limpios.py` rehace los apuntes cada vez que se retoca la limpieza, y un
texto redactado a mano dentro de un fichero regenerado se perdería en la primera regeneración. El apunte los
**incluye al regenerarse**, bajo el epígrafe `## Resumen del tema`, y el índice (`CATALOGO\notas-indice.md`)
marca con **«resumen escrito»** los temas que lo tienen. Los **apuntes de bloque** (la lectura fiable, donde
el material no se pierde por la frontera entre temas) avisan también, al empezar cada tema, **en qué fichero
de tema está su resumen**: quien lee el bloque no tiene por qué saber que existe.

## Cómo se ha comprobado (y no es una opinión)

Cuatro comprobaciones automáticas, ejecutables en cualquier momento desde
`F:\EspacioCodigo\proptech-access-control\docs\opofuente\_oficial\`:

| Script | Qué comprueba | Resultado |
|---|---|---|
| `comprobar_citas.py` | que **cada número de fragmento citado existe** en el apunte de ese tema | 1.473 citas, **0 inexistentes** |
| `comprobar_formato_resumenes.py` | que no hay encabezados `#` ni `##` (romperían el apunte), ni tabuladores, ni resúmenes sin párrafo de procedencia, ni ficheros vacíos | **0 problemas** en 33 ficheros |
| `comprobar_cuentas_resumenes.py` | que la cuenta de preguntas que dice cada resumen es **la del fichero del banco de ese tema** | 33 de 33 coinciden |
| `comprobar_integracion.py` | que los 33 apuntes de tema llevan su resumen y que los 4 de bloque llevan sus 33 avisos | **0 problemas** |

Además, se han leído a mano fragmentos concretos para verificar afirmaciones de los resúmenes nuevos
(3.4, 3.5, 4.6, 2.2, 2.4, 1.2, 1.9, 4.3, 4.4, 4.7): en todos los casos la afirmación estaba en el fragmento
citado, no en un parecido de palabras. Los subagentes que redactaron los suyos declararon haber comprobado
entre 22 y 32 afirmaciones cada uno contra el texto de los fragmentos con `_ver.py`.

**La comprobación de citas es la importante**: un resumen de estudio que se apoya en un fragmento que no
existe, o que existe pero dice otra cosa, es peor que no tener resumen, porque se estudia de memoria. Por eso
cada afirmación lleva su número y no hay ninguna afirmación sin número.

## Los dos fallos que se encontraron y se corrigieron

1. **La misma pregunta contada de dos maneras.** El índice del catálogo decía **1.919 preguntas** para el
   tema 2.4 y el fichero del banco de ese tema decía **1.487**. No era un error de escritura: el índice
   sumaba **todas** las preguntas asignadas al tema, y el banco solo **publica** las que sirven para estudiar
   (`sirve()` deja fuera las que no llegan a 15 caracteres y las de opciones vacías). El alumno veía las dos
   cifras, en sitios distintos, para el mismo tema. Arreglado en `apuntes_limpios.py`: el índice, el apunte y
   los resúmenes usan **la cuenta del fichero que se lee**, la que se puede contar a mano abriéndolo. La
   diferencia total era de **938 preguntas** (de 17.945 asignadas a 17.007 publicadas).
2. **Encargos con el título equivocado.** Al repartir el trabajo entre subagentes les describí de memoria
   algunos temas y me equivoqué en cinco (2.4 por 2.5, 3.6 descrito como SGBD relacional, 4.3 descrito como
   GNU/Linux, 4.4 y 4.7 con títulos que no eran). Se detectó **antes** de que escribieran los ficheros
   afectados, se les corrigió con el título copiado de la primera línea del apunte, y se comprobó el
   contenido final de los cinco. La lección queda escrita: **el título se copia del apunte, no se recuerda**.
3. **Citas mal puestas, que el comprobador no ve.** Que el fragmento exista no quiere decir que diga eso, y
   los resúmenes antiguos tenían varios casos. El del **3.6** atribuía a un fragmento un bloque entero de
   SOAP/REST que **no está en ningún fragmento** del apunte (retirado al reescribirlo). El del **4.1** daba
   «Live Migration» como dato de un fragmento cuando solo consta en el banco (ahora se cita como dato del
   banco) y afirmaba que un capítulo estaba «cortado a mitad» cuando su continuación es otro fragmento. En el
   **3.1** había **trece** defectos de atribución: una sigla colgada de dos fragmentos, una fila de tabla que
   contradecía a su propia sección y varias citas agrupadas donde solo un fragmento sostenía la frase. Los
   tres se corrigieron releyendo el resumen **contra el volcado completo de fragmentos**, afirmación por
   afirmación, y ninguna de esas relecturas encontró contenido inventado: lo que fallaba era **a qué
   fragmento se apuntaba**. Esa relectura completa **solo se ha hecho en esos tres** (3.1, 3.6 y 4.1); en los
   demás hay comprobación automática de citas y lecturas parciales. Hacerla en el resto es el trabajo fino que
   queda.

## Lo que los resúmenes declaran que no está

Un resumen útil dice también lo que el material no trae, en vez de rellenarlo con lo que uno sabe. Estos son
los huecos declarados por los propios resúmenes (están escritos dentro de cada uno):

- **1.4** (empleo público): el apunte solo tiene **14 fragmentos** para todo el tema; el resumen lo dice y se
  apoya en el banco para lo que solo está ahí.
- **2.1** (informática básica): de sus 77 fragmentos, **45 son de temas vecinos** (redes, bases de datos,
  seguridad) y van declarados uno a uno. No hay material de sistemas de numeración, jerarquía de memoria ni
  modos de direccionamiento, que el enunciado sí pide.
- **4.7** (OSI/TCP-IP): **29 de sus 54 fragmentos no son del tema** (51,9 % van al cajón «otros»). No hay
  teoría de las cuatro capas de TCP/IP, ni de TCP, UDP, IP, ICMP, ARP, DNS, DHCP, VoIP ni VPN.
- **3.5, 4.3, 4.4, 1.9, 1.6, 1.8**: apartados concretos sin material (seguridad en Java EE/.NET, gestión de
  usuarios y dispositivos en 4.4, DNI electrónico y portales en 1.9…), cada uno dicho en su resumen.
- **Contradicciones del banco con el material**: el resumen del **3.5** avisa de dos preguntas de exámenes
  oficiales cuya respuesta marcada contradice al material (Jakarta EE como «IDE para Java» y JAX-RS para
  mapear XML a clases). Eso no se ha tocado: el banco publica lo que dice el examen, y el resumen avisa.

## Dónde están los apuntes más finos (medido)

Un fragmento que entra en un tema pero **no encaja en ningún apartado** del enunciado oficial suele ser
material del tema vecino. Medido por apunte, la proporción de fragmentos que caen en «Otros fragmentos del
tema» es:

| En la parte alta | En la parte baja |
|---|---|
| 3.6 (59 %) · 4.7 (52 %) · 1.4 (50 %) · 2.5 (45 %) · 2.2 (41 %) · 1.7 (39 %) · 4.1 (37 %) | 3.9, 1.8, 4.8, 4.10 y 3.4, todos **por debajo del 5 %** |

Donde la proporción es alta, el apunte de tema hay que leerlo **con el de su bloque al lado**; donde es baja,
el de tema se sostiene solo. Está medido por `medir_ruido_por_tema.py`.

## Lo que queda por hacer, sin adornos

- **El techo conocido sigue siendo el mismo**: el tema de cada fragmento se decide por parecido de palabras y
  se midió en torno al **60 %** de acierto al nivel de tema (**86,7 %** al nivel de bloque). Los resúmenes no
  arreglan eso: **resumen fiel de un fragmento mal colocado sigue siendo material del tema vecino**. Por eso
  los apuntes de bloque siguen siendo la lectura fiable y los resúmenes lo dicen.
- **Los resúmenes del 4.8, 1.4, 1.3, 4.10 y 4.9 citan pocos fragmentos** (13, 14, 16, 20 y 23) en relación
  con el tamaño de su apunte (74, 14, 76, 59 y 65). En el 4.8 y el 4.10 es porque su material está repartido
  en muchos documentos y cada fragmento aporta poco; en el 1.3 y el 4.9, porque buena parte del apunte es de
  materias vecinas; en el 1.4, porque el apunte es pequeño (14 fragmentos, y su resumen cita los 14). Se
  pueden engordar leyendo los fragmentos que aún no se citan. Los que más citan son el 2.1 (77 de 77), el 1.6
  (72 de 75), el 1.7 (69 de 69), el 2.5 (65 de 69) y el 3.5 (65 de 67).
- **Los números de pregunta de un resumen y su banco cuadran, pero el «Compruébate» de cada apartado del
  apunte y la cuenta total del banco siguen siendo dos cuentas distintas** (una reparte las preguntas por
  apartado, la otra cuenta el fichero entero). No es un error, pero conviene saberlo al comparar.
- **Los resúmenes los ha escrito un asistente de IA leyendo el material**, no una persona: el trabajo se repartió
  entre varios agentes, cada uno con su tema, y la verificación de las citas es automática (los cuatro
  comprobadores). Lo que **no** está hecho es que una persona los haya leído de principio a fin: un resumen
  puede ser fiel al fragmento y aun así estar mal explicado, y eso solo se detecta leyéndolo. Los que se han
  leído (4.9, 1.3, 4.2, 4.8, 4.10, 1.8, 3.4, 4.6, 3.5, 2.2) se corrigieron a mano. Es la comprobación que
  falta y es trabajo de quien estudia.

## Reglas de la casa, para el siguiente que escriba uno

1. Se escribe en `F:\OpoFuente\RESUMENES\<tema>.md`. No se toca el apunte: se regenera.
2. **Encabezados de nivel 3** (`### `), nunca `#` ni `##`: el fichero se incrusta dentro de un apunte que ya
   los usa.
3. **Cada afirmación lleva su cita** al fragmento del que sale, entre paréntesis.
4. **Nada que no esté en el material.** Si falta, se escribe que falta. Si el banco contradice al material,
   se avisa.
5. Se termina con una sección sobre el banco (cuántas preguntas, dónde está el peso, qué practicar) y el
   párrafo de procedencia literal.
6. Antes de dar por bueno un resumen, se pasan los cuatro comprobadores de arriba.

Para leer el material antes de escribir (los dos que se usaron para estos 33):

- `apunte_mapa.py <tema>` — el apunte por apartados, con el número de cada fragmento y sus primeros 150
  caracteres: es el mapa.
- `apunte_fragmentos.py <tema> <n1> <n2> …` — el texto **entero** de los fragmentos que se le pidan, sin la
  etiqueta de procedencia: es lo que se lee antes de afirmar nada.
