# O4 · Plan de estudio hasta el examen

Reparto determinista de los temas pendientes entre la fecha de hoy y la del examen: modo
extensivo (un tema por semana) o intensivo (dos), fase 2 de supuestos y simulacro en las últimas
semanas —hasta cuatro, pero reservando siempre tres de lectura si el calendario lo permite—, repasos
espaciados a +1, +3 y +7 semanas cuando caben en las horas declaradas, progreso por bloque y pantalla
semanal. Sin modelo, sin red y sin coste.

**Estado: implementado, NO verificado.** `task_44318c127e15`, dispatch `ctx_995fa9c5bb19`, árbol
`f4e712ce85189a91830d73d65f89c01c4b6564df6e7bd9e0580daa72e437809c` sobre HEAD `6483111` (mismo
contenido de código que el dispatch anterior `ctx_8b718f53fba9`, árbol `d9f547f5…`). La puerta
unitaria `648dc9aeae21` no llega a arrancar: el harness responde
`sandbox_image_failed: ver log local de build, sin habilitar ejecución` (no es un fallo de pytest ni
del diff; con `argon2` ausente, antes, al menos se veía el `ModuleNotFoundError`). Siete intentos
acumulados con el mismo error de entorno. Ningún test se ha podido colectar. Esta pasada es
revisión estática: no cambia el código ni las pruebas, solo documenta el límite del reparto que
faltaba y refresca la evidencia. No hay puerta de integración registrada, así que las pruebas de integración escritas
no se han ejecutado. Esta pasada corrige dos defectos de la anterior, sin cambiar el alcance:
(a) con exactamente cuatro semanas la fase 2 se comía todas las de lectura y declaraba no
planificable cualquier tema pendiente; ahora se reservan tres de lectura y una de fase 2, y con una
semana o menos no se programa simulacro (los temas se reparten igual); (b) el progreso contaba la
semana en curso como esperada desde el lunes; ahora solo cuentan las semanas ya terminadas. No se
declara ninguna prueba verde. Evidencia de la pasada anterior (mismo `code 4` por entorno):
`F:\EspacioCodigo\flujo\estado\orca-evidencias\046dfb9ddfd2794490af4b0d043a2b722f6d1717421b32b4b92b5cc6c7bac6d3.json`
(`code 4`, 28,11 s). Este documento se editó después de ese árbol: es la única diferencia con él.

## Qué he construido

- `apps/api/opofuente/domain/study_plan.py` — planificador puro y determinista. Ordena los temas
  (flojos primero, luego por número de preguntas y por código), deriva el modo y reparte las semanas.
  La **fase 2** ocupa como mucho las cuatro últimas semanas, pero `_semanas_de_fase_2` reserva antes
  tres de lectura: cuatro semanas son tres de lectura y una de fase 2; dos o tres, una de fase 2 y el
  resto de lectura; una o menos, solo lectura y sin simulacro, con aviso en `recortes`. Los
  **repasos** se citan a +1, +3 y +7 semanas y se descartan si no caben en las horas semanales.
  Los que caen más allá de la fase de lectura **se dicen**: la semana de lectura acumula en
  `recortes` el tema y el intervalo que no se pudo programar, distinguiendo «límite de fase» (hay
  fase 2) de «límite del calendario» (plan corto, sin fase 2). **El trabajo obligatorio que no cabe
  en las horas también se dice**: dos lecturas y su test (320 min) o supuesto más simulacro (210
  min) pueden pedir más de lo declarado, y la semana lo declara con los minutos que sobran en vez de
  borrar un tema o acortar el simulacro.
- `apps/api/opofuente/application/plan_service.py` — lee los temas, llama al dominio y recorta la
  semana en curso para «Hoy». Calcula el progreso comparando lo leído con lo que el plan prometía a
  estas alturas, global y por bloque (`ProgresoDeBloque`), sin repetir el umbral en la pantalla.
  Solo cuentan las semanas cuyo fin (`empieza + 7 días`) ya pasó: la semana en curso no penaliza.
- `apps/api/opofuente/infrastructure/plan_repository.py` — temas con su peso y carencia, avance por
  bloque y la fila única del plan. Los temas sin preguntas ancladas no entran en el plan.
