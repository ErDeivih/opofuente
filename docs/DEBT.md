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
| [DEBT-001](#debt-001--clasificación-del-destino-de-datos-por-proveedor) | S09 | Sustituir `Settings.sends_data_off_device` por clasificación por proveedor | abierta |
| [DEBT-002](#debt-002--documentar-403-404-y-422-en-el-contrato) | S02 | Cerrar el caso real de validación fallida (422) con `field_errors` | parcialmente cerrada en S01 |
| [DEBT-003](#debt-003--uso-privado-del-temario-de-la-guardia-civil) | antes de publicar | No publicar el repositorio ni distribuir la aplicación con el temario de GC | abierta (condición previa) |
| [DEBT-004](#debt-004--parseo-seguro-de-xmlhtml-no-confiable) | S03 | Los extractores deben defenderse de XML/HTML no confiable | abierta |
| [DEBT-005](#debt-005--borrado-de-nodos-con-referencias-al-sincronizar-fixtures) | S05 | La siembra no puede borrar nodos con referencias | abierta |
| [DEBT-006](#debt-006--representación-exacta-de-fracciones-y-redondeo-en-la-puntuación) | S07 | Decidir y probar la aritmética exacta antes de calcular puntuaciones | abierta |

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

**Cambio exigido antes de S09.** Sustituir el booleano por un estado independiente por proveedor:

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
URLs sin nada que clasificar, y S09 es donde llegan los adaptadores y la prueba real de conexión.

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
**Estado:** parcialmente cerrada en S01 (403, 404 y el esquema del 422); queda abierto el caso real
de validación fallida.

**Problema.** El esquema OpenAPI documenta el 500 (`ProblemDetail`), el 503 de readiness
(`ReadinessProblem`) y los esquemas de las respuestas correctas, pero había errores que se servían
como `ProblemDetail` sin aparecer en el contrato, o con un esquema documentado que **no** era el que
se devuelve:

| Respuesta | Quién la produce | Cuerpo real | Estado |
|---|---|---|---|
| `403` | middleware de comprobación de `Origin` (métodos no seguros) | `ProblemDetail` (`code: forbidden_origin`) | **documentado en S01** en la primera ruta de escritura (`POST /oppositions/{id}/activate`), y no en rutas de lectura, donde no puede ocurrir |
| `404` | manejador global de `OpoFuenteError` / `StarletteHTTPException` | `ProblemDetail` | **documentado en S01** en todas las rutas que buscan un recurso por identificador |
| `422` | manejador global de `RequestValidationError` | `ProblemDetail` con `field_errors` | **esquema corregido en S01**: al declararlo en cada ruta, FastAPI ya no publica `HTTPValidationError` y el contrato apunta a `ProblemDetail` bajo `application/problem+json` |
| `405` | enrutador de Starlette | `ProblemDetail` | se sirve así, pero **no se documenta por ruta**: es un error de protocolo que no aporta información y añadirlo a cada operación sería ruido |

**Por qué no se cerró del todo.** El criterio 3 pedía «incluir un caso de validación fallida que
compare `field_errors`». En S01 ninguna ruta tiene parámetros tipados ni cuerpo, así que no existe
una petición que produzca un 422 real: probarlo exigiría inventar una ruta de prueba. Se cierra
cuando S02 añada la primera ruta con cuerpo o parámetros validados.

**Lo que falta.** Una prueba de contrato que provoque un 422 de verdad y compare `field_errors` del
cuerpo servido con el esquema documentado.

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

## DEBT-006 — Representación exacta de fracciones y redondeo en la puntuación

**Origen:** revisión de S01 (14/09/2026).

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

## DEBT-004 — Parseo seguro de XML/HTML no confiable

**Origen:** `# noqa: S314` justificado en la herramienta de fixtures de S01.

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
