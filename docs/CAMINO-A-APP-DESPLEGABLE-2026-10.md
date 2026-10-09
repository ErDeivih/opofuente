# De herramienta personal a app desplegable

**Para:** el propietario y DeepSeek · **De:** Claude · **6 oct 2026** · **Base:** `main = 8b09e59`
Complementa a `REDISENO-ALUMNO-TAI-Y-PANEL-ADMIN-2026-10.md`: aquel dice **qué ve el alumno**; este dice **qué hace falta para que lo vea otra persona desde internet**.

---

## 0. Diagnóstico: qué hay y qué falta

Medido sobre una copia de los datos reales:

| Aspecto | Hoy | Para desplegar |
|---|---|---|
| Usuarios | Uno solo. **Ninguna tabla tiene `user_id`**: sesiones, intentos, fallos y repasos son "del ordenador" | Cuentas, y el progreso de cada usuario separado |
| Base de datos | SQLite de **2,4 GB** con 700.000 tramos de tus fuentes, rutas de tus carpetas y 3 oposiciones | Una base pequeña con **solo** lo que se publica de TAI |
| Servidor | API en `127.0.0.1`, worker de importación, Qdrant e IA locales | Un servicio web con HTTPS y sin nada de la importación |
| Preguntas que se pueden publicar | **440** (exámenes oficiales del INAP). Las otras **16.303** son de bancos privados | Varios miles propias o de fuente pública (§2) |
| Explicaciones publicables | **0**: las 11.315 que hay vienen de material privado y están en borrador | Explicaciones propias, revisadas |
| Apuntes publicables | **0**: no existen apuntes escritos (solo el montaje automático de fuentes, con 1 instantánea guardada) | Apuntes propios por tema |
| Pruebas y puertas | `gates.ps1` en Windows, a mano | CI en la nube en cada cambio + entorno de pruebas |
| Legal | Nada (no hacía falta) | Aviso legal, privacidad (RGPD), derechos del contenido |

**Conclusión:** lo que falta no es pulir la app actual: es **separar en dos piezas** lo que hoy es una sola, y el cuello de botella real es el **contenido publicable**, no el código.

---

## 1. La decisión de arquitectura: el taller y la tienda

```
 TU ORDENADOR (el taller: la app actual)          INTERNET (la tienda: app nueva y ligera)
 ─────────────────────────────────────           ──────────────────────────────────────────
 Importar PDFs, clasificar, revisar               Alumno: temario, apuntes, tests,
 Corpus de 700k tramos, 3 oposiciones             simulacros, exámenes, fallos, progreso
 Panel admin: temas, apuntes, preguntas           Cuentas de usuario y progreso por usuario
 Marcar qué es "público"                          Solo contenido TAI publicado
            │                                                     ▲
            └──── "Publicar" ──► PAQUETE DE CONTENIDO ────────────┘
                     (temas, apuntes publicados, preguntas públicas con su correcta,
                      explicaciones publicadas, reglas del examen; con número de versión)
```

**Por qué así y no subir la app actual:**
- No sube nunca a internet tu corpus, tus rutas, tus otras oposiciones ni el material privado. La privacidad queda garantizada por construcción, no por un filtro de palabras.
- La app pública es pequeña (decenas de MB, no 2,4 GB), barata de alojar y fácil de mantener.
- Todo lo que ya funciona (importación, revisión, dossier) se queda donde está, sin rehacerlo para multiusuario.
- El panel de administración del rediseño (F6–F8) vive en el taller; un botón **Publicar** genera el paquete y lo sube.

**El paquete de contenido** (`content-pack-tai-<versión>.json` o `.sqlite`): temario, `topic_notes` publicadas, preguntas con `distribution = public` y su clave, explicaciones publicadas, `exam_parts`/`exam_rules`. Lleva **ids estables** (`stable_key`) para que, al publicar una versión nueva, el progreso de los usuarios siga apuntando a la misma pregunta. Si una pregunta cambia de correcta, el paquete lo dice y la app recalcula los intentos afectados.

---

## 2. El contenido: el trabajo de verdad

Para que un alumno la prefiera a una academia necesita, como mínimo: **todos los temas con preguntas, apuntes en cada tema y explicación en cada pregunta.** Fuentes legítimas:

