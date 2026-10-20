# Estado de la fase 3 — 20 de octubre de 2026

**Un folio. El detalle, en `docs/hitos/M0.md` y `docs/hitos/M1.md`.**

## Dónde está el árbol

```
main = 89903f4 · las 18 puertas en verde (en tramos: 1-8 batería · 9 494 pruebas · 10-17 · 18 E2E 93/93)
la puerta de codificación: SIN MOJIBAKE · 0 marcadores de conflicto · 1.352 ficheros mirados
gasto: 0 $ de 30        base real: intacta (a0a21413…, 2.748.612.608 B, cero escrituras)
```

## Qué está hecho

**M0 — cerrado.** Las tres ramas (F37, F39, F40) dentro de `main` con las 18 puertas detrás; **66 capturas
con datos reales** en `artifacts/recorrido-M0/`; **la tabla de los 20 defectos con 21 cifras medidas**. Y
**la puerta de codificación**, que en su primera pasada encontró **13 líneas de mojibake en el `.gitignore`
de `main`** — un defecto que ninguna otra puerta ve.

**M1 — seis de siete piezas.** La migración `0041` (la explicación lleva **cita literal** y **ancla**), las
**cuatro comprobaciones mecánicas** (cita en el apartado, letra = clave, nada sobre exámenes, 2-5 frases),
**`validar_lote`** (sin ancla no se llama al modelo, lo rechazado dice sus motivos), **el doble a coste
cero**, **el cliente del modelo**, **la cita en las tres correcciones** (alumno, sesión, resultado) y **las
dos pantallas**: la cita bajo la explicación en el test y en el Resultado. Y **el `--dry-run`** del
generador, que lee 20 preguntas con ancla de la copia y no gasta nada.

## Qué falta, y por qué

| qué | por qué no está |
|---|---|
| **el ensayo (20 preguntas → la cifra del coste)** | **`DEEPSEEK_API_KEY` no está en el entorno.** Es UNA llamada. Con ella sale `11.147 × coste_por_pregunta` frente a los **12 $** del hito. **Escrito y en seco, funcionando.** |
| **la bandeja de revisión con teclas** | **Decisión mía, reversible**: **hoy no hay una sola explicación generada que revisar**. Se hace **cuando las haya**, con el ensayo. Es pantalla nueva y su API. |
| **las capturas de M1** | **Dependen de lo anterior**: hoy la pantalla enseña las 11.315 privadas, **sin cita**, y no hay nada nuevo que fotografiar. |

## Los números del terreno, medidos hoy sobre la copia

```
anclas totales                       11.179
con clave servible y apartado escrito  10.027   ← el trabajo de verdad
  covered                             10.059
  doubtful                               860
  conflict                               260
explicaciones privadas que ya hay     11.315   ← son material, no se copian
```

## Lo que hace falta del propietario, y es una cosa

**`DEEPSEEK_API_KEY` en el entorno.** Con eso, **M1 se cierra en una corrida**: el ensayo da la cifra,
si cabe en 12 $ se generan las explicaciones, se capturan las pantallas y la bandeja se abre con algo
dentro.

## La deuda de método, dicha

**123 rondas para dos de nueve hitos.** **El 40 % se fue en arreglar mi propia herramienta** (mojibake,
envoltorios que partían `def`, `Replace` que no cambiaban nada) **y en descubrir que cada dato tiene dos
o tres caminos paralelos** (la corrección del alumno / de la sesión / del resultado; el contrato generado /
las interfaces escritas a mano). **La batería entera son 90 minutos** y se come ocho o diez rondas.
---

## Actualización al cerrar la ronda 161

**Lo que se ha hecho desde el folio original** (que era de la ronda 124):

**M1 — la bandeja de revisión está construida entera**, y son cuatro eslabones, **cada uno commiteado y con
las puertas verdes**:

| eslabón | dónde | commit |
|---|---|---|
| la consulta | `question_repository.explanations_pending` | `197f527` |
| el servicio | `QuestionService.explanations_pending` | `971e997` |
| la fila de la bandeja | `ExplanationTrayItemSchema` | `c303722` |
| la ruta | `GET /explanations/pending` | `e9f84ee` |

**Su prueba está escrita y PASA**, pero **no vive en el árbol**: **`mypy` pide el `type: ignore` en la línea
del `execute` y `ruff format` lo mueve al partir la llamada**, y **el helper que lo arreglaba cambia la
semántica del `INSERT`**. **Está todo en `docs/hitos/M1.md`**, con los tres tropiezos resueltos y el cuarto
diagnosticado.

**M3 — tres piezas dentro y probadas**, y una medida que descarta una vía:

```
domain/tarjetas.py        la tarjeta desde una forma regular · 6 pruebas
   y su cifra: 15 tarjetas de 19.316 hechos (0,1 %) — la vía sin modelo es un callejón
domain/repaso.py          SM-2 en el dominio, sin dependencias nuevas · 5 pruebas
domain/cola_del_dia.py    tarjetas y fallos entrelazados, tope que recorta la mezcla · 5 pruebas
```

**M2 — el paso 4 hecho**: **copia verificada con SHA-256 idéntica** (`A0A21413…C5AFF8`), `integrity_check`
**ok**, `foreign_key_check` **0 filas**, y **la política de dos copias escrita con sus cuatro
comprobaciones**. **Y el paso 3 medido**: **1.103 preguntas en cuarentena, 16 necesitan el modelo, y
cuestan 0,0114 $** — **dos llamadas**.

**Y la batería, corrida entera en la ronda 146**: **1-8 en la corrida** (la 7 con **824 pruebas de
integración**), **9 sola con 494**, **10-17 a mano**, **18 con 93 de E2E**. **18/18 con todo lo de hoy
dentro.**

## Lo que sigue esperando al propietario, y son dos cosas

1. **`DEEPSEEK_API_KEY` en el entorno** — **cierra el ensayo de M1, las 16 claves de M2 (un céntimo) y las
   tarjetas de M3**;
2. **los nombres de los tres escaneos del INAP** — **para el paso 2 de M2**.

**Todo lo demás que falta no depende de nadie**: **la prueba de la bandeja** (con el choque
`mypy`/`ruff` resuelto) y **su pantalla** (`TopicReviewPage` con otro mapa de teclas).

**Gasto: 0 $ de 30. Base real: intacta, `A0A21413…C5AFF8`, cero escrituras en toda la sesión.**
