#!/usr/bin/env sh
set -eu

CONTAINER_NAME="kanban-mvp"

docker stop "$CONTAINER_NAME"
docker rm "$CONTAINER_NAME"

echo "Server stopped"
