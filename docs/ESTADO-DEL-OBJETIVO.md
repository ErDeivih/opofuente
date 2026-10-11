# Estado del objetivo largo (TAI: los 33 temas y la app de estudio)

**Autoridad:** `docs/GOAL-DEEPSEEK-TRABAJO-LARGO-2026-10.md` · **Presupuesto de API:** 40 $ · **Se
avisa cada 10 $** · Última actualización: **11 oct 2026 (tanda f15: los temas se eligen por valor
medido —cuántas preguntas con clave utilizable—, se escriben **I.2** —publicado— e **I.4** —en
borrador con su motivo—, y el motor gana la previsión de coste de `--prever`, la limpieza del
encabezado que repite el título de otro apartado y un **tope de tiempo para la corrida entera**)**.

> **De las fechas:** la tanda anterior se etiquetó «11 oct» en este fichero, pero **su reloj, sus
> ficheros y sus marcas de base son del 10 de octubre** (la corrida de I.6 acabó a las 18:09 del
> 10-oct). Las etiquetas iban por delante. Esta tanda (f13) sí es del **11 de octubre**: empezó a las
> 11:20 y el reloj de la máquina marca 14:22 al escribir estas líneas.

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

*(f13 no llama al modelo a propósito: es el bloque de interfaz y de la ruta de escritura de los
avisos. f14 tampoco: es interfaz y consultas de lectura sobre la base; lo único que se ejecuta son las
herramientas locales —ruff, mypy, pytest, Vitest, Playwright—, que no cuestan. Las únicas llamadas de
las dos tandas fueron las de esas herramientas.)*

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
  de f13 + 0,00 $ de f14 + 2,6812 $ de f15 = **≈7,91 $**) el aviso de los 10 $ **sigue sin
  cruzarse**.

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
| resto (28) | sin empezar | | | | | | | |

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

### La tabla que decide qué tema se escribe primero (medida sobre la base real, 11-oct)

No es el orden del temario ni el de ningún documento: es, por cada tema, **cuántas preguntas tienen
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
   Faltan la pantalla de **Tests** (elegir temas, cuántas preguntas y cómo se corrigen: pasos 3 y 4 del
   §3) y, dentro del tema, las pestañas «Preguntas» y «Mi progreso» —hoy son enlaces a su dirección—,
   el buscador dentro del tema y la marca de leído del índice. La **bandeja del propietario** para los
   avisos del alumno tiene su ruta de lectura (`GET /notes-reports`) pero no su pantalla: es el bloque C.
7. **Los exámenes del INAP**: la pantalla existe y lee de la API, y hoy sale **vacía** porque no hay
   ninguno importado (D10). Lo que falta es la importación, no la pantalla: cuando los 32 PDF de
   `F:\OpoFuente\fuentes\inap-tai\` entren con su manifiesto, saldrán en la lista con su fecha, su
   número de preguntas y su botón, y el que no tenga plantilla activa dirá que todavía no se puede
   hacer en lugar de ofrecer un examen que falla. La ruta `POST /student/official-exams/{posicion}/sessions`
   ya está probada con un examen de verdad montado por la API (§4c)
8. Los **28 temas restantes** y los bloques C (panel) y D (datos: copias, epígrafes, INAP) siguen sin
   empezar, con D5 (copias verificadas) como primer paso del §6 del objetivo. En f15 se les ha puesto
   **orden de valor**: la tabla de preguntas con clave utilizable de cada tema es la que decide qué se
   escribe primero, y está abajo. **IV.2 (el 3.º, 797 preguntas con clave) tiene ya su índice escrito
   y probado** (`domain/catalogo_iv_2.py`, 13 apartados, 761 de sus 770 grupos situados por el
   enunciado): la próxima tanda empieza redactándolo, sin volver a decidir el árbol.
9. **Dos listones que no coinciden entre el documento y el código**, medidos en I.4 y anotados sin
   tocarlos (el §1.2 pide no relajar la puerta):
   - **párrafos casi repetidos**: el §2.3 pide **≤ 3 %** y el código lleva el tope al **5 %**
     (`MAX_PARRAFOS_REPETIDOS = 0.05`). I.4 está en 4,2 %: pasa el código y no el documento. O se baja
     el del código al 3 % (y entonces I.4, I.1 —2,2 %— y IV.7 siguen pasando, pero hay que volver a
     medir todos) o se sube el del documento al 5 %;
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
   reales**: son regiones que se desplazan y no se pueden recorrer con el teclado. No son de este
   bloque —las pantallas del alumno salen a 0— y se arreglan con el mismo remedio que se aplicó a las
   tablas de los apuntes (`tabindex` y nombre), pero tocan el panel: quedan anotadas para él.
