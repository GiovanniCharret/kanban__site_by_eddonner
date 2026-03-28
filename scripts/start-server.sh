#!/usr/bin/env sh
set -eu

PROJECT_ROOT="$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)"
IMAGE_NAME="kanban-mvp"
CONTAINER_NAME="kanban-mvp"
DATA_DIR="$PROJECT_ROOT/data"
DNS_PRIMARY="1.1.1.1"
DNS_SECONDARY="8.8.8.8"

mkdir -p "$DATA_DIR"

docker build -t "$IMAGE_NAME" "$PROJECT_ROOT"
docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker run -d --name "$CONTAINER_NAME" -p 8000:8000 --dns "$DNS_PRIMARY" --dns "$DNS_SECONDARY" --env-file "$PROJECT_ROOT/.env" --env KANBAN_DB_PATH=/app/backend/data/kanban.db -v "$DATA_DIR:/app/backend/data" "$IMAGE_NAME"

echo "Server started at http://localhost:8000"
