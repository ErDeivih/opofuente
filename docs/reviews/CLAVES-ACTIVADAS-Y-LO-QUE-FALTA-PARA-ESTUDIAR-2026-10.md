# Las claves se activaron, y lo que falta para poder estudiar (octubre 2026)

Resumen en una línea: el banco tenía **233 conjuntos con plantilla y 0 activas**, así que la
aplicación rechazaba cualquier sesión; ahora hay **154 activas** (6.623 preguntas estudiables), la
práctica por tema funciona en los 33 temas de TAI y los cuatro exámenes oficiales de TAI 2025 se
hacen y se corrigen de punta a punta. Lo que queda son 79 conjuntos con la clave a medias y las
reservas que le faltan al examen de Guardia Civil.

Todo lo que sigue está medido contra la aplicación en marcha (`http://127.0.0.1:8765/api/v1`) y
contra la base (`F:\OpoFuente\datos\opofuente.sqlite3`), con el script que se cita en cada punto.

---

## 1. El punto de partida, medido

| lo que se intentó | respuesta de la aplicación |
| --- | --- |
| práctica por tema I.1 (`POST /study-sessions`, modo `practice`) | **409** · «las preguntas de este tema no se pueden corregir todavía: 2000 sin plantilla activa y 2 que no se practican solas (reservas o tipo no soportado)» |
| examen oficial TAI 2025 A | **409** · «el conjunto no tiene ninguna clave activa: activar una plantilla es lo que decide con qué se corrige el examen» |
| examen oficial Guardia Civil 2026 A | **409** · el mismo |

Reproducible: `_oficial\probar_que_pasa_si_intento_estudiar.py` (en
`F:\EspacioCodigo\proptech-access-control\docs\opofuente`).

## 2. Activar una clave oficial no bastaba: faltaba la plantilla enlazada

`POST /question-sets/{id}/answer-keys/{clave}/activate` sobre las 6 claves oficiales respondía **409
«una clave oficial necesita la plantilla oficial enlazada»**. La regla está en
`domain/questions.py:217` (`can_activate`, invariante 4): si el conjunto es oficial, la clave necesita
`answer_key_versions.source_document_version_id`. En la base ese campo estaba **a NULL en las 233
claves**.

Por qué: el único sitio que enlaza la plantilla es
`application/auto_study_service.py:173` (`_link_answer_key`), y solo corre **al aceptar** la versión
de la plantilla (`after_version_accepted`, línea 105). Esas versiones se aceptaron antes de que
existieran los conjuntos, y no hay segunda oportunidad: aceptar otra vez responde 409. Y reimportar la
plantilla por `POST /question-sets/{id}/parse` con `kind=answer_key` **tampoco** sirve, porque
`_save_key_if_new` devuelve la clave que ya existe cuando los desenlaces coinciden — no le pone el
enlace.

Lo que se hizo, entonces:

1. **Comprobar que las claves dicen lo que dice la plantilla oficial**, pregunta a pregunta y
   emparejando por enunciado (no por número, ver §5). Resultado: **100 % de coincidencia** en los seis
   exámenes (`_oficial\enlazar_la_plantilla_oficial.py`).

   | examen | preguntas | contrastadas con el fichero oficial | coinciden |
   | --- | --- | --- | --- |
   | TAI libre 2025 A / B | 135 + 135 | 270 | 270 (100 %) |
   | TAI promoción interna 2025 A / B | 85 + 85 | 166 | 166 (100 %) |
   | Guardia Civil 2026 A / B | 121 + 120 | 240 | 240 (100 %) |

   (en promoción interna hay 2 preguntas por modelo sin clave en el fichero oficial: entran sin
   respuesta, y así se quedan).

2. **Escribir el enlace** en `answer_key_versions.source_document_version_id`, apuntando a la versión
   aceptada del PDF oficial de la plantilla que ya está en la biblioteca (p. ej. `Plantilla respuestas
   TAI-L-A_act.pdf`). Es el único camino: la API no tiene ruta para enlazar una clave que ya existe.

3. **Activar** las 6 por API. Las seis respondieron 200.

## 3. Las demás claves, por tandas de confianza

Decisión del propietario: activar por tandas, primero el material con la respuesta marcada o publicada,
y los mazos de la comunidad al final. Antes de activar se midió **qué se puede comprobar sin leer la
clave** (`_oficial\clasificar_las_claves_por_su_calidad.py`), porque muchas claves tienen varias
versiones y no todas pueden ser buenas:

