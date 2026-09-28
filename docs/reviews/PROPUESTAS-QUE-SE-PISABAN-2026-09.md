# Propuestas que se pisaban: por qué cinco temas del temario se quedaban sin material

**Fecha:** 28 de septiembre de 2026
**Rama:** `main`, árbol de trabajo `F:\temp-opofuente\opofuente-main` (el que sirve la aplicación en uso)
**Commit:** `9d2f81d` — «Propuestas que se pisaban: la señal fuerte ya no la borra la débil»
**Naturaleza:** dos defectos **encontrados midiendo** la cobertura sobre el material real, no leyendo el
código. No añade dependencias, no toca la base de datos, no cambia el contrato, no usa ningún modelo.
**De dónde sale:** del trabajo de catalogación del material del propietario (1.255 ficheros de TAI,
2.132 sujetos clasificables). Medir la cobertura del temario es lo que destapó las dos cosas.

## Lo que se midió, y lo que apareció

La cobertura del temario se mide con la aplicación de verdad, sobre la base de datos real, contando los
mapeos de los nodos de tipo `topic`. El 27 de septiembre daba **23 de 33** temas con material. Diez temas
sin nada, y cinco de ellos con una particularidad que no cuadraba: la base **sí** tenía una propuesta de
0,80 sobre ellos (el motor determinista veía el título oficial dentro del texto), y esa propuesta estaba
en estado `superseded` —retirada—, así que la banda alta nunca llegaba a aplicarla.

Ahí había dos defectos de contabilidad de propuestas, y los dos se entendían solo mirando lo que la
aplicación había escrito, no lo que el código parecía hacer.

### Defecto 1 — una propuesta nueva retiraba las que no eran suyas

`SqlAlchemyClassificationRepository._guardar_propuestas` hacía, por cada propuesta nueva:

1. comprobaba si esa propuesta (sujeto, eje, motor, valor) ya existía y, si existía, no hacía nada más;
2. si no existía, marcaba **todas** las pendientes de ese sujeto y ese eje como `superseded`, sin mirar de
   qué motor venían;
3. y añadía la nueva.

Con un solo motor y un solo valor por eje eso era correcto. Con los dos motores que hay hoy —el
determinista, que propone **un** tema por documento (el mejor: el que ve el título oficial en el texto,
hasta 0,80), y el de fragmentos, que propone **hasta tres** nodos con confianzas más bajas— es una
pérdida silenciosa de señal, en dos direcciones:

- **Entre motores**: el determinista propone I.3 con 0,80; después corre el de fragmentos para el mismo
  sujeto, propone III.2 con 0,25 y, al guardarlo, retira la de 0,80. Cuando la banda alta mira, la
  propuesta fuerte ya no está.
- **Dentro de una pasada**: el motor de fragmentos propone tres nodos por documento y solo sobrevivía el
  último que se escribía. Dos de cada tres nodos se perdían, y el que quedaba no era ni el primero ni el
  mejor: era el último de la lista.

La nota que el propio código escribía al retirar decía «Sustituida por una propuesta nueva **del mismo
motor**», y la consulta no filtraba por motor. La intención estaba escrita; el código hacía otra cosa.

Y había un tercer efecto, el peor de los tres: **un valor retirado no podía volver nunca**. La
comprobación de duplicados no mira el estado, así que un valor que ya existía en la tabla —aunque
estuviera `superseded`— contaba como «ya está» y no se volvía a escribir jamás. El corpus arrastraba
10.169 filas `superseded` que parecían opiniones vivas de los motores y no eran más que contabilidad
muerta.

### Defecto 2 — la banda alta miraba mil propuestas y decidía con azar

`ClassificationService._apply_high_band` recorría **una** página de 1.000 propuestas pendientes
(`list_proposals(status=pending, limit=1000)`) y aplicaba las que estuvieran ahí. Todas las propuestas de
una misma pasada **comparten instante** (`now` es el mismo para toda la pasada), así que el criterio de
orden (`created_at desc, id`) no dice nada: entraban mil al azar y el resto se quedaba pendiente. Con el
material real, una sola pasada dejó 14.162 filas: la cobertura de un tema dependía de qué identificadores
aleatorios cayeran dentro de la ventana.

