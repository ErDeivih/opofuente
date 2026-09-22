<#
.SYNOPSIS
    Utilidades compartidas por los scripts de OpoFuente.
.DESCRIPTION
    Todas las rutas se resuelven desde la raíz del repositorio. Ningún script toca la carpeta de
    originales del usuario: solo `OPOFUENTE_DATA_DIR`.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Con StrictMode, leer $LASTEXITCODE antes de ejecutar ningún comando nativo fallaría.
$LASTEXITCODE = 0

$script:OpoFuenteRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Get-OpoFuenteRepoRoot {
    return $script:OpoFuenteRepoRoot
}

function Invoke-OpoFuenteStep {
    <#
    .SYNOPSIS
        Ejecuta un paso de las puertas de calidad y falla si el proceso devuelve código distinto de cero.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][scriptblock]$Action
    )

    Write-Host ''
    Write-Host "=== $Name ===" -ForegroundColor Cyan
    & $Action
    if ($LASTEXITCODE -ne 0) {
        Write-Host "FALLO en '$Name' (código $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "OK: $Name" -ForegroundColor Green
}

function Get-OpoFuenteDataDir {
    if ($env:OPOFUENTE_DATA_DIR) { return $env:OPOFUENTE_DATA_DIR }
    return (Join-Path $script:OpoFuenteRepoRoot 'data')
}

function Get-OpoFuenteShell {
    <#
    .SYNOPSIS
        La ruta del intérprete de PowerShell para lanzar un script en otro proceso.
    .DESCRIPTION
        `pwsh` (PowerShell 7) **no está siempre en el PATH**: en equipos donde solo está el Windows
        PowerShell, `Start-Process -FilePath 'pwsh'` falla con «no se puede encontrar el archivo» y el
        arranque documentado no funciona. Se prefiere `pwsh` si está y, si no, se usa el intérprete que
        está ejecutando esto (`$PSHOME`), que es el que ya sabemos que existe.
    #>
    $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($null -ne $pwsh) { return $pwsh.Source }
    return (Join-Path $PSHOME 'powershell.exe')
}
