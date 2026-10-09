# Resumen completo de las rondas de trabajo (8-oct-2026)

Todo lo hecho en esta sesión, por bloques, con los commits y las mediciones. Al final: lo que queda, los
fallos que cometí (con su corrección) y lo que hay que decidir.

## Dónde está el repositorio

- **`main` = `c902f10`** («F4: clasificar las preguntas sin tema por lotes, y el fuera de temario»).
- `opofuente-main` tiene **47 ficheros sin guardar de Claude**, intactos para mí en todo momento.
- Árboles: `opofuente-arreglos`, `opofuente-alumno`, `opofuente-f2`, `opofuente-clasif`.
- **Ramas listas, con 18/18, sin fusionar**: `f5-pantalla-revision` (`82bdbb1` + `7143540`), paradas
  porque Claude tiene modificado `apps/web/src/api/queries.ts`, que también toca ese commit.
- Copias de seguridad en `F:\OpoFuente\datos\_copias` (varias de 2,47 GB, una por operación con escritura).
- Las claves de API **no han entrado en ningún repositorio**: viven en variables de entorno.

## Los bloques, en orden

### 1. La hora (`e510f97`)
El cronómetro empezaba en `2:00:03` y un examen de 120 minutos nacía agotado: SQLite no guarda zona, la
API servía la fecha sin UTC y el navegador la tomaba por hora de Madrid. Arreglado con un tipo de columna
`UtcDateTime` en las **79** columnas de fecha. Antes/después: 4.999 s reales donde contaba 12.199.

### 2. Sesiones y aviso de API caída (`a19d13a`)
Cada sesión **congela su etiqueta de contexto** (antes cinco exámenes oficiales eran cinco filas iguales);
`DELETE /study-sessions/{id}` que abandona si hay respuestas y borra si no; **un solo aviso** cuando la API
no responde, en vez de ocho «Failed to fetch»; fechas legibles.

### 3. Los apuntes por tema (`e5ce278`)
De los 53,6 s del tema I.1, **todo era la consulta** (Python eran 0,16 s): un `OR` de cinco condiciones
impedía usar los índices. Tres lecturas con índice y emparejamiento en memoria: **I.1 53,6 → 2,01 s,
II.1 51,6 → 1,99 s**, con una prueba que compara las dos consultas porque el dossier se archiva.

### 4. Diseño y capturas (`7f5b889`, `ef45b16`, `3ebe0dd`)
`npm run screens` recorre las rutas y escribe un informe con tiempos, errores de consola, axe y **palabras
prohibidas**. El detector se corrigió tras una revisión (dos listas, palabras completas, sin acentos;
11 pruebas). **0 errores de consola** en las 24 capturas. **v0**: prototipo del alumno, 21 capturas (dos
correcciones al guion: la clave necesita `v1:` y el campo es `message`). **Stitch**: 13 pantallas, 39
imágenes, con el hallazgo de que la miniatura es de 512 px y que `apply_design_system` no recolorea solo.

### 5. F1: las dos zonas (`8e10083`)
Zona de alumno (7 secciones) y panel (11), con las **diez direcciones viejas redirigidas conservando
consulta y ancla**, y fuera de la vista del alumno la bandeja, la revisión, los lotes y **la ruta del
directorio de datos**. Verificado por mí: **18/18, 257 unitarias web, 57 E2E, 503 de integración**.

### 6. Asignar tema a una pregunta, con auditoría (`ceb04a5`, `d0d6dfb`)
No existía ninguna forma por HTTP; la vez que se escribió directo en la base quedó **sin auditoría**.
Ahora `POST`/`GET`/`DELETE`, idempotente, **409 con motivo** si el destino no es un tema, actor
identificable (`local` o `llm:deepseek-flash`) y la carrera del `UNIQUE` cerrada releyendo.

### 7. Orden numérico y `distribution` (`73bb451`, `fd0f7de`, `1212871`)
`IV.10` salía detrás de `IV.1`. Arreglado **en SQL** (bloque → tema → epígrafe) y usado por el programa,
la cobertura y los temas de una pregunta: antes `['IV.1','IV.10','IV.2']`, después
`['IV.1','IV.2','IV.10']`. En la base, `position` y orden numérico coincidían en los 62 grupos, así que el
síntoma estaba en los listados planos (TAI y cuatro de Guardia Civil con `1.1.10` tras `1.1.1`).
`distribution` (`personal`/`public`) con dos migraciones separadas y **aplicadas a los datos reales**:
**4 públicos** (los cuatro exámenes del INAP) y **229 personales**, con 17.424 preguntas y 575 claves
intactas. Ojo: hay **ocho** filas con esos títulos (el importador corrió dos veces) y la migración marca
solo las cuatro activas.

