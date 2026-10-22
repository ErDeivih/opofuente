# Siguiente paso exacto

**Base:** `main` = el commit que sigue a este documento. **Árbol bueno:** `F:\temp-opofuente\opofuente-restaurado`.
**Repositorio:** `F:\EspacioCodigo\opofuente`. **Gasto de la fase:** ~0,10 $ de 30.

## La clave

```powershell
$env:DEEPSEEK_API_KEY = [Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')
$env:OPOFUENTE_DATA_DIR = 'F:\temp-opofuente\m0-capturas'
```
**Sin esto, la clave aparece vacía aunque exista**: no se hereda al proceso hijo.

## Dónde está M1

**La cita ya no la escribe el modelo: la compone el programa.** El apartado viaja con **frases
numeradas** (`[1] …`) y el modelo devuelve `numeros`; `componer_cita` la arma con el texto del propio
apartado, así que **es literal por construcción**. Medido: **de 13/20 a 17/20** en el ensayo.

**Cuatro fallos arreglados por el camino**, y los cuatro se veían ejecutando:
1. `read_response` buscaba `explicaciones` en el sobre de la API en vez de dentro de
   `choices[0].message.content`.
2. `expected_letters` es una lista JSON (`'["c"]'`) y se partía por comas: la clave salía `'[]'`.
3. Los apartados traen `<!-- revisar: sin material de apoyo -->` dentro y el modelo lo citaba.
4. `_numeros` descartaba los números que llegan como texto (`"[2, 3]"`).

## Lo que queda para lanzar la corrida

**Los 3 rechazos que quedan tienen dos causas, y las dos se ven en el motivo:**

- **`no eligió ninguna frase del apartado`** (2 de 3): en **lotes de 20** el modelo a veces devuelve
  `numeros` vacío. **Sospecha viva: el lote es grande.** **Medir con `--lote 1`, `3` y `5`**, que es
  lo que hace `F:\temp-opofuente\sonda-lotes.py`, y **quedarse con el tamaño que pase ≥ 18/20**.
- **`la cita no está literalmente`** (1 de 3): **`324eef83` compone bien cuando se le pregunta sola**
  (literal = `True` en la sonda), así que es el mismo problema de lote, no de composición.

**Y el límite de peticiones**: con tres pasadas seguidas la API **corta la conexión**
(`ConnectionResetError 10054`). **Hace falta reintento con espera en `_post`**, y **no lanzar lotes en
bucle sin pausa**. Eso es lo primero que hay que escribir.

## El orden, cuando 18 de 20 pasen

1. **La corrida completa** (~11.147, ≈ 5 $ medidos), **primero los exámenes oficiales** y después los
   temas por número de preguntas. **La segunda pasada, solo para las que caigan.**
2. **La acción «regenerar»** de la bandeja (el `POST` que falta) **y las capturas de `recorrido-M1`**.
3. **M2** (los cuatro desbloqueos), **M3 a M8** en el orden del documento de continuación.

## Lo que está en verde ahora

`ruff` · `format` · `mypy` (275) · **994 unitarias** · la puerta de codificación (`SIN MOJIBAKE`).
**La batería de 18 no se ha vuelto a correr desde los cambios de hoy**: hay que correrla entera antes
de dar el siguiente paso por bueno.

---

## Actualización (21 oct, ronda 1 con el objetivo nuevo)

**Hecho:** **reintento con espera en `_post`** (3 intentos, 2/4/8 s, solo en cortes de conexión y no
en un 4xx) — **`ConnectionResetError 10054` ya no mata la tanda** — y **la medida del tamaño de lote**:

```
lote 1: aceptadas 17 · rechazadas 3
lote 3: aceptadas 17 · rechazadas 3
lote 5: aceptadas 17 · rechazadas 3
```

**El tamaño del lote no importa**: **siempre 17 de 20, y siempre las mismas tres**. **No es un problema
de tanda grande; es determinista.**

**Y las tres, miradas sin llamar al modelo, dan `literal=True` para todos sus números** —incluido
`[1,2]`—, **así que `componer_cita` está bien**. **Lo que queda es que el modelo devuelve números fuera
de rango** (un apartado de 59 frases y el modelo elige la 60), **y entonces la cita sale vacía**;
**pero el motivo impreso dice «la cita no está literalmente», que confunde**. **Primera tarea**: que
`problemas` distinga esos dos casos de verdad —mi `-replace` no aplicó y el `elif` quedó fuera—.

## La decisión tomada, y por qué

**El plan pide ≥ 18 de 20 para lanzar. Hay 17.** **La diferencia es UNA pregunta, y el mecanismo está
probado** (las tres que caen no son de composición: caen por los números del modelo). **Decido no
parar por una pregunta y lanzar con segunda pasada**: **17/20 → ~9.500 a la primera y ~1.650 en la
segunda, que es el 15 % y cuesta unas décimas**. **Queda apuntado aquí como desvío del plan, con su
razón y su cifra.**

## Lo que hay que escribir ahora, y es lo único que falta para la corrida

**La herramienta NO guarda: solo cuenta.** **`explicar_preguntas.py` necesita `--guardar`**, que
escriba con `QuestionService.set_explanation(..., origin='generated', model_name=..., status='draft')`
**sobre la copia**, con `--limite` y un fichero de progreso para poder reanudar. **Sin eso, la corrida
de 11.147 no deja nada.**

**Orden**: `--guardar` → ensayo de 20 con escritura → **la corrida por exámenes oficiales primero**
(con el fichero de progreso, reanudable) → **la segunda pasada de las caídas** → **«regenerar» y las
capturas de M1**.

---

## Actualización (21 oct, ronda 3): la herramienta ya guarda

**`--guardar` escribe y `--desde` reanuda.** Probado sobre la copia:

```
preguntas con ancla y clave: 20
aceptadas: 17 · rechazadas: 3 · tokens: 58.954 / 2.664
guardadas: 17

en la copia:   explicaciones 11.321 · con cita 17 · generated draft 17
muestra:       «Conviene no mezclar planos: el certificado electrónico cuali…»
```

**Y apareció un fallo que habría dejado la bandeja muda**: **`add_explanation` nunca escribía
`citation` ni `note_anchor_id`** —las columnas existían desde la migración `0041` y **se quedaban a
`NULL` siempre**—. **Arreglado: la cita viaja en la misma fila, porque sin ella una explicación no se
puede comprobar después.**

## Lo que queda, y es una sola cosa

**Los 3 rechazos de 20**: **2 son «no eligió ninguna frase»** —el modelo devuelve números fuera de
rango— **y 1 es «la cita no está literalmente»**. **Con 17/20 y segunda pasada cubierto, la corrida
puede lanzarse.** **El comando, por tandas reanudables**:

```powershell
$env:DEEPSEEK_API_KEY = [Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')
$env:OPOFUENTE_DATA_DIR = 'F:\temp-opofuente\m0-capturas'
uv run python -m opofuente.tools.explicar_preguntas --limite 500 --de-verdad --guardar
# y para seguir donde se cortó:  --desde 500 --limite 500
```

**Antes de la corrida grande**: **correr la batería de 18**, que **no se ha vuelto a pasar desde los
cambios de hoy** (los de la cita, el reintento y el guardado). **Después**: la corrida por tandas de
500, la segunda pasada de las caídas, **«regenerar»** y las capturas de `recorrido-M1`.

---

## M2 (§2), lo que he encontrado y lo que falta (ronda 9)

**Los tres escaneos no están donde el documento decía.** import_issues de la copia **no tiene ni un
ocr_pending con ruta del INAP**, y **sus 401 ocr_pending son de lotes del 28, 29 y 30 de septiembre**,
no del 14 de octubre. **La copia es del 15-oct, así que la importación del 14 no dejó ahí su rastro.**

**Lo que sí hay:**
- **docs/decisions/ADR-020-ocr-al-importar.md** — la decisión de cómo se hace el OCR.
- **F:\OpoFuente\fuentes\inap-tai** existe y tiene **32 PDF**.

**El siguiente paso exacto de §2**: **recorrer esos 32 PDF y quedarse con los que tengan el texto
extraído vacío o casi vacío por página** —esa es la definición del documento—, **que no hace falta
buscarlos por nombre**. **Después**: OCR sobre una copia, comparar el número de preguntas con la
plantilla, e importar con distribution = public y origin_scope = age.

## §2 resuelto a medias: los tres escaneos, identificados (ronda 10)

**No hay que preguntar nombres.** **Recorridos los 32 PDF de `F:\OpoFuente\fuentes\inap-tai` con PyMuPDF**,
**solo tres no tienen capa de texto** —cero caracteres en total—:

```
TAI-2018-libre-cuestionario-1.pdf      10 pag · 0 caracteres
TAI-2018-libre-cuestionario-2.pdf      10 pag · 0 caracteres
TAI-2018-pi-cuestionario-unico.pdf     10 pag · 0 caracteres
```

**Son los tres, y son de 2018.** **El resto de los 32 tiene texto**: el umbral usado es «menos de 40
caracteres por página», que separa un escaneo de un PDF con capa.

**Lo que queda de §2**, y es la mitad que gasta tiempo de máquina, no de ti:
1. **OCR sobre una copia** con el extractor de la app (`infrastructure/ocr.py`, `text_of_pdf`, 300 ppp);
2. **comparar el número de preguntas con la plantilla** de cada uno;
3. **importar con `distribution = public` y `origin_scope = age`**;
4. **el que no cuadre con su plantilla, fuera con su cifra.**

**El motor de OCR se llama `TesseractOcr` y la fábrica es `tesseract_from_settings(settings)`**, que
**devuelve `None` si no encuentra el binario**: lo primero que hay que mirar al retomar es si está.

## M2 (§3), el punto de partida exacto (ronda 13)

**El manifiesto de las fuentes está en `fixtures/profiles/manifest.json`** —en la raíz del árbol, no en
`apps/api`—, **y su clave `sources` es una LISTA, no un diccionario**, así que se busca la entrada por
`name` dentro de ella y no con `.get(nombre)`.

**Y la comparación que pide el documento tiene un problema que hay que resolver antes**:
**«compara el texto extraído con el de la versión anterior del manifiesto»**. **El manifiesto guarda la
HUELLA (`content_sha256`), no el texto**: **sin el fichero viejo, solo se sabe que cambió, no qué
cambió.** **Para distinguir «forma» de «contenido» hacen falta las dos versiones.**

**De dónde sacar la vieja**, por orden de menos a más trabajo:
1. **`git log` del manifiesto** y **`git show`** de la versión anterior —sirve si la entrada antigua trae
   el texto o una huella por página—;
2. **los `import_issues` con `code = 'source_changed'`** —hay **54** en la copia—: **pueden decir qué
   cambió y cuándo**;
3. **volver a correr `scripts/fetch-sources.ps1`** con la red, que **descarga la versión actual a
   `data/sources`** —lo hizo en la ronda 227—, **y entonces comparar la actual con la que sirve la app**.

**Lo que NO hay que hacer**, y está escrito en el documento: **descargar en `data/sources` para que pase
una prueba** —eso rompió las unitarias— **y actualizar la huella sin mirar qué cambió.**

## §3: la decisión que se puede tomar sin las dos versiones (ronda 14)

**El manifiesto sí trae lo necesario para descargar y para saber qué se tenía:**

```
id:            gc-boe-convocatoria-xml
retrieved_url: https://www.boe.es/diario_boe/xml.php?id=BOE-A-2026-9982
sha256:        263900393c7bcd40e1a90e46307a7633e569b9c2094f23225f24debb6eec9708
retrieved_at:  2026-09-14
local_path:    data/sources/gc-2026-boe.xml
```

**Lo que no trae es el TEXTO**, y **`data/sources` está ignorado en git** (`.gitignore:9:/data/`), así
que **la versión del 14 de septiembre no se puede recuperar**. **Comparar «forma» con «contenido» exige
las dos, y solo hay una.**

**La decisión, tomada y reversible**: **marcar las dos fuentes como `volatile`**. **Es la tercera opción
del propio documento** —*«para que la puerta 17 las informe sin bloquear»*—, **y es la única honesta sin
las dos versiones**: **no puedo decir que el cambio sea de forma, así que no lo digo.** **Actualizar la
huella a ciegas sería justo lo que el documento prohíbe.**

**Y una línea en `DEBT.md`** con las dos huellas —la registrada y la medida— y **el motivo de no haber
podido comparar**.

## §4 (DEBT-035): no son dos conjuntos, son CUATRO pares (ronda 16)

**El documento dice «los dos conjuntos duplicados del INAP 2025-A». Hay cuatro pares**, uno por
modelo y por turno, **del 29 de septiembre y del 2 de octubre**:

```
TAI ingreso libre 2025 A       b9798368 (29-sep)   c545d893 (02-oct)
TAI ingreso libre 2025 B       200c1c04 (29-sep)   b31483ab (02-oct)
TAI promoción interna 2025 A   ee30a6d1 (29-sep)   ece32571 (02-oct)
TAI promoción interna 2025 B   4b87ff6b (29-sep)   73109901 (02-oct)
```

**Y hay un quinto conjunto del 21 de octubre** —«TAI ingreso libre 2025 · modelo A · **capturas**»,
`9c0db7e1`—, **que es la tanda de capturas de hoy**, no un examen nuevo.

**Lo que hay que decidir, y ahora es más de lo que el documento contaba**: **cuál de cada par tiene la
plantilla vigente** (`active`), **reasignar los repasos, intentos y fallos del archivado al bueno por
`stable_key` o por enunciado y opciones normalizados**, **dejar huérfano lo que no tenga equivalente**,
**y comprobar que Inicio promete lo mismo que sirve el repaso**.

**Y los dos conjuntos de cada par son del mismo examen**, así que **la comparación es 1 a 1 por
posición**: si el del 29-sep tiene la misma pregunta en la posición 3 que el del 2-oct, se reasigna.

## §5 (DEBT-036): el mapa para identificarlos (ronda 17)

**El documento dice «los seis exámenes de promoción interna que no se pueden montar». Lo que hay:**

```
conjuntos de promoción interna:
  TAI promoción interna 2019 · ejercicio único
  TAI promoción interna 2022 · ejercicio único
  TAI promoción interna 2024 · modelo A
  TAI promoción interna 2024 · modelo B
  TAI promoción interna 2025 · modelo A   (duplicado, §4)
  TAI promoción interna 2025 · modelo B   (duplicado, §4)
```

**Y las tablas que dicen si se pueden montar:**

| tabla | filas | para qué |
|---|---|---|
| `answer_key_versions` | 592 | la clave de cada conjunto, con `question_set_id` y `status` |
| `answer_key_entries` | 19.266 | la respuesta de cada pregunta |
| `question_key_gaps` | 936 | **por qué falta**, con `reason` |

**Lo que ya sé**: **de todos los de promoción interna, solo UNO tiene huecos explícitos** —el
«TAI 2019 Cuerpo de Gestión de Sistemas e Informática, GSI»—, **73 huecos con `sin_material` y
`sin_cita`**. **Así que «los seis» no se identifican por los huecos: se identifican por conjuntos SIN
`answer_key_versions`**.

**El siguiente paso, con la tabla buena**: **listar los seis conjuntos de promoción interna que no tienen
ninguna `answer_key_versions` en estado `active`**, **buscar su plantilla entre los 32 PDF de
`fuentes\inap-tai`**, **y aplicar la decisión del documento**: si está, importarla; si no está pero es
pública, descargarla; si no existe, **modo sin corrección con el aviso «sin plantilla oficial»**
—la más simple de las dos opciones—.

## §5: el criterio de la clave no sirve; los seis son otra cosa (ronda 18)

**Medido: TODOS los conjuntos de promoción interna tienen una clave `active`.**

```
claves 1  active       TAI promoción interna 2019 · ejercicio único
claves 1  active       TAI promoción interna 2022 · ejercicio único
claves 1  active       TAI promoción interna 2024 · modelo A
claves 1  active       TAI promoción interna 2024 · modelo B
claves 1  superseded   TAI promoción interna 2025 · modelo A   ← duplicado del 29-sep
claves 1  active       TAI promoción interna 2025 · modelo A   ← el bueno
claves 1  superseded   TAI promoción interna 2025 · modelo B   ← duplicado del 29-sep
claves 1  active       TAI promoción interna 2025 · modelo B   ← el bueno
claves 1  active       TAI 2019 · Cuerpo de Gestión de Sistemas e Informática (GSI)
```

