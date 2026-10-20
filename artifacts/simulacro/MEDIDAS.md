# El simulacro y el reloj, medidos (§3.3 y §3.4)

**F37 · 17 de octubre de 2026 · rama `f37-simulacro`, base `main = d312be0`**

Las cifras de este fichero están **medidas**, no heredadas. La referencia de partida es la del
recorrido (`artifacts/recorrido/RECORRIDO.md`, §5.5): **142,3 s** de `POST /student/mock-exams`, con
la pantalla sin decir nada y el recorrido rindiéndose a los 45 s. La sesión sí se creaba (106
preguntas).

---

## 1 · Dónde se iba el tiempo (lo que el documento pedía medir)

El simulacro **no tardaba por pintar ni por el modelo**: tardaba por **consultas**. Contadas con el
gancho de SQLAlchemy sobre el motor (`artifacts/simulacro/medir.py`), el montaje hacía:

| | consultas |
|---|---|
| **Antes** (`main`, misma copia de la base) | **154.231** |
| **Después** | **441** |

Y no eran consultas distintas: eran **la misma consulta repetida una vez por pregunta**. Las cinco
que más se repetían, con su número de repeticiones:

| repeticiones | consulta |
|---|---|
| **13.828** | el conjunto con sus tres `count(*)` (preguntas, reservas, incompletas) y sus claves |
| **13.793** | la fila de la pregunta, sus opciones, sus explicaciones y su entrada de la clave |
| **13.793** | las opciones de esa pregunta |
| **13.793** | el recuento de explicaciones de esa pregunta |

Era un **N+1 de manual**: la composición recorría el banco **pregunta a pregunta** —su fila, sus
opciones, su conjunto, su clave, sus exclusiones— en lugar de leerlo por lotes. En el simulacro
completo el banco de los 33 temas son **13.793 preguntas** de 246 conjuntos, así que el coste no lo
ponía el tamaño del test (106 preguntas) sino el tamaño del banco.

**Dónde se va el tiempo que queda**, cronometrado lectura a lectura (`artifacts/simulacro/donde.py`),
ya arreglado:

| lectura por lotes | tiempo | veces |
|---|---|---|
| `question_ids_of_nodes` (las preguntas de los 33 temas, en una consulta) | 1,41 s | 1 |
| `questions_by_ids` (las 13.793 fichas, sin opciones) | 0,75 s | 1 |
| `sets_by_ids` (los 246 conjuntos con sus recuentos) | 0,16 s | 2 |
| `excluded_question_ids_by_set` | 0,03 s | 2 |
| **total medido de lecturas** | **2,36 s** | |

El resto hasta el total son los filtros en memoria y el alta de la sesión (las 106 preguntas
congeladas con su clave).

## 2 · El arreglo, en la consulta

**Cinco lecturas por lotes en el repositorio** (`question_repository.py`), cada una una consulta para
todo el lote y **en tandas** de 900 identificadores (SQLite admite 999 en un `IN`):

1. `question_ids_of_nodes` — las preguntas de **todos** los nodos de la parte, en una consulta.
2. `questions_by_ids` — las fichas de esas preguntas, con `include_options=False`.
3. `sets_by_ids` — los conjuntos con sus recuentos, agrupados en tres consultas para todo el lote.
4. `active_key_entries_by_set` — **solo la plantilla activa** de cada conjunto, con su desenlace por
   pregunta. (Antes: las 584 versiones de plantilla del banco, para acabar usando 246.)
5. `excluded_question_ids_by_set` y `options_by_question_ids` — las exclusiones y las opciones, esta
   última **solo de las preguntas que sobreviven a los filtros**.

**Y no se ha puesto una caché por delante ni un `async` para que no bloquee**: el trabajo sigue
haciéndose entero y de forma síncrona, con menos viajes. Lo único que se guarda es lo ya leído
**dentro de la misma composición**: el supuesto del simulacro sale de temas que la primera parte ya
recorrió, así que antes se leía el banco dos veces para montar una sesión y ahora una.

**Lo que no cambia, y hay que decirlo**: el orden en el que se recorren las preguntas. El reparto
depende de ese orden, así que se recorre **una lista** (el orden del programa) y no un `set` de
Python, cuya iteración no está garantizada. Está comprobado con
`artifacts/simulacro/reproducibilidad.py`: **la misma semilla elige las mismas preguntas**, y sin
semilla el orden del programa es el mismo en dos pasadas.

## 3 · Los tiempos

| | antes | después |
|---|---|---|
| **referencia del recorrido** (servidor real, sin instrumentación) | **142,3 s** | — |
| **mismo arnés, `main` vs esta rama** (`medir.py --sin-contador`, copia idéntica de la base) | **126,9 s** | **3,2 s** y **3,7 s** (dos pasadas) |
| con el contador de consultas encendido (lo que cuesta contar 154.000 sentencias) | 183,7 s / 98,5 s | **6,2 s** |
| `donde.py` (arnés completo con cronómetros) | — | **4,9 s** |
| **consultas** | **154.231** | **441** |

La diferencia entre 142,3 y 126,9 son los arneses (el recorrido mide con `uvicorn` y HTTP; estas
cifras, con el cliente de pruebas en el mismo proceso). Por eso **el antes y el después que se
comparan se han medido con el mismo arnés y sobre la misma copia**: 126,9 s → 3,2 s es −97,5 %.

### El reloj del servidor y el de la pantalla, separados

