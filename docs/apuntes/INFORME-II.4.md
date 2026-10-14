# Informe de II.4 — Sistemas operativos, Windows, Unix y Linux y sistemas móviles

**Tanda:** f17 · **Fecha de la corrida:** 12 oct 2026 · **Estado:** **publicado** (versión archivada,
con la marca «Versión generada · en revisión»)

Las cifras de este informe están **medidas** sobre la base real con `apuntes --medir` y
`apuntes --esquema`, no heredadas de la corrida que las escribió. El índice de este tema se escribió
**en esta misma tanda, antes de gastar** (`domain/catalogo_ii_4.py`, 17 apartados, 481 de sus 501
grupos situados por el enunciado): no venía de una tanda anterior.

## 1. Hechos y apartados

| Qué | Antes de deduplicar | Después |
|---|---|---|
| Hechos | 1.046 | **848** (195 repetidos agrupados) |
| Apartados | — | **17** (ninguno pasó del tope de 150 hechos) |
| Grupos de preguntas | 501 | 499 en los apartados (+2 sin materia) |
| Preguntas | 577 | 575 en los apartados (+2 sin materia) |

- 20 grupos **no dicen de qué hablan por su enunciado** y se situaron por el texto de sus hechos; al
  final quedan **2 grupos y 3 hechos sin materia**, que van a la bandeja del propietario con su
  motivo (23 preguntas: dos de ellas son de otro tema y el índice no las esconde en un cajón).
- Revisión del índice: **PASA** · 17 apartados · 848 hechos.
- Ningún apartado pasó de 150 hechos, así que **no hubo que partir ninguno**: es la primera vez que
  un tema de este tamaño (501 grupos) cabe sin trozos.

## 2. Las puertas del §2.3

| Comprobación | Umbral | Medido | ¿Pasa? |
|---|---|---|---|
| Encabezados repetidos / misma cabecera | 0 | **0, tras el arreglo** | **sí** |
| Marcas internas visibles | 0 | 0 | **sí** |
| Tablas sin cabecera o columnas sin nombre | 0 | **0, tras el arreglo** | **sí** |
| Párrafos casi repetidos | ≤ 3 % | 0,3 % | **sí** |
| Hechos fuera de su materia | ≤ 3 % | **no implementada** (aviso del §5 del estado) | — |
| Extensión | ≤ 40 palabras × hechos | 26.367 de 41.840 | **sí** |
| **Preguntas cubiertas** (clave utilizable) | **≥ 90 %** | **443/462 = 95,9 %** | **sí** |
| Preguntas cubiertas (todas las que tienen clave) | — | 443/568 = 78,0 % | — |
| Conflictos de letra sin categorizar | 0 | 0 | **sí** |
| Copia literal de material no normativo | 0 párrafos | 0 | **sí** |
| Afirmaciones sobre exámenes no calculadas | 0 | 0 | **sí** |

**La corrida terminó con la forma en NO PASA, y se arregló sin volver a pagar** (ver §6: dos arreglos
de motor, los dos con su prueba que falla antes). Lo que la puerta encontró, con su frase:

- **1 cabecera compartida por 3 o más apartados**: cuatro apartados se titulaban «Unix y Linux: …» y
  la revisión mira las **tres primeras palabras** del título. Lo arregló la limpieza de forma, que
  ahora vuelve a poner el título que dice **el índice** (13 apartados lo tenían distinto del catálogo,
  porque el redactor acorta los títulos al escribir);
- **1 tabla sin cabecera utilizable** en `unix-comandos-y-shell`, fila 138: la tabla de operadores
  del shell tiene una fila cuyo contenido **es** la tubería (`` | ``), y sin escapar partía la fila
  en tres celdas donde la cabecera tiene dos. Se arregló escapándola: ahora la fila dice
  `` | `\|` | Tubería: encadena la salida de un comando con la entrada del siguiente | `` y el lector
  sigue viendo la misma tubería.

## 3. Incidencias en la bandeja del propietario, por categoría

