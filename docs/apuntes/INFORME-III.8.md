# Informe de III.8 — Accesibilidad, diseño universal, usabilidad y seguridad en el desarrollo · 14-oct-2026

**Rama `f21-temas-valor`** · base real (revisión `0037_origin_scope`). Corrida del 14-oct, lanzada y
**esperada dentro del turno** (la lección de II.2, ver §6). Segundo tema de la tanda f25 y **vigésimo
tercero** por valor de la tabla vuelta a medir hoy (**167** claves utilizables). **PUBLICADO**: pasa
las dos puertas con **152/155 = 98,1 %** de cobertura sobre clave utilizable.

## 1. El índice, antes de gastar (0 $)

| Qué | Cifra |
|---|---|
| Apartados del catálogo | **10**, por asunto dentro de sus cuatro epígrafes |
| Grupos situados por el enunciado (ensayo) | **144 de 147 = 98,0 %** |
| Techo medido de cobertura (`sin_materia_con_clave.py`) | **163/167 = 97,6 %** |
| Revisión del índice (`--esquema`) | **PASA** |
| Grupos y hechos sin materia al cerrar | **0 y 0** |

Solo **3 grupos** quedaron fuera del índice y los tres son de otro tema o sin sujeto: el **Portal de la
Transparencia** (artículo 11 de la Ley 19/2013, que es **I.4**), los **once principios generales de la
Ley 11/2007** (que es **I.8.1**) y un «señale la opción correcta» sin sujeto. No se lavan: van a la
bandeja con su motivo.

**Dos correcciones del ensayo antes de pagar (0 $)**: las preguntas de los **estándares de jure** y la
del **proceso de diseñar productos para el rango más amplio de personas** se quedaban sin apartado por
no nombrar su materia con las palabras que el catálogo esperaba; se añadieron dos patrones y el techo
subió de 96,4 % a **97,6 %**.

**El banco más descolgado de la serie**: **124 de sus 147 grupos no traen epígrafe** (el 84 %), y tres
de sus cuatro epígrafes oficiales (III.8.2, III.8.3 y III.8.4) tienen **0, 0 y 6 grupos**. Por eso el
índice va enteramente **por asunto**: la accesibilidad y la usabilidad por un lado —que es de lo que
habla el 80 % del banco— y los conceptos de seguridad en el desarrollo por otro.

**Las dos lecciones de f24, aplicadas antes de correr**: los títulos de los diez apartados **no
comparten las tres primeras palabras entre tres de ellos**, y **ningún patrón propio es una palabra
genérica**: en este banco «accesibilidad», «web», «usuario», «herramienta» y «seguridad» salen en casi
todos los enunciados y no deciden nada —lo que distingue una pregunta de otra es **la sigla** (`WCAG 2
2` frente a `RD 1112`, `aria` frente a `nielsen`)—; y el Real Decreto 1112/2018 se pide **por su
número**, porque en el banco hay otras normas que también son reales decretos.

## 2. Lo que se escribió

| Qué | Valor |
|---|---|
| Grupos y preguntas | 147 grupos · **170 preguntas** |
| Hechos | **286 guardados** → **233 en el plan** (53 repetidos agrupados) · 16 con la clave señalada |
| Apartados | **10** |
| Texto | 8.027 palabras de 11.560 (69,4 %) · párrafos repetidos **0,0 %** |

## 3. Las puertas (§2.3)

| Puerta | Umbral | Cifra de III.8 | Veredicto |
|---|---|---|---|
| Encabezados repetidos / marcas internas / tablas sin cabecera | 0 | 0 | PASA |
| Párrafos casi repetidos | ≤ 5 % | **0,0 %** | PASA |
| Extensión | ≤ 40 palabras × hecho | 8.027 de 11.560 | PASA |
| **Preguntas cubiertas (clave utilizable)** | **≥ 90 %** | **152/155 = 98,1 %** | **PASA** |
| Preguntas cubiertas (todas las claves) | — | 152/167 = 91,0 % | — |
| Hechos sin materia en el índice | 0 | **0 grupos y 0 hechos** | PASA |

La corrida **terminó entera**: **147 de 147 grupos comprobados**, 137 cubiertos (136 a la primera y
**1** tras añadir), 1 en conflicto con la clave y 1 «sin contestar por los apuntes».

## 4. La bandeja del propietario

**10 incidencias**, contadas en la base:

| Categoría | Cuenta |
|---|---|
| `norma_cambiada` (la clave contradice el material) | 8 |
| `clave_sospechosa` (los apuntes dicen otra letra) | 1 |
| `hueco_sin_material` (los apuntes no tienen el dato) | 1 |

## 5. Lo que costó, y la previsión

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 33 como mínimo y 58 como máximo | **57** (0 fallidas) — en el tope de la cota |
| Coste | 0,22 $ como mínimo y 0,39 $ como máximo | **0,2090 $** — por debajo del mínimo |
| Precio por llamada | — | **0,00367 $** |
| Tope de tiempo | 5.400 s | no se activó |
| Consumo | — | 430.901 tokens de entrada (266.880 en caché, 61,9 %) · 240.623 de salida |

## 6. Lo que este tema deja medido

- **Comprobar dentro del turno funciona**: **17 minutos** desde el lanzamiento hasta la versión
  archivada (147 grupos y 170 preguntas), frente a las horas que se fueron en II.2 por lanzarlo como
  trabajo de fondo y morir con el turno. La regla de f25 —**lanzar y esperar dentro del turno**—
  aplicada tal cual.
- **La cota de llamadas de `--prever` es un suelo en su extremo superior**: se quedó a una llamada del
  máximo (57 de 58) y el coste salió **por debajo del mínimo** (0,2090 $ frente a 0,22 $). Es lo que
  ya se midió en f24: la cota de arriba es un **techo** en dinero y un **suelo** en llamadas.
- **El techo medido antes de pagar (97,6 %) y la cobertura real (98,1 %) coinciden otra vez**: cuando
  el índice sitúa el 98 % del banco, el tema publica por encima del 98 %.

## 7. La puerta de datos del §1, al cerrar (0 $)

**120 conjuntos medibles · 19 en cuarentena · 9 dudosos · 83 sin poder medir.** Dos conjuntos más en
cuarentena que al cerrar II.2 (17 → 19): es la mecánica que hace subir los denominadores de los temas
escritos sin tocar su texto.

## 8. Lo que queda fuera, con el porqué

- los **3 grupos** que ningún índice sitúa: el Portal de la Transparencia (I.4), la Ley 11/2007 (I.8.1)
  y un enunciado sin sujeto, en la bandeja con su motivo;
- **I.8 (81,2 %), I.6 (71,4 %) e I.7 (57,1 %)**: los tres borradores que siguen, con su cifra y su causa
  medida (**0 grupos sin comprobar** en los tres: el hueco es material);
- **III.4**: sigue sin escribir; su banco es de otra materia en un 40 %, ya medido.
