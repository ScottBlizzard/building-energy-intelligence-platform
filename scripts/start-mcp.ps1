param(
  [ValidateSet("stdio", "sse", "streamable-http")]
  [string]$Transport = "stdio",
  [string]$HostAddress = "127.0.0.1",
  [int]$Port = 8765
)

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$env:MCP_TRANSPORT = $Transport
$env:MCP_HOST = $HostAddress
$env:MCP_PORT = "$Port"
$env:PYTHONPATH = "$root\backend"

if ($Transport -eq "stdio") {
  [Console]::Error.WriteLine("MCP stdio server is running. The terminal may stay blank because stdout is reserved for MCP JSON-RPC messages. Press Ctrl+C to stop it.")
} else {
  [Console]::Error.WriteLine("MCP $Transport server is starting at $HostAddress`:$Port. Streamable HTTP path: /mcp")
}

& "$root\.venv\Scripts\python.exe" -m app.mcp_server
