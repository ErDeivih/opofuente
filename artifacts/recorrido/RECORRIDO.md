# El recorrido con los datos reales

**F34 · 16 de octubre de 2026 · base `main = c4a7d8d` · rama `f34-recorrido`**

Esto es lo que pidió el §3 de `docs/RECORRIDO-Y-ACABADO-2026-10.md`: recorrer la aplicación **como la
usaría el propietario**, con **sus datos**, capturando cada paso a 1280 y a 390 y apuntando lo que
falla, lo que tarda y lo que un alumno no entendería. **No se ha tocado ni una línea de la
aplicación**: lo que aparezca aquí va al bloque que toque.

---

## 1 · Sobre qué datos se ha recorrido

La base real **no se ha tocado**. Se ha hecho una copia con el método de la casa —instantánea de
SQLite, ZIP con manifiesto, `verify_archive`, extracción y las tres comprobaciones de SQLite— y todo
lo que sigue se ha corrido contra la copia.

| | Base real (no tocada) | Copia de trabajo |
|---|---|---|
| ruta | `F:\OpoFuente\datos\opofuente.sqlite3` | `F:\temp-opofuente\f34-datos\opofuente.sqlite3` |
| bytes | **2.748.612.608** | **2.748.612.608** |
| SHA-256 | `a0a21413f6ab7d2ebc49194ff93fa7da5ac0d1d27b3417ce34481e5bffc5aff8` | `622aaa6fbe9cb200c5ee0f25f3e75f46d6adcf07d50ae098714d47f5abe3f238` |
| revisión | `0039_claves_derivadas` | `0040_cuentas_y_consentimiento` (head) |

- **El archivo de la copia**: `F:\temp-opofuente\f34-datos\backups\f34-20261016-132300.zip`,
  **811.750.221 bytes**, SHA-256 `2082617d88fa31183e7b797746f07ed2f5cfeb41f36a996e75a883af1114b27b`,
  alcance `database` (el estándar de D5: 0,81 GB, «solo base»). `verify_archive`: **sin problemas**.
- **La copia extraída**: `integrity_check` **ok** · `quick_check` **ok** · `foreign_key_check`
  **vacío** · 65 tablas.
- **La real, al terminar todo**: mismo tamaño y **mismo SHA-256** que al empezar. Comprobado con el
  hash, no con la fecha.
- **Las dos migraciones que faltaban se aplicaron a la copia**, no a la real:
  `0039_claves_derivadas → 0039_bandeja_por_conjunto → 0040_cuentas_y_consentimiento` en **3,5 s**
  (2,9 s en una primera pasada). Es exactamente lo que la aplicación hará allí donde arranque.
- **La API se ha levantado contra la copia**, no contra la real, en **127.0.0.1:8765** (estaba
  libre, así que no ha hecho falta otro puerto) y la web servida en 127.0.0.1:4173 desde este árbol.

*(Los datos de la copia se han repuesto dos veces desde el ZIP verificado durante el trabajo, para
que el recorrido bueno empezara del estado del propietario y no de los restos de las pruebas
anteriores. Después de reponer, se vuelven a aplicar las dos migraciones: 3,5 s.)*

**Y una cosa que hay que tener en cuenta al leer las cifras de Inicio, Fallos y Progreso**: el
recorrido **crea datos** —monta un test de 10, hace un examen oficial de 85 y contesta—, así que
esas pantallas se leen **con los tests del propio recorrido ya dentro**. Por eso Progreso dice «4
tests hechos» (los dos del propietario del 1-oct y los dos del recorrido) y «11 aciertos» (sus 4 más
los 7 del test de IV.7). No se ha inventado nada para la foto: es lo que había al pasar por ahí.

## 2 · Cómo se ha medido, y lo que NO puedo afirmar

El recorrido lo hace un guion de navegador de verdad
(`artifacts/recorrido/herramientas/recorrido.mjs`) que **pulsa lo que hay en pantalla** y, en cada
paso, guarda:

- el PNG a **1280×800** y a **390×844** (esta vez sí: los dos anchos, y el ancho del documento medido
  para saber si algo se desborda);
