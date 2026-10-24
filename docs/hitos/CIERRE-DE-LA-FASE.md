# La fase 3 sobre la base real: el cierre, con cifras

**Todo lo de este documento está contado en `F:\OpoFuente\datos\opofuente.sqlite3`, no en una copia.**

## La base real, antes y después

```
antes    0039 · 11.315 explicaciones (ninguna generada) · 0 tarjetas · 0 supuestos
después  0046 · 14.383 explicaciones (9.007 generadas) · 5.283 tarjetas · 18 supuestos
```

**Con copia verificada antes de cada tanda**: `20261023-103904-fc0160` (4.189,8 MB, 18.038 ficheros,
restaurable) y las copias de base de M1 y de la bandeja, todas con `integrity_check ok`.

## Los hitos

| hito | la cifra, contada en la base real |
|---|---|
| **M1** | **9.013 de 9.839 explicaciones** (91,6 %) · **las 268 de examen oficial, al 100 %** · 2,93 $ |
| **M3** | **5.283 tarjetas** en los **29** temas · mínimo 60 por tema · ninguno por debajo de 50 |
| **M5** | **18 supuestos** (9 por bloque) · **450 preguntas**, 25 por supuesto · 0,72 $ |
| **M6** | progreso **261 ms** · estadísticas **125 ms** (el listón eran 2 s) |
| **M7** | **12 decisiones del propietario** · 242 en cuarentena · 423 abiertas · rendimiento de 3,2 s a 230 ms |
| **M2** | el OCR **restaurado** · los 3 PDF de 2018 leídos · **no importados**: 51 de 100 no cuadra con la plantilla |

## Lo que hubo que construir, porque no existía

- **`tools/tarjetas.py`** — el generador de tarjetas con modelo, con la respuesta comprobada literalmente;
- **`tools/importar_fase3.py`** — el importador auditado e idempotente de lo generado en la copia;
- **`recortar_al_numero`** — quitar las preguntas sobrantes de un supuesto en vez de tirarlo;
- **`--sustituir-lo-privado`** — sustituir prosa sin cita por explicación con cita;
- **la cita por tramo** — de 0 de 20 aceptadas a 20 de 20;
- **el `psm 6` del OCR y sus dos normalizaciones**;
- **y la prueba de accesibilidad que dice el nodo, no solo la regla**.

## Los cuatro defectos reales que encontró la batería entera

1. **29 pruebas de integración en rojo** — los dobles de `redactar` no aceptaban `indicacion`.
2. **La cabeza de migraciones fijada a 0041** — obsoleta desde la 0046.
3. **El modo público servía los intentos de un banco privado** — el filtro se aplicaba donde `question_sets` no
   está unida, y ahí es un producto cartesiano.
4. **La portada**: la prueba describía `StudentHomePage` y la ruta sirve `HoyPage`.

**Y 27 fallos de accesibilidad, todos de una sola regla** — el nombre accesible tiene que contener el texto
visible **como trozo contiguo** — resueltos en nueve componentes.

## Lo que queda, y no es código

- **los cuestionarios oficiales de 2018**: el OCR lee 51 de 100, y el §2.5 manda no importar si no cuadra;
- **423 decisiones privadas de la bandeja**: los apuntes no cubren esas preguntas;
- **los supuestos en la pantalla del simulacro**: están en la base, no en la app.

**Y una espera**: la batería de las 18 puertas, corriendo, sin un solo fallo.
