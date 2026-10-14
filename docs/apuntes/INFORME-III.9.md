# Informe de III.9 — Repositorios, metodologías, pruebas y control de versiones · 13-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0036_claves_no_fiables`) · corrida del 13-oct 18:56–19:25.
Duodécimo tema por valor de la tabla del §4d (374 preguntas con clave utilizable), **sin catálogo**
antes de esta tanda. **PUBLICADO**: pasa las dos puertas del §2.3.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **13**, por asunto dentro de sus seis epígrafes |
| Grupos situados por el enunciado (ensayo) | **312 de 346 = 90,2 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **7 grupos y 15 hechos** (→ bandeja) |

Los 34 grupos que el ensayo no sitúa son de otro tema (Ruby on Rails, los órganos superiores de un
ministerio, claves de confidencialidad del bloque IV) o fragmentos sin sujeto; el reparto situó por sus
hechos la mayoría y al cerrar quedaron **7**.

## 2. La previsión y lo que costó

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 63 como mínimo y **108** como máximo | **111** (0 fallidas) |
| Coste | 0,43 $ como mínimo y **0,73 $** como máximo | **0,4961 $** |
| Tope decidido (cota de arriba × 4/3) | | **0,97 $** — **no se activó** |

La corrida entró **por el medio del rango previsto** y muy por debajo del tope: 111 llamadas a
**0,00447 $**, precio de tema **técnico** (hechos cortos y repetidos: 175 de 686 agrupados). Devolvió
608.311 tokens de salida (5.480 por llamada) y trajo 556.160 de los 874.331 de entrada en caché. **El
tope de tiempo no llegó a activarse**: terminó sola con las **346 de 346** comprobaciones hechas.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 346 grupos · **379 preguntas** |
| Hechos | **686 guardados** → **511 en el plan** (175 repetidos agrupados) |
| Apartados | **13** · ninguno pasó del tope de 150 hechos |
| Texto | 13 apartados · 107.042 caracteres · **16.960 palabras** de 27.440 (61,8 %) |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de III.9 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % (el doc pide 3 %) | **0,4 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 16.960 de 27.440 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **324/337 = 96,1 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 324/369 = 87,8 % | — |
| Hechos sin materia en el índice | 0 | 15 (en 7 grupos) | PASA (van a la bandeja) |

`--limpiar-forma` (0 $) tocó **13 apartados** y la forma siguió en PASA. La corrida terminó entera:
**346 de 346** grupos comprobados, 310 cubiertos (284 a la primera y **26 tras añadir** material en el
bucle de huecos — **el mejor de la serie**, por delante de los 24 de I.5 y los 20 de IV.2) y
**«sin contestar por los apuntes: 0»**: no hay ni una pregunta cuyo dato no esté en el texto.

## 5. La bandeja del propietario

**44 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice la norma o el material) | 31 |
| `pregunta_ambigua` | 8 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 5 |

## 6. La puerta de datos del §1, al cerrar (0 $)

**85 conjuntos medibles** (eran 81 al cerrar I.5), **12 en cuarentena · 8 dudosos · 81 sin poder
medir**: otro conjunto cruzó su umbral al recibir las anclas nuevas de III.9 y entró en cuarentena
solo. El denominador de la cobertura pasó de 341 a **337** preguntas por eso.

## 7. Coste y gasto

| | |
|---|---|
| Coste medido | **0,4961 $** · 111 llamadas (0 fallidas) · 29 minutos · tope no activado |
| Previsión | 0,43–0,73 $ (dentro del rango) |
| Gasto acumulado del objetivo | ≈ 13,22 $ antes de III.9 → **≈ 13,72 $** con III.9 |
