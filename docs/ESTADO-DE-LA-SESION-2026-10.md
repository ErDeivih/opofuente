# Estado de la sesión, para retomar sin preguntar (11-oct-2026)

Escrito y actualizado por DeepSeek. Lo que hay, lo que está en rama y lo que falta, con las cifras medidas.

## 1. Dónde está todo

`main` = **`029d9ad`** (tandas f15, f16 y f17 dentro) · datos reales migrados a **`0034`** (las migraciones
`0033` y `0034` se aplicaron el 12-oct: **el botón «Esto está mal» del alumno ya guarda**) · **gasto medido
≈10,58 $ de 40** —el aviso de los 10 $ **está cruzado**— · F: con **≈20 GB libres**.

**Precio real de un tema, medido en f17: 0,70–1,21 $** (II.4 0,7014 $ · IV.2 0,7585 $ · I.8 1,2119 $). Es
menos de lo que se temía (1,2–1,5 $), porque **el 70 % de los tokens de entrada vienen de caché**. Con ese
precio, los 26 temas que faltan **sí caben** en los ≈29,4 $ que quedan, si la media se mantiene: hay que
seguir midiendo, no prometerlo.

En `main` está: la hora, las sesiones limpias, los apuntes por tema en 2 s, las capturas con su detector de
palabras, **F1 las dos zonas**, la ruta auditada de asignar tema, el **orden numérico**, `distribution` en
los datos reales, la **capa `/api/v1/student/*`**, los **134 epígrafes**, **la clasificación** (1,45 $),
**la cola de revisión con teclado**, **la puerta de cobertura cableada** —mide, lo dice y decide—, **el
motor de tests** (puntuación estimada, `compose`, simulacro, rutas), **la zona del alumno completa** con
sus tokens y sus nueve pantallas, y **la tanda de apuntes f15**.

## 2. Apuntes: el precio real, que es la cifra que gobierna lo que queda

| Tema | Cobertura (clave utilizable) | Forma | Estado | Coste |
|---|---|---|---|---|
| **IV.7** | 95,8 % (430/449) | pasa | publicado | ≈0,37 $ |
| **I.1** | 98,5 % (1.965/1.995) | pasa | publicado | 1,9593 $ |
| **I.2** | **95,2 % (669/703)** | pasa · 24.061/49.320 palabras | **publicado** | **1,2187 $** (194 llamadas) |
| **I.6** | 72,5 % (187/258) · techo 84,1 % | pasa | borrador, motivo escrito | 1,1223 $ |
| **I.4** | **88,9 % (497/559)** — le faltan 7 preguntas | pasa · repetidos 4,2 % | **borrador, motivo escrito** | **1,4625 $** (169 llamadas) |

**Un tema cuesta entre 1,2 y 1,5 $.** Quedan **26 temas**: a ese precio son **31–38 $**, y con los 7,91 $
gastados el total aterrizaría en **39–46 $** → **el techo de 40 $ va a apretar**. Decisión tomada: seguir
**por orden de valor medido** (tabla de los 33 en `ESTADO-DEL-OBJETIVO.md` §4d: I.1 1.995, I.2 835,
**IV.2 797**, I.4 577, **II.4 566**, **I.8 566**…), avisar a los 10 $ y **parar al llegar a 40 $** con todo
documentado. Si el propietario quiere los 33 enteros, hay que subir el presupuesto: es decisión suya.

**Lo que hace barato seguir**: `--prever` dice llamadas y euros antes de pagar; `--limpiar-forma` y
`--publicar` no cuestan nada; el trabajo de un tema que queda en borrador **se conserva** y volver a
lanzarlo continúa desde ahí. **IV.2 ya tiene su índice escrito, ensayado y commiteado** (761 de sus 770
grupos situados por el enunciado): la próxima tanda empieza redactándolo.

**La previsión de I.4 falló un 42 %** y la causa está medida: devolvió 11.518 tokens de salida por llamada
frente a los 5.700 de media. La constante subió a 0,0068 $ (media de cinco corridas) y la regla decide con
la cota de arriba **más un tercio** en temas normativos y densos.

