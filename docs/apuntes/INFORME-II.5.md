# Informe de II.5 — Sistemas de gestión de bases de datos: relacionales, orientados a objetos y NoSQL · 14-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0037_origin_scope`). Corrida del 14-oct, lanzada y
**esperada dentro del turno**. Tercer tema de la tanda f25 y **vigésimo cuarto** por valor de la tabla
vuelta a medir hoy (**155** claves utilizables). **PUBLICADO**: pasa las dos puertas con
**150/154 = 97,4 %** de cobertura sobre clave utilizable.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **11** |
| Grupos situados por el enunciado (ensayo) | **136 de 143 = 95,1 %** |
| Techo medido de cobertura (`sin_materia_con_clave.py`) | **148/155 = 95,5 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **4 grupos y 6 hechos**, con su motivo |

**Este tema tiene un solo epígrafe oficial con contenido** —II.5.1, con 55 grupos— y **88 de sus 143
grupos no traen epígrafe** (el 62 %). Es el caso extremo de la regla: cuando el epígrafe es uno, **el
asunto lo pone entero el enunciado**.

**Dos correcciones del ensayo antes de pagar (0 $)**: las preguntas de las **bases de datos no
relacionales** y de la **base de datos local para una aplicación Android** se quedaban sin apartado;
con dos patrones más, el techo subió de 94,2 % a **95,5 %**.

**Las dos lecciones de f24, aplicadas antes de correr**: los títulos de los once apartados **no
comparten las tres primeras palabras entre tres de ellos**, y **ningún patrón propio es una palabra
genérica**. Aquí es donde más falta hacía: «datos», «base», «sistema» y «siguiente» salen en casi todos
los enunciados de este banco, y si contaran, cualquier pregunta caería en el primer apartado que los
nombrara. Lo que distingue una pregunta de otra es **la sigla y el nombre propio** (`ansi ?/? ?sparc`,
`codd`, `acid`, `nosql`, `mongodb`, `oracle`).

**Y una decisión de apartado que se dice en voz alta**: media docena de preguntas del banco son de
**polimorfismo, sobrecarga, encapsulación y generalización** —programación orientada a objetos, no
gestores—. Se quedan **con un apartado propio** («Los conceptos de la orientación a objetos que usa el
modelo») porque el modelo de datos orientado a objetos **se construye con ese vocabulario** —el OID, las
colecciones, la herencia de tipos— y porque es **el banco del propio tema** el que las pregunta;
repartirlas por los demás apartados sería lavarlas.

## 2. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 143 grupos · **158 preguntas** |
| Hechos | **282 guardados** → **219 en el plan** (63 repetidos agrupados) · 11 con la clave señalada |
| Apartados | **11** |
| Texto | 7.717 palabras de 11.280 (68,4 %) · párrafos repetidos **0,0 %** |

## 3. Las puertas (§2.3)

| Puerta | Umbral | Cifra de II.5 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % | **0,0 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 7.717 de 11.280 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **150/154 = 97,4 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 150/159 = 94,3 % | — |
| Hechos sin materia en el índice | 0 | 4 grupos y 6 hechos con su motivo | — |

La corrida **terminó entera**: **143 de 143 grupos comprobados**, 138 cubiertos (132 a la primera y
**6** tras añadir), **0 en conflicto con la clave** y **0 «sin contestar por los apuntes»**.

## 4. Lo que NO se coló, verificado y no supuesto

El ensayo dejaba **7 grupos fuera** del índice por ser de otro tema o ambiguos: el **hipervisor**
(IV.2), el mecanismo de **Docker** para persistir datos (IV.1), **SCRUM** (las metodologías del bloque
III), **Spring Boot** (III.5), las características de **C#** (III.2) y dos enunciados sin sujeto.

El motor tiene una red de seguridad —un hecho que no reconoce ninguna materia va **al apartado de la
pregunta de la que salió**, `repartir_hechos`— y esa es exactamente **la puerta por la que el material
ajeno se sienta dentro de un tema**, que es el defecto que se declaró en I.3. **Se ha comprobado
grupo por grupo con `donde_cayeron.py` (0 $) y los cinco aparecen «(sin ancla)»**: no se sentaron en
ningún apartado, se quedaron en la bandeja del propietario con su motivo. **El defecto de I.3 no se ha
repetido en II.2, III.8 ni II.5** (los seis grupos ajenos de los tres temas, todos sin ancla).

## 5. La bandeja del propietario

**9 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice el material) | 5 |
| `pregunta_ambigua` (sin clave con la que comprobar) | 4 |

## 6. Lo que costó, y la previsión

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 33 como mínimo y 58 como máximo | **51** (0 fallidas) |
| Coste | 0,22 $ como mínimo y 0,39 $ como máximo | **0,1663 $** — por debajo del mínimo |
| Precio por llamada | — | **0,00326 $** |
| Consumo | — | 460.880 tokens de entrada (338.560 en caché, 73,5 %) · 161.925 de salida |

**La tercera vez seguida que el coste sale por debajo del mínimo previsto** (II.2 0,0772 $ frente a
0,30 $; III.8 0,2090 $ frente a 0,22 $; II.5 0,1663 $ frente a 0,22 $). La cota de dinero de `--prever`
es un **techo** de verdad, y con el catálogo ensayado antes de pagar se queda holgada.

## 7. La puerta de datos del §1, al cerrar (0 $)

**121 conjuntos medibles · 19 en cuarentena · 9 dudosos · 83 sin poder medir.**

## 8. Lo que queda fuera, con el porqué

- los **4 grupos** (6 hechos) que ningún índice sitúa: los cinco de otro tema y los ambiguos, en la
  bandeja con su motivo y **sin ancla** (§4);
- **I.8 (81,2 %), I.6 (71,4 %) e I.7 (57,1 %)**: los tres borradores que siguen, con su cifra y su causa
  medida (**0 grupos sin comprobar** en los tres: el hueco es material);
- **III.4**: sigue sin escribir; su banco es de otra materia en un 40 %, ya medido.
