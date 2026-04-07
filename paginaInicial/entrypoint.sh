#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-1}" != "0" ]; then
    echo "$(date --iso-8601=seconds) | Aplicando migrações"
    until python manage.py migrate --noinput; do
        echo "$(date --iso-8601=seconds) | Migrações falharam, tentando novamente em 5s"
        sleep 5
    done
fi

exec "$@"
