# Para el propietario

Lo que conviene que sepas y **no** hace falta que contestes para que el trabajo siga. Lo que sí
necesita tu criterio está marcado como **«Decide tú»**.

## 13 oct 2026 — Ya puedes hacerte un test a tu medida (la zona del alumno queda cerrada)

**Lo que cambia para ti:** la pantalla **Tests** ya existe. Era la última del menú del alumno que
faltaba, y hasta hoy los tres enlaces que la llamaban —el «Test rápido de 20» de Inicio y el botón
«Test» del Temario y de cada tema— llevaban a una pantalla que decía que todavía no estaba.

Ahora, al entrar en **Tests**, eliges:

1. **de qué temas** (el programa entero, con una casilla por tema; cada tema te dice cuántas preguntas
   tiene y qué has contestado ya en él; los temas con los que todavía no hay preguntas salen apagados y
   lo dicen);
2. **cuántas preguntas** (10, 20, 25, 50 o 100);
3. **cuáles** (todas, las que no has visto, las que has fallado o las que marcaste dudosas);
4. **cómo se corrigen** (al responder o al terminar);
5. **si lleva reloj** (y cuánto duraría).

Y si entras desde un enlace que ya traía algo elegido (`?tema=IV.1` desde el Temario, `?count=20` desde
Inicio), la pantalla **llega con eso marcado**: el enlace no se pierde por el camino.

**Un dato que conviene que sepas, porque sorprende:** si **no** le pones el reloj del test, el test
**no** se queda sin tiempo — hereda el tiempo del examen, **120 minutos**. La pantalla lo dice con esas
palabras en vez de callárselo.

**Lo que la zona del alumno todavía no tiene** (medido en el programa, no de memoria): el enlace «Ver
en apuntes» desde una pregunta del test; «Repetir solo las falladas» en el resultado (el botón que hay
repite el test entero); el buscador dentro de un tema, la marca de lo leído y un modo repaso de los
apuntes; y las pestañas «Preguntas» y «Mi progreso» **dentro** del tema (hoy llevan fuera: a un test de
ese tema y al progreso general). Nada de eso está roto: son huecos que quedan por cerrar.

**Lo que sigue esperando al panel** y que no ha entrado en esta tanda: la pantalla para **leer y
aprobar los apuntes en borrador** desde el panel (era lo que el encargo dejaba «si sobra tiempo», y no
ha sobrado: primero se cerró la pantalla de Tests y se probó). Los borradores, mientras tanto, se
siguen leyendo en la zona del alumno con su marca «Versión generada · en revisión».

**No tienes que decidir nada de esto.** Si algo no cuadra, lo que más ayuda es «Esto está mal» desde el
párrafo, como siempre.

## 13 oct 2026 — Ya hay dónde arreglar una respuesta correcta (y 116 preguntas mal importadas, reparadas)

**Lo que cambia para ti:**

1. **La ficha de la pregunta existe.** Es la pantalla donde se arregla una respuesta correcta, y hasta
   hoy no había ninguna: el banco te dejaba *ver* una pregunta, no *arreglarla*. Se llega desde
   **«Incidencias»** (el botón «Ver la pregunta en el banco») y desde el banco de preguntas, y la
   dirección es `/admin/preguntas?pregunta=<id>`. Enseña seis cosas y **dos historiales**:

   - el enunciado y las opciones, con **cuál está marcada hoy** como correcta;
   - **de dónde sale esa respuesta**: la lista de respuestas del banco, si está en uso o sin aprobar,
     **el documento del que se importó** y en qué estado está esa versión del documento, y **con qué
     garantía se estudia ese banco** (fiable / en duda / no fiable, tal como lo dejó el bloque de las
     claves: se lee, no se recalcula);
   - **qué dicen los apuntes**, con la letra que contestan, la frase que lo demuestra y el enlace al
     apartado exacto;
   - **lo que el motor ha señalado** de esa pregunta, con su categoría;
   - si está **fuera del temario** y por qué;
   - y **qué se puede hacer**: marcar la respuesta correcta o reparar el texto.
2. **Marcar la respuesta correcta no pisa la anterior.** Se guarda una lista nueva y la de antes queda
   como sustituida, legible en el historial con la letra que daba. Cada cambio deja su **evento de
   auditoría** con lo que había y lo que hay, en la misma operación: no hay forma de cambiar una
   respuesta sin que quede escrito quién y cuándo.
3. **Sobre un examen oficial no se puede, y la pantalla lo dice.** Son **10 bancos**: los dos exámenes
   de la **Guardia Civil 2026** (modelos A y B) y los cuatro del **INAP** —TAI ingreso libre 2025 A y
   B, y TAI promoción interna 2025 A y B—, cada uno con la plantilla de la que salió. Ahí no hay botón
   de marcar: hay el motivo y la lista. En un banco protegido solo se puede limpiar el enunciado si se
   demuestra que las letras no cambian.
4. **Se han reparado 116 preguntas mal importadas, una a una y reversibles.** Lo que se arregla es
   texto que la extracción pegó mal: la **referencia del examen** que quedaba enganchada al final del
   enunciado (`… ¿Qué es LDAPS? 2013 Cuerpo de Gestión de Sistemas de la AGE - Gr.B`) y una **opción
   que se había tragado a la siguiente** (la del JCL: `JOB 0d) CALL` → `JOB` y `CALL`). Cada arreglo es
   una **vista nueva** de la pregunta; la de antes se conserva sustituida y con su motivo, así que
   cualquier arreglo se puede leer y deshacer. Y **la pregunta no se mueve de sitio**: sus temas y sus
   enlaces a los apuntes viajan con ella (203 temas y 47 enlaces movidos), de modo que el veredicto de
   un tema no cambia por haberle limpiado una coma al enunciado.
5. **Lo que no se puede reparar con una regla se queda donde está, y se dice por qué.** De las **11**
   preguntas que el sistema marcaba como reparables, **se ha reparado 1**. Las otras diez no se tocan
   porque **no están mal**: cinco son referencias legítimas a otra opción («… conforme a lo indicado en
   la opción c)»), dos son una opción que es el principio de otra y así estaban escritas, una son dos
   opciones que solo se diferencian en mayúsculas **y esa diferencia es justo lo que se pregunta**, una
   se llevó el resto del documento dentro (hay que volver al original) y una es un resto al que le
   falta texto. Y de los **21** enunciados con la referencia pegada, se han limpiado **20**: el que
   queda es un párrafo del BOE de 7.916 caracteres, que no es una referencia sino la pregunta entera.
   **Las 18 preguntas sin opciones siguen fuera del temario**, como estaban: eso no se arregla
   escribiendo, hay que volver al original.
6. **20 incidencias de tu bandeja se han cerrado solas** al reparar sus preguntas, con una nota que
   dice qué se hizo. Tu bandeja pasa de **430 pendientes a 410**.

**Decide tú (cuando quieras, no bloquea nada):**

- Las **diez reparables que no se tocan** están en la bandeja con su motivo, y **cinco de ellas no son
  un problema de importación**, son referencias a otra opción: si quieres, se puede afinar la regla
  para que deje de señalarlas. Mientras tanto, mirarlas es trabajo perdido.
- Dos de ellas (una de «Supuestos Prácticos» con un `ls -la` y otra sobre el artículo 148 de la
  Constitución) **no son un problema de texto sino de respuesta correcta**: lo que hay que hacer es
  abrir su ficha y marcar la buena.

## 13 oct 2026 — La bandeja del motor ya tiene pantalla, y sus 453 incidencias estaban mal etiquetadas

**Lo que cambia para ti:**

1. **Por fin hay dónde mirar las incidencias del motor.** Están en el panel, en **«Incidencias»**
   (`/admin/incidencias`), al lado de «Avisos». No es una lista de errores de nadie: es **lo que el
   sistema no ha podido resolver solo** al comprobar un tema contra las preguntas de su banco. Cada
   una lleva su categoría, el motivo concreto, la **pregunta que la provoca**, la frase de los apuntes
   que la demuestra cuando existe, y tres enlaces: al **apartado exacto de los apuntes**, a la
   **pregunta en el banco** y al **material del que salió la clave**. Y se puede **decidir** qué se
   hace con ella dejándolo escrito (pendiente / en curso / resuelta / descartada + una nota), con cada
   cambio auditado. El contador de pendientes sale en el menú, como el de los avisos del alumno.
2. **Las 453 estaban mal clasificadas y se han vuelto a clasificar.** De las **291** que decían
   «norma cambiada», **23 no eran ni incidencias** (la letra de los apuntes está en la clave: no hay
   nada que decidir) y **146** eran de conjuntos con la clave en cuarentena. El motor ponía esa
   etiqueta a toda pregunta con un dato dudoso **antes** de mirar la clave; el porqué está escrito con
   su línea de código en el estado del objetivo. **No se ha tocado el motor**: se ha corregido por
   encima, y las cifras nuevas son éstas, contadas en la base:

   | Categoría | Antes | Ahora |
   |---|---|---|
   | Pregunta mal importada (opciones fundidas, cortadas o de menos) | — | **29** |
   | Clave no fiable (conjunto en cuarentena, §1) | — | **158** |
   | Clave sospechosa (contradice los apuntes) | 110 | **200** |
   | Norma cambiada | 291 | **0** |
   | Hueco sin material | 40 | **34** |
   | Pregunta ambigua | 12 | **9** |
   | *(fuera: no eran incidencias)* | — | **23** |
   | **En la bandeja** | **453** | **430** |

3. **«Norma cambiada» se queda a cero, y es a propósito.** Esa categoría solo vale si hay **cita de la
   norma vigente con su versión o fecha**, y esa cita no está en los datos: la escribe una pasada del
   modelo que esta tanda no ha ejecutado (no se le ha dado presupuesto). Sin ella, una clave que
   contradice los apuntes se llama «clave sospechosa», que es lo que sí se puede afirmar. Cuando esa
   pasada exista, las que tengan la cita subirán solas.