1. **Exámenes oficiales anteriores.** El INAP publica los cuestionarios y las plantillas de respuestas de convocatorias anteriores (por ejemplo, la [plantilla de TAI promoción interna 2024 modelo B](https://www.inap.es/documents/59312/2364118/Plantilla+Cuestionario_TAI_PI_2024_B_definitiva.pdf/a36bbe4a-bef1-bf10-358d-61a4548e799e)). El taller ya sabe importar examen + plantilla. Objetivo: todas las convocatorias TAI disponibles (libre y promoción interna), que son varios miles de preguntas reales, clasificadas por tema con la clasificación que ya existe.
2. **Preguntas propias** escritas en el panel (F6), por tema.
3. **Explicaciones propias**, escritas o generadas con IA **a partir de la norma o de la documentación técnica pública** y **revisadas antes de publicar**. Nunca copiadas de bancos privados.
4. **Apuntes propios** por tema (F7), con el material del taller como apoyo. Los textos legales (Constitución, leyes del BOE) se pueden citar; en España los textos legales no tienen protección de propiedad intelectual. Los apuntes de academias, no.

**Meta mínima para abrir:** los 33 temas con ≥ 40 preguntas públicas cada uno, el 100 % de las preguntas con explicación y apuntes publicados en al menos los temas del bloque I. El panel admin debe enseñar este marcador ("Listo para publicar: 21/33 temas").

---

## 3. La pila recomendada

Pensada para que la mantenga una persona, en la UE y con poco coste al empezar:

| Pieza | Recomendación | Por qué |
|---|---|---|
| Base de datos y cuentas | **Supabase** (Postgres en región UE + Auth con email/enlace mágico y Google) | Cuentas, contraseñas y recuperación sin programarlas; copias de seguridad incluidas. Tienes el conector ya enlazado |
| Web del alumno | **Vercel** (la web React construida, estática) | Despliegue en cada `git push`, HTTPS y dominio. También tienes el conector |
| API del alumno | **FastAPI** en un contenedor (Render, Fly.io o Railway, región UE) | Reutiliza el dominio que ya existe (puntuación con −1/3, sesiones, repasos) en vez de reescribirlo |
| Errores en producción | Sentry (plan gratuito) | Saber que algo falla antes de que te lo digan |

Alternativa más simple si se prefiere un solo servicio: API + web en el mismo contenedor y Postgres gestionado. Los precios cambian: comprobar los planes vigentes antes de elegir.

**Cambios en el código que exige:**
- **Separar el código del alumno** en un paquete propio (`apps/study-api` o un módulo `opofuente.student`) que **no importe** nada de ingestión, corpus, clasificación ni rutas. Una prueba lo garantiza (análisis de imports).
- **Postgres además de SQLite**: el taller sigue en SQLite; la app pública en Postgres. La API del alumno no usa FTS5 ni nada propio de SQLite. Migraciones Alembic para las dos.
- **`user_id`** en sesiones, intentos, fallos, repasos y marcas de dudosa. Políticas RLS en Supabase (cada usuario solo lee lo suyo) **y** comprobación en la API.
- **Autenticación**: la API valida el JWT de Supabase en cada petición; nada de sesión propia.
- **Importador del paquete** en la API pública (`opofuente-student import-pack <fichero>`), idempotente y con prueba de "publicar dos veces = mismo resultado".

---

## 4. Seguridad, operación y calidad

- HTTPS, CORS cerrado al dominio propio, CSP **como cabecera**, límite de peticiones por usuario e IP, secretos solo en variables del servicio (nunca en git).
- **CI en GitHub Actions** (Linux) en cada push: pytest, vitest, lint, tipos, E2E con Playwright y el detector de palabras. `gates.ps1` sigue para el taller.
- **Dos entornos**: `staging` (se despliega solo desde `main`) y `producción` (se promociona a mano).
- Copias de seguridad diarias de la base pública y prueba de restauración mensual.
- Rendimiento objetivo: cualquier pantalla del alumno < 1 s; responder una pregunta < 200 ms.
- **PWA**: instalable en el móvil, funciona con cobertura mala (cachea la pregunta actual y envía la respuesta al volver la red).
- Accesibilidad AA (axe ya está en las pruebas).

---

## 5. Legal (orientativo: no soy abogado; conviene que lo revise alguien)

- **Aviso legal** (LSSI): titular, contacto.
- **Política de privacidad** (RGPD): qué datos (email, progreso), para qué, dónde (UE), cuánto tiempo, derechos. **Borrar cuenta** y **descargar mis datos** desde la propia app.
- **Cookies**: si solo hay las técnicas de sesión, basta con informar; si se añade analítica, banner con rechazo.
- **Contenido**: solo exámenes oficiales, normativa pública y material propio. Los 227 bancos privados y las 11.315 explicaciones que vienen de ellos se quedan en el taller (`distribution = personal`).
- **Términos de uso** y una nota visible de que no es una academia oficial ni está vinculada al INAP.

---

## 6. Revisión visual de los componentes de DeepSeek (las capturas de `/admin/ui`)

DeepSeek no puede ver imágenes; las he revisado yo. **La base está bien**: sobria, legible, el acierto y el fallo se distinguen por icono y texto, no solo por color, y el mapa de preguntas se entiende. Ajustes antes de F3:

1. **Barras de progreso sin cifra**: el Bloque I al 0 % parece vacío o roto. Poner el porcentaje a la derecha ("0 % · 0/405") y un mínimo visible.
2. **Cifras**: el subtítulo pequeño ("Bloque IV · Sistemas") bajo "78 %" se pierde; la etiqueta debe ir **encima** de la cifra, en `--text-2`.
3. **Opciones en móvil**: "Estado: Fallada" parte la línea por culpa del rótulo "✗ Tu respuesta". En pantallas estrechas, el rótulo debajo del texto de la opción.
4. **Pestañas en móvil**: "Mi progreso" salta a dos líneas. Que no se partan (`white-space: nowrap`) y que la fila haga scroll horizontal si no cabe.
5. **Botón deshabilitado**: el azul claro parece un botón activo. Gris (`--surface-2` con texto `--text-2`).
6. **Mapa de preguntas**: "sin contestar" y "contestada" se parecen demasiado. Contestada con fondo `--accent-soft` lleno; sin contestar solo con borde.
7. **El marco sigue siendo el antiguo** (cabecera con "Buscar en el corpus", estado del worker y de la IA, selector de oposición, menú lateral con Bandeja…): es lo que arregla F1, y es lo primero que salta a la vista.

---

## 7. El orden

El rediseño F1–F9 sigue valiendo; lo único que cambia es que la zona del alumno se construye **ya separada**, para que sea la app pública:

| Fase | Qué | Se acepta cuando… |
|---|---|---|
| **D0** | Ajustes visuales del §6 | capturas de `/admin/ui` revisadas por mí |
| **F1–F2** del rediseño | dos zonas + API del alumno, pero en un **módulo aislado** (`opofuente.student`) con `user_id` desde el primer día (en local, un usuario fijo) | prueba de imports: el módulo del alumno no importa ingestión/corpus |
| **F3–F5** | pantallas del alumno | recorrido de aceptación del rediseño |
| **F6–F8** | panel admin en el taller + campo `distribution` + marcador "listo para publicar" | cambiar una correcta en admin se refleja en el paquete |
| **D1** | **Paquete de contenido**: exportar desde el taller, importar en la API del alumno | publicar dos veces = mismo resultado; ninguna palabra prohibida dentro del paquete |
| **D2** | API del alumno sobre **Postgres** + autenticación con Supabase + RLS | dos usuarios de prueba no ven el progreso del otro (prueba E2E) |
| **D3** | **CI** en GitHub Actions + **staging** en Vercel/contenedor | un push a `main` deja staging actualizado y las pruebas en verde |
| **D4** | Contenido: importar los exámenes INAP anteriores, explicaciones y apuntes hasta la meta del §2 | marcador ≥ meta |
| **D5** | Legal, borrar/exportar cuenta, PWA, Sentry, copias | lista del §4 y §5 cumplida |
| **D6** | **Beta cerrada** con 5–10 opositores reales, y corregir | nadie se atasca en el recorrido; errores en Sentry resueltos |

D1–D3 pueden empezar en paralelo a F3–F5 porque no tocan las mismas piezas.

---

## 8. Lo que tienes que decidir tú

1. **Para quién**: ¿amigos y conocidos (beta cerrada, invitación) o abierta a cualquiera? Cambia el esfuerzo en legal, soporte y moderación.
2. **Gratis o de pago**: si es de pago, añade pasarela de pago, facturación y condiciones de venta. Recomendación: empezar gratis en beta cerrada.
3. **Pila**: Supabase + Vercel + contenedor (recomendada) u otra.
4. **Nombre y dominio.**
5. **Cuánto contenido propio** estás dispuesto a escribir o revisar (apuntes y explicaciones): es lo que más tiempo va a llevar y lo que decide si la app compite con una academia.
