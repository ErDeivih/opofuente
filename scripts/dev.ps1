<#
.SYNOPSIS
    Arranca API y web a la vez en desarrollo.
.DESCRIPTION
    La API se lanza en un proceso aparte; la web ocupa esta consola. Ctrl+C detiene ambos.
    Son procesos separados: el backend no empaqueta el frontend en desarrollo
    (02_ARCHITECTURE §1).
#>
[CmdletBinding()]
param()

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'common.ps1')

$apiScript = Join-Path $PSScriptRoot 'api.ps1'
# El intérprete se resuelve, no se escribe a mano: `pwsh` no está en todos los equipos (aquí no lo
# está) y `Start-Process -FilePath 'pwsh'` falla con «no se puede encontrar el archivo».
$shell = Get-OpoFuenteShell
$api = Start-Process -FilePath $shell -ArgumentList @('-NoProfile', '-File', $apiScript, '-Reload') -PassThru -WindowStyle Hidden
Write-Host "API arrancada en proceso $($api.Id)." -ForegroundColor Cyan

try {
    Push-Location $repoRoot
    try {
        Write-Host 'Web en http://127.0.0.1:5173  (Ctrl+C para detener todo)' -ForegroundColor Cyan
        npm run dev:web
    }
    finally {
        Pop-Location
    }
}
finally {
    if (-not $api.HasExited) {
        Stop-Process -Id $api.Id -Force
        Write-Host "API detenida (proceso $($api.Id))." -ForegroundColor Cyan
    }
}
