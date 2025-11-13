#!/bin/bash
set -euo pipefail

if [ "${RUN_AS_APPUSER:-0}" != "1" ]; then
  if [ "$(id -u)" -ne 0 ]; then
    echo "start-web.sh precisa iniciar como root para ajustar permissões" >&2
    exit 1
  fi

  DATA_DIR="/app/data"
  STATIC_DIR="/app/staticfiles"
  HOME_DIR="/home/appuser"
  SCRIPT_PATH="$(realpath "$0")"

  mkdir -p "${DATA_DIR}" "${STATIC_DIR}" "${HOME_DIR}"

  CURRENT_UID="$(id -u appuser)"
  CURRENT_GID="$(getent group appuser | cut -d: -f3)"
  DATA_UID="$(stat -c '%u' "${DATA_DIR}")"
  DATA_GID="$(stat -c '%g' "${DATA_DIR}")"

  if [ "${DATA_UID}" -eq 0 ]; then
    DATA_UID="${CURRENT_UID}"
  fi

  if [ "${DATA_GID}" -eq 0 ]; then
    DATA_GID="${CURRENT_GID}"
  fi

  if [ "${DATA_UID}" -ne "${CURRENT_UID}" ]; then
    usermod -o -u "${DATA_UID}" appuser
    CURRENT_UID="${DATA_UID}"
  fi

  if [ "${DATA_GID}" -ne "${CURRENT_GID}" ]; then
    groupmod -o -g "${DATA_GID}" appuser
    CURRENT_GID="${DATA_GID}"
  fi

  chown -R appuser:appuser /app "${HOME_DIR}"

  export RUN_AS_APPUSER=1
  exec su -p -s /bin/bash appuser -c "export RUN_AS_APPUSER=1; exec \"${SCRIPT_PATH}\""
fi

MIGRATION_LOCK="/app/data/.migrate.lock"
MIGRATION_FLAG="/app/data/.migrated"

mkdir -p "/app/staticfiles"

touch "${MIGRATION_LOCK}"
flock -x "${MIGRATION_LOCK}" python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "${RUN_INITIAL_FETCH:-1}" = "1" ]; then
  if ! python - <<'PY'
import django
django.setup()
from comissoes.models import Proposition
import sys
sys.exit(0 if Proposition.objects.exists() else 1)
PY
  then
    python manage.py fetch_commissoes || true
  fi
fi

touch "${MIGRATION_FLAG}"

gunicorn busca_comissoes_sf.wsgi:application \
  --bind 0.0.0.0:8080 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --access-logfile - \
  --error-logfile -
