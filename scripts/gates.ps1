<#
.SYNOPSIS
    Ejecuta TODAS las puertas de calidad en el orden de 10_TEST-PLAN §10.
.DESCRIPTION
    Orden: formato/lint -> typecheck -> unitarias -> integración -> contrato -> build ->
    migración desde cero -> siembra idempotente -> fixtures frente a las fuentes -> E2E.
    Un código distinto de cero bloquea. No se relaja ninguna configuración para que pase.

    Las puertas 17 y 18 necesitan las fuentes oficiales descargadas (`scripts/fetch-sources.ps1`),
    el temario fuente del temario común (copia `minicerebro/temario-c1.md` a
    `data/sources/temario-c1.md` o define `OPOFUENTE_TEMARIO_C1`), las fuentes de las convocatorias
    C1 (`data/sources/c1.txt` y `data/sources/convocatorias.csv`, o `OPOFUENTE_C1_LISTADO` y
    `OPOFUENTE_CONVOCATORIAS_CSV`) y el navegador de Playwright instalado
    (`npx playwright install chromium`).
.PARAMETER SkipE2e
    Omite las pruebas end-to-end (útiles cuando no hay navegador de Playwright instalado).
.EXAMPLE
    ./scripts/gates.ps1
    ./scripts/gates.ps1 -SkipE2e
#>
[CmdletBinding()]
param(
    [switch]$SkipE2e
)

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'common.ps1')

$gatesDataDir = Join-Path $repoRoot '.gates-data'
$started = Get-Date

Push-Location $repoRoot
try {
    Invoke-OpoFuenteStep -Name '1. ruff format --check' -Action { uv run ruff format --check . }
    Invoke-OpoFuenteStep -Name '2. ruff check' -Action { uv run ruff check . }
    Invoke-OpoFuenteStep -Name '3. mypy (estricto)' -Action { uv run mypy }
    Invoke-OpoFuenteStep -Name '4. eslint' -Action { npm run lint:web }
    Invoke-OpoFuenteStep -Name '5. typecheck TypeScript' -Action { npm run typecheck:web }
    Invoke-OpoFuenteStep -Name '6. pruebas unitarias backend' -Action { uv run pytest apps/api/tests/unit }
    Invoke-OpoFuenteStep -Name '7. pruebas de integración backend' -Action { uv run pytest apps/api/tests/integration }
    Invoke-OpoFuenteStep -Name '8. pruebas de contrato' -Action { uv run pytest apps/api/tests/contract }
    Invoke-OpoFuenteStep -Name '9. pruebas de componentes (Vitest)' -Action { npm run test:web }
    Invoke-OpoFuenteStep -Name '10. contrato OpenAPI y tipos sincronizados' -Action {
        uv run python -m opofuente.tools.export_openapi --check
        if ($LASTEXITCODE -ne 0) { return }
        npm run contracts:check
    }
    Invoke-OpoFuenteStep -Name '11. build backend' -Action { uv build }
    Invoke-OpoFuenteStep -Name '12. build frontend' -Action { npm run build:web }

    # Migración desde cero en un directorio de datos temporal, nunca el real.
    if (Test-Path $gatesDataDir) { Remove-Item -Recurse -Force $gatesDataDir }
    $env:OPOFUENTE_DATA_DIR = $gatesDataDir
    try {
        Invoke-OpoFuenteStep -Name "13. migración desde base vacía ($gatesDataDir)" -Action {
            uv run alembic upgrade head
        }
        # Verificación independiente del resultado: se abre el SQLite con sqlite3, sin pasar
        # por el motor de la aplicación.
        Invoke-OpoFuenteStep -Name '14. esquema migrado verificado con sqlite3' -Action {
            uv run python -c "import sqlite3,sys; from opofuente.config import get_settings; p=get_settings().data_paths.database; c=sqlite3.connect(p); rev=c.execute('select version_num from alembic_version').fetchone()[0]; rows=c.execute('select count(*) from app_metadata').fetchone()[0]; print('revision', rev, 'app_metadata', rows); sys.exit(0 if rows > 0 else 1)"
        }
        Invoke-OpoFuenteStep -Name '15. siembra de perfiles desde base vacía' -Action {
            uv run python -m opofuente.tools.seed_profiles
        }
        # Segunda ejecución: si algo cambiara, la siembra no sería idempotente.
        Invoke-OpoFuenteStep -Name '16. siembra idempotente (segunda ejecución sin cambios)' -Action {
            uv run python -m opofuente.tools.seed_profiles --check
        }
    }
    finally {
        Remove-Item Env:OPOFUENTE_DATA_DIR -ErrorAction SilentlyContinue
        if (Test-Path $gatesDataDir) { Remove-Item -Recurse -Force $gatesDataDir }
    }

    Invoke-OpoFuenteStep -Name '17. fixtures sincronizados con sus fuentes' -Action {
        # Primero el temario común y las convocatorias C1: sus fuentes son locales y no dependen de
        # las descargas del BOE. Si después fallan las de los perfiles, el motivo está en DEBT-028 y
        # así se ve que el temario y las convocatorias sí estaban sincronizados.
        uv run python -m opofuente.tools.build_curriculum_fixtures --check
        if ($LASTEXITCODE -ne 0) { return }
        uv run python -m opofuente.tools.build_c1_convocatorias_fixtures --check
        if ($LASTEXITCODE -ne 0) { return }
        uv run python -m opofuente.tools.build_profile_fixtures --check
    }

    if ($SkipE2e) {
        Write-Host ''
        Write-Host 'E2E omitido por -SkipE2e (no se declara ejecutado).' -ForegroundColor Yellow
    }
    else {
        Invoke-OpoFuenteStep -Name '18. E2E (Playwright)' -Action { npm run e2e }
    }
}
finally {
    Pop-Location
}

$elapsed = (Get-Date) - $started
Write-Host ''
Write-Host ("Todas las puertas ejecutadas en {0:mm\:ss} minutos." -f $elapsed) -ForegroundColor Green
