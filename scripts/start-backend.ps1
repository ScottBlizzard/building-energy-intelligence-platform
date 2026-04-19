param(
  [string]$HostAddress = "127.0.0.1",
  [int]$Port = 8000
)

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

uvicorn app.main:app --reload --host $HostAddress --port $Port --app-dir backend