- **lo que tarda la pantalla en quedar lista** (sin red pendiente, con `main` a la vista y **sin
  esqueletos ni textos de carga**: medir el esqueleto diría que va rápido cuando lo que tarda es el
  contenido);
- los errores de consola, y el texto de la pantalla leído del DOM.

**Lo que no puedo afirmar:** este modelo **no ve imágenes**. Los PNG son para que los mires tú. Todo
lo que aquí se dice de «lo que se ve» está leído del **DOM** (el texto, las etiquetas, los roles y la
geometría), no del píxel. Cuando algo solo se puede juzgar mirando (un color, un icono torcido), lo
digo en vez de darlo por bueno.

El registro crudo, paso a paso, está en `artifacts/recorrido/filas.json`, y la tabla de tiempos que
sale de él, en `artifacts/recorrido/TIEMPOS.md`.

**Las capturas**: 60 PNG (30 a 1280 y 30 a 390, uno por paso y ancho), 312 MB. Son capturas de
**página entera**, así que las de I.1 pesan **17–27 MB** cada una (la página mide 314.402 px de alto)
y tardan en abrirse: es el precio de retratar un tema entero de una vez, y también es un dato —una
pantalla que se sirve así no se puede revisar cómodamente—. Las del resto de pasos son normales.

## 3 · La noticia: con tus datos, lo que fallaba ya no falla

El 16-oct se revisaron 60 capturas hechas sobre **la siembra de pruebas** y no se pudo juzgar la
aplicación: el tema IV.7 salía «Sin apuntes · 0 preguntas», Inicio decía «Todavía no hay apuntes
escritos de ningún tema» y el resultado enseñaba preguntas inventadas. **Con tus datos, nada de eso
pasa**:

| Lo que se decía con la siembra | Lo que sale con tus datos (medido) |
|---|---|
| IV.7 «Sin apuntes · 0 preguntas» | **25 apartados** en el índice y **25 en el cuerpo**, 25 notas al margen, 25 botones «Esto está mal», estado **«Versión generada · en revisión · 403 preguntas»** |
| Inicio «Todavía no hay apuntes escritos de ningún tema» | La frase **no aparece**; Inicio lista **29 temas con apuntes**, 2 tests recientes y 2 atajos a tests |
| Preguntas inventadas en el resultado | El resultado de un test de 10 sale con **su hoja de respuestas de 10 filas**, **3 enlaces «Ver en apuntes»** (las tres falladas) y las cifras en español (**«6,00»**) |
| — | El temario lista **29 temas**; el panel de apuntes cuenta **28 temas con apuntes: 26 publicados y 2 en borrador, y 5 sin apuntes escritos** |

Es el primer recorrido sobre datos reales y la conclusión de fondo es esa: **la aplicación que va a
usar el propietario es la de verdad**, no una maqueta. Lo que sigue son los defectos que aparecen
cuando se usa esa aplicación de verdad.

## 4 · Los tiempos, por pantalla

La tabla completa, generada desde `filas.json`, está en `artifacts/recorrido/TIEMPOS.md`. Resumen:

- **Ninguna pantalla de carga normal pasa de 2,5 s** —Inicio 2,18 s, Temario 1,46 s, IV.7 1,68 s,
  I.1 2,14 s, Simulacros 2,50 s, Progreso 2,31 s, Exámenes 0,65 s, Resultado 0,34 s—, y las que son
  un salto dentro de la misma página (los apartados del índice) tardan **60–176 ms**.
- Las tres que sí tardan son del panel y del montaje, no de la lectura: **`/admin/apuntes` 5,37 s**,
  **la revisión de IV.7 3,45 s** y **el montaje de un simulacro, 142,3 s** (apartado 5).
- **Ninguna pantalla se desborda** a 390 px (el ancho del documento es ≤ 390 en las 32 capturas). Hay
  dos desbordes **dentro** de una caja en el panel (`section.card 375>364` en Incidencias y
  `div.apuntes__lectura 342>325` en la revisión de IV.7): contenido que se sale de su tarjeta, no de
  la página.
- **Un solo paso con errores de consola** en todo el recorrido: la respuesta a una pregunta del
  examen oficial (apartado 5.4).

## 5 · Paso a paso: lo que se ve, lo que falló, lo que tardó

