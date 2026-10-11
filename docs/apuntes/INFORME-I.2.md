# Informe de I.2 — Las Cortes Generales, el Tribunal Constitucional y el Defensor del Pueblo

**Tanda:** f15 · **Fecha de la corrida:** 11 oct 2026 · **Estado:** **publicado** (versión archivada,
con la marca «Versión generada · en revisión»)

Las cifras de este informe están **medidas** sobre la base real con `apuntes --medir` y
`apuntes --esquema`, no heredadas de la corrida que las escribió.

## 1. Hechos y apartados

| Qué | Antes de deduplicar | Después |
|---|---|---|
| Hechos | 1.233 | **696** (537 repetidos agrupados) |
| Apartados | — | **16** |
| Grupos de preguntas | 685 | 685 |
| Preguntas | 845 | 845 |

- 54 grupos **no dicen de qué hablan por su enunciado** («Señale la respuesta correcta», «Una de las
  siguientes afirmaciones es falsa») y se han situado por el texto de sus hechos.
- Revisión del índice: **PASA** · 16 apartados · 696 hechos · **0 grupos y 0 hechos sin materia**.
- El apartado más grande (`cortes-composicion`) se partió en dos (`-1`, 187 hechos, y `-2`, 20) al
  pasar del tope por apartado.

## 2. Las puertas del §2.3

| Comprobación | Umbral | Medido | ¿Pasa? |
|---|---|---|---|
| Encabezados repetidos / misma cabecera | 0 | 0 | **sí** |
| Marcas internas visibles | 0 | 0 | **sí** |
| Tablas sin cabecera o columnas sin nombre | 0 | 0 | **sí** |
| Párrafos casi repetidos | ≤ 3 % | 2,9 % | **sí** |
| Hechos fuera de su materia | ≤ 3 % | **no implementada** (aviso del §5 del estado) | — |
| Extensión | ≤ 40 palabras × hechos | 24.061 de 49.320 | **sí** |
| **Preguntas cubiertas** (clave utilizable) | **≥ 90 %** | **669/703 = 95,2 %** | **sí** |
| Preguntas cubiertas (todas las que tienen clave) | — | 669/835 = 80,1 % | — |
| Conflictos de letra sin categorizar | 0 | 0 | **sí** |
| Copia literal de material no normativo | 0 párrafos | 0 | **sí** |
| Afirmaciones sobre exámenes no calculadas | 0 | 0 | **sí** |

**Un hallazgo de forma, y cómo se cerró sin volver a pagar**: la corrida terminó con **1 encabezado
repetido** — `cortes-funciones` llevaba dentro un `### Defensor del Pueblo` y el tema tiene su
apartado «El Defensor del Pueblo»—. La puerta mide los encabezados de **todo** el tema y el título de
un apartado es uno más. Se arregló en la limpieza de forma (`--limpiar-forma`, gratis, sin llamar al
modelo): `sin_encabezados_repetidos_en_el_tema` ahora recibe los títulos y quita el encabezado del
cuerpo que repite el de **otro** apartado. 7.817 → 7.794 caracteres en ese apartado y la forma pasó.

## 3. Incidencias en la bandeja del propietario, por categoría

| Categoría | Cuántas |
|---|---|
| `norma_cambiada` (la clave contradice la norma o el material) | 73 |
| `clave_sospechosa` (los apuntes dicen otra letra, con la frase que lo demuestra) | 19 |
| `hueco_sin_material` (los apuntes no tienen el dato) | 6 |
| `pregunta_ambigua` (sin clave con la que comprobar) | 1 |
| **Total** | **99** |

**Todas las preguntas no cubiertas tienen categoría**, que es la otra mitad del §2.3.

## 4. Lo que costó, y lo que se dijo antes de pagarlo

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 115 como mínimo y 195 como máximo | **194** (0 fallidas) |
| Entrada | — | 2.149.315 tokens (1.516.416 de caché) |
| Salida | — | 1.493.911 tokens |
| Coste | 0,72 $ como mínimo y 1,23 $ como máximo | **1,2187 $** |

La previsión **acertó la cota de arriba** (194 frente a 195; 1,2187 $ frente a 1,23 $). El bucle de
huecos se llevó casi todo lo que separa el mínimo del máximo: 73 preguntas con la clave
contradiciendo la norma, 19 en conflicto y 6 sin frase.

**El tope de la tanda es 1,20 $ por tema y esta corrida hizo 1,2187 $**, 0,0187 $ por encima. Se
siguió porque el **mínimo** de la previsión (0,72 $) cabía de sobra; con el resultado delante, la
regla se endureció para los temas siguientes (el máximo previsto tiene que caber). Ver
`DECISIONES-TOMADAS-EN-EL-OBJETIVO.md` (11-oct).
