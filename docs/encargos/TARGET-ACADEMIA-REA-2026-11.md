# Objetivo de academia para estudiar con REA (y qué nos falta)

**Fecha:** 9 de noviembre de 2026 · **Origen:** encargo directo de David en el chat de relevo
(«probar la app contra una academia real… deja escrito qué app sería buen objetivo y por qué»).
**Para:** la siguiente sesión de REA en `F:\Proyectos\ProyectoServidor\rea-sandbox\estudiar-apps`.

> Este documento **elige un objetivo y lo justifica con evidencia**, no es un estudio de producto.
> No se ha copiado contenido de ninguna academia: solo se describe la **forma** de su app y de sus
> datos. Nada de lo aquí escrito se redistribuye.

---

## 0. Criterio de elección (el del propio laboratorio)

`estudiar-apps\AGENTS.md` exige **una función por investigación**, tres cestas (demostrado /
hipótesis / desconocido) y objetivos autorizados. `REFERENCIAS.md` §5 añade tres preguntas:

1. ¿Hace bien exactamente lo que OpoFuente quiere mejorar?
2. ¿Se puede observar como usuario?
3. ¿Es analizable sin fricción?

La función que OpoFuente tiene que mejorar no es «un temario»: es **cómo una app de academia
convierte un temario en estudio diario** (test por tema, progreso, repaso) y **cómo ata cada
pregunta a la norma**. El hueco declarado en `INVESTIGACION.md` es la **vigencia normativa** por
tema/pregunta (B-018), no el temario en sí (ya lo tenemos, versionado).

---

## 1. Laboratorio: estado verificado hoy (9/11/2026)

Comprobado con `node rea-local.mjs` desde el laboratorio:

| Pieza | Estado |
|---|---|
| REA CLI | **6.4.0** (`rea-local.mjs`), 127 comandos, 170 herramientas MCP |
| Ghidra / JDK | **sanos** (`ghidra-java` 21.0.12.1, decompile x86_64 correcto) |
| MCP de REA en DSH | **no registrado** en esta sesión: no hay herramientas REA en el cliente; se usa el CLI |
| Chrome | **156.0.8078.81** (`C:\Program Files (x86)\Google\Chrome\Application\chrome.exe`) |
| JADX (APK) | **no instalado**: `inspect-android-package` responde `capability_unavailable` y pide `REA_JADX_MCP_JAR` (jadx-headless-mcp 0.7.1) |
| Inventario de APK | **sí funciona** con `inspect-artifact` (sin JADX) |

**Ruta del laboratorio:** la skill `rea-windows-local` dice `F:\EspacioCodigo\ProyectoServidor\rea-sandbox`,
pero ese directorio está **vacío**; el bueno es **`F:\Proyectos\ProyectoServidor\rea-sandbox`**
(contiene `estudiar-apps`, `rea-local.mjs`, `tools\ghidra`, `tools\jdk`). Conviene corregir la skill
y `ESTADO.md` de `estudiar-apps`; si no, la próxima sesión arranca en un directorio muerto.

---

## 2. Candidatas (verificadas hoy)

| Objetivo | Qué es | Acceso | Qué se puede estudiar | Fricción |
|---|---|---|---|---|
| **EstudiaTAI v1.0.5** (APK, en disco) | App Android de test de TAI, **Kotlin + Jetpack Compose**, contenido offline | **Sin cuenta**: el APK ya está en `C:\Users\David\OneDrive\Escritorio\EstudiaTAI-v1.0.5.apk` (7.469.693 bytes, SHA-256 `20774d32…` medido por REA) | Estructura del contenido (4 bloques × temas), banco de test por tema, app móvil offline | Análisis de **contenido** sí (JSON en `assets/`); análisis de **código/UI** bloqueado hasta instalar JADX. No hay emulador en el laboratorio |
| **Oposiciones.red** (web) | Portal de estudio con simulacros atados al BOE y «dos fechas» de vigencia | Público sin cuenta en la ficha de simulacro (verificado: la página muestra el reparto y una pregunta resuelta; el resto pide suscripción de 9,90 €/mes) | **Cómo presenta la vigencia normativa** y el reparto real de un temario; cómo enlaza cada respuesta a su artículo del BOE | Web con muro parcial: solo lo visible sin cuenta. Nada de descargar su banco ni saltarse el muro |
| **TestReales** (web) | Exámenes oficiales por cuerpo y año, gratis | Público sin cuenta en el listado y en exámenes marcados «GRATIS» (verificado) | Cómo lista un examen oficial por convocatoria/año y cómo corrige con explicación | Mismo límite: solo lo público |
| **OpositaTest** (web) | Líder de test de oposiciones | Catálogo público; **el test requiere cuenta** (`/acceder`) | Flujo de test y estadísticas, pero **detrás de registro/pago** | No se puede observar la parte que interesa sin cuenta de David. No es primer objetivo |

