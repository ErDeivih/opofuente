<#
.SYNOPSIS
    Instalación limpia en Windows: entorno de Python y dependencias de Node.
.EXAMPLE
    ./scripts/install.ps1
#>
[CmdletBinding()]
param()

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'common.ps1')

& (Join-Path $PSScriptRoot 'check-requirements.ps1') -RepoRoot $repoRoot

Push-Location $repoRoot
try {
    Invoke-OpoFuenteStep -Name 'uv sync (entorno de Python y lockfile)' -Action {
        uv sync
    }
    Invoke-OpoFuenteStep -Name 'npm install (workspaces de Node)' -Action {
        npm install
    }
    Invoke-OpoFuenteStep -Name 'migración de la base de datos' -Action {
        uv run alembic upgrade head
    }
    Invoke-OpoFuenteStep -Name 'contrato OpenAPI y tipos TypeScript' -Action {
        uv run python -m opofuente.tools.export_openapi
        if ($LASTEXITCODE -ne 0) { return }
        npm run contracts:generate
    }
}
finally {
    Pop-Location
}

Write-Host ''
Write-Host 'Instalación terminada. Siguiente paso: ./scripts/dev.ps1' -ForegroundColor Green
Write-Host "Datos locales en: $(Get-OpoFuenteDataDir)"
