# Traspaso del trabajo de material a otro agente (OpoFuente, octubre de 2026)

Este documento lo escribió el agente que ha estado **metiendo y clasificando el material** de la aplicación
durante septiembre y octubre de 2026. Va dirigido a otro agente (Claude) que llegue a arreglar código o a
mejorar cosas. Está escrito para que no tengas que deducir nada: qué es el proyecto, cómo está hoy, qué se ha
hecho, **qué defectos de la aplicación se encontraron y cómo se reproducen**, qué trampas tiene su API, qué
herramientas hay ya escritas y qué queda pendiente.

Regla que se ha seguido en todo este trabajo, y que conviene mantener: **ninguna afirmación sin una medición y
su comando**. Todo lo que va aquí con un número se puede volver a medir.

---

## 1. Qué es OpoFuente

Aplicación **local y de un solo usuario** para preparar oposiciones. El propietario estudia con ella: guarda su
material, lo clasifica por el temario oficial, busca en él, monta un banco de preguntas por tema y hace
simulacros.

| | |
| --- | --- |
| código | `F:\temp-opofuente\opofuente-main` (monorepo: `apps/api` FastAPI, `apps/web` React + Vite) |
| datos de verdad | `F:\OpoFuente\datos\opofuente.sqlite3` (SQLite + FTS5) y `F:\OpoFuente\datos\{artifacts,extracted}` |
| API | `http://127.0.0.1:8765/api/v1` (loopback; el prefijo `/api/v1` importa: sin él todo da 404) |
| web | `http://127.0.0.1:5173` |
| oposiciones sembradas | `tai-age-2025` (TAI, 33 temas), `gc-cabos-guardias-2026` (Guardia Civil, 25 temas + 125 epígrafes), `celador-sacyl-2022` y su estabilización (fuera del alcance de este trabajo) |
| documentación del proyecto | `docs/` del repo: `DEBT.md` (deudas), `decisions/` (ADR), `slices/` (entregas), `product-spec/`, `OPERACION.md` |

Arranque: `scripts\api.ps1` (API) y `npm run dev:web` (web). Para consultar la base sin pelearse con
PowerShell hay un script de solo lectura en la carpeta de herramientas (ver §6).

**Quién trabajó en qué.** En este repositorio hay **otro agente trabajando en el código** (pantallas de
biblioteca, promoción de material, pruebas E2E): sus ficheros modificados se ven en `git status`. El trabajo de
este documento es el de **material y datos**, y se hizo casi todo por la **API**, no tocando el código. Si vas a
tocar código, mira `git status` antes.

---

## 2. Cómo está hoy (medido el 01-10-2026)

| | |
| --- | --- |
| preguntas en el banco | **16.984** (en 233 conjuntos) |
| con clave | 16.504 |
| con cita | 16.489 |
| **con tema de TAI** | **9.342** |
| con tema de Guardia Civil | 241 (241 de 241) |
| sólo con bloque | 2.238 |
| sin ningún mapeo | 5.349 |
| documentos en la biblioteca | **4.477** (todas sus versiones aceptadas) |
| versiones sustituidas | 1.446 (histórico, no cuentan) |
| **tramos citables** | **700.277** |
| mapeos al programa | 38.762 |
| oposiciones | TAI: 33 de 33 temas con material · GC: 25 de 25 |
| tema con menos material | III.4 (1.055 fragmentos) y II.2 (1.126) |
| tema con menos preguntas | IV.3 (70) y IV.4 (74) |
| búsqueda | funciona, **1,5 a 5,7 s** por consulta (ver §7, es el problema abierto) |

### De dónde sale el material

- `F:\OpoFuente\TAI` (6.038 ficheros, 6,4 GB): el pack de Preparatic, descargas de Drive, escritorio, Anki.
- `F:\OpoFuente\GUARDIA-CIVIL` (394 ficheros, 185 MB): convocatoria, temario, exámenes, normativa.
- `F:\OpoFuente\zips` (25 ficheros, **14,98 GB**): los paquetes originales; **no se tocan**, se descomprimen a
  `TAI\internet\descargas`.