### El hallazgo que decide: el APK de EstudiaTAI

Inventario estático con REA (`inspect-artifact`, evidencia `ev_bb3bc559…`, 185 ocurrencias, 147
nodos) y lectura de sus recursos:

- Android **Kotlin + Compose** (no Flutter, no React Native): `classes.dex`, `classes2.dex`,
  librerías `androidx.compose.*` y `lib/*/libandroidx.graphics.path.so`.
- Contenido **offline en `assets/`**: 21 JSON, uno por bloque/tema
  (`assets/block1/topic1.json` … `assets/block4/topic9.json`).
- `block1/topic1.json` es un **índice** (lista de 4 objetos `{blockId, topics}`).
- Los demás son `{topicId, questions:[…]}`: **402 preguntas** repartidas en 19 ficheros
  (15–32 por tema), con la forma `{questionId, question, options[4], correctAnswer:int}`.
- **No hay** en la pregunta: explicación, artículo/norma, fecha de vigencia ni convocatoria.
  Es un banco de test por tema, offline, sin trazabilidad normativa.

Eso es exactamente el contraste que buscábamos: una academia real resuelve **practicar por tema**
(volumen y offline) y **no** resuelve lo que OpoFuente ya modela (temario versionado, procedencia,
evidencia, corrección exacta). Y confirma el hueco de B-018: su pregunta no está atada a la norma.

---

## 3. Recomendación

### Objetivo nº 1 — EstudiaTAI v1.0.5 (APK ya en disco)

**Por qué:**
- Es de **TAI**, que es el objetivo real de OpoFuente (no una academia genérica de administrativo).
- **No necesita cuenta ni pago**: el artefacto existe y es analizable en local.
- **Cero fricción de red**: el contenido está en `assets/`, así que el 80 % de la pregunta
  («cómo organiza una academia el estudio por tema») se responde **sin emulador y sin JADX**.
- Es pequeño (7,5 MB) y su identidad está medida: ideal para el ciclo corto del laboratorio
  (inventario → contenido → informe con tres cestas).

**Función única de la primera investigación (una, no tres):**
> **«Cómo convierte EstudiaTAI un bloque del temario en una sesión de test por tema, y qué le
> enseña al alumno al corregir.»**

Pasos concretos:
1. Inventario (hecho: `inspect-artifact`, `ev_bb3bc559…`).
2. Contenido: `assets/*.json` — bloques, temas, número de preguntas por tema, forma de la
   pregunta; **sin copiar el texto** de las preguntas.
3. UI/corrección: instalar **JADX** (decisión de David: es un JAR de terceros que REA no descarga)
   y usar `inspect-android-package`; si no, dejar la UI como **desconocido** y limitar el informe
   a lo observado en los recursos.
4. Si David tiene la app en el móvil, un recorrido de 3 minutos (como se pidió en REF-TM01/TP01)
   cubre el estado vacío, el test y el resultado; esa observación va a la cesta de observación,
   no a la de «demostrado con REA».
5. Informe con las tres cestas, el «qué hago yo / por qué distinto» de
   `ESTUDIAR-LA-INTERFAZ.md` §5, y **cero** contenido copiado.

**Lo que OpoFuente puede aprender:** el mínimo que un opositor espera de una app de academia
(test por tema, offline, resultado inmediato) y qué **no** hay que imitar (banco sin explicación
ni norma). Sirve para decidir si el siguiente slice es contenido masivo, uso móvil u offline.

### Objetivo nº 2 — Oposiciones.red (web), solo para B-018

**Por qué:** es el competidor que **sí** resuelve lo que a nosotros nos falta (vigencia normativa,
pregunta atada a artículo, «vuelve al repaso»). La función a estudiar no es su catálogo, sino
**cómo presenta las dos fechas y el retorno al repaso**, que es B-018. Receta: Chrome con
`--remote-debugging-port=9222` y las herramientas web de REA; solo páginas públicas, sin cuenta,
sin muro y sin descargar su banco.

