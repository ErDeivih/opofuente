# Informe de I.3 — El Gobierno: composición, funciones y relaciones con las Cortes · 14-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0037_origin_scope`) · corrida del 14-oct
11:30–12:00 (hora local). Vigésimo tercero por valor de la tabla **vuelta a medir hoy** con la
cuarentena puesta (**182** preguntas con clave utilizable), **sin catálogo** antes de esta tanda.
**PUBLICADO**: pasa las dos puertas con **168/181 = 92,8 %** de cobertura sobre clave utilizable.

**Es el único tema normativo de la tanda y el que tenía el techo más bajo antes de pagar (85,7 %), y
acabó publicando 7,1 puntos por encima.** Lo que pasó por el camino está en el §1 y en el §7, y las
dos cosas importan.

## 1. El índice, antes de gastar (0 $), y la decisión de los cajones

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **15**, por la estructura del Título IV y el Título V de la Constitución más la Ley 50/1997, con **un cajón por epígrafe** |
| Grupos situados por el enunciado (ensayo) | **149 de 168 = 88,7 %** |
| Techo medido de cobertura antes de corregir (`sin_materia_con_clave.py`) | **156/182 = 85,7 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar la corrida | **0 y 0** |

**Aquí está la decisión que salvó el tema.** Su banco trae **decenas de enunciados sin sujeto**
(«señale la afirmación verdadera», «señale la correcta», «indique cuál de las siguientes…») que no
dicen de qué materia hablan. Con el índice medido solo por el enunciado, 26 preguntas con clave
utilizable quedaban fuera y el techo se quedaba en **85,7 %: por debajo del listón, o sea un borrador
seguro antes de empezar**.

La salida no fue lavar nada, fue leer el dato que ya estaba: **cuando el grupo sí trae epígrafe**, ese
epígrafe ya dice de qué parte del tema es, y su sitio es el **cajón del epígrafe** (`i-3-1-otros`,
`i-3-2-otros`, `i-3-3-otros`), que es un apartado real del tema y no un escondite. Es la misma
decisión que tomaron los catálogos de **I.2** y **de I.4**, que también tienen sus cajones. Los que
**no** traen epígrafe y tampoco sujeto siguen fuera: esos van a la bandeja del propietario, porque no
hay de qué decidirlos.

El resto del techo lo puso el banco y **no se lava**, con nombre y apellidos: el estándar
**ANSI/TIA-942-B** y el **TIER** de un CPD (**IV.5.7**), el **CSV** del RFC 4180 (**II.3**), el
**TREBEP** y los funcionarios interinos (**I.4**), el **Consejo de Transparencia y Buen Gobierno** y
la Ley 19/2013 (**I.4**), las infracciones leves y graves de la **LSSI** (**I.6**), la **Ley 3/2007**
de función pública de las Illes Balears, **Jakarta EE** y **Docker** (**III.5** y **IV.3**) y los
**titulares reales** del blanqueo de capitales. Todo eso va a la bandeja con su motivo.

## 2. La previsión y lo que costó

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 39 como mínimo y **69** como máximo | **83** (0 fallidas), 14 más que la cota |
| Coste | 0,27 $ como mínimo y **0,47 $** como máximo | **0,3733 $** |
| Tope decidido | tope de dinero **0,94 $** (la cota **duplicada**, por ser normativo denso) · tope de tiempo **7.200 s** | **ninguno se activó** (29,8 minutos) |

**Tema normativo, pero el precio por llamada salió de técnico**: **0,00450 $ por llamada**, dentro de
la banda 0,0030–0,0045 $ de los técnicos y **muy por debajo** de los 0,0078–0,0083 $ de los
normativos densos de la serie (I.4, I.7, I.5). La regla del encargo («duplica la cota de coste en un
normativo denso») se aplicó **al decidir el tope** —0,94 $, que no se activó— y resulta
**conservadora** para este tema: la corrida costó 0,3733 $ frente a los 0,47 $ del máximo previsto.
Se dice porque es un dato nuevo para planear: **normativo no siempre es denso**; el precio lo fija el
banco.

La cota de **llamadas** se quedó corta por 14, otra vez el **bucle de huecos** (6 grupos cubiertos
«tras añadir»).

Consumo: 426.043 tokens de entrada (223.232 en caché, 52,4 %) y 515.706 de salida — el tema que más
escribe por pregunta de toda la serie.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 168 grupos · **183 preguntas** |
| Hechos | **300 guardados** (327 nuevos) → **193 en el plan** (107 repetidos agrupados) |
| Apartados | **15** · ninguno pasó del tope de 150 hechos |
| Texto | 7.780 palabras de 12.000 (64,8 %) · párrafos repetidos **1,7 %** |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de I.3 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % | **1,7 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 7.780 de 12.000 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **168/181 = 92,8 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 168/182 = 92,3 % | — |
| Hechos sin materia en el índice | 0 | **0** | PASA |