### 5.1 Inicio → Temario → IV.7 → dos apartados → practicar

**Lo que se ve.** Inicio (2,18 s) saluda, dice «No tienes ningún test a medias», enseña el progreso
por bloque (II, III y IV en «Sin empezar») y **29 temas con apuntes**. Temario (1,46 s) lista los 29
temas con su código, su título y su estado. IV.7 (1,68 s) abre con **25 apartados** en el índice,
**25 en el cuerpo**, 25 notas al margen («Esto se pregunta») y 25 botones «Esto está mal», y su
estado dice «Versión generada · en revisión · 403 preguntas». Pulsar los dos primeros apartados del
índice salta a su ancla en **176 ms** y **60 ms**.

**Lo que falló.**

1. **No existe «Practicar este apartado».** El §3 lo pide y no está en ninguna parte: lo que hay es
   la pestaña **«Preguntas»** del tema, que lleva a `/tests?tema=IV.7`. Está dicho en
   `PARA-EL-PROPIETARIO.md` (13-oct) como hueco pendiente, así que no es una sorpresa: se apunta para
   que no se pierda.
2. **Dentro del tema no hay buscador ni modo repaso** (se comprueba en el apartado 5.2, que era su
   sitio).

**Lo que un alumno no entendería.** Nada de esta pantalla, y es una buena noticia: el tema se lee, el
índice navega y el texto llega formado (tablas incluidas).

### 5.2 Temario → I.1: índice, buscador dentro del tema y modo repaso

**Lo que se ve.** I.1 (2,14 s) abre con **21 apartados**, 21 en el índice y 21 en el cuerpo. La
página mide **314.402 px de alto**: es el tema más largo del programa (60.400 palabras) y se sirve
entero de una vez.

**Lo que falló.**

1. **El índice de un tema largo no se puede recorrer entero.** El índice de I.1 mide **1.405 px** y el
   de IV.7 **1.415 px**, en una ventana de 800. El último enlace de I.1 está a **1.636 px** del
   borde superior y el de IV.7 a **1.665 px**: **fuera de la ventana**. Medido con el navegador
   intentando pulsarlos de verdad: **no se puede pulsar ni el 20.º de 25 en IV.7, ni el 20.º de 21 en
   I.1** (espera agotada a los 6 s en los cuatro intentos). El índice es `position: sticky` y **más
   alto que la ventana**, así que su mitad de abajo no se alcanza ni desplazándose.
   *Esto es lo que más molesta de todo el recorrido*: en los dos temas más largos, la segunda mitad
   del índice —que es el índice con el que se estudia— no está.
2. **No hay buscador dentro del tema** («Buscar en el temario» existe, pero es el del Temario: busca
   temas, no dentro de un tema).
3. **No hay modo repaso.**
4. **No hay marca de lo leído.** No lo pide el §3, pero conviene saberlo: al volver a I.1 no hay
   ninguna señal de por dónde ibas.

### 5.3 Practicar IV.7 y ver el resultado

**Lo que se ve.** «Preguntas» (1,39 s) lleva a Tests con IV.7 ya marcado y el resumen «Test de 10
preguntas de 1 tema». El test (4,57 s desde el clic de «Empezar el test») abre con la pregunta, sus
cuatro opciones y la hoja de respuestas a la derecha. **El test avanza solo al contestar** (comprobado
pregunta a pregunta). Al terminar, el resultado (0,34 s) sale con la nota «6,00» en español, la hoja
de respuestas de 10 filas y **3 enlaces «Ver en apuntes»**, uno por fallada.

**Lo que falló.**

1. **«Ver en apuntes» no lleva al apartado.** El enlace es correcto —`/temario/IV.7#osi-capas`— pero
   al llegar **la página se queda arriba**: medido dos veces, `scrollY = 0` y el apartado al que
   apunta está a **10.288 px**. No es cosa de esperar: con 1,5 s y con 4 s da lo mismo. En otra
   pasada del recorrido bajó a 1.843 px, que tampoco es el apartado. Es justo el arreglo que se dio
   por hecho en el bloque de los avisos (F16) y **no funciona con este caso**.
