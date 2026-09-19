<#
.SYNOPSIS
    Empaqueta una release local: artefactos construidos, versión, revisión de esquema y comprobaciones.

.DESCRIPTION
    Una release **local** no se publica en ningún sitio: el repositorio es privado mientras el temario
    de Guardia Civil siga dentro (DEBT-003). Lo que hace este script es dejar en `dist/release/` todo lo
    necesario para volver a levantar esta misma versión en este equipo, con un manifiesto que dice de
    dónde salió cada cosa y qué comprobaciones se ejecutaron antes de empaquetar.

    El script **no** se inventa nada: si un artefacto no está, no lo fabrica; si una comprobación no se
    ha pedido, lo dice en el manifiesto en lugar de dar por hecho que pasó.
#>
[CmdletBinding()]
param(
    [switch]$SkipChecks,
    [string]$Name = ''
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'common.ps1')

Push-Location $repoRoot
try {
    $version = (Select-String -Path 'apps/api/opofuente/__init__.py' -Pattern '__version__ = "(.*)"').Matches[0].Groups[1].Value
    $revision = (Get-ChildItem 'apps/api/alembic/versions/00*.py' |
        Select-String -Pattern '^revision = "([^"]+)"' |
        ForEach-Object { $_.Matches[0].Groups[1].Value } |
        Sort-Object |
        Select-Object -Last 1)
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    if ([string]::IsNullOrWhiteSpace($Name)) { $Name = "opofuente-$version-$stamp" }

    $releaseDir = Join-Path $repoRoot 'dist/release'
    $target = Join-Path $releaseDir $Name
    if (Test-Path $target) { Remove-Item -Recurse -Force $target }
    New-Item -ItemType Directory -Force -Path $target | Out-Null

    # 1. Artefactos ya construidos. No se construye aquí: si falta algo, se dice y se para.
    $requeridos = @(
        @{ Origen = 'dist'; Filtro = 'opofuente-*.whl'; Destino = 'backend' },
        @{ Origen = 'apps/web/dist'; Filtro = '*'; Destino = 'web' }
    )
    $faltan = @()
    foreach ($item in $requeridos) {
        $origen = Join-Path $repoRoot $item.Origen
        if (-not (Test-Path $origen)) { $faltan += $item.Origen; continue }
        $destino = Join-Path $target $item.Destino
        New-Item -ItemType Directory -Force -Path $destino | Out-Null
        if ($item.Filtro -eq '*') {
            Copy-Item -Path (Join-Path $origen '*') -Destination $destino -Recurse -Force
        }
        else {
            $ficheros = @(Get-ChildItem -Path $origen -Filter $item.Filtro)
            if ($ficheros.Count -eq 0) { $faltan += "$($item.Origen)/$($item.Filtro)"; continue }
            $ficheros | Copy-Item -Destination $destino -Force
        }
    }
    if ($faltan.Count -gt 0) {
        throw "faltan artefactos construidos: $($faltan -join ', '). Ejecuta ./scripts/build.ps1 antes."
    }

    # 2. Lockfiles y configuración de ejemplo: sin ellos la release no se puede reproducir.
    Copy-Item 'uv.lock' $target -Force
    Copy-Item 'package-lock.json' $target -Force
    Copy-Item '.env.example' $target -Force

    # 3. Las comprobaciones que se hayan pedido, con su resultado real.
    $checks = @()
    if (-not $SkipChecks) {
        Write-Host 'Ejecutando las puertas de calidad antes de empaquetar...' -ForegroundColor Cyan
        & (Join-Path $PSScriptRoot 'gates.ps1')
        $checks += "puertas de calidad: código de salida $LASTEXITCODE"
        if ($LASTEXITCODE -ne 0) { throw "las puertas no están en verde: no se empaqueta una release roja" }
    }
    else {
        $checks += 'puertas de calidad: NO ejecutadas (-SkipChecks)'
    }

    # 4. El manifiesto de la release, en texto que se puede leer sin el programa.
    $manifiesto = @(
        "# Release local de OpoFuente",
        "",
        "- nombre: $Name",
        "- versión: $version",
        "- revisión de esquema: $revision",
        "- creada: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
        "- equipo: $env:COMPUTERNAME",
        "",
        "## Contenido",
        "",
        "- `backend/`: paquete de Python construido (`wheel`).",
        "- `web/`: bundle del frontend construido (`dist/`).",
        "- `uv.lock` y `package-lock.json`: versiones exactas de las dependencias.",
        "- `.env.example`: configuración de ejemplo (sin secretos).",
        "",
        "## Comprobaciones",
        "",
        ($checks | ForEach-Object { "- $_" }),
        "",
        "## Cómo levantar esta release",
        "",
        "1. Instala las dependencias con los lockfiles de este directorio (`uv sync --locked`, `npm ci`).",
        "2. Copia `.env.example` a `.env` y ajusta lo que haga falta (la ruta de datos, si quieres otra).",
        "3. Restaura una copia de seguridad con la aplicación arrancada, o empieza de cero.",
        "",
        "El manual completo está en `docs/OPERACION.md`.",
        "",
        "## Aviso",
        "",
        "Release **local y privada**: no se publica ni se distribuye. El temario de Guardia Civil que",
        "usan los fixtures es de uso privado (DEBT-003)."
    )
    Set-Content -Path (Join-Path $target 'RELEASE.md') -Value $manifiesto -Encoding UTF8

    Write-Host "Release local creada en $target" -ForegroundColor Green
    Get-ChildItem $target | Select-Object Name, Length
}
finally {
    Pop-Location
}
