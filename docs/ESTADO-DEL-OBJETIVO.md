# Estado del objetivo largo (TAI: los 33 temas y la app de estudio)

**Autoridad:** `docs/GOAL-DEEPSEEK-TRABAJO-LARGO-2026-10.md` · **Presupuesto de API:** 40 $ · **Se
avisa cada 10 $** · Última actualización: **10 oct 2026 (tanda f10: los tres arreglos del motor de
apuntes, IV.7 otra vez, I.6 e I.1)**.

> Este fichero lo abrió la tanda **f10**: hasta entonces no existía, así que el gasto acumulado de las
> tandas anteriores **no está medido aquí** (no hay registro del que heredarlo). Todo lo que se dice
> abajo está medido con los tokens que devolvió cada llamada; el coste es una estimación con la tabla
> de precios del proyecto (valle), no la factura.

## 1. Gasto de API

| Concepto | Llamadas | Entrada | Salida | Coste estimado |
|---|---|---|---|---|
| f10 · IV.7 (corrida + dos intentos de corrección) | 99 | 1.924.837 (1.600.384 de caché) | 586.589 | **0,6407 $** |
| f10 · I.6 (corrida + intento de corrección + un apartado) | 76 | 869.184 (530.688 de caché) | 867.672 | **0,6509 $** |
| **Total de la tanda f10** | **175** | **2.794.021** | **1.454.261** | **1,2916 $** |
| Presupuesto restante del objetivo | — | — | — | 40 $ − (lo anterior, sin registrar) − 1,29 $ |

**Aviso de los 10 $:** **no se ha cruzado** con esta tanda (1,29 $). El dato que falta para saber si
el objetivo va por la mitad es el **acumulado anterior**, y no está registrado en ninguna fuente: este
fichero no existía y ningún otro documento lleva la cuenta. Es lo primero que hay que arreglar en la
tanda siguiente (una línea de gasto por corrida).

## 2. Los 33 temas

| Tema | Estado | Hechos | Apartados | Cubiertas (grupos) | Conflictos | Dudosas de apuntes | Puertas de forma |
|---|---|---|---|---|---|---|---|
| **IV.7** | **publicado** (versión archivada) | 956 → 722 redactados | 25 | 423 de 473 (**89,4 %**) | 10 | 0 | **PASA las cinco** |
| **I.6** | **borrador** (no llega al 90 % de cobertura) | 346 → 299 redactados | 13 | 125 de 191 (**65,4 %**) | 45 | 0 | **PASA las cinco** |
| **I.1** | **índice en borrador, no se redacta** | 3.509 | 15 (borrador) | — | — | — | no pasa las comprobaciones del índice |
| resto (30) | sin empezar | | | | | | |

### IV.7, medido pregunta a pregunta (527 preguntas)

| Desenlace | Con clave activa | Con clave en borrador | Sin clave | Total |
|---|---|---|---|---|
| Cubierta | 160 | 275 | 17 | 452 |
| En conflicto con la clave | 8 | 5 | 0 | 13 |
| Dudosa (incidencia de clave) | 25 | 37 | 0 | 62 |

- **Con clave (activa o en borrador): 510.** Cubiertas 435 → **85,3 %**.
- **Con clave que el motor no ha señalado como contraria a la norma: 470.** Cubiertas 435 →
  **92,6 %**. Las 40 que quedan fuera de esa cuenta son las que el paso B marcó: ahí la letra no
  puede decidir por diseño (una clave que se sabe mala no convierte un acierto en un fallo), y las 40
  tienen su incidencia con su motivo.
- **Todas las preguntas no cubiertas tienen categoría de incidencia**: 50 en la bandeja del
  propietario — 40 `norma_cambiada` y 10 `clave_sospechosa`, con la frase verificada que las sostiene
  cuando la hay.

### I.6 (191 grupos, 303 preguntas)

- Cobertura **65,4 %** (125 de 191 grupos); 45 conflictos de letra, 21 incidencias de clave (20 con la
  clave señalada por el paso B) y **0 dudas por los apuntes**.
- Bandeja del propietario: **66 incidencias** — 45 `clave_sospechosa`, 20 `norma_cambiada` y 1
  `pregunta_ambigua`.