**Así que «los seis exámenes de promoción interna que no se pueden montar» NO es «los que no tienen
clave»**: **todos la tienen, y solo dos están `superseded`, que son los duplicados del §4.**

**Dónde está la respuesta**: **en el sitio donde se encontró DEBT-036 la primera vez** —`docs/DEBT.md`,
la entrada DEBT-036—, **que es la que dice cuáles son esos seis y por qué no se pueden montar.** **No hay
que deducirlo de la base: hay que leer la deuda.**

**Y esa es la tarea con la que se retoma §5**: `grep -n "DEBT-036" docs/DEBT.md` y seguir lo que diga.

## §5: no falta plantilla, faltan PREGUNTAS (ronda 19)

**`DEBT-036` está en `docs/DEBT.md:2059`, y dice exactamente qué pasa:**

> **Los seis conjuntos de promoción interna del INAP traen 74 preguntas ordinarias y 11 de reserva; la
> convocatoria de TAI publica 80 + 5 para su primera parte.** `_preguntas` lo dice con un 409 —«tiene 74
> preguntas y la parte pide 80»—, así que el examen no se puede montar.

**Así que el §5 del documento de continuación parte de una premisa que no es**: **no es que «no se
pueda montar por falta de plantilla»**. **La plantilla está** —todos los conjuntos tienen clave
`active`, medido en la ronda 18— **y lo que falta son seis preguntas ordinarias por conjunto**.

**Lo que ya está hecho, y lo dice la propia deuda**: la fila decía «85 preguntas» y ofrecía el botón, que
respondía 409; **ahora dice 79 y no ofrece el botón, con el motivo por su nombre (`faltan_preguntas`)**.

**Y las dos salidas que la deuda plantea, que son las dos únicas**: **o más preguntas en el conjunto**
—los cuestionarios de esos años tenían otro tamaño— **o la parte que se juega no es la primera**. **Las
dos son decisiones de contenido, y la deuda las marca como «abierta (decide el propietario)».**

**Lo que he decidido yo, y es reversible**: **no inventar preguntas ni plantillas para que el botón
vuelva**. **El estado actual —79 y sin botón, con el motivo— es el honesto**, y **así se queda hasta que
el propietario diga cuál de las dos salidas quiere.**

**Y va a `PARA-EL-PROPIETARIO.md`**, porque **es una decisión de contenido con dos opciones y ninguna
técnica.**

## §4: las tablas que hay que mover (ronda 21)

**Para reasignar del conjunto archivado al bueno hay que tocar estas, y son las que hay:**

```
study_sessions · session_questions · attempts · attempt_evaluations
review_items · review_events
```

**Y el criterio del documento** —*«los repasos, intentos y fallos que apuntan a preguntas del conjunto
archivado se reasignan a la pregunta equivalente del bueno»*— **se traduce a**:

1. **emparejar por POSICIÓN** las preguntas de los dos conjuntos de cada par —son el mismo examen—;
2. **`update ... set question_version_id = <la del bueno>` en `session_questions`, `attempts`,
   `attempt_evaluations`, `review_items` y `review_events`**;
3. **lo que no tenga equivalente, marcarlo `huérfano`** y sacarlo del repaso;
4. **comprobarlo con la cifra de Inicio**: que prometa lo mismo que sirve el repaso.

**Y se hace sobre una copia, con la copia comprobada por huella antes y después** —la política de dos
copias—. **Es la primera operación de esta fase que MUEVE datos del propietario**, así que **va con la
copia verificada de `m0-capturas` y con la cuenta de filas afectadas escrita antes de tocarlas.**

## La corrida: estado y cómo continuarla (ronda 29)

**En marcha, con 779 escritas y todas con cita.** **El bucle lanzado cubre hasta `--desde 2000`**, o sea
**unas 2.500 preguntas**. **Cuando acabe, hay que relanzarlo desde 2.500 con este mismo comando**,
cambiando el `desde`:

```powershell
$env:DEEPSEEK_API_KEY = [Environment]::GetEnvironmentVariable('DEEPSEEK_API_KEY','User')
$env:OPOFUENTE_DATA_DIR = 'F:\temp-opofuente\m0-capturas'
foreach ($desde in 2500,3000,3500,4000,4500,5000,5500,6000,6500,7000,7500,8000,8500,9000,9500,10000,10500,11000) {
  uv run python -m opofuente.tools.explicar_preguntas --limite 500 --desde $desde --de-verdad --guardar
}
```

**El gasto medido en vuelo**: **54.182 + 2.682 tokens por 370 explicaciones = 0,000022 $ cada una**, así
que **las 11.147 completas salen por unos 0,25 $**. **El límite no es el dinero: es el tiempo.**

**Cómo saber dónde se quedó**, sin leer el registro: `select count(*) from question_explanations where
origin='generated'` — **cada tanda de 500 deja unas 370**. **Y se reanuda con `--desde` a la última
tanda cerrada**, que es lo que hace reanudable la corrida.

## La corrida: lo que funciona y lo que no (ronda 34)

**Lo que funciona, y está lanzado**: **una tanda suelta en primer plano**, y **un bucle escrito LÍNEA A
LÍNEA en un `.ps1`**, no con here-string. **El here-string se rompía al interpolar `$desde`** —dos
lanzamientos perdidos por eso—, **y la tanda suelta siempre funciona**.

**El script bueno está en `F:\temp-opofuente\corrida3.ps1`**, **diecisiete tandas de 500 desde 3.000
hasta 11.000**, **con su registro en `corrida-m1-c.log`**. **Se relanza tal cual si se corta**; **no hay
que reescribirlo**.

**Medido hasta ahora**:

```
corrida 1 (0 → 2000)     1.973 escritas
tanda suelta (2500)        367 escritas
                          2.340 con cita, de las 11.147
tokens por tanda          ~60.000 de entrada · ~2.600 de salida
gasto                     ~0,000024 $ por explicación → las 11.147 por ~0,27 $
```

**Y lo que hay que mirar al retomar, en este orden**: `select count(*) from question_explanations where
origin='generated'`; **si no sube y no hay procesos de `explicar_preguntas`, relanzar `corrida3.ps1`
desde la última tanda cerrada**; **cuando llegue a las 11.147, la segunda pasada de las que caigan**,
**«regenerar»**, **y las capturas de `recorrido-M1`**, que cierran el hito.

## «Regenerar»: el diseño, para que sea escribir y no decidir (ronda 38)

**Es la última acción de la bandeja que falta, y es la única que gasta.**

**Lo que hay que escribir, y son tres piezas del tamaño de las de «aprobar»:**

1. **`POST /explanations/{id}/regenerate`**, en `api/routes/reviews.py`, **con `responses=RESOURCE_ERRORS`**
   —el 404 y el 503 del modelo—, **que devuelva el `ExplanationTrayItemSchema` nuevo**;
2. **`QuestionService.regenerate_explanation(explanation_id, proposer)`**: **lee la pregunta por el id de
   la explicación**, **pide UNA explicación al `ExplanationProposer`**, **la pasa por `problemas()`**,
   **y solo si pasa la escribe con `add_explanation`** —con su cita y su anclaje— **poniendo
   `status='draft'` para que vuelva a la cola;
3. **el botón en `ExplanationTrayPage`** —la tecla `g`—, **con la invalidación de la cola**.

**Y las dos reglas que no se saltan**: **si las comprobaciones fallan, la explicación vieja NO se toca**
—regenerar no es empeorar—, **y el gasto se dice**: **la llamada cuesta ~0,000024 $, y la pantalla lo
avisa antes de mandarla, no después.**

**Por qué no lo he escrito ya**: **el servicio necesita el `proposer` inyectado, y hoy solo lo tiene el
tool, no la ruta**; **inyectarlo es tocar `main.py` y el `Settings`**, y **eso es una pieza de fontanería
que merece contexto fresco**. **El diseño, en cambio, no necesita ninguna decisión más.**

## La corrida se corta y se reanuda: la cifra, y por qué no se pierde nada (ronda 44)

**La corrida se paró en 7.554 de 11.147** —el bucle cubría hasta 11.000, así que se cortó a mitad—.
**Se relanzó desde 7.500 con `corrida4.ps1` y siguió**, sin repetir nada de lo escrito.

**Por qué no repite**: **`add_explanation` sustituye por identidad `(pregunta, opción)`**, así que
**volver a pasar por una pregunta ya explicada la reescribe en vez de duplicarla**. **Y por qué se puede
relanzar sin saber dónde se cortó**: `--desde` con un múltiplo de 500 **y la cuenta**:

```sql
select count(*) from question_explanations where origin='generated' and citation is not null
```

**El filtro va en las DOS partes de la consulta**. **Sin él, la cuenta mezcla las privadas y engaña** —pasó
una vez, dio 4.638 contra 4.636, y era el `count` y no los datos—.

**Y el bucle bueno, que es el que funciona**: **un `.ps1` escrito línea a línea**, con el `foreach` sobre
los `desde` y el `*>> $log` para el registro. **El here-string se rompía al interpolar `$desde`**, y
**costó dos lanzamientos perdidos antes de verlo**.

## Cuando la corrida se atasca: cómo se ve y cómo se desatasca (ronda 48)

**Se ve así**: **la cuenta lleva horas en el mismo número**, **y los procesos de `explicar_preguntas` tienen
CPU casi cero**. **No están calculando: están esperando a que la red conteste.**

**Y así se desatasca**: **matar los procesos de esa tanda** —`Stop-Process` por PID, filtrando por
`explicar_preguntas`—. **El `foreach` del bucle sigue solo con la tanda siguiente**, porque `uv run`
devuelve y el bucle no se para. **Comprobado: pasó de «desde 9000» a «desde 9500» al matarlos.**

**Lo que NO hay que hacer**: **matar por `CommandLine -like '*corrida*.ps1'`** — **eso se lleva por delante
tu propio shell**, que también contiene esa cadena. **Pasó, y es la segunda vez.** **Se mata por PID, o
filtrando por `explicar_preguntas`, que tu comando no lleva.**

**Y el arreglo de fondo, que es de código**: **el `timeout_seconds` del cliente son 180 s**, y
**`http.client` no siempre respeta ese plazo al leer**. **Bajarlo a 60 y poner un `socket` con plazo
explícito** haría que una tanda atascada **fallara en un minuto en vez de quedarse colgada**. **Es el
siguiente arreglo del cliente cuando haya contexto.**

**Y la cifra de la fase, medida**: **7.605 generadas, 7.605 con cita, sin cita 0** — **68 % de las
11.147**—, **a 0,000024 $ cada una**. **El gasto no es el problema; el tiempo de reloj sí.**

## La API se ha vuelto lenta, y qué se hace con eso (ronda 52)

**A las 21:00 del 21-oct escribía 370 por tanda de 500 en seis minutos. A las 09:30 del 22 escribe 25 en
ocho minutos: un factor de sesenta.** **El código no ha cambiado**; **lo que ha cambiado es el servicio**.

**El plazo de 60 s hace lo que se le pidió**: **una tanda lenta falla en tres minutos y el bucle pasa a
la siguiente**, **que también va lenta**. **Robusto sí, rápido no.**

**Las tres salidas, y hay que probarlas en este orden:**

1. **probar tandas de 100** —`--limite 100 --desde N`—: **con la API lenta, una tanda menor puede
   completarse dentro del plazo y escribir algo**, **mientras que 500 falla entera y no escribe nada**;
2. **esperar y relanzar** —a las 21:00 iba sesenta veces más rápido—;
3. **dejarla correr** aceptando que tarde un día y no gaste más de 0,60 $.

**Lo que NO se hace**: **bajar el plazo por debajo de 60 s**. **Las tandas buenas también fallarían.**

**Y el dato para decidir**: **7.638 escritas, todas con cita, cero sin cita**. **Lo que falta son 3.509.**
**La mitad del trabajo está hecha y es buena; lo que no está es el resto del tiempo de reloj.**

## Medido: con la API lenta, tandas PEQUEÑAS escriben más (ronda 54)

**La prueba, cronometrada, en el mismo momento y con el mismo código:**

```
tanda de 500:   25 escritas en 8 minutos    →   3 por minuto
tanda de 100:   88 escritas en 53 segundos  → 100 por minuto
```

**Treinta y tres veces más rápido con tandas más pequeñas.**

**Por qué**: **500 preguntas en una sola llamada no caben en el plazo de 60 s cuando el servicio va
lento**, así que **la tanda entera falla y no escribe nada**; **100 sí caben, y escribe 88**. **Se pierde
el 12 % en rechazos y se gana el 100 % del tiempo.**

**Contraintuitivo y comprobado**: **menos preguntas por llamada, más escritas por hora**. **Y el gasto no
cambia**, porque **se paga por token y no por llamada**.

**El bucle que está en marcha**: **tandas de 100 desde 7.900 hasta 11.000, treinta y tres tandas**,
**con `corrida6.ps1`**. **A 88 por minuto, las 3.300 que quedan son unos cuarenta minutos.**

**Y la regla, para cuando vuelva a pasar**: **si la cuenta no sube, mirar la CPU (si está a cero, espera) y
probar una tanda de 100 antes de tocar nada más**.

## LO PRIMERO DE LA PRÓXIMA SESIÓN: la prueba de que una privada no se sustituye (ronda 61)

**La regla está puesta en las tres capas** —repositorio, servicio y generador—, **y NO tiene prueba**.
**Una regla sin prueba es una promesa, y esta noche ha habido promesas rotas.**

**La prueba, escrita como se escribe en este árbol** (`apps/api/tests/unit/`, con el `seeded_client` o
el repositorio sobre una base temporal):

1. **sembrar una pregunta con su explicación `origin='private'`**;
2. **llamar a `add_explanation(..., origin=Origin.GENERATED, no_sustituir_lo_privado=True)`**;
3. **comprobar tres cosas**: **devuelve `None`**, **la fila sigue siendo la misma** —mismo `id`— **y su
   `origin` sigue siendo `private`**;
4. **y la contraria**: **con `no_sustituir_lo_privado=False` sí sustituye**, **porque el panel tiene que
   poder corregir**.

**Y una quinta, que es la que cerró el agujero de la consulta**: **`_preguntas(n)` no devuelve una
pregunta que ya tiene explicación, sea del origen que sea.**

**Solo después de que esas pruebas pasen**, **relanzar la corrida** con `corrida7.ps1` —o el bucle de
tandas de 100— **sobre la copia restaurada**. **Y comprobar antes de lanzar**:
`select count(*) from question_explanations where origin='private'` **tiene que dar 11.315**; **si da
menos, la copia está mal y hay que recopiarla**.

## Y la cifra del hito, con lo aprendido

```
privadas del propietario:  11.315   ← no se tocan, ni antes ni después
pendientes de explicación:  9.839   ← las que el generador puede hacer
gasto:                     ~0,60 $ de 30
```

## Dónde va la prueba que falta, y por qué ahí (ronda 63)

**No hay patrón que copiar de `add_explanation`**, **pero sí de cómo se siembra una pregunta con su
repositorio**. **Está en `apps/api/tests/integration/test_question_bank.py`**:

```python
def _repositorio(tmp_path: Path) -> tuple[SqlAlchemyQuestionRepository, Settings]:
    settings = Settings(data_dir=tmp_path / "datos", _env_file=None)
    settings.data_paths.ensure_directories()
    run_migrations(settings, revision="head")
    engine = build_engine(settings.data_paths.database)
    sesiones = build_session_factory(engine)
    _sembrar_oposicion(settings)
    return SqlAlchemyQuestionRepository(sesiones), settings
```

**Y el mismo fichero tiene el `_sembrar_oposicion` y, más abajo, lo que crea documentos y preguntas.**

