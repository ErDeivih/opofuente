# Redespliegue de la demo (5 líneas)

1. **Render → Dashboard → servicio `opofuente-demo` → Manual Deploy → Deploy latest commit.** Si el
   servicio no existe: **New → Blueprint → repo `ErDeivih/opofuente` → `render.yaml`**.
2. Revisa **Environment**: `PUBLIC_ORIGIN` = URL real del servicio y, si quieres fijarla, `DEMO_PASSWORD`
   (sin ella se genera una aleatoria y se escribe en el log; sin `PUBLIC_ORIGIN` la práctica y las
   escrituras fallan por Origin). Guarda y redespliega.
3. Espera a que `curl -fsS <URL>/healthz` devuelva **200**; en el plan Free, si durmió, la primera
   petición tarda ~1 min (la plataforma despierta el contenedor).
4. Verifica con `node deploy/verificar-demo.mjs <URL>` (sin credenciales): **17/17** —temario, ficha del
   tema I.1 con apuntes, práctica terminada sin cuenta, administración 401— y capturas en
   `docs/capturas/deploy-local/`.
5. Si falla: **Render → Logs** (busca `Traceback`, `[crit]` o `502`) y `/healthz`. Si la URL responde
   **404 con `x-render-routing: no-server`**, no hay servicio con ese nombre: mira el nombre real en el
   dashboard o crea el blueprint del paso 1.

> **Demo estática ya publicada:** <https://erdeivih.github.io/opofuente-demo/>. Su redespliegue
> (build estático, repo público y verificación 8/8) está en [`DEMO-PAGES.md`](DEMO-PAGES.md).
