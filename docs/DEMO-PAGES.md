# Demo estática publicada en GitHub Pages

**URL verificada:** <https://erdeivih.github.io/opofuente-demo/> · **estado:** HTTP 200 y **52/52**
comprobaciones con Playwright contra la URL pública (10/11/2026). Publicada desde el repositorio
público `ErDeivih/opofuente-demo`, que contiene **solo el build** (sin código fuente, sin fixtures y
sin material privado).

## Qué es

Demo de lectura y práctica, sin backend: el temario va empaquetado y el progreso del visitante se
guarda en `localStorage`. **No hay cuenta, no hay servidor y no se envía nada.**

- Temario común completo: **5 bloques / 40 temas**.
- **40 temas con apuntes completos** y **40 prácticas de 10 preguntas** (400 preguntas con respuesta
  razonada); **0 pendientes**, marcados como tales; **0 solo resumen** por ahora.
- **12 convocatorias C1 de informática** a las que sirve el temario (10 por confirmar y 2 cerradas),
  más el perfil TAI. Se muestra en la portada, con enlace a las bases de cada una.
- **Mapa de cobertura publicado** en `#/cobertura`: los 40 temas con su estado y su práctica.
- **Guía de estudio** en `#/guia`: orden de bloques y temas flojos detectados desde las prácticas.
- **Modo examen** en `#/examen`: N preguntas aleatorias por bloque, sin corrección hasta el final, nota y revisión de fallos.
- **Estadísticas** en `#/estadisticas`: acierto por tema y bloque, y los 5 temas más flojos con enlace directo.
- **Portada corta**: cobertura, «Continuar donde lo dejé» y 3 prácticas siguientes; el resto está
  en la pestaña Prácticas. Las pestañas miden 44 px y la ficha lleva migas «Temario › I.1».
- **Práctica más rápida**: al elegir una opción se corrige al momento (sin «Comprobar») y aparece
  «Siguiente»; el progreso y las respuestas se guardan para reanudar.
- **Aviso único y corto** con «Cómo funciona»; el tema pendiente enlaza a «Ver temas completos»
  (temario filtrado por «Con apuntes»).
- Cobertura visible: en cada tema, sello de apuntes y de práctica; en cada bloque, «I: 11/12 con
  apuntes».
- Índice con **búsqueda por código o título** y filtros «Con apuntes» / «Con práctica».
- Correcciones con enlace al **texto oficial del BOE** cuando el tema lo cita.
- Un único aviso de demo, sin jerga ni avisos repetidos.

La aplicación completa (SQLite, biblioteca, banco propio, sesiones con puntuación) sigue siendo
local; para publicarla con backend hace falta una cuenta de Render/Hugging Face
([CUENTAS-Y-ACCESOS.md](CUENTAS-Y-ACCESOS.md)).

## Cobertura del temario común

| Bloque | Temas | Con apuntes | Pendientes | Con práctica |
|---|---|---|---|---|
| I · Administración y normativa | 12 | 12 | 0 | 12 |
| II · Informática básica y ofimática | 5 | 5 | 0 | 5 |
| III · Sistemas, redes y comunicaciones | 9 | 9 | 0 | 9 |
| IV · Datos y desarrollo | 7 | 7 | 0 | 7 |
| V · Seguridad y administración electrónica | 7 | 7 | 0 | 7 |
| **Total** | **40** | **40** | **0** | **40** |

Temas completos: I.1, I.2, I.3, I.4, I.5, I.6, I.7, I.8, I.9, I.10, I.11, I.12,
II.13, II.14, II.15, II.16, **II.17**, **III.18**, III.19, III.20, III.21, **III.22**, **III.23**, III.24, **III.25**, **III.26**, IV.27, **IV.28**, **IV.29**, **IV.30**, **IV.31**, **IV.32**, **IV.33**, **V.36**, **V.37**, **V.38**, **V.39**, **V.40**,
V.34 y V.35.
Cada uno cita su fuente (BOE consolidado, TUE/TFUE, RFC o ISO según el tema).

