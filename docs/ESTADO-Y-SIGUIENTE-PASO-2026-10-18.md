# Estado y siguiente paso — 18 de octubre de 2026, 23:00

**Para:** quien retome esto (Claude, o el bloque que mide) · **De:** DeepSeek
**Motivo:** los dos agentes están al final de su contexto con la batería de `main` a media
puerta 7. Esto es el estado exacto, la receta verificada y lo que falta, para que no haya
que reconstruirlo.

---

## 1 · Dónde está `main`

```
main = 54e9048
  8a1a14e  docs: rehacer ESTADO-DEL-OBJETIVO.md desde las dos versiones limpias (+2383/−2381)
  8ff04a9  F41: las 20 lineas de mojibake de test_claves_derivadas.py (fusionada, 1 fichero)
```

**`main` está SIN VERIFICAR por una batería completa.** La de `2537eb3` **murió a media
puerta 4** (murió la sesión de DSH y se llevó a la batería y al vigilante): **1, 2 y 3
verdes y nada más — es «una medición que no existió», no un verde ni un rojo.**

## 2 · Lo que está corriendo ahora mismo

```
gates-main-8a1a14e.txt · ANTES 22:47:33 · commit_medido=8a1a14e
puertas 1-6 OK · puerta 7 en marcha (arrancó ~22:53, ~65 min)
marca: «puerta 7 en marcha» · árbol: copia nueva con .venv propio y canario de entorno
```

**Si el registro no tiene línea `DESPUES` y la marca sigue diciendo «en marcha», la
medición NO EXISTIÓ.** No es un rojo. (Es la duodécima forma de `DEBT-022`: *la marca
miente por omisión*.)

## 3 · Los nueve puntos del §3, con su veredicto

| punto | commit | veredicto | ¿en main? |
|---|---|---|---|
| 1 lectura por capítulos | `d312be0` | 18/18 | **sí** |
| 2 ciclo de contestar | `d413e1c` | **18/18 en dos piezas** (1-17 de `d362572` + la 18 de `d413e1c`) | **sí** |
| 3 y 4 simulacro + reloj | `54a6883` | **18/18 en dos piezas** (1-7, 9, 12-18 de `4399fc3` + 8, 10, 11 de `54a6883`) | **no** |
| 5 el Resultado | `c794d4e` | **18/18 en una pasada** (1:16:46) | **sí** |
| 6 y 7 repaso + datos | `b96d512` | **18/18 en dos piezas** (1-6, 8-18 de `21cd8ab` + la 7 de `b96d512`) | **no** |
| 8 y 9 Inicio y panel | `fbe8428` | **pendiente: desde la puerta 3** (el `.venv` estaba copiado y se rehízo) | **no** |
| — mojibake | `8ff04a9` | 20/20, puerta 0 en la rama y 11 en `main` | **sí** |

## 4 · La receta de `f42-integracion` (verificada hoy)

```powershell
$repo = 'F:\temp-opofuente\opofuente-main'
git -C $repo worktree add F:\temp-opofuente\opofuente-f42 54e9048 --detach
git -C F:\temp-opofuente\opofuente-f42 checkout -b f42-integracion

# por cada rama, EN ESTE ORDEN: F37 54a6883 -> F39 b96d512 -> F40 fbe8428
git -C F:\temp-opofuente\opofuente-f42 merge --no-ff --no-commit <commit>
#   conflicto SOLO en docs/ESTADO-DEL-OBJETIVO.md:
#     la version buena es la de la integracion (main);
#     la seccion de la rama se extrae y se aplica (git escribe bytes: NO cmdlets de texto)
git -C $repo diff --output=F:\temp-opofuente\seccion-<rama>.patch <base> <commit> -- docs/ESTADO-DEL-OBJETIVO.md
git -C F:\temp-opofuente\opofuente-f42 apply --3way F:\temp-opofuente\seccion-<rama>.patch
#   si queda un «=======» huerfano SIN «<<<<<<<» ni «>>>>>>>»: se quita y se dice
```

**Las bases**: F37 ← `4399fc3`; F39 ← `21cd8ab`; F40 ← `fb8ea26`.

**Después de CADA fusión, las tres comprobaciones, en este orden:**

| comprobación | cómo | bueno |
|---|---|---|
| mojibake | `scripts-sombra\comprobar-mojibake.ps1 -Raiz <árbol>` | `exit 0` |
| conteo | `rama + main − base` por fichero | cuadra, **o se mira QUÉ fichero y POR QUÉ** |
| marcadores y secciones | 0 `<<<<<<<`/`=======`/`>>>>>>>`; F35…F40 **una vez cada una** | — |

