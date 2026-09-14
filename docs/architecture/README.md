# Arquitectura — notas de implementación

La arquitectura **vigente** es
[`docs/product-spec/02_ARCHITECTURE.md`](../product-spec/02_ARCHITECTURE.md). Este directorio
contiene solo notas de cómo se ha materializado, sin contradecirla.

## Forma del sistema

```text
Navegador (127.0.0.1:5173 dev / 4173 preview)
   |
   v
React SPA  --HTTP/JSON-->  FastAPI (127.0.0.1:8765)
                              |-- SQLite + FTS5
                              |-- almacén de artefactos por SHA-256   (S02)
                              |-- Qdrant local                        (S09)
                              |-- worker persistido                   (S02)
                              |-- adaptadores OCR / LLM / embeddings   (S03/S09)
```

## Capas del backend

| Capa | Ruta | Puede importar |
|---|---|---|
| Domain | `apps/api/opofuente/domain/` | solo biblioteca estándar |
| Application | `apps/api/opofuente/application/` | dominio y puertos propios |
| Infrastructure | `apps/api/opofuente/infrastructure/` | application, domain, SQLAlchemy, Alembic |
| API | `apps/api/opofuente/api/` | application, domain, FastAPI |
| Arranque | `apps/api/opofuente/main.py` | todo lo anterior (composición explícita) |
| Worker | `apps/api/opofuente/workers/` | application, domain, infrastructure (S02) |

El dominio no conoce FastAPI, SQLAlchemy, Qdrant ni el sistema de archivos.

## Decisiones de S00 que condicionan lo siguiente

1. **Estado en `app.state`, no en singletons.** `create_app(settings)` permite levantar una
   aplicación completa contra un directorio temporal; es lo que usan las pruebas y el E2E. En S01
   las dependencias de sesión deben seguir este patrón (`request.app.state.session_factory`).
2. **OpenAPI es la fuente de verdad.** `packages/contracts/openapi.json` se genera desde FastAPI y
   `packages/contracts/src/openapi.d.ts` se deriva de él. Un cambio de contrato que no se regenere
   rompe la puerta de contrato y el typecheck del frontend.
3. **Cadena de middlewares ASGI puros**, de dentro hacia fuera: CORS → cabeceras de seguridad →
   comprobación de Origin → identificador de correlación. Se evita `BaseHTTPMiddleware` para no
   romper SSE cuando llegue S09.
4. **Capacidades honestas.** `CapabilityStatus` distingue `enabled` (comprobado), `disabled`,
   `unavailable`, `configured_unverified` y `planned`. La UI no puede mostrar como operativo lo que
   no lo está.
5. **Logs con lista blanca de campos.** El formateador descarta cualquier `extra` no declarado en
   `SAFE_EXTRA_KEYS`, de modo que un descuido al registrar no filtra contenido.
