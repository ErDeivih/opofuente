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

---

## Para la sesión siguiente: por dónde se empieza

**El §4 bis lo dice y hoy se ha cumplido**: **el estado vive en los ficheros**. **Estos cuatro se leen en
quince minutos y bastan para continuar sin releer nada:**

1. **este folio** — qué está hecho y qué falta;
2. **`docs/hitos/M1.md`** — la bandeja, con los **cuatro muros** de su prueba y el diagnóstico del quinto;
3. **`docs/hitos/M2.md`** — la copia verificada, la política de dos copias y la cifra de la cuarentena;
4. **`docs/hitos/M3.md`** — la tarjeta, SM-2, la cola del día, **y el 0,1 % que descarta la vía sin modelo**.

### Lo primero, en este orden

1. **La prueba de la bandeja** (M1). **La siembra está resuelta y escrita**: `seeded_client`, el texto
   legible con `kind="questions"`, y la privada en una opción. **Lo que falta es un helper del árbol que
   envuelva las llamadas de SQLAlchemy** —una sola, con el único `type: ignore` en una línea corta— **y
   que `ruff format` no pueda mover**. **Sin eso, el sexto intento fallará igual que el quinto.**
2. **La pantalla de la bandeja** (M1): **`TopicReviewPage` con otro mapa de teclas**
   (`{ a: aprobar, e: editar, r: regenerar, j: siguiente, k: anterior }`). **Sus tres guardas de teclado ya
   están escritas y sirven tal cual.**
3. **Con la clave**: **el ensayo de 20 preguntas** (`uv run python -m opofuente.tools.explicar_preguntas
   --de-verdad --limite 20`), **las 16 claves en cuarentena** (`claves_derivadas --derivar`, **0,0114 $**)
   **y las tarjetas de M3**.
4. **Con los nombres de los tres escaneos**: **el OCR de M2**.

### Las reglas que hoy han costado rondas, para no repetirlas

- **La base del propietario no se escribe.** `A0A21413…C5AFF8`. Copia verificada al empezar cada tanda.
- **Ningún commit con una puerta en rojo.** Ni «ya lo arreglo después».
- **Las líneas de código no se editan por índice calculado.** Se lee la línea y se sustituye.
- **Antes de decir «esto es nuevo», buscar la pantalla o el método.** **Cinco veces hoy estaba ya.**
- **Antes de creer una cifra del plan, medirla.** El 0,1 % de las tarjetas y el céntimo de las claves solo
  se supieron midiendo.

---

## Cierre de la sesión: las cifras verificadas (rondas 178-179)

**Todo lo de abajo está corrido, no supuesto:**

```
main = 83b1322
ruff:        All checks passed            ·  645 ficheros
ruff format: 645 ya formateados
mypy:        Success — 275 ficheros
unitarias + preguntas + alumno + estudio:  1.065 pruebas en verde (6:11)
batería entera (ronda 146):  1-8 en la corrida, 9 sola (494), 10-17 a mano, 18 con 93 de E2E
puerta de codificación:  SIN MOJIBAKE · 0 marcadores · 1.362 ficheros
base del propietario:  A0A21413…C5AFF8 · 2.748.612.608 B · CERO ESCRITURAS
gasto:  0 $ de 30
```

**Y lo que se ha añadido desde el handover de la ronda 163**: **`filas` y `ejecutar`** (la puerta única a
SQLAlchemy en las pruebas, con su sonda), **el tool `tarjetas_estructurales`** con su cifra —**14 de
19.316, y la tarjeta incontestable fuera**—, **la cabecera de M0 corregida** (decía «en curso» y llevaba
cerrado sesenta rondas) y **el mapa de los seis muros de la prueba de la bandeja**.

## Los cuatro bloqueos, y son todos del propietario

| # | qué | qué desbloquea |
|---|---|---|
| 1 | **`DEEPSEEK_API_KEY` en el entorno** | el ensayo de M1 · las 16 claves de M2 (0,0114 $) · las tarjetas de M3 |
| 2 | **los nombres de los tres escaneos del INAP** | el OCR de M2 |
| 3 | **la decisión de DEBT-035** (cuál de los dos conjuntos duplicados es el bueno) | cuatro repasos que apuntan mal |
| 4 | **el material de DEBT-036** (los seis exámenes de promoción interna) | seis exámenes que no se pueden montar |

**Ninguno es código.** **Los tres primeros son una línea cada uno; el cuarto es material.**

## Y lo que queda de código, que no necesita a nadie

**La prueba de la bandeja** — **la vía es la de la API (pasó seis veces), con las cinco piezas ya escritas
en `M1.md`** — **y su pantalla** (`TopicReviewPage` con `{ a, e, r, j, k }`). **Las dos son de una sesión
con el fichero delante.**

---

## El árbol se perdió y se recuperó (20-oct, rondas 214-216)

