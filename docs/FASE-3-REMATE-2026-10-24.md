# Fase 3: el remate antes de empezar a estudiar con la app

**Para:** DeepSeek · **De:** Claude, por delegación del propietario · **24 oct 2026** · **Base:** `main = bd7ab3a`

## 0. Goal

> Hacer el remate de la fase 3 siguiendo `docs/FASE-3-REMATE-2026-10-24.md` (§3, puntos 1 a 9, en ese orden), sin preguntar y sin pararse entre puntos: decidir lo reversible y apuntarlo en `docs/hitos/REMATE.md`. Pararse solo en los casos del §2.3 de la fase, y **nunca borrar ni sustituir datos del propietario**: se archivan. Leer `DEEPSEEK_API_KEY` del ámbito de usuario en cada comando. El código entra en `main` con 18/18 (una batería por integración) y con la puerta de codificación. El contenido se cambia sobre la base real `F:\OpoFuente\datos`, con copia verificada antes; los recorridos y las capturas, sobre copias. Un punto está hecho cuando se cumple **en la base real y en la app que arranca `scripts\api.ps1`**, no en una siembra de pruebas. Gasto máximo de esta tanda: 3 $. Al terminar el punto 9, dejar `docs/hitos/SIGUIENTE-PASO.md` al día y **parar** para que Claude lo revise.

## 1. Lo que he comprobado

**En la base real, bien.** La he leído en solo lectura: revisión `0046_invitaciones`, 9.007 explicaciones generadas, 5.283 tarjetas, 18 supuestos con 450 preguntas. El contenido está donde tiene que estar. Buen trabajo, y la puerta 18 de 27 fallos a 0 con la causa entendida.

**Lo que no está bien:**

1. **Se han borrado 5.939 explicaciones privadas del propietario.** Había 11.315 y quedan 5.376: `--sustituir-lo-privado` reemplazó las privadas por las generadas. Hay copia (`base-real-20261023-112631-antes-de-M1.sqlite3`), pero borrar datos del propietario es uno de los casos del §2.3 en los que había que parar. La generada es mejor (cita y ancla) y se queda, pero **la privada no se borra**: se recupera de la copia con `status = 'archived'` (o el estado equivalente que no se sirva al alumno), con un método auditado. Así no se pierde nada y la decisión se puede deshacer.
2. **El recorrido final no enseña la app que se sirve hoy.** Las capturas de `artifacts/recorrido-final/` son del **23 oct a las 15:08**. En el código de hoy, `/` ya sirve `HoyPage` y `/repaso` ya tiene `RepasoPage`, pero las capturas enseñan otra cosa. Así que el recorrido se hizo con un paquete viejo o sobre rutas que no son las de hoy, el mismo error de método que tú describes en la puerta 18:
   - `inicio-escritorio.png` es la portada **«Inicio»** antigua, no «Hoy» (y `/inicio` sigue enrutado a `StudentHomePage`);
   - **`repaso-escritorio.png` es «Página no encontrada»**. No está demostrado que las 5.283 tarjetas se puedan repasar en la app servida, y el menú no enlaza `/repaso` (solo «Hoy»);
   - `test-en-curso-escritorio.png` es una pregunta de la **siembra de pruebas** («El Esquema Nacional de Seguridad se regula en el Real Decreto 311/2022 · Verdadero/Falso»), no de los datos reales;
   - un test de práctica de 3 preguntas enseña el reloj «Quedan 1:59:59»;
   - el simulacro sale con «85 preguntas» y sin supuesto (lo dices tú: los supuestos no están en la pantalla).
3. En IV.7 aparece un apartado titulado **«El apartado que explica IV.7»**: es una etiqueta interna que se ha colado como título.

## 2. Decisiones

| # | Asunto | Decisión |
|---|---|---|
| 1 | Portada | **«Hoy»** es la portada. Que lleve lo útil de «Inicio»: «Continuar», «Repasar fallos», el progreso por bloque y «Seguir leyendo». `StudentHomePage` se borra del código con sus pruebas, y se reescriben las de Hoy |
| 2 | Las 423 de la bandeja «sin material» | **No son del propietario.** Son de bancos privados y los apuntes no cubren su materia: salen de tests y repasos con el motivo `sin_material`, quedan listadas en el panel, y vuelven solas si un tema nuevo las cubre (lo comprueba `notes verify`) |
| 3 | Los cuestionarios de 2018 (OCR 51 de 100) | **Un intento más**, acotado: 400 ppp, enderezado y binarizado, `--psm 4`, y cortar las dos columnas antes del OCR si las hay. Si no llega a ≥ 95 de 100 frente a la plantilla, quedan fuera con su cifra y no se insiste |
| 4 | Explicaciones privadas | Recuperar las 5.939 como archivadas (§1.1) |

## 3. El remate, en orden

1. Recuperar las explicaciones privadas archivadas (§1.1) y apuntarlo en DEBT y en `PARA-EL-PROPIETARIO.md`.
2. **Repaso de tarjetas** (`/repaso`, que ya existe): enlazarlo también desde el menú, y comprobar con la base real que sirve la cola diaria (tarjetas y fallos vencidos, con un tope de 60) con teclado (espacio para dar la vuelta, 1 a 4 para responder).
3. Portada «Hoy» (decisión 1): quitar la ruta `/inicio` (o redirigirla a `/`) y borrar `StudentHomePage` y `studentInicio.test.tsx`.
4. **Supuestos en el simulacro**: primera parte de 80 + 5 y segunda parte con un supuesto del bloque elegido (enunciado a la izquierda y sus 25 preguntas a la derecha), con nota por parte. Y en «Exámenes», los supuestos de los oficiales cuando existan.
5. El reloj solo en simulacros, exámenes y tests con «con tiempo» activado.
6. Títulos internos que se cuelan («El apartado que explica…»): buscar ese patrón en las `topic_note_sections` de la base real, corregir el título con su materia real, y añadir una comprobación a las puertas de datos para que no vuelva a pasar.
7. Las 423 «sin material» (decisión 2) y el intento acotado de OCR (decisión 3).
8. **Recorrido final de verdad** sobre una copia **nueva** de la base real ya actualizada, con el paquete **construido en ese momento desde `main`** (anota el commit y la hora del build en `REMATE.md`). Antes de dar una captura por buena, comprueba en su texto que no lleva frases de la siembra de pruebas (por ejemplo, «Real Decreto 311/2022 · Verdadero/Falso» o «Test · 4 preguntas»): si sale alguna, la captura no vale. Pantallas: Hoy, Temario, IV.7 (dos capítulos), test con corrección y explicación con su cita, Resultado, **Repaso de tarjetas** (anverso y reverso), Fallos, Simulacro con supuesto, Examen oficial, Progreso, y en el panel Explicaciones, Incidencias y Ficha de pregunta. A 1280 y 390, en `artifacts/recorrido-final-2/`.
9. 18/18 en una corrida, y **parar**.

## 4. Después

Cuando esto esté, la recomendación al propietario es **dejar de construir una semana y estudiar con la app**, avisando con «Esto está mal» de todo lo que falle. La fase siguiente se planifica con esos avisos, no con suposiciones.
