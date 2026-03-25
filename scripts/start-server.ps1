$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$imageName = "kanban-mvp"
$containerName = "kanban-mvp"

docker build -t $imageName $projectRoot
docker rm -f $containerName 2>$null | Out-Null
docker run -d --name $containerName -p 8000:8000 --env-file "$projectRoot\.env" $imageName

Write-Host "Server started at http://localhost:8000"
