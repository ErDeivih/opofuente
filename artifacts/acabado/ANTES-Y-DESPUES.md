# El acabado de la interfaz (§2): antes y después, medido

**Base:** `main = 1caefb7` · **Rama:** `f33-acabado` · **Fecha:** 16-oct-2026

Este fichero no describe: **mide**. Son las capturas que el propietario revisa y las cifras que las
pruebas exigen, guardadas juntas para que se puedan comparar.

## Cómo se han hecho

```
artifacts/acabado/antes/     capturas contra el árbol SIN los arreglos (rojo previo)
artifacts/acabado/despues/   capturas contra el árbol CON los arreglos (verde)
```

Las dos corridas son el **mismo** guion (`apps/web/tests/screens/acabado.spec.ts`), a **1280×800** y
**390×844**, con `fullPage: true`, y cada prueba exige **0 violaciones de axe** (A/AA, incluidas 2.1 y
2.2) y **0 errores de consola**. El «antes» se obtuvo guardando los cambios en un `git stash`, compilando
ese árbol y lanzando el mismo guion: por eso los dos PNG son comparables.

| corrida | resultado | fichero de la salida |
| --- | --- | --- |
| `antes` | **3 fallos · 5 pasan** | `artifacts/acabado/screens-antes.txt` |
| `despues` | **8 pasan** | `artifacts/acabado/screens-despues.txt` |

## El rojo previo, enumerado

Las pruebas se escribieron **antes** del arreglo y se ejecutaron contra el árbol sin él. Estas son las
que estaban en rojo, con lo que decían:

**De componente** (`npx vitest run`, 10 fallos · 3 pasan, guardado en `artifacts/acabado/rojo-unitario.txt`):

| prueba | por qué estaba en rojo |
| --- | --- |
| `numeros.test.ts` (fichero entero) | no existía `src/lib/numeros.ts`: no había un solo sitio que decidiera el formato |
| `capturasDatos.test.ts` (fichero entero) | no existía `scripts/screens.mjs`: no había `--datos <dir>` |
| `acabadoResultado`: la nota en una línea (2) | la pantalla no escribía «Puntuación directa: 0,33 sobre 50 (estimada)» |
| `acabadoResultado`: la explicación, plegada (2) | los dos párrafos estaban **visibles** y no había botón que los plegara |
| `acabadoResultado`: la hoja de respuestas (2) | no había hoja corregida ni forma de bajar a una pregunta |
| `acabadoResultado`: «Ver en apuntes» (1) | no había ninguna salida al apartado |
| `cargaEsqueleto` (3) | no había esqueleto: las tres pantallas esperaban al servidor con un texto |

**De capturas**: el carril a 1280 px y el resultado a los dos anchos (los tres de arriba).

**De la escalera de migraciones** (`_medir_escalera.py`, borrado después de medir):

```
escalones a mano: 29
cadena real de alembic: 40
escalones que la lista a mano NO tiene: 11
```


## Arreglo 1 · El menú lateral no llegaba abajo

**Lo que se mide**: la altura del carril (`.carril`) contra la de su columna (`.marco-alumno__cuerpo`).

| | carril | columna | veredicto |
| --- | --- | --- | --- |
| antes | **800 px** | 1466,30 px | rojo: «el carril mide 800 px y su columna 1466.296875 px» |
| después | 1466,30 px | 1466,30 px | verde |

Y los **píxeles** de la captura, que es lo que el propietario ve. Perfil vertical en la columna del
carril (`x = 5`) de `acabado-inicio-escritorio.png`:

| | y = 0 … 799 | y = 800 … 1465 |
| --- | --- | --- |
| antes | blanco `(255,255,255)` | **gris del papel `(244,246,249)`** |
| después | blanco `(255,255,255)` | **blanco `(255,255,255)`** |

Es literalmente lo que él describió: *«el fondo blanco del carril acaba a 800 px y debajo se ve el
gris»*. La causa: el `height: 100vh` estaba en el propio carril, así que el blanco medía el alto de la
ventana y no el de la columna. Ahora el carril es la **columna** (se estira con la fila) y lo que viaja
pegado es `.carril__interior` (`position: sticky; top: 0; min-height: 100vh`).

A 390 px el carril no se pinta, la barra inferior sí, el ancho de ventana es 390 exacto y **no hay
desbordamiento horizontal** (`scrollWidth − innerWidth ≤ 0`): las dos comprobaciones pasan en las dos
corridas porque a 390 px no había nada roto — el defecto era de escritorio.

## Arreglo 2 · Los números, en español

En el «antes», la línea del resultado decía:

```
"0.0000"
```

