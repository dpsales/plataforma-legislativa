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

  chown -R appuser:appuser "${DATA_DIR}" "${STATIC_DIR}" "${HOME_DIR}"

  export RUN_AS_APPUSER=1
  exec su -p -s /bin/bash appuser -c "export RUN_AS_APPUSER=1; exec \"${SCRIPT_PATH}\""
fi

mkdir -p /app/staticfiles

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "${IMPORT_DEFAULT_JSON:-1}" = "1" ] && [ -f "/app/proposicoes_ids.json" ]; then
  if ! python - <<'PY'
import django
django.setup()
from monitoramento.models import TrackedDocument
import sys
sys.exit(0 if TrackedDocument.objects.exists() else 1)
PY
  then
    python manage.py import_document /app/proposicoes_ids.json || true
  fi
fi

if [ "${RUN_INITIAL_SYNC:-1}" = "1" ]; then
  python manage.py sync_proposicoes || true
fi

gunicorn busca_materias.wsgi:application \
  --bind 0.0.0.0:8080 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --access-logfile - \
  --error-logfile -
