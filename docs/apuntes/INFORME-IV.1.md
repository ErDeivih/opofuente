# Informe de IV.1 — Administración del sistema operativo y software de base · 13-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0036_claves_no_fiables`) · corrida del 13-oct
21:54–22:12 (hora local). Decimoctavo tema por valor de la tabla **vuelta a medir hoy** con la
cuarentena puesta (**228** preguntas con clave utilizable), **sin catálogo** antes de esta tanda.
**PUBLICADO**: pasa las dos puertas con **220/224 = 98,2 %** de cobertura sobre clave utilizable.

> El encargo lo traía con **228** y a IV.9 con **232**; medidos hoy son **228** y **227**. La bajada
> de IV.9 son los conjuntos que la puerta de claves del §1 metió en cuarentena al cerrar IV.8
> (99 → 103 conjuntos medibles, 12 → 14 en cuarentena). Manda la medición del día, y con ella IV.1
> (228) va **antes** que IV.9 (227): la diferencia es de una pregunta, pero es la medida.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **9**, por asunto dentro de sus dos epígrafes (8 en IV.1.1 y 1 en IV.1.2) |
| Grupos situados por el enunciado (ensayo) | **223 de 229 = 97,4 %** |
| Techo medido de cobertura (`sin_materia_con_clave.py`) | **218/224 = 97,3 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **0 y 0** |

Los **6 grupos que el ensayo no sitúa** son, leídos uno a uno, de **otro tema** y no se lavan:
Kubernetes (2 preguntas, IV.3), la memoria caché L1 (II.1), la desnormalización en una base de datos
(III.1), el término *mashup* (III.8) y el documento ERS del ciclo de vida (III.9). Van a la bandeja
del propietario con su motivo.

**Y una lección de método, la misma que dejó IV.8**: la sonda de pertenencia por palabras
(`pertenencia_por_tema.py`) daba aquí un **32,8 % de grupos «sin vocabulario del tema»** y era
**falso**: eran las versiones con nombre de Debian y macOS, los sistemas de ficheros, APT, Ansible,
los directorios del sistema y los tipos de mantenimiento, todo de IV.1. La sonda **orienta**; el
ensayo del reparto **decide**. Es la segunda vez seguida que la sonda da un susto que no era.

**El techo se quedó corto, y a favor**: el índice situaba 218 de las 224 con clave utilizable, y la
corrida cerró en **220/224**. Los dos grupos que el enunciado no situaba los colocó el motor **por el
texto de sus hechos**, que es el camino que tiene desde I.1: no queda ni un grupo sin materia.

## 2. La previsión y lo que costó

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 44 como mínimo y **76** como máximo | **79** (0 fallidas), 3 más que la cota |
| Coste | 0,30 $ como mínimo y **0,52 $** como máximo | **0,3281 $** |
| Tope decidido | tope de dinero **2 $** · tope de tiempo **5.400 s** | **ninguno se activó** (33 minutos) |

**IV.1 es un tema técnico y se portó como tal**: **0,00415 $ por llamada**, entre los 0,0030–0,0045 $
de la serie técnica y a la mitad de un normativo denso. La cota de coste de `--prever` volvió a ser un
**techo** (usa 0,0068 $/llamada, la media con los normativos dentro): se quedó **0,19 $ por encima** de
lo que costó de verdad. La cota de **llamadas** se quedó corta por 3, que es lo que el **bucle de
huecos** añadió (24 grupos cubiertos «tras añadir»).

Consumo: 908.965 tokens de entrada, **724.480 de ellos en caché (79,7 %)**, y 319.605 de salida.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 229 grupos · **230 preguntas** |
| Hechos | **431 guardados** (432 nuevos, 10 con la clave señalada) → **331 en el plan** (100 repetidos agrupados) |
| Apartados | **9** · ninguno pasó del tope de 150 hechos |
| Texto | 10.153 palabras de 17.240 (58,9 %) · párrafos repetidos **0,6 %** |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de IV.1 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % (el doc pide 3 %) | **0,6 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 10.153 de 17.240 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **220/224 = 98,2 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 220/228 = 96,5 % | — |
| Hechos sin materia en el índice | 0 | **0** | PASA |

La corrida terminó entera: **229 de 229 grupos comprobados**, 221 cubiertos (197 a la primera y 24
tras añadir), 3 en conflicto con la clave y **1 «sin contestar por los apuntes»**.

`--limpiar-forma` (0 $) alineó **8 títulos** de apartado con los del catálogo. `--limpiar-puertos`
(0 $) no tuvo nada que hacer: este tema no tiene tabla de puertos, así que la marca `tabla_unica`
del catálogo **no se usó** — y se dice, porque una marca que no se usa no ha demostrado nada.

## 5. La bandeja del propietario

**8 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice el material) | 4 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 3 |
| `hueco_sin_material` (los apuntes no tienen el dato) | 1 |

## 6. La puerta de datos del §1, al cerrar (0 $)

**103 conjuntos medibles** (eran 99 al cerrar IV.8), **14 en cuarentena · 9 dudosos · 82 sin poder
medir**, y **ningún conjunto cambió de veredicto**.

## 7. Coste y gasto

| | |
|---|---|
| Coste medido | **0,3281 $** · 79 llamadas (0 fallidas) · 33 minutos · ningún tope activado |
| Previsión | 0,30–0,52 $ (llamadas 3 por encima del máximo; coste dentro del rango, por la parte baja) |
| Gasto acumulado del objetivo | ≈ 15,35 $ antes de IV.1 → **≈ 15,68 $** con IV.1 |

## 8. Lo que queda fuera, con el porqué

- los **6 grupos** que el enunciado no sitúa, listados en el §1: son de otros temas y están en la
  bandeja del propietario con su motivo;
- **I.7** (58,4 %), **I.4** (88,9 %), **I.8** (82,0 %) e **I.6** (72,5 %): los cuatro borradores
  siguen **sin reanudar**, con su cifra escrita y por el mismo motivo medido (su hueco es de material
  y de criterio sobre las claves, no de una corrida más);
- **III.4** sigue **sin escribir**: su banco es de otra materia en un 40 %, ya medido.