- `F:\OpoFuente\{APUNTES,BANCO,CATALOGO,EN-TEXTO-LEGIBLE,TEXTO-RECUPERADO*}`: lo que produjo este trabajo.
- `F:\OpoFuente\APUNTES-anteriores` (661 ficheros, 169 MB): copias de los apuntes antes de cada cambio.

---

## 3. Qué se ha hecho

### 3.1 Catalogar la bandeja entera

Inventario de las bandejas contra la biblioteca, emparejando por nombre, tamaño y huella sha256
(`_oficial/auditoria_de_la_bandeja.py`). Resultado: **5.679 de 5.938 ficheros de TAI dentro (95,6 %)**; los 381
que no llegaron por nombre resultaron ser mis propios informes, vistas derivadas de documentos que ya estaban,
bloqueos temporales de Office y mi OCR. **No queda nada por ingerir.**

Ojo con una trampa que me hizo publicar un número falso: la primera versión del auditor buscaba el nombre sólo
en `original_name` y daba **589 ficheros perdidos**; la aplicación guarda a veces ese campo saneado. Hay que
mirar los **tres** campos (`original_name`, `display_location`, `source_path_display`) y, para lo que quede,
comparar huellas.

### 3.2 El banco de preguntas

- **16.984 preguntas** importadas de mazos de Anki (decks y tarjetas), exámenes oficiales, cuestionarios,
  cosechas del material propio y preguntas con la respuesta marcada en el texto (X, asterisco, negrita).
- **9.342 con tema de TAI** y **241 de Guardia Civil** (241 de 241). Para poner tema a las preguntas hay cuatro
  caminos medidos (texto, vocabulario, nombre del fichero, conjunto) más un diccionario de términos aprendido con
  partición de entrenamiento/validación/prueba.
- **Dos errores de etiquetado a escala corregidos**: 119 preguntas del **Tribunal Constitucional** estaban en
  I.1 cuando el temario lo pone en **I.2**, y 216 de las Cortes, el Congreso, el Senado y el Defensor del Pueblo
  también. Efecto: I.1 pasó de 2.317 a 1.988 e I.2 de 296 a 821.
- **Lo que no se pudo**: 5.349 sin ningún mapeo. De esas, 2.997 son de documentos heterogéneos (documentos que
  juntan preguntas de muchos sitios), 1.341 de documentos identificados sin tema declarado, **959 de otras
  administraciones y otros cuerpos** (fuera del alcance por decisión del propietario) y 53 sin documento. Las
  vías léxicas están agotadas y medidas; lo que hace falta es la decisión **DEBT-014**.

### 3.3 El material de texto: el hallazgo más grande

**La aplicación extraía el texto y luego lo tiraba.** De 4.281 versiones, 2.199 guardaban menos del 90 % de su
texto extraído: **195.127.818 caracteres extraídos contra 71.685.330 guardados (36,7 %)**.

La causa: **un tramo de evidencia se guarda recortado a 1.200 caracteres** y, además, la extracción se corta a
2.000.000. El texto no había que volver a extraerlo: está en `datos\extracted\<representación>\texto.txt`. Se
cortó en bloques de 800 caracteres y partes de ≤380.000 (`_oficial/recuperar_el_texto_que_no_cabe.py`) y se
reingresó **por tramos** (documentos que perdían 300.000+, 50.000+, 20.000+ y 10.000+ caracteres):

| | |
| --- | --- |
| ficheros ingeridos | **1.365** |
| mapeos heredados | **5.546** |
| fallos | 0 |
| **texto guardado** | **256.633.482 de 263.592.370 → 97,4 %** |
| tramos citables | 381.874 → **700.277** |

### 3.4 Los apuntes por tema

- **37 apuntes de TAI** (33 temas + 4 bloques) en `F:\OpoFuente\APUNTES`, dentro de la aplicación como **101
  partes**; **25 apuntes de Guardia Civil**, uno por tema.
- **Sin repetidos**: se quitaron **1.088 fragmentos repetidos palabra por palabra** (12,8 %), reescribiendo el
  resumen y **traduciendo sus referencias** (`([35], [37])`) con una invariante que se comprueba antes de
  escribir. Los dos primeros intentos se negaron a escribir y por eso no rompieron nada.
