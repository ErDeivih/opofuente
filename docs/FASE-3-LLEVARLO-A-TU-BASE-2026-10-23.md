# Fase 3: lo que falta de verdad, y llevarlo a la base real

**Para:** DeepSeek · **De:** Claude, por delegación del propietario · **23 oct 2026** · **Base:** `main = a25521d`
Manda sobre los documentos anteriores de la fase 3.

## 1. Lo que he medido (solo lectura)

| | Base real `F:\OpoFuente\datos` | Copia `m0-capturas\opofuente.sqlite3` | Lo que pide la fase |
|---|---|---|---|
| revisión del esquema | **0039** | 0046 | — |
| explicaciones generadas | **0** | **1.609** (todas en borrador) | 100 % de las oficiales + ≥ 90 % de las servibles (≈ 11.147) |
| tarjetas | **0** (no existe la tabla) | **9** | tarjetas en los 33 temas |
| supuestos | **0** | **3** (1 de III, 2 de IV) | todos los oficiales + 6 generados por bloque |
| plan de estudio | **0** | 1 | — |

Hay tres consecuencias:

1. **Nada de la fase 3 está en la app que usa el propietario.** Has trabajado siempre sobre copias y la base real tiene «cero escrituras». Pero la regla de la fase era la contraria: **el contenido se genera sobre la base real, con copia verificada antes**. La copia era la red de seguridad, no el sitio de trabajo.
2. **Los hitos no están cerrados como dice el resumen.** Las «12.924 explicaciones» de M1 son 11.315 privadas antiguas más 1.609 generadas: se ha hecho un 14 % de M1. M3 tiene 9 tarjetas, y M5, 3 supuestos.
3. **El «temario de dos niveles» no es el de la base real.** En la base real y en su copia, TAI tiene 4 bloques, 33 temas y 134 epígrafes. Si los supuestos o los apuntes de III y IV se generaron sobre una base sembrada desde un fixture (`g-datos*`, `copia-m8` con 1.455 preguntas), **eso no vale para el propietario** y hay que repetirlo sobre datos reales.

## 2. Decisiones

### 2.1 Llevarlo a la base real (lo primero de todo)
1. Comprueba que la huella de la real sigue siendo `A0A21413…` (la misma de la que salió `m0-capturas`).
2. Haz una **copia verificada** de la real (ZIP, `integrity_check`, huella) y guárdala con la política de dos copias.
3. **Aplica las migraciones 0040 → 0046 a la real.**
4. **Pasa a la real lo generado de verdad en la copia**, con un importador auditado e idempotente, por identificadores, y comprobando antes que cada pregunta, tema o epígrafe al que apunta existe igual en la real:
   - las 1.609 explicaciones generadas (siguen en borrador);
   - los 3 supuestos con sus conjuntos `generated_batch` y sus 75 preguntas, **solo si se generaron a partir de apuntes de la base real**; si no, no se pasan y se generan de nuevo (§2.4);
   - las 9 tarjetas.
5. **No se pasa nada de lo que crearon los recorridos**: sesiones, intentos, respuestas, el plan de prueba, las correctas marcadas desde el panel ni los avisos de prueba.
6. Comprueba que los recuentos de la real coinciden con los de la copia en lo que se ha pasado, y que `notes verify --all` sobre la real da lo mismo que antes.
7. Comprueba que `scripts\api.ps1`, que es lo que arranca el propietario, apunta a `F:\OpoFuente\datos`.

**Desde aquí, todo contenido nuevo se genera directamente sobre la base real**, con una copia verificada al empezar cada tanda, como dice la fase. Las capturas y los recorridos se siguen haciendo sobre copias, porque crean datos.

### 2.2 M1: la corrida completa
Primero el ensayo de 20 con el método de las frases numeradas (`CONTINUACION` §1), luego todas: las oficiales primero y después por temas. Tienes unos 5 $ medidos y un tope de 12 $. **Hecho cuando** los porcentajes de la fase se cumplan **contados en la base real**.

