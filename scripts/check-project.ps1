$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "Checking backend Python syntax..." -ForegroundColor Cyan
Get-ChildItem -Recurse backend -Filter *.py | ForEach-Object {
  python -m py_compile $_.FullName
}

if (Get-Command pytest -ErrorAction SilentlyContinue) {
  Write-Host "Running backend tests..." -ForegroundColor Cyan
  python -m pytest backend\tests -q
} else {
  Write-Host "pytest not found. Skipping backend tests." -ForegroundColor Yellow
}

if (Test-Path frontend\node_modules) {
  Write-Host "Building frontend..." -ForegroundColor Cyan
  Push-Location frontend
  npm run build
  Pop-Location
} else {
  Write-Host "frontend/node_modules not found. Skipping frontend build." -ForegroundColor Yellow
}

