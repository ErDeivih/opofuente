# Los mazos de Anki: 6.037 test con clave al banco y las tarjetas por tema (30-09-2026)

Los mazos de Anki llevaban desde septiembre en la biblioteca como **material** —una tarjeta por tramo, citables—
pero el banco de preguntas tenía **cero tarjetas**, y el `DEBT-023` explicaba el motivo para las tarjetas de
anverso/reverso: el modelo tiene el tipo `free_text_reference` y **no tiene dónde guardar el reverso**. Eso es
cierto y sigue siéndolo. Lo que no se había mirado es lo otro: **los mazos también traen test con opciones y con
su respuesta**, que son preguntas de las de siempre, con su clave, y esas no tienen ningún problema de modelo.

Esta es la medida de lo que había, lo que se ha hecho con cada cosa y **los dos defectos de la aplicación que han
aparecido por el camino**, con su reproducción.

## 1. Qué había dentro de los mazos (medido)

22 contenedores distintos por contenido (70 ficheros: el mismo mazo copiado en `pack`, en dos descargas de Drive
y en `escritorio`), leídos **con el extractor de la propia aplicación** (`opofuente.infrastructure.extractors.anki`)
para que lo que cuento yo y lo que leyó ella no puedan discrepar:

| forma | tarjetas | qué es |
| --- | --- | --- |
| `test` | **6.200** | pregunta con opciones y respuesta en sus campos |
| `pareja` | **7.665** | anverso/reverso (incluye Cloze de `Text`/`Extra`) |
| `cloze` | **1.497** | texto con hueco `{{c1::…}}` |
| `otra` | 41 | sin anverso ni reverso utilizables (oclusión de imagen, plantillas vacías) |
| **total** | **15.403** | |

De los 6.200 test, **6.037 son distintos** por la huella de la propia aplicación (`question_fingerprint`:
enunciado normalizado y juego de opciones sin orden): 163 son copias dentro de los propios mazos.

### Los cuatro formatos de test que traen los mazos

Cada uno guarda la clave a su manera, y se lee por regla, no por casualidad:

| formato | ejemplo | cómo se lee la clave |
| --- | --- | --- |
| `option_1 (A)…option_8 (H)` + `Ans` | `MCQ Ultimate V2.1` (3.499 tarjetas) | `Ans` es la **letra** |
| `Q_1…Q_5` + `Answers` | `AllInOne (kprim, mc, sc)` (1.580) | `Answers` es una **fila de marcas** (`0 1 0 0`) |
| `Answer1` + `Distractor2…4` | `00 Test 4 Preguntas + Nota` (919) | la correcta es la opción que se llama `Answer` |
| `Opcion_1…4` + `Respuesta` | `Básico-Fran` (205) | `Respuesta` trae **el texto** de la correcta |

Los mazos vienen de `[@trirodol] TAI_web`, `[@Be3402] Todos los mazos`, `[@Danie_e_e] ColecciónAnki.colpkg`,
`[@viclomu] BLOQUE_IV`, `[@xelarro] CE / EBEP / Tema 5` y `COMUNIDADES-MUCHOS_TESTS` (estos últimos, **1.580
preguntas de exámenes oficiales de otras administraciones**, con el examen de origen en su campo `Title`:
Aragón 2016, Cantabria 2011, Euskadi 2012, Extremadura 2014, AGE 2014…).

## 2. El tema: dos señales escritas, ninguna adivinada

Ninguna tarjeta se ha etiquetado a mano. El tema sale de:

1. **el rótulo del mazo**, que es la intención declarada de quien lo hizo (`B3 - 💻::T8 - Lenguajes de
   programación`, `BLOQUE_IV::05. Conceptos de seguridad…`, `B2 - 🖱️::T2 - Periféricos`), aplicado como
   **reglas** (una por mazo o familia de mazos): 8.887 tarjetas;
2. **la etiqueta de la tarjeta** (`redes`, `Java`, `UML`, `RGPD`…) en los dos mazos grandes que no rotulan tema
   (`TAI_web`, `TAI_web2`, 4.929 tarjetas): 4.800 tarjetas, cada etiqueta comprobada **leyendo dos tarjetas** de
   esa etiqueta antes de escribir su regla;
