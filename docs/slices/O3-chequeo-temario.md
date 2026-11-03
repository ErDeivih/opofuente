# O3 · Comprobación del temario guardado

Chequeo determinista, tema a tema, de que lo guardado es el tema que pide el enunciado oficial:
epígrafes con apartado, las seis partes de la estructura fija, 10-20 preguntas de autoevaluación con
clave, explicación y evidencia separadas y normas citadas con fecha de consolidación. Informativo y
no bloqueante. Sin modelo, sin red y sin coste.

**Estado: implementado, NO verificado.** `run_8eed83a73d15`, `task_ad51bce9d187`,
`dispatch ctx_63da02451bb7`. La puerta `648dc9aeae21` está roja por entorno (venv del sandbox sin
`argon2-cffi>=25.1.0` pese a estar declarado en `pyproject.toml`/`uv.lock`), no por el cambio; ningún
test llega a colectarse. No se declara ninguna prueba verde.

## Qué he construido

- `apps/api/opofuente/domain/temario_check.py` — módulo puro de dominio. Mide un tema a partir de
  sus primitivas (código, título, epígrafes oficiales y apartados) y devuelve una revisión con
  estado, motivos y las líneas del informe. No importa `application` ni infraestructura.
- `apps/api/tests/unit/test_temario_check.py` — dieciocho pruebas de dominio con una dataclass mínima
  que cumple el protocolo del apartado, sin BD ni red.
- `apps/api/opofuente/tools/apuntes.py` — `--comprobar-temario`, un paso que lee lo guardado,
  imprime el resumen y el detalle en markdown y no pide clave.

## Cómo fluye la información

1. `--comprobar-temario` (repetible con `--tema`) resuelve la ruta al nodo del tema
   (`node_id`) y lee sus epígrafes oficiales (`node`) y sus apartados guardados (`sections`).
2. El tool adapta esas estructuras a las primitivas del dominio y llama a `revisar_temario`.
3. El dominio, en una sola pasada:
   - **Epígrafes:** un epígrafe está cubierto si algún apartado con ese `epigraph_code` tiene
     cuerpo no vacío. Los que no, se listan como `epigrafes_sin_apartado`.
   - **Estructura:** reconoce las seis partes por el **título** del apartado (índice, normativa,
     resumen, mapa conceptual y preguntas) y llama desarrollo al texto que no cae en ninguna de
     las otras cinco.
   - **Preguntas:** dentro de los apartados de preguntas, cada línea que empieza por un número
     (`1.`, `2)`) abre una pregunta. Se aceptan los campos `Respuesta correcta:`/`Clave:`,
     `Explicación:` y `Evidencia:` al principio de línea (con o sin negrita). La clave cuenta solo si
     empieza por `a`, `b`, `c` o `d`; la evidencia no cuenta si falta o si repite literalmente la
     explicación. Se exigen entre 10 y 20 preguntas y ninguna incompleta. Las preguntas de varios
     apartados de preguntas se suman en el orden en que aparecen.
   - **Normas:** extrae las referencias con forma oficial y número (`Ley 39/2015`, `Real Decreto
     3/2010`, `Reglamento (UE) 2016/679`…) y solo da fecha de consolidación si la **misma línea**
     la declara (`texto consolidado`, `última actualización`, `vigente a/desde`…). La fecha de
     promulgación de la norma no cuenta.
4. El estado del tema se deriva de esos datos: `no evaluable` sin epígrafes oficiales, `ausente`
   sin apartados o sin texto, `parcial` si falta cualquier cosa (incluidas preguntas fuera de rango
   o incompletas) y `ok` cuando no falta nada.
5. El tool pinta el resumen corto y, debajo, el detalle markdown con tablas por epígrafe, parte,
   pregunta y norma.

## Ficheros y migraciones

- Nuevo: `apps/api/opofuente/domain/temario_check.py`.
- Nuevo: `apps/api/tests/unit/test_temario_check.py`.
- Modificado: `apps/api/opofuente/tools/apuntes.py` (import, flag y rama; helper
  `_comprobar_temario`).
- Sin migración: no cambia esquema ni escribe datos.

## Patrones y decisiones aplicadas

