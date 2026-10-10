# Estado del objetivo largo (TAI: los 33 temas y la app de estudio)

**Autoridad:** `docs/GOAL-DEEPSEEK-TRABAJO-LARGO-2026-10.md` · **Presupuesto de API:** 40 $ · **Se
avisa cada 10 $** · Última actualización: **10 oct 2026 (tanda f10: los tres arreglos del motor, IV.7
publicado, I.6 en borrador e I.1 sin redactar)**.

## 1. Gasto de API, una línea por corrida

**Lo anterior a la tanda f10 no está medido**: este fichero no existía y ninguna otra fuente llevaba
la cuenta, así que **no se puede sumar** y no se suma. Lo que sigue es lo medido desde aquí, con los
tokens que devolvió cada llamada; el coste es la estimación con la tabla de precios del proyecto
(valle), no la factura.

| Fecha | Tema | Corrida | Llamadas | Entrada | Salida | Coste |
|---|---|---|---|---|---|---|
| 10-oct | IV.7 | 1.ª (reanudada sobre lo de F9) | 3 | 17.030 | 8.753 | 0,0078 $ |
| 10-oct | IV.7 | 2.ª: el reparto por materia y la tabla de puertos | 92 | 1.878.741 | 522.743 | 0,5955 $ |
| 10-oct | IV.7 | intento 2: los cuatro apartados que fallaban | 4 | 29.066 | 55.093 | 0,0374 $ |
| 10-oct | IV.7 | apartado `ipv6` y primera pasada por la puerta | 3 | 18.774 | 18.110 | 0,0137 $ |
| 10-oct | IV.7 | la puerta, con la comprobación nueva | 2 | 12.172 | 3.203 | 0,0037 $ |
| 10-oct | I.6 | 1.ª | 62 | 794.749 | 763.013 | 0,5770 $ |
| 10-oct | I.6 | intento 2: el tope de extensión en el encargo | 13 | 70.035 | 102.510 | 0,0720 $ |
| 10-oct | I.6 | apartado `identificacion-clave` (tabla rota) | 1 | 4.400 | 2.149 | 0,0019 $ |
| 10-oct | I.6 | la puerta (en borrador: no llama a nadie) | 0 | 0 | 0 | 0,0000 $ |
| **Acumulado medido de f10** | | | **180** | **2.824.967** | **1.475.574** | **1,3090 $** |

Dos avisos para que nadie sume mal:

- **una corrida intermedia de la puerta de IV.7 no quedó registrada** (su salida se perdió al cerrar
  el proceso). Fue del mismo orden que las otras dos de puerta, unos céntimos: el acumulado real de
  f10 es **≈1,31 $**, no una cifra exacta;
- **el acumulado del objetivo no se puede dar.** Lo anterior a f10 no está en ninguna fuente. Con lo
  medido (≈1,31 $) el aviso de los 10 $ **no se ha cruzado** por esta tanda, pero no se puede afirmar
  nada sobre el total.

## 2. Los 33 temas

| Tema | Estado | Hechos | Apartados | Puerta de cobertura (clave utilizable) | Sobre todas las claves | Conflictos | Dudosas de apuntes | Forma |
|---|---|---|---|---|---|---|---|---|
| **IV.7** | **publicado** (versión archivada) | 958 → 724 redactados | 25 | **430/449 = 95,8 % PASA** | 430/511 = 84,1 % | 17 | 0 | **PASA las cinco** |
| **I.6** | **borrador con su motivo** (versión retirada) | 346 → 299 | 13 | **170/258 = 65,9 % NO PASA** | 170/283 = 60,1 % | 88 | 0 | **PASA las cinco** |
| **I.1** | **índice en borrador: no se redacta** | 3.509 | 15 (borrador) | — | — | — | — | no pasa las comprobaciones del índice |
| resto (30) | sin empezar | | | | | | | |