- Los apuntes **citan** cada afirmación con el número de fragmento y la fuente debajo, para que se pueda
  comprobar.

### 3.5 Guardia Civil, «como en TAI»

- **25 de 25 temas** con material (288.087 fragmentos agregados), **241 preguntas con clave** (medidas contra la
  plantilla oficial del examen de 2026, modelos A y B), apuntes por tema y una sola versión vigente de cada uno.
- **El Código 599** (la recopilación del BOE con la normativa de la oposición) estaba dentro **con el 2 % de su
  texto**; partido **una norma por documento**: **48 normas, 5.408.807 caracteres**. Con eso, **epígrafes del
  temario sin material: 55 → 34**.
- Los 34 que quedan son subdivisiones internas de normas ya mapeadas en su bloque («TÍTULO IV…», «FAO.»): el
  límite es que **la aplicación mapea por documento, no por sección**.

### 3.6 Preparatic (cuerpo superior TIC)

**133 temas de Preparatic** catalogados, **85 con correspondencia con temas de TAI** (49 directas, 36
relacionadas) y **48 declarados fuera del temario de TAI a propósito** (economía, presupuestos, liderazgo,
ITIL/COBIT, inteligencia artificial…). **303 documentos mapeados.** Dos caminos se probaron y se descartaron
**con la medición delante**: por el contenido del documento (el vocabulario tira hacia los temas con más
material: derecho administrativo acababa en «protección de datos») y por el título a secas (decide 52 de 133 y
algunas mal).

### 3.7 Fuentes de internet y normativa

- BOE consolidado para el bloque I, y documentación técnica para los bloques II a IV (MDN, W3C, Pro Git, ENS,
  PostgreSQL), con su procedencia escrita en cada documento.
- Material de otras administraciones (INAP, comunidades, ayuntamientos) recogido y en el banco, **sin tema de
  TAI** porque el propietario dejó esos organismos fuera del alcance: 959 preguntas.

---

## 4. Defectos de la aplicación encontrados (esto es lo que más te puede servir)

Todos están **reproducidos con medida**. Van de más grave a menos, con el apaño que usé y lo que creo que sería
el arreglo.

### 4.1 El texto extraído se recorta a 1.200 caracteres y se pierde (GRAVE)

- **Síntoma**: documentos largos con sólo 100 tramos y 118.084 caracteres guardados de 2.000.000 extraídos.
- **Medida**: 2.199 de 4.281 versiones guardaban menos del 90 % de su texto; en total faltaba el 63 %.
- **Dónde mirar**: el guardado de tramos (lo que era `evidence_spans.text`) y el tope de 1.200 al leer un tramo.
- **Apaño**: cortar el texto en bloques de 800 caracteres **antes** de ingerirlo (nada se trunca porque ningún
  tramo pasa de 1.200) y repartirlo en partes de ≤380.000.
- **Arreglo posible**: que el extractor corte por sí solo en tramos de ≤1.000 caracteres (o que guarde el texto
  completo y recorte sólo al servir). Mientras no se arregle, **toda tubería que meta texto debe pre-cortarlo**.

### 4.2 El detector de formato lee 4.096 bytes y tira `.txt` legibles (GRAVE para `.txt`)

- **Síntoma**: un `.txt` con acentos se guarda como `unsupported_preserved` («conservado sin extraer») y no se
  lee nada.
- **Causa**: el detector lee los primeros 4.096 bytes; si el corte parte un carácter UTF-8 cuyos bytes no
  existen en cp1252 (`0x8D`, `0x8F`, `0x90`, `0x9D`), decide que es binario.
- **Víctimas medidas en esta sesión**: **ocho** ficheros (textos de mazo, partes de apunte, una fuente del BOE,
  tres volcados de Preparatic).
- **Apaño**: `_oficial/limpieza_texto.py` → `asegurar_corte_limpio()`: relleno ASCII si el fichero es corto, y si
  el corte parte un carácter, se meten los espacios justos **al principio de esa línea** para que el carácter
  empiece en el byte 4.096. Está en el módulo compartido y lo usan todas las tuberías nuevas.
- **Arreglo posible**: decodificar con reemplazo al detectar, o mirar más bytes, o aceptar UTF-8 aunque el
  último carácter esté incompleto.

