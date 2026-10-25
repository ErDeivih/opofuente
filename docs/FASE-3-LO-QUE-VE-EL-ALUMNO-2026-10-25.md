# Fase 3: lo que ve el alumno, con tu base

**Para:** DeepSeek · **De:** Claude, por delegación del propietario · **25 oct 2026** · **Base:** `main = d23edc7`
Manda sobre `FASE-3-REMATE-2026-10-24.md`.

## 0. Goal

> Dejar la zona del alumno usable con la base real siguiendo `docs/FASE-3-LO-QUE-VE-EL-ALUMNO-2026-10-25.md` (§2, puntos 1 a 9, en ese orden), sin preguntar y sin pararse entre puntos: decidir lo reversible y apuntarlo en `docs/hitos/LO-QUE-VE-EL-ALUMNO.md`. Pararse solo en los casos del §2.3 de la fase, y nunca borrar ni sustituir datos del propietario: se archivan. Leer `DEEPSEEK_API_KEY` del ámbito de usuario en cada comando. El código entra en `main` con 18/18 y con la puerta de codificación. El contenido se cambia sobre la base real `F:\OpoFuente\datos`, con copia verificada antes; el recorrido, sobre una copia y con el paquete construido en ese momento desde `main`. **Una captura solo vale si su texto sale de la base real**, y eso lo comprueba un programa, no tú. Gasto máximo: 4 $. Al terminar, dejar `docs/hitos/SIGUIENTE-PASO.md` al día y parar para que Claude lo revise.

## 1. Lo que he comprobado

**Bien:** el esquema está en `0047`. Hay 5.939 explicaciones privadas archivadas, 5.376 privadas vivas y 9.007 generadas, y ninguna pregunta tiene dos explicaciones vivas. `/inicio` ya no existe, `Repaso` está en el menú, el reloj de la práctica está arreglado y el arreglo de `/api/v1` en `apiFetch` es un hallazgo importante. 18/18 y 0,05 $. Buen trabajo.

**Lo que no está bien:**

1. **El recorrido vuelve a enseñar la siembra.** En `artifacts/recorrido-final-2/`, `test-en-curso` y `resultado` enseñan «El Esquema Nacional de Seguridad se regula en el Real Decreto 311/2022 · Verdadero/Falso», «El modelo TCP/IP tiene cuatro capas» y «Test · 4 preguntas». Es la frase que el remate decía que invalidaba la captura. En la base real hay **0** preguntas con ese texto. Así que esas capturas salen de la siembra de la puerta 18, no de tu base, y el «85 de 85» no demuestra que un test real con explicación y cita funcione.
2. **El repaso sirve 9 tarjetas de 5.283.** Las 5.274 generadas siguen en `status = 'draft'` y solo se sirven las 9 estructurales («Quedan 9 de 9»). M3 no ha llegado al alumno.
3. **La pantalla de repaso:** en la captura se ve la respuesta («443») mientras pide «Pulsa espacio para ver la respuesta». Y las etiquetas de los botones salen pegadas: «Otra vezno me salía», «Difícilcon esfuerzo», «Bienme salía», «Fácilsin pensar».
4. **«Hoy» no cumple la decisión 1 del remate.** Sin fecha de examen solo hay un formulario sin estilo, con los campos pegados al texto. No están «Continuar», «Repasar fallos», «Repaso (N para hoy)», el progreso por bloque ni «Seguir leyendo».
5. **El simulacro enseña el enunciado del supuesto en la primera parte.** Sale al lado de la pregunta 1 («¿En qué parte de la CE se regula la nacionalidad española?»), y la hoja no separa las dos partes.
6. **Las 450 claves de los supuestos son de una sola pasada del modelo, sin contraste.** La fase pedía que un segundo modelo los respondiera a ciegas, con ≥ 90 % de coincidencia. Como la clave de la generación se perdió, ahora no hay nada contra lo que comparar.

## 2. El trabajo, en orden

1. **Tarjetas al alumno.**
   - Pasa a `active` las generadas que cumplan, comprobado por programa: la respuesta aparece literalmente en el hecho, tiene ≤ 25 palabras, la pregunta no la contiene y no hay otra tarjeta igual en el tema (frente normalizado).
   - Las que no cumplan se quedan en `draft` con su motivo.
   - Saca 50 al azar y haz que el modelo las responda a ciegas con el hecho delante. Si coincide < 90 %, para y apúntalo.
   - **Tope de nuevas**: 20 tarjetas nuevas al día como máximo (configurable en Ajustes), para que el primer día no salgan 5.000.
   - Informe: cuántas quedan activas por tema.
2. **Pantalla de repaso.** La respuesta oculta hasta pulsar espacio o el botón «Ver la respuesta». Los botones de nota con espacio y en dos líneas («Otra vez» / «no me salía»), deshabilitados hasta dar la vuelta. Al terminar, un resumen: hechas, a repasar mañana y volver a Hoy.
3. **Fallos vencidos en la cola del día**, como dejaste escrito: las preguntas falladas que vencen hoy entran en el repaso como pregunta de test, con su explicación al corregir. El tope de 60 sigue valiendo para las dos cosas juntas.
4. **«Hoy», de verdad**, con o sin plan:
   - arriba, «Continuar» (el test o la lectura a medias) y «Repaso: N para hoy»;
   - después, «Repasar fallos (N)», «Seguir leyendo: tema X» y el progreso por bloque (cuatro barras);
   - el formulario del plan, en una tarjeta con sus etiquetas encima de cada campo y el botón activo, como «Pon la fecha del examen y te reparto los temas».
   - Con el estilo del resto de la app, no HTML sin estilo.
5. **Simulacro en dos partes.**
   - La hoja separa «Primera parte» y «Segunda parte · Supuesto».
   - El enunciado del supuesto sale **solo** en las preguntas de la segunda parte. En el móvil, plegable encima de la pregunta.
   - En el resultado, la nota de cada parte y la total, como dejaste pendiente.
6. **Contraste de las claves de los supuestos.**
   - Una segunda pasada independiente: otra plantilla de instrucciones, las opciones barajadas y sin ver la primera clave.
   - Si coinciden, la clave se queda. Si no, la pregunta sale del supuesto y entra una reserva (si no hay reserva, el supuesto se queda con menos preguntas y se dice cuántas).
   - Un supuesto con < 90 % de coincidencia pasa entero a cuarentena.
   - Informe con el porcentaje por supuesto.
7. **El guardián de las capturas, por programa.**
   - El recorrido extrae el texto visible de cada pantalla (`innerText`) y lo compara con una lista de frases de la siembra, que se saca automáticamente de los fixtures de la puerta 18.
   - Si aparece una, la captura falla y el recorrido no termina en verde.
   - Además, el test del recorrido se monta con preguntas de un tema real elegido de la base (por ejemplo, IV.7), y la captura del resultado tiene que enseñar una **explicación con su cita**.
8. **Recorrido de nuevo** en `artifacts/recorrido-final-3/`, a 1280 y 390:
   - Hoy sin plan y Hoy con plan;
   - Repaso: anverso, reverso y resumen;
   - test real en curso;
   - resultado con explicación y cita;
   - Fallos;
   - simulacro, primera y segunda parte;
   - resultado del simulacro con nota por parte;
   - Temario e IV.7;
   - Progreso.
   Anota el commit y la hora del build.
9. 18/18 en una corrida, y **parar**.

## 3. Después

Con esto, la recomendación al propietario sigue siendo la misma: una semana estudiando con la app y avisando con «Esto está mal». La fase siguiente (diseño visual con v0/Stitch y despliegue) se planifica con esos avisos.
