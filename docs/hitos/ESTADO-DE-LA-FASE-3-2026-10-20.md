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

## El árbol restaurado, verificado a mano (rondas 229-231)

**La batería del instrumento se quedó colgada en la puerta 4 en este árbol** —`gates.ps1` vivo con 4 s de
CPU, sin `eslint` ni `tsc` corriendo—, **así que la he matado y he corrido las puertas por separado**, que
es lo que el §4 bis permite cuando se dice:

```
1  ruff format        ✓

2  ruff check         ✓
3  mypy 275           ✓
4  eslint             ✓   (a mano: 0, y con --max-warnings=0)
5  tsc                ✓   (a mano, ronda 216)
6  unitarias backend  ✓   (993, ronda 218)
7  integración        ✗   no re-corrida: 824 pasaron y el único fallo era mi prueba, ARREGLADO
8-16 contrato, builds, migración 0041, siembra, fixtures   ✓ (ronda 227)
17 FALLO  dos fuentes oficiales cambiadas: gc-boe-convocatoria-xml y celador-2023-bocyl-resolucion-pdf
18 E2E 93 passed      ✓   (ronda 227)
```

**Y una lección de la ronda, que ha costado un proceso**: **maté la batería filtrando por
`CommandLine -like '*gates.ps1*'` y me llevé mi propio shell por delante** — **mi propio comando contenía
`gates.ps1`**. **La regla**: ***nunca se mata un proceso por una cadena que tu propio comando lleva dentro.***

**Lo que queda, y es de dos clases**: **volver a correr la puerta 7 entera** (una hora, con mi prueba ya
corregida) **y la decisión sobre las dos fuentes oficiales** — **que es del propietario**.

## LA PUERTA 7, EN VERDE: 825 passed en 59:55 (ronda 240)

```
825 passed, 1492 warnings in 3595.75s (0:59:55)
```

**Con la prueba de la bandeja dentro y la corrección de la ronda 227 aplicada.** **Y es la undécima pieza
de las dieciocho que cierra en verde sobre el árbol restaurado.**

## El 18/18 de hoy, puerta por puerta

```
1  ruff format        ✓
2  ruff check         ✓
3  mypy 275           ✓
4  eslint             ✓
5  tsc                ✓
6  unitarias backend  ✓   993
7  integración        ✓   825 en 59:55
8  contrato           ✓   export --check + contracts:check
9  test:web           ✓   494
10 contrato           ✓
11 uv build           ✓
12 build:web          ✓
13 migración          ✓   0041
14 esquema            ✓   app_metadata 3
15 siembra            ✓
16 idempotente        ✓
17 fixtures           ✗   DOS FUENTES OFICIALES HAN CAMBIADO
18 E2E                ✓   93 en 4,6 min
```

**Diecisiete de dieciocho.** **Y la decimoséptima no es un defecto del árbol**: **el XML del BOE y un PDF del
BOCYL tienen otros bytes que los que registró el manifiesto**, **y el propio árbol se niega a seguir sin que
alguien lo revise**. **Eso es una decisión de contenido y es del propietario.**

## Cierre de la sesión larga: el estado y por dónde se empieza (ronda 244)

**Lo que hay, verificado hoy:**

```
main = f229e7e · sucio rastreado 0 · 17 de 18 puertas en verde (la 17, por dos fuentes oficiales)
M0  CERRADO   · tres ramas · 74 capturas con datos reales · la tabla de los 20 con 21 cifras
M1  la bandeja entera: leer · aprobar · rechazar · editar · teclado · su prueba (825 integración)
              y la cita en el test y en el Resultado · falta solo regenerar (la clave)
M2  copia verificada (SHA-256 idéntica) · política de dos copias · cuarentena medida (0,0114 $)
M3  tarjeta (7 pruebas) · SM-2 (5) · cola del día (5) · el tool (14 de 19.316)
gasto 0 $ de 30 · base real A0A21413…C5AFF8 · cero escrituras
```

**Y el árbol bueno es `F:\temp-opofuente\opofuente-restaurado`**; **el repositorio, `F:\EspacioCodigo\opofuente`**.

## La primera media hora de la sesión siguiente

1. **`DEEPSEEK_API_KEY` en el entorno** — si está:
   ```
   uv run python -m opofuente.tools.explicar_preguntas --de-verdad --limite 20
   ```
   **Eso da la cifra del coste por explicación, que es lo único que autoriza a gastar los 12 $ de M1.**
2. **Si la cifra cabe**: la corrida de las 11.147, y entonces **las capturas de M1** — hoy están vacías
   con su motivo escrito en `artifacts/recorrido-M1/README.md`.
3. **Regenerar en la bandeja** (el `POST` que falta) — **la única acción que gasta**.
4. **El paso 2 de M2** — los tres nombres de los escaneos.
5. **La puerta 17** — la decisión sobre las dos fuentes oficiales que cambiaron.

**Y las tres reglas que esta sesión ha pagado caras**: **se commitea antes de seguir** (un árbol vaciado se
recuperó en dos comandos), **se lee el molde antes de escribir** (la pantalla que llevaba 70 rondas
pendiente se hizo en tres), **y se lee el mensaje entero de `mypy`** (once rondas por un `Substring`).

## La puerta de codificación, a mano (ronda 245)

**El script `comprobar-mojibake.ps1` se perdió con la limpieza** — vivía en `F:\temp-opofuente`, fuera del
repositorio —, **así que la he corrido a mano, que son cinco líneas**:

