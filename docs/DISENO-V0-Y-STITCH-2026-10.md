# Diseño de la UI: una pasada por v0, el resto en Stitch

**Para:** DeepSeek · **De:** Claude · **7 oct 2026**
Encaja en `TRABAJO-PENDIENTE-PLATAFORMA-TAI-2026-10.md`: sustituye los tokens de color y tipografía de la Fase 3 y añade un componente nuevo (la hoja de respuestas). El orden de las fases no cambia.

---

## 0. Antes de nada: las claves

- Desde mi entorno no hay salida a `api.v0.dev` ni a `stitch.googleapis.com` (lo he probado desde la nube y desde el ordenador). **Las llamadas las haces tú**, desde Windows, como ya hiciste con Stitch.
- **v0**: lo que pegó el propietario (`v1:team_…:vcp_…`) **sí tiene la forma de una clave de API de v0** (la Platform API se autentica con `Authorization: Bearer <clave>`; las claves se crean en v0 → Settings → Keys). Úsala.
- Las claves van **solo** en variables de entorno de la sesión (`$env:V0_API_KEY`, y la de Stitch en la configuración del cliente MCP). **Nunca** en el repositorio, en `_oficial`, en un log ni en un commit. Antes de cada commit: `git grep -n "v1:team_\|AQ\.A"` debe salir vacío.
- Las dos claves se han escrito en un chat: cuando acabe este trabajo, el propietario debería **revocarlas y crear otras**.

---

## 1. La dirección de diseño (la decido yo; v0 y Stitch la ejecutan)

Los tokens que te di (fondo crema `#f7f6f3` + azul) eran correctos pero **genéricos**: así salen la mitad de las apps generadas. La app es de **opositores a TAI**, y su mundo tiene un objeto propio que nadie más usa: **la hoja de respuestas del examen oficial** (rejilla numerada con casillas A B C D que se rellenan, impresa en tinta azul de lectura óptica). Ese es el elemento memorable; todo lo demás, sobrio.

**Concepto: "la hoja de respuestas".**

| Token | Valor | Uso |
|---|---|---|
| Papel | `#F4F6F9` (blanco frío, no crema) | fondo de la app |
| Hoja | `#FFFFFF` | superficies, apuntes, enunciados |
| Tinta | `#18202B` | texto principal |
| Tinta suave | `#5A6472` | texto secundario |
| Línea | `#D5DCE6` | bordes y separadores |
| Azul de hoja óptica (acento único) | `#2347C5`, suave `#E7ECFB` | navegación activa, botón principal, foco, casillas marcadas, barras de progreso |
| Acierto | `#15734A`, suave `#E3F2EA` | **solo** corrección |
| Fallo | `#B42318`, suave `#FBE8E6` | **solo** corrección |
| Dudosa | `#9A6200`, suave `#FBF0D9` | marca de dudosa |

**Tipografía** (dos familias, autoalojadas con `@fontsource`: la CSP no deja cargar fuentes externas):
- **Interfaz y preguntas: Atkinson Hyperlegible Next.** Diseñada para máxima legibilidad (distingue bien `l/I/1`, `O/0`): tiene sentido en una app donde se leen siglas, cifras y comandos durante horas. Cuerpo 17 px, enunciado 20 px, interlineado 1,5.
- **Apuntes: Source Serif 4.** Texto largo en serif, 18 px, interlineado 1,65, máximo 68 caracteres por línea.
- Cifras tabulares (`font-variant-numeric: tabular-nums`) en notas, porcentajes y tiempos.
- Escala: 14 · 17 · 20 · 24 · 32. Títulos en peso 700, sin mayúsculas sostenidas, sin rótulos encima de cada título.

**Composición:**
- **Escritorio**: carril de navegación a la izquierda (7 entradas, iconos con texto), contenido alineado a la izquierda con ancho máximo 1080 px.
- **Móvil**: barra inferior con 5 entradas.
- **Modo test = modo examen**: al empezar un test desaparece la navegación. Enunciado y opciones a la izquierda; **a la derecha, la hoja de respuestas**: columna de números 1…N con sus casillas A B C D que se rellenan en azul al responder (en móvil, se abre desde un botón "Hoja"). Al corregir, la casilla correcta se marca en verde y la fallada en rojo, **como la plantilla oficial** sobre la hoja.
- **Apuntes**: índice de epígrafes a la izquierda (fijo al hacer scroll), texto en el centro, y en el margen derecho las notas "Esto cae" junto al párrafo al que se refieren, como anotaciones al margen (en móvil, bajo el párrafo).
- **Temario**: índice como el de un programa oficial: el número romano del bloque grande en el margen, temas numerados debajo con su barra de acierto fina y el número de preguntas.

