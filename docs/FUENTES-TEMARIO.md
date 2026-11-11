# Inventario de fuentes del temario

**Fecha:** 11/11/2026 · **Objetivo:** localizar material local suficiente para reescribir temas largos
(1.500-3.000 palabras) sin copiar y con fuentes citables.

## Método de extracción

- Recorridas las carpetas indicadas por David (`1. TAI_2026`, `Apuntes TAI`, `BLOQUE 1` a `BLOQUE 4`,
  `data/sources` y los PDF de Descargas ya copiados).
- Extracción con **PyMuPDF** (`fitz`) para PDF y **python-docx** para DOCX; texto guardado en
  `data/fuentes/_raw/` (ignorado por git) y consolidado por tema en `data/fuentes/<tema>.txt`.
- **147 ficheros** procesados, **1.587.965 caracteres** extraídos. **100 ficheros no tienen capa de
  texto** (0-500 caracteres): son PDF escaneados o imagen; no se han inventado citas de páginas que no
  se pueden leer. Se pueden OCRizar más adelante si hace falta.
- Los DOCX no tienen paginación fija: se citan como «DOCX, apartado X». Los PDF conservan marcadores
  `===== PÁGINA N =====` para citar página exacta.

## Carpetas y volumen

| Carpeta | Ficheros | Formato | Tipo de material |
|---|---|---|---|
| `1. TAI_2026` | 7 | DOCX + PDF | Temario completo TAI por bloques, actualizado 2026 |
| `Apuntes TAI` | 92 | DOCX + PDF | Temario TAI (Temas 1-14 y bloques I-IV), tests, supuestos, esquemas, resúmenes |
| `BLOQUE 1` | 7 | DOCX + PDF | Constitución, ENS, firma electrónica, catálogo de servicios |
| `BLOQUE 2` | 2 | DOCX + PDF | Algoritmos y preguntas de bloque II |
| `BLOQUE 3` | 2 | PDF | Patrones GoF y preguntas de bloque III (escaneados) |
| `BLOQUE 4` | 22 | DOCX + PDF | Supuestos prácticos, OSI, subnetting, CPD, CCN-CERT, Wi-Fi |
| `data/sources` | 15 | PDF + MD | BOE TAI, temario C1, PDFs de CAP y exámenes de otros cuerpos |

## Los 6 temas con más peso y mejores fuentes

Selección por volumen de fuente útil y peso en el examen: **Constitución**, **Redes**, **Bases de
datos**, **Seguridad de la información** y **ENS**.

| Tema | Ficheros disponibles | Páginas / tamaño | Tipo | Uso |
|---|---|---|---|---|
| **I.1 Constitución** | `Bloque 1 Actualizado 2026.docx` | DOCX, 168.022 caracteres | Apuntes completos TAI I.1 | Base del desarrollo |
| I.1 | `Constitución española.resumen.docx` | DOCX, 4.405 caracteres | Resumen | Estructura y repaso |
| I.1 | `TEST REPASO CE COMPLETA 2020.docx` | DOCX, 35.651 caracteres | Test | Preguntas y datos |
| I.1 | `TEST TITULO VII CE SIN SOLUCIONARIO.docx` | DOCX, 21.730 caracteres | Test | Preguntas |
| I.1 | `TEST ART. 1-52 INDIST SIN SOLUCIONARIO.docx` | DOCX, 29.118 caracteres | Test | Preguntas |
| I.1 | `Examenes.pdf`, `CE (Bloque 1).pdf`, `TAI - Bloque I - Temas.pdf` | 100, 52 y 98 pág. | Exámenes/apuntes | **Escaneados, sin texto**; no citados |
| **III.21 Redes** | `Tema 9.docx` | DOCX, 79.467 caracteres | Apuntes de redes | Administración, dispositivos, LAN |
| III.21 | `Tema 11.docx` | DOCX, 45.840 caracteres | Apuntes de comunicaciones | Medios, transmisión |
| III.21 | `Tema 12.docx` | DOCX, 26.942 caracteres | Apuntes OSI/TCP-IP | Modelo de capas |
| III.21 | `Bloque 4 Actualizado 2026.docx` | DOCX, 60.736 caracteres | Apuntes TAI IV | Redes locales, OSI |
| III.21 | `Modelo.OSI.Resumen.docx` | DOCX, 3.040 caracteres | Esquema | Repaso |
| III.21 | `IEEE.802.11.y.Wifi.Estandares.docx` | DOCX, 3.810 caracteres | Apuntes Wi-Fi | Estándares |
| III.21 | `Subnetting.pdf`, `Libro subnetting TRADUCIDO.pdf` | 15 y 57 pág. | Supuestos | **Escaneados**; no citados |
| **IV.27 Bases de datos** | `Tema 5.docx` | DOCX, 42.806 caracteres | Apuntes SGBD | Modelo relacional, ACID, NoSQL |
| IV.27 | `Tema 7.docx` | DOCX, 50.391 caracteres | Apuntes SGBD/backup | SGBD, seguridad, copias |
| IV.27 | `Bloque 3 Actualizado 2026.docx` | DOCX, 122.784 caracteres | Apuntes TAI III | Diseño, normalización |
| IV.27 | `PostgreSQL...pdf`, `PASO DE E-r...pdf`, `Supuesto Base de Datos.pdf` | 213, 1 y 3 pág. | Manual/supuesto | **Escaneados**; no citados |
| **V.34 Seguridad** | `Tema 10.docx` | DOCX, 97.394 caracteres | Apuntes SSI | CIA, amenazas, controles |
| V.34 | `Tema 14.docx` | DOCX, 69.204 caracteres | Apuntes seguridad de red | Perímetro, IDS/IPS, VPN |
| V.34 | `Bloque 4 Actualizado 2026.docx` | DOCX, 60.736 caracteres | Apuntes TAI IV | Seguridad, incidentes |
| V.34 | `Examenes.pdf`, `Seguridad.CCN-CERT.pdf`, `CCN-CERT - Soluciones.pdf` | 100, 2 y 2 pág. | Exámenes/fichas | **Escaneados**; no citados |
| **V.35 ENS** | `Bloque 1 Actualizado 2026.docx` | DOCX, 168.022 caracteres | Apuntes TAI I.8 | ENS, categorías, medidas |
| V.35 | `ENS.hellcito.pdf` | 3 pág. | Esquema | **Escaneado**; no citado |
| V.35 | `Como Categorizar un Sistema en el ENS_V.04.pdf` | 7 pág. | Guía | **Escaneado**; no citado |
| V.35 | `Catalogo-servicios-administracion-digital-version-2018.pdf` | 103 pág. | Catálogo | **Escaneado**; no citado |
| **V.39 Administración electrónica** | `Bloque 1 Actualizado 2026.docx` | DOCX, 168.022 caracteres | Apuntes TAI I.8/I.9 | Sede, registro, notificaciones, ENI |
| V.39 | Ley 39/2015, RD 203/2021 y ENI (BOE) | Normas consolidadas | Normativa | Contraste de artículos verificados |

