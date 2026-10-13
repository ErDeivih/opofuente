# Informe de IV.9 — Seguridad en redes, perímetro, acceso remoto, VPN y puesto · 13-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0036_claves_no_fiables`) · corrida del 13-oct
22:17–22:42 (hora local). Decimonoveno tema por valor de la tabla **vuelta a medir hoy** con la
cuarentena puesta (**227** preguntas con clave utilizable), **sin catálogo** antes de esta tanda.
**PUBLICADO**: pasa las dos puertas con **205/225 = 91,1 %** de cobertura sobre clave utilizable,
**el margen más estrecho de toda la serie** (1,1 puntos sobre el listón).

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **8**, por asunto dentro de sus cinco epígrafes |
| Grupos situados por el enunciado (ensayo) | **200 de 222 = 90,1 %** |
| Techo medido de cobertura (`sin_materia_con_clave.py`) | **207/227 = 91,2 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **12 y 22** (los grupos sí; los hechos se fueron con ellos) |

**El techo medido es lo más importante de este informe: 91,2 %.** El ensayo previo decía que, aunque
todo lo situado se cubriera, el tema no podía pasar del 91,2 %, porque **20 de sus 22 grupos no
situados tienen clave utilizable** y ningún índice puede responderlos: son de otro tema, leídos uno a
uno —el PoE, las VLAN, la capa 2, el IPv6 y el control de acceso al medio (IV.10); el RAID 6 y el
TIA-942 (IV.2 y IV.5); los principios del ENS y la gestión de incidencias (I.8 y IV.5); `heartbleed`
(IV.5); el `RFC 2142` y Exchange (IV.3)—. Se escribió **con esa cifra delante** y el tema publicó por
**1,1 puntos**: el margen lo puso el banco, no el índice.

## 2. La previsión y lo que costó

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 40 como mínimo y **68** como máximo | **73** (0 fallidas), 5 más que la cota |
| Coste | 0,27 $ como mínimo y **0,46 $** como máximo | **0,3204 $** |
| Tope decidido | tope de dinero **2 $** · tope de tiempo **5.400 s** | **ninguno se activó** (25 minutos) |

**Tema técnico, precio de técnico**: **0,00439 $ por llamada**, dentro de la banda 0,0030–0,0045 $ de
la serie. La cota de coste de `--prever` volvió a ser un **techo** (0,46 $ frente a 0,3204 $ reales).
La cota de **llamadas** se quedó corta por 5, otra vez el **bucle de huecos** (13 grupos cubiertos
«tras añadir»).

Consumo: 485.811 tokens de entrada (255.872 en caché, 52,7 %) y 412.536 de salida — el tema más
«hablador» de la serie por salida, que es lo que se paga.

**Y una incidencia de la corrida que se dice**: **el modelo no contestó por 2 preguntas**
(`a3491e88`, `f8b2dfbd`); esas dos no quedan cubiertas ni con incidencia, porque el fallo fue de la
llamada, no del material.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 222 grupos · **241 preguntas** |
| Hechos | **461 guardados** → **374 en el plan** (87 repetidos agrupados) |
| Apartados | **8** · ninguno pasó del tope de 150 hechos |
| Texto | 13.383 palabras de 18.440 (72,6 %) · párrafos repetidos **0,5 %** |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de IV.9 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 (tras el arreglo del §5) | PASA |
| Párrafos casi repetidos | ≤ 5 % (el doc pide 3 %) | **0,5 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 13.383 de 18.440 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **205/225 = 91,1 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 205/238 = 86,1 % | — |
| Hechos sin materia en el índice | 0 | 0 (22 hechos se fueron con sus 12 grupos) | PASA |

La corrida terminó entera: **222 de 222 grupos comprobados**, 197 cubiertos (184 a la primera y 13
tras añadir), 5 en conflicto con la clave y 4 «sin contestar por los apuntes».

## 5. La corrida dejó la forma en NO PASA, y se arregló a 0 $ (con una lección)

La corrida **no archivó la versión** por dos motivos de forma, los dos sobre la tabla de puertos:

1. **dos notas** de la tabla solo decían lo que un puerto **no** es (el defecto que el propietario
   levantó en IV.7: «21 FTP (control) → no es SSH ni SCP»), y
2. la tabla de puertos de **`acceso-remoto-seguro`** no estaba partida por familias.

