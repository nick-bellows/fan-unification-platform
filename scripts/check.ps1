# Run everything CI runs, locally, before pushing.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

ruff check .
if ($LASTEXITCODE -ne 0) { exit 1 }
ruff format --check .
if ($LASTEXITCODE -ne 0) { exit 1 }
mypy src tests
if ($LASTEXITCODE -ne 0) { exit 1 }
pytest
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "All local checks passed." -ForegroundColor Green