### Lo que **no** se propone

- Descompilar apps tras registro/pago (OpositaTest, campus de MasterD/Adams) sin cuenta de David.
- Copiar preguntas, temarios ni textos: **se copia la decisión de diseño, no la expresión**
  (`ESTUDIAR-LA-INTERFAZ.md` §4).
- Analizar dos objetivos en la misma sesión sin cerrar el anterior.

---

## 4. Qué nos falta (contraste medido con lo que ya tenemos)

| Pieza | EstudiaTAI | OpoFuente hoy | Conclusión |
|---|---|---|---|
| Contenido de test por tema | Sí, 402 preguntas offline | Banco propio, vacío en el corpus sintético; el real depende del material de David | **Volumen y offline** es lo que una academia da y nosotros no |
| Explicación de la respuesta | No | Sí (S06/S07, clave versionada) | Ventaja nuestra |
| Norma/artículo y vigencia | No | No (B-018 pendiente) | **Hueco real**; lo resuelve Oposiciones.red |
| Temario versionado / convocatorias | No: un temario plano | Sí (S13, versiones y particularidades) | Ventaja nuestra; no lo busques en la academia |
| Móvil | Sí (app nativa) | Web responsive | Decisión de producto, no de REA |
| Progreso y repaso | Por confirmar (UI no analizada) | Errores y repaso determinista | Verificar en la UI con JADX o recorrido |

**Conclusión de producto:** la academia gana en **practicar ya** (contenido y app); nosotros
ganamos en **trazabilidad** (versión, procedencia, corrección exacta). El siguiente slice no
debería ser «más pantallas», sino **llenar el banco de preguntas por tema** y **enseñar la
vigencia normativa** (B-018). El estudio de EstudiaTAI sirve para fijar el listón de contenido.

---

## 5. Fila lista para el laboratorio (no aplicada)

En `estudiar-apps\REFERENCIAS.md` §3 (datos y artefactos), añadir cuando se empiece:

```markdown
| **EstudiaTAI v1.0.5** | `C:\Users\David\OneDrive\Escritorio\EstudiaTAI-v1.0.5.apk` (7.469.693 B · SHA-256 `20774d32…`) | **Test por tema de TAI, offline, Kotlin+Compose**. Inventario `ev_bb3bc559…`. Verificar 9/11/2026 |
```

En `PENDIENTES.md`, una fila nueva (proyecto destino **OpoFuente**):

```markdown
| **O-01** | Cómo organiza una academia de TAI el test por tema y qué enseña al corregir | OpoFuente | EstudiaTAI (APK) | Media | `LISTA` |
```

Y actualizar `ESTADO.md` del laboratorio con la ruta real del sandbox
(`F:\Proyectos\ProyectoServidor\rea-sandbox`) y el estado de JADX.

---

## 6. Evidencia de esta elección

- Página pública del simulacro de Oposiciones.red consultada el 9/11/2026 (dos fechas, reparto,
  pregunta resuelta y enlace al BOE): <https://oposiciones.red/estudio/simulacro/BOE-A-2025-22895>.
- Listado público de exámenes de TestReales consultado el 9/11/2026 (exámenes «GRATIS» sin cuenta):
  <https://testreales.com/explorar?cuerpo=TAI>.
- OpositaTest: el catálogo es público pero «Hacer test gratis» lleva a `/acceder`
  (cuenta), verificado en <https://www.opositatest.com/>.
- APK: identidad y estructura medidas con `Get-FileHash` y `rea-local.mjs inspect-artifact`
  (evidencia `ev_bb3bc559…`), y lectura de los JSON de `assets/` **sin reproducir su contenido**.
- Manifiesto de la app (`META-INF/.../app-metadata.properties`): `androidGradlePluginVersion=8.8.0`.

---

## 7. Límites declarados

- No se ha ejecutado la app ni se ha instalado nada: todo es análisis estático de recursos.
- No se ha analizado el código Kotlin/Compose: sin JADX es **desconocido**, no «no existe».
- No se ha iniciado sesión en ninguna academia ni se ha descargado su material.
- No se ha copiado ni se copiará contenido de preguntas: solo la forma de los datos.
