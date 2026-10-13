# Informe de III.1 — Modelado de datos, modelo relacional y normalización · 13-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0036_claves_no_fiables`) · corrida del 13-oct 20:01–20:30.
Decimocuarto tema por valor de la tabla del §4d (302 preguntas con clave utilizable), **sin catálogo**
antes de esta tanda. **PUBLICADO**: pasa las dos puertas del §2.3, y con **la cobertura más alta de la
tanda**.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **8**, por asunto dentro de sus seis epígrafes |
| Grupos situados por el enunciado (ensayo) | **270 de 280 = 96,4 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **0 y 0** |

Los 10 grupos que el ensayo no sitúa son, leídos, de su materia con el enunciado corto («¿qué operador
devuelve columnas específicas, eliminando duplicados?», «¿cuál de las siguientes afirmaciones es
verdadera respecto a los dominios?»), y el reparto los situó por el texto de sus hechos: **no queda ni
un grupo sin materia**.

**Y el catálogo dice por qué no tiene apartados que otros temas sí tienen**: medido sobre su banco,
III.1 **no pregunta SQL, ni transacciones, ni disparadores, ni ACID** —eso es III.3, los lenguajes de
interrogación—, así que no hay apartado para ellos. Un apartado sin preguntas es un apunte que nadie
lee.

## 2. La previsión y lo que costó

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 49 como mínimo y **84** como máximo | **78** (0 fallidas) |
| Coste | 0,33 $ como mínimo y **0,57 $** como máximo | **0,3524 $** |
| Tope decidido (cota de arriba × 4/3) | | **0,76 $** — **no se activó** |

**Es el coste más bajo por tema de la serie** (con IV.6 pegado detrás): 78 llamadas a **0,00452 $**.
Tema **técnico** con hechos cortos y muy repetidos (195 de 607 agrupados por la deduplicación —casi un
tercio—) y con más de la mitad de la entrada en caché (241.536 de 455.187 tokens). Devolvió 473.461
tokens de salida (6.070 por llamada). **El tope de tiempo no llegó a activarse**: terminó sola con las
**280 de 280** comprobaciones hechas.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 280 grupos · **302 preguntas** |
| Hechos | **607 guardados** → **412 en el plan** (195 repetidos agrupados) |
| Apartados | **8** · ninguno pasó del tope de 150 hechos |
| Texto | 8 apartados · 82.446 caracteres · **13.151 palabras** de 24.280 (54,2 %) |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de III.1 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % (el doc pide 3 %) | **1,1 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 13.151 de 24.280 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **281/285 = 98,6 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 281/298 = 94,3 % | — |
| Hechos sin materia en el índice | 0 | **0** | PASA |

`--limpiar-forma` (0 $) tocó **7 apartados** y la forma siguió en PASA. La corrida terminó entera:
**280 de 280** grupos comprobados, 263 cubiertos (253 a la primera y 10 tras añadir material) y
**«sin contestar por los apuntes: 0»**.

**Es la mejor cobertura de la tanda** (98,6 %) con diferencia sobre las demás, y la explicación está en
los datos: es un tema de conceptos con vocabulario muy repetido, donde la deduplicación agrupa un tercio
de los hechos (195 de 607) y los apuntes caben con holgura en el tope de extensión.

## 5. La bandeja del propietario

**17 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice la norma o el material) | 13 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 4 |

## 6. La puerta de datos del §1, al cerrar (0 $)

**90 conjuntos medibles** (eran 87 al cerrar IV.6), **12 en cuarentena · 8 dudosos · 82 sin poder
medir**. El denominador de la cobertura de III.1 es 285 preguntas, ya sin las de los conjuntos en
cuarentena.

## 7. Coste y gasto

| | |
|---|---|
| Coste medido | **0,3524 $** · 78 llamadas (0 fallidas) · 29 minutos · tope no activado |
| Previsión | 0,33–0,57 $ (dentro del rango, por la parte baja) |
| Gasto acumulado del objetivo | ≈ 14,11 $ antes de III.1 → **≈ 14,46 $** con III.1 |
