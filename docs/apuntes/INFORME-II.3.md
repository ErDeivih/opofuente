# Informe de II.3 — Tipos abstractos, organizaciones de ficheros, algoritmos y formatos · 14-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0037_origin_scope`) · corrida del 14-oct
11:10–11:30 (hora local). Vigésimo segundo por valor de la tabla **vuelta a medir hoy** con la
cuarentena puesta (**189** preguntas con clave utilizable), **sin catálogo** antes de esta tanda.
**PUBLICADO tras un arreglo de 0 $**: pasa las dos puertas con **181/190 = 95,3 %** de cobertura
sobre clave utilizable.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **11**, por asunto dentro de sus cuatro epígrafes |
| Grupos situados por el enunciado (ensayo) | **161 de 171 = 94,2 %** |
| Techo medido de cobertura (`sin_materia_con_clave.py`) | **173/189 = 91,5 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **3 y 7** |

Los diez grupos que ningún índice sitúa son **de otro tema o no dicen de qué hablan**, y **16 de sus
preguntas tienen clave utilizable**: el *pharming* y las amenazas al puesto del usuario (**IV.9** e
**I.8**), la firma electrónica, el **CAdES** y el algoritmo de huella de **AutoFirma** (**I.6** y
**IV.5**), **SOAP/MTOM** y **REST** (**IV.3** y **IV.4**), la taxonomía de **Flynn** (**II.1**) y tres
enunciados sin sujeto («cuál de las siguientes afirmaciones NO es correcta», «indica la afirmación
INCORRECTA»). No se lavan: van a la bandeja con su motivo.

**Dos correcciones que el ensayo hizo antes de pagar** (0 $): la primera versión daba el apartado de
los **formatos** a cualquier enunciado que dijera «formato» —y con eso el **CAdES** («formato de
firma digital») entraba al tema—, y el de la **organización de ficheros** a cualquiera que dijera
«ficheros», con lo que **SOAP/MTOM** («enviar ficheros de gran tamaño») también entraba. Se pidió el
formato por su clase (`formato de archivo`, `de fichero`, `abierto`…) y el fichero por su frase; los
dos grupos volvieron a quedar fuera del índice, que es donde tienen que estar.

## 2. La previsión y lo que costó

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 37 como mínimo y **65** como máximo | **36 medidos** (0 fallidas) en el segundo intento, más el primero |
| Coste | 0,25 $ como mínimo y **0,44 $** como máximo | **0,0835 $ medidos** en el segundo intento, más el primero |
| Tope decidido | tope de dinero **2 $** · tope de tiempo **6.000 s** | **ninguno se activó** |

**Este tema gastó dos corridas y hay que decirlo con precisión**:

1. **Primer intento (12,6 min)**: hizo los hechos, redactó los 11 apartados y comprobó los 171
   grupos, y **no archivó la versión** porque la forma no pasaba. Su coste **se perdió**: el guion de
   la tanda escribía la salida de los dos intentos en el **mismo fichero**, y el segundo lo
   sobrescribió. Estimado por el plan: **9 + 11 + 17 llamadas y el bucle de huecos ≈ 0,10 $**.
2. **Segundo intento (7,5 min)**: **36 llamadas · 0,0835 $**, medido. No rehízo los hechos (`0
   nuevos`) ni la redacción, y volvió a comprobar y a cerrar.

**Y ese segundo intento no debía haber existido**: salió con **código 3**, que no es un fallo sino «no
pasa las comprobaciones de forma», y mi guion de la tanda reintentaba ante **cualquier** código
distinto de cero (estaba pensado para el proceso que muere a lo bruto, como le pasó a II.1). Un tema
que ha terminado bien y falla una puerta **no se relanza**: se arregla. Es un defecto del lanzador y
va como lección, con su coste: **≈0,12 $ de más en total** (0,0835 medidos + ≈0,10 estimados del
primero, cuando lo que hacía falta eran **0 $** de arreglo).

Total estimado del tema: **≈0,18 $**, de los que **0,0835 $ están medidos**.

## 3. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 171 grupos · **191 preguntas** |
| Hechos | **343 guardados** → **267 en el plan** (76 repetidos agrupados) |
| Apartados | **11** · ninguno pasó del tope de 150 hechos |
| Texto | 9.869 palabras de 13.720 (71,9 %) · párrafos repetidos **0,0 %** |

## 4. Las puertas (§2.3)

| Puerta | Umbral | Cifra de II.3 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 (tras el arreglo del §5) | PASA |
| Párrafos casi repetidos | ≤ 5 % | **0,0 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 9.869 de 13.720 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **181/190 = 95,3 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 181/194 = 93,3 % | — |
| Hechos sin materia en el índice | 0 | 3 grupos y 7 hechos con su motivo | — |

