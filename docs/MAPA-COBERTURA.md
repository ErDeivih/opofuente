# Mapa de cobertura del temario

**Publicado en la demo:** <https://erdeivih.github.io/opofuente-demo/#/cobertura> · **Verificado:**
35/35 comprobaciones (10/11/2026). La tabla cuenta **solo el contenido propio publicado**; el
material de academia o de terceros es referencia interna y no suma cobertura (decisión D-034).

## Resumen

| Bloque | Temas | Apuntes completos | Solo resumen | Pendientes | Con práctica |
|---|---|---|---|---|---|
| I · Administración y normativa | 12 | 11 | 0 | 1 | 11 |
| II · Informática básica y ofimática | 5 | 1 | 0 | 4 | 1 |
| III · Sistemas, redes y comunicaciones | 9 | 4 | 0 | 5 | 4 |
| IV · Datos y desarrollo | 7 | 1 | 0 | 6 | 1 |
| V · Seguridad y administración electrónica | 7 | 2 | 0 | 5 | 2 |
| **Total** | **40** | **19** | **0** | **21** | **19** |

Temas completos: I.1, I.2, I.3, I.4, I.5, I.6, I.7, I.8, I.9, I.10, I.12, II.13, III.19, III.20, III.21, III.24, IV.27, V.34, V.35. Los últimos incorporados son **III.19 Virtualización
y contenedores** (Docker) y **IV.27 Bases de datos relacionales** (PostgreSQL).

## Los 40 temas

| Tema | Título | Apuntes | Práctica |
|---|---|---|---|
| I.1 | La Constitución Española de 1978 | Completos | Con práctica |
| I.2 | La Unión Europea | Completos | Con práctica |
| I.3 | El régimen local | Completos | Con práctica |
| I.4 | Organización municipal | Completos | Con práctica |
| I.5 | El procedimiento administrativo (Ley 39/2015) | Completos | Con práctica |
| I.6 | El régimen jurídico del sector público (Ley 40/2015) | Completos | Con práctica |
| I.7 | El personal al servicio de las administraciones (TREBEP) | Completos | Con práctica |
| I.8 | La función pública local | Completos | Con práctica |
| I.9 | Las haciendas locales y el presupuesto | Completos | Con práctica |
| I.10 | La contratación del sector público (Ley 9/2017) | Completos | Con práctica |
| I.11 | Igualdad y violencia de género | Pendiente | Pendiente |
| I.12 | Transparencia y protección de datos en la Administración | Completos | Con práctica |
| II.13 | Arquitectura de ordenadores | Completos | Con práctica |
| II.14 | Sistemas operativos de usuario | Pendiente | Pendiente |
| II.15 | Ofimática | Pendiente | Pendiente |
| II.16 | Correo electrónico y colaboración | Pendiente | Pendiente |
| II.17 | Licencias y software libre | Pendiente | Pendiente |
| III.18 | Sistemas operativos de servidor | Pendiente | Pendiente |
| III.19 | Virtualización y contenedores | Completos | Con práctica |
| III.20 | Almacenamiento y copias de seguridad | Completos | Con práctica |
| III.21 | Redes | Completos | Con práctica |
| III.22 | Comunicaciones | Pendiente | Pendiente |
| III.23 | Servicios de red | Pendiente | Pendiente |
| III.24 | Monitorización y gestión de incidencias | Completos | Con práctica |
| III.25 | Cloud y centros de datos | Pendiente | Pendiente |
| III.26 | Soporte al puesto de trabajo | Pendiente | Pendiente |
| IV.27 | Bases de datos relacionales | Completos | Con práctica |
| IV.28 | SQL | Pendiente | Pendiente |
| IV.29 | Gestores de bases de datos | Pendiente | Pendiente |
| IV.30 | Programación | Pendiente | Pendiente |
| IV.31 | Desarrollo web | Pendiente | Pendiente |
| IV.32 | Interoperabilidad e integración | Pendiente | Pendiente |
| IV.33 | Informes y explotación de datos | Pendiente | Pendiente |
| V.34 | Seguridad de la información | Completos | Con práctica |
| V.35 | El Esquema Nacional de Seguridad (ENS, RD 311/2022) | Completos | Con práctica |
| V.36 | Criptografía y firma electrónica | Pendiente | Pendiente |
| V.37 | Protección de datos aplicada | Pendiente | Pendiente |
| V.38 | Ciberseguridad | Pendiente | Pendiente |
| V.39 | Administración electrónica práctica | Pendiente | Pendiente |
| V.40 | Accesibilidad y usabilidad | Pendiente | Pendiente |

## PDFs de apoyo y su código

Los cinco PDF se localizaron en `C:\Users\David\Downloads\catalogar\cap\teoria` y se copiaron a
`data/sources/` (ignorados por git). Se han cotejado por **contenido**, no por nombre: son
diapositivas de la asignatura *Computación de Altas Prestaciones* y todos corresponden a
**II.13 Arquitectura de ordenadores** como material de ampliación. No se les inventa un código
distinto (no hay otro tema del índice que trate procesadores) ni se publican.

| PDF | Páginas | Contenido | Detalle | Código asignado |
|---|---|---|---|---|
| `Tema1_1v2026.pdf` | 34 | TEMA 1 — ILP y técnicas de segmentación | Procesadores superescalares; pipeline | **II.13** (referencia interna) |
| `Tema1_2v2026.pdf` | 20 | TEMA 1 — Técnicas de predicción de saltos | Predicción de saltos; especulación | **II.13** (referencia interna) |
| `Tema2v2025.pdf` | 49 | TEMA 2 — Procesadores segmentados: planificación y especulación | Planificación de instrucciones | **II.13** (referencia interna) |
| `Tema3_1v2025.pdf` | 48 | TEMA 1 — Procesadores con múltiples emisiones | Emisión múltiple; superscalar | **II.13** (referencia interna) |
| `Tema3_2v2025.pdf` | 30 | TEMA 3 — Multithreading | Multithreading; paralelismo de hilos | **II.13** (referencia interna) |

## Coherencia del mapa y los sellos

Comprobado con el build y con Playwright sobre la URL pública (35/35): los 40 temas de la tabla
coinciden con los sellos de apuntes y práctica; los 19 completos tienen 3+ apartados, tabla, fuente y
10 preguntas; los 21 pendientes no tienen contenido publicado. La suma por bloque cuadra con el
total (19 + 21 = 40) y no hay temas «solo resumen» hoy.

## Regla de derechos

El material de academia y de terceros **no se publica** (D-034). Se usa solo como referencia interna
en `data/` o en el disco local. Los apuntes publicados son de redacción propia y citan fuente oficial
(BOE, TUE/TFUE, RFC, ISO, NIST). Un tema con PDF de apoyo sigue «Pendiente» si no tiene apuntes
propios publicados. El temario TAI recuperado (33/33 temas) tampoco se publica.