## Qué se ha cambiado

**En el guardado** (`classification_repository.py`), tres reglas, las tres sobre la misma pregunta —*¿de
quién es esta opinión?*—:

1. **La opinión de un motor sustituye solo a la de ese motor.** Un motor propone; otro motor no retira
   nada suyo. Es lo que ya decía la nota de la retirada.
2. **Los hermanos de una misma pasada no se pisan.** El eje del tema admite varios valores (`04 §7`: hasta
   tres nodos por documento), así que proponer tres temas no es cambiar de opinión dos veces. La
   retirada, dentro del mismo motor, se hace contra el **conjunto** de valores que ese motor propone en
   esa pasada: lo que no está en el conjunto, y sigue pendiente, se retira con su motivo.
3. **Una propuesta `superseded` vuelve a `pending` si su motor la vuelve a sostener.** Era contabilidad de
   la máquina, no una decisión de nadie. Lo que **no** se toca nunca: `accepted`, `rejected` y
   `auto_applied_provisional` —un rechazo del usuario sigue siendo un rechazo aunque el motor vuelva a
   proponer lo mismo—.

**Al aplicar la banda** (`classification_service.py`): las pendientes se recorren **enteras**, por
páginas de 1.000 (`PAGINA_DE_APLICACION`, que es tamaño de página y no un tope), y los identificadores se
recogen **antes** de decidir, porque decidir cambia el estado y movería la ventana bajo los pies.

## Lo que dicen los números

La misma pasada completa (2.132 sujetos), con el código de antes y con el de ahora:

| | antes | después |
|---|---|---|
| propuestas nuevas | 8.618 | 2.030 |
| propuestas que ya existían | 5.592 | 11.674 |
| **aplicadas provisionalmente por la banda** | **313** | **8.115** |
| sujetos sin señales | 110 | 146 |
| grupos de duplicados | 56 | 56 |

Y el estado de la base por eje:

| eje | antes | después |
|---|---|---|
| `topic` pendientes | 1.623 | 3.454 |
| `topic` aplicadas provisionalmente | 770 | **8.668** |
| `topic` retiradas (`superseded`) | 10.169 | 2.470 |
| `document_type` aplicadas | 109 | 326 |

**Cobertura del temario de TAI:** 23 de 33 temas → **30 de 33**. Mapeos provisionales en la base:
755 → 7.881, sobre 1.944 sujetos (cada documento deja artefacto y representación).

Los tres temas que siguen sin material, con lo mejor que hay hoy sobre ellos, para que se vea que el
problema ya no es de contabilidad sino de umbral:

| tema | propuesta más fuerte viva | motor | por qué no entra |
|---|---|---|---|
| `III.3` Lenguajes de interrogación… ANSI SQL | 0,65 | determinista | banda media: necesita revisión o calibración |
| `IV.2` Administración de bases de datos | 0,55 | determinista | banda media |
| `IV.5` Conceptos de seguridad de los sistemas de información | 0,44 | fragmentos | banda baja |

## Pruebas

- `apps/api/tests/integration/test_classification_supersede.py` (6): las tres reglas del guardado, con la
  infraestructura real (SQLite y migraciones) — dos motores sobre el mismo eje no se pisan; tres hermanos
  de una pasada sobreviven los tres; un motor que cambia de opinión retira la suya con su motivo; un valor
  que el motor vuelve a sostener vuelve a `pending`; un rechazo del usuario no se revive; repetir la
  pasada no cambia nada.
- `apps/api/tests/integration/test_classification_band_apply.py` (2): con más candidatas que una página se
  aplican **todas** (antes se aplicaba una sola página) y cada tema aplicado deja su mapeo; lo que no
  llega a la banda se queda pendiente y sin mapeo.
- Suite completa: **1.068 pruebas en verde**. `ruff check` y `ruff format --check` limpios. `mypy` limpio
  en los dos ficheros tocados (los 7 avisos `no-untyped-call` de `pymupdf` están en ficheros que esta
  intervención no toca).