**Lo que no queremos** (son los tics de las interfaces generadas): fondo crema, cada cosa en una tarjeta redondeada igual con la misma sombra, rótulos en MAYÚSCULAS encima de los títulos, metadatos unidos con "·", flechas "→" en los botones, degradados decorativos, animaciones de entrada en cada bloque, cifra gigante con rótulo pequeño como portada de Inicio.

---

## 2. Paso 1 — v0, **una sola llamada**

Los créditos son pocos: un único chat con todas las pantallas clave en un prototipo. No se itera en v0; lo que haya que corregir se corrige en Stitch o en el código.

### El encargo (cópialo tal cual en `initialMessage`)

```
Build a high-fidelity, clickable prototype (React + Tailwind, one app with client-side tabs/routes, mock data only, no backend) of the STUDENT side of a Spanish study platform for the civil-service exam "Técnico Auxiliar de Informática del Estado" (TAI). All UI copy in Spanish (Spain), plain and short, second person. No marketing page.

DESIGN CONCEPT – "la hoja de respuestas": the signature element is the official optical answer sheet (numbered rows with A B C D boxes printed in blue OMR ink, filled when answered). Everything else is calm and disciplined, built for 4–8 hour study sessions.
Colors (use exactly): app background #F4F6F9, surfaces #FFFFFF, text #18202B, secondary text #5A6472, lines #D5DCE6, single accent (OMR blue) #2347C5 with soft #E7ECFB. Green #15734A / soft #E3F2EA and red #B42318 / soft #FBE8E6 are ONLY for correct/incorrect answers; amber #9A6200 / #FBF0D9 only for "dudosa".
Type: "Atkinson Hyperlegible Next" for UI and questions (body 17px, question stem 20px, line-height 1.5); "Source Serif 4" for study notes (18px, line-height 1.65, max 68ch). Tabular numbers for scores and times. No all-caps labels, no eyebrow labels above headings, no "·"-joined metadata, no "→" in buttons, no gradients, no identical rounded cards everywhere, no entrance animations. Visible keyboard focus. Must work at 390px width.

LAYOUT: desktop = left navigation rail with 7 items (Inicio, Temario, Tests, Simulacros, Exámenes, Fallos, Progreso); mobile = bottom bar with 5 (Inicio, Temario, Tests, Fallos, Progreso).

SCREENS (make all of them, reachable from the nav or from buttons):
1. Inicio: "Continuar test" (Test · Bloque IV · 12 de 25, 14 min) as the main action; "Repasar 23 fallos"; progress per block as four thin bars with written % (I Organización del Estado y Administración electrónica 64 %, II Tecnología básica 42 %, III Desarrollo de sistemas 78 %, IV Sistemas y comunicaciones 55 %); quick actions "Test rápido de 20", "Simulacro", "Examen oficial"; last 5 tests with score.
2. Temario: like an official syllabus index. Big roman numeral per block in the margin; numbered topics under it, each with title (2 lines max), thin accuracy bar with %, number of questions, buttons "Apuntes" and "Test". Use real TAI topics, e.g. Bloque I tema 1 "La Constitución Española de 1978. Derechos y deberes fundamentales…", Bloque II tema 4 "Sistemas operativos…", Bloque IV tema 7 "El modelo TCP/IP y el modelo de referencia OSI…".
3. Tema IV-7 with tabs Apuntes / Preguntas / Mi progreso. Apuntes: sticky outline of sections on the left (one per official sub-heading), serif reading column in the middle with a comparison table (TCP vs UDP), and margin notes on the right called "Esto cae" next to the paragraph they refer to (below the paragraph on mobile). Button "Test de este tema" at the end.
4. Test configurator: choose blocks/topics (checkbox tree), number (10/25/50/100), which questions (todas / no vistas / falladas / dudosas), correction (al momento / al final), timer on/off, button "Empezar".
5. Test en curso (exam mode, navigation hidden): progress "12 de 25", timer, "Terminar". Stem + four options A–D as full-width rows (keyboard hints A–D, Enter, ←/→, M para dudosa). On the right, the ANSWER SHEET: rows 1–25, each with A B C D boxes; answered = filled blue, current row highlighted, dudosa = amber outline. On mobile the sheet opens from a "Hoja" button. Show one state after answering with immediate correction: chosen wrong option red with "Tu respuesta", correct green with "Correcta", a short explanation, link "Ver en apuntes", and on the sheet the correct box green and the wrong one red, like the official answer template.
6. Resultado: score with penalty (cada error resta 1/3), aciertos/fallos/en blanco, time, breakdown by topic, the full answer sheet corrected, buttons "Repasar fallos" and "Repetir solo las falladas".
7. Simulacros: real structure — Primera parte 80 preguntas (+5 reserva), Segunda parte supuesto práctico de 20 (+5) eligiendo bloque III o IV, 120 minutos, error resta 1/3; "Simulacro corto" 40 preguntas / 48 min; history of past simulacros with score per part and whether each part reaches 25/50 ("nota estimada").
8. Fallos: "23 para repasar hoy" + "Repasar"; failed questions grouped by topic with count and last date.
9. Progreso: table by topic sortable by accuracy, the 5 weakest topics highlighted, history of tests, a simple line of simulacro scores.

Do NOT include: admin, imports, sources, file names, PDFs, review queues, opposition selector, login.
```

