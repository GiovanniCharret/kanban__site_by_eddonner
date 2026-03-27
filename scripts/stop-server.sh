#!/usr/bin/env sh
set -eu

CONTAINER_NAME="kanban-mvp"

docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true

echo "Server stopped"