## Lo que NO arregla esto, y hay que decirlo

1. **Las bandas siguen sin calibrar** (Q005, `04 §8`). Que la cobertura suba de 23 a 30 no dice que las
   propuestas sean correctas: dice que la banda ya las ve. La precisión de lo que se aplica solo se mide
   con un conjunto etiquetado, y ese conjunto no existe todavía.
2. **La cobertura es provisional, no aceptada.** Todo lo aplicado es `auto_applied_provisional`, que es
   visible y reversible pero **no** es una decisión de una persona. En la pantalla de Programa se ve como
   provisional.
3. **Los tres temas que faltan son una decisión de producto, no un defecto**: aceptar tres propuestas a
   mano (la aplicación ya lo permite, con su evidencia delante) o calibrar la banda. Es el trabajo de
   revisión que mide DEBT-018.

## Un hallazgo que no he decidido, y que conviene mirar

Con los números delante aparece algo más grande que los dos defectos: **los motores proponen temas de
todas las oposiciones de la base para cualquier material**. `_profile_candidates` devuelve *todas* las
oposiciones sembradas, y el motor de temas recorre los nodos de todas ellas para cada sujeto. En esta base
hay cuatro programas (TAI, Guardia Civil, Celador SACYL y su estabilización), así que el material de TAI
recibe también mapeos del temario de la Guardia Civil:

| convocatoria del nodo | mapeos provisionales |
|---|---|
| `gc-cabos-guardias-2026` | 3.542 |
| `tai-age-2025` | **2.385** |
| `celador-sacyl-2022` | 1.678 |
| `celador-sacyl-estabilizacion-2022` | 276 |

Es decir: de 7.881 mapeos, dos de cada tres **no son del temario que el alumno está estudiando**. El
catálogo de apuntes no sufre esto (clasifica cada documento solo contra los 33 temas de TAI), pero la
pantalla de Programa de las otras oposiciones sí: enseña material de TAI como si fuera suyo.

No lo he tocado porque no es una decisión de implementación: es decidir **a qué programa pertenece un
material**, y de eso depende que la cobertura signifique algo. Las opciones, con lo que cuesta cada una:

- **Acotar los candidatos al programa asignado al material** (es lo que ya hace ADR-017 §3 con las
  preguntas: «sin asignación al programa, no hay conjunto»). Hoy no hay ninguna asignación de oposición
  aceptada (74 propuestas en ese eje, todas pendientes), así que esto dejaría la cobertura a cero hasta que
  alguien asigne el material a TAI.
- **Proponer sobre todos los programas y aplicar solo sobre el asignado**: igual que lo anterior, pero sin
  perder las propuestas de los demás (quedan pendientes, visibles).
- **Dejarlo como está** y aceptar que la pantalla de cada oposición enseña material de las demás.

Mi recomendación es la primera o la segunda, y en cualquier caso decidirlo antes de usar la cobertura como
medida de nada.

## Método, para repetir la medición

```powershell
$env:OPOFUENTE_DATA_DIR='F:\OpoFuente\datos'; $env:OPOFUENTE_PORT='8799'; $env:OPOFUENTE_HOST='127.0.0.1'
cd 'F:\temp-opofuente\opofuente-main\apps\api'
& 'F:\EspacioCodigo\opofuente\.venv\Scripts\python.exe' -m uvicorn opofuente.main:app --host 127.0.0.1 --port 8799

# una pasada completa y su medida (cobertura por tema, propuestas por eje y estado):
cd 'F:\EspacioCodigo\proptech-access-control\docs\opofuente\_oficial'
& 'F:\EspacioCodigo\opofuente\.venv\Scripts\python.exe' pasada_medida.py
```

La pasada tarda unos **30 minutos** para 2.132 sujetos (0,7 sujetos por segundo con la máquina ocupada
por otras dos pruebas a la vez; sola va más rápido). El cuello no es el motor de temas —6 milisegundos por
sujeto— sino el determinista, que compara el texto entero con cada título del programa.