### Cómo lanzarlo (PowerShell, en `F:\temp-opofuente\v0\`, fuera del repo)

```powershell
$body = @{ initialMessage = (Get-Content .\encargo-v0.txt -Raw) } | ConvertTo-Json -Depth 5
$r = Invoke-RestMethod -Method Post -Uri "https://api.v0.dev/v1/chats" `
      -Headers @{ Authorization = "Bearer $env:V0_API_KEY" } -ContentType "application/json" -Body $body
$r | ConvertTo-Json -Depth 20 | Set-Content .\respuesta-v0.json -Encoding utf8
```

La generación puede tardar varios minutos. De la respuesta guarda: el id del chat, el **enlace web del chat**, la **URL de la vista previa (demo)** y **los ficheros** de la última versión (si la respuesta no los trae, `GET https://api.v0.dev/v1/chats/{id}` y los ficheros de su `latestVersion`). Comprueba los nombres exactos de los campos en la [referencia de la Platform API](https://v0.app/docs/api/platform/overview). Escribe los ficheros en `F:\temp-opofuente\v0\codigo\`.

**Capturas** de la vista previa con Playwright (sin gastar créditos): las 9 pantallas a 1280×800 y 390×844 → `F:\temp-opofuente\opofuente-main\artifacts\design\v0\<pantalla>-<ancho>.png`. En la de test, una captura antes y otra después de responder.

**No hagas una segunda llamada a v0** sin que yo haya visto las capturas.

---

## 3. Paso 2 — Sacar el sistema del prototipo

Del código de v0 (clases de Tailwind y componentes), escribe `docs/DISENO-SISTEMA.md` con:
1. Tokens finales (colores, tipos, tamaños, espaciados, radios, sombras) **comparados con los del §1**: si v0 se ha desviado, gana el §1 salvo que yo diga otra cosa al ver las capturas.
2. La rejilla de cada pantalla (anchos de columnas, márgenes, puntos de corte).
3. El inventario de componentes que aparecen y cuáles faltan en `src/ui/`: como mínimo **`AnswerSheet`** (hoja de respuestas: estados vacía, marcada, actual, dudosa, correcta, fallada, en blanco tras corregir), `NavRail`, `BottomNav`, `SyllabusIndex`, `NotesLayout` (índice, columna, notas al margen), `MarginNote`, `ExamTopBar` (progreso, reloj, terminar).
4. No copies el código de v0 al repositorio (Tailwind no está en el proyecto y no se añade): se traduce a nuestro CSS con tokens.

---

## 4. Paso 3 — Seguir en Stitch (proyecto `projects/2395450215005392806`)

1. Actualiza el sistema de diseño del proyecto (o crea uno nuevo) con los tokens del §1 y la descripción del concepto "hoja de respuestas"; aplícalo a las 10 pantallas existentes.
2. Rehaz con `edit_screens` las que choquen con el concepto: **Test corregido** y **Mapa de preguntas** pasan a ser la hoja de respuestas; **Tema con apuntes** con notas al margen; **Temario** como índice de programa. Usa como referencia lo que salga de v0.
3. Genera la que falló por el 503: **Test en curso**.
4. Añade dos pantallas de administración, que también se van a construir: **Editor de apuntes** (Markdown a la izquierda, material del tema a la derecha, secciones con estado "pendiente"/"revisada", botones Guardar borrador / Publicar) y **Ficha de pregunta** (enunciado, opciones, marcar la correcta, explicación, tema).
5. **Descarga la captura de cada pantalla de Stitch** (las herramientas devuelven una URL de imagen por pantalla) a `artifacts/design/stitch/<pantalla>.png`.

---

## 5. Paso 4 — Parar y pasármelo

Entrega: las rutas de `artifacts/design/v0/` y `artifacts/design/stitch/`, el enlace al chat de v0 y `docs/DISENO-SISTEMA.md`. Yo reviso las imágenes y digo qué se queda. **Después**:
- tokens nuevos en `global.css`, fuentes con `@fontsource` (Atkinson Hyperlegible Next y Source Serif 4, solo los pesos que se usen), y `src/ui/` actualizado más los componentes nuevos, todos en `/admin/ui` con capturas;
- y se sigue con la **Fase 1** de `TRABAJO-PENDIENTE`, construyendo ya cada pantalla con este diseño.

Este trabajo de diseño cabe en **una sesión** y no puede retrasar la Fase 1 más allá de esa sesión.