- **Dominio puro con protocolo.** El dominio recibe primitivas y no depende de `application`, igual
  que `notes_quality` con su protocolo de apartado. Así se prueba sin BD y se puede reutilizar
  desde otro adaptador.
- **Reutilizar `normalise`** de `domain/rag.py` (la misma normalización con la que se indexa) para
  comparar títulos sin acentos ni signos.
- **Heurística estrecha y declarada.** Las partes se buscan en el título, no en el cuerpo; las
  normas, por su forma oficial numerada. Se prefiere un falso `parcial` visible a un `ok` que tape
  huecos.
- **La vigencia no se inventa.** No hay tabla de normas ni catálogo autorizado del BOE: el estado
  de vigencia es siempre `no evaluable` con motivo explícito.
- **La separación clave/explicación/evidencia se mide por campos, no por texto libre.** Cada campo
  tiene que empezar su línea con su etiqueta; así una explicación que menciona la palabra
  «evidencia» no se confunde con el campo. La evidencia que copia la explicación tampoco cuenta:
  el enunciado pide tres cosas, no dos repetidas.
- **No es una puerta.** `pasa` es informativo; no toca la puerta de forma ni la de cobertura por
  preguntas, y no se aplica retroactivamente.
- **Salida doble sin escribir en el repo.** El tool imprime resumen y detalle; el informe vive en
  este documento de slice. Un tool de runtime no escribe en `docs/` ni fuera de
  `OPOFUENTE_DATA_DIR` (regla dura del repositorio).
- **Sin clave ni modelo.** Va antes que cualquier rama que exija `DEEPSEEK_API_KEY`, como `--medir`
  y `--listar`.

## Seguridad y privacidad

- No hay llamada al modelo ni a la red: no se puede gastar dinero ni filtrar texto.
- Solo lectura de la base local; no escribe apartados, hechos ni versiones.
- El texto del tema no se imprime entero: salen referencias de norma, claves de apartado y estados.
- Un contenido importado sigue siendo dato: se mide, no se ejecuta.

## Puertas ejecutadas y resultado

El árbol incluye trabajo ajeno sin commitear de A2 (`build_profile_fixtures.py` y sus documentos),
que **no** forma parte de este cambio y se conserva intacto.

- `uv run --frozen pytest apps/api/tests/unit -q` (puerta `648dc9aeae21`): **roja por entorno**,
  no por el cambio. `ModuleNotFoundError: No module named 'argon2'` al cargar
  `apps/api/tests/conftest.py` → `opofuente.main` → `invitations` → `canjear` →
  `password_hashing`. `argon2-cffi>=25.1.0` está declarado en `pyproject.toml`; el entorno del
  sandbox no lo tiene instalado. Evidencia del árbol con el código de O3:
  `F:\EspacioCodigo\flujo\estado\orca-evidencias\303a875e1f8a8f40764d0a31292f68666ec644f1f2d19b85ad1d9a37239b86ca.json`
  (`code 4`, 16,3 s, `tree_hash bdc3f650…`, `subject_changed_after_gates: false`). Reintentos del
  30/10/2026 sobre el árbol actual: mismo `code 4` y mismo `ModuleNotFoundError: No module named
  'argon2'`, evidencias `0e8b566af41d1fb48a469419473a5dc7fe898dcaff481eb0e42732a87682a131.json`
  (`tree_hash ff47359f…`) y
  `debbdc4f476463fa4277d0fa37eb7353f8e9d0109ff5ed592a257628ea16b69a.json`
  (`tree_hash 17ee6794…`). Repetición del 30/10/2026 tras añadir el chequeo de preguntas:
  evidencia `F:\EspacioCodigo\flujo\estado\orca-evidencias\ca954b6b778b58b44fe7127de51d9e340a4dfc10d6947dbc2562b9ab6025ce52.json`
  (`code 4`, 16,9 s, `tree_hash f294821f…`, `subject_changed_after_gates: false`); repetido sobre el
  árbol final en
  `F:\EspacioCodigo\flujo\estado\orca-evidencias\27ab4c2d47396dcd85a09a434a268ae04157e57d11328fbe16ac4d9354e7a591.json`
  (`code 4`, 20,5 s, `tree_hash b7d960f6…`, `subject_changed_after_gates: false`). Es un bloqueo de
  capacidad del harness (el venv del sandbox no tiene `argon2-cffi`, aunque está en `pyproject.toml`
  y `uv.lock`), no un fallo de pruebas: ningún test llega a colectarse.
  Ningún test llegó a ejecutarse, así que **no** hay evidencia de que las dieciocho pruebas nuevas
  pasen: no se declara O3 verde.
