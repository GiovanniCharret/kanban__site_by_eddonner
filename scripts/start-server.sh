#!/usr/bin/env sh
set -eu

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
IMAGE_NAME="kanban-mvp"
CONTAINER_NAME="kanban-mvp"
DATA_DIR="$PROJECT_ROOT/data"
set --

if [ -n "${KANBAN_DOCKER_DNS:-}" ]; then
  OLD_IFS=$IFS
  IFS=','
  for dns_server in $KANBAN_DOCKER_DNS; do
    if [ -n "$dns_server" ]; then
      set -- "$@" --dns "$dns_server"
    fi
  done
  IFS=$OLD_IFS
fi

mkdir -p "$DATA_DIR"

docker build -t "$IMAGE_NAME" "$PROJECT_ROOT"
docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER_NAME" -p 8000:8000 "$@" --env-file "$PROJECT_ROOT/.env" --env KANBAN_DB_PATH=/app/backend/data/kanban.db -v "$DATA_DIR:/app/backend/data" "$IMAGE_NAME"

echo "Server started at http://localhost:8000"
