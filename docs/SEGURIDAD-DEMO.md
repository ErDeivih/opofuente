# Seguridad de la demo y reporte de erratas

**Fecha:** 10/11/2026 · **URL:** <https://erdeivih.github.io/opofuente-demo/>

## Cabeceras y CSP

GitHub Pages sirve estático y **no permite configurar cabeceras HTTP**. Por eso la demo declara en el
`<head>`:

- **CSP por `<meta>`**: `default-src 'none'`, `script-src 'self'`, `style-src 'self' 'unsafe-inline'`,
  `img-src 'self' data:`, `font-src 'self' data:`, `connect-src 'none'`, `media-src 'none'`,
  `object-src 'none'`, `base-uri 'none'`, `form-action 'none'`, `frame-src 'none'`,
  `worker-src 'none'`.
- **Referrer:** `<meta name="referrer" content="no-referrer">`.
- Con `connect-src 'none'` la página no puede hacer peticiones de red: encaja con una demo sin
  backend y evita exfiltración.

Límites dichos:

- `frame-ancestors` **no funciona** desde `<meta>`; no se incluye para no generar un aviso inútil. Para
  prohibir el encuadre haría falta una cabecera HTTP real, que Pages no ofrece.
- `style-src 'unsafe-inline'` es necesario por los estilos en línea de React (barra de progreso).
- Las cabeceras de seguridad completas (HSTS, X-Frame-Options, Permissions-Policy) requieren un
  servidor propio; quedan para el despliegue con backend.

La verificación comprueba que las dos etiquetas están presentes y que la página no lanza errores.

## Fecha y fuente de revisión

Cada tema declara `reviewedAt` (última revisión: **10/11/2026**) y `source` (norma y URL oficial). La
ficha muestra **«Revisión y fuente»** con la fecha y el enlace a la norma citada; el build exige que
ambos campos existan en los 40 temas.

## Reporte de erratas

Cada ficha de tema tiene un formulario **«¿Has visto una errata?»**:

1. Se describe la errata (tema, apartado, qué corregir).
2. Al pulsar **«Descargar constancia de errata»** se guarda un registro en `localStorage`
   (`opofuente-demo-erratas-v1`) y se descarga un **fichero JSON** con el historial de erratas de este
   navegador.
3. La demo no envía nada ni crea tickets: el fichero se descarga para que el usuario lo envíe por el
   canal que corresponda.

Esto es lo máximo que puede hacer una demo sin backend; no se simula un servidor ni una API.

## Verificación

- **61/61** comprobaciones con Playwright en la URL pública, incluidas CSP, `referrer`, fecha de
  revisión, descarga del JSON de errata y etiqueta **«Simulación»** en el examen.
- 12/12 enlaces de convocatoria abren (HTTP 200).
- 517 pruebas unitarias de backend y 225 de web; typecheck, eslint, ruff, mypy y build.
