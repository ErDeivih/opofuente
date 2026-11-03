# O5 · Simulacro con baremo oficial y lectura por bloque

Baremo de convocatoria cargado **solo** desde una fuente con procedencia verificable, con la
transformación de puntuación aplicada en backend, y agregado del diagnóstico por bloque sin
convertirlo en una nota. Sin modelo, sin red y sin coste.

**Estado: implementado, NO verificado.** `run_8eed83a73d15`, `task_4624b62f684a`, `dispatch
ctx_b576dc52e1a3`. La puerta unitaria `648dc9aeae21` sigue roja por entorno (el venv del sandbox no
tiene `argon2`) y ningún test llega a colectarse, así que **no se declara ninguna prueba verde**. La
última ejecución, sobre el árbol `eb2ecb3ee377c0ef5833445b4eb84c7bb4314b8f4a128fa6b41ecb9d59067fa3`,
devolvió `code 4` y ese mismo `ModuleNotFoundError`; los intentos previos sobre árboles intermedios
habían devuelto `waiting_resources` (capacidad `heavy` ocupada), no un resultado. Detalle y evidencia
en «Puertas ejecutadas».

## Qué he construido

- `apps/api/opofuente/domain/study.py` — baremo oficial: `BAREMO_NO_IMPORTADO`, `BaremoProcedencia`
  (URL http/https con host, sha256 de 64 hex en minúsculas, cita y fórmula no vacías),
  `Baremo`, `cargar_baremo` (rechaza claves desconocidas, campos faltantes, fechas que no son ISO y
  hash mal formado) y `calificacion_oficial`. Sin baremo cargado o sin transformación declarada, la
  calificación devuelve `available=False` con `reason=BAREMO_NO_IMPORTADO`: **no se aproxima**.
- `apps/api/opofuente/domain/diagnostic.py` — `BlockTally`, `BlockOutcome` y `read_blocks`. El
  agregado reutiliza `wilson_interval` y **declara** en la nota a cuántos temas agrega; un bloque de
  un solo tema lo dice en lugar de aparentar una segunda medición. `DiagnosticReading.blocks` es un
  campo nuevo con valor por defecto `()`.
- `apps/api/opofuente/infrastructure/question_repository.py` —
  `block_titles_of_questions(question_ids)`: el bloque de cada pregunta por el **primer tema aceptado**
  de su mapeo, deducido del prefijo de la ruta (`I.1` → `I`) dentro de la misma convocatoria. Si la
  convocatoria no declara nodos `block` (temas colgando de la raíz), la pregunta se agrupa por su
  propio tema.
- `apps/api/opofuente/application/study_service.py` — `diagnostic_reading` acumula el bloque de cada
  pregunta del conjunto congelado, cuenta los temas distintos de cada bloque y devuelve la lectura con
  `replace(lectura, blocks=read_blocks(...))`. La lectura por tema no cambia.
- Pruebas: `apps/api/tests/unit/test_study_domain.py` (ocho casos de baremo),
  `apps/api/tests/unit/test_diagnostic.py` (cinco casos de bloque) y una aserción en
  `apps/api/tests/integration/test_study_api.py` que fija que la respuesta HTTP **todavía no** publica
  `blocks`.

## Cómo fluye la información

1. `cargar_baremo` lee un documento de baremo ya descargado y comprobado: sin `procedencia`
   (URL, sha256, cita, fórmula) no hay baremo. El sistema no descarga ni interpreta PDFs.
2. `calificacion_oficial(puntuacion, baremo)` devuelve la nota solo si hay baremo y transformación;
   en cualquier otro caso marca el motivo, que es lo que el frontend puede mostrar.
3. Al pedir el diagnóstico de una sesión, `diagnostic_reading` recorre el conjunto congelado y, para
   cada pregunta, toma su primer tema aceptado y su bloque.
4. Los contadores por tema se acumulan como antes; en paralelo se acumulan por bloque, con el
   conjunto de temas distintos que lo componen.
