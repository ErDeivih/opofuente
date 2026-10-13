# Informe de III.7 — Aplicaciones web, HTML/XML, navegadores y lenguajes de script · 13-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0036_claves_no_fiables`) · corrida del 13-oct 20:55–21:19.
Decimosexto tema por valor de la tabla **vuelta a medir con la cuarentena puesta** (268 preguntas con
clave utilizable), **sin catálogo** antes de esta tanda. **PUBLICADO**: pasa las dos puertas del §2.3.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **11**, por asunto dentro de sus cinco epígrafes |
| Grupos situados por el enunciado (ensayo) | **226 de 248 = 91,1 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Techo medido de cobertura (`sin_materia_con_clave.py`) | **247/268 = 92,2 %** tras corregir el catálogo |
| Grupos y hechos sin materia al cerrar | **1 y 3** (una pregunta) |

**Este es el banco más heterogéneo de la tanda y el único donde el ensayo cambió el catálogo.** La
sonda de pertenencia (`pertenencia_por_tema.py`) dijo que 71,0 % de sus grupos hablan de su materia y
8,5 % de las dos, pero el 14,9 % que no reconocía su vocabulario era, leído, **mayoritariamente de
otros temas**: MySQL y modelo relacional (III.3 y III.4), `iptables` (IV.9), firma electrónica y FNMT
(I.6), archivística (III.8), textos legales, Exchange (IV.3) y ofimática. Con el primer catálogo el
techo medido quedaba en **89,2 %**, por debajo del listón.

Se corrigió **el catálogo, no el banco**: la pregunta de OWASP sobre la prevención del XSS es un grupo
de **8 preguntas** —el mayor de los que quedaban fuera— y es contenido del **desarrollo web**, así que
entra en el apartado de desarrollo web en servidor, con su resumen diciéndolo, y el techo sube a
**92,2 %**. Lo que sigue fuera son preguntas de otros temas y **no se lava**: van a la bandeja con su
motivo (21 preguntas con clave utilizable, de las que 8 eran de enunciados genéricos que el reparto
acabó situando por el texto de sus hechos).

## 2. La previsión y lo que costó

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 47 como mínimo y **81** como máximo | **103** (0 fallidas) |
| Coste | 0,32 $ como mínimo y **0,55 $** como máximo | **0,3990 $** |
| Tope decidido | tope de la corrida **2 $** · tope de tiempo **5.400 s** | **ninguno se activó** (24 minutos) |

La cota de **llamadas** se quedó corta por 22 (el bucle de huecos añadió 12 grupos y volvió a
comprobar), pero la de **coste** no se cruzó: 103 llamadas a **0,00387 $**, el precio de un tema
**técnico**. Es la tercera corrida seguida que se sale del máximo de llamadas y aun así entra en el
rango de dinero, y la explicación es la misma: `--prever` valora la llamada a **0,0068 $** (la media
con los normativos dentro) y un tema técnico cuesta la mitad.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 244 grupos · **272 preguntas** (eran 248 y 280: la puerta de claves puso dos conjuntos más en cuarentena al cerrar) |
| Hechos | **528 guardados** (536 nuevos) → **455 en el plan** (73 repetidos agrupados) |
| Apartados | **11** · ninguno pasó del tope de 150 hechos (el mayor, 93) |
| Texto | 11 apartados · **14.726 palabras** de 21.120 (69,7 %) |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de III.7 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % (el doc pide 3 %) | **0,9 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 14.726 de 21.120 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **218/233 = 93,6 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 218/261 = 83,5 % | — |
| Hechos sin materia en el índice | 0 | **1 grupo / 3 hechos** (1 pregunta) | PASA |

La corrida **terminó entera**: 248 de 248 grupos comprobados, **208 cubiertos** (196 a la primera y
**12 tras añadir material**) y 6 en conflicto con la clave. `--limpiar-forma` (0 $) tocó **10
apartados** —los títulos, alineados con el catálogo— y la forma siguió en PASA.

**Dos cifras para el mismo tema, y las dos se dicen**: la corrida cerró en **220/240 = 91,7 %** y, una
vez pasada la puerta de claves del §1 (que puso dos conjuntos más en cuarentena), el mismo tema mide
**218/233 = 93,6 %**: sus preguntas salieron del denominador solas.

## 5. La bandeja del propietario

**41 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice la norma o el material) | 26 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 6 |
| `hueco_sin_material` (los apuntes no tienen el dato) | 6 |
| `pregunta_ambigua` (no la sitúa ninguna materia del índice) | 3 |

## 6. La puerta de datos del §1, al cerrar (0 $)

**97 conjuntos medibles** (eran 93 al cerrar III.5), **14 en cuarentena · 9 dudosos · 79 sin poder
medir**, con **cuatro cambios de veredicto** auditados: pasan a `no_fiable`
`TAI_ejer_1_promo_AGE_2022` (8/15 = 53,3 %) y `2022_diccionario-concepto-terminos-AE` (8/25 = 32,0 %),
y a `dudosa` `TAI_ejer_sol_libre_AGE_2006` (10/52 = 19,2 %) y `Exámenes TAI - Test GSI (v2024)`
(68/429 = 15,9 %). Es la puerta entrando sola al cruzar el umbral, que es lo que el §1 pide de ella.

## 7. Coste y gasto

| | |
|---|---|
| Coste medido | **0,3990 $** · 103 llamadas (0 fallidas) · 24 minutos · ningún tope activado |
| Previsión | 0,32–0,55 $ (dentro del rango, por el medio) |
| Gasto acumulado del objetivo | ≈ 14,77 $ antes de III.7 → **≈ 15,17 $** con III.7 |