2. **La hoja de respuestas no se puede usar.** Los números de la hoja se dibujan como botones con
   `aria-label="Ir a la pregunta N"`, pero **no hacen nada**: en el componente no se le pasa la
   acción (`onIr`), así que el botón se pinta sin manejador. Medido: pulsar la fila 1 con el test en
   la pregunta 2 **deja la pantalla igual**. Y la ayuda del test promete «`←`/`→` recorren la hoja»:
   **esas teclas no están implementadas** (pulsar `→` no hace nada; `A`–`D`, `1`–`4` y `M` sí).
   Consecuencia: **una vez contestada una pregunta, desde la pantalla no se puede volver a ella.**
3. **Cambiar una respuesta no se puede.** La API contesta **409** con un motivo claro: «esa pregunta
   ya está respondida y el intento no se reescribe: para cambiarla, empieza otra sesión». Es una
   decisión, pero desde la pantalla el alumno ve que pulsa otra opción y **no cambia nada**.
4. **Y si se pulsa dos veces deprisa, el servidor revienta: 500.** En el registro de la API queda un
   `sqlite3.IntegrityError: UNIQUE constraint failed: attempts.session_question_id` y la respuesta sin
   cabecera de CORS, así que el navegador lo cuenta como *«blocked by CORS policy»* en vez de como
   error del servidor. Es el **único error de consola de todo el recorrido** y salió al contestar en
   el examen oficial.
5. **La hoja de respuestas de la siembra no dice nada de lo que pasó** hasta que la pregunta se
   corrige; con corrección «al responder», la casilla buena se pone verde en la hoja —eso funciona—
   pero **en la pregunta no se ve nada**, porque el test ya ha saltado a la siguiente. La corrección
   solo se lee en la hojita de la derecha.

**Lo que un alumno no entendería.** Dos cosas de texto:

- **«`[]`» como hueco de la pregunta.** En el test de IV.7 salieron **5 de 10** preguntas con el hueco
  escrito así: «En el modelo OSI, los cambios en una capa deben ser **[]** para el resto de niveles».
  Se entiende (las opciones son las palabras que rellenan el hueco) y **el banco tiene 28 preguntas
  así**, pero se lee como un error de importación. Merece un hueco de verdad (`___`) o la palabra
  entre las opciones.
- **«Puntuación directa: -0,21 (estimada)».** Con 0 aciertos y 1 fallo, la nota que se enseña es
  **negativa**. Los números cuadran con la penalización de un tercio, pero un alumno lee una nota que
  no existe.

### 5.4 Fallos → Repasar

**Lo que se ve.** Fallos (1,09 s) dice «4 preguntas falladas · 4 para repasar hoy», agrupa por tema
(I.1, I.2), ofrece «Test con mis fallos» y «Solo los de <tema>», y lista cada fallo con su enunciado,
su tema, cuándo y cuántas veces.

**Lo que falló.**

1. **Repasar no funciona con tus datos.** «Test con mis fallos» **sí hace la petición**, y la API
   contesta **409**: *«no hay ninguna pregunta que se pueda poner: de los temas elegidos, ninguna
   tiene plantilla activa con su respuesta (y las que no la tienen no se pueden corregir)»*. La
   pantalla **lo dice** («No se pudo montar…»), así que no es un botón muerto: es que **la pregunta
   que tienes fallada no se puede volver a corregir**, y con eso el «Repasar» del ciclo de estudio se
   queda sin nada que repasar. Es un problema de datos, no de pantalla, y es de los que más molestan:
   la pantalla promete «4 para repasar hoy» y luego no deja repasar ninguno.
2. **El botón «Repasar <tema>» de cada fallo no repasa: lleva a los apuntes** del tema
   (`/temario/<código>`). El nombre promete un test y lleva a la lectura. Es del §3 que se pidió
   («Fallos → Repasar»), así que la cuenta es: hay tres salidas y ninguna monta el test.

### 5.5 Simulacro: empezar, supuesto III, contestar 5, ver el reloj, abandonar

**Lo que se ve.** Simulacros (2,50 s) explica que es «el mismo número de preguntas, el mismo tiempo y
la misma penalización que el día del examen», ofrece **simulacro completo (110 preguntas · 120
minutos)** o **corto (40 · 48 minutos)**, y con el completo deja elegir **supuesto III o IV**, con la
lista de temas de cada bloque. El plan sale del perfil y se lee entero: 80 + 5 de reserva y 20 + 5,
de 0 a 50, mínimo 25, cada error descuenta 1/3.

