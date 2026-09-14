<#
.SYNOPSIS
    Siembra los perfiles oficiales (oposiciones, convocatorias, programa y reglas).
.DESCRIPTION
    La siembra es idempotente: repetirla no duplica nada. Con -Check falla si hubiera cambios
    pendientes, que es lo que se comprueba en las puertas de calidad.
#>
[CmdletBinding()]
param(
    [switch]$Check
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'common.ps1')

Push-Location $repoRoot
try {
    if ($Check) {
        Invoke-OpoFuenteStep -Name 'perfiles sincronizados con los fixtures' -Action {
            uv run python -m opofuente.tools.seed_profiles --check
        }
    }
    else {
        Invoke-OpoFuenteStep -Name "siembra de perfiles (datos: $(Get-OpoFuenteDataDir))" -Action {
            uv run python -m opofuente.tools.seed_profiles
        }
    }
}
finally {
    Pop-Location
}
