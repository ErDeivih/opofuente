# OpoFuente — ingestión, clasificación y deduplicación

## 1. Objetivo

Aceptar material desordenado sin exigir preparación previa y producir una biblioteca revisable. La
prioridad es no perder datos ni fabricar certeza: cada resultado debe poder explicarse, corregirse y
reproducirse.

## 2. Fuentes de entrada

### Carpeta/archivo local

Dos pasos separados:

1. **Inventario en lectura:** recorre, cuenta y toma metadatos; no copia.
2. **Importación confirmada:** copia a `data/tmp`, calcula SHA-256 en streaming y mueve atómicamente al
   almacén por hash.

No seguir enlaces simbólicos/junctions fuera de la raíz seleccionada. Registrar bucles y permisos
denegados como incidencias. Ignorar por defecto archivos ocultos del sistema, temporales Office,
ejecutables y directorios configurables (`node_modules`, `.git`, caches), mostrándolos en el resumen.

### Texto pegado

El usuario elige pista opcional: documento, preguntas o auto. Se crea un artefacto UTF-8 con origen
`paste`; el texto original permanece disponible.

### URL

Solo `http/https`, con protección SSRF: bloquear localhost, redes privadas, link-local, esquemas no
seguros y redirecciones a destinos bloqueados. Límite de tamaño, tiempo y redirecciones. Guardar URL
inicial/final, cabeceras relevantes y fecha. No eludir autenticación, paywalls, robots ni controles.

### ZIP

No ejecutar. Rechazar rutas absolutas, `..`, enlaces y ratios/tamaños de expansión peligrosos. Extraer
a temporal aislado y tratar cada miembro como ítem.

## 3. Formatos MVP

| Formato | Extracción | Notas |
|---|---|---|
| PDF | PyMuPDF | conservar páginas y coordenadas; detectar escaneado |
| DOCX | python-docx | párrafos, títulos y tablas; nunca macros |
| TXT/MD | decodificación segura | detectar UTF-8/Windows-1252 con aviso |
| HTML | BeautifulSoup/lxml | eliminar scripts, estilos y navegación repetida |
| CSV | asistente de columnas | delimitador/codificación/previsualización |
| JSON | esquema flexible guiado | límites de profundidad y tamaño |
| PNG/JPEG | metadatos + OCR opcional | original siempre conservado |
| Anki (`.apkg`, `.colpkg`) | lectura de la colección (SQLite, zstd desde Anki 2.1.50) | una tarjeta por tramo, con los nombres de campo de la baraja; la media **no** se extrae y se avisa (ADR-016) |

Archivos Office con macros, audio, vídeo, EPUB y PPTX quedan `unsupported_preserved`: se conservan
íntegros en el almacén, **sin ejecutar ni extraer** nada de ellos.

Un `.apkg` es un contenedor ZIP, pero **no se expande** como un ZIP: si se expandiera entrarían como
entradas sueltas la colección (un SQLite ilegible) y las imágenes de la baraja, y las tarjetas se
perderían. Se reconoce por el contenido —la colección dentro— y tiene su propio extractor.

Los ejecutables y bibliotecas (`.exe`, `.dll`, `.msi`, `.bat`, `.cmd`, `.com`, `.scr`, `.ps1`,
`.jar`, `.so`, `.dylib`) **no** se conservan: se omiten por seguridad, como dice §2. OpoFuente no
necesita el binario para estudiar y nunca lo va a ejecutar, así que guardarlo solo añade superficie
y ruido. La omisión se registra como incidencia con su motivo, nunca en silencio.

## 4. Máquina de estados del ítem

```text
discovered -> inventoried -> copied -> hashed -> extracted
          -> classified -> review_pending -> accepted -> indexed
                                    |             |
                                    v             v
                                 rejected     needs_review

Desde cualquier paso: failed | cancelled
```

Reintentar continúa desde el último artefacto válido. `cancelled` conserva informe y artefactos ya
referenciados; el usuario decide después si descarta el lote.

## 5. Extracción y calidad

### PDF

- extraer por página;
- medir caracteres útiles, proporción de símbolos y repetición;
- detectar cabecera/pie repetidos sin borrarlos del original;
- si una página no alcanza calidad, marcar `ocr_candidate`;
- OCR solo si está configurado y el usuario lo inicia/acepta;
- conservar texto nativo y OCR como representaciones diferentes;
- no fusionarlos sin trazabilidad.

### Estructura

El parser intenta conservar título, encabezados, listas, tablas, artículos, páginas y bloques de
preguntas. Los offsets siempre refieren al texto de una representación concreta.

