#!/usr/bin/env sh
set -eu

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
IMAGE_NAME="kanban-mvp"
CONTAINER_NAME="kanban-mvp"

docker build -t "$IMAGE_NAME" "$PROJECT_ROOT"
docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER_NAME" -p 8000:8000 --env-file "$PROJECT_ROOT/.env" "$IMAGE_NAME"

echo "Server started at http://localhost:8000"
