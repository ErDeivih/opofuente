# ADR-004 — Versión de TypeScript fijada a 5.9.x

- **Estado:** aceptada (S00)
- **Fecha:** 2026-09-14
- **Ámbito:** tooling del frontend
- **Revisar cuando:** `openapi-typescript` y `typescript-eslint` declaren soporte del compilador nativo

## Contexto

Al instalar las dependencias con `npm install` sin fijar versión, npm resolvió
`typescript@7.0.2` (etiqueta `latest`, compilador nativo). La instalación quedó marcada como
inválida (`npm ls typescript` → `invalid`) y la generación de tipos falló en ejecución:

```text
TypeError: Cannot read properties of undefined (reading 'createKeywordTypeNode')
    at node_modules/openapi-typescript/dist/lib/ts.mjs:11
```

## Datos

- `openapi-typescript@7.13.0` declara `peerDependencies: { "typescript": "^5.x" }` y usa la API
  `ts.factory` del compilador, que el compilador nativo 7 no expone igual.
- `typescript-eslint@8.70.0` (y sus paquetes `@typescript-eslint/*`) declaran
  `typescript: ">=4.8.4 <6.1.0"`.
- `typescript@5.9.3` es la última estable de la serie 5.x.

## Opciones

| Opción | Resultado |
|---|---|
| Quedarse en TypeScript 7 | `npm ls` en estado inválido y la puerta de contrato no puede generar tipos: falla real, no advertencia |
| Sustituir `openapi-typescript` por otra herramienta | añade una dependencia nueva sin resolver el desajuste con `typescript-eslint` |
| Fijar `typescript@^5.9.3` | todo el ecosistema queda en rango soportado; se pierde el compilador nativo por ahora |

## Decisión

Fijar `typescript` a `^5.9.3` como dependencia de desarrollo **en la raíz** del monorepo (además de
en los espacios de trabajo) para que `openapi-typescript`, instalado en `node_modules` raíz, pueda
resolver el módulo `typescript`. La versión queda registrada en `package-lock.json`.

No se ha silenciado nada: `npm ls typescript` queda limpio y la generación de tipos funciona.

## Consecuencias

- Se pierde temporalmente la velocidad del compilador nativo; se gana que las puertas de tipos y de
  contrato funcionan de verdad.
- Volver a TypeScript 6/7 exige comprobar que `openapi-typescript` y `typescript-eslint` lo
  soportan y volver a ejecutar `npm run contracts:check` y `npm run typecheck:web`.

## Reversión

Cambiar la versión en `package.json`, `npm install` y ejecutar las puertas 4, 5 y 10 de
`scripts/gates.ps1`.
