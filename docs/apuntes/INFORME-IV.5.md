# Informe de IV.5 — Seguridad de los sistemas de información · 13-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0036_claves_no_fiables`) · corrida del 13-oct 17:04–17:46.
Décimo tema por valor de la tabla del §4d (395 preguntas con clave utilizable), **sin catálogo** antes de
esta tanda. **PUBLICADO**: pasa las dos puertas del §2.3.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **16**, por asunto dentro de sus nueve epígrafes |
| Grupos situados por el enunciado (ensayo) | **381 de 387 = 98,4 %** — el mejor encaje de la tanda |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **0 y 0** |

Los 6 grupos que el ensayo no sitúa son contenido del tema con el enunciado truncado (descripciones de
herramientas del CCN, «el lema de Kerckchoffs», «un tipo de SAl»), y el reparto los situó por el texto de
sus hechos: al cerrar **no queda ni un grupo sin materia**.

## 2. La previsión y lo que costó

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 75 como mínimo y **130** como máximo | **125** (0 fallidas) |
| Coste | 0,51 $ como mínimo y **0,88 $** como máximo | **0,5452 $** |
| Tope decidido (cota de arriba × 4/3) | | **1,17 $** — **no se activó** |

La corrida entró **por debajo del mínimo previsto**: 125 llamadas a **0,00436 $** cada una, la mitad que
un normativo denso. Es lo que la serie tiene medido: un tema **técnico**, con hechos cortos y muy
repetidos, sale bastante más barato. Devolvió 697.018 tokens de salida (5.576 por llamada) y trajo
508.672 de los 846.375 de entrada en caché. **El tope de tiempo no llegó a activarse**: la corrida
terminó sola, con las 387 comprobaciones hechas.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 387 grupos · **402 preguntas** |
| Hechos | **740 guardados** → **633 en el plan** (107 repetidos agrupados) |
| Apartados | **16** · ninguno pasó del tope de 150 hechos |
| Texto | 16 apartados · **19.627 palabras** de 29.600 (66,3 %) |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de IV.5 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % (el doc pide 3 %) | **0,3 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 19.627 de 29.600 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **364/374 = 97,3 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 364/392 = 92,9 % | — |
| Hechos sin materia en el índice | 0 | **0** | PASA |

`--limpiar-forma` (0 $) tocó **15 apartados** y la forma siguió en PASA. **La corrida terminó entera**:
387 de 387 grupos comprobados, 361 cubiertos (349 a la primera y 12 tras añadir material en el bucle de
huecos).

## 5. La bandeja del propietario

**26 incidencias**, contadas en el informe y en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice la norma o el material) | 16 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 6 |
| `hueco_sin_material` (los apuntes no tienen el dato) | 4 |

Y las 399 anclas del tema: **349 cubiertas a la primera, 12 tras añadir, 6 en conflicto, 4 sin
contestar**.

## 6. La puerta de datos del §1, al cerrar (0 $)

**71 conjuntos medibles** (eran 65 al cerrar I.7), **11 en cuarentena · 7 dudosos · 85 sin poder
medir**, y **1 cambio de veredicto**, con su evento de auditoría:

| conjunto | antes | ahora |
|---|---|---|
| `PreparaTAI AGE-2026…` (respuesta en el material) | fiable | **no_fiable** (5/15 = 33,3 %) |

Es la puerta entrando **sola** en cuanto las anclas nuevas de IV.5 le dieron las 15 comprobaciones que
le faltaban para poder medirse. Sus preguntas salen del denominador de la cobertura (402 → 399
preguntas) y de los tests.

## 7. Coste y gasto

| | |
|---|---|
| Coste medido | **0,5452 $** · 125 llamadas (0 fallidas) · 42 minutos · sin tope activado |
| Previsión | 0,51–0,88 $ (salió por debajo del mínimo) |
| Gasto acumulado del objetivo | ≈ 11,77 $ antes de IV.5 → **≈ 12,32 $** con IV.5 |