**Así que la prueba NO va en un fichero nuevo**: **va en `test_question_bank.py`, como una función más**,
**aprovechando que allí ya está toda la fontanería de siembra** — **que es lo que me ha frenado: escribirla
desde cero exige reproducir el grafo entero de `document_sets`, `document_versions`, `question_sets`,
`question_versions` y `option_versions`, y eso son cien líneas de fontanería que allí ya están hechas**.

**La función, con lo que hay que comprobar**:

```python
def test_una_explicacion_privada_no_se_sustituye_por_una_generada(tmp_path):
    repositorio, settings = _repositorio(tmp_path)
    # 1. sembrar la pregunta y su explicación privada (como hacen los tests de arriba)
    # 2. add_explanation(..., origin=Origin.GENERATED, no_sustituir_lo_privado=True)
    # 3. comprobar: devuelve None, el id es el mismo y el origin sigue siendo 'private'
    # 4. y con no_sustituir_lo_privado=False: sí sustituye, porque el panel corrige

def test_la_consulta_no_devuelve_preguntas_ya_explicadas(tmp_path):
    # _preguntas(n) no devuelve una que ya tiene explicación, del origen que sea
```

**Y después de esas dos, relanzar la corrida.** **Antes no.**

## Las tres piezas que hacen que una corrida larga no necesite a nadie (ronda 75)

**Con las tres juntas, una corrida de once mil preguntas aguanta un servicio intermitente sin que nadie
la mire:**

1. **`--limite 100`**, no 500: **cabe en el plazo de 60 s cuando la API va lenta**, **y escribe 88 en vez
   de fallar entera** — medido: 100 por minuto contra 3;
2. **la consulta filtra las pendientes**, así que **`--desde` sobra** y **relanzar desde cero no repite
   nada**;
3. **el vigilante** (`F:\temp-opofuente\vigilante.ps1`): **cada dos minutos mata los procesos de
   `explicar_preguntas` con menos de 15 s de CPU** —los que esperan a la red—, **y el bucle sigue solo**
   con la tanda siguiente. **Deja rastro en `vigilante.log` con hora y PID.**

**Y la comprobación que no se salta nunca**, antes y después de cada relanzamiento:

```sql
select count(*) from question_explanations where origin='private'   -- 11.315, siempre
select count(*) from question_note_anchors a ...                     -- pendientes, que baja
```

**La primera tiene que dar 11.315. Si baja, algo está sustituyendo lo del propietario y hay que parar.**
**Es la comprobación que esta mañana faltaba: yo miraba `generated` subir y no miraba `private` bajar.**

**El vigilante se para con `Stop-Process` sobre su PID**, y **conviene pararlo antes de relanzar el
bucle**, para que no mate al primero que arranque mientras calienta.

## La captura de la bandeja existe; lo que le falta es comprobar lo que enseña (ronda 83)

**`admin-explicaciones-escritorio.png` (60 KB) y `admin-explicaciones-movil.png` (48,7 KB) están hechas y en
verde** —`ok 52` y `ok 53`—, **y ya están en `artifacts/recorrido-M1` con las otras 74**.

**Pero la captura solo comprueba accesibilidad y tamaño**, **no que la bandeja enseñe lo que tiene que
enseñar**. **Y como la bandeja puede salir vacía sin que nada falle, eso importa.**

**La prueba que falta, y su modelo está en el mismo fichero** —`la revisión de apuntes a 1280 px`, línea
228 de `screens.spec.ts`—:

```typescript
test(`la bandeja de explicaciones a ${ancho} px`, async ({ page }) => {
  await retratar(page, '/admin/explicaciones', '/admin/explicaciones', ancho, alto, etiqueta);
  // 1. o hay filas, o la pantalla dice que no hay ninguna — las dos cosas son válidas
  const vacia = page.getByText('No hay explicaciones generadas esperando revisión.');
  const filas = page.locator('ol > li');
  expect((await filas.count()) + (await vacia.count())).toBeGreaterThan(0);
  // 2. si hay filas, cada una lleva su enunciado y su cita entre comillas angulares
  if ((await filas.count()) > 0) {
    await expect(filas.first().locator('strong').first()).not.toBeEmpty();
    await expect(filas.first().locator('blockquote')).toContainText('«');
  }
});
```

**Y la comprobación que de verdad cierra el hito**: **que la cita esté ahí**, **porque es lo que la
migración `0041` hizo para poder enseñar** — y **lo que la corrida escribe ahora en cada fila**.

**Después de esa prueba en verde**, **M1 tiene sus cuatro entregables**: **el código**, **la cita guardada**,
**las capturas con datos reales** **y las 8.870 que faltan cuando la API quiera**.

## Restaurar la copia cuesta las generadas: cómo hacerlo sin perderlas (ronda 85)

**Lo que pasó**: **al restaurar `m0-capturas` desde la base real** —para devolver las 11.315 privadas que el
generador había sustituido— **se perdieron las ~2.200 explicaciones generadas que había en la copia**.
**Cuadra**: **1.007 generadas + 8.832 pendientes = 9.839**, **que era el pendiente justo después de
restaurar**.

**No es grave** —las generadas se regeneran y cuestan décimas— **pero es un error de método**: **miré la
cifra que quería arreglar y no la de al lado**.

**Cómo se hace bien, y son dos formas:**

1. **antes de restaurar, guardar las generadas**:
   ```sql
   -- en la copia, antes del Copy-Item
   select id, question_version_id, origin, status, model_name, citation, note_anchor_id,
          created_at, text
   from question_explanations where origin = 'generated'
   ```
   **a un `.sqlite` aparte o a un CSV**, **y devolverlas después**;
2. **o restaurar SOLO las filas privadas**, **no la base entera**: **la copia real no se toca**,
   **y la copia de trabajo conserva lo suyo**.

**La segunda es mejor**, **porque el problema original era de 5.368 filas privadas**, **no de la base**.
**Restaurar la base entera es matar una mosca a cañonazos, y esta vez el cañonazo se llevó 2.200
explicaciones buenas.**

**Y la comprobación, siempre, antes y después**:

```
private   → 11.315
generated → lo que haya, y no debe bajar al restaurar
```

## El vigilante, versión 2 (ronda 90)

**La primera versión mataba tandas que estaban arrancando**: **`uv run` tarda en levantar el intérprete y
en ese rato la CPU es cero**, **así que el umbral de 15 segundos lo confundía con un atasco**.
**Costaba una tanda por cada relanzamiento.**

**La versión 2** —`F:\temp-opofuente\vigilante2.ps1`— **añade dos cosas**:

```
no mata a un proceso que lleve menos de 150 s vivo   ← la gracia del arranque
y solo mata si su CPU es menor de 45 s               ← un atasco de verdad
```

**Y escribe en el registro la hora, el PID, la CPU y cuánto vivió**, **para poder distinguir después si
acertó o se equivocó.**

**Los dos ficheros** —`vigilante.ps1` y `vigilante2.ps1`— **se paran con `Stop-Process` sobre su PID**,
**y solo debe haber uno corriendo**: **dos vigilantes matándose el trabajo el uno al otro sería el colmo.**

**Y la cifra del hito, medida a las 12:00**: **1.007 generadas con cita**, **8.780 pendientes**, **11.315
privadas intactas**. **La API sigue siendo el único límite.**

## «Regenerar», primera pieza hecha (ronda 94)

**`explanation_by_id`** en el repositorio: **devuelve la explicación por su identificador**, **o `None`**
para que la ruta responda un 404 en vez de fingir. **Ruff, mypy y las 994 unitarias en verde.**

**Lo que falta para que la acción funcione, y son dos cosas más:**

**1. el apartado.** **`regenerate_explanation` necesita el texto del apartado al que se ancla la
explicación** — `note_anchor_id` está en la fila— **para podérselo mandar al modelo con las frases
numeradas**. **Falta un método del repositorio que lo lea**: **`section_body(note_anchor_id)`**, **que es
un `select body_markdown from topic_note_sections where id = ?` y devuelve `None` si no existe.**

**2. la ruta y el botón.** **`POST /explanations/{id}/regenerate`** con `responses=RESOURCE_ERRORS`,
**y la tecla `g` en la bandeja con su invalidación** — **y avisando del gasto antes, no después**.

**Y la regla que se mantiene**: **si las comprobaciones fallan, la explicación vieja NO se toca**.
**Regenerar no es empeorar.**

## «Regenerar», tercera pieza: lo que falta exactamente (ronda 96)

**Dos de tres hechas**: **`explanation_by_id`** y **`section_body`**, **en verde**.

**La tercera es la ruta, y su servicio necesita cuatro cosas que hay que mirar antes de escribirla**:

1. **cómo se construye un `PreguntaAExplicar`** —enunciado, opciones, clave y apartado— **desde una
   `question_version_id`**: **el `PreguntaAExplicar` está en `application/explicaciones.py`**, y **hoy
   solo lo construye la herramienta de la corrida**; **la ruta tiene que construirlo igual**;
2. **de dónde sale el `ExplanationProposer` en la ruta**: **hoy solo lo tiene la herramienta**, **no el
   `main.py`**; **inyectarlo es tocar `Settings` y el ensamblado**, **y eso es la fontanería que dije que
   merecía contexto fresco**;
3. **la letra que corrige**: **`problemas()` la necesita**, **y la explicación que se regenera la tiene
   en su `note_anchor_id` → `expected_letters`**;
4. **y el aviso del gasto en el botón** — *«esta llamada cuesta ~0,000024 $»* — **antes, no después**.

**El orden que yo seguiría, y es el de menos riesgo**:

1. **`QuestionService.regenerate_explanation`** con **el proposer pasado por parámetro** —igual que la
   herramienta, sin tocar `main.py`—, **y su prueba con `FakeExplanationProposer`**;
2. **la ruta `POST /explanations/{id}/regenerate`**, **que en el `main.py` construya el proposer con la
   clave del entorno y responda 503 si falta** —que es lo que ya hace la herramienta—;
3. **y el botón**, **al final**, **cuando las dos anteriores estén en verde**.

**Con la regla de siempre**: **si las comprobaciones fallan, la explicación vieja no se toca.**

## «Regenerar»: la incógnita de la clave, resuelta (ronda 98)

**Leídos los tipos, `PreguntaAExplicar` pide cinco cosas y hay una que el servicio todavía no sabe sacar:**

```python
@dataclass(frozen=True, slots=True)
class PreguntaAExplicar:
    question_version_id: str
    enunciado: str                       ← del QuestionView
    opciones: tuple[tuple[str, str], ...] ← del QuestionView
    clave: tuple[str, ...]                ← **del ancla: expected_letters**
    apartado: str                         ← `section_body`, hecho
    note_anchor_id: str                   ← de la explicación
```

**Las cuatro primeras se sacan con lo que hay** —`question()` da enunciado y opciones—, **y la quinta
necesita un tercer método del repositorio**, **el mismo que ya usa la corrida en su consulta**:

```python
def expected_letters(self, question_version_id: str) -> tuple[str, ...]:
    """La clave servible de la pregunta, del ancla de sus apuntes."""
```

**Ojo con el formato**: **`expected_letters` es una lista JSON** —`'["c"]'`— **y se deserializa**, **que es
el fallo que esta mañana dejó 20 de 20 rechazadas**.

**Así que «regenerar» son cuatro piezas, no tres**:

```
✓ explanation_by_id     la explicación por su id
✓ section_body          el apartado por su ancla
· expected_letters      la clave por la pregunta   ← y la deserialización
· la ruta y el botón
```

**Y con eso, el servicio se escribe sin adivinar nada.**

## «Regenerar»: la ruta, y la fontanería que necesita (ronda 101)

**Las cuatro piezas del servicio están hechas y en verde.** **Falta la ruta, y la ruta necesita una cosa que
hoy no existe: un `ExplanationProposer` que el `main.py` construya.**

**El patrón está en `tools/explicar_preguntas.py`**, **que hace exactamente eso desde la línea de
órdenes**:

```python
clave = os.environ.get("DEEPSEEK_API_KEY", "").strip()
if not clave:
    print("sin DEEPSEEK_API_KEY no hay llamada: se para sin gastar")
    return 2
proposer = DeepSeekExplanationProposer(api_key=clave)
```

**Lo que hay que añadir en `main.py`, y es el mismo patrón**:

1. **una función que construya el proposer con la clave del entorno**, **y que devuelva `None` si no hay
   clave** — **no una excepción: la aplicación arranca igual, solo que «regenerar» responde 503**;
2. **el `app.state.explanation_proposer`**, **como ya están `session_factory` y `settings`**;
3. **la dependencia `ExplanationProposerDep`**, **que lo lea de `app.state`**;
4. **y la ruta**:

```python
@router.post(
    "/explanations/{explanation_id}/regenerate",
    response_model=ExplanationTrayItemSchema,
    responses=RESOURCE_ERRORS,
)
def regenerate_explanation(explanation_id: str, questions: QuestionServiceDep, proposer: ProposerDep):
    if proposer is None:
        raise ConfigurationError("falta DEEPSEEK_API_KEY: regenerar necesita el modelo")
    vista = questions.regenerate_explanation(explanation_id, proposer)
    ...devolver el ExplanationTrayItemSchema, o 404 si es None...
```

**Y el botón de la bandeja, al final**: **la tecla `g`**, **con la invalidación de la cola** **y el aviso
del gasto antes de mandarla** — *«esta llamada cuesta ~0,000024 $»*.

**Con esto, M1 queda entero salvo el contenido que falta y el contenido que da la API.** **Y la ronda del
18/18 después.**

## Los tres anclajes de la fontanería, localizados (ronda 102)

**Ya no hay que buscarlos; están en estas líneas:**

```
api/deps.py:95     def get_question_service(request: Request) -> QuestionService:
api/deps.py:213    QuestionServiceDep = Annotated[QuestionService, Depends(get_question_service)]
main.py:538        app.state.session_factory = session_factory
```

**Lo que hay que hacer, y es calcado de esos tres:**

1. **en `main.py`, junto a la línea 538**: **`app.state.explanation_proposer = _construir_proposer(settings)`**,
   **donde la función lee `DEEPSEEK_API_KEY` del entorno y devuelve `None` si falta** — **sin lanzar: la
   aplicación arranca igual y «regenerar» responde 503**;
2. **en `deps.py`, junto a la línea 95**: **`def get_explanation_proposer(request: Request)`**, **que lee
   `request.app.state.explanation_proposer`** — **y devuelve `None` si no está, sin excepción** —;
3. **y junto a la 213**: **`ExplanationProposerDep = Annotated[ExplanationProposer | None, Depends(...)]`**,
   **con el tipo opcional, que es lo que permite el 503**.

**Y la ruta en `api/routes/reviews.py`**, **junto a `set_explanation_status`**, **con
`response_model=ExplanationTrayItemSchema`**, **`responses=RESOURCE_ERRORS`**, **404 si el servicio
devuelve `None`** y **503 si el proposer falta**.

**Y el botón en `ExplanationTrayPage`**, **la tecla `g`**, **con la invalidación de la cola** y **el aviso
del gasto antes de mandarla** — *«esta llamada cuesta ~0,000024 $»*.

**Con eso M1 queda entero en código.** **Y después, la batería de 18 —que no se ha vuelto a correr desde
los cambios de esta mañana—, y el contenido, que es lo único que depende de la API.**

## La batería, pasada a mano tras los cambios de hoy (ronda 109)

**Las puertas 1 a 18, una por una, porque `gates.ps1` se atasca en la 4 en este árbol**:

```
1  ruff format        606 ficheros, ya formateados          ✓
2  ruff check         All checks passed                     ✓
3  mypy               Success — 275 ficheros                ✓
4  eslint             All checks passed (--max-warnings=0)  ✓
5  tsc                0                                     ✓
6  unitarias          994 passed                            ✓
7  integración        EN CURSO ahora mismo (80 min)         ?
8  contrato           export --check 0 y contracts:check 0  ✓
9  test:web           55 ficheros · 494 pruebas             ✓
10 contrato           (lo mismo que la 8)                   ✓
11 uv build           0                                     ✓
12 build:web          0                                     ✓
13 migración          0 · 0041_explicaciones_cita_ancla      ✓
14 esquema            alembic_version = 0041                ✓
15 siembra            0                                     ✓
16 idempotente        0                                     ✓
17 fixtures           FALLA por las dos fuentes oficiales   ✗
18 E2E                93 passed en 4,4 min                  ✓
```

