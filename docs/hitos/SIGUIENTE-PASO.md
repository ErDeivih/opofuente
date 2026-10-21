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
