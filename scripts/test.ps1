<#
.SYNOPSIS
    Ejecuta las pruebas.
.PARAMETER Api
    Solo pruebas del backend (pytest).
.PARAMETER Web
    Solo pruebas del frontend (Vitest).
.EXAMPLE
    ./scripts/test.ps1
    ./scripts/test.ps1 -Api
#>
[CmdletBinding()]
param(
    [switch]$Api,
    [switch]$Web
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'common.ps1')

$runApi = $Api -or (-not $Api -and -not $Web)
$runWeb = $Web -or (-not $Api -and -not $Web)

Push-Location $repoRoot
try {
    if ($runApi) {
        Invoke-OpoFuenteStep -Name 'pytest (backend)' -Action { uv run pytest }
    }
    if ($runWeb) {
        Invoke-OpoFuenteStep -Name 'vitest (frontend)' -Action { npm run test:web }
    }
}
finally {
    Pop-Location
}
