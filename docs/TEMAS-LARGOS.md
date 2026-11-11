# Temas largos reescritos

**Fecha:** 11/11/2026 · **Objetivo:** que cada tema se pueda estudiar sin abrir otro PDF, con
redacción propia y fuentes citadas.

## Los diecinueve temas

| Tema | Título | Palabras | Apartados | Test cases | Tablas | Diagrama |
|---|---|---|---|---|---|---|
| I.1 | La Constitución Española de 1978 | **1.543** | 10 | 15 | 1 | SVG de estructura |
| II.13 | Arquitectura de ordenadores | **2.692** | 10 | 15 | 1 | SVG Von Neumann |
| II.14 | Sistemas operativos de usuario | **2.082** | 10 | 15 | 6 | — |
| III.18 | Sistemas operativos de servidor | **2.485** | 10 | 15 | 6 | — |
| III.19 | Virtualización y contenedores | **2.454** | 10 | 15 | 6 | — |
| III.20 | Almacenamiento y copias | **2.850** | 10 | 15 | 1 | — |
| III.21 | Redes | **3.152** | 10 | 15 | 1 | SVG pila OSI |
| III.24 | Monitorización e incidencias | **2.608** | 10 | 15 | 1 | — |
| III.22 | Comunicaciones | **2.950** | 10 | 15 | 1 | — |
| III.23 | Servicios de red | **2.528** | 10 | 15 | 6 | — |
| IV.27 | Bases de datos relacionales | **3.006** | 12 | 14 | 2 | — |
| IV.28 | SQL | **2.481** | 10 | 15 | 1 | — |
| IV.29 | Gestores de bases de datos | **2.679** | 10 | 15 | 1 | — |
| IV.30 | Programación | **2.591** | 10 | 15 | 1 | — |
| IV.31 | Desarrollo web | **2.898** | 10 | 15 | 1 | — |
| IV.32 | Interoperabilidad | **2.782** | 10 | 15 | 1 | — |
| V.34 | Seguridad de la información | **3.064** | 12 | 13 | 5 | SVG triada CIA |
| V.35 | ENS (RD 311/2022) | **2.488** | 12 | 14 | 3 | — |
| V.39 | Administración electrónica práctica | **2.448** | 12 | 15 | 3 | — |

**Media:** 2.620 palabras por tema · **281 casos tipo test** en total (10-15 por tema) · **48 tablas**
comparativas · **4 diagramas SVG propios**.

I.1, II.13, II.14, III.18, III.19, III.20, III.21, III.22, III.23, III.24, IV.28, IV.29, IV.30, IV.31 y IV.32 se han reescrito con la **estructura definitiva de 10 apartados**: ficha oficial, epígrafes,
introducción, desarrollo por epígrafe con norma al artículo, tabla, ejemplo, trampas, resumen, test
comentado y fuentes. Los demás temas siguen la misma idea y se irán adaptando a ese formato.

## Fuentes usadas

| Tema | Fuentes principales | Citas |
|---|---|---|
| I.1 | `Bloque 1 Actualizado 2026.docx`, `Constitución española.resumen.docx` y tests de la CE | 6 entradas, con apartados y líneas del consolidado |
| III.21 | `Tema 9.docx`, `Tema 11.docx`, `Tema 12.docx`, `Bloque 4 Actualizado 2026.docx`, `Modelo.OSI.Resumen.docx`, `IEEE.802.11...docx` | 5 entradas; discrepancias entre fuentes señaladas en el texto |
| IV.27 | `Tema 5.docx`, `Tema 7.docx`, `Bloque 3 Actualizado 2026.docx` | 8 entradas |
| V.34 | `Tema 10.docx`, `Tema 14.docx`, `Bloque 4 Actualizado 2026.docx`, `temario-c1.md` | 17 entradas |
| V.35 | `Bloque 1 Actualizado 2026.docx` (ENS), `V.35.txt` y **RD 311/2022 consolidado (BOE)** | 3 entradas; el texto local era corto para categorías/auditoría |
| V.39 | `Bloque 1 Actualizado 2026.docx` (TAI I.8/I.9), `V.39.txt`, Ley 39/2015, RD 203/2021 y ENI | 4 entradas; solo artículos verificados contra BOE |

Los DOCX no tienen paginación fija: se citan por apartado. Los PDF escaneados sin texto
(`Subnetting`, `PostgreSQL`, `CCN-CERT`, `ENS.hellcito`, `Como Categorizar...`) **no se citan como
leídos**; se indica expresamente en el material cuando aplica.

## Cómo se ha verificado

- **1.500 palabras mínimas**: test del build sobre los seis `longSections`.
- **JSON válido** y schema de secciones/tablas/testCases/sources.
- **Cero copia literal**: los redactores compararon shingles de 10-12 palabras contra el consolidado;
  se reformularon las coincidencias.
- **Demo**: Playwright comprueba que la ficha larga contiene casos tipo test, fuentes y un SVG propio.
- **Rigor**: cuando dos apuntes daban cifras distintas (TCP/IP 4 vs 5 capas, 802.11ac, 802.11be), se
  atribuyen ambas; cuando el material local no llegaba (ENS), se cita la norma oficial.

## Límites y siguiente paso

- **V.35**: el apartado ENS del DOCX local es un resumen; para ámbito, categorías, Anexo II,
  Declaración de Aplicabilidad y auditoría se usó el texto consolidado del RD 311/2022. Hay una
  discrepancia detectada entre el resumen local (6 principios) y el art. 5 vigente (7): conviene
  alinear la ficha corta en otra tarea.
- **V.34**: el material local no desarrolla las cláusulas de ISO/IEC 27001/27002; el tema las sitúa y
  explica el marco de gestión, pero no inventa números de control.
- Quedan 34 temas sin desarrollo largo. Los que **no tienen fuente local suficiente** son II.15
  (Ofimática), II.17 (Licencias), IV.33 (Informes/BI), I.9 (Haciendas locales) e I.10 (Contratación);
  V.40 (Accesibilidad) solo tiene fuente parcial.
- No se han incrustado imágenes de terceros; los tres diagramas son SVG propios escritos para esta
  demo.
