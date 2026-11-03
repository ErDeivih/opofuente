# O1 reducido — builder de programa A2 y parser de anexos del BOE

Fecha: 2026-10-30 · Slice: O1 (perfiles) · Estado: implementado sin fixture ni migración.

## Qué he construido

- `annex_program(path, *, annex_heading, program_heading)` en
  `apps/api/opofuente/tools/build_profile_fixtures.py`: parser único del temario del BOE, extraído
  del cuerpo de `tai_curriculum`. Reconoce el encabezado de anexo por clase (`anexo_num`/`anexo`),
  localiza el apartado de programa dentro del anexo y construye bloques (encabezados
  `centro_cursiva`), temas (párrafos numerados) y epígrafes (corte del título por punto seguido de
  espacio). Falla si falta el anexo o el apartado; no rellena nada.
- `a2_curriculum(path)`: builder de A2 (Gestión de Sistemas e Informática) sobre `A2_ANNEX =
  "ANEXO IX"` y `A2_PROGRAM = "3. Programa."`. **No** está en `CURRICULUM_BUILDERS`: no hay fuente
  A2 descargada ni registrada en el manifiesto, así que no genera fixture.
- `tai_curriculum` delega en `annex_program` con sus mismos parámetros: su comportamiento y su
  fixture no cambian.
- `apps/api/tests/unit/test_annex_program_builder.py`: pruebas del parser con un XML sintético
  mínimo (bloques, posiciones, rutas, profundidades, reconstrucción del título, corte entre anexos
  y fallo ante anexo o apartado ausentes).

## Cómo fluye la información

1. `load_manifest` verifica que la fuente descargada es la declarada (`sha256`, y `content_sha256`
   en volátiles).
2. `build_curriculum(code, sources)` toma de `CURRICULUM_BUILDERS` la fuente y el builder, y llama
   al builder con la ruta local ya verificada.
3. El builder devuelve el árbol de nodos; `build_curriculum` comprueba que las rutas no se repiten
   y calcula los recuentos.
4. `verify_quotes` comprueba cada cita literal del perfil contra el texto de la fuente antes de
   escribir.

El builder nuevo se inserta en el paso 3 cuando exista entrada en el paso 2; hoy no la tiene.

## Ficheros y migraciones

- Modificado: `apps/api/opofuente/tools/build_profile_fixtures.py` (`annex_program`,
  `A2_ANNEX`, `A2_PROGRAM`, `a2_curriculum`, `tai_curriculum` delegado).
- Nuevo: `apps/api/tests/unit/test_annex_program_builder.py`.
- Nuevo: este documento.
- Sin migraciones: la decisión del coordinador para O1 es no tocar esquema.

## Patrones y decisiones aplicadas

- Un solo parser para los anexos de temario del BOE en lugar de duplicar `tai_curriculum`. El anexo
  y el nombre del apartado son parámetros porque cambian entre convocatorias; el resto de la
  estructura se comprueba, no se supone.
- `position` es la posición dentro del padre y `official_code` conserva el número publicado, igual
  que en los demás builders.
- La partición en epígrafes se valida reconstruyendo el título oficial: si la unión no devuelve el
  título, el builder falla.
- A2 no se cablea «para que esté»: un builder sin fuente verificada no puede producir datos
  trazables, y añadirlo al mapa sugeriría una cobertura que no existe.
- Se conserva `tai-age-2025` tal cual; el id `gsi-a2-2026` queda reservado para cuando exista el
  perfil y su ADR.

## Seguridad y privacidad

- No se ha descargado ni copiado contenido nuevo. El XML de las pruebas es sintético y está escrito
  a mano: no reproduce texto oficial.
- `xml_paragraphs` sigue analizando XML solo después de verificar `sha256`; el builder nuevo no
  abre ninguna ruta que no venga del manifiesto.
- Sin datos personales, secretos ni rutas fuera del workspace.

## Puertas ejecutadas y resultado

- `validar` sobre la puerta unitaria del proyecto (`648dc9aeae21`,
  `uv run --frozen pytest apps/api/tests/unit -q`): **roja**, código 4, 18,3 s, árbol
  `680525f837a9533de13ee425c4e013525d90753cc083685e755e646cbaf3f2e6`, evidencia
  `F:\EspacioCodigo\flujo\estado\orca-evidencias\590decd548024fc9935c4b39215f014727d0b9c5bc0b9101de90793a39b7bdae.json`.
  Causa: `ModuleNotFoundError: No module named 'argon2'` al importar `conftest.py`
  (`infrastructure/password_hashing.py`). Es un incidente de entorno del sandbox, no de este
  cambio, pero **las pruebas nuevas tampoco se han ejecutado**: la colecta no llega a empezar. No
  se declara la puerta verde ni las pruebas pasadas.