4. **18 preguntas han salido de los tests** (de 769 a 787 marcas de «enunciado roto»): son las que **no
   se pueden contestar** porque les faltan opciones (fragmentos de leyes partidos, «...» como opción,
   dos opciones fundidas en una). Es lo que manda el §2 del documento de ajustes: lo que no se puede
   reparar con una regla no entra en tests, simulacros ni repasos. **Se pueden recuperar**: asignarles
   un tema levanta la marca.
5. **Y quedan dos cosas por hacer con las preguntas rotas, dichas para que no se pierdan**: **9** se
   pueden reparar partiendo la opción fundida y **21** llevan la referencia del examen pegada al
   enunciado («2011 Universidad…»), que hay que limpiar. Las dos cosas son escribir una **versión
   nueva** de la pregunta, y eso va con la pantalla de la ficha de pregunta (§5.4 del documento), no
   con esta tanda.
   *Las seis categorías, con lo que hay dentro de cada una*: **pregunta mal importada 29** (18 sin
   opciones suficientes —las que han salido de los tests—, 8 con una opción fundida, 2 con una cortada
   y 1 con dos repetidas); **clave no fiable 158**, todas de conjuntos con la clave en cuarentena (10
   de los 60 conjuntos que se pueden juzgar pasan del 30 % de discrepancias); **clave sospechosa 200**
   (85 con la frase de los apuntes que lo demuestra y 115 sin ella, y esas lo dicen en pantalla);
   **norma cambiada 0**; **hueco sin material 34**; **pregunta ambigua 9**.
   Y una cosa que conviene que sepas porque afecta a lo que ya estudias: **de los grupos que se van
   con las 18 preguntas, ninguno estaba cubierto por los apuntes**, así que la cobertura de I.6, I.4 e
   I.8 **no empeora**; I.6 pierde 5 grupos del denominador (le favorece uno o dos puntos) y los tres
   siguen como estaban.
6. **Todo esto se ha probado sobre una copia** de tu base (`F:\temp-opofuente\f18-datos`), nunca sobre
   la tuya: **tu base está en la revisión `0034`** y no se ha tocado. Para que estos cambios lleguen a
   tus datos hay que aplicar la migración `0035` (`scripts\migrate.ps1`) y ejecutar el comando de la
   reclasificación —primero en ensayo, que no escribe nada, y luego con `--aplicar`, que hace **copia
   verificada** antes de tocar la bandeja—: `uv run python -m opofuente.tools.reclasificar_incidencias`
   y `… --aplicar --excluir-no-reparables`.
7. **Las 18 puertas no se han corrido todavía**, y no por descuido: el §1 del documento de ajustes
   (las claves fiables y su cuarentena) está en marcha en otro bloque y las dos baterías no pueden usar
   a la vez el mismo puerto ni el mismo directorio de pruebas. Lo que sí está en verde son las pruebas
   locales: 41 de backend nuevas, las 344 de componentes y las 3 de extremo a extremo de esta pantalla.
8. **Una cosa que no he podido hacer y lo digo**: **no he mirado las capturas con mis ojos** (el modelo
   de esta sesión no lee imágenes). Lo que declaro de ellas es lo que el guion mide: 1280 y **390 px
   exactos**, **0 violaciones de accesibilidad**, **0 errores de consola**. Las tienes en
   `artifacts/screens/admin-incidencias-categoria-hueco_sin_material-{escritorio,movil}.png`.

**Decide tú** (nada urgente, nada bloquea):

- **Si las 21 con la referencia pegada** se limpian solas (quitando el texto del examen) o prefieres
  revisarlas una a una. Por ahora no se toca ninguna.
- **Si las 9 reparables** se parten automáticamente o las miras tú. Su caso está guardado con la regla
  que lo detectó.

## 12 oct 2026 — IV.2 y II.4 ya se leen, y hay dos temas nuevos que contestan de cada cinco preguntas

**Lo que cambia para ti:**

1. **IV.2** (Administración de bases de datos, almacenamiento, backup y virtualización) **ya está en la
   zona del alumno**, con la marca «Versión generada · en revisión». Es el **tercer tema por valor** de
   los que quedaban (797 preguntas con clave) y el que **mejor contesta** de todos los escritos hasta
   hoy: **757 de 758 preguntas** con clave utilizable, el **99,9 %** (el listón es el 90 %). Sobre
   todas las que tienen clave, 757 de 797 = 95,0 %. Son 16 apartados y 32.567 palabras.
2. **II.4** (sistemas operativos, Windows, Unix y Linux y móviles) **también se lee** desde hoy. Es el
   **quinto por valor** (566 preguntas con clave) y contesta al **95,9 %** de lo que se le puede
   preguntar (443 de 462). Sobre todas las que tienen clave, 443 de 568 = 78,0 %: en este tema el
   banco tiene 282 preguntas con una **clave que contradice el material**, y eso no lo arregla el
   texto. Son 17 apartados y 26.367 palabras.
3. **Lo que cuesta leerlos**: en **los dos** temas, «sin contestar por los apuntes: **0**». En IV.2,
   734 de sus 770 grupos quedan cubiertos con su letra y su cita; en II.4, 419 de 501. Los que quedan
   «a revisión» lo están porque **su clave** no se puede usar, no porque falte el dato. Es lo
   contrario de I.6, y es lo bueno que tienen estos dos.
4. **En tu bandeja del motor hay 36 incidencias nuevas de IV.2 y 82 de II.4** (IV.2: 35 claves que
   contradicen la norma y 1 que sostiene otra letra; II.4: 71 y 11). Necesitan tu criterio, y **esa
   bandeja todavía no tiene pantalla** (es la mitad que le falta al bloque C). Mientras tanto están
   guardadas y se pueden contar.
5. **Los dos temas costaron 0,7585 $ y 0,7014 $** (las previsiones eran 0,88–1,49 $ y 0,63–1,07 $): los
   dos por dentro de su tope. **I.8 quedó en borrador** (ver el punto 6) y costó 1,2119 $.
6. **I.8 (acceso electrónico, ENS, ENI y NTI) NO se publica: queda en borrador con dos motivos
   escritos, y lo puedes leer igual** (el borrador se ve en el panel, como I.4 e I.6):
   - contesta al **82,0 %** de las 516 preguntas con clave utilizable y el listón es el 90 %;
   - y su corrida **no terminó**: **el tope de tiempo que le puse la paró** con 389 de sus 442 grupos
     comprobados, así que ese 82,0 % es un **suelo**, no su techo. Lo escrito está guardado y el tema
     **se puede reanudar sin volver a pagar por lo que ya está**.
   La corrida costó 1,2119 $ de un tope de 1,32 $, así que **no quedaba margen para reanudarla sin
   salirse del tope**: por eso se para aquí y se anota, en vez de seguir gastando.
7. **Llevas ≈10,58 $ de los 40 $** (tanda f17: 2,6718 $ por los tres temas). Es el **primer aviso de
   los 10 $**, y queda anotado en el estado del objetivo como manda la decisión D3. Quedan ≈29,4 $, y
   el precio medido de un tema está entre 0,70 $ (técnico) y 1,21 $ (normativo denso).
8. **Y una cosa que se ahorró, dicha porque es la primera vez que pasa**: la corrida de II.4 terminó
   con la forma en NO PASA (una tabla con una celda de más y cuatro apartados con el mismo principio
   de título) y se arregló **sin volver a pagar**, con dos reparaciones de forma que ahora sabe hacer
   el motor. La alternativa era una corrida más de entre 0,34 $ y 0,80 $. La tabla era la de los
   operadores del shell: el operador «tubería» es él mismo una tubería y rompía la tabla.

**Lo que sigue** (el orden lo decide tu tabla de valor, no el del temario): el séptimo es **I.7**
(550 preguntas con clave), que **todavía no tiene índice**: lo primero es escribirlo y ensayarlo sin
gastar, como se ha hecho con II.4 e I.8. Y **I.8 se puede reanudar** cuando quieras priorizarlo, con
lo que ya está escrito.

**Decide tú:** nada nuevo. Lo que ya esperaba tu decisión sigue esperándola (las dos bandejas del
motor, el listón de párrafos repetidos del §5.9 del estado y el criterio sobre las claves de I.6,
I.4, IV.2, II.4 e I.8).

## 11 oct 2026 — ya puedes ver lo que marcas en los apuntes (y una cosa que tienes que hacer tú)

**Lo que cambia para ti:**

1. **El botón «Esto está mal» ya tiene bandeja.** Hasta ahora el aviso se guardaba y **no había dónde
   verlo**: estudiabas, marcabas lo que estaba mal y no podías mirarlo. Ahora está en el panel,
   **Avisos** (`/admin/avisos`): cada aviso con su tema, su apartado, **el motivo que escribiste**, la
   fecha y su estado. Se puede ir al **apartado exacto** de los apuntes con un clic, filtrar por
   estado y por tema, buscar por lo que dice, y **despacharlo**: en curso, resuelto o descartado, con
   la nota de lo que has hecho (por ejemplo «arreglado en la versión del 12-oct»). Cada cambio queda
   auditado, como cuando lo escribes tú.
   En el menú del panel, **Avisos** lleva un contador con los que **nadie ha mirado todavía**.
2. **«No son preguntas»** (`/admin/no-son-preguntas`): los enunciados que no se pueden contestar y las
   preguntas de otra administración, con el motivo por el que están fuera y un buscador. En tu base
   hay **769 enunciados rotos** y **325 de otra administración** (medidos, no heredados). No entran en
   tests, simulacros ni comprobaciones —eso ya era así— y **siguen en la base**: esta pantalla solo
   los enseña, **no borra ni edita nada**.
