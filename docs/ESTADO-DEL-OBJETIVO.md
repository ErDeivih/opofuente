# Estado del objetivo largo (TAI: los 33 temas y la app de estudio)

**Autoridad:** `docs/GOAL-DEEPSEEK-TRABAJO-LARGO-2026-10.md` · **Presupuesto de API:** 40 $ · **Se
avisa cada 10 $** · Última actualización: **17 oct 2026 (tanda f39: el repaso y los datos raros · 0 $ de API)**. La cabecera se quedó en la f21b y el cuerpo siguió hasta la f35: esto es el histórico y **la tanda f39 está al final**. Antes: **13 oct 2026 (tanda f21b: el contenido sigue por la tabla
de valor y por el encaje medido del banco. **III.5 (99,2 %), III.7 (93,6 %) e IV.8 (99,1 %) quedan
escritos y publicados** por 0,8953 $; **I.7 se queda en borrador con la decisión escrita** y su
bandeja —que estaba vacía— rellenada con 42 incidencias sin gastar un céntimo. Acumulado ≈ 15,35 $ de
40)**.

> **De las fechas:** la tanda anterior se etiquetó «11 oct» en este fichero, pero **su reloj, sus
> ficheros y sus marcas de base son del 10 de octubre** (la corrida de I.6 acabó a las 18:09 del
> 10-oct). Las etiquetas iban por delante. La tanda f13 sí es del **11 de octubre**: empezó a las
> 11:20 y el reloj de la máquina marcaba 14:22 al escribir sus líneas. Las tandas f15 y f16 son del
> 11-oct y la **f17 es del 12-oct**: su corrida de IV.2 empezó a las 12:39 y acabó a las 13:24.

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
| 11-oct | I.6 | recomprobación con la huella del texto (la bandeja) | 45 | 518.452 | 605.550 | 0,4411 $ |
| **Acumulado medido de f11** | | | **45** | **518.452** | **605.550** | **0,4411 $** |
| 10-oct | I.6 | corrida de reescritura (matada al ver que la lectura por apartados se quedaba corta) | — | — | — | **≈0,40 $ (no medido)** |
| 10-oct | I.6 | la reescritura con la lectura por apartados y su presupuesto | 81 | 800.724 | 817.710 | 0,6107 $ |
| 10-oct | I.6 | la reescritura con el tope del añadido: **la forma pasa** | 74 | 727.234 | 670.864 | 0,5116 $ |
| 10-oct | I.1 | la redacción con el índice nuevo: 21 apartados, 2.043 preguntas | 355 | 4.787.376 | 2.068.573 | 1,9593 $ |
| 10-oct | I.1 + I.6 | `--medir`, `--esquema`, `--prever`, `--limpiar-forma` y `--publicar` (solo lectura) | 0 | 0 | 0 | 0,0000 $ |
| **Acumulado medido de f12** | | | **510** | **6.315.334** | **3.557.147** | **3,0816 $** |
| 11-oct | — | f13: la interfaz (tokens, Inicio, Temario, apuntes y el aviso del alumno) | 0 | 0 | 0 | 0,0000 $ |
| **Acumulado medido de f13** | | | **0** | **0** | **0** | **0,0000 $** |
| 11-oct | — | f14: el cierre del ciclo de estudio (Resultado, Simulacro, Exámenes, Fallos y Progreso) | 0 | 0 | 0 | 0,0000 $ |
| **Acumulado medido de f14** | | | **0** | **0** | **0** | **0,0000 $** |
| 11-oct | I.2 | la redacción completa del tema (paso B a bucle de huecos) | 194 | 2.149.315 | 1.493.911 | 1,2187 $ |
| 11-oct | I.2 | `--medir`, `--limpiar-forma` y `--publicar` (solo lectura y limpieza) | 0 | 0 | 0 | 0,0000 $ |
| 11-oct | I.4 | la redacción completa del tema (paso B a bucle de huecos) | 169 | 1.963.599 | 1.946.630 | 1,4625 $ |
| 11-oct | I.4 | `--medir`, `--limpiar-forma` y `--publicar` (solo lectura y limpieza) | 0 | 0 | 0 | 0,0000 $ |
| **Acumulado medido de f15** | | | **363** | **4.112.914** | **3.440.541** | **2,6812 $** |
| 11-oct | — | f16: la bandeja de avisos del alumno y «No son preguntas» (bloque C) | 0 | 0 | 0 | 0,0000 $ |
| **Acumulado medido de f16** | | | **0** | **0** | **0** | **0,0000 $** |
| 12-oct | IV.2 | la redacción completa del tema (paso B a bucle de huecos) | 182 | 1.829.341 | 806.759 | 0,7585 $ |
| 12-oct | II.4 | la redacción completa del tema (paso B a bucle de huecos) | 166 | 1.567.294 | 777.151 | 0,7014 $ |
| 12-oct | I.8 | la redacción completa del tema, **parada en su tope de tiempo** (389 de 442 grupos comprobados) | 142 | 1.480.794 | 1.649.566 | 1,2119 $ |
| 12-oct | IV.2, II.4 y I.8 | `--esquema`, `--prever`, `--medir`, `--limpiar-forma` y `--publicar` (solo lectura y limpieza) | 0 | 0 | 0 | 0,0000 $ |
| **Acumulado medido de f17** | | | **490** | **4.877.429** | **3.233.476** | **2,6718 $** |

> **AVISO DE LOS 10 $: cruzado en esta tanda.** Con la corrida de I.8 el acumulado medido del
> objetivo pasa de **8,67 $** (al cerrar II.4) a **10,58 $** de los 40 $, contando lo anterior:
> ≈1,31 $ (f10) + 0,4411 $ (f11) + 3,0816 $ + ≈0,40 $ (f12) + 0,00 $ (f13) + 0,00 $ (f14) +
> 2,6812 $ (f15) + 0,00 $ (f16) + **2,6718 $ (f17)** = **≈10,58 $**. Quedan **≈29,4 $** y el precio
> medido de un tema está entre **0,70 $** (técnico, IV.2 y II.4) y **1,21 $** (normativo denso, I.8).
> **A este precio quedan entre 24 y 41 temas, así que el objetivo entero entra en el presupuesto**,
> pero el aviso se anota donde manda la decisión D3.

*(f13 no llama al modelo a propósito: es el bloque de interfaz y de la ruta de escritura de los
avisos. f14 tampoco: es interfaz y consultas de lectura sobre la base; lo único que se ejecuta son las
herramientas locales —ruff, mypy, pytest, Vitest, Playwright—, que no cuestan. f16, igual: interfaz,
una migración y consultas de lectura. Las únicas llamadas de las tres tandas fueron las de esas
herramientas.)*

Tres avisos para que nadie sume mal:

- **una corrida intermedia de la puerta de IV.7 no quedó registrada** (su salida se perdió al cerrar
  el proceso). Fue del mismo orden que las otras dos de puerta, unos céntimos: el acumulado real de
  f10 es **≈1,31 $**, no una cifra exacta;
- **dos corridas de f11 se lanzaron a la vez por error** y una se mató a los tres minutos, antes de
  escribir nada en la base ni de llamar al modelo con resultado: el gasto de f11 es el de la tabla;
- **una corrida de f12 se mató a propósito** (la primera reescritura de I.6): se vio en la base que la
  lectura por apartados estaba dejando 114 preguntas sin frase —y que el bucle de huecos iba a
  rellenarlas escribiendo de más— y se paró antes de que acabara. Su gasto **no está medido** (la
  salida se perdió al matar el proceso): es del orden de la corrida siguiente, **≈0,40 $**;
- **el acumulado del objetivo no se puede dar.** Lo anterior a f10 no está en ninguna fuente. Con lo
  medido (≈1,31 $ de f10 + 0,4411 $ de f11 + 3,0816 $ de f12 + ≈0,40 $ de la corrida matada + 0,00 $
  de f13 + 0,00 $ de f14 + 2,6812 $ de f15 + 0,00 $ de f16 + 2,6718 $ de f17 = **≈10,58 $**) **el
  aviso de los 10 $ se ha cruzado en f17** y queda anotado arriba, en la tabla de gasto.

**Y una corrección de método**: el informe de una corrida contaba la cobertura **antes** del bucle de
huecos, así que decía menos de la que el tema acababa teniendo (en I.1: 1.947 de 1.995 en el informe,
**1.965 de 1.995** en la base). Ahora la corrida vuelve a contar al terminar, `--medir` mide lo
guardado y `--prever` dice lo que costaría una corrida **antes** de pagarla.

## 2. Los 33 temas

| Tema | Estado | Hechos | Apartados | Puerta de cobertura (clave utilizable) | Sobre todas las claves | Conflictos | Dudosas de apuntes | Forma |
|---|---|---|---|---|---|---|---|---|
| **IV.7** | **publicado** (versión archivada) | 958 → 724 redactados | 25 | **430/449 = 95,8 % PASA** | 430/511 = 84,1 % | 17 | 0 | **PASA las cinco** |
| **I.6** | **borrador con su motivo** (versión retirada) | 346 → 299 | 13 | **187/258 = 72,5 % NO PASA** | 187/283 = 66,1 % | 20 (`clave_sospechosa`) | 20 | **PASA las cinco** (13.174 palabras de 13.840; repetidos 0,6 %) |
| **I.1** | **publicado** (versión archivada, con la marca «Versión generada · en revisión») | 3.511 → 1.724 redactados | 21 | **1.965/1.995 = 98,5 % PASA** | 1.965/2.035 = 96,6 % | 15 | 10 | **PASA las cinco** (60.400 palabras de 140.440; repetidos 2,2 %) |
| **I.2** | **publicado** (versión archivada, con la marca «Versión generada · en revisión») | 1.233 → 696 redactados | 16 | **669/703 = 95,2 % PASA** | 669/835 = 80,1 % | 19 | 6 | **PASA las cinco** (24.061 palabras de 49.320; repetidos 2,9 %) |
| **I.4** | **borrador con su motivo** | 1.056 → 721 redactados | 15 | **497/559 = 88,9 % NO PASA** | 497/579 = 85,8 % | 31 | 3 | **PASA las cinco** (27.787 palabras de 42.240; repetidos 4,2 %) |
| **IV.2** | **publicado** (versión archivada, con la marca «Versión generada · en revisión») | 1.543 → 1.126 redactados | 16 | **757/758 = 99,9 % PASA** | 757/797 = 95,0 % | 1 | 0 | **PASA las cinco** (32.567 palabras de 61.720; repetidos **0,2 %**) |
| **II.4** | **publicado** (versión archivada, con la marca «Versión generada · en revisión») | 1.046 → 848 redactados | 17 | **443/462 = 95,9 % PASA** | 443/568 = 78,0 % | 11 | 0 | **PASA las cinco, tras la limpieza** (26.367 palabras de 41.840; repetidos 0,3 %) |
| **I.8** | **borrador con su motivo** (2 motivos: cobertura 82,0 % y corrida parada por su tope de tiempo con 53 grupos sin comprobar) | 815 → 617 redactados | 18 | **423/516 = 82,0 % NO PASA** | 423/571 = 74,1 % | 7 | 9 | **PASA las cinco** (23.285 palabras de 32.600; repetidos 0,3 %) |
| resto (25) | sin empezar | | | | | | | |

*(Cifras de **esta** tanda, medidas con `apuntes --medir` sobre la base real —no heredadas de la
corrida que las escribió—. Las tres filas son del 10-oct: IV.7 es la única que no se ha tocado. La
fila de I.6 de la tanda anterior (64,3 %) describía un texto que ya no existe: I.6 se ha vuelto a
redactar entero con el tope de extensión del §2.3 y con la deduplicación, y su texto pasó de 111.000
caracteres a **83.815**.)*

### Lo que le falta a I.6 y por qué no es cuestión de escribir más

I.6 contesta al 72,5 % de lo que se le pregunta y **no puede llegar al 90 %**: de las 258 preguntas
con clave utilizable, 41 tienen una frase en los apuntes que sostiene **otra opción** que su clave (el
propietario tiene que decidir cuál de las dos está mal) y 30 no tienen frase. Si se rellenaran **todos**
los huecos de material, el techo sería **217/258 = 84,1 %** — medido, no estimado. Por eso el tema
queda en borrador con su motivo escrito, y no por falta de redacción: 58 de sus 63 incidencias son de
la clave, no de los apuntes.

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
- **I.6**: 187 de 258 = **72,5 %** con (b) → **NO PASA**. Con (a), 187 de 283 = 66,1 %.
- **I.1**: 1.965 de 1.995 = **98,5 %** con (b) → **PASA** y se publica. Con (a), 1.965 de 2.035 =
  96,6 %.

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

### I.6 (191 grupos, 303 preguntas), vuelto a redactar y medido el 10-oct

Cobertura **72,5 % con (b)** y 66,1 % con (a); **20 grupos en conflicto de letra** (41 preguntas),
20 preguntas sin frase en los apuntes, 36 incidencias de clave marcada por el paso B y 1 sin clave con
la que comprobar; la bandeja tiene **63 incidencias** (20 `clave_sospechosa`, 20 `norma_cambiada`, 20
`hueco_sin_material` y 3 `pregunta_ambigua`). La puerta de forma **ahora sí la pasa**: 13.174 palabras
de 13.840 (el tope es 40 × 346 hechos distintos) y 0,6 % de párrafos repetidos. **Se queda en
borrador** por la cobertura, y no por las frases: su techo medido es 84,1 %.

**Y las frases de sus conflictos siguen siendo frases de verdad después de reescribirlo.** La
migración `0032` guarda la huella del texto comprobado, así que al rehacer un apartado su comprobación
caduca y **se vuelve a comprobar**: la bandeja no hereda citas de un texto que ya no existe. Medido
con la misma comprobación que usa el motor (`verificar_cita`, y con el texto que el motor le da a esa
pregunta: la unión de sus apartados más lo que quepa de sus epígrafes):

| Qué se mide | Antes de reescribir | Después de reescribir |
|---|---|---|
| Anclas de conflicto cuya cita está en los apuntes de hoy | 66 de 70 | **41 de 41** |
| Frases de la bandeja (`clave_sospechosa`) que están en los apuntes de hoy | 35 de 38 | **20 de 20** |

### I.1 (2.008 grupos, 2.043 preguntas), redactado y publicado el 10-oct

Su índice **por fin cuadra**: 21 apartados, 1.724 hechos redactados y **0 hechos y 0 preguntas sin
materia**. De los 2.008 grupos, 209 no dicen de qué hablan por su enunciado («Una de las siguientes
afirmaciones es falsa») y se han situado por el texto de sus hechos; no ha hecho falta ni un cajón de
«otros» ni mandar ninguna pregunta a la bandeja por no caber. La puerta de cobertura pasa con
**1.965/1.995 = 98,5 %** y la de forma también (60.400 palabras de 140.440 y 2,2 % de repetidos). Su
bandeja tiene **61 incidencias** (35 `norma_cambiada`, 15 `clave_sospechosa`, 10 `hueco_sin_material`
y 1 `pregunta_ambigua`).

## 3. Los arreglos del motor (§2.1), con su prueba

| Arreglo | Qué hacía antes | Qué hace ahora | Prueba que falla antes |
|---|---|---|---|
| 1. Un hecho va al apartado de **su materia** | El reparto iba por la pregunta: el apartado de UDP hablaba de la cabecera de IPv6, de ARP y de ICMP | El texto del hecho decide; la pregunta es el respaldo si el texto no reconoce ninguna materia. El ancla de una pregunta admite **varios** apartados | `test_un_hecho_va_al_apartado_de_su_materia_y_no_al_de_su_pregunta`, `test_una_pregunta_puede_anclarse_en_varios_apartados`, `test_una_palabra_que_esta_en_media_asignatura_no_le_gana_a_la_de_una_materia` |
| 2. La tabla de puertos, **por familias y sin avisos de opciones falsas** | 47 filas seguidas con «No es DynamoDB», «No es MySQL»… | 4 tablas por familia, ordenadas, sin notas de distractor, y las confusiones de verdad en «Confusiones que caen» | `test_una_tabla_de_puertos_se_parte_por_familias`, `test_las_notas_que_solo_dicen_lo_que_un_puerto_no_es_se_van`, `test_la_puerta_de_forma_exige_la_tabla_partida_y_sin_notas_de_distractor` |
| 3. **Bucle de huecos** y bandeja del propietario | El resto se contaba en el informe y se perdía al cerrar la terminal | Una vuelta más de añadido para los huecos y, lo que siga sin resolverse, a la bandeja con su categoría y su frase | `test_lo_que_queda_sin_cubrir_recibe_la_categoria_de_quien_lo_arregla`, `test_el_detalle_de_una_clave_sospechosa_lleva_la_frase_que_lo_demuestra` |
| 4. **(f11) Una comprobación caduca cuando el apartado se reescribe** | La comprobación se guardaba con la cita y **se reutilizaba por la firma del grupo**: si el texto se rehacía, la bandeja seguía enseñando una frase que ya no estaba en los apuntes | Cada comprobación guarda la **huella** (`sha256`) del texto contra el que se verificó (migración `0032`), y solo se reutiliza si el texto de hoy tiene esa huella. Una fila sin huella (las de antes) se vuelve a comprobar | `test_una_comprobacion_caduca_cuando_el_apartado_se_reescribe` (falla con la regla vieja: la segunda corrida no volvía a comprobar) |
| 5. **(f12) Lo que no cabe en ninguna materia va a la bandeja del propietario, no al cajón y no para la corrida** | El tema **no se podía redactar**: `_paso_esquema` salía con `UnsupportedError` por 10 preguntas de 2.000, y sin decir cuáles | El árbol se escribe con lo que sí se puede situar; cada pregunta que no cabe va a la bandeja con `Motivo.SIN_MATERIA_EN_EL_INDICE` y su enunciado, y **cuenta en la puerta de cobertura** como no cubierta (si se cayera del denominador, la puerta se mediría sobre un conjunto del que se han ido las que peor están) | `test_una_pregunta_que_no_cabe_en_el_indice_va_a_la_bandeja_y_no_para_la_corrida` |
| 6. **(f12) Un grupo que no dice de qué habla se sitúa por el texto de sus hechos** | 296 grupos de I.1 sin materia: «Una de las siguientes afirmaciones es falsa» no casa con ningún patrón y no se puede escribir un comodín por cada muletilla de examen | Manda la materia que reconocen **más** de sus hechos (desempate por el orden del catálogo, para que dos corridas den el mismo índice). De 296 quedan **0** | `test_una_pregunta_que_no_dice_de_que_habla_va_a_la_materia_de_sus_hechos`, `test_un_grupo_sin_enunciado_ni_hechos_que_reconozcan_nada_se_queda_sin_materia` |
| 7. **(f12) El añadido de un apartado lleva su tope de palabras** | El apartado se redactaba con el tope del §2.3 y luego los añadidos le metían encima todo lo que hiciera falta: I.6 pasó de 12.300 palabras a **18.795** donde el tope son 13.840 | El encargo del añadido dice **cuántas palabras le quedan al apartado** (`tope_del_anadido`), nunca menos de 60: lo que no quepa se declara en la bandeja en vez de taparse escribiendo de más. I.6 quedó en **13.174** y su forma pasó | `test_el_anadido_lleva_su_tope_de_palabras_en_el_encargo` |
| 8. **(f12) Los trozos de una materia se escriben en orden y el segundo sabe lo que ya está puesto** | Una materia que no cabe en una llamada se partía, y cada trozo escribía **su propio índice**: I.1 acabó con «2. Composición de las Cámaras» y «3. Estatuto de los parlamentarios» dos veces | El segundo trozo recibe los encabezados del primero y no los repite; las materias distintas siguen escribiéndose a la vez | `test_los_trozos_de_una_materia_se_escriben_en_orden_y_sin_repetir_encabezados` |
| 9. **(f12) La comprobación recibe la unión de los apartados de la pregunta, y lo que quepa de su epígrafe** | Recibía el **epígrafe entero**: el de I.1 son nueve apartados de 150 hechos (≈300.000 caracteres) y no cabe en la ventana del modelo —el tema no se podía comprobar— | La unión de sus apartados (§2.1.1) más el resto de sus epígrafes mientras quepa en 60.000 caracteres. El corte es determinista y la huella se calcula con la misma función | `test_la_comprobacion_recibe_la_union_de_sus_apartados_y_lo_que_quepa_del_epigrafe`, `test_el_texto_de_la_comprobacion_se_corta_por_presupuesto` |
| 10. **(f12) Una columna de tabla sin titular se nombra** | La tabla de comparación se escribe con la primera celda de la cabecera vacía y así no se lee: I.1 tenía **cuatro** así | `nombrar_columnas_sin_titulo` le pone nombre a esa columna (y solo a esa). Los datos no se tocan | `test_una_columna_de_tabla_sin_titulo_se_nombra_y_deja_de_estar_rota` |
| 11. **(f17) Una tubería dentro de un `código` en una celda de tabla se escapa, y el medidor no parte por una tubería escapada** | La tabla de los operadores del shell de II.4 tiene una fila cuyo contenido **es** la tubería (`` \| ``): sin escapar, la fila se parte en tres celdas donde la cabecera tiene dos y la tabla deja de leerse. Y el arreglo no bastaba solo: `_celdas` volvía a partir por la tubería escapada, así que la reparación no se notaba | `escapar_tuberias_en_celdas` (al guardar un apartado y en `--limpiar-forma`) escapa la tubería que está entre acentos graves de una fila de tabla, y `_celdas` cuenta `\|` como contenido. Son las dos mitades de la misma cosa: lo que se mide y lo que se arregla hablan del mismo texto | `test_una_tuberia_escapada_cuenta_como_una_celda_y_no_como_un_separador` y `test_la_tuberia_que_va_dentro_de_un_codigo_de_una_celda_se_escapa_y_la_tabla_se_arregla` (**2 failed** con el código de antes; registro en `F:\temp-opofuente\f17-scratch\rojo-tuberia.txt`) |
| 12. **(f17) El título de un apartado se vuelve a poner desde su índice** | La puerta de forma **sí** medía las cabeceras compartidas («las tres primeras palabras del título») y la limpieza **no** podía arreglarlas: II.4 acabó con cuatro apartados titulados «Unix y Linux: …» y ponerles el título de su catálogo obligaba a **volver a pagar** la corrida (50–117 llamadas, 0,34–0,80 $ según `--prever`) | `--limpiar-forma` recalcula el plan del tema (con `indice_de` y `plan_de`, los mismos que usa la corrida) y pone a cada apartado el título que dice **su índice**. Es una reparación, no una invención: no hay título nuevo, hay el del catálogo. Tocó 13 apartados de II.4 y la forma pasó de NO PASA a PASA | `test_el_titulo_de_un_apartado_se_vuelve_a_poner_desde_su_indice` (con el código de antes no existía `titulos_que_cambian`: error de colección; registro en `F:\temp-opofuente\f17-scratch\rojo-titulo.txt`) |

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
   IPv6» y «Cabecera IPv4» se parecen 0,83 por trigramas y son dos apartados distintos.

## 4. El bloque de la app (f11)

Lo que se ha construido, y lo que se ha medido de cada cosa:

| Qué | Dónde | Cómo se comprueba |
|---|---|---|
| **Puntuación «estimada»** explícita | `domain/study.py` (`ScoringKind.ESTIMATED`) | `test_la_puntuacion_estimada_de_tai_da_28_125_exacto` (con el perfil real: `options_per_question` nulo), `test_la_estimacion_no_se_declara_aprobado_y_lo_dice`, `test_la_formula_de_guardia_civil_no_se_puede_usar_en_tai`, `test_la_segunda_parte_de_tai_tambien_se_estima` |
| **Una sola forma de componer** cualquier test | `StudyService.compose(spec)` + `PartSpec`/`CompositionSpec` | `test_un_test_de_tres_temas_de_bloques_distintos_se_compone_en_una_sola_forma`, `test_una_pregunta_de_dos_temas_no_cae_dos_veces`, `test_el_simulacro_monta_80_mas_20_con_su_supuesto_y_su_nota_por_parte`, `test_dos_supuestos_del_mismo_grupo_no_se_montan_los_dos` |
| **La capa del alumno** para montar y correr el test | `POST /student/tests`, `POST /student/mock-exams`, `GET/POST /student/sessions/{id}[/start|/answers|/finish]` | `test_student_api.py` (la prueba de contrato recorre **todas** las respuestas nuevas buscando lo prohibido) y `studentTest.test.tsx` en la web |
| **La pantalla del test en curso** con la hoja de respuestas (v0) | `apps/web/src/features/study/StudentTestRunner.tsx` + `AnswerSheet.tsx`, ruta `/test/:id` | 5 pruebas de componente (teclado, hoja por estados, corrección al final que **no** se enseña) y dos capturas en `artifacts/screens/test-en-curso-{escritorio,movil}.png` (axe 0, palabras prohibidas 0) |

## 4b. El bloque de la lectura del alumno (f13)

Lo que se ha construido en este bloque, y lo que se ha medido de cada cosa. **No ha gastado API**: no
se ha llamado a ningún modelo (es interfaz y la ruta de escritura de los avisos).

| Qué | Dónde | Cómo se comprueba |
|---|---|---|
| **Los tokens del diseño en un sitio único y aplicados de verdad** | `apps/web/src/styles/tokens.css` (color, tipografía, escala, espaciado, radios, sombra y estados) y las dos fuentes autoalojadas en `main.tsx` | `tests/unit/tokens.test.ts`: los 14 colores con su valor exacto, la escala 14·17·20·24·32, los radios, la sombra superpuesta y el foco; y **ninguna otra hoja declara un color a mano** (la prueba lee `ui.css` y `global.css` y falla si aparece un `#`) |
| **La hoja de respuestas no se estropea** | `.test-marco` pasa a tomar sus tokens del fichero del diseño (mismos valores que tenía) | Las 5 pruebas de `studentTest.test.tsx` siguen pasando y la captura `test-en-curso-*` sale con **axe 0 y palabras prohibidas 0** |
| **El marco del diseño**: carril de siete entradas con icono en escritorio y barra inferior de cinco en móvil | `apps/web/src/app/AppShell.tsx` + `apps/web/src/ui/Icons.tsx` (SVG en línea: la CSP no deja fuentes de iconos) | `shell.test.tsx` (siete entradas, una sola puerta al panel, salto al contenido) y `first-run.spec.ts` en la puerta E2E |
| **Inicio**: qué toca (seguir el test, repasar fallos), el progreso por bloque con el porcentaje escrito y los temas con apuntes con su estado | `apps/web/src/pages/student/StudentHomePage.tsx`, `GET /student/overview` | `studentInicio.test.tsx` (6 pruebas) y capturas `inicio-{escritorio,movil}.png` (axe 0, prohibidas 0) |
| **Temario**: índice del programa con el número romano en el margen, orden numérico, buscador por título y código, estado de cada tema y sus dos salidas | `apps/web/src/pages/student/SyllabusPage.tsx`, `GET /student/syllabus` | `studentTemario.test.tsx` (5) y capturas `temario-{escritorio,movil}.png` (axe 0, prohibidas 0) |
| **Tema con apuntes**: tres columnas (índice navegable, lectura en serif y nota al margen dentro de su apartado), tablas con cabecera, «Esto está mal» por apartado y el estado del tema | `apps/web/src/pages/student/TopicNotesPage.tsx`, `features/student/NotesBody.tsx`, `GET /student/topics/{codigo}/notes` | `studentApuntes.test.tsx` (8) y capturas `temario-IV-7-*` (IV.7, publicado) y `temario-I-6-*` (I.6, borrador), las cuatro con axe 0 y prohibidas 0. Las capturas se llaman por la **dirección** de la pantalla (`/temario/IV.7`), que es como las nombra la herramienta |
| **Un tema en borrador se lee y lo dice** (D2/D12) y uno sin apuntes no es un error | `GET /student/topics/{codigo}/notes` con `state` = `published` \| `draft` \| `none`, y `notes_state` en cada tema del temario y de Inicio | `test_student_notes_api.py` (los tres estados y el 404 del tema que no está); `studentApuntes.test.tsx` (borrador, publicado y sin apuntes) |
| **«Esto está mal» guarda de verdad** (D2): tabla `notes_reports` (migración `0033_avisos_del_alumno`) con su **evento de auditoría en la misma escritura**, el anclaje puesto por el servidor y el motivo en una línea | `POST /student/topics/{codigo}/reports`, `domain/notes_reports.py`, `infrastructure/notes_report_repository.py` | `test_student_notes_api.py` (el aviso, su ancla, su auditoría, el 422 sin motivo y el 404 de un apartado ajeno) y `test_migrations_0033.py` (los `CHECK` y la vuelta atrás) |
| **El aviso llega al propietario** | `GET /notes-reports` (bandeja, con filtro por estado y por tema) | `test_student_notes_api.py`: el aviso sale con su tema y su apartado, y sigue saliendo —con el título vacío— si el apartado se reescribió |

**Puertas: 18/18**, ejecutadas en **31:47 minutos** sobre este árbol (1.387 pruebas de backend entre
unitarias e integración, 294 de componentes, la suite E2E entera y las 18 puertas del `gates.ps1`).
El registro está en `F:\temp-opofuente\gates-f13-alumno.txt`. La primera pasada **falló en la puerta
18** (el desborde de 43 px que se cuenta abajo); se arregló la pantalla —no la prueba— y se volvió a
pasar entera.

### El desborde de 43 px del panel, y por qué está escrito aquí

La puerta 18 (responsividad del E2E) falló al aplicar el diseño: en la **bandeja del panel**
(`/admin/importar`), a 390 px, la página medía **433 px**. El culpable eran dos
`<input type="file">` de «Suelta aquí ficheros o carpetas» / «O elige una carpeta»: **393 px** cada
uno. Un control de formulario con `width: auto` **no se encoge** —toma su ancho intrínseco, el del
`size` por defecto más el botón del selector— y se salía de su caja.

La causa raíz fue **de este bloque**: puse el **cuerpo de 17 px del diseño en toda la aplicación**
(antes 16 px) y la familia nueva es más ancha; el panel está maquetado a 16 px y esos dos controles
se pasaron 43 px. Se arregla en dos sitios y se queda escrito por si vuelve:

1. **el cuerpo de 17 px es de la zona del alumno** (`.marco-alumno`); la base de la aplicación sigue
   en 16 px, así que el panel no cambia de medidas en un bloque que no es el suyo (§3.7 es el
   rediseño **del alumno**);
2. **`.form__input { max-width: 100% }`**: un control de formulario no puede salirse de su caja, sea
   cual sea la tipografía.

Medido con los datos reales a 390 px después del arreglo: `/bandeja` **390** (era 433), `/` **390**,
`/temario` **390**, `/temario/IV.7` **390**, `/temario/I.6` **390** (era 416 por la cadena
«fallecimiento/incapacidad/extinción/pérdida» de sus apuntes, que ahora se parte). Las tablas de los
apuntes **caben** en vez de desplazarse dentro de una caja: el contenedor con scroll exigiría un
`tabindex` que eslint prohíbe y dejaría una violación de axe (`scrollable-region-focusable`) o
contenido escondido tras un desplazamiento.

## 4c. El cierre del ciclo de estudio (f14)

Lo que se ha construido en este bloque, y lo que se ha medido de cada cosa. **No ha gastado API**: no
se ha llamado a ningún modelo (es interfaz y consultas de lectura sobre la base).

| Qué | Dónde | Cómo se comprueba |
|---|---|---|
| **El resultado de un test, pregunta a pregunta y por tema** | `GET /student/sessions/{id}/result`; `apps/web/src/pages/student/ResultPage.tsx` (`/resultado/:id`) | `test_student_result_api.py`: cada pregunta con su tema, sus opciones, lo que se marcó y la correcta, el tiempo por pregunta y el desglose por tema cuadrando con lo contestado; de un test sin terminar, 409 con su motivo. La prueba de contrato del alumno recorre **también** esta respuesta (es la más larga de la capa) buscando lo prohibido |
| **Cómo se enseña la estimación** | El aviso sale del **dominio** (`ESTIMATED_SCORE_NOTE` y `estimated_verdict_note`) y la pantalla lo pinta tal cual, con su énfasis | `studentResultado.test.tsx` (6 pruebas): el aviso «…esto no es la calificación oficial», la nota por parte con su banda y su mínimo, el tiempo, el desglose por tema con el porcentaje escrito, la pregunta que la plantilla no corrige (`void`, «No se corrige») y las dos salidas |
| **El plan del simulacro antes de montarlo** | `GET /student/mock-exams` (lee la convocatoria); `MockExamPage.tsx` (`/simulacros`) | `test_student_result_api.py`: 80 + 5 y 20 + 5, la banda 0-50, el mínimo 25, la penalización `1/3` y los 120 minutos **leídos del perfil**; los bloques III y IV con sus temas; y la variante corta con las cifras de la aplicación (40 y 48 min, **sin** reservas). Otra prueba monta el simulacro y comprueba que el tiempo que prometía el plan es el que tiene la sesión |
| **Los exámenes oficiales importados** | `GET /student/official-exams` y `POST /student/official-exams/{posicion}/sessions`; `OfficialExamsPage.tsx` (`/examenes`) | `test_student_result_api.py`: con un examen importado (80 + 5 y su plantilla enlazada) se lista y se monta (201, modo `official_exam`, 85 preguntas y 120 minutos); una posición que no existe es 404; **sin** ninguno, la lista sale vacía y no se rellena. `studentExamenes.test.tsx` (4) comprueba las dos pantallas, incluido el «Todavía no hay exámenes oficiales importados» |
| **Los fallos, y el test que sale de ellos** | `GET /student/mistakes`; `MistakesPage.tsx` (`/fallos`) | `test_student_result_api.py`: tres fallos con su tema, su fecha y cuántas veces; el reparto por tema suma; aplazar un repaso baja el «para repasar hoy»; una pregunta fallada y después acertada **deja de estar** (manda el último intento, igual que el filtro `failed`). `studentFallos.test.tsx` (5) comprueba el test con todos los fallos y el de un solo tema, y que sin fallos no se ofrece ninguno |
| **El progreso, con el porcentaje escrito** | `GET /student/progress` (con `tests_finished`); `ProgressPage.tsx` (`/progreso`) | `test_student_result_api.py`: `tests_finished` cuenta los tests **terminados** (no los que caben en el historial de 20). `studentProgreso.test.tsx` (4): el porcentaje escrito por bloque y por tema, los aciertos, «Sin empezar» en lo que no se ha tocado, los más flojos y la evolución con enlace al resultado |
| **El cierre, con capturas a dos anchos** | `apps/web/tests/screens/screens.spec.ts` (42 capturas) | `artifacts/screens/`: `resultado`, `simulacros`, `examenes`, `fallos` y `progreso`, en escritorio y móvil, **las diez con 0 violaciones de axe y 0 palabras prohibidas**. El resultado, los fallos y el progreso se capturan sobre un test **terminado de verdad**, montado por la API (conjunto, plantilla, catalogación, respuestas y cierre) antes de entrar |
| **Que no se desborde a 390 px** | `apps/web/tests/e2e/first-run.spec.ts`: la puerta de responsividad recorre ahora también `/simulacros`, `/examenes`, `/fallos` y `/progreso` | Las filas de estas pantallas (código, título, cifras y acción) se apilan en móvil con `minmax(0, 1fr)` y `overflow-wrap: anywhere`; ninguna hoja escribe un color a mano (la prueba de tokens de F13 lo sigue comprobando). **Medido en las capturas**: las diez imágenes de móvil miden exactamente **390 px de ancho** (una captura de página completa con desplazamiento horizontal saldría más ancha), y las de escritorio, 1280 |

**Puertas: 18/18**, ejecutadas en **33:01 minutos** sobre este árbol (1.396 pruebas de backend entre
unitarias —741—, integración —626— y contrato —29—, 318 de componentes, 61 E2E —con la puerta de
responsividad ampliada a las cuatro pantallas nuevas— y las 18 puertas del `gates.ps1`). El registro
está en `F:\temp-opofuente\gates-f14-alumno.txt`.

**Y una prueba que falla antes**: las cinco pantallas se escribieron **después** de sus pruebas. La
primera pasada de `npm run test:web` falló en los cinco ficheros nuevos con «Failed to resolve import
… Does the file exist?» —es decir, las pruebas no encontraban las pantallas, que es exactamente lo que
tienen que decir— y la segunda pasó con 318/318. Lo mismo en el backend: `test_student_result_api.py`
se escribió contra las rutas nuevas y falló hasta que estuvieron.

## 4d. La tanda de apuntes con el gasto bajo control (f15)

Esta tanda vuelve al bloque A (los apuntes) con una regla nueva, la que manda en todo el bloque:
**prever antes de pagar**. Lo que se ha construido y lo que se ha medido:

| Qué | Dónde | Cómo se comprueba |
|---|---|---|
| **Elegir los temas por valor, medido y no heredado** | `F:\temp-opofuente\f15-scratch\valor_por_tema.py` (lectura de la base real; su tabla está abajo) | La tabla de las 33 filas sale de la base: por cada tema, sus grupos, sus preguntas y **cuántas tienen clave utilizable** (las que tienen clave, sin las que el paso B marca como contrarias a la norma). No es el orden del temario |
| **`--prever` dice lo que cuesta, no solo lo que rehace** | `application/topic_notes_service.py` (`_prevision_de_llamadas`) | `test_el_comando_prever_dice_lo_que_costaria_la_corrida_antes_de_pagarla` y `test_la_prevision_baja_cuando_el_tema_ya_esta_escrito`. Las dos **fallan antes** del arreglo |
| **El índice de un tema se ensaya antes de gastar** | `F:\temp-opofuente\f15-scratch\ensayo_reparto.py` (lectura) y `--esquema` | Ensayo del reparto: I.2 situaba 631 de sus 685 grupos por el enunciado y IV.2, 761 de 770; lo que no casa se sitúa por el texto de sus hechos. Tres patrones estaban mal y se vieron aquí, no en la factura |
| **Un encabezado del cuerpo que repite el título de otro apartado se quita** | `domain/notes_quality.py` (`sin_encabezados_repetidos_en_el_tema` con `titulos`) y `--limpiar-forma` | `test_un_encabezado_del_cuerpo_que_repite_el_titulo_de_otro_apartado_se_quita` (falla antes). Es lo que dejaba a I.2 con la forma en NO PASA: `cortes-funciones` llevaba un `### Defensor del Pueblo` dentro y el tema tiene su apartado «El Defensor del Pueblo» |

### I.2 (845 preguntas, 685 grupos), escrito y publicado el 11-oct

Se eligió **el primero por valor de los 30 que quedan**: 835 preguntas con clave utilizable, medido
sobre la base. Su índice se definió antes (`domain/catalogo_i_2.py`, 16 apartados) y se ensayó antes
de gastar un céntimo.

| Qué se midió | Valor |
|---|---|
| Cobertura (clave utilizable) | **669/703 = 95,2 % PASA** |
| Cobertura (todas las que tienen clave) | 669/835 = 80,1 % |
| Hechos | 1.233 (de 16 apartados) |
| Forma | **PASA** · 24.061 palabras de 49.320 · repetidos 2,9 % |
| Índice | PASA · 16 apartados · **0 grupos y 0 hechos sin materia** |
| Bandeja del propietario | **99 incidencias**: 73 `norma_cambiada`, 19 `clave_sospechosa`, 6 `hueco_sin_material`, 1 `pregunta_ambigua` |
| Llamadas y coste | **194 llamadas · 1,2187 $** |

**Lo que `--prever` dijo y lo que costó**, que es lo que pidió el propietario:

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 115 como mínimo y 195 como máximo | **194** |
| Coste | 0,72 $ como mínimo y 1,23 $ como máximo | **1,2187 $** |

La previsión **acertó la cota de arriba** (194 frente a 195; 1,2187 $ frente a 1,23 $) y falló la de
abajo por 79 llamadas: el bucle de huecos se llevó casi todo lo que separa el mínimo del máximo
(73 preguntas con la clave contradiciendo la norma, 19 en conflicto y 6 sin frase en los apuntes). Es
una corrida de las caras del rango, no de las baratas.

**Y una cosa que se dice porque no salió como se esperaba**: el tope por tema del bloque es **1,20 $**
y esta corrida hizo **1,2187 $**, 0,0187 $ por encima. La previsión ya lo avisaba —su máximo era
1,23 $— y la decisión fue seguir porque su **mínimo** (0,72 $) cabía de sobra; con el resultado
delante, la regla se endurece para los temas siguientes: **se escribe entero el tema cuyo máximo
previsto quepa en el tope**, y el que no, se deja para otra tanda o se le reduce el alcance. El
detalle está en `DECISIONES-TOMADAS-EN-EL-OBJETIVO.md`.

### I.4 (602 preguntas, 546 grupos), escrito y medido el 11-oct: **se queda en borrador**

Se eligió por la misma regla —es el 4.º por valor, 577 preguntas con clave— y **después de que su
previsión máxima (1,03 $) cupiera en el tope**, que es la regla endurecida tras lo de I.2.

| Qué se midió | Valor |
|---|---|
| Cobertura (clave utilizable) | **497/559 = 88,9 % NO PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 497/579 = 85,8 % |
| Hechos | 1.056 (de 15 apartados) |
| Forma | **PASA** · 27.787 palabras de 42.240 · repetidos 4,2 % |
| Índice | PASA · 15 apartados · 2 grupos y 4 hechos sin materia |
| Bandeja del propietario | **55 incidencias**: 30 `clave_sospechosa`, 17 `norma_cambiada`, 5 `pregunta_ambigua`, 3 `hueco_sin_material` |
| Llamadas y coste | **169 llamadas · 1,4625 $** |

**El motivo escrito del borrador**: contesta al 88,9 % de las 559 preguntas con clave utilizable y el
listón del §2.3 es el 90 %. **No se toca el listón**: le faltan 7 preguntas cubiertas y 62 de sus 546
grupos están sin cubrir, de los cuales 31 tienen la frase en los apuntes sosteniendo **otra letra**
que la clave y 3 no tienen frase. Como en I.6, buena parte del hueco es criterio del propietario
sobre las claves (47 de sus 55 incidencias son de la clave, no del texto), así que el tema queda en
borrador y visible en el panel, con esta frase.

**Y aquí la previsión falló, medido:**

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 96 como mínimo y 164 como máximo | **169** |
| Coste | 0,60 $ como mínimo y 1,03 $ como máximo | **1,4625 $** |

La cota de llamadas se quedó corta por 5 (169 frente a 164) y la de **dinero por un 42 %**. La causa
está medida: I.4 devolvió **11.518 tokens de salida por llamada** donde la media de las tres corridas
antiguas era 5.700, así que su llamada costó 0,00865 $ y no los 0,0063 $ de la tabla. Con eso:

- `COSTE_MEDIO_POR_LLAMADA_USD` sube a **0,0068 $** (la media de las **cinco** corridas medidas) y su
  docstring lleva las cinco, el recorrido de 0,0055 a 0,0087 y el aviso de que para un tema
  normativo denso la cota de arriba de `--prever` es un **suelo**, no un techo;
- y la decisión del tope de 1,20 $ por tema se toma sobre esa cota **más un tercio** cuando el tema
  es normativo y denso.

### La tabla que decide qué tema se escribe primero (medida sobre la base real, 11-oct)No es el orden del temario ni el de ningún documento: es, por cada tema, **cuántas preguntas tienen
una clave con la que se puede acertar** —el número que decide si el apunte sirve para aprobar—. Se
mide con `valor_por_tema.py` sobre la base real y se ordena por esa columna.

| # | Tema | Grupos | Preguntas | Con clave | **Clave utilizable** | Hechos | Estado |
|---|---|---|---|---|---|---|---|
| 1 | I.1 | 2.008 | 2.043 | 2.035 | **1.995** | 3.511 | hecho (publicado) |
| 2 | I.2 | 685 | 845 | 835 | **835** | 1.233 | **hecho en f15 (publicado)** |
| 3 | IV.2 | 770 | 807 | 797 | **797** | 0 | índice escrito (f15), sin redactar |
| 4 | I.4 | 546 | 602 | 577 | **577** | 1.056 | **borrador en f15 (88,9 %)** |
| 5 | II.4 | 501 | 577 | 566 | **566** | 0 | sin empezar |
| 6 | I.8 | 442 | 606 | 566 | **566** | 0 | sin empezar |
| 7 | I.7 | 377 | 586 | 550 | **550** | 0 | sin empezar |
| 8 | IV.5 | 423 | 460 | 452 | **452** | 0 | sin empezar |
| 9 | IV.7 | 474 | 528 | 511 | **449** | 958 | hecho (publicado) |
| 10 | III.4 | 411 | 434 | 433 | **433** | 0 | sin empezar |
| 11 | III.9 | 372 | 435 | 429 | **429** | 0 | sin empezar |
| 12 | I.5 | 347 | 415 | 404 | **404** | 0 | sin empezar |
| 13 | IV.6 | 324 | 354 | 340 | **340** | 0 | sin empezar |
| 14 | III.7 | 279 | 344 | 332 | **332** | 0 | sin empezar |
| 15 | III.1 | 287 | 324 | 318 | **318** | 0 | sin empezar |
| 16 | III.5 | 262 | 277 | 276 | **276** | 0 | sin empezar |
| 17 | IV.9 | 247 | 279 | 264 | **264** | 0 | sin empezar |
| 18 | I.6 | 191 | 303 | 283 | **258** | 346 | borrador (techo medido 84,1 %) |
| 19 | IV.8 | 237 | 253 | 252 | **252** | 0 | sin empezar |
| 20 | II.1 | 235 | 256 | 248 | **248** | 0 | sin empezar |
| 21 | IV.1 | 233 | 236 | 234 | **234** | 0 | sin empezar |
| 22 | II.3 | 185 | 226 | 224 | **224** | 0 | sin empezar |
| 23 | III.3 | 188 | 214 | 214 | **214** | 0 | sin empezar |
| 24 | II.5 | 162 | 200 | 196 | **196** | 0 | sin empezar |
| 25 | IV.10 | 192 | 199 | 194 | **194** | 0 | sin empezar |
| 26 | II.2 | 180 | 187 | 184 | **184** | 0 | sin empezar |
| 27 | III.8 | 153 | 185 | 182 | **182** | 0 | sin empezar |
| 28 | I.3 | 168 | 183 | 182 | **182** | 0 | sin empezar |
| 29 | IV.4 | 167 | 174 | 168 | **168** | 0 | sin empezar |
| 30 | IV.3 | 142 | 165 | 163 | **163** | 0 | sin empezar |
| 31 | III.2 | 157 | 168 | 162 | **162** | 0 | sin empezar |
| 32 | III.6 | 148 | 165 | 161 | **161** | 0 | sin empezar |
| 33 | I.9 | 136 | 145 | 137 | **137** | 0 | sin empezar |

*(La columna «clave utilizable» sale de la base: son las preguntas con clave activa o en borrador
**sin** las que el paso B marca como contrarias a la norma. En los tres temas ya escritos se ve el
efecto: I.1 baja de 2.035 a 1.995, IV.7 de 511 a 449 e I.6 de 283 a 258. En los 30 sin empezar no hay
hechos todavía, así que coincide con «con clave»: es el techo, y bajará cuando el paso B los lea.)*

**Puertas: 18/18**, ejecutadas en **41:25 minutos** sobre este árbol (742 pruebas unitarias de
backend, 630 de integración, 29 de contrato, 318 de componentes —34 ficheros—, 61 E2E de Playwright y
las 18 puertas del `gates.ps1`). El registro está en `F:\temp-opofuente\gates-f15-apuntes.txt`. **La
primera pasada no falló ninguna puerta**, así que no hubo que arreglar nada para que pasaran.

## 4e. El bloque C arranca: la bandeja de avisos y «No son preguntas» (f16)

Lo que se ha construido en esta tanda, y lo que se ha medido de cada cosa. **No ha gastado API**: es
interfaz, una migración y consultas de lectura sobre la base.

| Qué | Dónde | Cómo se comprueba |
|---|---|---|
| **El aviso se puede despachar** (era lo que faltaba: el alumno marcaba y el propietario no tenía dónde mirarlo) | `PATCH /notes-reports/{id}` con `{status, note}` y el actor en el cuerpo o en `X-OpoFuente-Actor` | `test_el_propietario_despacha_el_aviso_con_su_nota_y_su_evento`: el estado, la nota y el **evento de auditoría** (`notes.report_updated`, objeto `note_report`) en la misma escritura, y la auditoría **sin** el texto de la nota |
| **El estado que faltaba**: `in_progress` («lo he visto y estoy en ello») y la **nota** de lo que se ha hecho | Migración `0034_avisos_en_curso_y_nota` (columna `resolution_note` + `CHECK` de los cuatro estados), `domain/notes_reports.py`, `db_models.py` | `test_migrations_0034.py`: los cuatro estados entran y uno inventado no, la nota en blanco no entra, las restricciones y los índices de `0033` sobreviven a la recreación de la tabla, y la vuelta atrás devuelve los tres estados y deja «en curso» otra vez pendiente |
| **Qué cuenta como despachado lo decide el dominio** | `reviewed_at_for`: cerrar deja fecha, reabrir la borra; la nota no se tira al reabrir | `test_cerrar_un_aviso_deja_fecha_y_reabrirlo_la_borra`, `test_reabrir_un_aviso_borra_la_fecha_de_revision_y_conserva_la_nota` |
| **Los números de la bandeja, contados en la base** | Los cuatro contadores y el `total` del filtro viajan con la lista (`pending` sigue siendo solo `open`) | `test_la_bandeja_filtra_por_estado_tema_y_busqueda`: por estado, por tema y por texto, y el contador de pendientes **no** mira el filtro |
| **La pantalla de la bandeja**: tema, apartado, motivo del alumno, fecha, estado, **enlace al apartado exacto**, filtros y búsqueda, y los cuatro botones con su nota | `apps/web/src/pages/NoteReportsPage.tsx` (`/admin/avisos`), `features/avisos/NoteReportRow.tsx`, el contador en el menú (`app/sectionCounts.ts`) | `noteReports.test.tsx` (6) y las capturas `admin-avisos-{escritorio,movil}.png` |
| **El enlace al apartado deja el apartado a la vista** —y hacía falta un arreglo: el ancla del navegador **no** basta, porque los apuntes llegan por la API después del primer pintado | `app/apartadoDeLaDireccion.ts` (`useApartadoDeLaDireccion`), montado en el marco del alumno (`StudentZone`, `app/routes.tsx`) | Medido con Playwright **antes** del arreglo: apartado a 5.894 px y `scrollY` en **0**. `apartadoDeLaDireccion.test.tsx` (4) y la prueba de extremo a extremo «el enlace al apartado deja el apartado a la vista» (apartado detrás de 120 párrafos, `toBeInViewport` y `scrollY > 1000`) |
| **La sección «No son preguntas»** (D6): los enunciados rotos y las de otra administración, con su motivo, quién lo decidió y un buscador; **sin** borrar ni editar nada | `apps/web/src/pages/NoSonPreguntasPage.tsx` (`/admin/no-son-preguntas`) y `q` en `GET /question-exclusions` | `noSonPreguntas.test.tsx` (5), `test_los_enunciados_fuera_de_temario_se_pueden_buscar_y_contar_por_motivo` y las capturas `admin-no-son-preguntas-{escritorio,movil}.png` |
| **Las cifras por motivo, dichas desde la base** | `totals_by_reason` en la respuesta de exclusiones, contado con un `GROUP BY` y no contando la página | La captura de «No son preguntas» dice **769** de enunciado roto y **325** de otra administración, medidos en la base |

**Lo que se ha medido en los datos reales del propietario** (solo lectura, y con una **copia** para
retratar):

- `notes_reports` (los avisos del alumno): **0 filas**, y la tabla **no existe** en su base, que está
  en la revisión **`0032`**: las migraciones `0033` y `0034` **no se han aplicado nunca** a sus datos.
  Es decir: el botón «Esto está mal» guarda en la copia y en las pruebas, pero en su base falla hoy
  por falta de tabla. Se aplica con `scripts/migrate.ps1` (ver `PARA-EL-PROPIETARIO.md`).
- `question_curriculum_exclusions` (lo que no son preguntas): **769 `enunciado_roto` + 325
  `otra_administracion`**, contados en la base. El documento decía «754 + los nuevos»: son 769.
- `notes_incidents` (la bandeja del motor): **333**, y **no tiene ni ruta ni pantalla**: es la primera
  mitad del §4.1 del objetivo («una sola bandeja con todo lo que necesita su criterio»), y queda
  fuera de esta tanda, que era la mitad del alumno.
- Las **333** y las **769 + 325** son cosas distintas: el número «333 avisos» de la nota del
  propietario es la bandeja **del motor**, no la del alumno. La bandeja del alumno nace **vacía**.

**Las capturas** (`artifacts/screens/`): `admin-avisos-{escritorio,movil}.png` y
`admin-no-son-preguntas-{escritorio,movil}.png`, con **0 violaciones de axe** y **0 errores de
consola** en las cuatro, y **390 px exactos** de ancho en las dos de móvil (medido en el PNG: una
captura de página completa más ancha que el viewport sería un desplazamiento horizontal). Salen de
una **copia** de la base real (`F:\temp-opofuente\f16-datos`, nunca la suya): la de avisos lleva un
aviso **creado por la ruta del alumno** sobre los apuntes reales de IV.7 —al no haber ninguno en la
base, y no inventarse filas a mano— y la de «No son preguntas», los **769** enunciados rotos reales.

**Y un hallazgo del detector de palabras prohibidas**: en el panel, y con los datos reales, sale
**una** palabra: **«Celador»**, y no la pone ninguna de las dos pantallas nuevas —viene del **selector
de oposición** del marco del panel, que enseña las oposiciones del propietario—. La regla está escrita
para la **zona del alumno** («esta zona es solo de TAI») y la propia puerta del rediseño la aplica
solo a `STUDENT_NAV_ITEMS`; el panel la enseña a propósito. Lo que sí era de estas pantallas —los
títulos del programa del filtro de tema, que llevaban «representación» y «versiones» a la interfaz—
está arreglado marcándolos como contenido, y la prueba E2E lo comprueba: **0 jerga interna** en las
dos pantallas a los dos anchos.

**Puertas: 18/18**, ejecutadas sobre este árbol: **747** unitarias de backend, **641** de integración,
**29** de contrato, **333** de componentes (37 ficheros) y **67** de extremo a extremo. El registro
está en `F:\temp-opofuente\gates-f16-panel.txt`. **De los tiempos de esta corrida no me fío**: el
reloj de la máquina saltó a mitad (la suite de integración se atribuye **12:03:33** de duración, que
es imposible, y el contador de las puertas dice 11:24 min), así que aquí no se da ninguna duración
como medida. Lo que sí es del registro son los códigos de salida y los recuentos.

Las puertas hicieron falta **cinco intentos**, y se cuentan todos porque un fallo de puerta que se
repite es información:

1. **intento 1**: se **paró a propósito** en la puerta 7, para meter el arreglo del ancla (abajo) antes
   de gastar otra corrida entera;
2. **intento 2**: falló la **puerta 1** (`ruff format --check`): dos ficheros de prueba nuevos sin
   formatear. Se pasó `ruff format` y se repitió;
3. **intento 3**: falló la **puerta 7** con `test_changes.py` — **ajeno y no reproducible**; se cuenta
   con su evidencia más abajo;
4. **intento 4**: falló la **puerta 18** (E2E) con
   `strict mode violation: getByRole('region', { name: 'Fuera de temario' }).getByLabel('Tema')
   resolved to 2 elements`. La causa era **mía**: la prueba nueva de «No son preguntas» dejaba su marca
   de fuera de temario en la base compartida de la suite, y la región de la cola de clasificación pinta
   **un selector «Tema» por fila**: dos filas, dos controles con el mismo nombre accesible, y Playwright
   —con razón— no elige. La prueba nueva ahora **levanta su marca al terminar** (asignándole un tema,
   que es como la levanta la aplicación) y comprueba que no deja ninguna. **No se tocó el localizador de
   la otra prueba ni se relajó nada**; su registro está en
   `F:\temp-opofuente\gates-f16-panel-intento2-fallo-e2e-topic-review.txt`;
5. **intento 5**: **18/18**, con el registro en `F:\temp-opofuente\gates-f16-panel.txt`.

Lo único que cambió en el árbol **después** de la corrida que dio 18/18 es esta propia línea del
registro (documentación): ninguna puerta lee `docs/*.md`.

**Y una prueba que falla antes**: el dominio, la migración, la ruta de despacho y la búsqueda se
escribieron **antes** que su implementación. Con el código de `main` y solo las pruebas nuevas: **7
rojas** (las 5 del despacho y la búsqueda de la bandeja, las 2 de exclusiones) y **1 error de
colección** (el test del dominio no encontraba `CLOSED_STATUSES`). Con la implementación puesta, esos
ficheros pasan **36 de 36**; el registro del rojo está en `F:\temp-opofuente\f16-scratch\rojo-antes.txt`.

**Y un rojo que no era de esta tanda** (se anota, no se toca): en la primera corrida de las puertas,
la 7 falló **una vez** en`test_changes.py::test_una_version_nueva_propone_un_cambio_con_su_diff_y_sus_afectados`
(`assert cambio["sections_changed"] == 1` dio **0**, en `test_changes.py:145`). No es de esta tanda y
no se ha tocado la prueba:

- es del bloque de cambios, y el diff de esta tanda **no toca ni un fichero** de ese camino
  (`change_*`, `document_*`, `extraction*`, `ingestion*`, `jobs*`): lo que se toca es `notes_reports`,
  el `q` de las exclusiones y la interfaz del panel;
- **corrió antes que ninguna prueba nueva**: en la suite, `test_changes.py` está al **6 %** y las
  nuevas entran al **50 %** (`test_migrations_0034`), **69 %** (`test_question_topics_bulk_api`) y
  **80 %** (`test_student_notes_api`). Lo único común son los módulos importados;
- **pasa en aislamiento** (`1 passed`) y **el fichero entero** (`9 passed`) en este mismo árbol;
- y **vuelve a pasar en la corrida completa** siguiente (`test_changes.py .........`, 9 de 9), en el
  mismo punto de la suite.

Es decir: una prueba **inestable bajo carga** —esa corrida de la suite de integración fue la más lenta
de las tres, con la máquina ocupada por otros proyectos—, no un fallo del código de esta tanda: en la
corrida siguiente el mismo fichero pasó entero (`test_changes.py .........`). El registro de la corrida
que falló se guarda en `F:\temp-opofuente\gates-f16-panel-intento1-fallo-test_changes.txt`.

**Lo que se queda fuera, y por qué**:

1. **la bandeja del motor** (las 333 incidencias `notes_incidents`: claves sospechosas, huecos,
   normas cambiadas) sigue **sin ruta y sin pantalla**: el §4.1 del objetivo la pide **en la misma
   bandeja** que los avisos del alumno, y eso es una tanda propia (con la ficha de pregunta, los
   apuntes y el temario del bloque C). Esta tanda era la mitad del alumno;
2. **la aplicación de las migraciones a su base**: no se ha tocado —las copias son la tarea D5, que
   esta tanda tiene prohibida—, y por eso queda dicho arriba y en `PARA-EL-PROPIETARIO.md`;
3. **las tres violaciones de accesibilidad del panel** que el §5.9 dejó anotadas (`/cambios` y
   `/buscar` a 390 px): son de otras pantallas y siguen ahí. Las dos de esta tanda salen a **0**.

## 4f. La tanda de apuntes sigue, por valor y con el tope medido (f17)

Esta tanda vuelve al bloque A (los apuntes) con la regla que se acordó en f15 y **la aplica tal
cual**: primero el tema de más valor de los que quedan, `--esquema` y ensayo antes de facturar,
`--prever` enseñado antes de la corrida, y un tope por tema que es **la cota de arriba de `--prever`
más un tercio** cuando el tema es normativo y denso, respaldado por un tope de tiempo
(`--tiempo-maximo`) que para la corrida conservando lo escrito.

| Qué | Dónde | Cómo se comprueba |
|---|---|---|
| **El índice de II.4**, escrito y ensayado antes de gastar | `domain/catalogo_ii_4.py` (17 apartados) y su registro en `topic_index.py` | `ensayo_reparto.py II.4`: **481 de 501 grupos** situados por el enunciado; `--esquema` dice **`revision del indice: PASA`**; 58 pruebas de `topic_index` en verde; `ruff check` limpio |
| **El índice de I.8**, escrito y ensayado antes de gastar | `domain/catalogo_i_8.py` (18 apartados, estructurados por las normas del tema) | `ensayo_reparto.py I.8`: **426 de 442 grupos** situados por el enunciado; **`revision del indice: PASA`**; los 16 que no se sitúan son preguntas de **otro** tema que están en el banco de I.8 (McCall, la Ley 34/2002, arquitecturas cliente/servidor) y van a la bandeja con su motivo, que es lo que el índice manda |

### IV.2 (807 preguntas, 770 grupos), escrito y publicado el 12-oct

Es el **tercero por valor** (797 preguntas con clave) y su índice venía de f15. Es la corrida **más
barata de la serie** y la que deja el tema con la mejor cobertura medida hasta hoy.

| Qué se midió | Valor |
|---|---|
| Cobertura (clave utilizable) | **757/758 = 99,9 % PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 757/797 = 95,0 % |
| Hechos | 1.543 antes de deduplicar → **1.126** redactados (417 repetidos agrupados) |
| Apartados | **16** (13 materias; 3 se partieron por el tope de 150 hechos) |
| Forma | **PASA** · 32.567 palabras de 61.720 · repetidos **0,2 %** |
| Índice | PASA · **0 grupos y 0 hechos sin materia** |
| Bandeja del propietario | **36 incidencias**: 35 `norma_cambiada`, 1 `clave_sospechosa`, 0 huecos y 0 ambiguas |
| Llamadas y coste | **182 llamadas · 0,7585 $** · 45 minutos |

**Lo que `--prever` dijo y lo que costó:**

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 129 como mínimo y 219 como máximo | **182** (0 fallidas) |
| Coste | 0,88 $ como mínimo y 1,49 $ como máximo | **0,7585 $** |

La previsión acertó el rango por el medio y **el coste salió por debajo del mínimo**: 182 llamadas a
**0,00417 $** cada una, donde la media de la tabla es 0,0068 $. La causa está medida: devolvió
**4.432 tokens de salida por llamada** (la media de las corridas anteriores es ~8.000) y traía
1,29 M de los 1,83 M de tokens de entrada en caché. Un tema **técnico**, con hechos cortos y muy
repetidos (417 de 1.543 se agruparon), sale más barato que uno normativo denso.

**Las tres cosas que conviene retener de esta corrida:**

1. **`--limpiar-forma` no tocó nada** (0 apartados): es la primera corrida de la serie que termina con
   la forma en PASA **sin reparaciones**. I.1 necesitó cuatro tablas y dos encabezados; I.2, un
   encabezado;
2. **el listón de repetidos no apretó**: IV.2 sale al **0,2 %**, así que la discrepancia del §5.9
   (el documento pide ≤ 3 % y el código lleva el tope al 5 %) **no le afecta** ni en un sentido ni en
   el otro. Sigue sin tocarse, como en f15;
3. **«sin contestar por los apuntes: 0»**: en IV.2 no hay ni una pregunta cuyo dato no esté en el
   texto. De sus 770 grupos, 734 quedaron cubiertos con letra y cita (714 a la primera y 20 tras
   añadir material en el bucle de huecos) y el resto está «a revisión» porque **su clave** no se puede
   usar, no porque falte el texto. Es lo contrario de I.6, y es lo que explica el 99,9 %.

**Y una comprobación que hizo el propio camino**: el informe de la corrida y `--medir` dan **la misma
cifra** (757/758 y 757/797), contada dos veces por caminos distintos —una al terminar la corrida y
otra leyendo lo guardado—. Las cifras de este documento son las de `--medir`.

### II.4 (577 preguntas, 501 grupos), escrito y publicado el 12-oct

Es el **quinto por valor** (566 preguntas con clave). Su índice se escribió **y se ensayó en esta
tanda** (`domain/catalogo_ii_4.py`, 17 apartados, 481 de sus 501 grupos situados por el enunciado),
que es el orden que manda el bloque: el árbol se decide antes de pagar.

| Qué se midió | Valor |
|---|---|
| Cobertura (clave utilizable) | **443/462 = 95,9 % PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 443/568 = 78,0 % |
| Hechos | 1.046 antes de deduplicar → **848** redactados (195 repetidos agrupados) |
| Apartados | **17** · ninguno pasó del tope de 150 hechos, así que **no hubo que partir ninguno** |
| Forma | **PASA tras la limpieza** · 26.367 palabras de 41.840 · repetidos 0,3 % |
| Índice | PASA · 17 apartados · 848 hechos · **2 grupos y 3 hechos sin materia** (a la bandeja) |
| Bandeja del propietario | **82 incidencias**: 71 `norma_cambiada`, 11 `clave_sospechosa` |
| Llamadas y coste | **166 llamadas · 0,7014 $** · 50 minutos |

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 92 como mínimo y 158 como máximo | **166** (0 fallidas) |
| Coste | 0,63 $ como mínimo y 1,07 $ como máximo | **0,7014 $** |

La cota de llamadas se quedó corta por 8 y el coste cayó por el medio del rango: el bucle de huecos
(71 claves que contradicen la norma y 11 en conflicto) no se puede prever, y el precio por llamada sí
depende del tema. El tope (1,07 × 4/3 = **1,43 $**, con 5.000 s de tiempo) **no se activó**.

**Y lo que hace distinta esta corrida: acabó con la forma en NO PASA y no se volvió a pagar.**
`--limpiar-forma` (0 $) arregló las dos cosas que la puerta encontró —una tabla cuya fila tenía una
celda de más y cuatro apartados con la misma cabecera— y hizo falta **extender dos reparaciones**
(§3, arreglos 11 y 12, cada uno con su prueba que falla antes). Sin ellas, poner los títulos al día
habría costado entre 0,34 $ y 0,80 $ según `--prever`: es la primera vez en el bloque que un rojo de
forma se cierra **sin volver a llamar al modelo**.

**Y la cifra que este tema comparte con IV.2**: «sin contestar por los apuntes: **0**». De los 501
grupos, 419 quedaron cubiertos con letra y cita (403 a la primera, 16 tras añadir) y los 82 que
quedan «a revisión» lo están porque **su clave** no se puede usar, no porque falte el texto.

### I.8 (606 preguntas, 442 grupos), escrito el 12-oct: **se queda en borrador, con dos motivos**

Es el **sexto por valor** (566 preguntas con clave). Su índice se escribió y se ensayó en esta tanda
(`domain/catalogo_i_8.py`, 18 apartados estructurados por las normas del tema, 426 de 442 grupos
situados por el enunciado).

| Qué se midió | Valor |
|---|---|
| Cobertura (clave utilizable) | **423/516 = 82,0 % NO PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 423/571 = 74,1 % |
| Hechos | 815 antes de deduplicar → **617** redactados (191 repetidos agrupados) |
| Apartados | **18** |
| Forma | **PASA** · 23.285 palabras de 32.600 · repetidos 0,3 % |
| Índice | PASA · 18 apartados · 617 hechos · **4 grupos y 7 hechos sin materia** |
| Bandeja del propietario | **60 incidencias**: 43 `norma_cambiada`, 9 `hueco_sin_material`, 7 `clave_sospechosa`, 1 `pregunta_ambigua` |
| Llamadas y coste | **142 llamadas · 1,2119 $** · 84 minutos, **parada por su tope de tiempo** |

**Los dos motivos del borrador, escritos como manda D2:**

1. **la cobertura es el 82,0 %** de las 516 preguntas con clave utilizable (listón 90 %): le faltan
   41 preguntas cubiertas. **No se toca el listón**;
2. **la corrida no terminó**: el tope de tiempo (5.000 s) la paró con **389 de los 442 grupos
   comprobados**, así que el 82,0 % es un **suelo**, no el techo. Lo dice el propio informe:
   «se agotó el tiempo de la corrida: no se han hecho las llamadas que quedaban. Lo escrito está
   guardado y volver a lanzar el comando sigue desde ahí».

**No se ha reanudado en esta tanda a propósito, y el porqué es la medida que faltaba**: la corrida
costó **1,2119 $** de un tope de **1,32 $** (la cota de arriba de `--prever`, 0,99 $, más un tercio).
Quedaban 0,11 $ de margen y reanudar cuesta más que eso. **El tope se respetó** —ni el dinero ni el
tiempo se pasaron— y lo escrito se conservó, que es exactamente para lo que está el mecanismo.

**Y esta corrida es la demostración de que la regla del tope está bien puesta**: la cota de arriba de
`--prever` (0,99 $) no habría bastado, y el tope «duro» de 1,20 $ de f15 **se habría cruzado**
(1,2119 $). Con la cota **más un tercio**, la corrida se quedó dentro. La causa está medida: I.8
devolvió **11.617 tokens de salida por llamada** (la media de la tabla es ~8.000), así que su llamada
costó **0,00853 $**. Es el segundo tema normativo y denso de la serie —tras I.4, con 0,00865 $— y se
comporta exactamente como la regla supone.

**Puertas: 18/18**, ejecutadas en **38:45 minutos** sobre este árbol (750 pruebas unitarias de
backend, 641 de integración, 29 de contrato, 333 de componentes —37 ficheros—, **67** de extremo a
extremo de Playwright y las 18 puertas del `gates.ps1`). El registro está en
`F:\temp-opofuente\gates-f17-apuntes.txt`. **La primera pasada no falló ninguna puerta**, así que no
hubo que arreglar nada para que pasaran: los dos arreglos de motor de esta tanda (§3, 11 y 12) se
hicieron **durante** el trabajo de los temas, con su prueba que falla antes, y llegaron a las puertas
ya en verde. Es la segunda tanda seguida sin un solo intento fallido de puerta (f15 también fue 18/18
a la primera).

**Capturas**: **no se han hecho**, y se dice por qué. Lo que cambia esta tanda en la lectura del
alumno son **datos** (los apuntes de IV.2 y de II.4, y el borrador de I.8), no código de lectura:
ninguna pantalla de la zona del alumno ni del panel se ha tocado, y la puerta 18 (E2E de Playwright)
recorre esa misma ruta con el texto real de un tema. Lo que **sí** cambió de código es `notes_quality`
y el comando `apuntes`, que no los lee ninguna pantalla; su efecto se ve en la forma de los apuntes
(§4f) y en las tablas escapadas.

## 4g. El bloque C sigue: la bandeja del motor y la reclasificación de las incidencias (f18)

Esta tanda cierra la **otra mitad** del §4.1 del objetivo —la bandeja del **motor**— y obedece además
al **§2** de `AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO-2026-10.md`, que manda en lo que diga el goal.
**No ha gastado API**: es interfaz, una migración, reglas mecánicas y consultas.

### Lo que se ha construido

| Qué | Dónde | Cómo se comprueba |
|---|---|---|
| **La incidencia se puede despachar** (lo que faltaba: el motor la escribía y **no tenía ningún estado**) | `PATCH /notes-incidents/{id}` con `{status, note}` y el actor en el cuerpo o en `X-OpoFuente-Actor` | `test_el_propietario_despacha_la_incidencia_con_su_nota_y_su_evento`: estado, nota y **evento de auditoría** (`notes.incident_updated`, objeto `note_incident`) en la misma escritura, y la auditoría **sin** el texto de la nota |
| **Los estados que faltaban**: los cuatro que la aplicación ya usa para despachar una bandeja, más la nota y la fecha de revisión | Migración **`0035_incidencias_despachables`** (`status`, `resolution_note`, `reviewed_at`, sus dos `CHECK` y el índice `status·category`), `domain/notes_incidents.py`, `db_models.py` | `test_migrations_0035.py` (6): los cuatro estados entran y uno inventado no, la nota en blanco no entra, las restricciones e índices de `0031` sobreviven a la recreación de la tabla, y la vuelta atrás se lleva las tres columnas y devuelve las categorías nuevas a las de antes |
| **Las seis categorías del §2**, con su orden de comprobación | `CategoriaIncidencia` (dominio), `domain/notes_incidents.py` (`categoria_reclasificada`) y el `CHECK` de `0035` | `test_notes_incidents_domain.py` (18): el orden (forma → cuarentena → clave → norma → apuntes), las cuatro reglas mecánicas, el falso positivo y la guarda del truncado |
| **La reclasificación de las 453**, por un comando y por rutas auditadas | `python -m opofuente.tools.reclasificar_incidencias` (ensayo por defecto; `--aplicar` hace **copia verificada** antes) | `test_reclasificar_incidencias.py` (7): el falso positivo sale de la bandeja, `norma_cambiada` queda a cero, lo irreparable sale del temario con `enunciado_roto`, todo deja su evento y **la segunda pasada escribe cero cambios** |
| **La pantalla de la bandeja**: categoría, motivo, el porqué del dominio, la pregunta que la provoca, la frase verificada, el apartado, el material y los cuatro botones con su nota | `apps/web/src/pages/IncidentsPage.tsx` (`/admin/incidencias`), `features/incidencias/IncidentRow.tsx`, el contador en el menú (`app/sectionCounts.ts`) | `incidencias.test.tsx` (9) y `tests/e2e/incidencias.spec.ts` (3) |
| **El enlace a lo que la provoca**, sin buscarlo a mano | Al **apartado de los apuntes** por su ancla (`/temario/<tema>#apartado-<ancla>`), a la **pregunta** en el banco (`/admin/preguntas?pregunta=<id>`, que es nuevo) y al **material** del que salió la clave (`/admin/biblioteca?documento=<id>`) | La prueba de extremo a extremo pulsa el enlace a la pregunta y comprueba que **abre su ficha**; el enlace al apartado se comprueba por su `href` y el caso sin apartado dice que no se pudo situar |
| **Las cifras por categoría, contadas en la base** | `totals_by_category` con un `GROUP BY` que **no mira el filtro**, y las cuatro de estado | La prueba de la pantalla enseña **una** fila y comprueba que los botones siguen diciendo 29/158/200/0/34/9 con «Todas 430» |

### Las cifras nuevas, contadas en la base

Medidas en la copia de la base real (`F:\temp-opofuente\f18-datos`, migrada a `0035`) **después** de
pasar el comando con `--aplicar --excluir-no-reparables`:

| Categoría | Antes | **Después** |
|---|---|---|
| `pregunta_mal_importada` | — | **29** |
| `clave_no_fiable` | — | **158** |
| `clave_sospechosa` | 110 | **200** |
| `norma_cambiada` | 291 | **0** |
| `hueco_sin_material` | 40 | **34** |
| `pregunta_ambigua` | 12 | **9** |
| *(fuera: no era una incidencia)* | — | **23** |
| **Total en la bandeja** | **453** | **430** |

Se escribieron **303 reclasificaciones** y **23 salidas** (326 cambios, cada uno con su evento), y
**18 preguntas** salieron del temario con `enunciado_roto` (de 769 a 787). Por regla mecánica:
`menos_de_tres_opciones` 18, `opcion_con_patron_de_otra` 9, `opcion_truncada` 2,
`opciones_duplicadas` 1. Las **21** que llevan la referencia del examen pegada al enunciado **no** se
tocan: el §2 dice que eso se limpia, y limpiar un enunciado es escribir una versión nueva de la
pregunta (va con la ficha de pregunta, §5.4).

**Los numeradores y denominadores de cada caja**, que es lo que hace falta para leer las cifras:

| Caja | Cuántas | De dónde salen y qué se hizo |
|---|---|---|
| `pregunta_mal_importada` | **29** | 18 por `menos_de_tres_opciones` (esas 18 son las que han salido del temario), 8 por una opción fundida, 2 por una opción cortada y 1 por dos opciones repetidas. Las **11** reparables se quedan en la bandeja con su regla escrita |
| `clave_no_fiable` | **158** | todas de conjuntos con la clave en cuarentena: **10 de los 60** conjuntos con 15 o más comprobaciones pasan del 30 % (otros 6 quedan `dudosa` entre el 15 % y el 30 %, y 44 son fiables; 84 conjuntos tienen menos de 15 y no se juzgan) |
| `clave_sospechosa` | **200** | **85** con la frase de los apuntes que lo demuestra y **115** sin ella (el motor solo la guardaba para los conflictos de letra; esas filas lo dicen en pantalla) |
| `norma_cambiada` | **0** | ninguna: la cita de la norma vigente con su versión o fecha no está en los datos, y sin ella la categoría no se puede afirmar |
| `hueco_sin_material` | **34** | de las 40: 4 se fueron a `pregunta_mal_importada` y 2 eran falsos positivos |
| `pregunta_ambigua` | **9** | de las 12: 3 eran falsos positivos y ninguna otra regla las toca |
| **fuera de la bandeja** | **23** | falsos positivos: la letra de los apuntes **está** en la clave (18 venían de `norma_cambiada`, 3 de `pregunta_ambigua` y 2 de `hueco_sin_material`) |
| **fuera del temario** | **787** | las marcas de `enunciado_roto` de «No son preguntas»: las 769 de antes más las **18** de esta tanda |

### Qué cambia esto en el veredicto de un tema (§3), medido

**La reclasificación de categorías no cambia ninguna cobertura.** El denominador que decide es «clave
utilizable», y sale de los **hechos dudosos** del paso B
(`topic_notes_service.py:361-365` construye `dudosos_de_la_clave` con `hecho.doubtful`, y las cuatro
llamadas que lo usan —líneas 379, 395, 883 y 943— pasan `clave_utilizable=grupo.signature not in
dudosos_de_la_clave`), **no** de `notes_incidents`. Lo que sí lo toca son las **18 preguntas que han
salido del temario**: una pregunta fuera de temario no entra en la comprobación de los apuntes. Medido
grupo a grupo en la copia:

| Tema | Grupos que se van enteros | De esos, en el denominador | Cubiertos (numerador) | Grupos que se quedan con otras preguntas |
|---|---|---|---|---|
| **I.6** | 5 | **5** | 0 | 4 |
| **IV.7** | 1 | **1** | 0 | 0 |
| **I.2** | 1 | **1** | 0 | 1 |
| **IV.2** | 1 | **1** | 0 | 0 |
| **I.4** | 0 | 0 | 0 | 3 |
| **II.4** | 0 | 0 | 0 | 2 |

Es decir: **de las tres que el §3 manda volver a medir, I.6 pierde 5 grupos del denominador, I.4
ninguno e I.8 ninguno**; y **ninguno de los que se van estaba cubierto**, así que el numerador no
baja. El efecto es de uno o dos puntos **a favor** en I.6 (que está en borrador por el 72,5 % y sigue
por debajo del 90 %) y **no cambia ningún veredicto**. La vuelta a medir de I.6, I.4 e I.8 que pide el
§3 sigue siendo del §1 (la cuarentena sí saca preguntas del denominador) y este dato es el trozo que
aporta esta tanda.

### El defecto del motor que explicaba las etiquetas, con su evidencia

La categoría `norma_cambiada` **nunca** describió una norma cambiada. El motor la pone cuando
`clave_dudosa=True`, es decir cuando **alguno de los hechos de la pregunta es dudoso**, y lo hace
**antes** de mirar la letra: `application/topic_notes_service.py:1019` pasa
`clave_dudosa=any(hecho.doubtful …)` y `domain/topic_notes.py:814` devuelve `DUDOSA` +
`CLAVE_CONTRADICE_LA_NORMA` sin comparar letras. De ahí los falsos positivos: 23 incidencias cuya letra
de los apuntes **está** en la clave. **No se ha tocado el motor** (esta tanda lo tiene prohibido): la
reclasificación lo corrige por encima, la categoría pasa a significar lo que dice el §2 y el defecto
queda aquí escrito con su línea de código.

### La prueba que falla antes

Con el código de `main` (`db422ba`) y **solo los ficheros de prueba nuevos**: el dominio no existe
(`ModuleNotFoundError: opofuente.domain.notes_incidents`), la migración no tiene columnas
(`no such column: status`), la ruta de la bandeja es un **404** y la pantalla no está
(`Failed to resolve import … IncidentsPage`), con el menú del panel esperando **14** entradas donde
ahora hay **15**. El registro está en `F:\temp-opofuente\f18-scratch\rojo-antes.txt`.

### Las capturas

`artifacts/screens/admin-incidencias-categoria-hueco_sin_material-{escritorio,movil}.png`, con **0
violaciones de axe** y **0 errores de consola** en las dos, **1280 px** y **390 px exactos** de ancho.
Salen de la **copia** (`F:\temp-opofuente\f18-datos`), nunca de la base del propietario, y **con las
incidencias reales ya reclasificadas**: el filtro es `?categoria=hueco_sin_material` (34 incidencias
reales) porque sin filtro el PNG mide **262.914 px de alto** —medido— y no hay visor que lo abra; las
**seis cifras** se ven igual en los botones, porque se cuentan en la base y no miran el filtro (§4 de
las decisiones del 13-oct). Del detector de palabras prohibidas, con los datos reales, sale **una**:
**«Celador»**, y no la pone esta pantalla —viene del **selector de oposición** del marco del panel, el
mismo hallazgo que en f16—. El **Y no se han podido mirar a ojo**: el modelo de esta sesión no lee
imágenes; lo que se declara de ellas es lo que el guion mide (ancho exacto, violaciones, errores y
tamaño).

### Las puertas y las pruebas locales

**Las 18 puertas no se han corrido en esta tanda**, y se dice por qué: el §2 del documento de ajustes
manda que **primero** corra el bloque del **§1** (claves fiables y cuarentena `key_reliability`), y las
dos baterías no pueden usar a la vez el puerto 8765 ni el directorio de datos de las pruebas. El
registro de esta tanda, cuando se lance, va a **`F:\temp-opofuente\gates-f18-panel-incidencias.txt`**,
con **todos los intentos y sus causas** contados. Lo que sí se ha corrido, sobre este árbol y sin
puerto:

- **backend**: la suite **entera** de unitarias e integración corrió sobre este árbol —**1430 en
  verde**— y dejó **dos rojas, las dos de esta tanda y las dos arregladas**: la mía de la bandeja
  esperaba **cuatro** cifras por categoría (ahora son seis, las dos nuevas salen con cero) y la de la
  cadena de migraciones daba por cabeza la `0034` (ahora es la `0035`). Las dos se han vuelto a pasar
  en verde en su fichero (**18 pruebas**). No se ha lanzado una segunda corrida completa para no
  competir por la máquina con la batería del §1, que es la que está en marcha. Las nuevas, en verde:
  18 unitarias del dominio de la reclasificación, 6 de la migración `0035`, 7 del comando y 10 de la
  ruta y el despacho de la bandeja;
- **frontend**: **344** pruebas de componentes en verde (38 ficheros), con las 9 nuevas de la bandeja
  y las 32 de la ficha de pregunta (2 nuevas del enlace `?pregunta=`);
- **extremo a extremo**: las **3** de `incidencias.spec.ts` en verde (el ciclo con datos reales
  montados en la base de la suite, y las dos de responsividad y accesibilidad a 1280 y 390).

**Colisión de ficheros que hay que decir**: el §1 va a añadir la columna `key_reliability` a
`question_sets` (migración propia) y este bloque **lee** esa columna por su nombre si existe
(`notes_incident_repository.key_reliability`), así que no la escribe ni la modela. Los dos bloques
tocan `infrastructure/db_models.py` (clases distintas) y **los dos añaden una migración con
`down_revision = 0034`**: quien fusione segundo tiene que reencadenar la suya. La mía
(`0035_incidencias_despachables`) está sin fusionar en `f18-panel-incidencias`.

## 4h. El bloque C sigue: la ficha de pregunta (f20)

El §4.2 de los ajustes pide «el sitio donde el propietario arregla las claves dudosas» y dice que hoy
no existe. Existe desde esta tanda: **`/admin/preguntas?pregunta=<id>`** —la dirección que la bandeja
del motor y el banco ya usaban para «abrir la pregunta»— ya no cae en la tabla del banco, cae en la
**ficha**, y la ficha no es un visor: es donde se cambia una respuesta correcta y donde se ve qué se
está estudiando y con qué garantía.

### Lo que se ha construido

1. **La ficha** (`QuestionFilePage` + `QuestionFile`), con seis bloques y **dos historiales**:
   la pregunta con sus opciones y **cuál está marcada hoy**; de dónde sale esa respuesta (la lista de
   respuestas del banco, su estado, **el material del que salió con el estado de *su* versión** y el
   veredicto de fiabilidad del banco); qué dicen los apuntes, con la letra, la **frase** que lo
   demuestra y el enlace al apartado exacto; las incidencias del motor con su categoría; si está fuera
   del temario y por qué; y qué se puede hacer. Debajo, el historial de la pregunta y el de la lista de
   respuestas, **con la letra que cada uno daba a esta pregunta**: es lo que hace que «no se pisa la
   anterior» sea un hecho y no una promesa.
2. **Marcar la respuesta correcta por ruta auditada** (`POST /question-files/{id}/answer-key`), sin SQL
   suelto: se escribe una **lista de respuestas nueva** con el **mismo estado** que la que manda, la
   anterior pasa a `superseded` y **se conserva**, y en la **misma transacción** queda el evento
   `question.answer_key_marked` con el **antes y el después** y el actor.
3. **Nunca sobre una clave oficial.** El dominio (`protege_cambiar_la_clave`) protege por dos caminos
   y la pantalla lo dice con su motivo y con **la lista de bancos protegidos**: los dos exámenes de la
   Guardia Civil 2026 (modelos A y B, `official_exam`) y los cuatro exámenes del INAP —TAI ingreso
   libre 2025 A/B y TAI promoción interna 2025 A/B—, cada uno con la plantilla de la que salió. Son
   **10 conjuntos**, y los dos caminos dan exactamente esos diez.
4. **Reparar lo reparable** (`POST /question-files/{id}/repairs` y el comando
   `python -m opofuente.tools.reparar_preguntas`): una **vista nueva** de la pregunta, la anterior
   sustituida y con su motivo, **el sitio viaja con ella** (temas, anclas y fuera-de-temario se mueven,
   no se copian) y la respuesta correcta la sigue **sin cambiarle ninguna letra**. Y las incidencias de
   esa pregunta se despachan por **la ruta auditada de la bandeja**, no por SQL.
5. **Las reglas, en el dominio y con guardas** (`domain/question_file.py`): quitar la referencia del
   examen pegada al final del enunciado (todas las que haya, con el guardián de que la cola no lleve
   una pregunta, no pase de 120 caracteres y quede un enunciado que cierre) y partir una opción que se
   tragó a la siguiente (solo si hay dos trozos y el primero no lleva un `?`).

### Las cifras, contadas en la base (copia `F:\temp-opofuente\f20-datos`)

| | antes | después |
| --- | --- | --- |
| enunciados con la referencia pegada (de 17.424 vigentes) | 130 | **14** |
| … de esos, limpiables por la regla | 116 | **0** |
| … de los **21** que además tenían incidencia (el bloque del panel) | 20 limpiables | **20 limpiadas, 1 se queda** |
| de las **11** «reparables» de la bandeja, reparables por una regla | 1 | **1 reparada (el JCL), 0 quedan** |
| incidencias de la bandeja en `open` | 430 | **410** (20 despachadas con su nota) |
| preguntas con más de una vista | 0 | **116** (y 116 `superseded`) |
| temas y anclas sobre preguntas vigentes | 19.819 y 6.311 | **19.819 y 6.311** |

Los dos «21» y «11» del encargo, uno a uno: **de los 21 enunciados con la referencia pegada se
limpian 20**; el que se queda es un párrafo del BOE de **7.916 caracteres** que no es una referencia
sino el texto entero de la pregunta, y el guardián lo rechaza. **De las 11 mal importadas que una
regla marcaba como reparables se repara 1** —la del JCL, que además llevaba las dos reglas: la
referencia pegada *y* una opción que se había tragado a la siguiente, `JOB 0` + `d) CALL` → `JOB` y
`CALL`—. Las otras diez **no se tocan y se dice por qué**, con el motivo agrupado:

- **5** son referencias legítimas a otra opción («… conforme a lo indicado en la opción c)»): la
  pregunta está bien escrita y lo que falla es la regla mecánica, no el texto;
- **2** son una opción que es el principio de otra y así estaban escritas: se arreglan marcando la
  respuesta correcta, no el texto;
- **1** son dos opciones que solo se diferencian en las mayúsculas (`LC_COLLATE`) **y esa diferencia
  es justo lo que se pregunta**;
- **1** es una opción que se llevó el resto del documento dentro: hay que volver a extraerla del
  original, no partirla a ciegas;
- **1** es un resto al que le falta el principio o el final, y ninguna regla puede adivinar lo que se
  perdió.

Y **las 18 preguntas sin opciones** que el bloque del panel ya había sacado del temario
(`enunciado_roto`) siguen donde estaban: eso no es una reparación de texto, es volver al original.

### Por qué las reparaciones no se hacen «todas de golpe»

Se reparan **116 de 130**, no las 130, y las 14 que quedan están miradas una a una: son «Microsoft Word
2013 estándar», «el Plan España Digital 2025», «el BOE del 14 de julio»… **no son referencias de
examen**, son el contenido de la pregunta. Y de las 130, **109 no tenían ninguna incidencia**: el
comando limpia 96 de ellas —13 no se pueden, por lo mismo— porque el encargo lo pide, pero ninguna se
había señalado nunca.

### La prueba que falla antes

Once pruebas se han puesto **rojas apagando su pieza**, una a una y volviéndolas a poner:

| pieza apagada | pruebas que se ponen rojas |
| --- | --- |
| `partir_opcion_fundida` (devuelve `None`) | **3** unitarias del dominio, con el caso real del JCL |
| la guarda de la clave oficial (`protege_cambiar_la_clave`) | **2** de integración: el rechazo del examen oficial y el de la lista que viene de un documento |
| dejar la lista anterior en el historial (se borra en vez de sustituirla) | **1**: la plantilla nueva con la anterior conservada |
| que el sitio viaje (`_carry_place`) | **2**: la vista nueva se lleva el tema y la clave sigue a la pregunta |
| el historial de la pregunta (se recorta a una vista) | **2**: el historial y la reparación |
| la dirección `?pregunta=` → la ficha (vuelve a la tabla del banco) | **1** de componentes, que monta el árbol de direcciones entero |

Las dos últimas filas se hicieron **sobre el árbol ya escrito** (con el fichero de dominio y el de
infraestructura copiados y restaurados byte a byte: los dos hashes coinciden). Y el **e2e** que prueba
la dirección tenía su rojo antes de escribir nada: en `main`, ese enlace abría la **tabla del banco**
—la prueba de f18 esperaba «Pregunta 1» y ahora espera «Ficha de la pregunta»—; el cambio de esa
expectativa es el que dice que la dirección cambió de destino.

### Las capturas

`artifacts/screens/admin-preguntas-ficha-{escritorio,movil}.png`, con **0 violaciones de axe** y **0
errores de consola** en las dos, **1280 px** y **390 px exactos** de ancho y sin scroll horizontal.
Salen de la **copia** (`F:\temp-opofuente\f20-datos`), nunca de la base del propietario, y con una
pregunta **real y de verdad del caso de uso**: una de un banco en cuarentena (`clave_no_fiable`),
elegida por la API de la bandeja, **vigente** (no una vista ya sustituida) y con el veredicto de
fiabilidad del §1 a la vista. Del detector de palabras prohibidas sale **una**: **«Celador»**, y no la
pone esta pantalla —viene del **selector de oposición** del marco del panel, el mismo hallazgo que en
f16 y f18—. Las imágenes **no se han mirado a ojo** (el modelo de esta sesión no lee imágenes); lo que
se declara de ellas es lo que el guion mide.

### Las puertas y las pruebas locales

**Las 18 puertas pasan a la primera**, en **39:41 minutos**, con el registro completo —todos los
intentos y sus causas— en **`F:\temp-opofuente\gates-f20-pregunta.txt`**: formato, lint, mypy
estricto, eslint, tipos, **792** unitarias de backend, **684** de integración, **29** de contrato,
**357** de componentes en 39 ficheros, contrato OpenAPI y tipos sincronizados, los dos build, la
migración desde base vacía con su verificación por `sqlite3`, la siembra idempotente, los fixtures
frente a las fuentes y las **74** extremo a extremo.

**Y se han vuelto a pasar enteras con `main` dentro** —el §1 de las claves ya fusionado en la rama—,
que es lo que hace que la fusión no pueda romper `main`: **las 18, a la primera, en 45:36**, con el
registro en **`F:\temp-opofuente\gates-f20-fusion.txt`** y **827** unitarias, **696** de integración,
**29** de contrato, **359** de componentes en 40 ficheros y **74** extremo a extremo. Los dos bloques
tocamos seis ficheros a la vez y los seis están resueltos: el **contrato** (`openapi.json` y
`openapi.d.ts`) se **regenera** con los dos pasos de la puerta 10 —comprobado que la suma no pierde
nada: 0 rutas y 0 esquemas de `main` que falten, 0 míos que falten, **164 rutas y 277 esquemas**—, el
**cuadro de decisiones** es una adición y se **suma** (verificado que no se pierde ni se cambia una
línea de nadie), y las **capturas** (`screens.spec.ts`) y los **dos documentos** entran cada uno con
lo suyo (el bloque de la marca «clave en revisión» del §1 y el de la ficha, separados, sin nombres
repetidos). Lo corrido durante la tanda, sobre este árbol:

- **backend**: la suite **entera** (unitaria, integración, contrato y migraciones) —**1505 en verde**,
  cero rojas— y las nuevas de esta tanda, 44: **24 unitarias** del dominio (las dos reglas con sus
  guardas, el motivo de no reparar y la protección de la clave oficial) y **20 de integración** de la
  ficha, el marcado y la reparación, incluidos los dos rechazos de la clave oficial y la comprobación
  de que la anterior **se conserva**;
- **frontend**: **357** pruebas de componentes en verde (39 ficheros), **13** de ellas nuevas de la
  ficha (la pantalla, la procedencia, los apuntes, la incidencia, el marcado con su antes, el rechazo
  del banco oficial, la reparación con su motivo obligatorio, la que no se puede reparar, los dos
  historiales y la dirección);
- **extremo a extremo**: **74** en verde (la suite entera), **4** nuevas de la ficha: el ciclo completo
  —abrir desde el enlace de la bandeja, ver de dónde sale la respuesta, marcarla con su evento de
  auditoría, reparar la referencia pegada y comprobar en la base que la lista anterior se conserva—,
  el rechazo del examen oficial con **la lista de respuestas intacta**, y las dos de accesibilidad y
  responsividad. **Una trampa que costó una corrida**: esta prueba creaba sus preguntas **catalogadas
  en un tema** y eso le cambiaba la muestra al **diagnóstico** de otra prueba (`study.spec.ts`, de 6 a
  8 preguntas) —se midió: la prueba del diagnóstico pasa sola y falla después de la mía—; se arregló
  **no catalogando** las preguntas de esta prueba, porque el sitio que viaja se prueba en la de
  integración y en la corrida sobre la copia. Y **la del banco** (`incidencias.spec.ts`, de f18) se ha
  actualizado: su enlace ya no lleva a la tabla sino a la ficha;
- **capturas**: las **50** del guion en verde, con las dos nuevas de la ficha.

### La copia, y la colisión de revisiones que hay que decir

La copia de trabajo se hizo **de la base real** (nunca al revés) y allí se corrieron las reparaciones y
las medidas. **La base real ya está en `0036_claves_no_fiables`** —el §1 aplicó su migración—, y este
árbol conoce hasta **`0035_incidencias_despachables`**, así que la copia se marca en `0035` cambiando
**solo su fila de `alembic_version`**: el esquema de la copia es el de la base real (un superconjunto
del de 0035) y por eso la ficha **lee `question_sets.key_reliability` de verdad** —221 conjuntos
`fiable`, 6 `dudosa` y 10 `no_fiable`— en lugar de decir que la columna no existe. Es la única fila que
se ha tocado a mano, está dicha aquí y no afecta a ninguna migración: **esta tanda no añade ninguna**,
porque la ficha lee tablas que ya existían y lo que escribe son filas nuevas de
`answer_versions`/`question_versions` y sus eventos. Colisión con el §2 de los apuntes: ninguna; con el
§1, la de arriba (su revisión `0036`).

## 5. Lo que queda abierto

1. **El acumulado de gasto anterior a f10 no existe** y ya no se puede medir. Desde aquí se anota una
   línea por corrida (§1).
2. **I.1 está publicado** con el 98,5 % de cobertura y la forma pasando. Su índice cuadra: 21
   apartados, 1.724 hechos y **0 sin materia**.
3. **La puerta «hechos fuera de su materia (≤ 3 %)»** del §2.3 sigue sin implementar.
4. **I.6 está en borrador por la cobertura (72,5 %), y su techo medido es el 84,1 %**: 41 preguntas de
   las 258 tienen en los apuntes una frase que sostiene otra opción que su clave y 30 no tienen frase.
   **No se arregla escribiendo más**: es criterio del propietario sobre las claves. Su forma ya pasa.
5. **`prever` antes de pagar**: `apuntes --prever` dice lo que le haría una corrida al tema (qué
   apartados se conservan, cuáles se vuelven a redactar y cuáles se tiran) **sin llamar a nadie**. El
   plan de una corrida se calcula una vez y no cambia mientras se escribe; entre corridas sí puede
   cambiar —una pregunta nueva, un hecho que llega, el índice redefinido— y entonces ese texto se tira
   y se vuelve a escribir. Las 90 secciones que se rehicieron en la corrida de I.1 eran las del índice
   **anterior** (escritas el 9-oct, antes de que existiera el catálogo): una migración de una vez, no
   un trabajo repetido.
6. **La zona del alumno está casi entera**: desde f13 están la pantalla del test (f11), **Inicio**,
   **Temario** y **Tema con apuntes** —con el **sistema de diseño aplicado** (§3.7: tokens en un
   fichero único y las dos fuentes autoalojadas) y el aviso «Esto está mal» guardando de verdad por su
   ruta auditada—, y desde f14 **Resultado, Simulacros, Exámenes oficiales, Fallos y Progreso** (§4c).
   **Desde F22 está la pantalla de Tests** (§F22): la que deja elegir temas, cuántas preguntas, cuáles,
   cómo se corrigen y si lleva reloj, con los tres enlaces que ya le apuntaban funcionando de verdad.
   Con eso, las **siete entradas del menú** del alumno tienen pantalla. Lo que sigue faltando, medido
   en el código y **listado en §F22.4**: el enlace «Ver en apuntes» desde el test en curso, «Repetir
   solo las falladas» en el resultado (hoy repite el test entero), las pestañas «Preguntas» y «Mi
   progreso» **dentro** del tema (hoy son enlaces fuera), el buscador dentro del tema, la marca de
   leído del índice y el modo repaso de los apuntes. La **bandeja del propietario** para los avisos
   del alumno ya tiene **ruta y pantalla** desde f16 (`/admin/avisos`, §4e): se ven, se despachan y se
   auditan. La **revisión de apuntes en el panel** (§4.3 del objetivo: leer un borrador y aprobarlo)
   sigue **sin pantalla propia**; la **bandeja del motor** ya tiene ruta, pantalla y contador desde
   f18.
7. **Los exámenes del INAP**: la pantalla existe y lee de la API, y hoy sale **vacía** porque no hay
   ninguno importado (D10). Lo que falta es la importación, no la pantalla: cuando los 32 PDF de
   `F:\OpoFuente\fuentes\inap-tai\` entren con su manifiesto, saldrán en la lista con su fecha, su
   número de preguntas y su botón, y el que no tenga plantilla activa dirá que todavía no se puede
   hacer en lugar de ofrecer un examen que falla. La ruta `POST /student/official-exams/{posicion}/sessions`
   ya está probada con un examen de verdad montado por la API (§4c)
8. Los **25 temas restantes** y el bloque D (datos: copias, epígrafes, INAP) siguen sin empezar, con
   D5 (copias verificadas) como primer paso del §6 del objetivo. El **bloque C ha empezado** en f16 con
   sus dos primeras pantallas (la bandeja de avisos del alumno y «No son preguntas», §4e) y **f18 le
   añade la bandeja del motor** —con su ruta, su pantalla, su contador en el menú y la reclasificación
   de las 453 incidencias (§4g)—; le faltan la **ficha de pregunta**, los **apuntes** y el **temario**
   del §4 del objetivo, que es donde se limpiarán los enunciados con la referencia del examen pegada y
   se repararán las preguntas mal importadas que sí se pueden reparar (dos opciones fundidas, una
   cortada, una repetida). En f15 se les ha puesto
   **orden de valor** a los temas: la tabla de preguntas con clave utilizable de cada tema es la que
   decide qué se escribe primero, y está abajo. **IV.2 (el 3.º) e II.4 (el 5.º) quedaron escritos y
   publicados en f17**; **I.8 (el 6.º) quedó en borrador** con sus dos motivos y **es reanudable**:
   lo escrito está en la base y volver a lanzarlo sigue desde donde se paró, sin volver a pagar por
   lo que ya está (§4f). Los tres tienen su índice escrito y ensayado. El séptimo por valor es **I.7
   (550)**, que **todavía no tiene catálogo**: lo primero de la próxima tanda es escribirlo y
   ensayarlo, como se hizo con estos tres.
9. **Dos listones que no coinciden entre el documento y el código**, medidos en I.4 y anotados sin
   tocarlos (el §1.2 pide no relajar la puerta):
   - **párrafos casi repetidos**: el §2.3 pide **≤ 3 %** y el código lleva el tope al **5 %**
     (`MAX_PARRAFOS_REPETIDOS = 0.05`). I.4 está en 4,2 %: pasa el código y no el documento. O se baja
     el del código al 3 % (y entonces I.4, I.1 —2,2 %— y IV.7 siguen pasando, pero hay que volver a
     medir todos) o se sube el del documento al 5 %. **Lo medido en f17 no lo aprieta**: IV.2 sale al
     **0,2 %** y II.4/I.8 no tienen texto todavía. Sigue **sin tocarse**, por la misma razón que en
     f15: cambiarlo altera el veredicto de un tema ya medido (I.4, que está en borrador) y no es un
     arreglo de esta tanda;
   - **hechos fuera de su materia (≤ 3 %)**: sigue **sin implementar** (era el punto 3 de esta lista
     desde f12).
10. **Una lección de medida que conviene no volver a aprender**: a mitad de la corrida de I.4 pareció
   que estaba colgada. **No lo estaba.** El proceso que se miraba era el **lanzador `uv`**, que marca
   0 s de CPU siempre porque solo espera; el que trabaja es su **nieto**. La comprobación que sirve es
   el conteo en la base (278 → 544 comprobaciones en 10 min) y la conexión TCP del nieto a la API. Y
   de ahí salió el hueco real: no había **tope de tiempo para la corrida entera**, y ya lo hay
   (`--tiempo-maximo`, `0` = sin tope), con su prueba de un modelo que tarda más que el tope.
9. **Tres violaciones de accesibilidad en el panel** (`scrollable-region-focusable` en `/cambios` y en
   `/buscar` a 390 px) que aparecen al fotografiar las pantallas del propietario **con los datos
   reales**: son regiones que se desplazan y no se pueden recorrer con el teclado. No son de f16 —las
   dos pantallas de la bandeja salen a **0**, con datos reales— y se arreglan con el mismo remedio que se aplicó a las
   tablas de los apuntes (`tabindex` y nombre), pero tocan el panel: quedan anotadas para él.


---

## F19 · Las claves que no son fiables (§1 del objetivo) — 13-oct-2026

**Rama `f19-claves-fiables`** (worktree `F:\temp-opofuente\opofuente-claves`, desde `db422ba`), migración **`0036_claves_no_fiables`**. Sin fusionar.

### 1. La copia verificada (Paso 0)

`F:\OpoFuente\datos\backups\20261013-113403-e4c97c.zip` · **799.306.361 bytes** · SHA-256 del ZIP `9434fa9b858c04514648f6cb2ec0c966dec4db94dca2f5461a561f89433be49c`. Método del proyecto: instantánea con la API de respaldo de SQLite → ZIP con `force_zip64` y manifiesto → `verify_archive` → extracción a temporal en C: y `PRAGMA integrity_check`. Comprobado: 2/2 entradas con CRC correcto, 0 problemas en la verificación, SHA-256 de la base extraída **idéntico** al de la instantánea (`b9a68c2e…0a6f465`), `integrity_check` = ok, `quick_check` = ok, `foreign_key_check` = 0 filas, cabecera SQLite 660.686 páginas × 4096 = 2.706.169.856 bytes exactos, revisión `0034_avisos_en_curso_y_nota`. 332 s. **No se ha borrado ninguna copia** (quedan 3).

### 2. La discrepancia, medida otra vez (no heredada)

Universo: `question_note_anchors` ⋈ `question_versions` ⋈ `question_sets`, **una pregunta cuenta una vez**, conjunto de origen = `question_versions.question_set_id` → `question_sets.title` (0 títulos vacíos, 0 preguntas sin conjunto). Medible = ancla con letra de los apuntes y con clave no vacía. Discrepante = la letra de los apuntes no está entre las de la clave.

**6.311 anclas · 5.929 con letra y clave · 5.925 preguntas distintas · 528/5.925 = 8,91 % global.**

| conjunto | comprobadas | discrepantes | % | veredicto |
|---|---|---|---|---|
| TAI · C_ejer_1_libre_DZA_2026 (marcadas) | 18 | 16 | 88,89 | `no_fiable` |
| TAI · Test por temas (marcadas) | 32 | 26 | 81,25 | `no_fiable` |
| TAI · TEST VARIOS (marcadas) | 64 | 49 | 76,56 | `no_fiable` |
| TAI · Test Aragón 2015 (marcadas) | 31 | 23 | 74,19 | `no_fiable` |
| TAI · 1600-Preguntas-Constitución-Española (marcadas) | 71 | 51 | 71,83 | `no_fiable` |
| TAI · TEST B1 (marcadas) | 71 | 51 | 71,83 | `no_fiable` |
| TAI · baquedano (marcadas) | 105 | 70 | 66,67 | `no_fiable` |
| TAI · Supuestos Practicos Bloque IV (marcadas) | 22 | 8 | 36,36 | `no_fiable` |
| TAI · «…drive-download…SIMULACROS y» (respuesta en el material) | 15 | 5 | 33,33 | `no_fiable` |
| TAI · TAI_ejer_1_A_libre_AGE_2024 (clave publicada) | 15 | 5 | 33,33 | `no_fiable` |
| TAI · 2022_diccionario-concepto-terminos-AE (marcadas) | 21 | 6 | 28,57 | `dudosa` |
| TAI · Doc Adicional (marcadas) | 28 | 7 | 25,00 | `dudosa` |
| TAI · 01.- eAdministracion (marcadas) | 19 | 4 | 21,05 | `dudosa` |
| TAI · 2025_Diccionario_conceptos_AE_11_ed (marcadas) | 15 | 3 | 20,00 | `dudosa` |
| TAI · Material adicional (marcadas) | 15 | 3 | 20,00 | `dudosa` |
| TAI · Doc adicional (marcadas) | 60 | 9 | 15,00 | `dudosa` |

Y **80 conjuntos quedan por debajo del mínimo de 15 comprobadas** (364 preguntas): no se cuarentenan porque no se pueden medir. Los otros 44 medibles son `fiable` (el peor, 14,29 %).

**Preguntas afectadas: `no_fiable` 10 conjuntos = 1.117 preguntas** (380 con clave activa, 461 anclas) **fuera de tests, simulacros, repasos, práctica por tema y diagnóstico, y fuera del denominador de cobertura**; **`dudosa` 6 conjuntos = 984 preguntas** (332 anclas), que entran con la marca **«clave en revisión»**.

### 3. Los tres arreglos que se intentaron

| conjunto | discrepancia | preguntas ±1/±2 | opciones giradas | conclusión |
|---|---|---|---|---|
| C_ejer_1_libre_DZA_2026 | 88,9 % | 87,5 % | 44,4 % (peor) | no es desplazamiento |
| Test por temas | 81,2 % | 84,4 % | 80,0 % | no es desplazamiento |
| TEST VARIOS | 76,6 % | 75,0 % | 73,4 % | no es desplazamiento |
| Test Aragón 2015 | 74,2 % | 67,7 % | 74,2 % | no es desplazamiento |
| TEST B1 / 1600-Preguntas | 71,8 % | 68,6 % | 74,6 % | no es desplazamiento |
| baquedano | 66,7 % | 66,7 % | 68,6 % | no es desplazamiento |
| Supuestos Practicos Bloque IV | 36,4 % | 35,0 % | 36,4 % | no es desplazamiento |
| «…SIMULACROS y» | 33,3 % | 33,3 % | 33,3 % | no es desplazamiento |
| TAI_ejer_1_A_libre_AGE_2024 | 33,3 % | 86,7 % con +1 **solo sobre 15 anclas** | 93,3 % con +1 | **es el caso del INAP: se explica por la numeración, no por la clave** |

Ningún conjunto baja del 10 % con un desplazamiento de preguntas ni con una rotación de opciones, salvo el del INAP —donde el conjunto tiene 15 anclas y la comparación por contenido (abajo) demuestra que la clave **sí** es la oficial—. **El apartado 4a no explica ninguno de los nueve conjuntos de «respuestas marcadas»: no era un desplazamiento.**

### 4. INAP 2024 modelo A — dictamen

Se han leído las dos plantillas oficiales (`TAI-2024-libre-plantilla-definitiva-unico-{A,B}.pdf`) y el cuestionario A, y se han comparado con la clave guardada **por contenido** (alineando por enunciado, no por número):

- **Es el modelo A, no el B**: la clave guardada coincide con la plantilla oficial **A en 66/73 = 90,4 %** y con la **B en 35,2 %**; el orden de las preguntas también es el de A (el de B solo casa en 17/76).
- **La numeración NO cuadra**: faltan **2 preguntas oficiales** en el conjunto (la 57 y la 76), así que desde la posición 57 la numeración va una por detrás de la oficial y desde la 75, dos; y el conjunto tiene **0 reservas** cuando la plantilla publica 5 para la primera parte.
- Aun corrigiendo el desplazamiento, **7 preguntas siguen discrepando** con la plantilla oficial (posiciones 1, 2, 4, 6, 7, 8 y 9) y **3 que la plantilla declara ANULADA (22, 51, 70) llevan clave «a»** en el conjunto.
- **Dictamen**: es clave **oficial** y no se toca. Y como la numeración no cuadra, no es «todo cuadra y aun así discrepa»: son **incidencias para el propietario** (faltan 2 preguntas, no hay reservas, 7 claves no son las de la plantilla), con estas cifras.

### 5. Lo que se ha construido (con prueba que falla antes de cada regla)

- `domain/key_reliability.py` — el veredicto, las dos fronteras, la medida por conjunto y la prueba del desplazamiento. Puro, sin base de datos.
- `alembic/versions/0036_claves_no_fiables.py` — `key_reliability` (`fiable` · `dudosa` · `no_fiable`), `key_checked_count`, `key_discrepant_count`, `key_measured_at`, con sus `CHECK` e índice. **Vuelta atrás probada** (quita las cuatro columnas y deja el esquema como estaba; volver a subir las devuelve).
- `infrastructure/key_reliability_repository.py` — mide, guarda y **audita** cada cambio de veredicto; `set_verdict` para devolver un conjunto a `fiable` por la vía auditada; idempotente.
- **Cuarentena en los sitios reales**: `_preguntas` (práctica por conjunto y examen oficial: se niega con los dos números), `compose` (test de varios temas y simulacro), `_create_topic_session`, `_create_review_session` (repaso), `_create_diagnostic_session` y `question_groups` (denominador de la cobertura).
- **Marca «clave en revisión»** para las dudosas: `StudentQuestionView.in_review`, `StudentRunView.questions_in_review` y `StudentResultQuestionView.in_review`, en la API y en el contrato.
- **Puerta de datos permanente** al cerrar cada tema (`_puerta_de_claves` en `tools/apuntes.py`, en la corrida y en `--publicar`; `--medir` la enseña sin aplicar): recalcula la discrepancia por conjunto y el que cruce el 30 % **entra en cuarentena solo**.
- La discrepancia **se puede volver a medir en cualquier momento sin gastar**: `medir_conjuntos` es puro y la puerta es una consulta.

### 6. Lo que queda fuera, y por qué

- **Claves derivadas (4b)**: no ejecutadas. Ver la decisión del 13-oct en `DECISIONES-TOMADAS-EN-EL-OBJETIVO.md`.
- **Bandeja del propietario para los conjuntos en cuarentena**: hoy los conflictos de letra ya llegan a `notes_incidents` (`clave_sospechosa`), pero un conjunto en cuarentena **no crea una incidencia por conjunto**. Es la pieza que le dice «estos 10 conjuntos, con estas cifras, y estas son tus preguntas» en una fila, y no está.
- **Marca en la pantalla del alumno**: **hecha y retratada** —el distintivo se pinta en el test en curso (`StudentTestRunner`) y en el resultado (`ResultPage`), con su estilo (`.marca-clave-en-revision`, que reutiliza el patrón `.marca` de la casa y su par de colores ya verificado), su prueba de componente que se demuestra en rojo apagando la marca, y sus **capturas**—. Lo único que queda **escrito y no ejecutado** es la aserción de las capturas (ver §9): necesita los puertos 8765 y 4173 libres, y el 8765 lo tiene otro bloque.
- **Aserción de las capturas del alumno**: escrita en `apps/web/tests/screens/screens.spec.ts` y **sin ejecutar** —las capturas que hay son de la corrida anterior—. Relanzar con `cd apps\web; npm run screens` cuando el puerto 8765 esté libre. Detalle y qué se comprueba, en §9.

### 9. Las capturas de la marca (escritorio y móvil, 0 axe)

`npm run screens`, 48 capturas en 2,0 min, **0 violaciones de axe** («Ninguna: axe no encuentra
violaciones A/AA en ninguna pantalla»), 0 errores de consola y 0 palabras prohibidas. Las cuatro que
enseñan la marca:

| fichero | ruta retratada | ancho | carga | axe |
|---|---|---|---|---|
| `test-en-curso-escritorio.png` | `/test/0bee477c…` | 1280×800 | 665 ms | 0 |
| `test-en-curso-movil.png` | `/test/e4021b8c…` | 390×844 | 664 ms | 0 |
| `resultado-escritorio.png` | `/resultado/fa8462e9…` | 1280×800 | 707 ms | 0 |
| `resultado-movil.png` | `/resultado/fa8462e9…` | 390×844 | 700 ms | 0 |

**Cómo se consigue que la marca salga en el retrato**, que es lo que tiene truco: la marca solo se
pinta si el conjunto es `dudosa`, y la suite de capturas monta su propio conjunto (tres preguntas,
sin apuntes), así que la puerta de datos **no puede medirlo** —no llega a las 15 comprobadas— y el
veredicto se queda en `fiable`. La herramienta de capturas escribe entonces el veredicto directamente
en **su** base (`.e2e-data`, que se borra en cada corrida) con `node:sqlite`, que viene con Node 24:
sin dependencias nuevas y sin procesos de más. Va en la herramienta y no en la puerta a propósito:
esto retrata, no juzga.

**La cadena de evidencia, comprobada en la base de la suite**: los conjuntos de la captura quedan
`dudosa` (2 de 3), sus 3 y 4 preguntas son las de las sesiones retratadas
(`0bee477c…` y `e4021b8c…` en curso, `fa8462e9…` terminada), y de ahí sale el `in_review = true` que
la interfaz convierte en el rótulo. Comprobado **por la API**, levantada aparte en un puerto libre
(8799, sin tocar el 8765 de otro bloque) sobre esa misma base: el test en curso devuelve
`question.in_review = true` y `questions_in_review = 3`; la pantalla de resultado, que lee otra ruta,
devuelve `in_review` por pregunta `[true, true, true, false]` — **tres de cuatro**—.

#### Lo que queda **escrito y NO ejecutado** en las capturas

> **Actualización (13-oct-2026, F22):** ya **no** queda pendiente. La aserción se ejecutó en la
> corrida de capturas de F22 (54/54, con `test-en-curso` y `resultado` a los dos anchos entre ellas)
> y **pasó**: la marca «clave en revisión» está demostrada en un navegador de verdad. El texto de
> abajo se conserva tal como se escribió, porque cuenta por qué estaba pendiente y cómo se cierra.

La herramienta lleva ahora una aserción por captura del alumno, para que la evidencia no dependa de
que alguien mire el PNG:

```ts
// apps/web/tests/screens/screens.spec.ts, en las capturas «test-en-curso» y «resultado»
await expect(page.getByText(MARCA_EN_REVISION).first()).toBeVisible();
```

**Está escrita y no se ha ejecutado**, y se dice aquí para que no parezca verde:

- **Qué hace**: si el rótulo «clave en revisión» no está en pantalla, esas dos capturas **fallan** en
  vez de guardar un PNG que no enseña lo que tiene que enseñar.
- **Por qué no se ha ejecutado**: las capturas que hay son de la corrida **anterior** a la aserción.
  Para ejecutarla hay que volver a lanzar la suite de capturas, y eso necesita los puertos **8765**
  (API) y **4173** (vista previa) libres; el 8765 lo tiene tomado el bloque de `opofuente-preguntas`
  desde las 15:36 y **no se le toca el servidor a otro bloque**.
- **Cómo se relanza** (desde `apps/web`, con esos dos puertos libres):

  ```powershell
  cd apps\web
  npm run screens
  ```

  Y se comprueba en `artifacts/screens/report.md`: las filas `test-en-curso` y `resultado` de los dos
  anchos tienen que salir con **0 violaciones de axe**, y las 48 capturas tienen que pasar.
- **Mientras no se ejecute**, lo que sostiene que la marca está dentro es lo de arriba: la base de la
  suite (`dudosa`), la API (`in_review = true`, `[true, true, true, false]`) y la prueba de componente
  que demuestra el pintado. Las tres cosas son evidencia; **la aserción es la que cierra el círculo, y
  está pendiente**.



### 7. §3 · Cobertura de I.6, I.4 e I.8 con la cuarentena puesta y sin ella

**Método**: copia de la base real con la API de respaldo de SQLite (nunca la real) en `C:\…\Temp\f19-datos`, migrada a la cabeza —aplica la `0036`— y `TopicNotesService.medir`, que sale de lo guardado y **no llama al modelo**. Coste **0 $**.

| tema | antes | después | denominador | cubiertas | veredicto |
|---|---|---|---|---|---|
| **I.6** | 187/258 = **72,5 %** | 170/239 = **71,1 %** | 258 → 239 (−19) | 187 → 170 (−17) | NO PASA |
| **I.4** | 497/559 = **88,9 %** | 490/551 = **88,9 %** | 559 → 551 (−8) | 497 → 490 (−7) | NO PASA |
| **I.8** | 423/516 = **82,0 %** | 405/494 = **82,0 %** | 516 → 494 (−22) | 423 → 405 (−18) | NO PASA |

**Ninguno cruza el 90 %.** La cuarentena **baja I.6** (72,5 → 71,1) y deja I.4 e I.8 igual, y el motivo está medido: de las preguntas que salen del denominador la mayoría **estaban cubiertas** (17 de 19 en I.6, 7 de 8 en I.4, 18 de 22 en I.8), así que quitar numerador y denominador a la vez mueve la razón hacia abajo cuando esas preguntas estaban por encima de la media del tema. La cuarentena **no regala cobertura: la limpia**, y el número deja de estar sostenido por claves que no son de fiar.

Puerta de claves sobre la copia: **144 conjuntos medibles** (128 `fiable`, 6 `dudosa`, 10 `no_fiable`) y **16 cambios de veredicto**, cada uno con su evento de auditoría. Anclas: 6.311 · **461 en cuarentena** · **332 dudosas**.

Anclas de conjuntos que **no** son `fiable`, por tema: **I.6 107** · **I.4 95** · **I.8 187**. Los `no_fiable` que toca cada uno: I.6 → baquedano 11, TEST VARIOS 11, Test por temas 5, Test Aragón 2015 4, TAI_ejer_1_A 2, drive-download 1; I.4 → baquedano 11, TAI_ejer_1_A 1, drive-download 1; I.8 → baquedano 28, Test Aragón 6, TEST VARIOS 6, drive-download 4, TAI_ejer_1_A 3, C_ejer_1_libre_DZA 2. El resto son `dudosa`, que entran con la marca.

**Precisión de método**: el código agrupa por **`set_id`**, no por título. Cuatro títulos de exámenes del INAP 2025 están repetidos en **dos conjuntos distintos** cada uno («TAI ingreso libre 2025 · modelo A» y sus tres hermanos), así que agrupar por título da 140 grupos donde hay 144 conjuntos: por título se pueden juntar dos claves distintas.

### 8. El desplazamiento, probado **entero** — y una lectura al revés que se corrige

**Lo que pasó, porque queda escrito.** La primera salida de esta prueba imprimía
`discrepantes/comprobadas`, y se leyó «las opciones, 3 puesto(s): **21/21 = 100,0 %**» como «21
aciertos de 21». Quiere decir **21 discrepantes de 21: cero aciertos**. Se sacó de ahí un «hallazgo»
—claves corridas una opción en cinco conjuntos `dudosa`— que **era falso**, y llegó a proponerse
como decisión. El error tenía además una causa de fondo: la fila «hoy» salía de la discrepancia de
las anclas y las alternativas de la **plantilla de hoy** por posición, y esas dos cosas no son la
misma línea base; una tabla con dos orígenes se puede leer al revés sin que nada avise.

**Lo que se ha corregido en el código, no solo en el texto:**

1. `probar_desplazamientos` toma la clave **del propio ancla** (`expected_letters`), que es el dato
   con el que se midió la discrepancia: la fila «hoy» y las alternativas son la misma línea base.
2. El dominio **comprueba que la línea base cuadra**; si no cuadra, devuelve una sola lectura y dice
   que no compara, en lugar de enseñar una comparación que no es de lo mismo.
3. La fila de **hoy no puede explicarse a sí misma** (`es_alternativa`): si hoy ya coincidiera no
   habría discrepancia que explicar.
4. La salida del comando imprime **aciertos sobre total** con la etiqueta delante, compara con el
   azar (25 %, cuatro opciones) y solo marca «EXPLICA» por encima del 90 %.
5. Las posiciones con más de una pregunta no se mueven (no está definida «la clave de al lado»), y
   se dejan fuera **también de la línea base**, para que «hoy» y las alternativas sean el mismo
   conjunto de preguntas.

**La medida buena, con las dos secuencias del mismo acto de comprobación** (registro completo en
`F:\temp-opofuente\f19-scratch\desplazamiento.txt`):

| conjunto | hoy (aciertos) | mejor alternativa | ¿explica? |
|---|---|---|---|
| 2022_diccionario-concepto-terminos-AE | 15/21 = 71,4 % | clave −1: 9/20 = 45,0 % | **no** |
| 01.- eAdministracion | 15/19 = 78,9 % | clave −1: 10/19 = 52,6 % | **no** |
| 2025_Diccionario_conceptos_AE_11_ed | 12/15 = 80,0 % | clave −1: 8/15 = 53,3 % | **no** |
| Material adicional | 6/15 = 40,0 % | clave −1: 5/14 = 35,7 % | **no** |
| Doc Adicional | 16/28 = 57,1 % | clave −1: 11/27 = 40,7 % | **no** |
| Doc adicional | 24/25 = 96,0 % | clave −2 / +2: 43,8 % | **no** |

Y en los diez `no_fiable` lo mismo (baquedano, TEST VARIOS, Test por temas, Test Aragón 2015,
1600-Preguntas, TEST B1, Supuestos Practicos, drive-download, C_ejer_1_libre_DZA y
TAI_ejer_1_A): **la lectura de hoy es la mejor o está al lado, y ninguna alternativa pasa del
50 %**. Las rotaciones se quedan en el **nivel del azar**. Con la prueba ya completa, **los 16
conjuntos que no son fiables dicen lo mismo: no es un desplazamiento**.

**Conclusión, la de siempre y ahora con la prueba entera: las claves no están corridas, están mal en
muchos sitios**, y el paso siguiente es la clave derivada del §1. No hay ninguna excepción que
aplicar ni ninguna lista que mantener.

## F21 · La tanda de contenido por valor: cuatro índices y la base que había que migrar (13-oct-2026)

**Rama `f21-temas-valor`** (worktree `F:\temp-opofuente\opofuente-contenido`, desde `main = d67e799`).
Es la primera tanda que aplica el **ritmo nuevo del §4** de `AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO-2026-10.md`:
contenido **directo sobre la base real**, sin rama de contenido y **sin batería de 18 puertas**, decidido
por las puertas de datos del tema.

### 1. La base real no estaba migrada: la cuarentena estaba en el código, no en los datos

`main = d67e799` ya trae el motor de F19, pero la base real estaba en **`0034_avisos_en_curso_y_nota`**:
la columna `question_sets.key_reliability` **no existía** y cualquier lectura fallaba con
`no such column: question_sets.key_reliability` — `--listar`, `--esquema`, `--prever` y la corrida.
Es decir: la cuarentena que el encargo da por puesta **no estaba aplicada a los datos**.

| Qué | Cómo |
|---|---|
| Migración | `alembic upgrade head` → `0035_incidencias_despachables` + `0036_claves_no_fiables` (aditivas: cuatro columnas con `server_default`, tres `CHECK` y un índice; la vuelta atrás de la `0036` está probada por F19) |
| Copia de seguridad | `20261013-113403-e4c97c.zip` (revisión **0034**, verificada hoy) — es la vuelta atrás real |
| Veredictos | Poblados por la **vía auditada** (`measures()` + `apply()`, actor `f19:puerta-de-claves`): **144 conjuntos medibles**, **16 cambios de veredicto**, cada uno con su evento de auditoría → **10 `no_fiable` · 6 `dudosa` · 221 `fiable`** |
| Coste | **0 $** (la puerta de claves no llama al modelo) |

Las cifras coinciden **exactamente** con las que F19 midió sobre una copia (§7 de F19): mismos 16
cambios, mismos 10 conjuntos en cuarentena. La decisión está en `DECISIONES-TOMADAS-EN-EL-OBJETIVO.md`.

### 2. «Dos temas a la vez» no es posible, y el límite no es la API

El §4 pide lanzar dos temas a la vez si la API lo aguanta y medir el 429. **Medido**: el motor tiene
una marca **única** en `app_metadata` — `CLAVE_APUNTES = "apuntes_en_curso"`, en
`infrastructure/run_lock.py`— y **sin el tema en la clave**, así que la segunda corrida (del mismo tema
o de otro) se niega con `ClassificationAlreadyRunningError` y sale con código 1 **antes de llamar al
modelo**. No hay 429: la API no se llega a tocar. La sonda de latencia confirma que la API está sana
(**6,2 s y 6,6 s** por petición pequeña).

El candado es **deliberado** y está documentado en su propio módulo: el 10-oct-2026 dos corridas de
`apuntes` a la vez sobre I.6 obligaron a matar la segunda. Abrirlo **por tema**
(`clave=f"{CLAVE_APUNTES}:{tema}"`) es un cambio de **motor** —con su prueba que falla antes y sus
18/18— y no cambia lo que se puede entregar en esta tanda: queda **propuesto**, no hecho.

### 3. La tabla de valor, vuelta a medir con la cuarentena puesta

La tabla del §4d se midió el 11-oct, **antes** de la cuarentena. Vuelta a medir hoy (`valor_por_tema.py`
sobre la base real, con `question_groups` filtrando ya los conjuntos `no_fiable`): los números bajan
en los temas que tienen conjuntos en cuarentena y **suben los que quedan por hacer**. Los diez primeros
por **clave utilizable**:

| # | Tema | Grupos | Preguntas | Con clave | **Clave utilizable** | Hechos | Estado |
|---|---|---|---|---|---|---|---|
| 1 | I.1 | 1.998 | 2.023 | 2.016 | **1.985** | 3.511 | publicado |
| 2 | IV.2 | 751 | 767 | 757 | **739** | 1.543 | publicado |
| 3 | I.2 | 613 | 692 | 682 | **656** | 1.233 | publicado |
| 4 | I.4 | 537 | 589 | 564 | **549** | 1.056 | borrador (88,9 %) |
| 5 | **I.7** | 364 | 564 | 528 | **528** | 0 | **esta tanda** |
| 6 | I.8 | 413 | 557 | 517 | **491** | 815 | borrador (82,0 %) |
| 7 | II.4 | 446 | 481 | 471 | **435** | 1.046 | publicado |
| 8 | IV.7 | 442 | 472 | 459 | **433** | 958 | publicado |
| 9 | III.4 | 405 | 416 | 415 | **415** | 0 | **NO se escribe (ver §5)** |
| 10 | IV.5 | 387 | 402 | 395 | **395** | 0 | **esta tanda** |

*(La columna «clave utilizable» sale de la base con la cuarentena puesta. En los temas ya escritos se ve
su efecto: I.1 2.035 → 1.985, IV.7 511 → 433, I.6 283 → 239.)*

### 4. Los cuatro índices, escritos y ensayados **antes** de pagar (0 $)

El bloque manda que el árbol se decida antes de facturar: `--esquema` y el ensayo de reparto (los dos
de solo lectura) deciden si el catálogo sirve antes de que se llame a nadie.

| tema | apartados | grupos situados por el enunciado | revisión del índice | previsión (`--prever`) | tope |
|---|---|---|---|---|---|
| **I.7** | 19 (por las normas del tema) | **339/364 = 93,1 %** | PASA | 72–125 llamadas · 0,49–0,85 $ | 1,13 $ |
| **IV.5** | 16 (por asunto) | **381/387 = 98,4 %** | PASA | 75–130 llamadas · 0,51–0,88 $ | 1,17 $ |
| **I.5** | 14 (por sus cinco normas) | **300/340 = 88,2 %** | PASA | 61–105 llamadas · 0,41–0,71 $ | 0,95 $ |
| **III.9** | 13 (por asunto) | **312/346 = 90,2 %** | PASA | 63–108 llamadas · 0,43–0,73 $ | 0,97 $ |

Los grupos que ningún catálogo sitúa **no** se esconden en un cajón: van a la bandeja del propietario
con su motivo, que es lo que el índice manda. En I.7 están clasificados **uno a uno** y el informe lo
dice: ~14 grupos son de **otro tema** (cartografía del IGN, ciberseguridad/NIS, TLS, HDB, EBEP,
Haciendas Locales, Ley 39/2015) y el resto son **fragmentos de norma sin sujeto** («…tendrá como mínimo
las siguientes funciones» = funciones del delegado de protección de datos), que el reparto sitúa **por
el texto de sus hechos** —el camino que el motor tiene para eso desde I.1—.

### 5. III.4 **no** se escribe, con la cifra delante

Antes de gastar medio día en su catálogo se midió su banco (`pertenencia_utf8.py`, una sonda de
pertenencia por palabras sobre los enunciados): de **405 grupos**, solo **237 (58,5 %)** hablan de
diseño y programación orientada a objetos, patrones o UML —su materia—; **85 (21,0 %)** son de
**fundamentos de programación** (el resultado de `5<<2`, bucles, tipos primitivos de Java, compiladores,
tipado, paradigmas) y **71 (17,5 %)** no reconocen ninguna de las dos listas y, leídos, también son de
esa otra materia. La cobertura no podría pasar del ~60 %: escribirlo sería dejarlo en **borrador
seguro** o **lavar** preguntas mal clasificadas dentro de apartados que no existen. Es un problema de
**clasificación** —de la bandeja del motor, no de los apuntes— y queda dicho con su número.

### 6. Una trampa del montaje, dicha

El montaje de la tanda manda copiar `data\sources\*` desde `opofuente-arreglos`. Esa copia deja el
árbol **inconsistente con su propio `fixtures/profiles/manifest.json`**: las dos fuentes volátiles
(`gc-pagina-oficial-html`, `gc-nota-legal-html`) están descargadas de nuevo en `-arreglos` y su
manifiesto es otro. Efecto medido: `tests/unit/test_profile_fixtures.py` pasa en `opofuente-main` y
**falla** en el árbol nuevo. No se toca el manifiesto —es de otro bloque— ni se relaja la prueba: se
copian las fuentes **de `opofuente-main`**, que son las que cuadran con el manifiesto de esta rama.
Con eso, **803 pruebas unitarias en verde** y `ruff` limpio en `opofuente/domain`.

### 7. I.7, redactado el 13-oct: **borrador, con dos motivos medidos**

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **291/498 = 58,4 % NO PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 291/531 = 54,8 % |
| Hechos | 738 guardados → **610 en el plan** (128 repetidos agrupados) |
| Apartados | **19** · ninguno pasó del tope de 150 hechos |
| Forma | **PASA** · 25.768 palabras de 29.520 (87,3 %) · repetidos 1,6 % · `--limpiar-forma` tocó 15 apartados |
| Índice | PASA · **3 grupos y 6 hechos sin materia** (van a la bandeja) |
| Anclas | 564 · **303 cubiertas · 196 huecos · 59 dudosas · 6 en conflicto** |
| Llamadas y coste | **144 llamadas (0 fallidas) · 1,1903 $** · 90 minutos, **parada por su tope de tiempo** |
| Previsión | 72–125 llamadas · 0,49–0,85 $ → **el máximo se cruzó** |

**Los dos motivos del borrador:**

1. **la cobertura es el 58,4 %** de las 498 preguntas con clave utilizable. **No se toca el listón**;
2. **la corrida no terminó**: el tope de tiempo (5400 s) la paró con **257 de los 364 grupos**
   comprobados y el **bucle de huecos apenas arrancado** (3 grupos cubiertos «tras añadir»). El 58,4 %
   es un **suelo**, no el techo. Terminarlo cuesta, medido y sin pagarlo, **38–94 llamadas ·
   0,26–0,64 $**; no se ha hecho porque los tres temas siguientes tienen índice ya ensayado y mejor
   encaje de banco, y no se vuelve a pagar por lo escrito.

**El tope de dinero se cruzó en 0,06 $ (5,3 %)** y se dice: la cota de llamadas se quedó corta por 19
(144 frente a 125) y el bucle de huecos es el que las añadió. El precio por llamada salió a
**0,00826 $** —el tercero de los normativos densos de la serie, tras I.4 (0,00865 $) e I.8
(0,00853 $)—, así que la regla del tope («la cota de arriba más un tercio») volvió a quedarse corta con
un tema de este tipo: **con I.4 e I.8 son ya tres de tres**, y la cota de arriba de `--prever` no
alcanza cuando el banco es normativo y denso.

**Y queda a medias, dicho**: la bandeja del propietario de I.7 está **vacía** porque las incidencias las
escribe el final del bucle de huecos, que es lo que el tope cortó. Los 196 huecos y los 59 dudosos
están en las anclas con su motivo, pero **no se ven en la bandeja** hasta que se retome la corrida.

**La puerta de datos del §1, al cerrar**: **65 conjuntos medibles** (eran 60), **10 en cuarentena · 7
dudosos · 85 sin poder medir**, con **3 cambios de veredicto** auditados —Material Adicional y
Normativa pasan a `dudosa`, Doc adicional vuelve a `fiable`—. Es la puerta entrando sola al cruzar el
umbral, que es lo que el §1 pide de ella.

### 8. IV.5, redactado y **publicado** el 13-oct: el mejor encaje de la tanda

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **364/374 = 97,3 % PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 364/392 = 92,9 % |
| Hechos | 740 guardados → **633 en el plan** (107 repetidos agrupados) |
| Apartados | **16** · ninguno pasó del tope de 150 hechos |
| Forma | **PASA** · 19.627 palabras de 29.600 · repetidos 0,3 % |
| Índice | PASA · **0 grupos y 0 hechos sin materia** |
| Bandeja del propietario | **26 incidencias**: 16 `norma_cambiada`, 6 `clave_sospechosa`, 4 `hueco_sin_material` |
| Llamadas y coste | **125 llamadas (0 fallidas) · 0,5452 $** · 42 minutos, **sin tope activado** |
| Previsión | 75–130 llamadas · 0,51–**0,88 $** → la corrida entró **por debajo del mínimo** |

Es el tema **técnico** de la tanda y se comporta como tal: **0,00436 $ por llamada**, la mitad que un
normativo denso. Y es la corrida **más limpia de la serie**: terminó sola (387 de 387 comprobaciones,
sin corte de tiempo), el índice no dejó **ni un grupo sin materia** y la forma pasó sin reparaciones
que la rompieran.

**La puerta de datos del §1 volvió a entrar sola**: **71 conjuntos medibles** (eran 65), **11 en
cuarentena**, y un conjunto nuevo —`PreparaTAI AGE-2026…`, con 5/15 = 33,3 %— pasó a `no_fiable` en
cuanto las anclas de IV.5 le dieron las comprobaciones que le faltaban. Sus preguntas salieron del
denominador (402 → 399).

### 9. I.5, redactado y **publicado** el 13-oct: pasa por el margen más estrecho de la tanda

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **344/376 = 91,5 % PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 344/389 = 88,4 % |
| Hechos | 622 guardados → **436 en el plan** (181 repetidos agrupados) |
| Apartados | **14** · ninguno pasó del tope de 150 hechos |
| Forma | **PASA** · 18.235 palabras de 24.880 · repetidos 2,3 % · `--limpiar-forma` tocó 13 apartados |
| Índice | PASA · 2 grupos y 2 hechos sin materia |
| Bandeja del propietario | **38 incidencias**: 11 `clave_sospechosa`, 11 `norma_cambiada`, 9 `hueco_sin_material`, 7 `pregunta_ambigua` |
| Llamadas y coste | **115 llamadas (0 fallidas) · 0,8966 $** · 67 minutos, **sin tope activado** |
| Previsión | 61–105 llamadas · 0,41–0,71 $ → la corrida **cruzó el máximo** (115 llamadas, +26 % en coste) |

**Pasa por el margen más estrecho de la serie** (1,5 puntos sobre el listón), y el margen lo da el
**bucle de huecos**: 24 grupos se cubrieron «tras añadir» —el segundo mejor de la tanda tras los 20 de
IV.2—; sin ellos, el tema se quedaría en el **85,1 %**. Es un tema **normativo** de cinco leyes: 115
llamadas a 0,0078 $, con hechos largos y poco repetidos (181 de 610 agrupados, frente a 107 de 740 en
el técnico IV.5).

**La puerta de datos del §1** cerró en **81 conjuntos medibles · 11 en cuarentena · 8 dudosos**, y el
denominador de la cobertura pasó de 377 a **376** preguntas: otro conjunto cruzó su umbral al recibir
las anclas nuevas y sus preguntas salieron del cómputo **solas**.

### 10. III.9, redactado y **publicado** el 13-oct: el bucle de huecos que más ha recuperado

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **324/337 = 96,1 % PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 324/369 = 87,8 % |
| Hechos | 686 guardados → **511 en el plan** (175 repetidos agrupados) |
| Apartados | **13** · ninguno pasó del tope de 150 hechos |
| Forma | **PASA** · 16.960 palabras de 27.440 · repetidos 0,4 % · `--limpiar-forma` tocó 13 apartados |
| Índice | PASA · 7 grupos y 15 hechos sin materia |
| Bandeja del propietario | **44 incidencias**: 31 `norma_cambiada`, 8 `pregunta_ambigua`, 5 `clave_sospechosa` |
| Llamadas y coste | **111 llamadas (0 fallidas) · 0,4961 $** · 29 minutos, **sin tope activado** |
| Previsión | 63–108 llamadas · 0,43–**0,73 $** → la corrida entró por el medio del rango |

Es el tema **técnico** de la tanda que mejor aprovecha el bucle de huecos: **26 grupos** se cubrieron
«tras añadir» —el mejor de la serie, por delante de los 24 de I.5 y los 20 de IV.2—, y cierra con
**«sin contestar por los apuntes: 0»**. Y es el segundo más barato: 111 llamadas a **0,00447 $**, con
175 de 686 hechos agrupados por la deduplicación.

**La puerta de datos del §1** cerró en **85 conjuntos medibles · 12 en cuarentena · 8 dudosos**: otro
conjunto entró **solo** al recibir las anclas del tema, y el denominador de la cobertura pasó de 341 a
**337** preguntas.

### 11. IV.6, redactado y **publicado** el 13-oct: la corrida más barata de la serie

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **288/297 = 97,0 % PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 288/311 = 92,6 % |
| Hechos | 626 guardados → **488 en el plan** (138 repetidos agrupados) |
| Apartados | **16** · ninguno pasó del tope de 150 hechos |
| Forma | **PASA** · 15.339 palabras de 25.040 · **repetidos 0,0 %** · `--limpiar-forma` tocó 15 apartados |
| Índice | PASA · 4 grupos y 5 hechos sin materia |
| Bandeja del propietario | **25 incidencias**: 14 `norma_cambiada`, 5 `pregunta_ambigua`, 4 `clave_sospechosa`, 2 `hueco_sin_material` |
| Llamadas y coste | **105 llamadas (0 fallidas) · 0,3916 $** · 28 minutos, **sin tope activado** |
| Previsión | 62–108 llamadas · 0,42–**0,73 $** → la corrida salió **por debajo del mínimo** |

**Es la corrida más barata de la serie**: 105 llamadas a **0,00373 $**, con el 55 % de la entrada en
caché (353.664 de 642.841 tokens) y 4.685 tokens de salida por llamada. **Es también la primera con
párrafos repetidos al 0,0 %** y la que cierra con menos preguntas «sin contestar por los apuntes»
(2 de 321).

**Y el ensayo evitó un reparto mal hecho**: `802 ?11` estaba como patrón del apartado de organismos y
**38 de los 310 grupos** acabaron ahí por citar la norma al principio del enunciado. Corregido en el
mismo ensayo (0 $): organismos bajó de 38 a 10 grupos y el WiFi subió de 45 a 72. El defecto no llegó
a la corrida porque el ensayo se hace antes de pagar, que es la regla de la tanda.

**La puerta de datos del §1** cerró en **87 conjuntos medibles · 12 en cuarentena · 9 dudosos**.

### 12. III.1, redactado y **publicado** el 13-oct: la mejor cobertura de la serie

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **281/285 = 98,6 % PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 281/298 = 94,3 % |
| Hechos | 607 guardados → **412 en el plan** (195 repetidos agrupados) |
| Apartados | **8** · ninguno pasó del tope de 150 hechos |
| Forma | **PASA** · 13.151 palabras de 24.280 · repetidos 1,1 % · `--limpiar-forma` tocó 7 apartados |
| Índice | PASA · **0 grupos y 0 hechos sin materia** |
| Bandeja del propietario | **17 incidencias**: 13 `norma_cambiada`, 4 `clave_sospechosa` |
| Llamadas y coste | **78 llamadas (0 fallidas) · 0,3524 $** · 29 minutos, **sin tope activado** |
| Previsión | 49–84 llamadas · 0,33–**0,57 $** → dentro del rango, por la parte baja |

**Es la mejor cobertura de la serie** (98,6 %) y **el tema más barato por corrida** (0,3524 $): un tema
de conceptos con vocabulario muy repetido —la deduplicación agrupa **195 de 607 hechos**, casi un
tercio— que cierra con **«sin contestar por los apuntes: 0»** y **ni un grupo sin materia**.

**La puerta de datos del §1** cerró en **90 conjuntos medibles · 12 en cuarentena · 8 dudosos**.

### 13. El balance de la tanda (f21), con las cifras medidas

| tema | previsión (llamadas · $) | real (llamadas · $) | cobertura (clave utilizable) | veredicto |
|---|---|---|---|---|
| **I.7** | 72–125 · 0,49–0,85 | 144 · **1,1903** | 291/498 = **58,4 %** | **borrador** |
| **IV.5** | 75–130 · 0,51–0,88 | 125 · **0,5452** | 364/374 = **97,3 %** | **publicado** |
| **I.5** | 61–105 · 0,41–0,71 | 115 · **0,8966** | 344/376 = **91,5 %** | **publicado** |
| **III.9** | 63–108 · 0,43–0,73 | 111 · **0,4961** | 324/337 = **96,1 %** | **publicado** |
| **IV.6** | 62–108 · 0,42–0,73 | 105 · **0,3916** | 288/297 = **97,0 %** | **publicado** |
| **III.1** | 49–84 · 0,33–0,57 | 78 · **0,3524** | 281/285 = **98,6 %** | **publicado** |
| | | **3,8722 $** (los seis temas) | | **5 publicados · 1 borrador** |

**Cinco temas publicados y uno en borrador, por 3,8722 $.** El acumulado del objetivo queda en **≈ 14,45 $ de 40**. La forma pasó en los seis sin volver a
llamar al modelo (`--limpiar-forma` reparó 15, 15, 13, 13, 15 y 7 apartados, 0 $). La puerta de claves
del §1 se recalculó al cerrar cada tema y fue subiendo sola: **65 → 71 → 81 → 85 → 87 → 90 conjuntos
medibles**, con **10 → 11 → 11 → 12 → 12 → 12 en cuarentena**, cada cambio con su evento de auditoría.

**Lo que la tanda deja medido sobre el precio de un tema**, que es lo que hace falta para planear los
que quedan:

- un tema **técnico** sale a **0,0037–0,0045 $ por llamada** (IV.6 0,00373, III.1 0,00452, III.9
  0,00447, IV.5 0,00436);
- un tema **normativo denso** sale a **0,0078–0,0083 $** (I.7 0,00826, I.5 0,0078), alrededor del
  **doble**;
- y la **cota de arriba de `--prever` se quedó corta en los tres normativos densos** de la serie (I.4,
  I.8 y I.7). La regla del tope («la cota de arriba más un tercio») es la que impidió que I.7 se fuera
  más allá, pero conviene contar con el doble de precio por llamada cuando el tema es normativo.

**Lo que queda a medias, dicho**: **I.7** (borrador por cobertura, con su corrida cortada por el tope
de tiempo y su bandeja vacía porque es el final del bucle de huecos quien la escribe). Terminarlo
cuesta, medido y sin pagarlo, **38–94 llamadas · 0,26–0,64 $**.

---

## F21b · La tanda de contenido sigue: los técnicos por valor y la decisión escrita sobre I.7 (13-oct-2026)

**Rama `f21-temas-valor`** (worktree `F:\\temp-opofuente\\opofuente-contenido`), con **`main = 570e40d`
dentro** (la rama iba por detrás y se puso al día antes de empezar: `5e7ce6f..570e40d`, avance rápido,
sin choques). Es la segunda tanda con el **ritmo del §4** de `AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO-2026-10.md`:
contenido **directo sobre la base real**, sin rama de contenido y sin batería de 18 puertas. La copia
verificada del día (`20261013-113403-e4c97c.zip`, revisión `0034`) y las migraciones `0035`/`0036` ya
estaban hechas por f21 y no se han vuelto a tocar.

### 1. La tabla de valor, vuelta a medir con la cuarentena puesta

Los números del encargo son los del **principio** de f21; medidos hoy sobre la base real son algo más
bajos, porque la puerta de claves del §1 fue poniendo conjuntos en cuarentena durante aquella tanda
(**10 → 12**) y sus preguntas salen del denominador:

| Tema | Del encargo | **Medido hoy** | Grupos | Preguntas |
|---|---|---|---|---|
| III.7 | 271 | **268** | 248 | 280 |
| III.5 | 268 | **264** | 258 | 265 |
| IV.9 | 235 | **232** | 227 | 246 |
| IV.8 | 232 | **232** | 225 | 233 |
| IV.1 | 230 | **228** | 229 | 230 |

La diferencia no cambia el orden y queda dicha: una cifra que va a un documento se mide, no se hereda.

### 2. III.5, redactado y **publicado** el 13-oct: el tema más barato de la serie

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **253/255 = 99,2 % PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 253/265 = 95,5 % |
| Hechos | 528 guardados (532 nuevos) → **437 en el plan** (91 repetidos agrupados) |
| Apartados | **10** · ninguno pasó del tope de 150 hechos |
| Forma | **PASA** · 12.253 palabras de 21.120 · repetidos **0,0 %** · `--limpiar-forma` tocó 9 apartados |
| Índice | PASA · **1 grupo y 3 hechos sin materia** (una pregunta; cuatro grupos de C++ son de III.2 y van a la bandeja) |
| Bandeja del propietario | **12 incidencias**: 10 `norma_cambiada`, 1 `clave_sospechosa`, 1 `pregunta_ambigua` |
| Llamadas y coste | **80 llamadas (0 fallidas) · 0,3078 $** · 17 minutos, **sin tope activado** |
| Previsión | 49–85 llamadas · 0,33–**0,58 $** → las llamadas dentro del rango y el coste **por debajo del mínimo** |

**Es el tema más barato de la serie** (0,00385 $ por llamada, precio de tema **técnico**) y el de mejor
cobertura (99,2 %). Y deja medida una cosa que hacía falta para planear: en un tema técnico la cota de
coste de `--prever` es un **techo**, no un suelo —usa 0,0068 $ por llamada, la media con los normativos
dentro, y un técnico cuesta la mitad—. Es exactamente la cara opuesta de I.4, I.8 e I.7.

### 3. III.7, redactado y **publicado** el 13-oct: el banco más heterogéneo, y el ensayo que lo salvó

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **218/233 = 93,6 % PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 218/261 = 83,5 % |
| Hechos | 528 guardados (536 nuevos) → **455 en el plan** (73 repetidos agrupados) |
| Apartados | **11** · ninguno pasó del tope de 150 hechos |
| Forma | **PASA** · 14.726 palabras de 21.120 · repetidos 0,9 % · `--limpiar-forma` tocó 10 apartados |
| Índice | PASA · **1 grupo y 3 hechos sin materia** |
| Bandeja del propietario | **41 incidencias**: 26 `norma_cambiada`, 6 `clave_sospechosa`, 6 `hueco_sin_material`, 3 `pregunta_ambigua` |
| Llamadas y coste | **103 llamadas (0 fallidas) · 0,3990 $** · 24 minutos, **sin tope activado** |
| Previsión | 47–**81** llamadas · 0,32–0,55 $ → **22 llamadas más** que la cota de arriba, y el coste dentro del rango |

Su banco es el que más preguntas de otros temas trae (MySQL y modelo relacional, `iptables`, firma
electrónica y FNMT, archivística, textos legales, ofimática). Con el primer catálogo el **techo medido**
era el **89,2 %** —un borrador seguro— y **el ensayo evitó pagarlo**: la pregunta de OWASP sobre la
prevención del XSS es un grupo de **8 preguntas** y es contenido del **desarrollo web**, así que entró
en el apartado de desarrollo web en servidor y el techo subió a **92,2 %**. Lo que sigue fuera son
preguntas de otros temas y no se lava: va a la bandeja con su motivo.

**Y las dos cifras del mismo tema se dicen**: la corrida cerró en **220/240 = 91,7 %** y, una vez
pasada la puerta de claves (que puso dos conjuntos más en cuarentena), el mismo tema mide
**218/233 = 93,6 %**. Sus preguntas salieron del denominador solas.

### 4. I.7: la decisión escrita, con la cifra delante

**I.7 se queda en borrador y no se reanuda en esta tanda.** Medido hoy, sin pagar nada:

| Qué | Cifra |
|---|---|
| Cobertura hoy | **291/498 = 58,4 %** sobre clave utilizable · 291/531 = 54,8 % sobre todas |
| Lo que costaría reanudarlo | **38–94 llamadas · 0,26–0,64 $** (`--prever` sobre lo guardado) |
| Lo que falta para el 90 % | **157 preguntas** de las 207 que quedan fuera |
| Grupos con clave utilizable **sin comprobar** | **0** (341 de 341 tienen su comprobación guardada) |
| Lo que recupera el bucle de huecos | **un añadido por apartado** (19 como máximo); en esta serie ha recuperado **8, 12, 20, 24 y 26 grupos** |
| Su bandeja, antes / después | **0 → 42 incidencias** (23 `norma_cambiada`, 11 `hueco_sin_material`, 4 `clave_sospechosa`, 4 `pregunta_ambigua`) |

Dos razones, y las dos medidas: **no queda nada sin comprobar**, así que la cobertura solo puede subir
por el bucle de huecos, y **no le faltan comprobaciones: le falta material** —sus 196 huecos dicen que
los apuntes no contestan al 40 % de un banco normativo denso, y su precio por llamada es el **doble**
que el de los técnicos que sí publican—. Por eso van primero los técnicos; I.7 se retoma **con su
cifra** cuando se acaben.

**Y su bandeja ya no está vacía**: se rellenó por el **mismo camino auditado de la corrida**
(`_paso_huecos`, con un modelo de nulo que no añade nada, `f21b-scratch/rellenar_bandeja_utf8.py`), sin
llamar a nadie y **sin inventar una sola incidencia**: las 42 filas salen de las comprobaciones que ya
estaban en la base. Es lo que la regla 3 del encargo pide: un hueco que no se ve es un hueco que no
existe.

### 5. IV.8, redactado y **publicado** el 13-oct: el tema más barato del objetivo

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **221/223 = 99,1 % PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 221/231 = 95,7 % |
| Hechos | 426 guardados (430 nuevos) → **344 en el plan** (82 repetidos agrupados) |
| Apartados | **9** · uno partido por el tope de 150 hechos |
| Forma | **PASA** · 9.541 palabras de 17.040 · repetidos **0,0 %** · `--limpiar-forma` tocó 8 apartados |
| Índice | PASA · **0 grupos y 0 hechos sin materia** |
| Bandeja del propietario | **10 incidencias**: 8 `norma_cambiada`, 2 `clave_sospechosa` |
| Llamadas y coste | **63 llamadas (0 fallidas) · 0,1885 $** · 15 minutos, **sin tope activado** |
| Previsión | 41–70 llamadas · 0,28–**0,48 $** → llamadas dentro del rango y coste **por debajo del mínimo** |

**Es el tema más barato del objetivo**: 63 llamadas a **0,00299 $** cada una, por debajo del 0,00373 $
de IV.6. Y deja una lección de forma que costó 0 $: la corrida cerró con la **forma en NO PASA** porque
la limpieza de la tabla de puertos solo se aplica si el **catálogo marca esa materia como
`tabla_unica`**, y no la marcaba. Bastó añadir la marca (**un atributo del catálogo, sin tocar el
motor**) y pasar **`--limpiar-puertos`** (0 $) para partir la tabla por familias y dejar la forma en
PASA; después, `--publicar` (0 $). Es la tercera vez en la serie que una reparación de 0 $ evita volver
a pagar una corrida.

### 6. El balance de la tanda (f21b), con las cifras medidas

| tema | previsión (llamadas · $) | real (llamadas · $) | cobertura (clave utilizable) | veredicto |
|---|---|---|---|---|
| **III.5** | 49–85 · 0,33–0,58 | 80 · **0,3078** | 253/255 = **99,2 %** | **publicado** |
| **III.7** | 47–81 · 0,32–0,55 | 103 · **0,3990** | 218/233 = **93,6 %** | **publicado** |
| **IV.8** | 41–70 · 0,28–0,48 | 63 · **0,1885** | 221/223 = **99,1 %** | **publicado** |
| | | **0,8953 $** (los tres temas) | | **3 publicados · 0 borradores** |

**Tres temas publicados por 0,8953 $**, con **0,30 $ de media** por tema. El acumulado del objetivo
queda en **≈ 15,35 $ de 40** (≈ 14,45 $ al cerrar f21). La forma pasó en los tres sin volver a llamar
al modelo (`--limpiar-forma` reparó 9, 10 y 8 apartados y `--limpiar-puertos` 1 tabla, todo 0 $). La
puerta de claves del §1 se recalculó al cerrar cada tema y siguió subiendo sola: **90 → 93 → 97 → 99
conjuntos medibles**, con **12 → 12 → 14 → 14 en cuarentena**, cada cambio con su evento de auditoría
(cuatro cambios de veredicto al cerrar III.7, ninguno al cerrar III.5 ni IV.8).

**Lo que la tanda deja medido sobre el precio de un tema**, que es lo que hace falta para planear los
que quedan:

- un tema **técnico** sale a **0,0030–0,0039 $ por llamada** (IV.8 0,00299, III.5 0,00385, III.7
  0,00387), y la corrida entera a **0,19–0,40 $**;
- para un tema técnico la **cota de coste de `--prever` es un techo**, no un suelo: usa 0,0068 $ por
  llamada (la media con los normativos dentro) y un técnico cuesta la mitad. Es exactamente lo
  contrario de lo que pasa con I.4, I.8 e I.7;
- la cota de **llamadas** de `--prever` se quedó corta en las tres corridas de la serie f21 (la de
  III.7 por 22), así que el **bucle de huecos** sigue siendo la partida que no se puede acotar de
  antemano.

**Lo que queda fuera, con el porqué:**

- **I.7** (58,4 %, borrador): decidido y escrito con su cifra, y con su bandeja rellenada;
- **I.4 (88,9 %), I.8 (82,0 %) e I.6 (72,5 % / techo 84,1 %)**, los tres borradores anteriores, siguen
  **sin reanudar**: son normativos densos y su hueco es de **criterio sobre las claves** y de material,
  no de una corrida más;
- **IV.9 (232) y IV.1 (228)**, los dos siguientes por valor, **no se han empezado**: no tienen catálogo
  y escribir uno es el trabajo de la próxima tanda (el ensayo es lo primero, como en estos tres);
- **III.4 (412)** sigue **sin escribir** por el motivo ya medido (su banco es de otra materia en un
  40 %).

---

## F21c · La tanda de contenido cierra los dos que faltaban por valor: IV.1 y IV.9 (13-oct-2026)

**Rama `f21-temas-valor`** (worktree `F:\\temp-opofuente\\opofuente-contenido`), con **`main = 02cfdb3`
dentro** al empezar (la rama ya estaba en ese commit: `git merge main` respondió «Already up to date»).
**Y `main` avanzó a mitad de la tanda**: F22 (`a256321`, la pantalla de Tests) entró en `main` mientras
se corrían los temas, así que **al cerrar se fusionó `main` en esta rama** (un solo choque, en los tres
documentos, resuelto **sumando los dos bloques**; el código de F22 entra sin tocar). Es la
tercera tanda con el **ritmo del §4** de `AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO-2026-10.md`: contenido
**directo sobre la base real**, sin rama de contenido y **sin batería de 18 puertas**. La copia
verificada del día (`20261013-113403-e4c97c.zip`, revisión `0034`) y las migraciones `0035`/`0036` ya
estaban hechas por f21 y **no se han vuelto a tocar**.

### 1. La tabla de valor, vuelta a medir hoy, y el orden que sale de ella

Los números del encargo son los del principio de f21b; medidos hoy con la cuarentena puesta (la
puerta del §1 metió dos conjuntos más al cerrar IV.8) son más bajos:

| Tema | Del encargo | **Medido hoy** | Grupos | Preguntas |
|---|---|---|---|---|
| **IV.1** | 230 | **228** | 229 | 230 |
| **IV.9** | 235 | **227** | 222 | 241 |

**El orden se invierte respecto al encargo** (que decía «IV.9 (232) y IV.1 (228)»): medidos hoy, IV.1
va primero por **una pregunta**. La diferencia es ruido, pero la regla del encargo es que **manda la
medición del día**, así que se corrió IV.1 y después IV.9, y queda escrito.

### 2. Los dos índices, escritos y ensayados **antes** de pagar (0 $)

| tema | apartados | grupos situados por el enunciado | techo medido | revisión del índice |
|---|---|---|---|---|
| **IV.1** | 9 (por asunto, en sus 2 epígrafes) | **223/229 = 97,4 %** | **218/224 = 97,3 %** | PASA |
| **IV.9** | 8 (por asunto, en sus 5 epígrafes) | **200/222 = 90,1 %** | **207/227 = 91,2 %** | PASA |

Los grupos que ningún índice sitúa **no** se lavan: van a la bandeja del propietario con su motivo.
En IV.1 son **6** (Kubernetes, la caché L1, la desnormalización, *mashup* y el ERS del ciclo de vida);
en IV.9 son **22**, y **20 de ellos tienen clave utilizable**, que es lo que pone su techo.

**La sonda de pertenencia por palabras volvió a dar un susto que no era**: en IV.1 decía que el
**32,8 %** de sus grupos no hablaban de su materia y, leídos, eran las versiones con nombre de Debian
y macOS, `ext2/3/4`, APT, Ansible, los directorios del sistema y los tipos de mantenimiento —todo de
IV.1—. Es la segunda vez seguida que orienta mal (en IV.8 pasó lo mismo): **la sonda orienta, el
ensayo decide**.

### 3. IV.1, redactado y **publicado** el 13-oct

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **220/224 = 98,2 % PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 220/228 = 96,5 % |
| Hechos | **431 guardados** (432 nuevos, 10 con la clave señalada) → 331 en el plan |
| Apartados | **9** · ninguno pasó del tope de 150 hechos |
| Forma | **PASA** · 10.153 palabras de 17.240 (58,9 %) · repetidos 0,6 % · `--limpiar-forma` alineó 8 títulos |
| Índice | PASA · **0 grupos y 0 hechos sin materia** al cerrar |
| Bandeja del propietario | **8 incidencias**: 4 `norma_cambiada`, 3 `clave_sospechosa`, 1 `hueco_sin_material` |
| Llamadas y coste | **79 llamadas (0 fallidas) · 0,3281 $** · 33 minutos, **sin tope activado** |
| Previsión | 44–76 llamadas · 0,30–**0,52 $** → 3 llamadas por encima del máximo y el coste dentro del rango |

**Tema técnico, precio de técnico**: 79 llamadas a **0,00415 $**, con el **79,7 % de la entrada en
caché**. La cota de coste de `--prever` volvió a ser un **techo** (0,0068 $/llamada es la media con
los normativos dentro) y se quedó 0,19 $ por encima de lo que costó de verdad.

### 4. IV.9, redactado y **publicado** el 13-oct: el margen más estrecho de la serie

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **205/225 = 91,1 % PASA** (umbral 90 %) |
| Cobertura (todas las que tienen clave) | 205/238 = 86,1 % |
| Hechos | **461 guardados** → 374 en el plan (87 repetidos agrupados) |
| Apartados | **8** · ninguno pasó del tope de 150 hechos |
| Forma | **PASA tras arreglo de 0 $** · 13.383 palabras de 18.440 (72,6 %) · repetidos 0,5 % |
| Índice | PASA · 12 grupos y 22 hechos sin materia (se fueron con sus grupos) |
| Bandeja del propietario | **34 incidencias** (la más llena de la serie): 15 `pregunta_ambigua`, 11 `norma_cambiada`, 4 `clave_sospechosa`, 4 `hueco_sin_material` |
| Llamadas y coste | **73 llamadas (0 fallidas) · 0,3204 $** · 25 minutos, **sin tope activado** |
| Previsión | 40–68 llamadas · 0,27–**0,46 $** → 5 llamadas por encima del máximo y el coste dentro del rango |

**Publica por 1,1 puntos**, y eso se sabía antes de pagar: el techo medido era **91,2 %** porque
**20 de los 22 grupos que ningún índice sitúa tienen clave utilizable** y son de otros temas (PoE,
VLAN, IPv6 y control de acceso al medio de IV.10; RAID 6 y TIA-942 de IV.2 y IV.5; el ENS y la
gestión de incidencias de I.8 y IV.5; `heartbleed` de IV.5; `RFC 2142` y Exchange de IV.3). El
margen lo puso **el banco**, no el índice.

**Y dos preguntas quedan sin cubrir y sin incidencia** (`a3491e88`, `f8b2dfbd`): **el modelo no
contestó** por ellas. Es un fallo de la llamada, no del material, y se dice en su informe.

### 5. La lección de esta tanda: **un tema no puede tener dos tablas de puertos**

La corrida de IV.9 **no archivó la versión**: dejó la forma en NO PASA por dos motivos, los dos de la
tabla de puertos (dos notas que solo decían lo que un puerto **no** es, y la tabla del acceso remoto
sin partir por familias). Se marcó también ese apartado y se volvió a pasar `--limpiar-puertos`
(0 $)… y apareció el defecto de verdad: cada tabla recibe los encabezados «Servicios de red»,
«Escritorio remoto y otros» y «Confusiones que caen», y la puerta de **encabezados repetidos** —que
mira el tema entero— los cuenta **dos veces**. No hay orden de limpiezas que lo tape.

**Lo que se hizo, midiendo antes de tocar nada y a 0 $**: **consolidar las dos tablas en una**. Las
cuatro filas que no estaban en la del cortafuegos (23 Telnet, 69 TFTP, 3389 RDP y 5900 RFB/VNC) se
movieron allí **literalmente** —su mismo servicio, su misma nota, sin inventar ninguna fila—, el
bloque duplicado se quitó del acceso remoto y la marca `tabla_unica` volvió a estar **solo** en el
apartado del cortafuegos. Después, `--publicar` (0 $). **Es la cuarta vez en la serie que una
reparación de 0 $ evita volver a pagar una corrida**, y la primera que **mueve** contenido de un
apartado a otro.

### 6. El balance de la tanda (f21c), con las cifras medidas

| tema | previsión (llamadas · $) | real (llamadas · $) | cobertura (clave utilizable) | veredicto |
|---|---|---|---|---|
| **IV.1** | 44–76 · 0,30–0,52 | 79 · **0,3281** | 220/224 = **98,2 %** | **publicado** |
| **IV.9** | 40–68 · 0,27–0,46 | 73 · **0,3204** | 205/225 = **91,1 %** | **publicado** |
| | | **0,6485 $** (los dos temas) | | **2 publicados · 0 borradores** |

**Dos temas publicados por 0,6485 $**, con **0,32 $ de media** por tema. El acumulado del objetivo
queda en **≈ 16,00 $ de 40** (≈ 15,35 $ al cerrar f21b). La forma pasó en los dos: IV.1 con
`--limpiar-forma` (8 títulos, 0 $) y IV.9 con la consolidación de sus dos tablas de puertos (0 $).
La puerta de claves del §1 se recalculó al cerrar cada tema: **99 → 103 → 105 conjuntos medibles**,
con **14 en cuarentena** y **9 dudosos** en los dos cierres, y **ningún conjunto cambió de veredicto**.

**Lo que la tanda deja medido sobre el precio de un tema**:

- un tema **técnico** sale a **0,0030–0,0045 $ por llamada** (IV.1 0,00415, IV.9 0,00439) y la corrida
  entera a **0,19–0,40 $**: son ya **seis técnicos seguidos** dentro de la banda;
- para un técnico la **cota de coste de `--prever` es un techo**, no un suelo: se quedó por encima en
  los dos temas de esta tanda (0,52 $ frente a 0,3281 $, y 0,46 $ frente a 0,3204 $);
- la cota de **llamadas** se quedó corta en **5 de las 6 corridas** de f21 y f21b, siempre por el
  **bucle de huecos**: es la partida que no se puede acotar de antemano;
- y el **techo medido antes de pagar** (`sin_materia_con_clave.py`) es la cifra que decide si el tema
  merece la pena: IV.8 91,8 % → publicó 99,1 %; IV.1 97,3 % → publicó 98,2 %; **IV.9 91,2 % → publicó
  91,1 %**, al filo.

### 7. Lo que queda fuera, con el porqué

- **I.7** (58,4 %), **I.4** (88,9 %), **I.8** (82,0 %) e **I.6** (72,5 %): los cuatro borradores
  **siguen sin reanudar**, con su cifra escrita y por el mismo motivo medido —su hueco es de
  **material** y de criterio sobre las claves, no de una corrida más—;
- **III.4 (409)** sigue **sin escribir**: su banco es de otra materia en un 40 %, ya medido;
- los **12 grupos de IV.9** y los **6 de IV.1** que ningún índice sitúa: están en la bandeja del
  propietario con su motivo, y en IV.9 son los que ponen el techo en el 91,2 %;
- las **2 preguntas de IV.9** por las que el modelo no contestó: sin cubrir y sin incidencia.

**Con IV.1 e IV.9 quedan publicados 15 de los 33 temas** (medido en la base: 15 temas con versión
archivada **y** apartados escritos; hay una instantánea de II.1 del 6-oct que es del **dossier** del
tema, sin apartados, y no cuenta como tema escrito). Están escritos 19: los 15 publicados más los
cuatro borradores. Los que faltan por escribir son los que la tabla pone por debajo de 227 claves
utilizables (II.1 216, III.3 201, II.3 189, I.3 182, IV.10 180, II.2 173, III.8 169, II.5 155…) más
los cuatro borradores y III.4.

## F22 · La pantalla de Tests: la zona del alumno se cierra (13-oct-2026)

**Rama `f22-zona-alumno`** (árbol `F:\temp-opofuente\opofuente-alumno2`, desde `main = 570e40d`). Sin
fusionar. **Coste de API: 0 $** — es interfaz y una lectura; no se ha llamado a ningún modelo.

### 1. Qué se ha construido: la pantalla que el alumno usaba con el enlace roto

`/tests` estaba en la pantalla de «esta sección todavía no está» (`ComingSoonPage`) y **tres enlaces
vivos le apuntaban ya**: `/tests?count=20` desde Inicio («Test rápido de 20»), `/tests?tema=X` desde el
botón «Test» del Temario y `/tests?tema=X` desde la pestaña «Preguntas» del tema. El motor estaba
hecho y probado desde f11 (`POST /student/tests`); lo que faltaba era la pantalla que traduce un
formulario a esa petición.

Lo que se ve y lo que se puede hacer:

| Qué | Cómo funciona |
|---|---|
| **De qué temas** | El árbol del programa, bloque a bloque, con una casilla por tema. Cada tema dice **cuántas preguntas tiene disponibles** y **qué se ha contestado ya** en él («12 contestadas · 75 % de acierto», o «Sin contestar todavía»). Un tema **sin preguntas sale desactivado** y lo dice, en vez de ofrecer una casilla que no puede cumplir. La casilla del bloque marca y desmarca sus temas (con estado intermedio real, `indeterminate`) |
| **Cuántas preguntas** | Los cinco tamaños que sirve el servidor con lo que durarían: 10 · 20 · 25 · 50 · 100 |
| **Qué preguntas** | Todas · las que no he visto · las que he fallado · las que marqué dudosas (los cuatro filtros del contrato: `all`/`unseen`/`failed`/`flagged`) |
| **Cómo se corrigen** | Al responder · al terminar (`immediate`/`at_end`) |
| **El tiempo** | Un interruptor para poner el reloj del test, con **los minutos que le pondría el servidor**; apagado, dice el tiempo que lleva el test de todas formas (el del examen, 120 minutos en TAI) |
| **Antes de empezar** | Un resumen con lo que se va a montar: «Test de 20 preguntas de 2 temas», y si hay menos preguntas que las pedidas lo dice **antes** de pulsar («solo hay 12 disponibles, así que tendrá 12») |
| **La dirección** | `?tema=X` (repetible) llega con ese tema marcado y `?count=N` con ese tamaño elegido, que es lo que hacen los tres enlaces que ya existían |

### 2. Dónde vive, y qué no se ha tocado

| Qué | Dónde |
|---|---|
| La pantalla | `apps/web/src/pages/student/TestsPage.tsx`; ruta `/tests` en `app/routes.tsx` |
| Los estilos | `global.css`, con los tokens de siempre (ni un `#` fuera de `tokens.css`) |
| El plan del formulario | `GET /student/tests/plan` → `StudentTestPlanView` · `StudentTestPlanSchema` · `student_test_plan` |
| La petición del test | El **mismo** `POST /student/tests` de f11, sin tocar |

**No se ha tocado** el motor (`StudyService.compose`, `_minutos_de_test`), ni la hoja de respuestas, ni
la marca «clave en revisión» (`in_review` sigue llegando del servidor y el texto lo pone la interfaz,
como estaba), ni la bandeja del motor, ni la ficha de pregunta, ni los temas de apuntes, ni
`origin_scope`, ni el INAP. **No hay migración**: solo se añade una lectura.

### 3. Las pruebas, con sus rojos previos

| Prueba | Antes | Después |
|---|---|---|
| `apps/api/tests/integration/test_student_api.py::test_el_plan_del_test_dice_los_tamanos_y_los_minutos_que_luego_se_aplican` | **404** en `/api/v1/student/tests/plan` (`assert 404 == 200`) | pasa: los cinco tamaños, los minutos que anuncia el plan **iguales** a los que recibe cada sesión montada con reloj, y sin reloj el tiempo del perfil (120) |
| `apps/web/tests/unit/studentTestsConfig.test.tsx` (11 pruebas) | `Failed to resolve import "../../src/pages/student/TestsPage" … Does the file exist?` | 11/11 |
| `shell.test.tsx` (la prueba de la sección pendiente) | exigía el aviso «Llega en la siguiente fase» en `/tests` | exige que **no** esté y que el título sea el de la pantalla (ver la decisión del 13-oct) |

**Dos trampas medidas al escribir las pruebas**, y las dos están ahora en una aserción:

1. **sin reloj del test la sesión no se queda sin tiempo**: hereda el de la parte del perfil con la que
   se corrige ese material (**120 minutos** en TAI, porque el tiempo vive en el ejercicio único y la
   parte lo hereda por `parent_code`). La pantalla lo enseña en vez de decir «sin tiempo», y la prueba
   de integración lo comprueba montando el test sin reloj;
2. `timed=True` con un tamaño pequeño **sí** manda sobre el perfil (20 minutos para 10 preguntas), así
   que el interruptor cambia algo de verdad; es la `max()` de `compose` y se prueba con los cinco
   tamaños.

### 4. Lo que queda de la zona del alumno, contado en el código

**Lo que ya está** (medido sobre el árbol, no heredado de la lista):

| Qué | Cifra |
|---|---|
| Entradas del menú del alumno con pantalla | **7 de 7** (Inicio, Temario, Tests, Simulacros, Exámenes, Fallos, Progreso) |
| Direcciones del alumno | **10**: las 7 del menú más `/temario/:codigo`, `/test/:id` y `/resultado/:id` |
| Ficheros de pantalla del alumno | **9** (`apps/web/src/pages/student/*.tsx`) |
| Rutas de la capa del alumno | **18** (`apps/api/opofuente/api/routes/student.py`) |
| Pruebas de componente del alumno | **10 ficheros · 179 `expect`** (uno de ellos, el de F22, con 11 pruebas) |
| Pruebas de integración del alumno | **3 ficheros · 260 `assert`** |

**Lo que falta del §3 del objetivo, punto por punto y con su cifra** (nada de esto se ha tocado):

| Paso del §3 | Estado medido | Lo que falta |
|---|---|---|
| 1 · `compose` + `POST /student/tests`, `/mock-exams`, `GET /official-exams` | **hecho** (f11/f14), y F22 le añade la lectura del plan | nada |
| 2 · Test en curso con hoja de respuestas | **hecho**: teclado `A`–`D`/`1`–`4`, `M`, `←`/`→` e `Intro` (líneas 102–121 del `StudentTestRunner`), corrección al momento o al final, hoja en móvil | **«Ver en apuntes» al párrafo exacto: 0 apariciones** en la zona del alumno (el enlace no existe; la hoja de respuestas se corrige pero no lleva al texto) |
| 3 · Resultado | **hecho**: nota por parte, tiempo, desglose por tema, pregunta a pregunta (incluida la que la plantilla no corrige) | **«Repetir solo las falladas»: no está.** El botón que hay repite el test entero (`filter: 'all'` y el mismo número de preguntas, `ResultPage.tsx:44-51`); el filtro `failed` **ya existe en el motor**, así que es una salida de pantalla, no motor |
| 4 · Inicio, Temario, Tema con pestañas | **hecho** en lo esencial (índice con números romanos y barras, tres columnas de lectura) | de las **3 pestañas** del tema, «Apuntes» es la pantalla y las otras **2 apuntan fuera**: «Preguntas» → `/tests?tema=X` (desde F22 lleva a un test de ese tema, **no** a la lista de sus preguntas) y «Mi progreso» → `/progreso` (el general, no el del tema) |
| 5 · Lectura de apuntes (Stitch) | **hecho**: índice navegable, serif a 68 caracteres, tablas con cabecera, nota al margen por apartado («N preguntas de este tema se contestan en este apartado») y «Esto está mal» por apartado, guardando por su ruta | **buscador dentro del tema: 0**; **marca de leído: 0**; **modo repaso: 0** (no hay vista de tablas sueltas, ni «Datos que caen», ni «Confusiones que caen», ni resumen); **«Practicar este apartado»: 0** |
| 6 · Simulacros, Exámenes oficiales, Fallos y Progreso | **hecho** (f14) | nada (los exámenes salen vacíos porque **no hay ninguno importado**: es D10, datos) |
| 7 · Fuentes autoalojadas y tokens | **hecho** (f13/f14) | nada |

**Y lo que queda del panel** (§4 del objetivo), que no es de este bloque: la **revisión de apuntes**
(leer un borrador y aprobarlo) sigue sin pantalla propia —es lo que el encargo dejaba «si sobra
tiempo», y **no ha sobrado**: se ha cerrado primero el punto 1 y se ha probado—; la **ficha de
pregunta** llegó en f20 y el **temario** del panel sigue pendiente.

### 5. Las capturas (`npm run screens`): 54, las cuatro nuevas a 1280 y 390

`npm run screens`, **54 capturas en 2,0 min**, **54 pasan**, **0 errores de consola** y **0
violaciones de axe** en las 54. Las cuatro de la pantalla nueva:

| fichero | ruta retratada | ancho medido | carga | axe | palabras prohibidas |
|---|---|---|---|---|---|
| `tests-escritorio.png` | `/tests` (con datos sembrados) | **1280 × 5838** | 726 ms | 0 | 0 |
| `tests-movil.png` | `/tests` | **390 × 9300** | 718 ms | 0 | 0 |
| `tests-elegido-escritorio.png` | `/tests?tema=IV.1&count=20` | **1280 × 5838** | 713 ms | 0 | 0 |
| `tests-elegido-movil.png` | `/tests?tema=IV.1&count=20` | **390 × 9300** | 715 ms | 0 | 0 |

Los anchos están medidos sobre el PNG (cabecera IHDR), no deducidos: **los cuatro miden exactamente
1280 y 390 px**. Y las dos capturas de la dirección **afirman sobre la pantalla cargada** que la
casilla de `IV.1` y el tamaño de 20 llegan marcados, para que la evidencia no dependa de mirar el
PNG: un enlace que lleva a una pantalla que ignora lo que pides es el fallo que estas dos pruebas
existen para que no vuelva.

**Un intento fallido, con su causa**: la primera corrida de `npm run screens` murió al arrancar la
vista previa —`The directory "dist" does not exist. Did you build your project?`— porque en un árbol
nuevo no hay `dist` y la herramienta sirve el paquete construido. Se construyó (`npm run build:web`,
1,33 s) y la segunda corrida pasó entera.

**Y una cosa que estaba escrita sin ejecutar y ya se ha ejecutado** (§F19.9): la aserción de las
capturas de la marca «clave en revisión» —`await expect(page.getByText(MARCA_EN_REVISION).first())
.toBeVisible()` en `test-en-curso` y en `resultado`, a los dos anchos— **pasó** en esta corrida. Las
cuatro capturas que la llevan están entre las 54 que pasan, así que la marca queda demostrada en un
navegador de verdad a 1280 y a 390 px, y no solo por la prueba de componente. La marca no se ha
tocado: el servidor sigue mandando `in_review` y el texto lo sigue poniendo la interfaz.

**Un hallazgo que no es de este bloque y se deja dicho**: en el informe de capturas, **`/admin/ui` a
390 px mide 393** (3 px de desborde en la galería de componentes del panel). No es de F22: el PNG de
la corrida de F19 (13-oct, anterior a este árbol) mide **los mismos 393**, y el de F0 medía 390. La
puerta de responsividad del E2E **no cubre** esa pantalla (recorre las del alumno y `/admin/importar`),
así que el desborde lleva dos tandas sin que ninguna puerta lo mire; queda anotado para el panel.

### 6. Las puertas: **18/18** en 41:56 minutos

Ejecutadas con `scripts\gates.ps1` sobre este árbol, con el registro en
**`F:\temp-opofuente\gates-f22-alumno.txt`** (lanzado con `Start-Process -RedirectStandardOutput`,
nunca con `>`). Las 18 en verde: formato, ruff, mypy, eslint, typecheck, **1.553 pruebas de backend**
(unitarias + integración + contrato), **370 de componentes**, contrato OpenAPI y tipos sincronizados,
los dos builds, la migración desde base vacía con su verificación por `sqlite3`, la siembra idempotente,
las fixtures de perfil y la **E2E entera** —que ahora recorre `/tests` también a 390 px—.

**Y los intentos, con su causa**, que es lo que hace falta para que la próxima sesión no repita el
fallo:

| intento | hasta dónde llegó | causa | qué se hizo |
|---|---|---|---|
| **1** | puerta **2** (ruff check) | `E501 Line too long (101 > 100)` en `test_student_api.py:638`: un comentario mío de tres líneas. Yo había pasado `ruff check apps/api/opofuente` (que estaba limpio) y **no** `ruff check .` sobre el repositorio entero, que es lo que hace la puerta | se reescribió el comentario y se comprobó con `ruff check .` **y** `ruff format --check .` antes de relanzar. Registro: `F:\temp-opofuente\gates-f22-alumno-intento1-fallo-ruff.txt` |
| **2** | **18/18** | — | — |

**Los rojos previos de las pruebas, guardados tal cual** (no transcritos a mano):
`F:\temp-opofuente\f22-scratch\rojo-plan-del-test.txt` (el `404` de la ruta que aún no existía) y
`F:\temp-opofuente\f22-scratch\rojo-pantalla-tests-err.txt` (`Failed to resolve import
"../../src/pages/student/TestsPage" … Does the file exist?`).

### 7. La fusión con `main` (`02cfdb3`): los tres documentos se suman, el código no se toca

El bloque de contenido (`F21b`) entró en `main` antes, y los dos habíamos añadido al final de los
mismos tres documentos. **Commit de la fusión: `cfd3756`** (padres `bbb73c0` y `02cfdb3`).

**Cómo se resolvió, y por qué así:**

- los choques eran **solo texto en los tres documentos** (`DECISIONES`, `ESTADO` y
  `PARA-EL-PROPIETARIO`); en los dos primeros el conflicto era literalmente «los dos añadimos al
  final». `PARA-EL-PROPIETARIO` lo auto-fusionó git;
- la resolución es el **merge automático de git** (`git merge-file --diff3`, el mismo motor que usa
  `git merge`), con el bloque en conflicto **concatenado**: primero la parte de `main` (F21b y sus 5
  decisiones) y después la mía (la sección F22 y sus 10 decisiones), en orden cronológico. Todo lo
  que **no** estaba en conflicto queda exactamente como git lo fusionó: no se toca ni una línea;
- **no se elige: se suma**, y está comprobado **por conteo**, no a ojo. La lista de líneas con
  contenido del fichero resuelto es **idéntica, en el mismo orden**, a la del merge automático con
  los dos bloques concatenados (DECISIONES 156 líneas con contenido, ESTADO 1.564, PARA 572). Y las
  secciones están enteras: **61 filas** de decisión = 44 de antes + **7 de `main`** (F21b) + **10
  mías** (F22); en el estado, la sección **F21b** de `main` con **157 líneas** y la **F22** con **147**.

**Ese conteo cazó una pérdida real**: en un primer intento de resolución a mano se me quedó fuera un
separador `---` de la junta, y por eso la resolución se rehízo desde `git merge-file`. Y una segunda
trampa del mismo intento, dicha para la próxima sesión: **`Set-Content -Encoding UTF8` de PowerShell
5.1 escribe BOM y CRLF**; los documentos del repositorio van en UTF-8 **sin BOM** y con LF, y así se
escribieron (desde Python).

**El código no se toca en esa fusión**, comprobado fichero a fichero:

- los cuatro ficheros de código que trae `main` (`catalogo_iii_5.py`, `catalogo_iii_7.py`,
  `catalogo_iv_8.py` y `topic_index.py`) quedan **idénticos** a la versión de `main`;
- mis **16** ficheros de código, pruebas y contratos quedan **idénticos** a `0853626`: la fusión no
  les ha hecho nada;
- y el choque que se temía **no existe**: `main` **no tocó nada de `apps/web`** (ni `screens.spec.ts`
  ni `routes.tsx`). El bloque de contenido trajo tres catálogos, su registro, tres informes y sus
  documentos.

**Puertas de la fusión: 18/18 en 51:32 minutos**, registro en
**`F:\temp-opofuente\gates-f22-fusion.txt`** (827 unitarias + 697 integración + 29 contrato,
370 componentes y E2E 74/74). **Dos intentos, con su causa:**

| intento | hasta dónde llegó | causa | qué se hizo |
|---|---|---|---|
| **1** | puerta **7** (integración): 696 pasan y **1 error** | `sqlite3.OperationalError: database or disk is full` al montar `test_question_topics_bulk_api.py`. **No era del código**: F: se quedó sin espacio porque **otro bloque (`opofuente-inap`) estaba importando los 32 exámenes del INAP** contra la base real (2,6 GB, en F:) *a la vez*. Registro: `gates-f22-fusion-intento1-fallo-disco.txt` | se liberaron **749 MB** de temporales propios (`.pytest-tmp`, `.gates-data`, `test-results`), se comprobó que F: volvía a 6,3 GB libres y se relanzó entera |
| **2** | **18/18** | — | — |

Lo que ese fallo enseña, y conviene no volver a aprender: **el disco es un recurso compartido entre
bloques**, como el puerto 8765. La batería escribe una base por prueba en `.pytest-tmp` (dentro del
árbol, por el `--basetemp` de `pyproject.toml`) y necesita varios GB libres en F: durante 40 minutos;
si otro bloque escribe en F: a la vez, la puerta 7 puede caer por `database or disk is full` **sin
que el código tenga nada que ver**. Lo que lo distingue: el mensaje de SQLite y el proceso del otro
bloque.

## F23 · Los exámenes del INAP y de dónde sale cada conjunto (13-oct-2026)

**Rama `f23-inap`** (worktree `F:\temp-opofuente\opofuente-inap`, desde `main = a256321`). Sin fusionar.
**Coste de API: 0 $** — no se ha llamado a ningún modelo: es conversión de PDF, datos y una pantalla.

### 1. `origin_scope`: qué es y cómo queda en los datos

El objetivo (`DECISIONES-Y-SIGUIENTE-TANDA §1`, `GOAL D10`) lo define como **la procedencia del
conjunto** con tres valores, y su única consecuencia es **qué entra en un simulacro**:

| valor | qué significa | qué hace |
|---|---|---|
| `age` | Administración General del Estado (INAP, Guardia Civil) | entra en todo |
| `otra_administracion` | otra administración (ayuntamientos, comunidades, universidades) | **fuera** de un simulacro y de un examen (`exam_like`); cuenta en tests por tema y en los apuntes |
| `desconocida` | material cuya administración de origen no se puede afirmar | entra en todo (el valor por defecto, y el que **no excluye de nada**) |

Lo que se ha construido:

| qué | dónde |
|---|---|
| La columna, su `CHECK` de tres valores y su índice | migración `0037_origin_scope` (`apps/api/alembic/versions/0037_origin_scope.py`) |
| El vocabulario, con su porqué | `domain/questions.py` → `OriginScope` |
| Declararla al crear y cambiarla después, **auditado** | `CreateQuestionSetSchema.origin_scope` y `PatchQuestionSetSchema.origin_scope`; `QuestionService.set_origin_scope` → `question_set.origin_scope_changed` |
| La consecuencia: el simulacro deja fuera `otra_administracion` | `study_service._candidatas` con `CompositionSpec.exam_like` |
| Que el alumno sepa qué practica | `origin_scope` en la lista de exámenes (contrato del alumno, vista, esquema y `OfficialExamsPage`) |
| El relleno hacia atrás de los 237 conjuntos que ya estaban | `tools/marcar_procedencia.py` (regla por título, con su motivo, **49** cambios auditados) |

**En los datos, medido:** 242 conjuntos no archivados → **30 `age`** (15 exámenes oficiales + 15
bancos privados que son exámenes de la AGE: los tres «examen completo, con su plantilla» y los doce
`TAI_ejer_*_AGE_*`), **28 `otra_administracion`** (12 de administración local, 11 de comunidades o
parlamentos, 5 de universidades) y **184 `desconocida`**.

### 2. Los 16 exámenes del INAP: qué ha entrado y qué no

El manifiesto tiene **16 cuestionarios**, cada uno con su plantilla. El comando
`tools/importar_inap.py` convierte el PDF (numeración oficial, reservas marcadas, cabeceras fuera),
comprueba que la plantilla **encaja en el orden del documento** y escribe por los métodos del
servicio. La segunda mitad (`tools/inap_biblioteca.py`) sube la plantilla a la biblioteca por las
rutas de la API, la promociona a documento `answer_key`, la acepta y la **enlaza** a la clave —que es
lo que la deja **activa** y el examen practicable.

| # | examen | qué ha pasado | preguntas |
|---|---|---|---|
| 1-3 | **2018** libre 1.º, libre 2.º y PI | **FUERA**: los tres cuestionarios son escaneos **sin capa de texto** (0 caracteres en 10 páginas) y el OCR no está operativo (sin `tesseract.exe`; solo hay `tessdata`) | — |
| 4-13 | **2019, 2022, 2024, 2025 extraordinario** (libre y PI, modelos A y B) | **IMPORTADOS** (9 conjuntos, 9 claves): 135 preguntas (120 + 15 reservas) los de libre y 85 (74 + 11) los de PI, con la numeración oficial por secciones (80/5/20/5/20/5 y 50/5/12/3/12/3) | 135 / 85 |
| 14-17 | **2025** libre A y B, PI A y B | **YA ESTABAN y no se han duplicado**: se ha verificado que sus claves coinciden con las plantillas oficiales **135/135** y **85/85** alineando en el orden del documento | 135 / 85 |

**El resultado en la zona del alumno** (`GET /student/official-exams`): **13 exámenes oficiales**,
**11 practicables** (clave activa), todos con su procedencia (`age`) y su número de preguntas.

**Los dos que no se pueden hacer todavía, con el motivo medido** (2022 libre y 2025 extraordinario):
la clave se queda en **borrador** porque su plantilla **ya estaba en la biblioteca desde el 29-sep**
con la evidencia **recortada** —1.198 de 1.276 caracteres citables— por el fallo de extracción que se
corrigió en octubre (`MAX_EVIDENCE_CHARS`, `domain/evidence.py`). Sin las últimas líneas, el enlace
—que compara la plantilla con la clave pregunta a pregunta— confirma **60 de 135** y **se niega**, en
vez de activar una clave que no puede demostrar. **El choque lo ha detectado el sistema, no se ha
tapado.** Medido sobre la biblioteca entera: **3.474 de 5.162** versiones cortas tienen la evidencia
recortada (**1,71 M** de caracteres que no se pueden citar).

### 3. El TAI 2024 modelo A, que ya estaba en el banco con la numeración desplazada

| copia | qué es | qué se ha hecho |
|---|---|---|
| `ddc98b71…` «TAI_ejer_1_A_libre_AGE_2024 (preguntas con clave publicada)» | **banco privado**, 78 preguntas, posiciones 1..78 sin reservas, clave con 78 entradas, **`no_fiable`** desde F19 | **no se toca** (la cuarentena no se toca). Cubre el **58 %** del documento oficial |
| `3516c265…` «TAI ingreso libre 2024 (examen completo, con su plantilla)» | banco privado, 135 preguntas con 15 reservas, `fiable` | **no se toca**: cubre el **99 %** del documento oficial de 2024 A (y el 98 % del B) |
| **el nuevo** «TAI ingreso libre 2024 · modelo A (examen oficial INAP)» | **examen oficial** con la numeración oficial (80+5 / 20+5 / 20+5), `origin_scope = age`, `public`, clave **activa** enlazada a la plantilla | es la **verdad practicable** |

**Una sola verdad, dicha**: para practicar el examen de 2024 A se usa el conjunto oficial nuevo (el
único que aparece en la pantalla de exámenes y el único cuya clave está activa y enlazada a la
plantilla oficial). Las dos copias del banco privado se quedan como estaban —una de ellas en
cuarentena, así que sus preguntas no entran en tests, simulacros ni repasos— y su solapamiento queda
escrito con su cifra.

### 4. La clave oficial, intacta y protegida

- **La clave se copia tal cual**: el comando manda el texto de la plantilla oficial
  (`texto_de_plantilla`, sin tocar una letra: `ANULADA`, `MODIFICADA` y la numeración reiniciada se
  quedan como están) y el importador la aplica **en orden**. No hay ninguna interpretación.
- **La guarda ya existía y cubre lo importado**: `protege_cambiar_la_clave` protege por el **tipo**
  del conjunto (`official_exam`) o por tener la plantilla enlazada a un documento, y los exámenes
  importados son las dos cosas. La prueba nueva lo comprueba con un examen montado como lo deja el
  importador: `protected_sets` lo incluye con su motivo y `POST
  /question-files/{id}/answer-key` responde **409 sin escribir nada** (la clave sigue siendo `a`).
- **Y la invariante no se ha relajado**: activar la clave de un examen oficial exige la plantilla
  enlazada (`can_activate`). En vez de saltársela, la plantilla entra en la biblioteca **por el
  pipeline de la API** (subida → extracción del worker → promoción a `answer_key` → aceptación) y el
  enlace **verifica las 135 respuestas** antes de activar. Ese es el dato firme del §1: no una lista
  de nombres, sino un documento enlazado y comprobado.

### 5. Las pruebas, con sus rojos previos

| prueba | qué defiende |
|---|---|
| `apps/api/tests/unit/test_inap.py` (9) | la conversión: numeración oficial, reservas marcadas con `(R)`, opciones partidas que se juntan, cabeceras que no ensucian la última opción, una línea que empieza por número y **no** es la pregunta (se declara), un PDF sin capa de texto que se rechaza, la plantilla tal cual, y —la que cierra el círculo— que el texto convertido lo lee el **parser de verdad** del proyecto sin una sola incidencia. Uno de los casos mide el PDF real de 2024 A (80/5/20/5/20/5, 120 ordinarias, 15 reservas, cero líneas descartadas) |
| `apps/api/tests/integration/test_origin_scope.py` (4) | la procedencia declarada, cambiada y **auditada** con su antes y su después; el vocabulario cerrado y el `PATCH` vacío rechazados **sin escribir**; `exam_like` que deja fuera las 6 preguntas de otra administración y trae las 6 de la AGE (y que el test por tema sí las trae); y el examen oficial importado **protegido**, con la ficha devolviendo 409 |
| `apps/api/tests/integration/test_migrations_0037.py` (4) | la columna con sus tres valores, el valor por defecto `desconocida` sobre lo que ya estaba, los `CHECK` anteriores que sobreviven a la recreación de la tabla, y la vuelta atrás que se lleva columna, `CHECK` e índice y se puede volver a subir |

### 6. Lo que queda fuera, y por qué

1. **Los tres exámenes de 2018**: sin capa de texto y sin OCR instalado. No se transcriben a mano.
2. **Dos exámenes sin clave activa** (2022 libre y 2025 extraordinario): la evidencia recortada de su
   plantilla en la biblioteca. La salida es volver a extraer la evidencia de esas versiones con el
   código de hoy, y **no hay ruta para hacerlo** (es trabajo pendiente, no un rodeo).
3. La `held_at` de los 13 exámenes queda nula: ni el cuestionario ni la plantilla declaran la fecha,
   y no se inventa.

### 7. Añadidos tras la revisión del agente padre (13-oct-2026, noche)

**Las 32 descargas son 16 cuestionarios y sus 16 plantillas.** El manifiesto `inap-tai` trae las dos
cosas por examen, y por eso cada examen se puede importar **con su clave**: sin la plantilla no se
importa la clave, y sin clave el examen no se puede corregir.

**a) La procedencia llega también a los conjuntos archivados (53 cambios, no 49).** El primer relleno
leía la lista de conjuntos **vivos**, así que los cuatro archivados de 2025 (`b9798368`, `200c1c04`,
`ee30a6d1`, `4b87ff6b`) se quedaban en `desconocida`. Era un agujero **de la regla, no de los datos**:
los cuatro **son** exámenes oficiales del INAP. `marcar_procedencia.py` gana `--incluir-archivados` y
quedan en `age` (**4 cambios más**). La protección de una clave oficial no depende de que un conjunto
salga en la lista de vivos.

**b) Los modelos A y B no comparten clave: son dos plantillas distintas sobre el mismo cuestionario.**
Medido entrada a entrada, en el orden del documento, sobre las dos claves **activas**:

| pareja | entradas | iguales | distintas |
|---|---|---|---|
| TAI libre 2025, A contra B | 135 y 135 | 47 | **88** |
| TAI promoción interna 2025, A contra B | 85 y 85 | 40 | **45** |

(Ejemplos del de libre: posición 3 → A «c», B «a»; posición 4 → A «a», B «c»; posición 5 → A «d», B
«b».) El cuestionario es el mismo —medido por firma: 131 de 135 en el de libre y **85 de 85** en el de
promoción interna— y lo que cambia es la plantilla, que es como el INAP cruza las respuestas entre
modelos. **Ninguno de los dos sobra**: los dos nombres parecidos son los dos modelos publicados.

**c) La plantilla recortada, con nombre y apellidos.** Los dos exámenes que se ven y no se pueden
hacer son **«TAI ingreso libre 2022 · ejercicio único»** y **«TAI ingreso libre 2025 ·
extraordinario»**: la versión de su plantilla que **ya estaba en la biblioteca desde el 29-sep** tiene
la evidencia recortada (1.198 de 1.276 caracteres citables), y el enlace que verifica la plantilla
contra la clave confirma 60 de 135 y **se niega**. El sistema lo detectó solo; no se ha tapado ni se
ha activado una clave a medias. La reparación —volver a extraer el texto de esas versiones con el
código de hoy— **no tiene ruta todavía**, y alcanza a **3.474 de 5.162** versiones cortas de la
biblioteca (**1,71 M** de caracteres que no se pueden citar).

### 8. Las capturas, y la batería con sus intentos y sus causas

**Las capturas de la pantalla de Exámenes, con un examen oficial de verdad.** El guion de capturas
(`apps/web/tests/screens/screens.spec.ts`) monta un examen oficial **por las rutas de la API** —tipo
`official_exam`, procedencia `age`, sus 135 preguntas con la numeración oficial por secciones
(80 + 5 + 20 + 5 + 20 + 5), su visibilidad a `public` y su clave activada— y retrata `/examenes` a los
dos anchos. Y **afirma** lo que la captura tiene que enseñar, para que la evidencia no sea un PNG que
hay que mirar a ojo:

| comprobación | resultado |
|---|---|
| la procedencia se lee en pantalla («Administración General del Estado») | sí |
| el número de preguntas del examen se lee («135 preguntas») | sí |
| violaciones de accesibilidad (axe, `wcag2a/2aa/21a/21aa/22aa`) | **0** |
| errores de consola | 0 |
| tamaño de la captura de escritorio | `artifacts/screens/examenes-oficiales-escritorio.png` · **1280×800** |
| tamaño de la captura de móvil | `artifacts/screens/examenes-oficiales-movil.png` · **390×847** |

El `expect(violaciones).toEqual([])` es una exigencia **nueva** del guion: hasta ahora el informe
apuntaba las violaciones pero no bloqueaba. Se añade para esta captura, que es la que se ha pedido con
«0 axe», y sin cambiar el comportamiento de las demás (el guion de capturas **no** entra en las
puertas: `npm run e2e` mira solo `tests/e2e`).

**La batería de 18 puertas, con sus tres intentos y la causa de cada uno.**

| intento | commit | hasta dónde llegó | causa | qué se hizo |
|---|---|---|---|---|
| **1** | `70b89c4` | **puerta 7** (integración) | dos pruebas cayeron **bajo la carga de mis propios comandos en paralelo** (`npm ci`, `typecheck`, `lint`, el script de procedencia y la API en el 8799): `test_changes.py::test_confirmar_un_cambio_actualiza_la_revision_...` (`assert 0 >= 1` al buscar «veinte» tras confirmar un cambio) y un **error de teardown** en `test_classification.py::test_el_mismo_texto_pegado_dos_veces...` (`InvariantViolationError: el trabajo pertenece a otro worker`). **No son de mi cambio**: el mismo par pasa aislado (2/2) y juntos (23/23) en cuanto la máquina está quieta, y en la corrida completa anterior a la batería ya habían pasado | se guardó el registro (`gates-f23-inap-intento1-fallo-puerta7.txt`), se aislaron las dos pruebas para demostrar que pasan, se paró mi API y **se repitió la batería con la máquina quieta** |
| **2** | `e93dbd5` | **18/18** | — | registro: `gates-f23-inap-intento2-18de18-en-e93dbd5.txt` (integración **705 pasan**, contrato **29**, componentes **370**, E2E **74**) |
| **3** | `8c8cdf0` (el de la fusión) | **18/18** | — | la fusión trae código de `main`, así que el árbol que midió el intento 2 **no era** el que se fusiona: se repitió entera en vez de dar por bueno un registro de otro árbol. Registro: `gates-f23-inap-intento3-18de18-en-8c8cdf0.txt` (unitarias **836**, integración **705**, contrato **29**, componentes **370**, E2E **74**) |

Los tres registros están en `F:\temp-opofuente\`, sin transcribir: son la salida literal de la batería.
**El cambio de estos párrafos es posterior a la tercera batería y solo toca `docs/*.md`**, que ninguna
de las 18 puertas lee (ruff, mypy y las suites miran `apps/`; el paso 17 mira los fixtures de perfil y
los `docs/apuntes/` de las fuentes, no estos tres documentos).

## F24 · La tanda de contenido cierra los cinco que quedaban por valor (14-oct-2026)

**Rama `f21-temas-valor`** (worktree `F:\temp-opofuente\opofuente-contenido`), puesta al día **antes de
empezar**: `git merge main` respondió **«Fast-forward»** desde `09a38cc` hasta **`511a8a9`** (el bloque
del INAP y el de la zona del alumno entran sin tocar nada). Base real en **`0037_origin_scope`**. Es la
cuarta tanda con el **ritmo del §4** de `AJUSTES-AL-OBJETIVO-CLAVES-Y-RITMO-2026-10.md`: contenido
**directo sobre la base real**, sin rama de contenido y **sin batería de 18 puertas**.

**Copia verificada al empezar la tanda**, que es nueva porque la anterior era de la revisión `0036`:
`20261014-101138-3c75b9.zip` (805.529.470 B, revisión `0037_origin_scope`), verificada de verdad
(`verify_archive` sin problemas, CRC de las 2 entradas correcto, `PRAGMA integrity_check` = ok,
`quick_check` = ok, `foreign_key_check` = 0 filas, y los bytes extraídos coinciden con la instantánea:
sha256 `f3fa671d…`, 665.588 páginas × 4096 = el tamaño exacto).

### 1. La tabla de valor, vuelta a medir hoy, y los cinco catálogos

Medida hoy con la cuarentena puesta, coincide con la del encargo y **manda esa medición**:

| Tema | Del encargo | **Medido hoy** | Grupos | Preguntas | Apartados del catálogo | Techo medido (0 $) |
|---|---|---|---|---|---|---|
| **II.1** | 216 | **216** | 214 | 223 | 14 | **96,3 %** |
| **III.3** | 201 | **201** | 181 | 201 | 14 | **93,5 %** |
| **II.3** | 189 | **189** | 171 | 191 | 11 | **91,5 %** |
| **I.3** | 182 | **182** | 168 | 183 | 15 | **85,7 %** |
| **IV.10** | 180 | **180** | 185 | 185 | 12 | **97,2 %** |

**Ninguno tenía catálogo**, así que escribirlo y ensayarlo fue lo primero (0 $) en los cinco, y los
cinco `--esquema` **PASAN**. El techo medido es la cifra que decide y **es un suelo, no un techo**: I.3
prometía 85,7 % y publicó **92,8 %**.

### 2. Los cinco temas, redactados y **publicados** el 14-oct

| Qué | **II.1** | **III.3** | **II.3** | **I.3** | **IV.10** |
|---|---|---|---|---|---|
| Cobertura (clave utilizable) | **201/204 = 98,5 %** | **191/208 = 91,8 %** | **181/190 = 95,3 %** | **168/181 = 92,8 %** | **171/175 = 97,7 %** |
| Cobertura (todas las claves) | 201/214 = 93,9 % | 191/213 = 89,7 % | 181/194 = 93,3 % | 168/182 = 92,3 % | 171/181 = 94,5 % |
| Forma | PASA · 1,1 % rep. | PASA · 0,7 % | **PASA tras arreglo de 0 $** · 0,0 % | PASA · 1,7 % | PASA · 0,0 % |
| Índice | PASA · 0 y 1 sin materia | PASA · 5 y 11 | PASA · 3 y 7 | PASA · **0 y 0** | PASA · 1 y 1 |
| Hechos | 447 → 365 en el plan | 382 → 322 | 343 → 267 | 300 → 193 | 386 → 314 |
| Bandeja | **13** | 20 | 13 | 11 | 10 |
| Llamadas · coste | 26 · **0,0577 $** (cierre) | 83 · **0,2432 $** | 36 · **0,0835 $** (2.º intento) | 83 · **0,3733 $** | 71 · **0,2440 $** |
| Precio por llamada | — | **0,00293 $** | **0,00232 $** | 0,00450 $ | 0,00344 $ |
| Minutos | 14,3 + 13 | 13,8 | 12,6 + 7,5 | 29,8 | 18 |
| Veredicto | **publicado** | **publicado** | **publicado** | **publicado** | **publicado** |

### 3. El balance de la tanda (f24), con las cifras medidas

| tema | previsión (llamadas · $) | real | cobertura (clave utilizable) | veredicto |
|---|---|---|---|---|
| **II.1** | 46–81 · 0,31–0,55 | 26 medidas + la primera (no medida) · **0,0577 $ medidos** | 201/204 = **98,5 %** | **publicado** |
| **III.3** | 42–74 · 0,29–0,50 | 83 · **0,2432 $** | 191/208 = **91,8 %** | **publicado** |
| **II.3** | 37–65 · 0,25–0,44 | 36 en el 2.º intento · **0,0835 $ medidos** | 181/190 = **95,3 %** | **publicado** |
| **I.3** | 39–69 · 0,27–0,47 | 83 · **0,3733 $** | 168/181 = **92,8 %** | **publicado** |
| **IV.10** | 40–70 · 0,27–0,48 | 71 · **0,2440 $** | 171/175 = **97,7 %** | **publicado** |
| | | **1,0017 $ medidos** (≈1,30–1,46 $ con lo estimado) | | **5 publicados · 0 borradores** |

**Cinco temas publicados y ninguno en borrador.** El acumulado del objetivo queda en **≈ 17,3 $ de
40** (≈ 16,00 $ al cerrar f21c). La forma pasó en los cinco y **no costó ninguna llamada**:
`--limpiar-forma` alineó tres títulos en II.3, una tabla se reparó insertando la línea de separación
que le faltaba, y `--publicar` cerró los cinco (0 $). La puerta de claves del §1 se recalculó al cerrar
cada tema: **108 → 110 → 112 → 113 → 116 conjuntos medibles**, con **15 → 16 → 16 → 16 → 17 en
cuarentena**, cada cambio con su evento de auditoría.

**Lo que la tanda deja medido sobre el precio de un tema**:

- un tema **técnico** sale a **0,0023–0,0045 $ por llamada** y la corrida entera a **0,08–0,24 $**:
  III.3 (**0,00293 $**) y II.3 (**0,00232 $**) son los dos temas más baratos del proyecto;
- **«normativo» no quiere decir «caro»**: I.3 salió a **0,00450 $** por llamada, la banda de los
  técnicos, no la de los normativos densos (I.4, I.5, I.7: 0,0078–0,0083 $). El precio lo fija el
  banco, no la etiqueta. La regla de **duplicar la cota** en los normativos se aplicó al decidir el
  tope de I.3 (0,94 $) y resultó **conservadora**: la corrida costó 0,3733 $;
- la cota de **llamadas** de `--prever` se quedó corta en cuatro de las cinco corridas (por 1, 9, 14 y
  el bucle de huecos), pero **en IV.10 solo por una**: es la primera vez en la serie que el bucle de
  huecos no desborda la previsión;
- la cota de **coste** volvió a ser un **techo** en todos los técnicos (III.3 0,50 → 0,2432; IV.10 0,48
  → 0,2440; II.3 0,44 → 0,0835 medidos).

**Lo que la tanda deja medido sobre el método**:

- **un techo medido por el enunciado no es un techo**: I.3 prometía 85,7 % (por debajo del listón) y
  publicó 92,8 %. Lo que lo sube es el camino del motor que sitúa un grupo por **los hechos de sus
  preguntas**, y en I.3 además los **cajones de epígrafe**;
- **ese mismo camino es el que deja entrar material de otro tema**: es el defecto de I.3 del §5, y hoy
  **no hay ninguna puerta que mire si el apartado al que se ancla una respuesta es del tema**;
- **los títulos del catálogo pasan por la puerta de encabezados repetidos**: tres apartados que
  compartan las tres primeras palabras del título dejan el tema sin publicar. Se mira **antes de
  correr**, que es gratis;
- **los patrones genéricos son la puerta de entrada del material ajeno**: `ansi`/`iso`/`estándar` en
  III.3 y `formato`/`fichero` en II.3. El ensayo los caza a 0 $.

### 4. Dos corridas cuyo informe se perdió, dicho con su causa y su cifra

**II.1 murió a lo bruto** con `STATUS_HEAP_CORRUPTION` (`exit=-1073740022`, `0xC0000374`) **después**
de archivar la versión: los hechos, los apartados y 207 de 214 comprobaciones quedaron escritos, pero
**el informe —llamadas y coste— se perdió con el búfer**, así que su coste va **estimado (0,20–0,36 $)**
y no medido. Un proceso muerto deja echado el candado `apuntes_en_curso`, y los cuatro temas
siguientes se negaron **antes de llamar a nadie** (coste 0 $) hasta que se soltó por el camino que el
propio motor documenta. **No fueron dos corridas a la vez**: la serie era en serie. Arreglos aplicados:
`python -u` y reintento tras soltar el candado.

**Y un defecto del lanzador, con su coste**: el reintento estaba puesto para **cualquier** código
distinto de cero, y un **código 3** no es un fallo sino «no pasa la puerta de forma». A **II.3** le
costó una segunda corrida de **0,0835 $** que no arreglaba nada (lo que hacía falta era una reparación
de **0 $**), y el guion escribía los dos intentos en el **mismo fichero**, así que el coste del primero
(≈0,10 $) se perdió. **≈0,12 $ de más por dos defectos del guion, no del motor.**

**II.1 se completó** con una segunda corrida (0,0577 $, 26 llamadas, sin rehacer ni un hecho ni un
apartado): subió de 96,6 % a **98,5 %**, comprobó 213 de 213 y dejó las incidencias escritas. Y su
bandeja, que la corrida muerta dejó **vacía**, se rellenó a **0 $** por el mismo camino auditado de la
corrida (`_paso_huecos` con un modelo nulo que no añade nada): **0 → 10**.

### 5. El defecto de I.3, con su tamaño, y la puerta que falta

**Uno de los 15 apartados de I.3 (`i-3-1-otros`) no es material del tema**: contiene el estándar
**ANSI/TIA-942-B** del CPD (MDA, HDA, EDA), que es de **IV.5.7**. Medido: **1 apartado de 15**, **2
hechos de 300** (0,7 %), **730 caracteres** de ~45.000 (1,6 %) y **5 preguntas de 181**. El grupo no
trae epígrafe y ningún patrón lo sitúa —así que el índice lo deja fuera—, pero el motor tiene un camino
para no perder un hecho que no reconoce ninguna materia: **caerlo a la materia de la pregunta de la que
sale**; con esas anclas, el grupo acabó en el cajón y sus respuestas se contaron como cubiertas.

**No se ha borrado a propósito**: la puerta de cobertura **cuenta comprobaciones guardadas, no el
texto**, así que quitar los hechos y vaciar el apartado dejaría la cifra publicada en 92,8 % mientras
el alumno ya no lee esas frases. La cifra honesta, descontando el lavado, es **163/181 = 90,1 %**, que
también pasa el listón; en el informe van **las dos**.

**Y queda dicho como hueco del método**: hoy **no hay ninguna puerta que mire si el apartado al que se
ancla una respuesta es del tema**. La de cobertura dice cuántas respuestas están contestadas, no por
quién. Es la comprobación que falta si «no se lava» tiene que ser una medida y no un propósito.

### 6. Lo que queda fuera, con el porqué

- **I.7 (57,1 %), I.8 (81,2 %) e I.6 (71,4 %)**: los tres borradores que quedan, con su cifra escrita y
  por el motivo **ahora medido por causa** (§7): **0 grupos sin comprobar** en los tres, así que todo
  lo que les falta está comprobado y sin cubrir —eso es **material**— y ninguna corrida mueve su cifra
  ni un punto;
- **III.4** sigue **sin escribir**: su banco es de otra materia en un 40 %, ya medido;
- **los 8 grupos de II.1, 5 de III.3, 10 de II.3, 19 de I.3 y 5 de IV.10** que ningún índice sitúa:
  están en la bandeja del propietario con su motivo, y son los que ponen el techo de cada tema;
- **la pregunta del CPD en I.3**: contada como cubierta y declarada en el §5, con las dos cifras;
- **las 2 preguntas de IV.10 y las 2 de IV.9** por las que el modelo no contestó: sin cubrir y sin
  incidencia, porque el fallo es de la llamada y no del material.

**Con estos cinco quedan publicados 20 de los 33 temas**, y con el cierre de I.4 del §7, **21**.

### 7. I.4 se cierra el 14-oct a coste 0 $: publicado, y pasa por **0,2 puntos**

**I.4 estaba escrito desde el 11-oct y quedó en borrador cuando medía 497/559 = 88,9 %.** No se ha
escrito ni una línea nueva: lo que ha cambiado es **el denominador**, que se mueve solo con la
cuarentena de claves del §1 (al cerrar f21 había **10** conjuntos en cuarentena; hoy hay **17**, y sus
preguntas salen del cómputo). La puerta, medida hoy sobre lo guardado:

| Puerta | Umbral | 11-oct | **14-oct** | Veredicto |
|---|---|---|---|---|
| Preguntas cubiertas (clave utilizable) | ≥ 90 % | 497/559 = 88,9 % | **489/542 = 90,2 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 497/579 = 85,8 % | 489/555 = 88,1 % | — |
| Párrafos casi repetidos | ≤ 5 % (el código) | 4,2 % | 4,2 % | PASA |
| Extensión | ≤ 40 palabras × hecho | 27.787 de 42.240 | 27.787 de 42.240 | PASA |

`--publicar --tema I.4` mide las dos puertas **sobre lo ya guardado** y archiva la versión si pasan:
**0 llamadas · 0,0000 $**. **Es la sexta vez en la serie que una reparación de 0 $ evita volver a
pagar una corrida, y la primera en que la reparación es simplemente volver a medir.**

**Se publica, y el margen va dicho: pasa al 90,2 %, margen de 0,2 puntos.** Tres razones: cumple la
regla del objetivo **tal como está escrita** (y aplicarle otra a este tema sería cambiarla a mitad de
camino, después de veinte temas); **publicar no es aprobar para siempre** —sale con la marca «Versión
generada · en revisión» y desde el panel se retira, así que es reversible—; y el margen queda escrito
para que, si algún día vuelve a caer (una comprobación que entre en duda, o un conjunto que **salga**
de la cuarentena y devuelva sus preguntas al cómputo), nadie piense que se coló.

### 8. La medición por causa, que zanja la duda de los borradores

`margen_por_causa.py` (0 $, en `F:\temp-opofuente\f24-scratch\`) separa las dos causas por las que una
pregunta puede no estar cubierta: **sin comprobar** (lo arregla una corrida) y **comprobada y no
cubierta** (eso es **material**, y no lo arregla ninguna corrida más). `margen_de_cierre.py` solo no
las separaba, y es justo lo que decide entre cerrar un tema y dejarlo en borrador.

| tema | hoy (clave utilizable) | **sin comprobar** | **comprobada y NO cubierta = MATERIAL** | ¿cruza el 90 % con una corrida? |
|---|---|---|---|---|
| **I.4** | 505/561 = 90,0 % (la puerta mide 489/542 = 90,2 %) | **0** | 56 | **CRUZA — ya está por encima** |
| **I.8** | 410/505 = 81,2 % | **0** | **95** | **no** |
| **I.6** | 177/248 = 71,4 % | **0** | **71** | no |
| **I.7** | 300/525 = 57,1 % | **0** | **225** | no |

**Los tres borradores lo están porque les falta material, no porque su corrida se cortara**: **0 grupos
sin comprobar** en los tres. Eso zanja la duda que se arrastraba desde el §3 del encargo.
**El contraste que lo demuestra, medido**: en **II.1** los 7 grupos sin comprobar **sí** tenían clave
utilizable, y completarlos subió el tema de **96,6 % a 98,5 %** por **0,0577 $**. Un tema cortado se
termina; un tema con hueco de material se queda en borrador con su cifra.

**Con el cierre de I.4 quedan publicados 21 de los 33 temas.** Están escritos 24: los 21 publicados más
los tres borradores (I.7, I.8 e I.6). Los que faltan por escribir son los que la tabla pone por debajo
de 180 claves utilizables —**II.2 (173), III.8 (169), II.5 (155)** y los siguientes— más los tres
borradores y III.4.

## F25 · La tanda de contenido sigue por los de menos valor, y una corrida que se murió con el turno (14-oct-2026)

**Rama `f21-temas-valor`**, base real **`0037_origin_scope`**, copia verificada del día
(`20261014-101138-3c75b9.zip`). Mismo ritmo del §4: contenido directo sobre la base real, sin rama de
contenido y sin batería de 18 puertas.

### 1. I.4 se cierra a coste 0 $, y pasa por 0,2 puntos

Detalle completo en el §7 de F24 y en `docs/apuntes/INFORME-I.4.md`. En una línea: **489/542 = 90,2 %**
de cobertura por clave utilizable y forma PASA, con `--publicar` (0 llamadas, 0,0000 $). **Publica
porque cumple la regla tal como está escrita, el margen va dicho y es reversible.** Con esto quedan
**21 de 33**.

### 2. La tabla de valor, vuelta a medir hoy, y el orden de lo que queda

Medida hoy (la cuarentena ya va por **17** conjuntos, así que los números siguen bajando):

| Tema | Claves utilizables |
|---|---|
| **II.2** | **172** |
| **III.8** | **167** |
| **II.5** | **155** |
| IV.4 | 150 |
| III.6 · IV.3 | 145 |
| III.2 | 140 |
| I.9 | 133 |

**III.4 (407)** sigue **fuera** con su medición: su banco es de otra materia en un 40 %.

### 3. Los tres catálogos, escritos y ensayados antes de pagar (0 $)

| Tema | Apartados | Índice | **Techo medido** | Previsión | Estado |
|---|---|---|---|---|---|
| **II.2** | **17** | PASA | **169/172 = 98,3 %** | 44–79 llam. · 0,30–0,54 $ | **publicado** |
| **III.8** | **10** | PASA | **163/167 = 97,6 %** | 33–58 llam. · 0,22–0,39 $ | catálogo listo |
| **II.5** | **11** | PASA | **148/155 = 95,5 %** | 33–58 llam. · 0,22–0,39 $ | catálogo listo |

**Las dos lecciones de f24, aplicadas desde el principio y comprobadas con una cuenta antes de
correr**: los títulos de los tres catálogos **no comparten las tres primeras palabras entre tres
apartados** (lo que dejó II.3 sin publicar) y **ningún patrón propio es una palabra genérica**
(«velocidad», «estándar», «acceso», «datos», «base» salen en casi todos los enunciados de estos
bancos). Lo que es de otro tema va a la bandeja con su motivo: en II.2 la **NTI de Digitalización**
(I.8.4); en III.8 el **Portal de la Transparencia** (I.4) y los once principios de la **Ley 11/2007**
(I.8.1); en II.5 el **hipervisor** (IV.2), **SCRUM**, **Docker**, **Spring Boot** y **C#**.

### 4. II.2, redactado y **publicado** el 14-oct

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **163/165 = 98,8 % PASA** — **la mejor de toda la serie** |
| Cobertura (todas las claves) | 163/172 = 94,8 % |
| Hechos | **325 guardados** → **268 en el plan** (57 agrupados) |
| Apartados | **17** · ninguno pasó el tope de 150 hechos |
| Forma | **PASA** · 8.045 palabras de 13.000 · repetidos **0,0 %** |
| Índice | PASA · **0 grupos y 0 hechos sin materia** |
| Bandeja del propietario | **9**: 7 `norma_cambiada`, 2 `clave_sospechosa` |
| Llamadas y coste | **40 (0 fallidas) · 0,0772 $** · 12 minutos, sin tope activado |
| Previsión | 44–79 llamadas · 0,30–**0,54 $** → coste muy por debajo del mínimo |
| Precio por llamada | **0,00193 $**, el más bajo del proyecto (comprobar es diez veces más barato que redactar) |

### 5. Una corrida murió con el turno del agente, y se dice con su cifra

**El lanzamiento de II.2 (13:01) se hizo como trabajo de fondo de la sesión, y los trabajos de fondo
no sobreviven al final del turno.** Al morir el padre murió el hijo:

| Qué | Cifra |
|---|---|
| Lo que dejó escrito | **325 hechos, los 17 apartados y 53 de 175 comprobaciones** (nada perdido) |
| Su coste | **no medido**: `corrida-II.2-1.out.txt` quedó a **0 bytes** (el volcado murió con el proceso) |
| Estimación de su coste | **≈0,10–0,15 $** (9 llamadas de hechos + 17 de redacción + ~6 de comprobación) |
| El candado | quedó **echado**; hubo que soltarlo por el camino que documenta el motor |
| La reanudación | 13:40, con `-u` y **fichero de salida nuevo**: **175/175 comprobadas por 0,0772 $** |

**`python -u` no salva la salida en ese caso**: lo que la redirige es el proceso padre y su búfer muere
con él. **Lo que sí sobrevive es lo escrito en la base**, así que reanudar es barato.

**Y una sospecha que la medición desmintió**: durante esa hora, el `python` que consumía CPU **no era
esta corrida**, sino el `pytest` de integración de **otro árbol** (`opofuente-apuntes`), que arrancó a
las 14:41:14 por casualidad. La reanudación comprobó **10 grupos por minuto** (53 → 175 en doce
minutos): la lentitud aparente no era de la API, era que la corrida ya estaba muerta.

**La regla que esto fija para las próximas tandas**: **lanzar y esperar dentro del turno** (que es lo
que se hizo en f24, y por eso allí no pasó), o aceptar que habrá que reanudar —lo que cuesta 40
llamadas y 0,0772 $ para 122 grupos, que es de lo más barato que se puede pagar—.

### 6. Lo que queda fuera, con el porqué

- **I.8 (81,2 %), I.6 (71,4 %) e I.7 (57,1 %)**: los tres borradores siguen **con su cifra** y con la
  causa medida —**0 grupos sin comprobar** en los tres, así que su hueco es **material** y ninguna
  corrida lo mueve—;
- **III.4**: sigue **sin escribir**; su banco es de otra materia en un 40 %, ya medido;
- los grupos que ningún índice sitúa (3 en II.2, 8 en II.1, 5 en III.3, 10 en II.3, 19 en I.3, 5 en
  IV.10): en la bandeja del propietario con su motivo;
- **la pregunta del CPD en I.3**: contada como cubierta y declarada en el §5 de F24, con las dos
  cifras.

**Con I.4 y II.2 quedaban publicados 22 de los 33 temas** (y con III.8 y II.5 de los §7 y §8, **24**; el
recuento final, en el §10).

### 7. III.8, redactado y **publicado** el 14-oct

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **152/155 = 98,1 % PASA** |
| Cobertura (todas las claves) | 152/167 = 91,0 % |
| Techo medido antes de pagar | 163/167 = **97,6 %** |
| Hechos | **286 guardados** → **233 en el plan** (53 agrupados) · 16 con la clave señalada |
| Apartados | **10** · el banco más descolgado de la serie: **124 de 147 grupos sin epígrafe** (84 %) |
| Forma | **PASA** · 8.027 palabras de 11.560 · repetidos **0,0 %** |
| Índice | PASA · **0 grupos y 0 hechos sin materia** |
| Bandeja del propietario | **10**: 8 `norma_cambiada`, 1 `clave_sospechosa`, 1 `hueco_sin_material` |
| Llamadas y coste | **57 (0 fallidas) · 0,2090 $** · **17 minutos**, sin tope activado |
| Previsión | 33–58 llamadas · 0,22–0,39 $ → **57 llamadas (al tope de la cota) y coste por debajo del mínimo** |
| Precio por llamada | **0,00367 $** |

**Y el índice hizo su trabajo con el banco más difícil**: tres de sus cuatro epígrafes oficiales tienen
**0, 0 y 6 grupos**, así que el asunto lo puso entero el enunciado —144 de 147 grupos situados (98,0 %)
y un techo medido de 97,6 % que la corrida convirtió en **98,1 %**.

### 8. II.5, redactado y **publicado** el 14-oct

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **150/154 = 97,4 % PASA** |
| Cobertura (todas las claves) | 150/159 = 94,3 % |
| Techo medido antes de pagar | 148/155 = **95,5 %** |
| Hechos | **282 guardados** → **219 en el plan** (63 agrupados) · 11 con la clave señalada |
| Apartados | **11** · un solo epígrafe oficial con contenido y **88 de 143 grupos sin epígrafe** |
| Forma | **PASA** · 7.717 palabras de 11.280 · repetidos **0,0 %** |
| Índice | PASA · **4 grupos y 6 hechos sin materia**, con su motivo |
| Bandeja del propietario | **9**: 5 `norma_cambiada`, 4 `pregunta_ambigua` |
| Llamadas y coste | **51 (0 fallidas) · 0,1663 $** |
| Previsión | 33–58 llamadas · 0,22–0,39 $ → **coste por debajo del mínimo** |
| Precio por llamada | **0,00326 $** |

### 9. Lo que la tanda deja medido, y lo que se ha verificado en vez de suponer

- **Comprobar dentro del turno funciona y es rápido**: III.8 tardó **17 minutos** y II.5 **13**, frente
  a las horas perdidas en II.2 por lanzarlo como trabajo de fondo. La regla queda: **lanzar y esperar
  dentro del turno**.
- **La cota de dinero de `--prever` es un techo y se queda holgada** cuando el catálogo se ensaya antes
  de pagar: **tres de tres** corridas salieron por debajo del mínimo previsto (II.2 0,0772 $ de 0,30 ·
  III.8 0,2090 $ de 0,22 · II.5 0,1663 $ de 0,22), mientras que la cota de **llamadas** se quedó al
  tope en III.8 (57 de 58).
- **El defecto de I.3 no se ha repetido, y está comprobado, no supuesto**: el motor sienta un hecho sin
  materia en el apartado de la pregunta de la que salió (`repartir_hechos`), que es la puerta por la que
  el material ajeno entra en un tema. Se ha mirado **grupo por grupo con `donde_cayeron.py` (0 $)** y
  **los seis grupos ajenos de II.2, III.8 y II.5 aparecen «(sin ancla)»**: la NTI de Digitalización
  (I.8.4), el Portal de la Transparencia (I.4), la Ley 11/2007 (I.8.1), el hipervisor (IV.2), Docker
  (IV.1), SCRUM, Spring Boot (III.5) y C# (III.2) **se quedaron en la bandeja del propietario con su
  motivo** en vez de sentarse en un apartado.
- **El techo medido antes de pagar y la cobertura real coinciden en los tres**: 98,3 % → **98,8 %**
  (II.2), 97,6 % → **98,1 %** (III.8) y 95,5 % → **97,4 %** (II.5). Con el catálogo ensayado, el techo
  es un suelo.

### 10. La tanda f25, en una tabla

| Tema | Techo (0 $) | **Cobertura publicada** | Todas las claves | Forma | Bandeja | Llamadas · coste | Previsión |
|---|---|---|---|---|---|---|---|
| **II.2** | 98,3 % | **163/165 = 98,8 %** | 94,8 % | PASA 0,0 % | 9 | 40 · **0,0772 $** | 0,30–0,54 $ |
| **III.8** | 97,6 % | **152/155 = 98,1 %** | 91,0 % | PASA 0,0 % | 10 | 57 · **0,2090 $** | 0,22–0,39 $ |
| **II.5** | 95,5 % | **150/154 = 97,4 %** | 94,3 % | PASA 0,0 % | 9 | 51 · **0,1663 $** | 0,22–0,39 $ |

**Los tres publicados, los tres con las dos puertas en PASA, y el coste medido de la tanda: 0,4525 $**
(más **≈0,10–0,15 $ estimados** de la corrida de II.2 que murió con el turno y cuyo informe se perdió).

**Con I.4 y estos tres quedan publicados 24 de los 33 temas.** Están escritos 27: los 24 publicados
más los tres borradores (I.8, I.6 e I.7). Los que faltan por escribir son **IV.4 (150), III.6 y IV.3
(145), III.2 (140) e I.9 (133)**, más **III.4**, que sigue fuera con su medición.

### 11. La causa raíz del material ajeno, y el bloque de motor que queda pendiente

**La puerta por la que entró el material del CPD en I.3 tiene nombre**: `repartir_hechos`, la red de
seguridad del motor por la que **un hecho que no reconoce ninguna materia va al apartado de la pregunta
de la que salió**. Esa red **existe para no perder hechos** —y hace bien su trabajo— pero **no comprueba
que el destino sea del tema**: sitúa el hecho por **de dónde vino la pregunta**, no por lo que dice. Es
una causa raíz, no una anécdota, y sus dos caras están escritas en `DECISIONES` (**F25b**) con el caso
del CPD medido: 1 de 15 apartados, 2 de 300 hechos, 730 caracteres y 5 de 181 preguntas.

**Hoy la única defensa es mirarlo a mano**, y por eso `donde_cayeron.py` (0 $) forma parte del método:
el ensayo dice **cuántos** grupos quedan fuera del índice, pero no **dónde acaban**. Se pasó sobre II.2,
III.8 y II.5 y los seis grupos ajenos salieron **«(sin ancla)»**.

**Y queda pendiente, apuntado y no hecho** (**F25c** en `DECISIONES`): **un solo bloque de motor para un
solo agujero** —nadie comprueba que el sitio donde acaba un hecho o una comprobación sea suyo—, que
junta tres hallazgos: que **no hay puerta que mire si el apartado al que se ancla una respuesta es del
tema** (lo dijo la tanda de I.3), que **la cobertura cuenta dos veces una pregunta que el índice no
sitúa** (lo encontró el panel) y que **`repartir_hechos` es la causa de lo primero**. Cuando toque, será
un bloque de motor con su prueba que falla antes y **con el caso del CPD como prueba de regresión**. No
se toca ahora: el encargo es escribir temas y un cambio de motor arrastra las 18 puertas.

### 12. IV.4, redactado y **publicado** el 14-oct, y el hallazgo que vale para todos los catálogos

| Qué | Valor |
|---|---|
| Cobertura (**clave utilizable**) | **141/145 = 97,2 % PASA** |
| Cobertura (todas las claves) | 141/151 = 93,4 % |
| Techo medido antes de pagar | 143/147 = **97,3 %** |
| Hechos | **308 guardados** → **261 en el plan** (47 agrupados) · 17 con la clave señalada |
| Apartados | **15** |
| Forma | **PASA** · 8.879 palabras de 12.320 · repetidos **0,0 %** |
| Índice | PASA · 4 grupos y 9 hechos sin materia, los cuatro de otro tema y con su motivo |
| Bandeja del propietario | **10**: 6 `norma_cambiada`, 4 `pregunta_ambigua` |
| Llamadas y coste | **70 (0 fallidas) · 0,1522 $** |
| Previsión | 38–68 llamadas · 0,26–0,46 $ → **70 llamadas (por encima del máximo) y coste por debajo del mínimo** |

**El hallazgo del día, que no es de este tema sino de todos los catálogos: el normalizador convierte la
barra en espacio, como ya hacía con el guion, el punto y la coma, así que un patrón escrito
`/etc/passwd` no puede casar nunca** —el texto que ve el motor es « etc passwd »—. Los patrones de
ficheros hay que escribirlos **con el espacio del separador**: `etc ?passwd`, `etc ?shadow`,
`etc ?gshadow`, `login ?defs`. **Es un patrón muerto que no da ningún error**: el catálogo carga, el
índice dice PASA y el grupo se cae a la bandeja sin que nadie se entere.

**Y el ensayo previo se volvió a pagar solo**: el primer ensayo dejó **22 grupos sin materia y el techo
en 85,7 %** —por debajo del listón, o sea borrador seguro—; con los arreglos (el de la barra y tres
patrones demasiado literales, como «estadísticas y conexiones» donde el enunciado dice «conexiones y
estadísticas») el techo subió a **97,3 %**: **dieciséis puntos de cobertura por no haber pagado la
corrida antes de ensayar.**

**Una decisión de apartado, dicha**: las preguntas de **usuarios conectados, sesión remota, procesos en
un equipo remoto y fecha del último reinicio** son administración del sistema y no de la red, así que
tienen **apartado propio** en vez de forzarlas dentro de «la red en Linux» o «la red en Windows». Y lo
que es de otro tema va a la bandeja, comprobado **sin ancla**: el ataque de denegación distribuida
(IV.9), las funciones de la capa de transporte (IV.7), SAN y NAS (IV.2) y la Ley 7/1985 (derecho
administrativo).

**Con IV.4 quedan publicados 25 de los 33 temas.**

### 13. La tanda f25, en una tabla

| Tema | Techo (0 $) | **Cobertura publicada** | Todas las claves | Forma | Llamadas · coste | Previsión |
|---|---|---|---|---|---|---|
| **II.2** | 98,3 % | **163/165 = 98,8 %** | 94,8 % | PASA 0,0 % | 40 · **0,0772 $** | 0,30–0,54 $ |
| **III.8** | 97,6 % | **152/155 = 98,1 %** | 91,0 % | PASA 0,0 % | 57 · **0,2090 $** | 0,22–0,39 $ |
| **II.5** | 95,5 % | **150/154 = 97,4 %** | 94,3 % | PASA 0,0 % | 51 · **0,1663 $** | 0,22–0,39 $ |
| **IV.4** | 97,3 % | **141/145 = 97,2 %** | 93,4 % | PASA 0,0 % | 70 · **0,1522 $** | 0,26–0,46 $ |

**Los cuatro publicados**, los cuatro con las dos puertas en PASA y **0,0 % de párrafos repetidos**.
**Coste medido de la tanda: 0,6047 $** (más **≈0,10–0,15 $ estimados** de la corrida de II.2 que murió
con el turno). **Cuatro de cuatro corridas salieron por debajo del mínimo previsto en dinero**, y en
IV.4 la cota de **llamadas** se superó (70 frente a 68): **la de dinero es un techo, la de llamadas no.**

**Quedan publicados 25 de los 33.** Están escritos 28: los 25 publicados más los tres borradores
(I.8, I.6 e I.7). Los que faltan por escribir son **III.6 y IV.3 (145), III.2 (140) e I.9 (133)**, más
**III.4**, que sigue fuera con su medición.

## F24-panel · La revisión de los apuntes en el panel (14-oct-2026)

> **Las puertas, en una línea, para que no haya que reconstruirlo dentro de un mes**: las **18 en verde,
> repartidas en tres corridas** (la 1-8 en el intento 10, la 9-12 en el 11 y la 13-18 en el 13), con
> **dos percances de entorno** —una prueba de componentes que falla por carga y pasa sola, y dos caídas
> con un código nativo de Windows (`0xC0000409`) que a mano salen en 0— y **un fallo real mío por el
> camino**, que encontró la puerta 7 (la cadena de migraciones hacia atrás no tenía mi escalón). El
> detalle, en el §7; cada intento con su mensaje literal, en
> `F:\temp-opofuente\gates-f24-apuntes.txt`.
>
> Esta sección se llama **`F24-panel`** y no `F24` porque el bloque de contenido usó ese número a la vez
> para su propia sección (`F24`, `F24b`, `F24c`, `F25`, `F25b`, `F25c`, `F25e` están tomados). Así ninguna
> cita futura puede apuntar a la sección equivocada.

**Rama `f24-revision-apuntes`** (worktree `F:\temp-opofuente\opofuente-apuntes`, desde
`main = 511a8a9`, con `main` ya **fusionado en la rama** hasta `7cf1544`). La fusión a `main` la hace el
agente padre.

**La fusión con `main`, medida** (commits `5636a3b` con `a2a6511` y el que trae `7cf1544`): los documentos
que chocaron se resolvieron **sumando**, y no a ojo —**cero** marcadores de conflicto y **unión exacta**:
`líneas(fusión) == líneas(main) ∪ líneas(mías)` en los tres—. En la última, `main` añadía **59** líneas
(la sección de IV.4) y las mías eran **193**; los encabezados del ESTADO pasan de **20** (main) a **21**,
las entradas del propietario de **17** a **18**, y la tabla de decisiones cuadra por
**176 = 162 (main) + 173 (mías) − 159 (en las dos)**. Después de fusionar, y ya con el código de las tres
tandas de contenido dentro: `ruff format --check` (509 ficheros), `ruff check`, `mypy` (235 ficheros),
`eslint`, `tsc` y el contrato sincronizado, con **912 pruebas de backend** y **379 de componentes** en
verde.
**Coste de API: 0 $** — no se ha llamado a ningún modelo. La cifra de un borrador se **lee** de las
comprobaciones que el motor ya dejó guardadas, con el mismo camino que `apuntes --medir`
(`TopicNotesService.medir`), así que el panel y el comando no pueden dar dos números del mismo tema.

### 1. Qué se ha construido, y dónde

| qué | dónde |
|---|---|
| La decisión, en su tabla, con el rechazo **obligado a llevar motivo** (`CHECK`) | migración `0038_revision_de_apuntes` (`apps/api/alembic/versions/0038_revision_de_apuntes.py`) |
| El vocabulario del motivo: `ReviewDecision`, `MotivoDelBorrador` (12 códigos), `Razon` con su cifra, `CifrasDelTema`, `razones_del_tema` | `domain/notes_review.py` |
| Leer las comprobaciones guardadas del tema y la decisión escrita | `infrastructure/notes_review_repository.py` |
| Medir los borradores, componer la ficha y decidir | `application/notes_review_service.py` |
| Tres rutas y una cuarta barata para el contador del menú | `api/routes/notes_review.py` (`GET /notes-review`, `GET /notes-review/summary` **antes** de la de parámetro —ADR-018—, `GET /notes-review/{codigo}`, `POST /notes-review/{codigo}/decision`) |
| El rechazo sin motivo, como error de campo | `domain/errors.py` → `InvalidReviewError`; `api/errors.py` lo sirve 422 con `field_errors` |
| La decisión, en la misma transacción y auditada | `notes.topic_reviewed` con `before_json`/`after_json` (y sin copiar la nota al evento) |
| La tabla del panel: estado, cifras, motivo con su cifra y decisión | `apps/web/src/pages/NotesReviewPage.tsx` (`/admin/apuntes`) |
| La ficha: motivo, los apartados **como los lee el alumno**, «los peores primero» y la decisión | `apps/web/src/pages/NotesReviewTopicPage.tsx` (`/admin/apuntes/:codigo`) |
| La entrada del menú y su contador | `app/navigation.ts`; `app/sectionCounts.ts` con `GET /notes-review/summary` |
| El lector del texto | `features/student/NotesBody` — **el mismo** componente que la zona del alumno |

**Publicar es archivar por el camino de siempre** (`DossierService.archive`): la aprobación no escribe
una versión a mano, y por eso lo que ve el alumno cambia igual que si se hubiera publicado desde el
comando.

### 2. Cómo está cada borrador, medido hoy, y qué enseña el panel

Medido el 14-oct-2026 sobre la copia de la base real (`f24-datos`, `integrity_check: ok`), con los 33
temas del TAI: **15 publicados**, **4 en borrador** (I.4, I.6, I.7 e I.8), **19 con apuntes** y 14 sin
apuntes escritos. (La copia es una **fotografía** de esa mañana: la base del propietario siguió
creciendo mientras se trabajaba en esta tanda —a las 13:00 tenía 340 apartados y 10.904 comprobaciones
frente a los 274 y 9.923 de la copia—, así que estas cifras son las de la copia con la que se midió y se
retrató, no las de su base de ahora mismo.) Lo que la pantalla dice de cada borrador, con la misma frase
y la misma cifra que devuelve la API:

| tema | cobertura (puerta) | qué le pasa (titular del motivo) | apartados · hechos | sin frase | en revisión o contra el material | incidencias |
|---|---|---|---|---|---|---|
| **I.4** | 489 de 542 = **90,2 %** | **Cumple las dos puertas** y no está publicado: nadie archivó su versión. **Aprobarlo lo publica** | 15 · 1.056 | 3 | 30 + 16 | 55 |
| **I.6** | 164 de 230 = **71,3 %** | Le faltan **43** preguntas cubiertas | 13 · 346 | 20 | 19 + 13 | 63 |
| **I.7** | 289 de 493 = **58,6 %** | Le faltan **155** preguntas cubiertas | 19 · 738 | 11 | 4 + 24 | 42 |
| **I.8** | 394 de 477 = **82,6 %** | Le faltan **36** preguntas cubiertas | 18 · 815 | 9 | 7 + 24 | 0 |

(«Sin frase» son las preguntas que los apuntes no contestan; «en revisión o contra el material» son las
que tienen la respuesta correcta marcada —`dudosas_clave`— o en conflicto con lo que dicen los apuntes
—`conflictos`—. Las cifras son las del **titular medido** el 14-oct-2026 con el código del motor tal
cual; la de «todas las claves» —sin excluir las dudosas— va en la ficha: I.4 87,9 %, I.6 68,3 %,
I.7 54,9 % e I.8 78,5 %.) Los cuatro tienen la **forma** en verde: lo que los frena es la cobertura, no
el texto.

Un tema **publicado** no se mide en la tabla: enseña su estado y sus cifras, y dice «sin medir en esta
tabla» en vez de un cero que mentiría; su ficha sí lo mide al abrirla (y ahí se ve su cobertura de hoy).

### 3. Qué puertas mira, y qué pasa al decidir

| decisión | qué escribe | qué pasa después |
|---|---|---|
| **Aprobar** | su fila en `topic_notes_reviews`, su evento y —si las dos puertas del §2.3 pasan— la versión archivada | el tema queda **publicado** y el alumno lo lee como publicado; si no pasan, queda **aprobado y sin publicar** y la respuesta dice **qué puerta** lo frena (`blocked_by`: `cobertura` o `forma`) |
| **Rechazar** | su fila (con la nota, obligatoria) y su evento | el motivo queda guardado y el tema sigue en borrador |

El listón **no se toca**: aprobar un tema del 82 % no lo publica, y la pantalla lo dice con la cifra
delante. La aprobación **no** cambia ninguna clave, ni la cuarentena, ni `key_reliability`, ni la marca
`in_review` del alumno: lo único que mueve es qué versión está archivada.

**La decisión sobrevive a una corrida del motor**, y está probado por partida doble: en integración (se
reescriben `question_note_anchors` y `notes_incidents` con el repositorio de verdad y la decisión sigue
donde estaba) y en extremo a extremo (una corrida escrita con `node:sqlite` sobre la base de la suite,
y al recargar el panel sigue el «Rechazado» con su nota, con el motivo de datos ya refrescado).

### 4. Coste y tiempos medidos (14-oct-2026, base real)

| qué | cuánto |
|---|---|
| `GET /notes-review` en frío | ~15 s |
| `GET /notes-review` con la caché de SQLite caliente | **7,0 a 8,1 s** (tres vueltas) para los 4 borradores |
| `GET /notes-review/{codigo}` (ficha de un tema) | 1,2 s |
| Medir los **19** temas con apuntes (lo que **no** hace la tabla) | **31,8 s** |
| `GET /notes-review/summary` (el contador del menú) | una lectura, sin medir nada |
| Medir los 4 borradores **con cuatro hilos** | 7,6 a 8,1 s — **no mejora** el serie (7,0 a 7,8 s): `medir` no suelta el GIL. Descartado |

### 5. Las pruebas, con sus rojos previos

| prueba | qué defiende |
|---|---|
| `apps/api/tests/unit/test_notes_review_domain.py` (**17**) | los 12 motivos y su orden (el titular primero, y `sin_decision` solo cuando no está publicado); las cifras con su cifra y **sin** cifra cuando el tema no se mide; el rechazo sin motivo que **no** valida; el «le faltan» con aritmética entera (el 90 % de 542 son 488, no 487,8); y el tema sin preguntas comprobables, que lo dice en vez de enseñar un «0 de 0» |
| `apps/api/tests/integration/test_notes_review_api.py` (**14**) | la tabla con el estado y el motivo medido; el contador del menú que cuadra (`published + draft == with_notes`); la ficha con sus apartados, su texto y su forma; aprobar un tema que **no** llega y verlo sin publicar con la puerta que lo frena; aprobar el que llega y verlo **publicado** (con su versión archivada y su evento); rechazar sin motivo (422 con `body.note`) y con motivo (guardado, auditado y leído); y la corrida del motor que **no toca** la decisión |
| `apps/api/tests/integration/test_migrations_0038.py` (**4**) | la tabla, el `CHECK` de dos decisiones, el rechazo sin motivo que la base **no** admite, y una decisión por tema, con su vuelta atrás y su vuelta a subir |
| `apps/api/tests/integration/test_migrations_downgrade.py` (actualizada) | la cadena de migraciones hacia atrás **incluye ya el escalón de `0038`**: al bajar de él, `topic_notes_reviews` desaparece. No es un adorno: sin ese escalón la prueba falla (decía «se esperaba estar en 0037» y la cabeza es `0038`), y con él se ejecuta de verdad el `downgrade` de la migración nueva |
| `apps/web/tests/unit/apuntesRevision.test.tsx` (**9**) | la tabla con el estado y el motivo **con su cifra** (y el publicado que dice que no se ha medido); el enlace a la ficha; el contador; los temas sin apuntes aparte; la ficha que lee el apartado con su tabla y sus cifras; «los peores primero» que reordena **sin cambiar el número de lectura**; aprobar por la ruta auditada con su cuerpo exacto; y rechazar, que sin motivo **no se puede enviar** |
| `apps/web/tests/e2e/apuntes-revision.spec.ts` (**4**) | lo mismo, en el navegador y con datos: la tabla con el motivo y su cifra; la ficha que enseña **el mismo texto** que la zona del alumno (comparado carácter a carácter); aprobar → publicado (y el alumno lo ve publicado); rechazar sin motivo → **422**, con motivo → guardado, y **la corrida del motor** después; y accesibilidad y móvil (**0 violaciones de axe** y **390 px exactos**) |

**Los rojos previos** (guardados en `F:\temp-opofuente\f24b-panel-scratch\rojo-antes.txt` y
`rojo-antes-front.txt`): en un árbol del commit base (`511a8a9`, sin mi código y **solo** con los
ficheros de prueba nuevos) las tres pruebas de backend **no se pueden ni recoger**
(`ImportError: cannot import name 'InvalidReviewError'`, `ModuleNotFoundError: No module named
'opofuente.infrastructure.notes_review_repository'`) y, corriendo sola la de la migración —que sí se
recoge—, **fallan las cuatro** con `sqlite3.OperationalError: no such table: topic_notes_reviews`; la
de componente cae al resolver el import (`Failed to resolve import
"../../src/pages/NotesReviewPage"`). El árbol de prueba se retiró después (`git worktree remove`).

### 6. Lo que queda fuera, y por qué

1. **El editor de apartados y «Regenerar este apartado»** (§4.3 del objetivo). Regenerar cuesta una
   corrida del modelo y pertenece a la tanda de contenido, que decide con las puertas de datos del
   tema; y un editor de texto para 33 temas es otra pantalla, no esta. Lo que **sí** está es lo que
   evita releer sesenta páginas: el orden «los peores primero» y las cifras de cada apartado.
2. **«Marcar revisado» por apartado**: se decidió por tema. El motor **sí** reescribe
   `needs_review_reason` de un apartado, y una marca de revisión al lado de eso se leería como
   contradictoria; y la decisión que publica o deja en borrador es sobre el tema.
3. **Los dos hallazgos del motor, medidos y no tocados** (esta tanda tiene prohibido cambiar el motor):
   **(a)** un grupo **sin** comprobación guardada no cuenta en la puerta —ni arriba ni abajo—, así que
   un tema con apartados y sin comprobaciones mide «0 de 0» y no pasa; **(b)** una pregunta que el
   índice no sabe situar se cuenta **dos veces** —como `sin_materia_en_el_indice` y además como su
   comprobación—, y el denominador sube con la misma pregunta que ya contaba en los dos lados (se
   descubrió al escribir la prueba: una sola pregunta daba «1 de 2»).
4. **El segundo motivo de I.8** («la corrida se paró al agotar su tope de tiempo») **no está en la
   base**: se dijo en su día en un informe, y el panel solo enseña motivos de datos con su cifra. No se
   inventa ni se copia de un documento.
5. **La tabla no mide los temas publicados** (sí su ficha): medirlos costaría 31,8 s para repetir lo
   que ya dice su estado.

### 7. Las 18 puertas

Corridas el 14-oct-2026 sobre el árbol `f24-revision-apuntes` con `scripts/gates.ps1` (y, para los
dos tramos finales, con su mismo `common.ps1` y su `Invoke-OpoFuenteStep`, porque volver a correr la
puerta 7 cuesta 42 minutos y ya estaba verde en esa corrida).

**Resultado: las 18 en verde, repartidas en tres corridas** (la 1-8 en el intento 10, la 9-12 en el
11 y la 13-18 en el 13), con dos percances de entorno y un fallo real mío por el camino —todo ello
contado más abajo—. No es un «18/18 de una sola pasada» y no se va a decir que lo sea.

| puerta | qué comprueba | resultado |
|---|---|---|
| **1. ruff format --check** | El formato de Python (E501 a 100 caracteres) | OK (intento 10) |
| **2. ruff check** | El lint de Python | OK (intento 10) |
| **3. mypy (estricto)** | Los tipos en estricto, 227 ficheros | OK (intento 10) |
| **4. eslint** | El lint del front | OK (intento 10) |
| **5. typecheck TypeScript** | Los tipos del front | OK (intento 10) |
| **6. pruebas unitarias backend** | Las unitarias de Python (**853** pruebas) | OK (intento 10) |
| **7. pruebas de integración backend** | Integración, con base y migraciones de verdad (42 minutos) | OK (intento 10) |
| **8. pruebas de contrato** | El contrato OpenAPI | OK (intento 10) |
| **9. pruebas de componentes (Vitest)** | Los componentes del front (**379** pruebas) | OK (intento 11) |
| **10. contrato OpenAPI y tipos sincronizados** | `openapi.json` y los tipos derivados al día | OK (intento 11) |
| **11. build backend** | El paquete de Python | OK (intento 11) |
| **12. build frontend** | El paquete del front | OK (intento 11) |
| **13. migración desde base vacía** | La cadena entera sobre un directorio nuevo (revisión `0038`) | OK (intento 13) |
| **14. esquema migrado verificado con sqlite3** | La revisión y los metadatos, leídos sin la aplicación | OK (intento 13) |
| **15. siembra de perfiles desde base vacía** | Los perfiles oficiales, desde cero | OK (intento 13) |
| **16. siembra idempotente (segunda ejecución sin cambios)** | Volver a sembrar no cambia nada | OK (intento 13) |
| **17. fixtures de perfil sincronizados con las fuentes oficiales** | Los fixtures frente a las fuentes | OK (intento 13) |
| **18. E2E (Playwright)** | La suite entera en el navegador (**78** pruebas, mis 4 incluidas) | OK (intento 13) |

Las cifras de las pruebas de esa corrida:

- unitarias de backend: **853 pruebas**;
- integración: **853 pruebas (y 2 fallos en el primer intento, arreglados)**;
- componentes: **379 pruebas**;
- extremo a extremo: **41 pruebas, 42**.

**Las 18 están en verde, y hay que decirlo como es: repartidas en tres corridas.** La 1 a la 8 en el
intento 10, la 9 a la 12 en el intento 11 y la 13 a la 18 en el intento 13. No es un 18/18 de una
sola pasada, y el registro lo cuenta con sus causas:

1. **Un fallo de verdad, mío, que encontró la puerta 7**: la lista escrita a mano de la cadena de
   migraciones hacia atrás (`test_migrations_downgrade.py`) empezaba en `0037` y al subir la cabeza a
   mi `0038` fallaba. Arreglado **añadiendo mi escalón** (y con él se ejecuta de verdad el `downgrade`
   de la migración nueva). No se tocó ninguna comprobación para que callara.
2. **Dos percances de entorno**, los dos medidos:
   - la puerta **9 cayó con 1 de 379 pruebas**: `questions.test.tsx`, un fichero que **pasa solo**
     (32 de 32 en 20,3 s frente a 65 s con la máquina cargada; el entorno `jsdom` se creó 42 veces en
     esa corrida). Es carga, no lógica;
   - y la puerta **13 cayó dos veces con un código NATIVO de Windows: `-1073740022` = `0xC0000409`**
     (fallo rápido del proceso, sin una línea de la migración en el registro). Repetida a mano —
     incluso con la misma redirección de salida que usa el lanzador— la misma migración desde base
     vacía termina en **0** y deja la revisión `0038_revision_de_apuntes`; en el intento 13 pasa sola.
3. **La E2E falló una vez por una prueba mía mal contada** (los eventos de auditoría del tema en
   absoluto en vez de la diferencia: el registro es de solo añadir), y quedó arreglada antes de la
   corrida final: **78 de 78** en la puerta 18.

#### Los dos códigos nativos del mismo día: la máquina, no el código

El mismo 14-oct-2026, con dos árboles distintos y en dos bloques distintos, murieron dos procesos con
códigos nativos de memoria: el de esta tanda con **`0xC0000409`** (fallo rápido del proceso) en la
migración desde base vacía, y el del bloque de **contenido** con **`0xC0000374` (corrupción de
montón)** al morir su corrida. Dos árboles, dos códigos distintos, el mismo día: **no es el código de
ninguno de los dos, es la máquina con presión de memoria** (los dos bloques corriendo máquinas de
estados y suites enteras a la vez). Queda escrito para el que venga: **si una puerta vuelve a caer con
un código nativo, lo primero que se mira es la memoria y los procesos, no el `diff`**.

#### Una decisión para la próxima vez

**Reintentar una puerta que cae con un código nativo, una vez y contada, es legítimo.** No es
«reintentar hasta que salga verde»: es distinguir un fallo **del proceso** (memoria, un fichero a
medias, un antivirus) de un fallo **del código**, que se arregla y no se reintenta. Un reintento de
una prueba que falla por lógica **no se hace nunca**, y aquí no se ha hecho: la puerta 7 se arregló
(era un fallo real), la 9 se midió (pasa sola) y la 13 se reintentó **dos veces** porque su código de
salida era nativo y su comando, a mano, salía en 0.

### 8. Las capturas

Las cuatro capturas están en `artifacts/screens/` (ignorado por git, como en las tandas anteriores) y se
hicieron **contra una copia de la base real** (`F:\temp-opofuente\f24-datos`, `integrity_check: ok`),
nunca contra la del propietario:

| captura | fichero | carga | axe | consola |
|---|---|---|---|---|
| La tabla de los 33 temas, escritorio | `artifacts/screens/admin-apuntes-escritorio.png` | 10.756 ms | **0** | 0 |
| La tabla, móvil (390 px exactos) | `artifacts/screens/admin-apuntes-movil.png` | 10.187 ms | **0** | 0 |
| La ficha del borrador **I.7**, escritorio | `artifacts/screens/admin-apuntes-I-7-escritorio.png` | 3.700 ms | **0** | 0 |
| La ficha de I.7, móvil | `artifacts/screens/admin-apuntes-I-7-movil.png` | 3.386 ms | **0** | 0 |

La prueba de capturas **no se limita a retratar**: comprueba que en la tabla se ven las dos cosas que
pide el entregable —un tema **publicado** y un **borrador con su motivo y su cifra**—, que la ficha
enseña el motivo y el texto apartado a apartado, que no hay **ninguna violación de axe** y que el ancho
de la captura de móvil es **390 px exactos**. Los cuatro PNG salen con la misma aplicación y los mismos
dos anchos que el resto de la suite.

#### Los 6 fallos de capturas del informe son preexistentes (demostrado)

El informe de esa corrida apuntó 6 capturas en rojo, **ninguna mía**. Para no quedarse en «no la he
tocado», se corrieron esas 6 en un árbol con **`main` limpio** (`511a8a9`) y una copia aparte de la base
real (`f24-datos-main`, revisión `0037`): allí **fallan 5 igual** —`revision` a 1280 px, `test-en-curso`
y `resultado` a los dos anchos— y la sexta, `revision` a 390 px, es **de borde** (la captura tarda ~102 s
y el límite son 120 s; repetida dos veces a solas en mi árbol, **pasa las dos**). La causa de
`test-en-curso` y `resultado` está medida: en las dos copias hay **0 conjuntos con
`key_reliability = 'in_review'`**, que es la marca que esa captura espera ver. Y el «Celador» que el
informe marca en las pantallas del panel **ya salía el 6-oct-2026** en el informe de F0 de
`opofuente-main` (en las dos filas de cada pantalla del panel): viene del **selector de oposición** de la
cáscara, que lista las tres oposiciones de la base real, no de la pantalla de apuntes —los dos payloads
de la revisión no contienen esa palabra, comprobado.

## F27 · El motor comprueba que el sitio donde acaba un hecho o una comprobación sea suyo (14-oct-2026)

**Rama `f27-medidor-anclas`** (worktree `F:\temp-opofuente\opofuente-medidor`), base **`main = 4290817`**.
Cierra **F25c** y **F25b**: los tres hallazgos eran el mismo agujero y se arreglan en **un solo bloque de
motor**, con el caso del CPD de I.3 como prueba de regresión. Las decisiones están en `DECISIONES`
(**F27**). Las 18 puertas y su registro, al final de esta sección.

### 1. Los tres arreglos, con su prueba que falla antes

| # | Arreglo | Qué hacía antes | Qué hace ahora | Prueba (en rojo con el motor de antes) |
|---|---|---|---|---|
| **1** | **`repartir_hechos` no sienta un hecho que no nombra ninguna materia del tema** (`F25b`) | Un hecho que no reconocía ninguna materia se caía al apartado de la **pregunta de la que salía** «para no perderlo»: es la puerta por la que el material de otro tema se sentó dentro de un tema | El hecho va a `sin_materia` con su texto (**no se pierde**), se cuenta (`hechos_de_su_pregunta`) y su pregunta va a la bandeja con su motivo, que ahora **lleva el texto de los hechos sin apartado**. El **cajón** de un epígrafe deja de votar y de recibir hechos: no reconoce nada, recoge | `test_un_hecho_sin_materia_no_se_sienta_en_el_apartado_de_su_pregunta` (**rojo**: `assert False` en «no se sienta en ningún apartado»), `test_un_hecho_sin_materia_no_se_sienta_en_el_cajon_de_su_epigrafe` (**rojo**: `AttributeError`, el método no existía) |
| **1-bis** | **El caso del CPD de I.3, como regresión** | El grupo del estándar **ANSI/TIA-942-B** no trae epígrafe y ningún patrón de I.3 lo sitúa, pero sus dos hechos llevaban el epígrafe **I.3.1 que les puso el modelo**, y su voto al cajón `i-3-1-otros` sentó al grupo y contó sus **5 respuestas como cubiertas** (medido en `F25b`: 1 apartado de 15, 2 hechos de 300, 730 caracteres y 5 preguntas de 181) | El grupo no cabe en ninguna materia del tema (va a la bandeja con su motivo) y sus hechos no se sientan en ningún apartado | `test_el_material_del_cpd_de_i_3_no_se_sienta_en_ningun_apartado_y_va_a_la_bandeja` (**rojo**: `assert [] == ['3bf0acd5…']`, el grupo **sí** estaba situado) |
| **2** | **La puerta que falta: cobertura por apartado propio** (lo dejó medido el bloque de I.3) | La puerta decía **cuántas** respuestas estaban contestadas y no **por quién**: una pregunta sin apartado propio se comprobaba contra el **primer apartado de su epígrafe** (el respaldo `por_defecto`) y esa comprobación contaba como cobertura | El ancla es `IndiceDelTema.apartados_propios_de`: los apartados de sus hechos y, si no tiene ninguno, el de la materia en la que el índice la sitúa. Un ancla en un apartado ajeno **no cuenta como cobertura** | `test_una_comprobacion_anclada_en_un_apartado_ajeno_no_cuenta_como_cobertura` (**rojo**: `preguntas_cubiertas_con_clave == 3`, contaba la pregunta sin apartado como cubierta) |
| **3** | **El doble conteo, una sola vez** (lo encontró el panel) | La misma pregunta entraba **dos** veces: como hueco (`grupos_sin_materia`) y con su comprobación guardada | Cada pregunta se cuenta **una sola vez**, y ese «una vez» es **no cubierta** (su comprobación está anclada a un apartado que no es el suyo). Los **dos** recuentos —el de la corrida y el del comando— se unifican en `_contar_cobertura` | `test_una_pregunta_que_el_indice_no_situa_cuenta_una_sola_vez` (**rojo**: `assert 4 == 3`, tres preguntas contadas como cuatro) |

**El rojo, tal cual salió** (5 fallos, con el motor de `HEAD` y solo las pruebas nuevas puestas):
`F:\temp-opofuente\f27-scratch\rojo-antes.txt` (10,19 s). **Después, verde**: 75 pruebas de las dos
suites tocadas (41 unitarias de `test_topic_index.py` y 34 de integración de `test_topic_notes.py`).

### 2. Antes y después, tema a tema, medido sobre la base real

Medido con el mismo camino que `apuntes --medir` (`servicio.medir`), **sin llamar a ningún modelo** y
**sin escribir una fila**: `F:\temp-opofuente\f27-scratch\medir_cobertura.py`. Las dos salidas están
guardadas (`cobertura-antes.txt` y `cobertura-despues.txt`). «Antes» es el motor de `4290817`; «después»
las tres reglas nuevas. Los 25 publicados y los tres borradores (I.4, que estaba en borrador cuando se
escribieron estas notas, **se publicó el 14-oct** y va con los publicados):

| tema | antes | después | diferencia | veredicto | estado |
|---|---|---|---|---|---|
| I.1 | 1958/1985 = 98,6 % | 1958/1985 = **98,6 %** | 0,0 | PASA | publicado |
| I.2 | 628/656 = 95,7 % | 626/656 = **95,4 %** | −0,3 | PASA | publicado |
| **I.3** | 168/181 = 92,8 % | 152/181 = **84,0 %** | **−8,8** | **NO PASA** | **publicado** |
| **I.4** | 489/542 = 90,2 % | 483/540 = **89,4 %** | **−0,8** | **NO PASA** | **publicado** |
| I.5 | 339/371 = 91,4 % | 335/367 = **91,3 %** | −0,1 | PASA | publicado |
| I.6 | 164/230 = 71,3 % | 164/230 = **71,3 %** | 0,0 | NO PASA | borrador |
| I.7 | 287/491 = 58,5 % | 287/488 = **58,8 %** | +0,3 | NO PASA | borrador |
| I.8 | 389/472 = 82,4 % | 389/469 = **82,9 %** | +0,5 | NO PASA | borrador |
| II.1 | 200/203 = 98,5 % | 200/203 = **98,5 %** | 0,0 | PASA | publicado |
| II.2 | 162/164 = 98,8 % | 162/164 = **98,8 %** | 0,0 | PASA | publicado |
| II.3 | 179/188 = 95,2 % | 173/182 = **95,1 %** | −0,1 | PASA | publicado |
| II.4 | 419/431 = 97,2 % | 419/431 = **97,2 %** | 0,0 | PASA | publicado |
| II.5 | 150/154 = 97,4 % | 146/150 = **97,3 %** | −0,1 | PASA | publicado |
| III.1 | 278/281 = 98,9 % | 278/281 = **98,9 %** | 0,0 | PASA | publicado |
| III.3 | 190/204 = 93,1 % | 177/191 = **92,7 %** | −0,4 | PASA | publicado |
| III.5 | 251/253 = 99,2 % | 250/252 = **99,2 %** | 0,0 | PASA | publicado |
| III.7 | 213/226 = 94,2 % | 212/225 = **94,2 %** | 0,0 | PASA | publicado |
| III.8 | 152/155 = 98,1 % | 152/155 = **98,1 %** | 0,0 | PASA | publicado |
| III.9 | 322/335 = 96,1 % | 314/327 = **96,0 %** | −0,1 | PASA | publicado |
| IV.1 | 218/222 = 98,2 % | 218/222 = **98,2 %** | 0,0 | PASA | publicado |
| IV.10 | 171/175 = 97,7 % | 170/174 = **97,7 %** | 0,0 | PASA | publicado |
| IV.2 | 736/736 = 100,0 % | 736/736 = **100,0 %** | 0,0 | PASA | publicado |
| IV.4 | 140/144 = 97,2 % | 136/140 = **97,1 %** | −0,1 | PASA | publicado |
| IV.5 | 361/371 = 97,3 % | 361/371 = **97,3 %** | 0,0 | PASA | publicado |
| IV.6 | 282/290 = 97,2 % | 279/287 = **97,2 %** | 0,0 | PASA | publicado |
| IV.7 | 417/426 = 97,9 % | 417/426 = **97,9 %** | 0,0 | PASA | publicado |
| IV.8 | 220/221 = 99,5 % | 220/221 = **99,5 %** | 0,0 | PASA | publicado |
| IV.9 | 204/221 = 92,3 % | 195/212 = **92,0 %** | −0,3 | PASA | publicado |

**En total se caen 78 preguntas cubiertas** de las **9.687** que contaba el motor de antes (el **0,8 %**):
son respuestas que se apuntaban a un tema con una comprobación anclada en un apartado que **no era el
suyo**, o con un hecho sentado en el apartado de su pregunta. **Ningún veredicto pasa de NO PASA a PASA
por este arreglo** —no era su trabajo—, y **dos publicados sí cambian de veredicto**:

### 3. Los dos temas publicados que dejan de llegar al 90 %, con nombre y con cifra

| tema | publicado con | mide hoy con la puerta nueva | qué se le ha descontado |
|---|---|---|---|
| **I.3** | 168/181 = **92,8 %** | **152/181 = 84,0 %** | **16 preguntas**: las 5 del estándar **ANSI/TIA-942-B** del CPD (de IV.5.7) y las 11 de otros **ocho grupos ajenos** que estaban sentados en sus cajones: el **CSV** del RFC 4180 (de II.3), el **TREBEP** y los **funcionarios interinos** (de I.4), las **infracciones leves**, el **ANSI SQL**, **Jakarta EE** (de III.5) y **Docker** (de IV.3) |
| **I.4** | 489/542 = **90,2 %** | **483/540 = 89,4 %** | **6 preguntas**: el **kernel de Android** (de IV.1) y la **Ética Pública** —que el índice no sitúa y se comprobaba contra el primer apartado de su epígrafe—, más el hueco duplicado de las tres que quedan |

**Y una corrección a un informe anterior, dicha**: el §7 del `INFORME-I.3.md` descontaba **solo el CPD**
y daba **163/181 = 90,1 %** como «cifra honesta». **Se quedó corto**: el lavado de I.3 son **16** preguntas
y no 5, porque los otros ocho grupos ajenos también entraron por la misma puerta (los cajones
`i-3-1-otros`, `i-3-2-otros` y `i-3-3-otros`) y el informe no los miró uno a uno. La cifra de hoy,
**152/181 = 84,0 %**, es la del motor con la puerta nueva; el texto publicado **no se ha tocado** y el
material ajeno sigue escrito donde estaba.

**Y la decisión ya está tomada, con estas palabras**: **I.3 e I.4 se quedan publicados** con su cifra nueva
a la vista, porque **lo que ha cambiado es la medición, no el material** y **retirar dos temas que el
propietario puede estudiar es peor que decirle la cifra**. La pantalla de revisión de apuntes ya los enseña
con el número medido —el bloque del panel la construyó **leyendo la medición**, no un valor guardado—, así
que el propietario puede retirarlos con un clic si quiere. Está escrito en `DECISIONES` (**F27**) y en
`PARA-EL-PROPIETARIO`.

**Lo que sí queda medido y comprobado**: las nueve preguntas que pierden la cobertura en I.3 son
**exactamente las que su propio catálogo declara de otro tema** (la lista está en la cabecera de
`catalogo_i_3.py`), y ninguna de ellas es una pregunta de I.3 mal medida. La sonda que lo dice, grupo a
grupo y con la materia que **nombra** cada hecho, es `F:\temp-opofuente\f27-scratch\sonda_perdidas.py`
(salida en `perdidas-I.3.txt`).

### 4. El doble conteo, medido por separado

Con el motor de antes y la misma base (`medir_doble_conteo_aislado.py`, salida `doble-conteo-aislado.txt`):
**16 de los 28 temas con apuntes** tenían preguntas contadas dos veces —**91 preguntas**—, y la cifra
cambiaba entre **+0,3 y +8,1 puntos**. La medición que había documentada (10 de 19 temas, 41 preguntas,
+0,3 a +4,2) era de una base con 19 temas; la base ha crecido.

| tema | grupos contados dos veces | preguntas (utilizables) | cifra de antes | contando una vez | cuánto cambiaba |
|---|---|---|---|---|---|
| I.2 | 1 | 2 | 626/656 = 95,7 % | 626/654 | +0,3 |
| I.3 | 10 | 16 | 152/181 = 84,0 % | 152/165 | +8,1 |
| I.4 | 3 | 7 | 483/540 = 89,4 % | 483/533 | +1,2 |
| I.5 | 2 | 4 | 335/367 = 91,4 % | 335/363 | +1,0 |
| I.7 | 3 | 3 | 287/488 = 58,8 % | 287/485 | +0,4 |
| I.8 | 4 | 3 | 389/469 = 82,9 % | 389/466 | +0,5 |
| II.3 | 3 | 6 | 173/182 = 95,1 % | 173/176 | +3,2 |
| II.5 | 4 | 4 | 146/150 = 97,3 % | 146/146 | +2,7 |
| III.3 | 5 | 13 | 177/191 = 92,7 % | 177/178 | +6,8 |
| III.5 | 1 | 1 | 250/252 = 99,2 % | 250/251 | +0,4 |
| III.7 | 1 | 1 | 212/225 = 94,2 % | 212/224 | +0,4 |
| III.9 | 7 | 8 | 314/327 = 96,0 % | 314/319 | +2,4 |
| IV.10 | 1 | 1 | 170/174 = 97,7 % | 170/173 | +0,6 |
| IV.4 | 4 | 4 | 136/140 = 97,1 % | 136/136 | +2,9 |
| IV.6 | 4 | 3 | 279/287 = 97,2 % | 279/284 | +1,0 |
| IV.9 | 11 | 9 | 195/212 = 92,0 % | 195/203 | +4,1 |

*(La columna «cifra de antes» de esta tabla es la que mide el motor **nuevo** con el resto de reglas
puestas —por eso I.3 dice 84,0 % y no 92,8 %—, y la de «contando una vez» es la aritmética de la opción
que conservaba el resultado guardado. Con la puerta nueva esa opción **no se sostiene**: sería contar
como cubierta una respuesta por un apartado ajeno, que es justo lo que el hallazgo 2 prohíbe. Por eso la
cifra final de un tema con doble conteo **no sube** «lo que subía» en esta tabla.)*

**Dicho en una línea**: el doble conteo **nunca dejaba pasar un tema malo** (la pregunta entraba una vez
como hueco y otra con su resultado, así que el cociente salía por debajo del verdadero), y ahora la
cuenta está donde tiene que estar. El arreglo que sí cambia veredictos es el de las anclas, y los dos
que cambia son I.3 e I.4, los dos **a peor**, porque lo que se les descontaba era lavado.

### 5. Lo que queda fuera, y las consecuencias dichas

- **No se ha escrito ni una fila en la base del propietario.** Toda la medición es de solo lectura
  (`servicio.medir` sobre `F:\OpoFuente\datos`, con el modelo sustituido por uno que se niega a
  usarse). Coste de API de este bloque: **0 $**.
- **El texto publicado no se reescribe**, ni el de I.3 ni el de I.4 ni el de ningún otro: el material
  ajeno que tenían sentado sigue escrito donde estaba. Lo que cambia es que **ya no cuenta**, y la
  decisión de qué hacer con él es del propietario.
- **Los informes por tema no se han tocado** (`docs/apuntes/INFORME-*.md`): el encargo de este bloque
  solo permite escribir en los tres documentos de seguimiento. La corrección de la cifra de I.3 está,
  por tanto, **en esta sección y en `PARA-EL-PROPIETARIO`**, no en su informe.
- **La próxima corrida de I.2, I.3 o I.4 costará más de lo normal y es una decisión del propietario**:
  son los tres temas con cajones de epígrafe, y con la regla nueva sus cajones se quedan **sin hechos**.
  La regla que ya existía (`_apartados_que_pierden_hechos`) rehace el texto de los apartados que pierden
  hechos, y el cajón que se queda sin hechos **sale del plan**. Las preguntas que vivían en el cajón
  **no pierden su cobertura** —su ancla son los apartados donde están sus hechos de verdad, y eso está
  comprobado con la sonda `sonda_cajones.py`—, así que una corrida con el reparto nuevo deja el tema en
  la cifra honesta de esta sección. No se ha corrido nada.
- **Y la otra cara del ancla propia, dicha**: el ancla sale del **índice de hoy**, así que **si a una
  materia del catálogo se le cambia la clave, su apartado guardado deja de anclar** hasta que el tema se
  vuelva a correr (entonces `plan_de` deja el apartado viejo en `sobran` y el texto se rehace). No ha
  pasado en la serie: los catálogos que se han tocado entre corridas cambiaron **patrones y títulos**, no
  claves.
- **Lo que no se ha hecho, y por qué**: el hallazgo **(a)** que quedó apuntado con este —un grupo con
  apartado propio y **sin comprobación guardada** no entra en la puerta (ni en el numerador ni en el
  denominador), así que un tema con apartados y sin comprobaciones mide «0 de 0»— **no se toca**: no es
  de los tres que este bloque cierra, y cambiarlo mueve el denominador de todos los temas otra vez. Sigue
  apuntado en `DECISIONES` (14-oct, el párrafo de los dos hallazgos del motor).

### 6. Las 18 puertas: **18/18, repartidas en dos corridas**, con los dos intentos y su causa

El registro literal está en **`F:\temp-opofuente\gates-f27-medidor.txt`** (los dos intentos en el mismo
fichero, con su cabecera de intentos) y el del segundo intento, aparte, en
`gates-f27-medidor-intento2.txt`. Se lanzó con `Start-Process -RedirectStandardOutput` y **sin tuberías**,
con el `gates.ps1` del árbol y su mismo juez (`common.ps1` + `Invoke-OpoFuenteStep`).

| Intento | Qué se corrió | Resultado | Causa del fallo |
|---|---|---|---|
| **1** | `scripts/gates.ps1` entero, de una pasada, sobre el motor nuevo | **puertas 1-17 OK · puerta 18 FALLO (código 1)**: 76 pasan y **2 caen**, las dos de `apuntes-revision.spec.ts` | **Fallo de lógica, no nativo**, y medido: el spec del panel siembra su apartado con la clave **`powershell-y-cmdlet`, que no es una materia del catálogo de IV.1** (sus nueve materias están en `catalogo_iv_1.py`; la de esa pregunta es `administracion-de-windows`). El escenario solo pasaba **por el respaldo que este bloque quita**, así que el tema medía `1/1 = 100,0 %` antes y `0/1 = 0,0 %` después. **Se arregla la semilla, no la expectativa** (que sigue siendo `1/1 = 100,0 %` y «Aprobarlo la publica»), y queda escrito en `DECISIONES` (**F27**) |
| **2** | las puertas que **pueden ver el fichero arreglado** —eslint (4), typecheck (5) y E2E (18)—, con el **mismo juez** | **4 OK · 5 OK · 18 OK**, con **78 de 78** en Playwright | — |

**Por qué se repartió así, y no se volvió a correr entera**: entre los dos intentos lo único que cambió
fue **un fichero de pruebas E2E** (`apps/web/tests/e2e/apuntes-revision.spec.ts`); las otras quince puertas
ya estaban verdes en el intento 1 **sobre el mismo árbol de código** y no leen ese fichero. Aun así se
repitieron las dos que sí podrían leerlo (eslint y typecheck) además de la que cayó. Decir «18/18 de una
pasada» sería falso; decir que no está verde, también. Es la misma decisión que se tomó en **F24-panel**
(«repartidas en tres corridas», con el mismo `common.ps1`).

**Lo que midió cada suite** (literal en el registro): unitarias **856**, integración **726** (43:15),
contrato **29**, componentes **379** (42 ficheros), E2E **78**, y las 18 puertas del `gates.ps1` en verde
entre las dos corridas. **Ninguna puerta cayó con un código nativo** (los dos códigos nativos que se
pagaron en esta serie —`0xC0000409` y `0xC0000374`— no han aparecido aquí).

---

## F28 · La plataforma desplegable (S28, §8 a §11 del objetivo vivo) — 15-oct-2026

**Rama**: `f28-plataforma`, sobre `main = e03b354` (más `a7e7f78`, que trae el objetivo vivo al
repositorio). Árbol: `F:\temp-opofuente\opofuente-plataforma`.

### Qué se ha construido

| Apartado | Qué hay | Dónde |
|---|---|---|
| **§8 · Cuentas y sesiones** | Alta, acceso, recuperación, cierre de sesión, baja, **puerta de rutas** y freno de intentos. Contraseñas con **argon2id**, testigos guardados como resumen, cookie `HttpOnly` + `SameSite=Lax`, **sin revelar si un correo existe** (ni al dar de alta ni al pedir el enlace) y **cada movimiento auditado** | `domain/accounts.py`, `accounts_service.py`, `account_repository.py`, `routes/accounts.py`, `session_gate.py`, migración `0039` |
| **§9 · Legales y control de datos** | Aviso legal, privacidad y cookies servidos por la API (una sola redacción, la que el programa puede comprobar), **consentimiento real** —antes de aceptar no se pone ninguna cookie no necesaria— y **un inventario de datos que se cruza contra el esquema** en las dos direcciones | `domain/legal.py`, `legal_service.py`, `routes/legal.py`, `lib/consent.ts`, `CookieNotice.tsx`, `LegalPage.tsx` |
| **§10 · Analítica** | **Montada**, propia y agregada: dos tipos de suceso y un vocabulario cerrado de etiquetas. **Sin cuenta, sin sesión, sin dirección, sin navegador y sin texto libre**; el servidor comprueba el consentimiento en cada petición | `domain/analytics.py`, `analytics_service.py`, `analytics_repository.py`, `routes/platform.py`, `lib/analytics.ts` |
| **§11 · Pagos** | **Solo el hueco y la bandera apagada**, con la propuesta escrita: Stripe (recomendada), Paddle y Redsys, con qué habría que contratar, qué costaría **sin verificar** y qué datos personales saldrían | `domain/payments.py`, `GET /api/v1/payments/plans` |
| **Punto 6 · El temporal** | Si `datos\tmp` no admite escritura —es un enlace a `E:`—, **se dice con la ruta exacta** y se usa un temporal de repuesto **en la misma unidad que la base**; si no vale ninguno, **el arranque falla** en lugar de arrancar a medias | `config.resolve_tmp_directory`, `main.py`, `test_temporal_de_datos.py` |

### Las banderas

`OPOFUENTE_ACCOUNTS_ENABLED=0` · `OPOFUENTE_LEGAL_ENABLED=0` (la cuarta, ver `DECISIONES`) ·
`OPOFUENTE_ANALYTICS_ENABLED=0` · `OPOFUENTE_PAYMENTS_ENABLED=0`. **Con las cuatro a 0 el árbol se
comporta como `e03b354`** para quien estudia sin cuenta, y hay una prueba que lo comprueba. La
analítica y los pagos **exigen** el marco legal encendido (encenderlos sueltos falla al arrancar, con
el motivo escrito).

### Los rojos previos (medidos, no prometidos)

Las tres pruebas de integración del bloque, ejecutadas contra el árbol **sin** el bloque
(`F:\temp-opofuente\f28-rojo`, detached HEAD en `e03b354`), con el intérprete del árbol de trabajo y
`PYTHONPATH` apuntando al árbol base:

```
19 failed, 2 passed, 2 errors in 113.93s
```

- **19 rojos** en `test_plataforma_cuentas.py`: las rutas nuevas contestan **404** (el alta, el
  acceso, la recuperación, la puerta de rutas, el freno, la baja, la auditoría…).
- **2 errores de recolección**: `test_plataforma_legal.py` y `test_temporal_de_datos.py` no se pueden
  ni importar contra la base (`No module named 'opofuente.domain.legal'`,
  `cannot import name 'resolve_tmp_directory'`), porque lo que prueban no existe allí.
- **Y 2 verdes**, que son los dos que **no deben cambiar**: `test_el_alumno_sin_cuenta_sigue_estudiando`
  (el estudio sin cuenta funciona igual) y `test_el_fichero_del_enlace_no_esta_en_la_respuesta`.
- Registro literal: `F:\temp-opofuente\f28-rojos-previos.txt`.

### Lo que queda fuera

- **El §12 (acabado de interfaz) no es de este bloque**: el encargo recibido son los puntos 8 a 11.
- **No hay servicio de correo contratado**: el enlace de recuperación se deja en `datos/recovery/`.
- **`Secure` de la cookie está apagado** (se sirve por `http://127.0.0.1`).
- **Los pagos no están integrados** y sus comisiones **no se han podido verificar**.
- **Los textos legales llevan marcas `[PENDIENTE: …]`** en los datos del titular: no se inventan.

### Gasto

**0 $**: este bloque no llama a ningún modelo. Su coste es de memoria y de tiempo de puertas, no de API.



---
## D11 · La entrega antigua `s14-promover-sin-guardar`, medida y fusionada (15-oct-2026)

El goal (D11) pide **una** cosa con esta rama: pasarla por las puertas **una vez**; si da 18/18,
fusionarla; si no, anotarla en `DEBT.md` y no volver a ella. **Dio 18/18 y entró.**

La rama es del **29 de septiembre** (`8f3718d`, «S14 sin guardar: promover de la Bandeja a la
Biblioteca») y se rescató del árbol de trabajo. Aporta **9 ficheros y 1.472 líneas, ninguna borrada**:
`apps/web/src/api/library.ts` (+40), `apps/web/src/api/queries.ts` (+69),
`apps/web/src/features/ingestion/PromotePanel.tsx` (+344),
`apps/web/src/features/ingestion/labels.ts` (+5), `apps/web/src/pages/TrayPage.tsx` (+11),
`apps/web/tests/e2e/promote.spec.ts` (+169), `apps/web/tests/unit/promote.test.tsx` (+363),
`docs/slices/S14.md` (+114) y `docs/TRASPASO-DE-MATERIAL-A-CLAUDE.md` (+357). De los nueve, **cinco ya
existían sin rastrear en `main`** (copias byte-idénticas, comprobadas con `git hash-object`), que es lo
que hizo fallar la primera fusión: se registraron en `1aa0f87` sin cambiar un byte y la fusión entró.

### 1. Qué se midió, y contra qué `main` (que no es el mismo árbol)

- **Lo que se midió:** `4f7a1f0` = `main@4290817` + `s14` — el merge que el encargo pide **antes** de medir.
- **Lo que entró en `main`:** `c6f9184` = `main@195cbb8` + `s14`.

Las dos cosas **no son el mismo árbol y se dice con la cifra**: entre `4290817` (14-oct 17:18) y
`195cbb8` (15-oct 11:28, **diez minutos antes de que arrancara la batería**) `main` ganó el trabajo del
bloque de apuntes —**918 líneas**: `application/topic_notes_service.py`, `domain/topic_index.py`, sus
dos pruebas y 9 líneas de `apps/web/tests/e2e/apuntes-revision.spec.ts`—. Así que:

- **la entrega `s14` está medida** (sus 9 ficheros son byte-idénticos en los dos árboles);
- **la composición `195cbb8 + s14` no la midió esta batería**, la midió el bloque de apuntes en su rama;
- poner «18/18» a secas sobre `c6f9184` sería **heredar** la cifra, que es lo que prohíbe el §1.4.

Queda ofrecida la re-medición sobre `c6f9184` (una pasada, ~54 min con la máquina cargada) para poder
anotar la cifra a nombre de ese commit.

### 2. La fusión: limpia, y contada en cuatro niveles

`git merge --no-edit main` desde el árbol `s14` con `main@4290817`: **auto-merge, 0 conflictos, exit 0**,
`git ls-files -u` **vacío** y ningún fichero tocado a mano. El único fichero con auto-merge real fue
`apps/web/src/api/queries.ts`, que `main` también había tocado: git **sumó** las dos partes.

La verificación no es «no parece que se perdiera nada». Se extrajeron los cuatro árboles con
`git archive` y se comprobó, **fichero a fichero**, `Counter(merge) == Counter(main) + Counter(s14) −
Counter(base)`:

| Qué | main | s14 | base | esperado | medido |
|---|---|---|---|---|---|
| ficheros | 836 | 649 | 644 | 841 | **841** |
| líneas | 323.564 | 241.947 | 240.475 | 325.036 | **325.036** |
| líneas de contenido | 294.564 | 220.880 | 219.593 | 295.851 | **295.851** |
| identidad por fichero (843 ficheros × 2 métricas) | | | | 0 | **0 discrepancias** |

Y lo que no se ve en un total: **0 marcadores de conflicto** en los 841 ficheros rastreados, **234 filas
de decisión** y **18 entradas del propietario** antes y después, con
`docs/DECISIONES-TOMADAS-EN-EL-OBJETIVO.md` y `docs/PARA-EL-PROPIETARIO.md` **byte-idénticos** (mismo
SHA-256). Los dos únicos ficheros de `s14` ausentes del merge son `HomePage.tsx` y `home.test.tsx`, que
**`main` había borrado a propósito**: la identidad cuadra igual (0 + 132 − 132 = 0).

### 3. Las 18 puertas: 18/18, una pasada, sin códigos nativos

Registro: **`F:\temp-opofuente\gates-s14.txt`** (y `gates-s14.err.txt`, 15.321 bytes **sin un solo
error**: son los `INFO` de alembic, el aviso de tamaño de trozo de Vite y la salida de `uv build`).
Lanzadas con `Start-Process -RedirectStandardOutput/-RedirectStandardError`, **sin tuberías**, y con
**Windows PowerShell 5.1** porque `pwsh` **no está instalado en esta máquina** (no hay ningún `pwsh.exe`
en disco; `dev.ps1` ya lo dice: «aquí no lo está»). Su `Test-OpoFuenteExitCodeDetection` comprobó
**antes de la primera puerta** que este intérprete ve los códigos de salida.

- **Una sola pasada**, **código de salida 0**, **54:00 minutos** (el reloj de fuera mide 54:01).
- **Ninguna puerta cayó con código nativo y por tanto ninguna se reintentó.** No hubo ni un rojo: **no
  hay intentos que contar**.
- Lo que midió cada suite, **literal del registro**: unitarias backend **853**, integración **724**
  (**45:11** — es la puerta que se come el tiempo: con la máquina cargada, más del doble de lo normal),
  contrato **29**, componentes **389** (43 ficheros, 61,39 s) y E2E **80** (3,5 min).
- **Las dos pruebas del entregable pasan y salen nombradas**: `promote.spec.ts` **2/2** en verde
  (E2E-20, «se pasa a la biblioteca desde la pantalla, y sin aceptar» y «volver a pasar el mismo
  material no duplica documentos») y `promote.test.tsx` dentro de los 389 de componentes.
- **La RAM no tumbó nada**: se midió antes (1,4 GB libres y sin tendencia a subir —37 procesos `node`
  aparcados—), así que no se esperó, y la batería terminó con 4,27 GB libres.

### 4. Las migraciones: la rama no trae ninguna

`s14` aporta **0 ficheros** en `apps/api/alembic/versions/`, así que no hay nada que reencadenar. El
árbol fusionado tiene **una sola cabeza**: `alembic heads` → **`0038_revision_de_apuntes (head)`**, y
`alembic branches` **no imprime nada** (ningún punto de rama), con la cadena lineal
`0034 → 0035 → 0036 → 0037 → 0038`. La trampa existe y ya está resuelta en `main`:
`0036_claves_no_fiables` resuelve su revisión previa **al importar** (`0035` si está en el directorio,
`0034` si no), justo para que dos bloques no dejen dos cabezas al fusionar.

### 5. Lo que queda fuera, con el porqué

- **No se corrieron capturas** (`npm run screens` **no** forma parte de las 18). Esta entrega no
  construye una pantalla nueva: mete una que ya estaba escrita dentro de una pantalla que ya existía, y
  lo que la respalda son las pruebas de componentes y el E2E, no una captura.
- **El entregable entra sin retoques**, y dos cosas suyas se dicen para que no sorprendan: el panel
  enlaza a **`/biblioteca`**, que es una dirección de antes y **redirige** a `/admin/biblioteca` (las
  direcciones viejas se conservan a propósito en `ROUTE_REDIRECTS`, para no romper marcadores ni las
  pruebas que entran por URL), y trae un `eslint-disable-next-line react-hooks/exhaustive-deps` **con su
  motivo escrito**. La puerta 4 (eslint) pasa con él.
- **`docs/TRASPASO-DE-MATERIAL-A-CLAUDE.md`** (29-sep, 357 líneas) entra en el árbol y convive con los
  traspasos de octubre (`PARA-CLAUDE-RESUMEN-DE-LAS-RONDAS…`, `RESUMEN-COMPLETO-DE-LAS-RONDAS…`,
  `OBJETIVO-VIVO-2026-10.md`). Es el más antiguo de los cuatro; se anota, no se borra.
- **La entrega no está obsoleta, y esto se comprobó antes de fusionar**: `main` **no tenía** la
  promoción en la interfaz —no hay ningún fichero `promote*` rastreado y **ningún** `POST
  /api/v1/documents` desde la web; los únicos POST a `/documents/…` son versiones de un documento que ya
  existe—. El hueco que `s14` tapa seguía abierto.
- **La limitación que la propia entrega declara** (y que se deja escrita, no arreglada): con un lote
  grande, aceptar sigue siendo **un clic por versión** en la Biblioteca, porque ADR-009 reserva la
  aceptación a una persona y una versión. `s14` mueve el cuello de botella, no lo quita; decidir si se
  acepta en bloque (agrupando por documento) es una decisión de diseño que no toma este bloque.

### 6. La segunda medición, sobre `c6f9184`, y por qué hacía falta

La medición de arriba certificó **`4f7a1f0`**, pero lo que entró en `main` fue **`c6f9184`**, y entre los
dos `main` había ganado 918 líneas del bloque de apuntes —incluidas **9 líneas de
`apps/web/tests/e2e/apuntes-revision.spec.ts`**, que es un fichero que **la puerta 18 ejecuta**—. Por eso
la cifra se volvió a medir **sobre el commit que está en `main`**. Esto es lo que salió.

**El árbol medido es exactamente `c6f9184`**: `HEAD` desacoplado en ese commit, con
`git status --porcelain` **vacío** antes y después de las dos corridas. `main`, en cambio, se movió **dos
veces más** mientras se medía (`5a62d0d` → `6b3db4ab` → `cef3308`); eso ya no se pierde, porque **los dos
registros llevan su procedencia** (ver el punto 4 y **DEBT-030**).

| Tramo | Cuándo | Puertas | Resultado |
|---|---|---|---|
| **1** | 12:45:36 → 13:51:11 (65 min) | 1–9 | **1–8 OK** · **9 FALLO (código 1)** · 10–18 no llegaron a correr |
| *diagnóstico* | 13:52 | — | los **dos ficheros** que cayeron pasan **42/42 en aislamiento**, mismo árbol y mismo juez |
| **2** | 14:59:24 → 15:06:02 (**06:39**) | 9–18 | **9–18 OK, `exit 0`** · componentes **389/389** · E2E **80/80** |

**Veredicto: `c6f9184` pasa las 18, en dos tramos**, y el único rojo del camino fue un **falso negativo
por contención**, medido y no supuesto:

- Los dos fallos del tramo 1 son `TestingLibraryElementError: Unable to find role="button"` dentro de dos
  `waitFor` que esperan un botón que aparece **tras una petición asíncrona** (`promote.test.tsx:150` y
  `questions.test.tsx:217`): firma de tiempo, no de expectativa.
- **`questions.test.tsx` no viene de `s14`**: la rama aporta **9 ficheros** (`git diff 4f7a1f0^2
  4f7a1f0`) y ese no es uno de ellos. Un fallo en un fichero que la rama no toca no puede ser de la rama.
- Los dos ficheros **pasan 42/42 en aislamiento**, sobre el mismo árbol y con el mismo juez.
- Y el terreno, con la cifra: en el tramo 1 la puerta 7 tardó **1:00:20** (frente a **45:11** en la primera
  medición) y Vitest creó jsdom **43 veces con 471 s de tiempo rastreado (53 %)**. Es **DEBT-022**.

**El tramo 2 no repite el tramo 1, y se dice por qué**: el árbol es byte-idéntico (mismo `HEAD`, árbol
limpio) y las puertas 1–8 ya estaban verdes sobre él, así que solo se re-juzga **lo que quedó sin
veredicto**. Es el mismo criterio con el que **F24-panel** quedó «18/18 repartidas en tres corridas», con
el mismo `common.ps1`. Y el tramo 2 se corrió **a propósito con la máquina cargada** (CPU 90–100 %, cuatro
suites de integración ajenas): que la puerta 9 pase ahí **es un veredicto más fuerte**, no uno más cómodo
— el riesgo que se corría era un falso **rojo**, que es justo lo que sabemos detectar; un falso verde es
lo que no estaba en juego y no se ha fabricado.

**Los dos registros, con su procedencia** (lo que **DEBT-030** pedía, y ya está en el acta):

| Fichero | Qué es | Procedencia que lleva dentro |
|---|---|---|
| `F:\temp-opofuente\gates-s14.txt` (43.995 B) | tramo 1, salida literal, `exit=1` | `ANTES … main=5a62d0d…` → `DESPUES … main=6b3db4ab…` |
| `F:\temp-opofuente\gates-s14-tramo2.txt` (38.963 B) | tramo 2, salida literal, `exit=0` | `ANTES … main=cef3308…` → `DESPUES … main=cef3308…` |

*(Sus `.err.txt` van al lado: 30.498 y 15.321 bytes, sin un error real — son los `INFO` de alembic, el
aviso de tamaño de trozo de Vite y las salidas de `uv build`.)*

**Y el instrumento hizo su trabajo el primer día que se usó**: en el tramo 1, `main` **se movió de verdad
durante los 65 minutos** (`5a62d0d` → `6b3db4ab`, las 83 líneas de `DECISIONES` del commit `F28b`). Sin
esa cabecera, hoy habría vuelto a escribirse una cifra contra un commit que no era el medido — que es
exactamente el agujero que **DEBT-030** describía y que ya está cerrado.


## F29 · Devolver al estudio las preguntas en cuarentena: la clave derivada (15-oct-2026)

**Rama `f29-claves-derivadas`** (worktree `F:\temp-opofuente\opofuente-claves2`, desde `main = e03b354`),
migración **`0039_claves_derivadas`**. Sin fusionar. Cierra el **§1** de
`SIGUIENTE-TANDA-CIERRE-DEL-OBJETIVO-2026-10.md`, que es el encargo.

**Lo que cambia, en una frase.** Una pregunta de un conjunto en cuarentena vuelve al estudio cuando
**dos fuentes independientes dicen la misma letra** —los apuntes, con su cita verificada, y el modelo
preguntado **sin apuntes**— y su clave se guarda como `derived` (**nunca** `active`), con la marca
«clave revisada automáticamente» en la zona del alumno. Las que no consiguen esa coincidencia siguen
fuera **con su motivo escrito**.

### 1. La copia verificada (paso 0)

`F:\OpoFuente\datos\backups\20261015-101027-00483c.zip` · **811.170.724 bytes** · SHA-256 del ZIP
`adc596ef4d916de8841aba97d35792953680b7c599f268a7f8830701a6e9b2bb`. Método del proyecto
(`BackupService.create` con alcance `database` → ZIP con manifiesto → `verify` → extracción a un
temporal y `integrity_check`): **verify 2/2 entradas, 0 problemas**, base extraída 2.746.511.360
bytes, `integrity_check` **ok**, `quick_check` **ok**, `foreign_key_check` **0 filas**, revisión de la
copia `0037_origin_scope`. No se ha borrado ninguna copia.

### 2. Lo que se ha construido, con su prueba que falla antes

| # | Pieza | Qué hace | Prueba (rojo antes) |
|---|---|---|---|
| 1 | `domain/derived_keys.py` | La coincidencia de las dos fuentes, los **tres motivos** de quedarse fuera (en ese orden), la protección de la clave oficial por **tres caminos** y la decisión del 90 %. Puro: se prueba sin base de datos | `tests/unit/test_derived_keys.py` (**20 pruebas**) |
| 2 | `alembic/versions/0039_claves_derivadas.py` | `question_derived_keys` (una fila por pregunta, con sus dos fuentes y su cita; `CHECK (key_state = 'derived')`) y `question_key_gaps` (por qué sigue fuera). **Vuelta atrás probada** | `tests/integration/test_migrations_0039.py` (**5**) |
| 3 | `infrastructure/derived_key_repository.py` | La ruta **auditada**: guarda la clave con su evento, los motivos con un evento por conjunto, el rechazo del oficial y la decisión | `tests/integration/test_claves_derivadas.py` (**12**) |
| 4 | `ports.AnswerKeyModel` + `DeepSeekNotesModel.responder` | La segunda fuente: la pregunta **sola** (enunciado y opciones), `temperature=0`, sin apuntes en el mensaje | lectura pura `read_respuestas_independientes` |
| 5 | `tools/claves_derivadas.py` | `--listar`, `--prever`, `--derivar` (`--tope-usd`, `--limite`, `--seco`), `--decidir`, `--informe` | — |
| 6 | `study_service`: `_banco`, `_correccion_de` y los **cinco sitios** que eligen preguntas | La pregunta entra por **su** clave: derivada sí; motivo escrito no (**aunque el conjunto vuelva**); si no, el veredicto del conjunto | `test_la_pregunta_derivada_entra_en_el_test_con_su_letra`, `test_la_pregunta_sin_clave_fiable_sigue_fuera_aunque_el_conjunto_vuelva` |
| 7 | Zona del alumno: `derived_key` en la API y la marca en el test y en el resultado | El alumno ve **«clave revisada automáticamente»**, distinta de «clave en revisión» (una dice de dónde sale la letra; la otra, que se duda) | `apps/web/tests/unit/marcaClaveDerivada.test.tsx` (2) |

**El rojo, tal cual salió** (`F:\temp-opofuente\f29-scratch\rojo-antes.txt`), revirtiendo **una**
regla y corriendo **solo** la prueba que la fija:

1. sin mirar la clave derivada en la composición → `UnsupportedError: no hay ninguna pregunta que se
   pueda poner` (la pregunta vuelve a quedarse fuera, como antes);
2. guardando la clave derivada como `active` → `sqlite3.IntegrityError: CHECK constraint failed:
   ck_derived_key_state` (la base la rechaza: «nunca `active`» **no** depende de que alguien se
   acuerde).

### 3. La copia de la base y la migración

La copia del §1 es de la revisión `0037_origin_scope`. Al empezar la corrida se aplicó la cabeza
(`0039`) sobre la base real: **sube también la `0038_revision_de_apuntes` de F24**, que ya está en
`main` y la base real no tenía —sin ella el código de `main` no arranca—. Las dos son aditivas y las
dos tienen vuelta atrás probada.

### 4. La corrida, con su previsión delante y su tope

`--prever` (0 $, antes de pagar): **10 conjuntos entran, 5 se rechazan por clave oficial** (122
preguntas de la AGE), **74 preguntas** con letra y cita por preguntar, 8 llamadas,
**0,0030–0,0033 $**. Tope puesto en **0,50 $ y 200 llamadas**.

Corrida real (`--derivar`):

| | |
|---|---|
| llamadas | **13** (0 fallidas) |
| preguntas preguntadas | **74** |
| tokens | 16.701 de entrada (1.536 de caché) · **75.510 de salida** |
| coste medido | **0,0478 $** |
| coste por pregunta | **0,000646 $** |
| claves derivadas | **59 (79,7 % de las preguntas preguntadas)** |

**Y una corrección dicha: la previsión se quedó 14,5 veces corta.** Estimaba 12 tokens de salida por
pregunta (lo que ocupa una letra en JSON) y el modelo devolvió ≈1.020: **la previsión era
0,0030 $ y costó 0,0478 $**. La constante está corregida con lo medido
(`TOKENS_DE_SALIDA_POR_PREGUNTA = 1020`) para que la próxima avise de verdad. El tope no se acercó
ni de lejos y el total es de cinco céntimos, así que la corrida no se paró; con una base 16 veces
mayor (los 1.283 candidatos posibles de hoy, si todos tuvieran cita) sí habría que decidir si merece
la pena: costaría ≈0,8 $.

### 5. El antes/después por conjunto, contado en la base y con el motor

«Antes» es **0** por el veredicto `no_fiable` (la cuarentena cortaba el conjunto entero: lo demuestra
el rojo del §2, no una suposición). «Después» está contado **llamando a `_candidatas`**, que es el
embudo real de la composición, y sin escribir nada
(`F:\temp-opofuente\f29-scratch\antes-despues.txt`):

| conjunto | preguntas | devueltas al estudio (test por tema) | derivadas | corroboradas | % con clave fiable | ¿vuelve a tests? |
|---|---|---|---|---|---|---|
| TAI · SIMULACROS y TEST | 28 | **9** | 10 | 0 | 35,7 % | no (faltan 16) |
| TAI · 1600-Preguntas-Constitución | 75 | **3** | 3 | 20 | 30,7 % | no (faltan 45) |
| TAI · TEST B1 | 75 | **3** | 3 | 20 | 30,7 % | no (faltan 45) |
| TAI · Supuestos Practicos Bloque IV | 67 | **1** | 1 | 14 | 22,4 % | no (faltan 46) |
| TAI · Test por temas | 90 | **7** | 8 | 0 | 8,9 % | no (faltan 73) |
| TAI · Test Aragón 2015 | 102 | **1** | 1 | 8 | 8,8 % | no (faltan 83) |
| TAI · baquedano | 318 | **19** | 23 | 5 | 8,8 % | no (faltan 259) |
| TAI · 2019 GSI promoción | 80 | **1** | 1 | 6 | 8,8 % | no (faltan 65) |
| TAI · TEST VARIOS | 192 | **4** | 9 | 7 | 8,3 % | no (faltan 157) |
| TAI · C_ejer_1_libre_DZA_2026 | 50 | **0** | 0 | 2 | 4,0 % | no (faltan 43) |
| **TOTAL** | **1.077** | **48** | **59** | **82** | **13,1 %** | **0 conjuntos** |

**Ningún conjunto alcanza el listón del 90 %** (el mejor mide 35,7 %), así que la decisión de volver
—tomada y auditada conjunto a conjunto con su cifra— es **que ninguno vuelve entero**. Lo que vuelve
es cada pregunta con su clave derivada.

**Los dos números de «devueltas» no son el mismo a propósito**: hay **59 claves derivadas** y **48**
alcanzables por un test por tema; las **11** restantes no están catalogadas en ningún tema (no las
sitúa el índice), así que vuelven por la **práctica de un conjunto** o el **repaso**, que son los
otros caminos que eligen preguntas.

### 6. Lo que sigue fuera, y por qué (contado en la base)

De las **1.077** preguntas de los 10 conjuntos procesados: **628 sin material** (los apuntes no las
contestan), **293 sin cita** (dan una letra pero no la frase que la sostenga) y **15 sin
coincidencia** (las dos fuentes hablan y no dicen lo mismo: **esas 15 son del propietario**, y son las
que la bandeja del §2 tiene que enseñar agrupadas por conjunto). Las **82 corroboradas** (los apuntes
confirman la letra de la plantilla activa) cuentan para el listón pero **no entran hasta que su
conjunto vuelva**, porque su letra sale de la plantilla que está en cuarentena.

Y **las claves oficiales no se han tocado**: 5 conjuntos de la AGE con su respuesta publicada
**rechazados** y auditados (`question_set.derived_key_refused`), 122 preguntas.

### 7. Las 18 puertas, y la fusión con `main`

**18/18 en una sola pasada.** El registro literal está en
`F:\temp-opofuente\gates-f29-claves-derivadas.txt`, lanzado con `Start-Process` y **sin
tuberías**, con el `gates.ps1` del árbol y su mismo juez. Lo que midió cada suite (literal en el
registro): unitarias **876**, integración **742** (1:07:39), contrato **29**, componentes **381** (43
ficheros), E2E **78** (3,9 min), migración desde base vacía, siembra idempotente y fixtures de perfil
en verde. **Ninguna puerta cayó y no hubo ningún código nativo.** El puerto (8765/4173) estaba libre
cuando se lanzó la 18, comprobado con `netstat` antes.

**Una prueba se añadió después de que la 7 arrancara** (`test_el_alumno_ve_la_marca_de_la_clave_derivada`,
la que comprueba `derived_key` por la API del alumno). Se corrió aparte y está verde (**12 pruebas**
del fichero). Decir que la 7 la midió sería falso; el fichero entero se ha vuelto a correr después.

**La fusión con `main` (`cef3308`, que trae el contenido —III.4 publicado, I.4 republicado, D4—, D11
y `s14`) se resuelve SUMANDO, y se verifica contando**: los dos únicos conflictos eran
`DECISIONES-TOMADAS-EN-EL-OBJETIVO.md` y `ESTADO-DEL-OBJETIVO.md` (cada bloque añade lo suyo al
final). La comprobación es `Counter(fusión) == Counter(main) + Counter(mía) − Counter(base)` línea a
línea, con `base = e03b354`:

| documento | base | main | mía | fusión | faltan | sobran | marcadores | filas de decisión (base → main → mía → fusión) |
|---|---|---|---|---|---|---|---|---|
| `DECISIONES` | 375 | 617 | 383 | **625** | 0 | 0 | **0** | 191 → 201 → 199 → **209** |
| `ESTADO` | 3.150 | 3.259 | 3.294 | **3.403** | 0 | 0 | **0** | 165 → 165 → 166 → **166** |

Las dos filas cuadran: **209 = 201 + 199 − 191** (mis ocho decisiones entran enteras y ninguna de
`main` se pierde). Sobre el resultado: **`ruff check .` limpio, `mypy` estricto limpio** (240
ficheros) y **128 pruebas de integración** de los ficheros que tocan esto y lo que trajo `main`
(derivadas, cuarentena, apuntes, migraciones, estudio y alumno) **en verde**.

**Aviso de tráfico que queda dicho**: el bloque de la bandeja por conjunto crea
`0039_bandeja_por_conjunto` colgando de `0038`; como esta rama entra primero con
`0039_claves_derivadas`, **su `down_revision` tiene que re-apuntar a la mía** (él ya lo sabe). Con las
dos colgando de `0038` habría dos cabezas y `alembic upgrade head` no sabría por dónde seguir.

**Tres pruebas existentes se tocan, y se dice por qué** (no es relajar el juez):

- `test_migrations_downgrade.py`: la cadena se recorre hacia atrás y **cada migración añade su
  escalón**; el de `0039` entra con las dos tablas que su vuelta atrás se lleva. Sin él, la prueba
  afirmaba estar en `0038` cuando la cabeza ya es `0039`.
- `test_study_session.py` y `test_study_api.py` («sin clave activa no hay sesión»): el camino nuevo
  permitía montar una sesión de un conjunto **sin plantilla activa y sin ninguna clave derivada**, que
  no se podría corregir. `_correccion_de` vuelve a negarse con **el mismo** `ClassificationConflictError`
  que publicaba el contrato; la expectativa **no** se ha tocado.

### 8. Lo que queda fuera de este bloque, y por qué

- **El §2 (la bandeja por conjunto) no se hace aquí**: el encargo pide **dejar el dato y el motivo**, y
  están (`question_key_gaps`, con su recuento por conjunto y su evento de auditoría).
- **La interacción con la puerta de datos del §1.4**: si un conjunto llegara al 90 % y volviera a
  `fiable`, la puerta que se recalcula al cerrar cada tema lo mediría **con las anclas guardadas** —que
  no cambian con la derivación— y podría devolverlo a cuarentena. Hoy **no le pasa a ninguno** (ninguno
  llega al 90 %), pero queda dicho.
- **La previsión de salida estaba mal** (§4) y el cliente del modelo **no lleva `max_tokens`**: el
  modelo devuelve ~1.020 tokens de salida por pregunta cuando solo se lee una letra. Recortarlo sería
  un cambio en un camino compartido con los apuntes y no se ha hecho aquí.
- **Una clave derivada se va con su ancla, y eso se ha visto en vivo.** La fila guarda el **ancla**
  que la sostiene (la cita verificada) y su clave foránea es `ON DELETE CASCADE`: si el tema se vuelve
  a correr y el apartado se rehace, el ancla desaparece y **la clave derivada se va con ella** —que es
  lo correcto: una letra sin la cita que la sostiene no es una clave derivada—. Medido: la corrida
  escribió **59** claves a las 13:12 (local); a las 14:25 el bloque de contenido corrió **I.8**, se
  rehicieron apartados de baquedano y **6 de sus 23 claves** se fueron con sus anclas (medido a las
  16:00: **53 claves**, y las 6 preguntas se han quedado **sin ninguna ancla**). No es un fallo: es el
  precio de que la clave dependa de su evidencia. **La consecuencia práctica hay que decirla**: un
  tema que se reescriba puede devolver a la cuarentena preguntas que ya habían vuelto, y la forma de
  que no pase es **volver a correr `--derivar` al cerrar cada tema** (cuesta ~0,0006 $ por pregunta y
  salta las ya derivadas: con los 1.283 candidatos de hoy, ≈0,8 $). Queda como recomendación, no como
  puerta automática: hacerlo puerta es una decisión del propietario.

---

## F32 · El «0 de 0» del medidor: un grupo con apartado propio y sin comprobación guardada pasa a ser trabajo pendiente (15-oct-2026 · §4 de `SIGUIENTE-TANDA-CIERRE-DEL-OBJETIVO-2026-10`)

### 1. El defecto, medido, y por qué movía el denominador de todos los temas

`TopicNotesService._contar_cobertura` recorre los grupos del tema y le da a cada uno un desenlace. Tenía
cuatro y un `continue` de más:

```python
if apartados:
    # Tiene apartado propio y no hay comprobación guardada: no entra en la puerta.
    continue
```

Un grupo **con apartado propio escrito y sin comprobación guardada** se caía de la puerta **por los dos
lados**: no entraba en el numerador (no hay comprobación que lo demuestre) **ni en el denominador** (el
`continue` lo saltaba entero). Las consecuencias, y las dos se midieron:

1. la cifra de ese tema se calculaba sobre un conjunto **más pequeño** —solo las preguntas que sí tenían
   comprobación guardada—, así que salía **más alta de lo que es**;
2. en el caso extremo —apartados escritos y **ninguna** comprobación guardada— el denominador se quedaba
   **vacío**, la línea de puerta no se imprimía y el tema medía «**0 de 0**»: una casilla vacía que no
   dice ni si está bien ni cuánto le falta.

El hallazgo se apuntó el 14-oct como «medido y **no** tocado» (`DECISIONES`, el párrafo de los dos
hallazgos del motor) precisamente porque cambiarlo mueve el denominador de todos los temas. El §4 del
documento de cierre lo convierte en encargo.

### 2. La regla que entra

Un grupo **con apartado propio y sin comprobación guardada** cuenta como **pendiente de comprobar**:
**entra en el denominador y no en el numerador**, y se cuenta aparte. Ni suma cobertura (sería mentira:
no hay nada que la demuestre) ni se cae del denominador (sería peor: esconde trabajo por hacer).

El quinto desenlace **no** se ha metido en el enumerado `Coverage` a propósito: `Coverage` es lo que dice
una fila guardada en `question_note_anchors`, y esa tabla tiene un `CHECK` de cuatro valores
(`ck_anchor_result`, `apps/api/opofuente/infrastructure/db_models.py`). Un «pendiente» **no se guarda
nunca** —lo que hace el medidor al encontrárselo es contarlo—, así que meterlo en el enumerado que se
persiste sería declarar un valor que no puede existir en la base. Vive en `CoverageReport.add_pendiente`
y en tres campos nuevos (`pendientes`, `preguntas_pendientes`,
`preguntas_pendientes_con_clave_utilizable`), y el `elif` de la línea de puerta garantiza que **nunca más
se imprime un «0 de 0»**: si no hay denominador con clave, se dice por qué.

### 3. La prueba que falla antes

Dos pruebas, y las dos se vieron **en rojo** sobre el árbol sin el arreglo:

- **unitaria** (`apps/api/tests/unit/test_puerta_de_cobertura.py`, 5 pruebas nuevas): el recuento. Sin el
  arreglo fallan con `AttributeError: 'CoverageReport' object has no attribute 'add_pendiente'`.
- **de integración** (`apps/api/tests/integration/test_topic_notes.py::test_un_tema_con_apartados_y_sin_comprobaciones_no_mide_cero_de_cero`):
  el caso real. Corre un tema entero (dos apartados con texto, dos comprobaciones guardadas), borra las
  comprobaciones —que es el estado que deja una corrida parada por su tope de tiempo entre la redacción
  y la comprobación— y **mide**. Sin el arreglo, la primera aserción que cae es la que mide el defecto:
  `assert informe.coverage.preguntas_con_clave_utilizable == 2` → **`assert 0 == 2`**. El orden de las
  aserciones es a propósito: primero el defecto **medido** (el denominador vacío) y después la cuenta
  nueva, para que el rojo de antes del arreglo sea el «0 de 0» y no un atributo que aún no existe.

Con el arreglo: **14 pruebas verdes** entre las dos (las 8 de la puerta que ya existían, las 5 nuevas y
la de integración).

### 4. Cómo se midió, y por qué no sobre la base viva

La base del propietario **se estaba moviendo mientras se medía**: los bloques de plataforma y de claves
estaban corriendo. Se vio de la forma más incómoda: dos medidas seguidas del **mismo** medidor dieron
para I.8 `261/320 = 81,6 %` (la primera) y `297/367 = 80,9 %` (la segunda), con el **denominador
cambiado solo**, de 320 a 367, sin que nadie tocara los apuntes.

Así que la tabla de este bloque sale de una **instantánea consistente** de la base
(`sqlite3.Connection.backup` sobre `F:\OpoFuente\datos\opofuente.sqlite3`, 2 748 469 248 bytes, 25 s,
**solo lectura**) y **las dos versiones del medidor se miden sobre la misma instantánea**. Se comprobó
con una huella del contenido de las siete tablas que deciden la puerta (`question_note_anchors`,
`answer_key_entries`, `answer_key_versions`, `curriculum_mappings`, `topic_note_sections`, `topic_facts`,
`question_derived_keys`): **idéntica antes, en medio y después** de las dos medidas
(`5754bf1b…`). Coste: **0 $** y ni una fila escrita.

### 5. La tabla de los 33, antes y después

«Antes» = `main` en `cef3308` (la definición de hoy). «Ahora» = `f32-medidor`. Las dos columnas que
deciden son las de **clave utilizable**; las de «todas» se miden y se enseñan pero no deciden. «con
apartado» son los grupos con apartado propio y texto (los que la puerta puede medir) y «comprobadas» los
que tienen comprobación guardada.

| Tema | grupos | con apartado | comprobadas | antes (utilizable) | ahora | antes (todas) | ahora | pendientes | veredicto |
|---|---|---|---|---|---|---|---|---|---|
| **I.1** | 1998 | 1998 | 1998 | 1958/1985 = 98,6 % | 1958/1985 = 98,6 % | 1958/2016 = 97,1 % | 1958/2016 = 97,1 % | — | PASA |
| **I.2** | 613 | 612 | 612 | 626/656 = 95,4 % | 626/656 = 95,4 % | 626/682 = 91,8 % | 626/682 = 91,8 % | — | PASA |
| **I.3** | 168 | 158 | 158 | 152/181 = 84,0 % | 152/181 = 84,0 % | 152/182 = 83,5 % | 152/182 = 83,5 % | — | NO PASA |
| **I.4** | 536 | 533 | 532 | 490/550 = 89,1 % | 490/550 = 89,1 % **«cambia»** | 490/562 = 87,2 % | 490/563 = 87,0 % | 1 grupo(s) · 1 preg. (0 en la que decide) | NO PASA |
| **I.5** | 334 | 332 | 332 | 343/375 = 91,5 % | 343/375 = 91,5 % | 343/385 = 89,1 % | 343/385 = 89,1 % | — | PASA |
| **I.6** | 168 | 168 | 168 | 171/240 = 71,2 % | 171/240 = 71,2 % | 171/249 = 68,7 % | 171/249 = 68,7 % | — | NO PASA |
| **I.7** | 364 | 361 | 257 | 291/495 = 58,8 % | 291/495 = 58,8 % | 291/528 = 55,1 % | 291/528 = 55,1 % | — | NO PASA |
| **I.8** | 409 | 405 | 213 | 261/320 = 81,6 % | 261/488 = 53,5 % **«cambia»** | 261/337 = 77,4 % | 261/516 = 50,6 % | 150 grupo(s) · 201 preg. (168 en la que decide) | NO PASA |
| **I.9** | 131 | 0 | 0 | sin línea | sin línea | sin línea | sin línea | — | sin línea (sin apartados) |
| **II.1** | 212 | 212 | 211 | 202/205 = 98,5 % | 202/205 = 98,5 % | 202/214 = 94,4 % | 202/214 = 94,4 % | — | PASA |
| **II.2** | 173 | 173 | 173 | 162/164 = 98,8 % | 162/164 = 98,8 % | 162/170 = 95,3 % | 162/170 = 95,3 % | — | PASA |
| **II.3** | 170 | 167 | 167 | 174/183 = 95,1 % | 174/183 = 95,1 % | 174/187 = 93,0 % | 174/187 = 93,0 % | — | PASA |
| **II.4** | 445 | 445 | 445 | 424/436 = 97,2 % | 424/436 = 97,2 % | 424/468 = 90,6 % | 424/468 = 90,6 % | — | PASA |
| **II.5** | 143 | 139 | 139 | 149/153 = 97,4 % | 149/153 = 97,4 % | 149/158 = 94,3 % | 149/158 = 94,3 % | — | PASA |
| **III.1** | 273 | 273 | 273 | 281/284 = 98,9 % | 281/284 = 98,9 % | 281/294 = 95,6 % | 281/294 = 95,6 % | — | PASA |
| **III.2** | 294 | 0 | 0 | sin línea | sin línea | sin línea | sin línea | — | sin línea (sin apartados) |
| **III.3** | 178 | 173 | 173 | 177/191 = 92,7 % | 177/191 = 92,7 % | 177/197 = 89,8 % | 177/197 = 89,8 % | — | PASA |
| **III.4** | 246 | 244 | 244 | 243/246 = 98,8 % | 243/246 = 98,8 % | 243/257 = 94,6 % | 243/257 = 94,6 % | — | PASA |
| **III.5** | 252 | 251 | 251 | 251/253 = 99,2 % | 251/253 = 99,2 % | 251/259 = 96,9 % | 251/259 = 96,9 % | — | PASA |
| **III.6** | 141 | 0 | 0 | sin línea | sin línea | sin línea | sin línea | — | sin línea (sin apartados) |
| **III.7** | 230 | 229 | 229 | 216/233 = 92,7 % | 216/233 = 92,7 % | 216/257 = 84,0 % | 216/257 = 84,0 % | — | PASA |
| **III.8** | 145 | 145 | 145 | 154/157 = 98,1 % | 154/157 = 98,1 % | 154/167 = 92,2 % | 154/167 = 92,2 % | — | PASA |
| **III.9** | 332 | 325 | 325 | 319/332 = 96,1 % | 319/332 = 96,1 % | 319/354 = 90,1 % | 319/354 = 90,1 % | — | PASA |
| **IV.1** | 227 | 227 | 227 | 218/222 = 98,2 % | 218/222 = 98,2 % | 218/226 = 96,5 % | 218/226 = 96,5 % | — | PASA |
| **IV.2** | 747 | 747 | 747 | 738/738 = 100,0 % | 738/738 = 100,0 % | 738/753 = 98,0 % | 738/753 = 98,0 % | — | PASA |
| **IV.3** | 125 | 0 | 0 | sin línea | sin línea | sin línea | sin línea | — | sin línea (sin apartados) |
| **IV.4** | 149 | 145 | 145 | 138/142 = 97,2 % | 138/142 = 97,2 % | 138/147 = 93,9 % | 138/147 = 93,9 % | — | PASA |
| **IV.5** | 381 | 381 | 380 | 367/377 = 97,3 % | 367/377 = 97,3 % | 367/389 = 94,3 % | 367/389 = 94,3 % | — | PASA |
| **IV.6** | 305 | 301 | 301 | 285/294 = 96,9 % | 285/294 = 96,9 % | 285/308 = 92,5 % | 285/308 = 92,5 % | — | PASA |
| **IV.7** | 431 | 431 | 431 | 419/428 = 97,9 % | 419/428 = 97,9 % | 419/450 = 93,1 % | 419/450 = 93,1 % | — | PASA |
| **IV.8** | 220 | 220 | 220 | 221/222 = 99,5 % | 221/222 = 99,5 % | 221/228 = 96,9 % | 221/228 = 96,9 % | — | PASA |
| **IV.9** | 217 | 206 | 206 | 196/213 = 92,0 % | 196/213 = 92,0 % | 196/223 = 87,9 % | 196/223 = 87,9 % | — | PASA |
| **IV.10** | 182 | 181 | 181 | 170/174 = 97,7 % | 170/174 = 97,7 % | 170/179 = 95,0 % | 170/179 = 95,0 % | — | PASA |

### 6. Qué cambia de veredicto, y qué no

- **Ningún tema cambia de veredicto.** I.4 e I.8 siguen en **NO PASA**, y los 31 restantes siguen en el
  veredicto que ya tenían. La puerta no se ha movido: el umbral sigue en el 90 %.
- **Los cuatro números que el encargo pedía vigilar no se mueven**: III.4 **98,8 %**, II.2 **98,8 %**,
  III.8 **98,1 %** y II.5 **97,4 %**, idénticos al decimal con las dos definiciones.
- **Los 26 temas publicados siguen publicados y ninguno se ha retirado.** Medido sobre la misma
  instantánea: **26 nodos con versión archivada y apuntes** (`dossier_snapshots` con `notes`), 7 sin
  versión (I.6, I.7, I.8, I.9, III.2, III.6 y IV.3). A **ninguno** de los 26 le cambia el número que
  decide. Y dos de ellos siguen **por debajo del listón con su cifra a la vista**, como se decidió:
  **I.3 = 152/181 = 84,0 %** e **I.4 = 490/550 = 89,1 %**. Lo que ha cambiado es **la medición, no el
  material**.
- **Y la razón de que no haya nada que decidir con los publicados, medida**: los dos **únicos** temas con
  grupos pendientes de comprobar son I.8 (en borrador) e I.4; y el grupo pendiente de I.4 es uno cuya
  clave marcó el paso B como contraria a la norma, así que **no entra en el denominador que decide** (sí
  en el segundo, que es el que movió 562 → 563). Dicho de otro modo: **ningún tema publicado tiene
  preguntas pendientes de comprobar dentro del número que decide si pasa**, así que este arreglo no
  despublica ni baja del listón a ninguno. Si algún día lo tuviera, la regla ya escrita es la del §4: se
  queda publicado **con su cifra a la vista** y decide el propietario.
- **Los cuatro temas sin línea de puerta** (I.9, III.2, III.6 y IV.3) **siguen sin ella, y es correcto**:
  tienen **0 apartados**. La regla del §4 es para grupos **con apartado propio**; un tema sin nada escrito
  no tiene trabajo pendiente de comprobar, tiene trabajo pendiente de escribir, y su cifra la dice el
  panel con su motivo («todavía no tiene apuntes»). No es el «0 de 0» del §4 y no se ha tocado.

### 7. La volatilidad del denominador que el encargo pedía juzgar: **mejora**

El encargo pedía decir si el cambio **empeora o mejora** que «las cifras de un tema puedan moverse entre
dos medidas seguidas porque el denominador cambia solo cuando otro bloque escribe en la base». Se midió
con **dos instantáneas** separadas en el tiempo y las **dos** versiones del medidor sobre cada una:

| instantánea | medidor viejo (I.8) | medidor nuevo (I.8) |
|---|---|---|
| 1 | 261/**320** = 81,6 % | 261/**488** = 53,5 % (150 grupos pendientes) |
| 2 | 297/**367** = 80,9 % | 297/**488** = 60,9 % (113 grupos pendientes) |

**Mejora, y es el mecanismo lo que cambia**: el denominador del medidor viejo **se movió** (320 → 367)
porque otro bloque guardó comprobaciones —cada comprobación nueva metía su pregunta en el denominador—,
y el del nuevo **no se movió** (488 = 488). Con la regla del §4 el denominador lo decide **quién tiene
apartado propio con texto**, que no cambia cuando alguien guarda una comprobación; lo único que se mueve
es el numerador, y **hacia arriba** (261 → 297), que es lo que tiene que pasar cuando se hace el trabajo.

**Lo que no arregla, y se dice**: este cambio quita **una** de las causas de movimiento —la que dependía
de qué comprobaciones había guardadas en el instante de la lectura—, no todas. Una reescritura de los
apuntes, una reclasificación de preguntas o un tema nuevo corriendo siguen moviendo denominadores, y eso
es de los bloques que **escriben** en la base, no del medidor. La solución de fondo —medir siempre sobre
una copia congelada, como se ha hecho aquí para comparar— es una decisión sobre el procedimiento de
medida, no sobre el medidor, y no es de este encargo.

### 8. Las 18 puertas

**Medido el 15-oct-2026 sobre `6a13358`** (el código de `e824123` + los tres documentos de cierre), con la **guarda de mutación** puesta: `HEAD` y `git status --porcelain` comprobados **antes y después de cada puerta**, y las tres piezas declarando `arbol=limpio`. **18/18, en tres piezas** —no porque se saltara nada, sino porque la puerta 7 cayó **una vez por contención demostrada** y se reintentó—:

| Pieza | Puertas | Resultado | Registro |
|---|---|---|---|
| Batería completa | **1-6** | verdes | `F:\temp-opofuente\gates-f32-medidor-completa.txt` |
| ↳ la misma corrida | **7** | **rojo por contención**: `1 failed, 726 passed, 1 error` de 727, en **44:28** | ídem |
| Tramo 2 | **8-18** | **verdes**, en **00:05:31**: Vitest 43 ficheros/389 pruebas, los dos builds, migraciones, siembra y E2E **80/80** | `F:\temp-opofuente\gates-f32-medidor-tramo2.txt` |
| Tramo 3 | **7** (reintento) | **verde**: `727 passed in 2234.54s (0:37:14)` | `F:\temp-opofuente\gates-f32-medidor-tramo3.txt` |

**La contención está demostrada con su cifra**, no afirmada. En aislamiento sobre el **mismo** árbol: `test_classification.py` da **14/14 en 76,21 s** y `test_library_api.py` **16/16 en 70,75 s**, y las dos pruebas que cayeron —`test_classification.py::test_resolver_un_duplicado_queda_auditado_y_no_borra_nada` (`assert 'running' == 'succeeded'`) y el teardown de `test_library_api.py::test_el_diff_compara_dos_versiones_del_mismo_documento` (`InvariantViolationError: el trabajo pertenece a otro worker`)— dan **6/6 en tres vueltas**. La puerta 7 sola tarda **37-44 minutos**; las **once** del tramo 2 caben en **5:31**. Es el poste largo por naturaleza y el primero que se rompe cuando la máquina va cargada. **No se tocó ninguna prueba ni ninguna configuración.**

Cabeceras de procedencia (tomadas al arrancar, no reconstruidas después):

```
batería completa  ANTES fecha=2026-10-15T17:31:50+02:00  commit_medido=6a133584b7a13d2d1e156bcc1383406bc014e0af  main=e64c030cc22fb0afdfda8697e0a46bcd7bfa2ee0  arbol=limpio
tramo 2           ANTES fecha=2026-10-15T18:25:30+02:00  commit_medido=6a133584b7a13d2d1e156bcc1383406bc014e0af  main=b9a29239b41fd55b6a59a9e49a12d9d2644c6e03  arbol=limpio
tramo 3           ANTES fecha=2026-10-15T18:31:14+02:00  commit_medido=6a133584b7a13d2d1e156bcc1383406bc014e0af  main=b9a29239b41fd55b6a59a9e49a12d9d2644c6e03  arbol=limpio
```

Y una nota de instrumento que va aquí porque afecta a la procedencia: en la batería completa el `main` **sí se movió** durante la corrida —de `e64c030` a `b9a2923`, un commit del agente que corre las baterías que solo toca `docs/DEBT.md` y **cero líneas de código**—, pero la línea `DESPUES` de aquel registro lo decía mal, porque **reutilizaba el `main` del arranque en vez de releerlo**. El fallo es del lanzador, está **corregido** (la línea `DESPUES` vuelve a leer `main`), y queda **escrito en el propio registro** con las dos cifras. Ninguna puerta cambia de resultado: el commit medido no se movió en ningún momento.

### 9. Lo que queda fuera, con el porqué

- **No se ha escrito ni una fila en la base del propietario.** Toda la medición es de solo lectura, y esta
  vez ni siquiera sobre la base viva: sobre una instantánea. Coste de API: **0 $**.
- **No se ha corrido ningún tema, ni siquiera los afectados.** I.8 tiene 150 grupos pendientes de
  comprobar y ahora se ve; **comprobarlos cuesta dinero** y lo decide quien corra el tema, no este bloque.
  Con la regla nueva, correr I.8 (o I.4) **sí vuelve a contar** lo que compruebe: cada grupo que pase de
  pendiente a comprobado mueve el numerador y no el denominador.
- **Los informes por tema no se han tocado** (`docs/apuntes/INFORME-*.md`): el encargo de este bloque solo
  permite escribir en los tres documentos de seguimiento. La corrección de la cifra de I.8 está, por
  tanto, **en esta sección y en `PARA-EL-PROPIETARIO`**, no en su informe.
- **El caso «apartado propio vacío y sin comprobación» sigue como estaba**: un grupo cuyo apartado existe
  en la base pero **sin texto** (`resultado is None and firma not in sin_materia`) se sigue saltando. No
  es el caso del §4 —la regla habla de un grupo **con apartado**, y un apartado sin texto no es un
  apartado— y el trabajo que le falta es **redactar**, no comprobar. Queda dicho aquí y no se toca.
- **La cifra de I.8 se mueve sola mientras otros bloques trabajen**: lo medido en la instantánea 2 es
  `297/488 = 60,9 %` y en la 1 era `261/488 = 53,5 %`. Las dos son verdad y la diferencia es trabajo
  hecho. Por eso la tabla del apartado 5 lleva su fecha y su huella y no se presenta como un número
  eterno.

## F31 · La bandeja del propietario, agrupada por conjunto (15-oct-2026)

**Rama `f31-bandeja`** sobre `main = 5a62d0d`. Es código: **las 18 puertas están pendientes de correr**
(el encargo pide no lanzarlas hasta que el propietario dé el turno, porque hay tres baterías en marcha).
Lo que sí está hecho y medido, por piezas:

### La tabla del §1, medida en la base real (solo lectura, 15-oct-2026)

| Categoría | Incidencias | Conjuntos |
|---|---:|---:|
| `norma_cambiada` | 502 | — |
| `clave_sospechosa` | 173 | — |
| `pregunta_ambigua` | 106 | — |
| `hueco_sin_material` | 87 | — |
| `pregunta_mal_importada` | **0** | — |
| `clave_no_fiable` | **0** | — |
| **Total** | **868** (todas `open`) | **150** |

- La cifra de **603** del documento de cierre es de hace días: hoy hay **868**, y **88 más** de lo que
  decía. Por eso todo se ha contado otra vez en la base.
- **Oficiales** (`set_type='official_exam'`, 19 conjuntos): **24** incidencias, todas `pregunta_ambigua`;
  12 de ellas son falsos positivos del motor (la letra de los apuntes está en la clave).
- **La reclasificación del §2 (de `f18`) no se había ejecutado nunca sobre la base real**: por eso no
  hay ni una `pregunta_mal_importada` ni una `clave_no_fiable` escritas. Aplicada, deja: `clave_sospechosa`
  406 · `clave_no_fiable` 209 · falsos positivos **86** (salen) · `hueco_sin_material` 66 ·
  `pregunta_mal_importada` **61** (a «No son preguntas») · `pregunta_ambigua` 40.

### La cifra de la medida de éxito

| | Entradas de decisión real |
|---|---:|
| Antes (todas las incidencias, una a una) | **868** |
| Después de agrupar, de resolver por regla y de proponer en bloque | **146** |
| Conjuntos no oficiales con algo pendiente | 134 |
| Incidencias oficiales pendientes (una fila cada una) | 12 |

**146 < 150**, y el margen es corto: la cifra la mueven 1.295 incidencias que pueden aparecer en
cualquier corrida de apuntes. Queda dicho.

### Qué se ha construido

- **`domain/tray.py`**: la sección (oficial aparte), las tres acciones en bloque, el permiso y la regla
  de la cifra. Puro, sin base de datos.
- **`GET /notes-incidents/tray`**, **`GET /notes-incidents/tray/actions`** y
  **`POST /notes-incidents/tray/bulk`** (con `409` y su motivo para un conjunto oficial).
- **Migración `0039_bandeja_por_conjunto`**: dos estados nuevos (`propuesta_lista`, `no_son_preguntas`).
- **`opofuente.tools.resolver_bandeja`**: la resolución automática del §3 (reclasifica, descarta los
  falsos positivos, manda las mal importadas a «No son preguntas» y deja las derivadas en «propuesta
  lista»). Ensayo por defecto.
- **La pantalla**: sección «Exámenes oficiales» arriba y sin acciones, y «La bandeja por conjunto» con
  una fila por conjunto, su resumen, sus acciones y su despliegue.
- **Pruebas**: 12 unitarias del dominio y 5 de integración de la ruta (incluida la que rechaza tocar una
  clave oficial), 4 de componente y 2 specs E2E con capturas a 1280/390, axe y errores de consola. Las
  cuatro garantías tienen su **rojo previo** medido.

### Lo que queda fuera y por qué

- **Las 18 puertas**: se corren cuando el propietario dé el turno. El puerto 8765 lo necesitan tres
  baterías.
- **Aplicar la resolución a la base real**: `resolver_bandeja --aplicar` sobre una copia verificada. No
  se ha hecho: escribir en la base del propietario con tres baterías dentro no es reversible de verdad.
- **Los dos estados nuevos no los usa todavía el motor**: solo la resolución automática. Hasta que se
  ejecute, la bandeja enseña las 868 como `open`.

## F33 · El acabado de la interfaz: los cinco arreglos del §2, vistos en las capturas (16-oct-2026)

**Rama:** `f33-acabado` · **Base:** `main = 1caefb7` · **Encargo:** §2 de
`RECORRIDO-Y-ACABADO-2026-10.md`, tal como el propietario lo escribió **mirando sus capturas**. Nada de
esto es una opinión sobre el diseño: son cinco defectos que él vio.

**Nada fusionado.** Las 18 puertas las corre el bloque que mide.

### Los cinco arreglos, con lo que se mide

| # | Lo que vio | Lo que se ha hecho | La cifra |
| --- | --- | --- | --- |
| 1 | «el menú lateral no llega abajo: acaba a media pantalla» | el carril es la **columna** (se estira con la fila) y lo que viaja pegado es `.carril__interior` | carril **800 px** con la columna en **1.466,30** → ahora **1.466,30**. Y el píxel: `x=5` dejaba de ser blanco en `y=800` y ahora lo es hasta el final |
| 2 | «las notas salen como 0.0000 en vez de 0,00» | **un solo** módulo decide (`src/lib/numeros.ts`) y **todos** los sitios lo consumen | 7 sitios en 3 formatos distintos (punto-4-cifras, `toFixed(2)`, `toFixed(1).replace`) → 1 formato |
| 3 | «la pantalla de resultado abre con dos párrafos» | **una línea** + botón «¿Por qué estimada?»; los párrafos **no se borran**, se pliegan | la prueba exige el texto en el documento **y** `not.toBeVisible()` |
| 4 | «el resultado no muestra la hoja de respuestas ni Ver en apuntes» | `AnswerSheet` (diseño v0) arriba, con «bajar a la pregunta»; «Ver en apuntes» **al apartado** | `/temario/IV.7#el-modelo-tcp-ip-y-sus-capas`, resuelto por el servidor desde `question_note_anchors` |
| 5 | «indicadores de carga y el mismo estilo en todas las pantallas» | esqueleto a los **300 ms** en Temario, Progreso y Tema; un botón secundario, una etiqueta, un espaciado | 3 pruebas de esqueleto en rojo previo; axe **0** y consola **0** en las 8 capturas |

### La prueba, con su rojo previo

Se escribieron **antes** del arreglo y se corrieron contra el árbol sin él:

- **componente** (`vitest`): **10 fallos · 3 pasan** (guardado en `artifacts/acabado/rojo-unitario.txt`);
- **capturas** (`playwright`, el mismo guion a 1280 y 390): **3 fallos · 5 pasan** → después **8 pasan**;
- **la escalera de migraciones**: la lista a mano tenía **29** escalones y la cadena real de alembic
  **40** — **11 no estaban**, y son exactamente los que hacían caer la puerta 7 al añadir una migración.

### El §1 que se sumó a la tanda: la escalera, derivada

La prueba de la vuelta atrás de las migraciones **ya no tiene una lista escrita a mano**. Los escalones
salen de `ScriptDirectory.walk_revisions()` (la cadena, de la cabeza a la raíz) y las tablas que se lleva
cada bajada, del propio guion de la migración (`op.create_table`, resolviendo constantes de texto). Si un
nombre no se puede leer, la prueba **falla y lo dice** en lugar de comprobar menos de lo que cree. Con
eso, la migración nueva entra sola: `test_migrations_downgrade.py` pasa de 29 a 40 escalones y **9
pruebas en verde**.

### El §3.2 que se ha construido: `npm run screens -- --datos <dir>`

El otro punto que faltaba (§3, el recorrido con los datos reales) empieza por aquí. `--datos <carpeta>`
captura contra una **copia**, sin tocar la siembra: se mapea a `OPOFUENTE_E2E_DATA_DIR`, que es la
variable que `playwright.config.ts` **ya** respetaba y que **no** borra el directorio, y las capturas
salen a `artifacts/screens-datos` para no pisar las de la siembra. Al arrancar **dice contra cuál está
capturando**.

### Lo que se ha cambiado, fichero a fichero

- **API (5 ficheros + contrato)**: `StudentNoteAnchorSchema` en el resultado del alumno
  (`topic_code` + `anchor`), resuelto con una consulta nueva del repositorio que une
  `question_note_anchors` con `topic_note_sections` y solo acepta `result='covered'`. Contrato OpenAPI y
  tipos regenerados (`contracts:check` en verde).
- **Web (22 ficheros)**: `lib/numeros.ts` y `components/Esqueleto.tsx` nuevos; `ui/Disclosure.tsx` gana
  `Plegable`; `AppShell.tsx` parte el carril en dos; `ResultPage.tsx` junta los arreglos 2, 3 y 4;
  `answerSheetModel.ts` traduce el resultado a filas de la hoja; `global.css` unifica botón, etiqueta,
  estados y espaciado.
- **Pruebas**: 6 ficheros de componente nuevos (`numeros`, `acabadoResultado`, `acabadoTextos`,
  `cargaEsqueleto`, `capturasDatos`) y un guion de capturas nuevo (`tests/screens/acabado.spec.ts`,
  8 capturas). Dos pruebas viejas del formato del número, actualizadas **con su razón escrita dentro**.

### Lo que queda fuera y por qué

- **El recorrido con los datos reales (§3, el punto 7 del objetivo)**: no se ha hecho. Es el bloque
  siguiente; esta tanda deja construida la pieza que le hacía falta (`--datos`) y las capturas del
  acabado.
- **Las 18 puertas**: no las corre este bloque. Se han corrido las locales: `ruff format --check .` (558
  ficheros), `ruff check .`, `mypy` (261 ficheros), `eslint`, `tsc`, las **434** de componente, las
  **950** de unidad y contrato del backend y las **273** de alumno/estudio/migraciones.
- **Los colores de dentro de la hoja de respuestas** están comprobados por la prueba sobre la pantalla
  (`data-estado="correcta"` / `"fallada"`), no leyendo el PNG: esta máquina no ve imágenes.
- **La palabra «rojo»**: el detector la lee como el banco privado «Rojo» sin distinguir mayúsculas, así
  que el texto nuevo dice «el color del fallo». Queda anotado en `PARA-EL-PROPIETARIO.md` para que el
  propietario decida si el detector debería distinguir la mayúscula.

### El cierre de la puerta 18: las diez aserciones y la prosa del servidor

La puerta 18 dio **4 fallos / 79 pasan**, y las cuatro eran el mismo hecho: las pruebas E2E seguían
fijando el formato **viejo** del número. Buscadas **por patrón** y no por rojo, eran **diez**:

| fichero | líneas | lo que esperaban |
| --- | --- | --- |
| `keys.spec.ts` | 102, 123, 130, 133, 138 | `3 puntos`, `-1 puntos` y **`3 · Primera parte…`** |
| `study.spec.ts` | 178, 186, 191, 248, 357 | `-0.3333 (-1/3)`, `0 puntos`, `0.6667 (2/3)`, `-1 puntos`, `0.34 – 1.00` |

Una de ellas —`getByText('0 puntos')`— **no habría fallado nunca**: casaba con `0,00 puntos` porque lo
contiene como trozo. Es el caso que el aislamiento no ve. Y una onceava (`25.0`, con el `.` del regex
sin escapar) no habría cazado nunca un cambio de formato. Las once llevan su razón escrita dentro.

**Y la prosa del servidor**, que era el otro lado del mismo encargo: el frontend quedó unificado en
siete sitios y **la frase del servidor se quedó con el punto**, así que en la **misma fila** de la tabla
del diagnóstico convivían `0,34 – 1,00` (la columna, pintada por la pantalla) y `0.3424 a 1.0` (la nota
de esa fila). Se añade `apps/api/opofuente/domain/numeros.py` —el hermano de `src/lib/numeros.ts`— y
pasan por él las cuatro frases que lee una persona: la estimación de una parte (`0,33 sobre 50 … (25)`),
el mínimo publicado (`el mínimo de 25`), la nota del diagnóstico (`0,34 a 1,00`) y la cobertura del
panel (`489/542 = 90,2 %`, que es **como su propio docstring decía que se enseña**). `decimal_text` no se
toca: sigue siendo el decimal del contrato. Los identificadores y los informes de consola tampoco.

Medido: `ruff format --check .` (560 ficheros), `ruff check .`, `mypy` (262), `eslint`, `tsc`, **962**
de unidad y contrato del backend, **136** de integración de alumno/estudio/apuntes, **434** de
componente (433 en la corrida completa y 10/10 en aislamiento: el fallo era el `promote.test.tsx` de
siempre por carga) y la **puerta 18 entera: 83 pasan**. Las capturas del acabado, regeneradas.

---

## f35 — La lectura de los apuntes: un capítulo por pantalla (16-oct-2026)

**Base `main = c4a7d8d`, rama `f35-lectura`.** Es el **punto 1 del §3** de
`docs/REVISION-DEL-RECORRIDO-Y-ARREGLOS-2026-10.md`: los cinco defectos de la pantalla con la que se
estudia, medidos sobre una **copia verificada** de la base real (`F:\temp-opofuente\f35-datos`,
SHA-256 `622aaa6f…`; la real, con el mismo SHA-256 al terminar).

### Por qué esta pantalla y no otra

El recorrido la dejó la primera de la lista «por lo que más molesta a quien estudia», y con razón: es
**el índice y la página con los que se estudia**. Los tres defectos del §3.1 estaban medidos y los dos
del propietario, descritos. Todo lo de abajo está medido antes y después, con la misma copia y los
mismos dos anchos (1280 y 390).

### Las tres cifras

| Cifra | Antes | Después |
|---|---|---|
| Altura de la página del tema (1280 px) | IV.7 **110.427 px** · I.1 **314.402 px** | IV.7 **20.433** (capítulo IV.7.1) · I.1 **118.982** (capítulo I.1.1) |
| Ancho de la columna de texto (1280 px) | **370 px** | **647 px** (68 caracteres) |
| `scrollY` al pulsar «Ver en apuntes» | **0**, con el párrafo a **10.288 px** | **6.640**, con el párrafo arriba y a la vista |

Y el mismo enlace con un apartado del segundo capítulo (`#apartado-puertos`), que es el caso que
obliga a abrir el capítulo que lo contiene: **0 → 34.971 px** a 1280 y **0 → 61.022 px** a 390, con el
párrafo a 0 px de la ventana en los dos.

El índice, que era lo que más molestaba: **1.415 px / 1.405 px** `sticky` en una ventana de 800 —su
mitad de abajo no se alcanzaba ni desplazándose— pasa a **610 px / 752 px**, pegado y con su propio
scroll (446 px de recorrido en I.1). El 20.º apartado, que no se podía pulsar, ahora sí.

Las tablas: el ancho natural de las de los apuntes es mediana de **919 px** en IV.7 y **1.205 px** en
I.1 (máximo 3.295), así que **no caben** en una columna de lectura y cabían **partiendo las palabras**
(«Aplic|ación»). Ahora la tabla mide lo suyo (`max-content`) y **se desplaza su marco**: a 1280 se
desplazan 7 de 12 en IV.7 y 37 de 42 en I.1, y ninguna celda parte una palabra.

### Qué se ha tocado

- **Servidor** (`apps/api`): `GET /student/topics/{código}/notes` acepta `?capitulo=`; la respuesta
  trae `chapter` (el capítulo servido), `chapters` (el índice completo **sin los cuerpos** —lo que
  hace que el índice quepa y que un anclaje se pueda situar en su capítulo—) y `sections` con el texto
  del capítulo abierto. El anclaje de repaso (`StudentNoteAnchorView`) viaja con su `epigraph_code`.
- **Web** (`apps/web`): `TopicNotesPage` lee por capítulos (índice con scroll propio, capítulo y
  apartado en curso marcados, «Anterior / Siguiente», corrección de la dirección cuando el capítulo
  pedido ya no existe), `NotesBody` pinta cada tabla en su marco, `ResultPage` construye el enlace con
  el capítulo y el prefijo `apartado-`, y `global.css` trae la rejilla nueva. El efecto del ancla
  acepta el anclaje pelado (marcas del navegador de antes) y **revisa** la colocación cuando la página
  crece al cargar la fuente.

### Lo que no mejora, dicho por su nombre

**I.1.1 sigue midiendo 118.982 px**: el programa oficial da a la Constitución **cuatro** epígrafes y
los 21 apartados se reparten 12 / 5 / 2 / 2, así que el primer capítulo se lleva el **66 % del texto**.
Paginar por epígrafes es lo que se pidió; el capítulo que queda gordo es el que el programa define
como gordo. Si esa página sigue siendo incómoda, lo que hay que revisar es **la granularidad de los
epígrafes de I.1**, y eso es una decisión sobre el programa, no sobre la pantalla.

### Pruebas

- **Rojas antes, verdes después**: 8 de componente/contrato en la web (`studentApuntes` y
  `acabadoResultado`) y 7 en la API (`test_student_notes_api` 6 + `test_student_result_api` 1),
  capturadas con el código de `main` y estas pruebas encima.
- **Capturas y cifras**: `apps/web/tests/screens/lectura.spec.ts`, seis casos (IV.7, I.1 y el ancla ×
  1280 y 390), que exigen **0 violaciones de axe** y **0 errores de consola** y comprueban cada cifra
  de arriba. La corrida buena: **6 pasan**. Las cifras quedan en `artifacts/lectura/medidas.json` y el
  antes y el después en `artifacts/lectura/MEDIDAS.md`.
- **Locales**: `ruff check .` limpio, `ruff format --check .` (562 ficheros), `mypy` (262 ficheros)
  limpio, `eslint` limpio, `tsc` limpio, **453** de componente (todas) y las de API de apuntes,
  resultado y alumno/estudio.
- **Las 18 puertas no las corre este bloque** (las corre el que mide, con su protocolo).

---

## Tanda f39 — El repaso de fallos y los tres datos raros (17 oct 2026)

**De dónde sale.** `docs/REVISION-DEL-RECORRIDO-Y-ARREGLOS-2026-10.md` §2 y §3.6–3.7, con la
corrección del propietario: **repasar fallos no fallaba por falta de material, es un fallo del
programa**. Sin llamadas al modelo: **0 $**.

### 0. La copia verificada, y la real intacta

| | |
|---|---|
| la real | `F:\OpoFuente\datos\opofuente.sqlite3` · **2.748.612.608 bytes** · SHA-256 `a0a21413…c5aff8` **antes y después** |
| la copia | `F:\temp-opofuente\f39-datos\opofuente.sqlite3` · mismos 2.748.612.608 bytes · SHA-256 `622aaa6f…e3f238` |
| el archivo | `F:\temp-opofuente\f39-datos\backups\f39-004325.zip` · **811.750.195 bytes** · SHA-256 `e1698609…89a586` |
| método de la casa | instantánea con la API de respaldo de SQLite (origen en `mode=ro`) → ZIP con manifiesto y `force_zip64` → **`verify_archive`: sin problemas** → extracción → comprobaciones |
| la copia comprobada | `integrity_check` **ok** · `quick_check` **ok** · `foreign_key_check` **0 filas** · **65 tablas** · 671.048 páginas × 4.096 = el tamaño exacto · la extraída coincide con la instantánea (`622aaa6f…`) |
| migraciones | `0039_claves_derivadas → 0039_bandeja_por_conjunto → 0040_cuentas_y_consentimiento`, **14,3 s**, solo en la copia |
| la API | levantada contra la copia. **Puerto 8775**: el 8765 lo ocupa la batería de las 18 |

### 1. El repaso: Inicio dice N y el repaso sirve N

**Lo que había** (medido sobre la copia, con el código de `main`):

- `GET /student/overview` → `due_reviews` **5**.
- `POST /study-sessions` `mode=error_review` → **409**: «el repaso de q001 no sabe a qué parte del
  examen pertenece».
- `POST /student/tests` con `filter: failed` (el botón «Test con mis fallos») → **409**: «no hay
  ninguna pregunta que se pueda poner: … ninguna tiene plantilla activa con su respuesta».

**Por qué eran dos políticas.** La práctica por conjuntos y la práctica por tema aceptaban **clave
derivada** (`0039`) además de la plantilla activa; el repaso exigía plantilla `active` y, encima, una
parte declarada. Y el contador de Inicio contaba `review_items` vencidos **sin preguntar si se podían
corregir**.

**Lo que hay ahora**, con `infrastructure/key_policy.py` como única fuente de la regla:

| | antes | después |
|---|---|---|
| `due_reviews` de Inicio | **5** | **1** |
| preguntas que sirve la sesión de repaso | **0** (409) | **1** |
| las dos cifras coinciden | no | **sí** |
| lo que el repaso dice haber dejado fuera | — | 4, con su motivo, en la nota de la sesión |

**Por qué 1 y no 5, con los cinco nombres.** De las cinco vencidas, cuatro son del conjunto
`b9798368` —una **segunda copia** del INAP 2025 modelo A que el importador dejó archivada— y su única
plantilla está en `superseded`: **ninguna sesión puede corregirlas**, ni el repaso ni un test. La
quinta es de un banco privado con plantilla activa y su entrada, pero la práctica en la que se falló
no declaró parte; antes eso abortaba el repaso entero y ahora se corrige al momento, como una práctica
por tema. Prometer 5 sería prometer lo que la corrección no puede dar. Queda en **DEBT-035** con su
criterio de cierre.

**La prueba** (`apps/api/tests/integration/test_repaso_servible.py`, 4 casos):

1. **la cifra de Inicio es la que el repaso sirve** — dos fallos vencidos, uno corregible: Inicio dice
   1 y el repaso sirve 1. Con la política vieja falla en la primera línea (contaba 2);
2. el fallo sin clave **no se cuenta ni se ofrece** (`servable_total`) y la pantalla dice por qué;
3. **un fallo con clave derivada se puede repasar** — conjunto en cuarentena, derivada de dos fuentes
   independientes, y la pregunta se congela con la letra derivada (`("b",)`), no con la del banco;
4. la fila del examen cuenta lo que el examen tiene (85 preguntas de conjunto → **80** servidas).

Y la política se comprueba contra sí misma: el caso 1 saca las dos cifras de sitios distintos —el
contador, en SQL, y la sesión, por el motor— y tienen que dar lo mismo.

### 2. Los tres datos raros

**2.1 · El 135 contra el 85: de dónde salía.** **No era un error de importación.** El conjunto del
INAP de ingreso libre trae **135 versiones vigentes: 115 ordinarias y 20 de reserva**, y así las
publica el cuestionario. El examen sirve **85** porque la convocatoria de TAI publica **80 ordinarias
+ 5 de reserva** para su primera parte y `_preguntas` toma esas. La fila contaba las del conjunto;
ahora cuenta las que el examen tiene, con la **misma** regla que lo monta
(`StudyService.exam_size`).

| fila | antes | después |
|---|---|---|
| INAP ingreso libre (×7) | 135 | **85** |
| INAP promoción interna (×6) | 85 | **79** |

Y por el camino salió otra mentira de la misma fila: los seis de promoción interna **no se pueden
montar** —74 ordinarias para una parte de 80— y la fila ofrecía el botón, que contestaba 409. Ahora
dicen **79** y el motivo por su nombre (`faltan_preguntas`); los dos sin plantilla activa dicen
`faltan_respuestas`. Queda en **DEBT-036**.

**2.2 · La fecha de los 13 exámenes.** **13 de 13 tienen fecha ahora**, y es **el año**, sacado del
título —que el importador copió del propio documento—: «TAI ingreso libre 2019 …» → 2019. **No hay
día en el origen**: comprobado abriendo los PDF, la cabecera rotula `2025 - TAI-L (MODELO A)`,
`2022 - TAI-P`, `2024 - TAI-P · MODELO A` y el `2019` va en el pie; las fechas completas que aparecen
en el texto son **citas de normas** —«27 de abril de 2016», el RGPD—, no la del examen. La fecha de
celebración la anuncia el órgano de selección aparte. Por eso `held_at` sigue vacío —poner un 1 de
enero sería inventarse el día y el mes— y la fila enseña «**Ejercicio de 2019**». Un título que no
declare año diría «Sin fecha publicada: el documento de origen no la declara».

**2.3 · Los 28 `[]`, separados por caso.** Medidos sobre el texto crudo de las 28:

| caso | cuántas | qué es | qué se hace |
|---|---|---|---|
| **hueco de una frase para completar** | **21** | todas del conjunto «B4 - ::Modelo OSI»: «los cambios en una capa deben ser **[]** para el resto de niveles» | se enseña **`_____`** |
| **corchete de código** (`int[][]`, `float[] saldoMensual`, `notas[] = {…}`, `int v[]={…}`, `String[] args`) | **7** | POO (2), Java/Jakarta (1), MUCHOS_TESTS (1), Tai_BBDD_2025 (1), baquedano (1) y el supuesto práctico de 2006 (1) | se queda **como está**: convertirlo daría `int_____` |

La regla es una sola y está en `domain/questions.py`: un `[]` es hueco cuando **no cuelga de una
palabra**. Las 28 están en la prueba del dominio, una por una (`HUECOS_DEL_PROPIETARIO`, 28 casos
parametrizados). **No se ha reescrito el material**: el arreglo es de lectura, en la capa del alumno
(la pregunta del test, el resultado y la lista de fallos).

### 3. Lo que se ha tocado

- **nuevo** `infrastructure/key_policy.py` — la política de claves, en SQL y una sola vez.
- `study_service` — la usan los tres sitios que eligen preguntas; el repaso ya no exige parte;
  `exam_size` para la fila del examen.
- `student_repository` / `question_repository` — el contador, los fallos y el tamaño de la fila.
- `student_service`, `student_schemas`, `routes/student` — `held_year`, `blocked_reason`,
  `servable_total`, los huecos y el año.
- `domain/questions.py` — `mostrar_huecos` y `ano_del_titulo`.
- web — la fila del examen (año y motivo) y el botón de fallos (solo si hay algo que corregir).
- contratos regenerados (`openapi.json` y `openapi.d.ts`).

### 4. Las puertas, en local

`ruff check .` limpio · `ruff format --check .` (564 ficheros) · `mypy` (263 ficheros) limpio ·
`eslint` limpio · `tsc` limpio · `build:web` construido · **457 pruebas de componente (53 ficheros)**
· las de API de alumno, estudio, repaso, claves derivadas y el dominio de preguntas. **Las 18 no las
corre este bloque**: las corre el que mide.

### 5. Lo que queda fuera, con su porqué

- **DEBT-035**: los cuatro repasos que apuntan al conjunto duplicado archivado. Se podrán contar y
  servir cuando el importador no deje dos copias del mismo examen o el historial se repunte; la
  decisión es del propietario.
- **DEBT-036**: los seis exámenes de promoción interna con 74 preguntas para una parte de 80: o falta
  material o la parte que se juega es otra.
- **El `[]` del material no se reescribe** (decisión del 17-oct): el arreglo es de lectura.

