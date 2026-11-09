# syntax=docker/dockerfile:1
#
# Imagen de demostración de OpoFuente: web estática + API en el mismo contenedor.
#
# La API sigue escuchando SOLO en 127.0.0.1 dentro del contenedor (la guardia de loopback del
# producto no se toca); lo que se publica es nginx en $PORT, que sirve la web y hace de proxy de
# `/api/` hacia la API. Es el «proxy en la misma máquina» del plan de despliegue, aplicado dentro
# del contenedor.

# --- 1. build de la web ----------------------------------------------------------------------
FROM node:24-bookworm-slim AS web

WORKDIR /src

# Se instalan los workspaces con el lockfile versionado.
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/contracts/package.json packages/contracts/package.json
RUN npm ci

COPY packages/contracts ./packages/contracts
COPY apps/web ./apps/web

# `same-origin`: el bundle llama a `/api/v1/...` en el mismo origen donde se sirve.
ENV VITE_API_BASE_URL=same-origin
RUN npm run build:web

# --- 2. runtime -------------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# uv para sincronizar el entorno desde el lockfile; nginx hace de fachada pública.
COPY --from=ghcr.io/astral-sh/uv:0.12.12 /uv /uvx /bin/
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx supervisor curl apache2-utils openssl \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

WORKDIR /app

COPY pyproject.toml uv.lock alembic.ini README.md ./
COPY apps/api ./apps/api
COPY fixtures ./fixtures
RUN uv sync --frozen --no-dev

# Base de demostración: temario común + perfil TAI + 40 preguntas sintéticas. Sin Guardia Civil
# ni Celador (DEBT-003: uso privado). Se empaqueta y el entrypoint la copia al volumen efímero.
RUN .venv/bin/python -m opofuente.tools.build_demo_database \
        --out /opt/demo/opofuente-demo.sqlite3 --workdir /tmp/demo-build

COPY --from=web /src/apps/web/dist /srv/www
COPY deploy/nginx.conf.template /etc/nginx/templates/opofuente.conf.template
COPY deploy/supervisord.conf /etc/supervisor/conf.d/opofuente.conf
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod 0755 /entrypoint.sh

# La API se queda en loopback dentro del contenedor; nginx escucha en $PORT.
ENV PORT=7860 \
    OPOFUENTE_HOST=127.0.0.1 \
    OPOFUENTE_PORT=8765 \
    OPOFUENTE_DATA_DIR=/data \
    OPOFUENTE_WORKER_ENABLED=false \
    OPOFUENTE_LOG_LEVEL=INFO

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/healthz" >/dev/null || exit 1

ENTRYPOINT ["/entrypoint.sh"]