**Lo que falló.**

1. **Montar el simulacro tarda 142,3 s** —medido con `POST /student/mock-exams`—. **Dos minutos y
   veintidós segundos** mirando una pantalla que no dice nada: a los 45 s seguía igual y el recorrido
   se rindió ahí. La sesión sí se acabó creando (106 preguntas, `draft`). Es exactamente el caso que
   avisabas: *un recorrido que funciona pero tarda 8 segundos por pantalla no está listo*; este
   tarda **142** y no hay barra, ni esqueleto, ni «esto puede tardar un minuto».
2. **No hay reloj en el test.** La sesión tiene su límite (120 minutos) y el **runner del alumno no
   pinta ningún cronómetro**: ni el tiempo que queda ni el que llevas. El cronómetro existe en el
   runner del panel, no en el del alumno.
3. **No hay forma de abandonar.** No hay botón, ni enlace, ni acción: la sesión se queda «en curso»
   para siempre si el alumno cierra la pestaña. Para el recorrido hubo que salir por la dirección, y
   se dice aquí porque el §3 pide «abandonar» y **la aplicación no ofrece esa acción**.
4. **La variante corta no la he podido medir**: pedida por API con `case_block` nulo contesta 422.
   Puede ser mi petición (el formulario de la web no manda el campo cuando no toca) y **no lo doy por
   fallo**: lo digo como lo que es, una medida que no he podido hacer.

### 5.6 Examen oficial: el INAP 2025 modelo A

**Lo que se ve.** Exámenes oficiales (0,65 s) lista **13 exámenes**, cada uno con su administración,
«Sin fecha publicada · 135 preguntas» y el botón «Hacer este examen». Dos dicen «Todavía no se puede
hacer: faltan sus respuestas». El INAP 2025 modelo A abre (0,96 s) un examen de **85 preguntas** con
su cabecera («Pregunta 1 de 85», «Examen oficial · 85 preguntas») y **avanza al contestar**. Al
terminar, el resultado (1,32 s) sale con la nota, la hoja y el desglose por parte.

**Lo que falló.**

1. **La fila del examen y el examen no dicen lo mismo: 135 preguntas en la lista, 85 al abrirlo.**
   Un alumno que elige «135 preguntas» y se encuentra 85 no sabe si le falta algo.
2. **Ningún examen tiene fecha** (13 de 13, «Sin fecha publicada»), aunque el campo existe.
3. **Y una cosa que sí está bien y conviene decirlo**: en la base hay versiones repetidas de algunos
   exámenes (19 conjuntos oficiales para 13 exámenes), y **la lista las unifica**: los 13 títulos que
   se ven son distintos, sin repetir ninguno. El deduplicado funciona.
4. **Un error de consola**: la respuesta a una pregunta se perdió con un 500 del servidor
   (`UNIQUE constraint failed: attempts.session_question_id`) que el navegador leyó como error de
   CORS. De tres respuestas, **solo una llegó** («0 aciertos · 1 fallo · 0 en blanco»).

### 5.7 Progreso

**Lo que se ve** (2,31 s): «4 tests hechos · 11 aciertos en total», el progreso por bloque con el
porcentaje escrito (Bloque I, 57 %, 4 de 7 contestadas), por tema (I.1 75 % 3 de 4; I.2 50 % 1 de 2),
«Lo que hay que repasar», «Lo que no has empezado» (**«Sin empezar»**, no un 0 % que parezca un
suspenso) y «Cómo evolucionas».

**Lo que falló.** Nada. Es la pantalla que mejor se comporta de todo el recorrido: cifras con
porcentaje, nada vacío y ningún texto raro.

### 5.8 Panel: Incidencias por banco → banco → ficha → marcar una correcta