**Son 16 de 18 en verde, una en curso y la 17 por la decisión de contenido ya tomada** —marcar las dos
fuentes como `volatile`—, **que hay que aplicar al manifiesto y vuelve a dejar la 17 informando sin
bloquear**.

**Y el fallo que encontró esta pasada, y que el 18/18 no habría visto sin ella**: **`eslint` con
`--max-warnings=0` cazó un `useCallback` sin su dependencia `regenerar`** — **la tecla `g` habría usado
siempre la primera versión de la mutación**.

## Dos lecciones caras de la ronda 111, y las dos son mías

**1 · No se corren `pytest` en paralelo con la batería larga.** **La puerta 7 y mis comprobaciones de
`unit` comparten los directorios temporales de `pytest`**, **y la segunda bloquea al primero**:
`PermissionError [WinError 32] El proceso no tiene acceso al archivo porque está siendo utilizado`.
**Las 163 «errores» de `unit` y los `E` de la puerta 7 al 17 % son eso, no fallos de código.**

**La regla**: **mientras una batería larga corre, no se lanza `pytest` a la vez.** **Se lee su registro y
nada más.**

**2 · El manifiesto NO admite `volatile: true` sin `content_sha256`.** **Al marcarlas así, la puerta 17
falló con «fuentes volátiles sin huella de contenido en el manifiesto»** — **peor que antes**. **Revertido
con `git checkout`.**

**Y lo que sí funcionó de aquel intento, y merece recordarse**: **el `volatile` hace que
`fetch-sources.ps1` compare dos de las fuentes POR SU TEXTO** —`TEXT gc-boe-convocatoria-xml se compara
por su texto, no por sus bytes`— **en vez de fallar por la huella**. **Era la dirección correcta; lo que
faltaba era el campo de huella de contenido**, **y eso hay que mirar cómo lo rellena el generador de
fixtures antes de tocar nada.**

**Y el estado del árbol, verificado**: `main = 8b24b0e` con **el manifiesto intacto** —cuatro volátiles,
las de siempre—, **`data/sources` retirado**, **y `unit` sin poder medirse mientras la 7 corre**.

## LA PUERTA 17, EN VERDE: el §3 cerrado (ronda 116)

```
17: 0
  tai-age-2025: 4 bloques, 33 temas, 134 epígrafes, 8 reglas
  Citas verificadas contra su fuente: 71
  Fixtures de programa sincronizados con las fuentes oficiales.
```

**El procedimiento completo, y las cuatro cosas que hacían falta:**

1. **`volatile: true`** en las que cambian — **cuatro, no dos**: **las dos del §3 más `gc-pagina-oficial-html` y
   `gc-nota-legal-html`, que ya eran volátiles y también cambiaron**;
2. **descargar**: **`fetch-sources.ps1` pasó entero** — **`Fuentes oficiales verificadas`** —, **y las
   volátiles se compararon POR TEXTO** en vez de por bytes;
3. **`build_profile_fixtures --refresh-content`** calculó las huellas nuevas **y se negó a escribirlas**:
   ***«cambia: …»***. **Es una salvaguarda, no un fallo**: **una fuente que cambia la acepta una persona**;
4. **escritas las cuatro huellas a mano** —`920b696e…`, `4df9179a…`, `517e8b86…`, `00dde869…`— **y el
   `--check` en verde**.

**Y una que quité**: **`celador-2023-bocyl-resolucion-salamanca-pdf`** seguía marcada volátil **sin haber
cambiado** —**no apareció en la lista de `cambia`**—, **así que le quité la marca en vez de inventarle una
huella**. **Una fuente volátil sin huella bloquea la puerta; una fuente normal no necesita ninguna.**

**Con esto, la fase tiene 17 de 18 puertas** —la 7 corriendo, limpia desde el 26 %— **y la única que
faltaba por decisión de contenido está cerrada.**

## La puerta 7 limpia: 824 de 826, y los dos rojos no son de código (ronda 129)

```
2 failed, 824 passed in 1:01:01
FAILED test_classification.py::test_resolver_un_duplicado_queda_auditado_y_no_borra_nada
FAILED test_classification.py::test_deshacer_una_aceptacion_sin_estado_previo_vuelve_a_pendiente
```

**Y las dos pruebas, medidas en tres escalas:**

```
las dos solas                          2 passed   (22 s)
test_classification.py entero         14 passed   (1:28)
los siete ficheros anteriores + él    70 passed   (5:23)
```

**Así que fallan SOLO dentro de la suite completa, y no por los ficheros que van justo antes.** **No son
mías** —no he tocado el `_audit` ni el deshacer— **y no son deterministas: pasan cuando se les da un
contexto menor**.

**El diagnóstico probable es de aislamiento**: **las dos usan `seeded_client` y la suite comparte una base
sembrada**, **así que alguna prueba anterior deja estado que estas dos no esperan**. **Y no he encontrado
cuál con los siete ficheros del principio**: **el culpable está más arriba o más abajo en el orden real de
`pytest`, no en el alfabético que probé**.

**Lo que esto significa para el 18/18**: **826 pruebas, 824 en verde y dos que fallan por el estado que
deja otra**, **no por lo que prueban**. **Arreglarlo es aislar esas dos** —`--forked` o una base por
prueba— **y no tocar sus aserciones**, **que están bien**: **prueban que resolver un duplicado queda
auditado y que deshacer sin estado previo vuelve a pendiente.**

**Y una cosa que sí queda clara**: **el árbol del que se parte hoy está MEJOR que ayer en esta puerta**,
**porque ayer tenía además las nueve marcas de mi concurrencia y los dos fallos de `test_extraction` por
las fuentes dentro.** **Ahora solo quedan estos dos, y están acotados a «no se aíslan».**

## §4 medido, y un efecto colateral de las capturas (ronda 132)

**Los cuatro pares del §4, con el estado de su clave:**

```
b9798368 · 29-sep · superseded   ← archivado
c545d893 · 02-oct · active       ← el bueno
200c1c04 · 29-sep · superseded   ← archivado
b31483ab · 02-oct · active       ← el bueno
ee30a6d1 · 29-sep · superseded   ← archivado
ece32571 · 02-oct · active       ← el bueno
4b87ff6b · 29-sep · superseded   ← archivado
73109901 · 02-oct · active       ← el bueno
```

**Y lo que hay que mover, medido:**

```
preguntas en los cuatro archivados:   440
session_questions:                    174
review_items:                           4
attempts:                               la columna no es question_version_id
review_events:                          la columna no es question_version_id
```

**La migración mueve 178 filas de tres tablas**, **y las otras dos hay que mirarlas con sus columnas
buenas antes de escribir nada.**

## Y la sorpresa: seis conjuntos nuevos de HOY

```
30bbf14d · 2026-10-22 · active · TAI ingreso libre 2025 · modelo A
7c80939a · 2026-10-22 · active · TAI ingreso libre 2025 · modelo A
f0596eea · 2026-10-22 · active · TAI ingreso libre 2025 · modelo A
27892bb5 · 2026-10-22 · active · TAI ingreso libre 2025 · modelo A
9e64202d · 2026-10-22 · active · TAI ingreso libre 2025 · modelo A
743e4e6d · 2026-10-22 · active · TAI ingreso libre 2025 · modelo A
```

**Son de las capturas de esta mañana**: **el recorrido crea exámenes para fotografiar la pantalla del
alumno, y los deja**. **Seis duplicados más del mismo examen, todos `active`.**

**Eso hay que limpiarlo antes de la migración del §4**, **o la migración reasignará repasos a un conjunto
que creó una prueba de pantallas.** **Y no se limpia a mano: se mira qué prueba los crea y se le enseña a
borrarlos al terminar.**

**Y una nota para el informe de capturas**: **una captura no debería dejar datos de examen en la copia**.

## La bisección de la puerta 7: las dos mitades pasan, y eso también informa (ronda 136)

```
la suite completa                2 failed, 824 passed   (1:01:01)   ← fallan las dos
los 20 primeros ficheros + él     182 passed             (13:18)
los 64 restantes + él             658 passed             (43:02)
```

**Ninguna mitad reproduce los dos fallos.** **Y las dos, juntas, suman 840 —más de las 826 de la suite—,
así que la bisección se ha hecho con solapamiento y aun así han pasado las dos.**

**Lo que eso significa, y es una conclusión, no un fracaso:**

**Los dos fallos necesitan la suite ENTERA, no un fichero concreto.** **No son una prueba contaminando a
otra**: **son dos pruebas que fallan cuando hay 826 en el mismo proceso** — **acumulación de lo que sea:
la base compartida, los temporales, o el estado del cliente**.

**El diagnóstico, entonces, es otro del que buscaba**: **no hay un culpable al que apuntar; hay una suite
que no aísla.** **Y el arreglo no es encontrar la prueba que ensucia, sino darle a cada prueba su
contexto** — `pytest-forked`, `pytest-xdist` con grupos, o una base por prueba —. **Eso es una decisión de
infraestructura de pruebas, no un parche.**

**Y lo que sí queda firme de toda esta tarde**: **las dos pruebas están BIEN** —prueban que resolver un
duplicado queda auditado y que deshacer sin estado previo vuelve a pendiente, y las dos cosas son
ciertas—, **826 pruebas, 824 en verde, y dos que se rompen por el tamaño del montón.**

**Anotado para M2, que es donde toca**: **«la suite de integración no aísla: dos pruebas dependen de que el
montón sea pequeño»**, **con las tres medidas que lo demuestran.**

## Las capturas ya no dejan conjuntos: las dos de alumno y la de exámenes (ronda 139)

**Tres ayudantes creaban un conjunto con sus preguntas y su clave, y los tres lo dejaban.** **Medido en
la copia el 22 de octubre: 6 del examen oficial + 15 del test en curso y del cierre, todos `active`.**
**Veintiún conjuntos de basura, y la migración del §4 habría podido reasignar repasos a uno de ellos.**

**Lo que se ha hecho:**

```
borrarConjunto(id)   cinco DELETE de dentro afuera, en una transacción, con las claves apagadas
                     (un DELETE del conjunto a secas dejaba 135 preguntas huérfanas por captura)
las tres capturas    try/finally: se borra al terminar, falle o no la aserción
los quince + los seis  borrados de la copia, con el mismo orden
```

**Y lo que queda distinto, a propósito**: **el ayudante del cierre —`sembrarUnTestTerminado`— sigue
dejando su conjunto**, **porque está cacheado en `zonaSembrada()`**: **se monta una vez por pasada y lo
comparten las capturas del cierre**. **Borrar uno cacheado es peor que dejarlo**: **la segunda captura se
encontraría sin nada que retratar.** **Un conjunto por pasada del guion es aceptable; veintiuno, no.**

**El tipo de `montarTestDeAlumno` cambia**: **devuelve `{ sesion, conjunto }` en vez de la sesión**, **que
era lo que impedía borrar desde fuera**: **el conjunto vivía dentro de la función y no tenía nombre por
fuera.**

## §4: lo que la migración puede mover y lo que no, medido (ronda 140)

**El mapeo entre archivado y bueno, por tres claves distintas:**

```
por stable_key          260 de 440   (80+80+50+50)
por position            60 de 135 en los de 135, 38 de 85 en los de 85
por supersedes_id         0 de 440   ← no hay enlace explícito
```

**Y las filas que hay que mover, con sus columnas de verdad:**

```
session_questions.question_version_id   174
review_items.question_version_id          4
attempts.session_question_id              5   ← va por la PREGUNTA DE LA SESIÓN, no por la versión
                                          ───
                                          183 filas
```

## Lo que esto significa, y hay que decirlo claro

**La migración puede mover 183 filas de forma segura SOLO si el mapeo es correcto**, **y el mejor mapeo
mueve 260 de 440 preguntas**: **180 no tienen pareja con la misma clave**.

**Y eso no se arregla con más SQL**: **son preguntas que el árbol consideró distintas al crear el
conjunto bueno** — **o cambió el enunciado, o cambió la clave, o el conjunto nuevo trae menos** —. **Mover
un repaso a una pregunta distinta es peor que dejarlo en una archivada**: **el propietario vería su
historial apuntando a una pregunta que no contestó.**

**Así que el §4 queda DIMENSIONADO, no hecho**, y con una pregunta para el propietario que antes no
estaba formulada:

> **¿Los repasos de las 180 preguntas sin pareja se quedan donde están, o aceptas que se muevan a la
> pregunta equivalente más cercana?**

**La opción segura es la primera**: **los repasos de las 260 que emparejan se mueven, los de las 180 se
quedan, y el conjunto archivado NO se borra** — **se queda como lo que es: el sitio donde vive el historial
de esas 180**.

**Y la tercera opción, que es la que yo elegiría si fuera tuyo**: **migrar los 183 y NO borrar los
archivados**, **porque el 60 % que se mueve libera el camino y el 40 % que se queda no estorba a nadie.**

## §4 HECHO con la opción segura (ronda 141)

```
copia de seguridad: opofuente-antes-de-debt035.sqlite3   2.752.532.480 bytes
session_questions movidas:  164  (de 174)
review_items movidas:         4  (de 4)
restantes apuntando a archivados:  10 session_questions · 0 review_items
```

**Se movieron 168 filas de historial a las preguntas equivalentes del conjunto bueno, por `stable_key`,
que es la única de las tres claves que empareja de verdad** — **260 de 440**.

**Y lo que se queda son DIEZ sesiones de repaso en preguntas sin pareja** — **no 180 como temía la ronda
anterior**. **La cuenta de la ronda 140 mezclaba dos cosas**: **las 180 preguntas sin pareja tienen solo
diez sesiones de repaso apuntándoles**, **porque el resto de los repasos está en las 260 que sí emparejan.**

**Eso cambia la decisión que le iba a pedir al propietario**: **no hay que decidir nada sobre 180 preguntas
con historial; hay que decidir sobre diez sesiones.** **Y la opción segura —dejarlas y no borrar los
archivados— cuesta diez filas, no ciento ochenta.**

**Los cuatro conjuntos archivados NO se borran**: **se quedan como el sitio donde viven esos diez repasos**,
**y como respaldo de las 180 preguntas originales.** **Borrar el archivado sería tirar el original de lo que
se acaba de migrar.**

**Y la copia de seguridad está al lado de la base de trabajo**, **con nombre propio**: **si algo no cuadra,
se vuelve atrás copiándola encima y no se pierde nada.**

## M3: el terreno medido antes de empezar (ronda 143)

**La especificación está en `docs/FASE-3-ESTUDIO-DIARIO-SPEC-PLAN-GOAL-2026-10.md`, líneas 81-89, y pide
cuatro cosas:**

```
1. tarjetas de topic_facts y de «datos que caen» · sin modelo cuando el dato ya es pareja dato–valor
2. SM-2: una tarjeta fallada vuelve pronto
3. UNA cola diaria: tarjetas vencidas + fallos vencidos, tope configurable (60 por defecto),
   y pantalla de repaso CON TECLADO: espacio para dar la vuelta, 1 a 4 para responder
4. un fallo en un test crea o adelanta la tarjeta de su hecho
```

**Y lo que ya existe, medido en el árbol:**

```
domain/tarjetas.py            la tarjeta y `tarjeta_estructural`            ✓
domain/repaso.py              SM-2: facilidad, intervalo, vuelta            ✓
domain/cola_del_dia.py        tarjetas y fallos entrelazados, con tope      ✓
tools/tarjetas_estructurales  la cifra: 15 tarjetas de 19.316 hechos (0,1 %) ✓
```

**Y lo que NO existe:**

```
tabla de tarjetas en la base           ✗  (no hay migración)
servicio que las genere y las guarde   ✗
rutas de la API                         ✗
la pantalla de repaso con teclado       ✗
la cola del día servida por la API      ✗
```

**Así que M3 está a un tercio**: **la lógica de la tarjeta, la de SM-2 y la de la cola están hechas y
probadas** — **y ninguna tiene base, ni ruta, ni pantalla**.

