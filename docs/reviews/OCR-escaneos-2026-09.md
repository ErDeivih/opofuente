# OCR sobre los escaneos: qué se ha probado y qué sale (23 de septiembre de 2026)

**Origen:** petición del propietario —«instala Tesseract para lo de las imágenes y pruébalo»— y el
aviso de DEBT-020, que dice que la plantilla de respuestas de Celador es un escaneo sin capa de texto.

**Material usado:** `data/sources/celador-2022-plantilla-respuestas.pdf` (2 páginas, escaneo puro: **0
caracteres** de texto nativo, comprobado con PyMuPDF). Es material oficial de un proceso selectivo,
conservado en local y sin redistribución (DEBT-003); aquí solo se mide si una máquina puede leerlo.

## Qué se instaló

- **Tesseract 5.4.0** con `winget install UB-Mannheim.TesseractOCR` (instalado sin administrador; el
  binario queda en `C:\Program Files\Tesseract-OCR\tesseract.exe`).
- **Modelo español**: `spa.traineddata` (rápido, 2,3 MB) y `spa_best.traineddata` (13,6 MB), descargados
  de `tesseract-ocr/tessdata_fast` y `tessdata_best`.
- Los modelos van a un directorio **del usuario** (`<datos>/tessdata` con los `configs` de Tesseract),
  porque `C:\Program Files` no es escribible sin administrador y Tesseract necesita ahí los idiomas
  **y** los ficheros de configuración (`tsv` entre ellos).

## Lo que se midió

| Prueba | Resultado |
|---|---|
| Texto nativo del PDF | **0 caracteres** (por eso hace falta OCR) |
| Prosa (cabecera y pie de página) | **correcta**: el OCR reproduce el título y la nota de impugnaciones palabra por palabra; verificado leyendo la imagen |
| Tabla de 77 respuestas, OCR de página completa (`--psm 6`) | **destroza** la tabla: las líneas de la rejilla se leen como caracteres («216» donde pone 16, «a» donde pone 11) |
| Tabla, OCR por columnas + emparejado por orden de línea | 47/77 (`spa`) y **53/77** (`spa_best`), **y el emparejado no es de fiar**: una línea perdida desplaza todas las siguientes sin avisar |
| Tabla, OCR celda a celda | no se pudo: `find_tables()` de PyMuPDF no detecta tablas en una imagen sin texto, y quitar la rejilla antes del OCR no llegó a buen término en esta sesión |

Y la verdad de la tabla, leída **mirando la imagen** (no por OCR), para poder puntuar:

```text
1:C  2:C  3:A  4:C  5:C  6:D  7:D  8:C  9:D 10:D 11:A 12:B 13:B 14:A 15:B 16:D 17:D 18:D 19:B
20:B 21:B 22:C 23:C 24:A 25:D 26:C 27:A 28:A 29:B 30:C 31:C 32:D 33:C 34:D 35:A 36:B 37:A 38:D 39:A
40:A 41:B 42:D 43:A 44:A 45:B 46:B 47:A 48:C 49:A 50:D 51:C 52:B 53:A 54:C 55:D 56:D 57:D 58:D 59:A
60:D 61:B 62:D 63:A 64:B 65:C 66:D 67:A 68:D 69:D 70:A 71:C 72:D 73:A 74:A 75:C 76:B 77:B
```

De las 53 que el OCR leyó con el modelo «best», **unas 48 coinciden** con lo que dice la imagen. Es
decir: **un 60-70 % de la tabla**, y sin forma de saber *cuáles* están mal sin abrir la imagen.

## Qué se concluye

1. **El OCR sirve para texto**, y eso es lo que importa para el material de estudio: apuntes
   escaneados o fotografiados se pueden leer y citar como fuentes. Es la entrada que necesita el
   dossier del tema (ADR-019).
2. **El OCR solo no lee una tabla con rejilla de forma fiable.** Con 48 de 53 aciertos y sin saber
   cuáles fallan, importar la plantilla oficial desde este escaneo sería meter respuestas falsas en el
   banco de preguntas, que es peor que no tenerlas.
3. Por eso **DEBT-020 sigue abierta** para esa clave, y ahora con la medida en la mano: o se teclea una
   vez (77 letras, con esta tabla como comprobación), o se hace un lector de tablas de verdad (detectar
   la rejilla y OCRizar cada celda), que es otro trabajo y no lo que se ha pedido aquí.
4. **Lo que sí se puede hacer ya, y es lo siguiente**: que la aplicación use Tesseract para las páginas
   **sin capa de texto**. Hoy la capacidad se declara «configurada sin verificar» y una imagen queda
   `ocr_pending` con su aviso; con el binario y el modelo instalados, esa página se puede leer.

## Cómo se repite

El método está en los guiones de comprobación usados en la sesión (fuera del repositorio, porque son
herramientas de medición, no producto): renderizar a 300-400 ppp, OCR con `-l spa`, y para tablas
recortar por columnas. Los recortes y los textos leídos quedaron en `F:\temp-opofuente\ocr-prueba`.