### Calidad

Estados: `good`, `usable_with_warnings`, `ocr_unreviewed`, `poor`, `failed`. Una representación `poor`
no entra en RAG por defecto.

## 6. Detección del tipo documental

Orden de decisión:

1. identificadores oficiales y plantillas deterministas;
2. estructura: densidad de preguntas/opciones, títulos, artículos, tabla de respuestas;
3. vocabulario y entidades;
4. similitud con ejemplos confirmados;
5. clasificador LLM opcional con salida JSON validada.

Tipos:

`convocation`, `curriculum`, `law_or_regulation`, `official_technical`, `private_syllabus`,
`personal_notes`, `official_exam`, `answer_key`, `private_question_bank`, `practical_case`,
`flashcards`, `community_material`, `unknown`.

El LLM recibe fragmentos mínimos representativos, no el documento completo salvo confirmación. Su
respuesta no modifica entidades críticas directamente; crea propuestas.

## 7. Clasificación temática

Para cada perfil activo:

1. recuperar nodos candidatos por coincidencia de títulos/entidades;
2. buscar similitud contra descripciones oficiales del programa;
3. evaluar fragmentos representativos;
4. proponer hasta tres nodos con explicación;
5. permitir `transversal` y múltiples asignaciones;
6. registrar que un documento solo cubre parcialmente un tema.

No forzar cada elemento dentro de TAI o GC. `shared`, `unassigned` y `out_of_scope` son resultados
válidos.

## 8. Confianza y revisión

No fijar umbrales antes del conjunto etiquetado. El diseño admite tres bandas configuradas y calibradas:

- alta/bajo riesgo: `auto_applied_provisional`, visible y reversible;
- media: cola de revisión con alternativas;
- baja/conflicto: sin asignar.

Siempre requieren confirmación explícita:

- autoridad oficial;
- respuesta correcta;
- anulación;
- relación `supersedes`;
- derechos de reutilización;
- publicación de un derivado generado.

La revisión en lote agrupa por regla, carpeta, tipo y etiqueta propuesta. Antes de aceptar muestra
muestra aleatoria y excepciones. El usuario puede excluir elementos y deshacer todo el lote.

## 9. Deduplicación

### Exacta

SHA-256 sobre bytes. Un artefacto, múltiples orígenes. Precisión esperada 100 %.

### Mismo contenido, codificación/maquetación diferente

Hash de texto normalizado por representación. Se propone como `same_text`; no se borra ninguno porque
puede cambiar paginación/citación.

### Casi duplicado documental

MinHash/SimHash o similitud por secciones, más metadatos. Resultado es `DuplicateCluster` con relación
`revision_candidate`, `subset`, `superset` o `similar`. Confirmación humana antes de establecer versión.

### Preguntas

Normalizar sin numeración ni etiquetas, pero conservar negaciones y puntuación significativa. Comparar
enunciado, conjunto de opciones y equivalencia con opciones reordenadas. Una similitud alta solo crea
cluster; no fusiona automáticamente claves o explicaciones.

## 10. Parseo de preguntas

Pipeline:

1. detectar bloques de enunciado/opciones;
2. conservar página/posición;
3. inferir tipo de pregunta;
4. detectar número, reserva, modelo y parte;
5. crear pregunta sin clave si esta no está en el mismo artefacto;
6. parsear plantillas como documento independiente;
7. proponer alineación mediante número/modelo/huella de opciones;
8. mostrar previsualización y conflictos;
9. confirmar set y clave.

El importador CSV permite mapear columnas: `stem`, `option_a..`, `correct`, `explanation`, `topic`,
`source`, `tags`. No interpreta fórmulas. Exporta filas rechazadas con causa.

## 11. Lotes e informe

Contadores obligatorios y mutuamente explicados:

- descubiertos;
- omitidos por política;
- copiados nuevos;
- artefactos exactos existentes;
- extraídos buenos/con avisos/fallidos;
- propuestas por estado;
- preguntas creadas/incompletas/conflictivas;
- pendientes de revisión;
- cancelados.

El informe enlaza cada cifra a sus elementos y se exporta en JSON/CSV.

## 12. Prueba de aceptación con datos reales

Antes de importar todo TAI:

- crear copia de 20–50 archivos;
- manifestar manualmente tipo, tema y duplicados esperados;
- calcular precisión/recall por etiquetas críticas;
- medir minutos de revisión;
- corregir reglas;
- repetir sin limpiar manualmente la base.

No declarar éxito basándose solo en fixtures sintéticos.

