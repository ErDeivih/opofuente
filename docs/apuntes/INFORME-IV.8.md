# Informe de IV.8 — Internet: arquitectura, evolución, servicios y HTTP/SSL · 13-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0036_claves_no_fiables`) · corrida del 13-oct 21:20–21:35.
Decimoséptimo tema por valor de la tabla vuelta a medir con la cuarentena puesta (232 preguntas con
clave utilizable), **sin catálogo** antes de esta tanda. **PUBLICADO**: pasa las dos puertas, con la
**cobertura más alta de la serie** (99,1 %) y **el coste más bajo del objetivo** (0,1885 $).

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **8**, por asunto dentro de sus cuatro epígrafes (el plan salió con 9: una materia pasó de 150 hechos y se partió) |
| Grupos situados por el enunciado (ensayo) | **206 de 225 = 91,6 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Techo medido de cobertura (`sin_materia_con_clave.py`) | **213/232 = 91,8 %** |
| Grupos y hechos sin materia al cerrar | **0 y 0** |

Los 19 grupos que el ensayo no sitúa son, leídos, de su materia con el enunciado corto y se situaron
por el texto de sus hechos: **no queda ni un grupo sin materia**.

**Y una lección de método que se dice**: la sonda de pertenencia por palabras (`pertenencia_por_tema.py`)
daba aquí un **55,6 %** de grupos «sin vocabulario del tema», y era **falso** —eran los códigos de
estado de HTTP, el SSL, los puertos y el DNS, todo del tema—; en III.5 dio un 28,7 % «sin vocabulario»
que también era material propio, y en III.7 un 14,9 % que **sí** era de otros temas. La sonda
**orienta**, el ensayo del reparto **decide**.

## 2. La previsión y lo que costó

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 41 como mínimo y **70** como máximo | **63** (0 fallidas) |
| Coste | 0,28 $ como mínimo y **0,48 $** como máximo | **0,1885 $** |
| Tope decidido | tope de la corrida **2 $** · tope de tiempo **5.400 s** | **ninguno se activó** (15 minutos) |

**Es el tema más barato del objetivo**: 63 llamadas a **0,00299 $** por llamada (por debajo del
0,00373 $ de IV.6, que era el mínimo de la serie), con 237.824 de 381.384 tokens de entrada en caché
(62 %) y 218.819 de salida. Las llamadas entraron en el rango previsto y el dinero se quedó **por
debajo del mínimo**, otra vez porque `--prever` valora la llamada a 0,0068 $ (la media con los
normativos dentro) y un tema técnico cuesta menos de la mitad.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 224 grupos · **232 preguntas** |
| Hechos | **426 guardados** (430 nuevos) → **344 en el plan** (82 repetidos agrupados) |
| Apartados | **9** (una materia partida en 150 + 1) · ninguno pasó del tope de 150 hechos |
| Texto | 9 apartados · **9.541 palabras** de 17.040 (56,0 %) |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de IV.8 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % (el doc pide 3 %) | **0,0 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 9.541 de 17.040 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **221/223 = 99,1 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 221/231 = 95,7 % | — |
| Hechos sin materia en el índice | 0 | **0** | PASA |

La corrida terminó entera: 224 de 224 grupos comprobados, 214 cubiertos (213 a la primera y 1 tras
añadir) y **«sin contestar por los apuntes: 0»**.

### Y una reparación de forma que costó 0 $, porque la corrida dejó el tema sin publicar

La corrida cerró con la **forma en NO PASA**: `la tabla de puertos de servicios-de-internet no está
partida por familias`. La causa está medida: la limpieza de la tabla de puertos solo se aplica al
guardar si el **catálogo marca esa materia como `tabla_unica`**, y el catálogo de esta tanda no la
marcaba. Se añadió la marca (**un atributo del catálogo, sin tocar el motor**) y **`--limpiar-puertos`**
(0 $) partió la tabla por familias (2 confusiones que caen) y dejó la forma en **PASA**. `--limpiar-forma`
(0 $) alineó además 8 títulos con el catálogo. El tema se publicó después, con `--publicar` (0 $).

Es la tercera vez en la serie que **una reparación de forma de 0 $ evita volver a pagar una corrida**, y
la primera en que la causa es una marca del catálogo y no el texto.

## 5. La bandeja del propietario

**10 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice la norma o el material) | 8 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 2 |

## 6. La puerta de datos del §1, al cerrar (0 $)

**99 conjuntos medibles** (eran 97 al cerrar III.7), **14 en cuarentena · 9 dudosos · 79 sin poder
medir**, y **ningún conjunto cambió de veredicto**.

## 7. Coste y gasto

| | |
|---|---|
| Coste medido | **0,1885 $** · 63 llamadas (0 fallidas) · 15 minutos · ningún tope activado |
| Previsión | 0,28–0,48 $ (llamadas dentro del rango; coste por debajo del mínimo) |
| Gasto acumulado del objetivo | ≈ 15,17 $ antes de IV.8 → **≈ 15,35 $** con IV.8 |