3. **Una cosa que tienes que hacer tú** (no la he hecho yo a propósito, porque las copias son otra
   tarea y tu base es tuya): **tu base está en la revisión `0032` y le faltan las migraciones `0033`
   y `0034`**. O sea: la tabla de los avisos **no existe todavía en tus datos**, y el botón «Esto está
   mal» de tus apuntes **falla hoy** al guardar. Se arregla con `scripts\migrate.ps1` (crea la tabla y
   el estado «en curso»; no toca ni una pregunta, ni un apunte, ni una clasificación, y se puede
   deshacer). Cuando lo pases, la bandeja arranca **vacía** —no hay ningún aviso tuyo guardado— y se
   irá llenando con lo que marques.
4. **Y una cifra que hay que no confundir**: los **333 avisos** de tu bandeja del motor (claves
   sospechosas, huecos sin material, normas cambiadas) son **otra cosa** y **todavía no tienen
   pantalla**: su bandeja no tiene ni ruta. Es la mitad que falta del bloque del panel y va en su
   propia tanda, junto con la ficha de pregunta y el temario.

**Lo que verás cuando entres:** dos entradas nuevas en el menú del panel, **Avisos** y **No son
preguntas**, entre «Clasificación» y «Cambios». Las capturas de las dos, en escritorio y móvil, están
en `artifacts/screens/` (`admin-avisos-*` y `admin-no-son-preguntas-*`), sin violaciones de
accesibilidad. Las puertas de calidad dan **18/18**.

**Y el enlace al apartado, que no funcionaba y ya funciona:** el enlace decía la dirección del
apartado (`/temario/IV.7#apartado-…`) pero el navegador **no bajaba** hasta él, porque los apuntes
llegan un momento después de abrir la página. Se midió (el apartado estaba a 5.894 px y la página
seguía arriba del todo) y se arregló: ahora se baja al apartado al llegar desde el panel, y también
desde el índice del tema. Es lo único que se ha tocado del marco del alumno, y no se ha tocado
ninguna de sus pantallas ni sus tokens.

**Y una cosa honesta sobre el detector de palabras prohibidas:** en las capturas del panel sale
«Celador». **No lo pone ninguna de las dos pantallas nuevas**: lo pone el selector de oposición del
marco del panel, que enseña tus oposiciones. La regla («esta zona es solo de TAI») está escrita para
la zona del alumno, y así la aplica la puerta del rediseño. Si alguna vez quieres que el panel no
enseñe el nombre de las otras oposiciones hasta que lo pidas, dímelo: es un cambio del marco, no de
estas pantallas.

## 11 oct 2026 — I.2 ya se lee; I.4 se queda en borrador con su motivo, y dos cosas del motor

**Lo que cambia para ti:**

1. **I.2 (las Cortes, el Tribunal Constitucional y el Defensor del Pueblo) está publicado y se lee.**
   Contesta al **95,2 %** de las 703 preguntas que tienen una clave con la que se puede acertar (sobre
   todas las que tienen clave, el 80,1 %), y pasa las dos puertas. Son 16 apartados y 1.233 hechos. Su
   bandeja te deja **99 incidencias**: 73 de norma cambiada, 19 de clave sospechosa, 6 de hueco sin
   material y 1 de pregunta ambigua.
2. **I.4 (el EBEP, la Ley 19/2013 de transparencia y la Agenda 2030) se queda en borrador, y no por
   falta de texto**: contesta al **88,9 %** y el listón es el 90 % —le faltan 7 preguntas—. Su forma
   **sí pasa** y sus 15 apartados están escritos, así que lo tienes en el panel con el motivo escrito.
   De sus 546 grupos, 62 están sin cubrir y **31 de ellos tienen en los apuntes la frase que sostiene
   otra opción distinta de la clave**: igual que en I.6, buena parte del hueco es tu criterio sobre
   las claves (47 de sus 55 incidencias son de la clave, no del texto). **No he bajado el listón para
   que pasara.**
3. **Tu bandeja** va por **333 incidencias** —medidas en la base, no sumadas de informes—: I.2 99, I.6 63, I.1 61, I.4 55 y IV.7 55. Las categorías están en el §3 de cada `docs/apuntes/INFORME-<tema>.md`.
4. **Dos cosas del motor que interesaban**, las dos con prueba que falla antes:
   - **`--prever` ahora dice lo que cuesta**, no solo lo que rehace: llamadas de hechos, de redacción
     y de comprobación, la cota de arriba del bucle de huecos y los euros. En I.2 acertó la cota de
     arriba (dijo 195, hizo 194); en I.4 se quedó corto en dinero (dijo 1,03 $, costó 1,46 $) porque
     ese tema devuelve el doble de texto por llamada. Ya está corregida la tabla, con las cinco
     corridas medidas dentro.
   - **Un tope de tiempo para la corrida entera** (`--tiempo-maximo`): sin él, una corrida larga solo
     se puede parar matando el proceso. Ahora para de llamar sola, lo escrito se conserva y volver a
     lanzarla sigue desde ahí. (El tope **por llamada**, 300 s, ya estaba.)
5. **Y una cosa que conté mal y corrijo aquí**: a mitad de la tanda de I.4 parecía que la corrida
   estaba colgada. Se miró y **no lo estaba** —el proceso que se miraba era el lanzador, que siempre
   marca 0 s de CPU—: seguía escribiendo y con la conexión a la API abierta. Lo dejo escrito para que
   nadie más saque esa conclusión de ese dato.

### I.2 y la tanda, con detalle

**Lo que cambia para ti:** hay un tema más en la zona del alumno. **I.2** contesta al **95,2 %** de
las 703 preguntas que tienen una clave con la que se puede acertar (sobre todas las que tienen clave,
el 80,1 %), y pasa las dos puertas, así que se ha publicado con la marca «Versión generada · en
revisión». Son 16 apartados y 1.233 hechos.

1. **Y una decisión tuya que se ve en el texto**: este tema se llevó preguntas de **otras partes de
   la Constitución** (la Corona, el Gobierno, los derechos, la organización territorial, el Poder
   Judicial y la Ley de transparencia) —son del orden de una de cada tres de sus 546 grupos—. Como
   esas preguntas **caen en este bloque** y tú estudias por temas, tienen su apartado propio en el
   índice en vez de un cajón de «otros». Si prefieres que no estén, dímelo y se quitan.
2. **Tu bandeja tiene 99 incidencias nuevas de I.2**: 73 de **norma cambiada** (la clave contradice
   la norma o el material: ahí el que hay que revisar es la clave), 19 de **clave sospechosa** (los
   apuntes dicen otra letra y llevan la frase que lo demuestra), 6 de **hueco sin material** y 1 de
   **pregunta ambigua** (sin clave con la que comprobar). Con eso, la bandeja va por 215 incidencias
   (el total medido de la tanda entera, con I.4 dentro, está en el punto 3 de la sección de arriba).
3. **Lo que costó, y lo que se dijo antes de pagarlo**: la corrida hizo **194 llamadas y 1,2187 $**.
   La previsión que el motor da **antes** de gastar un céntimo decía 115–195 llamadas y 0,72–1,23 $,
   así que acertó la cota de arriba. Lo caro no fue escribir: fueron los 73 conflictos de clave, que
   obligan a volver a comprobar y a añadir. **Y se pasó 0,0187 $ del tope por tema (1,20 $)**; a
   partir de ahora solo se escribe entero el tema cuya previsión **máxima** quepa en el tope. Por eso
   **IV.2**, que es el siguiente por valor (797 preguntas con clave), se queda para la próxima tanda:
   su previsión máxima es 1,38 $. Su índice ya está escrito y probado, así que la próxima tanda
   empieza redactándolo.
4. **Y una cosa del motor que interesaba**: los temas de apuntes ya no se eligen por el orden del
   temario sino **por cuántas preguntas con clave tiene cada uno**, medido sobre tu base. La tabla de
   los 33 está en `ESTADO-DEL-OBJETIVO.md`; los tres primeros que quedan son IV.2 (797), I.4 (577) e
   II.4 (566).

## 11 oct 2026 — El ciclo de estudio se cierra: resultado, simulacro, exámenes, fallos y progreso

**Lo que cambia para ti:** ya puedes hacer un test y **ver qué has fallado y de qué tema era**, montar
un simulacro con el perfil de verdad, ver los exámenes oficiales que haya importados, repasar tus
fallos —y montar un test solo con ellos— y mirar tu progreso por bloque y por tema. Las cinco
pantallas están en la zona del alumno, con capturas en escritorio y móvil.

1. **Resultado** (al terminar un test): la nota, el desglose **por parte** —en un simulacro, la
   primera parte y el supuesto, cada una con su banda—, el **tiempo** empleado, el desglose **por
   tema** con el porcentaje escrito, y las preguntas una a una con **tu respuesta, la correcta y su
   tema**. Desde ahí, «Repetir este test» (vuelve a montarlo con los mismos temas) o «Repasar IV.7»
   para ir a los apuntes de ese tema. Las preguntas que la plantilla no corrige (anuladas o en
   conflicto) salen como «No se corrige» y **no** cuentan como fallo tuyo.
2. **La nota es una estimación**, y lo dice con el texto largo del motor, no con una frase mía:
   «Es una **estimación**: la puntuación directa (aciertos menos errores por su penalización) escalada
   a la banda que publica la convocatoria para esta parte. La calificación oficial 0-50 resulta de los
   baremos que fija la Comisión de Selección, y esa tabla no está importada: esto no es la calificación
   oficial.» Cuando importes el baremo oficial, ese aviso cambiará solo.
3. **Simulacro real**: eliges variante (completa o corta) y, si es completa, el **bloque del supuesto
   (III o IV)**. Antes de empezar se ve **qué va a caer**: 80 preguntas más 5 de reserva y un supuesto
   de 20 más 5, los 120 minutos y la penalización de un tercio —todo leído de la convocatoria, nada
   escrito a mano—, más los temas de cada bloque del supuesto con las preguntas que tienen hoy.
