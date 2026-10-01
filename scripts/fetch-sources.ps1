<#
.SYNOPSIS
    Descarga las fuentes oficiales de los perfiles y comprueba sus hashes.
.DESCRIPTION
    Los documentos se guardan en `data/sources` (ignorado por git: los originales no se versionan).
    Después se comprueban contra `fixtures/profiles/manifest.json`: si un documento cambia, el hash
    deja de coincidir y la verificación falla. Con -VerifyOnly no se descarga nada.

    Las fuentes marcadas `volatile` en el manifiesto (páginas que el servidor sirve distintas en cada
    descarga) **no se comprueban aquí**: su texto visible lo comprueba
    `uv run python -m opofuente.tools.build_profile_fixtures --check`.
.PARAMETER VerifyOnly
    Solo comprueba los ficheros ya descargados.
#>
[CmdletBinding()]
param(
    [switch]$VerifyOnly
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'common.ps1')

$sourcesDir = Join-Path $repoRoot 'data/sources'
$manifestPath = Join-Path $repoRoot 'fixtures/profiles/manifest.json'

if (-not (Test-Path $manifestPath)) { throw "Falta el manifiesto de fuentes: $manifestPath" }
$manifest = Get-Content $manifestPath -Raw -Encoding utf8 | ConvertFrom-Json

$userAgent = 'OpoFuente/0.1 (proyecto personal local; uso privado)'
$missing = @()
$mismatch = @()

Push-Location $repoRoot
try {
    if (-not $VerifyOnly) {
        New-Item -ItemType Directory -Force -Path $sourcesDir | Out-Null
        foreach ($source in $manifest.sources) {
            $target = Join-Path $repoRoot $source.local_path
            Write-Host ("Descargando {0} -> {1}" -f $source.id, $source.local_path) -ForegroundColor Cyan
            try {
                Invoke-WebRequest -Uri $source.retrieved_url -UserAgent $userAgent -TimeoutSec 120 `
                    -MaximumRedirection 10 -OutFile $target -ErrorAction Stop
            }
            catch {
                Write-Host ("  FALLO al descargar: {0}" -f $_.Exception.Message) -ForegroundColor Red
            }
        }
    }

    foreach ($source in $manifest.sources) {
        $target = Join-Path $repoRoot $source.local_path
        if (-not (Test-Path $target)) {
            $missing += $source.id
            continue
        }
        $hash = (Get-FileHash $target -Algorithm SHA256).Hash.ToLower()
        # Con StrictMode, leer una propiedad que no está en el JSON es un error: se pregunta antes.
        $propiedadVolatile = $source.PSObject.Properties['volatile']
        $esVolatil = $null -ne $propiedadVolatile -and $propiedadVolatile.Value
        if ($esVolatil) {
            # El servidor sirve esta página distinta en cada descarga (identificadores que el gestor
            # de contenidos inventa al renderizar), así que su `sha256` de bytes no puede coincidir
            # nunca. Se verifica por su **texto visible**: de eso se encarga la herramienta, y aquí
            # solo se dice para que nadie lo lea como un fallo.
            Write-Host ("  TEXT {0,-28} se compara por su texto, no por sus bytes" -f $source.id) -ForegroundColor DarkGray
        }
        elseif ($hash -ne $source.sha256) {
            $mismatch += ("{0}: {1} != {2}" -f $source.id, $hash.Substring(0, 12), $source.sha256.Substring(0, 12))
        }
        else {
            Write-Host ("  OK {0,-28} {1}" -f $source.id, $hash.Substring(0, 12)) -ForegroundColor Green
        }
    }

    if ($missing.Count -gt 0) {
        Write-Host ''
        Write-Host 'Faltan documentos descargados:' -ForegroundColor Red
        $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
        throw 'Faltan fuentes oficiales.'
    }

    if ($mismatch.Count -gt 0) {
        Write-Host ''
        Write-Host 'Los documentos descargados no coinciden con el manifiesto:' -ForegroundColor Red
        $mismatch | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
        Write-Host 'Si la fuente oficial ha cambiado, hay que revisar los fixtures y actualizar el manifiesto.' -ForegroundColor Yellow
        throw 'Hash de fuente oficial distinto al registrado.'
    }

    Write-Host ''
    Write-Host 'Fuentes oficiales verificadas.' -ForegroundColor Green
    Write-Host 'Siguiente paso: uv run python -m opofuente.tools.build_profile_fixtures'
}
finally {
    Pop-Location
}
