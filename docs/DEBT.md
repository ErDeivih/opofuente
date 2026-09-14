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
3. Prueba de contrato: el esquema del 500/`SettingsSchema` incluye los nuevos campos y no queda
   ningún booleano llamado `sends_data_off_device`.
4. La pantalla de Ajustes muestra, por proveedor, si los datos salen del equipo (07_UI-UX §11).

---

## DEBT-002 — Documentar 403 y 404 en el contrato

**Origen:** corrección del 503 de `/health/ready` (commit corrector de S00).

**Problema.** El esquema OpenAPI documenta el 500 (`ProblemDetail`) y el 503 de readiness
(`ReadinessProblem`), pero el 403 `forbidden_origin` que produce el middleware de Origin y el 404/405
que produce el manejador global se sirven como `ProblemDetail` sin aparecer en el contrato.

**Por qué no ahora.** En S00 no existe ningún endpoint de escritura, así que el 403 no puede
ocurrir en una ruta concreta y documentarlo en rutas `GET` sería inexacto (la comprobación de Origin
solo actúa sobre métodos no seguros).

**Criterio de cierre.** Cuando exista la primera ruta de escritura (S02), documentar `403` con
`ProblemDetail` en las rutas donde el middleware puede rechazarlas, y añadir una prueba de contrato
que compruebe que el media type documentado es `application/problem+json` y que el `$ref` apunta a
`ProblemDetail`.
