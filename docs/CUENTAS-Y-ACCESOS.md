# Cuentas y accesos para publicar OpoFuente

**Fecha:** 9 de noviembre de 2026 · **Estado:** la **demo estática ya está publicada y verificada**
en <https://erdeivih.github.io/opofuente-demo/> (GitHub Pages, 8/8 comprobaciones; ver
[`DEMO-PAGES.md`](DEMO-PAGES.md)). La **app completa con backend** sigue sin URL: Render no tiene
ningún servicio con el nombre documentado (`404 x-render-routing: no-server`) y en esta máquina no hay
cuenta ni token de proveedor. Este documento cubre esa vía y las cuentas que hacen falta.

## Demo estática ya publicada (no necesita cuenta)

- URL: <https://erdeivih.github.io/opofuente-demo/>.
- Qué enseña: temario 5/40, **13 temas completos** con apartados, tablas, ejemplos y fuente, **13
  prácticas de 10 preguntas** (130 en total) y ficha de pregunta; **27 temas en preparación**
  marcados como tales. Progreso en `localStorage`.
- Cómo se regenera y publica: [`DEMO-PAGES.md`](DEMO-PAGES.md).
- No incluye Guardia Civil, corpus real ni material de academias.

## Por qué la app con backend sigue sin URL

`https://opofuente-demo.onrender.com` responde **404** con `x-render-routing: no-server` y cuerpo
`Not Found`. Eso no es una demo dormida ni un servicio borrado: **Render no tiene ningún servicio con
ese nombre**. La URL de este documento es la *esperada* si el servicio se llama `opofuente-demo`; se
escribió como destino, no como dirección viva. No hay sesión ni token de Render/HF en la máquina
(comprobado otra vez), así que no puedo listar el dashboard ni redesplegar.

Qué hacer ahora, en orden:

1. **Si ya creaste el servicio en Render con otro nombre**, copia la URL real del dashboard. Será
   `https://<nombre-del-servicio>.onrender.com` y es la que hay que poner en `PUBLIC_ORIGIN`.
2. **Si no existe**, crea el blueprint con los pasos de abajo. No hace falta dominio ni tarjeta para
   el plan Free.
3. **Si quieres que el siguiente agente lo verifique sin ti**, pega aquí (o en una variable
   `RENDER_API_KEY` de la sesión) una API key de Render con permiso de lectura: con ella se listan
   servicios y se comprueba el estado real. No la subas al repositorio.

## Por qué la app con backend todavía no se ha desplegado (y por qué no la puedo crear yo)

El encargo pedía desplegar en un proveedor gratuito y, si algo requería una cuenta o un pago, **no
hacerlo** y dejarlo escrito. En esta máquina **no hay ninguna sesión de proveedor cloud** (la demo
estática sí se ha publicado porque GitHub ya estaba autenticado y no hace falta servidor):

| Proveedor | Estado comprobado el 9/11/2026 |
|---|---|
| Hugging Face | `hf auth whoami` → no hay sesión; no hay token en `~/.cache/huggingface` |
| Supabase | `supabase projects list` → sin `SUPABASE_ACCESS_TOKEN` |
| Render / Fly.io / Railway / Cloudflare / Vercel / Netlify | su CLI no está instalado ni hay token en el entorno |
| GitHub | **sí**: `gh auth status` → cuenta `ErDeivih`, con scope `repo` |

Crear cuentas o pegar tarjetas está fuera de lo que puedo hacer. Por eso el despliegue está
**preparado y probado en local con el artefacto real** (imagen Docker, mismas rutas, mismo nginx,
misma base de demo) y solo falta el alta.

## Qué se va a desplegar (y por qué este proveedor)

**Render, plan Free, un único servicio web Docker.** No es el plan del documento de fase 2 (Postgres
+ API + web separadas) porque **la aplicación todavía no funciona sobre Postgres**: usa SQLite con
FTS5, `PRAGMA` y migraciones `batch_alter_table`; migrarla son 6-10 slices (ver
`PLAN-DESPLIEGUE-FASE2-2026-11.md` §4.1). Para una demo pública que cargue el temario y el banco, lo
correcto es **un contenedor con SQLite dentro** y datos sintéticos empaquetados.

