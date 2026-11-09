# Observabilidad mínima de la demo

**Qué es:** dos contadores propios, sin cuentas de terceros, para saber **qué pantallas se usan** y
**qué errores ve el navegador** en el despliegue de demostración. No sustituye a un APM ni a Sentry;
es lo mínimo para no volar a ciegas en una demo pública.

## Qué se recoge (y qué no)

| Evento | Campos | Límite |
|---|---|---|
| `page_view` | `screen` (nombre estable de la pantalla: `inicio`, `temario`, `preguntas`…) | lista blanca de 15 nombres; un nombre desconocido responde 422 y no cuenta |
| `error` | `screen` + `message` (máx. 200 caracteres, saneado) | hasta 20 errores recientes en memoria; el resto solo se cuenta |

**No se guarda:** IP, `User-Agent`, cookies, texto de documentos o preguntas, rutas de disco,
identificadores de usuario. El saneado sustituye rutas absolutas (Windows, UNC, POSIX) por `[ruta]` y
recorta a 200 caracteres. El cuerpo máximo del evento es 4 KB (413 si se pasa).

**Retención:** memoria del proceso; **se pierde en cada reinicio**. La demo no tiene base para esto ni
migración: es deliberado.

**Privacidad:** no sale nada hacia terceros. El navegador manda los eventos a la propia API, en el
mismo origen. La web solo los envía en build de producción o con `VITE_TELEMETRY=on`; en desarrollo y
en las pruebas está apagada (ver `apps/web/src/telemetry.ts`).

## Cómo leerlo

```powershell
$url = 'http://127.0.0.1:8099'           # o la URL del despliegue
$cred = Get-Credential -UserName demo    # la contraseña de la demo
Invoke-RestMethod "$url/api/v1/telemetry/summary" -Credential $cred | ConvertTo-Json -Depth 4
```

Devuelve:

```json
{
  "total": 42,
  "by_type": { "page_view": 40, "error": 2 },
  "by_screen": { "inicio": 8, "temario": 20, "preguntas": 12, "…": 0 },
  "recent_errors": [
    { "screen": "preguntas", "message": "TypeError: …", "at": "2026-11-09T18:50:00" }
  ]
}
```

La respuesta no incluye usuarios ni sesiones: para eso haría falta un identificador, y la demo no lo
tiene a propósito.

## Qué se ve en el despliegue

- Los **logs de la plataforma** (Render/HF) muestran las peticiones y errores del servidor; la API ya
  loguea JSON saneado y `x-correlation-id`.
- Los contadores de arriba cubren lo que el servidor no ve: **qué pantalla se abre** y **qué error
  peta en el navegador**.
- `GET /healthz` (sin credenciales, para la plataforma) refleja la salud real de la API, no solo la
  de nginx.

## Límites conocidos (dichos, no escondidos)

1. **Sin persistencia:** reiniciar el servicio pone los contadores a cero.
2. **Sin rate limit:** un cliente podría inflar contadores; los tipos y pantallas están acotados y el
   cuerpo limitado a 4 KB, pero no hay throttling. En una demo cerrada con contraseña es aceptable.
3. **Saneado por patrón:** quita rutas y recorta; no es un análisis semántico de cualquier texto.
4. **Lista blanca duplicada** en TS y Python a propósito (una pantalla nueva exige tocar los dos).
5. **Sin pantalla que pinte el resumen:** es un endpoint de operación; pedir la UI sería otro slice.