Es el decimal que manda el servidor (`decimal_text`, punto y cuatro cifras) pintado tal cual. En el
«después» dice `Puntuación directa: 0,00 (estimada)` y la prueba exige
`/^Puntuación directa: \d+,\d{2}( sobre \d+)? \(estimada\)$/` **y** que la línea no contenga
`/\d\.\d/`. El «sobre 50» de la captura del propietario sale cuando la convocatoria publica el máximo
de la parte; con la sesión sembrada —que no declara parte— no hay máximo y la pantalla no se lo
inventa.

**Los números unificados y dónde** (un solo módulo, `apps/web/src/lib/numeros.ts`):

| qué | antes | ahora | dónde estaba |
| --- | --- | --- | --- |
| nota (puntuación) | `0.0000` | `0,00` | `api/study.ts` (`formatScore`), `pages/student/ResultPage.tsx` (×2) |
| nota por parte | `0.3333` | `0,33` | `pages/student/ResultPage.tsx` |
| intervalo del diagnóstico | `0.21 – 1.00` | `0,21 – 1,00` | `features/study/DiagnosticPanel.tsx` |
| segundos de un reíndice | `0.01 s` | `0,01 s` | `pages/SettingsPage.tsx` |
| cobertura de los apuntes | `toFixed(1).replace('.', ',')` | `formatearPorcentaje(…, {decimales: 1})` | `api/notesReview.ts` |
| porcentajes del alumno | `Math.round(x*100) %` | `formatearPorcentaje(x)` | `ResultPage`, `ProgressPage`, `SyllabusPage` (×2), `StudentHomePage`, `TestsPage` |
| máximo de la prueba | `String(50)` | `formatearEscala(50)` | `features/study/StudyResultPanel.tsx` |

Eran **tres** formatos: el decimal del servidor (punto, 4 cifras), un `toFixed(2)` en dos pantallas y un
`toFixed(1).replace('.', ',')` en otra. Ahora hay **una** decisión, y las tres pruebas que fijaban el
formato viejo (`study.test.tsx`: `1.6667 (5/3)` y `0.21 – 1.00`) se han actualizado **con su razón
escrita en el propio test**: eran las pruebas las que estaban fijando el formato equivocado.

**Los porcentajes** siguen sin decimales salvo donde hacen falta (la cobertura de los apuntes, que se
compara contra el listón del 90 %).

## Arreglo 3 · El resultado, en una línea

* antes: abría con **dos párrafos** sobre los baremos de la Comisión y el mínimo de 25, visibles.
* después: **una línea** («Puntuación directa: … (estimada)») y un botón **«¿Por qué estimada?»**
  (`aria-expanded="false"`) que despliega **los mismos dos párrafos** —no se han borrado—.
  La prueba exige las dos cosas: que el texto siga en el documento y que **no sea visible** por defecto.

## Arreglo 4 · La hoja de respuestas y «Ver en apuntes»

* antes: el resultado no tenía hoja de respuestas ni salida a los apuntes por pregunta.
* después: la hoja del **diseño v0** (`AnswerSheet`, la misma que se usa mientras se contesta) arriba,
  con las casillas A–D, **verde la correcta y el color del fallo la fallada**; pulsar un número baja a
  esa pregunta; y **«Ver en apuntes»** bajo cada fallada con el **anclaje del apartado**
  (`/temario/IV.7#el-modelo-tcp-ip-y-sus-capas`), resuelto por el servidor desde la comprobación del
  motor (`question_note_anchors`). Sin anclaje no se ofrece la salida, en vez de mandar a la portada del
  tema.

## Arreglo 5 · Esqueletos de carga y coherencia

No se ve en una captura porque dura 300 ms, así que se mide donde se puede medir: en la prueba de
componente, que exige que **el Temario, el Progreso y el Tema** enseñen su esqueleto cuando el servidor
tarda y que una respuesta rápida **no lo haga parpadear**. En el «antes» las tres pruebas estaban en
rojo.

La coherencia (botón secundario, etiqueta, espaciado y estados) son reglas de CSS: en el «antes» y el
«después» las capturas de Temario y Progreso pasan axe y consola en cero, así que el cambio de estilos
no ha roto nada.

## Lo que estas capturas NO demuestran

* **El color de dentro de la hoja de respuestas** (casilla verde / casilla fallada) está comprobado por
  la prueba sobre el DOM (`data-estado="correcta"` / `"fallada"`), no leyendo el PNG. El PNG es para
  mirarlo, y esta máquina no ve imágenes.
* El carril se ha medido como **altura de caja** y como **píxel**; no se ha medido su comportamiento al
  desplazar la página a mano en un navegador con ventana real.