**Lo que se ve.** Incidencias del motor (1,72 s) abre con **«Qué espera tu criterio»**, los filtros por
categoría y estado, y **157 grupos por banco**, cada uno con sus cuatro acciones («Dejar fuera del
estudio», «Marcar como “no son preguntas”», «Ver lo que tiene dentro», «Aceptar todas las derivadas»)
y su selector de decisión. «Ver lo que tiene dentro» (0,16 s) abre el banco y deja **200 enlaces «Ver
la pregunta en el banco»**. La ficha (1,17 s) abre en `/admin/preguntas?pregunta=…`, enseña las
cuatro opciones marcables y un solo botón, «Guardar la respuesta correcta». **Marcar funciona**:
cuando el recorrido marca una, la copia queda con una **versión de clave nueva** (`018e692d-…`,
`draft`) y su **evento de auditoría** `question.answer_key_marked`.

**Lo que falló.**

1. **Un grupo abre 200 preguntas de golpe**, con el enunciado entero de cada una y el detalle de la
   incidencia (fuente, apartado, lo que anotó la corrida) debajo. La página se vuelve larguísima y el
   trabajo real —despachar incidencias— se hace cuesta abajo.
2. **El texto de las incidencias se repite tres veces**: la categoría («Hueco sin material · La
   pregunta no tiene frase en los apuntes») sale en el título, en el cuerpo y otra vez en el detalle.
3. **Los contadores de la cabecera y la lista no se pueden comparar**: la pantalla tiene filtros, pero
   el número de grupos que se ve (157) no es el de incidencias de la base (959 en `open`, contadas en
   la copia).

**Lo que un alumno no entendería** (esto es panel, o sea, tú): «1 pregunta(s) 1 preguntas no tienen
ninguna frase en los apuntes que las justifique» — la concordancia se rompe (fuera del singular se ve
«10 fila con 3 celda(s) y una cabecera de 2 columna(s)», en la revisión de I.8). Son frases que
genera el servidor y que se leen raras.

### 5.9 Panel: revisión de los apuntes de IV.7

**Lo que se ve.** Apuntes (5,37 s — la pantalla más lenta de las de lectura, y aun así por debajo de
6 s) resume el estado de los 28 temas con apuntes: **26 publicados, 2 en borrador, 5 sin apuntes
escritos y 2 esperando tu decisión**, con I.4 e I.6 con su cobertura y sus incidencias sin despachar.
La revisión de IV.7 (3,45 s) abre con «Publicado · Ya pasó las dos puertas y su texto quedó
archivado», **420/432** de cobertura y las acciones «Aprobar los apuntes» / «Rechazar con este
motivo». Se ha **leído**, no se ha decidido nada.

**Lo que falló.** Los desbordes de dentro de las tarjetas a 390 px (`div.apuntes__lectura 342>325`)
que se han dicho en los tiempos: contenido que se sale de su caja, no de la página.

## 6 · Lo que no se ha podido capturar, dicho por su nombre

- **No he mirado los PNG.** Este modelo no lee imágenes. Las capturas están ahí para que las mires
  tú; lo que afirmo de ellas es lo que el guion midió en el DOM.
- **El reloj del simulacro**: no hay ningún reloj que capturar. Se dice en 5.5.
- **Abandonar un simulacro**: no existe la acción. Se dice en 5.5.
- **La variante corta del simulacro**: no he podido medirla por API (422) y no la doy por rota.
- **«Practicar este apartado», el buscador dentro del tema y el modo repaso**: no existen, así que no
  hay captura de ellos. Las tres capturas que hay son de lo que sí hay.
- **El diálogo del navegador** («¿seguro que quieres salir?»): no aparece en ningún punto del
  recorrido, ni al cerrar un test a medias.

## 7 · Las capturas contra la copia (`npm run screens -- --datos`)

El §3.2 pide, además del recorrido, pasar la herramienta de capturas **contra la copia**. Hecho:
`npm run screens -- --datos F:\temp-opofuente\f34-datos` —lanzado **desde `apps/web`**, porque el
script `screens` vive ahí y desde la raíz del repositorio falla con `Missing script: "screens"`; el
comando tal como está escrito en el documento es el que no funciona, no la herramienta—.

| | |
|---|---|
| pruebas | **66** (`acabado.spec.ts` y `screens.spec.ts`) |
| resultado | **60 pasan · 6 fallan · 12,8 minutos** |
| salida | `artifacts/screens-datos/` con **68 PNG** y `report.md` |

