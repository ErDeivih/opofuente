# Estado del objetivo largo (TAI: los 33 temas y la app de estudio)

**Autoridad:** `docs/GOAL-DEEPSEEK-TRABAJO-LARGO-2026-10.md` · **Presupuesto de API:** 40 $ · **Se
avisa cada 10 $** · Última actualización: **11 oct 2026 (tanda f11: la bandeja de I.6 con sus frases
verificadas, la puntuación estimada y la composición única —`compose`— con el test de varios temas, el
simulacro y su pantalla)**.

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

Tres avisos para que nadie sume mal:

- **una corrida intermedia de la puerta de IV.7 no quedó registrada** (su salida se perdió al cerrar
  el proceso). Fue del mismo orden que las otras dos de puerta, unos céntimos: el acumulado real de
  f10 es **≈1,31 $**, no una cifra exacta;
- **dos corridas de f11 se lanzaron a la vez por error** y una se mató a los tres minutos, antes de
  escribir nada en la base ni de llamar al modelo con resultado: el gasto de f11 es el de la tabla;
- **el acumulado del objetivo no se puede dar.** Lo anterior a f10 no está en ninguna fuente. Con lo
  medido (≈1,31 $ de f10 + 0,4411 $ de f11 = **≈1,75 $**) el aviso de los 10 $ **no se ha cruzado**.

## 2. Los 33 temas

| Tema | Estado | Hechos | Apartados | Puerta de cobertura (clave utilizable) | Sobre todas las claves | Conflictos | Dudosas de apuntes | Forma |
|---|---|---|---|---|---|---|---|---|
| **IV.7** | **publicado** (versión archivada) | 958 → 724 redactados | 25 | **430/449 = 95,8 % PASA** | 430/511 = 84,1 % | 17 | 0 | **PASA las cinco** |
| **I.6** | **borrador con su motivo** (versión retirada) | 346 → 299 | 13 | **166/258 = 64,3 % NO PASA** | 166/283 = 58,7 % | 28 | 25 | **NO PASA** (18.666 palabras de 13.840; repetidos 12,9 %) |
| **I.1** | **índice en borrador: no se redacta** | 3.509 | 15 (borrador) | — | — | — | — | no pasa las comprobaciones del índice |
| resto (30) | sin empezar | | | | | | | |

*(Cifras de I.6 medidas el 11-oct en su propia corrida, sobre la base real. **El texto de I.6 cambió
entre la corrida de f10 y esta**: al empezar f11 sus apartados sumaban 79.495 caracteres y su
comprobación citaba frases que ya no estaban en ellos; la corrida de f11 los encontró reescritos
—111.000 caracteres, escritos por otra tanda que trabaja en la misma base, como avisa el §4— y
recomprobó las 191 preguntas contra ese texto. Por eso las cifras de I.6 no son las de f10: no es que
el tema haya empeorado, es que **el texto que se mide es otro**. La puerta de forma, además, ahora no
la pasa.)*

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
- **I.6**: 166 de 258 = **64,3 %** con (b) → **NO PASA**. Con (a), 166 de 283 = 58,7 %. No llega con
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

### I.6 (191 grupos, 303 preguntas), medido el 11-oct

Cobertura **64,3 % con (b)** y 58,7 % con (a); **28 conflictos de letra**, 25 preguntas sin frase en
los apuntes, 20 incidencias de clave marcada por el paso B y 8 sin clave con la que comprobar; banda
de la bandeja: **81 incidencias** (38 `clave_sospechosa`, 20 `norma_cambiada`, 15
`hueco_sin_material` y 8 `pregunta_ambigua`). La puerta de forma **no la pasa** (18.666 palabras de
13.840; párrafos repetidos 12,9 %). **Se queda en borrador**, y con estos números no es por las
frases: 58 de sus 81 incidencias son de la clave, no de los apuntes.

**Y lo que faltaba de la tanda anterior ya está: la frase que demuestra cada conflicto.** Medido
después de la corrida, con la misma comprobación que usa el motor (`verificar_cita` contra el texto de
los apuntes por epígrafe):

