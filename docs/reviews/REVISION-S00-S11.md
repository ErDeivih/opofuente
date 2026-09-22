# Revisión S00–S11 — acta

**Fecha:** 19 de septiembre de 2026
**Alcance:** los doce slices entregados (S00–S11) contra su contrato literal en
`docs/product-spec/11_IMPLEMENTATION-SLICES.md`, sus criterios de aceptación, el plan de pruebas
(`10_TEST-PLAN.md`), la matriz de trazabilidad (`16_TRACEABILITY-AND-DEFINITION-OF-DONE.md`) y
`docs/DEBT.md`.
**Método:** revisión por lectura sobre el árbol en `28e0895` (S11 cerrado), slice a slice, contrastando
cada entregable y cada criterio con el código y con las pruebas que los citan. Las cifras de las tablas
de puertas **no** se reprodujeron durante la lectura (habrían exigido ejecutar las suites y escribir
cachés); sí se comprobó, para S07–S09, el recuento **exacto** de pruebas recolectadas en cada commit de
cierre, y coincidía con lo declarado. Al final de estas reparaciones se ejecutaron las 18 puertas sobre
el árbol final, y esa corrida sí está reproducida (ver «Puertas»).

**Regla aplicada al clasificar cada hallazgo**, porque no todo lo que parece un fallo lo es:

| Tipo | Qué significa | Qué se hace con él |
|---|---|---|
| **Defecto real** | el producto o la API hacen algo distinto de lo que dicen, o prometen lo que no cumplen | se arregla, no se documenta |
| **Promesa excesiva** | el código está, la documentación cuenta más de lo que hay | se corrige el texto al estado real |
| **Hueco de prueba** | el comportamiento existe, ninguna prueba lo demuestra | se escribe la prueba; si no se puede, se registra |
| **Deuda vencida** | una obligación con plazo ya superado que nadie reasignó | se cierra o se declara fuera de plazo |
| **Está, pero no se ve** | el entregable existe y la revisión no lo encontraba | no es un hallazgo: se anota la ruta |

---

## 1. Veredicto por slice

| Slice | Veredicto | Lo esencial |
|---|---|---|
| **S00** | correcto con salvedades | Repositorio, puertas, esqueleto, migración y health existen de verdad. Su documentación describía un repositorio que ya no existe. |
| **S01** | correcto con salvedades | Los cinco entregables y los cinco criterios, con las cifras oficiales del temario verificadas contra el fixture. Prometía un E2E del 403 que no existía. |
| **S02** | correcto con salvedades | Almacén atómico, inventario de solo lectura, lotes, worker con lease y Bandeja completa. La guarda `path_outside_root` no tenía ninguna prueba. |
| **S03** | correcto con salvedades | Extractores, representaciones, OCR declarado, ZIP/URL endurecidos y lector con avisos. El criterio «SSRF tras redirección» no tenía prueba que lo demostrara. |
| **S04** | correcto con salvedades | Las cinco propuestas, bandas, lote con excepciones, deshacer que restaura y audita, duplicados y cobertura: todo con pruebas y con los números del corrector coincidiendo con el código. La **puerta humana** del contrato no se ejecutó. |
| **S05** | correcto con salvedades | Documento lógico, versiones, derechos, secciones, evidencias, promoción, diff y mapeos muchos-a-muchos: completo y probado. **Colecciones: API sin producto.** |
| **S06** | incompleto → corregido | Banco de preguntas completo y bien probado, pero faltaba una mitad literal del entregable: el **asistente JSON**. No estaba declarado en ningún sitio. Cerrado en esta revisión. |
| **S07** | correcto con salvedades | Motor de sesiones, aritmética exacta y cierre de DEBT-006: reales y bien probados. El «baremo oficial» es una costura, y el cronómetro no tenía prueba. |
| **S08** | correcto con salvedades | Fórmula GC exacta, seis errores, reservas y recálculo versionado con casos a mano. El criterio de personalidad/físicas estaba implementado sin prueba. |
| **S09** | incompleto respecto a su contrato, declarado | Qdrant, embeddings, LLM real y dataset patrón no existen y están declarados (ADR-012, DEBT-014). Lo entregado está bien probado. **Tres filtros del contrato no filtraban nada.** |
| **S10** | correcto | Revisión de errores, cola, exportación y borrado con historial. Revisión propia. |
| **S11** | correcto | Cambio de material, dependencias, derivados y revisión selectiva: solo lo que depende de una sección cambiada queda pendiente. Revisión propia, con un hueco de aceptación cerrado. |