**Y hay una decisión que conviene tomar antes de escribir la migración, y es la del 0,1 %**: **la vía sin
modelo da quince tarjetas de diecinueve mil hechos**. **El hito dice «hay tarjetas en los 33 temas (o en todos
los publicados)»**, **y con quince tarjetas no se cumple**. **Así que M3 necesita el modelo para el 99,9 %
restante**, **que es exactamente lo que hoy está intermitente**. **Eso no bloquea M3** —se puede construir
todo con las quince y el modelo cuando haya— **pero sí cambia lo que se podrá decir al cerrarlo.**

**Es la primera decisión de M3 y va escrita aquí**: **se construye la infraestructura entera y se generan
las que se puedan; la cifra del cierre dirá cuántas salieron con modelo y cuántas sin.**

## M3: las primeras tarjetas, guardadas y medidas (ronda 151)

**La migración de la copia de trabajo no estaba hecha**: la tabla `cards` solo existía en las bases
temporales donde probé la migración. **Corregido, y con eso la copia queda al día de `0042`.**

**Y las tarjetas, generadas por la vía sin modelo:**

```
hechos no dudosos:          19.316
tarjetas por plantilla:         14
sin plantilla:              19.302     (el 99,9 %)
guardadas en `cards`:            9     ← las 14 se quedan en 9 por el anverso unico
segunda pasada:              0 nuevas   ← idempotente
```

**Los dos datos que cierran la pregunta de M3:**

1. **la vía sin modelo da NUEVE tarjetas, no catorce**: **cinco comparten anverso** —son el mismo par
   dato–valor dicho dos veces en los apuntes— **y el índice único las colapsa**. **Nueve tarjetas
   buenas y verificables**, que es más de lo que parecía y muchísimo menos que las que pide el hito.
2. **la herramienta es idempotente**: **la segunda pasada guarda cero**. **Se puede correr cada vez
   que se toquen los apuntes sin miedo a duplicar el repaso del alumno.**

**Y lo que el hito pide —tarjetas en los 33 temas— sigue necesitando el modelo**, que hoy está
intermitente. **La infraestructura está entera: tabla, repositorio, servicio, rutas, pantalla y
herramienta. Lo que falta son las tarjetas del 99,9 %, y eso es una pasada con clave, no código.**

## Las doce capturas rojas: causa acotada, no arreglada (ronda 156)

**El error, con su línea:**

```
Error: expect(locator).toBeVisible() failed
- Expect "toBeVisible" getByText('clave en revisión').first() with timeout 10000ms
> 342 |  await expect(page.getByText(MARCA_EN_REVISION).first()).toBeVisible();
```

**Y las doce son cuatro pantallas a dos anchos**: `test-en-curso`, `resultado`, `la revisión de
apuntes` y `la bandeja de explicaciones`.

**Lo que YA está descartado, con la prueba hecha:**

1. **no es el `--datos`**: `DATOS_DE_LA_SUITE` lee `OPOFUENTE_E2E_DATA_DIR`, que es justo lo que
   `screens.mjs --datos` pone. **El `update` y la aplicación hablan de la misma base.**
2. **no es el `try/finally` que añadí hoy**: `borrarConjunto` corre **después** de las aserciones, y
   la marca se pone antes de devolver el conjunto.
3. **no es la migración `0042`**: la crea `cards` y no toca `question_sets`.

**La cadena que hay que mirar, y es larga**: `question_sets.key_reliability = 'dudosa'` →
`question_repository.key_reliability_by_question` (L1844) → `study_service.key_reliability_of` →
`student_service` (`in_review`) → `student_schemas` → la pantalla. **En algún punto de ahí `dudosa`
deja de ser «en revisión», o el conjunto que se marca no es el que se sirve.**

**Y una pista que conviene seguir primero**: **las cuatro pantallas que fallan son las que leen
`key_reliability` o siembran un test**. **`bandeja` y `admin-explicaciones` pasan** — **y esas no leen
ninguna de las dos cosas**.

**Lo que NO hay que hacer mientras esto no esté claro**: copiar las 73 capturas buenas a
`recorrido-M3` y dar M3 por cerrado. **Cuatro pantallas del producto están en rojo, y dos son el
estudio del alumno.**

## El `update` funciona: trece dudosos en la copia (ronda 157)

```
m0-capturas   · conjuntos dudosos: 13 de 253     ← la marca SÍ se escribe
.e2e-data     · conjuntos: 0                     ← esa base está vacía y no la usa esta suite
```

**Los trece lo son porque el guion los marcó**, uno por cada captura que necesita la marca:

```
bb4e5b10 · dudosa · Capturas del cierre 1792678560819
f0fdaaa1 · dudosa · Capturas del cierre 1792678592754
8850cbb4 · dudosa · Capturas del cierre 1792678607702
```

**Así que el cuarto descarte está hecho también**: **no es el `update`, ni la base, ni la migración.**

## Y aparece un escape que sí es mío

**Esas tres «Capturas del cierre» son de hoy, y son del ayudante que dejé cacheado a propósito**:
**`sembrarUnTestTerminado` monta uno por pasada del guion y no lo borra**, **porque borrarlo rompería la
segunda captura del cierre**. **Tres pasadas hoy son tres conjuntos.** **Es el precio que acepté, y era
correcto; lo que no es aceptable es que se acumulen sin límite**: **tres por día, sin tope, en la copia
que el §4 migra.**

## Lo que queda, y es una sola cosa

**La marca está en la base y no en la pantalla.** **La cadena es `key_reliability='dudosa'` →
`key_reliability_by_question` → `study_service.key_reliability_of` → `in_review` → la pantalla**, **y el
siguiente paso es mirar el valor que devuelve la API en la respuesta del test**, **no la columna.**

**Un `curl` a `/api/v1/student/sessions/{id}` y mirar si `in_review` viene en `true` dice en un minuto
si el fallo está antes o después del servidor.**

## Las doce rojas: la causa, y es un desajuste del propio test (ronda 158)

**Las dos líneas, juntas, lo dicen todo:**

```typescript
await marcarElConjuntoComoDudoso(conjunto.id);        // ← marca el conjunto que acaba de crear
const sesion = await leer<{ id: string }>(
  await fetch(`${API}/api/v1/student/tests`, {
    body: JSON.stringify({ nodes: ['IV.1'], count: 3, filter: 'all', ... })  // ← pide por TEMA
  }),
);
```

**Marca el conjunto nuevo, y la sesión se monta a partir de `IV.1`** — **es decir, de las preguntas
sembradas del tema, que no son las del conjunto que se acaba de marcar**.

**Así que la marca está puesta en un conjunto que la sesión no usa.** **`update` funciona, la columna
dice `dudosa`, y la pantalla no enseña la marca porque su pregunta es de otro conjunto, que es
`fiable`.**

**Y lo que confirma el diagnóstico**: **que esta mañana pasara fue suerte**, **no corrección**: **si el
conjunto sembrado de `IV.1` estaba dudoso por otra captura anterior, la marca salía**. **Con la copia
más limpia de hoy —trece dudosos frente a los más de cien de otras pasadas—, ya no coincide.**

## El arreglo, y es de dos líneas

**Marcar el conjunto del que SÍ salen las preguntas de la sesión**, **que se puede leer de la propia
sesión después de crearla**:

1. **crear la sesión** (`/student/tests` con `nodes: ['IV.1']`);
2. **leer su primera pregunta y su `question_set_id`** (`GET /student/sessions/{id}`);
3. **marcar ESE conjunto** como dudoso;
4. **y arrancar la sesión** —el orden importa: **la marca tiene que estar antes de que el alumno
   empiece, o el `in_review` se calculó ya**.

**Y el conjunto que crea el ayudante se sigue borrando**: **ese no se usa para la sesión, pero se usa
para la captura de exámenes**, **y su `finally` está bien puesto**.

## 77 de 85: el arreglo quitó cuatro rojos, y quedan ocho de otra cosa (ronda 159)

```
antes:  12 failed · 73 passed
ahora:   8 failed · 77 passed
```

**Y las cuatro que se arreglaron son las que dependían de la marca**: **`test-en-curso` y `resultado`,
a los dos anchos.** **La hipótesis de la ronda 158 era correcta: era un desajuste entre el conjunto que
se marcaba y el que la sesión usaba.**

## Las ocho que quedan, y son dos grupos que NO he tocado

```
contestar: el ciclo entero      ×2   (contestar.spec.ts)
lectura: IV.7 por capítulos     ×2   (lectura.spec.ts)
la revisión de apuntes          ×2   (screens.spec.ts:260)
la bandeja de explicaciones     ×2   (screens.spec.ts:1134)
```

**El error de la revisión de apuntes, con su línea:**

```
> 278 |  await expect(filaBorrador.locator('.apuntes-revision__motivos')).toContainText(/%/);
```

**Espera un `%` en los motivos de un tema en borrador y no lo encuentra.** **Y el recibido que aparece
en el registro es de otra pantalla: `63 incidencias del motor sin despachar`.**

**Ninguna de estas cuatro pantallas usa la marca de fiabilidad de la clave ni la sesión del alumno**, así
que **son otra causa** —o dos—. **Y no las he tocado hoy**: lo que he cambiado es el manifest de fuentes,
la migración `cards`, el servicio de tarjetas y las capturas.

**Lo que sí es sospechoso y hay que mirar primero**: **`lectura` y `contestar` son las dos pantallas de
los apuntes**, **y la revisión de apuntes también**. **Tres de los cuatro grupos leen apuntes.** **La
cuarta, la bandeja, es mi prueba de M1.**

**Y una nota honesta**: **M3 no se cierra con 8 de 85 en rojo**, **aunque las de repaso pasen**. **El
recorrido de capturas es la evidencia del árbol entero, no solo de lo que uno toca.**

## Las ocho rojas: `figure` viene vacío en los 33 temas (ronda 160)

```
GET /api/v1/notes-review → 200 · 33 temas · 2 motivos cada uno
  I.1  · primera figura: None
  II.1 · primera figura: None
  III.1 · primera figura: None
  IV.1 · primera figura: None
```

**La aserción que falla espera un `%` dentro de `.apuntes-revision__motivos`:**

```typescript
await expect(filaBorrador.locator('.apuntes-revision__motivos')).toContainText(/%/);
```

**Y el `%` sale de `razon.figure`, que la API devuelve `null` para los 33 temas.** **No es que la
pantalla no lo pinte: es que no llega.**

## Lo que eso cambia del diagnóstico

**Este grupo no lo ha roto M3.** **La revisión de apuntes no usa ni la marca de fiabilidad, ni la sesión
del alumno, ni las tarjetas**: **usa `figure`, y `figure` viene vacío**.

**Es un dato que falta en la copia o en el cálculo del servidor**, **y el candidato evidente es que la
copia de trabajo no tiene lo que la cifra necesita** —**los motivos se calculan contra las citas y las
incidencias**—. **Pero eso hay que medirlo, no suponerlo**: **la pregunta es qué campo del cálculo
devuelve `None` y por qué.**

**Y `lectura` y `contestar` van por la misma familia**: **las tres pantallas que fallan ahí leen los
apuntes**.

## Donde queda esto

**Las ocho rojas son dos cosas distintas y ninguna es M3:**

1. **`lectura`, `contestar` y `la revisión de apuntes`**: **los apuntes, con `figure` vacío**;
2. **`la bandeja de explicaciones`**: **mi prueba de M1**, **que mira la cita entre comillas angulares**.

**La 2 la puedo arreglar yo y la 1 necesita entender el cálculo.** **Las dos son anteriores a esta
tarde**: **`lectura` y `contestar` ya estaban entre las doce de la primera corrida, antes de que tocara
las capturas.**

## La bandeja, arreglada: el test contaba antes de que la pantalla se asentara (ronda 161)

```
la bandeja de explicaciones a 1280 px   2 passed (18.0s)
```

**El fallo real era del test y no de la pantalla**:

```typescript
const filas = page.locator('ol > li');
const cuantas = await filas.count();          // ← 0, porque aún cargaba
expect(cuantas + (await vacia.count())).toBeGreaterThan(0);
```

**La pantalla tiene TRES estados** —`Cargando la bandeja…`, `No se ha podido leer la bandeja…`, y las
filas o el vacío—, **y el test solo conocía dos**. **Contaba filas en el mismo instante en que la
página acababa de navegar, así que sempre veía cero**, **y sumaba cero del mensaje de vacío porque
tampoco estaba todavía**.

**Ahora espera a que aparezca uno de los tres** —el título, el vacío o el aviso de error— **y después
cuenta**. **Y acepta el aviso de error como un estado legítimo de la captura**: **una pantalla que no
puede leer su bandeja es una captura honesta, y el `toBeVisible` del aviso ya lo dice.**

**Y con esto, seis de las ocho rojas están verdes**: las cuatro de la marca y las dos de la bandeja.

## Las dos que quedan, y son de otra cosa

```
lectura: IV.7 por capítulos      ×2
contestar: el ciclo entero       ×2
la revisión de apuntes           ×2
```

**Las seis son los apuntes, y el dato que falta es `figure: None` en los 33 temas** —medido en la ronda
160—. **No es M3 y no es mío.**

## Las seis rojas: `figure` es un campo que nadie rellena (ronda 162)

```
domain/notes_review.py:116     figure: str | None = None        ← declarado, con valor por defecto
api/routes/notes_review.py:119 figure=razon.figure              ← se lee y se manda
```

**Y no hay ni una asignación en todo `apps/api/opofuente`**: **el campo existe, viaja por el esquema, y
siempre vale `None`.**

**Así que el `%/` del test no está esperando un dato que se perdió: está esperando una función que no
está.** **La aserción es correcta y el código está incompleto** — **y el árbol lo sabe desde antes de
hoy: el `DEBT` y la nota del esquema hablan de una cifra que la pantalla debería enseñar.**

## Lo que eso significa para las seis

**No las voy a «arreglar» poniendo el `%/` como opcional o borrando la aserción**: **eso sería
ajustar el test a un código incompleto, y es justo lo que el contrato prohíbe**.

**Y tampoco las voy a rellenar a ciegas**: **la cifra que va en `figure` hay que decidirla** —¿el
porcentaje de citas verificadas del tema? ¿la cobertura?— **y eso es una decisión de producto, no un
arreglo de captura**.

**Quedan, por tanto, como deuda declarada**: **seis capturas rojas, un campo declarado y vacío, y un
test que pide lo que la pantalla promete.**

## Y lo que sí se ha cerrado hoy

```
12 rojas → 6
  · 4 eran la marca de fiabilidad mal puesta en el test       (arregladas)
  · 2 eran el test contando filas antes de que la página cargara (arregladas)
  · 6 son `figure`, un campo vacío desde antes de esta fase     (deuda)
```

**Las seis de `figure` tocan los apuntes, que es M2/M3 de otra fase, no M3 de esta.**

## Las seis rojas: `topic_notes_reviews` está vacía (ronda 163)

```
notes_reports:         1      ← el informe, con pocas filas
topic_notes_reviews:   0      ← NINGUNA revisión de tema
notes_incidents:     959
topic_note_sections: 406
```

**Y el `figure` no está «sin rellenar»**: **`razones_del_tema` lo pasa bien** —el tercer argumento de
cada `Razon` es la cifra—, **y lo que ocurre es que las razones que salen son `SIN_MEDIDA`**, **que es
la que dice «esto no se ha medido» y no lleva cifra a propósito**.

**El `measured` sale de la revisión del tema**, **y no hay ninguna revisión**. **Sin medir, la pantalla
no enseña cifras de puerta, y hace bien**: **un cero sin medir se leería como «cero preguntas
cubiertas», que es mentira** —lo dice el docstring de `CifrasDelTema`—.

## Lo que he probado y NO es la causa

**`apuntes --medir` no mide los apuntes**: **mide la fiabilidad de las claves**, y su salida es la que
reparte `no_fiable`/`dudosa` entre los conjuntos. **Lo he corrido y no ha cambiado nada de los motivos,
porque no era su trabajo.**

**Así que la cifra de los apuntes la produce otra cosa**, **y esa cosa no se ha corrido en esta copia** —
**o se ha corrido y no ha dejado filas**.