- La **API sigue escuchando en `127.0.0.1`** dentro del contenedor: la guardia de loopback no se
  toca. Lo público es nginx, que sirve la web y hace de proxy de `/api/`.
- La **web se sirve desde el mismo origen** (`VITE_API_BASE_URL=same-origin`), sin CSP rota ni URL
  de API horneada a la máquina de desarrollo.
- La base es la **demo empaquetada** en la imagen: temario común (5 bloques / 40 temas), perfil TAI
  2025, **el tema I.1 con apuntes propios (citados del BOE)** y una **práctica de 10 preguntas sobre
  ese tema**, además de 40 preguntas sintéticas de banco. No incluye Guardia Civil ni Celador
  (DEBT-003) ni el corpus real de David.
- **Acceso sin cuenta:** la demo se puede visitar y **practicar sin registrarse** (lectura y
  `study-sessions` son públicos). La administración (importar, copias, ajustes) queda detrás de
  autenticación básica: si no defines `DEMO_PASSWORD`, el entrypoint genera una aleatoria y la escribe
  en el log del servicio. No hay login de usuario ni cuentas de alumno.
- El plan Free **no tiene disco persistente**: cada reinicio vuelve al estado inicial de la demo.
  Es una demo de lectura y práctica, no un servicio con datos.

## Paso a paso (lo que tiene que hacer David)

### 1. Crear la cuenta de Render (5 minutos)

1. Abre <https://dashboard.render.com/register>.
2. Elige **Sign up with GitHub** y autoriza con la cuenta que ya está en esta máquina
   (`ErDeivih`). No hay que crear contraseña nueva ni pegar una tarjeta para el plan Free; si Render
   la pidiera, **no la pongas**: usa la alternativa de Hugging Face (abajo).
3. Verifica el correo si lo pide.

### 2. Desplegar el blueprint

1. En Render: **New → Blueprint**.
2. Conecta el repositorio `ErDeivih/opofuente` (privado; Render pide instalar su GitHub App una vez).
3. Rama: la que se quiera publicar (hoy `rescate/fase0-2026-10-26`, commit `72a634b` + lo de esta
   sesión). Render leerá `render.yaml` de la raíz y creará el servicio `opofuente-demo`.
4. Aplica el blueprint. El primer build tarda **5-10 minutos** (instala Node, Python y compila la
   web). El servicio se llama `opofuente-demo` → la URL será
   `https://opofuente-demo.onrender.com` salvo que el nombre esté ocupado.

### 3. Pegar las variables que faltan (2 minutos)

En **Dashboard → opofuente-demo → Environment**:

| Variable | Valor exacto | ¿Secreta? | Para qué |
|---|---|---|---|
| `PUBLIC_ORIGIN` | `https://opofuente-demo.onrender.com` (la URL real que te dé Render) | no | La API solo acepta escrituras cuyo `Origin` esté autorizado |
| `DEMO_USER` | `demo` (ya viene en `render.yaml`) | no | Usuario de la autenticación básica de nginx |
| `DEMO_PASSWORD` | una contraseña larga que elijas | **sí** | Sin ella la demo queda **abierta a cualquiera**; no la publiques |
| `OPOFUENTE_WORKER_ENABLED` | `false` (ya viene) | no | La demo no procesa material: no necesita worker |

Guarda y pulsa **Manual Deploy → Deploy latest commit** (o *Restart*): el arranque traduce
`PUBLIC_ORIGIN` a la configuración de CORS/Origin.

### 4. Verificar la URL (2 minutos)

Con la URL y el usuario/contraseña:

```powershell
$url = 'https://opofuente-demo.onrender.com'
$cred = Get-Credential -UserName demo   # pega DEMO_PASSWORD cuando la pida
Invoke-WebRequest "$url/healthz" -UseDefaultCredentials   # 200 ok
Invoke-WebRequest "$url/api/v1/curricula" -Credential $cred | Select-Object -ExpandProperty StatusCode
Invoke-WebRequest "$url/api/v1/question-sets" -Credential $cred | Select-Object -ExpandProperty StatusCode
```

Y en el navegador (pedirá usuario/contraseña): abrir `/` → **Temario** (5 bloques / 40 temas) y
**Preguntas** (conjunto «Banco de demostración (datos sintéticos)» con 40 preguntas). El botón
«Empezar una práctica» también funciona; lo que no hay es tu corpus real.

