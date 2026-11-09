# Demo estática publicada en GitHub Pages

**URL verificada:** <https://erdeivih.github.io/opofuente-demo/> · **estado:** HTTP 200 y 8/8
comprobaciones con Playwright (9/11/2026). Publicada desde el repositorio público
`ErDeivih/opofuente-demo`, que contiene **solo el build** (sin código fuente, sin fixtures y sin
material privado).

## Qué es (y qué no)

Es una **demo de lectura y práctica**, sin backend. El temario y las dos prácticas van empaquetados
en el build; el progreso se guarda en `localStorage` del navegador. **No hay cuenta, no hay servidor
y no se envía nada.**

- Temario común: 5 bloques / 40 temas.
- Apuntes completos del **tema I.1** (La Constitución) y del **tema II.13** (Arquitectura de
  ordenadores), citados del BOE cuando aplica.
- **Dos prácticas de 10 preguntas** con corrección y explicación al momento, y ficha de cada pregunta.
- Aviso visible en todas las pantallas: demo estática, datos en el navegador.
- No incluye Guardia Civil, ni el corpus real, ni material de academias.

La aplicación completa (SQLite, biblioteca, banco propio, sesiones con puntuación) sigue siendo
local; para publicarla con backend hace falta una cuenta de Render/Hugging Face
([CUENTAS-Y-ACCESOS.md](CUENTAS-Y-ACCESOS.md)).

## Regenerar y publicar (5 líneas)

1. `uv run python -m opofuente.tools.build_static_demo` (regenera `apps/web/demo/data.json` desde el
   fixture del temario y `fixtures/demo/tema-*.json`).
2. `npm run build:demo` (build estático en `apps/web/dist-demo/`).
3. Copia el contenido de `dist-demo` a un clon del repo público `ErDeivih/opofuente-demo` (rama
   `main`), junto a `.nojekyll`.
4. `git add -A && git commit -m "demo" && git push origin main`; GitHub Pages reconstruye solo.
5. Verifica: `node docs/interfaz/capturar-demo-pages.mjs https://erdeivih.github.io/opofuente-demo/`
   → **8/8** y capturas.

## Verificación y capturas

`docs/interfaz/capturar-demo-pages.mjs` comprueba, contra la URL pública: temario 5/40, apuntes de
I.1, ficha de pregunta con explicación, práctica completada (10 preguntas), progreso persistido en
`localStorage`, segunda práctica y ausencia de errores de página.

Capturas a **390 y 1280** en [`docs/capturas/demo-pages/`](capturas/demo-pages/):

| Pantalla | 1280 | 390 |
|---|---|---|
| Temario | `temario-1280.png` | `temario-390.png` |
| Práctica (II.13) | `practica-ii13-1280.png` | `practica-ii13-390.png` |
| Ficha de pregunta | `pregunta-i1-1280.png` | `pregunta-i1-390.png` |
| Ficha de tema I.1 | `tema-i1-1280.png` | `tema-i1-390.png` |
| Resultado de la práctica | `resultado-1280.png` | — |

## Límites dichos

- Sin backend: no hay cuentas, ni progreso entre dispositivos, ni banco completo, ni biblioteca.
- El progreso vive en el navegador: borrar datos del sitio lo elimina.
- La demo publica únicamente contenido propio/sintético; el repositorio principal sigue privado.
- GitHub Pages sirve estático sin cabeceras propias; el HTML lleva una CSP por `<meta>` que bloquea
  cualquier conexión de red (`connect-src 'none'`).