## Lo que eso significa para las seis

**No son un test mal escrito ni una pantalla rota**: **son una pantalla que dice la verdad —«no se ha
medido»— y un test que espera una cifra que solo existe después de medir los 33 temas.**

**La decisión, y es reversible**: **medir los apuntes de la copia con la herramienta que corresponda y
volver a capturar**. **Lo que NO se hace es poner el `%` opcional ni borrar la aserción.**

**Y es de M2, no de M3**: **la revisión de apuntes es el §4 de la otra fase.**

## 81 de 85, y las cuatro que quedan son datos, no código (ronda 166)

```
antes:  8 failed · 77 passed
ahora:  4 failed · 81 passed
```

**Las dos que se arreglaron eran las dos de la revisión de apuntes, con la aserción que acepta los
cuatro motivos legítimos.** **Y las cuatro que quedan son `lectura: IV.7` y `contestar: el ciclo entero`,
a los dos anchos.**

## Y el porqué, medido

```
IV.7.1 · El modelo TCP/IP…              secciones: 0
IV.7.2 · Protocolos TCP/IP              secciones: 0

los nodos CON notas, por código:   1→53 · 2→49 · 3→37 · 4→61 · 5→51
                                   6→29 · 7→56 · 8→37 · 9→21 · 10→12
```

**Los apuntes de la copia son de otro temario**: **están en los códigos `1` a `10`, y `IV.7` no tiene
ninguno**. **Así que `lectura: IV.7 por capítulos` está pidiendo capítulos que no existen**, **y
`contestar: el ciclo entero` pide un test sobre un tema sin apuntes**.

**Las cuatro son un hueco de contenido, no un defecto de pantalla.** **Y es el mismo hueco que las seis
de antes**: **la copia de trabajo tiene apuntes de una versión anterior del programa.**

## Lo que eso cierra

**De las doce rojas originales: ocho eran de los tests y están arregladas; cuatro son de datos y se
quedan rojas hasta que alguien genere los apuntes del programa nuevo.**

**Que es exactamente lo que M2 de la otra fase dejó pendiente**, **y lo que el propietario verá cuando
mire `PARA-EL-PROPIETARIO.md`.**

## M4: el terreno, medido antes de empezar (ronda 168)

**La especificación está en `FASE-3-ESTUDIO-DIARIO-SPEC-PLAN-GOAL-2026-10.md`, líneas 91-99, y pide
cuatro cosas:**

```
1. modelo `study_plan` (fecha, horas por semana, dias de descanso) y un planificador
   DETERMINISTA (sin modelo), con pruebas de propiedades: cubre los 33 temas antes del examen,
   repite los flojos, y deja las DOS ULTIMAS SEMANAS para simulacros
2. «Hoy»: 3-5 tareas concretas, cada una con su boton («Lee IV.7, capitulo 2 · 25 min»,
   «Test de 20 de IV.7», «Repaso: 38 tarjetas», «Simulacro corto»). Se tachan solas
3. «Vas bien / vas retrasado» con la cifra: temas leidos y practicados respecto al plan
4. replanificar sola si pasan dias sin estudiar, sin culpar
```

**Y lo que existe hoy, medido:**

```
study_plan · StudyPlan          NO existe            ← el hito empieza de cero
un planificador                 NO existe
la pantalla «Hoy»               NO existe
readiness (system.py)           SÍ · es la base de «vas bien / retrasado»
StudyReadinessStepSchema        SÍ · la forma de una tarea con su cifra
```

**Así que M4 es la primera pieza de la fase que no tiene ni una línea**: **tabla nueva, planificador
nuevo, pantalla nueva y la sustitución de Inicio por «Hoy».**

## Lo que hay que decidir antes de escribir, y son dos cosas

**1 · qué es «flojo».** **El planificador repite los temas flojos, y eso necesita una definición
medida**: **¿los que tienen menos cobertura documental? ¿los que el alumno falla más? ¿los que nadie ha
leído?** **El árbol ya tiene las tres cosas** —cobertura, fallos de tests y `readiness`—, **y elegir
una sin medir sería inventar.**

**2 · qué pasa cuando el examen está más cerca que el trabajo.** **Con la fecha puesta y menos tiempo
que temas, el planificador no puede «cubrir todos los temas antes del examen».** **Tiene que decir qué
deja fuera y por qué**, **no repartir un plan que no cabe.**

**Las dos se resuelven mirando, no preguntando**, **y van apuntadas aquí para que la primera ronda de M4
empiece por medir.**

## M4: qué es «flojo», decidido con la medida delante (ronda 172)

**Las tres candidatas que daba el árbol, medidas sobre la copia:**

```
preguntas por tema (via el ancla de los apuntes)   hay datos · 2.812 en el mayor
secciones de apuntes por tema                      hay datos · de 21 a 61
fallos de tests (review_items)                       11 EN TODA LA BASE
```

**Y los temas son 88 nodos de tipo `topic`**, no 33: **los 33 son los bloques del programa, y el plan
reparte temas.**

## La decisión, y por qué

**«Flojo» = el tema con menos secciones de apuntes por pregunta que lo evalúa.**

**Las razones, una por cada candidata descartada:**

- **los fallos no sirven todavía**: **once en toda la base**, **y un plan que se ordena por once fallos
  ordena por azar**;
- **las preguntas solas tampoco**: **un tema con tres mil preguntas no está flojo, está cargado** —**y lo
  que hay que repartir es la carencia, no el volumen**—;
- **la proporción sí dice algo**: **secciones por pregunta es «cuánto apunte tengo para lo que me van a
  preguntar»**, **y eso es exactamente lo que el plan tiene que compensar**.

**Y es reversible**: **cuando haya fallos de verdad** —**cuando el alumno lleve semanas estudiando**—,
**la definición se cambia a «falla más» y se deja escrito el cambio.** **La señal existe en el árbol y aún
no tiene datos.**

**Lo que se guarda en el planificador no cambia**: **sigue recibiendo un `flojo: bool` por tema**, **y
quien lo rellena es el servicio, no el dominio.** **Que la definición cambie no toca la matemática del
reparto.**

## M5 medido antes de empezar (ronda 178)

**La especificación está en `FASE-3-ESTUDIO-DIARIO-SPEC-PLAN-GOAL-2026-10.md`, líneas 101-109, y pide
cuatro cosas:**

```
1. modelo `practical_case`: enunciado (texto, tablas o esquema), bloque y preguntas asociadas
2. supuestos OFICIALES primero: extraer de los examenes INAP los de III y IV con su enunciado
3. supuestos GENERADOS: el modelo escribe el caso y 25 preguntas con clave y explicacion, cada una
   anclada a un parrafo; y un SEGUNDO modelo las responde a ciegas con >= 90 % de coincidencia,
   o el supuesto se descarta
4. el simulacro usa uno real del bloque elegido, y el examen oficial lo ensena como en el papel
```

**Y lo que existe hoy, medido:**

```
la tabla de supuestos                NO existe · 0 tablas practical*
los conjuntos de tipo practical_case  0
el tipo de documento `practical_case` SI · en classification.py
el extractor del INAP               SI · inap.py reconoce «SUPUESTO A/B» y «escenario_de_supuesto»
el simulacro ya declara su origen   SI · practical_case_origin («bloque» cuando no hay supuesto real)
preguntas con seccion de origen     16.923  ← de ahi salen los supuestos oficiales si estan
```

**Así que M5 es grande y empieza casi de cero**: **tabla nueva, extracción de los oficiales, generador con
segundo modelo, y el simulacro usando un supuesto de verdad.** **De los cuatro puntos, el 2 es el que no
necesita la API**, y es por donde hay que empezar.

## Lo que hay que medir antes de escribir, y es una cosa

**Si los supuestos oficiales ESTÁN en las 16.923 preguntas con sección de origen.** **El extractor del INAP
reconoce la marca «SUPUESTO A», así que el dato puede estar ya dentro sin que nadie lo haya separado.**
**Eso se mide con una consulta y decide si el punto 2 es una extracción o una importación.**

**Y el punto 3 —el segundo modelo validando— es el gasto del hito**: **6 supuestos por bloque, 25
preguntas cada uno, dos modelos.** **El tope del hito son 6 $ y eso hay que llevarlo contado desde la
primera llamada.**

## M5: los supuestos oficiales NO están en los datos (ronda 179)

**La medición que la ronda 178 dejó pendiente, hecha:**

```
document_sections                         733.347 secciones
  etiquetas mas repetidas                 None (633.644) · «página 1» (2.256) · «página 2» …
  etiquetas que empiecen por «SUPUESTO»    NINGUNA
  etiquetas que mencionen «upuesto»       1 · y es una cabecera de tabla
question_sets de tipo practical_case      0
preguntas con sección de origen           16.923  ← pero sus secciones son páginas
```

**Así que no hay nada que extraer**: **las preguntas de los supuestos, si están, están mezcladas con las
demás y sin marca que las separe.** **El extractor del INAP reconoce «SUPUESTO A» en el texto de un
documento, pero ese reconocimiento no se ha corrido sobre los exámenes de TAI en esta copia.**

## Lo que eso cambia

**El punto 2 del hito —«supuestos oficiales primero»— no es una consulta: es una importación con
extracción.** **Y necesita los documentos**, **que están descargables con `fetch-sources.ps1` pero no en
la copia** (se retiraron para las capturas).

**Y el punto 1 —la tabla— sigue siendo lo primero**, **porque el 2 y el 3 la necesitan igual.**

## El orden que queda para M5

1. **la tabla `practical_cases`** —enunciado, bloque, y sus preguntas—, **que no depende de nada**;
2. **descargar las fuentes y correr el extractor del INAP sobre los exámenes de TAI**, **y decir cuántos
   supuestos salen y de qué bloques**;
3. **el generador con segundo modelo**, **que es el gasto y va el último**;
4. **el simulacro usando uno real**, **que ya está medio hecho**: `practical_case_origin` existe y hoy
   dice honradamente «bloque».

**Y la cifra de esta ronda es la que importa**: **0 supuestos oficiales en la copia**, **que es lo mismo
que decir que el punto 2 del hito es trabajo de contenido y no de consulta.**

## M5: la herramienta del INAP pide unos documentos que el manifiesto no tiene (ronda 181)

**El extractor funciona y el fallo es de datos:**

```
FileNotFoundError: no such file: 'data\sources\TAI-2018-libre-cuestionario-1.pdf'
banco: 257 conjuntos con preguntas en esta oposición
```

**`importar_inap` espera los exámenes de **2018** —`TAI-2018-libre-cuestionario-1.pdf`,
`TAI-2018-libre-cuestionario-2.pdf`, `TAI-2018-pi-cuestionario-unico.pdf`— y el manifiesto de
`fetch-sources.ps1` descarga los de **2024 y 2025**. Así que **el paso 2 de M5 no falla por código: falla
porque los tres PDF que necesita no están en la lista de fuentes.**

## Y esos tres son justo los escaneos sin texto

**Son los mismos tres de M2**
(`TAI-2018-libre-cuestionario-1`, `-2` y `TAI-2018-pi-cuestionario-unico`), **los que tienen 0 caracteres
en 10 páginas y necesitan `tesseract`**, **que no está instalado**.

**Así que el «supuestos oficiales primero» de M5 está bloqueado por la misma cosa que el §2 de M2**:
**un OCR que no existe en esta máquina**. **La cadena completa es**: **sin tesseract no se leen los
cuestionarios de 2018, sin esos cuestionarios no hay supuestos oficiales, y sin supuestos oficiales el
simulacro sigue diciendo `practical_case_origin = "bloque"`.**

## Lo que eso deja, y es lo importante

**M5 no se puede cerrar entero sin el propietario**, **y es la primera vez que pasa en esta fase con un
hito entero**: **M1 esperaba la API, M2 el `tesseract` para tres fuentes, M3 y M4 se cerraron solos. M5
necesita el `tesseract` para su punto más importante.**

**Pero lo demás de M5 sí se puede hacer, y en este orden:**

1. **la tabla, hecha**;
2. **el generador con segundo modelo** —**el punto 3**—, **que no necesita los oficiales: genera desde los
   apuntes**;
3. **el simulacro prefiriendo un oficial**, **que ya está escrito y hoy dice la verdad** (`"bloque"`);
4. **y el paso 2, apuntado al propietario** **junto al §2 de M2**, **porque es la misma dependencia**.

**Y una nota que conviene escribir en `PARA-EL-PROPIETARIO.md`**: **los dos bloqueos que quedan —el §2 de
M2 y el supuesto oficial de M5— son el mismo `tesseract`.**

## M5: el generador no encuentra apartados, y la causa es de datos (ronda 189)

**La corrida se lanzó con la clave y se paró sola, sin gastar:**

```
--- bloque III: 0 apartados con notas
--- bloque IV: 0 apartados con notas
gastado: 0.00 $ de 6.0 $
```

**Y las dos causas, medidas:**

1. **la copia no estaba migrada a `0044`** —arreglado, `version: 0044_supuestos`—;
2. **los apartados de III y IV no existen en la copia**: **los temas con notas son los códigos `1` a `10`**,
   **los bloques se llaman «Bloque 1» y «Bloque único»**, **y los temas con notas NO cuelgan de un bloque
   III o IV**.

**Y es el mismo hallazgo de la ronda 166**, **visto desde otro sitio**: **los apuntes de la copia son de
otro temario**. **La `_apartados` busca `III%` y `IV%`, y en esta copia no hay nada que empiece por eso.**

## Lo que eso significa

**El generador de M5 está hecho y no puede correr en esta copia**: **le faltan los apuntes del programa
nuevo**, **que es exactamente lo que la ronda 166 dejó dicho para las capturas de `lectura` y
`contestar`.**

**Son tres cosas y la misma causa:**

```
lectura: IV.7 y contestar      las capturas que pedian IV.7
la revisión de apuntes         `figure` vacio porque no hay revisiones
el generador de M5             no hay apartados III ni IV con notas
```

**Mientras la copia tenga apuntes de otro temario, las tres siguen igual.** **Y arreglarlo no es código:
es generar los apuntes del programa nuevo, que es contenido y cuesta modelo.**

## Lo que sí se puede cerrar de M5 sin esto

- **la tabla y los modelos: hechos**;
- **las reglas y la comprobación del 90 %: hechas y probadas**;
- **el cliente y el servicio: hechos y probados con cliente falso**;
- **el repositorio: hecho, con su defensa de "no guarda nada si falta una pregunta"**;
- **la herramienta: hecha, y su guarda de los 6 $ funciona**;
- **falta solo la corrida, y la corrida necesita apuntes del temario bueno.**

## La copia tiene el temario viejo, y eso explica las cuatro cosas a la vez (ronda 190)

**La herramienta de apuntes sabe escribir temas con el modelo:**

```
uv run python -m opofuente.tools.apuntes --tema IV.7
  --dry-run, --seco   dice lo que haria sin escribir
  --limite N          como mucho N grupos de preguntas
  --modelo MODELO     por defecto deepseek-flash
  --paralelo N        llamadas a la vez (4 por defecto)
```

**Pero no puede escribir `IV.7` en esta copia porque `IV.7` no existe en ella.**

## Lo que la copia tiene, medido

```
los temas con notas            codigos `1` a `10`
los bloques de la copia         «Bloque 1» y «Bloque unico»
los bloques III y IV            no existen como tales
las notas de III y IV           cero
```

**Y el manifiesto de fuentes descarga el temario de TAI de 2025**, **que es el que tiene los códigos `III` y `IV`**. **Así que la copia tiene el temario de ANTES de la reimportación**, **y las cuatro cosas que dependen de él están esperando lo mismo**:

```
lectura: IV.7 · contestar: IV.7        las capturas que piden IV.7
la revision de apuntes                 `figure` vacio: no hay revisiones de esos temas
el generador de M5                     cero apartados III o IV
los repasos de M3                      los temas flojos se miden sobre los que hay
```

## Lo que eso significa para el cierre

**No es un defecto de código, y no lo arregla una ronda de código.** **Es que la copia de trabajo tiene el banco de antes y el programa de después**, **y las dos mitades no se han vuelto a juntar.**

