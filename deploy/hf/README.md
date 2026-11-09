---
title: OpoFuente demo
emoji: 📚
colorFrom: blue
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
---

# OpoFuente — demo

Espacio de demostración de OpoFuente (biblioteca local de oposiciones). Es la alternativa a Render
si Render pide tarjeta: Hugging Face Spaces ejecuta el mismo `Dockerfile` del repositorio sin coste.

## Cómo publicarlo

1. Crea una cuenta en <https://huggingface.co/join> y un token de escritura en
   <https://huggingface.co/settings/tokens>.
2. `hf auth login` (o `huggingface-cli login`) con ese token.
3. Crea un Space **Docker** vacío llamado, por ejemplo, `opofuente-demo`.
4. Sube el repositorio al Space. El `README.md` de la raíz del Space debe ser **este** fichero
   (el frontmatter `sdk: docker` y `app_port: 7860` son obligatorios):

   ```powershell
   git remote add space https://huggingface.co/spaces/<usuario>/opofuente-demo
   git push space HEAD:main --force
   ```

   Si el Space rechaza el README del repositorio, copia este fichero como `README.md` en la raíz
   antes del push.
5. En *Settings → Variables and secrets* del Space define:
   - `PUBLIC_ORIGIN` = `https://<usuario>-opofuente-demo.hf.space`
   - `DEMO_USER` = `demo`
   - `DEMO_PASSWORD` = una contraseña que elijas (secreto)
   - `OPOFUENTE_WORKER_ENABLED` = `false`
6. Reinicia el Space. La URL pública es `https://<usuario>-opofuente-demo.hf.space`.

## Límites

- CPU básica gratuita, sin tarjeta; el Space se duerme por inactividad y despierta solo.
- Disco efímero: cada reinicio vuelve a la base de demostración empaquetada (no hay datos reales ni
  progreso persistente).
- No subas el corpus real: la demo está pensada con datos sintéticos y el temario común.
