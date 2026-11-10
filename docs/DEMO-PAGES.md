# Demo estática publicada en GitHub Pages

**URL verificada:** <https://erdeivih.github.io/opofuente-demo/> · **estado:** HTTP 200 y **10/10**
comprobaciones con Playwright contra la URL pública (10/11/2026). Publicada desde el repositorio
público `ErDeivih/opofuente-demo`, que contiene **solo el build** (sin código fuente, sin fixtures y
sin material privado).

## Qué es (y qué no)

Es una **demo de lectura y práctica**, sin backend. El temario y las prácticas van empaquetados en el
build; el progreso del visitante se guarda en `localStorage`. **No hay cuenta, no hay servidor y no se
envía nada.**

- Temario común completo: **5 bloques / 40 temas**.
- **13 temas redactados** con contenido propio: apartados, definiciones, tablas, ejemplos, fuente y
  **10 preguntas con respuesta razonada** cada uno (130 preguntas).
- **27 temas en preparación**: se marcan como tales en el temario y en su ficha; no se muestra un
  párrafo vacío ni relleno.
- Ficha de pregunta con enunciado, opciones, respuesta correcta y explicación.
- Aviso visible en todas las pantallas: demo estática, datos en el navegador.

La aplicación completa (SQLite, biblioteca, banco propio, sesiones con puntuación) sigue siendo
local; para publicarla con backend hace falta una cuenta de Render/Hugging Face
([CUENTAS-Y-ACCESOS.md](CUENTAS-Y-ACCESOS.md)).

## Progreso del contenido (40 temas)

| Bloque | Temas | Completos | En preparación |
|---|---|---|---|
| I · Administración y normativa | 12 | **9** (I.1, I.2, I.3, I.5, I.6, I.7, I.9, I.10, I.12) | 3 (I.4, I.8, I.11) |
| II · Informática básica y ofimática | 5 | **1** (II.13) | 4 (II.14-II.17) |
| III · Sistemas, redes y comunicaciones | 9 | **2** (III.21, III.24) | 7 |
| IV · Datos y desarrollo | 7 | **0** | 7 (IV.27-IV.33) |
| V · Seguridad y administración electrónica | 7 | **1** (V.34) | 6 |
| **Total** | **40** | **13** | **27** |

- **Completos:** 13 · **Con preguntas:** 13 (cada tema completo lleva su práctica de 10) ·
  **Pendientes:** 27 · **Preguntas:** 130.

Cada tema completo cita su fuente; las principales:

| Tema | Fuente |
|---|---|
| I.1 | Constitución Española (BOE-A-1978-31229) |
| I.2 | TUE y TFUE, versiones consolidadas publicadas por el BOE |
| I.3 | Ley 7/1985, de bases del régimen local |
| I.5 | Ley 39/2015, del procedimiento administrativo común |
| I.6 | Ley 40/2015, de régimen jurídico del sector público |
| I.7 | RDL 5/2015 (TREBEP) |
| I.9 | RDL 2/2004 (texto refundido de la Ley de Haciendas Locales) |
| I.10 | Ley 9/2017, de contratos del sector público |
| I.12 | Ley 19/2013; RGPD y LO 3/2018 |
| II.13 | Apuntes propios sobre arquitectura de computadores |
| III.21 | IETF RFC 791 (IPv4) y RFC 8200 (IPv6) |
| III.24 | ISO/IEC 20000-1:2018 (gestión del servicio) |
| V.34 | ISO/IEC 27001:2022 (SGSI) |

## Regenerar y publicar (5 líneas)

1. Edita o añade contenido en `fixtures/demo/temas/<path>.json` (esquema en
   [`fixtures/demo/README.md`](../fixtures/demo/README.md)).
2. `uv run python -m opofuente.tools.build_static_demo` (regenera `apps/web/demo/data.json`).
3. `npm run build:demo` (build estático en `apps/web/dist-demo/`, con `data.json` publicado).
4. Copia `dist-demo` al clon del repo público `ErDeivih/opofuente-demo` (rama `main`, junto a
   `.nojekyll`), `git add -A && git commit -m "demo" && git push origin main`.
5. Verifica: `node docs/interfaz/capturar-demo-pages.mjs https://erdeivih.github.io/opofuente-demo/`
   → **10/10** y capturas.

## Verificación y capturas

El script comprueba contra la URL pública: 40 temas y 5 bloques, progreso visible, 13 temas
completos, un tema completo con apartados y fuente, un tema pendiente que dice «En preparación», una
práctica completada de 10 preguntas, persistencia en `localStorage` y ausencia de errores de página.

Capturas a **390 y 1280** en [`docs/capturas/demo-pages/`](capturas/demo-pages/):

| Pantalla | 1280 | 390 |
|---|---|---|
| Temario con progreso | `temario-1280.png` | `temario-390.png` |
| Tema completo | `tema-completo-1280.png` | `tema-completo-390.png` |
| Tema en preparación | `tema-pendiente-1280.png` | `tema-pendiente-390.png` |
| Práctica | `practica-1280.png` | `practica-390.png` |
| Ficha de pregunta | `pregunta-1280.png` | `pregunta-390.png` |
| Resultado | `resultado-1280.png` | — |

## Límites dichos

- Sin backend: no hay cuentas, ni progreso entre dispositivos, ni banco completo, ni biblioteca.
- El progreso del visitante vive en su navegador; borrar datos del sitio lo elimina.
- 27 temas aún no están redactados: la demo lo dice, no los rellena.
- El temario TAI recuperado (33/33 temas, 330 preguntas) está **en local y es privado**: procede de
  material de terceros y no se publica aquí. Inventario y derechos en
  [`TEMARIO-RECUPERADO.md`](TEMARIO-RECUPERADO.md).
- La demo publica únicamente contenido propio; el repositorio principal sigue privado.
- GitHub Pages sirve estático sin cabeceras propias; el HTML lleva una CSP por `<meta>` que bloquea
  cualquier conexión de red (`connect-src 'none'`).
