# Informe de II.1 — Informática básica, representación de la información, arquitectura y componentes internos · 14-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0037_origin_scope`) · corrida del 14-oct
10:36–10:51 (hora local), **completada** el mismo día a las 12:20–12:33. Vigésimo tema por valor de
la tabla **vuelta a medir hoy** con la cuarentena puesta (**216** preguntas con clave utilizable),
**sin catálogo** antes de esta tanda. **PUBLICADO**: pasa las dos puertas con
**201/204 = 98,5 %** de cobertura sobre clave utilizable.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **14**, por asunto dentro de sus cinco epígrafes |
| Grupos situados por el enunciado (ensayo) | **206 de 214 = 96,3 %** |
| Techo medido de cobertura (`sin_materia_con_clave.py`) | **208/216 = 96,3 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **0 y 1** |

Ocho grupos no los sitúa ningún índice y **8 de sus 9 preguntas tienen clave utilizable**: cuatro son
enunciados que no dicen de qué hablan («señale la afirmación FALSA», «indique cuál es verdadera»), uno
es el patrón de diseño *Bridge* de GoF (**III.4**), otro la definición de algoritmo (**II.3**) y el
último, «cuál de las siguientes relaciones NO es correcta», tampoco nombra materia. Ninguno se lava:
van a la bandeja del propietario con su motivo.

## 2. La previsión y lo que costó, con la muerte del proceso dicha

| | `--prever` dijo | La primera corrida | La que la completó |
|---|---|---|---|
| Llamadas | 46 como mínimo y **81** como máximo | **no se pudo medir** | **26** (0 fallidas) |
| Coste | 0,31 $ como mínimo y **0,55 $** como máximo | **no se pudo medir** | **0,0577 $** |
| Tope decidido | tope de dinero **2 $** · tope de tiempo **6.000 s** | ninguno activado (14,3 min) | ninguno activado (13 min) |

**El coste de la primera corrida no se pudo medir, y se dice**: el proceso murió con
`STATUS_HEAP_CORRUPTION` (`exit=-1073740022`, `0xC0000374`) **después** de archivar la versión, y el
informe —que es donde viven las llamadas y el coste— se fue con la salida en búfer, que se perdió al
morir el proceso sin volcarla. Lo que sí quedó en la base: **447 hechos, 14 apartados y 207 de 214
grupos comprobados**. La estimación por el plan es la de `--prever`: 46–81 llamadas y, a precio de
tema técnico (**0,0030–0,0045 $** por llamada), **0,20–0,36 $**. Es una estimación, no una medida, y
va marcada como tal.

**Los arreglos que deja, aplicados al resto de la tanda**: `python -u` (sin búfer, para que un proceso
que muera a lo bruto no se lleve por delante lo ya escrito) y el reintento tras soltar el candado, que
es el remedio que el propio motor documenta. El candado quedó echado por el proceso muerto y hubo que
soltarlo: `apuntes_en_curso` en `app_metadata`.

**Y por qué se completó**: la corrida muerta dejó **7 grupos sin comprobar** y sus 7 preguntas con
clave utilizable **sin categoría de incidencia**, que es lo que el §2.3 pide para lo no cubierto. La
segunda corrida los comprobó **todos** (213 de 213), subió la cobertura de 96,6 % a **98,5 %** y dejó
las incidencias escritas. Costó **0,0577 $** y trece minutos, y convierte una cifra que era un suelo
en la cifra final.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 213 grupos · **221 preguntas** |
| Hechos | **447 guardados** → **365 en el plan** (82 repetidos agrupados) |
| Apartados | **14** · ninguno pasó del tope de 150 hechos |
| Texto | 11.673 palabras de 17.880 (65,3 %) · párrafos repetidos **1,1 %** |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de II.1 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % | **1,1 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 11.673 de 17.880 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **201/204 = 98,5 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 201/214 = 93,9 % | — |
| Hechos sin materia en el índice | 0 | 0 grupos y 1 hecho | PASA |

La corrida de cierre **terminó entera**: **213 de 213 grupos comprobados**, 200 cubiertos (197 a la
primera y 3 tras añadir), 2 en conflicto con la clave y 1 «sin contestar por los apuntes» (que va a la
bandeja como `hueco_sin_material`).

## 5. La bandeja del propietario

**13 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice el material) | 10 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 2 |
| `hueco_sin_material` (los apuntes no tienen el dato) | 1 |

**Y se dice cómo se llenó**: la corrida que murió dejó la bandeja **vacía**, porque es el final del
bucle de huecos el que la escribe y eso es justo lo que el proceso muerto no alcanzó. Se rellenó a
**0 $** por el **mismo camino auditado de la corrida** (`_paso_huecos` con un modelo nulo que no añade
nada, `rellenar_bandeja_utf8.py`): **0 → 10 incidencias**, todas de lo ya comprobado, ninguna
inventada. Es la regla 3 de la tanda: un hueco que no se ve es un hueco que no existe.

## 6. La puerta de datos del §1, al cerrar (0 $)

**116 conjuntos medibles · 17 en cuarentena · 8 dudosos · 83 sin poder medir**. Al cerrar II.1 la
cuarentena pasó de 14 a **15** conjuntos: entró `2022_diccionario-concepto-terminos-AE` (8/25 = 32,0 %).

## 7. Coste y gasto

| | |
|---|---|
| Coste medido (corrida de cierre) | **0,0577 $** · 26 llamadas (0 fallidas) · 13 minutos |
| Coste estimado de la corrida que murió | **0,20–0,36 $** (su informe se perdió con el proceso) |
| Total del tema | **≈0,26–0,42 $** (0,0577 $ medidos) |
| Arreglos posteriores | **0 $** (`--publicar` y el relleno de la bandeja) |
| Previsión | 46–81 llamadas · 0,31–0,55 $ |

## 8. Lo que queda fuera, con el porqué

- los **8 grupos** que ningún índice sitúa (9 preguntas, 8 con clave utilizable): cuatro son enunciados
  sin sujeto, uno es el patrón *Bridge* (III.4), uno la definición de algoritmo (II.3) y otro tampoco
  nombra materia. Están en la bandeja con su motivo;
- **I.7** (58,4 %), **I.4** (88,9 %), **I.8** (82,0 %) e **I.6** (72,5 %): los cuatro borradores siguen
  sin reanudar, con su cifra escrita;
- **III.4** sigue sin escribir: su banco es de otra materia en un 40 %, ya medido.

## 9. Lo que este tema deja medido

- El techo medido antes de pagar (96,3 %) quedó **por debajo** de la cobertura real (98,5 %): cuando el
  índice sitúa casi todo, el techo no es un techo.
- **Una corrida que muere a lo bruto no pierde el trabajo** (hechos, apartados y comprobaciones están
  escritos uno a uno) pero **sí pierde el informe**: de ahí `-u`, `--medir` para volver a medirlo a
  0 $ y `--publicar` para cerrar la puerta de cobertura sin llamar a nadie.
- **Un tema de este tamaño cabe en 14 minutos**, y completarlo cuando se corta cuesta 26 llamadas
  (0,0577 $) porque no rehace ni un hecho ni un apartado.