### 4.3 Un `.md` se extrae sólo por sus encabezados

- **Síntoma**: un apunte de 80 KB quedaba en **447 caracteres** (0,7 %): el texto del tramo es el título.
- **Apaño**: escribir los apuntes como **texto plano** (sin `#` ni `**`) y agrupar las líneas en bloques de 800.
  Con eso el texto conservado pasó del 55 % al **98,2 %**.
- **Arreglo posible**: extraer el `.md` como texto y usar los encabezados sólo para la jerarquía de secciones.

### 4.4 La versión sustituida de un documento/pregunta y el mapeo polimórfico

Tres cosas distintas que se juntan y dan errores sutiles:

1. **El mapeo al programa es polimórfico**: una misma asignación se guarda contra `document_version`, contra su
   `representation` o contra su `artifact`, y **la mayoría del material está mapeado por dos de las tres vías**.
   Cualquier consulta que sume por fila de mapeo **cuenta el doble**: medí 177.288 fragmentos donde había
   129.099 (factores de ×1,00 a ×1,80 según el tema). Si escribes código que agrega, **cuenta cada versión una
   vez por nodo**.
2. **`mark-supersedes` sólo admite versiones del mismo documento** (409 si no). Por eso, cada vez que se
   rehacía un apunte y se volvía a ingerir, se creaba **otro documento con el mismo título** y quedaban dos
   generaciones aceptadas a la vez. Se arregla promocionando **con `document_id`** (`POST /documents`), que
   añade una versión al documento que ya existe.
3. **De `superseded` no se vuelve**: aceptar una versión sustituida contesta **409 «No se puede aceptar una
   versión «superseded»»**. Si por error se marca como sustituida una parte que hacía falta, hay que volver a
   ingerirla como contenido nuevo.

### 4.5 `POST /question-sets/{id}/parse` con `kind=answer_key` devuelve 500 en 11 de 24 conjuntos

- **Síntoma**: 500 determinista (no es la carga de la máquina: se reintentó con la máquina ociosa).
- **No es por posiciones repetidas**: los dos grupos las tienen (los que fallan, de 2 a 202; los que funcionan de
  1 a 268).
- **Efecto**: 113 entradas que son texto de norma (no preguntas) siguen sin poder anularse.
- **Reproducción guardada**: `F:\OpoFuente\CATALOGO\anuladas-por-no-ser-preguntas.json` y
  `_oficial\anular-aplicado2.txt`.

### 4.6 Los nombres de campo de las barajas modernas de Anki se pierden

- `notetypes.config` es **protobuf**, no JSON; los nombres están en la tabla `fields`. Resultado: 4 documentos y
  1.851 fragmentos con «campo 1: …» en vez del nombre del campo.

### 4.7 No hay forma de retirar ni archivar un documento

- Para las generaciones viejas de apuntes y para el Código 599 truncado **no existe ruta**: se quedan en la
  biblioteca y en la búsqueda. Un «archivar documento» (o que `mark-supersedes` admita documentos distintos con
  el mismo título) resolvería varias cosas de golpe.

### 4.8 Otras trampas que encontré y que conviene saber

- **La ingesta va de una en una**: un trabajo de clasificación largo bloqueó la cola de ingesta **~6 horas** (se
  canceló con `POST /jobs/{id}/cancel`).
- **Dos escritores a la vez** → 500 `database is locked`.
- **`accept` devuelve 409 si la versión ya está aceptada** (la promoción acepta sola). Contarlo como fallo dio 56
  falsos negativos.
- **El título se sanea**: `31/1995` se guarda como `31-1995`. Buscar citas por su forma con barra falla.
- **La búsqueda es `POST /search` con `{"query": …}`**, no `GET`.
- **Importar por CSV: una fila por petición.** Mandando 344 filas se aplicaron 110 temas (desalineación);
  mandando una fila por petición, siempre. Y la pregunta se localiza por **huella**, no por enunciado literal
  (`trim(stem) = ?` encontraba un tercio).

---

## 5. Lo que queda por hacer, por orden de valor

1. **Arreglar el recorte de tramos y el detector de 4.096 bytes** (§4.1 y §4.2): son los dos defectos que más
   material han costado, y los dos se pueden arreglar en el extractor.