- `apps/api/opofuente/api/routes/plan.py` — `GET /plan`, `PUT /plan`, `GET /plan/calendario` y
  `GET /plan/progreso`, con los esquemas `PlanSchema`, `SemanaSchema` (incluye `fase` y `recortes`)
  y `TareaSchema`.
- `apps/web/src/api/plan.ts`, `apps/web/src/features/plan/destino.ts`,
  `apps/web/src/pages/PlanPage.tsx` y los enlaces desde «Hoy» — cliente, destinos de cada tarea y
  calendario completo con los recortes visibles. La ruta se conserva al recargar porque el plan
  guardado se vuelve a pedir al servidor.
- Pruebas: `apps/api/tests/unit/test_study_plan.py` (dominio) y
  `apps/api/tests/integration/test_plan_api.py` (API del plan con corpus sintético).

## Cómo fluye la información

1. El alumno pone la fecha del examen, las horas semanales y el día de descanso (`PUT /plan`).
   Sin fecha guardada no hay plan: el servidor no inventa una fecha por defecto.
2. `PlanService.plan()` lee del repositorio los temas del programa activo que tienen al menos una
   pregunta anclada, con su bloque y su número de preguntas.
3. `planificar()` calcula las semanas que hay hasta el examen (`días // 7`) y reparte la fase 2 con
   `_semanas_de_fase_2`: un máximo de cuatro semanas finales, pero solo las que sobran después de
   reservar tres de lectura. Con eso deriva el modo según los temas que caben por semana de lectura.
4. Los temas que no caben se devuelven en `fuera` y `fuera_detalle`, y el plan se marca
   `planificable=False` con un motivo que los nombra.
5. Antes de pintar las semanas se deciden los repasos: cada tema leído genera citas a +1, +3 y +7
   semanas; las que caen fuera de la fase de lectura se anotan como recorte en la semana de lectura,
   y las que no caben en el presupuesto de minutos se descartan con un recorte por horas. Si las
   tareas obligatorias ya superan el presupuesto (dos lecturas y test, o supuesto y simulacro), la
   semana añade un aviso con los minutos pedidos, los declarados y los que sobran; no se quita
   ninguna tarea obligatoria.
6. La fase 2 pinta un supuesto práctico cada semana y un simulacro completo en la última. No se
   programan lecturas ni repasos dentro de ella. El supuesto y el simulacro conservan su duración
   real (90 y 120 min) aunque la semana declarada sea más corta: se avisa, no se acortan.
7. `GET /plan/calendario` devuelve exactamente el mismo plan que el `PUT`; `GET /plan/progreso`
   compara los temas con apuntes y los contestados con los que el plan daba por leídos en las
   semanas ya terminadas (no en la que está en curso), y desglosa por bloque.
8. `PlanPage` pinta cada semana con su fase, sus tareas enlazadas a la pantalla correspondiente y
   sus recortes en texto; «Hoy» reutiliza la semana en curso.

## Ficheros y migraciones

- Modificados: `apps/api/opofuente/domain/study_plan.py`,
  `apps/api/opofuente/application/plan_service.py`,
  `apps/api/opofuente/infrastructure/plan_repository.py`,
  `apps/api/opofuente/api/routes/plan.py`, `apps/web/src/api/plan.ts`,
  `apps/web/src/app/routes.tsx`, `apps/web/src/pages/HoyPage.tsx` y
  `apps/web/src/styles/global.css`.
- Nuevos: `apps/web/src/features/plan/`, `apps/web/src/pages/PlanPage.tsx`,
  `apps/api/tests/unit/test_study_plan.py` y
  `apps/api/tests/integration/test_plan_api.py`.
- Sin migración: `StudyPlanRecord` ya existía y no cambia el esquema. El plan no se guarda como
  derivación: se recalcula en cada lectura.

## Patrones y decisiones aplicadas

- **Dominio puro y determinista.** La fecha de hoy entra por parámetro; no hay `now()` ni azar
  dentro del planificador. Dos ejecuciones con los mismos datos dan el mismo plan, que es lo que
  permite compararlo con el de la semana pasada.
- **La fase 2 no se come el plan.** Se queda con las semanas que sobran tras reservar tres de
  lectura, como mucho cuatro; con una semana o menos no hay fase 2 y el calendario se dedica a leer,
  avisando de que no habrá simulacro. Los repasos nunca se cuelan en la fase 2.