### 8. La capa del alumno (`47c1399`)
`/api/v1/student/{overview,syllabus,topics/{codigo},progress}` con **esquemas propios sin campos
prohibidos** (no se filtra al final: no hay dónde ponerlos), temas por código legible y nunca UUID,
`owner_id` en las cinco tablas del progreso con migración de ida y vuelta, y las dos variables
(`OPOFUENTE_STUDENT_OPPOSITION`, `OPOFUENTE_PUBLIC_MODE`). La prueba que lo sostiene recorre **las 7
respuestas** con TAI y Celador sembrados y falla si una clave o un valor contiene lo que no debe, exigiendo
además 33 temas y progreso real: sin datos, «no hay fugas» no demostraría nada.

### 9. Los 134 epígrafes de TAI (`71f7b44`)
Derivados del **ANEXO V del BOE** dentro del constructor de fixtures, con una sola regla (punto seguido de
espacio) y un invariante comprobado antes de escribir: **los epígrafes de un tema, unidos, reproducen su
título oficial sin perder un carácter**. `plataforma.NET` no se parte. TAI pasa de 37 a **171** nodos
(4 bloques, 33 temas, 134 epígrafes) y se siembra en los datos reales con **134 altas, 0 bajas, 0 cambios**
y el hash idéntico en otras 16 tablas.

### 10. La clasificación (`c902f10` + corridas)
La ruta por lotes **no es un segundo camino de escritura** (cada fila entra por el mismo `assign_topic`:
mismo `UNIQUE`, mismo evento `question.mapped`, con una prueba que lo compara campo a campo contra la
base); un epígrafe se escribe **con** su tema; asignar un tema **levanta** la marca de fuera de temario.
El **fuera de temario** vive en su propia tabla (`0028`), con motivo validado y **sin código ni posición:
imposible confundirlo con un tema**, excluido de simulacros y exámenes oficiales y contando en la práctica.
Umbrales con la calidad medida delante: **≥0,75 se asigna; 0,5–0,75 a la cola; <0,5 no se escribe**.

**Resultado en los datos**: 1.138 asignadas, **736 a la cola**, 1.076 fuera de temario, 507 sin propuesta,
**0 errores de escritura**, confianza media 0,875. Las preguntas sin ningún mapeo pasan de **3.460 a
1.586**, y la resta cuadra (3.460 − 1.138 − 736 = 1.586). **Coste real: 1,45 $** (medido en tokens).

### 11. La pantalla de la cola (`82bdbb1`, `7143540`) — en rama, 18/18 cada commit
`/admin/clasificacion`, en el menú del panel: la cola, «Fuera de temario» y «Preguntas en dos temas». Con
**teclado de verdad** (`J/K`, `1…9`, `A` aceptar, `C` cambiar, `F`/`X` fuera de temario, `R` retirar, `S`
saltar, `G` guardar el lote), **una tarjeta por pregunta** con el enunciado, el tema y epígrafe propuestos,
la confianza y **el motivo que dio la IA**. Además: la **guarda de corrida** (dos clasificaciones no se
pisan; la marca se suelta aunque falle) y la **guarda del panel** rehecha para **derivar de
`navigation.ts` y `routes.tsx`** en vez de llevar una lista escrita a mano. Dos cosas que no se podían
hacer y ahora sí: **aceptar una propuesta no cambiaba nada** (el mapeo ya estaba y la ruta es idempotente)
y no había forma de **dejar una pregunta con un solo tema**.

### 12. Apuntes de los tres temas piloto — en marcha
IV.7, I.6 e I.1, guiados por las preguntas ya clasificadas, con dominio propio (`topic_notes`) separado del
dossier, comprobación pregunta a pregunta y marcas de revisión para lo que no se pueda sostener. **Parada
obligatoria** después de los tres para que los lean el propietario y Claude.

## Mediciones, antes y después

| | antes | después |
|---|---|---|
| Cronómetro de una práctica | 2:00:03 al empezar | hora real |
| Apuntes del tema I.1 | 53,6 s | **2,01 s** |
| Apuntes del tema II.1 | 51,6 s | **1,99 s** |
| Guardar una versión | 21 s | 3,6 s |
| Orden de los temas | `IV.1, IV.10, IV.2` | `IV.1, IV.2, IV.10` |
| Conjuntos públicos / privados | todos privados | **4 públicos / 229 privados** |
| Nodos del programa de TAI | 37 | **171** (4/33/134) |
| Preguntas sin tema | 5.249 | **1.586** |
| Coste de clasificar todo | — | **1,45 $** |

## Las cuatro trampas de las puertas (documentadas en `README` y en `docs/reviews/`)

1. **Nunca** `gates.ps1` dentro de una tubería: el stderr de `uv` se vuelve error terminante y la puerta 11
   falla con código −1 sin estar rota.