| Categoría | Cuántas |
|---|---|
| `norma_cambiada` (la clave contradice la norma o el material) | 71 |
| `clave_sospechosa` (los apuntes dicen otra letra, con la frase que lo demuestra) | 11 |
| `hueco_sin_material` (los apuntes no tienen el dato) | 0 |
| `pregunta_ambigua` (sin clave con la que comprobar) | 0 |
| **Total** | **82** |

**Y una cifra que este tema comparte con IV.2**: «sin contestar por los apuntes: **0**». De los 501
grupos, 419 quedaron cubiertos con su letra y su cita (403 a la primera y 16 tras añadir material en
el bucle de huecos) y los 82 que quedan «a revisión» lo están porque **su clave** no se puede usar,
no porque falte el texto. La diferencia con IV.2 es de grado, y está medida: aquí la cobertura sobre
clave utilizable es el 95,9 % y sobre todas las claves el 78,0 % —282 preguntas del banco de este
tema tienen una clave que contradice el material, y eso no lo arregla el texto—.

## 4. Lo que costó, y lo que se dijo antes de pagarlo

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 92 como mínimo y 158 como máximo | **166** (0 fallidas) |
| Entrada | — | 1.567.294 tokens (1.109.504 de caché) |
| Salida | — | 777.151 tokens |
| Coste | 0,63 $ como mínimo y 1,07 $ como máximo | **0,7014 $** |
| Duración | — | 50 minutos (13:26 → 14:16) |

La **cota de llamadas se quedó corta por 8** (166 frente a 158) y el **coste cayó por el medio del
rango**. Es el mismo patrón que I.4 (que se pasó de la cota de llamadas) y el contrario que IV.2 (que
se quedó por debajo del mínimo del dinero): las llamadas del bucle de huecos no se pueden prever —en
II.4 hubo 71 claves que contradicen la norma y 11 en conflicto— y el precio por llamada sí depende
del tema (aquí 0,00423 $ por llamada frente a los 0,0068 $ de la media).

**El tope de esta tanda no se activó**: el tope era la cota de arriba más un tercio (**1,07 × 4/3 =
1,43 $**) con un tope de tiempo de 5.000 s, y la corrida se quedó en 0,7014 $ y 50 minutos.

## 5. Lo que se dejó escrito

- **Publicado**: la cobertura PASA (95,9 %) y la forma PASA tras la limpieza, así que `--publicar`
  archivó la versión. El tema se lee en la zona del alumno con la marca «Versión generada · en
  revisión».
- **82 incidencias** esperan el criterio del propietario en la bandeja del motor (`notes_incidents`).
- **La limpieza de forma se pagó una vez y sirvió para dos cosas**: los títulos y la tabla. La
  corrida no se repitió (`--prever` decía que volver a lanzarla costaría 50–117 llamadas, 0,34–0,80 $,
  solo por los títulos): se arregló con dos reparaciones de forma de 0 $.

## 6. Los dos arreglos de motor de esta tanda, con su prueba que falla antes

Los dos salieron de esta corrida y los dos están en `domain/notes_quality.py`, con su prueba en
`tests/unit/test_notes_quality.py`:

1. **Una tubería dentro de un `código` en una celda de tabla se escapa** (`escapar_tuberias_en_celdas`,
   aplicada al guardar y en `--limpiar-forma`) y **el medidor deja de partir por una tubería
   escapada** (`_celdas`). Son las dos mitades de la misma cosa: sin lo primero la tabla no se puede
   arreglar y sin lo segundo el arreglo no se nota. Con el código de antes, las dos pruebas nuevas
   **fallan** (`2 failed`); con el arreglo, las 34 del fichero pasan. El registro del rojo está en
   `F:\temp-opofuente\f17-scratch\rojo-tuberia.txt`;
2. **El título de un apartado se vuelve a poner desde su índice** (`titulos_que_cambian` y
   `_titulos_del_indice`, en `--limpiar-forma`). Cierra la asimetría que dejó esta corrida: la puerta
   de forma **sí** medía las cabeceras compartidas y **no** había forma de arreglarlas sin pagar otra
   corrida. Con el código de antes, la prueba nueva no puede ni importarse (error de colección: la
   función no existía) y las 93 del fichero pasan después. El registro del rojo está en
   `F:\temp-opofuente\f17-scratch\rojo-titulo.txt`.
