# Informe de III.5 — Jakarta EE/Jakarta y .NET: arquitectura, persistencia, seguridad e interfaces · 13-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0036_claves_no_fiables`) · corrida del 13-oct 20:38–20:54.
Decimoquinto tema por valor de la tabla **vuelta a medir con la cuarentena puesta** (264 preguntas con
clave utilizable), **sin catálogo** antes de esta tanda. **PUBLICADO**: pasa las dos puertas del §2.3,
con la **mejor cobertura de la serie** (99,2 %) y el **coste más bajo por tema**.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **10**, por asunto dentro de sus tres epígrafes |
| Grupos situados por el enunciado (ensayo) | **253 de 258 = 98,1 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Techo medido de cobertura (`sin_materia_con_clave.py`) | **249/254 = 98,0 %** |
| Grupos y hechos sin materia al cerrar | **1 y 3** (una pregunta) |

Los 5 grupos que el ensayo no sitúa están leídos uno a uno: **4 son de C++** (`printf`, el calificador
`const`, los inicializadores y la herencia) y son de **III.2 —lenguajes de programación—**, no de este
tema, más una herramienta de .NET (`NSwag`) que el reparto situó por el texto de sus hechos. Van a la
bandeja del propietario con su motivo, y **no se lavan** dentro de un apartado que no existe.

## 2. La previsión y lo que costó

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 49 como mínimo y **85** como máximo | **80** (0 fallidas) |
| Coste | 0,33 $ como mínimo y **0,58 $** como máximo | **0,3078 $** |
| Tope decidido | tope de la corrida **2 $** · tope de tiempo **5.400 s** | **ninguno se activó** (17 minutos) |

**Es el tema más barato de la serie**: 80 llamadas a **0,00385 $** —precio de tema **técnico**, el de
IV.6 (0,00373 $) y no el de un normativo denso (0,0078–0,0083 $)—, con **473.600 de 657.579 tokens de
entrada en caché (72 %)** y 348.539 de salida (4.357 por llamada).

Y una cosa que conviene decir porque es la cara opuesta de lo que pasó con I.4, I.8 e I.7: aquí la
**cota de coste de `--prever` quedó por encima de lo real** (0,3078 $ frente al mínimo de 0,33 $). La
previsión usa **0,0068 $ por llamada** (la media de las cinco corridas medidas, con los normativos
dentro); un tema técnico cuesta **la mitad**, así que para él esa media es un **techo**, no un suelo.
Lo que acertó fue la cota de llamadas (80 frente a 49–85).

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 258 grupos · **265 preguntas** |
| Hechos | **528 guardados** (532 nuevos) → **437 en el plan** (91 repetidos agrupados) |
| Apartados | **10** · ninguno pasó del tope de 150 hechos (el mayor, 97) |
| Texto | 10 apartados · **12.253 palabras** de 21.120 (58,0 %) |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de III.5 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % (el doc pide 3 %) | **0,0 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 12.253 de 21.120 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **253/255 = 99,2 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 253/265 = 95,5 % | — |
| Hechos sin materia en el índice | 0 | **1 grupo / 3 hechos** (1 pregunta) | PASA |

La corrida **terminó entera**: 258 de 258 grupos comprobados, **247 cubiertos** (239 a la primera y 8
tras añadir material), **1 en conflicto** con la clave y **«sin contestar por los apuntes: 0»**.
`--limpiar-forma` (0 $) tocó **9 apartados** —los títulos, alineados con el catálogo— y la forma siguió
en PASA.

## 5. La bandeja del propietario

**12 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice la norma o el material) | 10 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 1 |
| `pregunta_ambigua` (no la sitúa ninguna materia del índice) | 1 |

## 6. La puerta de datos del §1, al cerrar (0 $)

**93 conjuntos medibles** (eran 90 al cerrar III.1), **12 en cuarentena · 8 dudosos · 81 sin poder
medir**, y **ningún conjunto cambió de veredicto**: las anclas de III.5 no movieron a nadie por encima
del 30 %. El denominador de la cobertura es **255 preguntas**, ya sin las de los conjuntos en
cuarentena.

## 7. Coste y gasto

| | |
|---|---|
| Coste medido | **0,3078 $** · 80 llamadas (0 fallidas) · 17 minutos · ningún tope activado |
| Previsión | 0,33–0,58 $ (la corrida salió **por debajo del mínimo**, y se dice por qué) |
| Gasto acumulado del objetivo | ≈ 14,46 $ antes de III.5 → **≈ 14,77 $** con III.5 |
