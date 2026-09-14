<#
.SYNOPSIS
    Comprueba que las herramientas necesarias están disponibles y con la versión esperada.
.DESCRIPTION
    Se ejecuta antes de instalar nada. Falla con un mensaje claro si falta algo o si la versión
    no es compatible con el stack fijado (Python 3.12, Node >= 20).
#>
[CmdletBinding()]
param(
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')

$problems = New-Object System.Collections.Generic.List[string]

function Test-Command {
    param([string]$Name, [string]$VersionArgs, [string]$Minimum, [string]$Hint)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        $problems.Add("Falta '$Name'. $Hint")
        return
    }
    $raw = (& $Name $VersionArgs 2>&1 | Select-Object -First 1)
    Write-Host ("  {0,-10} {1}" -f $Name, $raw)
}

Write-Host 'Comprobando herramientas:' -ForegroundColor Cyan
Test-Command -Name 'python' -VersionArgs '--version' -Minimum '' -Hint 'Instala Python 3.12 desde python.org.'
Test-Command -Name 'uv' -VersionArgs '--version' -Minimum '' -Hint 'Instala uv: https://docs.astral.sh/uv/'
Test-Command -Name 'node' -VersionArgs '--version' -Minimum '' -Hint 'Instala Node.js 20 o superior.'
Test-Command -Name 'npm' -VersionArgs '--version' -Minimum '' -Hint 'npm viene con Node.js.'
Test-Command -Name 'git' -VersionArgs '--version' -Minimum '' -Hint 'Instala Git para Windows.'

if (Test-Path (Join-Path $RepoRoot '.venv')) {
    Write-Host '  .venv      presente' -ForegroundColor DarkGray
}

if ($problems.Count -gt 0) {
    Write-Host ''
    Write-Host 'Requisitos no satisfechos:' -ForegroundColor Red
    $problems | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
    throw 'Faltan herramientas obligatorias.'
}

# Python debe ser 3.12.x: el proyecto fija requires-python >=3.12,<3.13.
$pythonVersion = (& python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
if ($pythonVersion -ne '3.12') {
    throw "Python $pythonVersion no es compatible: se requiere 3.12.x."
}

Write-Host ''
Write-Host 'Requisitos correctos.' -ForegroundColor Green