*(Cifras medidas el 10-oct a las 16:08 sobre la base real. Otra tanda está escribiendo en la misma
base —hay preguntas nuevas entrando por la cola de clasificación—, así que el número de preguntas
sube; la puerta se mide sobre lo que hay en cada corrida y su resultado queda en el informe de esa
corrida.)*

### La puerta de cobertura: qué número decide y sobre qué conjunto

El §2.3 pide «preguntas cubiertas ≥ **90 %** de las que tienen clave». Hay **dos** conjuntos posibles
y el número cambia según cuál se use, así que el informe del tema dice **los dos**, siempre, con su
denominador escrito:

- **(a) todas las que tienen clave** (activa o en borrador): es el conjunto literal de la frase.
- **(b) las que tienen clave utilizable**: las mismas **sin** las que el propio motor ha marcado como
  contrarias a la norma (el paso B las señala con `doubtful`). Una pregunta cuya respuesta marcada
  contradice la norma **no tiene una respuesta con la que se pueda acertar**, así que contarla en
  contra de los apuntes sería culpar al texto de un fallo del banco.

**El que decide es (b)**, decidido por el propietario delegado y anotado en
`DECISIONES-TOMADAS-EN-EL-OBJETIVO.md` (con su vuelta atrás: aplicar (a) y los dos temas pasan a
borrador). Medido hoy:

- **IV.7**: 430 de 449 = **95,8 %** con (b) → **PASA** y se publica. Con (a), 430 de 511 = 84,1 %.
- **I.6**: 170 de 258 = **65,9 %** con (b) → **NO PASA**. Con (a), 170 de 283 = 60,1 %. No llega con
  ninguno de los dos.

Antes de cablearla, la puerta existía en el documento y **no en el código**: `--exigir-calidad` solo
miraba las cinco comprobaciones de forma, así que un tema con el 85 % podía quedar archivado. Ahora
las dos deciden, el número sale en el informe de cada tema —también cuando queda en borrador— y un
tema que no pasa **no se queda publicado**: si tenía una versión archivada de una corrida anterior, se
**retira con su motivo** y auditada (es reversible: en cuanto pase, el comando la archiva otra vez).

### IV.7, pregunta a pregunta (528 preguntas, 511 con clave, el 10-oct a las 16:08)

| Desenlace | Con clave activa | Con clave en borrador | Sin clave | Total |
|---|---|---|---|---|
| Cubierta | 159 | 271 | 17 | 447 |
| En conflicto con la clave | 7 | 10 | 0 | 17 |
| Dudosa (incidencia de clave) | 27 | 37 | 0 | 64 |

Y la bandeja del propietario de IV.7: **55 incidencias con su categoría** (40 `norma_cambiada`, 14
`clave_sospechosa` y 1 `hueco_sin_material`), cada una con su motivo y con la frase verificada que la
sostiene cuando la hay. **Todas las preguntas no cubiertas tienen categoría**, que es la otra mitad
del §2.3.

### I.6 (191 grupos, 303 preguntas)

Cobertura 65,9 % con (b) y 60,1 % con (a); 45 conflictos de letra, 20 incidencias de clave marcada por
el paso B y **0 dudas por los apuntes**; banda de la bandeja: **66 incidencias** (45
`clave_sospechosa`, 20 `norma_cambiada` y 1 `pregunta_ambigua`). Pasa las cinco comprobaciones de
forma (12.340 palabras de 13.840; repetidos 0,7 %). **Se queda en borrador**: 65 de sus 66
incidencias son de la clave, no de los apuntes, así que no se arregla escribiendo más.

## 3. Los tres arreglos del motor (§2.1), con su prueba

