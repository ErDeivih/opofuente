param([string]$Raiz = (Split-Path -Parent $PSScriptRoot))

# La puerta de codificacion: acentos rotos y marcadores de conflicto.
#
# TODO EL FICHERO ES ASCII A PROPOSITO. El `write` guarda los .ps1 en UTF-8 SIN BOM y PowerShell
# 5.1 los lee como ANSI: un `Ã` escrito aqui se convierte en `Ãƒ` y el patron de mojibake queda
# escrito roto dentro del guardia que lo busca. Por eso cada caracter especial va como [char], y
# este comentario tampoco lleva acentos.

$aT = [char]0x00C3
$aC = [char]0x00C2
$patron = ([string]$aT) + '[\x80-\xBF]|' + ([string]$aC) + '[' + [char]0x00B7 + [char]0x00AA + '-' + [char]0x00BF + ']|' + [char]0x00E2 + [char]0x20AC

$excepciones = @{
    'docs\DEBT.md' = 'los EJEMPLOS de DEBT-029, escritos a proposito'
    'docs\FASE-3-ESTUDIO-DIARIO-SPEC-PLAN-GOAL-2026-10.md' = 'describe la puerta y cita el patron'
    'docs\LA-FUSION-2537eb3-RESUELTA-2026-10.md' = 'documenta la reparacion y cita las secuencias'
    'docs\hitos\ESTADO-DE-LA-FASE-3-2026-10-20.md' = 'cuenta esta puerta y cita el mojibake como ejemplo'
}

$ficheros = @(
    Get-ChildItem $Raiz -Recurse -File -Include *.md,*.ts,*.tsx,*.py,*.json,*.css,*.ps1 -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -notmatch '\\(node_modules|\.venv|dist|\.git)\\' }
)

$malos = 0
$exceptuadas = 0

foreach ($fichero in $ficheros) {
    $relativa = $fichero.FullName.Substring($Raiz.Length).TrimStart('\')
    $lineas = @(Select-String -Path $fichero.FullName -Pattern $patron -ErrorAction SilentlyContinue)
    if ($lineas.Count -eq 0) { continue }
    if ($excepciones.ContainsKey($relativa)) {
        $exceptuadas = $exceptuadas + $lineas.Count
        Write-Host ("  exceptuadas {0} linea(s) en {1}: {2}" -f $lineas.Count, $relativa, $excepciones[$relativa])
        continue
    }
    $malos = $malos + $lineas.Count
    Write-Host ("  {0} · {1} linea(s)" -f $relativa, $lineas.Count) -ForegroundColor Red
}

$abre = ([string][char]60) * 7
$cierra = ([string][char]62) * 7
$marcadores = 0
foreach ($fichero in $ficheros) {
    foreach ($linea in @(Get-Content $fichero.FullName -ErrorAction SilentlyContinue)) {
        if ($linea.StartsWith($abre) -or $linea.StartsWith($cierra)) { $marcadores = $marcadores + 1 }
    }
}

Write-Host ("mojibake: revisados {0} ficheros de texto" -f $ficheros.Count)
if ($exceptuadas -gt 0) {
    Write-Host ("  {0} linea(s) exceptuadas en {1} fichero(s), con su motivo arriba" -f $exceptuadas, $excepciones.Count)
}

if ($malos -gt 0) {
    Write-Host ""
    Write-Host ("MOJIBAKE: {0} linea(s) con acentos rotos" -f $malos) -ForegroundColor Red
    Write-Host "Se arregla reescribiendo el fichero en UTF-8 (sin BOM, desde fuente limpia)."
    Write-Host "Nunca releyendo el roto como ANSI: eso es lo que lo produjo."
    exit 11
}

if ($marcadores -gt 0) {
    Write-Host ""
    Write-Host ("MARCADORES de conflicto: {0} linea(s)" -f $marcadores) -ForegroundColor Red
    exit 12
}

Write-Host "SIN MOJIBAKE" -ForegroundColor Green
exit 0
