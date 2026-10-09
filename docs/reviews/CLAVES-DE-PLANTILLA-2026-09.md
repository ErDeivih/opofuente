# Las claves del banco, contrastadas contra las plantillas oficiales (29-30 de septiembre de 2026)

El objetivo pedía «montar un banco único de preguntas con sus respuestas **y contrastarlo contra las
plantillas oficiales**». Esto es ese contraste, y ha encontrado un fallo real de lectura en la cosecha: **41
respuestas del banco estaban mal** y una más venía de una plantilla provisional ya corregida por el INAP.

## El contraste

`contrastar_claves_en_la_app.py` compara, dentro de la aplicación, la respuesta que el banco da a cada
pregunta con la de la **plantilla oficial**, emparejando por la **huella** de la pregunta (enunciado
normalizado y juego de opciones sin orden) y comparando **el texto de la opción**, no la letra: la misma
pregunta aparece en el modelo A y en el B con las opciones en otro orden, así que comparar letras daría
desacuerdos que no existen.

Primera pasada:

| | |
| --- | --- |
| preguntas que están en el examen oficial y en el banco privado | 50 |
| la respuesta coincide | 41 (**82 %**) |
| **la respuesta NO coincide** | **9** |

Las 9 estaban todas en `TAI · Cuestionario TAI-P-ModeloA`.

## Lo que no era

Lo primero que parecía: un **desplazamiento de numeración** (la respuesta de la pregunta *n* guardada en la
*n−1*). Se midió (`probar_desplazamiento.py`) comparando la letra del banco con la plantilla en varias
posiciones:

| desplazamiento | coincidencias |
| --- | --- |
| −2 | 12 de 48 (25 %) |
| −1 | 12 de 49 (24 %) |
| **0** | **40 de 50 (80 %)** |
| +1 | 13 de 49 (27 %) |
| +2 | 12 de 48 (25 %) |

No hay desplazamiento global: 24-27 % es lo que sale por azar. El fallo estaba en otro sitio.

## Lo que era

La plantilla del INAP, leída tal cual, es así:

```
PLANTILLA DEFINITIVA DE RESPUESTAS DEL EJERCICIO ÚNICO
Cuerpo de Técnicos Auxiliares de Informática … - Promoción Interna
MODELO A

Primera parte
1.
d
2.
b
…
10. a
…
50. b
Preguntas de reserva
1.
b
…
Supuesto I
1.
b
…
```

Dos cosas que el lector de claves no soportaba:

1. **El número y la letra van en líneas distintas** para las preguntas de una cifra. El lector exigía que la
   tabla ya hubiera empezado para aceptar un número suelto, así que las respuestas 1 a 9 **no se leían**; las
   ocupaban las de la sección `Preguntas de reserva`, que también numera desde 1.
2. **Cada sección reinicia la numeración** (`Primera parte` 1..50, `Preguntas de reserva` 1..5,
   `Supuesto I` y `Supuesto II` 1..12). Leídas de corrido, se mezclan.

Arreglado en `_oficial/cosechar_claves_propias.py` (`tablas_de_clave`): se acepta el par en dos líneas desde
la primera respuesta y **cada retroceso en la numeración cierra la tabla y abre otra**.

## Lo que se cambió, y con qué garantía

Volver a cosechar todo el árbol dio un fichero con **1.201 filas** frente a las 1.347 anteriores: el arreglo
corrige unas plantillas y **estropea otras** (hay maquetas que no son `número / letra` ni tienen secciones).
Así que no se reemplaza la cosecha en bloque: se comprueba **pareja a pareja contra el fichero**
(`verificar_letras_contra_plantilla.py`) y solo se acepta la lectura nueva donde coincide **al 100 %** con la
plantilla.

| plantilla | lectura nueva contra el fichero | ¿se aplica? |
| --- | --- | --- |
| Plantilla respuestas TAI-P-ModeloA.pdf | 50 de 50 (100 %) | **sí** |
| Plantilla respuestas TAI-P-ModeloB.pdf | 50 de 50 (100 %) | **sí** |
| TAI_sol_1_A_promo_AGE_2024.pdf | 50 de 50 (100 %) | **sí** |
| TAI_sol_1_B_promo_AGE_2024.pdf | 50 de 50 (100 %) | **sí** |
| TAI_sol_1_promo_AGE_2022.pdf | 46 de 46 (100 %) | **sí** |
| TAI_sol_1_libre_AM_2023.pdf | 89 de 89 (100 %) | **sí** (no cambiaba nada) |
| TAI_sol_2_libre_AM_2023.pdf | 30 de 30 (100 %) | **sí** (no cambiaba nada) |
| 2019 - GSI promoción interna - plantilla | 80 de 80 (100 %) | **sí** |
| TAI_sol_1_B_libre_AGE_2024.pdf | 74 % | no |
| TAI_sol_1_A_libre_AGE_2024.pdf | 72 % | no |
| TAI_sol_1_libre_AGE_2022.pdf | 62 % | no |
| tai-pi-plantilla-definitiva.pdf | 29 % | no |
| C_sol_1_libre_* / SIMULACRO_* / Soluciones simulacro 1 | sin datos comparables (otra maqueta) | no |