5. `read_blocks` calcula el intervalo de Wilson de cada bloque, ordena por título y redacta la nota
   («N de M en la muestra… el bloque agrega K temas y no es una nota»).
6. La lectura por tema se devuelve intacta; el agregado por bloque viaja en `DiagnosticReading.blocks`
   y **no** se serializa en la respuesta HTTP en este turno.

## Ficheros y migraciones

- `apps/api/opofuente/domain/study.py`
- `apps/api/opofuente/domain/diagnostic.py`
- `apps/api/opofuente/infrastructure/question_repository.py`
- `apps/api/opofuente/application/study_service.py`
- `apps/api/tests/unit/test_study_domain.py`
- `apps/api/tests/unit/test_diagnostic.py`
- `apps/api/tests/integration/test_study_api.py`
- `docs/slices/O5-simulacro-baremo.md` (este documento)

**Sin migración**: no hay columnas nuevas. El bloque se deduce de la ruta de los nodos curriculares
que ya existen. No se toca `packages/contracts/` ni el esquema OpenAPI (ver decisión más abajo).

## Patrones y decisiones aplicadas

- **Procedencia antes que comodidad.** El baremo exige URL, sha256, cita y fórmula. No hay valores por
  defecto ni umbrales inferidos: los PDF del INAP no son fuente de la tabla y no se ha intentado
  deducirla.
- **Agregado honesto.** El bloque no se contesta (se contesta por temas), así que se presenta como
  suma con su intervalo y su número de temas; el texto dice explícitamente que no es una nota.
- **Bloque por ruta, no por posición.** El prefijo de la ruta (`path.split('.')[0]`) es lo que publica
  el temario; cuando no hay nodo `block`, el tema se usa como bloque en lugar de inventar jerarquía.
- **Contrato HTTP intacto en este turno (decisión del coordinador, vía `ask`).** Exponer `blocks`
  obliga a regenerar `packages/contracts/openapi.json`, `src/openapi.d.ts` y a reejecutar las puertas
  de contrato; sin shell no se pueden regenerar, y editarlos a mano daría un verde falso. Por eso el
  campo queda en dominio/servicio, con tests, y la tarea de contrato queda diferida.
- **Tests como candado.** La aserción `assert "blocks" not in lectura` documenta el estado actual: el
  día que se exponga será una decisión explícita con su regeneración de contrato.

## Seguridad y privacidad

- Contenido importado se trata como no confiable: el baremo se valida campo a campo y no se ejecuta
  nada de lo que traiga.
- Sin red: no se descargan PDFs ni se consultan URLs de procedencia; solo se valida su forma.
- Sin secretos nuevos, sin datos reales en pruebas (corpus sintético) y host por defecto `127.0.0.1`
  sin cambios.
- El hash de procedencia es un sha256 en minúsculas; una cadena mal formada se rechaza en la carga, no
  en la calificación.

## Puertas ejecutadas y resultado

| Puerta | Comando | Resultado |
|---|---|---|
| `648dc9aeae21` | `uv run --frozen pytest apps/api/tests/unit -q` | **Roja por entorno.** `code 4`, `ModuleNotFoundError: No module named 'argon2'` (`tests/conftest.py:25` → `opofuente.main` → `api/routes/invitations.py` → `tools/canjear.py` → `infrastructure/password_hashing.py:18`). Ningún test se colecta, así que no dice nada del cambio. Primera ejecución, árbol `5d0d3fc7ffeb9b174499e3242d32bbd00605b46d5e7101f7f6b477ed1dba672d`; después, árbol `95c8d9d2a54d38ba3f3fd161ef29c333ad9aff6a23538c8d2281bc22bec7f28d`, 17,89 s; última ejecución, árbol `eb2ecb3ee377c0ef5833445b4eb84c7bb4314b8f4a128fa6b41ecb9d59067fa3`, 19,62 s, `subject_changed_after_gates: false`. Evidencias: `…\orca-evidencias\d56f4bf4db350971617210ddf64b007a6cc1c7ddcd21d3f96f2faf69fc050110.json`, `…\26aabeec6a9a2d965f9764d7dbcd15ba0b48f2ea39cd76e423f0e671264d66bc.json` y `…\895db21ed05dda663d924ac139dbe2721f01f942b44fcaf8feb5f45ceaf59578.json`. |
| `9df85043f3a0` | `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/gates.ps1` | **No ejecutada**: incluye `export-openapi -Check` y no se puede regenerar el contrato en este turno. |
| Reintentos de `648dc9aeae21` | idem | Varios intentos devolvieron `waiting_resources` (capacidad `heavy` ocupada), no un resultado; los que sí se ejecutaron dieron siempre `code 4` con el mismo `ModuleNotFoundError`. |

