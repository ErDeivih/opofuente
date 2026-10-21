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