| grupo | conjuntos | preguntas |
| --- | --- | --- |
| **limpias** (una sola versión y cubre ≥ 90 % del conjunto) | 154 | 6.515 |
| **a revisar** (varias versiones; 42 de ellas no cubren lo mismo) | 59 | 2.593 |
| **flojas** (la mejor cubre menos de la mitad) | 20 | 7.876 |
| sin ninguna clave | 0 | 0 |

Se activó **solo el grupo limpio**: 148 conjuntos nuevos (los 6 oficiales ya lo estaban) = 5.834
preguntas, 148 de 148 sin un solo fallo (`_oficial\activar_las_claves_por_tandas.py --limpias
--aplicar`).

Estado de las claves después: **154 activas, 417 en borrador (79 conjuntos)**.

### Por qué el grupo «flojo» lo está (y por qué no se activa)

No es que falte material: es que la clave se quedó a medias. Ejemplo medido
(`_oficial\medir_a_que_preguntas_apunta_cada_clave.py`), el conjunto
`TAI · 1600_preguntas_constitucion_espanola_1`: 1.547 preguntas y **ocho** versiones de plantilla, y
las ocho apuntan a las mismas posiciones **1..200**. Al importar una plantilla suelta la aplicación
alinea **por número de pregunta** (`question_service.py:521` → `questions_by_position`), y ese fichero
trae cientos de test seguidos, cada uno con su tabla de respuestas que numera desde 1: la tabla del
tramo 3 acaba sobre las preguntas del tramo 1. Activar eso corregiría con la respuesta equivocada.

Los otros dos grandes del grupo flojo tienen el mismo aspecto (200 filas exactas, que es el tamaño de
página con el que se importaron): `BLOQUE GENERAL::TESTS GENERALS::MUCHOS_TESTS` (1.519 preguntas,
200 con clave), `Tai_BBDD_2025` (839, 200), `Exámenes TAI - Test GSI (v2024)` (828, 200),
`astrocuestion` (1.229, 53 con 54 versiones). Para activarlos hay que **rehacer la clave con las
numeraciones absolutas** (una sola versión que cubra el conjunto entero), no activar lo que hay.

## 4. Lo que ya se puede hacer hoy

- **Práctica por tema**: funciona en los 33 temas de TAI. Preguntas estudiables hoy: **6.623**
  (antes 0). Por tema, de 59 (IV.3) a 559 (IV.2); los temas flacos quedan bien porque su material es
  de ficheros con una sola tabla de respuestas: II.2 83 de 83, IV.3 59 de 70, IV.1 138 de 148,
  III.6 92 de 105.
- **Examen oficial**: los cuatro de TAI 2025 (libre y promoción, modelos A y B) se montan, se
  contestan y se corrigen. Comprobado de punta a punta
  (`_oficial\probar_el_examen_de_punta_a_punta.py`): creación 201, arranque 200, respuestas 201 con su
  corrección, y resultado con penalización 1/3 y reservas repartidas; la sesión de `primera_parte`
  sale con 85 preguntas (80 + 5 reservas) y la etiqueta de la clave activa.
- Además, los tres exámenes completos de TAI 2019, 2022 y 2024 («con su plantilla») ya tienen clave
  activa, así que también se pueden hacer como examen.

## 5. Lo que le falta al examen de Guardia Civil 2026

`POST /study-sessions` con la parte `conocimientos_generales` responde **409**:

> la parte «conocimientos_generales» pide 5 reservas y el conjunto tiene 0: faltan reservas para el
> examen oficial

La convocatoria declara 100 preguntas ordinarias + 5 de reserva, y `study_service.py:1254` exige que el
conjunto tenga al menos esas 5 reservas. Los conjuntos de GC tienen **0** (`is_reserve = 0` en las 241
preguntas). Y no es que no existan: están en la página 17 del PDF oficial
(`GC-oficial-INGRESO-GC-2026-TIPO-A.pdf`, 19 páginas), preguntas **101 a 105**, más la reserva de
idioma (la 21 de la prueba de lengua inglesa, al final de la página 19). Lo que pasó es que la versión
de texto que se llevó a la biblioteca se cortó justo en la instrucción anterior:

> LAS SIGUIENTES PREGUNTAS SE CONTESTARÁN EN LAS CASILLAS NUMERADAS DEL 101 AL 105 DEL APARTADO DE
> RESERVA.

Comprobado con pymupdf sobre el PDF original (`_oficial\buscar_la_reserva_que_falta_en_gc.py`).
Arreglarlo es: añadir esas 6 preguntas al conjunto con `is_reserve` y `reserve_order`, darles su letra
de la plantilla oficial y volver a activar. Además los conjuntos de GC **mezclan dos partes** en un
mismo conjunto (conocimientos e idioma) con **posiciones repetidas** (21 posiciones duplicadas en el
modelo A, 20 en el B), porque cada parte numera desde 1; conviene numerar el bloque de idioma por
encima de 200 para que la parte de conocimientos no se lleve preguntas de inglés.

## 6. Defectos de la aplicación que ha destapado esto

1. **No hay ruta para enlazar (ni desenlazar) la plantilla oficial de una clave que ya existe.** El
   enlace solo se hace al aceptar la versión, así que cualquier clave creada antes (o importada por
   `parse`) se queda imposible de activar para siempre. Falta un `PATCH`/`POST` de enlace, o que
   `parse` con `source_document_version_id` actualice la clave existente en vez de devolverla sin tocar.
2. **La alineación por número es frágil cuando el conjunto tiene secciones que numeran desde 1**
   (varios test seguidos, o dos partes de un mismo examen). El aviso de `_link_answer_key` («casi
   todas sus líneas caen en una pregunta del examen, 95 %») **no lo detecta**: 93 líneas de una
   plantilla cayeron en 135 preguntas y dio 100 % de encaje. Un conjunto con posiciones repetidas
   merece que la importación de plantilla se niegue, en vez de alinear a ciegas.
3. **Preguntas sin respuesta dentro de un conjunto con clave activa**: la composición de práctica
   incluye cualquier pregunta del conjunto (`study_service.py:380`) aunque la clave activa no tenga
   entrada para ella (`key_outcome=None`, línea 405). Conviene decidir si esas preguntas se excluyen.
4. Las sesiones en estado `draft` no se pueden cerrar (`finish` responde 409): las que crean las
   pruebas de humo se quedan en la lista. En esta máquina hay 2 así.

Y una cosa mía, no de la aplicación: los importadores de claves se quedaron en 200 filas por conjunto
(el tamaño de página con el que se pedían las preguntas), lo que explica los conjuntos «flojos».

## 7. Cómo se reproduce

```
cd F:\EspacioCodigo\proptech-access-control\docs\opofuente\_oficial
$py = "F:\EspacioCodigo\opofuente\.venv\Scripts\python.exe"

& $py probar_que_pasa_si_intento_estudiar.py                 # por qué no se podía estudiar
& $py medir_las_tandas_de_claves.py                          # tandas por procedencia
& $py clasificar_las_claves_por_su_calidad.py                # limpias / a revisar / flojas
& $py enlazar_la_plantilla_oficial.py                        # contraste de las 6 claves oficiales
& $py enlazar_la_plantilla_oficial.py --enlazar --activar     # enlaza y activa
& $py activar_las_claves_por_tandas.py --limpias              # simulacro de la tanda limpia
& $py activar_las_claves_por_tandas.py --limpias --aplicar    # la activa
& $py probar_el_examen_de_punta_a_punta.py                    # examen oficial completo
& $py medir_a_que_preguntas_apunta_cada_clave.py "constitucion"  # el caso de las 8 versiones
& $py buscar_la_reserva_que_falta_en_gc.py                    # las reservas 101-105 del PDF de GC
```

## 8. Lo que queda por hacer, en orden

1. **Rehacer las claves de los 20 conjuntos flojos** con numeración absoluta (3.500 preguntas de TAI
   que hoy no se pueden practicar), y decidir las 59 «a revisar».
2. **Guardia Civil 2026**: añadir las 6 reservas, renumerar el bloque de idioma y activar; después el
   examen de GC también se podrá hacer.
3. **5.249 preguntas sin tema** de TAI (de 16.743): sin tema no entran en la práctica por tema.
4. **3.067 documentos sin asignar** al programa de TAI (de 4.477 aceptados).
5. Los tres defectos de §6, empezando por el enlace de la plantilla (es el que deja conjuntos
   inactivables para siempre).