3. el **texto de la tarjeta**, solo con el enlace fuerte —el que se midió en **96,2 %** contra el orden de los
   exámenes oficiales—; el vocabulario del tema se descartó en su día (66,7 %) y aquí no se usa.

Resultado: **13.687 de 15.403 tarjetas con tema** y **1.716 sin tema**, que son casi todas las 1.580 de otras
administraciones (sus exámenes no son del temario de TAI, y ponerles un tema sería inventarlo) más 136 tarjetas
sin texto utilizable.

### La comprobación que se hizo antes de fiarse del rótulo

Los mazos `B4 - 🛜::T1 … T10` no traen título, solo el número. Se **leyeron** sus tarjetas: `T1` es Debian y GRUB
(IV.1), `T2` MySQL y copias (IV.2), `T3` el RFC 822 del correo (IV.3), `T4` SNMP y gestión de red (IV.4), `T5`
amenaza/vulnerabilidad/impacto (IV.5), `T6` Wi-Fi y 802.11 (IV.6), `T7` el modelo OSI (IV.7), `T8` W3C y puertos
(IV.8), `T9` cortafuegos y niveles (IV.9), `T10` VLAN y conmutación (IV.10). **Diez de diez** coinciden con la
numeración del programa, así que la regla `b4 …::t<n> → IV.<n>` está justificada, no supuesta.

### El límite de esta regla, medido

El rótulo es del temario de **quien hizo el mazo**, y ese temario no numera igual que el de la convocatoria. El
caso concreto: el mazo `B3 - 💻::T8 - Lenguajes de programación` trae preguntas de **PHP, JavaScript, CSS y HTML**,
y en el programa de la aplicación los lenguajes web están en **III.7** (aplicaciones web), no en III.2. Medido
(`medir_html_en_los_lenguajes.py`): **25 de las 77** preguntas de III.2 llevan términos de web en el enunciado
(PHP 11, JavaScript 5, atributos 4, CSS 3, HTML 2).

No se han movido, y el motivo es que **no todas son lo mismo**: «en PHP, para eliminar una variable…» es
construcción del lenguaje (III.2) y «¿cuál de los siguientes es un preprocesador CSS?» es aplicación web (III.7).
Separarlas pide decidir pregunta a pregunta, que es justo lo que no se hace aquí. Queda dicho, con su número, para
que quien quiera afinar lo afine con una regla, no a mano.

## 3. Lo que ha entrado en la aplicación
Los test van al **banco** como pregunta normal, con **cita**: un texto limpio con una pregunta por párrafo por
mazo y parte (83 ficheros), ingerido como documento, `import-document` para la cita y un **CSV** con `correct`,
`topic` (la ruta del nodo del programa) y la **procedencia** de cada pregunta (mazo, número de tarjeta, fichero y
examen de origen) en su explicación.

| qué | antes | ahora |
| --- | --- | --- |
| preguntas en el banco | 5.224 | **11.292** |
| con tema | 4.023 (77,0 %) | **8.570** |
| con clave | 5.184 | **11.234** |
| con cita | 5.213 | **11.250** |
| conjuntos de preguntas | 31 | **105** |
| documentos en la biblioteca | 3.228 | **3.347** |
| temas del programa sin preguntas | **3** (II.2, III.2, IV.5) | **0** |

- **6.068** preguntas nuevas en 74 conjuntos `Banco privado · mazo de la comunidad «…»`: **todas completas**,
  6.037 con clave y 6.037 con cita.
- Los tres temas que estaban a cero por preguntas ya no lo están: **II.2 periféricos 83**, **III.2 lenguajes de
  programación 77**, **IV.5 seguridad de los sistemas de información 108**. El tema con menos preguntas del
  programa pasa a ser **III.7 (8)**.
- Las **5.576 tarjetas de estudio** con tema entraron como documentos de tipo `flashcards` (36 ficheros) y se
  **mapearon a su nodo del programa**: la biblioteca de cada tema tiene ya sus tarjetas, citables y buscables.
- Los **apuntes** se han refrescado con el material nuevo (`anadir_material_de_la_biblioteca_a_los_apuntes.py`):
  **2.458 fragmentos añadidos en 28 apuntes** (hasta 12 por documento y 150 por apunte, como se decidió al medir
  el exceso la vez anterior). Las versiones anteriores están guardadas en
  `F:\OpoFuente\APUNTES-anteriores\2026-09-30-1439`.

