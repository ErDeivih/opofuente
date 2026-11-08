# Capturas del temario — revisión visual

Capturas generadas por la prueba de extremo a extremo `apps/web/tests/e2e/temario.spec.ts` el
**8 de noviembre de 2026**, contra la base sintética de la suite (`.e2e-data`), nunca contra datos
reales ni contra el corpus del propietario.

Se regeneran con la variable de capturas apuntando a esta carpeta desde la raíz del repositorio:

```powershell
$env:OPOFUENTE_CAPTURAS_DIR = (Join-Path (Get-Location) 'docs/capturas')
./scripts/e2e.ps1        # las 52 pruebas; las capturas del temario quedan aquí
```

| Fichero | Qué enseña |
|---|---|
| `temario-indice-390.png` | índice del temario a 390×844: 5 bloques, 40 temas, búsqueda y avance |
| `temario-indice-1280.png` | el mismo índice en escritorio a 1280×900 |
| `temario-ficha-390.png` | ficha del tema 1 a 390×844: apuntes, preguntas, las 12 convocatorias C1 y la referencia del TAI, con sus enlaces oficiales |
| `temario-ficha-1280.png` | la misma ficha en escritorio a 1280×900 |

La prueba comprueba, con esas mismas vistas, que `scrollWidth` no supera el ancho de la ventana
(cero scroll horizontal) y que el número de enlaces oficiales de la ficha coincide con las
apariciones que devuelve la API.