- **El recorte se dice, no se esconde.** Un repaso que no cabe por horas o por fase aparece en
  `recortes` con el tema y el intervalo. Distinguir el motivo (fase 2 frente a calendario) evita
  mandar al alumno a buscar una cita que no existe.
- **El progreso se mide contra el plan, no contra el total.** «Vas bien» significa «llevas los
  temas que el plan prometía a estas alturas»; empatar cuenta como ir bien. Solo cuentan semanas
  terminadas: la semana en curso no se debe desde el lunes. La frase se compone en el servicio para
  que la pantalla no decida el umbral.
- **Un plan sin fecha no existe.** No hay fecha por defecto en el servidor; el formulario de la
  pantalla es el que pide la fecha.
- **Los temas sin preguntas no entran.** No se puede practicar lo que nadie evalúa.

## Seguridad y privacidad

- Sin llamada al modelo ni a la red: no hay coste ni salida de texto.
- Solo lectura de la base local para calcular el plan; la única escritura es la fila del plan que
  decide el alumno.
- El corpus de las pruebas es sintético y mínimo; no se copian contenidos de la oposición.
- Los originales de `F:\EspacioCodigo\opofuente` no se han tocado.
- El contenido guardado sigue siendo dato: se reparte, no se ejecuta.

## Puertas ejecutadas y resultado

El árbol incluye trabajo ajeno sin commitear de A2/O2/O3 que **no** forma parte de este cambio y se
conserva intacto.

- `uv run --frozen pytest apps/api/tests/unit -q` (puerta `648dc9aeae21`): **no ejecutada**. Los
  siete intentos acumulados sobre este mismo contenido devuelven
  `{"ok": false, "error": "sandbox_image_failed: ver log local de build, sin habilitar ejecución"}`:
  pytest ni arranca, así que no hay salida que atribuir al diff. **Es capacidad del harness, no un
  fallo de las pruebas**, y no se reintenta en bucle. En la pasada anterior la puerta llegaba a
  cargar `conftest.py` y fallaba por `ModuleNotFoundError: No module named 'argon2'` (evidencia
  `F:\EspacioCodigo\flujo\estado\orca-evidencias\046dfb9ddfd2794490af4b0d043a2b722f6d1717421b32b4b92b5cc6c7bac6d3.json`,
  `code 4`, 28,11 s, `tree_hash d95cc1c7…`). En ningún caso hay evidencia de que las pruebas nuevas
  pasen.
- Las pruebas de integración de `test_plan_api.py` **no se han ejecutado**: no hay puerta de
  integración registrada para este proyecto y el worker no dispone de shell. Se entregan escritas,
  sin declararlas verdes.
- La puerta completa `scripts/gates.ps1` (`9df85043f3a0`) no se ha ejecutado: exige un worktree
  desechable propio y no se puede correr desde el workspace de trabajo.

## Prueba manual

Con el entorno completo (`argon2-cffi` instalado) y una copia autorizada de datos:

```powershell
uv run pytest apps/api/tests/unit/test_study_plan.py -q
uv run pytest apps/api/tests/integration/test_plan_api.py -q
```

Después, con la API y la web en desarrollo (`./scripts/dev.ps1`):

1. Abrir «Plan», poner una fecha de examen a ocho semanas y 40 h semanales.
2. Comprobar que salen cuatro semanas de lectura y cuatro de fase 2, con un supuesto por semana y el
   simulacro al final.
3. Cambiar la fecha a cuatro semanas: deben salir tres de lectura y una de fase 2, con los temas
   pendientes dentro del plan (no «fuera» por la reserva).
4. Cambiar la fecha a una semana: una sola semana de lectura, sin fase 2 ni simulacro, con un
   recorte que lo dice y los temas repartidos en esa semana.
5. Comprobar que la semana 1 avisa de que el repaso `+7` cae en la fase 2.
6. Recargar: el calendario sigue ahí y coincide con el que devolvió el `PUT`.
7. Bajar las horas a 3: los repasos que no caben aparecen como recorte por horas y la semana no
   supera el presupuesto.
8. Con siete temas y seis semanas (modo intensivo) y 5 h semanales: la semana de lectura avisa de
   que pide 320 min frente a 300 y no borra ninguno de los dos temas.
