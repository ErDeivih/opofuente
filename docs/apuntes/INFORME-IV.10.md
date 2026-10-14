# Informe de IV.10 — Redes locales, tipología, transmisión, acceso y dispositivos · 14-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0037_origin_scope`) · corrida del 14-oct
12:00–12:18 (hora local). Vigésimo cuarto por valor de la tabla **vuelta a medir hoy** con la
cuarentena puesta (**180** preguntas con clave utilizable), **sin catálogo** antes de esta tanda.
**PUBLICADO**: pasa las dos puertas con **171/175 = 97,7 %** de cobertura sobre clave utilizable, la
mejor cobertura de la tanda.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **12**, por asunto dentro de sus cinco epígrafes |
| Grupos situados por el enunciado (ensayo) | **180 de 184 = 97,8 %** |
| Techo medido de cobertura (`sin_materia_con_clave.py`) | **175/180 = 97,2 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **1 y 1** |

Es el banco más desequilibrado de la serie y se dice con la cifra: de sus **184 grupos, 126 no traen
epígrafe** (el 68 %) y son casi todos de lo mismo —la familia de normas IEEE 802, Ethernet, la VLAN,
el Wi-Fi, el cableado y los dispositivos de la red local—, mientras que los cinco epígrafes oficiales
son un esqueleto de 18, 4, 3, 7 y 27 grupos.

**Dos correcciones del ensayo, antes de pagar (0 $)**: el patrón `media-independent handover` se
escribió con guion y el texto normalizado lo trae con espacio, así que esa pregunta se quedaba sin
apartado; y `ansi/?eia/?tia ?568` esperaba barras que la normalización convierte en espacios. Las dos
se vieron en el ensayo y se corrigieron antes de la corrida.

**Y una decisión que se toma con la cifra delante: el encaminamiento se queda dentro del tema.** Este
banco pregunta por los protocolos de encaminamiento (RIP, OSPF, BGP, vector de distancia, estado de
enlace, vector de camino) y por las tablas de encaminamiento en el contexto de los equipos de
interconexión, que es literalmente el epígrafe `IV.10.5` («Dispositivos de interconexión»), y un
encaminador es un dispositivo de interconexión. Se les da **su propio apartado, explícito** —10 grupos
con clave utilizable—, en vez de repartirlos por los demás o de mandarlos fuera. No se lavan dentro
de otro apartado: se declaran.

Lo que **sí** es de otro tema y no se lava: la pregunta por los **semáforos** de los sistemas
operativos (**II.4**) y la definición de **proxy** (**IV.9**). Dos de las 180 preguntas con clave
utilizable, a la bandeja con su motivo.

**La tabla de puertos no existe en este tema**, así que ninguna materia lleva la marca `tabla_unica`:
aquí los números que se memorizan son las categorías de cable, los identificadores de VLAN y los
tamaños de trama. Es una decisión defensiva con su porqué medido: lo que rompió la forma de IV.9 fue
tener **dos** tablas de puertos, y donde no hay tabla única no puede haber duplicado.

## 2. La previsión y lo que costó

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 40 como mínimo y **70** como máximo | **71** (0 fallidas), 1 más que la cota |
| Coste | 0,27 $ como mínimo y **0,48 $** como máximo | **0,2440 $** |
| Tope decidido | tope de dinero **2 $** · tope de tiempo **6.000 s** | **ninguno se activó** (18 minutos) |

**Tema técnico, precio de técnico**: **0,00344 $ por llamada**, dentro de la banda 0,0030–0,0045 $.
La cota de coste de `--prever` volvió a ser un **techo** (0,48 $ frente a 0,2440 $ reales). La cota de
**llamadas** se quedó corta por **una**: es la primera vez en la serie que el bucle de huecos no
desborda la previsión.

Consumo: 449.252 tokens de entrada (268.928 en caché, 59,9 %) y 294.359 de salida.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 184 grupos · **184 preguntas** |
| Hechos | **386 guardados** (386 nuevos, 13 con la clave señalada) → **314 en el plan** (72 agrupados) |
| Apartados | **12** · ninguno pasó del tope de 150 hechos |
| Texto | 9.301 palabras de 15.440 (60,2 %) · párrafos repetidos **0,0 %** |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de IV.10 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % | **0,0 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 9.301 de 15.440 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **171/175 = 97,7 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 171/181 = 94,5 % | — |
| Hechos sin materia en el índice | 0 | 1 grupo y 1 hecho con su motivo | — |

La corrida **terminó entera**: **184 de 184 grupos comprobados**, 175 cubiertos (168 a la primera y 7
tras añadir), 1 en conflicto con la clave y 2 «sin contestar por los apuntes» (que van a la bandeja
como `hueco_sin_material`).

## 5. La bandeja del propietario

**10 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice el material) | 6 |
| `hueco_sin_material` (los apuntes no tienen el dato) | 2 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 1 |
| `pregunta_ambigua` (sin clave con la que comprobar) | 1 |

## 6. La puerta de datos del §1, al cerrar (0 $)

**116 conjuntos medibles · 17 en cuarentena · 8 dudosos · 83 sin poder medir**. Es el cierre con más
conjuntos medibles y más conjuntos en cuarentena de toda la serie.

## 7. Coste y gasto

| | |
|---|---|
| Coste medido | **0,2440 $** · 71 llamadas (0 fallidas) · 18 minutos · ningún tope activado |
| Arreglos posteriores | ninguno: el tema pasó las dos puertas a la primera |
| Previsión | 40–70 llamadas · 0,27–0,48 $ (1 llamada por encima del máximo; coste por debajo del mínimo) |

## 8. Lo que queda fuera, con el porqué

- el **grupo de los semáforos** y el de **proxy** (2 preguntas con clave utilizable): son de II.4 y
  IV.9, están en la bandeja con su motivo y son los que ponen el techo del 97,2 %;
- **las 2 preguntas por las que el modelo no contestó**: quedan sin cubrir y sin incidencia, porque el
  fallo fue de la llamada y no del material;
- **I.7** (58,4 %), **I.4** (88,9 %), **I.8** (82,0 %) e **I.6** (72,5 %): los cuatro borradores siguen
  sin reanudar, con su cifra escrita;
- **III.4** sigue sin escribir: su banco es de otra materia en un 40 %, ya medido.

## 9. Lo que este tema deja medido

- **La mejor cobertura de la tanda (97,7 %)** en el banco más desequilibrado de la serie (68 % de
  grupos sin epígrafe): cuando el ensayo sitúa el 97,8 % y el techo medido es el 97,2 %, el tema
  publica con holgura. Confirma, por cuarta vez, que **el techo medido antes de pagar es la cifra que
  decide**.
- **Un `tabla_unica` de menos es mejor que uno de más**: donde no hay tabla única no puede haber dos.
- **Una decisión de contenido dicha vale más que una escondida**: el encaminamiento se quedó dentro
  del tema con su apartado y con su porqué, en vez de repartirse por los demás.