## 3. Dos discrepancias anotadas, sin tocar

1. **Párrafos casi repetidos**: el §2.3 del objetivo pide **≤3 %**; el código aplica **≤5 %** (y su
   comentario dice que el 5 % viene de un informe del propietario). I.4 está en **4,2 %**: pasa el código y
   no el documento. **Bajar un listón para que algo pase está prohibido**; subirlo cambiando el código sin
   decírselo, también. Es una línea del propietario.
2. La puerta **«hechos fuera de su materia (≤3 %)» sigue sin implementar**.

## 4. En marcha y lo que falta

- **En rama**: `f16-panel-bandeja` (el panel: **la bandeja del propietario** y **«No son preguntas»**),
  con migración `0034` para el estado «en curso» y la nota de qué se ha hecho.
- **Panel (C)**: falta el resto — revisar apuntes, y las incidencias del motor ya tienen pantalla.
- **La pantalla de Tests** (elegir temas y cuántas): su entrada ya existe y dice qué hará.
- **27 temas de apuntes** (26 menos IV.2, que tiene el índice listo).
- **Los exámenes del INAP (D10)**: **32 PDF verificados** en `F:\OpoFuente\fuentes\inap-tai\` con su
  `MANIFIESTO.md`. **Falta construirlos**: `origin_scope` **no existe en el código** (columna + migración +
  esquemas + relleno + uso en el simulacro) y solo después importar (`distribution=public`). Avisos: los 4
  exámenes de TAI 2025 **ya se importaron** (migración `0026`, 8 filas para 4 exámenes) y los 3
  cuestionarios de 2018 **necesitan OCR** (Tesseract no está instalado; sí los datos de idioma).
- **Los 30 hechos con `epigraph_code` mal guardado (D4)**: `topic_facts.reassign_epigraph`, actor
  `f10:epigrafes`.
- **La entrega antigua** `s14-promover-sin-guardar` (D11): una pasada por las puertas; si 18/18, fusionar;
  si no, a `DEBT.md` y no volver.

## 5. Reglas y trampas que no hay que volver a aprender

- **Cinco trampas de las puertas**: nada de tuberías para `gates.ps1`; el registro con
  `Start-Process -RedirectStandardOutput` y **nunca** con `>`; `data\sources` en todo árbol nuevo; el
  puerto 8765 libre para la E2E; y **`DEEPSEEK_API_KEY` no se hereda al proceso hijo** (leerla del ámbito
  de usuario en cada comando).
- **Una cifra que va a un documento se mide, no se hereda.** De ahí salieron los errores de esta sesión y
  de ahí salieron sus remedios: la cola agrupada por pregunta, la guarda de corrida y el total de la
  bandeja **contado en la base** (333), no sumado de informes.
- **Una puerta que existe en un documento y no en el código no es una puerta.** Y una que existe en el
  código con otro número que el documento, tampoco: hay que decidir cuál manda.
- **Arreglar la pantalla, no la prueba.** Cuando la puerta de responsividad falló por 43 px, el arreglo fue
  la causa (17 px de cuerpo aplicados a toda la app), no el spec. Y cuando Playwright se negó a elegir
  entre **dos controles con el mismo nombre accesible** en una región, eso es un defecto de accesibilidad,
  no un capricho del test.
- **Un contador que avanza es la única prueba de que algo trabaja.** Un lanzador (`uv`) marca 0 s de CPU
  siempre: mirarlo llevó a creer colgada una corrida que estaba escribiendo (278→544 comprobaciones en
  10 min, con la conexión a la API abierta). Lo que se mide es **el avance**, no un proceso.
- **Una prueba que falla a veces y se reintenta deja de avisar.** Nada de reintentar hasta el verde.
- **Una sola corrida a la vez** (marcas `apuntes_en_curso` / `clasificacion_en_curso`).
- Copia **verificada** antes de cualquier escritura masiva; escribir solo por rutas auditadas; **18/18 para
  fusionar**.
