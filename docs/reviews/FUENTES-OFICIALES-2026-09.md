# Fuentes oficiales para el temario y los exámenes de TAI (septiembre 2026)

Este documento responde a una pregunta concreta: **qué material oficial, público y gratuito se puede
traer por internet para mejorar los apuntes y el banco de preguntas**, y con qué coste. Lo que sigue
está **comprobado con peticiones HTTP reales**, no supuesto a partir de una búsqueda.

## 1. Lo que se ha comprobado que funciona

### 1.1. Las leyes, enteras y al día, por la API de datos abiertos del BOE

`https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/<BOE-A-…>`

Devuelve el **texto consolidado completo** de la norma en XML. Dos detalles que costaron un intento cada
uno y conviene no olvidar: **exige la cabecera `Accept: application/xml`** (sin ella responde 400) y el
identificador es el `BOE-A-…` del documento original, no el de la última modificación.

Probado con las **17 normas que el bloque I pregunta literalmente**: **17 de 17 descargan**. Ejemplos de
tamaño: Ley 9/2017 (contratos), 2,1 MB de XML; Ley 40/2015, 824 KB; Constitución, 208 KB.

Hay una segunda vía equivalente: `https://www.boe.es/buscar/xml.php?id=<BOE-A-…>`.

**Lo descargado** (en `F:\OpoFuente\TAI\internet\boe\leyes-consolidadas\`), con su **XML original** —que
es la fuente— y un **`.txt` derivado** que es lo que la bandeja sabe leer: el XML no es un formato que el
extractor reconozca, así que sin esa conversión el material entraría como «conservado sin extractor».

La conversión descarta a propósito el bloque `<analisis>` del XML, que contiene las relaciones con otras
normas (derogaciones, modificaciones): eso **no es la norma**, y mezclado haría que un apunte citara una
derogación como si fuera un artículo. El texto resultante conserva títulos, bloques y artículos (la Ley
39/2015 sale con 306 apartados «Artículo N» reconocibles).

### 1.2. Los exámenes oficiales de TAI con sus plantillas de respuestas, en la sede del INAP

La sede del INAP (`sede.inap.gob.es`) publica, **por convocatoria**, los cuestionarios y las plantillas
de respuestas de sus procesos. La página del cuerpo de TAI enlaza **diez convocatorias**:

- Ingreso libre: 2018 · 2019 · 2020-2021-2022 · 2023-2024 · **2025**
- Promoción interna: 2018 · 2019 · 2020-2021-2022 · 2021-2024 · **2025**

Recorridas las diez: **151 documentos** enlazados, de los que **22 son cuestionario o plantilla** (el
resto es papeleo del proceso: admitidos, exclusiones, sedes, cronograma). Se han descargado los de la
convocatoria 2025 —**12 documentos, 0 fallos**— en `F:\OpoFuente\TAI\internet\inap\examenes-oficiales\`:

| Documento | Qué es |
|---|---|
| `Cuestionario TAI-L-ModeloA.pdf` / `-ModeloB.pdf` | Examen de **ingreso libre 2025**, los dos modelos (312 KB cada uno) |
| `Plantilla respuestas TAI-L-A_act.pdf` / `-B_act.pdf` | **Plantilla de respuestas actualizada** (tras impugnaciones) del mismo examen |
| `Cuestionario TAI-P-ModeloA.pdf` / `-ModeloB.pdf` | Examen de **promoción interna 2025** |
| `Plantilla respuestas TAI-P-ModeloA.pdf` / `-B.pdf` | Plantilla provisional |
| `Plantilla respuestas Def TAI-P-A.pdf` / `-B.pdf` | **Plantilla definitiva** |
| `cuestionario_TAI-L_ext…pdf` + `Plantilla_respuestas_prov_TAI-L_ext…pdf` | Convocatoria extraordinaria |
| `tai-pi-*.pdf` (3, aparte) | Cuestionario OEP19 y plantillas de promoción interna |

**Tres cosas que cambian el trabajo, medidas sobre los ficheros descargados:**

1. **Traen texto nativo, no son escaneos.** El cuestionario de promoción interna OEP19 son **32.249
   caracteres** de texto extraíble; el de ingreso libre 2025, 63.314. No hace falta OCR.
2. **Las plantillas se leen enteras y sin ambigüedad.** La de ingreso libre 2025 da las respuestas de las
   **80 preguntas de la primera parte**, las **5 de reserva**, los **supuestos I y II (20 preguntas cada
   uno + 5 de reserva)**: 135 respuestas oficiales en una sola página de texto, en minúscula y sin
   casillas que adivinar. En la de promoción interna OEP19 aparece incluso la marca **`ANULADA`** en la
   pregunta anulada, que es exactamente el dato que hoy el banco no sabe.
3. **El examen trae sus propias reglas**: número de preguntas, reserva, **penalización de 1/4 por error**,
   noventa minutos y las dos partes. Está escrito en el enunciado oficial, así que se puede citar.

Además, el cuestionario de 2025 declara **80 preguntas** en la primera parte, no las 50 del proceso de
2019: el examen ha cambiado de forma entre convocatorias, y eso también es material de estudio.

### 1.3. Lo descargado, con su hash

Todo lo descargado queda anotado en `F:\OpoFuente\CATALOGO\fuentes-oficiales.json` con su **URL**, su
**sha256**, su tamaño y su fecha. El guion `traer_fuentes_oficiales.py` es idempotente: si el fichero ya
está con el mismo hash, no lo vuelve a bajar, y si el hash cambia, se ve. Es la misma idea que ya usa el
proyecto con las fuentes de los perfiles (`scripts/fetch-sources.ps1`, 18 fuentes verificadas).

## 2. Lo que se puede hacer con esto, por orden de valor

1. **Importar el examen de tu convocatoria con sus respuestas oficiales.** Las preguntas y las letras
   están en texto; lo que falta es el extractor (numerar enunciado, opciones y letra) y su paso por el
   banco. Es el material de más valor que existe para esta oposición: preguntas del examen real, con la
   respuesta que dio el tribunal.
2. **Contrastar lo que ya tenemos.** El banco tiene **2.896 preguntas de examen**, de 48 ficheros, que
   entraron por una recopilación de terceros (el fondo de baquedano). Tener las plantillas **oficiales**
   permite medir cuántas de esas respuestas coinciden con la oficial: un número que hoy no se conoce y
   que dice de golpe si el material de terceros es fiable o no.
3. **Añadir las normas al material de estudio.** Los `.txt` de las 17 leyes son la fuente para los temas
   del bloque I, donde el examen pregunta el artículo literal. Ya están en la bandeja: entran al
   inventariar y clasificar como cualquier otro documento.
4. **Bajar las nueve convocatorias restantes** (el índice ya está levantado en
   `CATALOGO\inap-tai-documentos.json`): son más exámenes oficiales con sus plantillas, y el coste es una
   descarga cada uno.

## 3. Lo que NO hace falta para nada de esto

- **Un navegador.** Todo lo anterior son peticiones HTTP a URLs estables: ni Playwright ni un modelo que
  decida qué botón pulsar.
- **Un modelo de decisión tipo Jev.** Ver el análisis en la respuesta a la pregunta del vídeo: el modelo
  es real, pero es de nube, propietario, devuelve un número sin justificación auditable y no aporta nada
  al caso de descargar PDF y XML estáticos.
- **OCR.** Los exámenes de 2025 y 2019 traen texto. El OCR se reserva para los escaneos que ya se
  procesaron aparte (ver `OCR-de-los-124-2026-09.md`).

## 4. Riesgos y límites, dichos

- **Cobertura desigual por convocatoria**: la 2025 y la de 2019 sí publican cuestionario y plantilla; en
  alguna otra el enlace lleva solo al BOE de la convocatoria y no al examen. Cada convocatoria se comprueba
  al bajarla, no se supone.
- **Los enlaces cambian**: son ficheros con nombre variable en una sede electrónica. Por eso el manifiesto
  guarda la URL y el hash: si un enlace se rompe, se sabe cuál y qué tenía.
- **Derechos**: son documentos públicos de una administración para preparar una oposición. Se guardan como
  copia para uso personal y estudio, con su procedencia, sin redistribuir.