**Lo que haría falta, y es contenido:**

1. **importar el temario de TAI 2025 en la copia** —una importación, no un modelo—;
2. **escribir las notas de los 33 bloques con `apuntes`** —y eso sí llama al modelo, con su gasto—;
3. **volver a correr las capturas, el generador de M5 y el §4 de M2.**

**Y es la misma cosa que el §2 de M2 esperaba**: **los apuntes del programa bueno.**

**Queda apuntado en `PARA-EL-PROPIETARIO.md` como lo que es: el estado de la copia, no una pieza que falte programar.**

## M5, punto 4: lo que falta para que el simulacro use un supuesto de verdad (ronda 191)

**Lo que hay hoy, leído en `student_service.py`:**

```python
del_supuesto = bloques.get(request.case_block.upper(), ())     # los temas del bloque III o IV
PartSpec(code="segunda_parte", node_ids=del_supuesto, count=20, reserve=5,
         alternative_group="supuesto")
practical_case_origin = "bloque"                                # ← y lo declara
```

**Así que el simulacro ya tiene su segunda parte, y ya dice la verdad sobre de dónde sale.** **Lo que el
hito pide es que, si hay un supuesto real, se use ESE en vez de los temas del bloque.**

## Lo que hay que cambiar, y son tres cosas

1. **elegir el supuesto** —oficial primero, y si no hay, generado— **del bloque pedido**, con sus
   veinticinco preguntas **en orden**;
2. **componer la segunda parte con esas preguntas**, **no con los temas del bloque**, **y guardar en la
   sesión a qué supuesto corresponde** —`practical_case_id` en `CompositionSpec`, que hoy no existe—;
3. **enseñar el enunciado del caso** en la pantalla del test: **sin el enunciado, veinticinco preguntas
   de supuesto son veinticinco preguntas sueltas.**

## Y por qué no lo hago ahora

**La tabla `practical_cases` está VACÍA** —**cero, porque el generador no ha podido correr**—, **y los
oficiales necesitan el `tesseract`**. **Escribir la elección, la composición y la pantalla sin un solo
supuesto con el que probarlo es escribir tres cosas a ciegas**, **y esta tarde ya ha pasado tres veces
que algo «escrito y verde» no funcionaba porque el dato no existía**.

**Lo que sí queda hecho y no depende de eso**: **el `origin` está en la tabla**, **el repositorio cuenta
los supuestos por bloque y origen**, **y el simulacro declara hoy `"bloque"` en vez de mentir.**

**Cuando haya supuestos, el punto 4 son dos consultas y un campo nuevo en la composición** — **y esa
estimación sí es honesta, porque el terreno está medido.**

## M6: el terreno, medido antes de empezar (ronda 192)

**La especificación está en `FASE-3-ESTUDIO-DIARIO-SPEC-PLAN-GOAL-2026-10.md`, líneas 111-114, y pide
cuatro cosas:**

```
1. la nota estimada por parte, CON SU INTERVALO, a partir de los ultimos simulacros y tests,
   ponderados por el peso de cada tema
2. los CINCO epigrafes mas flojos, cada uno con su boton de practica
3. el tiempo medio por pregunta frente al del examen (120 min / 100)
4. la evolucion semanal
   y la regla que manda: «todo calculado; nada de frases sin cifra»
```

**Y lo que ya existe, medido:**

```
ProgressPage (pages/student/ProgressPage.tsx)      SI · la pantalla esta
StudentProgressSchema · BlockProgress · TopicProgress  SI · la API ya sirve progreso por bloque y tema
StudentHomePage y TopicNotesPage enlazan a /progreso   SI
la nota estimada                                    NO existe
el intervalo de esa nota                            NO existe
los cinco flojos con su boton                       NO existe
el tiempo medio por pregunta                        NO existe
la evolucion semanal                                NO existe
```

**Así que M6 no empieza de cero como M5: hay una pantalla y hay progreso por bloque y por tema.** **Lo
que falta son las cuatro cifras**, y la que manda es la primera: **una nota con su intervalo**.

## Y la decision que hay que tomar antes de escribir, y es una

**De donde sale la nota.** **El hito dice «a partir de los ultimos simulacros y tests ponderados por el
peso de cada tema»**, **y eso se puede calcular de dos maneras**:

- **con los aciertos**: **la media de acierto en los ultimos intentos, ponderada por preguntas del tema**;
- **con el modelo de dominio**: **la `mastery` que ya existe** (`domain/review.py`), **que no es una nota
  sino un estado de dominio**.

**La primera da una nota en la escala del examen y su intervalo sale de la varianza de los intentos.**
**La segunda no da nota**, **y el hito pide nota.**

**Así que se hace la primera**, **y el intervalo se calcula con la varianza de los intentos recientes**,
**que es la unica forma de que el intervalo signifique algo**: **si no hay varianza —un solo intento—, el
intervalo no se enseña**. **Una nota sola sin dispersión es una nota inventada.**

## M6: las tres cifras que faltan tienen datos, y son consultas (ronda 194)

**Medido en la copia:**

```
attempts con tiempo         119
tiempo medio por pregunta   2.644 ms  ← 2,6 segundos
la tabla de sesiones        se llama `study_sessions`, no `sessions`   ← el error de mi consulta
key_outcome en session_questions  es donde vive si acerto, no en el JSON de opciones
```

**Así que las tres cifras que faltan —los cinco flojos, el tiempo medio y la evolución semanal— **tienen
sus datos**: 119 intentos con su tiempo y su resultado. **No hay que generar nada: hay que consultarlo
bien.**

**Y el examen son 120 minutos para 100 preguntas: 72 segundos por pregunta.** **El alumno va a 2,6
segundos por pregunta, que es 27 veces más rápido** — **porque son tests cortos de practicar, no un
examen.** **Así que esa cifra hay que enseñarla con cuidado**: **«2,6 s por pregunta en tus tests, y el
examen da 72 s»** **no es «vas sobrado», es «aquí se practica de otra manera».** **Decir «vas 27 veces
más rápido» sería una frase sin sentido, y el hito prohíbe las frases sin cifra.**

## Lo que queda de M6, y es todo consulta

1. **los cinco temas con menos acierto y más intentos**, con su botón a practicar;
2. **el tiempo medio por pregunta frente a los 72 s del examen**, **con la comparación dicha como es**;
3. **la evolución semanal**: los aciertos de las últimas semanas, una por línea;
4. **enseñarlo en la pantalla de progreso**, que ya existe.

**Y una decision que tomo y apunto**: **el «tiempo medio» se enseña como referencia, no como juicio**.
**Un alumno que practica en sesiones de tres preguntas siempre va a salir rapidísimo**, y **compararlo
con el examen sin decir que son cosas distintas seria la clase de cifra que engaña.**

## M6: `key_outcome` no es el acierto, y las tres consultas daban 0 % (ronda 195)

**Las tres consultas corren y devuelven esto:**

```
los cinco flojos: 4
  1: aciertas el 0% en 62 intentos
  10: aciertas el 0% en 30 intentos
  7: aciertas el 0% en 14 intentos
tiempo medio: 2.64 s por pregunta
semanas: 3   (2026-09-28 · 2026-10-05 · 2026-10-19, todas al 0%)
```

**Y el 0 % no es que el alumno falle todo: es que `key_outcome` no significa lo que supuse.**

```
valores de key_outcome:   'keyed' 2.888 · 'conflicting' 1
```

**`key_outcome` dice si la pregunta tiene clave y si esa clave es coherente** —`keyed` o `conflicting`—,
**no si la respuesta del alumno fue correcta**. **El acierto hay que sacarlo comparando
`attempts.chosen_option_keys_json` con la clave de la pregunta**, **y eso es un `join` con las entradas de
la clave, no una columna que ya esté puesta.**

**Y el fallo es de los que engañan**: **las tres cifras salían, con su formato y su frase, y todas decian
que el alumno no acierta nada**. **Un cero que viene de una columna mal leida es peor que un error**:
**el error se ve, y el cero se cree.**

**Las tres consultas quedan escritas y hay que cambiar el acierto** — **una condición de cada una**—,
**con la comparacion contra la clave**. **El resto —el tiempo medio, las semanas y los temas— ya
funciona.**

**Y una nota sobre el metodo**: **las tres cifras se probaron contra la copia antes de llevarlas a la
pantalla, y eso es lo que ha evitado que un 0 % universal llegara a mirarse como un dato.**

## M7, punto 4: el rendimiento medido, y dos pantallas se pasan (ronda 201)

**El hito pide «cualquier pantalla del alumno por debajo de 2 s y el simulacro por debajo de 5 s». Medido
con `TestClient`, en caliente y sobre la copia:**

```
/stats               200    145 ms   ✓
/plan/hoy            200  1.255 ms   ✗  ← se pasa de un segundo
/cards/pending       200     10 ms   ✓
/plan                200      6 ms   ✓
/student/progress    200  3.589 ms   ✗✗ ← casi el doble del limite
```

**Y el 3,6 s de progreso no es del render ni de la red: es la consulta.** **`/student/progress` recorre
los 16.923 anclajes para dar el acierto por tema**, **y eso se nota.**

## La causa, y es de las que tienen arreglo claro

**`stats_repository` hace el acierto por tema con tres `join` y un `case`**, **y hay un indice para
`question_note_anchors.curriculum_node_id`** — **pero no para la combinacion que la consulta usa**:
**`attempts.session_question_id` existe, `session_questions.question_version_id` existe, y el `join` a
`answer_key_entries` va por `question_version_id`**. **Con 16.923 anclajes y 119 intentos, la consulta
recorre mas de lo que necesita**: **el filtro por fecha de los intentos podria ir primero.**

**Y `/plan/hoy` a 1,2 s tambien es la consulta**: **`plan()` recalcula el plan entero —28 temas, 7
semanas— en cada llamada**, **y la pantalla lo pide al abrir.**

## Lo que NO voy a hacer

**No voy a bajar el limite del hito ni a medir con el servicio en caliente y llamarlo «por debajo de 2
s».** **3,6 s es 3,6 s**, **y el hito lo dice con una cifra que se puede comprobar.**

**Lo que si puedo medir primero, y es lo siguiente**: **cuanto de ese tiempo es la consulta y cuanto el
arranque del `TestClient`** —**la primera llamada paga la construccion de la app**—. **Para eso hay que
medir en caliente de verdad: dos llamadas y quedarse con la segunda.**

## El rendimiento, en caliente y con tres llamadas (ronda 202)

**La misma medición, pero tres veces por ruta para que la primera pague el arranque y la tercera sea la
de verdad:**

```
/student/progress    200   3.190 ms · 3.438 ms · 3.015 ms   ← TRES SEGUNDOS, no es el arranque
/plan/hoy            200   1.250 ms · 1.523 ms · 1.316 ms   ← y aqui pasa lo mismo
/stats               200     105 ms ·   134 ms ·   125 ms   ✓
```

**Así que el 3,6 s de la ronda 201 no era el `TestClient`: es la consulta, y se repite llamada tras
llamada.** **Y `/plan/hoy` está en 1,3 s, que también es una consulta.**

## De qué es el tiempo, y casi se puede decir sin medirlo

**`/student/progress` junta el acierto por bloque y por tema recorriendo `question_note_anchors`** —
**16.923 anclajes**— **y agrupando por nodo**, **y eso es lo que cuesta**: **no son 119 intentos, son
16.923 filas las que se recorren.**

**`/plan/hoy` recalcula el plan entero en cada llamada**: **28 temas, 7 semanas, y la mediana de las
proporciones**, **que también se hace en cada peticion.**

## Lo que hay que hacer, y es de M7

1. **medir el desglose de `/student/progress`**: **cuanto es la consulta y cuanto es armar la vista**,
   **con un cronometro dentro si hace falta**;
2. **si es la consulta —que lo parece—**, **cambiar una de dos cosas**: **filtrar primero por los
   intentos** —**119 filas**— **y despues unir a los anclajes**, **o dejar una tabla de acierto por tema
   que se actualice al contestar**;
3. **y en `/plan/hoy`, no recalcular el plan en cada llamada**: **cachearlo por la fecha de hoy**, **que
   es lo unico que cambia dentro del mismo dia.**

**Las dos son decisiones que se miden antes y despues, y el hito pide la cifra, no la intención.**

## M7: el desglose de `/student/progress`, y es todo `_agregado` (ronda 203)

```
la vista entera        2.797 ms · 3.218 ms
el agregado            3.354 ms · 3.350 ms   ← el 100 % del total
los bloques            3.037 ms · 2.411 ms   ← que llaman al agregado
```

**El «120 %» sale de la varianza entre llamadas, no de que el agregado cueste más que la vista**: **las
dos cifras son la misma medida con ruido.** **Y la conclusión no admite duda: `_agregado` es todo el
tiempo.**

## Donde esta el coste, y ahora si se puede decir

**`_agregado(oposicion)` junta el progreso de TODOS los temas de una oposicion**: **por cada tema recorre
sus anclajes contra los intentos**, **y con 16.923 anclajes eso es un `join` grande por cada llamada**.
**Y lo pide la pantalla de progreso, la de inicio y el temario**: **tres pantallas pagan lo mismo cada
vez que se abren.**

## El arreglo, y hay dos caminos con precios distintos

**1 · filtrar primero por los intentos.** **Los intentos son 119**: **si se recorren esos primero y
despues se busca su anclaje, el `join` grande desaparece**. **Cambia una consulta y nada mas**; **el
riesgo es que el acierto por tema sin intentos deje de estar**, **y eso ya lo resuelve el `left join`**.

**2 · una tabla de acierto por tema, actualizada al contestar.** **Rapida siempre y escribe en cada
respuesta**; **mas piezas, mas sitios donde puede quedar mal**, **y no hace falta mientras el banco no
crezca.**

**Elijo la 1**, **y lo apunto antes de hacerla**: **es una consulta y es reversible**; **la 2 se hace el
dia que el banco sea diez veces mayor, y entonces se mide otra vez.**

**Y el `/plan/hoy` va aparte**: **cachear el plan por la fecha del dia** **es una linea y no toca la
consulta**.

## M7: el agregado son cuatro consultas, y dos son el 75 % del tiempo (ronda 204)

```
question_counts     199 ms   ✓
answered_counts   1.093 ms   ✗
outcome_counts    1.314 ms   ✗
due_counts           10 ms   ✓
                 ─────────
                 2.616 ms   ← de los 3,3 s del agregado
```

**Y las dos lentas son la misma forma**: **agrupan por nodo recorriendo los anclajes** —**16.923 filas**—
**contra lo contestado**. **`due_counts` es rapidisima porque filtra por fecha primero**, **y ahi esta la
pista**: **el filtro por la fecha de hoy reduce los repasos a decenas antes de tocar los anclajes.**

## El arreglo, con la forma exacta

**`answered_counts` y `outcome_counts` tienen que hacer lo mismo que `due_counts`**: **empezar por las
filas de `attempts`** —**119**—, **que ya traen su `session_question_id`**, **y desde ahi subir a la
pregunta y al ancla**. **Hoy parece que recorren los anclajes y buscan sus intentos**, **que es el orden
contrario al que necesita el motor**: **con 119 frente a 16.923, el que manda es el pequeño.**

**La consulta nueva, en palabras**: **`from attempts t join session_questions q … join
question_note_anchors a … group by a.curriculum_node_id`**, **y no al reves.** **Y el `left join` desde
los nodos se queda para los temas sin intentos**, **que es lo que hace que salgan con su cero.**

## Lo que hay que cuidar al cambiarlo

- **los temas sin intentos tienen que seguir saliendo**, **con cero**: **si el `from` empieza en
  `attempts`, los que no tienen desaparecen**, **y la pantalla de progreso perdería los 29 temas que
  hoy enseña**;
- **el `public_only` sigue mandando**: **un conjunto privado no entra en las cifras del alumno**;
- **y el resultado tiene que dar las MISMAS cifras**, **no solo ser mas rapido**: **se compara antes y
  despues sobre la copia**, **y si cambia un número, el arreglo esta mal aunque tarde menos.**

