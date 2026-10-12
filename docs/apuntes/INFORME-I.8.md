# Informe de I.8 — Acceso electrónico, procedimiento electrónico, ENS, ENI y NTI

**Tanda:** f17 · **Fecha de la corrida:** 12 oct 2026 · **Estado:** **borrador con su motivo
escrito** (la puerta de cobertura **NO PASA** y la corrida se paró en su tope de tiempo)

Las cifras de este informe están **medidas** sobre la base real con `apuntes --medir`, `apuntes
--esquema` y `apuntes --publicar`, no heredadas de la corrida. El índice de este tema se escribió
**en esta misma tanda, antes de gastar** (`domain/catalogo_i_8.py`, 18 apartados estructurados por
las normas del tema, 426 de sus 442 grupos situados por el enunciado).

## 1. Hechos y apartados

| Qué | Antes de deduplicar | Después |
|---|---|---|
| Hechos | 815 | **617** (191 repetidos agrupados) |
| Apartados | — | **18** |
| Grupos de preguntas | 442 | 438 en los apartados (+4 sin materia) |
| Preguntas | 606 | 601 en los apartados (+5 sin materia) |

- 16 grupos **no dicen de qué hablan por su enunciado** y se situaron por el texto de sus hechos; al
  final quedan **4 grupos y 7 hechos sin materia**, que van a la bandeja con su motivo.
- Revisión del índice: **PASA** · 18 apartados · 617 hechos.
- Revisión de forma: **PASA** · 23.285 palabras de 32.600 · repetidos 0,3 %. La limpieza de forma
  tocó **17 títulos** (el redactor los acorta al escribir y la limpieza les devuelve el de su índice:
  es el arreglo 12 del §3 del estado) y **0 cuerpos**.

## 2. Las puertas del §2.3

| Comprobación | Umbral | Medido | ¿Pasa? |
|---|---|---|---|
| Encabezados repetidos / misma cabecera | 0 | 0 | **sí** |
| Marcas internas visibles | 0 | 0 | **sí** |
| Tablas sin cabecera o columnas sin nombre | 0 | 0 | **sí** |
| Párrafos casi repetidos | ≤ 3 % | 0,3 % | **sí** |
| Hechos fuera de su materia | ≤ 3 % | **no implementada** (aviso del §5 del estado) | — |
| Extensión | ≤ 40 palabras × hechos | 23.285 de 32.600 | **sí** |
| **Preguntas cubiertas** (clave utilizable) | **≥ 90 %** | **423/516 = 82,0 %** | **NO** |
| Preguntas cubiertas (todas las que tienen clave) | — | 423/571 = 74,1 % | — |
| Conflictos de letra sin categorizar | 0 | 0 | **sí** |
| Copia literal de material no normativo | 0 párrafos | 0 | **sí** |
| Afirmaciones sobre exámenes no calculadas | 0 | 0 | **sí** |

## 3. El motivo escrito del borrador

**Son dos, y el segundo importa tanto como el primero:**

1. **la cobertura medida es el 82,0 %** de las 516 preguntas con clave utilizable, y el listón del
   §2.3 es el 90 %. **No se toca el listón**: le faltan 41 preguntas cubiertas;
2. **la corrida no terminó**: se paró en su **tope de tiempo** (5.000 s) con **389 de los 442 grupos
   comprobados**, así que el 82,0 % es un **suelo**, no el techo del tema. La última línea del informe
   lo dice con esas palabras («se agotó el tiempo de la corrida: no se han hecho las llamadas que
   quedaban. Lo escrito está guardado y volver a lanzar el comando sigue desde ahí»).

**Lo que esto significa para el propietario**: el tema **se lee en el panel** (está en borrador, con
su motivo) y **no se tira nada**: los 815 hechos, los 18 apartados y las comprobaciones hechas están
en la base, y **reanudarlo no vuelve a pagar por lo escrito**. Lo que falta es terminar de comprobar
los 53 grupos que quedaron y, si hace falta, el bucle de huecos.

**Y no se ha reanudado en esta tanda, a propósito**: la corrida costó **1,2119 $** de un tope de
**1,32 $** (la cota de arriba de `--prever`, 0,99 $, más un tercio). Quedaban 0,11 $ de margen, y
reanudar cuesta más que eso. **El tope se respetó**: ni el dinero ni el tiempo se pasaron, y lo
escrito se conservó, que es exactamente para lo que está el mecanismo.

## 4. Lo que costó, y lo que se dijo antes de pagarlo

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 84 como mínimo y 145 como máximo | **142** (0 fallidas) |
| Entrada | — | 1.480.794 tokens (961.920 de caché) |
| Salida | — | **1.649.566 tokens** |
| Coste | 0,57 $ como mínimo y 0,99 $ como máximo | **1,2119 $** |
| Duración | — | 84 minutos (14:24 → 15:48) |

**Aquí la previsión se quedó corta en dinero por un 22 %**, y la causa está medida, igual que en I.4:
I.8 devolvió **11.617 tokens de salida por llamada** donde la media de la tabla es ~8.000, así que su
llamada costó **0,00853 $** y no los 0,0068 $ de la media. **Es un tema normativo y denso, y se
comporta como tal** —el segundo de la serie, después de I.4 (0,00865 $ por llamada)—.

**Y esta corrida es la demostración de que la regla del tope está bien puesta**: la cota de arriba de
`--prever` (0,99 $) no habría bastado, y el tope «duro» de 1,20 $ de f15 se habría cruzado (1,2119 $).
Con la cota de arriba **más un tercio** (1,32 $), la corrida se quedó dentro. La regla que se aprobó
tras I.4 es la que ha evitado, esta vez, que un tema se saliera de su presupuesto.

## 5. Incidencias en la bandeja del propietario, por categoría

| Categoría | Cuántas |
|---|---|
| `norma_cambiada` (la clave contradice la norma o el material) | 43 |
| `clave_sospechosa` (los apuntes dicen otra letra, con la frase que lo demuestra) | 7 |
| `hueco_sin_material` (los apuntes no tienen el dato) | 9 |
| `pregunta_ambigua` (sin clave con la que comprobar) | 1 |
| **Total** | **60** |

De los 389 grupos comprobados, 329 quedaron cubiertos con su letra y su cita (318 a la primera y 11
tras añadir material). **Nueve preguntas no tienen ninguna frase en los apuntes que las justifique**:
son huecos de material de verdad, y son las que reanudar la corrida tiene que intentar rellenar.