`mapa_de_material_por_tema.py` lo confirma: **33 temas · sin material asignado: 0 · con menos de 50 fragmentos:
0 · sin ninguna pregunta: 0.**

## 4. Dos defectos de la aplicación, medidos y reproducidos

### 4.1 Los nombres de campo de las barajas modernas se pierden

El extractor de Anki lee los nombres de campo de `notetypes.config` esperando **JSON**. Desde Anki 2.1.28 ese
campo es **protobuf**: `json.loads` falla, `_json()` devuelve `None` y la baraja se guarda con «campo 1: …»,
«campo 2: …» en lugar de «Anverso: …», «Reverso: …». Los nombres **sí están** en la tabla `fields`
(`ntid, ord, name`) de la propia colección, que el extractor no mira.

Medido con la base de dentro de cada contenedor: `[@xelarro] CE.apkg`, `EBEP-Transparencia-2030.apkg`,
`Tema 5.apkg` y `[@Danie_e_e] ColecciónAnki.colpkg` son modernas (`config` empieza por `b'\x1a'`/`b'\x10'`, no por
`{`) y traen su tabla `fields` completa (`['00 Tipo Test 4 Preguntas', 'Answer1', 'Distractor2', 'Distractor3',
'Distractor4', 'Explanation (optional)']`, `['Question', 'option_1 (A)'…, 'Ans', 'Explanation']`…). Las antiguas
(`[@viclomu] BLOQUE_IV.apkg`, `[@trirodol] TAI_web…`) sí traen JSON y hoy se leen bien.

Consecuencia hoy, medida en la biblioteca: **4 documentos y 1.851 fragmentos** guardados con nombres genéricos —
`[@Danie_e_e] ColecciónAnki.colpkg` (932), `CE.apkg` (555), `EBEP-Transparencia-2030.apkg` (237) y `Tema 5.apkg`
(127)— justo las cuatro colecciones modernas. Las tarjetas de esos mazos se citan sin decir qué campo es cada
cosa. El arreglo es leer `fields` cuando `config` no sea JSON (una consulta y un `dict`); el texto ya guardado
solo mejora con una reingesta, y eso hay que decidirlo, no colarlo.

De paso, medido: `CE.apkg` y `Tema 5.apkg` están en la biblioteca clasificados como `law_or_regulation`, que no es
lo que son (son barajas de test). No lo he tocado.

Reproducción: `ver_nombres_de_campo_de_las_barajas.py`.

### 4.2 Un texto que se lee como texto acaba en «conservado sin extraer», y sin decir por qué

`detect_format` decide el formato con los **primeros 4.096 bytes** (`SNIFF_BYTES`) y `try_decode_text` no recorta
ese bloque al límite de carácter —a diferencia de `read_bounded`, que sí lo hace—. Si el corte parte un carácter
UTF-8 por la mitad y el byte que queda es uno de los que **no existen en cp1252** (`0x8D`, `0x8F`, `0x90`,
`0x9D`), fallan las dos decodificaciones, el fichero se clasifica **binario**, y el plan es
`preserve` → `unsupported_preserved` («conservado sin extraer», DEBT-008) **sin ningún aviso que explique que era
un `.txt` perfectamente legible**.

Medido: de 83 textos de mazo, **2 cayeron en el caso** (`b3-t1-modelo-e-r-parte-1.txt` y
`bloque-general-tests-generals-muchos-tests-parte5.txt`, 284 preguntas) porque el byte 4.096 caía dentro de un
emoji de la cabecera (🍀, 💻). Reproducido invocando la propia aplicación
(`preguntar_por_que_no_se_extraen.py`): los cuatro ficheros son UTF-8 válidos, sin bytes nulos, y la aplicación
dice `familia 'binary'` para los dos que llevan el emoji partido.

Arreglo del lado de los textos: los generadores ahora **comprueban cada fichero con el detector de la
aplicación** y, si hace falta, le ponen delante un bloque ASCII de exactamente 4.096 bytes (`asegurar_que_parece_texto`
de `mazos_de_anki_a_texto.py`). Los dos ficheros se regeneraron, se ingirieron aparte y sus **284 preguntas
entraron con su cita y su clave** (`mazos-de-anki-arreglados`).