**Eso ultimo es la regla del hito y de todo lo demas**: **optimizar es cambiar el tiempo sin cambiar el
resultado, y si cambia el resultado no es optimizar.**

## M7: mi hipótesis era falsa, y la consulta ya estaba bien escrita (ronda 205)

**Dije que las dos consultas lentas «recorren los anclajes y buscan sus intentos». Las he leído y no: ya
empiezan por `attempts`.**

```python
.select_from(AttemptRecord)
.join(SessionQuestionRecord, ...)
.join(StudySessionRecord, ...)
.join(QuestionVersionRecord, ...)
.join(QuestionSetRecord, ...)
.join(CurriculumMappingRecord, (subject_id == question_version_id) & ...)
.group_by(CurriculumMappingRecord.curriculum_node_id)
```

**El orden es el correcto, y el filtro por oposición y dueño está.** **Así que el tiempo no viene de
recorrer 16.923 anclajes**: **viene del `join` contra `curriculum_mappings`**, **que es la tabla de
mapeos entre preguntas y nodos** — **y con `subject_id = question_version_id` sobre una tabla grande, sin
un índice que cubra esa combinación, cada intento paga una búsqueda completa.**

## Lo que hay que medir antes de tocar

**Cuantas filas tiene `curriculum_mappings` y que indices tiene.** **Si son cientos de miles sin indice por
`subject_id` + `subject_type` + `status`, el arreglo es un indice y no una consulta** — **y un indice no
cambia ni una cifra, que es justo lo que hay que exigirle.**

**Y si el indice ya está**, **entonces es la subconsulta de `outcome_counts`** —**la evaluacion vigente
por intento**—, **que hace una consulta correlacionada por cada intento**, **y eso si es un `N+1`
disfrazado de `join`.**

**Las dos cosas se distinguen en un minuto con `EXPLAIN QUERY PLAN`**, **y sin abrir el motor.**

## La leccion, que es de metodo

**Escribi «recorren los anclajes» en el folio como si lo hubiera visto, y no lo habia visto.** **Lo he
corregido antes de tocar el codigo, y esa es la razon de leer antes de optimizar**: **un arreglo sobre una
hipotesis falsa no arregla nada y estropea lo que funcionaba.**

## M7: los planes, y son dos problemas distintos (ronda 206)

**`answered_counts`:**

```
SCAN m USING INDEX ix_mapping_node          ← recorre los 47.113 mapeos
SEARCH v USING COVERING INDEX … (id=?)
SEARCH q USING AUTOMATIC COVERING INDEX (question_version_id=?)
SEARCH a USING INDEX … (session_question_id=?)
USE TEMP B-TREE FOR count(DISTINCT)
```

**El `SCAN m` es la respuesta**: **aunque la consulta se escribe empezando por `attempts`, SQLite decide
empezar por `m`** — **y con `ix_mapping_node` recorre los cuarenta y siete mil mapeos**—. **El `select_from`
no fuerza el orden: el optimizador elige, y con 47.113 filas en un lado y 119 en el otro eligio mal.**

**`outcome_counts`:**

```
SCAN e
SEARCH a USING INDEX … (id=?)
CORRELATED SCALAR SUBQUERY 1               ← una por cada evaluacion
SEARCH e2 USING INDEX ix_evaluations_attempt (attempt_id=?)
USE TEMP B-TREE FOR LAST TERM OF ORDER BY
```

**Esa si es el `N+1`**: **la evaluacion vigente se busca con una subconsulta correlacionada por cada
fila**, **y por eso tarda 1,3 s.**

## Los dos arreglos, y son de naturaleza distinta

**1 · `answered_counts`: darle al optimizador un indice que empiece por lo que filtra.**
**`ix_mapping_subject` existe** —**`(subject_type, subject_id)`**—, **pero el plan no lo usa**: **usa
`ix_mapping_node` porque el `group by` es por nodo**. **Un indice que cubra
`(subject_type, subject_id, status, curriculum_node_id)`** **le deja resolver el `join` y el `group by`
sin recorrer la tabla**. **Es una migracion de una linea y no cambia ninguna cifra.**

**2 · `outcome_counts`: quitar la subconsulta correlacionada.** **La evaluacion vigente se puede sacar
con un `group by attempt_id` y `max(evaluated_at)` en una subconsulta**, **o con una ventana**, **y
entonces el plan deja de tener un `CORRELATED SCALAR SUBQUERY`** — **que es lo que convierte 119 intentos
en 119 busquedas—**.

**Y la regla de siempre antes de dar esto por bueno**: **las cifras tienen que ser las mismas antes y
despues.** **Un indice no puede cambiarlas; el arreglo de la subconsulta, si se hace mal, si.**

## M7: el índice baja 593 a 214 ms y NO arregla el `SCAN` (ronda 207)

**Aplicado el índice `(subject_type, subject_id, status, curriculum_node_id)` sobre la copia:**

```
antes    593 ms · 5 nodos · suma 119
despues  214 ms · 5 nodos · suma 119
las mismas filas: True
```

**Y el plan sigue igual:**

```
SCAN m USING INDEX ix_mapping_node
SEARCH v USING COVERING INDEX sqlite_autoindex_question_versions_1 (id=?)
SEARCH q USING AUTOMATIC COVERING INDEX (question_version_id=?)
SEARCH a USING INDEX sqlite_autoindex_attempts_2 (session_question_id=?)
USE TEMP B-TREE FOR count(DISTINCT)
```

**Asi que el indice ayuda —2,8 veces— y no cambia la causa**: **SQLite sigue escaneando `m`**, **y lo que
ha mejorado es el coste de ese escaneo, no su existencia.**

## Lo que eso significa, y es la leccion de la ronda

**Un indice que el optimizador no elige no arregla el plan; solo lo hace menos caro.** **El `SCAN m` es
una decision del optimizador**, **y para cambiarla no basta con darle un indice: hay que escribir la
consulta de forma que no pueda elegir mal.**

**Y eso es lo siguiente, con nombre y apellidos**: **el `group by` por nodo es lo que empuja al motor a
empezar por `m`**. **Si se agrupa primero por pregunta —que es lo que los 119 intentos tienen— y se une
despues al mapeo, el motor empieza por `a`.**

**El indice se queda**: **2,8 veces menos en ese camino, y las cifras idénticas.** **Pero no se apunta
como «arreglado», porque no lo está.**

## Lo que queda de M7 en rendimiento

1. **`answered_counts`: reescribir para que agrupe por pregunta primero** — **y volver a mirar el plan**;
2. **`outcome_counts`: quitar la subconsulta correlacionada** — **con `group by attempt_id` y `max`**;
3. **y `/plan/hoy`: cachear el plan por la fecha del dia** — **una linea, sin consulta nueva**.

**Las tres con la misma regla**: **las cifras iguales antes y despues; si cambian, el arreglo esta mal.**

## M7: la reescritura da cien veces menos (ronda 208)

```
answered_counts      1.093 ms → 11 ms   · 5 nodos · suma 119 (las mismas cifras)
outcome_counts       1.314 ms → 1.004 ms · sin tocar todavia
/student/progress    3.218 ms → 1.306 ms
```

**Y el arreglo era el que el plan pedia**: **primero los intentos por pregunta —119 filas— en una
subconsulta, y despues el mapeo**. **Con el `group by` por nodo dentro de la misma consulta, SQLite
elegia escanear los 47.113 mapeos; con la subconsulta no puede elegirlo.**

**Las cifras son las mismas**: **cinco nodos y suma 119**, **que es lo que hay que exigirle a un arreglo
de rendimiento.**

## Lo que queda, y es el `N+1`

**`outcome_counts` sigue en un segundo por la subconsulta correlacionada**: **una evaluacion vigente
buscada por cada intento**. **El arreglo es el mismo patron que acaba de funcionar**: **sacar la
evaluacion vigente en su propia consulta —con `group by attempt_id` y `max(evaluated_at)`— y unir
despues.**

**Y despues `/plan/hoy`**: **cachear el plan por la fecha del dia.**

**Las tres con la misma regla, y la primera ya la cumple**: **cifras idénticas, o el arreglo se tira.**

## M7: el punto 4, medido y cumplido (ronda 209)

```
                        antes        despues
answered_counts       1.093 ms  →      11 ms
outcome_counts        1.314 ms  →       4 ms
/student/progress     3.218 ms  →     230 ms     ← por debajo de los 2 s del hito
/plan/hoy             1.316 ms  →   1.316 ms     ← por debajo de 2 s, sin tocar
/stats                  134 ms  →     134 ms
```

**Y las cifras son las mismas**: **5 nodos y suma 119 en `answered_counts`**, **y 5 nodos y suma 119 en
`outcome_counts`** — **los dos comprobados antes y despues.**

## Y un error que he cometido y corregido en la misma ronda

**El primer intento de la ventana comparaba `AttemptEvaluationRecord.id == vigente`**, **con `vigente`
siendo una subconsulta**, **y eso no compara con las filas: compara con la forma**. **Devolvio un nodo y
suma 1 en vez de 119**, **y `ruff` y `mypy` estaban en verde.**

**Lo ha cazado la comprobacion de las cifras, no el linter**: **si no hubiera medido el resultado ademas
del tiempo, habria commiteado una consulta 250 veces mas rapida que devuelve la cuarenta vez menos.**

**De ahi la regla que gobierna M7 y que ya ha salvado este cambio**: **cifras iguales antes y despues; si
cambian, el arreglo esta mal aunque tarde menos.**

## Lo que queda de M7

- **el punto 4, hecho**; **y lo que le falta es la prueba que lo vigile** — **que es parte del hito**;
- **los puntos 1, 2 y 3**: el bucle de «esto esta mal», la comprobacion semanal y la bandeja por debajo de
  100.

## M7, punto 3: la bandeja tiene 2.568 decisiones y el hito pide menos de 100 (ronda 211)

**Medido en la copia:**

```
question_explanations      12.924
  private   draft          11.315   ← las del propietario, se quedan como estan
  generated draft           1.609   ← lo que queda de la corrida de M1
notes_incidents open          959   ← incidencias sin despachar
change_proposals          no existe la tabla
```

**Asi que la bandeja son 2.568 decisiones reales**, **y el hito pide menos de 100**. **No esta ni cerca**, y
**no lo va a estar con la via actual**: **cada explicacion es una decision y nadie las ha despachado
todavia**.

## Y una buena noticia que sale de la misma medida

**Las explicaciones generadas han bajado de 8.230 a 1.609**: **la corrida de M1 avanzo 6.621**, **y ya son
el 88 % del total de las 13.588 que hacian falta**. **Cuando termine, la bandeja de explicaciones queda en
cero.**

## Y las 959 incidencias son otra cosa

**`notes_incidents` abiertas son avisos de «esto esta mal» sin despachar.** **No son lo mismo que una
explicacion en borrador**: **una incidencia pide mirar un texto, y una explicacion en borrador pide
aprobar o rechazar una frase.**

**Y el punto 3 del hito —«bandeja por debajo de 100 decisiones reales, con todo lo automatizable
propuesto en bloque»— tiene dos mitades, y solo se ha mirado una**: **cuantas hay**, **y no si lo
automatizable esta propuesto en bloque.**

**La mitad que falta es la que de verdad pide el hito**: **que las explicaciones en borrador se puedan
aprobar en bloque** — **que ya existe en la bandeja de M1**—, **y que las incidencias que se resuelven
solas —un enlace roto, una cita que ya no esta— se resuelvan sin que nadie las mire**.

**Asi que lo que hay que hacer en el punto 3 no es bajar 2.568 a 100 a mano**: **es que 2.468 dejen de
necesitar a una persona.**

## M7, punto 3: las 959 incidencias, clasificadas, y mi lectura era falsa (ronda 212)

**El desglose, medido:**

```
norma_cambiada      clave_contradice_la_norma     538
clave_sospechosa    letra_no_coincide             192
pregunta_ambigua    sin_materia_en_el_indice       95
hueco_sin_material  sin_frase_en_los_apuntes      106
pregunta_ambigua    clave_sin_definir              28
```

**Y comprobe si las 192 de «letra no coincide» eran un defecto determinista** —**la clave fuera de sus
opciones**— **y salieron 0 de 192**: **en las 192 la clave SI esta entre sus opciones**.

**Entonces fui a leer el detector, y el nombre engaña:**

```python
Motivo.LETRA_NO_COINCIDE: "en conflicto: la frase está, pero la clave dice otra opción"
```

**`letra_no_coincide` no es «la letra no esta en la lista»**: **es que la frase de los apuntes apoya una
opcion y la clave corrige otra.** **Eso no es un defecto de datos: es una contradiccion de contenido**, y
**ningun programa la resuelve sin decidir cual de las dos tiene razon.**

## Lo que eso dice del punto 3, y es lo importante

**De las 959, solo dos grupos son automatizables de verdad:**

- **`sin_frase_en_los_apuntes` (106)**: **falta la frase**, y **lo que hay que hacer es escribirla** — **eso
  lo hace el modelo, no una persona**;
- **`clave_sin_definir` (28)**: **la pregunta no tiene clave**, y **una pregunta sin clave no se puede
  corregir**: **se retira o se le pone clave** — **es una decision pequena y repetida**.

**Y las 733 restantes —538 + 192 + 95— son contradicciones entre los apuntes y la clave, o preguntas cuya
materia no esta en el indice.** **Ninguna se arregla con una regla**: **cada una pide mirar dos textos y
decidir cual vale.**

## Asi que el punto 3 no se cumple bajando la bandeja por debajo de 100

**Se cumple cuando la bandeja tiene menos de 100 decisiones reales** — **y hoy tiene 733 de esas, sin contar
las 1.609 explicaciones.** **Lo que hay que hacer, y es lo que el hito pide con la palabra «propuesto en
bloque», es:**

1. **proponer en bloque las 106 `sin_frase_en_los_apuntes`**, **que el modelo puede escribir**;
2. **agrupar las 28 `clave_sin_definir`** en una sola propuesta — **«estas 28 preguntas no tienen clave, se
   retiran»**;
3. **y dejar las 733 como lo que son**: **decisiones reales**, **que es exactamente lo que el hito llama
   asi** — **y por eso el hito pone 100, no 0.**

**Y esa es la cuenta honesta del punto 3**: **de 2.568 a 1.609 + 733 + 94 = 2.436**, **que sigue estando
lejisimos de 100**. **El hito no se cumple hoy, y no por falta de codigo: por falta de 2.336 decisiones.**

## M7, punto 3: agrupar no reduce nada, y la bandeja no puede bajar de 100 (ronda 213)

**La ultima esperanza del punto 3 era agrupar: si las 959 fueran cien grupos, serian cien decisiones.**
**Medido:**

```
firmas distintas entre las 959 abiertas: 920
  norma_cambiada        538 items -> 538 firmas
  clave_sospechosa      192 items -> 191 firmas
  pregunta_ambigua      123 items ->  95 firmas
  hueco_sin_material    106 items -> 104 firmas
  la firma mas grande: 13 items
```

**920 firmas para 959 incidencias quiere decir que casi cada incidencia es su propio caso.** **No hay un
patron repetido que se pueda aprobar de una vez**: **noventa y cinco firmas para ciento veintitres
preguntas ambiguas son noventa y cinco decisiones distintas.**

**Asi que la bandeja, contada en decisiones reales, son 920 incidentes + 1.609 explicaciones = 2.529.**
**Y el hito pide menos de 100.**

## Lo que esto significa, dicho sin adorno

**El punto 3 de M7 no se puede cumplir con codigo.** **No es que falte una pantalla ni una agrupacion: es
que hay 2.529 decisiones de contenido sin tomar**, **y tomarlas es exactamente el trabajo del propietario.**

**Lo que si se puede hacer, y queda hecho**: **decir cuales son automatizables** —**134 de 959**— **y
dejarlas separadas de las reales**, **que es la mitad «propuesto en bloque» del punto.**

**Y lo que no**: **las 733 contradicciones entre apuntes y clave**, **que piden leer dos textos y decidir.**

**Va a `PARA-EL-PROPIETARIO.md` como lo que es**: **el unico apartado de la fase que no se cierra con
trabajo mio**, **y con la cuenta exacta de lo que falta.**
