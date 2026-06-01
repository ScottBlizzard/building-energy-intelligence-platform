$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

function Invoke-Checked {
  param(
    [Parameter(Mandatory = $true)]
    [scriptblock]$Command,
    [Parameter(Mandatory = $true)]
    [string]$FailureMessage
  )

  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw $FailureMessage
  }
}

Write-Host "Checking backend Python syntax..." -ForegroundColor Cyan
Get-ChildItem -Recurse backend -Filter *.py | ForEach-Object {
  $file = $_.FullName
  Invoke-Checked { python -m py_compile $file } "Python syntax check failed: $file"
}

if (Get-Command pytest -ErrorAction SilentlyContinue) {
  Write-Host "Running backend tests..." -ForegroundColor Cyan
  Invoke-Checked { python -m pytest backend\tests -q } "Backend tests failed."
} else {
  Write-Host "pytest not found. Skipping backend tests." -ForegroundColor Yellow
}

if (Test-Path frontend\node_modules) {
  Write-Host "Building frontend..." -ForegroundColor Cyan
  Push-Location frontend
  try {
    Invoke-Checked { npm run build } "Frontend build failed."
  } finally {
    Pop-Location
  }
} else {
  Write-Host "frontend/node_modules not found. Skipping frontend build." -ForegroundColor Yellow
}
