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
| [DEBT-002](#debt-002--documentar-403-y-404-en-el-contrato) | S02 | Documentar en OpenAPI los errores 403/404 que ya se sirven como `ProblemDetail` | abierta |

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

**Problema.** El esquema OpenAPI documenta el 500 (`ProblemDetail`), el 503 de readiness
(`ReadinessProblem`) y los esquemas de las respuestas correctas, pero hay errores que se sirven como
`ProblemDetail` sin aparecer en el contrato, o con un esquema documentado que **no** es el que se
devuelve:

| Respuesta | Quién la produce | Cuerpo real | Documentado hoy |
|---|---|---|---|
| `403` | middleware de comprobación de `Origin` (métodos no seguros) | `ProblemDetail` (`code: forbidden_origin`) | no aparece |
| `404` / `405` | manejador global de `StarletteHTTPException` | `ProblemDetail` | no aparece |
| `422` | manejador global de `RequestValidationError` | `ProblemDetail` con `field_errors` | lo genera FastAPI como `HTTPValidationError` (`detail: [...]`), que **no** es nuestra forma |

El caso del 422 es el más engañoso de los tres: en cuanto S02 añada la primera ruta con cuerpo,
FastAPI documentará automáticamente un `HTTPValidationError` y `apply_problem_media_type` lo moverá a
`application/problem+json`. El media type quedaría bien y el esquema, mal: un consumidor que genere
tipos desde el contrato obtendría un tipo que el servidor nunca devuelve.

**Por qué no ahora.** En S00 no existe ninguna ruta de escritura ni ninguna ruta con cuerpo, así que
el 403 no puede ocurrir en una ruta concreta, y no hay ninguna 422 documentada que corregir.
Documentarlos ahora en rutas `GET` sería inexacto.

**Criterio de cierre.** Cuando exista la primera ruta de escritura (S02):

1. Documentar `403` con `ProblemDetail` solo en las rutas donde el middleware puede rechazarlas, y
   `404`/`405` donde correspondan; no añadir respuestas que no puedan ocurrir.
2. **El 422 documentado debe coincidir con el cuerpo real**: `ProblemDetail` con `field_errors`
   (o un esquema derivado que lo declare), no `HTTPValidationError`. Si FastAPI sigue generándolo
   automáticamente, hay que sustituirlo en el esquema —con el mismo mecanismo determinista que
   `apply_problem_media_type`, sin escribir nombres de componente a mano— o desactivar su generación
   automática cuando no proceda.
3. Prueba de contrato que compruebe, para cada error documentado: media type
   `application/problem+json`, `$ref` al componente esperado, y que los campos del esquema son los
   mismos que devuelve el cuerpo servido en una petición real (como ya se hace con el 503 de
   readiness). Incluir un caso de validación fallida que compare `field_errors`.
4. Nada de esto se cierra declarando «el 422 lo genera FastAPI»: si el esquema documentado no es el
   que se sirve, la deuda sigue abierta.
