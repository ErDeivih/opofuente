<#
.SYNOPSIS
    Genera el contrato OpenAPI desde FastAPI y los tipos TypeScript derivados.
.DESCRIPTION
    OpenAPI es la fuente de verdad. `-Check` no escribe: falla si el contrato o los tipos
    commiteados están desincronizados (ADR-002).
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
        Invoke-OpoFuenteStep -Name 'contrato OpenAPI sincronizado' -Action {
            uv run python -m opofuente.tools.export_openapi --check
        }
        Invoke-OpoFuenteStep -Name 'tipos TypeScript sincronizados' -Action {
            npm run contracts:check
        }
    }
    else {
        Invoke-OpoFuenteStep -Name 'exportar OpenAPI' -Action {
            uv run python -m opofuente.tools.export_openapi
        }
        Invoke-OpoFuenteStep -Name 'generar tipos TypeScript' -Action {
            npm run contracts:generate
        }
    }
}
finally {
    Pop-Location
}
