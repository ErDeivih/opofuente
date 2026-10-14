# Informe de II.2 — Periféricos, impresión, almacenamiento y visualización · 14-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0037_origin_scope`). Corrida lanzada el 14-oct a
las 13:01, **muerta con el turno del agente** a los ~34 minutos (ver §2) y **reanudada a las 13:40**
hasta cerrar. Vigésimo segundo tema por valor de la tabla **vuelta a medir hoy** con la cuarentena
puesta (**172** claves utilizables). **PUBLICADO**: pasa las dos puertas con **163/165 = 98,8 %** de
cobertura sobre clave utilizable, **la mejor de toda la serie**.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **17**, por asunto dentro de sus cuatro epígrafes |
| Grupos situados por el enunciado (ensayo) | **172 de 175 = 98,3 %** |
| Techo medido de cobertura (`sin_materia_con_clave.py`) | **169/172 = 98,3 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **0 y 0** |

Solo **3 grupos** quedaron fuera del índice, y son tres enunciados sin sujeto («señale la respuesta
correcta (diferenciador)», «de las siguientes afirmaciones, señale la INCORRECTA», «indique cuál de
las siguientes es la afirmación correcta»). No se lavan: van a la bandeja.

**Cuatro correcciones del ensayo antes de pagar (0 $)**: las preguntas del interfaz de 16 Gbps, de
la tecnología de disco por bus serie, del almacenamiento en disco y de la impresión más económica se
quedaban sin apartado por no nombrar su materia con las palabras que el catálogo esperaba; y el patrón
de la NTI de digitalización se dejó **fuera a propósito**, porque es de **I.8.4**.

**Las dos lecciones de la tanda anterior, aplicadas antes de correr** (y comprobadas con una cuenta,
no a ojo): los títulos de los 17 apartados **no comparten las tres primeras palabras entre tres de
ellos** —lo que dejó II.3 sin publicar— y none de los patrones propios es una palabra genérica
(«velocidad», «estándar», «puerto» y «dispositivo» salen en casi todos los enunciados y no deciden
nada).

## 2. La corrida que murió con el turno, contada con su cifra

| | |
|---|---|
| Lanzada | 13:01:17 |
| Muerta | ~13:35, **con el turno del agente** |
| Lo que dejó escrito | **325 hechos, los 17 apartados y 53 de 175 comprobaciones** (nada perdido) |
| Su coste | **no medido**: `corrida-II.2-1.out.txt` quedó a **0 bytes** (el volcado se perdió con la muerte) |
| El candado | quedó **echado** (`apuntes_en_curso`, testigo `49eef7eb…`) y hubo que soltarlo |
| Reanudada | 13:40:20, tras soltar el candado, con `-u` y en un fichero de salida **nuevo** |
| La reanudación | **175 de 175 comprobadas**, 40 llamadas, **0,0772 $** |

**La causa está medida y es del método, no del motor**: la corrida se lanzó como **trabajo de fondo de
la sesión**, y **los trabajos de fondo no sobreviven al final del turno**. Al morir el padre murió el
hijo, y con él el volcado: `python -u` **no salva la salida si al que matan es al proceso que la
redirige**, porque PowerShell retiene el búfer hasta que el proceso termina. Lo que sí salva el
trabajo es que **lo escrito queda en la base**: no se perdió ni un hecho ni un apartado, y relanzar
continúa desde donde se quedó.

**Y una medición que corrige una sospecha**: durante esa hora, el proceso que consumía CPU **no era
esta corrida** —era el `pytest` de integración de **otro árbol** (`opofuente-apuntes`), que arrancó a
las 14:41:14 por casualidad—. La reanudación comprobó **10 grupos por minuto** (53 → 175 en doce
minutos), así que la lentitud aparente no era de la API: era que la corrida ya estaba muerta.

## 3. La previsión y lo que costó

| | `--prever` dijo | La corrida que cerró |
|---|---|---|
| Llamadas | 44 como mínimo y **79** como máximo | **40** (0 fallidas) |
| Coste | 0,30 $ como mínimo y **0,54 $** como máximo | **0,0772 $** |
| Tope decidido | tope de dinero **2 $** · tope de tiempo **5.400 s** (la muerte dejó el primero en 6.000 s) | **ninguno se activó** |