- No llega al 90 % de cobertura, así que **se queda como borrador con su motivo** (§2.2.7): lo que
  falta es de la clave (65 de las 66 incidencias son de clave o de conflicto, no de apuntes), no de
  escribir más.

## 3. Los tres arreglos del motor (§2.1), con su prueba

| Arreglo | Qué hacía antes | Qué hace ahora | Prueba que falla antes |
|---|---|---|---|
| 1. Un hecho va al apartado de **su materia** | El reparto iba por la pregunta: el apartado de UDP hablaba de la cabecera de IPv6, de ARP y de ICMP | El texto del hecho decide; la pregunta es el respaldo cuando el texto no reconoce ninguna materia. El ancla de una pregunta admite **varios** apartados | `test_un_hecho_va_al_apartado_de_su_materia_y_no_al_de_su_pregunta`, `test_una_pregunta_puede_anclarse_en_varios_apartados`, `test_una_palabra_que_esta_en_media_asignatura_no_le_gana_a_la_de_una_materia` |
| 2. La tabla de puertos, **por familias y sin avisos de opciones falsas** | 47 filas seguidas con «No es DynamoDB», «No es MySQL»… | Una tabla por familia, ordenada, sin notas de distractor y con las confusiones de verdad en «Confusiones que caen» | `test_una_tabla_de_puertos_se_parte_por_familias`, `test_las_notas_que_solo_dicen_lo_que_un_puerto_no_es_se_van`, `test_la_puerta_de_forma_exige_la_tabla_partida_y_sin_notas_de_distractor` |
| 3. **Bucle de huecos** y bandeja del propietario | El resto se contaba en el informe y se perdía al cerrar la terminal | Una vuelta más de añadido para los huecos y, lo que siga sin resolverse, a la bandeja con su categoría y su frase | `test_lo_que_queda_sin_cubrir_recibe_la_categoria_de_quien_lo_arregla`, `test_el_detalle_de_una_clave_sospechosa_lleva_la_frase_que_lo_demuestra` |

Medido en IV.7 con el motor arreglado: **24 notas de distractor retiradas**, **22 confusiones** en su
bloque, **4 familias** (servicios de red, correo, bases de datos, escritorio remoto y otros), **0
puertos repetidos** y **0 notas sin sentido**. El apartado de UDP pasó de 16 hechos —con la cabecera
de IPv4, 127.0.0.1, ARP, IPv6 e ICMP— a **8, todos de UDP**.

Y una cuarta cosa que hacía falta para que el arreglo se **viera**: un apartado cuya clave no cambia
pero **pierde hechos** se vuelve a redactar (su texto se escribió con otros hechos). Sin eso, IV.7
quedaba con el texto viejo y solo cambiaban las comprobaciones.

## 4. Lo que queda abierto

1. **El acumulado de gasto anterior no existe.** No hay fuente de la que heredarlo; hay que empezar a
   llevar la cuenta por corrida desde ya.
2. **I.1 no se puede redactar todavía.** Su índice por materias está en borrador y **no pasa sus
   propias comprobaciones**: cuatro apartados se pasan de 150 hechos y **295 preguntas (de 2.006) no
   casan con ninguna materia** —enunciados cortos sin artículo ni institución («Una de las siguientes
   afirmaciones es falsa», «Los acuerdos adoptados, para ser válidos»)—. Hacen falta más patrones o
   mandarlas a la cola de clasificación, y eso es trabajo de contenido.
3. **Dos puertas del §2.3 no están medidas ni automatizadas en el comando**:
   - «hechos fuera de su materia (≤ 3 %)», que el §2.1.1 pide con el modelo clasificando cada hecho
     de un apartado. Lo determinista sí está probado: cada hecho acaba en el apartado de lo que
     afirma, y los cuatro casos del propietario están cubiertos por prueba;
   - **la cobertura ≥ 90 %**: `--exigir-calidad` solo mira las cinco comprobaciones de forma, así que
     archivó la versión de I.6 (que pasa la forma) aunque su cobertura es del 65,4 %. Decidido **no**
     cambiar el comando en esta tanda (habría convertido IV.7 en borrador, contra la lectura del
     propietario) y dejarlo escrito aquí para decidirlo con él.
4. Los **30 temas restantes** y los bloques B y C siguen sin empezar, como estaba previsto.
