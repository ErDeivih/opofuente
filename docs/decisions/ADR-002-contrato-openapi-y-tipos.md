# ADR-002 — Generación del contrato OpenAPI y de los tipos TypeScript

- **Estado:** aceptada (S00)
- **Fecha:** 2026-09-14
- **Ámbito:** contrato API ↔ frontend

## Contexto

`02_ARCHITECTURE.md` §2 exige que `packages/contracts` contenga «OpenAPI generado y tipos
TypeScript derivados; la fuente de verdad del contrato es FastAPI/OpenAPI». `08_API-CONTRACT.md`
§13 añade que «CI genera tipos TypeScript y falla si hay diff sin registrar». Faltaba decidir con
qué herramienta se generan los tipos y cómo se detecta la desincronización.

## Opciones

| Opción | A favor | En contra |
|---|---|---|
| Escribir los tipos a mano | sin dependencias | se desincroniza en silencio; el typecheck no protege nada |
| `openapi-typescript` (dev dependency de `packages/contracts`) | deriva tipos directamente del JSON de FastAPI, sin runtime, ampliamente usado, MIT | una dependencia de desarrollo más |
| `openapi-generator` / clientes generados completos | cliente listo | genera mucho código de runtime que no se necesita; más superficie que auditar |
| Solo comprobar el JSON con un test | barato | no protege al frontend: nada impide usar campos inexistentes |

## Decisión

1. `uv run python -m opofuente.tools.export_openapi` escribe `packages/contracts/openapi.json`
   (claves ordenadas → diff determinista).
2. `npm run contracts:generate` deriva `packages/contracts/src/openapi.d.ts` con
   `openapi-typescript`, sin runtime.
3. Dos puertas impiden la deriva:
   - `pytest` compara el esquema en memoria con `openapi.json` y falla si difieren;
   - `npm run contracts:check` regenera los tipos en memoria y falla si el fichero commiteado
     difiere.
4. `apps/web` declara `@opofuente/contracts` como dependencia de desarrollo e importa los tipos
   generados, de modo que un cambio de contrato rompe el `tsc`.

## Consecuencias

- Cambiar la API obliga a regenerar contrato y tipos en el mismo commit; el mensaje de error de las
  puertas indica el comando exacto.
- `openapi.json` y `openapi.d.ts` se versionan: son el contrato revisable en un diff.
- Riesgo: `openapi-typescript` es una dependencia de desarrollo de terceros (MIT, mantenida). No
  entra en el bundle: solo produce un `.d.ts`.

## Reversión

Eliminar la dependencia y el paso de generación; `openapi.json` seguiría existiendo y la puerta de
pytest del backend seguiría vigente. El frontend tendría que declarar sus tipos a mano.
