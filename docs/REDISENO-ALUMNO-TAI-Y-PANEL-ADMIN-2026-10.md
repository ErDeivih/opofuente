# Rediseño: OpoFuente como app de estudio TAI + panel de administración

**Para:** DeepSeek · **De:** Claude · **Fecha:** 6 oct 2026 · **Base:** `main = e5ce278`
**Sustituye en prioridad** a P1 y P2 de `docs/PLAN-PARA-DEEPSEEK-2026-10.md` (lo pendiente de P0 sigue valiendo; ver §9).

---

## 0. La idea en cinco líneas

1. La app pasa a tener **dos zonas**: la del **alumno** (`/`) y la del **administrador** (`/admin`).
2. El alumno ve **solo TAI** y solo lo que sirve para estudiar: temario por bloques y temas, apuntes, tests, simulacros, exámenes oficiales, fallos y progreso. **Nada** de fuentes, revisiones, bandeja, cambios, avisos, rutas de Windows, Celador ni Guardia Civil.
3. El administrador (el propietario) tiene un panel para **gestionar temas, apuntes por tema, preguntas por tema y por bloque, sus opciones y cuál es la correcta**, corregir lo que esté mal y **añadir temas** cuando entre más material.
4. Todas las pantallas actuales de "trastienda" (Bandeja, Biblioteca, Revisión, Cambios, Errores de importación, Ajustes) **se mueven a `/admin`**; no se borran.
5. La organización copia lo que ya hacen las academias y plataformas TAI (§1): no hay que inventar nada.

---

## 1. Qué ofrecen las plataformas TAI (referencia para no repensar)

Revisadas: EstudiaTAI, OpositaTest, Adams (Adams Test), OposiciónInformática, OposTIC, Typed AI, Easy‑Quizzz. Lo que se repite en todas es lo que tiene que tener la app:

| Lo que ofrecen todas | Cómo lo hacen | En OpoFuente |
|---|---|---|
| **Temario por bloques y temas** | 4 bloques TAI (I Organización del Estado y AE · II Tecnología básica · III Desarrollo de sistemas · IV Sistemas y comunicaciones) | Ya existe: 37 nodos (4 bloques, 33 temas) en la convocatoria activa |
| **Test por tema / por bloque** | Eliges bloques o temas, nº de preguntas (10/20/30/50/todas), aleatorio, solo falladas | Existe `practice` con **un** tema; falta multi‑tema, bloque y filtros |
| **Simulacro** | Examen completo con tiempo y penalización | Hay `mock_exam`; hay que componerlo con la estructura real (§3.6) |
| **Exámenes oficiales** | Banco de exámenes INAP de años anteriores, hechos como en el examen | 4 cuestionarios INAP 2025 (libre A/B, promoción interna A/B) |
| **Repaso de fallos** | "Test de falladas", libreta de errores, repetición espaciada | Existen `error_review`, `/reviews/due`, `/learning-errors` |
| **Corrección con explicación** | Tras responder: correcta en verde, la tuya en rojo, explicación | Hay 11.315 explicaciones en la base |
| **Estadísticas** | % acierto por tema, historial de tests, fortalezas y debilidades | Hay `/reviews/mastery` y resultados de sesión; falta la pantalla |
| **Mapa de preguntas** | Rejilla 1…N para saltar, ver respondidas/dudosas | Hay `navigate`; falta la rejilla |

Lo que **no** muestran nunca al alumno: de dónde sale cada pregunta, estados de importación, versiones, revisiones internas. Eso es nuestra "paja".

