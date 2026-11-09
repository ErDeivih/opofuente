#!/bin/sh
# Arranque del contenedor de demostración.
#
# - Copia la base de demo empaquetada al volumen efímero si no existe (cada reinicio vuelve al
#   estado inicial: es una demo, no un servicio con datos).
# - Traduce PUBLIC_ORIGIN a la lista de orígenes que exige la API para aceptar escrituras.
# - Opcionalmente activa autenticación básica de borde (DEMO_USER/DEMO_PASSWORD).
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

# La API exige que el Origin de las escrituras esté autorizado. En el despliegue, la web y la API
# comparten origen, así que basta con declarar ese origen una vez.
if [ -n "${PUBLIC_ORIGIN:-}" ] && [ -z "${OPOFUENTE_CORS_ORIGINS:-}" ]; then
    export OPOFUENTE_CORS_ORIGINS="[\"$PUBLIC_ORIGIN\"]"
fi

# Autenticación de borde: sin login propio en la app, una URL pública no debe quedar abierta.
: > /etc/nginx/conf.d/auth.inc
if [ -n "${DEMO_PASSWORD:-}" ]; then
    DEMO_USER="${DEMO_USER:-demo}"
    printf '%s:%s\n' "$DEMO_USER" "$(openssl passwd -apr1 "$DEMO_PASSWORD")" > /etc/nginx/.htpasswd
    # nginx lee el fichero como www-data: el hash no debe quedar solo para root.
    chown root:www-data /etc/nginx/.htpasswd
    chmod 0640 /etc/nginx/.htpasswd
    {
        printf 'auth_basic "OpoFuente (demo)";\n'
        printf 'auth_basic_user_file /etc/nginx/.htpasswd;\n'
    } > /etc/nginx/conf.d/auth.inc
fi

sed "s/__PORT__/${PORT}/g" /etc/nginx/templates/opofuente.conf.template > /etc/nginx/conf.d/opofuente.conf

# La base empaquetada ya está en la cabeza de Alembic; se comprueba por si la imagen cambia.
cd /app
/app/.venv/bin/alembic -c alembic.ini upgrade head

exec /usr/bin/supervisord -c /etc/supervisor/conf.d/opofuente.conf
