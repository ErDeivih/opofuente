# Reparación de CI: manifiestos, rutas saneadas y plan (31 de octubre de 2026)

Tarea de recuperación sobre el árbol sucio de `ErDeivih/equipo-ia` (HEAD `6483111`). No es un slice
nuevo: arregla el bloqueo de imagen del sandbox y los ocho fallos que impedían que la puerta unitaria
`648dc9aeae21` fuese verde. No he hecho commit, push ni despliegue.

## Qué he construido

1. **Manifiestos npm** (intento anterior de la misma tarea): la raíz declara
   `workspaces: ["apps/web", "packages/contracts"]`; `apps/web/package.json` pide
   `@opofuente/contracts: ^0.0.0`, que es lo que el `package-lock.json` v3 ya resolvía como paquete
   local (`link: true`). El protocolo `workspace:*` era de pnpm y `npm ci` lo rechazaba
   (`source_manifest_invalid`).
2. **`safe_paths.abbreviate` es multiplataforma**: parte la ruta sobre `/` y `\` y quita la raíz
   (letra de unidad, UNC, `/` inicial) como texto. Antes usaba `Path` del anfitrión y, en el
   contenedor Linux, `C:/Material` se abreviaba como `…/C:/Material` y no como `…/Material`; una raíz
   suelta (`C:/`) se colaba entera.
3. **`safe_paths.redact_paths` cubre rutas arraigadas a la unidad**: `_WINDOWS_PATH` acepta también
   `\carpeta\fichero.ext` (una barra invertida inicial), que es como aparece una ruta POSIX en un
   mensaje redactado a separadores Windows. Antes `_safe_message` publicaba la ruta temporal entera.
4. **`safe_zip.inspect_zip` normaliza el nombre a `/` antes de validarlo**, igual que hace `zipfile`
   en Windows. Así `..\x.txt` se rechaza como traversal («sale de la carpeta»), con el mismo
   resultado en Linux y en Windows. `check_member_name` sigue rechazando la barra invertida cuando
   se le pasa un nombre sin normalizar (contrato de la prueba directa de la guarda).
5. **`PlanService.plan` delega en `SqlAlchemyPlanRepository.plan`**, que recalcula el plan con
   `planificar` a partir del calendario guardado y los temas. `progreso` y `hoy` ya llamaban a
   `self.plan`; con el repositorio como costura, el plan es el mismo que ve la pantalla y el
   progreso cuenta las semanas que el plan fijo de las pruebas declara.

## Cómo fluye la información

ZIP → `inspect_zip` normaliza el nombre → `check_member_name` valida traversal, barra invertida,
unidades/ADS, dispositivos reservados y sufijos que Windows recorta → `ZipMember` ya normalizado.
Errores → `redact_paths` recorta unidades, UNC y rutas arraigadas → `abbreviate` deja solo los
últimos componentes → `_safe_message` guarda/publica el texto sin rutas.
Calendario guardado + temas → `SqlAlchemyPlanRepository.plan(hoy)` → `planificar` →
`PlanService.plan`/`progreso`/`hoy`.

## Ficheros y migraciones

Sin migraciones. Cambiados: `apps/api/opofuente/infrastructure/safe_paths.py`,
`apps/api/opofuente/infrastructure/safe_zip.py`,
`apps/api/opofuente/infrastructure/plan_repository.py`,
`apps/api/opofuente/application/plan_service.py`, `apps/web/package.json` y `package-lock.json`
(estos dos, del intento anterior). No he tocado pruebas.

## Patrones y decisiones aplicadas

- **Mismo resultado en Windows y en Linux**: lo que se sanea o se valida es una ruta de Windows, así
  que la lógica no depende de `Path` del anfitrión.
- **La costura es el repositorio**: el dominio calcula, la infraestructura compone los datos y el
  servicio no duplica el reparto.
- Se conserva el mensaje específico de cada defensa; la normalización del nombre ocurre en la capa
  que lo va a expandir, no en la guarda que lo valida.

## Seguridad y privacidad

Se refuerza el saneado: ninguna ruta absoluta de Windows (unidad, UNC o arraigada) debe llegar a
`jobs.error_message` ni a la API. El traversal de ZIP se cierra igual en Linux, donde antes el
mensaje era genérico de barra invertida y el nombre crudo podía escapar de la carpeta al expandirse.

## Puertas ejecutadas y resultado

- `validar --gate 648dc9aeae21` («unitarias de la API»): **verde**, `1091 passed, 3 skipped`,
  código 0, `subject_changed_after_gates: false`. El `tree_hash`, el id de evidencia y los segundos
  exactos de la pasada final sobre este mismo árbol van en el recibo de entrega (`worker_done`); la
  ejecución anterior sobre el árbol sin este documento dio `eca694e670acc1a6ebfe312dc212c89466ba937b3d6e28f0c3b7e2d0663f7153`.
- `validar --gate 9df85043f3a0` (`scripts/gates.ps1` completo): **no ejecutada**; el orquestador la
  rechaza con «solo worktree desechable propio». Queda pendiente para el cierre de CI del
  coordinador sobre un worktree desechable.

## Prueba manual

1. `POST /documents` con un ZIP que contenga `..\x.txt` → 422 con «sale de la carpeta (..)» también
   en Linux; nada escrito fuera del destino.
2. Error de trabajo con ruta `C:\Users\…\Material\…` o `\workspace\…\…` → `jobs.error_message` no
   contiene la ruta absoluta.
3. `GET /plan` y `GET /plan/progress` con un plan guardado → el progreso desglosa los mismos bloques
   que el plan devuelto.

## Limitaciones conocidas

- Los nombres de ZIP con barra invertida pero sin traversal (`apuntes\tema.txt`) se aceptan y se
  tratan como `/`: es lo que ya hacía `zipfile` en Windows y lo que espera la puerta.
- El plan se recalcula en cada lectura; no hay caché ni estado de lectura por tema.
- La puerta completa `gates.ps1` puede tardar ~54 min y comparte plaza de pruebas pesadas.

## Qué se rompe si cambias X

- Si `abbreviate` vuelve a usar `Path`, los mensajes dejan de coincidir entre Windows y Linux y
  vuelven a publicar la unidad o la raíz.
- Si `inspect_zip` valida el nombre crudo, `..\x.txt` vuelve a dar «barra invertida» en Linux y la
  prueba de traversal de ZIP falla.
- Si `PlanService.plan` vuelve a construir el plan con `self._planes.temas()`, `progreso`/`hoy` dejan
  de hablar del mismo plan que el repositorio y los dobles de prueba dejan de servir.

## Qué criticaría un revisor senior

- Que la normalización de nombres de ZIP viva en `inspect_zip` y no en un único punto compartido con
  la extracción; hoy la coherencia depende de que `extract_zip_safely` use `member.name`.
- Que `PlanService` dependa del método concreto del repositorio SQLAlchemy en vez de un puerto
  explícito; el `type: ignore` de las pruebas lo delata.
- Que no haya prueba de integración del ZIP con nombre normalizado en extracción real, solo unitaria
  de la inspección.

## Puerta completa 9df85043f3a0: bloqueada por prerequisito del arnés (1 de noviembre de 2026)

Reproducción exacta sobre el árbol actual:

- Comando: `validar` con `project=opofuente`, `gate=9df85043f3a0`.
- `tree_hash` del candidato: `d0185dd4834b88c8a5e1034b61bf0a9f57d627be65d575c2a8639915d2a46e19`.
- HEAD `6483111dfd7e7939aabb260cd28abd98b146f5c2`, rama `ErDeivih/equipo-ia`.
- Resultado: `stage=prerequisite`, `seconds=0`, `tests_executed_by_this_lookup=false` y mensaje
  literal:

```
Error: public_fixture_hash_mismatch: gc-boe-convocatoria-xml; no actualizar el hash ni fabricar la fuente
```

Es un rechazo del prerequisito del orquestador antes de arrancar el guion, no un fallo del producto
ni del slice: `fixtures/` no aparece modificado frente a HEAD. `fixtures/profiles/manifest.json`
declara para `gc-boe-convocatoria-xml` `sha256=263900393c7b…` (bytes) y `volatile=true` con
`content_sha256=920b696e…` (texto visible); la copia local en `data/sources` dio `9f6b802314ac…`,
porque el BOE republicó ese XML (`docs/hitos/ESTADO-DE-LA-FASE-3-2026-10-20.md:245`). El código del
repositorio compara las fuentes volátiles por su texto (`build_profile_fixtures.verify_sources`, con
prueba unitaria), pero el prerequisito del orquestador usa un hash protegido distinto que no se
refresca desde un worker, y `scripts/**` y `data/sources` no son accesibles desde el sandbox del
trabajador.

Evidencia verde disponible (no re-ejecutada ni sustituida):

- `648dc9aeae21` (unitarias API): verde sobre `tree_hash=d0185dd4…`, evidencia
  `7a95fbcf9033a1478eb61ef6a8af8f113cb29f16e68a522077bede51dbb85f0d`,
  `tests_executed_by_this_lookup=false`.

Escalación registrada (decisión del coordinador, 1 de noviembre de 2026, hilo
`msg_cfba3924b2b9`): no tocar `fixtures/profiles/manifest.json`, ni el `sha256`, ni `data/sources`,
ni regenerar la fuente; el entorno CI con acceso a `scripts/**` y `data/sources` debe ejecutar
`9df85043f3a0` en un worktree desechable propio sobre `tree_hash=d0185dd4…` y devolver fichero de
evidencia, ID de puerta y resultado. Si el hash protegido debe refrescarse, lo decide y ejecuta
quien custodia el guard, nunca el worker.

### Verificación posterior en el sandbox y reparto de custodia (1 de noviembre de 2026)

Reintento de reparación sobre el árbol con la puerta unitaria verde. Para separar «fichero ausente»
de «hash distinto» se añadió el sondeo público de solo lectura `_probar-vista-previa.mjs` (existencia,
tamaño, `sha256` de bytes y huella de texto de cada `sources[]` del manifiesto; no imprime contenido),
registrado como puerta `5a471fa62eaf`. Resultados:

- `5a471fa62eaf` (sondeo): verde, 2,3 s, evidencia
  `02e09ed033e6149cadbd48646f52edb7dad21c7db405a6633c0a902a88b7e26f`, sobre
  `tree_hash=9d3a44e861e64bc7ea84c6f493b20c205624a8740af47b346bb99258ba3fe236` y
  `execution_profile_hash=2c78892a894ed06614a3134f10e447b06664b5270e87b3e73083f1384c484154`.
- El sandbox ve `data/sources`, pero **no** recibe `data/sources/gc-2026-boe.xml`
  (`existe:false`), ni varias fuentes de celador; los ficheros TAI sí están. Es decir, el
  prerequisito aborta antes de copiar esa fuente y compara contra una copia protegida que vive fuera
  de las fuentes públicas legibles por el trabajador.
- `fixtures/profiles/manifest.json` sigue **sin cambios** frente a HEAD (`git_estado` con diff vacío
  para ese fichero).
- `validar` con `9df85043f3a0` se mantiene en `stage=prerequisite`, `0 s`, mismo mensaje literal. No
  se declara verde.

Decisión del coordinador en el hilo `msg_7e71979b18e8` (respuesta `msg_0e1f46f486c7`): opción A,
ejecutada por el custodio del guard y no por el trabajador; no tocar el manifiesto, sus `sha256` ni
`data/sources`; conservar `_probar-vista-previa.mjs` y la puerta `5a471fa62eaf` en el árbol final; y
abrir escalación pidiendo que, tras verificar que la huella de texto sigue siendo `920b696e…`, se
refresque el hash público protegido de `gc-boe-convocatoria-xml` al `9f6b802314ac…` completo, se
documente y se ejecute `9df85043f3a0` en un worktree desechable propio sobre el `tree_hash` final. El
trabajador no dispone de capacidad para custodiar o refrescar ese hash: si el arnés no la expone, debe
decirse tal cual en la escalación en vez de simularla.

Estado: CI completo **pendiente de custodia**. La batería de 18 puertas sigue sin ejecutarse
(`prerequisite`), no se declara verde ni roja de producto. Sin commit, push, merge ni despliegue. Esta
nota se actualizó después de la última validación verde del sondeo, así que el `tree_hash` del
workspace vuelve a diferir por este cambio documental.

## Cierre del reintento por capacidad externa del arnés (1 de noviembre de 2026)

Reintento de reparación sobre el árbol y perfil vigentes de la Task `task_8c1d0f8fe966`, Dispatch
`ctx_dcb251f9db0d`. Reproducción exacta:

- `tree_hash=43029d71d6224efd1167012b76ab7d1a7be1ce8b541bd1a6399f7c33a1659ea9`,
  `execution_profile_hash=2c78892a894ed06614a3134f10e447b06664b5270e87b3e73083f1384c484154`,
  HEAD `6483111dfd7e7939aabb260cd28abd98b146f5c2`, rama `ErDeivih/equipo-ia`.
- `validar` con `project=opofuente`, `gate=9df85043f3a0`: `stage=prerequisite`, `seconds=0`,
  `tests_executed_by_this_lookup=false` y mensaje literal
  `Error: public_fixture_hash_mismatch: gc-boe-convocatoria-xml; no actualizar el hash ni fabricar la fuente`.
- Ese rechazo lo emite el **runner Orca antes de arrancar `scripts/gates.ps1`**; no es una salida del
  producto ni del slice. La cadena `public_fixture_hash_mismatch` no aparece en ningún código del
  repositorio accesible al trabajador; solo en esta nota.
- Sondeo de solo lectura `_probar-vista-previa.mjs` por `diagnosticar` (evidencia
  `e6a1b42d26523cc3505f10388f5efe025df95fd7d9b7fb05b9d359067aa34717`, sobre el `tree_hash`
  anterior): en el sandbox `/workspace/data/sources` **no existe** `gc-2026-boe.xml` ni las fuentes
  BOCYL de celador; los `tai-*` sí existen y coinciden con su `sha256` declarado. Es decir, el
  prerequisito aborta antes de copiar la fuente y compara contra una copia protegida fuera de las
  fuentes públicas legibles por el trabajador.
- `fixtures/profiles/manifest.json` sigue **sin cambios** frente a HEAD (`git_estado` con diff vacío
  para ese fichero); no se ha tocado `sha256`, `volatile`, `content_sha256` ni `data/sources`.

Evidencia verde conservada sobre `tree_hash=43029d71…` (no re-ejecutada ni sustituida): puertas
`648dc9aeae21` (unitarias API) y `5a471fa62eaf` (sondeo). El CI completo sigue **NO declarado
verde**: la puerta `9df85043f3a0` no llega a ejecutar sus 18 comprobaciones.

Decisión del coordinador en el hilo `msg_b3050b9635c6` (respuesta `msg_574c65056c8b`): cerrar la
Task como **failed solo por prerequisito del harness, no por el producto**, sin tocar el manifiesto ni
las fuentes, y registrar escalación al custodio del guard/runner con dos vías técnicas posibles:
aprovisionar el fixture oficial `gc-2026-boe.xml` en el sandbox, o refrescar el hash protegido. La
decisión es del custodio, no del trabajador. Sin commit, push, merge ni despliegue.

Esta nota se escribe después de las validaciones verdes citadas, así que el `tree_hash` del workspace
difiere del probado únicamente por este cambio documental.

## Reparación de `verify_sources`: los bytes exactos mandan (1 de noviembre de 2026)

Task `task_8c1d0f8fe966`, Dispatch `ctx_b573a9c734ef`, Run `run_8eed83a73d15`. El coordinador
corrigió el arnés (`prepare_sources` ignoraba `volatile`/`content_sha256`) y pidió la causa
reproducida en producto. La reproducción dio el fallo real de la puerta `648dc9aeae21`
(`AssertionError: assert '00dde869…' == '8a7bce83…'`) y el sondeo `5a471fa62eaf` demostró que
`data/sources/celador-2022-bocyl-orden.pdf` tiene **exactamente** los bytes declarados
(`c1cbedf37e44…`, `size=1052182`), mientras que su `content_sha256` declarado (`8a7bce83…`) se había
calculado sobre otra descarga.

**Causa:** `verify_sources` usaba la proyección de texto como comprobación **exclusiva** de toda
fuente `volatile` (`continue` antes de comparar bytes). Una fuente volátil cuyos bytes coinciden con
el original archivado se rechazaba si su texto proyectado no coincidía con la huella guardada. La
huella de contenido existe porque algunos servidores cambian identificadores de renderizado entre
descargas; es un respaldo para bytes variables, no una prueba más fuerte que el propio documento.

**Arreglo:** se calcula primero el `sha256` de bytes para todas las fuentes; si coincide con el
manifiesto, la fuente se acepta. Solo si no coincide y la fuente es `volatile` se compara
`content_fingerprint` con `content_sha256` (y una volátil sin huella sigue siendo error explícito).
No se ha tocado el manifiesto, ni `data/sources`, ni ninguna huella. Se añadió la regresión unitaria
`test_una_fuente_volatil_con_los_bytes_exactos_no_se_rechaza_por_su_proyeccion` y se ajustó
`test_las_paginas_que_cambian_en_cada_descarga_se_verifican_por_bytes_o_por_texto` para exigir la
huella de contenido **solo** cuando los bytes difieren. La prueba anterior afirmaba la invariante
equivocada (proyección = bytes) y por eso era roja con el original correcto.

**Ficheros:** `apps/api/opofuente/tools/build_profile_fixtures.py` (docstring de módulo, `Source`,
`verify_sources`), `apps/api/tests/unit/test_profile_fixtures.py`. Sin migraciones.

**Puertas sobre el árbol intermedio (antes de esta nota):** `648dc9aeae21` verde,
`1102 passed, 3 skipped, 33.96 s`, `tree_hash=e5f4b90f2a32a5fa01cd905015abd28ec43b803a0e10fa6cdc27d38ea78221da`,
evidencia `8de594f184db36d09ca4aa0838127b9986a554b6a26539e7a52661197413bb72`; caducada para el
árbol final por este cambio documental y re-ejecutada después de escribirlo.

**Limitación:** si una fuente volátil se republica con bytes distintos y el mismo texto, el respaldo
sigue funcionando; si se republica con bytes exactos distintos de los declarados y cambia el texto,
se rechaza, que es lo correcto. El mensaje de error de huella volátil menciona `--refresh-content`,
que actualiza `content_sha256` solo tras verificar las citas.

## La puerta completa ya arranca; el bloqueo actual es del entorno (1 de noviembre de 2026)

El arreglo del arnés (`prepare_sources` ya respeta `volatile`/`content_sha256`) resolvió el
`public_fixture_hash_mismatch`: la puerta `9df85043f3a0` **ya supera el prerequisito de fixtures** y
llega a ejecutar `scripts/gates.ps1`. Falla a los **6,5 s**, no a los 54 min, en la **primera**
comprobación (`ruff format --check`) porque `scripts/common.ps1:119`
(`Assert-OpoFuentePuertosLibres`) invoca `Get-NetTCPConnection`, y el PowerShell del sandbox Linux no
incluye ese cmdlet:

```
The term 'Get-NetTCPConnection' is not recognized as a name of a cmdlet,
function, script file, or executable program.
```

No es un fallo del producto ni de `verify_sources`: es capacidad del entorno de ejecución. Evidencia
del rechazo: `686eaeee5228dcbcc8969d285cb5219afb1ce81e64751bd855f120683b9445f7`, sobre
`tree_hash=25305c7c44fd696a8db3be8945d32376705037d202bceaaafbf38b67495f4eba`. Decisión del
coordinador en el hilo `msg_f1c6713f7288` (respuesta `msg_578841ac6d01`): opción (a), sin editar
`scripts/common.ps1` (ruta no pública); el custodio del harness ejecuta `gates.ps1` en PowerShell de
Windows con `Get-NetTCPConnection`, o hace que el arnés degrade el chequeo de puertos a no-op cuando
el cmdlet no exista. Las puertas de producto conservadas como verdes sobre el árbol vigente son
`648dc9aeae21` (unitarias API, evidencia `79f219c0…`) y `5a471fa62eaf` (sondeo, evidencia
`4f60df0d…`); no se declara el CI completo verde. Sin commit, push, merge ni despliegue.

## Cierre de la Task de reparación por capacidad del arnés (2 de noviembre de 2026)

Task `task_8c1d0f8fe966`, Dispatch `ctx_2e24a58409fe`, Run `run_8eed83a73d15`. Reproducción exacta
sobre el árbol vigente, antes de tocar esta nota:

- `tree_hash=78f77d412639aa624314ebb875b37ca0d1af219b48f6e4f54173b109a731fe69`,
  `execution_profile_hash=74b3b1d8a8ad6b2bf980026584e4cf4c340208524325fd92eb12d31d23c1babb`,
  HEAD `6483111dfd7e7939aabb260cd28abd98b146f5c2`, rama `ErDeivih/equipo-ia`.
- `validar(9df85043f3a0)`: `ok=false`, `code=1`, `9.34 s`, sin `stage=prerequisite` (el
  prerequisito de fixtures ya está superado). Aborta en la primera comprobación,
  `=== 1. ruff format --check ===`, en `scripts/common.ps1:119`
  (`Assert-OpoFuentePuertosLibres`) con el literal
  `The term 'Get-NetTCPConnection' is not recognized as a name of a cmdlet, function, script file, or executable program`.
  Evidencia: `7f57713d41520d4528bc470fda47f6df58c6e47e6cd7fb77010f9afa79acfbe4`,
  `subject_changed_after_gates: false`.
- `candidate_coverage` sobre ese árbol: verdes `648dc9aeae21`
  (`c75760709f0935bcbe985d98fb01a28b478612b80eb384891f2c3a2abf95f855`, 1102 passed/3 skipped) y
  `5a471fa62eaf` (`51c726343c47c8bd1279b0a16904d1c6b5acdefb755b0f972547f705bb27dd2d`); la única
  pendiente es `9df85043f3a0`.

Causa aislada: es capacidad del intérprete, no lógica de producto. `Get-NetTCPConnection` es un
cmdlet del módulo `NetTCPIP`, ausente en el PowerShell del sandbox Linux; la guarda de puertos de
`scripts/common.ps1` lo invoca antes de cada una de las 18 comprobaciones, así que `gates.ps1` muere
antes de ejecutar la comprobación 1 y ninguna fuente publicada del producto puede evitarlo. El
fichero que causaría el arreglo (`scripts/common.ps1`) está fuera de las fuentes públicas del
trabajador: `read`, `grep` y `edit` lo rechazan por política. El coordinador (hilo
`msg_f22a5c61df5b` → respuesta `msg_89db7a23c210`) no autoriza tocarlo y mantiene que pertenece al
arnés/custodio.

Necesidad concreta para cerrar la puerta (una de dos):

1. Versión portable de `Assert-OpoFuentePuertosLibres` que degrade a aviso/no-op cuando
   `Get-NetTCPConnection` no exista, conservando el comportamiento en Windows y actualizando su
   prueba si la hubiera; o
2. ejecución de `scripts/gates.ps1` en PowerShell de Windows sobre el `tree_hash` final, devolviendo
   el recibo de `9df85043f3a0`.

No se ha tocado `fixtures/profiles/manifest.json`, sus `sha256`/`volatile`/`content_sha256`, ni
`data/sources`, ni `scripts/**`. Tras esta nota se re-ejecutan las dos puertas verdes para que
certifiquen el árbol final; el CI completo sigue **NO declarado verde** (no llega a ejecutar sus 18
comprobaciones) y no hay commit, push, merge ni despliegue.

## Reproducción separada en el Dispatch de reparación `ctx_c49ce1e1e721` (2 de noviembre de 2026)

Task `task_8c1d0f8fe966`, Run `run_8eed83a73d15`, sobre el perfil vigente
`74b3b1d8a8ad6b2bf980026584e4cf4c340208524325fd92eb12d31d23c1babb` (ya no el `2c78892a…` de los
cierres anteriores). Reproducción sobre el árbol exacto
`tree_hash=25ad3f1e73c89f992eb3e5c5b3fa35e3ac1140e1765312d533c9ac4b160dec42`, HEAD
`6483111dfd7e7939aabb260cd28abd98b146f5c2`, rama `ErDeivih/equipo-ia`:

- `validar(9df85043f3a0)`: `ok=false`, `code=1`, `4.248 s`, evidencia
  `ae686ac1d5a397fff4bb147a81e409e15d28b5001032c5aed95ed9bbba6c3373`, sin `stage=prerequisite`.
  Aborta en `=== 1. ruff format --check ===`, dentro de `/workspace/scripts/common.ps1:119`
  (`Assert-OpoFuentePuertosLibres`), con el literal
  `The term 'Get-NetTCPConnection' is not recognized as a name of a cmdlet, function, script file, or executable program`.
- `648dc9aeae21` (unitarias API): **verde**, `1102 passed, 3 skipped`, 64,2 s, evidencia
  `52f9ec9faf455cf1be171c6dd913d115d20774360bcf30d321045c79ac2822ad`.
- `5a471fa62eaf` (sondeo de fuentes): **verde**, 3,0 s, evidencia
  `1495353e9223b7ae20fc183c3914728b1ebd460abe56c727cc5cc431e3216cbe`.

El bloqueo de fixtures queda **resuelto en este entorno**: el sondeo ve `data/sources/gc-2026-boe.xml`
con `sha256=9f6b802314ac857a984621f57bdf452f88aed1da0ec81050de2838b9632428cd` y huella de texto
`920b696e1057dfdbc4c0db04b909048cc57e45063a0fd4c3ca2d2faa23e9d29e`, coherente con el manifiesto
(`declarado=263900393c7b…`, `volatile=true`, `content_sha256=920b696e…`) y con la reparación de
`verify_sources`. Por tanto el único rojo restante es la guarda de puertos del arnés invocada antes de
la comprobación 1.

`scripts/common.ps1` sigue fuera de las fuentes públicas del trabajador (`read`/`edit` rechazados por
política de rutas), así que el arreglo no es aplicable desde aquí. Decisión del coordinador (hilo
`msg_7f48f9334ff6` → respuesta `msg_545918576e56`): opción B, escalar al custodio del arnés; la
opción C (PowerShell de Windows) queda como respaldo del mismo custodio. Escalación registrada:
`msg_1ebfa28f230c`, pidiendo guarda portable de `Assert-OpoFuentePuertosLibres` (usar
`Get-NetTCPConnection` solo si existe; en Linux aviso/no-op) con su prueba, y reejecución de
`9df85043f3a0` sobre `tree_hash=25ad3f1e…` con fichero de evidencia e ID, o ejecución en PowerShell de
Windows sobre el mismo árbol.

No se ha tocado `fixtures/profiles/manifest.json`, sus hashes, `data/sources`, ni `scripts/**`; no hay
commit, push, merge ni despliegue. El CI completo sigue **NO declarado verde**. Esta nota se escribe
después de las validaciones citadas, así que el `tree_hash` del workspace difiere del probado solo por
este cambio documental.

## Formato de `apps/api` reparado; queda solo la guarda de puertos del arnés (2 de noviembre de 2026)

Task `task_3509b0b3e522`, Dispatch `ctx_c2a4d4facf39`. Decisión del coordinador (hilo
`msg_37182cd72bd7` → respuesta `msg_4a63fbd789e5`): no ampliar `source_globs`, no editar
`scripts/common.ps1` (fuera del workspace) y atacar el primer rojo dentro de `apps/api`.

- Reproducción del rojo de la puerta `9df85043f3a0`: aborta en `scripts/common.ps1:119`
  (`Assert-OpoFuentePuertosLibres`) con
  `The term 'Get-NetTCPConnection' is not recognized…`, antes de ejecutar la comprobación 1.
  Evidencia `18f7c60630b66d483f4e32bcb148902af0f6367b8e6b86f2a8b2a49f4fe4aa6b` sobre
  `tree_hash=5f9bc9568c9f7257f8438fb92bed3e83cf7e2b9748312299ca6a27bbcc0696c8`.
- Estado del formato en ese árbol: `uv run --frozen ruff format --check apps/api` daba `status=1`,
  «15 files would be reformatted». Evidencia diagnóstica
  `c43b072b07b06be6d195310d1c46545b7fc4c6cfb26687f61710aaffd7e8a0f0`, `tree_hash=1bb44829…`.
- Arreglo: formato de ruff (solo disposición, sin cambio de comportamiento) en 15 ficheros de
  `apps/api`: `opofuente/api/routes/student.py`, `opofuente/application/plan_service.py`,
  `opofuente/application/topic_pdf.py`, `opofuente/domain/convocation_registry.py`,
  `opofuente/domain/study_plan.py`, `opofuente/domain/temario_check.py`,
  `opofuente/infrastructure/topic_pdf.py`, `opofuente/tools/build_profile_fixtures.py`,
  `tests/integration/test_plan_api.py`, `tests/integration/test_student_notes_api.py`,
  `tests/unit/test_profile_fixtures.py`, `tests/unit/test_study_plan.py`,
  `tests/unit/test_temario_check.py`, `tests/unit/test_topic_pdf.py` y
  `tests/unit/test_topic_pdf_render.py`.
- Verificación: sonda diagnóstica (la `_probar-vista-previa.mjs` con una comprobación temporal de ruff,
  retirada después) → `ruffFormatCheck.status=0`, «515 files already formatted». Evidencia
  `2bdaca66897fa0a0b6dff06e285ab75a21bba6cf4cc3939f7d5d784a4cae507d`,
  `tree_hash=e316dca036c51d43d763987295fed5478970a44d3b5927ae3023616a5d05a68e`; pasos intermedios
  `82c9e4669da0e9e163c33f7c04907b024525b00ffaa22bf68c71b0c44eb60321`.
- `_probar-vista-previa.mjs` queda restaurado a su contenido de solo lectura (huellas de fuentes del
  manifiesto); no se tocó `fixtures/profiles/manifest.json`, ni sus hashes, ni `data/sources`, ni
  `scripts/**`, ni se relajó ninguna prueba.

Escalación al custodio del arnés (misma necesidad ya registrada): guarda portable de
`Assert-OpoFuentePuertosLibres` (usar `Get-NetTCPConnection` solo si `Get-Command` lo encuentra;
en Linux aviso/no-op, mismo comportamiento en Windows, con su prueba), o ejecución de
`scripts/gates.ps1` en PowerShell de Windows sobre el `tree_hash` final con recibo de
`9df85043f3a0`. Esta nota se escribe antes de re-ejecutar las puertas, así que los resultados de
`5a471fa62eaf`, `648dc9aeae21` y `9df85043f3a0` sobre el árbol final van en el recibo de entrega.
El CI completo sigue **NO declarado verde** y no hay commit, push, merge ni despliegue.

## Nuevo intento de batería completa; el árbol citado no existe y la guarda del arnés sigue roja (2 de noviembre de 2026)

Task `task_638861d90964`, Dispatch `ctx_42b899dc680a`, Run `run_8eed83a73d15`, con el encargo de
completar la evidencia del árbol `17b57d2f02d42963760366e5bcec7e1568de2e700ef2c846379697ffe61bee31`
para la puerta pendiente `9df85043f3a0`.

- Ese `17b57d2f…` **no corresponde al workspace actual**: `git_estado` da
  `tree_hash=04bd87b3db5c0b0ef3aef92ab82accdd11e835b9d72946c5b1a71c9c78597216`, HEAD
  `6483111dfd7e7939aabb260cd28abd98b146f5c2`, rama `ErDeivih/equipo-ia`, y la cadena no aparece en
  ninguna fuente pública del workspace. La reproducción se hace, por tanto, sobre el árbol real actual.
- Reproducción previa a esta nota: `validar(9df85043f3a0)` sobre
  `tree_hash=04bd87b3…`/`execution_profile_hash=74b3b1d8…` devuelve `ok=false`, `code=1`, `2.55 s`,
  evidencia `93fecce4cd45b4241344ea75a659366d9583b1b6d9bb41fd3a8ca04e70f86c2d`, y aborta en
  `=== 1. ruff format --check ===` dentro de `/workspace/scripts/common.ps1:119`
  (`Assert-OpoFuentePuertosLibres`) con
  `The term 'Get-NetTCPConnection' is not recognized as a name of a cmdlet, function, script file, or executable program`.
  La cobertura de ese árbol ya tenía verdes `648dc9aeae21` y `5a471fa62eaf`.
- La causa sigue siendo capacidad del intérprete del sandbox, no lógica de producto, y el fichero que
  la corrige (`scripts/common.ps1`) sigue fuera de las fuentes públicas del trabajador
  (`read`/`grep`/`edit` rechazados por política). No se ha tocado `scripts/**`, ni
  `fixtures/profiles/manifest.json`, ni sus hashes, ni `data/sources`, ni ninguna prueba.
- Necesidad para cerrar la puerta, ya escalada y sin cambio: guarda portable de
  `Assert-OpoFuentePuertosLibres` con prueba, o ejecución de `scripts/gates.ps1` en PowerShell de
  Windows sobre el `tree_hash` final con recibo de `9df85043f3a0`.

Esta nota se escribe **antes** de la batería final de esta Task; sus resultados y evidencias van en el
`worker_done`. El CI completo sigue **NO declarado verde** y no hay commit, push, merge ni despliegue.

## Batería completa en un turno CI sobre el árbol vigente (2 de noviembre de 2026)

Task `task_638861d90964`, Dispatch `ctx_68809cd5fe85`, Run `run_8eed83a73d15`, con el mismo encargo:
completar la evidencia del árbol `17b57d2f02d42963760366e5bcec7e1568de2e700ef2c846379697ffe61bee31`
para la puerta pendiente `9df85043f3a0`.

- `git_estado` sigue sin encontrar `17b57d2f…` en este workspace; el árbol real antes de esta nota es
  `tree_hash=65e788814a273ac9c3d6bbf973819d7a9e34039949e5530382bc79697b1c1e55`, HEAD
  `6483111dfd7e7939aabb260cd28abd98b146f5c2`, rama `ErDeivih/equipo-ia`. La reproducción se hace sobre
  el árbol real, como en los intentos anteriores.
- Sobre ese árbol ya constan verdes `648dc9aeae21` (unitarias API, evidencia
  `4d0e332ea0c6861f80f12f62294a1795a9efd82ec1b9f70a19286cf9db5bfd15`) y `5a471fa62eaf` (sondeo,
  evidencia `e5f4f047c560e3ec66ab006194b89edc461125934a194ca5de8d03d48d6bff8e`); la única evidencia
  que falta registrar es `9df85043f3a0`.
- Causa del rojo conocida y ya aislada: `scripts/common.ps1:119` (`Assert-OpoFuentePuertosLibres`)
  invoca `Get-NetTCPConnection`, ausente en el PowerShell del sandbox Linux, y aborta antes de la
  comprobación 1. `scripts/**` sigue fuera de las fuentes públicas del trabajador
  (`read`/`grep`/`edit` rechazados por política), así que el arreglo pertenece al custodio del arnés:
  guarda portable (`Get-Command` con aviso/no-op en Linux y mismo comportamiento en Windows, con su
  prueba) o ejecución de `scripts/gates.ps1` en PowerShell de Windows sobre el `tree_hash` final con
  recibo de `9df85043f3a0`.
- Esta nota se escribe **antes** de la última batería, que se ejecuta en un solo turno CI (`validar`
  sin gate, corta al primer fallo). Sus resultados, IDs de evidencia y veredicto van en el
  `worker_done`; no se edita nada después. No se toca `scripts/**`, ni
  `fixtures/profiles/manifest.json`, ni sus hashes, ni `data/sources`, ni ninguna prueba, y no hay
  commit, push, merge ni despliegue.

## Nuevo perfil CI y batería completa sobre el árbol real (3 de noviembre de 2026)

Task `task_638861d90964`, Dispatch `ctx_076585952fd5`, Run `run_8eed83a73d15`, con el mismo encargo:
completar la evidencia del árbol `17b57d2f02d42963760366e5bcec7e1568de2e700ef2c846379697ffe61bee31`
para la puerta pendiente `9df85043f3a0`.

- `git_estado` sigue sin encontrar `17b57d2f…` en este workspace. El árbol real antes de esta nota es
  `tree_hash=9abc8de99d895620a1c2dd9dfca63a2730d6bf28e43c4cbd88717542cda08fbb`, HEAD
  `6483111dfd7e7939aabb260cd28abd98b146f5c2`, rama `ErDeivih/equipo-ia`. La reproducción se hace
  sobre el árbol real, como en los intentos anteriores.
- Perfil de ejecución vigente: `994775df8794710e2f939680bdf1e38b4fb1e089355f2490ad26854652991f30`
  (imagen `sha256:ee7fd2a3b916cf9645d0da85c29aeec42254d25f03c6da8d1bcd81e6b331fb27`), distinto del
  `74b3b1d8…` de los cierres anteriores.
- Estado de infraestructura: las primeras llamadas a `validar` devolvieron
  `container_cleanup_unknown`; después, `status=waiting_infrastructure` con razón «Docker Desktop
  está abierto; esperar su motor». No se ha reiniciado Docker, no se ha salido del sandbox y no se ha
  ejecutado ninguna prueba todavía en esta Task.
- Causa del último rojo conocido, ya aislada en intentos previos: `scripts/common.ps1:119`
  (`Assert-OpoFuentePuertosLibres`) invoca `Get-NetTCPConnection`, ausente en el PowerShell del
  sandbox Linux, y aborta antes de la comprobación 1. `scripts/**` sigue fuera de las fuentes públicas
  del trabajador, así que el arreglo pertenece al custodio del arnés: guarda portable con prueba o
  ejecución de `scripts/gates.ps1` en PowerShell de Windows sobre el `tree_hash` final con recibo de
  `9df85043f3a0`. Si el nuevo perfil ya incluye ese cmdlet, la batería lo dirá.

Esta nota se escribe **antes** de la última batería, que se ejecuta en un solo turno CI (`validar`
sin gate, corta al primer fallo) en cuanto el motor de Docker esté disponible. Sus resultados, IDs de
evidencia y veredicto van en el `worker_done`; no se edita nada después. No se toca `scripts/**`, ni
`fixtures/profiles/manifest.json`, ni sus hashes, ni `data/sources`, ni ninguna prueba, y no hay
commit, push, merge ni despliegue.


