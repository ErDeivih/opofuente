<#
.SYNOPSIS
    Aplica las migraciones de base de datos en el directorio de datos configurado.
.EXAMPLE
    ./scripts/migrate.ps1
#>
[CmdletBinding()]
param()

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'common.ps1')

Push-Location $repoRoot
try {
    Invoke-OpoFuenteStep -Name "alembic upgrade head (datos: $(Get-OpoFuenteDataDir))" -Action {
        uv run alembic upgrade head
    }
    Invoke-OpoFuenteStep -Name 'revisión aplicada' -Action {
        uv run alembic current
    }
}
finally {
    Pop-Location
}