Ningún slice queda sin entregar. S06 y S09 eran los dos que no cumplían su contrato literal al
empezar esta revisión; S06 se ha completado y S09 mantiene sus ausencias declaradas con su deuda.

---

## 2. Defectos reales arreglados en esta revisión

### 2.1 El asistente JSON de S06 no existía (y no estaba declarado)

El entregable dice «Parser desde texto/documento y asistente CSV/**JSON**». Había texto, CSV con mapeo y
plantilla suelta; **ninguna** vía JSON: `ParseQuestionSetSchema.kind` admitía tres valores, la ruta tenía
tres ramas y la interfaz tres opciones. La mitad «documento» estaba declarada (DEBT-010); la mitad JSON
**no aparecía ni en `S06.md` ni en `DEBT.md`**: no es que no se viera, es que no estaba.

**Arreglado:**

- `domain/questions.py`: `parse_questions_json` con `JSON_QUESTION_FIELDS`, `JSON_UNSTORED_FIELDS`,
  `_json_rows`, `_json_key_value` y `_json_ignored_fields`. Entiende una lista o un objeto con
  `questions`/`items`; resuelve la clave como letra, posición, texto de la opción o lista; una pregunta
  mala **no** aborta el lote; un texto que no es JSON se declara como incidencia y no se inventa nada.
- `application/question_service.py`: `import_from_json` (misma ruta que el CSV, mismo informe).
- `api/question_schemas.py` y `api/routes/questions.py`: `kind="json"` y su rama.
- `apps/web`: `ImportKind` gana `json`, el panel ofrece la opción y explica el formato que espera.

### 2.2 Tres filtros del contrato de búsqueda no filtraban nada (S09)

`SearchRequestSchema` aceptaba `opposition_id`, `convocation_id` y `curriculum_node_ids`, y el
repositorio **solo los guardaba** en `filters_json` para auditoría: nunca los aplicaba. `05_RAG §2` pide
que la evidencia esté asignada a la convocatoria activa o compartida explícitamente, y eso no ocurría.
Buscar con el ámbito de TAI podía devolver material de Guardia Civil sin decirlo, y ninguna prueba
pasaba esos filtros.

Y el mismo repositorio filtraba **después** del `LIMIT`: pedía los mejores `limit*4` por `bm25` y luego
descartaba por documento, idioma o autoridad sin motivo, así que un fragmento elegible podía
desaparecer de la respuesta y la pantalla afirmaba «ningún fragmento publicado responde» sobre algo que
sí respondía.

**Arreglado** en `infrastructure/search_repository.py`:

- la consulta es una constante (`SQL_BUSQUEDA`) y los valores van siempre como parámetros ligados,
  con `bindparam(expanding=True)` para las listas (una cadena constante no puede interpolar nada, y la
  regla de seguridad del proyecto no admite excepciones);
- el ámbito de programa se resuelve con una **CTE recursiva** sobre `curriculum_nodes` —pedir un bloque
  incluye sus temas y epígrafes, igual que hace la cobertura— y por los **mapeos** de la versión
  (versión, artefacto, representación, sección o fragmento), con los mapeos rechazados fuera;
- los cuatro filtros explícitos viajan al `WHERE`, así que la ventana de `bm25` ya está acotada;
- lo que sigue decidiéndose en el dominio es la **elegibilidad** (vigencia, estado y calidad), y lo
  descartado se informa con su motivo.

### 2.3 La pantalla Programa decía que la cobertura no se calcula

`ProgramPage.tsx` mostraba «No disponible todavía: se calcula cuando existan fuentes asignadas (S05)» y
el docstring de `api/routes/profiles.py` afirmaba que `GET /curriculum-nodes/{id}/coverage` no existía.
Esa ruta existe desde S04 (`api/routes/classification.py`) y es la que sostiene la pantalla de Revisión.
Texto corregido en los dos sitios para decir dónde se calcula de verdad.

### 2.4 `/capabilities` prometía un OCR que no iba a llegar

El estado `configured_unverified` decía «La extracción OCR real se implementa en S03» y se etiquetaba en
la interfaz con «S03», un slice ya cerrado que decidió **no** implementarlo. Quien tuviera Tesseract
instalado leía que el OCR estaba en camino. Ahora dice que el binario está pero la aplicación **no lo
llama**, y no se promete ningún slice.

### 2.5 La bandeja describía una omisión que ya no ocurre

`TrayPage.tsx` listaba «formatos sin extractor» entre los omitidos del inventario, cuando desde S03 esos
formatos **se conservan** (`unsupported_preserved`). El texto pasa a «ficheros no soportados».

### 2.6 El README describía S03 como estado actual

Decía «Estado actual: S03 completado» y afirmaba que no había clasificación, biblioteca, IA ni sesiones
de estudio: todo eso existe desde S04–S07 y S09. También documentaba `uv sync` + `npm install` mientras
`scripts/install.ps1` ejecuta `uv sync --locked` + `npm ci`. Reescrito al estado real (S11), con lo que
**todavía no** existe y por qué.

---

## 3. Huecos de prueba cerrados en esta revisión

| Criterio que no tenía prueba | Prueba añadida |
|---|---|
| S03 «SSRF bloquea redes no permitidas **tras redirección**» | `test_el_fetch_no_sigue_una_redireccion_hacia_una_red_interna` (`test_safe_inputs.py`): la primera respuesta redirige a `interno.test` → `127.0.0.1` y la conexión falsa **revienta** si alguien intenta el host interno, así que la prueba no pasaría con una implementación que solo validara la URL inicial |
| S02 guarda `path_outside_root` de la copia | `test_una_entrada_cuya_ruta_resuelve_fuera_de_la_raiz_no_se_copia` (`test_import.py`): entrada con `../secreto.txt`, incidencia, fallo de la entrada y un solo artefacto creado |
| S05 `downgrade` de la 0013 «ejecutado de verdad» (y 0014–0020, ninguno lo tenía) | `test_migrations_downgrade.py` (nuevo, 8 pruebas): recorre la cadena hasta 0012 escalón a escalón comprobando revisión y tablas retiradas, vuelve a subir, y alcanza cada revisión **desde cero** |
| S08 «personalidad y físicas no se presentan como evaluadas» | `declara en el resultado lo que la convocatoria no evalúa y no lo presenta como evaluado` (`study.test.tsx`): las dos reglas de la convocatoria llegan al panel del resultado |
| S11 «reindexación/caché respetan la revisión del corpus» | `test_confirmar_un_cambio_actualiza_la_revision_y_lo_que_la_busqueda_puede_citar` y `test_una_respuesta_guardada_conserva_la_revision_con_la_que_se_respondio` (`test_changes.py`) |
| S10 «Inicio recomienda la siguiente tarea» | `home.test.tsx` (nuevo, 3 pruebas) |
| DEBT-011 paginación del banco | `pagina el banco con el desplazamiento en el servidor y dice en qué tramo está` (`questions.test.tsx`) |
| E2E-05 «practicar las aceptadas» | `question-practice.spec.ts` (nuevo): importa por JSON, activa la plantilla y **practica** la pregunta, comprobando que la clave del JSON llega a la corrección |
| S06 asistente JSON | 5 pruebas de dominio + 3 de integración + 1 de componente |

---

## 4. Deuda: lo que se cierra y lo que se declara

**Cerrada:**

- **DEBT-011** (la pantalla del banco solo enseñaba 100 preguntas). Su plazo era «antes de S09» y S09,
  S10 y S11 se entregaron sin cumplirla ni reasignarla: era una deuda vencida leída como «abierta y en
  plazo». Cerrada con paginación real (desplazamiento en el servidor, tramo visible, «página anterior /
  siguiente», y el filtro vuelve a la primera página) y su prueba de interfaz. Queda declarado en la
  misma entrada que la **lista de conjuntos** sigue pidiendo `limit=100`.

**Abierta y fuera de plazo, ahora declarada como tal:**

- **DEBT-010** (preguntas sin enlazar a su sección): plazo «antes de S11», S11 entregado y la obligación
  sigue viva. `S11.md` ya reconocía que las aristas hacia preguntas llegarán «cuando llegue DEBT-010».
- **DEBT-013** (recálculo en bloque): plazo «antes de S09/S11», los dos entregados y el recálculo sigue
  siendo de una sesión.

**Nuevas:**

- **DEBT-017** — las colecciones existen en la API y no en la interfaz (S05). El backend está completo y
  probado; `apps/web/src` no tiene una sola coincidencia de `collection` y `S05.md` las presentaba como
  visibles en el producto.
- **DEBT-018** — la puerta humana de S04 (`11_IMPLEMENTATION-SLICES.md`: «importar copia de 20–50
  archivos TAI y medir revisión; si no ahorra tiempo, no iniciar S05 sin rediseño aprobado») no se
  ejecutó y S05 arrancó igualmente. La evidencia mínima de RF-03 pide «métricas de muestra» y las únicas
  que hay son del dataset sintético. Es una condición previa al uso de material real, no una mejora.
- **DEBT-019** — el estado `unsupported_preserved` se guarda y se sirve, pero no hay prueba de interfaz
  ni de contrato que lo muestre legible, y la documentación de S02 describe la omisión que ya no ocurre.
  (Es la parte del cierre de DEBT-008 que se apoyaba en pruebas de interfaz y un E2E que no existían.)

**Revisadas y correctas:** DEBT-001 (S12), DEBT-002 (S02), DEBT-003 (condición previa), DEBT-004 (S03),
DEBT-005 (S04), DEBT-006 (S07), DEBT-007 (S12), DEBT-008 (S03, con la salvedad de DEBT-019), DEBT-009
(S06), DEBT-012 (S11+, coherente con lo que hay), DEBT-014 (S10+), DEBT-015 (S12), DEBT-016 (S11+).

---

## 4 bis. Lo que necesita una decisión del propietario

**ADR-013 — rutas añadidas al contrato** (nuevo, `docs/decisions/`). Siete slices declararon rutas
fuera de `08_API-CONTRACT.md`, cada una en su ficha y en el `summary` de la ruta, y todas quedaron como
«pendiente de ratificación» repartidas por siete documentos. Lo que faltaba no era la declaración, era
una **lista única que se pudiera aprobar de una vez**: es lo que hace el ADR, con la consecuencia
escrita de retirar cada una.

Lo que hay que ratificar, en corto:

| Decisión | Qué implica aceptarla | Qué implica rechazarla |
|---|---|---|
| Las rutas añadidas siguen (ADR-013) | el contrato escrito deja de ser la lista completa de rutas; el OpenAPI sí lo es | hay que retirar las rutas señaladas y asumir la consecuencia de cada una (pantallas sin datos que ya tienen) |
| `POST /classification-runs` (S04) | la clasificación se puede pedir desde la interfaz | Revisión no puede lanzar una clasificación nueva |
| `GET /documents/{id}/diff` (S05) | la pestaña «Versiones y diff» compara de verdad | se pierde el diff de versiones |
| `GET /study-sessions` (S07) | se puede retomar una sesión sin recordar su id | no hay forma de listar sesiones |
| `POST /study-sessions/{id}/recalculate` (S08) | corregir una clave recalcula sin cambiar notas a escondidas | una clave mal importada no se puede corregir hacia atrás |
| Las 16 rutas de S09/S10/S11 | las tres pantallas (Buscar, Errores, Cambios) funcionan como se ven | cada pantalla pierde la mitad de lo que enseña |

Ninguna de estas rutas es un atajo: todas siguen el mismo contrato de errores, la misma comprobación de
`Origin` y la misma validación de esquema que las del contrato. Lo que se pide es la decisión, no la
corrección.

---

## 5. Lo que no se ha podido comprobar, dicho sin rodeos

- **Las cifras de las tablas de puertas de cada slice no se reprodujeron durante la lectura.** Habría
  exigido ejecutar las suites y escribir dentro del repositorio. Lo que sí se comprobó: los recuentos
  exactos de pruebas recolectadas en los commits de cierre de S07, S08 y S09 coinciden con lo declarado,
  incluidos los desgloses por fichero y los E2E por construcción (bucles de viewports).
- **El inventario del propietario que cita `S04.md` (109 ficheros, 0 omitidos, 0 incidencias) no es
  verificable**: la cifra solo consta en la ficha del slice y no hay artefacto versionado del
  inventario. La copia se inventarió en lectura y **no** se importó (ver DEBT-018).
- **El `sha256` de los fixtures de perfiles frente a las fuentes oficiales** no se ha vuelto a calcular:
  lo que hay es el manifiesto con su hash, la cita literal y la prueba de que el manifiesto declara las
  fuentes y sus derechos.
- **Que CI se haya ejecutado alguna vez**: el repositorio sigue **sin remoto**, así que el flujo de
  GitHub Actions está escrito y sin historial de ejecuciones. Es coherente con la limitación declarada
  en `S00.md`.
- **El recuento de ficheros que informa `ruff format`** (248 en S11, 249–251 ahora) no cuadra con el
  número de ficheros `.py`/`.pyi` del árbol. Como coincide exactamente con la cifra declarada para el
  mismo commit y sale de la herramienta, se toma como salida real y no como cifra inventada; no se ha
  averiguado de dónde sale el extra.

---

## 6. Deriva documental corregida o declarada

Los documentos de slice son **registros históricos**, pero se leen como estado actual, y varios habían
quedado congelados antes de slices posteriores. Corregido en las fichas afectadas; lo que no se corrige
aquí queda listado para no perderlo:

| Documento | Qué decía | Estado real |
|---|---|---|
| `README.md` | «S03 completado»; sin clasificación, biblioteca, IA ni sesiones; `uv sync` + `npm install` | S11; todo eso existe; `uv sync --locked` + `npm ci` — **corregido** |
| `S00.md` | «15 puertas», «10 scripts», `workers/` vacío, 403/404 fuera del contrato | 18 puertas, 14 scripts, worker real, 403/404 documentados |
| `S01.md` | 403 «probado en integración y E2E»; dos índices únicos comprobados provocando `IntegrityError` | no hay E2E del 403; solo se dispara el de convocatoria |
| `S02.md` | tres nombres de prueba inexistentes; `/files`, `/paste`, `/url` → 404; `.pptx`/`.xlsx`/`.epub` no se copian | las rutas existen y el contrato exige que estén; los formatos se conservan |
| `S03.md` | `safe_xml` como defensa del DOCX; 26 pruebas en `test_extractors.py` | la defensa real está en `extractors/docx.py`; hay 50 |
| `S04.md` | 160 vs 162 pruebas de integración; lista de ficheros incompleta | incoherencia menor, sin corregir |
| `S07.md` | el repaso de errores no existe y responde 409 | existe desde S10 |
| `S08.md` | no menciona los modelos A/B | el mecanismo vive en S06 |
| `S09.md` | `downgrade` «probado»; «nueve esquemas»; `include_private` como interruptor de búsqueda | ninguna prueba ejecutaba ese `downgrade` (ahora sí, ver §3); hay 10 esquemas; la búsqueda no expone ese campo |

---

## 7. Puertas

Se ejecutaron las 18 puertas de `scripts/gates.ps1` sobre el árbol final de esta revisión, con el
directorio de datos del E2E borrado antes de empezar (acumularlo hace fallar pruebas que cuentan
elementos). Resultado: **18/18 en verde, código de salida 0** (quinta corrida; las cuatro anteriores
fallaron y están contadas abajo, porque un «18/18» sin eso no dice nada).
Los recuentos del árbol final, que son los que hay que leer en lugar de los de cada slice (cada uno
declara los suyos y son de árboles históricos):

| Puerta | Resultado |
|---|---|
| 1 | `ruff format --check`: 251 ficheros ya formateados |
| 2 | `ruff check`: sin avisos, incluidas las reglas de seguridad |
| 3 | `mypy` estricto: 124 ficheros sin errores |
| 4 | `eslint`: sin avisos |
| 5 | `typecheck` TypeScript: sin errores |
| 6 | unitarias backend: **431** (S11 declaraba 425) |
| 7 | integración backend: **348** (S11 declaraba 331) |
| 8 | contrato: 23 |
| 9 | componentes (Vitest): **148** (S11 declaraba 142) |
| 10–17 | contrato sincronizado, builds, migración hasta `0020`, esquema con `sqlite3`, siembra 268 entidades, siembra idempotente, fixtures por `sha256` |
| 18 | E2E (Playwright): **35** (S11 declaraba 34) |

Las diferencias son exactamente lo añadido en esta revisión (ver §3), y no un cambio de árbol
silencioso. La corrida verde tardó 17:41 minutos de reloj, con la integración comiendo 10:38 de esos
minutos: es el precio de las suites de base de datos reales, y no se ha tocado para «ganar tiempo».

**Corridas que fallaron, y por qué**, porque un «18/18» sin esto no dice nada:

1. La primera falló en la puerta 1: dejé dos ficheros de prueba sin formatear.
2. La segunda falló en la puerta 9 (`program.test.tsx`), y **tenía razón**: la prueba seguía esperando
   el texto viejo de Programa, el que decía que la cobertura no se calcula. Al corregir el texto del
   producto, su prueba tenía que cambiar con él.
3. La tercera volvió a fallar en la puerta 9, esta vez en `intake.test.tsx`, por una prueba **inestable
   de verdad**: escribir un texto largo carácter a carácter en un `textarea` controlado que
   re-renderiza por pulsación tardaba más que el tiempo límite y llegaba a colar un espacio entre
   letras (`Suelto.` llegaba como ` S uelto.`). Arreglado con `paste`/`fireEvent.change`, que es lo que
   hace una persona al pegar material. Es un fallo del método de prueba, no del producto, y por eso se
   arregla donde está. La suite de componentes se repitió cuatro veces seguidas después del arreglo
   (148/148 cada vez) antes de dar la puerta por buena.
4. La cuarta llegó hasta la puerta 18 y falló en **dos** guiones E2E, los dos por culpa de esta misma
   revisión: `program.spec.ts` seguía esperando el texto viejo de cobertura (el mismo cambio de §2.3,
   ahora en la capa de navegador), y el guion nuevo de practicar tenía una **carrera**: comprobaba el
   encabezado de la configuración justo después del clic de «Preparar otra sesión», sin esperar a que
   terminara la consulta que ese clic dispara. Se arregló esperando a que el botón desaparezca, que es
   esperar a lo que de verdad cambia.
5. La quinta corrida es la que cierra la revisión; su resultado está en el commit.

Ninguna de las cuatro anteriores se resolvió tocando una configuración de puertas ni relajando una
aserción: en los cuatro casos había algo que arreglar de verdad.

---

## 8. Qué criticaría un revisor senior de esta revisión

1. **He arreglado tres cosas que no eran «revisar».** Reimplementar el asistente JSON, hacer que los
   filtros de ámbito filtren y paginar el banco son cambios de producto hechos durante una revisión.
   El método del proyecto dice que la deuda no se implementa fuera de su slice; la defensa es que los
   tres eran **entregables o criterios ya prometidos** y no mejoras nuevas (S06 JSON, contrato §8 de
   S09, criterio de cierre de DEBT-011), pero conviene decirlo en voz alta: la revisión ha ampliado el
   alcance, y quien lea el diff debe poder distinguir «arreglo» de «mejora».
2. **Quedan cuatro cosas que sé y no he cerrado**: la interfaz de colecciones (DEBT-017), la puerta
   humana de S04 (DEBT-018), el estado conservado sin extractor en la pantalla (DEBT-019) y la lista de
   conjuntos sin paginar. Ninguna es un misterio: están escritas con su criterio de cierre. Lo que no
   haría es presentar esta revisión como «todo verde»: está verde lo que se ejecutó, y lo que no se
   ejecutó está dicho en §5.
3. **La deriva documental no se ha corregido entera.** He tocado las fichas de los slices donde el texto
   era **falso para el usuario** y he listado el resto en una tabla. Corregir cuarenta frases de ocho
   documentos históricos habría producido un diff enorme y difícil de revisar, a cambio de nada que el
   producto note. Es una decisión, no un olvido, y por eso está escrita.

---

## 9. Cierre posterior de lo que esta revisión dejó abierto (21 de septiembre de 2026)

Esta acta es del 19 de septiembre y describe lo que había entonces. Lo que sigue se ha cerrado
**después**, y se apunta aquí para que quien empiece por este documento no lea como viva una deuda ya
cerrada. El registro vivo es `docs/DEBT.md`.

| Lo que esta revisión dejó abierto | Cuándo se cerró y dónde está la prueba |
|---|---|
| **DEBT-001** (el destino de los datos era un booleano global) | 21 de septiembre: clasificación por proveedor con su motivo, y el booleano retirado del contrato **y** de `Settings` |
| **DEBT-010** (una pregunta importada no quedaba enlazada a su sección) | 20 de septiembre: `POST /question-sets/{id}/import-document` crea la cita de cada pregunta y la ficha abre el original. ADR-014 decide lo que **no** se guarda (la parte detectada y las etiquetas) |
| **DEBT-012** (simulacro y diagnóstico declarados y sin implementar) | 21 de septiembre: los dos modos construidos de punta a punta y el contrato declara los cinco |
| **DEBT-013** (el recálculo no se podía hacer en bloque) | 20 de septiembre: recálculo en bloque con informe por sesión, y la pantalla dice cuántas sesiones quedan desactualizadas |
| **DEBT-015** (el índice no se podía rehacer desde la interfaz) | Entregado en S12; la entrada se escribió al revisar el registro de deuda |
| **DEBT-017** (las colecciones existían en la API y no en la interfaz) | 20 de septiembre: pantalla, filtro en el servidor, alta y **baja** de miembros |
| **DEBT-019** (el estado conservado sin extractor no llegaba a la pantalla) | 20 de septiembre: la bandeja enseña el nombre legible y su motivo |
| La lista de conjuntos sin paginar (nota de DEBT-011) | **Sigue abierta** como parte viva de DEBT-011, tal como se declaró |

Y lo que sigue abierto de verdad, con su motivo: **DEBT-003** (condición previa a publicar),
**DEBT-014** (no hay proveedor de lenguaje ni de embeddings: es una decisión, ADR-012), **DEBT-016**
(necesita datos reales de estudio y un ADR con los umbrales) y **DEBT-018** (la puerta humana de S04: la
mitad de la máquina está medida con 30 ficheros reales y falta el tiempo de revisión del propietario).
Las tres primeras no se pueden cerrar escribiendo código; la cuarta necesita a una persona.