**Las 68 capturas están** (las de siempre más `temario-IV-7-*`, que era justo el tema que con la
siembra salía «Sin apuntes · 0 preguntas»). **Lo que falla son 6 comprobaciones del propio guion**,
escritas para la siembra:

1. **«la revisión de apuntes» (1280 y 390)**: el guion entra en un tema y exige que sus motivos lleven
   un porcentaje; con los datos reales ese tema **no tiene apuntes escritos** («Este tema todavía no
   tiene apuntes escritos: no hay nada que revisar») y sus 42 incidencias no llevan porcentaje.
2. **«test-en-curso» y «resultado» (1280 y 390)**: exigen ver la marca **«clave en revisión»**, que el
   guion provoca forzando a `dudosa` el conjunto que acaba de crear; con los datos reales las
   preguntas de esas sesiones no salen de ese conjunto y la marca no aparece.

No son fallos de la aplicación con datos reales: son **suposiciones del guion sobre la siembra**. Se
apunta porque el §3.2 las pide y porque el que vuelva a correr esto necesita saber que esas seis no
dicen nada de la aplicación.

**Y una cosa del informe que no sale bien**: `report.md` trae **4 filas de 66**. La causa está en la
propia herramienta: cuando una prueba falla, Playwright reinicia el proceso, el `afterAll` vuelve a
correr y `escribirInforme()` **borra su carpeta de filas** al terminar, así que la segunda pasada
escribe solo lo suyo. Los PNG están todos; lo que se pierde es la tabla de tiempos, accesibilidad y
palabras prohibidas de las 62 capturas anteriores. De las cuatro que sí quedaron: **0 errores de
consola, 0 violaciones de axe y 0 palabras prohibidas**.

## 8 · Lo que hay que arreglar, por lo que más molesta a quien estudia

1. **El índice de un tema largo no se puede recorrer entero.** En IV.7 no se alcanza ni el 20.º de
   25; en I.1, ni el 20.º de 21. El índice es `sticky` y más alto que la ventana. *Es lo primero
   porque es el índice con el que se estudia.*
2. **«Ver en apuntes» no baja al apartado** (medido: `scrollY = 0`, apartado a 10.288 px). La mitad
   del valor de tener los apuntes citados está en ese salto.
3. **Montar un simulacro tarda 142 s y la pantalla no dice nada.** O se acelera, o dice qué está
   haciendo y cuánto puede tardar.
4. **Repasar los fallos no funciona con los datos del propietario** (409: ninguna plantilla activa
   con su respuesta). La pantalla lo explica; lo que no hay es con qué repasar.
5. **No se puede volver a una pregunta ya contestada**: la hoja no navega (los números no hacen
   nada), `←`/`→` no existen aunque la ayuda los prometa, y cambiar una respuesta da 409.
6. **Un 500 al contestar dos veces deprisa** (`UNIQUE constraint failed:
   attempts.session_question_id`), y el navegador lo lee como error de CORS.
7. **El examen oficial no enseña el tiempo que queda** (ni el que llevas) y **no se puede abandonar**.
8. **Al abrir un test se repite el `POST /start` entre 4 y 12 veces** (medido 4-6 en varias pasadas y
   12 en otra). Una bastaría.
9. **La nota puede salir negativa** («Puntuación directa: -0,21 (estimada)»).
10. **La fila del examen oficial dice 135 preguntas y el examen tiene 85**, y **ninguno de los 13
    exámenes tiene fecha** («Sin fecha publicada» en los 13).
11. **Los «`[]`» como hueco** en 28 preguntas del banco (5 de las 10 que salieron en el test).
12. **Concordancias del panel**: «1 pregunta(s) 1 preguntas no tienen…», «10 fila con 3 celda(s)…».
13. **La bandeja del motor abre 200 preguntas de golpe** y repite cada texto tres veces.
14. **El guion de capturas depende de la siembra** (6 de sus 66 comprobaciones exigen cosas que solo
    produce la siembra) y su informe se pierde cuando una prueba falla.

Nada de esto se ha tocado: el recorrido **documenta**. Lo que salga de aquí va al bloque que le toque,
y ahí se decidirá si toca código (y entonces sí, batería de 18).
