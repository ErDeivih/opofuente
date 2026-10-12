# Informe de IV.2 — Administración de bases de datos, almacenamiento, backup y virtualización

**Tanda:** f17 · **Fecha de la corrida:** 12 oct 2026 · **Estado:** **publicado** (versión archivada,
con la marca «Versión generada · en revisión»)

Las cifras de este informe están **medidas** sobre la base real con `apuntes --medir` y
`apuntes --esquema`, no heredadas de la corrida que las escribió. El índice de este tema **no** se
escribió en esta tanda: venía de f15 (`domain/catalogo_iv_2.py`, 13 apartados, 761 de sus 770 grupos
situados por el enunciado). Esta tanda lo **redacta**.

## 1. Hechos y apartados

| Qué | Antes de deduplicar | Después |
|---|---|---|
| Hechos | 1.543 | **1.126** (417 repetidos agrupados) |
| Apartados | — | **16** (13 materias, 3 partidas por el tope) |
| Grupos de preguntas | 770 | 770 |
| Preguntas | 807 | 807 |

- 8 grupos **no dicen de qué hablan por su enunciado** y se situaron por el texto de sus hechos; el
  índice acaba con **0 grupos y 0 hechos sin materia** (los 8 acabaron dentro de una materia).
- Revisión del índice: **PASA** · 16 apartados · 1.126 hechos · **0 grupos y 0 hechos sin materia**.
- Tres apartados pasaban del tope de 150 hechos y se partieron: `bbdd-relacionales` (159 → `-1`, 150,
  y `-2`, 9), `raid` (185 → 150 y 35) y `almacenamiento-en-red` (209 → 150 y 59). La partición es
  determinista y la hace el motor; no es una decisión de contenido.

## 2. Las puertas del §2.3

| Comprobación | Umbral | Medido | ¿Pasa? |
|---|---|---|---|
| Encabezados repetidos / misma cabecera | 0 | 0 | **sí** |
| Marcas internas visibles | 0 | 0 | **sí** |
| Tablas sin cabecera o columnas sin nombre | 0 | 0 | **sí** |
| Párrafos casi repetidos | ≤ 3 % | **0,2 %** | **sí** |
| Hechos fuera de su materia | ≤ 3 % | **no implementada** (aviso del §5 del estado) | — |
| Extensión | ≤ 40 palabras × hechos | 32.567 de 61.720 | **sí** |
| **Preguntas cubiertas** (clave utilizable) | **≥ 90 %** | **757/758 = 99,9 %** | **sí** |
| Preguntas cubiertas (todas las que tienen clave) | — | 757/797 = 95,0 % | — |
| Conflictos de letra sin categorizar | 0 | 0 | **sí** |
| Copia literal de material no normativo | 0 párrafos | 0 | **sí** |
| Afirmaciones sobre exámenes no calculadas | 0 | 0 | **sí** |

**La limpieza de forma no gastó nada y no hizo falta**: `--limpiar-forma` tocó **0 apartados**. Es la
primera corrida de esta serie que termina con la forma en PASA sin reparaciones (I.1 necesitó cuatro
tablas y dos encabezados, I.2 un encabezado). El motivo está en el propio catálogo: sus 13 materias
son «de lo que afirma» cada hecho y sus títulos no se repiten entre apartados.

## 3. Incidencias en la bandeja del propietario, por categoría

| Categoría | Cuántas |
|---|---|
| `norma_cambiada` (la clave contradice la norma o el material) | 35 |
| `clave_sospechosa` (los apuntes dicen otra letra, con la frase que lo demuestra) | 1 |
| `hueco_sin_material` (los apuntes no tienen el dato) | 0 |
| `pregunta_ambigua` (sin clave con la que comprobar) | 0 |
| **Total** | **36** |

Las **35 `norma_cambiada`** son las que el paso B marcó con la clave contraria a la norma; hay
además **35 incidencias de clave** contadas aparte y **1 en conflicto** (la frase está en los
apuntes y sostiene otra opción). Todas las preguntas no cubiertas tienen categoría, que es la otra
mitad del §2.3.

**Y una cifra que conviene leer bien**: «sin contestar por los apuntes: **0**». En este tema no hay
ni una pregunta cuya respuesta no esté en el texto: de las 770 comprobadas, 734 quedaron cubiertas
con su letra y su cita (714 a la primera y 20 tras añadir material en el bucle de huecos); el resto
(`a revisión`, 36) lo está porque **su clave** no se puede usar, no porque falte el dato. Es lo
contrario de I.6 —donde 30 preguntas no tenían frase— y explica que la cobertura sobre clave
utilizable salga al 99,9 %.

## 4. Lo que costó, y lo que se dijo antes de pagarlo

| | `--prever` dijo | La corrida hizo |
|---|---|---|
| Llamadas | 129 como mínimo y 219 como máximo | **182** (0 fallidas) |
| Entrada | — | 1.829.341 tokens (1.293.184 de caché) |
| Salida | — | 806.759 tokens |
| Coste | 0,88 $ como mínimo y 1,49 $ como máximo | **0,7585 $** |
| Duración | — | 45 minutos (12:39 → 13:24) |

**La previsión acertó el rango por el medio y el coste salió por debajo del mínimo.** Es la primera
corrida de la serie que cuesta menos de lo previsto: 182 llamadas (dentro de 129–219) pero a
**0,00417 $ por llamada** en vez de los 0,0068 $ de la media. La causa está medida: devolvió
**4.432 tokens de salida por llamada** donde la media de la tabla es ~8.000, y con la mitad del
catálogo ya en caché (1,29 M de 1,83 M de entrada). Un tema técnico, con hechos cortos y muy
repetidos (417 de 1.543 se agruparon en la deduplicación), sale más barato que uno normativo denso.

**El tope de esta tanda no se activó.** El tope por tema era la cota de arriba de `--prever` más un
tercio cuando el tema es normativo y denso (**1,49 × 4/3 = 1,99 $** para IV.2) y se le puso un tope
de tiempo (`--tiempo-maximo 7400`, ~2 h) para que una corrida que se acercara al tope se parara
sola conservando lo escrito. Ni el dinero (0,7585 $ de 1,99 $) ni el tiempo (45 min de 2 h) llegaron
cerca: **no hubo nada que parar**.

## 5. Lo que se dejó escrito y lo que queda para el propietario

- **Publicado**: `--publicar` midió las dos puertas sobre lo guardado y las dos pasan, así que la
  versión está **archivada** (el propio comando dice «versión del tema: ya estaba guardada»: la
  corrida la archivó al terminar porque `--exigir-calidad` también pasó). El tema se lee en la zona
  del alumno con la marca «Versión generada · en revisión».
- **36 incidencias** esperan su criterio en la bandeja del motor (`notes_incidents`), que todavía no
  tiene pantalla: son 35 claves que contradicen la norma y 1 que sostiene otra letra. El texto de los
  apuntes está del lado que dice la norma, con la frase que lo demuestra.
- **Lo que no se ha tocado**: el listón del 90 % (no hacía falta), la deduplicación, y ninguna de las
  dos discrepancias del §5 del estado (`párrafos repetidos` al 5 % en el código frente al 3 % del
  documento, y `hechos fuera de su materia` sin implementar). IV.2 sale al **0,2 %** de repetidos, así
  que el listón del 3 % tampoco le habría afectado.
