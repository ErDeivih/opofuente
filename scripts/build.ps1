<#
.SYNOPSIS
    Construye los artefactos: paquete de Python y bundle del frontend.
#>
[CmdletBinding()]
param()

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'common.ps1')

Push-Location $repoRoot
try {
    Invoke-OpoFuenteStep -Name 'uv build (paquete Python)' -Action { uv build }
    Invoke-OpoFuenteStep -Name 'vite build (frontend)' -Action { npm run build:web }
}
finally {
    Pop-Location
}
