$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$imageName = "kanban-mvp"
$containerName = "kanban-mvp"
$dataDir = Join-Path $projectRoot "data"
$dnsServers = @()
if ($env:KANBAN_DOCKER_DNS) {
  $dnsServers = $env:KANBAN_DOCKER_DNS.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ }
}

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

docker build -t $imageName $projectRoot
$existingContainer = docker ps -aq -f "name=^${containerName}$"
if ($existingContainer) {
  docker rm -f $containerName | Out-Null
}

$dockerRunArgs = @(
  "run"
  "-d"
  "--name"
  $containerName
  "-p"
  "8000:8000"
)

foreach ($dnsServer in $dnsServers) {
  $dockerRunArgs += @("--dns", $dnsServer)
}

$dockerRunArgs += @(
  "--env-file"
  "$projectRoot\.env"
  "--env"
  "KANBAN_DB_PATH=/app/backend/data/kanban.db"
  "-v"
  "${dataDir}:/app/backend/data"
  $imageName
)

& docker @dockerRunArgs

Write-Host "Server started at http://localhost:8000"
