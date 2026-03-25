$ErrorActionPreference = "Stop"

$containerName = "kanban-mvp"

docker stop $containerName
docker rm $containerName

Write-Host "Server stopped"