Fuentes: [EstudiaTAI](https://estudiatai.com/) · [Adams Test TAI](https://www.adams.es/adams-test) · [OpositaTest TAI](https://www.opositatest.com/) · [OposiciónInformática](https://oposicioninformatica.com/) · [Typed AI vs OpositaTest](https://typedai.com/comparar/typed-ai-vs-opositatest) · [OposiciónTAI](https://oposiciontai.com/)

---

## 2. Mapa de la app

```
ZONA ALUMNO (/)                         ZONA ADMIN (/admin)
─────────────────                       ────────────────────
Inicio          /                       Resumen            /admin
Temario         /temario                Temario (editar)   /admin/temario
  └ Tema        /temario/:codigo        Apuntes            /admin/apuntes/:codigo
Tests           /tests                  Preguntas          /admin/preguntas
Simulacros      /simulacros               └ Pregunta       /admin/preguntas/:id
Exámenes        /examenes               Importar           /admin/importar   (= Bandeja + Biblioteca actuales)
Fallos          /fallos                 Revisión           /admin/revision   (la actual)
Progreso        /progreso               Cambios            /admin/cambios    (la actual)
(pantalla test) /test/:sesion           Errores import.    /admin/errores    (la actual)
(resultado)     /test/:sesion/resultado Ajustes            /admin/ajustes    (la actual)
                                        Buscar en fuentes  /admin/buscar     (la actual)
```

- `:codigo` es legible: `I-1`, `IV-10`. No UUID en la URL del alumno.
- La navegación del alumno es una barra con 7 entradas (en móvil, barra inferior con 5: Inicio, Temario, Tests, Fallos, Progreso; Simulacros y Exámenes dentro de Tests).
- La zona admin tiene su propio menú lateral y un aviso fijo arriba "Modo administración". Enlace discreto "Administrar" en el pie de la zona alumno.
- **Las rutas antiguas** (`/bandeja`, `/revision`, `/cambios`, `/biblioteca`, `/preguntas`, `/errores`, `/ajustes`, `/buscar`, `/programa`, `/estudiar`) redirigen a la nueva ubicación. Nada de 404.

---

## 3. Zona alumno, pantalla a pantalla

Regla general para todas: **una acción principal por pantalla, visible sin hacer scroll**. Nada de párrafos explicando la app.

### 3.1 Inicio `/`
- Si hay un test a medias: tarjeta grande **"Continuar test"** (título, 12/50, tiempo).
- **"Repasar fallos (N)"** si hay preguntas vencidas.
- **Progreso por bloque**: 4 barras (I–IV) con % de acierto y preguntas vistas/total.
- Tres botones rápidos: **Test rápido (20 preguntas al azar)**, **Simulacro**, **Examen oficial**.
- Últimos 5 tests con nota.
- ✗ Quitar: acciones pendientes de revisión, avisos, contadores de bandeja, cualquier texto sobre fuentes.

### 3.2 Temario `/temario`
- Acordeón por bloque (I, II, III, IV). Cada tema: número, título (2 líneas como máximo, completo en tooltip), **% acierto**, **preguntas disponibles**, y dos botones: **Apuntes** y **Test**.
- Orden **numérico**: hoy IV.10 sale tras IV.1 (orden por texto de `path`). Ordenar por bloque romano y número de tema.
- Botón por bloque: **"Test del bloque"**.

### 3.3 Tema `/temario/:codigo`
- Cabecera: "Bloque IV · Tema 7 · El modelo TCP/IP…".
- Pestañas: **Apuntes** · **Preguntas** (botón Test de este tema con selector 10/25/50/todas) · **Mi progreso** (aciertos, fallos, última vez).
- **Apuntes** = los apuntes **publicados** desde el panel (§4.2), en lectura limpia (tipografía legible, índice lateral de encabezados). Si aún no hay apuntes publicados: "Apuntes en preparación" y el botón de test. **No** se muestran tramos crudos de fuentes, ni nombres de PDF, ni versiones, ni huellas.

### 3.4 Tests `/tests` (configurador)
Un solo formulario corto:
- **Qué**: bloques y/o temas (selección múltiple con casillas; "todo el temario" por defecto).
- **Cuántas**: 10 · 25 · 50 · 100.
- **Cuáles**: todas · no vistas · falladas · dudosas.
- **Corrección**: al momento · al final.
- **Con tiempo**: no · sí (minutos = preguntas × 1,2, editable).
- Botón **Empezar**. Debajo, "Tests guardados / a medias".

### 3.5 Pantalla de test `/test/:sesion`
- Enunciado grande, opciones A‑D como botones de ancho completo.
- Teclado: **A‑D / 1‑4** elige, **Enter** confirma/siguiente, **←/→** navega, **M** marca dudosa.
- Barra superior: progreso (12/50), tiempo (si aplica), botón **Mapa** (rejilla 1…N: respondida, dudosa, en blanco, actual) y **Terminar**.
- Corrección inmediata: correcta en verde, elegida mal en rojo, **explicación** si existe, y enlace **"Ver en apuntes del tema"**. Nada más.
- Botón **"Esta pregunta está mal"** (abre caja de texto → `POST /questions/{id}/report-issue`); el alumno no ve qué pasa después; el admin lo ve en su panel.
- ✗ Quitar: evidencias, fuente, conjunto de origen, estado de clave, "examen oficial" como etiqueta de procedencia en cada pregunta.

### 3.6 Simulacros `/simulacros`
Estructura **real** de TAI 2025, ya cargada en la base (`exam_parts` / `exam_rules` de la convocatoria activa; **leerla de ahí, no hardcodear**):
- **Primera parte**: 80 preguntas (+5 reserva) de todo el programa, 0‑50 puntos, mínimo 25.
- **Segunda parte**: supuesto práctico, **20 preguntas (+5 reserva)**, el alumno elige **bloque III o IV**.
- **120 minutos** para todo. Error resta **1/3**, blanco no resta.
- Resultado: puntuación directa por parte, ¿supera 25/50 en cada una?, y la nota 0‑100 marcada como **"estimada"** (la oficial depende del baremo del tribunal: regla `official_scaled_score_requires_published_criteria`).
- Opción "Simulacro corto" (40 preguntas, 48 min) para practicar entre semana.
- Reparto de la primera parte proporcional a las preguntas disponibles por bloque (configurable en admin).

### 3.7 Exámenes oficiales `/examenes`
- Lista de los cuestionarios oficiales INAP (hoy: libre 2025 A/B, promoción interna 2025 A/B) con año y nota del alumno si ya lo hizo.
- Se hacen **igual que en el examen** (tiempo, penalización, corrección al final). Al acabar, se puede repasar con explicaciones.

### 3.8 Fallos `/fallos`
- Contador grande: **N preguntas para repasar hoy** + botón **Repasar** (`error_review`, límite 20).
- Lista agrupada por tema: preguntas falladas, cuántas veces, última vez. Botón "Test con las falladas de este tema".

### 3.9 Progreso `/progreso`
- % acierto por bloque y por tema (tabla ordenable; los 5 temas más flojos destacados arriba).
- Historial de tests (fecha, tipo, nota, aciertos/fallos/blancos) → abre el resultado.
- Evolución de la nota de simulacros (línea simple).

### 3.10 Resultado `/test/:sesion/resultado`
- Nota con penalización, aciertos/fallos/blancos, tiempo.
- Desglose por tema.
- Botones: **Repasar fallos de este test**, **Repetir solo las falladas**, **Volver al temario**.
- El título del test es el que eligió el alumno ("Test · Bloque IV · 25 preguntas"), no el nombre del conjunto de origen.

### 3.11 Solo TAI y nada personal (requisito duro)
- La zona alumno fija la oposición a `tai-age` por configuración (`OPOFUENTE_STUDENT_OPPOSITION=tai-age`). **No hay selector de oposición** para el alumno.
- Ninguna respuesta de la API de alumno incluye: rutas de fichero, nombres de PDF/carpetas, títulos de bancos privados ("Rojo -General", "Test GSI"…), ids de documento, nombre del propietario ni otras oposiciones.
- **Test automático obligatorio**: un E2E que recorre todas las pantallas de alumno y falla si el HTML contiene `:\`, `Users`, `.pdf`, `Celador`, `Guardia Civil`, `Rojo`, `GSI`, `revisión`, `bandeja`, `fuente`, o un UUID visible. (Lista en un fichero de constantes para ampliarla.)

---

## 4. Zona admin

### 4.1 Temario `/admin/temario`
- Árbol bloque → tema. Por tema: preguntas asignadas, apuntes publicados sí/no, % de preguntas sin respuesta correcta.
- **Crear tema** (en un bloque), **crear bloque**, **renombrar**, **reordenar** (arrastrar o flechas), **archivar** (no borrar si tiene preguntas o intentos).
- Backend: hoy los nodos solo se leen. Nuevos endpoints:
  - `POST /api/v1/convocations/{id}/curriculum-nodes` `{parent_id, node_type, official_code, title, description}`
  - `PATCH /api/v1/curriculum-nodes/{id}` `{title?, description?, position?, official_code?}`
  - `POST /api/v1/curriculum-nodes/{id}/archive`
  - Recalcular `path`/`depth` al reordenar. Cada cambio deja `audit_events`.

### 4.2 Apuntes por tema `/admin/apuntes/:codigo`
Esto es lo nuevo importante. Hoy el "dossier" es un **montaje automático** de tramos de fuentes: sirve como materia prima, no como apuntes para el alumno.
- **Modelo nuevo** `topic_notes`: `id, curriculum_node_id, version_no, body_markdown, status (draft|published|archived), created_at, published_at, note` (motivo del cambio). Versionado: editar crea versión nueva; el alumno ve la última `published`.
- Pantalla en dos columnas: **izquierda editor Markdown** con vista previa; **derecha "Material del tema"** = el dossier actual (tramos de fuentes, con buscador) para copiar/pegar o insertar como cita.
- Botones: **Guardar borrador**, **Publicar**, **Ver historial** (diff entre versiones), **Restaurar versión**.
- Botón **"Crear borrador desde el material"**: genera un primer borrador con los títulos de sección del dossier (sin IA obligatoria; si hay modelo local disponible, opcional).
- Endpoints: `GET/POST /api/v1/curriculum-nodes/{id}/notes`, `GET /api/v1/curriculum-nodes/{id}/notes/{version_id}`, `POST …/notes/{version_id}/publish`. Endpoint de alumno: `GET /api/v1/student/topics/{codigo}/notes` (solo la publicada, solo Markdown).

### 4.3 Preguntas `/admin/preguntas`
- Tabla con filtros: bloque, tema, **sin tema**, **sin respuesta correcta**, **reportadas por alumnos**, en conflicto, conjunto, texto.
- Columnas: enunciado (recortado), tema, correcta (A‑D o "—"), estado, reportes.
- Acciones en lote: **asignar a tema**, quitar de tema, archivar.

### 4.4 Ficha de pregunta `/admin/preguntas/:id`
Todo editable en un formulario:
- Enunciado, opciones (añadir/quitar/reordenar), **marcar la correcta** (radio), explicación general y por opción, tema(s) y bloque, activa/archivada.
- Al guardar: nueva versión de la pregunta (las sesiones ya hechas no cambian; usa `recalculate-sessions` existente si cambia la correcta y ofrécelo con un aviso claro).
- Reportes de alumnos de esa pregunta, con botón "resuelto".
- **Nueva pregunta**: botón en la tabla y en cada tema ("Añadir pregunta a este tema").
- Backend (hoy faltan):
  - `POST /api/v1/question-sets/{id}/questions` (crear) — usar un conjunto `admin_bank` por oposición para las creadas a mano.
  - Ampliar `PATCH /questions/{id}` o nuevo `PUT /questions/{id}/content` que acepte `{stem, options[], correct_option_key, explanation?, note}` y escriba `question_versions` + `option_versions` + entrada de clave + explicación en **una transacción**.
  - `POST/DELETE /api/v1/questions/{id}/topics` para asignar/quitar tema (escribe `curriculum_mappings` con `subject_type='question_version'`, `status='accepted'`).
  - `GET /api/v1/question-issue-reports?status=open`.

### 4.5 Lo que ya existe, movido
Importar (Bandeja + Biblioteca), Revisión, Cambios, Errores de importación, Buscar en fuentes y Ajustes pasan tal cual bajo `/admin`. Su mejora (P0.2 búsqueda, P2 ruido) sigue en el plan anterior, con **prioridad baja** frente a lo de aquí.

### 4.6 Acceso
Hoy es una app local de un usuario. Para separar zonas basta, en esta fase, con: zona admin solo si `OPOFUENTE_ADMIN=1` (por defecto activado en local) y la API de admin bajo `/api/v1/admin/*` o con la misma condición. **No** implementar cuentas de usuario todavía (ver §8, decisión del propietario).

---

## 5. API del alumno (fina y limpia)

Para que la zona alumno no dependa de endpoints que devuelven datos internos, crear una capa `GET/POST /api/v1/student/*` que solo devuelve lo que se pinta:

| Endpoint | Devuelve |
|---|---|
| `GET /student/overview` | test a medias, fallos vencidos, % por bloque, últimos tests |
| `GET /student/syllabus` | bloques y temas ordenados numéricamente: código, título, nº preguntas, % acierto, ¿apuntes? |
| `GET /student/topics/{codigo}` | cabecera del tema + progreso |
| `GET /student/topics/{codigo}/notes` | Markdown publicado |
| `POST /student/tests` | crea sesión desde `{nodes[], count, filter, feedback, timed}`; internamente `practice` multi‑tema |
| `POST /student/mock-exams` | `{variant: full|short, case_block: III|IV}` según `exam_parts` |
| `GET /student/official-exams` | lista de oficiales con nota previa |
| `GET /student/progress` | por tema, historial, evolución |

Las de sesión (`current-question`, `answers`, `navigate`, `finish`, `result`) se reutilizan, pero su respuesta para el alumno **no** debe llevar `evidence`, `source_*`, títulos de conjunto ni rutas. Añadir un esquema `StudentQuestionView` y testear que no contiene esas claves.

Requiere en backend:
- `practice` con **varios** `curriculum_node_ids` (hoy uno) y con bloque = todos sus temas.
- Filtros "no vistas / falladas / dudosas" (usar `attempts`, `learning_errors`, marca de dudosa — añadir `flagged` a la respuesta si no existe).
- Composición de simulacro por `exam_parts`.

Todo nuevo endpoint va al contrato (`packages/contracts/openapi.json`) y se regeneran los tipos, como siempre.

---

## 6. Diseño visual (reglas cortas)

- Mantener CSS propio (no añadir Tailwind ni librerías de componentes: el repo no las usa y la migración no compensa). Centralizar **tokens** en `global.css`: color primario, éxito (verde), error (rojo), aviso, gris; espaciado 4/8/12/16/24/32; radios; 2 tamaños de sombra; tipografía base 16‑17 px, enunciado 19‑20 px.
- Componentes reutilizables en `src/ui/`: `Button` (primario/secundario/fantasma), `Card`, `ProgressBar`, `Tabs`, `Accordion`, `OptionButton` (estados: normal, elegida, correcta, incorrecta, deshabilitada), `QuestionGrid`, `StatTile`, `EmptyState`, `Modal`.
- Contraste AA (ya hay axe en E2E; mantenerlo verde). Foco visible. Todo usable con teclado.
- Responsive: probar a **390 px** (móvil) y **1280 px**. En móvil, opciones a ancho completo y botón "Siguiente" fijo abajo.
- Textos: frases cortas, segunda persona, sin jerga interna (nada de "conjunto", "clave", "tramo", "mapeo", "representación", "versión" en la zona alumno).
- Estados vacíos útiles: "Aún no has hecho ningún test · [Empezar test rápido]".

---

## 7. Herramientas para que DeepSeek **vea** lo que construye

El problema hasta ahora: DeepSeek programa la UI sin verla. Solución en dos niveles:

**a) Playwright MCP (si tu entorno admite servidores MCP).** Te da un navegador que puedes manejar y del que puedes sacar capturas y el árbol de accesibilidad.
```json
{ "mcpServers": { "playwright": { "command": "npx", "args": ["@playwright/mcp@latest"] } } }
```
Uso: abre `http://127.0.0.1:5173`, recorre la pantalla que acabas de tocar, mira la captura **antes** de dar la tarea por hecha. Guías: [Playwright MCP y verificación visual](https://argos-ci.com/blog/playwright-mcp-visual-testing), [guía de Playwright MCP](https://qaskills.sh/blog/playwright-mcp-browser-automation-guide).

**b) Sin MCP: script de capturas en el repo** (hazlo primero, sirve siempre y también para mí):
- `apps/web/e2e/screens.spec.ts` + `npm run screens`: visita cada ruta de alumno y admin a **1280×800 y 390×844**, con datos de prueba sembrados, y guarda `artifacts/screens/<ruta>-<ancho>.png`.
- Además escribe `artifacts/screens/report.md` con: ruta, tiempo de carga, errores de consola, violaciones axe, y si aparece alguna palabra prohibida de §3.11.
- Si tu modelo puede leer imágenes, míralas; si no, el `report.md` es tu control. **En el informe de cada entrega, adjunta las capturas de las pantallas tocadas** para que el propietario y yo las revisemos.

---

## 8. Decisiones del propietario (no las tomes tú)

1. **"Que lo use cualquiera"** implica, si sale de tu PC: cuentas de usuario, progreso por usuario y despliegue. Esta fase deja todo preparado (API de alumno separada, admin aparte) pero **sigue siendo local y de un usuario**.
2. **Derechos de las preguntas.** De los 231 cuestionarios TAI, 4 son exámenes oficiales del INAP (públicos) y **227 son bancos privados** (academias, apuntes de terceros). Para uso personal no hay problema; **para ofrecerlos a otras personas probablemente no se pueda** sin permiso. Propuesta: campo `distribution` en `question_sets` (`personal` | `public`) y que una futura versión pública solo sirva `public` + preguntas creadas por el propietario. Ahora solo añadir el campo (por defecto `personal`, oficiales INAP `public`).
3. Si las explicaciones o los apuntes se generan con IA, si se revisan antes de publicar (propuesta: sí, todo pasa por "Publicar" en admin).

---

## 9. Orden de trabajo y cómo se acepta cada fase

Una rama por fase, como hasta ahora; prueba que falla antes y pasa después; puertas en verde; capturas en el informe.

| Fase | Contenido | Se acepta cuando… |
|---|---|---|
| **F0** | Script de capturas (§7b) + test de palabras prohibidas (§3.11) en modo informe | Hay PNG de todas las rutas actuales y un `report.md` |
| **F1** | Dos zonas: router, layout alumno, layout admin, redirecciones de rutas viejas; mover pantallas actuales a `/admin` | Ninguna ruta vieja da 404; la barra del alumno solo tiene las 7 entradas |
| **F2** | API `/student/*` (overview, syllabus, topics, progress) + orden numérico de temas + filtro solo TAI | Test de API: ninguna respuesta de alumno contiene claves/valores prohibidos |
| **F3** | Inicio, Temario, Tema (sin apuntes aún), Progreso | Capturas 390/1280; axe verde |
| **F4** | Tests: configurador, multi‑tema/bloque, filtros, pantalla de test con teclado y mapa, resultado | Desde Inicio hasta resultado de un test de 10 en **menos de 4 clics**; navegación completa con teclado |
| **F5** | Simulacros por `exam_parts` + Exámenes oficiales + Fallos | Simulacro completo 80+20 con elección III/IV, 120 min, −1/3; nota "estimada" |
| **F6** | Admin: Preguntas (tabla, ficha, crear, editar, marcar correcta, asignar tema, reportes) | Cambiar la correcta de una pregunta se ve en el siguiente test del alumno; queda auditado |
| **F7** | Admin: Apuntes por tema (`topic_notes`, editor, publicar, historial) + pestaña Apuntes del alumno | Publicar en admin → visible en `/temario/:codigo`; restaurar versión funciona |
| **F8** | Admin: Temario (crear/renombrar/reordenar/archivar temas) | Un tema nuevo aparece en el temario del alumno y admite preguntas y apuntes |
| **F9** | Activar el test de palabras prohibidas como **bloqueante** en las puertas | Puertas 18/18 |

Del plan anterior siguen vivos y **van antes de F4**: P0.4 segunda mitad (dossier del bloque paginado — lo necesita la columna "Material del tema" de F7, así que puede ir antes de F7) y la puerta 18 en rojo por lentitud de Revisión (P2.2): al mover Revisión a admin, arregla su lentitud o marca esa prueba como de admin con su propio límite **justificado**, nunca subiendo el límite sin más.

---

## 10. Recorrido de aceptación final (lo hará el propietario)

1. Abro `/`: veo Inicio con progreso por bloque y "Test rápido". No veo nada de fuentes ni de otras oposiciones.
2. Temario → Bloque IV → Tema 7 → leo apuntes → "Test de este tema" 10 preguntas.
3. Respondo con el teclado, marco una dudosa, veo explicación al fallar, termino.
4. Resultado → "Repetir falladas".
5. Simulacros → completo, elijo bloque III, veo el reloj de 120 min.
6. Exámenes → TAI libre 2025 modelo A.
7. Fallos → repaso las vencidas.
8. Progreso → mis 5 temas más flojos.
9. Administrar → Preguntas → filtro "reportadas" → corrijo la correcta de una → vuelvo a la zona alumno y el cambio está.
10. Administrar → Apuntes del tema IV.7 → edito un párrafo → Publicar → lo veo como alumno.
11. Administrar → Temario → creo "Bloque IV · Tema 11 (prueba)" → aparece en el temario.
12. Todo ello también en el móvil (390 px).