**El precio por llamada más bajo del proyecto: 0,00193 $** (III.3 estaba en 0,00293 $ y II.3 en
0,00232 $). Es lógico: la corrida que cerró solo tuvo que **comprobar** lo que ya estaba escrito —no
escribió ni un hecho ni un apartado— y sus llamadas son cortas. Consumo: 183.256 tokens de entrada
(121.088 en caché, 66,1 %) y 82.928 de salida.

**El coste total del tema no está medido en su totalidad y se dice**: la corrida muerta gastó su parte
(9 llamadas de hechos + 17 de redacción + unas 6 de comprobación ≈ 32 llamadas) y **su informe se
perdió**. Estimado a precio de tema técnico (0,0030–0,0045 $ por llamada de las que escriben, que son
más caras que las de comprobar): **≈0,10–0,15 $**. El total del tema queda en **≈0,18–0,23 $**, de los
que **0,0772 $ están medidos**.

## 4. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 175 grupos · **175 preguntas** |
| Hechos | **325 guardados** → **268 en el plan** (57 repetidos agrupados) |
| Apartados | **17** · el mayor, `el-bus-usb-sus-versiones-y-sus-conectores`, con 38 hechos |
| Texto | 8.045 palabras de 13.000 (61,9 %) · párrafos repetidos **0,0 %** |

## 5. Las puertas (§2.3)

| Puerta | Umbral | Cifra de II.2 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % | **0,0 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 8.045 de 13.000 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **163/165 = 98,8 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 163/172 = 94,8 % | — |
| Hechos sin materia en el índice | 0 | **0 grupos y 0 hechos** | PASA |

La corrida de cierre **terminó entera**: **175 de 175 grupos comprobados**, 166 cubiertos (160 a la
primera y 6 tras añadir), 2 en conflicto con la clave y **0 «sin contestar por los apuntes»**.

**El techo medido antes de pagar (98,3 %) y la cobertura real (98,8 %) coinciden**: cuando el índice
sitúa el 98,3 % del banco, no hay margen que perder y el tema publica con holgura.

## 6. La bandeja del propietario

**9 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice el material) | 7 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 2 |

## 7. La puerta de datos del §1, al cerrar (0 $)

**117 conjuntos medibles · 17 en cuarentena · 8 dudosos · 84 sin poder medir**. Es el cierre con más
conjuntos medibles de la serie.

## 8. Coste y gasto

| | |
|---|---|
| Coste medido (corrida que cerró) | **0,0772 $** · 40 llamadas (0 fallidas) · 12 minutos |
| Coste estimado de la corrida muerta | **≈0,10–0,15 $** (su informe se perdió con el proceso) |
| Total del tema | **≈0,18–0,23 $** (0,0772 $ medidos) |
| Arreglos posteriores | **0 $** (ninguno: pasó las dos puertas) |
| Previsión | 44–79 llamadas · 0,30–0,54 $ |

## 9. Lo que queda fuera, con el porqué

- los **3 grupos** que ningún índice sitúa: tres enunciados sin sujeto, en la bandeja con su motivo;
- **I.8 (81,2 %), I.6 (71,4 %) e I.7 (57,1 %)**: los tres borradores que siguen, con su cifra y con la
  causa medida (**0 grupos sin comprobar** en los tres: su hueco es material);
- **III.4**: sigue sin escribir; su banco es de otra materia en un 40 %, ya medido.

## 10. Lo que este tema deja medido

- **Una corrida de fondo no sobrevive al turno del agente**, y al morir se lleva su informe aunque
  lleve `-u`: lo que redirige la salida es el proceso padre, y su búfer muere con él. **Lo que sí
  sobrevive es lo escrito en la base**, así que la regla para las próximas tandas es: **lanzar y
  esperar dentro del turno**, o aceptar que habrá que reanudar (que es barato: 40 llamadas y 0,0772 $
  para comprobar 122 grupos).
- **La mejor cobertura de la serie (98,8 %)** sale de un banco homogéneo, un catálogo de 17 apartados
  que no deja nada fuera y **0 grupos sin materia**: cuando el ensayo sitúa el 98,3 %, el tema publica
  al 98,8 %.
- **Comprobar es diez veces más barato que redactar**: 0,00193 $ por llamada frente a los 0,0030–0,0045 $
  de una corrida que escribe. Reanudar un tema solo para terminar sus comprobaciones es de las cosas
  más baratas que se pueden hacer.