El montaje se ha medido **en el navegador y en el servidor a la vez**
(`apps/web/tests/screens/simulacro.spec.ts`). El servidor publica lo que tardó la composición en una
cabecera `Server-Timing`, que se añadió para esto: sin las dos cifras no se puede decir qué parte es
consulta y qué parte es pintura.

| pasada | navegador | servidor (composición) | lo que se va en pintar y viajar |
|---|---|---|---|
| 1 | **3.812 ms** | **3.734 ms** | 78 ms |
| 2 | **4.523 ms** | **4.443 ms** | 80 ms |

**El tiempo es la consulta, no la pantalla**: entre el 97 % y el 98 % de la espera es la composición
en el servidor. Consecuencia práctica: lo que quede por bajar hay que bajarlo del banco, no del
navegador. (La segunda pasada es más lenta por la carga de la máquina en ese momento; las dos están
por debajo de los 5 s, la segunda con **477 ms de margen** — conviene saberlo: el margen no es
enorme.)

## 4 · Simulacro y examen oficial: el reloj y «Abandonar»

- **Reloj visible** en el runner del alumno, que es **el mismo componente** para el simulacro y para el
  examen oficial: «Quedan 1:50:00» y «Llevas 10:00», con aviso a los cinco minutos y aviso aparte
  cuando se agota.
- **De dónde sale la hora**: del servidor. La sesión lleva `started_at` y un campo nuevo
  **`server_now`**, del **mismo reloj**, así que la resta `server_now − started_at` mide el tiempo que
  lleva corriendo el test con un solo reloj. El del navegador solo mide el trozo que pasa desde que
  llegó la respuesta. Un equipo con la hora mal puesta cuenta lo mismo que uno en hora.
- **El reloj informa, no decide**: llegar a cero no bloquea la pantalla. Quién decide qué pasa al
  agotarse el tiempo es el servidor, y esa regla no se ha inventado en el navegador.
- **«Abandonar» con confirmación**, que dice cuántas llevas y qué pasa con ellas.

### La decisión sobre el intento abandonado, escrita

**Se conserva y no cuenta.** Lo que ya se contestó queda guardado, la sesión pasa a `abandoned` y
**no cuenta** ni como test terminado ni como nota (Inicio y Progreso solo miran los terminados).
Solo se borra la sesión en la que **no se contestó nada**, porque ahí no hay historial que perder y
dejar una fila vacía es lo que llenó el banco de sesiones «sin empezar» el 5 de octubre.

**Y se puede volver a salir**, que es la mitad que importa: la sesión abandonada **se abre**, la
pantalla dice qué es, no deja contestar y ofrece «Salir». Abandonar dos veces devuelve **200** con el
mismo parte (no 500), y una sesión **terminada** no se convierte en abandonada: tiene su resultado.

## 5 · Las capturas

`apps/web/tests/screens/simulacro.spec.ts`, contra la copia de la base, a **1280 y 390**, con
**0 violaciones de axe y 0 errores de consola** exigidos por la propia prueba (no mirados en el PNG).
La corrida buena: **4 de 4 pasan**.

| qué | 1280 | 390 |
|---|---|---|
| el simulacro montado, con su reloj | `simulacro-con-reloj-1280.png` | `simulacro-con-reloj-390.png` |
| mientras monta («Preparando tu simulacro…») | `simulacro-preparando-1280.png` | `simulacro-preparando-390.png` |
| el test abandonado | `test-abandonado-1280.png` | `test-abandonado-390.png` |
| el examen oficial con su reloj | `examen-oficial-con-reloj-1280.png` | `examen-oficial-con-reloj-390.png` |

Lo que la prueba **comprueba**, además de retratar:

1. el simulacro se monta en **menos de 5 s**, medido en el navegador **y** en el servidor;
2. mientras monta, el botón está **ocupado** y la pantalla dice «Preparando tu simulacro…»;
3. el reloj del simulacro enseña **lo que queda y lo que llevas**; el del examen oficial, también
   (medido: «Quedan 1:59:59 · Llevas 0:00», los 120 minutos de su convocatoria);
4. «Abandonar» **pide confirmación**, y si se cancela no pasa nada;
5. **abandonar y volver a entrar funciona**: la sesión se abre, dice qué es, no deja contestar y
   ofrece «Salir»;
6. **abandonar dos veces devuelve 200** con el mismo parte (`este test ya estaba abandonado: sigue
   conservado para repasar y no cuenta como test hecho`), no 500 ni 404;
7. y la sesión abandonada **no sale** como el test a medias de Inicio.

Los PNG no se rastrean (se rehacen en cada corrida, `.gitignore`); lo que se rastrea es esta medición
y el guion que la produce.

## 6 · Lo que este arreglo NO hace

- **No pone un tope de tiempo que corte el test.** El reloj enseña; el servidor guarda el límite. Que
  al agotarse el tiempo se cierre la sesión sola es otra decisión (y hoy no está tomada).
- **No arregla el ciclo de contestar** (§3.2): está en `f36-contestar`, sin fusionar, y aquí no se ha
  tocado. El «peor arnés» del montaje **no** se ha reutilizado.
- **No toca la base real.** Todo se ha medido sobre una copia hecha con `snapshot_database` (API de
  respaldo de SQLite, no copia de fichero): 2.748.612.608 bytes, SHA-256
  `622aaa6fbe9cb200c5ee0f25f3e75f46d6adcf07d50ae098714d47f5abe3f238` — **el mismo que publicó el
  recorrido para su copia**—, y las migraciones `0039` y `0040` aplicadas encima.
