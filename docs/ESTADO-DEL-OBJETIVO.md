# Estado del objetivo largo (TAI: los 33 temas y la app de estudio)

**Autoridad:** `docs/GOAL-DEEPSEEK-TRABAJO-LARGO-2026-10.md` · **Presupuesto de API:** 40 $ · **Se
avisa cada 10 $** · Última actualización: **11 oct 2026 (tanda f13: la zona del alumno estrena el
diseño —Inicio, Temario y los apuntes en tres columnas—, los tokens viven en un solo sitio y el botón
«Esto está mal» guarda el aviso de verdad, auditado y en la ruta que leerá la bandeja del
propietario; sin gastar API)**.

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

*(f13 no llama al modelo a propósito: es el bloque de interfaz y de la ruta de escritura de los
avisos. Las únicas llamadas de esta tanda fueron las de las herramientas locales —pytest, Playwright,
eslint—, que no cuestan.)*

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
  de f13 = **≈5,23 $**) el aviso de los 10 $ **sigue sin cruzarse**.

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
| resto (30) | sin empezar | | | | | | | |

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
6. **La zona del alumno va por la mitad**: desde f13 están la pantalla del test (f11), **Inicio**,
   **Temario** y **Tema con apuntes** —con el **sistema de diseño aplicado** (§3.7: tokens en un
   fichero único y las dos fuentes autoalojadas) y el aviso «Esto está mal» guardando de verdad por su
   ruta auditada—. Faltan **Resultado, Simulacros, Exámenes oficiales, Fallos y Progreso** (pasos 3, 6
   y 7 del §3), y dentro del tema, las pestañas «Preguntas» y «Mi progreso» —hoy son enlaces a su
   dirección, que llega en el bloque siguiente—, el buscador dentro del tema y la marca de leído del
   índice. La **bandeja del propietario** para los avisos del alumno tiene su ruta de lectura
   (`GET /notes-reports`) pero no su pantalla: es el bloque C.
7. **`GET /student/official-exams`**: los exámenes del INAP tienen que importarse antes (D10) para
   poder listarse con su nota. Hoy listarlos sería listar conjuntos internos.
8. Los **30 temas restantes** y los bloques C (panel) y D (datos: copias, epígrafes, INAP) siguen sin
   empezar, con D5 (copias verificadas) como primer paso del §6 del objetivo.
9. **Tres violaciones de accesibilidad en el panel** (`scrollable-region-focusable` en `/cambios` y en
   `/buscar` a 390 px) que aparecen al fotografiar las pantallas del propietario **con los datos
   reales**: son regiones que se desplazan y no se pueden recorrer con el teclado. No son de este
   bloque —las pantallas del alumno salen a 0— y se arreglan con el mismo remedio que se aplicó a las
   tablas de los apuntes (`tabindex` y nombre), pero tocan el panel: quedan anotadas para él.