- `ruff`/`mypy` no se han ejecutado desde aquí (sin shell). El código nuevo no introduce
  dependencias y respeta el límite de 100 columnas, pero **no está verificado por herramienta**.
- No se declara ninguna puerta verde en este documento.

## Prueba manual

Con la fuente A2 descargada y verificada:

```
uv run python - <<'PY'
from pathlib import Path
from opofuente.tools.build_profile_fixtures import a2_curriculum
nodos = a2_curriculum(Path("data/sources/<fichero-a2>"))
print(sum(1 for b in nodos for t in b["children"]), "temas")
PY
```

Hoy no se puede ejecutar: la fuente no está descargada y `data/sources` no es legible desde este
entorno.

## Limitaciones conocidas

- El builder A2 **no se ha ejecutado contra el BOE real**. Sus pruebas demuestran el parser frente
  a un XML sintético, no que el ANEXO IX tenga encabezado `ANEXO IX`, apartado `3. Programa.` ni
  bloques en `centro_cursiva`. Verificarlo es el primer paso antes de cablearlo.
- Sin fuente A2 no hay `gsi-a2-2026.profile.json` ni `.curriculum.json`, y por tanto no hay perfil
  sembrable ni recuentos oficiales.
- A1 (133 temas) queda fuera de O1: su fuente no está en el manifiesto ni es accesible.
- El anexo de solapes no puede tener filas todavía: ver más abajo.
- Plazas, titulación y requisitos no se han incorporado como datos: no hay cita literal disponible
  en este entorno y un número sin cita no entra en un fixture ni en esta documentación como si lo
  fuera.

## Anexo — solapes C1/A2/A1 (sin datos verificados)

Objetivo: documentar, tema a tema, qué contenido comparten C1 (TAI, ya verificado), A2 y A1, para
que la academia y el estudiante sepan qué estudiar una sola vez. Formato previsto: una fila por
pareja de temas solapados, con `tema_origen`, `tema_destino`, `tipo` (total/parcial) y la cita de
ambos temarios.

Estado real: **no se puede rellenar**. C1 está disponible y verificado, pero A2 y A1 no tienen
fuente accesible en este entorno, y comparar un temario con otro exige el texto de los dos. Escribir
filas «razonables» sería inventar contenido oficial, que es justo lo que el contrato prohíbe. El
anexo se completará como tarea posterior, con los fixtures A1/A2 ya verificados. La tabla de
equivalencias en base de datos (`curriculum_equivalences`) tampoco se crea en O1: requiere ADR y
migración propios.

## Qué se rompe si cambias X

- Si añades A2 a `CURRICULUM_BUILDERS` sin fuente en el manifiesto, `build_curriculum` fallará con
  `KeyError`/fuente ausente al recorrer perfiles; y si además creas el `.profile.json`, `main()`
  intentará verificar citas contra una fuente inexistente.
- Si cambias el corte de epígrafes (`_SENTENCE_BREAK`), se mueven los 134 epígrafes de TAI y fallan
  el recuento por tema y la reconstrucción del título.
- Si relajas `annex_program` para «tolerar» un anexo distinto, TAI y A2 pueden mezclar temarios de
  otros cuerpos: el corte por clase de anexo es lo que lo impide.
- Si cambias `A2_ANNEX`/`A2_PROGRAM`, las pruebas sintéticas siguen pasando aunque el valor sea
  falso: son constantes que solo se validan contra el documento real.

## Qué criticaría un revisor senior

- Que se añade un builder que nunca se ha ejecutado contra su fuente; la respuesta es que está
  deliberadamente desconectado y documentado, pero un revisor puede preferir no tenerlo hasta
  verificarlo.
- Que el XML sintético reproduce la forma que el propio parser espera: prueba el contrato, no la
  realidad del BOE. Es la limitación central y está declarada.
- Que plazas, titulación y requisitos quedan sin documentar pese a la decisión de incluirlos como
  texto citado; sin acceso a la fuente no hay cita, y sin cita no hay dato.
- Que las puertas de formato/tipos no se hayan podido ejecutar desde el trabajador.
