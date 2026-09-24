# ADR-020 — El OCR se ejecuta cuando está configurado, y se declara siempre

**Fecha:** 24 de septiembre de 2026.
**Estado:** aceptada por el codificador, por delegación del propietario («ratificaciones decide tú»,
23/09/2026), con la instrucción expresa de conectar y probar Tesseract.
**Afecta a:** `04_INGESTION-AND-CLASSIFICATION.md` §5 («OCR solo si está configurado y el usuario lo
inicia/acepta»), `infrastructure/extractors`, `/capabilities`, `docs/OPERACION.md` §8.

## Contexto

La especificación de ingestión dice, para los PDF, dos cosas a la vez:

> - si una página no alcanza calidad, marcar `ocr_candidate`;
> - **OCR solo si está configurado y el usuario lo inicia/acepta**;
> - conservar texto nativo y OCR como representaciones diferentes;
> - no fusionarlos sin trazabilidad.

Las tres últimas se cumplen sin discusión. La segunda es la que admite dos lecturas: «el usuario lo
inicia» puede querer decir *por fichero* (una acción explícita sobre cada entrada pendiente) o *una
vez, al configurar el OCR* (quien instala Tesseract y lo declara en la configuración está aceptando
que se lea lo que no traiga texto).

El propietario pidió el 23/09/2026 «instala tesseract para lo de las imágenes y pruébalo» y, en la
misma sesión, que la aplicación «lea la info y use esa info para nutrir cada tema» a medida que añade
fuentes. Su material real es en buena parte fotografiado o escaneado (apuntes, capturas de temario,
plantillas oficiales), así que la lectura de escaneos no es un extra: es la vía normal de entrada.

## Opciones

1. **OCR por fichero, con acción explícita.** La entrada queda `ocr_pending` y hay que pulsar «Leer
   con OCR» en cada una. Cumple la letra de la especificación. Coste: con 200 apuntes escaneados son
   200 pulsaciones, y cada olvido deja material invisible para el buscador y para el dossier del tema
   sin que nada lo recuerde salvo una lista de pendientes.
2. **OCR automático cuando está configurado.** Configurar el OCR es la aceptación; lo reconocido se
   guarda como representación `ocr` aparte, con su calidad `ocr_unreviewed`, su extractor y su
   versión. Coste: se ejecuta sin preguntar, y hay que asegurarse de que el resultado **se ve**
   (tipo, calidad y aviso) en lugar de pasar por texto del documento como si nada.
3. **Automático con interruptor por lote.** Un ajuste que decide si esta importación OCRiza o no.
   Coste: un ajuste más que explicar y que nadie recuerda haber puesto.

## Decisión

**Opción 2.** El OCR se ejecuta al importar cuando el binario está configurado **y su sonda pasa**
(existe, responde y tiene el idioma pedido). «Configurado» es la aceptación del usuario, y la
aplicación lo dice en tres sitios para que no haya nada implícito:

- **Ajustes → capacidades**: si el OCR está operativo, con la versión del binario, los idiomas y el
  directorio de modelos; si no, con el motivo exacto («no tiene el idioma spa: solo puede leer eng y
  osd»);
- **la representación**: tipo `ocr`, extractor `tesseract_ocr` y calidad `ocr_unreviewed`, que en el
  catálogo de calidades significa «leído por una máquina, sin revisar» y no entra en RAG como texto
  humano;
- **la entrada**: si no se pudo leer, queda `ocr_pending` con su incidencia, distinguiendo «no se ha
  ejecutado» de «se ejecutó y no reconoció nada».

Reglas que acompañan a la decisión, y que son las que la hacen defendible:

- **el texto nativo no se toca**: el OCR es otra representación, con su propia fila, su propio texto y
  sus propios tramos de página; nunca se fusiona ni sustituye (04_INGESTION §5);
- **sin sonda no hay OCR**: tener una ruta escrita en el `.env` no basta, igual que no basta para
  declarar el almacén operativo;
- **solo se OCRiza lo que no trae texto del material**: un PDF con capa de texto no pasa por OCR, y
  los metadatos de una imagen no cuentan como su texto;
- **se puede apagar**: sin `OPOFUENTE_TESSERACT_PATH` la aplicación funciona exactamente como antes de
  esta decisión.

## Consecuencias

- Un escaneo o una foto entran al corpus por la vía normal, sin pasos extra: eso es lo que necesitan
  el buscador y el dossier del tema (ADR-019).
- El coste en tiempo es del orden de segundos por documento escaneado, en el worker, no en la
  petición: un lote con escaneos tarda más y la bandeja lo dice.
- La calidad `ocr_unreviewed` es información, no un adorno: quien compile un tema desde el dossier
  tiene que ver de qué fuentes viene el texto y con qué calidad.
- **No** se importa automáticamente nada que sea una **clave de respuestas**: una tabla con rejilla
  no se lee de forma fiable (medido: 76 de 77 en el mejor caso, una sin leer) y eso es lo que DEBT-020
  mantiene abierto. La prosa sí; una tabla que decide una nota, no sin que alguien la revise.

## Reversión

Volver a la opción 1 no requiere migración: el registro de extractores dejaría de construir el
extractor de OCR cuando la configuración no lo pida, y las representaciones `ocr` ya guardadas se
quedan como están (son texto leído, con su procedencia). Lo que **no** se puede revertir sin perder
información es borrar las representaciones `ocr` de la base: no se hace.
