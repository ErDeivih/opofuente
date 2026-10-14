# Informe de III.3 — Lenguajes de interrogación, ANSI SQL, procedimientos y disparadores · 14-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0037_origin_scope`) · corrida del 14-oct
10:56–11:10 (hora local). Vigésimo primero por valor de la tabla **vuelta a medir hoy** con la
cuarentena puesta (**201** preguntas con clave utilizable), **sin catálogo** antes de esta tanda.
**PUBLICADO**: pasa las dos puertas con **191/208 = 91,8 %** de cobertura sobre clave utilizable.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **14**, por asunto dentro de sus cuatro epígrafes |
| Grupos situados por el enunciado (ensayo) | **176 de 181 = 97,2 %** |
| Techo medido de cobertura (`sin_materia_con_clave.py`) | **188/201 = 93,5 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **5 y 11** |

Los cinco grupos que ningún índice sitúa son **de otro tema, leídos uno a uno**, y **13 de sus
preguntas tienen clave utilizable**: el estándar **ANSI/TIA-942-B** de las zonas de un CPD y el
**TIER** de un CPD (**IV.5.7**), el formato de imagen **JPG** (**II.3.4**), el **sistema de ficheros
de un CD-ROM** (**II.3.2**) y el **cable de par trenzado** con su estándar de extremos (**IV.10.3**).
No se lavan: van a la bandeja del propietario con su motivo.

**Dos correcciones que el ensayo hizo antes de pagar** (0 $, y son la lección del tema): el patrón
`\bansi\b` y el `\biso\b` sueltos se llevaban al apartado del **estándar SQL** tres grupos que solo
decían «estándar ANSI/TIA-942», «ISO 9660» y «estándar de extremos del cable»; y la palabra
**`estándar`** en los `patrones_debiles` del mismo apartado barría cualquier enunciado que la
mencionara. Se pidió el estándar por su nombre completo (`ansi sql`, `estándar sql`, `iso 9075`) y
`estándar` salió de los débiles. Sin eso, tres preguntas de otros temas habrían acabado respondidas
por los apuntes del tema.

## 2. La previsión y lo que costó

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 42 como mínimo y **74** como máximo | **83** (0 fallidas), 9 más que la cota |
| Coste | 0,29 $ como mínimo y **0,50 $** como máximo | **0,2432 $** |
| Tope decidido | tope de dinero **2 $** · tope de tiempo **6.000 s** | **ninguno se activó** (13,8 minutos) |

**Tema técnico, precio de técnico, y el más barato del proyecto**: **0,00293 $ por llamada**, por
debajo de los 0,00299 $ de IV.8. La cota de coste de `--prever` volvió a ser un **techo** (0,50 $
frente a 0,2432 $ reales, la mitad). La cota de **llamadas** se quedó corta otra vez por el **bucle de
huecos** (7 grupos cubiertos «tras añadir»).

Consumo: 745.075 tokens de entrada (570.112 en caché, **76,5 %**, el mejor aprovechamiento de la
serie) y 219.078 de salida.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 181 grupos · **200 preguntas** |
| Hechos | **382 guardados** (382 nuevos, 10 con la clave señalada) → **322 en el plan** (60 agrupados) |
| Apartados | **14** · ninguno pasó del tope de 150 hechos |
| Texto | 9.408 palabras de 15.280 (61,6 %) · párrafos repetidos **0,7 %** |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de III.3 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % | **0,7 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 9.408 de 15.280 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **191/208 = 91,8 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 191/213 = 89,7 % | — |
| Hechos sin materia en el índice | 0 | 5 grupos y 11 hechos con su motivo | — |

La corrida **terminó entera**: **181 de 181 grupos comprobados**, 174 cubiertos (167 a la primera y
7 tras añadir), 3 en conflicto con la clave y **0 «sin contestar por los apuntes»**.

**La cobertura se mide sobre 208 y no sobre 201, y se dice**: al cerrar el tema, sus propias anclas
dieron las comprobaciones que le faltaban a un conjunto y la puerta de claves lo midió por primera
vez. Es el comportamiento documentado (el denominador se mueve solo), y por eso van las dos cifras.

## 5. La bandeja del propietario

**20 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `pregunta_ambigua` (sin clave con la que comprobar) | 13 |
| `norma_cambiada` (la clave contradice el material) | 4 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 3 |

## 6. La puerta de datos del §1, al cerrar (0 $)

**110 conjuntos medibles · 16 en cuarentena · 8 dudosos · 82 sin poder medir**. Es el cierre con más
conjuntos medibles de la tanda hasta aquí.

## 7. Coste y gasto

| | |
|---|---|
| Coste medido | **0,2432 $** · 83 llamadas (0 fallidas) · 13,8 minutos · ningún tope activado |
| Arreglos posteriores | ninguno: el tema pasó las dos puertas a la primera |
| Previsión | 42–74 llamadas · 0,29–0,50 $ (llamadas 9 por encima del máximo; coste por debajo del mínimo) |

## 8. Lo que queda fuera, con el porqué

- los **5 grupos** que ningún índice sitúa (13 preguntas con clave utilizable), listados en el §1: son
  de IV.5.7, II.3 y IV.10, están en la bandeja con su motivo y son los que ponen el techo del 93,5 %;
- **I.7** (58,4 %), **I.4** (88,9 %), **I.8** (82,0 %) e **I.6** (72,5 %): los cuatro borradores siguen
  sin reanudar, con su cifra escrita;
- **III.4** sigue sin escribir: su banco es de otra materia en un 40 %, ya medido.

## 9. Lo que este tema deja medido

- El **precio por llamada más bajo del proyecto** (0,00293 $) y el mejor aprovechamiento de caché
  (76,5 %): el banco de SQL repite vocabulario hasta el punto de que 570.112 de 745.075 tokens de
  entrada salen de caché.
- **Dos patrones genéricos (`ansi`, `iso`) y una palabra en los débiles (`estándar`) bastan para que
  tres preguntas de otros temas acaben dentro del tema.** El ensayo los cazó a 0 $; sin él, habrían
  viajado hasta la corrida.