4. **Exámenes oficiales**: la pantalla está montada y **lee de la aplicación**, pero **todavía no hay
   ninguno importado** (es el bloque del INAP: los 32 PDF están descargados en
   `F:\OpoFuente\fuentes\inap-tai\`). Mientras no los haya, dice con esas palabras «Todavía no hay
   exámenes oficiales importados» y explica de dónde saldrán, en vez de rellenar la lista con bancos
   de práctica. Cuando estén importados saldrán con su fecha, su número de preguntas y un botón para
   hacerlos, y el que esté a medias dirá por qué no se puede hacer todavía.
5. **Fallos**: tus preguntas falladas —las que fallaste **la última vez** que las contestaste—, con su
   tema, la fecha, **cuántas veces** las has fallado y si ya toca repasarlas. De aquí sale un test:
   «Test con mis fallos» (con todos) o «Solo los de IV.7» (por tema), y el motor vuelve a elegir sobre
   tus intentos de verdad, no sobre la lista.
6. **Progreso**: por bloque y por tema, con el **porcentaje escrito**, los aciertos, **cuántos tests
   has hecho** (el número de verdad, no los que caben en la lista), lo que hay que repasar y **lo que
   no has empezado** —un tema sin tocar dice «Sin empezar», no un 0 % que parecería un suspenso—, y la
   evolución: cada test terminado, con su nota y su enlace al resultado.

**Lo que queda fuera, y por qué:** la pantalla de **Tests** (elegir temas y cuántas preguntas) sigue
pendiente y su entrada dice qué hará; dentro del tema, las pestañas «Preguntas» y «Mi progreso», el
buscador y la marca de leído tampoco entran aquí. **No se ha tocado nada del panel** de administración,
ni los apuntes de los 30 temas, ni la importación del INAP, ni la entrega antigua.

**Lo que no gasta nada:** este bloque **no ha llamado a ningún modelo**. Es interfaz y consultas a tu
base.

## 11 oct 2026 — Inicio, Temario y los apuntes ya se leen; y el botón «Esto está mal» funciona

**Lo que cambia para ti:**

1. **La zona del alumno tiene ya el diseño aplicado** (el de `DISENO-V0-Y-STITCH`, que aprobaste en
   D12): papel blanco frío, un solo azul para la acción, Atkinson Hyperlegible Next para la interfaz
   y Source Serif 4 para leer los apuntes —las dos fuentes van dentro de la aplicación, no se
   descargan de internet—. Todo el color, el tipo y la forma viven en **un fichero**
   (`apps/web/src/styles/tokens.css`), y hay una prueba que impide que otra hoja vuelva a escribir un
   color a mano. Si un día quieres cambiar el azul, se cambia ahí y cambia en toda la aplicación.
2. **Inicio** enseña lo que toca hacer (el test a medias, los fallos que tocan repasar), cómo vas por
   bloque —con el porcentaje escrito, no solo la barra— y qué apuntes puedes leer, con su estado.
3. **Temario** es el índice del programa, con los temas en orden numérico (IV.7 antes de IV.10), su
   número de preguntas, su barra de acierto y **un buscador** por título o por código.
4. **Tema con apuntes**: el texto en tres columnas —índice de apartados a la izquierda, lectura en el
   centro, notas al margen a la derecha—, con las tablas bien formadas y el índice navegable.
5. **Los temas en borrador se ven y se leen**, con la marca «Borrador». No se esconden: leerlos es
   justo lo que hace falta para que me digas qué está mal. Los publicados llevan la marca «Versión
   generada · en revisión».
6. **El botón «Esto está mal»** está en cada apartado de los apuntes. Pide el motivo en una línea y lo
   guarda de verdad (con su ancla y su evento de auditoría, no en un registro de pantalla). **Hoy lo
   puedes ver abriendo `http://127.0.0.1:8765/api/v1/notes-reports` con la aplicación arrancada**: ahí
   sale cada aviso con su tema, su apartado y tu texto. La bandeja con pantalla —con filtros y con el
   botón de despacharlo— es el bloque siguiente (el panel de administración), y cuando llegue saldrá
   en ella.

**Lo que todavía no está** (y no lo he fingido): las pantallas de **Resultado, Simulacro, Exámenes
oficiales, Fallos y Progreso** son el bloque siguiente. Las pestañas del tema «Preguntas» y «Mi
progreso» llevan a su dirección, que hoy dice que llegará; el buscador dentro del tema y la marca de
«leído» en el índice tampoco están todavía.

**Nada de esto ha gastado API**: este bloque es de interfaz y de la ruta de escritura de los avisos.

## 10 oct 2026 — I.1 ya se puede leer, I.6 contesta a tres de cada cuatro, y el motor ya no paga de más

**Lo que cambia para ti:**

1. **I.1 está publicado** (La Constitución Española de 1978, con sus derechos, su garantía y
   suspensión y La Corona). Está en la zona del alumno con la marca «Versión generada · en revisión».
   Contesta al **98,5 %** de lo que el banco pregunta (1.965 de 1.995 con clave utilizable), y su
   índice cuadra por fin: 21 apartados, 1.724 hechos redactados y **ninguna pregunta sin sitio**.
   Antes no se podía ni empezar: 295 de sus 2.006 preguntas no casaban con ninguna materia.

2. **I.6 sigue en borrador, y ahora con el número que lo explica.** Contesta al **72,5 %** (antes
   64,3 %), pero **no puede llegar al 90 %**: de sus 258 preguntas con clave utilizable, **41** tienen
   en los apuntes una frase que sostiene **otra opción** que la clave, y 30 no tienen frase. Si se
   rellenaran todos los huecos de material el techo sería el **84,1 %** — medido, no estimado. Lo que
   falta no es texto: son claves. **Decide tú:** esas 41 están en tu bandeja con la frase que las
   sostiene, para que digas cuál de las dos está mal (la clave o los apuntes).

3. **Lo que ya está bien en I.6** (y costó dos intentos): su texto pasó de 18.666 palabras a
   **13.174** donde el tope son 13.840, sus párrafos repetidos del 12,9 % al **0,6 %**, y **la puerta
   de forma pasa por primera vez**. El motivo del exceso era el motor: al rellenar los huecos, los
   añadidos escribían sin contar con el tope del apartado.

4. **Su bandeja ya no enseña frases que no existen.** Al reescribir los apuntes, cada comprobación
   caduca y se vuelve a comprobar: **41 de 41** anclas de conflicto y **20 de 20** frases de la
   bandeja están **de verdad** en los apuntes de hoy. Es lo que arregló la tanda anterior y ahora se
   ha comprobado después de reescribir el tema entero.

**Dos cosas que deberías saber sobre el gasto y el trabajo:**

- **El motor ya no paga dos veces sin enterarse.** `apuntes --prever` dice, **sin llamar a nadie**,
  qué apartados se conservan, cuáles se vuelven a redactar y cuáles se tiran; y `apuntes --publicar`
  publica midiendo lo guardado, sin volver a pagar una corrida. Dentro de una corrida el plan se
  calcula **una vez** y no cambia mientras se escribe.
- **Las 90 secciones que se rehicieron en I.1 no eran trabajo repetido**: eran las del índice
  **anterior**, escritas el 9 de octubre antes de que existiera el catálogo (el tema se redactó una
  vez, con el índice nuevo: 21 apartados). La línea del informe que dice «90 apartados que ya no están
  en el plan» se refiere a eso, y ahora se ve **antes** de lanzar la corrida.

**Gasto:** medido en esta tanda **3,0816 $** (I.1 1,9593 + I.6 1,1223), más **≈0,40 $** de una corrida
que se mató a propósito al ver que iba por mal camino. El acumulado del objetivo es **≈5,23 $**: **no**
se ha cruzado el aviso de los 10 $.

## 11 oct 2026 — Tu 28,125 ya está en la aplicación, y la bandeja de I.6 ya enseña pruebas de verdad

**Los tres asuntos de esta tanda, y lo que cambia para ti:**

1. **El 28,125.** Ya está calculado por la aplicación, exacto (`225/8`), con la cuenta que hiciste:
   los 45 de la puntuación directa escalados a la banda de la parte (`50 · 45/80`). Se llama
   **«estimada»** y se dice así en la pantalla, porque **no es la calificación oficial**: esa sale de
   los baremos de la Comisión, que no están importados. La otra fórmula (la de Guardia Civil, que
   resta un tercio por alternativa) **no se ha usado** porque el anexo V de TAI no publica cuántas
   alternativas tiene cada pregunta y no me parece honesto inventármelas. Donde la aplicación no puede
   afirmar un aprobado, no lo afirma: pone la estimación y si llega o no al mínimo publicado.

2. **La bandeja de I.6 volvía a estar mal, y ya no lo está.** Las 45 frases que te enseñaba como
   «prueba» del conflicto **no estaban en los apuntes**: 43 de 45 no aparecían por ningún lado del
   texto que ibas a leer. La causa era del motor (reutilizaba la comprobación de un texto anterior
   aunque el apartado se hubiera reescrito) y está arreglada. Medido después: **38 de 38** frases de la
   bandeja y **70 de 70** anclas de conflicto están **de verdad** en los apuntes de hoy.

3. **Puedes ver un test con su hoja de respuestas.** Hay una pantalla nueva: enunciado y opciones a la
   izquierda, la hoja de respuestas a la derecha (la rejilla numerada con casillas A B C D, que se
   rellenan en azul, la dudosa en ámbar y, al corregir, la correcta en verde y la fallada en rojo), sin
   la navegación (modo examen). Se contesta con el teclado (`A`–`D`, `1`–`4`, `M` para dudosa). Las dos
   capturas, a 1280 y a 390, están en `artifacts/screens/test-en-curso-escritorio.png` y
   `artifacts/screens/test-en-curso-movil.png`.

**Dos cosas que deberías saber aunque no haya que decidir nada:**

- **I.6 cambió de texto mientras esta tanda trabajaba.** Otra tanda escribe en la misma base (lo dice
  el estado del objetivo): sus apartados pasaron de 79.495 a 111.000 caracteres. La cobertura que se
  mide hoy es 64,3 % (la de antes era 65,9 %, y describía un texto que ya no existe) y ahora tampoco
  pasa la revisión de forma (18.666 palabras donde el tope son 13.840, y un 12,9 % de párrafos
  repetidos). Sigue en borrador, con sus 81 incidencias en la bandeja. **Decide tú:** si quieres que
  lo vuelva a redactar entero con el tope de extensión del plan (cuesta unos 0,60 $) o que se quede
  como está hasta que decidas sobre las claves.

- **Gasto:** lo medido desde que hay cuenta son ≈1,75 $ (1,31 $ de la tanda anterior y 0,44 $ de
  esta). **No** se ha cruzado el aviso de los 10 $, y el total del objetivo no se puede dar: lo
  anterior al 10 de octubre no está registrado en ninguna parte.

## 10 oct 2026 — La puerta del 90 % de IV.7: con qué número se midió

**IV.7 se publicó midiendo sobre las claves utilizables: 430 de 449 = 95,8 %.** Contando **todas** las
claves (activas o en borrador) es 430 de 511 = **84,1 %**, y con ese número quedaría en borrador.

Por qué se eligió el primer denominador: hay 62 preguntas cuya **respuesta marcada contradice la
norma** —el propio motor las señala al escribir los hechos— y una pregunta así no tiene una respuesta
con la que se pueda acertar. Contarlas en contra de los apuntes sería culpar al texto de un fallo del
banco; esas 62 están en tu bandeja, con su categoría y su motivo, esperando tu criterio.

**Decide tú:** si prefieres el criterio estricto (todas las claves), dímelo y **los dos temas vuelven a
borrador** (IV.7 y I.6), porque con ese denominador ninguno de los dos llega. La decisión y su vuelta
atrás están escritas en `docs/DECISIONES-TOMADAS-EN-EL-OBJETIVO.md`.

## Lo demás, en una línea cada cosa

- **IV.7**: publicado. El apartado de UDP ya no habla de IPv6, de ARP ni de ICMP (16 hechos con
  material ajeno → 8, todos de UDP); la tabla de puertos va en cuatro tablas por familia, sin los
  avisos «No es DynamoDB» (24 retirados) y con las confusiones de verdad en «Confusiones que caen».
- **I.6**: en borrador, y **con el motivo escrito**: contesta al **72,5 %** de lo que se le pregunta y
  su techo medido es el 84,1 %. De sus 63 incidencias, 40 son de la clave (20 `norma_cambiada` y 20
  `clave_sospechosa`), no de los apuntes. No se arregla escribiendo más. Su forma ya pasa: 13.174
  palabras de 13.840 y 0,6 % de párrafos repetidos.
- **I.1**: **publicado**. Su índice cuadra (21 apartados, 1.724 hechos, 0 sin materia) y contesta al
  98,5 % de sus 1.995 preguntas con clave utilizable. Sus 61 incidencias están en tu bandeja.
- **Tu bandeja** ya tiene lo que no se pudo resolver solo: 55 incidencias en IV.7 y 81 en I.6, cada una
  con su categoría (clave sospechosa, norma cambiada, hueco sin material, pregunta ambigua), su motivo
  y, cuando la hay, **la frase de los apuntes que lo demuestra**.


---

## Las claves que no son de fiar (13-oct-2026) — lo que se ha hecho y lo que te toca a ti

**El problema, medido.** De los conjuntos con los que ya estudias, **10 tienen la clave mal** y no es opinión: se ha comparado, pregunta a pregunta y **una vez por pregunta**, la letra que dan tus apuntes con la letra de la clave. En un conjunto de 18 preguntas, 16 no cuadran: eso no es que los apuntes se equivoquen, es que la clave salió mal del material.

| conjunto | no cuadran | de | % |
|---|---|---|---|
| C_ejer_1_libre_DZA_2026 | 16 | 18 | 89 % |
| Test por temas | 26 | 32 | 81 % |
| TEST VARIOS | 49 | 64 | 77 % |
| Test Aragón 2015 | 23 | 31 | 74 % |
| 1600-Preguntas-Constitución-Española | 51 | 71 | 72 % |
| TEST B1 | 51 | 71 | 72 % |
| baquedano | 70 | 105 | 67 % |
| Supuestos Practicos Bloque IV | 8 | 22 | 36 % |
| «…drive-download…SIMULACROS y» | 5 | 15 | 33 % |
| TAI_ejer_1_A_libre_AGE_2024 (clave publicada) | 5 | 15 | 33 % |

**Qué se ha hecho con ellos.** Estos 10 conjuntos (**1.117 preguntas**, 380 con clave activa) **ya no entran en tus tests, simulacros ni repasos**, y tampoco cuentan para medir la cobertura de los apuntes. No se ha borrado nada: las preguntas siguen en la base y volverán en cuanto su clave esté arreglada. Otros 6 conjuntos (**984 preguntas**) están entre el 15 % y el 30 %: **entran, con la marca «clave en revisión»**.

**Lo que probé para arreglarlas sin gastar: no era un desplazamiento.** Lo primero que se comprueba es si la clave está corrida una pregunta o una opción (eso sería barato de arreglar). Se probó con las nueve tandas grandes: **ninguna baja del 10 %** moviéndola una o dos preguntas ni girando las opciones. Así que la clave no está corrida: está mal en muchos sitios, y arreglarla de verdad necesita el paso siguiente.

**El INAP 2024 modelo A: tu clave es la oficial, y el problema es la numeración.** Comparé tu plantilla con las dos oficiales del INAP. **Es la del modelo A** (coincide con ella en el 90 % de las preguntas y con la del B solo en el 35 %) y **no la he tocado**, como manda la regla. Pero **faltan 2 preguntas** de las 80 (la 57 y la 76) y **no están las 5 de reserva**: eso hace que las posiciones desde la 57 vayan una por detrás de las del examen. Con eso corregido, **7 claves no son las de la plantilla oficial** y **3 preguntas que el INAP anuló (22, 51, 70) llevan respuesta en tu copia**. Son incidencias tuyas: dime si quieres que las repase contigo.

**Lo que te toca a ti.** Los 10 conjuntos necesitan que mires su clave: son las preguntas que hoy están fuera de tus tests. Y sigue en pie lo que pediste: **una clave oficial no se cambia nunca sola**.

**Lo que todavía no está.** El «clave revisada automáticamente» que pediste (la letra de los apuntes **y** el modelo **sin los apuntes** de acuerdo → se guarda como revisada, no como oficial) **no se ha ejecutado**: son 1.117 preguntas con gasto de modelo y una marca nueva en la pantalla del alumno, y hacerlo a medias habría dejado claves a medio revisar. Queda como el siguiente bloque, con su previsión de gasto delante. El aviso «clave en revisión» ya se ve en la pantalla: sale junto al número de la pregunta mientras haces el test y también en la lista de resultados, para que sepas que esa respuesta no está confirmada. **Y tienes las cuatro fotos para verlo sin levantarte**: `artifacts/screens/test-en-curso-escritorio.png`, `test-en-curso-movil.png`, `resultado-escritorio.png` y `resultado-movil.png`, en escritorio y a 390 px, sin una sola violación de accesibilidad.

**Y una cosa que conviene que sepas: la cuarentena no sube las cifras de los apuntes, las limpia.** Al quitar de la medida las preguntas de esos 10 conjuntos, I.6 baja del 72,5 % al 71,1 % (salen 19 preguntas del denominador y 17 de ellas estaban cubiertas), y I.4 e I.8 se quedan igual (88,9 % y 82,0 %). Ninguno llega al 90 % con el que se publica. Es lo esperable: el número deja de estar sostenido por claves que no son de fiar.




**Y una corrección que te debo, porque la publiqué antes de comprobarla.** Durante un rato te dije
que en cinco conjuntos «dudosos» la clave estaba **corrida una opción** y que eso tenía arreglo
barato. **Era falso y ya está corregido**: leí mal mi propia tabla —una fila que decía «21 de 21»
era *21 fallos de 21*, no 21 aciertos—. Lo he vuelto a medir con la definición buena y con la
prueba completa, conjunto a conjunto: **en ninguno de los 16 se explica la discrepancia por un
desplazamiento**; ninguna alternativa sube del 50 %, y el azar con cuatro opciones es el 25 %. La
conclusión no cambia: **esas claves no están corridas, están mal en muchos sitios**, y arreglarlas
pide el paso de la clave revisada automáticamente, no una resta de letras. También he arreglado la
herramienta para que no se pueda volver a leer al revés: ahora dice «aciertos sobre total» y no
compara nada si su línea base no cuadra.

---

## 13-oct-2026 · La cuarentena de claves ya está aplicada a **tus datos** (y cuatro temas nuevos de apuntes)

**Esto te toca lo que estudias, así que va lo primero.** La cuarentena de claves que se anunció el
13-oct estaba **en el programa, no en tu base**: la base estaba en la revisión anterior y le faltaba la
columna del veredicto. Ya está aplicada, y con ella **la medida hecha sobre tus datos**:

- **10 conjuntos con la clave en cuarentena** (1.117 preguntas): sus preguntas **no entran** en tests,
  simulacros, repasos, práctica por tema ni diagnóstico, y **no cuentan** en la cobertura de los apuntes.
  Son los que ya se dijeron: C_ejer_1_libre_DZA_2026, Test por temas, TEST VARIOS, Test Aragón 2015,
  1600-Preguntas-Constitución, TEST B1, baquedano, Supuestos Prácticos Bloque IV, TAI_ejer_1_A (INAP
  2024) y el simulacro de drive-download.
- **6 conjuntos marcados «dudosa»** (984 preguntas): entran, con la marca **«clave en revisión»** visible
  al corregir.
- **16 cambios de veredicto**, cada uno con su registro de auditoría.
- Y la puerta se **recalcula sola al cerrar cada tema**: al escribir los apuntes de estos cuatro temas,
  **dos conjuntos más** (`PreparaTAI AGE-2026` y otro) cruzaron su umbral y entraron en cuarentena sin
  que nadie se acordara de mirarlo. Es lo que el ajuste pedía.

### Los apuntes: cuatro temas nuevos, tres publicados y uno en borrador

Por la tabla de valor (cuántas preguntas tienen clave **utilizable**), y con el índice de cada tema
escrito y **ensayado antes de pagar** (0 $):

| tema | previsión | coste real | cobertura (clave utilizable) | veredicto |
|---|---|---|---|---|
| **IV.5** · Seguridad de los sistemas de información | 0,51–0,88 $ | **0,5452 $** | **97,3 %** | **publicado** |
| **III.9** · Repositorios, metodologías, pruebas y control de versiones | 0,43–0,73 $ | **0,4961 $** | **96,1 %** | **publicado** |
| **I.5** · Igualdad, violencia de género, LGTBI, discapacidad y dependencia | 0,41–0,71 $ | **0,8966 $** | **91,5 %** | **publicado** |
| **IV.6** · Comunicaciones, medios de transmisión y redes | 0,42–0,73 $ | **0,3916 $** | **97,0 %** | **publicado** |
| **I.7** · Protección de datos personales y derechos digitales | 0,49–0,85 $ | **1,1903 $** | 58,4 % | **borrador** |

**I.7 se queda en borrador con dos motivos escritos**: su corrida **se paró por su tope de tiempo**
(compuso 257 de 364 grupos) y el bucle que rellena los huecos apenas arrancó. Los apuntes están
escritos y guardados (19 apartados, 25.768 palabras) y **volver a lanzarlo cuesta 0,26–0,64 $**, sin
pagar otra vez por lo hecho. **Dos cosas que conviene que sepas de I.7**: su bandeja de incidencias
está **vacía** (las escribe el final del bucle que el tope cortó) y su tope de dinero se cruzó en
0,06 $.

### Una cifra que te sirve para lo que queda: el precio de un tema

Medido en esta tanda: **0,0037–0,0045 $ por llamada en un tema técnico** y **0,0078–0,0083 $ en uno
normativo y denso** (casi el doble). Y la cota de arriba de la previsión **se ha quedado corta en los
tres temas normativos densos** (I.4, I.8 y ahora I.7). La regla del tope («la cota de arriba más un
tercio») **sigue siendo la correcta** —es la que impidió que I.7 se fuera de las manos— pero conviene
saber que en un tema normativo hay que contar con el doble de precio por llamada que en uno técnico.

### Lo que sigue, y lo que necesitaría

- **III.4 (Diseño y programación orientada a objetos)** **no se escribe**, y está medido: de sus 405
  grupos, solo el **58,5 %** son de su materia; el resto son **fundamentos de programación** (bucles,
  operadores a nivel de bits, tipos primitivos de Java), que son de III.2. Su cobertura no podría pasar
  del 60 %: **es un problema de clasificación de preguntas, no de apuntes**, y adivinar dónde va cada
  una es trabajo de la bandeja, no de los apuntes.
- **Los siguientes por valor** son III.1, III.7, III.5, IV.9 y IV.8, y todos necesitan su catálogo
  antes de la corrida (el ensayo de reparto, que es gratis y va antes de pagar).
- **I.7 es el único tema que pide una segunda corrida** (0,26–0,64 $) para rellenar sus huecos y
  llenar su bandeja.

### Al cerrar la tanda: **cinco temas publicados y uno en borrador**, por 3,87 $

| tema | previsión | coste real | cobertura | veredicto |
|---|---|---|---|---|
| IV.5 · Seguridad de los sistemas de información | 0,51–0,88 $ | 0,5452 $ | 97,3 % | publicado |
| III.9 · Repositorios, metodologías, pruebas y control de versiones | 0,43–0,73 $ | 0,4961 $ | 96,1 % | publicado |
| I.5 · Igualdad, violencia de género, LGTBI, discapacidad y dependencia | 0,41–0,71 $ | 0,8966 $ | 91,5 % | publicado |
| IV.6 · Comunicaciones, medios de transmisión y redes | 0,42–0,73 $ | 0,3916 $ | 97,0 % | publicado |
| III.1 · Modelado de datos, modelo relacional y normalización | 0,33–0,57 $ | 0,3524 $ | **98,6 %** | publicado |
| I.7 · Protección de datos personales y derechos digitales | 0,49–0,85 $ | 1,1903 $ | 58,4 % | borrador |

Van a la zona del alumno con la marca «Versión generada · en revisión», como los anteriores. Si algo
está mal, lo que más ayuda es **«Esto está mal»** desde el propio párrafo: queda anclado al apartado y
me llega con el texto delante.

### La tanda siguiente (13-oct, por la tarde): dos temas técnicos más y una decisión sobre I.7

Se han escrito y **publicado** dos temas más, elegidos **midiendo su banco antes de pagar** (el ensayo
del reparto es gratis):

| tema | previsión | coste real | cobertura | veredicto |
|---|---|---|---|---|
| III.5 · Jakarta EE y .NET: arquitectura, persistencia, seguridad e interfaces | 0,33–0,58 $ | **0,3078 $** | **99,2 %** | publicado |
| III.7 · Aplicaciones web, HTML/XML, navegadores y lenguajes de script | 0,32–0,55 $ | **0,3990 $** | **93,6 %** | publicado |
| IV.8 · Internet: arquitectura, servicios, HTTP y SSL/TLS | 0,28–0,48 $ | **0,1885 $** | **99,1 %** | publicado |

Los tres son **técnicos**, y eso se nota en la factura: **0,0030–0,0039 $ por llamada**, la mitad que
un tema normativo denso (0,0078–0,0083 $), y **0,30 $ de media por tema**. Aun así, III.7 avisó de lo
que cuesta su banco: de sus 248 grupos, casi una quinta parte son preguntas de **otros temas** (MySQL,
cortafuegos, firma electrónica, archivística), y ésas no se responden desde III.7 —van a tu bandeja con
su motivo—. Con el primer índice, su techo se quedaba en el 89 %: **el ensayo previo evitó pagar un
borrador seguro**.

**Y uno de los tres se quedó sin publicar al terminar la corrida por una tontería que se arregló sin
pagar**: la tabla de puertos de servicios de Internet no salía partida por familias. La causa era que
el catálogo no decía «aquí vive la tabla de puertos»; se añadió esa marca y la limpieza (0 $) la partió
y la dejó bien. Lo cuento porque es la tercera vez que **una reparación de forma gratis evita repetir
una corrida**.

**I.7 (protección de datos) se queda en borrador y no se ha reanudado, con la cifra delante**: cubre
el **58,4 %** y para el 90 % le faltan **157 preguntas** de las que quedan fuera. Reanudarlo cuesta
0,26–0,64 $, pero **no lo arregla**: no queda ni un grupo sin comprobar, así que la cobertura solo
puede subir rellenando huecos, y lo que le falta es **material** (196 preguntas sin respuesta en los
apuntes). Va después de los técnicos.

**Lo que sí se ha hecho por I.7, y era lo que pedía el encargo**: su **bandeja estaba vacía** —las
incidencias las escribe el final del bucle que el corte de tiempo no alcanzó— y ahora tiene **42
filas** (23 claves que contradicen el material, 11 huecos sin material, 4 claves sospechosas y 4
preguntas ambiguas). Se han escrito **sin llamar al modelo** (0 $) desde las comprobaciones que ya
estaban guardadas: un hueco que no se ve es un hueco que no existe.

**El acumulado del objetivo va por ≈ 15,35 $ de 40 $**, muy por debajo del aviso de los 20 $. A este
precio (0,19–0,40 $ un tema técnico) quedan temas de sobra dentro del presupuesto.

## 13 oct 2026 — Dos temas más publicados (administración de sistemas y seguridad en redes)

Se han escrito y **publicado** los dos que quedaban por valor que no tenían índice. Van con la marca
«Versión generada · en revisión», como los anteriores:

| tema | previsión | coste real | cobertura | veredicto |
|---|---|---|---|---|
| IV.1 · Administración del sistema operativo y software de base | 0,30–0,52 $ | **0,3281 $** | **98,2 %** | publicado |
| IV.9 · Seguridad en redes, perímetro, acceso remoto, VPN y puesto | 0,27–0,46 $ | **0,3204 $** | **91,1 %** | publicado |

**Lo que cambia para ti:**

1. **IV.1 (administración del sistema)** sale muy bien: cubre el **98,2 %** de las preguntas y su
   temario es el del día a día del administrador —usuarios y permisos, procesos y servicios, discos y
   sistemas de ficheros, paquetes y versiones de Debian y macOS, PowerShell y `cmd`, y el
   mantenimiento y la reparación—. Su bandeja te deja **8 incidencias** (4 claves que contradicen el
   material, 3 en las que los apuntes dicen otra letra y 1 hueco).

2. **IV.9 (seguridad en redes) publica al filo, y lo sabíamos antes de pagar**: cubre el **91,1 %**
   cuando el listón es el 90 %. La razón está medida y no es del índice: de los 22 grupos de preguntas
   que ningún apartado puede situar, **20 tienen clave** y son de **otros temas** (el PoE y las VLAN,
   que son de IV.10; el RAID y el TIA-942, de IV.2 y IV.5; la gestión de incidencias, de IV.5; el
   `RFC 2142` y Exchange, de IV.3). Se escribió con esa cifra delante: su techo era el 91,2 %.
   **Y su bandeja es la más llena de todas: 34 incidencias** (15 preguntas sin clave con la que
   comprobarse, 11 claves que contradicen el material, 4 claves sospechosas y 4 huecos). Ahí tienes
   trabajo real de revisión: son las preguntas que el banco trae mal o sin respuesta.

3. **Dos preguntas se quedaron sin cubrir porque el modelo no contestó** por ellas (un fallo de la
   llamada, no del material): no llevan incidencia porque no hay nada que revisar, pero quedan
   dichas en el informe del tema.

4. **Una cosa que se aprendió arreglando, y que conviene que sepas**: la corrida de IV.9 dejó el tema
   sin publicar porque el redactor escribió **dos tablas de puertos** en dos apartados distintos, y un
   tema **no puede tener dos**: cada una lleva sus encabezados («Servicios de red», «Confusiones que
   caen») y la comprobación de encabezados repetidos los cuenta dos veces. Se arregló **sin pagar
   nada**: las cuatro filas que faltaban (Telnet 23, TFTP 69, RDP 3389 y VNC 5900) se movieron a la
   tabla del cortafuegos **tal como estaban escritas** —no se inventó ninguna— y el bloque duplicado
   se quitó. Es la cuarta vez que una reparación gratis evita repetir una corrida.

**El acumulado del objetivo va por ≈ 16,00 $ de 40 $**, todavía por debajo del aviso de los 20 $.
Quedan **15 de los 33 temas publicados** y cuatro borradores (I.4, I.6, I.7 e I.8) que no se reanudan
porque lo que les falta es material y criterio sobre las claves, no otra corrida.

**Lo que más ayuda ahora mismo**, si tienes un rato: las bandejas de **IV.9** (34 filas) e **IV.1**
(8) en el panel de incidencias, y el botón **«Esto está mal»** desde el propio párrafo de los apuntes
cuando algo no cuadre: queda anclado al apartado y llega con el texto delante.

---

## Qué ha cambiado para ti en esta tanda (F23 · los exámenes del INAP)

**Ya puedes hacer exámenes oficiales del INAP en la pantalla de Exámenes, con la clave que publicó la
Administración.** Son **11 exámenes** listos (de 13 que aparecen), con su número de preguntas y su
procedencia a la vista. **Coste de API: 0 $** (esto es conversión de PDF y datos, no ha llamado a
ningún modelo).

### Los 16 cuestionarios del INAP que descargaste: qué ha pasado con cada uno

| Examen | Qué ha pasado | Preguntas |
|---|---|---|
| **2019** libre y promoción interna | **Importados y listos** | 135 y 85 |
| **2022** promoción interna | **Importado y listo** | 85 |
| **2024** libre A y B, promoción interna A y B | **Importados y listos** (los cuatro) | 135 y 85 |
| **2025** libre A y B, promoción interna A y B | **Ya estaban** de la tanda anterior y **no se han duplicado**: comprobé que sus claves coinciden con las plantillas oficiales, **135 de 135 y 85 de 85** | 135 y 85 |
| **2025 extraordinario** | **Importado**; su examen se ve, pero todavía no se puede hacer (ver abajo) | 135 |
| **2022 libre** | **Importado**; su examen se ve, pero todavía no se puede hacer (ver abajo) | 135 |
| **2018** libre 1.º, libre 2.º y promoción interna | **Fuera**: los tres son **escaneos** (fotos de papel) y hay que pasarles OCR antes. Tu equipo no tiene el OCR instalado, así que no los he transcrito a mano: transcribir 30 páginas «a ojo» no es importar, es inventar | — |

**Los dos que se ven y no se pueden hacer** (2022 libre y 2025 extraordinario) tienen un motivo
concreto y **lo ha detectado el propio sistema**, no lo he tapado yo: la plantilla de esos dos
exámenes **ya estaba en tu biblioteca desde el 29 de septiembre**, guardada antes de que se arreglara
un fallo de extracción de texto que **recortaba** lo que se podía citar (de 1.276 caracteres se
guardaban 1.198). Sin las últimas líneas de la plantilla, la comprobación que enlaza la plantilla con
la clave **confirma 60 de las 135 respuestas y se niega**, que es lo correcto: antes que activar una
clave que no puede demostrar, se para y lo dice. La pantalla te lo dice con su aviso («Todavía no se
puede hacer: faltan sus respuestas»).

**Y ahí hay algo que te interesa más allá de estos dos exámenes**: he medido cuántas versiones de tu
biblioteca tienen ese texto recortado y son **3.474 de 5.162** (1,71 millones de caracteres que no se
pueden citar). El arreglo del código ya está hecho desde octubre, pero **los datos viejos no se han
vuelto a extraer**, y no hay todavía una herramienta que lo haga. Es trabajo pendiente y está apuntado.

### De dónde sale cada pregunta, ahora escrito en los datos

Cada conjunto de la aplicación dice de dónde sale, con tres valores posibles:

- **Administración General del Estado** (los exámenes del INAP y los de la Guardia Civil),
- **Otra administración** (ayuntamientos, comunidades, universidades),
- **Desconocida** (cuando no se puede afirmar; **es el valor de partida y no quita nada de ningún
  sitio**).

**Para qué sirve, en la práctica, una sola cosa**: en un **simulacro** o en un **examen**, las
preguntas de otra administración **no entran**, porque el simulacro tiene que parecerse al examen que
te vas a encontrar. En un **test por tema** y en los **apuntes sí cuentan**, porque ahí el material es
para estudiar. Y en la pantalla de Exámenes lo ves escrito en cada fila, para que sepas qué estás
practicando.

De tus 242 conjuntos: **30 son de la AGE**, **28 de otra administración** y **184 quedan como
«desconocida»** (tu material propio, del que el título no dice la administración). Los 30 y los 28 los
he clasificado **por el título**, con la regla escrita y **49 cambios registrados en la auditoría**;
los 184 se quedan como estaban porque decir «AGE» de un banco que no lo declara sería afirmar lo que
no se sabe.

### La clave oficial, intacta, y tú no la puedes romper por accidente

- La clave se ha copiado **literalmente de la plantilla oficial**, sin interpretar nada. Donde la
  plantilla dice «ANULADA», queda anulada; donde reinicia la numeración en cada supuesto, se respeta.
- **La guarda protege los exámenes importados**: si intentas cambiar la respuesta correcta de una
  pregunta de un examen oficial desde su ficha, la aplicación **lo rechaza** (y no escribe nada). Hay
  una prueba nueva que lo comprueba con un examen montado igual que los tuyos.
- Y no he relajado la comprobación que impide activar la clave de un examen oficial sin su plantilla
  enlazada: es justo lo que demuestra que la clave que se aplica es la del documento oficial.

### El examen de 2024 que estaba mal numerado

El **TAI libre 2024 modelo A** que ya tenías en el banco privado (78 preguntas, 7 posiciones
desplazadas, marcado como no fiable) **sigue ahí y no lo he tocado**, porque está en cuarentena y de
ahí no se toca nada. Lo que he hecho es importar el **examen oficial de verdad**, con la numeración
oficial (80 + 5 de la primera parte y 20 + 5 de cada supuesto), 15 reservas, y su clave activa
enlazada a la plantilla oficial. **Una sola verdad practicable**: para practicar 2024 A se usa el
examen oficial nuevo. Las copias viejas del banco privado no entran en tests ni simulacros (una está
en cuarentena), así que no se cruzan.

### Lo que queda pendiente de esta tanda

1. Las **capturas** de la pantalla de Exámenes con un examen oficial (escritorio y móvil) y el
   resultado de las **18 puertas**: van en el informe del bloque.
2. **«Volver a extraer» el texto de las versiones viejas de la biblioteca** (los 1,71 M de caracteres
   recortados). Con eso, los dos exámenes que hoy no se pueden hacer quedarían listos sin tocar
   ninguna clave.
3. **Los tres exámenes de 2018**: necesitan el OCR instalado en tu equipo (`tesseract` con el idioma
   español). Cuando esté, se importan con el mismo comando.

## Tanda del 14-oct-2026 (F24): cinco temas más, y una cosa que quiero que sepas

### Lo que ya puedes leer

**Cinco temas nuevos publicados**, con sus apuntes en la zona del alumno y la marca «Versión generada ·
en revisión». Con estos son **20 de los 33**:

| Tema | Materia | Cobertura (clave utilizable) |
|---|---|---|
| **II.1** | Informática básica, representación de la información, arquitectura y componentes internos | **98,5 %** |
| **III.3** | Lenguajes de interrogación, ANSI SQL, procedimientos y disparadores | **91,8 %** |
| **II.3** | Tipos abstractos, organizaciones de ficheros, algoritmos y formatos | **95,3 %** |
| **I.3** | El Gobierno: composición, funciones y relaciones con las Cortes | **92,8 %** |
| **IV.10** | Redes locales, tipología, transmisión, acceso y dispositivos | **97,7 %** |

Coste medido de la tanda: **1,0017 $**. El acumulado del objetivo va por **≈17,3 $ de 40**.

### Una cosa que tienes que saber, y por la que te la cuento antes que nada

**En el tema I.3 hay un apartado que no es de ese tema.** Se titula «Áreas de distribución del CPD
según ANSI/TIA-942» y habla del **MDA, el HDA y el EDA**, que son cosas de un Centro de Procesamiento
de Datos: eso pertenece a **IV.5.7**, no a «El Gobierno».

- Es **1 apartado de 15**, **2 hechos de 300** y **730 caracteres** de unos 45.000 (el **1,6 %** del
  tema). Son **5 preguntas** de las 181 que cubre el tema.
- **Lo he dejado escrito a propósito, en vez de borrarlo**, y quiero que sepas por qué: la puerta que
  mide la cobertura **cuenta comprobaciones guardadas, no el texto**. Si quitara esos hechos y vaciara
  el apartado, el número que ves seguiría diciendo 92,8 % mientras tú ya no leerías esas frases: un
  dato que no corresponde con lo que hay. La cifra **honesta**, descontando ese apartado, es **90,1 %**,
  que también pasa el listón; en el informe van las dos, dichas.
- **Lo que falta para que no vuelva a pasar** es una comprobación que hoy no existe: que mire si el
  apartado al que se ancla una respuesta **es del tema**. La de cobertura dice cuántas respuestas están
  contestadas, no por quién. Queda anotado como lo que es, un hueco del método.

Si prefieres que ese apartado desaparezca de la vista, se puede vaciar en un minuto (0 $), pero
entonces el 92,8 % deja de ser cierto: dímelo y lo hago con la cifra corregida en el panel.

### Dos corridas cuyo coste no se pudo medir (y por qué)

**II.1** se murió a lo bruto a los 14 minutos (un fallo de memoria de Windows, no del motor): el
trabajo quedó escrito y el tema se publicó, pero **el informe con las llamadas y el coste se perdió**.
Su coste va **estimado en 0,20–0,36 $**, no medido, y lo digo así en su informe. Se completó después
por **0,0577 $** y subió de 96,6 % a 98,5 %.

**En II.3**, un defecto de mi guion de lanzamiento (reintentaba cuando no debía y escribía los dos
intentos en el mismo fichero) hizo **una corrida de más de 0,0835 $** y perdió el coste de la primera
(≈0,10 $): **≈0,12 $ de más**, dicho con su cifra.

### Copias de seguridad

Hice **copia verificada nueva** al empezar (revisión `0037`, comprobada entera: integridad, CRC,
recuentos y bytes) porque la más reciente era de **antes** de la migración del INAP. **No he borrado
ninguna de las anteriores**: la política dice conservar dos y el motivo era el disco, y hoy sobran
**78,9 GB** en `F:`. Tienes **tres copias verificadas**; si prefieres volver a dos, dime cuál se va.

## 14-oct-2026 · Ya puedes revisar los apuntes desde el panel: ver por qué un tema no está publicado, leerlo y decidir

Hasta hoy, saber por qué I.6, I.7 o I.8 seguían en borrador obligaba a mirar un informe. Ya no: hay
una pantalla nueva en el menú del panel.

### Qué puedes hacer ahora

**Menú → Apuntes** (nueva entrada, con un contador que te dice cuántos temas esperan tu decisión).

1. **La tabla de los 33 temas** con su estado —Publicado, En borrador, Sin apuntes—, sus cifras y, en
   los cuatro borradores, **el motivo con su número**. No hay que abrir nada para saber qué pasa.
2. **Pinchas un tema y lo lees entero**, apartado a apartado, **igual que lo lee el alumno** (mismo
   texto, mismas tablas, mismos títulos) y con las cifras de cada apartado: cuántos hechos tiene,
   cuántas preguntas se contestan en él y cuántas quedan sin resolver.
3. **Un botón «Los peores primero»** ordena los apartados por lo que queda sin resolver, para no
   releerte sesenta páginas cuando solo quieres ver lo que está peor.
4. **Al final, tu decisión**, con una nota tuya:
   - **Aprobar los apuntes**: publica el tema **si cumple las dos puertas** del §2.3 (el 90 % y la
     forma del texto). Si no las cumple, el tema queda aprobado y sin publicar, y la pantalla te dice
     **qué puerta** lo ha frenado.
   - **Rechazar con este motivo**: la nota es **obligatoria**. Sin ella el botón no se puede pulsar (y
     el servidor tampoco lo admite), para que dentro de un mes se sepa por qué.

Cada decisión queda **auditada** —quién, cuándo, y qué había antes y después— y **no se pierde** aunque
el motor vuelva a comprobar el tema: está probado que una corrida nueva no borra tu decisión.

### Cómo están tus cuatro borradores (medido hoy, 14-oct-2026)

| tema | cobertura | qué le pasa |
|---|---|---|
| **I.4** | 489 de 542 = **90,2 %** | **Cumple las dos puertas**: no está publicado porque nadie archivó su versión. **Aprobarlo lo publica** |
| **I.6** | 164 de 230 = **71,3 %** | Le faltan **43** preguntas por contestar en los apuntes |
| **I.7** | 289 de 493 = **58,6 %** | Le faltan **155** |
| **I.8** | 394 de 477 = **82,6 %** | Le faltan **36** |

Los quince temas publicados no se miden en la tabla (ya pasaron las puertas); su ficha sí los mide si
la abres, y ahí verás también sus apartados.

### Tres cosas que no cambian (a propósito)

1. **El listón del 90 % no se ha tocado.** Aprobar un tema del 82 % **no** lo publica: te dirá que la
   cobertura no llega. Lo contrario sería colar por la puerta de atrás justo lo que la puerta impide.
2. **La zona del alumno no se ha tocado**: sigue leyendo lo mismo y con la misma marca. Lo único que
   cambia es que, cuando apruebas un tema que cumple las puertas, deja de estar en borrador.
3. **Esto no llama a ningún modelo y no cuesta dinero**: la cifra se lee de las comprobaciones que el
   motor ya dejó guardadas.

### Lo que te toca a ti

1. Abrir **Apuntes** y decidir sobre los cuatro. **I.4 se publica con un clic** (si el texto te
   convence, claro: la cifra dice que contesta al 90,2 % de lo que se puede corregir, no que esté bien
   escrito).
2. Para I.6, I.7 e I.8 hay que **escribir más apuntes o reasignar preguntas**: eso es la tanda de
   contenido, no esta pantalla. Lo que sí puedes hacer ya es **rechazarlos con tu motivo**, que queda
   guardado y a la vista de quien siga con ellos.
3. Si algún tema te parece mal publicado, dímelo: hoy la tabla no mide los publicados, así que habría
   que abrir su ficha (una a una) para ver su cobertura de hoy.

## 14-oct-2026 · El motor ya comprueba que el sitio donde acaba un hecho o una respuesta sea suyo (y dos temas publicados bajan del listón al medirlos bien)

Este bloque no ha escrito apuntes ni los ha tocado: ha arreglado **cómo se mide**. Tres cosas que
estaban mal y que eran la misma: **nadie comprobaba que el apartado donde acaba un hecho —o donde se
apoya una respuesta— fuera suyo**. Lo cuento con las cifras porque una de ellas te afecta.

### 1. Una respuesta contaba como buena aunque se apoyara en un apartado que no era el suyo

La cobertura decía **cuántas** respuestas estaban contestadas, y no **por quién**. Si una pregunta no
tenía apartado propio, el motor la comprobaba contra el **primer apartado de su epígrafe** —que puede no
tener nada que ver— y, si ahí aparecía la frase, la contaba como cubierta. Eso ya no pasa: una respuesta
solo cuenta si su apartado es suyo.

### 2. Un hecho que no dice de qué habla se sentaba en el apartado de su pregunta

Es lo que metió el estándar del **CPD** (que es de IV.5.7) dentro de **I.3**. Ahora un hecho que no
nombra ninguna materia del tema **no se sienta en ningún apartado**: se queda en la bandeja con su
motivo y su texto, y su pregunta se te enseña para que decidas. **No se pierde nada**: se ve.

### 3. La misma pregunta se contaba dos veces (y eso solo podía perjudicarte)

Una pregunta que el índice no sabe situar entraba dos veces en la cuenta: como hueco y además con su
comprobación. El cociente salía **por debajo** del verdadero, así que **nunca dejaba pasar un tema malo:
podía bloquear uno bueno**. Medido: **16 de los 28 temas** tenían preguntas contadas dos veces (**91
preguntas**), entre +0,3 y +8,1 puntos de diferencia. Hoy cada pregunta cuenta **una sola vez**.

### Lo que esto cambia en tus temas, con nombre y con cifra

**El listón del 90 % no se ha tocado** y no se ha cambiado la forma de medir para que nada pase. Al
medir con la puerta buena, **dos temas publicados dejan de llegar al 90 %**:

| tema | publicado con | mide hoy | qué se le ha descontado |
|---|---|---|---|
| **I.3** (el Gobierno) | 168/181 = **92,8 %** | **152/181 = 84,0 %** | **16 preguntas** que no son de I.3: las 5 del estándar del **CPD** (de IV.5.7) y las 11 de otros ocho grupos ajenos —el **CSV** del RFC 4180, el **TREBEP**, los **funcionarios interinos**, las **infracciones leves**, el **ANSI SQL**, **Jakarta EE** y **Docker**— que estaban sentados en sus cajones |
| **I.4** (función pública) | 489/542 = **90,2 %** | **483/540 = 89,4 %** | **6 preguntas**: el **kernel de Android** (que es de IV.1) y la **Ética Pública**, que el índice no sitúa y se comprobaba contra el primer apartado de su epígrafe |

**No he tocado ni una línea de esos dos temas.** Siguen publicados y se leen igual: lo que ha cambiado es
la cifra, que ahora dice lo que de verdad contestan sus apuntes. **La decisión es tuya** y tienes tres
caminos, ninguno urgente:

1. **dejarlos como están** — se leen bien y el alumno no nota nada; la cifra queda dicha aquí y en el
   panel;
2. **retirarlos** desde el panel (vuelven a borrador, sin perder nada del texto) hasta que se limpien; o
3. **volver a correrlos** cuando toque: una corrida con el reparto nuevo deja fuera el material ajeno y
   los apartados que pierden hechos se rehacen — eso **sí cuesta dinero** (≈0,4–1,5 $ por tema) y lo
   decides tú.

### Y una corrección que te debo

El informe de I.3 decía que, descontando el material del CPD, su cifra honesta era **163/181 = 90,1 %**
—o sea, que pasaba—. **Se quedó corto**: no miró los otros ocho grupos ajenos, que entraron por la misma
puerta. La cifra buena es **152/181 = 84,0 %**. Lo digo porque el informe te dio una cifra que ya no
sostengo.

### Lo que no cambia

- **Tus datos no se han tocado**: todo esto es lectura (`--medir`) sobre tu base, sin escribir una fila y
  sin llamar a ningún modelo. Coste: **0 $**.
- **El listón sigue en el 90 %** y aprobar un tema del 82 % **no** lo publica.
- **La zona del alumno no cambia**: lee lo mismo.