| Arreglo | Qué hacía antes | Qué hace ahora | Prueba que falla antes |
|---|---|---|---|
| 1. Un hecho va al apartado de **su materia** | El reparto iba por la pregunta: el apartado de UDP hablaba de la cabecera de IPv6, de ARP y de ICMP | El texto del hecho decide; la pregunta es el respaldo si el texto no reconoce ninguna materia. El ancla de una pregunta admite **varios** apartados | `test_un_hecho_va_al_apartado_de_su_materia_y_no_al_de_su_pregunta`, `test_una_pregunta_puede_anclarse_en_varios_apartados`, `test_una_palabra_que_esta_en_media_asignatura_no_le_gana_a_la_de_una_materia` |
| 2. La tabla de puertos, **por familias y sin avisos de opciones falsas** | 47 filas seguidas con «No es DynamoDB», «No es MySQL»… | 4 tablas por familia, ordenadas, sin notas de distractor, y las confusiones de verdad en «Confusiones que caen» | `test_una_tabla_de_puertos_se_parte_por_familias`, `test_las_notas_que_solo_dicen_lo_que_un_puerto_no_es_se_van`, `test_la_puerta_de_forma_exige_la_tabla_partida_y_sin_notas_de_distractor` |
| 3. **Bucle de huecos** y bandeja del propietario | El resto se contaba en el informe y se perdía al cerrar la terminal | Una vuelta más de añadido para los huecos y, lo que siga sin resolverse, a la bandeja con su categoría y su frase | `test_lo_que_queda_sin_cubrir_recibe_la_categoria_de_quien_lo_arregla`, `test_el_detalle_de_una_clave_sospechosa_lleva_la_frase_que_lo_demuestra` |

Medido en IV.7: **24 notas de distractor retiradas**, **22 confusiones** en su bloque, **4 familias**,
**0 puertos repetidos** y **0 notas sin sentido**. El apartado de UDP pasó de 16 hechos —con la
cabecera de IPv4, 127.0.0.1, ARP, IPv6 e ICMP— a **8, todos de UDP**.

Tres cosas más hicieron falta para que esto se viera y para que las puertas no marcaran temas que
están bien:

1. **Un apartado que pierde hechos se vuelve a redactar**: su texto se escribió con otros hechos (sin
   esto, la clave `udp` no cambiaba y el texto viejo se quedaba).
2. **El tope de extensión va en el encargo del apartado** (40 palabras por hecho), no solo en el
   informe: I.6 salió con 82 palabras por hecho y no pasó; con el tope dicho antes de escribir bajó a
   41 y pasó.
3. **Dos encabezados que difieren en una cifra o una sigla no son el mismo encabezado**: «Cabecera
   IPv6» y «Cabecera IPv4» se parecen 0,83 por trigramas y son dos apartados distintos. Sin esa
   guarda, la puerta de encabezados repetidos bloqueaba IV.7 por un falso positivo. Se aplica igual al
   medir y al arreglar (`mismo_encabezado`), y el perdón de «el apartado se titula a sí mismo» usa un
   criterio más permisivo a propósito (`parece_el_mismo_titulo`).

## 4. Lo que queda abierto

1. **El acumulado de gasto anterior a f10 no existe** y ya no se puede medir. Desde aquí se anota una
   línea por corrida (§1).
2. **I.1 no se puede redactar todavía.** Su índice por materias está en borrador y **no pasa sus
   propias comprobaciones**: cuatro apartados se pasan de 150 hechos y **295 preguntas (de 2.006) no
   casan con ninguna materia** —enunciados cortos sin artículo ni institución («Una de las siguientes
   afirmaciones es falsa», «Los acuerdos adoptados, para ser válidos»)—. Hace falta más contenido
   (patrones) o mandarlas a la cola de clasificación.
3. **La puerta «hechos fuera de su materia (≤ 3 %)»** del §2.3 sigue sin implementar: el §2.1.1 la
   pide con el modelo clasificando cada hecho de un apartado. Lo determinista sí está probado (cada
   hecho en el apartado de lo que afirma, y los cuatro casos que citó el propietario, por prueba).
4. Quedan pendientes de la tanda anterior, por este orden: las **frases que demuestran cada conflicto
   de I.6** en la bandeja, y la **primera pantalla de la app** (los tests de varios temas y el
   simulacro real, con el caso de 50 aciertos, 15 fallos y 15 en blanco = 28,125 sobre 50).
5. Los **30 temas restantes** y los bloques B y C, sin empezar.