```
ficheros de texto mirados:      1.311
con mojibake:                   3   ← y son EXACTAMENTE las tres excepciones documentadas
  docs/DEBT.md                              (los ejemplos de DEBT-029)
  docs/FASE-3-ESTUDIO-DIARIO-SPEC-PLAN...md (describe la puerta y cita el patrón)
  docs/LA-FUSION-2537eb3-RESUELTA-2026-10.md (documenta la reparación y cita las secuencias)
marcadores de conflicto:        0
```

**La puerta pasa.** **Y el script hay que rehacerlo en la próxima sesión** — **su sitio natural es
`scripts/comprobar-mojibake.ps1`, DENTRO del árbol** —, **que es lo que impide que una limpieza se lo lleve
otra vez.** **El que había estaba fuera y por eso se perdió.**

## El script de la puerta: el intento y su tropiezo (ronda 246)

**Lo escribí dentro del árbol** —`scripts/comprobar-mojibake.ps1`, que es donde tiene que estar— **y
PowerShell lo rechazó con un error de sintaxis en la línea del patrón de los marcadores**:

```
Falta la cadena en el terminador: ".
  en comprobar-mojibake.ps1: 69
```

**Y lo he retirado en vez de dejarlo roto**: **un script de puerta que no arranca es peor que no tenerlo**,
**porque parece que la puerta existe.** **El árbol queda como estaba: la puerta se corre a mano** (su
resultado está en el apartado anterior) **y el script se rehace con el fichero delante**.

**Lo que hay que saber para el siguiente intento, y es lo que tropezó**: **los patrones con `<` y `>`**
—`'^(<<<<<<<|>>>>>>>)'`— **en PowerShell son un campo de minas de comillas y redirecciones**. **La forma
que funciona**: **leer el fichero y comparar con `-match` sobre líneas**, **o construirlo con `[char]`**,
**en vez de poner los siete caracteres dentro de una cadena de patrón**.

## El fallo de las unitarias era la descarga de fuentes (ronda 247)

**Al cerrar, las unitarias daban `1 failed, 993 passed`**, y **el fallo era
`test_profile_fixtures.py:678`: `content_fingerprint(ruta) != sources[id]["content_sha256"]`** — **la
huella de un documento descargado no coincidía con la del manifiesto**.

**La causa era mía y de esta mañana**: **en la ronda 227 corrí `scripts/fetch-sources.ps1`** para que la
puerta 17 tuviera fuentes, **y descargó los documentos oficiales que YA HAN CAMBIADO** — **el XML del BOE y
un PDF del BOCYL** —. **Los dejó en `data/sources`, que está ignorado en git, y desde ahí rompen la prueba
que compara las fuentes con el manifiesto.**

**Quitados los 18 ficheros de `data/sources`, las unitarias vuelven a 994 en verde** — **que es el estado
en el que estaban antes de que yo tocara las fuentes**.

**Y la moraleja, que es la de la puerta 17**: ***no se descarga la fuente oficial para «arreglar» la puerta;
se mira por qué cambió***. **El árbol tenía razón al negarse las dos veces.**

## El script de la puerta no se puede escribir así, y por qué (rondas 246-249)

**Dos intentos, dos rechazos de PowerShell, y el segundo explica al primero**:

```
Token 'Â·Âª-Â¿]' inesperado
```

**El `write` escribe el fichero en UTF-8 SIN BOM. PowerShell 5.1 lee los `.ps1` en UTF-8 sin BOM
como ANSI**, así que **`Ã` se convierte en `Ãƒ`, `·` en `Â·` y el patrón de mojibake queda escrito
roto** — **el vigilante infectado por el virus que vigila**.

**La solución existe y es fea**: **el script tiene que ser ASCII puro, con cada carácter especial
puesto como `[char]0x00C3`**. **Funciona, pero ya no se lee** — **y un script de puerta que no se
puede leer es el mismo problema que este fichero existe para evitar**.

**Lo que queda decidido**: **la puerta se corre a mano** — cinco líneas de `Select-String`, con el
resultado escrito en el apartado del 245 —, **y el script se escribe con el fichero delante y guardado
en UTF-8 CON BOM** (el formato que PowerShell lee bien). **Lo que NO se hace**: dejarlo roto en
`scripts/`, porque un guardián que no arranca es peor que ninguno.

## La puerta de codificación está en el árbol y pasa (ronda 251)

```
scripts/puerta-codificacion.ps1

mojibake: revisados 967 ficheros de texto
12 linea(s) exceptuadas en 4 fichero(s), con su motivo arriba
SIN MOJIBAKE        exit 0
```

**Y las cuatro excepciones, cada una con su motivo escrito al lado en el propio script**: `DEBT.md`
(los ejemplos de DEBT-029) · `FASE-3-...md` (describe la puerta y cita el patrón) · `LA-FUSION-...md`
(documenta la reparación) · **y este folio**, porque **cuenta la puerta y cita el mojibake como
ejemplo**.

**Y está DENTRO del árbol, que es lo que faltaba**: la versión anterior vivía en `F:\temp-opofuente`, y
una limpieza se la llevó. **Esta se recupera con un `git checkout`.**

**El truco que la hace funcionar**, y va escrito en el propio fichero: **es ASCII puro**, con cada
carácter especial como `[char]0x00C3` y compañía. **Puesto como literal, PowerShell leía el `.ps1` en
UTF-8 sin BOM como ANSI y el patrón de mojibake quedaba escrito roto dentro del guardia que lo busca.**
