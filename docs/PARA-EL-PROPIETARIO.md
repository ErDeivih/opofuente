# Para el propietario

Lo que conviene que sepas y **no** hace falta que contestes para que el trabajo siga. Lo que sí
necesita tu criterio está marcado como **«Decide tú»**.

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
