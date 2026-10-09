# Guardia Civil: el material por tema, de 0 fragmentos a 1.758 (30-09-2026)

El banco de Guardia Civil tenía 240 preguntas en 25 temas, pero el **material de la biblioteca estaba a cero**:
`mapa_de_material_de_gc.py` (nuevo) midió las 25 columnas de fragmentos y **todas** daban 0, con 84 documentos
suyos en la biblioteca —temario oficial, código electrónico 599, exámenes, plantillas, foros— **ninguno mapeado**
a un nodo del programa. Y los apuntes de GC (`F:\OpoFuente\GUARDIA-CIVIL\APUNTES`, un fichero por tema) no estaban
en la aplicación.

## Lo que se ha hecho

1. **Los 25 apuntes entran en la biblioteca** como `personal_notes` y se **mapean a su nodo** del programa
   (`1 DERECHOS HUMANOS.md` → nodo `1`). Comprobado: **25 de 25** temas con material, 0 sin material.
2. **Y se arregla su texto**, porque la primera ingesta guardó **el 0,7 %**: de un apunte de 80 KB la biblioteca
   conservaba 447 caracteres en 17 fragmentos, y al mirarlos por dentro eran **solo los títulos**
   (`'# Tema 22. ARMAS Y EXPLOSIVOS'`, 29 caracteres). La causa está en el extractor de la aplicación: un `.md` se
   parte por sus `#` (`_markdown_sections`, `extractors/text_files.py:215`) y el tramo acaba guardando el título,
   mientras que un `.txt` se parte por párrafos (`_block_sections`) y conserva el cuerpo.
   Arreglo: los apuntes se reescriben como **texto plano en párrafos de 1.000 caracteres como mucho**
   (`arreglar_el_texto_de_los_apuntes_de_gc.py`), se ingieren (25 ficheros, 1,26 MB) y se añaden como **versión
   nueva del mismo documento** (no como otro apunte), y se mapea la versión nueva a su tema.

| | antes | ahora |
| --- | --- | --- |
| fragmentos de material de GC | **0** | **4.314** |
| temas con material | 0 de 25 | **25 de 25** |
| texto de los apuntes conservado | **0,7 %** | **98,2 %** |

### La segunda vuelta del texto: del 55 % al 98,2 %

Con los apuntes ya en texto plano se conservaba el **55 %**, y la causa era otra vez el recorte: un **bloque** (las
líneas seguidas sin línea en blanco entre ellas —una lista de guiones, por ejemplo) es **un** fragmento, y el
fragmento se recorta a 1.200 caracteres, así que la cola de cada lista se perdía. Arreglado agrupando las líneas en
bloques de **800 caracteres como mucho** (`AGRUPADO`): 2.556 párrafos y **98,2 %** del texto conservado.

## Las claves de 2021-2025: las tres vías, comprobadas y cerradas por ahora

Los exámenes de 2021 a 2025 **se leen enteros** (137-158 preguntas cada uno, con capa de texto), así que lo único
que falta para llevarlos al banco es su clave. Se han probado las tres vías posibles y **las tres están medidas**:

1. **Las plantillas oficiales son escaneos**: 0 caracteres extraíbles (`medir_lo_legible_de_gc.py`).
2. **Las copias de las academias se publican como imagen**, no como texto: traje cuatro páginas al material
   ([vmoposiciones](https://vmoposiciones.com/examenes-guardia-civil-pdf/),
   [Método GC](https://metodogc.com/examenes-oposiciones-guardia-civil/examen-2024/),
   [Polaris](https://www.polarisoposiciones.com/examenes-convocatorias-anteriores/guardia-civil/2024),
   [Centro Guardia Civil](https://academiacentroguardiacivil.es/plantillas-de-respuestas-disponibles-para-las-pruebas-de-guardia-civil-2024/)),
   las dejé en `internet\plantillas-con-texto` y **ninguna** trae una secuencia de pares «número letra»: 0 tramos
   con pinta de plantilla en las cuatro.
3. **El OCR de las 20 plantillas escaneadas no llega**: leídas buscando pares número+letra, la mejor
   (`GC-legacy-2024-…28_09_24`) saca **91 claves de 100** y le faltan **12 números**; las de 2021 y 2022 no pasan
   de 22-34 claves. Con 12 faltas el emparejamiento por posición se rompe y a partir de ahí todo lo que venga
   detrás queda desplazado.

**Decisión**: esos exámenes se quedan como **material** en la biblioteca (se pueden leer y estudiar) y **no entran
al banco**, porque una clave inventada es peor que una pregunta sin clave. Cuando aparezca una plantilla legible
—oficial en texto o una copia publicada como tabla—, entra sin más.

## Lo que queda, medido y sin adornos

- El **1,8 %** que no se conserva es lo que quitan las marcas de Markdown (`**`, comillas invertidas) al pasar a
  texto plano; el texto de los apuntes está entero.
- **Los exámenes de GC de 2021 a 2025 no se han metido al banco** y no es un olvido: sus preguntas se leen
  perfectamente (medido: 137–158 preguntas por examen, con capa de texto), pero **sus plantillas oficiales están
  escaneadas** (0 caracteres) y las de `vmoposiciones` son imágenes con marca de agua: solo se les extrae la marca.
  Los exámenes se han añadido a la biblioteca como material, sin mapear a tema (un examen cubre varios temas y el
  mapeo del modelo es documento → nodo: mapearlo entero a un tema sería mentir).
- **Las marcas de respuesta correcta no existen en estos PDFs**: `medir_respuestas_marcadas_en_gc.py` muestra que
  **todas** las opciones vienen en negrita (el número de opciones en negrita es igual al de opciones), así que la
  negrita no distingue nada, y no hay asteriscos ni X. La respuesta de 2021–2025 depende de las plantillas.
- **Un tema sin preguntas**: `25 LENGUA ESPAÑOLA` (0 preguntas; el resto, entre 1 y 80). Los 25 temas sí tienen
  material.

## Cómo se reproduce

```
python mapa_de_material_de_gc.py                          # 0 → 1.758 fragmentos, 25 de 25 temas con material
python apuntes_de_gc_a_la_biblioteca.py --ingerir         # los 25 apuntes (.md) como documentos
python apuntes_de_gc_a_la_biblioteca.py --aplicar         # promocionar, aceptar y mapear a su nodo
python medir_lo_que_queda_de_los_apuntes_de_gc.py         # el 0,7 % (medición del defecto)
python ver_por_dentro_un_apunte_de_gc.py --tema 22        # por qué: los fragmentos eran los títulos
python arreglar_el_texto_de_los_apuntes_de_gc.py --solo-textos --ingerir --aplicar   # el 98,2 %
python medir_lo_legible_de_gc.py                          # qué PDFs tienen texto y cuáles son escaneos
```

Salidas: `F:\OpoFuente\GUARDIA-CIVIL\internet\apuntes-en-texto` (los textos planos),
`F:\OpoFuente\GUARDIA-CIVIL\CATALOGO\{apuntes-en-la-app.json, apuntes-en-texto-en-la-app.json}`.