### 5. Alternativa si Render pide tarjeta: Hugging Face Spaces

Mismo `Dockerfile`, sin coste y sin tarjeta. Cuenta en <https://huggingface.co/join> y token de
escritura en <https://huggingface.co/settings/tokens>. Instrucciones completas en
[`deploy/hf/README.md`](../deploy/hf/README.md). Variables equivalentes: `PUBLIC_ORIGIN`
(`https://<usuario>-opofuente-demo.hf.space`), `DEMO_USER`, `DEMO_PASSWORD`.

## Qué NO hay que hacer

- **No crear una base en Neon/Supabase**: la app no habla Postgres todavía (ver arriba); una URL con
  Postgres no arrancaría.
- **No pegar secretos** en el repositorio, en capturas ni en el chat: `DEMO_PASSWORD` solo en el
  panel del proveedor.
- **No desplegar el corpus real** ni el directorio `data/` de David: la imagen empaqueta solo la
  base de demo sintética.
- **No abrir la demo sin contraseña**: la app no tiene login propio y quedaría cualquiera con acceso
  a escrituras (importar, crear sesiones, borrar material).

## Qué falta exactamente para tener la URL

1. Crear la cuenta de Render con GitHub (o la de Hugging Face) — **David, 5 min**.
2. Aplicar el blueprint y esperar el build — **David, 2 clics y 5-10 min**.
3. Pegar `PUBLIC_ORIGIN` y `DEMO_PASSWORD` — **David, 2 min**.
4. Verificar con `deploy/verificar-demo.mjs` (abajo) — **David o el siguiente agente, 2 min**.

## Lo que sí está hecho y probado en local

- `Dockerfile` multi-stage (web + API + nginx + supervisor) y `.dockerignore`; imagen local de 583 MB.
- `deploy/entrypoint.sh`, `deploy/nginx.conf.template`, `deploy/supervisord.conf`.
- `render.yaml`, `deploy/hf/README.md` y `deploy/verificar-demo.mjs` (verificación con Playwright).
- Base de demo reproducible: `uv run python -m opofuente.tools.build_demo_database` (temario común,
  perfil TAI y 40 preguntas sintéticas con clave activa; sin Guardia Civil ni Celador).
- Observabilidad en la propia API: `POST /api/v1/telemetry/events` y `GET /api/v1/telemetry/summary`
  (ver [`OBSERVABILIDAD.md`](OBSERVABILIDAD.md)).
- Carga: `load/k6-50vu.js` con 50 usuarios concurrentes (ver [`CARGA.md`](CARGA.md)).

## Prueba local (ejecutada el 9/11/2026, noche)

Contenedor arrancado en el puerto 8099 con `PUBLIC_ORIGIN=http://127.0.0.1:8099` y **sin
`DEMO_PASSWORD`** (administración con contraseña aleatoria escrita en el log):

| Comprobación | Resultado |
|---|---|
| `GET /healthz` (proxy a la salud real de la API) | **200** |
| `GET /` y `/temario` sin credenciales | **200**: la demo se visita sin cuenta |
| `GET /api/v1/curricula` | **200**: temario común `informatica-c1-v1` activo + programa del TAI |
| `GET /api/v1/question-sets` | **2** conjuntos: banco de 40 preguntas y práctica del tema I.1 (10 preguntas) |
| Ficha del tema I.1 | **3.141 caracteres de apuntes** propios (BOE) |
| **Práctica completa sin cuenta** | sesión creada (201), 10 respuestas, `finish` y resultado **200** |
| `POST /api/v1/backups` sin credenciales | **401**: la administración sigue protegida |
| `deploy/verificar-demo.mjs` | **17/17**: portada, temario, ficha con apuntes, práctica terminada, admin 401, sin errores |
| k6, 50 VUs, 60 s | 7 565 peticiones, **0 fallos**, p95 **453 ms** (medido antes del cambio de acceso) |

**Capturas de la prueba local:** [`docs/capturas/deploy-local/`](capturas/deploy-local/) (inicio,
temario, banco y ficha del tema I.1 a 1280 y 390, servidas por el contenedor).

**Lo que no se pudo probar:** la URL pública real (falta la cuenta, sección de arriba) y el
comportamiento del plan Free de Render (0,1 CPU, siesta por inactividad): los números de carga son de
este equipo.
