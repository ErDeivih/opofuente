#!/bin/sh
# Arranque del contenedor de demostración.
#
# - Copia la base de demo empaquetada al volumen efímero si no existe (cada reinicio vuelve al
#   estado inicial: es una demo, no un servicio con datos).
# - Traduce PUBLIC_ORIGIN a la lista de orígenes que exige la API para aceptar escrituras.
# - Protege la administración con autenticación básica: si no hay DEMO_PASSWORD, genera una
#   aleatoria y la escribe en el log (la demo se puede visitar y practicar sin cuenta).
# - Genera la configuración de nginx con $PORT y arranca API + nginx bajo supervisor.
set -eu

PORT="${PORT:-7860}"
export PORT

DATA_DIR="${OPOFUENTE_DATA_DIR:-/data}"
export OPOFUENTE_DATA_DIR="$DATA_DIR"
mkdir -p "$DATA_DIR" /var/log/supervisor

if [ ! -f "$DATA_DIR/opofuente.sqlite3" ]; then
    cp /opt/demo/opofuente-demo.sqlite3 "$DATA_DIR/opofuente.sqlite3"
fi

# La API exige que el Origin de las escrituras esté autorizado. La web y la API comparten origen,
# así que basta con declarar ese origen una vez (necesario también para la práctica pública).
if [ -n "${PUBLIC_ORIGIN:-}" ] && [ -z "${OPOFUENTE_CORS_ORIGINS:-}" ]; then
    export OPOFUENTE_CORS_ORIGINS="[\"$PUBLIC_ORIGIN\"]"
fi

# Administración con contraseña: si no se define, se genera una y se deja en el log del servicio.
DEMO_USER="${DEMO_USER:-demo}"
if [ -z "${DEMO_PASSWORD:-}" ]; then
    DEMO_PASSWORD="$(openssl rand -hex 12)"
    printf '[demo] DEMO_PASSWORD no definida: administración protegida con contraseña aleatoria: %s\n' \
        "$DEMO_PASSWORD" >&2
fi
printf '%s:%s\n' "$DEMO_USER" "$(openssl passwd -apr1 "$DEMO_PASSWORD")" > /etc/nginx/.htpasswd
chown root:www-data /etc/nginx/.htpasswd
chmod 0640 /etc/nginx/.htpasswd

sed "s/__PORT__/${PORT}/g" /etc/nginx/templates/opofuente.conf.template > /etc/nginx/conf.d/opofuente.conf

# La base empaquetada ya está en la cabeza de Alembic; se comprueba por si la imagen cambia.
cd /app
/app/.venv/bin/alembic -c alembic.ini upgrade head

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/opofuente.conf
