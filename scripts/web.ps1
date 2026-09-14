<#
.SYNOPSIS
    Arranca el servidor de desarrollo del frontend (Vite).
.DESCRIPTION
    Escucha en 127.0.0.1:5173. La URL de la API se configura con VITE_API_BASE_URL
    (por defecto http://127.0.0.1:8765).
#>
[CmdletBinding()]
param()

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'common.ps1')

Push-Location $repoRoot
try {
    Write-Host 'Web en http://127.0.0.1:5173' -ForegroundColor Cyan
    npm run dev:web
}
finally {
    Pop-Location
}
