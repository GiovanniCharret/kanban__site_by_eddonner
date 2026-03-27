$ErrorActionPreference = "Stop"

$containerName = "kanban-mvp"

$existingContainer = docker ps -aq -f "name=^${containerName}$"
if ($existingContainer) {
  docker stop $containerName | Out-Null
  docker rm $containerName | Out-Null
}

Write-Host "Server stopped"
