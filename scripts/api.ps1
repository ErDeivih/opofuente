<#
.SYNOPSIS
    Arranca la API local en loopback.
.DESCRIPTION
    Migra primero la base de datos y después sirve la API. El host y el puerto se leen de
    OPOFUENTE_HOST / OPOFUENTE_PORT (por defecto 127.0.0.1:8765). Nunca se escucha en 0.0.0.0.
.PARAMETER Reload
    Recarga automática al cambiar el código (solo desarrollo).
#>
[CmdletBinding()]
param(
    [switch]$Reload
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'common.ps1')

$host_ = if ($env:OPOFUENTE_HOST) { $env:OPOFUENTE_HOST } else { '127.0.0.1' }
$port = if ($env:OPOFUENTE_PORT) { $env:OPOFUENTE_PORT } else { '8765' }

Push-Location $repoRoot
try {
    & (Join-Path $PSScriptRoot 'migrate.ps1')
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "API en http://${host_}:${port}  (documentación: /api/v1/docs)" -ForegroundColor Cyan
    $arguments = @('run', 'uvicorn', 'opofuente.main:app', '--host', $host_, '--port', $port)
    if ($Reload) { $arguments += '--reload' }
    uv @arguments
}
finally {
    Pop-Location
}