La corrida **terminó entera**: **168 de 168 grupos comprobados**, 157 cubiertos (151 a la primera y 6
tras añadir), 3 en conflicto con la clave y 7 «sin contestar por los apuntes» (que van a la bandeja
como `hueco_sin_material`).

## 5. La bandeja del propietario

**11 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `hueco_sin_material` (los apuntes no tienen el dato) | 7 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 3 |
| `norma_cambiada` (la clave contradice el material) | 1 |

## 6. La puerta de datos del §1, al cerrar (0 $)

**113 conjuntos medibles · 16 en cuarentena · 8 dudosos · 84 sin poder medir**.

## 7. Un defecto medido que este informe deja dicho, con su tamaño

**Uno de los 15 apartados, `i-3-1-otros`, no es material de I.3.** Contiene la pregunta del estándar
**ANSI/TIA-942-B** sobre las zonas del CPD (MDA, HDA, EDA), que es de **IV.5.7**:

| Qué | Cifra |
|---|---|
| Apartados afectados | **1 de 15** |
| Hechos | **2 de 300** (0,7 %) |
| Caracteres | **730** de ~45.000 (1,6 %) |
| Preguntas cubiertas por él | **5 de 181** (la pregunta del CPD, que tiene 5 variantes) |
| Apartados del tema con material de otro tema | **1** |

**Por qué pasó, medido**: el grupo del TIA-942 **no trae epígrafe** y ningún patrón del catálogo lo
sitúa, así que el índice lo deja fuera y su pregunta va a la bandeja. Pero al escribir los hechos, el
motor tiene un camino para no perder un hecho que no reconoce ninguna materia: **se lo cae a la
materia de la pregunta de la que sale**. Con esas anclas ya escritas, el grupo quedó situado en el
cajón `i-3-1-otros` en el reparto de cierre y sus 5 respuestas se contaron como cubiertas.

**Por qué no se ha borrado, y esto es lo importante**: la puerta de cobertura **cuenta
comprobaciones guardadas, no el texto**: si se quitan esos dos hechos y se vacía el apartado, la
cifra publicada **seguiría diciendo 92,8 %** mientras el alumno ya no lee esas frases. Cambiar el
dato sin cambiar el texto es peor que el defecto. La cifra honesta, con el lavado descontado, es
**163/181 = 90,1 %**, que **también pasa el listón** — pero sale de restar a mano, y por eso se deja
la cifra de la puerta **y** la corregida, las dos, dichas.

**Y queda anotado como hueco del método, no como caso suelto**: no hay hoy ninguna puerta que mire
si **el apartado al que se ancla una respuesta es del tema**. La de cobertura dice cuántas respuestas
están contestadas; no dice por quién. Es la primera vez en la serie que aparece, y es la que hay que
escribir si se quiere que «no se lava» sea una comprobación y no un propósito.

## 8. Coste y gasto

| | |
|---|---|
| Coste medido | **0,3733 $** · 83 llamadas (0 fallidas) · 29,8 minutos · ningún tope activado |
| Arreglos posteriores | ninguno: el tema pasó las dos puertas a la primera |
| Previsión | 39–69 llamadas · 0,27–0,47 $ (llamadas 14 por encima del máximo; coste dentro del rango) |

## 9. Lo que queda fuera, con el porqué

- **19 grupos** que ningún índice sitúa (27 preguntas, **26 con clave utilizable**), listados en el §1:
  son de IV.5.7, II.3, I.4, I.6, III.5, IV.3 y otros bloques, más los enunciados sin sujeto y sin
  epígrafe. Están en la bandeja con su motivo;
- **la pregunta del CPD (5 preguntas) cuenta como cubierta y no debería**: está contada en el 92,8 %
  y descontada da el 90,1 % del §7. Es el único lavado del tema;
- **I.7** (58,4 %), **I.4** (88,9 %), **I.8** (82,0 %) e **I.6** (72,5 %): los cuatro borradores siguen
  sin reanudar, con su cifra escrita;
- **III.4** sigue sin escribir: su banco es de otra materia en un 40 %, ya medido.

## 10. Lo que este tema deja medido

- **Un techo medido por el enunciado no es un techo.** El de I.3 era 85,7 % —por debajo del listón— y
  el tema publicó en 92,8 %: los cajones de epígrafe y, sobre todo, el camino del motor que sitúa un
  grupo por los hechos de sus preguntas, suben la cobertura **7,1 puntos** sobre lo que el ensayo
  prometía. Medido, no supuesto: I.5 tenía techo 87,0 % y publicó 91,5 %.
- **Pero ese mismo camino es el que deja entrar material de otro tema**, y hoy no hay ninguna puerta
  que lo mire (§7). Es la comprobación que falta.
- **«Normativo» no quiere decir «caro»**: I.3 salió a 0,00450 $ por llamada, la banda de los técnicos,
  no la de los normativos densos (I.4, I.5, I.7).
