# Informe de I.4 — El EBEP, la Ley 19/2013 de transparencia y la Agenda 2030

**Tanda:** f15 · **Fecha de la corrida:** 11 oct 2026 · **Estado:** **borrador con su motivo**
(visible en el panel; no se publica)

Las cifras de este informe están **medidas** sobre la base real con `apuntes --medir` y
`apuntes --esquema`, no heredadas de la corrida que las escribió.

## 1. Hechos y apartados

| Qué | Antes de deduplicar | Después |
|---|---|---|
| Hechos | 1.056 | **721** (331 repetidos agrupados) |
| Apartados | — | **15** |
| Grupos de preguntas | 544 | 544 |
| Preguntas | 602 | 602 |

- 36 hechos no reconocen ninguna materia por sus palabras y van al apartado de la pregunta de la que
  salen (no se pierden).
- Revisión del índice: **PASA** · 15 apartados · 721 hechos · **2 grupos y 4 hechos sin materia**, que
  van a la bandeja con `Motivo.SIN_MATERIA_EN_EL_INDICE`.

## 2. Las puertas del §2.3

| Comprobación | Umbral | Medido | ¿Pasa? |
|---|---|---|---|
| Encabezados repetidos / misma cabecera | 0 | 0 | **sí** |
| Marcas internas visibles | 0 | 0 | **sí** |
| Tablas sin cabecera o columnas sin nombre | 0 | 0 | **sí** |
| Párrafos casi repetidos | ≤ 3 % | 4,2 % | **no** |
| Hechos fuera de su materia | ≤ 3 % | **no implementada** (aviso del §5 del estado) | — |
| Extensión | ≤ 40 palabras × hechos | 27.787 de 42.240 | **sí** |
| **Preguntas cubiertas** (clave utilizable) | **≥ 90 %** | **497/559 = 88,9 %** | **no** |
| Preguntas cubiertas (todas las que tienen clave) | — | 497/579 = 85,8 % | — |
| Conflictos de letra sin categorizar | 0 | 0 | **sí** |
| Copia literal de material no normativo | 0 párrafos | 0 | — |
| Afirmaciones sobre exámenes no calculadas | 0 | 0 | **sí** |

**La revisión de forma dice PASA en el informe de la corrida y aquí hay una fila que no, y el motivo
está medido**: la puerta del §2.3 y `revisar_apuntes` **no usan el mismo tope** en esa fila.

- **Párrafos casi repetidos**: el §2.3 pide **≤ 3 %**; el código lleva el tope al **5 %**
  (`MAX_PARRAFOS_REPETIDOS = 0.05`, y el propio comentario del código dice «el 5 % del informe del
  propietario»). Medido: **4,2 %**. Pasa la puerta del código y **no** la del documento.
- **Extensión**: aquí **sí** coinciden las dos, y se comprobó: el código mide contra los hechos
  **distintos** (`hechos_distintos(hechos)`), que es lo que dice el §2.3 («40 palabras × hechos
  distintos»). El informe enseña «de 42.240 (40 x 1.056)» porque la cabecera de la corrida usa el
  total; el hallazgo, que es el que decide, usa los distintos. Pasa por los dos lados.

No se toca ninguno de los dos listones: se deja escrito, que es lo que el §1.2 pide. **La de
cobertura es la que decide el borrador** y esa coincide en los dos sitios.

## 3. El motivo escrito del borrador

Contesta al **88,9 %** de las 559 preguntas con clave utilizable y el listón del §2.3 es el 90 %:
**le faltan 7 preguntas cubiertas**. De sus 544 grupos comprobables, **62 están sin cubrir**:

| Por qué no está cubierta | Cuántas preguntas |
|---|---|
| En conflicto: la frase está en los apuntes y sostiene otra opción que la clave | 31 |
| La clave contradice la norma o el material (marca del paso B) | 17 |
| No hay ninguna frase en los apuntes que la justifique | 3 |
| La pregunta no tiene clave con la que comprobarla | 3 |

**47 de sus 55 incidencias son de la clave, no del texto** (30 `clave_sospechosa` y 17
`norma_cambiada`), así que —como en I.6— buena parte del hueco es criterio del propietario sobre las
claves y no se arregla escribiendo más. Su forma pasa, así que el tema se queda visible en el panel
con esta frase y el texto sirve para estudiar.

## 4. Incidencias en la bandeja del propietario, por categoría

| Categoría | Cuántas |
|---|---|
| `clave_sospechosa` (los apuntes dicen otra letra, con la frase que lo demuestra) | 30 |
| `norma_cambiada` (la clave contradice la norma o el material) | 17 |
| `pregunta_ambigua` (sin clave con la que comprobar) | 5 |
| `hueco_sin_material` (los apuntes no tienen el dato) | 3 |
| **Total** | **55** |

## 5. Lo que costó, y lo que se dijo antes de pagarlo: aquí la previsión falló

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 96 como mínimo y 164 como máximo | **169** (0 fallidas) |
| Entrada | — | 1.963.599 tokens (1.259.648 de caché) |
| Salida | — | 1.946.630 tokens |
| Coste | 0,60 $ como mínimo y 1,03 $ como máximo | **1,4625 $** |

La cota de **llamadas** se quedó corta por 5 y la de **dinero por un 42 %**. La causa está medida:
I.4 devolvió **11.518 tokens de salida por llamada** donde la media de las tres corridas antiguas era
5.700, así que su llamada costó **0,00865 $** y no los 0,0063 $ de la tabla. Es un tema **normativo y
denso**, y ahí la cota de arriba de `--prever` es un suelo, no un techo. Con eso se corrigió
`COSTE_MEDIO_POR_LLAMADA_USD` (0,0068 $, la media de las **cinco** corridas medidas) y la regla de
decisión del tope por tema. Ver `DECISIONES-TOMADAS-EN-EL-OBJETIVO.md` (11-oct).
