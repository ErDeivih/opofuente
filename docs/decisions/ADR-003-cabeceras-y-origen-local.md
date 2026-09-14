# ADR-003 — Endurecimiento HTTP del backend local en el MVP

- **Estado:** propuesta para revisión del propietario (no bloquea S00)
- **Fecha:** 2026-09-14
- **Ámbito:** seguridad del transporte local

## Contexto

`09_SECURITY-PRIVACY-AND-RIGHTS.md` §2 exige escuchar solo en `127.0.0.1`, CORS y allowlist de
Origin local, CSP estricta y no servir directorios estáticos desde rutas de usuario; §4 y §12 de
`08_API-CONTRACT.md` añaden «protección CSRF/origin incluso sin login». El MVP no tiene
autenticación porque es de un único usuario en loopback.

## Decisión propuesta (implementada en S00)

1. `OPOFUENTE_HOST` debe ser loopback; cualquier otro valor provoca `ConfigurationError` al
   arrancar, con mensaje que remite a un proyecto de autenticación aparte.
2. CORS con lista explícita de orígenes (`127.0.0.1`/`localhost` en 5173 y 4173),
   `allow_credentials=False`.
3. Middleware propio que **rechaza con 403 `forbidden_origin`** toda petición no segura
   (POST/PUT/PATCH/DELETE) que traiga cabecera `Origin` fuera de la allowlist. Las peticiones sin
   `Origin` (curl, scripts locales, SSE) se permiten: no hay credenciales de navegador que robar.
4. Cabeceras en todas las respuestas de la API: `Content-Security-Policy: default-src 'none'`,
   `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`,
   `Cross-Origin-Resource-Policy: same-origin`.
5. Identificador de correlación por petición, devuelto en `X-Correlation-ID`, usado en logs y en
   el cuerpo de error (nunca rutas absolutas ni contenido).

## Límites reconocidos

- La CSP de las respuestas de la API no protege el HTML del SPA: en desarrollo lo sirve Vite y en
  preview el servidor de Vite. La CSP del documento llega cuando el backend sirva el frontend
  construido (S12).
- La comprobación de Origin no sustituye autenticación. Antes de cualquier uso en LAN o nube, hace
  falta el proyecto separado de autenticación y aislamiento multiusuario.
- No hay token CSRF porque no hay sesión ni cookies; si se añaden, esta decisión debe revisarse.

## Reversión

Los middlewares son tres clases independientes en `apps/api/opofuente/api/middleware.py`; quitar
uno no afecta al resto de la aplicación. La comprobación de host está aislada en un validador de
`Settings`.