La corrida **terminó entera**: **171 de 171 grupos comprobados**, 164 cubiertos (161 a la primera y 3
tras añadir), 3 en conflicto con la clave y **0 «sin contestar por los apuntes»**.

## 5. La corrida dejó la forma en NO PASA, y se arregló a 0 $ (con una lección del catálogo)

La corrida **no archivó la versión** por dos motivos de forma, y **el primero era del catálogo, no
del texto**:

1. **tres apartados con las mismas tres primeras palabras del título**: «**Los algoritmos de**
   ordenación», «**Los algoritmos de** búsqueda» y «**Los algoritmos de** grafos y de optimización».
   La puerta de *misma cabecera* mira el tema entero y exige que **no haya tres apartados** que
   empiecen igual: es la comprobación del epígrafe partido en trozos (los 19 «Protocolos TCP/IP: …»
   de IV.7.2). Los títulos eran míos;
2. **una tabla sin fila de cabecera** en `la-organizacion-de-los-ficheros` (al redactor se le fue la
   línea `|---|---|` entre el encabezado y las filas), que es un defecto mecánico de Markdown.

**Lo que se hizo, a 0 $ y sin escribir nada nuevo**:

- **los tres títulos se renombraron en el catálogo** (mi decisión, reversible, 0 $) —«Ordenación de
  datos: la burbuja, la selección, el pivote y los demás», «Búsqueda de un dato: binaria, secuencial
  y por función aritmética» y «Grafos y optimización: Dijkstra, Prim, Kruskal, Bellman-Ford y A*»— y
  `--limpiar-forma` alineó los tres en el texto ya escrito;
- y **la tabla se reparó insertando la línea de separación que faltaba**, con tantas columnas como
  declara su encabezado y sin tocar ni una fila ni un dato.

Se pasó `--publicar` (0 $) y el tema quedó archivado. **Es la quinta vez en la serie que una
reparación de 0 $ evita volver a pagar una corrida**, y la primera en que el defecto está **en el
catálogo** y no en el texto.

**Y una reparación dentro de la reparación, dicha**: el primer arreglo de la tabla insertó una
separadora detrás de **cada** fila en vez de detrás del encabezado, y hubo que normalizar la sección
(encabezado, **una** separadora, filas seguidas). Se detectó leyendo el texto reparado y se arregló
antes de publicar; ninguna fila ni ningún dato se perdió.

## 6. La bandeja del propietario

**13 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `pregunta_ambigua` (sin clave con la que comprobar) | 6 |
| `norma_cambiada` (la clave contradice el material) | 4 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 3 |

## 7. La puerta de datos del §1, al cerrar (0 $)

Al cerrar la corrida: **112 conjuntos medibles · 16 en cuarentena · 8 dudosos · 82 sin poder medir**.
Al publicar (después de los arreglos): **116 medibles · 17 en cuarentena · 8 dudosos · 83 sin poder
medir**.

## 8. Coste y gasto

| | |
|---|---|
| Coste medido (segundo intento) | **0,0835 $** · 36 llamadas (0 fallidas) |
| Coste estimado del primer intento | **≈0,10 $** (su salida se sobrescribió: defecto del guion) |
| Total del tema | **≈0,18 $** (0,0835 $ medidos) |
| Arreglos posteriores | **0 $** (`--limpiar-forma`, la reparación de la tabla y `--publicar`) |
| Previsión | 37–65 llamadas · 0,25–0,44 $ |

## 9. Lo que queda fuera, con el porqué

- los **10 grupos** que ningún índice sitúa (16 preguntas con clave utilizable), listados en el §1:
  son de IV.9, I.8, I.6, IV.5, IV.3, IV.4 y II.1, más tres enunciados sin sujeto; están en la bandeja
  con su motivo y son los que ponen el techo del 91,5 %;
- **I.7** (58,4 %), **I.4** (88,9 %), **I.8** (82,0 %) e **I.6** (72,5 %): los cuatro borradores siguen
  sin reanudar, con su cifra escrita;
- **III.4** sigue sin escribir: su banco es de otra materia en un 40 %, ya medido.

## 10. Lo que este tema deja medido

- **Los títulos del catálogo también pasan por la puerta de encabezados repetidos**: tres apartados
  que compartan las tres primeras palabras del título dejan el tema sin publicar aunque el texto esté
  perfecto. Es un defecto que se arregla en el catálogo, a 0 $, y que conviene mirar **antes de
  correr**.
- Una corrida que falla una puerta de forma **no se relanza**: se repara. Relanzarla cuesta una
  corrida entera de comprobación (36 llamadas) y no arregla nada.
- Los patrones genéricos de un catálogo (`formato`, `fichero`, `estándar`, `ansi`) son la vía por la
  que una pregunta de otro tema entra en los apuntes: el ensayo los caza a 0 $.