**Los árboles de `F:\temp-opofuente\opofuente-*` perdieron su `.git` y todos los ficheros de primer nivel
menos `apps`.** **No fue un fallo de código**: **algo vació esos directorios** —no se sabe qué— **mientras la
sesión se interrumpía dos veces seguidas.**

**Lo que se perdió**: **los ficheros de enlace de los worktrees y, con ellos, su vista del árbol**.
**Lo que NO se perdió**:
- **el repositorio, que está en `F:\EspacioCodigo\opofuente`**, con **`main = 63fad50`** y **los 105 commits
  de la sesión dentro**;
- **y la base del propietario**, con la misma huella del primer minuto.

**Cómo se recuperó, y son dos comandos**:

```
git -C F:\EspacioCodigo\opofuente worktree prune
git -C F:\EspacioCodigo\opofuente worktree add F:\temp-opofuente\opofuente-restaurado main
```

**Y después, porque no se commitea**: `uv sync --frozen` y `npm ci`.

## El árbol que hay que usar a partir de ahora

```
F:\temp-opofuente\opofuente-restaurado     ← el bueno
F:\EspacioCodigo\opofuente                 ← el repositorio (de aquí salen los worktrees)
F:\temp-opofuente\opofuente-main y demás   ← huérfanos; NO usar
```

**Y el aviso que queda para siempre**: ***lo que se commitea se recupera en dos comandos; lo que no, se
reinstala.*** **Hoy el trabajo de 216 rondas volvió en dos minutos porque cada pieza estaba commiteada.**

## Lo que la recuperación NO trajo: las capturas de M0 (ronda 223)

**Los cinco documentos de hito están** (`M0.md` 31 KB, `M1.md` 60 KB, `M2.md` 8 KB, `M3.md` 6 KB y este
folio 11 KB) **y `artifacts/recorrido-M1/README.md` también** — **lo que está en git, está**.

**Y `artifacts/recorrido-M0/` NO está**: **sus 66 PNG (33 MB) se perdieron**, **y es lo correcto**: **estaban
en `.gitignore` a propósito** — **33 MB de imágenes regenerables no entran en el repositorio** —, así que
**la recuperación no podía traerlos**.

**Se regeneran, y el comando está escrito**: `npm run screens --workspace @opofuente/web -- --datos <copia
verificada>`, **que deja los PNG en `artifacts/screens-datos` y de ahí se copian a `recorrido-M0`**.

**La regla que esto confirma, y no es nueva**: ***lo que se ignora en git es lo que hay que poder
regenerar***. **Las capturas lo son —un comando—; el `.venv` y `node_modules` también —dos comandos—; y el
trabajo de la sesión no lo era, y por eso estaba commiteado.**

## La batería sobre el árbol restaurado, con sus dos rojos explicados (rondas 217-227)

```
1-6   verdes (ruff · format · mypy 275 · eslint · tsc · 993 unitarias)
7     824 passed, 1 failed  ← MI prueba, y el fallo era mío: pedía ?limit=1 a una ruta que ya no
                              tiene parámetro de consulta (se lo quité para que no metiera el 422
                              en el contrato). ARREGLADO y verificado sola: 1 passed (084be2e).
8     contrato (export --check + contracts:check)     ✓
9     test:web · 55 ficheros · 494 pruebas            ✓
10-12 contrato, uv build, build:web                   ✓
13-16 migración (0041) · esquema · siembra · idempotente  ✓
17    FALLO: dos fuentes oficiales han cambiado
        gc-boe-convocatoria-xml           9f6b802314ac != 263900393c7b
        celador-2023-bocyl-resolucion-pdf 80e3343ff075 != 30552d886eac
      «Si la fuente oficial ha cambiado, hay que revisar los fixtures y actualizar el manifiesto.»
18    E2E · 93 passed en 4,6 min                      ✓
```

**Y los dos rojos, explicados:**

**El de la 7 era mío, y ya está**: **la prueba de la bandeja afirmaba un tope que se pedía por la
dirección**, y **la dirección ya no lleva parámetro** — **porque cualquier parámetro tipado mete el 422 de
FastAPI en el contrato y la puerta 8 lo rechaza**. **Arreglado y verificado**: `1 passed`.

**El de la 17 no es mío**: **dos documentos oficiales han cambiado sus bytes desde que se registró el
manifiesto** — **el XML del BOE y un PDF del BOCYL** —. **Eso no se arregla con un comando**: **es una
decisión de contenido** — **o se acepta que la fuente cambió y se actualiza el manifiesto, o se investiga
por qué**. **Y es del propietario, no del codificador.**

**Lo que queda de la batería**: **volver a correr la 7 entera** (una hora) **para tenerla limpia con la
prueba ya corregida**, **y la decisión sobre las dos fuentes**.