2. **Rendimiento de la búsqueda**: con 700.277 tramos, consultas comunes tardan **1,5-5,7 s** (antes ~1 s).
   O afinar el índice léxico (FTS5) o decidir **DEBT-014**.
3. **Temas con el banco flojo**: IV.3 (70 preguntas), IV.4 (74), III.2 (79), II.2 (83), II.3 (91), II.1 (93).
   Hay material suficiente; lo que falta son preguntas de esos temas.
4. **Las 5.349 preguntas sin mapeo** (§3.2): las 959 de otras administraciones están fuera de alcance; las
   otras **4.390** necesitan la decisión DEBT-014.
5. **Los 34 epígrafes de Guardia Civil sin material** (§3.5): hace falta mapeo **por sección**, hoy no existe.
6. **La cola del texto perdido**: el 2,6 % que queda (337 documentos que pierden entre 5.000 y 20.000
   caracteres). Mismo procedimiento con el umbral en 5.000.
7. **`crudo-docx.jsonl`**: 2.164 preguntas con opciones y **0 con clave**; están fuera del banco a propósito.
8. **Las plantillas de los exámenes de Guardia Civil 2021-2025**: los exámenes son legibles pero las plantillas
   oficiales son escaneos; el OCR deja 12 a 80 números sin leer. Se quedan como material.
9. **DEBT-023** (el reverso de una tarjeta de Anki no tiene dónde vivir) y **DEBT-020** (la plantilla de Celador
   escaneada) siguen abiertas.

---

## 6. Las herramientas que dejo