La causa está medida: el redactor escribió una **segunda tabla de puertos** dentro del acceso remoto
en vez de en el apartado marcado, y la limpieza por familias **solo se aplica al apartado que el
catálogo marca**. Se marcó también ese apartado y se volvió a pasar `--limpiar-puertos` (0 $)… y
apareció el defecto de verdad: **un tema no puede tener dos tablas de puertos**, porque cada una
recibe los encabezados «Servicios de red», «Escritorio remoto y otros» y «Confusiones que caen», y la
puerta de **encabezados repetidos** —que mira el tema entero— los cuenta dos veces. No hay arreglo de
forma que lo tape: el orden natural del motor (forma → puertos) vuelve a crear los duplicados.

**Lo que se hizo, y se hizo midiendo antes de tocar nada** (0 $, ensayo en seco con la revisión de
forma delante): **consolidar las dos tablas en una**. Las cuatro filas que no estaban en la del
cortafuegos (23 Telnet, 69 TFTP, 3389 RDP y 5900 RFB/VNC) se movieron allí **literalmente**, con su
mismo servicio y su misma nota —no se inventó ninguna fila—, el bloque duplicado se quitó del acceso
remoto y la marca `tabla_unica` volvió a estar **solo** en el apartado del cortafuegos, que es el
diseño documentado. Las filas de FTP, SSH y HTTPS que estaban en las dos se quedaron una sola vez.

Con eso, la forma quedó en **PASA** y el tema se publicó con `--publicar` (0 $).

**Es la cuarta vez en la serie que una reparación de 0 $ evita volver a pagar una corrida**, y la
primera en que la reparación **mueve** contenido de un apartado a otro: se hace porque las filas son
las mismas que escribió el modelo, no texto nuevo.

## 6. La bandeja del propietario

**34 incidencias**, contadas en la base — **la bandeja más llena de la serie**:

| Categoría | Cuenta |
|---|---|
| `pregunta_ambigua` (sin clave con la que comprobar) | 15 |
| `norma_cambiada` (la clave contradice el material) | 11 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 4 |
| `hueco_sin_material` (los apuntes no tienen el dato) | 4 |

## 7. La puerta de datos del §1, al cerrar (0 $)

**105 conjuntos medibles** (eran 103 al cerrar IV.1), **14 en cuarentena · 9 dudosos · 83 sin poder
medir**, y **ningún conjunto cambió de veredicto**.

## 8. Coste y gasto

| | |
|---|---|
| Coste medido | **0,3204 $** · 73 llamadas (0 fallidas) · 25 minutos · ningún tope activado |
| Arreglos posteriores de forma y publicación | **0 $** (`--limpiar-puertos`, `--limpiar-forma`, consolidación y `--publicar`) |
| Previsión | 0,27–0,46 $ (llamadas 5 por encima del máximo; coste dentro del rango) |
| Gasto acumulado del objetivo | ≈ 15,68 $ antes de IV.9 → **≈ 16,00 $** con IV.9 |

## 9. Lo que queda fuera, con el porqué

- los **12 grupos** que ningún índice sitúa (22 preguntas, 20 con clave utilizable), listados en el
  §1: son de otros temas, están en la bandeja con su motivo y son los que ponen el techo del 91,2 %;
- las **2 preguntas** por las que el modelo no contestó (`a3491e88`, `f8b2dfbd`): es un fallo de la
  llamada, no del material; quedan sin cubrir y sin incidencia;
- **I.7** (58,4 %), **I.4** (88,9 %), **I.8** (82,0 %) e **I.6** (72,5 %): los cuatro borradores
  **siguen sin reanudar**, con su cifra escrita y por el motivo ya medido;
- **III.4** sigue **sin escribir**: su banco es de otra materia en un 40 %.

## 10. Lo que este tema deja medido para los que quedan

- Un tema **técnico** sigue saliendo a **0,0030–0,0045 $ por llamada** y la corrida entera a
  **0,19–0,40 $**: con IV.1 (0,3281 $) y IV.9 (0,3204 $) son ya **seis técnicos seguidos** en la banda.
- La **cota de llamadas de `--prever` se quedó corta en 5 de las 6 corridas** de f21 y f21b, siempre
  por el bucle de huecos: es la partida que no se puede acotar de antemano.
- El **techo medido antes de pagar** (`sin_materia_con_clave.py`) es la cifra que decide: en IV.8 era
  91,8 % y publicó en 99,1 %; en IV.1 era 97,3 % y publicó en 98,2 %; en IV.9 era **91,2 %** y publicó
  en **91,1 %** — rozando el listón. Con techo por debajo de ~93 %, el tema se escribe sabiendo que el
  margen es estrecho.