- `pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/gates.ps1` (puerta `9df85043f3a0`):
  **no ejecutada**. Los intentos devolvieron primero `waiting_resources` (capacidad *heavy*
  ocupada) y después el rechazo de política `solo worktree desechable propio`: esta puerta no se
  puede correr desde el workspace de trabajo, solo desde un worktree desechable. No hay evidencia
  de formato, lint, tipos, integración ni build para este árbol.

## Prueba manual

Con el entorno completo (con `argon2-cffi` instalado) y datos autorizados:

```powershell
uv run python -m opofuente.tools.apuntes --tema IV.7 --comprobar-temario
```

Debe salir un bloque `[IV.7] … · temario: …` con epígrafes con/sin apartado, partes que faltan,
recuento de preguntas y cuántas están completas, normas con y sin fecha,
`vigencia: no evaluable (sin catálogo autorizado del BOE)` y, debajo, las tablas de detalle
(incluida la de preguntas con sus tres campos). No debe pedir `DEEPSEEK_API_KEY` ni tocar la base.

## Limitaciones conocidas

- Las seis partes se reconocen por el título: un tema que las tenga con otros nombres saldrá
  `parcial` (visible, no silencioso).
- `desarrollo` cuenta cualquier texto que no sea de las otras cinco partes; un apartado suelto
  cuenta como desarrollo.
- Solo se reconocen normas numeradas con forma oficial. La Constitución o una norma sin número
  citada no aparecen, y por tanto no pueden quedar «sin fecha».
- Una fecha solo cuenta si la línea declara consolidación; una norma con la fecha en otra línea
  saldrá sin fecha.
- Las preguntas se reconocen por numeración al principio de línea y los campos por su etiqueta al
  principio de línea. Un tema con otro formato (preguntas sin numerar, etiquetas dentro de la
  misma línea que la pregunta) saldrá `parcial` aunque las preguntas existan: es un falso negativo
  visible, no un aprobado que tape el hueco.
- La comprobación de la clave es formal (letra `a`-`d`): no verifica que la clave sea la correcta
  ni que la evidencia sostenga de verdad la respuesta.
- No evalúa vigencia, derogación ni corrección de errores: falta catálogo autorizado del BOE.

## Qué se rompe si cambias X

- Cambiar `Estado` o sus valores rompe el contrato de stdout y este informe; el consumidor es
  humano, pero conviene mantener los nombres.
- Cambiar el nombre del protocolo o sus atributos rompe el adaptador de `apuntes.py` y las pruebas.
- Relajar la detección de partes o de normas convierte el chequeo en un `ok` cosmético: es la
  parte que más fácil se degrada.
- Hacer que el chequeo bloquee cambia la semántica de publicación y contradice la decisión de
  mantenerlo informativo.

## Qué criticaría un revisor senior

- Que el reconocimiento de partes por título es frágil y debería vivir en el índice del tema
  (estructura declarada) en vez de en cadenas.
- Que el chequeo no mide si el **contenido** del apartado cubre el epígrafe, solo que existe y
  tiene texto: es una comprobación estructural, no semántica.
- Que el chequeo de preguntas es de forma: cuenta que haya 10-20 con tres campos separados, pero no
  juzga si la clave es correcta, si el distractor es plausible ni si la evidencia sostiene la
  respuesta.
- Que las pruebas no se hayan podido ejecutar en este turno por el entorno; la primera tarea
  pendiente es correr `uv run pytest apps/api/tests/unit -q` con `argon2-cffi` presente.
- Que tampoco se haya podido correr la puerta completa desde este workspace (necesita worktree
  desechable): falta la evidencia de formato, lint, tipos, integración y build.
- Que escribir el informe a mano en `docs/slices` en vez de generarlo desde el tool introduce
  deriva entre lo medido y lo publicado.