## Regenerar y publicar

1. Edita o añade contenido en `fixtures/demo/temas/<path>.json` (esquema en
   [`fixtures/demo/README.md`](../fixtures/demo/README.md)).
2. `uv run python -m opofuente.tools.build_static_demo` (regenera `apps/web/demo/data.json`).
3. `npm run build:demo` (build estático en `apps/web/dist-demo/`, con `data.json` publicado).
4. Copia `dist-demo` al clon del repo público `ErDeivih/opofuente-demo` (rama `main`, junto a
   `.nojekyll`), `git add -A && git commit -m "demo" && git push origin main`.
5. Verifica: `node docs/interfaz/capturar-demo-pages.mjs https://erdeivih.github.io/opofuente-demo/`
   → **52/52** y capturas.

## Verificación y capturas

El script comprueba contra la URL pública: portada con 12 convocatorias y un solo aviso, 40 temas,
portada corta con continuar, pestañas de 44 px, enlaces de convocatoria con texto, cobertura por
bloque, mapa de 40 filas, sellos, búsqueda y filtros, migas, tema pendiente con enlace filtrado,
corrección al elegir sin «Comprobar», enlace al BOE, reanudación por la pregunta 3, práctica completa,
`localStorage`, ausencia de errores de página y **12/12 enlaces de convocatoria con su nombre**
(HTTP 200 comprobado con `docs/interfaz/verificar-convocatorias.mjs`).

Revisión final móvil en [`REVISION-FINAL-2026-11-10.md`](REVISION-FINAL-2026-11-10.md). Capturas a
**390 y 1280** en [`docs/capturas/demo-pages/`](capturas/demo-pages/):

| Pantalla | 1280 | 390 |
|---|---|---|
| Portada (convocatorias y cobertura) | `portada-1280.png` | `portada-390.png` |
| Temario con avance por bloque | `temario-1280.png` | `temario-390.png` |
| Mapa de cobertura (40 temas) | `cobertura-1280.png` | `cobertura-390.png` |
| Tema completo | `tema-completo-1280.png` | `tema-completo-390.png` |
| Tema pendiente | `tema-pendiente-1280.png` | `tema-pendiente-390.png` |
| Práctica | `practica-1280.png` | `practica-390.png` |
| Ficha de pregunta | `pregunta-1280.png` | `pregunta-390.png` |
| Lista de prácticas | — | `practicas-390.png` |
| Buscador (`III.20`) | — | `buscador-390.png` |
| Tema III.19 | — | `tema-iii-19-390.png` |
| Tema III.20 | — | `tema-iii-20-390.png` |
| Tema III.26 | — | `tema-iii-26-390.png` |
| Tema IV.30 | — | `tema-iv-30-390.png` |
| Guía de estudio | — | `guia-390.png` |
| Tema V.40 | — | `tema-v-40-390.png` |
| Examen (ajustes) | — | `examen-390.png` |
| Resultado del examen | — | `examen-resultado-390.png` |
| Estadísticas | — | `estadisticas-390.png` |
| Corrección con BOE | `correccion-1280.png` | — |
| Resultado | `resultado-1280.png` | — |

## Límites dichos

- Sin backend: no hay cuentas, ni progreso entre dispositivos, ni banco completo, ni biblioteca.
- El progreso vive en el navegador; borrar datos del sitio lo elimina.
- **Temario completo**: los 40 temas están redactados y con práctica.
- El temario TAI recuperado (33/33 temas, 330 preguntas) está **en local y es privado**: procede de
  material de terceros y no se publica aquí. Inventario y derechos en
  [`TEMARIO-RECUPERADO.md`](TEMARIO-RECUPERADO.md).
- Los PDF de `Downloads\catalogar` son un curso de Computación de Altas Prestaciones; se han copiado
  como complemento de II.13 y no se publican. Cotejo en [`FUENTES-PDF.md`](FUENTES-PDF.md).
- La demo publica únicamente contenido propio; el repositorio principal sigue privado.
