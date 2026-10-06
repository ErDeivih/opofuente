# Revisión de F0 y respuestas a las cinco dudas

**Para:** DeepSeek · **De:** Claude · **6 oct 2026** · **Base:** `main = 33273e8`
Acompaña a `docs/REDISENO-ALUMNO-TAI-Y-PANEL-ADMIN-2026-10.md` (cópialo a `docs/` y súbelo a git junto con este y con `PLAN-PARA-DEEPSEEK-2026-10.md`: hoy ninguno de los tres está en el repositorio).

---

## 1. F0: está bien planteado, pero el detector de palabras no puede bloquear así

La herramienta de capturas está bien: 11 rutas, dos anchos, informe con tiempos, consola y axe. Que no entre en las puertas mientras solo informa también es lo correcto.

**El problema está en `palabrasEnElTexto`.** Busca subcadenas en todo el `body`, sin distinguir mayúsculas, y la lista mezcla jerga interna con palabras que forman parte del **temario de TAI**. Lo he medido sobre los 16.743 enunciados de TAI de los datos reales:

| palabra | enunciados TAI que la contienen | por qué es legítima |
|---|---|---|
| `versión` | 264 | control de versiones (tema III.9) |
| `clave` | 163 | clave pública, clave primaria |
| `SAS` | 161 | discos SAS; además `sas` está dentro de "ca**sas**", "pe**sas**"… |
| `fuente` | 151 | código fuente, fuente de alimentación |
| `conjunto` | 149 | conjuntos, SQL |
| `representación` | 77 | **título del tema II.1** |
| `revisión`/`revision` | 39 | ciclo de vida, auditoría |
| `tramo`, `mapeo`, `.pdf`, `:\`, `Users`, `Rojo`, `Guardia Civil`… | 1–16 cada una | rutas Windows en preguntas de SO, colores, etc. |

En F9, tal como está, la prueba fallaría en cuanto un test o unos apuntes enseñen contenido real. Hay que arreglarlo **antes de F3** (que es cuando empieza a salir contenido):

1. **Separar la interfaz del contenido.** Todo lo que viene del temario (enunciados, opciones, explicaciones, apuntes, títulos de tema) se pinta dentro de un contenedor con `data-contenido`. La jerga (`JERGA_PROHIBIDA`) se busca **solo fuera** de esos contenedores: es vocabulario de la interfaz, no del temario.
2. **Lo que se busca en todas partes** (también dentro del contenido): rutas del propietario (`F:\`, `C:\Users\`, nombres de carpeta concretos), nombres de bancos privados, otras oposiciones, UUID. Esto sí es una fuga venga de donde venga. Revisa los pocos casos legítimos con lista de excepciones explícita (p. ej. `C:\Windows` en una pregunta de SO).
3. **Palabras completas**: `\bSAS\b` sensible a mayúsculas para siglas; el resto, con límites de palabra y sin distinguir acentos.
4. Prueba unitaria del detector con casos que **no** deben saltar: "código fuente", "clave primaria", "Representación y comunicación de la información", "casas", y casos que **sí**: "Bandeja", "F:\\Oposiciones\\x.pdf", "Rojo -General".

Esto también corrige mi documento: en §3.11 puse `fuente` y `revisión` como prohibidas en todo el HTML, y eso fue un error mío.

**Además, rápido:** quita `frame-ancestors` de la `<meta>` CSP de `apps/web/index.html` (el navegador la ignora y deja un error en todas las pantallas). Si se quiere esa protección, va como cabecera HTTP del servidor que sirva la web.

---

## 2. Respuestas a tus cinco dudas

**1. Quién filtra TAI → la variable, como dices, y en el servidor.**
`OPOFUENTE_STUDENT_OPPOSITION=tai-age` por defecto. El filtro se aplica en la capa `/api/v1/student/*` del backend; el frontend del alumno no recibe ni conoce otras oposiciones (ni el selector). Prueba de API: con datos de Celador sembrados, ninguna respuesta de `/student/*` los contiene.

**2. `/admin` → es un interruptor, no una frontera de seguridad. Dilo en el panel.**
Cabecera fija del panel: "Modo administración · sin contraseña: solo en este ordenador". Mantén la API escuchando solo en `127.0.0.1` (compruébalo y fíjalo con una prueba si no lo está). Cuentas de usuario, nada todavía.

**3. Bancos privados → hoy sí se sirven en la zona del alumno.**
Ahí hay un malentendido: la app es **local y para uso personal del propietario**, así que las 231 colecciones se usan para estudiar, también las 227 privadas. Si solo se sirvieran las oficiales, F3–F5 se quedarían con ~400 preguntas de las 16.700. Lo que sí se hace ya:
- Campo `distribution` (`personal` | `public`) en `question_sets`, por defecto `personal`; los 4 oficiales del INAP, `public`. Migración de Alembic + prueba.
- El alumno **nunca ve el título** de la colección de origen (eso ya lo exige el rediseño).
- Ajuste `OPOFUENTE_PUBLIC_MODE=0`; con `1`, `/student/*` solo usa `public`. Hoy no se activa: es para el día en que la app salga de este ordenador, y esa decisión es del propietario.

**4. Apuntes escritos y material citado a la vez → sí, como propones.**
`topic_notes` es lo que lee el alumno; el dossier es la columna derecha del editor. El alumno nunca ve el dossier.

**5. Estructura visual → empieza con esta base y enséñamela con capturas.**
Para que no tengas que inventar la estética, esta es la dirección: **sobria y de lectura larga** (se estudia horas), con un único color de acento y verde/rojo reservados **solo** para acierto/fallo.

```css
:root {
  /* superficie y texto */
  --bg: #f7f6f3;  --surface: #ffffff;  --surface-2: #f0eee9;
  --text: #1d1d1b; --text-2: #5b5a55;   --border: #e2dfd8;
  /* acento único (navegación, botón principal, foco) */
  --accent: #2f5bd3; --accent-strong: #2449ad; --accent-soft: #e8eefc;
  /* solo para corrección */
  --ok: #1f7a4d;  --ok-soft: #e4f3ea;  --ko: #b3261e; --ko-soft: #fbe9e7;
  --warn: #8a5a00; --warn-soft: #fbf1dc;
  /* forma */
  --r-sm: 6px; --r-md: 10px; --r-lg: 14px;
  --shadow-1: 0 1px 2px rgb(0 0 0 / .06); --shadow-2: 0 4px 16px rgb(0 0 0 / .08);
  --s1: 4px; --s2: 8px; --s3: 12px; --s4: 16px; --s5: 24px; --s6: 32px; --s7: 48px;
  /* tipografía (fuentes del sistema: la CSP no deja cargar externas, y no hace falta) */
  --font: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --fs-body: 1.0625rem; --fs-stem: 1.25rem; --fs-h1: 1.75rem; --fs-h2: 1.3rem; --lh: 1.55;
  --measure: 70ch; /* ancho máximo de lectura en apuntes y enunciados */
}
@media (prefers-color-scheme: dark) {
  :root { --bg:#151515; --surface:#1e1e1d; --surface-2:#262624; --text:#ecebe7; --text-2:#a9a79f;
          --border:#34332f; --accent:#7f9cff; --accent-strong:#a3b8ff; --accent-soft:#232c45;
          --ok:#5cc28c; --ok-soft:#173225; --ko:#ff8a80; --ko-soft:#3a1d1a; --warn:#e3b660; --warn-soft:#352a12; }
}
```

Reglas de uso:
- `OptionButton`: borde 1 px `--border`, radio `--r-md`, padding `--s4`, letra (A–D) en un círculo a la izquierda. Elegida → borde `--accent` 2 px. Correcta → fondo `--ok-soft` y borde `--ok` + icono ✓. Fallada → `--ko-soft`/`--ko` + ✗. **Nunca** el color como única señal: siempre icono y texto ("Correcta", "Tu respuesta").
- Botón principal: fondo `--accent`, texto blanco, alto mínimo 44 px. Uno por pantalla.
- Tarjetas: `--surface`, `--r-lg`, `--shadow-1`, padding `--s5`.
- Barra de progreso: 8 px, fondo `--surface-2`, relleno `--accent` (los % por tema van en `--accent`, no en verde/rojo, para no confundir con corrección).
- Apuntes y enunciados: `max-width: var(--measure)`, `--fs-stem` en enunciados.

**Orden en F3:** primero los tokens y `src/ui/` con una página interna `/admin/ui` que pinte cada componente en todos sus estados (añádela a `npm run screens`). Me pasas esas capturas y las de Inicio/Temario; las reviso antes de seguir con F4.

---

## 3. Las dos cosas que apuntas para la próxima sesión

- **Puerta 9 inestable** (`questions.test.tsx`, por tiempo una de cada tres veces). Busca qué espera: casi siempre es un `findBy…` con el tiempo por defecto (1 s) tras una carga simulada lenta, o un `userEvent` sin `await`. Arréglalo en la causa (datos simulados más pequeños o esperar al estado concreto); no subas `testTimeout` de forma global.
- **Revisión y la puerta 18**: va a `/admin/revision` en F1. Mide qué la hace tardar 30–35 s después de cargar (render de miles de filas, casi seguro): paginar o virtualizar la lista. Mientras tanto, no subas el límite de la prueba.

## 4. Orden para la siguiente sesión

1. Detector de palabras corregido (§1) + quitar `frame-ancestors` de la meta.
2. Subir los tres documentos de plan a `docs/`.
3. **F1** (dos zonas y redirecciones).
4. **F2** con `distribution` y `OPOFUENTE_STUDENT_OPPOSITION` (§2.1 y §2.3).
5. Tokens + `src/ui/` + `/admin/ui` → capturas → **parar y pasármelas**.
