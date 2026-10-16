| # | paso | URL | carga (ms) | desborde a 390 px | errores de consola |
|---|---|---|---|---|---|
| 01 | 01-inicio | `/` | 2176 | no | 0 |
| 02 | 02-temario | `/temario` | 1455 | no | 0 |
| 03 | 03-tema-IV7 | `/temario/IV.7` | 1682 | no | 0 |
| 04 | 04-IV7-apartado-1 | `/temario/IV.7#apartado-tcpip-arquitectura` | 176 | no | 0 |
| 05 | 05-IV7-apartado-2 | `/temario/IV.7#apartado-osi-que-es` | 60 | no | 0 |
| 06 | 06-IV7-practicar | `/tests?tema=IV.7` | 1391 | no | 0 |
| 07 | 07-test-configurado | `/tests?tema=IV.7` | — | no | 0 |
| 08 | 08-test-contestado | `/test/4365584d-6c04-4d32-bfec-2f9628100ce9` | 10439 | no | 0 |
| 09 | 09-resultado | `/resultado/4365584d-6c04-4d32-bfec-2f9628100ce9` | 336 | no | 0 |
| 10 | 10-ver-en-apuntes | `/temario/IV.7#osi-capas` | 46 | no | 0 |
| 11 | 11-fallos | `/fallos` | 1086 | no | 0 |
| 12 | 12-fallos-repasar | `/fallos` | 53 | no | 0 |
| 13 | 13-tema-I1 | `/temario/I.1` | 2142 | no | 0 |
| 14 | 14-I1-indice-ultimo | `/temario/I.1` | 15072 | no | 0 |
| 15 | 15-simulacros | `/simulacros` | 2498 | no | 0 |
| 16 | 16-simulacro-supuesto-III | `/simulacros` | — | no | 0 |
| 17 | 17-simulacro-empezado | `/simulacros` | 45063 | no | 0 |
| 18 | 18-simulacro-5-contestadas | `/simulacros` | undefined | no | 0 |
| 19 | 19-simulacro-abandonado | `/simulacros` | undefined | no | 0 |
| 20 | 20-examenes | `/examenes` | 654 | no | 0 |
| 21 | 21-examen-inap-2025-A | `/examenes` | — | no | 0 |
| 22 | 22-examen-inap-empezado | `/test/af8d5f58-9fe9-42c0-a65d-a1c0b078c654` | 961 | no | 0 |
| 23 | 23-examen-3-contestadas | `/test/af8d5f58-9fe9-42c0-a65d-a1c0b078c654` | — | no | 0 |
| 24 | 24-examen-terminado | `/resultado/af8d5f58-9fe9-42c0-a65d-a1c0b078c654` | 1320 | no | 2 |
| 25 | 25-progreso | `/progreso` | 2309 | no | 0 |
| 26 | 26-panel-incidencias | `/admin/incidencias` | 1715 | no | 0 |
| 27 | 27-panel-banco-abierto | `/admin/incidencias` | 156 | no · section.card (375>364); ul.conjuntos (357>327) | 0 |
| 28 | 28-panel-ficha-pregunta | `/admin/preguntas?pregunta=4104af79-e027-417b-9837-4c32d5a9acdb` | 1165 | no | 0 |
| 29 | 29-panel-ficha-acciones | `/admin/preguntas?pregunta=4104af79-e027-417b-9837-4c32d5a9acdb` | — | no | 0 |
| 30 | 30-panel-marcar-correcta | `/admin/preguntas?pregunta=4104af79-e027-417b-9837-4c32d5a9acdb` | 37 | no | 0 |
| 31 | 31-panel-apuntes | `/admin/apuntes` | 5372 | no | 0 |
| 32 | 32-panel-apuntes-IV7 | `/admin/apuntes/IV.7` | 3448 | no · div.apuntes__lectura (342>325); article.apartado (326>293) | 0 |

Pasos con tiempo medido: 25 · suma: 100812 ms

## Los ocho pasos más lentos

- **45063 ms** · 17-simulacro-empezado (`/simulacros`)
- **15072 ms** · 14-I1-indice-ultimo (`/temario/I.1`)
- **10439 ms** · 08-test-contestado (`/test/4365584d-6c04-4d32-bfec-2f9628100ce9`)
- **5372 ms** · 31-panel-apuntes (`/admin/apuntes`)
- **3448 ms** · 32-panel-apuntes-IV7 (`/admin/apuntes/IV.7`)
- **2498 ms** · 15-simulacros (`/simulacros`)
- **2309 ms** · 25-progreso (`/progreso`)
- **2176 ms** · 01-inicio (`/`)

## Errores de consola (1 pasos)

### 24-examen-terminado

- Access to fetch at 'http://127.0.0.1:8765/api/v1/student/sessions/af8d5f58-9fe9-42c0-a65d-a1c0b078c654/answers' from origin 'http://127.0.0.1:4173' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
- Failed to load resource: net::ERR_FAILED

