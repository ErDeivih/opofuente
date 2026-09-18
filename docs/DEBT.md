# Deuda técnica obligatoria

Deuda **registrada y con criterio de cierre**, no una lista de deseos. Cada entrada indica qué hay
que cambiar, en qué slice, por qué no se hace ahora y cómo se comprobará que está cerrada.

Reglas:

- una entrada solo se cierra cuando su criterio de cierre se ejecuta (no cuando «parece hecho»);
- una entrada que afecte a seguridad, privacidad o autoridad se trata como bloqueante del slice
  indicado, no como mejora opcional;
- nada de esta lista se implementa fuera de su slice para no ampliar el alcance.

| ID | Slice | Obligación | Estado |
|---|---|---|---|
| [DEBT-001](#debt-001--clasificación-del-destino-de-datos-por-proveedor) | S12 | Sustituir `Settings.sends_data_off_device` por clasificación por proveedor | abierta (reasignada de S09 a S12: los proveedores no llegan en S09, ver DEBT-014) |
| [DEBT-002](#debt-002--documentar-403-404-y-422-en-el-contrato) | S02 | Cerrar el caso real de validación fallida (422) con `field_errors` | **cerrada en S02** |
| [DEBT-003](#debt-003--uso-privado-del-temario-de-la-guardia-civil) | antes de publicar | No publicar el repositorio ni distribuir la aplicación con el temario de GC | abierta (condición previa) |
| [DEBT-004](#debt-004--parseo-seguro-de-xmlhtml-no-confiable) | S03 | Los extractores deben defenderse de XML/HTML no confiable | **cerrada en S03** |
| [DEBT-005](#debt-005--borrado-de-nodos-con-referencias-al-sincronizar-fixtures) | S04 | La siembra no puede borrar nodos con referencias | **cerrada en S04** |
| [DEBT-006](#debt-006--representación-exacta-de-fracciones-y-redondeo-en-la-puntuación) | S07 | Decidir y probar la aritmética exacta antes de calcular puntuaciones | **cerrada en S07** |
| [DEBT-007](#debt-007--higiene-del-almacén-artefactos-sin-origen-y-temporales) | S12 | Recolector de artefactos sin origen, temporales `.part` y purga de trabajos | abierta |
| [DEBT-008](#debt-008--conservar-los-formatos-sin-extractor-en-lugar-de-omitirlos) | S03 | Conservar PPTX/XLSX/EPUB y similares como `unsupported_preserved` | **cerrada en S03** |
| [DEBT-009](#debt-009--el-texto-plano-no-produce-secciones-y-sin-secciones-no-hay-citas) | S06 | El texto plano y el texto pegado no producen secciones: sin ellas no hay citas ni diff | **cerrada en S06** |
| [DEBT-010](#debt-010--una-pregunta-importada-no-queda-enlazada-a-su-sección) | S06/S11 | Importar preguntas no las enlaza a la sección que las sostiene, y `tags`/`source`/`parte` se leen pero no se guardan | abierta |
| [DEBT-011](#debt-011--la-pantalla-del-banco-solo-enseña-las-primeras-100-preguntas) | S09 | La pantalla del banco pide 100 preguntas y no permite recorrer el resto de un conjunto grande | abierta |
| [DEBT-012](#debt-012--modos-de-sesión-declarados-y-sin-implementar) | S08+ | Simulacro, diagnóstico y repaso de errores están en el vocabulario del modelo y no implementados | abierta (S08 añadió los modos de **corrección** de GC, no los modos de sesión) |
| [DEBT-013](#debt-013--el-recálculo-no-se-puede-hacer-en-bloque) | S09+ | Recalcular una clave corregida es sesión a sesión, y solo se conserva un resultado anterior | abierta |
| [DEBT-014](#debt-014--sin-proveedor-de-embeddings-ni-de-lenguaje-el-rag-es-extractivo) | S10+ | No hay embeddings, ni índice vectorial, ni proveedor de lenguaje: la búsqueda es léxica y la respuesta extractiva | abierta |
| [DEBT-015](#debt-015--el-índice-léxico-se-puede-rehacer-pero-no-desde-la-interfaz) | S12 | El índice léxico se rehace desde el servicio y no hay acción en Ajustes que lo haga | abierta |

---

## DEBT-001 — Clasificación del destino de datos por proveedor

**Origen:** revisión externa de S00 (14 de septiembre de 2026).

**Problema.** `Settings.sends_data_off_device`
(`apps/api/opofuente/config.py`) es un booleano global que no describe el destino real:

| Configuración | Devuelve | Debería |
|---|---|---|
| `llm_provider=ollama` con endpoint en `127.0.0.1` | `true` | indicar que **no** sale del equipo |
| `llm_provider=openai_compatible` apuntando a un servidor local (LM Studio, vLLM) | `true` | indicar que **no** sale del equipo |
| `embedding_provider=openai_compatible` (remoto) | `true`, pero se informa dentro del bloque de **LLM** | informarlo en el bloque de **embeddings** |

Hoy no hay fuga: ambos proveedores están `disabled` por defecto y la aplicación no realiza ninguna
llamada saliente. El riesgo es de **información al usuario**: la pantalla de Ajustes debe poder decir
si los datos salen del equipo y por qué proveedor.

**Cambio exigido antes de S12** (Ajustes: proveedores y capacidades). Sustituir el booleano por un
estado independiente por proveedor:

```text
disabled | local | remote | unknown
```

- `disabled`: no configurado;
- `local`: endpoint resuelto a loopback o red privada declarada como propia;
- `remote`: destino fuera del equipo;
- `unknown`: no se puede determinar con la información disponible (nunca debe presentarse como
  `local`).

La clasificación se calcula sobre el **endpoint efectivo** (URL resuelta, no solo su texto), se
expone por separado para `llm` y para `embeddings`, y `unknown` es el valor conservador por defecto.

**Por qué no ahora.** Implementarlo sin proveedor activo significaría escribir una clasificación de
URLs sin nada que clasificar. S09 iba a ser el slice donde llegaran los adaptadores, y **finalmente no
llegaron** (ADR-012: sin modelo de embeddings decidido no se descarga nada, y el proveedor de lenguaje
tampoco se enchufa), así que la obligación se traslada a S12, que es donde vive la pantalla de Ajustes
que el criterio 4 exige. Hoy la aplicación no hace ninguna llamada saliente y ambas capacidades se
declaran `disabled`/`unavailable` con su motivo, así que el booleano no engaña a nadie; sigue siendo un
booleano global y por eso no se cierra.

**Criterio de cierre.**

1. `Settings` expone la clasificación por proveedor en `/settings` y en `/capabilities`.
2. Pruebas unitarias: endpoint `127.0.0.1`/`localhost`/`::1` → `local`; IP privada declarada →
   `local`; dominio público → `remote`; URL no resoluble o vacía → `unknown`.
3. Prueba de contrato: los esquemas documentados de `/settings` (`SettingsSchema`, con su bloque
   `llm` y su bloque `embeddings` por separado) y de `/capabilities` (`CapabilitiesSchema`, en el
   detalle de las capacidades `llm` y `embeddings`) incluyen la clasificación por proveedor, y no
   queda ningún booleano llamado `sends_data_off_device` en ninguna de las dos respuestas.
4. La pantalla de Ajustes muestra, por proveedor, si los datos salen del equipo (07_UI-UX §11).

---

## DEBT-002 — Documentar 403, 404 y 422 en el contrato

**Origen:** corrección del 503 de `/health/ready` (commit corrector de S00).
**Estado: cerrada en S02.** S01 documentó 403, 404 y el esquema del 422; S02 añade las primeras
rutas con cuerpo y parámetros validados, y con ellas la prueba del caso real que faltaba.

**Problema.** El esquema OpenAPI documenta el 500 (`ProblemDetail`), el 503 de readiness
(`ReadinessProblem`) y los esquemas de las respuestas correctas, pero había errores que se servían
como `ProblemDetail` sin aparecer en el contrato, o con un esquema documentado que **no** era el que
se devuelve:

| Respuesta | Quién la produce | Cuerpo real | Estado |
|---|---|---|---|
| `403` | middleware de comprobación de `Origin` (métodos no seguros) | `ProblemDetail` (`code: forbidden_origin`) | **documentado en S01** en la primera ruta de escritura (`POST /oppositions/{id}/activate`), y no en rutas de lectura, donde no puede ocurrir |
| `404` | manejador global de `OpoFuenteError` / `StarletteHTTPException` | `ProblemDetail` | **documentado en S01** en todas las rutas que buscan un recurso por identificador |
| `422` | manejador global de `RequestValidationError` | `ProblemDetail` con `field_errors` | **esquema corregido en S01** al declararlo en cada ruta; **caso real probado en S02** |
| `405` | enrutador de Starlette | `ProblemDetail` | se sirve así y **no se documenta por ruta**: es un error de protocolo que no aporta información y añadirlo a cada operación sería ruido. Decisión aceptada, no deuda pendiente |

**Qué faltaba y cómo se cerró.** El criterio 3 pedía «un caso de validación fallida que compare
`field_errors`», y en S01 ninguna ruta tenía parámetros tipados ni cuerpo, así que no existía una
petición capaz de producir un 422 real. S02 añade `POST /api/v1/inventories` (cuerpo validado) y
parámetros de consulta validados (`limit`, `offset`, `status`), y con ellos la prueba
`test_el_422_servido_cumple_el_esquema_documentado` (`apps/api/tests/contract/test_openapi_contract.py`):

1. provoca un 422 real con `{"source_path": ""}` y con `?limit=0`;
2. comprueba que el cuerpo servido tiene todos los campos requeridos del `ProblemDetail` documentado;
3. comprueba que cada entrada de `field_errors` tiene **exactamente** las propiedades del componente
   `FieldError` documentado (`field`, `message`) y que el campo señalado es el que falla de verdad
   (`body.source_path`, `query.limit`).

## DEBT-003 — Uso privado del temario de la Guardia Civil

**Origen:** verificación de derechos al construir los fixtures de S01 (ADR-006).

**Problema.** Las condiciones generales del portal de la Guardia Civil limitan la licencia de sus
contenidos a la descarga y al uso privado, y prohíben la reproducción, distribución o comunicación
pública sin autorización expresa de la Dirección General. El temario oficial de los 25 temas está
versionado en `fixtures/profiles/gc-cabos-guardias-2026.curriculum.json` porque el producto existe
para estudiar ese programa, y OpoFuente es local, de un solo usuario y no redistribuye: ese es el
ámbito que la licencia cubre.

**Obligación.** El repositorio y la aplicación deben seguir siendo privados. Antes de publicar el
repositorio, distribuirlo, alojarlo en un servicio accesible a terceros o dar acceso a cualquier
tercero, hay que **retirar el temario de GC de los fixtures y cargarlo desde la copia privada del
usuario** (importación manual del PDF), o contar con autorización expresa de la Dirección General de
la Guardia Civil (`sugerencias-intranet@guardiacivil.org`).

La ratificación de ADR-006 (14/09/2026) **no cierra esta obligación**: autoriza el uso privado
actual, no la publicación futura.

**Criterio de cierre.** La decisión se cierra cuando el propietario confirma que el repositorio y la
aplicación seguirán siendo privados (queda como decisión registrada), o cuando se sustituye el
fixture por importación manual del PDF. La alternativa está descrita en ADR-006.

## DEBT-005 — Borrado de nodos con referencias al sincronizar fixtures

**Origen:** revisión de S01 (14/09/2026).
**Estado: cerrada en S04**, que es el slice que crea `curriculum_mappings` (el propietario lo autorizó
así: «S04 crea `curriculum_mappings` y cierra DEBT-005 dentro de S04»).

**Problema.** `SqlAlchemyProfileRepository._sync_curriculum` borra los nodos que ya no aparecen en el
fixture
(`apps/api/opofuente/infrastructure/profile_repository.py`, bloque «Nodos que ya no están en el
fixture: se eliminan»). Hoy es seguro porque nada los referencia, pero en S05 aparecerán
`curriculum_mappings`: documentos, secciones, evidencias y preguntas asignadas a nodos del programa.
A partir de ahí, sincronizar un fixture **podría borrar un nodo con material asignado**, y con
`ON DELETE CASCADE` se llevaría por delante las asignaciones sin avisar.

**Obligación.** Antes de crear `curriculum_mappings`, la sincronización de fixtures no podrá borrar
en silencio un nodo que tenga referencias. Hay que diseñar y probar una de estas políticas (o una
combinación): versionado del nodo, sustitución explícita con reasignación, o **bloqueo** de la
sincronización con un informe de nodos imposibles de retirar.

**Criterio de cierre.**

1. Política escrita y decidida (ADR si afecta al modelo) sobre qué ocurre con un nodo con referencias
   que desaparece del fixture.
2. Integridad referencial real en la base (`ON DELETE RESTRICT` o equivalente) para que el borrado
   silencioso sea imposible, y migración que la aplique.
3. Prueba de regresión: un nodo con un mapeo asignado no se borra; la sincronización informa del
   conflicto y deja el estado consistente.

**Cómo se cerró (S04), criterio por criterio.**

1. **Política: bloquear la retirada y informarla** (`docs/decisions/ADR-007-nodos-con-material-asignado.md`).
   Se descarta el borrado en cascada (destruye clasificación sin avisar), el versionado de nodos (decisión
   de modelo mayor, propia de cuando el temario se reorganice de verdad) y la reasignación automática
   (afirmaría una equivalencia que el usuario no ha confirmado). Un nodo bloqueado queda intacto y la
   siembra lo declara; retirarlo exige una acción explícita que S04 no decide por el usuario.
2. **Integridad real y migración**: `0012_classification_and_review` crea `curriculum_mappings` con
   `FOREIGN KEY (curriculum_node_id) REFERENCES curriculum_nodes (id) ON DELETE RESTRICT`, y SQLite las
   aplica (`PRAGMA foreign_keys=ON` desde S02). Prueba:
   `test_un_nodo_con_material_asignado_no_se_puede_borrar` (un `DELETE` directo por SQL falla con
   `IntegrityError` y el nodo y su mapeo siguen ahí) y `test_un_nodo_sin_material_si_se_puede_borrar`
   (la restricción no bloquea lo que no tiene referencias).
3. **Regresión de la siembra**: `test_un_nodo_con_material_asignado_no_se_retira_al_sembrar` parte de
   los perfiles sembrados, asigna material a un tema, vuelve a sembrar con un fixture al que le faltan
   los dos últimos temas y comprueba que el tema **sin** material se retira, el que **sí** tiene
   material se conserva, el mapeo sigue existiendo y el informe declara un conflicto
   (`SeedReport.blocked == 1`, con el nodo señalado). La siembra avisa además de que no converge con el
   fixture: `changed` es `True` en ese caso a propósito, porque el estado de la base ya no puede
   coincidir con el fixture mientras el nodo esté asignado.

## DEBT-006 — Representación exacta de fracciones y redondeo en la puntuación

**Origen:** revisión de S01 (14/09/2026).
**Estado: cerrada en S07.**

**Problema.** `exam_parts.wrong_penalty_fraction` y los umbrales se guardan como `float`
(SQLite `REAL`). La penalización de TAI es **un tercio exacto** y la fórmula de GC es
`Px = (Y/T)·(A − E/(N−1))`: calcularlas con aritmética binaria introduce errores de representación
(0,3333333333 no es 1/3) que pueden cambiar un resultado oficial por una décima y, con umbrales
enteros y redondeos publicados, decidir entre apto y no apto.

**Obligación.** Antes de calcular puntuaciones (S07/S08), decidir y probar la representación exacta:
`Decimal` con precisión y modo de redondeo declarados, fracción exacta (`Fraction`) o reglas
parametrizadas versionadas por convocatoria. Los `float` almacenados sirven como **información**
(qué dice la convocatoria), no como autoridad de cálculo.

**Criterio de cierre.**

1. Decisión registrada (ADR) con la representación elegida, la precisión y la regla de redondeo, y
   con la cita de la convocatoria que la justifica cuando exista.
2. Casos matemáticos de TAI y GC verificados con cálculo manual exacto (aciertos, errores, blancos,
   reservas y anuladas) comparados con el motor real.
3. Prueba que demuestre que un tercio no se calcula con `float`: por ejemplo, `3` errores en una
   parte con penalización de un tercio no pueden dejar un residuo binario visible en el resultado.
4. Si la convocatoria no publica el criterio de transformación, la interfaz sigue mostrando
   «calificación oficial no disponible» (regla ya vigente desde S00/S01).

**Cómo se cerró (S07), criterio por criterio.**

1. **Decisión: `docs/decisions/ADR-010-aritmetica-exacta-y-calificacion-oficial.md`.** Aritmética con
   `Fraction`; el decimal almacenado es información y la fracción exacta es la más simple que coincide
   con él (tolerancia media unidad de su última cifra, denominador ≤ 100), o el cálculo **falla**;
   el decimal se calcula solo al mostrar, con `ROUND_HALF_UP` a cuatro decimales; y la calificación
   oficial 0-50 no se calcula sin el baremo publicado.
2. **Casos verificados con cálculo manual exacto**: `tests/unit/test_study_domain.py` calcula a mano
   aciertos, errores, blancos, anuladas y reservas (68 aciertos y 10 errores dan `68 − 10/3`), y las
   pruebas de integración del slice repiten el caso por la API real, parte a parte.
3. **Un tercio no se calcula con `float`**:
   `test_tres_errores_descuentan_exactamente_un_punto` exige `exact_score(0, 3, 1/3) == Fraction(-1)` y
   que no quede residuo; la evaluación se guarda como `-1/3`, no como `-0.3333333333`.
4. **Sin baremo no hay calificación oficial**: `SessionResult.official_available` es falso con su nota
   escrita, `pass_score` viaja como dato declarado y ni la API ni la interfaz dicen «apto».

## DEBT-004 — Parseo seguro de XML/HTML no confiable

**Origen:** `# noqa: S314` justificado en la herramienta de fixtures de S01.
**Estado: cerrada en S03.**

**Problema.** `apps/api/opofuente/tools/build_profile_fixtures.py` analiza XML y PDF descargados.
Hoy es seguro porque el fichero se verifica por `sha256` contra el manifiesto antes de leerlo. Pero
S03 añadirá extractores que leerán **contenido del usuario**, que sí es entrada no confiable:
XML con entidades externas, HTML con scripts y ZIPs con traversal (09_SECURITY-PRIVACY-AND-RIGHTS
§3 y §5).

**Obligación.** En S03, cada extractor debe defenderse de entrada no confiable: sin resolución de
entidades externas (`defusedxml` o configuración equivalente), sin ejecutar contenido activo, con
límites de tamaño y profundidad, y con sus pruebas negativas correspondientes.

**Criterio de cierre.** Extractores de S03 con pruebas negativas (entidades externas, XML con
`DOCTYPE`, HTML con scripts, ZIP con traversal y con ratio de expansión abusivo) y sin `# noqa` de
seguridad pendientes en el código de producción.

**Cómo se cerró (S03).**

| Defensa | Dónde vive | Prueba negativa |
|---|---|---|
| XML/HTML sin resolver entidades ni DTD | `infrastructure/safe_xml.py`: `resolve_entities=False`, `load_dtd=False`, `no_network=True`, `huge_tree=False`, `DOCTYPE` rechazado antes de parsear y tope de bytes | `tests/unit/test_safe_inputs.py` (DOCX con `DOCTYPE` y entidad `file:///C:/Windows/win.ini`) |
| Nada de contenido activo en HTML | `extractors/text_files.py` usa `html.parser` de la biblioteca estándar (no un motor de navegador), descarta `script`, `style`, `iframe`, `nav` y `footer`, y **nunca** ejecuta ni sigue nada; el texto con instrucciones para un modelo entra como texto literal | `test_el_html_no_ejecuta_nada_al_extraer_en_el_pipeline`, `tests/unit/test_extractors.py` |
| ZIP sin traversal, sin enlaces, sin bombas | `infrastructure/safe_zip.py`: nombres validados (absolutos, `..`, separadores invertidos, unidades de Windows y enlaces), tope de entradas, de bytes y de ratio, y expansión acotada en profundidad | `tests/unit/test_safe_inputs.py` (traversal, bomba de ratio, bombas anidadas, enlace simbólico), `test_un_zip_con_traversal_se_rechaza_sin_expandir`, `test_un_zip_dentro_de_otro_no_se_expande` |
| URL sin SSRF | `infrastructure/url_guard.py`: solo `http`/`https`, resolución DNS y bloqueo de loopback, privadas, link-local, metadatos y reservadas; **cada** redirección se revalida y la conexión se hace contra la IP ya comprobada (defensa ante rebinding) | `tests/unit/test_safe_inputs.py`, `test_una_url_interna_se_rechaza_sin_descargar`, `test_la_guarda_de_url_rechaza_y_no_crea_lote` |
| Sin `# noqa` de seguridad pendientes | `uv run ruff check .` con las reglas de seguridad activas: sin `S314` ni equivalentes en el código de S03 | puerta 2 |

---

## DEBT-007 — Higiene del almacén: artefactos sin origen y temporales

**Origen:** revisión de S02 (14/09/2026).

**Problema.** El almacén de S02 solo **añade**. No hay nada que retire:

| Qué queda atrás | Cuándo | Consecuencia |
|---|---|---|
| Ficheros `data/tmp/ingest-<uuid>.part` | el proceso muere a mitad de una copia (corte de luz, `taskkill`, cuelgue). El código borra el temporal en `OSError` y en cancelación cooperativa, pero no ante una muerte del proceso | basura en `tmp/` que nadie vuelve a mirar |
| Artefactos en `data/artifacts/sha256/` | cuando se borre material (hoy todavía no se puede borrar un lote por la API) | el contenido permanece aunque ningún origen lo referencie |
| Filas de `jobs` | nunca se purgan los trabajos terminados | la tabla crece sin límite; con `--batch-max-entries` alto, cada importación añade trabajos |

Hoy no hay pérdida de datos ni riesgo: el material del usuario es de solo lectura y el almacén es
aditivo. El problema es que **el disco crece y no hay forma de saber qué sobra**, y eso importa en
una aplicación pensada para acumular decenas de miles de documentos en el equipo del usuario.

**Obligación.** Antes de dar por buena la pantalla de almacenamiento (S12), implementar:

1. **Recolector de temporales**: borrar los `*.part` de `data/tmp/` con una antigüedad mayor que el
   lease máximo, informando de cuántos se han retirado. **Dentro de la acción explícita de limpieza,
   no en el arranque**: una purga automática al iniciar sería justo la purga silenciosa que prohíbe
   el criterio 1. Al arrancar, como mucho se *avisa* de cuántos temporales hay y de su antigüedad.
2. **Recolector de artefactos sin origen**: un artefacto con **cero** filas en `artifact_origins` y
   con antigüedad mayor que una ventana declarada puede retirarse. Nunca se retira un artefacto con
   algún origen, y la operación es explícita (se pide, se informa de lo retirado), no automática.
3. **Purga de trabajos**: política de retención escrita (por ejemplo, los trabajos terminados con
   más de N días) y aplicada por el propio recolector.

Y todo ello sin tocar jamás un fichero del usuario: el recolector solo mira dentro del directorio de
datos.

**Criterio de cierre.**

1. Comando o endpoint explícito («liberar espacio») con informe de lo retirado, y ninguna purga
   silenciosa en segundo plano ni al arrancar.
2. Prueba de que un artefacto **compartido** (dos orígenes) sobrevive al recolector aunque uno de
   sus lotes se haya borrado.
3. Prueba de que un `*.part` reciente (una copia en curso) **no** se borra, y uno antiguo sí, y de
   que el resultado (cuántos y cuáles) se informa.
4. Prueba de que los originales del usuario no se tocan: instantánea de tamaños y fechas antes y
   después del recolector, igual que en las pruebas de S02.
5. La pantalla de almacenamiento muestra espacio usado, nº de artefactos y resultado de la última
   limpieza (07_UI-UX §11).

## DEBT-008 — Conservar los formatos sin extractor en lugar de omitirlos

**Origen:** revisión de S02 (15/09/2026). La especificación se corrigió el mismo día (ver abajo).
**Estado: cerrada en S03.**

**Problema.** `FilesystemInventory` clasifica `.epub`, `.pptx`, `.ppt`, `.xlsx`, `.xls`, `.odt` y
`.ods` como `omitted_unsupported` y **no los copia**. La especificación dice otra cosa:

> «Archivos Office con macros, audio, vídeo, EPUB y PPTX quedan `unsupported_preserved`: se conservan
> íntegros en el almacén, **sin ejecutar ni extraer** nada de ellos.» — `04_INGESTION-AND-CLASSIFICATION §3`

`unsupported_preserved` significa que el original **se conserva** en el almacén (con su hash y su
origen) y que simplemente no se extrae todavía. Omitirlos tiene dos consecuencias: el usuario pierde
material que sí quería guardar (un resumen en PPTX, un temario en EPUB) y OpoFuente no puede
reconocerlo después cuando llegue el extractor, porque nunca lo copió.

**Contradicción resuelta en la especificación (15/09/2026).** §2 pide omitir los ejecutables por
defecto y §3 los metía en `unsupported_preserved`: las dos frases no podían ganar a la vez. El
propietario autorizó corregir el texto canónico, y ahora §3 dice explícitamente que los ejecutables
**no** se conservan, con el motivo. La regla queda así y es la que S03 implementará:

| Qué | Regla | Por qué |
|---|---|---|
| Ejecutables y bibliotecas (`.exe`, `.dll`, `.msi`, `.bat`, `.cmd`, `.com`, `.scr`, `.ps1`, `.jar`, `.so`, `.dylib`) | **se omiten** (§2) | decisión de seguridad: OpoFuente no necesita el binario para estudiar y no lo va a ejecutar nunca; guardarlo solo añade superficie y ruido. Se registra como incidencia, no se copia |
| Temporales de Office (`~$…`), ocultos del sistema y basura (`Thumbs.db`, `desktop.ini`) | **se omiten** (§2) | no son material del usuario: son restos del sistema |
| Office con macros (`.docm`, `.xlsm`, `.pptm`), audio, vídeo, `.epub`, `.pptx`, `.xlsx`, `.odt`, `.ods` | **se conservan** como `unsupported_preserved` (§3) | sí son material del usuario y lo querrá después; se conservan **sin ejecutar ni extraer** nada de ellos |

Es decir: `unsupported_preserved` es «lo conservo aunque todavía no sé leerlo», y no un permiso para
guardar binarios ejecutables.

**Obligación.** En S03, al añadir los extractores:

1. los formatos de la tercera fila se copian al almacén como cualquier otro fichero y quedan en
   estado `unsupported_preserved` (conservado, sin extracción y sin ejecución alguna);
2. el informe del lote los cuenta en su propio contador (`preserved_unsupported`), separado de los
   omitidos por política y de los fallidos;
3. la interfaz explica que están guardados pero todavía no se pueden leer, en lugar de decir que se
   han omitido;
4. los ejecutables, los temporales de Office, los ocultos y los enlaces que salen de la carpeta
   **siguen** omitiéndose, con su incidencia y su contador, exactamente como en S02.

**Criterio de cierre.**

1. Un lote con un `.pptx`, un `.epub` y un `.xlsx` los copia al almacén: hay artefacto y origen para
   cada uno, con su `sha256` verificado, y no se ejecuta ni se extrae nada.
2. El contador `preserved_unsupported` aparece en el informe y el total sigue cuadrando
   (`total = copied + pending + failed + cancelled + source_changed + preserved_unsupported`).
3. Prueba de contrato y de interfaz: el estado se muestra como «conservado sin extractor», no como
   omitido ni como fallido.
4. Prueba de no regresión: un `.exe`, un `.ps1`, un `~$temporal.docx` y un enlace que sale de la
   carpeta **no** se copian y se declaran como omitidos, con los mismos códigos de incidencia que en
   S02.

**Cómo se cerró (S03), criterio por criterio.**

1. `FilesystemInventory` ya no omite `.pptx`, `.xlsx`, `.ods`, `.epub`, `.docm`, audio ni vídeo: los
   copia como cualquier otro fichero (`PRESERVED_EXTENSIONS` en `filesystem_inventory.py`) y la
   extracción los deja en `unsupported_preserved`. Un `.zip` que llega **dentro** de otro contenedor
   tampoco se expande: se conserva igual de íntegro. Prueba:
   `test_la_extraccion_clasifica_por_formato_y_conserva_lo_que_no_puede_leer`
   (`resumen.xlsx` → `unsupported_preserved` con su incidencia `unsupported_preserved`),
   `test_un_zip_dentro_de_otro_no_se_expande`, y en el E2E de la bandeja el `.xlsx` aparece copiado.
2. `ImportCounters.preserved_unsupported` es un término propio de la ecuación
   (`BALANCE_TERMS` en `domain/ingestion.py`) y `balanced_counters` lo comprueba; el informe lo sirve
   la API y la interfaz lo muestra en los datos del lote. Pruebas:
   `test_la_extraccion_clasifica_por_formato_y_conserva_lo_que_no_puede_leer`,
   `test_la_extraccion_se_puede_cancelar_y_deja_el_lote_coherente` (el total sigue cuadrando con el
   término nuevo) y las pruebas de contrato del informe.
3. El estado se sirve con su propio nombre (`unsupported_preserved`) y su incidencia dice «Conservado
   sin extraer: …» con el motivo del registro de extractores; la bandeja lista el estado y la
   incidencia en la tabla de entradas del lote. Pruebas: contrato (`RepresentationSchema` y estados
   documentados), `test_s02_domain.py` (transiciones válidas del estado nuevo) y las pruebas de
   Vitest de la bandeja.
4. No regresión: los ejecutables siguen en `OMITTED_EXTENSIONS`/`DANGEROUS_SUFFIXES` (no se copian ni
   se conservan, ni siquiera dentro de un ZIP: `test_un_zip_se_expande_en_entradas_del_lote_y_se_extrae`
   comprueba que `material.zip/basura.exe` **no** existe), los temporales de Office, los ocultos y los
   enlaces que salen de la carpeta mantienen sus códigos de incidencia en
   `tests/integration/test_inventory.py` y en el E2E.

## DEBT-009 — El texto plano no produce secciones (y sin secciones no hay citas)

**Origen:** cierre de S05 (17 de septiembre de 2026), al probar el diff entre versiones.

**Problema.** `PlainTextExtractor` (`apps/api/opofuente/infrastructure/extractors/text_files.py`) solo
calcula secciones para Markdown (`_markdown_sections`) y devuelve `sections=()` para `.txt`; el texto
**pegado** entra por ese mismo camino. Sin secciones no se crean `document_sections`, y con eso:

| Consecuencia | Dónde se nota |
|---|---|
| Cero `evidence_spans` | la pestaña de la ficha se queda sin citas y «copiar cita» no tiene sección que citar |
| `diff_versions` sin nada que comparar | `GET /documents/{id}/diff` responde vacío aunque el texto haya cambiado |
| Estructura vacía | la pestaña «Estructura» no lista nada |

No es un fallo de S05: S05 traduce y guarda lo que el extractor produce y **no inventa estructura**
(`document_section_type` documenta que un párrafo no es un artículo porque lo parezca). Pero el
material más probable de quien estudia —sus propios apuntes en texto— es justo el que queda sin citas.

**Obligación antes de S06** (el banco de preguntas exige citar documento y sección): decidir y
registrar (ADR) cómo se estructura el texto plano. Opciones: que el extractor emita **tramos técnicos**
por bloque de párrafos (respetando líneas en blanco y encabezados `Tema N`), o que la sección se
derive al promocionar con una sección `technical` que cubra el texto completo **y lo diga en su
etiqueta**. Lo que no vale es inventar jerarquía.

**Criterio de cierre.**

1. Decisión registrada, con su cita y su porqué.
2. Un `.txt` y un texto pegado producen al menos una sección marcada como tal, y de ella sale una
   evidencia con su etiqueta de cita.
3. Prueba de que el diff de dos versiones de texto plano informa de lo que cambió (hoy está probado
   con secciones inyectadas y con la ausencia declarada).
4. Prueba negativa: un texto sin estructura reconocible no se presenta como si tuviera capítulos.

**Cómo se cerró (S06), criterio por criterio.**

1. **Decisión: `docs/decisions/ADR-008-tramos-del-texto-plano.md`.** Un tramo (`paragraph`) por bloque
   separado por una línea en blanco, con offsets exactos sobre el texto normalizado, **sin llamar
   «título» a nada** (adivinar encabezados estaba descartado por el propio proyecto), con tope de 500
   tramos y sin cambiar lo que ya hacía Markdown.
2. **Secciones y evidencias de verdad**: `PlainTextExtractor` calcula los tramos con
   `_block_sections` y, al promocionar, S05 los traduce a `technical` y recorta cada evidencia con sus
   offsets. Pruebas: `test_un_texto_plano_deja_un_tramo_por_bloque_con_sus_offsets`,
   `test_un_texto_sin_lineas_en_blanco_es_un_solo_tramo` y
   `test_los_tramos_de_un_texto_enorme_se_acotan` (`tests/unit/test_extractors.py`). El camino
   completo —pegar, extraer, promocionar, citar— está en S05, que ya usaba el texto real de la
   representación.
3. **Diff de dos versiones de texto pegado**: `test_el_diff_compara_dos_versiones_del_mismo_documento`
   (`tests/integration/test_library_api.py`) comprueba sobre el camino real que el servidor informa de
   un bloque cambiado y otro añadido, con el texto de cada lado. Antes esta prueba **declaraba** que no
   había nada que comparar; ahora compara.
4. **Prueba negativa**: `test_un_texto_vacio_no_inventa_ningun_tramo` (un texto en blanco no produce
   secciones y queda `empty`) y, en el mismo fichero, el tramo no lleva `title` nunca: ni un texto con
   pinta de temario se presenta como si tuviera capítulos. El caso del Markdown sin nombre original
   —donde sí podría colarse una adivinación— se cubre en
   `test_sin_el_nombre_original_un_markdown_pierde_los_encabezados_y_un_json_su_vista_previa`.

## DEBT-010 — Una pregunta importada no queda enlazada a su sección

**Origen:** cierre del importador de S06 (17 de septiembre de 2026).

**Problema.** El parser de preguntas lee **texto** (pegado, de un fichero o de una hoja CSV) y guarda
cada pregunta con sus opciones, su clave y —cuando el CSV trae la columna `topic`— su nodo del programa.
Lo que **no** hace todavía:

| Qué falta | Consecuencia |
|---|---|
| Enlazar la pregunta con la **sección** del documento del que salió | `GET /questions/{id}/evidence` devuelve vacío y la ficha no puede abrir la cita que sostiene el enunciado |
| Guardar la **parte** del examen que el parser detecta («Parte 2», «Primera parte») | `parsed.parts_detected` se informa y se pierde: no hay dónde guardarla, porque el modelo no liga preguntas a `exam_parts` |
| Guardar las columnas `tags` y `source` del CSV | el asistente las lee y el informe declara que **no** se guardan (`ignored_columns`), en lugar de fingir que sí |

El importador desde un **documento** de la biblioteca (con su versión, su sección y su evidencia) es la
mitad que falta de «parser desde texto/documento»: hoy el camino es texto y CSV.

**Obligación.** Antes de que la ficha de pregunta pueda enseñar el original al lado con su cita (07_UI-UX
§7) y antes de S11 (cambios e invalidación, que necesita saber qué preguntas dependen de qué evidencia):

1. decidir dónde vive la parte del examen (¿`question_sets.part_code`? ¿una tabla de relación con
   `exam_parts`?) y registrarlo en un ADR si toca al modelo;
2. importar preguntas **desde una versión de documento**: trocear por secciones, crear la evidencia de
   cada pregunta (`question_evidence`) con su `role` y su `claim`, y dejar la cita abrible;
3. dar sitio a `tags` y `source` (etiquetas propias por pregunta) o quitarlos del mapeo del asistente si
   se decide que no se guardan nunca.

**Criterio de cierre.**

1. Una pregunta importada de un documento tiene al menos una evidencia `accepted` con su span, su página
   y su etiqueta de cita, y `GET /questions/{id}/evidence` la devuelve.
2. La ficha muestra esa cita junto al enunciado y se puede abrir el original en su página.
3. Prueba de que la parte detectada no se pierde en silencio: o se guarda, o el informe dice que no se
   guarda (hoy hace lo segundo solo para `tags` y `source`).

## DEBT-011 — La pantalla del banco solo enseña las primeras 100 preguntas

**Origen:** cierre de la interfaz de S06 (17 de septiembre de 2026).

**Problema.** `apps/web/src/api/questions.ts` pide las preguntas del conjunto con
`limit=100&offset=0` y la pantalla no tiene forma de pedir la página siguiente. El servidor página de
verdad (`limit`/`offset`, con el total en la respuesta) y la tabla **lo declara** en su leyenda («100 de
350 preguntas del conjunto»), así que no engaña; pero con un banco real —cientos de preguntas
importadas de un temario— lo que se ve es la primera centena, y las demás solo existen para la API.
Lo mismo vale para la lista de conjuntos y su selector.

**Obligación antes de S09** (búsqueda y listados): que la pantalla permita recorrer el conjunto completo
—paginación explícita o carga incremental— y que el recuento de la leyenda corresponda a lo que se
puede llegar a ver, sin truncar en silencio ni depender de que alguien lea la leyenda.

**Criterio de cierre.**

1. Un conjunto con más de 100 preguntas se puede recorrer entero desde la pantalla, y el recuento que
   muestra coincide con `total` del servidor.
2. Prueba de interfaz con un conjunto de más de una página: se llega a la última pregunta y se ve la
   última página, no solo la primera.
3. La paginación se conserva al cambiar de filtro (estado, origen, reservas) sin mezclar páginas de
   filtros distintos.

## DEBT-012 — Modos de sesión declarados y sin implementar

**Origen:** cierre de S07 (17 de septiembre de 2026).

**Problema.** 06_QUESTIONS §5 define cinco modos de sesión y 03_DATA-MODEL §7 los nombra en el
vocabulario de `study_sessions` (`practice`, `error_review`, `official_exam`, `mock_exam`,
`diagnostic`). S07 implementa **dos**: práctica y examen oficial. Pedir cualquiera de los otros tres
responde 409 `unsupported` con el motivo, así que no se simula nada; pero el producto promete esos
modos y hoy no existen:

| Modo | Qué le falta |
|---|---|
| `error_review` (repaso de errores) | la cola determinista de repaso (`review_items`) y la clasificación de la causa del fallo, que son de S10 |
| `mock_exam` (simulacro) | la composición que evita preguntas vistas recientemente y la etiqueta de «no oficial» |
| `diagnostic` (diagnóstico) | la muestra estratificada por tema y la estimación con incertidumbre (no un porcentaje de dominio con dos preguntas) |

**Obligación.** Implementar cada modo **con lo que promete la especificación**, o retirarlo del
vocabulario si el producto decide no ofrecerlo. Mientras no exista, el vocabulario del modelo y el del
contrato no coinciden a propósito: el contrato solo declara los modos que se corrigen de verdad
(`SessionModeName` en `api/study_schemas.py`).

**Criterio de cierre.**

1. Cada modo pendiente o bien está implementado de punta a punta (crear, componer, corregir y
   resultado) con su prueba de API y de interfaz, o bien ha desaparecido del vocabulario del modelo con
   su migración.
2. El contrato declara exactamente los modos que existen, y el vocabulario del modelo y el del contrato
   vuelven a coincidir.
3. Una prueba comprueba que un modo declarado en el contrato no responde 409 `unsupported`.

## DEBT-013 — El recálculo no se puede hacer en bloque

**Origen:** cierre de S08 (17 de septiembre de 2026).

**Problema.** Recalcular con una clave corregida es una acción **de una sesión**
(`POST /study-sessions/{id}/recalculate`), y solo se conserva el resultado **anterior** inmediato
(`study_sessions.previous_result_json`). Dos consecuencias reales:

| Qué pasa | Consecuencia |
|---|---|
| Una clave mal importada se corrige después de veinte sesiones | hay que recalcular veinte veces, una por una; las que nadie recuerde quedan con la puntuación vieja |
| Se recalcula dos veces (una clave v2 y luego una v3) | el resultado de la v1 se pierde: solo queda el de la v2, aunque las evaluaciones de todas sí se conservan |

**Obligación antes de S09/S11** (cambios e invalidación, que ya sabe qué depende de qué): poder
recalcular **el conjunto** de sesiones afectadas por una clave nueva, con un informe de cuántas
cambiaron y cuánto, y conservar el histórico de resultados (o dejar claro que la evaluación por clave
es el histórico y el resultado agregado es solo el vigente).

**Criterio de cierre.**

1. Existe una acción que recalcula todas las sesiones terminadas que usaron una clave concreta, con
   un informe por sesión (antes, después y si cambió).
2. Una prueba comprueba que una sesión ya recalculada no se recalcula dos veces con la misma clave
   (idempotencia) y que el resultado de la clave intermedia sigue siendo legible.
3. La interfaz dice cuántas sesiones quedan desactualizadas después de activar una clave nueva, en
   lugar de dejar que se descubra sesión a sesión.

## DEBT-014 — Sin proveedor de embeddings ni de lenguaje, el RAG es extractivo

**Origen:** apertura de S09 (18 de septiembre de 2026), con la decisión ADR-012.

**Problema.** `05_RAG` §4 pide índice vectorial con embeddings y §6 pide que un modelo redacte la
respuesta con esquema JSON validado. En S09 no hay ni lo uno ni lo otro, y a propósito:

| Qué falta | Qué hay en su lugar | Qué se pierde |
|---|---|---|
| Modelo de embeddings (se fija por ADR tras benchmark en español) | búsqueda léxica FTS5 con `bm25` | recall: otra forma de decir lo mismo puede no encontrarse |
| Índice vectorial local (Qdrant con payload de identificadores) | el puerto `VectorSearch` con una implementación que declara no estar disponible | recuperación híbrida y RRF real |
| Proveedor de lenguaje | composición **extractiva**: la respuesta son fragmentos citados del corpus | redacción, estilo didáctico y comparación en prosa |
| Rerank y verificador de entailment (§6) | la invariante de citas (`assert_grounded`) y el estado `insufficient` | comprobación independiente de la fidelidad |

No es una simulación: la búsqueda funciona de verdad, responde de verdad y **declara** en cada
respuesta que la recuperación fue solo léxica y quién la redactó (`extractive`, sin modelo). El
conjunto patrón de §9 (50 consultas TAI, 30 GC, 20 de rechazo) tampoco existe, así que las métricas de
§10 no se han medido y no se declaran.

**Obligación.** Decidir el modelo de embeddings con un benchmark en español y su ADR, implementar el
adaptador vectorial y el proveedor de lenguaje (local o remoto, con la clasificación de destino de
DEBT-001), construir el conjunto patrón de §9 y medir §10 antes de declarar el RAG en uso normal
(§11: Recall@10 ≥ 0,90 y ninguna respuesta `supported` con afirmación central sin evidencia).

**Criterio de cierre.**

1. Existe un ADR con el benchmark en español y el modelo elegido, y ninguna descarga ocurre al iniciar
   sin aviso.
2. `strategy: hybrid` recupera de verdad por dos vías y la respuesta declara `strategies` con ambas.
3. El conjunto patrón de §9 está versionado y las métricas de §10 se calculan con él; una prueba falla
   si Recall@10 baja de 0,90 o si una respuesta `supported` cita un fragmento no entregado.
4. La pantalla de búsqueda deja de declarar la degradación léxica porque ya no la hay.

## DEBT-015 — El índice léxico se puede rehacer, pero no desde la interfaz

**Origen:** cierre de S09 (18 de septiembre de 2026).

**Problema.** `SearchService.rebuild()` rehace el índice léxico desde SQLite (`05_RAG` §4: los índices
son reconstruibles) y está probado (`tests/integration/test_search_rag.py`), pero **ninguna ruta HTTP lo
expone** y la pantalla de Ajustes no ofrece nada parecido. Hoy el índice se mantiene por disparadores
en `evidence_spans`, así que solo hace falta rehacerlo si algo se desincroniza; cuando eso pase, hará
falta abrir una consola de Python contra la aplicación, que es exactamente lo que un producto local no
debe exigir.

**Obligación antes de S12** (Ajustes: almacenamiento, capacidades instaladas y copias): una acción
«rehacer índices» con su confirmación, el recuento de fragmentos indexados y la fecha del último
rehecho, y su prueba de interfaz.

**Criterio de cierre.**

1. La acción existe en Ajustes, dice cuántos fragmentos ha indexado y no toca el texto de las
   evidencias (el índice es derivado).
2. Una prueba comprueba que, tras borrar el índice a mano, la acción lo reconstruye y la búsqueda
   vuelve a encontrar el mismo fragmento.
3. La interfaz no permite lanzarla dos veces a la vez ni la presenta como una operación instantánea si
   el corpus es grande.
