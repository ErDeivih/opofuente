<#
.SYNOPSIS
    Ejecuta las pruebas end-to-end con Playwright.
.DESCRIPTION
    Construye el frontend y lanza Playwright, que arranca por su cuenta la API (migrando antes
    el directorio `.e2e-data`, nunca el directorio real) y el servidor de preview.
#>
[CmdletBinding()]
param()

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'common.ps1')

Push-Location $repoRoot
try {
    Invoke-OpoFuenteStep -Name 'build del frontend (necesario para el preview)' -Action {
        npm run build:web
    }
    Invoke-OpoFuenteStep -Name 'playwright test' -Action {
        npm run e2e
    }
}
finally {
    Pop-Location
}
