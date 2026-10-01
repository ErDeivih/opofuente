<#
.SYNOPSIS
    Utilidades compartidas por los scripts de OpoFuente.
.DESCRIPTION
    Todas las rutas se resuelven desde la raíz del repositorio. Ningún script toca la carpeta de
    originales del usuario: solo `OPOFUENTE_DATA_DIR`.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Con StrictMode, leer $LASTEXITCODE antes de ejecutar ningún comando nativo fallaría. Se inicia la
# variable **global**, que es la que escriben los comandos nativos: asignarla sin ámbito dentro de un
# script que se carga con `.` crea una copia local que puede tapar a la global.
$global:LASTEXITCODE = 0

$script:OpoFuenteRepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

function Get-OpoFuenteRepoRoot {
    return $script:OpoFuenteRepoRoot
}

function Invoke-OpoFuenteStep {
    <#
    .SYNOPSIS
        Ejecuta un paso de las puertas de calidad y falla si el proceso devuelve código distinto de cero.
    .DESCRIPTION
        El 1 de octubre de 2026 una ejecución completa de `gates.ps1` imprimió «OK» en las puertas 17
        y 18 aunque sus comandos fallaron (un traceback de Python y Playwright en rojo), y no se pudo
        reproducir aislando el ayudante. Por eso el paso no se fía de una sola señal:

        - pone a cero el código **global** antes de ejecutar y lee el **global** después;
        - una excepción dentro de la acción también es un fallo (con código 1 si no hay otro);
        - el «OK» dice el código con el que se decidió, para que el registro se pueda auditar.

        Además, `Test-OpoFuenteExitCodeDetection` comprueba al empezar las puertas que este
        intérprete detecta de verdad un comando que falla.
    #>
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][scriptblock]$Action
    )

    Write-Host ''
    Write-Host "=== $Name ===" -ForegroundColor Cyan
    $global:LASTEXITCODE = 0
    $excepcion = $null
    try {
        & $Action
    }
    catch {
        $excepcion = $_
    }
    $codigo = $global:LASTEXITCODE
    if ($null -ne $excepcion) {
        Write-Host "Excepción en '$Name': $excepcion" -ForegroundColor Red
        if ($codigo -eq 0) { $codigo = 1 }
    }
    if ($codigo -ne 0) {
        Write-Host "FALLO en '$Name' (código $codigo)" -ForegroundColor Red
        exit $codigo
    }
    Write-Host "OK: $Name (código $codigo)" -ForegroundColor Green
}

function Test-OpoFuenteExitCodeDetection {
    <#
    .SYNOPSIS
        Comprueba que este intérprete ve el código de salida de un comando nativo que falla.
    .DESCRIPTION
        Si no lo ve, ninguna puerta podría fallar y todas dirían «OK». Se lanza `node` (que las
        puertas ya necesitan) con salida 3 y se exige leer 3; si no, se detiene todo antes de la
        primera puerta.
    #>
    $global:LASTEXITCODE = 0
    & node -e "process.exit(3)"
    $visto = $global:LASTEXITCODE
    $global:LASTEXITCODE = 0
    if ($visto -ne 3) {
        Write-Host ("Este intérprete no detecta el código de salida de un comando que falla " +
            "(esperado 3, visto $visto): las puertas no serían de fiar y no se ejecutan.") -ForegroundColor Red
        exit 1
    }
    Write-Host 'Comprobación previa: el intérprete detecta los fallos de los comandos (código 3 visto).' -ForegroundColor DarkGray
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