**Y al final, las 18 sobre `f42-integracion`** (copia nueva, `.venv` propio con
`uv sync --frozen`, `node_modules`, `data/sources`, canario `uv run mypy` → 0). **Esa es la
que va a `main`, y la fusiona el agente principal con un `--no-ff`.**

## 5 · Lo que falta, en orden

1. **La batería de `8a1a14e`** (en marcha): si sale verde, el árbol base está sano.
2. **El cableado del instrumento**, cuando esa batería cierre:
   - la puerta del mojibake **antes de la 1**, con su cuenta (*«1.014 ficheros · 10 líneas
     exceptuadas en 3 ficheros, con su motivo»* — un cero sin contexto no dice si miró);
   - **la marca con hora** (`puerta 4 en marcha desde 17:23:05`);
   - **el vigilante fuera de la sesión** (o latido con hora);
   - **`ABORTADA: la marca es huérfana`** al arrancar si el proceso de la marca no vive.
3. **`f42-integracion`** con las tres fusiones y **sus 18**.
4. **Fusionar en `main`** y verificar (conteo + mojibake + secciones).
5. **El cierre**: recorrido sobre **copia nueva de la base del propietario** (2.748.612.608 B,
   `a0a21413…`), **tabla antes/después de los 20 defectos con la cifra de cada uno**,
   capturas a 1280 y 390, y **PARAR**.

## 6 · Las cifras del cierre, ya medidas

| defecto | antes | después |
|---|---|---|
| página de IV.7 | 110.427 px | 20.433 px |
| página de I.1 | 314.402 px | 118.982 px |
| columna de lectura a 1280 | 370 px | 647 px |
| «Ver en apuntes» → párrafo | 0 px | 34.971 (1280) · 61.022 (390) |
| `POST /start` por test abierto | 27 | 1 |
| contestar dos veces seguidas | 500 | 200 |
| cambiar una respuesta | 409 | 200 |
| montar el simulacro | 142,3 s | 3,2 s |
| consultas a SQLite | 154.231 | 441 |
| hoja de respuestas del Resultado | `rgba(0,0,0,0)` | `rgb(21,115,74)` / `rgb(180,35,24)` |
| práctica | `6,00 sobre 50 · mínimo 25` | `Netos con penalización: 6,00 · 60 %` |
| nota negativa | `-0,33` | `0,00` (exacta en el pliegue) |
| Inicio promete / repaso sirve | 5 / 0 | **1 / 1** |
| fila del examen | 135 | 85 (y 79 los de promoción interna) |
| exámenes con fecha | 0 de 13 | **13 de 13** (el año que declara el documento) |
| los 28 `[]` | 28 iguales | **21 huecos (`_____`) + 7 corchetes de código** |
| «67 %» del bloque I | en línea propia | en su fila (0 px de desviación) |
| lista de apuntes en Inicio | los 29 temas | **«Seguir leyendo»** |
| simulacro en Simulacros | «110 preguntas · 120 minutos» | **«100 preguntas (+10 de reserva) · 120 min»** |
| `/admin/apuntes` | 5,37 s | **0,835 s** |
| ficha de IV.7 | 3,45 s | **3,18 s — no baja de 2, y se dice por qué** |

## 7 · Las formas de `DEBT-022`, y las frases que valen

Doce formas de un rojo que no es del código: mutación del árbol · puerto ajeno · `vite preview`
propio · flake de componentes · el pool de `vitest` que no arranca · E2E por lo que corrió antes ·
la máquina que se duerme (→ **tope por puerta**) · `.pytest-tmp` en paralelo · **una guarda que
juzga puertas que no abren puerto** (→ alcance limitado, y **un solo mecanismo, un solo código**) ·
**el `.venv` copiado** · **el mojibake** · **la sesión que se muere y se lleva al medidor y al
vigilante** (→ marca con hora, vigilante fuera, marca huérfana).

> ***Un número que no cuadra es una pregunta, no un veredicto.***
> ***Cuando hay un solo mecanismo, el rojo que sale se puede atribuir.***
> ***Un `.venv` copiado arranca pero puede no ser el intérprete que resuelven las herramientas.***
> ***El fichero pasaba todas las puertas porque lo que estaba mal no era su codificación, eran sus caracteres.***
> ***Si el literal no lo compara nada escrito a mano, arreglarlo no cambia el juicio; y si cambia el juicio, no se toca.***
> ***Un intento medido y descartado vale más que un «optimizado» sin cifra.***
> ***Una prueba que deja datos no es una prueba, es una fuga que aparece tres ficheros más allá.***