| Qué se mide | Antes de f11 | Después de f11 |
|---|---|---|
| Frases de la bandeja (`clave_sospechosa`) que están **de verdad** en los apuntes de hoy | **2 de 45** | **38 de 38** |
| Anclas de conflicto cuya cita está en los apuntes de hoy | **2 de 88** | **70 de 70** |

## 3. Los arreglos del motor (§2.1), con su prueba

| Arreglo | Qué hacía antes | Qué hace ahora | Prueba que falla antes |
|---|---|---|---|
| 1. Un hecho va al apartado de **su materia** | El reparto iba por la pregunta: el apartado de UDP hablaba de la cabecera de IPv6, de ARP y de ICMP | El texto del hecho decide; la pregunta es el respaldo si el texto no reconoce ninguna materia. El ancla de una pregunta admite **varios** apartados | `test_un_hecho_va_al_apartado_de_su_materia_y_no_al_de_su_pregunta`, `test_una_pregunta_puede_anclarse_en_varios_apartados`, `test_una_palabra_que_esta_en_media_asignatura_no_le_gana_a_la_de_una_materia` |
| 2. La tabla de puertos, **por familias y sin avisos de opciones falsas** | 47 filas seguidas con «No es DynamoDB», «No es MySQL»… | 4 tablas por familia, ordenadas, sin notas de distractor, y las confusiones de verdad en «Confusiones que caen» | `test_una_tabla_de_puertos_se_parte_por_familias`, `test_las_notas_que_solo_dicen_lo_que_un_puerto_no_es_se_van`, `test_la_puerta_de_forma_exige_la_tabla_partida_y_sin_notas_de_distractor` |
| 3. **Bucle de huecos** y bandeja del propietario | El resto se contaba en el informe y se perdía al cerrar la terminal | Una vuelta más de añadido para los huecos y, lo que siga sin resolverse, a la bandeja con su categoría y su frase | `test_lo_que_queda_sin_cubrir_recibe_la_categoria_de_quien_lo_arregla`, `test_el_detalle_de_una_clave_sospechosa_lleva_la_frase_que_lo_demuestra` |
| 4. **(f11) Una comprobación caduca cuando el apartado se reescribe** | La comprobación se guardaba con la cita y **se reutilizaba por la firma del grupo**: si el texto se rehacía, la bandeja seguía enseñando una frase que ya no estaba en los apuntes | Cada comprobación guarda la **huella** (`sha256`) del texto contra el que se verificó (migración `0032`), y solo se reutiliza si el texto de hoy tiene esa huella. Una fila sin huella (las de antes) se vuelve a comprobar | `test_una_comprobacion_caduca_cuando_el_apartado_se_reescribe` (falla con la regla vieja: la segunda corrida no volvía a comprobar) |

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

## 5. Lo que queda abierto

1. **El acumulado de gasto anterior a f10 no existe** y ya no se puede medir. Desde aquí se anota una
   línea por corrida (§1).
2. **I.1 no se puede redactar todavía.** Su índice por materias está en borrador y **no pasa sus
   propias comprobaciones**.
3. **La puerta «hechos fuera de su materia (≤ 3 %)»** del §2.3 sigue sin implementar.
4. **I.6 está en borrador con dos motivos**: la cobertura (64,3 %) y ahora también la forma (18.666
   palabras de 13.840, repetidos 12,9 %). Su texto lo rehizo otra tanda mientras esta trabajaba: hay
   que decidir si se vuelve a redactar con el tope de extensión del §2.1 o si se deja como está.
5. **La pantalla del test es la primera de la zona del alumno**: faltan Inicio, Temario, Tema con
   apuntes, Resultado, Simulacros, Exámenes oficiales, Fallos y Progreso (§3 del objetivo, pasos 3–6),
   y los **tokens del diseño** (§3.7: las fuentes autoalojadas y el cambio de los colores de toda la
   aplicación). En f11 solo se han añadido los tokens de la hoja como tokens **nuevos**, sin tocar los
   del panel.
6. **`GET /student/official-exams`**: los exámenes del INAP tienen que importarse antes (D10) para
   poder listarse con su nota. Hoy listarlos sería listar conjuntos internos.
7. Los **30 temas restantes** y los bloques C (panel) y D (datos: copias, epígrafes, INAP) siguen sin
   empezar, con D5 (copias verificadas) como primer paso del §6 del objetivo.
