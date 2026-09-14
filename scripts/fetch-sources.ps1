<#
.SYNOPSIS
    Descarga las fuentes oficiales de los perfiles y comprueba sus hashes.
.DESCRIPTION
    Los documentos se guardan en `data/sources` (ignorado por git: los originales no se versionan).
    Después se comprueban contra `fixtures/profiles/manifest.json`: si un documento cambia, el hash
    deja de coincidir y la verificación falla. Con -VerifyOnly no se descarga nada.
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
        if ($hash -ne $source.sha256) {
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
