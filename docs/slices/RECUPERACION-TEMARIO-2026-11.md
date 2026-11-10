## Qué he construido

Recuperación del temario TAI ya escrito en sesiones anteriores, sin reescribirlo: 33/33 temas con
apunte, resumen y 10 preguntas por tema; 151 imágenes extraídas de los PDF de los bloques 2-4; todo
consolidado en `data/temario-recuperado/` (ignorado por git) con manifiesto y fuentes.

## Cómo fluye la información

`F:\OpoFuente\APUNTES` + `RESUMENES` + `BANCO\por-tema-de-la-app\TAI` → `recover_temario.py` →
`data/temario-recuperado/temas/*.md`, `preguntas/*.json`, `imagenes/` y `manifest.json`.
La demo pública no consume estos ficheros: el material es de terceros y no se publica.

## Ficheros y migraciones

- `apps/api/opofuente/tools/recover_temario.py` (nuevo): parsea apuntes, banco y PDF; escribe el
  dataset privado.
- `apps/api/tests/unit/test_recover_temario.py` (nuevo): parser, selección de 10 preguntas y
  consolidación con fixtures sintéticos.
- `docs/TEMARIO-RECUPERADO.md` (nuevo): búsqueda, inventario, 33 temas, imágenes, derechos.
- Sin migración de base de datos.

## Patrones y decisiones aplicadas

- No se toca `F:\OpoFuente`: solo lectura. La salida va a `data/` (gitignored).
- Se prefiere lo ya escrito: el apunte se copia con front-matter; no se regenera texto.
- 10 preguntas por tema con respuesta y fuente; se prefieren las que ya traen marca de correcta.
- Estado honesto: si faltara un tema TAI, el manifiesto lo lista y el comando sale con código 1.

## Seguridad y privacidad

- El material recuperado incluye apuntes de academia; queda **privado** y no se publica.
- La demo de GitHub Pages sigue con los 13 temas propios.
- Los originales no se mueven ni se borran.

## Puertas ejecutadas y resultado

- `uv run pytest apps/api/tests/unit -q` → **517 passed**.
- `uv run ruff check apps/api` → verde; `uv run mypy` → 175 ficheros, verde.
- Ejecución real del recuperador: 33/33 temas, 330 preguntas (330 con respuesta), 151 imágenes.

## Prueba manual

`uv run python -m opofuente.tools.recover_temario` → manifiesto con 33 temas y 0 faltantes; abrir
`data/temario-recuperado/temas/I.1.md` y `preguntas/I.1.json`.

## Limitaciones conocidas

- El mapeo TAI → temario común de 40 temas es editorial y no se ha hecho: el común tiene 13 temas
  propios y 27 pendientes.
- Las preguntas recuperadas traen respuesta y fuente, no una explicación larga propia.
- Los PDF de `Downloads\catalogar` son de otra materia (Computación de Altas Prestaciones).

## Qué se rompe si cambias X

- Si cambias la estructura de `APUNTES` o el nombre `N.M`, el parser deja de encontrar temas.
- Si mueves `data/temario-recuperado`, la documentación y el comando apuntan a otra ruta.
- Si publicas el dataset, cambias el régimen de derechos: no hacerlo sin confirmación.

## Qué criticaría un revisor senior

- Que el banco por tema puede tener preguntas repetidas entre modelos A/B; se deduplica por enunciado,
  pero conviene revisar las 33 selecciones.
- Que el mapeo al temario común sigue pendiente y es lo que de verdad acerca esto a la demo pública.
