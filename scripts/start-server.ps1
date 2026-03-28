$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$imageName = "kanban-mvp"
$containerName = "kanban-mvp"
$dataDir = Join-Path $projectRoot "data"

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

docker build -t $imageName $projectRoot
$existingContainer = docker ps -aq -f "name=^${containerName}$"
if ($existingContainer) {
  docker rm -f $containerName | Out-Null
}
docker run -d --name $containerName -p 8000:8000 --env-file "$projectRoot\.env" --env KANBAN_DB_PATH=/app/backend/data/kanban.db -v "${dataDir}:/app/backend/data" $imageName

Write-Host "Server started at http://localhost:8000"
