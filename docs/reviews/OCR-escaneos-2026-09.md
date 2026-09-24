# OCR sobre los escaneos: qué se ha probado y qué sale (23 de septiembre de 2026)

**Origen:** petición del propietario —«instala Tesseract para lo de las imágenes y pruébalo»— y el
aviso de DEBT-020, que dice que la plantilla de respuestas de Celador es un escaneo sin capa de texto.

**Material usado:** `data/sources/celador-2022-plantilla-respuestas.pdf` (2 páginas, escaneo puro: **0
caracteres** de texto nativo, comprobado con PyMuPDF). Es material oficial de un proceso selectivo,
conservado en local y sin redistribución (DEBT-003); aquí solo se mide si una máquina puede leerlo.

## Qué se instaló, y dónde

- **Tesseract 5.4.0** (`winget install UB-Mannheim.TesseractOCR`), sin administrador. El binario queda
  en `C:\Program Files\Tesseract-OCR\tesseract.exe` y ese directorio **no es escribible** por el
  usuario (comprobado: copiar un modelo dentro da «Acceso denegado»).
- **Modelos de idioma** en `%LOCALAPPDATA%\OpoFuente\tessdata`: los que trae la instalación (`eng`,
  `osd`) **copiados tal cual** —mismo SHA-256, comprobado— más `spa.traineddata`. También se copian
  `configs\` y `tessconfigs\`, que es lo que hace falta para salidas como `tsv`.
- El `spa.traineddata` instalado es **byte a byte** el oficial de `tesseract-ocr/tessdata`
  (`sha256 0b0fcbb4665189e01ab8019e591f014dd7260460de072543edd4b2cb4ede7c96`, 18 256 019 bytes): se
  descargó y se comparó el hash. Los otros dos modelos oficiales se descargaron solo para medir:
  `tessdata_fast` (2 294 433 bytes) y `tessdata_best` (13 570 187 bytes); el rápido se conserva en el
  directorio como `spa_fast.traineddata` para poder pedirlo por nombre.
- La aplicación **resuelve ese directorio sola** si no se configura otro (`default_tessdata` en
  `infrastructure/ocr.py`), y lo dice en el informe de capacidades; si se quiere otro sitio,
  `OPOFUENTE_TESSERACT_TESSDATA`.

## Lo que se midió

| Prueba | Resultado |
|---|---|
| Texto nativo del PDF | **0 caracteres** (por eso hace falta OCR) |
| Prosa (cabecera, nota de impugnaciones, pie) | **correcta**: el título, el plazo de impugnaciones y el pie salen palabra por palabra, con acentos |
| Tabla de 77 respuestas, página entera a 300 ppp, modelo oficial `tessdata` | **76 de 77 leídas y 76 correctas**: 0 mal leídas, 1 sin leer (la 75) |
| La misma tabla, modelo `tessdata_best` (13,6 MB) | 72 leídas, 72 correctas, 5 sin leer (5, 30, 33, 48, 65) |
| La misma tabla, modelo `tessdata_fast` (2,3 MB) | 63 leídas, 62 correctas (la 1 sale «A» y es «C»), 14 sin leer |
| La misma tabla a **400 ppp** en vez de 300 | **peor**: el modelo oficial baja a 70 leídas y 2 mal; el «best» sube a 75 leídas y 1 mal |
| Tabla con rejilla, OCR de página completa con `--psm 6` | **destroza** la tabla: las líneas de la rejilla se leen como caracteres («216» donde pone 16) |

El recuento de aciertos se hace normalizando las confusiones de glifo que el propio OCR comete dentro
del alfabeto de la tabla (`€`→`C`, `S`/`4`→`A`…). Es una transformación declarada, no un ajuste a
medida: sin ella el modelo oficial daría 4 «errores» que son la misma letra mal dibujada. **El dato que
no depende de ninguna normalización es el otro: 1 respuesta de 77 no se lee.**

## La clave de respuestas, verificada mirando la imagen

La primera transcripción a mano de esta sesión tenía **dos errores**: daba 46:B y 57:D cuando la
plantilla dice 46:D y 57:C. Se descubrieron al comparar la puntuación con lo que leía el OCR y **mirar
el recorte de esas dos filas**: el OCR tenía razón y la transcripción no. Es exactamente el error que la
regla «no inventar datos» existe para cazar, y por eso la clave se ha re-verificado entera leyendo los
77 pares en cuatro rejillas de recortes (`F:\temp-opofuente\ocr-prueba\rejilla\rejilla-1..4.png`), con
la geometría de cada fila dada por Tesseract y **la letra leída a ojo**.

```text
1:C  2:C  3:A  4:C  5:C  6:D  7:D  8:C  9:D 10:D 11:A 12:B 13:B 14:A 15:B 16:D 17:D 18:D 19:B
20:B 21:B 22:C 23:C 24:A 25:D 26:C 27:A 28:A 29:B 30:C 31:C 32:D 33:C 34:D 35:A 36:B 37:A 38:D 39:A
40:A 41:B 42:D 43:A 44:A 45:B 46:D 47:A 48:C 49:A 50:D 51:C 52:B 53:A 54:C 55:D 56:D 57:C 58:D 59:A
60:D 61:B 62:D 63:A 64:B 65:C 66:D 67:A 68:D 69:D 70:A 71:C 72:D 73:A 74:A 75:C 76:B 77:B
```

La medición anterior de esta misma sesión («unas 53 de 77, y sin saber cuáles están mal») queda
**superada**: estaba hecha con el modelo rápido, con un emparejado por líneas que se desplazaba sin
avisar y contra la clave errónea. Con el método de esta página, la tabla se lee prácticamente entera.

## Qué se concluye

1. **El OCR sirve para texto**, y es lo que importa para el material de estudio: apuntes escaneados o
   fotografiados se pueden leer y citar como fuentes. Es la entrada que necesita el dossier del tema
   (ADR-019), y desde S03 la aplicación ya lo hace: un PDF sin capa de texto o una imagen se OCRizan
   **solo si la sonda pasa**, y el resultado se guarda como representación `ocr`, aparte del texto
   nativo, con su aviso y su calidad `ocr_unreviewed`.
2. **La tabla también se lee, pero no entera y no sola.** 76 de 77 con el modelo oficial a 300 ppp es
   un resultado excelente para *proponer* una clave; no es un resultado para **importarla sin mirarla**,
   porque la que falta (la 75) no avisa de que falta dentro de una tabla de 77 filas, y un fallo
   silencioso sería una respuesta falsa en el banco de preguntas.
3. Por eso la decisión para DEBT-020 es: **si se importa la plantilla desde el escaneo, entra como
   propuesta a revisar, nunca como verdad**; y la vía manual (teclear 77 letras contra la clave de esta
   página) sigue siendo la de verdad. Lo que **no** se hace es importar automáticamente en silencio.
4. **La mejor configuración medida es la que usa la aplicación**: modelo oficial `tessdata` del
   usuario, 300 ppp. Subir a 400 ppp empeora el resultado, así que la resolución por defecto del
   adaptador (`DEFAULT_DPI = 300`) no es una elección arbitraria.
5. **Un detalle que corrige lo que se creía:** el nombre del fichero no dice qué modelo es. El
   `spa.traineddata` que se había instalado al principio era el de `tessdata_fast` (el «rápido»), que es
   el que peor lee esta tabla; el binario elige por **nombre de fichero**, no por contenido, así que
   tener el modelo equivocado bajo el nombre correcto es un fallo silencioso. Ahora el fichero instalado
   es el oficial completo y el rápido se conserva aparte, como `spa_fast.traineddata`.

## Cómo se repite

Los guiones de medición viven **fuera del repositorio** (`F:\temp-opofuente\`), porque son herramientas
de medición, no producto:

| Guion | Qué hace |
|---|---|
| `comparar_modelos_ocr.py` | Renderiza la página 1 a 300/400 ppp, OCRiza con cada modelo y puntúa contra la clave verificada |
| `detallar_errores_ocr.py` | Dice **qué** preguntas falla cada modelo (no solo cuántas) |
| `rejilla_respuestas.py` | Construye las cuatro rejillas con las 77 filas recortadas, para leer la clave a ojo |
| `probar_ocr_app.py` | Pasa el escaneo real y el sintético por el **adaptador de la aplicación** y enseña tipo, estado, avisos, páginas y texto |
| `comprobar_codificacion.py` | Comprueba en qué codificación escribe Tesseract en stdout (UTF-8, verificado) |

Y la prueba automática que queda en el repositorio: `apps/api/tests/unit/test_ocr.py` (sonda, comandos,
páginas y fallos, con un runner inyectado) más dos pruebas que **ejecutan el binario de verdad** sobre
una imagen y un PDF sintéticos legibles; se saltan si el equipo no tiene Tesseract con español, y en
este equipo **se ejecutan**.
