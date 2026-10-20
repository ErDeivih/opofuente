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