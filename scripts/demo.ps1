# Full local run against the compose stack: generate -> init-db -> pipeline -> evaluate
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

if (-not $env:PREFECT_API_URL) {
    $env:PREFECT_API_URL = "http://127.0.0.1:4200/api"
}

fanuni generate
if ($LASTEXITCODE -ne 0) { exit 1 }
fanuni init-db
if ($LASTEXITCODE -ne 0) { exit 1 }
fanuni pipeline
if ($LASTEXITCODE -ne 0) { exit 1 }
fanuni evaluate
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Demo complete. Dashboards: cd site; npm run sources; npm run dev" -ForegroundColor Green
