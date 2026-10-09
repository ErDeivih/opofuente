# Guardia Civil: una sola generación de apuntes, el mapa bien medido y el Código 599 dentro entero (30-09-2026)

Tres cosas de Guardia Civil, las tres medidas antes de escribirlas. La tercera es la que más cambia las cosas:
**el texto de la normativa estaba dentro de la aplicación pero no se podía leer**.

## 1. Tres generaciones del mismo apunte, las tres aceptadas y mapeadas

Los apuntes de Guardia Civil se rehicieron tres veces (el primero leyendo el `.md` sólo por sus encabezados, el
segundo con los párrafos bien cortados, el tercero con el texto definitivo). Cada rehacer creó una **versión
nueva del mismo documento**, y las tres quedaron aceptadas y mapeadas. Medido en el tema 1:

| versión | tramos | qué tenía |
| --- | --- | --- |
| 12:54 | **17** | sólo los títulos: el 10 % del texto |
| 13:00 | 85 | los párrafos ya cortados |
| 13:05 | **162** | el texto definitivo |

El tema contaba las tres, así que enseñaba también la del 10 %.

Esto **no** es el problema de TAI: aquí las versiones son del **mismo documento**, así que `mark-supersedes`
funciona (la aplicación sólo lo rechaza con 409 entre documentos distintos). Con
`dejar_una_sola_version_vigente.py`: se queda la última, se le quitan los mapeos a las anteriores y se marca que
la última las sustituye.

Resultado sobre **40 documentos** con más de una versión aceptada (25 apuntes de Guardia Civil, 9 fuentes de
internet y 6 exámenes): **71 versiones retiradas, 59 mapeos quitados, 0 fallos**. Los apuntes de Guardia Civil
quedan en **25 versiones vigentes y 50 sustituidas**, una por tema.

## 2. El mapa de Guardia Civil medía otra cosa

`mapa_de_material_de_gc.py` contaba **sólo** los mapeos de tipo `document_version`, y en Guardia Civil el
material de las normas está mapeado contra **epígrafes** (7.421 mapeos) y bloques (2.085). Los temas salían con
36 a 264 fragmentos cuando su propio dossier devuelve **686 fuentes y 40.985 pasajes**. Arreglado, con las dos
lecciones que ya había aprendido en TAI:

- se cuentan las **tres vías** del mapeo polimórfico (`document_version`, `representation` y `artifact`), cada
  versión **una vez por nodo**;
- el material de un tema es el suyo **más el de sus descendientes** (`10` incluye `10.1`, `10.1.1`…), y la
  agregación se hace por **unión de versiones, no sumando las partes**: un documento mapeado al tema *y* a uno de
  sus epígrafes se contaba dos veces (el tema 10 pasaba de 71.045 a **53.362** fragmentos al corregirlo).

Ahora el mapa dice: **25 de 25 temas con material**, **288.087 fragmentos** agregados, 241 preguntas y 240 con
clave. El más flojo es Deontología Profesional (58 fragmentos) y el más lleno, Derecho Administrativo (53.362).

## 3. El Código 599 estaba dentro… con el 2 % de su texto

De los 125 epígrafes del temario de Guardia Civil, **55 no tenían ni un fragmento**. La explicación no era que
faltara el material: era que **no se podía leer**.

Medido: el PDF del Código electrónico 599 (la recopilación del BOE con la normativa de la oposición) son
**17,9 MB**; la aplicación le extrajo **2.000.000 de caracteres** y guardó **100 tramos con 118.084 caracteres en
total**, porque un tramo se guarda recortado a 1.200 caracteres. Es decir: **el 94 % de la normativa no existía
para la aplicación**, y por eso los epígrafes estaban vacíos.

La solución es la receta que ya está medida en esta sesión —partir el texto en bloques de ≤800 caracteres antes
de ingerirlo— más una idea propia de este material: **una norma por documento**, que es como se estudia.
`partir_el_codigo_599.py` parte las 86.017 líneas del texto ya extraído por las marcas de sección del cuerpo
(`§ 29` y el nombre de la norma en la línea siguiente), descarta el índice y los encabezados de página, y
escribe:

| | |
| --- | --- |
| normas convertidas en documento | **48** |
| caracteres | **5.408.807** (frente a los 118.084 que había) |
| ficheros | 50 (3 partes para el Reglamento de Armas, que pasa de 380.000 caracteres) |
| ingeridos | **50 de 50**, cero sin extraer |
| corte de 4.096 bytes | comprobado en los 50: ninguno partido |

Con eso dentro, `cerrar_los_huecos_de_gc.py` cierra huecos atando cada epígrafe a la norma que le toca, con
tres reglas y la medición de cada una:

1. **la cita en el propio epígrafe o en sus antecesores** («13.2.1 TÍTULO Preliminar» hereda la ley del bloque
   «13.2 Ley 5/2014 de Seguridad Privada»): es lo que cierra la mayoría;
2. **la cita en el nombre del documento**, prefiriendo el **texto de la norma** (los ficheros del Código 599) a
   un resumen o a unas preguntas frecuentes sobre ella. Trampa encontrada y arreglada: la aplicación **sanea el
   nombre del fichero** y convierte `31/1995` en `31-1995` al poner el título, así que buscando sólo la forma
   con barra el informe decía que las normas no estaban dentro **cuando sí lo estaban** (de 3 epígrafes a 20 al
   buscar las dos formas);
3. **la frase del epígrafe en el texto**, para los tratados que no tienen forma de ley («Declaración Universal
   de Derechos Humanos»). Dos intentos fallidos y por qué: quitar las palabras de enlace de la frase
   («convenio europeo **para la** protección **de los** derechos») rompe la frase y no casa con nada; y el
   título del epígrafe acaba en punto y el texto de dentro no, así que la frase hay que buscarla sin puntuación.

**Epígrafes vacíos: 55 → 34.** Los 34 que quedan son subdivisiones internas de normas que **ya están mapeadas**
en su bloque o su tema («TÍTULO IV. Disposiciones sobre las cooperaciones reforzadas», «SEGUNDA PARTE. No
discriminación y ciudadanía de la Unión», «FAO.»): el material se alcanza desde el tema, pero la vista del
epígrafe sale vacía porque la aplicación mapea **por documento, no por sección**. Eso es un límite del modelo,
no material que falte.

## 4. Dónde queda todo

| | |
| --- | --- |
| temas de Guardia Civil con material | **25 de 25** (288.087 fragmentos agregados) |
| preguntas de Guardia Civil | **241**, con clave **240** |
| temas sin preguntas | 1 (Lengua Española: su examen no la pregunta, medido) |
| apuntes de Guardia Civil | 25 documentos, **una sola versión vigente** cada uno |
| epígrafes sin material | **34** de 125 (eran 55) |
| base | 4.281 documentos · 4.281 versiones aceptadas · **381.874 fragmentos** · 33.249 mapeos · 0 en cola |

Lo que sigue abierto de Guardia Civil: los 34 epígrafes del §3 (límite del modelo por documento) y las
plantillas de los exámenes 2021-2025, que son escaneos sin texto fiable (medido antes: OCR con 12 a 80 números
sin leer).