Están en `F:\EspacioCodigo\proptech-access-control\docs\opofuente\_oficial\` (**405 scripts**; casi todos son
trabajo de una vez, pero éstos importan). El intérprete que usan es
`F:\EspacioCodigo\opofuente\.venv\Scripts\python.exe`.

| para qué | script |
| --- | --- |
| preguntar a la base sin pelearse con PowerShell | `consulta.py "select …"`, `--tablas`, `--columnas TABLA` |
| copia coherente de la base para medir sin bloquear la aplicación | `bd_snapshot.py` |
| **lo que la aplicación guarda de verdad**: mapa de temas con fragmentos, documentos y preguntas | `mapa_de_material_por_tema.py` (TAI) y `mapa_de_material_de_gc.py` (GC, agrega los epígrafes) |
| inventario de la bandeja contra la biblioteca | `auditoria_de_la_bandeja.py` |
| texto que la aplicación no puede leer | `recuperar_el_texto_que_no_cabe.py` |
| apuntes: sin repetidos, al día, mapeados | `medir_lo_que_se_repite_en_los_apuntes.py`, `quitar_lo_repetido_de_los_apuntes.py`, `apuntes_al_dia_en_la_app.py`, `dejar_los_apuntes_mapeados.py` |
| una sola versión vigente por documento | `dejar_una_sola_version_vigente.py` |
| meter una carpeta en la aplicación (inventario + copia) | `ingerir_texto_legible.py --carpeta RUTA` |
| promocionar y aceptar todo lo que tiene texto | `rellenar_biblioteca.py` |
| partir un corpus por normas (el Código 599) | `partir_el_codigo_599.py` |
| reglas de tema y su medición | `reglas_estrechas.py`, `temas_estrechos_de_uno_en_uno.py`, `terminos_por_tema_medidos.py`, `tema_por_el_conjunto.py` |
| limpieza de texto y **la guarda del corte de 4.096 bytes** | `limpieza_texto.py` |

**Informes** (con todas las mediciones y sus comandos): `docs/reviews/` del repositorio de la aplicación —
**29 documentos**. Los más útiles para empezar: `ESTADO-DEL-MATERIAL-2026-09.md` (resumen y por dónde sigue),
`TEXTO-EXTRAIDO-QUE-NO-SE-PODIA-LEER-2026-09.md` (§4.1), `GUARDIA-CIVIL-UNA-GENERACION-Y-EL-CODIGO-599-2026-09.md`,
`BANDEJA-COMPLETA-Y-PREPARATIC-2026-09.md`, `APUNTES-SIN-REPETIDOS-2026-09.md`,
`TEMAS-DE-LAS-PREGUNTAS-CORREGIDOS-2026-09.md`, `MAZOS-DE-ANKI-2026-09.md`.

---

## 7. Avisos que te ahorrarán tiempo (y disgustos)

1. **No muevas ni borres nada de las bandejas originales.** El material del propietario se lee, nunca se toca.
2. **`F:\OpoFuente\zips` son 14,98 GB**: se descomprimen a `TAI\internet\descargas`; no los ingieras directamente.
3. **El temario de Guardia Civil es de uso privado** (DEBT-003): el repositorio no se publica mientras esté
   dentro.
4. **Antes de dar algo por bueno, mide**: el proyecto entero está escrito así, y varias de las correcciones de
   este documento salieron de medir y encontrar que lo que yo mismo había publicado estaba mal.
5. **Cuidado con las tuberías que suman mapeos** (§4.4.1): es el error más fácil de repetir.
6. **Toda tubería que meta `.txt`** debe pasar por `limpieza_texto.escribir_texto_ingestable()` y **cortar en
   bloques de 800** (§4.1 y §4.2). Si no, el material entra ilegible o a medias, y no se nota hasta que se
   estudia con ello.
7. **Los datos de las pruebas E2E van a `.e2e-data`**, no a los datos de verdad (DEBT-026), y la suite no debe
   correr contra un servidor ajeno (DEBT-021).

---

## 8. Lo que sigue siendo decisión del propietario

- **DEBT-014** (embeddings o modelo local): sin decidir. Es lo que desbloquearía las 4.390 preguntas sin tema y
  lo que probablemente arreglaría el rendimiento de la búsqueda. Hay dos informes con medidas esperándolo:
  `INFORME-BASES-VECTORIALES-LOCALES-2026-09.md`, `INFORME-LLM-LOCAL-CPU-ESPANOL.md`,
  `modelos-embeddings-es-cpu.md` y `PROPUESTA-BUSQUEDA-2026-09.md`.
- **DEBT-018** (la puerta humana de revisión sobre material real): la mitad de la máquina está medida; falta el
  tiempo de revisión del propietario.
- **DEBT-016** (dificultad observada y umbrales de dominio): provisionales.
- **DEBT-028** (la aplicación no sabe si un proceso selectivo está abierto o cerrado).

---

## 9. Cómo volver a medir lo que dice este documento

El intérprete de las herramientas es `F:\EspacioCodigo\opofuente\.venv\Scripts\python.exe` y los scripts están en
`F:\EspacioCodigo\proptech-access-control\docs\opofuente\_oficial\`. Desde esa carpeta:

```powershell
$py = "F:\EspacioCodigo\opofuente\.venv\Scripts\python.exe"

# el estado de la base en una línea
& $py consulta.py "select (select count(*) from question_versions) as preguntas, (select count(*) from logical_documents) as documentos, (select count(*) from evidence_spans) as tramos, (select count(*) from curriculum_mappings) as mapeos"

# el mapa de temas de TAI (fragmentos, documentos, preguntas y claves por tema)
& $py mapa_de_material_por_tema.py

# el de Guardia Civil (agrega los epígrafes de cada tema y dice qué epígrafes están vacíos)
& $py mapa_de_material_de_gc.py

# cuánto texto extraído se queda sin guardar (el defecto §4.1)
& $py medir_el_texto_que_no_se_guarda.py --peores 10

# lo que se repite dentro de los apuntes
& $py medir_lo_que_se_repite_en_los_apuntes.py

# la bandeja contra la biblioteca
& $py auditoria_de_la_bandeja.py
```

Para comprobar que la aplicación responde y que la búsqueda va (ojo: el prefijo `/api/v1` y es **POST**):

```powershell
$cuerpo = @{ query = "cortafuegos perimetral"; limit = 3 } | ConvertTo-Json
$bytes = [System.Text.Encoding]::UTF8.GetBytes($cuerpo)   # sin esto, los acentos dan 400 por el cliente, no por la aplicación
Invoke-RestMethod -Uri "http://127.0.0.1:8765/api/v1/search" -Method Post -ContentType "application/json; charset=utf-8" -Body $bytes
```