La cosecha que queda es `test-en-pareja.jsonl` (vieja como base, con las parejas verificadas sustituidas):
**41 respuestas corregidas**.

| fichero | respuestas corregidas |
| --- | --- |
| Cuestionario TAI-P-ModeloA.pdf | 9 |
| Cuestionario TAI-P-ModeloB.pdf | 9 |
| TAI_ejer_1_B_promo_AGE_2024.pdf | 8 |
| TAI_ejer_1_promo_AGE_2022.pdf | 8 |
| TAI_ejer_1_A_promo_AGE_2024.pdf | 5 |
| 2019 - GSI promoción interna - cuestionario | 2 |

Y una corrección distinta, que el contraste volvió a destapar: la **pregunta 7** del cuestionario TAI-P-A
venía de la plantilla **provisional** (`a`), y la **definitiva** del INAP la corrigió (`d MODIFICADA`). Se
reescribe con la definitiva (`usar_plantilla_definitiva.py`, comprobado 50 de 50 contra el fichero). La
definitiva es la que manda: es la que corrige.

Después se rehacen los conjuntos afectados (`rehacer_conjuntos.py`) y se vuelve a pasar el contraste:

| | antes | después |
| --- | --- | --- |
| preguntas que están en los dos sitios | 50 | 50 |
| la respuesta coincide | 41 (**82 %**) | **50 (100 %)** |

Al rehacer los conjuntos se pierden los **temas** que tenían sus preguntas (se borran y se vuelven a crear), y
eso se vio en el recuento: 1.116 → 1.030. Se volvieron a enlazar con `temas_del_banco_en_la_app.py --aplicar`
y el banco quedó otra vez con **1.116 preguntas con tema**.

## Lo que queda pendiente, medido

Tres plantillas del material de terceros (`TAI_sol_1_A_libre_AGE_2024`, `TAI_sol_1_B_libre_AGE_2024`,
`TAI_sol_1_libre_AGE_2022`) **no cuadran con el fichero con ninguna de las dos lecturas**: la vieja y la nueva
coinciden con lo que dice la plantilla solo entre el **62 % y el 74 %** de las veces. Eso apunta a que el
emparejamiento número↔letra está mal para esas parejas (probablemente porque la numeración del cuestionario no
empieza donde la de la plantilla). No se ha tocado nada ahí: cambiar una respuesta por una lectura que **no**
se ha podido verificar sería peor que dejarla como está. Queda como trabajo con nombre y número.

## La lección

Una plantilla **no** es una lista de pares «número letra»: es un documento con secciones que numeran por su
cuenta y con dos formas de escribir el par (en una línea o en dos). Y una cosecha **no** se reemplaza en
bloque: se comprueba contra el fichero y se sustituye solo lo verificado, porque un arreglo que mejora ocho
parejas y estropea cuatro no es un arreglo. Lo que destapó el fallo fue el contraste contra el examen oficial:
sin él, estas 41 respuestas habrían seguido mal en el banco y nadie lo habría sabido.

## Ficheros

- `_oficial/contrastar_claves_en_la_app.py`: el contraste contra las plantillas oficiales, con el texto de la
  opción y por conjunto.
- `_oficial/cosechar_claves_propias.py`: el lector de plantillas arreglado (par en dos líneas y secciones).
- `_oficial/verificar_letras_contra_plantilla.py`: comprueba una cosecha contra los ficheros de plantilla.
- `_oficial/fusionar_cosechas.py`: mezcla dos cosechas aceptando solo las parejas verificadas al 100 %.
- `_oficial/usar_plantilla_definitiva.py`: reescribe una pareja con la plantilla definitiva.
- `_oficial/rehacer_conjuntos.py`: deshace los conjuntos afectados con una sola copia de seguridad.
- `_oficial/probar_desplazamiento.py`, `_oficial/leer_plantilla_y_comparar.py`,
  `_oficial/medir_impacto_del_arreglo.py`, `_oficial/comparar_cosechas*.py`,
  `_oficial/buscar_plantillas_definitivas.py`, `_oficial/ver_plantilla_cruda.py`: las medidas que decidieron
  qué se aplicaba y qué no.
