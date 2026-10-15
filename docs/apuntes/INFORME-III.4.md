# Informe de III.4 — Diseño y programación orientada a objetos, patrones y UML · 15-oct-2026

**Rama `f21-temas-valor`** · base real (revisión **`0039_claves_derivadas`**). Corrida del 15-oct,
lanzada y **esperada dentro del turno**. Tema de la tanda de cierre, **con el banco arreglado antes de
escribirlo** por la ruta auditada (ver §1). **PUBLICADO**: pasa las dos puertas con
**244/247 = 98,8 %** de cobertura sobre clave utilizable, y con la **última medida** —la que manda— en
**243/246 = 98,8 %**.

## 1. Lo primero fue arreglar su banco, no escribirlo

El §5.2 del orden nuevo lo pedía así: **antes de escribir III.4, reclasificar a III.2 las preguntas que
no eran de su materia**. Se hizo por la ruta auditada (`QuestionService.assign_topic`, actor
`f28:reclasificacion-iii4`), con copia verificada antes, y **está contado con su cifra en `DECISIONES`
F28d**:

| | Preguntas |
|---|---|
| Se quedan en **III.4** | **275** |
| A **III.2** como decisión (`accepted`) | **92** |
| A **III.2** como propuesta (`provisional`, **la cola**) | **67** |
| **Total movido** | **159** |

**El «40 %» del documento era una estimación; lo medido es 36,6 %.** **Idempotencia probada**: la
segunda pasada encontró **0 que mover** y escribió **0**. **Antes/después medido contra la copia y
contra la base viva**: **III.2 pasó de 142 a 294 grupos** (147 → 299 preguntas) y **III.4 de 400 a 248**
(413 → 261). De 159 asignaciones salen 152 grupos: los otros 7 ya estaban en el destino.

## 2. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **15**, por asunto dentro de sus cuatro epígrafes |
| Grupos situados por el enunciado (ensayo, tras los arreglos) | **242 de 248 = 97,6 %** |
| Techo medido de cobertura (`sin_materia_con_clave.py`) | **254/260 = 97,7 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **2 grupos y 30 hechos**, con su motivo |

**Los 6 grupos que el índice no sitúa**: **cuatro son de III.2** (el método teórico para un calendario
de restricciones, dos de matrices declaradas en Java y el `switch-case`), **uno es de II.5** (el driver
JDBC que convierte las llamadas a la API de ODBC) y uno es un enunciado sin sujeto. **No se lavan**: se
quedan en la bandeja del propietario.

### Dos arreglos de 0 $ que valieron diez puntos de techo

1. **Faltaba un apartado entero.** El epígrafe oficial **III.4.3 es «Ventajas e inconvenientes»** y el
   catálogo no lo cubría, así que las preguntas de «¿cuál **NO** es una ventaja de la POO?» o «¿cuál es
   una característica clave de la orientación a objetos?» no tenían dónde caer: **era un fallo de
   lectura del enunciado, no de los patrones**, y se arregla añadiendo el apartado que faltaba.
2. **Un patrón que no casaba por la forma de la palabra**: los enunciados dicen «orientad**a** a
   objetos» y el patrón buscaba «orientaci**ón** a objetos». Las dos formas van ya en el patrón — y es
   la misma lección que la barra de `/etc/passwd`: **el patrón tiene que contar con cómo se escribe la
   pregunta, no con cómo la escribiría yo**.

**El techo pasó de 86,9 % a 97,7 %.** Es la cuarta vez en la serie que el ensayo previo ahorra una
corrida entera o un borrador.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 246 grupos · **255 preguntas** |
| Hechos | **530 guardados** → **363 en el plan** (167 repetidos agrupados) |
| Apartados | **15** |
| Texto | 11.221 palabras de 21.200 (52,9 %) · párrafos repetidos **0,0 %** |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de III.4 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % | **0,0 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 11.221 de 21.200 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **244/247 = 98,8 %** · última medida **243/246 = 98,8 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 244/260 = 93,8 % · última **243/257 = 94,6 %** | — |
| Hechos sin materia en el índice | 0 | 2 grupos y 30 hechos con su motivo | — |

La corrida **terminó entera**: **246 de 246 grupos comprobados**, 232 cubiertos (227 a la primera y 5
tras añadir), 1 en conflicto con la clave y **0 «sin contestar por los apuntes»**.

**Y se dan las dos medidas, que es la regla de hoy**: la de la corrida (**244/247**) y **la última**
(**243/246**), dos minutos después y sobre la misma base. **El denominador se mueve solo** mientras otros
bloques escriben. **Vale la última**, y las dos coinciden en el 98,8 %.

## 5. La bandeja del propietario

**16 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice el material) | 13 |
| `pregunta_ambigua` (sin clave con la que comprobar) | 2 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 1 |

## 6. Lo que costó, y la previsión

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 53 como mínimo y **93** como máximo | **83** (0 fallidas) |
| Coste | 0,36 $ como mínimo y **0,63 $** como máximo | **0,2437 $** — por debajo del mínimo |
| Precio por llamada | — | **0,00294 $** |
| Consumo | — | 590.410 tokens de entrada (398.208 en caché, 67,4 %) · 258.501 de salida |

**Quinta corrida seguida por debajo del mínimo previsto en dinero**, y la cota de llamadas otra vez
dentro de su horquilla. El coste del tema en total: **0,2437 $** de la corrida **más 0 $ de la
reclasificación** (la ruta auditada no llama al modelo), más el ensayo (0 $).

## 7. La puerta de datos del §1, al cerrar (0 $)

**124 conjuntos medibles · 17 en cuarentena · 11 dudosos · 83 sin poder medir.**

## 8. Lo que queda fuera, con el porqué

- los **6 grupos** que ningún índice sitúa: cuatro de **III.2**, uno de **II.5** y uno sin sujeto, en la
  bandeja con su motivo;
- las **67 propuestas** de la reclasificación: están en la **cola de revisión** del propietario y **no
  cuentan** en el diagnóstico mientras estén así;
- **I.8 (81,2 %), I.6 (71,4 %) e I.7 (57,1 %)**: los tres borradores que siguen, con su cifra y su causa
  medida (**0 grupos sin comprobar** en los tres: el hueco es material).

## 9. Lo que este tema deja medido

- **Arreglar el banco antes de escribir sale más barato que escribir sobre un banco sucio**: la
  reclasificación costó **0 $** (no llama al modelo) y dejó el tema en **98,8 %** con un catálogo que
  reclama todo lo que tiene.
- **Un apartado que falta no se nota hasta que se ensaya**: el epígrafe III.4.3 estaba en el enunciado
  del tema y el catálogo no lo cubría. Es el segundo caso de la serie —después de los cajones de I.3—
  en que **leer el enunciado entero** vale más que escribir patrones.
- **Y el patrón tiene que contar con la forma de la pregunta**: «orientada» frente a «orientación» es
  el mismo caso que la barra de `/etc/passwd` y que el punto de `802.11`. **Tres veces el mismo error
  de forma, y las tres cazadas a 0 $.**