Se ha abierto una escalación de harness pidiendo `uv sync --frozen` en el venv del sandbox (o recrear
`.venv` desde `uv.lock`) y la re-ejecución de `648dc9aeae21` sobre este mismo árbol. No se ha tocado
el venv, `pyproject.toml` ni `uv.lock`.

## Prueba manual

Con el entorno resuelto:

1. `./scripts/migrate.ps1` y `./scripts/dev.ps1`.
2. Importar un temario con bloques (`I`, `I.1`, `I.1.1`) y anclar preguntas a temas.
3. Crear un diagnóstico, contestar algunas preguntas y abrir el diagnóstico: la respuesta HTTP sigue
   sin campo `blocks`, y la lectura por tema no cambia.
4. En pruebas, `read_blocks` con un `BlockTally(topics=2, answered=4, correct=3)` devuelve un
   `BlockOutcome` con la nota «3 de 4 en la muestra… agrega 2 temas… no es una nota».
5. Un JSON de baremo sin `procedencia` o con sha256 mal formado debe fallar al cargar
   (`BaremoInvalidError`), no al calificar.

## Limitaciones conocidas

- El baremo oficial **no** está importado: no hay sha256 calculado ni tabla de transformación (prohibido
  inferirla). Hasta que se importe con procedencia, la calificación oficial queda `available=False`
  con motivo `BAREMO_NO_IMPORTADO`.
- El agregado por bloque no se publica por HTTP: vive en dominio/servicio y en tests.
- Sin puertas verdes: la puerta unitaria no colecta por `argon2` y la de gates no se ejecutó.
- La deducción del bloque depende de que las rutas del temario usen el prefijo del bloque; un temario
  con rutas no jerárquicas agruparía por tema (degradación declarada, no silenciosa).

## Qué se rompe si cambias X

- Si quitas la validación de procedencia del baremo, vuelven los umbrales sin cita: se pierde la
  garantía de oficialidad y la calificación pasa a ser una invención.
- Si calculas el bloque por posición del nodo en vez de por la ruta, un temario reordenado cambia el
  agregado sin cambiar el contenido.
- Si expones `blocks` por HTTP sin regenerar OpenAPI y el cliente, las puertas de contrato deben caer;
  si las editas a mano, caen en falso verde.
- Si conviertes la nota del bloque en porcentaje o en «dominio», incumples `06_QUESTIONS` §5.

## Qué criticaría un revisor senior

- Que la tabla de transformación no esté importada deja la calificación oficial sin ejercitar de
  extremo a extremo; solo está probada la ruta «no importado» y una transformación sintética.
- El agregado por bloque no tiene prueba de integración porque no se publica; el cableado del servicio
  queda cubierto solo por lectura de código.
- `block_titles_of_questions` no filtra versiones sustituidas (igual que `node_titles_of_questions`);
  es consistente, pero conviene revisarlo cuando el banco empiece a sustituir versiones.
- Un bloque compuesto solo por preguntas sin tema se agrupa como «sin tema asignado» y cuenta cero
  temas; la nota lo dice, pero la etiqueta puede confundir en la interfaz cuando se exponga.
- La evidencia de puertas es de este árbol (`eb2ecb3e…`) salvo las dos últimas ediciones de este mismo
  documento; no debe asumirse que el árbol está verificado: la puerta no colecta por `argon2`.
