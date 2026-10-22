<#
.SYNOPSIS
    Instala OpoFuente en una carpeta y la deja lista para arrancar (M8).

.DESCRIPTION
    **Lo que hace, en orden, y se para en el primer fallo**:

      1. comprueba que estan `uv` y `pnpm`;
      2. crea la carpeta de datos;
      3. migra la base;
      4. importa el paquete publico, si se le da uno;
      5. crea el administrador, si estan el correo y la contrasena;
      6. dice como arrancar.

    **No arranca nada.** **Instalar y arrancar son dos cosas**: si el instalador
    dejara el servidor corriendo, cerrar la ventana lo mataria y el propietario
    no sabria si esta instalado o no.

    **Y no se despliega en ningun sitio**: no publica, no contrata, no abre
    puertos.

.PARAMETER Datos
    Donde vive la base. Por defecto `F:\OpoFuente\datos`.

.PARAMETER Paquete
    El fichero del paquete publico. Si no se da, la base se queda vacia de
    contenido y solo con el esquema.

.PARAMETER Correo
    El correo del administrador. Si no se da, no se crea cuenta.

.EXAMPLE
    .\scripts\instalar.ps1 -Paquete .\paquete.json -Correo dueno@ejemplo.test
#>
[CmdletBinding()]
param(
    [string]$Datos = 'F:\OpoFuente\datos',
    [string]$Paquete = '',
    [string]$Correo = ''
)

$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
function Decir($texto) { Write-Host "  $texto" }

Decir "instalando en $Datos"

# 1. las herramientas, antes de tocar nada: si falta una, no se crea ni una
# carpeta. Un instalador que deja medio entorno y falla al final es peor que
# uno que ni empieza.
foreach ($herramienta in @('uv', 'pnpm')) {
    if (-not (Get-Command $herramienta -ErrorAction SilentlyContinue)) {
        throw "falta ${herramienta}: instalalo y vuelve a lanzar esto"
    }
    Decir "$herramienta esta"
}

# 2. la carpeta de datos
if (-not (Test-Path $Datos)) {
    New-Item -ItemType Directory -Path $Datos -Force | Out-Null
    Decir "carpeta de datos creada"
} else {
    Decir "carpeta de datos ya existia"
}
$env:OPOFUENTE_DATA_DIR = $Datos

# 3. migrar
Push-Location $raiz
try {
    uv run alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'la migracion fallo' }
    Decir 'base migrada'
} finally {
    Pop-Location
}

# 4. el contenido publico, si hay paquete
if ($Paquete) {
    if (-not (Test-Path $Paquete)) { throw "no existe el paquete: $Paquete" }
    Push-Location (Join-Path $raiz 'apps\api')
    try {
        uv run python -m opofuente.tools.paquete_publico revisar --paquete $Paquete
        if ($LASTEXITCODE -ne 0) { throw 'el paquete lleva datos de una persona: no se importa' }
        uv run python -m opofuente.tools.paquete_publico importar --paquete $Paquete
        if ($LASTEXITCODE -ne 0) { throw 'la importacion fallo' }
        Decir 'paquete importado'
    } finally {
        Pop-Location
    }
} else {
    Decir 'sin paquete: la base queda con el esquema y sin contenido'
}

# 5. el administrador, si hay correo. La contrasena NO se pasa por argumento:
# la lee el comando del entorno, y si no esta, se niega.
if ($Correo) {
    if (-not $env:OPOFUENTE_ADMIN_PASSWORD) {
        throw 'falta OPOFUENTE_ADMIN_PASSWORD en el entorno para crear el administrador'
    }
    Push-Location (Join-Path $raiz 'apps\api')
    try {
        uv run python -m opofuente.tools.crear_administrador --correo $Correo
        if ($LASTEXITCODE -ne 0) { throw 'no se pudo crear el administrador' }
    } finally {
        Pop-Location
    }
} else {
    Decir 'sin correo: no se ha creado ninguna cuenta'
}

Write-Host ''
Decir 'instalado. Para arrancar:'
Decir "  `$env:OPOFUENTE_DATA_DIR='$Datos'"
Decir '  cd apps\api; uv run uvicorn opofuente.main:app --port 8000'
Decir '  cd apps\web; pnpm dev'