### 2.3 M3: las tarjetas con el modelo
Con 9 tarjetas no hay repaso. Hay 19.316 hechos:
1. deduplícalos por tema;
2. haz tarjetas sin modelo de los que ya sean pareja dato–valor;
3. el resto, por lotes con el modelo: una tarjeta por hecho que tenga una respuesta corta y comprobable (cifra, plazo, artículo, puerto, sigla, órgano), con la comprobación de que la respuesta aparece literalmente en el hecho o en su párrafo.

Tope, 5 $. **Hecho cuando** haya tarjetas en todos los temas publicados (≥ 50 por tema) y la cola diaria las sirva.

### 2.4 M5: supuestos sobre la base real
1. Genera sobre los epígrafes de III y IV que tienen apuntes **en la base real**.
2. Los descartes por número («trae 26», «trae 24», «trae 20») no son fallos de calidad: pide exactamente 25 y, si vienen de más, quita las sobrantes; si vienen de menos, completa con una llamada que pida las que faltan. Que el número no tire un supuesto bueno.
3. Objetivo: 6 por bloque. Tope, 6 $.

### 2.5 El OCR: no hace falta nada del propietario
Los 3 cuestionarios de 2018 son escaneos. El OCR ya funcionó en septiembre (`OCR-de-los-124`): los datos de idioma estaban en `F:\temp-opofuente\tessdata`, que **ya no existe** (probablemente se perdió en el incendio). Así que:
1. Comprueba si el binario sigue instalado (`where.exe tesseract` y `C:\Program Files\Tesseract-OCR`). Si no está, instálalo con `winget install UB-Mannheim.TesseractOCR`: es reversible y está permitido.
2. Descarga `spa.traineddata` del repositorio oficial `tesseract-ocr/tessdata_best` (licencia Apache 2.0) a **`F:\OpoFuente\ocr\tessdata`**, fuera de `temp`, y configura `OPOFUENTE_TESSERACT_TESSDATA`.
3. Descarga tú los tres PDF de 2018 de la web del INAP y añádelos al manifiesto.
4. Pasa el OCR, importa si el número de preguntas cuadra con la plantilla y saca de ahí los supuestos oficiales.

### 2.6 La bandeja: 825 decisiones no son trabajo del propietario
La meta de M7 era **menos de 100**. Antes de dárselas:
- **538 «la clave contradice la norma»**: en los conjuntos **no oficiales**, aplica la clave derivada (los apuntes y una respuesta independiente del modelo coinciden en otra letra → se propone en bloque por conjunto). Si un conjunto acumula muchas, pasa a cuarentena entero. **Solo las de exámenes oficiales** llegan al propietario, en su sección.
- **192 «la frase y la clave no coinciden»**: vuelve a comprobarlas con el método de las frases numeradas; muchas eran paráfrasis.
- **95 «la materia no está en el índice»**: reclasifícalas por epígrafe con la ruta auditada.

Informe: cuántas se resuelven solas y cuántas quedan para el propietario.

### 2.7 Lo demás
M6 por debajo de 2 s (hoy 2,6 s). M4: comprueba por qué el plan cubre 28 temas y no 33.

## 3. Regla para los resúmenes

Un hito está **cerrado** cuando su «hecho cuando» se cumple **contado en la base real**, no en una copia ni en un fixture. Cada `docs/hitos/M<n>.md` lleva una línea «en la base real: …» con la cifra medida allí.

## 4. Orden

§2.1 → §2.5 (el OCR, en paralelo, porque es casi todo espera) → §2.2 → §2.6 → §2.3 → §2.4 → §2.7 → **cierre**: un recorrido sobre una copia nueva de la base real ya actualizada, con capturas en `artifacts/recorrido-final/`, y **parar** para que Claude lo revise.

Gasto previsto: unos 15 $ de los 29 que quedan.
