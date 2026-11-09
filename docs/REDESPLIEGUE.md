# Redespliegue de la demo (5 líneas)

1. **Render → Dashboard → servicio `opofuente-demo` → Manual Deploy → Deploy latest commit.** Si el
   servicio no existe: **New → Blueprint → repo `ErDeivih/opofuente` → `render.yaml`**.
2. Revisa **Environment**: `PUBLIC_ORIGIN` = URL real del servicio y `DEMO_PASSWORD` = la contraseña;
   guarda y redespliega (sin `PUBLIC_ORIGIN` las escrituras fallan por Origin; sin `DEMO_PASSWORD` la
   demo queda abierta).
3. Espera a que `curl -fsS <URL>/healthz` devuelva **200**; en el plan Free, si durmió, la primera
   petición tarda ~1 min (la plataforma despierta el contenedor).
4. Verifica con `node deploy/verificar-demo.mjs <URL>` y `DEMO_USER`/`DEMO_PASSWORD`: **7/7** y
   capturas en `docs/capturas/deploy-local/`.
5. Si falla: **Render → Logs** (busca `Traceback`, `[crit]` o `502`) y `/healthz`. Si la URL responde
   **404 con `x-render-routing: no-server`**, no hay servicio con ese nombre: mira el nombre real en el
   dashboard o crea el blueprint del paso 1.
