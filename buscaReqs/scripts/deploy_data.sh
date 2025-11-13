#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SERVICE_DIR/.." && pwd)"

PYTHON_BIN="${PYTHON_BIN:-python}"
GENERATOR_ARGS="${GENERATOR_ARGS:-}"
TARGET_BRANCH="${TARGET_BRANCH:-main}"
COMMIT_MESSAGE="${COMMIT_MESSAGE:-bot: atualiza busca.html}"
PUSH_CHANGES="${PUSH_CHANGES:-1}"

OUTPUT_FILE_REL="buscaReqs/templates/requisicoes/busca.html"
OUTPUT_FILE="$REPO_ROOT/$OUTPUT_FILE_REL"

echo "[deploy_data] Gerando HTML com configuração atual..."
cd "$SERVICE_DIR"

# Constrói a lista de argumentos garantindo a coleta padrão (--api --verbose)
DEFAULT_GENERATOR_ARGS=(--api --verbose)
if [[ -n "$GENERATOR_ARGS" ]]; then
    # shellcheck disable=SC2206 # divisão intencional por whitespace
    EXTRA_ARGS=($GENERATOR_ARGS)
else
    EXTRA_ARGS=()
fi

GENERATOR_FLAGS=()
for arg in "${DEFAULT_GENERATOR_ARGS[@]}"; do
    GENERATOR_FLAGS+=("$arg")
done
for arg in "${EXTRA_ARGS[@]}"; do
    GENERATOR_FLAGS+=("$arg")
done

"$PYTHON_BIN" buscaReqs15.py "${GENERATOR_FLAGS[@]}" --output "$OUTPUT_FILE"

echo "[deploy_data] Arquivo gerado em $OUTPUT_FILE_REL"

if [[ "${SKIP_GIT:-0}" == "1" ]]; then
    echo "[deploy_data] Variável SKIP_GIT=1 detectada; finalizando sem versionar."
    exit 0
fi

cd "$REPO_ROOT"

if git remote get-url origin >/dev/null 2>&1; then
    HAS_ORIGIN_REMOTE=1
    echo "[deploy_data] Garantindo sincronização com origin/$TARGET_BRANCH"
    git fetch origin "$TARGET_BRANCH"
else
    HAS_ORIGIN_REMOTE=0
    echo "[deploy_data] Nenhum remoto 'origin' configurado; prosseguindo apenas com commits locais."
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$CURRENT_BRANCH" != "$TARGET_BRANCH" ]]; then
    echo "[deploy_data] Alterando branch de $CURRENT_BRANCH para $TARGET_BRANCH"
    git checkout "$TARGET_BRANCH"
fi

git add "$OUTPUT_FILE_REL"

if git diff --cached --quiet; then
    echo "[deploy_data] Nenhuma alteração detectada em $OUTPUT_FILE_REL."
    git reset "$OUTPUT_FILE_REL"
    exit 0
fi

git commit -m "$COMMIT_MESSAGE"

if [[ "$PUSH_CHANGES" == "1" ]]; then
    if [[ "$HAS_ORIGIN_REMOTE" == "1" ]]; then
        git push origin "$TARGET_BRANCH"
        echo "[deploy_data] Push enviado para origin/$TARGET_BRANCH."
    else
        echo "[deploy_data] PUSH_CHANGES=1, mas não há remoto 'origin'; nenhuma publicação realizada."
    fi
else
    echo "[deploy_data] PUSH_CHANGES=0; commit criado apenas localmente."
fi