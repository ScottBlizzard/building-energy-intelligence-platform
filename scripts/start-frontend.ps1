param(
  [int]$Port = 5173
)

$root = Split-Path -Parent $PSScriptRoot
Set-Location (Join-Path $root "frontend")

npm run dev -- --host 0.0.0.0 --port $Port
