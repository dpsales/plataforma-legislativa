#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS:-1}" != "0" ]; then
    echo "$(date --iso-8601=seconds) | Applying migrations..."
    MAX_ATTEMPTS=30
    ATTEMPT=0
    until python manage.py migrate --noinput; do
        ATTEMPT=$((ATTEMPT + 1))
        if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
            echo "$(date --iso-8601=seconds) | Migrations failed after $MAX_ATTEMPTS attempts. Continuing without migrations."
            break
        fi
        WAIT_TIME=$((5 * ATTEMPT))
        echo "$(date --iso-8601=seconds) | Migration attempt $ATTEMPT failed. Retrying in ${WAIT_TIME}s..."
        sleep $WAIT_TIME
    done
fi

exec "$@"