El arreglo de verdad es de la aplicación: recortar el bloque de sniffing al límite de carácter (lo que ya sabe
hacer `_trim_to_character_boundary`) o, cuando menos, **decir el motivo** en el aviso del elemento.

Reproducción: `ver_si_los_textos_rechazados_son_copias.py` y `preguntar_por_que_no_se_extraen.py`.

## 5. Lo que se ha dejado fuera, dicho en números

Nada se ha borrado ni se ha metido a medias:

- **169 tarjetas** sin pareja anverso/reverso utilizable: 128 del mazo `Git Cheat Sheet` (su anverso es el campo
  `Explanation` y viene vacío en la mitad de las tarjetas) y 41 con texto vacío u oclusión de imagen (que son
  imágenes: no hay texto que extraer).
- **1.519 preguntas** de exámenes de **otras administraciones** entraron **sin tema**, y se declaró: su examen de
  origen va en la explicación de cada pregunta. Son preguntas con clave oficial, útiles para practicar, pero no del
  temario de TAI.
- **18 preguntas sin clave** de las 31 que quedaron sin clave al importar: se intentó recuperar la clave
  localizando la opción correcta **por su texto** entre las opciones que la aplicación leyó
  (`poner_clave_a_las_preguntas_sueltas_de_los_mazos.py`); 13 se recuperaron y las otras 18 se dejan **sin clave a
  propósito**, con su motivo, porque su opción correcta no se localiza sin ambigüedad. En el banco entero quedan
  **58 preguntas sin clave** (40 de antes + 18) y **42 sin cita** (11 de antes + 31 de los mazos).
- **47 mazos** (9.066 tarjetas) no han dado ningún test: son mazos que solo traen anverso/reverso o Cloze, así
  que su sitio es el material por tema, no el banco. Se han quedado ahí.

## 6. `DEBT-023` sigue abierta, y esto no la cierra

Las tarjetas de anverso/reverso y las Cloze **no** se han metido como preguntas, y no por falta de ganas: el
modelo sigue sin tener dónde guardar la respuesta de referencia. Lo que sí se ha hecho es dejar esas 5.576
tarjetas **en la biblioteca y mapeadas a su tema**, que es la mitad honesta: se estudian y se citan, pero no se
contestan. Los criterios de cierre del `DEBT-023` (un ADR que decida dónde vive el reverso, y una prueba con una
baraja sintética de tarjeta → estudio → respuesta autoevaluada) **siguen pendientes**, y la decisión es de
arquitectura: no la tomo yo.

Las dos deudas de arriba (§4.1 y §4.2) están redactadas aquí con su medición y su reproducción para que quien
lleve el libro de deudas les ponga número; no las he escrito en `DEBT.md` para no pisar el fichero que se está
tocando desde el otro lado.

## 7. Cómo se reproduce todo esto

```
python cosechar_tarjetas_de_anki.py                    # 15.403 tarjetas → BANCO\tarjetas-de-anki.jsonl
python temas_de_las_tarjetas.py                        # rótulo + etiqueta + texto → 13.687 con tema
python mazos_de_anki_a_texto.py                        # textos de test y de tarjetas + manifiesto
python mazos_de_anki_a_la_app.py --ingerir             # 83 + 36 ficheros
python mazos_de_anki_a_la_app.py --test --aplicar      # 74 conjuntos, 6.068 preguntas
python mazos_de_anki_a_la_app.py --tarjetas --aplicar  # 36 documentos mapeados a su tema
python comprobar_mazos_en_la_app.py --conjunto "mazo de la comunidad"   # lo medido en §3
python mapa_de_material_por_tema.py                    # 33 temas, ninguno sin material ni sin preguntas
```

Salidas de material: `F:\OpoFuente\TAI\internet\mazos-de-anki\{test,tarjetas}`, catálogos en
`F:\OpoFuente\CATALOGO\{tarjetas-de-anki.json, temas-de-las-tarjetas.json, mazos-de-anki-textos.json,
mazos-de-anki-en-la-app.json, mazos-claves-recuperadas.json}`.