2. El registro con `Start-Process -RedirectStandardOutput`, **nunca con `>`**: los `OK:` van por
   `Write-Host` y `>` no los captura.
3. Un árbol de trabajo nuevo **no trae `data\sources`** (está ignorado por git) y la puerta 17 falla con
   «faltan fuentes locales» pareciendo un fallo del código.
4. **El puerto 8765 tiene que estar libre** para la puerta 18 (Playwright no reutiliza servidor). Y el
   directorio de datos de la E2E **debe limpiarse de verdad**: con la cola acumulada, la prueba de
   accesibilidad pasaba de 1,5 s a 39 s.

## Mis tres fallos, y qué salió de ellos

1. **Leí un resumen intermedio como total**: las «855 asignadas, 532 a la cola, 8 fuera de temario» eran
   un corte por banco, no el final. Lo real fue 1.789 preguntas tocadas y 3.581 mapeos.
2. **Heredé una cifra sin medirla**: dije que los 125 epígrafes eran de Celador; son de **Guardia Civil**.
3. **Di por bueno un informe ajeno**: creí que una corrida anterior había ido sobre una copia y había
   escrito en los datos reales.

Los tres los cazó la comprobación de otro agente, no yo. De ahí salieron tres arreglos de fondo: la
**corrección documentada** en los propios informes (con el error a la vista), la **cola agrupada por
pregunta** y la **guarda de corrida**. La lección, escrita: **una cifra que va a un documento se mide, no
se hereda**.

## Lo que ha aparecido en los datos y no buscábamos

- **754 fragmentos de reglamento importados como si fueran preguntas** (bancos «Doc adicional» y
  «baquedano»): terminan en dos puntos, no preguntan nada. No es un falso positivo de la IA; lo comprobé
  leyendo seis a mano.
- **21 preguntas cuentan en dos temas**, y **19 no las escribió la IA** (catalogación heredada y
  migraciones), incluido el examen oficial del INAP de 2025 con I.3 + II.3.
- **4 preguntas con dos temas y 9 con más de un epígrafe** por dos corridas que se pisaron, con sus
  identificadores listos para despachar.
- **227 bancos privados** cuya licencia sigue sin resolver, y ~2.100 preguntas de otras administraciones
  tratadas por contenido (la informática se queda, las leyes ajenas fuera).

## Lo que queda, en el orden del propietario

1. **Fusionar la cola de revisión** (`82bdbb1`, `7143540`): solo falta que Claude guarde
   `apps/web/src/api/queries.ts`. No se ha forzado a propósito: mover `main` por la puerta de atrás
   dejaría fuera del fichero 57 líneas nuevas, que desaparecerían en silencio al siguiente guardado.
2. **Despachar la cola**: 736 propuestas, 1.078 exclusiones y 507 sin propuesta (segunda pasada).
3. **Tests de varios temas y simulacro real** en el código que ya corrige (una sola forma de montar
   cualquier test), con el caso de comprobación del propietario: 50 aciertos, 15 fallos y 15 en blanco dan
   **28,125 sobre 50**.
4. **Las pantallas del alumno** con el diseño elegido (Stitch escritorio y editor de apuntes, v0 móvil).
5. **El panel completo**: temario editable, apuntes con versiones y publicar, preguntas con su correcta.
6. **Los exámenes anteriores del INAP** importados con sus claves.
7. **Los tres temas piloto de apuntes** (en marcha) y, tras la parada, los 33.

## Documentos

**40 ficheros** en `docs/` escritos o modificados hoy, entre ellos: `F1-LAS-DOS-ZONAS`,
`F2-PLAN-DE-EJECUCION`, `PASO-A-APUNTES-LO-QUE-HAY-QUE-DECIDIR`, `PILOTO-DE-CLASIFICACION-BANCOS-1-Y-2`,
`COLA-DE-REVISION-Y-LO-QUE-QUEDO-BLOQUEADO`, `CLASIFICACION-COMPLETA`, `PARA-CLAUDE-RESUMEN-DE-LAS-RONDAS`,
`F0-CAPTURAS-Y-PALABRAS-PROHIBIDAS` y `PUERTA-18-EN-ROJO-POR-LA-REVISION`.

## Claves de API a revocar

Las tres se pasaron por el chat y **no están en el repositorio** (verificado con `git grep` y búsqueda en
todos los árboles): v0 (`team_5TkgZHeYajsWdrcTSmbq6QzM:vcp_…`), Stitch
(`AQ.Ab8RN6JRkwFmOvREpRKsiEivNGYPhBWNVthBrefYStuldbCctw`) y DeepSeek (`sk-fe8df2cb8ead45a1bd6c402c1b527437`).