9. Con una fecha a ocho semanas y 2 h semanales: la última semana avisa de que supuesto y simulacro
   piden 210 min frente a 120, y las tareas conservan 90 y 120 min.
10. Entrar el lunes de la primera semana: «progreso» debe dar 0 esperados y «vas bien»; el martes de
    la segunda, solo la primera semana cuenta como esperada.

## Limitaciones conocidas

- Los minutos por tarea (150 por tema, 20 por test, 30 por repaso, 90 por supuesto, 120 por
  simulacro) son una estimación declarada, no una medida del alumno.
- El aviso de horas no impide un plan que no cabe: enseña el exceso y deja decidir si se amplían
  las horas o se acepta. No redistribuye temas ni recorta el simulacro a la baja.
- «Leído» significa «tiene apuntes guardados», no «lo ha abierto»: no hay registro de lectura.
  «Practicado» significa «ha contestado al menos una pregunta de ese tema».
- El plan reparte **todos** los temas con al menos una pregunta anclada, no solo los pendientes: al no
  existir un estado de lectura por tema, el planificador no puede saber que un tema ya está cubierto y
  lo volverá a citar. Es un límite conocido y deliberado (no se inventa estado de lectura); si algún
  día se registra lectura real, `plan_repository.temas()` es el punto de filtrado.
- La fase 2 es fija en su máximo de cuatro semanas y en el mínimo de tres de lectura: no se adapta a
  exámenes muy largos o muy cortos más allá de existir o no. Con una semana o menos se avisa de que
  no hay simulacro, pero no se ofrece un plan alternativo.
- La semana en curso no cuenta como esperada hasta que termina: el progreso va por detrás del
  calendario los primeros días de cada semana. Es deliberado para no penalizar el lunes.
- Los repasos que caen en la fase 2 no se recolocan dentro de ella: se avisa y se dejan fuera. Es
  una decisión de producto, no un olvido.
- El plan se recalcula en cada lectura: si cambian los temas o sus preguntas, el calendario cambia
  sin historial de planes anteriores.
- Las pruebas de integración dependen de un corpus sintético insertado por SQL; no cubren los
  perfiles sembrados reales.

## Qué se rompe si cambias X

- Cambiar `INTERVALOS_REPASO`, `FASE_2_SEMANAS`, `SEMANAS_DE_LECTURA_MINIMAS` o los minutos por
  tarea cambia el calendario que el alumno ya vio y las pruebas de dominio.
- Cambiar el criterio de `_orden` cambia qué temas se quedan fuera; es la decisión de producto más
  visible del planificador.
- Quitar el aviso de `recortes` vuelve a esconder repasos que no existen: el alumno buscaría una
  cita que el plan no ha programado. Lo mismo con el aviso de horas: sin él, la semana promete más
  minutos de los declarados y nadie lo ve.
- Volver a acortar supuesto o simulacro al presupuesto semanal cambia la duración del examen
  simulado sin decirlo y rompe la prueba de la fase 2.
- Cambiar `leido_y_practicado()` o `avance_por_bloque()` cambia el significado de «vas bien» sin
  tocar la pantalla. Volver a contar la semana en curso adelanta el progreso y vuelve a marcar en
  rojo el lunes.
- Apagar `PRAGMA foreign_keys` para sembrar pruebas rompería la integridad: el listener de `db.py`
  lo vuelve a activar en cada conexión.

## Qué criticaría un revisor senior

- Que la estimación de minutos es arbitraria y no se contrasta con el ritmo real del alumno.
- Que «leído» se mide por existencia de apuntes y no por lectura: el progreso puede ir «bien» sin
  que el alumno haya abierto el tema.
- Que la fase 2 fija en cuatro semanas (con tres de lectura garantizadas) no se justifica con
  evidencia y podría no encajar en convocatorias con calendarios atípicos.
- Que los repasos descartados por la fase 2 se avisan pero no se ofrecen como alternativa dentro de
  la fase 2 (por ejemplo, un repaso corto antes del supuesto).
- Que las pruebas no se hayan podido ejecutar en este turno porque el harness no arranca la imagen:
  la primera tarea pendiente es correr unitarias e integración con `argon2-cffi` presente y la puerta
  completa en worktree desechable, sobre este árbol exacto.
- Que el test de integración siembra el corpus por SQL: verifica la API, pero no el camino real de
  importación de perfiles.