## Fuentes por tema y estado

| Cobertura | Temas |
|---|---|
| **Fuente suficiente para tema largo** | I.1, III.21, IV.27, V.34, V.35; también I.2, I.3, I.4, I.5, I.11, I.12, II.13, II.14, II.16, III.18, III.19, III.20, III.22, III.23, III.24, III.25, III.26, IV.28, IV.29, IV.30, IV.31, IV.32, V.36, V.37, V.38, V.39 (TAI cubre la mayor parte) |
| **Fuente parcial** | I.6 (firma/identidad: TAI I.6, pero ENS/firma escaneados), I.7 (protección de datos: TAI I.7), I.8 (función pública local: solo TREBEP estatal), III.18/III.24 (TAI IV.1/IV.5 parcial), V.40 (accesibilidad: TAI III.8, poca extensión) |
| **Sin fuente directa suficiente** | **II.15 Ofimática**, **II.17 Licencias y software libre**, **IV.33 Informes/BI**, **I.9 Haciendas locales**, **I.10 Contratación pública** |

### Temas que no se deben reescribir todavía

1. **II.15 Ofimática**: no hay un tema TAI equivalente; solo referencias sueltas. Habría que usar
   documentación oficial de LibreOffice/Microsoft, no los apuntes locales.
2. **II.17 Licencias**: no hay material local específico; hay que partir de fuentes oficiales
   (OSI, SPDX, EUPL) y del texto legal.
3. **IV.33 Informes y BI**: no existe tema TAI; el material local no cubre BI con profundidad.
4. **I.9 Haciendas locales** e **I.10 Contratación**: el TAI estatal no contiene Haciendas locales ni
   la Ley 9/2017 con detalle; harían falta bases y manuales específicos.
5. **V.40 Accesibilidad**: TAI III.8 la menciona, pero no hay un texto extenso local; completar con
   WCAG/EN 301 549.

## Ficheros de trabajo

- `data/fuentes/I.1.txt` (257.073 caracteres consolidados)
- `data/fuentes/III.21.txt` (220.285)
- `data/fuentes/IV.27.txt` (216.321)
- `data/fuentes/V.34.txt` (227.669)
- `data/fuentes/V.35.txt` (168.260)

Estos ficheros son material de trabajo **interno** (derechos de terceros): no se publican ni se
commitean. La demo publicada seguirá usando redacción propia y citas de fuente oficial.

## Resultado

Los seis temas elegidos se han reescrito y están en [TEMAS-LARGOS.md](TEMAS-LARGOS.md): 2.448-3.064 palabras por tema, 85 casos tipo test, 30 tablas y 3 SVG propios.
