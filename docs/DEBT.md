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
| [DEBT-001](#debt-001--clasificación-del-destino-de-datos-por-proveedor) | S12 | Sustituir `Settings.sends_data_off_device` por clasificación por proveedor | **cerrada** (21 de septiembre de 2026: clasificación por proveedor con su motivo, booleano retirado del contrato **y** de `Settings`, y la misma frase en Ajustes y en el estado del sistema) |
| [DEBT-002](#debt-002--documentar-403-404-y-422-en-el-contrato) | S02 | Cerrar el caso real de validación fallida (422) con `field_errors` | **cerrada en S02** |
| [DEBT-003](#debt-003--uso-privado-del-temario-de-la-guardia-civil) | antes de publicar | No publicar el repositorio ni distribuir la aplicación con el temario de GC | abierta (condición previa) |
| [DEBT-004](#debt-004--parseo-seguro-de-xmlhtml-no-confiable) | S03 | Los extractores deben defenderse de XML/HTML no confiable | **cerrada en S03** |
| [DEBT-005](#debt-005--borrado-de-nodos-con-referencias-al-sincronizar-fixtures) | S04 | La siembra no puede borrar nodos con referencias | **cerrada en S04** |
| [DEBT-006](#debt-006--representación-exacta-de-fracciones-y-redondeo-en-la-puntuación) | S07 | Decidir y probar la aritmética exacta antes de calcular puntuaciones | **cerrada en S07** |
| [DEBT-007](#debt-007--higiene-del-almacén-artefactos-sin-origen-y-temporales) | S12 | Recolector de artefactos sin origen, temporales `.part` y purga de trabajos | **cerrada en S12** (backend e interfaz: foto del almacén, retirada con confirmación y prueba de que lo referenciado no se toca) |
| [DEBT-008](#debt-008--conservar-los-formatos-sin-extractor-en-lugar-de-omitirlos) | S03 | Conservar PPTX/XLSX/EPUB y similares como `unsupported_preserved` | **cerrada en S03** |
| [DEBT-009](#debt-009--el-texto-plano-no-produce-secciones-y-sin-secciones-no-hay-citas) | S06 | El texto plano y el texto pegado no producen secciones: sin ellas no hay citas ni diff | **cerrada en S06** |
| [DEBT-010](#debt-010--una-pregunta-importada-no-queda-enlazada-a-su-sección) | S06/S11 | Importar preguntas no las enlaza a la sección que las sostiene, y `tags`/`source`/`parte` se leen pero no se guardan | **cerrada** (20 de septiembre de 2026: importación desde una versión de documento con su cita, abrible en su página; la parte y las etiquetas se declaran, con la decisión en ADR-014) |
| [DEBT-011](#debt-011--la-pantalla-del-banco-solo-enseña-las-primeras-100-preguntas) | S09 | La pantalla del banco pide 100 preguntas y no permite recorrer el resto de un conjunto grande | **cerrada en la revisión de S00–S11** (obligación vencida desde S09; se cerró con paginación real y prueba) |
| [DEBT-012](#debt-012--modos-de-sesión-declarados-y-sin-implementar) | S11+ | Simulacro y diagnóstico están en el vocabulario del modelo y no implementados | **cerrada** (21 de septiembre de 2026: simulacro con el perfil exacto que evita lo visto hace poco y diagnóstico con muestra por temas e intervalo de Wilson; el contrato declara los cinco modos) |
| [DEBT-013](#debt-013--el-recálculo-no-se-puede-hacer-en-bloque) | S09+ | Recalcular una clave corregida es sesión a sesión, y solo se conserva un resultado anterior | **cerrada** (20 de septiembre de 2026: recálculo en bloque con informe por sesión, y la pantalla de plantillas dice cuántas sesiones quedan desactualizadas y las recalcula) |
| [DEBT-014](#debt-014--sin-proveedor-de-embeddings-ni-de-lenguaje-el-rag-es-extractivo) | S10+ | No hay embeddings, ni índice vectorial, ni proveedor de lenguaje: la búsqueda es léxica y la respuesta extractiva | abierta |
| [DEBT-015](#debt-015--el-índice-léxico-se-puede-rehacer-pero-no-desde-la-interfaz) | S12 | El índice léxico se rehace desde el servicio y no hay acción en Ajustes que lo haga | **cerrada en S12** (entregada y probada, con la honestidad del criterio 2 escrita: el índice es FTS5 de contenido externo y «borrarlo a mano» no lo vacía) |
| [DEBT-016](#debt-016--la-dificultad-observada-no-existe-y-los-umbrales-de-dominio-son-provisionales) | S11+ | El dominio se estima sin dificultad observada, con umbrales provisionales | abierta |
| [DEBT-017](#debt-017--las-colecciones-existen-en-la-api-y-no-en-la-interfaz) | S12 | Las colecciones se pueden crear y llenar por la API; ninguna pantalla las enseña | **cerrada** (20 de septiembre de 2026: pantalla, filtro en el servidor, alta y **baja** de miembros, con dos defectos que la propia superficie destapó y se arreglaron) |
| [DEBT-018](#debt-018--la-puerta-humana-de-s04-no-se-ejecutó) | antes de usar material real | S04 pedía medir la revisión sobre 20–50 ficheros reales antes de abrir S05, y no se hizo | abierta (la **mitad de la máquina está medida** con 30 ficheros reales —90 propuestas, 38 pendientes de revisar—; falta el tiempo de revisión del propietario, la decisión y su confirmación) |
| [DEBT-019](#debt-019--el-estado-conservado-sin-extractor-no-llega-a-la-pantalla) | S12 | `unsupported_preserved` se guarda y se sirve, pero no hay prueba de interfaz ni de contrato que lo muestre legible | **cerrada** (el estado se enseña con su nombre y su motivo, y hay prueba de la API de punta a punta y prueba de interfaz) |
| [DEBT-020](#debt-020--la-clave-oficial-de-celador-está-escaneada-y-no-se-puede-importar) | S09+ | La plantilla oficial de respuestas correctas de Celador es un escaneo sin capa de texto: la clave existe y no entra en la aplicación | abierta |
| [DEBT-021](#debt-021--la-puerta-e2e-puede-correr-contra-un-servidor-ajeno) | antes de dar por buena una corrida E2E | La suite E2E reutiliza cualquier servidor que escuche en el 8765: corre contra su base de datos y escribe en ella | abierta |
| [DEBT-022](#debt-022--la-suite-e2e-no-distingue-la-máquina-está-cargada-de-esto-se-ha-roto) | antes de dar por buena la puerta E2E | La suite tarda 1,8 min en vacío y 11 cargada, y sus esperas fijas pueden caducar sin decir si el problema es el código o el ordenador (los cuatro rojos que primero se le atribuyeron eran del servidor reutilizado, DEBT-021) | abierta |
| [DEBT-023](#debt-023--una-tarjeta-de-anki-no-puede-ser-una-pregunta-porque-no-hay-dónde-guardar-su-respuesta) | S12.6 | El modelo tiene el tipo `free_text_reference` y no tiene dónde guardar la respuesta de referencia: el reverso de una tarjeta no entra | abierta |
| [DEBT-024](#debt-024--la-clasificación-se-pide-de-forma-síncrona-y-con-el-corpus-entero-tarda-demasiado) | S12.6 | «Buscar propuestas ahora» clasifica todo el corpus en la misma petición: con material real tarda decenas de segundos y bloquea la pantalla | cerrada |
| [DEBT-025](#debt-025--corregir-una-pregunta-infla-el-conjunto-y-puede-volver-a-preguntarse-el-texto-viejo) | S12.6 | La versión sustituida de una pregunta corregida cuenta como pregunta: el conjunto se infla, el banco enseña el enunciado viejo y una sesión nueva puede componerse con él | **cerrada** (22 de septiembre de 2026: las consultas del banco dejan fuera `superseded`, y la historia se sigue leyendo pidiéndola) |
| [DEBT-026](#debt-026--la-suite-e2e-toma-su-directorio-de-datos-del-entorno-y-escribe-donde-le-digan) | S12.6 | Playwright resuelve su directorio de datos con `OPOFUENTE_DATA_DIR`: con esa variable puesta apuntando a una copia del corpus del propietario, correr la suite a mano escribe las pruebas **dentro de su material** | **cerrada** (22 de septiembre de 2026: la suite usa siempre `.e2e-data` y, para apuntarla a otro sitio, una variable propia) |
| [DEBT-027](#debt-027--07_ui-ux-no-está-aplicada-entera) | S12.6 | La especificación de interfaz pide cosas que no existen: pausar un lote, tabla de revisión virtualizada, columnas de preguntas y próxima revisión en el Programa, lector sincronizado y explicación por opción | abierta (auditada sección a sección el 22 de septiembre de 2026; lo que faltaba en Inicio y en las comprobaciones de accesibilidad ya está) |

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

**Estado: cerrada (21 de septiembre de 2026), con el último trozo hecho al revisar el registro.** S12
entregó la clasificación por proveedor; lo que quedaba era lo que el criterio 3 pedía y nadie había
hecho: **quitar el booleano**. Criterio por criterio:

1. **`/settings` y `/capabilities`** exponen la clasificación por proveedor con su motivo
   (`llm.destination` + `destination_reason`, `embeddings.destination` + `destination_reason`). Las
   capacidades de `llm` y `embeddings` dicen **su** destino: antes el detalle del modelo de lenguaje se
   calculaba con un booleano global que mezclaba los dos, así que un endpoint de embeddings remoto
   aparecía acusando al modelo de lenguaje de enviar los fragmentos fuera.
2. **Pruebas unitarias de la clasificación** (`apps/api/tests/unit/test_provider_destination.py`, 21
   casos): loopback por nombre, `::1`, IPv4-mapped, rangos privados, link-local → `local`; dominios
   públicos y direcciones fuera de rango → `remote`; vacío, no-URL y esquema que no es http(s) →
   `unknown`; proveedor desactivado → `disabled`; proveedor activo **sin** endpoint → `unknown`; y que
   el motivo nombre el host y no la URL entera.
3. **El booleano ya no existe**: ni en la respuesta (`LlmSettingsSchema`) ni en `Settings`. Se quitó
   `Settings.sends_data_off_device` (que después de S12 era el resumen conservador de los dos
   proveedores) porque tener dos formas de decir el mismo destino es tener dos formas de equivocarse, y
   una de ellas ya se equivocó: `sends_content_off_device` sigue existiendo como la **regla** («`unknown`
   cuenta como que sí sale») que usan la pantalla y las capacidades.
4. **La pantalla lo enseña**: Ajustes muestra, por proveedor, «no sale de tu equipo» / «sale a un
   tercero» / «no se puede determinar» / «sin proveedor», y **el estado del sistema usa la misma
   frase** (antes decía «todo local» o «enviaría datos fuera» a partir del booleano): una sola manera
   de decirlo, en un solo sitio (`features/system/labels.ts`).

Lo que **no** cierra esta entrada: sigue sin haber proveedor de lenguaje ni de embeddings, así que estas
pantallas dicen «sin proveedor» y nada se envía. Eso es DEBT-014, no esta deuda: aquí lo que se pedía era
que **cuando** haya proveedor, la aplicación sepa —y diga— a dónde va el contenido.

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

**Estado: cerrada en S12.** Lo entregado, criterio por criterio:

1. **Rutas explícitas, sin purga automática**: `GET /housekeeping` mide y **no escribe**;
   `POST /housekeeping/temps`, `/orphan-artifacts` y `/old-jobs` retiran lo que se les pide, con
   `confirm: true` obligatorio en el cuerpo (un `confirm` falso responde 409 y no toca nada). No hay
   ninguna purga al arrancar ni en segundo plano.
2. **Lo referenciado no se toca**: la consulta de huérfanos comprueba **cinco** referencias
   (`artifact_origins`, `document_versions`, `extracted_representations`, `item_representations` e
   `ingestion_items.artifact_id`), y la retirada **vuelve a comprobarlo** antes de borrar: entre la
   foto y la retirada puede haber pasado tiempo. Probado en
   `test_lo_referenciado_no_se_propone_retirar` y `test_retirar_lo_referenciado_se_salta_y_se_dice`.
3. **Temporales**: se retiran los `.part` y los árboles de trabajo que quedan en `tmp/`, siempre
   **dentro** del árbol de datos (`is_within`) y nunca nada de fuera, con el recuento y los bytes
   liberados en la respuesta. Probado en `test_retirar_temporales_respeta_los_que_estan_fuera_del_arbol`.
   La antigüedad mínima que pedía el criterio **no** se ha implementado: la retirada es explícita y
   solo mira `tmp/`, así que un temporal en curso solo se retira si alguien lo pide a propósito —y en
   ese caso tampoco se le estaría quitando nada al usuario—. Queda escrito aquí como diferencia
   consciente con el texto original del criterio.
4. **Los originales del usuario**: el servicio solo mira dentro de `data/` (es una guarda explícita,
   no una promesa), y la comprobación de que nada de fuera se toca está en la prueba del punto 3.
5. **La pantalla**: la foto del almacén (`usage` por área, candidatos con su motivo y `reclaimable_bytes`)
   es lo que Ajustes enseña; el resultado de cada retirada viaja con su detalle. La interfaz de la
   pantalla de Ajustes se cierra en el commit siguiente de S12.

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
mitad que falta de «parser desde texto/documento»: hoy el camino es texto, CSV y JSON.

**Plazo vencido (revisión de S00–S11, 19 de septiembre de 2026).** El plazo era «antes de S11» y S11
está entregado: `docs/slices/S11.md` reconoce que las aristas hacia preguntas llegarán «cuando llegue
DEBT-010», así que la obligación sigue viva pero **fuera de plazo**. Lo que sí se cerró en la revisión
fue la otra mitad del entregable: el asistente **JSON**, que no existía y no estaba declarado en ningún
sitio.

**Obligación.** Antes de que la ficha de pregunta pueda enseñar el original al lado con su cita (07_UI-UX
§7) y antes de S11 (cambios e invalidación, que necesita saber qué preguntas dependen de qué evidencia)
—plazo **ya vencido**, ver arriba—:

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

**Estado: cerrada (20 de septiembre de 2026).** Criterio por criterio, y con las decisiones escritas:

1. **Cita con su fragmento, su página y su etiqueta.** `POST /question-sets/{id}/import-document` (ruta
   añadida al contrato, registrada en ADR-013) lee la versión por sus fragmentos, reconstruye el texto
   conservando la estructura de líneas y crea, por pregunta, una `question_evidence` con papel `stem`,
   estado `accepted` y el fragmento exacto del que se leyó el enunciado. El texto de la versión se lee
   en el orden que dejó la extracción y la **sección** de origen se guarda en
   `question_versions.source_section_id` —el campo existía desde S05 y nadie lo rellenaba—. Probado en
   `test_importar_desde_un_documento_enlaza_cada_pregunta_con_su_fragmento`: tres preguntas, tres citas,
   cada una con su span, su página, su etiqueta de cita y su sección, y sin cruzarse entre secciones.
2. **La ficha enseña la cita y la abre.** La evidencia se pinta con su etiqueta, su texto y su enlace
   «abrir el original» a `GET /document-versions/{id}/original#page=N`. Probado en la interfaz (`la cita
   se puede abrir en el original y en su página`, y el caso sin página, que no inventa un salto) y de
   extremo a extremo en `E2E-05 importación: las preguntas de un documento entran con su cita y se abre
   el original`, que sube un temario por la Bandeja, lo promociona, acepta su versión, importa las
   preguntas **desde la pantalla** y abre la cita.
3. **La parte detectada no se pierde en silencio, y se decidió dónde vive.** El rótulo del material viaja
   en el informe (`parts_detected`) con el texto que dice que **no** se guarda por pregunta, y el
   **ADR-014** decide por qué: el modelo no liga preguntas a `exam_parts`, emparejar «Parte 2» con un
   código de la convocatoria sería adivinar, y guardar el rótulo suelto sería un dato que ninguna
   pantalla lee. Probado en la prueba de integración (el rótulo `["2"]` llega declarado) y en la de
   interfaz.

**Lo que la deuda pedía y se resolvió decidiendo, no implementando** (todo en el ADR-014): `tags` y
`source` —y `section`, `reference`, `image`, `id` del JSON— siguen leyéndose y declarándose en
`ignored_columns`, pero ya no como un «todavía»: **es su destino final**, porque ninguna pantalla,
filtro ni exportación consume etiquetas libres y la procedencia ya está resuelta con la cita. Quitar
`tags` y `source` del mapeo contradiría `04_INGESTION` §10 sin ganar nada; guardarlos sería coleccionar
datos que nadie lee.

**Dos cosas que este cierre añade y conviene saber:**

- **Solo se importa de la versión aceptada.** Una candidata no es la versión buena (la regla de la
  Biblioteca), así que la pantalla deja el botón deshabilitado y dice qué hacer mientras la versión no
  esté aceptada. Está decidido en el ADR-014 y probado en la interfaz.
- **Volver a importar el mismo documento repara las citas**: la pregunta ya estaba (idempotente por
  huella) y el enlace se crea si no existía, sin duplicar nada. Probado en
  `test_importar_dos_veces_el_mismo_documento_no_duplica_ni_la_pregunta_ni_la_cita`, y el caso contrario
  —una versión sin texto extraído— en `test_una_version_sin_fragmentos_no_inventa_citas`: el informe
  trae su incidencia y **no** se crea ninguna evidencia vacía.

**Lo que queda fuera a propósito:** la parte del examen no se guarda (ADR-014, con lo que haría falta
para guardarla) y las etiquetas libres tampoco. Ninguna de las dos es una promesa incumplida: las dos
están decididas y se declaran donde se leen.

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

**Estado: cerrada en la revisión de S00–S11 (19 de septiembre de 2026).** La obligación se fijó «antes
de S09» y los slices S09, S10 y S11 se entregaron sin cumplirla ni reasignarla: era una deuda vencida
que se estaba leyendo como abierta y en plazo. Se cerró en la revisión, con lo que pide el criterio:

- `apps/web/src/api/questions.ts` acepta el desplazamiento y `useSetQuestions` lo incluye en la clave de
  la consulta, así que dos páginas del mismo filtro son dos respuestas distintas;
- `features/questions/QuestionTable.tsx` dice «*desde*–*hasta* de *total* preguntas del conjunto» y
  ofrece «Página anterior» / «Página siguiente», que piden al servidor con `offset`;
- cambiar cualquier filtro (estado, origen, reservas) vuelve a la primera página: no se mezclan páginas
  de filtros distintos;
- la prueba de interfaz `pagina el banco con el desplazamiento en el servidor y dice en qué tramo está`
  recorre 250 preguntas en dos páginas y vuelve atrás.

Lo que **no** cierra esta entrada: la lista de conjuntos sigue pidiendo `limit=100&offset=0`. Un
poseedor de más de cien conjuntos de preguntas no cabe en esa lista, y eso queda declarado aquí como
parte viva de la deuda aunque el criterio de cierre (preguntas de un conjunto) esté cumplido.

## DEBT-012 — Modos de sesión declarados y sin implementar

**Origen:** cierre de S07 (17 de septiembre de 2026).

**Problema.** 06_QUESTIONS §5 define cinco modos de sesión y 03_DATA-MODEL §7 los nombra en el
vocabulario de `study_sessions` (`practice`, `error_review`, `official_exam`, `mock_exam`,
`diagnostic`). S07 implementó **dos** (práctica y examen oficial) y **S10 añadió el repaso de
errores**, que compone la sesión con lo vencido de la cola. Pedir cualquiera de los otros dos
responde 409 `unsupported` con el motivo, así que no se simula nada; pero el producto promete esos
modos y hoy no existen:

| Modo | Qué le falta |
|---|---|
| `mock_exam` (simulacro) | la composición que evita preguntas vistas recientemente y la etiqueta de «no oficial» |
| `diagnostic` (diagnóstico) | la muestra estratificada por tema y la estimación con incertidumbre (no un porcentaje de dominio con dos preguntas) |

**Obligación.** Implementar cada modo **con lo que promete la especificación**, o retirarlo del
vocabulario si el producto decide no ofrecerlo. Mientras no exista, el vocabulario del modelo y el del
contrato no coinciden a propósito: el contrato solo declara los modos que se corrigen de verdad
(`SessionModeName` en `api/study_schemas.py`, que desde S10 incluye `error_review`).

**Criterio de cierre.**

1. Cada modo pendiente o bien está implementado de punta a punta (crear, componer, corregir y
   resultado) con su prueba de API y de interfaz, o bien ha desaparecido del vocabulario del modelo con
   su migración.
2. El contrato declara exactamente los modos que existen, y el vocabulario del modelo y el del contrato
   vuelven a coincidir.
3. Una prueba comprueba que un modo declarado en el contrato no responde 409 `unsupported`.

**Estado: cerrada (21 de septiembre de 2026).** Los dos modos que faltaban están construidos, y el
vocabulario del modelo y el del contrato vuelven a coincidir:

1. **Simulacro (`mock_exam`)** — «el perfil exacto, sin llamarse oficial, evitando lo visto hace poco»
   (06_QUESTIONS §5). Monta el tamaño y las reservas de la convocatoria, corrige **al terminar** (el
   dominio lo exigía desde S07 y no había modo que lo usara) y ordena el banco por frescura antes de
   elegir: primero las preguntas que no se han intentado en los últimos 60 días —la misma ventana que
   usa la estimación de dominio— y solo después las demás. La sesión nace con su **nota de
   composición** («ninguna de sus preguntas se había intentado en los últimos 60 días» o «N de M ya se
   habían intentado, porque el banco no daba para más»), que se **enseña** mientras se contesta y en el
   resultado: un aviso que el servidor manda y nadie pinta no existe. Y el resultado se explica con
   `MOCK_EXAM_NOTE`: el perfil es el del examen, pero **no es un examen oficial**.
2. **Diagnóstico (`diagnostic`)** — «muestra pequeña estratificada, con estimación por tema y
   **intervalo**, no un porcentaje de dominio» (§5). Compone una muestra **repartida por temas** del
   programa (round-robin: una de cada tema antes de repetir en uno, empezando por las preguntas menos
   intentadas, con el tope declarado y los temas que se quedan fuera por el tope escritos), congela las
   preguntas **sin parte** —no es un examen de una parte— y `GET /study-sessions/{id}/diagnostic` (ruta
   añadida al contrato, registrada en ADR-013) devuelve la lectura: por tema, lo contestado y su
   **intervalo de Wilson al 95 %**, con el tamaño de la muestra delante y la frase que dice que no es una
   nota ni un dominio. Los temas sin ninguna respuesta en la muestra se declaran, y una pregunta sin tema
   asignado no entra en la muestra y se cuenta (no se reparte a un tema que no le corresponde).
   **Corrige al terminar**, y no por copiar al examen: la muestra mide lo que sabes ahora, y ver la
   respuesta a mitad mejoraría las siguientes preguntas del mismo tema —que es lo que se está midiendo—;
   pedir otra corrección se rechaza con el motivo.
3. **El contrato declara los cinco** (`SessionModeName`), y una prueba —`los_cinco_modos_del_vocabulario_se_pueden_pedir`— comprueba que ninguno responde «no implementado»: los que se niegan, se niegan
   por falta de material (sin temas, sin nada vencido) y lo dicen con ese motivo.

**Un defecto que apareció al construir el diagnóstico, y que se arregla aquí:** la pantalla creaba los
conjuntos **sin convocatoria**, así que la columna `topic` de un CSV no tenía contra qué resolverse y los
temas se perdían **en silencio** (el asistente ofrecía la columna, el informe no decía nada y el banco
quedaba sin cobertura de programa). Ahora el formulario manda la convocatoria activa de la oposición y el
informe declara los temas que no se han podido emparejar (`topic_without_convocation`, `topic_not_found`)
en lugar de callárselos.

**Pruebas:** unitarias del dominio (`test_diagnostic.py`: reparto round-robin, tope con temas fuera,
muestra sin temas, y los intervalos calculados a mano —2 de 2 da (0,34; 1,0) y no «dominio perfecto»—);
de API (`test_un_simulacro_monta_el_perfil_exacto_y_no_se_llama_oficial`,
`test_un_simulacro_evita_las_preguntas_vistas_hace_poco` —que comprueba **en la composición**, no solo en
la nota, que ninguna vista entra—, `test_un_simulacro_sin_banco_suficiente_repite_y_lo_dice`,
`test_un_diagnostico_compone_una_muestra_pequena_por_tema`,
`test_un_diagnostico_corrige_al_terminar_y_no_deja_elegirlo`,
`test_la_lectura_del_diagnostico_da_por_tema_un_intervalo`,
`test_la_lectura_por_temas_no_vale_para_una_practica` y
`test_un_diagnostico_sin_temas_suficientes_no_se_monta`); de interfaz (el simulacro se pide con el perfil
y sin campos que la convocatoria fija; el diagnóstico se pide sin conjunto ni parte; la nota de
composición se enseña mientras se contesta **y** en el resultado; la lectura se enseña con su intervalo y
su aviso); y de extremo a extremo, los dos modos por el navegador:
`E2E-06 un simulacro monta el perfil exacto y el resultado no se llama oficial` (importa las 85 preguntas
del perfil, monta el simulacro desde la pantalla, termina sin contestar y lee el resultado) y
`E2E-06 un diagnóstico reparte la muestra por temas y la lee con su intervalo` (importa un CSV con temas,
monta el diagnóstico, contesta la muestra entera y lee el intervalo).

**Lo que la revisión propia de este cierre encontró y arregló**, porque no lo cubría ninguna prueba: la
**nota de composición no se pintaba en ninguna parte** (el servidor la mandaba y la guardaba, y la
pantalla no la enseñaba, así que el «cuántas he repetido» que promete el simulacro era invisible). Ahora
se enseña en las dos pantallas donde la sesión está a la vista: mientras se contesta y en el resultado, y
hay una prueba de interfaz que la fija.

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

**Plazo vencido (revisión de S00–S11, 19 de septiembre de 2026).** S09 y S11 están entregados y la
obligación no se cumplió ni se reasignó: el recálculo sigue siendo de una sesión (`POST
/study-sessions/{id}/recalculate`, S08) y `S11.md` no la menciona. Sigue abierta y fuera de plazo, con
su sitio natural en la pantalla de claves (avisar de cuántas sesiones quedan desactualizadas) y no en
un slice futuro.

**Criterio de cierre.**

1. Existe una acción que recalcula todas las sesiones terminadas que usaron una clave concreta, con
   un informe por sesión (antes, después y si cambió).
2. Una prueba comprueba que una sesión ya recalculada no se recalcula dos veces con la misma clave
   (idempotencia) y que el resultado de la clave intermedia sigue siendo legible.
3. La interfaz dice cuántas sesiones quedan desactualizadas después de activar una clave nueva, en
   lugar de dejar que se descubra sesión a sesión.

**Estado: cerrada (19 de septiembre de 2026).** Lo entregado:

1. **`POST /question-sets/{set_id}/recalculate-sessions`** recalcula **todas** las sesiones
   terminadas del conjunto con su clave activa y devuelve un informe con **una entrada por sesión**:
   puntuación antes, puntuación después, plantilla antes, plantilla después y si cambió. Las sesiones
   que siguen en marcha no entran —se corrigen al terminar— y se dice en el propio informe.
   Probado en `test_recalcular_en_bloque_todas_las_sesiones_del_conjunto`, que comprueba además que
   el resultado anterior de cada sesión sigue legible (`recalculation.previous_total`).
2. Sumado a lo que ya hacía S08, recalcular dos veces con la misma clave es idempotente
   (`save_evaluation` no escribe una evaluación nueva si ya existe para ese intento y esa clave).
3. **El criterio 3, cerrado.** La pantalla de plantillas dice cuántas sesiones terminadas del
   conjunto no están corregidas con la plantilla activa y ofrece recalcularlas de una vez. Se apoya en
   **`GET /question-sets/{set_id}/outdated-sessions`** (ruta añadida al contrato), que cuenta por
   sesión y no por impresión: mira la evaluación **vigente** de cada intento y la compara con la clave
   activa, así que el número baja a cero cuando se recalcula en lugar de quedarse encendido. Las
   sesiones terminadas **sin ninguna corrección guardada** se cuentan aparte, porque no hay nada que
   comparar y contarlas como pendientes dejaría un número que no bajaría nunca. Probado en
   `test_decir_cuantas_sesiones_quedan_desactualizadas_tras_activar_una_clave` (0 → 2 → 0,
   comprobando además que los tres recuentos suman las terminadas),
   `test_una_sesion_terminada_sin_correcciones_no_se_cuenta_como_desactualizada` y, de interfaz, en
   las tres de `preguntas: plantillas`; de extremo a extremo, en el guion `E2E-06 activar una clave
   corregida avisa y recalcula lo ya corregido`, que recorre el ciclo completo contra el servidor
   real: sesión fallada (−1) → clave corregida → «1 sesión desactualizada» → recalcular → «0
   desactualizadas» con «de −1 a 3» en el informe.

**Nota sobre el alcance:** el recálculo en bloque se limita al **conjunto** de preguntas, que es el
ámbito de la plantilla. Una clave puede cubrir material de varios conjuntos (el mismo temario
importado dos veces), y en ese caso hay que pedirlo una vez por conjunto: se dice aquí en lugar de
prometer un «recalcular todo» que hoy no existe.

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

**Estado: cerrada (19 de septiembre de 2026), en S12, con una honestidad sobre el criterio 2.**
Entregado en la pantalla de Ajustes, sección «Índice de búsqueda»:

1. `GET /search/index` dice si el índice está completo, cuántos fragmentos hay y cuántos faltan, y
   `POST /search/reindex` lo rehace. La pantalla enseña el antes y el después, los segundos que ha
   tardado y de dónde venían los fragmentos; el texto de las evidencias no se toca: el índice es
   derivado. Probado en `test_rehacer_el_indice_dice_lo_que_ha_hecho` (integración) y en
   `test_rehacer_el_indice_cuenta_antes_y_despues` / `test_rehacer_el_indice_vacio_lo_dice_sin_fingir_trabajo`
   (unitarias).
2. **El criterio 2 no se puede cumplir como está escrito, y se dice por qué**: el índice es FTS5 de
   contenido externo, y `DELETE FROM evidence_fts` (o `delete-all`) no lo vacía, así que un «borrado
   a mano» desde SQL mide otra cosa. Lo que sí está probado es (a) que tras un `rebuild` de SQLite la
   búsqueda encuentra el mismo fragmento (`test_migrations_0018.py`) y (b) que la acción deja el índice
   completo y la búsqueda sigue encontrando lo que ya estaba. La variante «faltan fragmentos» se
   prueba en la unitaria de `index_health`, donde el descuadre se puede simular de verdad.
3. El botón se deshabilita mientras la operación está en marcha (estado `ocupado` compartido con el
   resto de acciones de la pantalla) y el resultado se da con cifras y con el tiempo medido, no como
   un «hecho» instantáneo.

## DEBT-016 — La dificultad observada no existe y los umbrales de dominio son provisionales

**Origen:** cierre de S10 (18 de septiembre de 2026).

**Problema.** 06_QUESTIONS §9 pide estimar el dominio «basada en intentos recientes, **dificultad** y
repetición», y §4 lista «dificultad observada» entre los filtros del banco. S10 construyó la
estimación con lo que existe —acierto en una ventana reciente, con recuento— y lo declara en cada
respuesta, pero:

| Qué falta | Consecuencia |
|---|---|
| La dificultad de cada pregunta (no hay campo en `question_versions` ni estimación por intentos) | dos temas con el mismo acierto se ven igual aunque uno tenga preguntas mucho más difíciles |
| Umbrales de dominio calibrados | los actuales (`0,6` y `0,8` de acierto reciente) son provisionales y están escritos en un solo sitio con su aviso: nadie los ha validado con datos reales de estudio |
| El filtro «dificultad observada» en el banco | 06_QUESTIONS §4 promete un filtro que no existe |

**Obligación.** Con datos reales de estudio (el propietario empieza la prueba personal al cerrar S12),
decidir si la dificultad se estima desde los intentos (proporción de aciertos por pregunta) o se declara
en el material, incorporarla a la estimación de dominio y al filtro del banco, y **fijar los umbrales en
un ADR** con los datos que los sostienen.

**Criterio de cierre.**

1. Existe una medida de dificultad por pregunta, con su origen declarado (estimada o importada).
2. La estimación de dominio la usa, y su explicación dice de dónde sale cada término.
3. Los umbrales están respaldados por un ADR con datos de la prueba personal, y el banco puede filtrar
   por dificultad observada.
4. Una prueba comprueba que dos preguntas con los mismos intentos y distinta dificultad no dan el mismo
   dominio.

## DEBT-017 — Las colecciones existen en la API y no en la interfaz

**Origen:** revisión de S00–S11 (19 de septiembre de 2026), sobre el entregable de S05.

**Problema.** El entregable de S05 dice «Biblioteca, filtros, lector, versiones **y colecciones**», y
07_UI-UX §6 pide filtrar la lista de la biblioteca «por oposición, tipo, autoridad, estado, versión,
derechos, calidad **y colección**». El backend está entero y probado —`GET/POST /collections` y
`POST /collections/{id}/items`, con `test_una_coleccion_agrupa_sin_duplicar` y
`test_las_colecciones_agrupan_sin_duplicar`—, pero **no hay ninguna pantalla**: `apps/web/src` no
contiene ni una coincidencia de `collection`, y `features/library/DocumentDetail.tsx` declara cinco
pestañas, ninguna de colecciones. `docs/slices/S05.md` presentaba las colecciones como visibles en el
producto: era una promesa que el código no cumplía.

**Obligación antes de S12** (Ajustes y cierre del producto): una superficie real para las colecciones
—crear, listar, añadir y quitar miembros, y filtrar la biblioteca por colección— o retirar la promesa
del entregable y de la interfaz con su ADR. Lo que no vale es dejarlo como está: una API sin producto
que la prosa del slice cuenta como entregada.

**Criterio de cierre.**

1. Se puede crear una colección, meter un documento dentro y verla en la pantalla, con sus miembros.
2. La lista de la biblioteca se puede filtrar por colección, y el filtro se dice en pantalla como los
   demás.
3. Una prueba de interfaz recorre crear → añadir → filtrar → ver el documento dentro.
4. Si el producto decide no ofrecer colecciones, el entregable de S05 y 07_UI-UX §6 se corrigen con su
   ADR, y esta entrada se cierra por decisión, no por implementación.

**Estado: cerrada (19 de septiembre de 2026).** Se entregó la superficie real, criterio por criterio:

1. **Pantalla**: `apps/web/src/features/library/CollectionsPanel.tsx` lista las colecciones con su
   número de miembros (y su descripción), permite crear una con nombre y descripción, y **quitar
   miembros**: cada colección con miembros se despliega para verlos por su id y quitarlos uno a uno.
2. **Filtro en el servidor**: `GET /documents?collection_id=…`. El filtro se resuelve con un `EXISTS`
   correlacionado por los **cinco** tipos de sujeto (versión, artefacto, representación, sección y
   evidencia), así que un documento entra en la colección también si lo que está dentro es una cita
   suya. La pantalla lo dice cuando está filtrando y no descarta nada por su cuenta.
3. **Pruebas**: de contrato, `test_la_biblioteca_se_filtra_por_coleccion` (con los dos casos: miembro
   por versión y miembro por evidencia); de interfaz, las cinco de `biblioteca: colecciones` que
   recorren crear, filtrar, añadir la versión activa, quitar un miembro y el caso sin colecciones; y
   de extremo a extremo, el paso 11 de `E2E-04 documento compartido`, que crea la colección, añade la
   versión activa, filtra por ella, quita el miembro y comprueba contra la API que el documento sigue
   existiendo con sus dos versiones.
4. **Quitar un miembro no borra material**: `DELETE /collections/{collection_id}/items` quita el
   sujeto de la colección y no toca ni el documento, ni su versión, ni la cita. La pantalla lo dice
   con esas palabras en el aviso (`El documento no se ha borrado`) y el aviso aparece **donde se hizo
   la operación**, que es la tarjeta de colecciones.

**Dos defectos que solo aparecieron al terminar de verdad la superficie, y que merecen quedar
escritos** (los dos arreglados aquí, no aplazados):

- El aviso de la retirada guardaba su texto en el mismo estado que el de «añadir a una colección», y
  ese estado solo se pintaba dentro de la ficha de un documento abierto: quitar un miembro **con la
  ficha cerrada no avisaba de nada**. Se separaron los dos avisos y cada uno se pinta donde se
  provoca la acción.
- Con el filtro de una colección vacía activo, la lista enseñaba «Todavía no hay ningún documento» y
  el texto de que la biblioteca nace promocionando material: la biblioteca tiene documentos, lo que
  estaba vacío era la colección. Ahora ese caso dice lo que pasa.

**Y un fallo que encontró la prueba de integración, que merece quedar escrito:** la primera versión de
la consulta no correlacionaba las subconsultas a mano (`correlate(LogicalDocumentRecord)`), y
SQLAlchemy metía el documento en el `FROM` interno: el filtro devolvía **todos** los documentos en
lugar de los de la colección. Una consulta que «funciona» y devuelve de más es exactamente el tipo de
fallo que ninguna prueba de forma detecta; lo detectó contar los resultados.

## DEBT-018 — La puerta humana de S04 no se ejecutó

**Origen:** revisión de S00–S11 (19 de septiembre de 2026).

**Problema.** `11_IMPLEMENTATION-SLICES.md` fija para S04 una puerta humana explícita: «Importar copia
de 20–50 archivos TAI y medir revisión. **Si no ahorra tiempo, no iniciar S05 sin rediseño aprobado**».
`docs/slices/S04.md` reconoce que la copia se inventarió en lectura y no se importó, y aun así dio S05
por desbloqueado. La matriz de trazabilidad exige para RF-03 «propuestas, bulk, undo y **métricas de
muestra**», y las únicas métricas entregadas son de un dataset **sintético** —correctas y
reproducibles, pero no de material real—. No había entrada en esta lista: la puerta quedó abierta sin
que nadie la registrara.

**Obligación antes de usar material real de estudio.** Importar una copia de 20–50 ficheros TAI
reales (nunca los originales: la importación copia por contenido y no toca el origen), medir el tiempo
de revisión de la clasificación y decidir con ese número si el diseño se sostiene. Si no ahorra tiempo,
se rediseña la pantalla de revisión antes de seguir construyendo encima.

**Criterio de cierre.**

1. Existe un informe versionado con el tiempo de revisión medido sobre material real, con el número de
   propuestas revisadas, aceptadas, corregidas y descartadas.
2. La decisión («se sostiene» o «se rediseña así») queda escrita, con su ADR si toca rediseñar.
3. El propietario confirma el número: es una puerta humana, no una medición automática.

**Estado: abierta, con la mitad de la máquina medida (21 de septiembre de 2026).** Se importó una copia
de 30 ficheros reales del propietario (29 PDF y 1 DOCX, 11,8 MB) en una base **aparte** —nunca la real y
nunca los originales— y se midió lo que la máquina puede medir. El informe está en
`docs/reviews/DEBT-018-revision-material-real.md`, con el método para repetirlo. Los números:

| Paso | Medida |
|---|---|
| Inventario en lectura (30 ficheros) | 1,4 s · 30 descubiertos · 0 incidencias |
| Copia + extracción (el worker) | 2,8 s · 30 de 30 extraídos · 0 fallidos · 0 conservados sin extractor |
| Clasificación determinista | 46,7 s |
| Propuestas generadas | 90 (60 `topic`, 28 `document_type`, 2 `authority`) |
| **Pendientes de revisar a mano** | **38** (52 quedaron aplicadas de forma provisional) |

Lo que esto dice del diseño, sin adornos: **38 propuestas para 30 ficheros**, 26 de ellas de
`document_type`. El coste de la revisión no es despreciable y se concentra en un eje: ahí tiene su primer
objetivo cualquier rediseño que quiera ahorrar tiempo.

**Por qué sigue abierta:** falta lo que no puede medir la máquina —el **tiempo de revisión** del
propietario sobre esas 38 propuestas, los recuentos de revisadas/aceptadas/corregidas/descartadas, la
decisión escrita y su confirmación (criterio 3). Lo que hay es la mitad reproducible; la mitad que
decide si el producto ahorra tiempo necesita una persona, y esa persona es el propietario.

## DEBT-019 — El estado «conservado sin extractor» no llega a la pantalla

**Origen:** revisión de S00–S11 (19 de septiembre de 2026), sobre la deriva documental de S02 y S03.

**Problema.** Desde S03 un `.pptx`, `.xlsx` o `.epub` **no se omite**: se copia y se conserva como
`unsupported_preserved` (DEBT-008, cerrada). La documentación de S02 sigue describiendo lo contrario
(«`.pptx`, `.xlsx`, `.epub` y similares **no se copian**»), y `DEBT-008` se cerró citando pruebas de
interfaz y un E2E con un `.xlsx` que no existen: el estado se guarda y se sirve, pero ninguna prueba de
interfaz comprueba que el estado llegue a la pantalla con su nombre legible.

**Obligación antes de S12**: que el estado «conservado sin extractor» se vea en la bandeja con su
nombre y su explicación (no como el código crudo del enum), con prueba de contrato y de interfaz, y
corregir los documentos de S02 que describen la omisión que ya no ocurre.

**Criterio de cierre.**

1. Una entrada conservada sin extractor se ve en la bandeja con un texto legible que dice que se ha
   copiado y que no hay extractor para su formato.
2. Una prueba de interfaz y una de contrato lo comprueban con un `.xlsx` real de fixture.
3. Los documentos de S02 y S03 que afirman la omisión quedan corregidos o marcados como históricos.

**Estado: cerrada (19 de septiembre de 2026).** Criterio por criterio:

1. **La bandeja ya no pinta el enum crudo**: `TrayPage.tsx` tiene un mapa `ITEM_STATUS` con el nombre
   legible y el tono de cada estado. `unsupported_preserved` se enseña como «conservada sin extractor
   (copiada, sin texto)», con tono de aviso —no de fallo— y con el motivo que sirve el servidor al
   lado. Antes se veía `unsupported_preserved`, que no dice nada a quien lo lee.
2. **Dos pruebas nuevas**: `test_un_formato_sin_extractor_se_conserva_y_la_api_lo_dice` (integración,
   de punta a punta: un `.xlsx` entra por una carpeta, el worker lo copia y lo extrae sin extractor, y
   la API devuelve el estado con su motivo; el `.txt` del mismo lote sí se extrae) y `un formato sin
   extractor se ve como conservado y sin texto, no como un fallo` (interfaz).
3. **La documentación de S02 ya estaba corregida** en la revisión de S00–S11: la limitación 3 de
   `docs/slices/S02.md` dice ahora, en su sitio, que S03 cambió ese comportamiento y que esa frase
   describe el estado de S02. La de S03 se revisó y no afirmaba la omisión.

**Lo que este cierre no incluye:** prueba de **contrato** del estado en el esquema (el criterio 2
pedía una de interfaz y una de contrato). Lo que hay es la de integración —que comprueba el valor
servido por la ruta real— y la de interfaz; el esquema no gana un `Literal` con los estados de entrada
porque ya valida el campo como texto y añadirlo sería un cambio de contrato para una deuda ya cubierta
por dos capas. Queda dicho en lugar de contarlo como hecho.

---

## DEBT-020 — La clave oficial de Celador está escaneada y no se puede importar

**Origen:** alta del tercer perfil (`celador-sacyl-2022`, 22 de septiembre de 2026).

**Problema.** El tribunal publicó la **plantilla de respuestas correctas** del ejercicio de Celador
del llamamiento del 12 de noviembre de 2023, y es la clave de las 77 preguntas de ese cuestionario.
Pero el PDF que publica el portal de Salud es un **escaneo sin capa de texto**: PyMuPDF no extrae ni
una palabra de sus dos páginas. La aplicación importa preguntas y claves **leyendo texto**; sin texto
no hay enunciados, ni opciones, ni clave, y no se puede rellenar a mano un cuestionario de 77
preguntas sin transcribirlo entero.

Esto no es un defecto de la herramienta: es una característica de la fuente, y el proyecto no inventa
datos que no puede leer. Se registra para no dar por hecho que «está publicada, luego se puede
importar».

**Obligación antes de usar este perfil para practicar con preguntas oficiales:** o bien incorporar un
lector de PDF escaneado (OCR local, sin salida a la red) con su prueba sobre este documento concreto,
o bien declarar en la interfaz que la clave de este ejercicio no se puede importar y ofrecer la
transcripción manual con su cita. Lo que no vale es dejar creer que la clave entra sola.

**Criterio de cierre.**

1. La plantilla de Celador se importa de punta a punta (OCR local verificado pregunta a pregunta
   contra el escaneo, o transcripción manual con su incidencia), y las 77 preguntas quedan con su
   clave y su cita a la página del escaneo.
2. Hay una prueba con **el documento real** (no con un PDF de laboratorio) que comprueba que las
   respuestas importadas coinciden con la plantilla publicada.
3. Si se elige no hacerlo, la interfaz dice, con esas palabras, que la clave oficial de este ejercicio
   no se puede importar y por qué, y ninguna pantalla promete lo contrario.

**Estado: abierta.** El perfil sirve para estudiar el programa (16 temas) y las reglas del examen,
que es para lo que se dio de alta; la clave oficial de este ejercicio queda pendiente de esa decisión.

---

## DEBT-021 — La puerta E2E puede correr contra un servidor ajeno

**Origen:** alta del tercer perfil (`celador-sacyl-2022`, 22 de septiembre de 2026).

**Problema.** `apps/web/playwright.config.ts` levanta su propia API sobre `.e2e-data`… salvo que ya
haya algo escuchando en `127.0.0.1:8765`, porque usa `reuseExistingServer: !process.env.CI`. En esta
máquina había quedado vivo un servidor de la medición de DEBT-018, con
`OPOFUENTE_DATA_DIR=F:\temp-opofuente\datos-apuntes-tai` (una copia del material real del
propietario). Las primeras corridas de la suite E2E de este trabajo **reutilizaron ese servidor**: no
se migró ni se sembró `.e2e-data`, las pruebas hablaron con la base de esa medición y **escribieron en
ella** (lotes, documentos, conjuntos de preguntas, propuestas de clasificación). Además, los fallos
que produjeron parecían una regresión del cambio que se estaba midiendo, y no lo eran.

Nada de esto se ve: la suite no dice contra qué base está corriendo, y el puerto ocupado no produce
ningún aviso.

**Obligación antes de dar por buena cualquier corrida de E2E:** que la suite compruebe que el servidor
que reutiliza es el suyo, o que no reutilice ninguno.

**Criterio de cierre.**

1. Antes de reutilizar un servidor, la suite lee `GET /api/v1/settings` y compara `data_dir` con el
   directorio de datos del E2E; si no coincide, falla con un mensaje que dice qué servidor ocupa el
   puerto y con qué datos.
2. Prueba de que, con un servidor ajeno escuchando en el puerto, la suite no reutiliza ni escribe
   nada.
3. `docs/OPERACION.md` explica cómo liberar los puertos 8765 y 4173 antes de correr las puertas.
4. La medición de DEBT-018 se rehace sobre una copia limpia: la actual recibió datos de E2E y sus
   recuentos ya no son solo del material real.

**Estado: abierta, con los criterios 1, 2 y 3 cerrados.** Lo entregado en S12.4 (22 de septiembre de
2026): la suite **ya no reutiliza** ningún servidor (`reuseExistingServer: false` en los dos: la API y
la vista previa), así que un puerto ocupado hace fallar la corrida en vez de correrla contra la base de
otro; y `docs/OPERACION.md` §5 explica cómo liberar los puertos. Queda el criterio 4, que es del
propietario (rehacer la medición de DEBT-018 sobre una copia limpia).

**Criterio 2, cumplido y ejecutado (23 de septiembre de 2026).** Se levantó un listener propio en
`127.0.0.1:8765` que no habla el protocolo de la aplicación y se lanzó una corrida corta de la suite:

| Qué se midió | Resultado |
|---|---|
| código de salida de la corrida | **1** (no corre) |
| mensaje | `Error: Process from config.webServer was not able to start. Exit code: 3` y `[Errno 10048] error while attempting to bind on address ('127.0.0.1', 8765)` |
| peticiones recibidas por el servidor ajeno | 10, **todas** `GET /api/v1/health/live` (la sonda con la que Playwright decide si reutilizar); **ninguna escritura** |

La corrida falla, no se ejecuta ninguna prueba y el servidor ajeno no recibe nada más que sondas de
lectura: la suite no escribe en datos que no son suyos. Como guarda permanente, además de esta
medición, queda una prueba de componentes (`playwright-config.test.ts`) que lee la configuración de
verdad y falla si alguien vuelve a poner `reuseExistingServer: true` o si la API del E2E deja de fijar
su propio `OPOFUENTE_DATA_DIR`.

Lo que se aprendió al hacerlo, y que conviene no olvidar: el servidor y la vista previa que arranca
Playwright **sobreviven** a una corrida interrumpida. Con la reutilización activa, un servidor viejo
apuntando a un `.e2e-data` que ya se había borrado hacía fallar cuatro pruebas por motivos que
parecían del producto (un 409 al aceptar una versión, un texto que no aparecía) y dedicar una tarde a
buscarlos donde no estaban.

---

## DEBT-022 — La suite E2E no distingue «la máquina está cargada» de «esto se ha roto»

**Origen:** verificación de S12.1 (22 de septiembre de 2026).

**Problema.** La misma suite, sobre el mismo árbol y con `.e2e-data` borrado, dio dos resultados
opuestos según el estado de la máquina y del puerto:

| Corrida | Entorno | Resultado |
|---|---|---|
| con el perfil nuevo | un servidor E2E viejo ocupando el 8765 (y la base ya borrada) | 34 pasan, **10 fallan**; la suite tarda 11 min |
| sin el perfil nuevo, para comparar | igual | **las mismas cuatro pruebas** fallan por los mismos motivos |
| con el perfil nuevo, puerta 18 de `gates.ps1` | puertos libres, máquina descargada | **45 pasan**, en 1,8 min |

**Corrección al diagnóstico inicial (22 de septiembre de 2026, S12.4).** Lo que primero se atribuyó a
la carga de la máquina era, sobre todo, **el servidor reutilizado** de DEBT-021: cuatro pruebas
fallaban igual con cualquier árbol porque hablaban con un `uvicorn` viejo cuya base de datos ya no
existía. Con eso cerrado, la carga de la máquina ya no produjo ningún rojo, aunque sí alarga la suite
de 2 a 11 minutos.

Lo que queda de esta deuda es entonces más estrecho y más honesto:

| Prueba | Qué decía el fallo |
|---|---|
| `questions.spec.ts:118` | «aceptar la versión: 409» — era el servidor ajeno (DEBT-021) |
| `questions.spec.ts:195` | no aparecía el texto «con clave activa» — lo mismo |
| `review.spec.ts:186` | no aparecía «propuestas nuevas» — lo mismo, más la clasificación síncrona (DEBT-024) |
| `review.spec.ts:400` | tiempo agotado — carga de la máquina |

**Tercera causa, medida en S12.2 (23 de septiembre de 2026): el directorio de datos del E2E acumula
estado y hay selectores que lo notan.** Corriendo la puerta 18 con `.e2e-data` de varias corridas
interrumpidas (no de una corrida limpia), dos pruebas fallaron por motivos que no eran del código:

| Prueba | Qué decía el fallo | Causa |
|---|---|---|
| `questions.spec.ts:118` | «aceptar la versión: 409» | la versión de una corrida anterior ya estaba aceptada |
| `changes.spec.ts:141` | `getByText('propuesto, sin aplicar')` resolvió a **3** elementos | tres conjuntos de cambios sin aplicar, uno de esta corrida y dos heredados |

Ninguna de las dos pruebas crea un dato único (mismo fichero de entrada, misma frase buscada), así que
funcionan solo mientras el directorio esté recién hecho o el dato anterior no colisione. Con
`.e2e-data` borrado, la puerta volvió a estar verde. Lo que esto añade a la obligación de arriba: **una
prueba que reutiliza datos tiene que decir de qué dato habla** (por fila, por identificador o por
nombre propio), o el rojo no se puede atribuir.

**Las dos se arreglaron el 23 de septiembre de 2026** (segunda vez que aparecieron, ya sin servidor
ajeno de por medio), aplicando esa regla a cada una:

| Prueba | Qué hace ahora |
|---|---|
| `questions.spec.ts:118` | el texto que se pega lleva una nota con el sufijo de la corrida: la promoción es idempotente **por artefacto** (el mismo contenido no se promociona dos veces), así que sin contenido único la segunda corrida recibía la versión ya aceptada de la primera y «aceptar» contestaba 409 |
| `changes.spec.ts:141` | la propuesta se busca **por el título de su documento** (que lleva el sufijo) y se selecciona antes de leer el detalle, en vez de dar por hecho que la primera de la lista es la suya |

Comprobado de la forma que importa: las dos pruebas, **dos veces seguidas sobre el mismo
`.e2e-data`** con restos de una corrida interrumpida dentro. Verdes las dos veces.

**Obligación:** que el resultado de la puerta 18 signifique algo por sí solo, sin tener que mirar
cuánto tardó la suite ni qué procesos había abiertos.

**Criterio de cierre.**

1. La puerta distingue «ha tardado más» de «no funciona»: o el trabajo de fondo se completa de forma
   determinista dentro de la prueba, o la espera se declara con su motivo y su medida, y el informe
   dice cuál de las dos cosas ha pasado.
2. Una corrida con la máquina cargada no produce rojos por tiempo.
3. **Añadido el 23/09/2026:** una corrida sobre un directorio de datos ya usado, con restos de corridas
   anteriores interrumpidas, da el mismo resultado que una sobre el directorio recién hecho. Es lo que
   hace falta para que un rojo hable del código y no de la basura que quedó.

**Estado: abierta.** Con los puertos libres y la máquina descargada la puerta está verde (52/52 en
~3 min) **también sobre un directorio reutilizado**; de los tres criterios, el 3 ya está cumplido por
las pruebas que se arreglaron aquí, y quedan el 1 y el 2 (declarar la espera y no producir rojos por
tiempo con la máquina cargada).

---

## DEBT-023 — Una tarjeta de Anki no puede ser una pregunta porque no hay dónde guardar su respuesta

**Origen:** entrada de Anki en S12.3 (22 de septiembre de 2026).

**Problema.** Una tarjeta de Anki es un enunciado con su respuesta (el anverso y el reverso). El
modelo de preguntas tiene el tipo `free_text_reference` —una pregunta sin opciones, «de referencia»—
pero **no tiene ninguna columna ni campo para la respuesta de referencia**: se comprobó buscando el
sitio donde viviría y no existe. Importar una baraja como preguntas dejaría, por tanto, el reverso
fuera, que es justo lo que hace útil la tarjeta.

Por eso S12.3 las deja entrar como **material estudiable y citable** (una tarjeta por tramo, con su
cita), clasificado como tarjetas, y no inventa una pregunta a medias.

**Obligación antes de prometer que las barajas «se convierten en preguntas»:** decidir dónde vive la
respuesta de referencia, con su migración, su contrato y su interfaz. Las opciones, para decidir
cuando toque:

- un campo de respuesta de referencia en la versión de la pregunta (sirve para `free_text_reference`
  y para las preguntas abiertas de un supuesto práctico);
- o un tipo de estudio propio de tarjetas (anverso/reverso) que no pase por el banco de preguntas.

**Criterio de cierre.**

1. La decisión está escrita en un ADR, con lo que se descarta y por qué.
2. Una tarjeta importada de una baraja conserva su reverso y se puede estudiar con él a la vista.
3. Hay una prueba con una baraja sintética que comprueba el recorrido completo: tarjeta → estudio →
   respuesta cotejada o autoevaluada, sin inventar corrección automática donde no la hay.

**Estado: abierta.** Hoy la baraja entra entera como material y se puede buscar y citar; lo que no se
puede es responderla como pregunta.

---

## DEBT-024 — La clasificación se pide de forma síncrona y con el corpus entero tarda demasiado

**Origen:** verificación de S12.4 (22 de septiembre de 2026), al medir la puerta E2E.

**Problema.** `POST /api/v1/classification-runs` clasifica **todo** el corpus y no vuelve hasta
terminar. Con el material real del propietario (30 ficheros) la medición de DEBT-018 dio **46,7
segundos**; con un corpus más grande la petición sigue creciendo. La consecuencia se vio de dos
formas:

- la pantalla de Revisión bloquea el botón «Buscar propuestas ahora» hasta que termina, y con el
  corpus entero eso puede ser un minuto de espera sin progreso visible;
- las pruebas E2E que lo pulsan esperan un texto con un plazo fijo y, en una máquina cargada, se
  agotan antes de que la clasificación acabe (es parte de lo que hace ruidosa la puerta 18, DEBT-022).

Es el mismo problema que resolvió el recálculo de claves en S09/S11: una operación larga no puede
vivir dentro de una petición.

**Obligación antes de trabajar con corpus grandes:** que clasificar sea un **trabajo** con su
progreso, como extraer y recalcular, y que la pantalla diga en qué va.

**Criterio de cierre.**

1. La clasificación se encola y devuelve un identificador de trabajo; la pantalla muestra el avance y
   el resultado cuando termina.
2. Clasificar dos veces seguidas no duplica propuestas (ya se cumple: la prueba de idempotencia
   existente tiene que seguir verde con el camino nuevo).
3. Con el corpus del propietario, la petición responde en menos de un segundo y el trabajo informa de
   su progreso real.

**Estado: cerrada** (22 de septiembre de 2026, S12.6).

**Qué se hizo.** Clasificar dejó de ser una petición larga y pasó a ser un trabajo del pipeline, como
extraer y recalcular claves:

- `POST /api/v1/classification-runs` responde **202** con el trabajo encolado (`enqueue_run`, con la
  clave de idempotencia `classify_document:corpus`: dos pulsaciones seguidas no clasifican dos veces,
  la segunda devuelve el trabajo que ya estaba vivo);
- el trabajador lo ejecuta con el manejador `classify_document`, que ya existía para la vía automática;
- la pantalla de Revisión **sigue el trabajo** (`useJob`), enseña el paso que informa el servidor y su
  avance mientras corre, y recarga las propuestas cuando termina;
- la pasada informa de sus tramos —`clasificando material (N de M)`, `guardando propuestas`,
  `aplicando lo que se decide solo`, `buscando duplicados`— en lugar de saltar de 0,05 a 1, y cada
  informe es también el punto donde se comprueba si han pedido cancelar.

**Cómo se comprueba.**

| Criterio | Prueba o medición | Resultado |
|---|---|---|
| 1. Se encola y la pantalla muestra el avance y el resultado | `tests/integration/test_classification.py::test_la_pasada_de_clasificacion_informa_de_sus_tramos` y `apps/web/tests/unit/review.test.tsx` | 202 con `job_type=classify_document`; el avance no retrocede, lleva al menos tres tramos intermedios con su paso y termina con el resumen; la pantalla enseña paso y porcentaje |
| 1b. Cancelar corta la pasada | `…::test_cancelar_una_pasada_de_clasificacion_la_corta_a_mitad` | se corta entre tramos, en lugar de dejarla terminar entera |
| 2. Clasificar dos veces no duplica propuestas | la prueba de idempotencia de S04, sin cambios | verde |
| 3. La petición responde en menos de un segundo | medición sobre una copia del corpus del propietario (186 sujetos) | **0,097 s** de respuesta; el trabajo tarda 48,2 s |

La medición del criterio 3 se hizo el 22 de septiembre de 2026 con
`F:\temp-opofuente\medir_clasificacion_job.py`, sobre una **copia nueva** de `datos-apuntes-tai` (nunca
sobre la carpeta del propietario ni sobre la copia de DEBT-018). El trabajo terminó en `succeeded` con
el resumen «186 sujetos: 4 propuestas nuevas, 390 ya existentes, 2 sin señales, 0 aplicadas
provisionalmente, 0 grupos de duplicados». La referencia anterior —la misma pasada, de forma
síncrona— era de 46,7 s (DEBT-018): el trabajo tarda lo mismo, pero la petición ya no espera.

**Lo que sigue en pie.** Una pasada clasifica como mucho `limit` sujetos (200 por defecto). El corpus
medido tiene 186, así que entró entero, pero uno mayor necesitará varias pasadas o un límite más alto;
el resumen dice cuántos sujetos ha visto, no cuántos quedan por ver.

---

## DEBT-025 — Corregir una pregunta infla el conjunto y puede volver a preguntarse el texto viejo

**Origen:** verificación de S12.6 (22 de septiembre de 2026), buscando cómo contar las preguntas de un
conjunto para la pantalla de «listo para estudiar».

**Problema.** Corregir una pregunta deja la anterior en la base con estado `superseded` (a propósito:
hay que poder leer qué decía). Pero **ninguna** consulta del banco filtraba ese estado, así que la
versión sustituida seguía contando como pregunta del conjunto. Medido sobre la API real, con un
conjunto de 3 preguntas y **una** corrección:

| Consulta | Antes de corregir | Después de corregir |
|---|---|---|
| `GET /question-sets/{id}` → `question_count` | 3 | **4** |
| `GET /questions?set_id=…` | 3 | **4** (con la sustituida dentro, estado `superseded`) |
| `POST /study-sessions` con `count` = 10 | — | 409: «el conjunto tiene **4** preguntas y se han pedido 10» |

De dónde sale el daño, más allá del recuento:

- `all_questions` es la lista de la que una sesión elige su composición: una sesión nueva podía
  preguntar **el enunciado viejo** de una pregunta ya corregida, y contarla dos veces (el examen
  oficial de 70 preguntas pasa a 71 con una corrección, 72 con dos).
- `questions_by_position` alinea una plantilla suelta por posición: con la sustituida dentro, dos
  filas comparten posición y la plantilla se alinea con la que devuelva el orden de la consulta.
- `questions_without_topic` (catalogación de S12.6) y `node_titles_of_set` (diagnóstico) veían la
  versión vieja como una pregunta más sin tema.

**Qué se hizo** (22 de septiembre de 2026, S12.6). Se aplicó una sola regla, escrita una vez en el
repositorio (`_NO_SUSTITUIDAS`): **una versión sustituida no es una pregunta del conjunto**. Se aplica
al listado del banco, a la composición de sesiones, a los recuentos del conjunto, a la alineación por
posición, a la catalogación por tema y a la estratificación del diagnóstico. Solo queda fuera
`superseded`: una pregunta `annulled` sigue siendo parte del examen, y quien lo dice es su clave.

Dos excepciones deliberadas, con su motivo escrito en el código:

- **`_identidades` y `_stable_keys` sí ven las sustituidas**: son la comprobación de «esa pregunta ya
  estaba» al importar. Si no las vieran, volver a importar el texto original crearía una pregunta
  nueva con el enunciado equivocado que alguien ya había corregido, y la clave estable de la corregida
  cambiaría.
- **`GET /questions?status=superseded` sigue funcionando**: la historia no se esconde, se pide. Sin
  estado en la consulta se listan las preguntas; con él, lo que se pida.

**Cómo se comprueba.**
`tests/integration/test_question_api.py::test_una_pregunta_corregida_no_cuenta_dos_veces` recorre el
caso entero: el conjunto sigue con 2 preguntas, el banco no enseña la sustituida, la sustituida se lee
por su identificador y se lista por estado, la sesión de 3 se rechaza diciendo que hay 2 y la de 2 se
crea con 2.

**Lo que sigue en pie.** El recuento cuenta **versiones vivas**, no preguntas distintas por
`stable_key`: si dos importaciones crearan dos versiones vivas de la misma pregunta por un camino que
no pase por la huella, contarían dos. No se ha visto que ocurra —la importación es idempotente por
contenido—, pero el recuento no lo impide.

---

## DEBT-026 — La suite E2E toma su directorio de datos del entorno y escribe donde le digan

**Origen:** verificación de S12.6 (22 de septiembre de 2026), al mirar una captura de la pantalla de
Inicio con material: la captura enseñaba **348 propuestas pendientes, 150 avisos de importación y 11
cambios propuestos** después de importar dos ficheros sintéticos.

**Problema.** `apps/web/playwright.config.ts` resolvía su directorio de datos así:

```ts
const e2eDataDir = process.env.OPOFUENTE_DATA_DIR ?? path.join(repoRoot, '.e2e-data');
```

`OPOFUENTE_DATA_DIR` es la variable con la que se apunta **la aplicación** a sus datos: la que el
propietario tiene puesta en su máquina, a veces señalando una copia de su corpus real. Una suite que
la hereda no prueba una base de datos de pruebas: prueba **la suya**, y le escribe dentro. Las puertas
no lo veían porque `scripts/gates.ps1` borra esa variable antes de la puerta 18 (`Remove-Item
Env:OPOFUENTE_DATA_DIR`), así que el camino automático estaba a salvo; el camino manual —el que se usa
para depurar y para mirar la interfaz— no.

Medido el 22 de septiembre de 2026, con esa variable puesta apuntando a una copia del corpus del
propietario:

| Corrida | Directorio de datos usado | Efecto |
|---|---|---|
| `npx playwright test` a mano | la copia del corpus del propietario | dos ficheros sintéticos, su clasificación y sus sesiones **dentro de su material**; la base de la copia se reescribió a las 23:27-23:34 |
| puerta 18 de `gates.ps1` | `.e2e-data` (la variable se borra antes) | ninguna: la puerta estaba bien |

La carpeta real del propietario (`C:\Users\David\OneDrive\Escritorio\Apuntes TAI`) **no** se tocó: la
aplicación nunca escribe en el material de origen, solo copia de él. Lo que se contaminó fue la copia
de medición de DEBT-018/DEBT-024, que ya estaba contaminada de corridas anteriores por el mismo motivo.

**Qué se hizo** (22 de septiembre de 2026, S12.6). La suite deja de mirar la variable de la aplicación:

- su directorio es siempre `.e2e-data`, dentro del repositorio;
- para apuntarla a otro sitio hay una variable **propia** y explícita, `OPOFUENTE_E2E_DATA_DIR`, que
  nadie tiene puesta sin querer;
- el porqué queda escrito en la config y en `docs/OPERACION.md` §5, que es donde se busca cuando algo
  va mal.

**Cómo se comprueba.** Con `OPOFUENTE_DATA_DIR` puesta apuntando a la copia del corpus, una corrida
completa de las 45 pruebas E2E crea y usa `.e2e-data` y **no toca** la copia: su `opofuente.sqlite3`
conserva la fecha de modificación anterior (23:30:20, frente a los ficheros de `.e2e-data` de las
23:33-23:34).

**Lo que sigue en pie.** El mismo patrón podría repetirse en cualquier otro sitio que resuelva datos
desde el entorno (`scripts/dev.ps1`, `scripts/*.ps1`): se revisó que las puertas y los scripts del
repositorio fijan su propio directorio, pero no hay una comprobación automática de que **ningún**
proceso de prueba herede `OPOFUENTE_DATA_DIR`. La prueba de las 49 E2E es hoy la única red.

---

## DEBT-027 — 07_UI-UX no está aplicada entera

**Estado: cerrada** (23 de septiembre de 2026).

**Origen:** pregunta del propietario del 22 de septiembre de 2026 —«¿está aplicado lo de UI/UX,
experiencia sencilla de usuario completamente?»— al terminar S12.6.

**Problema.** La respuesta honesta era que **no**: la especificación de interfaz tiene catorce
secciones y cinco de ellas pedían cosas que no existían o no se parecían a lo pedido. Lo que más
cantaba estaba en la primera pantalla, que es donde el propietario mira todos los días.

**Auditoría sección a sección** (22 de septiembre de 2026). Lo que se encontró y lo que se hizo:

| Sección | Estado antes | Qué se hizo |
|---|---|---|
| §1 Principios | cumplidos (nada depende solo del color; lo automático se explica; las operaciones largas son trabajos) | — |
| §2 Estructura | **faltaban los contadores** `[pendientes] [conflictos] [vencidos] [revisar]` | contadores reales, con la cifra del servidor y nombre accesible que la explica |
| §3 Inicio | **faltaban** dominio y actividad reciente; «Acciones necesarias» era un texto fijo | dominio, actividad reciente y acciones reales |
| §4 Bandeja | el estado se leía como valor crudo del enum; **sin pausar**; sin tabla virtualizada | estados en palabras y etiquetas compartidas; el resto sigue pendiente |
| §5 Programa | falta preguntas por estado y próxima revisión por nodo | el dominio ya estaba; **las otras dos columnas, cerradas el 23 de septiembre de 2026** (abajo, con el defecto que apareció al ir a servirlas) |
| §6 Biblioteca | **lector sincronizado página ↔ texto: ya estaba** | nada: la auditoría se corrigió al leer el código (ver abajo) |
| §7 Preguntas | badges de origen, conflictos arriba y original al lado están; **falta** explicación por opción | **cerrado en S12.7**: el modelo ya la soportaba; faltaba el camino (importación, API y ficha) |
| §8–§11 | cumplidas por S07–S12 (configuración, pregunta, corrección, resultado, errores, cambios, ajustes) | — |
| §12 Estados y mensajes | cumplida en general | — |
| §13 Accesibilidad | faltaba el flujo con teclado (no estaba probado en ninguna pantalla) | probado en la pregunta y su corrección |
| §14 Aceptación visual | Programa no tenía tres anchos; Pregunta y Corrección no tenían nada | Programa a 1440/1024/390 y pregunta/corrección con accesibilidad y teclado; **el caso de 1.000 filas, medido y cerrado** |

**Segunda pasada: el caso de las 1.000 filas y la cola que se cortaba en 200** (22 de septiembre de
2026, misma sesión). Medir el caso grande destapó un defecto de verdad, no un problema de rendimiento:

| Medición | Resultado |
|---|---|
| Importar 1.000 preguntas por el importador real | 1,1 s |
| `GET /questions?limit=100` (primera y última página) | 42–56 ms |
| `GET /questions?limit=200` | 122 ms |
| `GET /classification-proposals?limit=200` (120 propuestas) | 12 ms |
| Banco, hasta la primera fila en pantalla (1440×900) | 515 ms · 100 filas en el DOM · 1.841 nodos |
| Revisión, hasta las propuestas (1440×900) | 899 ms · 127 filas en el DOM · 5.656 nodos |
| Scroll horizontal a 1440/1024/390 | ninguno (los tres anchos) |

Lo que salió de ahí:

- **La cola de revisión estaba cortada en 200 y lo decía mal.** `fetchProposals` pedía las primeras
  200 propuestas y la tabla titulaba con `proposals.length`: con el corpus del propietario (348
  pendientes) la pantalla decía «200 propuestas esperando tu decisión» —una cifra falsa— y **148
  propuestas eran inalcanzables** desde la interfaz. Arreglado: la lista se **pagina** (como el banco
  desde DEBT-011), el título usa el `total` del servidor y hay «Página anterior / Página siguiente»
  con «Mostrando X–Y de N». Las aplicadas provisionalmente pasan a su propia tabla, porque no son lo
  mismo que una propuesta que espera decisión y su total es otro.
- **No hace falta virtualizar**: el DOM nunca tiene mil filas porque el servidor pagina (100 por
  página en el banco, 200 en la revisión), y con 120 propuestas la tabla tarda 899 ms en estar lista
  con 5.656 nodos. Virtualizar habría sido optimizar un problema que no existe; lo que existía era un
  tope sin paginador.
- **Dos pruebas nuevas lo defienden**: la de integración recorre las diez páginas de 1.000 preguntas y
  comprueba que suman mil sin repetir ninguna, y la E2E recorre el banco de la primera a la última
  página en la interfaz.

**Qué falta todavía** (esto es lo que deja abierta la deuda):

**Tercera pasada: la auditoría tenía dos errores, y uno de ellos era una promesa de menos** (23 de
septiembre de 2026). Al ir a cerrar los puntos que quedaban, leyendo el código antes de escribirlo:

- **§6 «lector sincronizado página ↔ texto» ya estaba hecho** y la auditoría lo dio por ausente: el
  lector enseña cada sección con su página y ofrece **abrir esa página del original** (`#page=N`) y el
  fichero original copiado. Lo que no existe —y no puede existir— es el camino inverso (pinchar en el
  PDF y que se resalte el texto), porque el original se abre en otra pestaña del navegador.
- **§7 «explicación por opción» no era un problema de modelo**: `question_explanations` tiene
  `option_stable_key` con índice único por `(pregunta, opción)` desde S06. Faltaba el **camino**: que
  entrara al importar, que se pudiera leer y escribir por la API y que la ficha la enseñara. Eso es
  ahora **S12.7**, entregado.

Lo que queda abierto, ya solo una cosa:

1. **Pausar un lote** (§4): el trabajo se puede cancelar, no pausar. Pausar de verdad exige decidir qué
   pasa con las entradas a medias y con su trabajo ya encolado; no se inventa un botón que solo cambie
   una etiqueta. *(Cerrado el 23 de septiembre de 2026: ver la quinta pasada, abajo.)*

**Cuarta pasada: las dos columnas del Programa, y el defecto que apareció al ir a servirlas** (23 de
septiembre de 2026). `07_UI-UX` §5 pide cuatro columnas por nodo: fuentes, preguntas
(oficiales/verificadas/dudosas), dominio y próxima revisión. Faltaban las dos del medio:

- **`GET /reviews/mastery` sirve ahora el estado de estudio de cada nodo**: cuántas preguntas tiene
  —por **estado** y por **origen**, que son los dos ejes que pide la especificación—, cuántos repasos
  tiene vencidos y cuándo toca el siguiente programado. La ruta conserva su nombre (está registrada en
  ADR-013): el dominio sigue siendo el núcleo y las otras dos cifras viajan con él, porque las tres se
  leen de la misma pantalla con la misma clave. Se cuenta con la **misma regla que el banco**: versiones
  vigentes con mapeo aceptado; si contara otra cosa, dos pantallas darían dos cifras distintas de lo
  mismo.
- **El árbol del Programa** enseña en cada fila `preguntas: N`, las dudosas siempre visibles
  (`en conflicto`, `anulada`) —que son las que piden algo— y `repaso: fecha` / `repaso vencido: N` /
  `sin repaso programado`. La ficha del nodo seleccionado desglosa el total por origen y por estado.
- **El defecto que apareció al ir a servirlas**: `/reviews/mastery` estaba declarada **detrás** de
  `/reviews/{review_id}`, así que FastAPI la atendía con `review_id="mastery"` y contestaba el 404 de
  «no existe repaso con ese identificador». **La columna de dominio del Programa no se había servido
  nunca**, y nada lo delataba: las pruebas de componentes simulan `fetch`, las de la API probaban el
  servicio y no la ruta, y un 404 en una consulta opcional no rompe ninguna pantalla. Lo cazó una prueba
  escrita para esta deuda que pedía la ruta por HTTP. Corregido el orden, y con él una regla nueva
  (**ADR-018**) y una prueba de contrato que recorre el orden real de las rutas y sabe fallar (se
  comprueba con el caso que la motivó).

Lo que queda de §5, si alguna vez se pide: **la columna de fuentes** (aceptadas/candidatas/obsoletas)
por nodo ya existe, pero se enseña en la ficha del nodo y no en la fila del árbol; subirla al árbol
exigiría otra consulta agregada por nodo, y no es lo que la deuda pedía.

Verificación de esta pasada: **18/18 puertas** (497 unitarias, 447 integración, 26 contrato, 210
Vitest, **53 E2E**), y la 18 corrida **sobre un `.e2e-data` reutilizado y sucio**, no sobre uno recién
hecho: era la forma de comprobar de paso el criterio 3 de DEBT-022. Dos cosas aparecieron en el
camino y se corrigieron: un `flex-wrap` que faltaba en las etiquetas del árbol (con las columnas
nuevas, la fila desbordaba a 390 px y rompía la puerta de responsive) y las dos pruebas E2E que
dependían de que el directorio estuviera limpio.

**Quinta pasada: pausar un lote, que era lo último que quedaba** (23 de septiembre de 2026). `07_UI-UX`
§4 pide «pausar/cancelar» y solo existía cancelar. Pausar no es cancelar, y esa diferencia es la que
decide el diseño entero:

- **El lote deja de avanzar donde está.** Estado nuevo `paused` en el lote y **en su trabajo**: un
  trabajo `paused` no lo reclama el worker (`claim_next` solo mira `queued` y `cancel_requested`), así
  que no hay ni un hilo de sondeo ni una espera artificial.
- **Lo que está en curso termina.** El manejador comprueba la pausa **entre entradas** y lanza
  `JobPausedError`, que el worker traduce a `paused`: no se mata nada a mitad de una copia, así que no
  quedan artefactos a medio registrar. Lo copiado sigue copiado y el informe se recalcula del estado
  real para que diga la verdad mientras está detenido.
- **Reanudar retoma donde se quedó.** El trabajo detenido vuelve a la cola y el manejador empieza por
  la primera entrada que no esté hecha (`pending_entries`), sin resetear ninguna entrada —eso es lo que
  hace el reintento, que es otra cosa—. Si no queda trabajo detenido, se encola el de la fase en la que
  se quedó el lote y, si no queda nada, se cierra como terminado en vez de dejarlo en pausa para
  siempre.
- **La consecuencia que no se ve, y por eso se prueba**: el índice único parcial de idempotencia
  enumeraba los estados «vivos». Con `paused` fuera de esa lista, pausar un lote habría **liberado su
  clave** y un segundo `ingest_batch` del mismo lote podría haberse encolado mientras el primero está
  en pausa: dos trabajos avanzando el mismo lote. La migración `0023` lo recrea con el predicado nuevo
  y hay una prueba que lo comprueba (dos trabajos con la misma clave, el segundo rechazado).
- **Una carrera que el diseño cierra**: el worker reclama el trabajo y, entre la reclamación y la
  primera línea del manejador, alguien pausa el lote. Si el manejador escribiera `running` sin mirar,
  desharía la pausa recién pedida. Ahora la transición a `running` es condicional
  (`start_running` devuelve `False` si el lote está en pausa) y en ese caso el trabajo queda `paused`.
- **Y el mensaje dice lo que se pidió**: `InvalidBatchStateError` acepta el verbo de la acción, así que
  un 409 al pausar dice «solo se puede pausar si está queued o running», no «reintentar».

Verificación: pruebas de migración (estados, idempotencia, índices y claves foráneas), de integración
(pausa antes de arrancar, reanudación que termina la copia, 409 en los estados que no valen, la rama
sin nada pendiente), de la API (pausar/reanudar por HTTP con el worker parado), de componentes (el
botón y la etiqueta «en pausa», en palabras y no como valor crudo) y E2E (el contrato de estado de las
dos rutas contra el servidor real). La pausa **con el lote a medias** se prueba en la integración, con
el worker parado: en la E2E el worker es real y un lote de tres ficheros termina antes de que nadie lo
pause, así que esperar a mitad sería una carrera, no una prueba —y está dicho en el propio guion—.

**Lo que se decidió NO hacer, y por qué** (para que no vuelva a aparecer como pendiente sin contexto):
- **Virtualizar la tabla de revisión**: medido, no hace falta (arriba). Si algún día el servidor deja
  de paginar, el problema volverá y la medición es la referencia.
- **Panel lateral con fragmentos justificativos** (§4): la evidencia va **en la propia fila** desde S04
  —una propuesta que no se puede comprobar no se puede revisar— y además se abre la ficha con su cita.
  Un panel lateral duplicaría lo que ya está delante y escondería la evidencia en un clic más.

**Estado: cerrada.** El 23 de septiembre de 2026 se cerraron las tres cosas que quedaban de la
especificación de interfaz: el caso de 1.000 filas (medido), las cuatro columnas del Programa y
pausar/cancelar el lote. Lo que sigue abierto no es de esta deuda sino de las que se citan en cada
pasada (DEBT-022 para la suite E2E con la máquina cargada, DEBT-028 para el estado del proceso
selectivo).

## DEBT-028 — La aplicación no sabe si un proceso selectivo está abierto o cerrado

**Origen:** S12.2 (segunda convocatoria de Celador), 23 de septiembre de 2026, al tener que decir qué
se podía afirmar de la convocatoria del proceso de estabilización.

**Problema.** De una convocatoria la aplicación guarda su acto, su fecha de publicación, su fecha de
ejercicio (con la nota que explica de dónde sale, desde la migración
`0022_convocation_exam_date_note`) y su estado interno
(`draft`/`active`/`available`/`superseded`/`archived`, que habla de si la aplicación trabaja con ella,
no del proceso administrativo). **No guarda si el plazo de solicitudes está abierto, ni si el proceso
sigue vivo.** Eso vive hoy en la prosa de la nota del fixture:

- la convocatoria de estabilización se publicó el 28 de diciembre de 2022 y su plazo de solicitudes
  (20 días hábiles, base 5.1.1) cerró en enero de 2023;
- su ejercicio no tiene fecha publicada: la fijará la resolución de admitidos (base 8.3), y en las
  fuentes conservadas no hay ninguna que lo fije.

Un lector de la interfaz ve «sin fecha de ejercicio» en el selector y, al elegirla, la nota que dice
por qué (el plazo cerró y la fijará la resolución de admitidos). Lo que no ve es un aviso en el propio
selector: «este proceso ya no admite solicitudes» o «este proceso sigue pendiente», que es lo que de
verdad decide si tiene sentido estudiar para él. La pantalla no puede inventarlo: no hay dato.

**Qué haría falta.** Una fuente que publique el estado del proceso de forma estructurada (el portal de
procesos selectivos de Salud de Castilla y León lo publica en HTML, sin condiciones de reutilización
declaradas, como el resto), una tabla de hitos por convocatoria (publicación, plazo, listas
provisionales, listas definitivas, ejercicio, resultado) y una regla de lectura: qué se puede afirmar
cuando solo se conoce el hito anterior. No es un campo `open: true/false`: los procesos tienen varios
estados intermedios y una fecha sola no los distingue.

**Por qué no se hizo en S12.2.** Porque el alcance era la convocatoria, y meter aquí un modelo de
hitos —con su fuente, su manifiesto y su extracción— habría dejado el slice a medias. La nota del
fixture es la información disponible hoy, y está escrita para que nadie tenga que deducirla.

**Estado: abierta.** No bloquea estudiar: la aplicación declara lo que no consta en lugar de
presentar un examen pendiente como si estuviera convocado.
