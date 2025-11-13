#!/bin/bash
set -euo pipefail

if [ "${RUN_AS_APPUSER:-0}" != "1" ]; then
  if [ "$(id -u)" -ne 0 ]; then
    echo "start-beat.sh precisa iniciar como root para ajustar permissões" >&2
    exit 1
  fi

  DATA_DIR="/app/data"
  HOME_DIR="/home/appuser"
  SCRIPT_PATH="$(realpath "$0")"

  mkdir -p "${DATA_DIR}" "${HOME_DIR}"

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
  fi

  if [ "${DATA_GID}" -ne "${CURRENT_GID}" ]; then
    groupmod -o -g "${DATA_GID}" appuser
  fi

  chown -R appuser:appuser /app "${HOME_DIR}"

  export RUN_AS_APPUSER=1
  exec su -p -s /bin/bash appuser -c "export RUN_AS_APPUSER=1; exec \"${SCRIPT_PATH}\""
fi

celery -A busca_comissoes_mistas beat \
  --loglevel "${CELERY_LOGLEVEL:-INFO}" \
  --logfile - \
  --pidfile /app/data/celerybeat.pid
