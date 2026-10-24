# El remate de la fase 3, punto por punto

**De:** DeepSeek · **Para:** Claude, por delegación del propietario · **24 oct 2026**
**Documento que manda:** `docs/FASE-3-REMATE-2026-10-24.md`

**Base de partida:** `main = 20d24fe` (el documento del remate commiteado).

Aquí se apunta **lo que se decide y por qué**, para que la decisión se pueda revisar o deshacer sin
reconstruirla. **Un punto solo se da por hecho cuando se cumple en la base real y en la app que
arranca `scripts\api.ps1`**, no en una siembra de pruebas.

---

## Punto 1 · Las 5.939 explicaciones privadas, archivadas

### Lo que pasó, medido

```
copia antes de M1:  11.315 privadas + 1.609 generadas
base real después:   5.376 privadas + 9.007 generadas
```

**`--sustituir-lo-privado` reemplazó 5.939 privadas en la misma fila.** Comprobado fila a fila: **el
`id` no cambió** — la generada ocupó la fila de la privada — y **el texto original solo quedaba en la
copia**.

### La decisión: se archivan, no se borran

**Estado nuevo `archived` + el único por pregunta pasa a parcial.** **La privada y la generada son
la misma fila hoy**, así que archivar **no puede ser un `update`**: hay que insertar una fila nueva,
y para eso hacen falta dos cosas que la 0047 añade:

1. **el `CHECK` de estados tiene que admitir `archived`** — hoy solo admite `draft`, `reviewed` y
   `rejected`, así que el original **no se habría podido guardar**;
2. **el único `uq_explanation_question` tiene que dejar de cubrir las archivadas** — si no, la
   segunda fila de la misma pregunta choca.

**Sigue habiendo una sola explicación viva por pregunta**: el índice pasa a cubrir
`option_stable_key IS NULL AND status <> 'archived'`. **Y lo que se sirve no cambia**: `explanations_of`
filtra las archivadas.

### Lo que se hizo

- **`0047_explicaciones_archivadas`**: reconstruye la tabla **a mano**, con el `CREATE TABLE` entero.
  **No con `batch_alter_table`**: el modo por lotes refleja la tabla con SQLAlchemy, y **SQLAlchemy
  no refleja los `CHECK` de SQLite**, así que habría borrado `ck_explanation_origin`,
  `ck_explanation_text` y `ck_explanation_generated` **sin que nadie lo notara al día siguiente**.
- **`tools/recuperar_explicaciones_privadas.py`**: copia las privadas de la copia a la base real con
  `status = 'archived'`, con comprobación de referencia **fila a fila**, `--aplicar` obligatorio para
  escribir, e **idempotente** (relanzarlo no duplica).
- **La instantánea verificada**: `base-real-20261024-222022-antes-de-recuperar-privadas.sqlite3`,
  2.641,7 MB, `integrity_check ok`.

### La cifra, contada en la base real

```
revision            0047_explicaciones_archivadas
explicaciones       20.322
  generadas          9.007
  privadas          11.315   <- las 11.315 de antes de M1, todas
estado
  draft             14.383
  archivadas         5.939   (todas privadas)
vivas por pregunta       0   (ninguna pregunta con dos vivas)
preguntas que el alumno ve con explicación   14.383   (las mismas que antes)
```

**Y relanzar el importador da `candidatas: 0`.** **La decisión se puede deshacer**: bajar la 0047
borra las archivadas y vuelve la tabla anterior (dicho en el `downgrade`).

### Dónde se apuntó

- **`DEBT.md`**: la entrada de la sustitución, cerrada con su cifra.
- **`PARA-EL-PROPIETARIO.md`**: qué se recuperó y cómo se deshace.

---

## Punto 2 · El repaso de tarjetas, en el menú

### Lo que se hizo

- **`/repaso` entra en el menú del alumno** (`navigation.ts`): antes **solo se llegaba desde «Hoy»**,
  así que una pantalla que existe no se encontraba.
- **La portada pasa a llamarse «Hoy»** en el menú, que es lo que sirve `/`.

### Lo comprobado, en la app que arranca `scripts\api.ps1` y sobre la base real

```
GET /api/v1/cards/queue   ->  200
claves de la respuesta:  tarjetas, total
tarjetas servidas:       9
la primera:  {"front":"¿Qué puerto utiliza HTTPS?","back":"443","citation":"443",
              "due_at":"2026-10-22T14:02:40","interval_days":0,"repetitions":0}
```

**Sirve tarjetas de verdad, con su cita y su fecha de vuelta**, no de una siembra de pruebas. **Nueve
porque nueve están vencidas hoy**; el tope de 60 está en `cola_del_dia` y **no se ve recortado porque
no hay más vencidas**.

**El teclado ya estaba**: espacio para dar la vuelta y 1 a 4 para responder (`RepasoPage`).

### Lo que NO está, y se dice

**La cola sirve tarjetas, no fallos vencidos.** `cola_del_dia` **ya sabe entrelazar las dos listas y
recortar por el tope**, y `review_items` **ya existe** en la base; **lo que falta es que
`CardService.cola` los traiga y que la respuesta y la pantalla sepan de dos tipos de entrada**. **Es
un cambio de contrato de la API, no un adorno**, así que no se hace de paso dentro de este punto.

**Lo que el propietario pidió de este punto —que se llegue desde el menú y que sirva las tarjetas—
está hecho y medido.**

---

## Punto 3 · La portada es «Hoy», y `/inicio` se va

### Lo que se hizo

- **`StudentHomePage` borrada** del código, con su prueba (`studentInicio.test.tsx`).
- **La ruta `/inicio` ya no pinta nada**: entra en `ROUTE_REDIRECTS` como **`/inicio -> /`**.
  **Se redirige en vez de dejar un 404** porque hay marcadores y enlaces dentro de la app que siguen
  apuntando ahí.
- **`apiCaida.test.tsx`** montaba `StudentHomePage` para probar el aviso de API caída: **ahora monta
  `HoyPage`** y comprueba su texto de error (`No se pudo leer el plan. Reintenta en un momento.`).
- **`shell.test.tsx`**: tres aserciones afirmaban «siete entradas». **Ahora son ocho** —entra
  «Repaso»— y la primera se llama «Hoy». **Y la lista de redirecciones incluye `/inicio -> /`.**

### Lo medido

```
tsc --noEmit        0
vitest              54 ficheros · 486 pruebas · todas en verde
```

**Una prueba menos que antes** (54 en vez de 55) porque `studentInicio.test.tsx` se ha ido **con la
pantalla que probaba**, que es lo que manda el documento.

---

## Punto 4 · Los supuestos en el simulacro — **diseñado, no hecho**

### Lo que hay hoy, medido

**El simulacro completo monta 80 + 5 de todos los temas y 20 + 5 del bloque elegido** —`create_mock_exam`,
`student_service.py:810`—, **y las 20 preguntas de la segunda parte salen de los TEMAS del bloque, no
de un supuesto**. **La sesión lo declara** (`practical_case_origin`), pero **lo que se pinta son 20
preguntas de tema**: por eso el simulacro «sale con 85 preguntas y sin supuesto».

**Los 18 supuestos están en la base** y **sus 450 preguntas son versiones de pregunta de verdad**
(`practical_case_questions.question_version_id` → `question_versions`), **con sus opciones y su clave**.
**9 del bloque III y 9 del IV.**

### Lo que hay que hacer, y por qué no hace falta migración

**El enunciado no hay que guardarlo en la sesión**: se **deduce** de las preguntas de la parte
—`select practical_case_id from practical_case_questions where question_version_id in (…)`—, así que
**no hay columna nueva ni migración**.

1. **`PartSpec.question_version_ids`** (opcional), y **`_candidatas`** devuelve exactamente esas cuando
   viene, en vez de repartir por nodo. **Es el sitio por donde pasan todas las composiciones**, así que
   no hay un segundo camino que corregir.
2. **`create_mock_exam`**: para la variante completa, **elegir un supuesto del bloque pedido** y montar
   la segunda parte con sus **25** preguntas, **sin reservas** (el supuesto no las lleva).
3. **La vista**: el enunciado del supuesto, deducido como arriba, para que la pantalla lo enseñe.
4. **La pantalla**: enunciado a la izquierda y sus 25 preguntas a la derecha, **y nota por parte** —la
   primera y la segunda se puntúan por separado, que ya está en `StudentMockExamPartSchema`—.
5. **En «Exámenes»**, los supuestos de los oficiales cuando existan.

**Nada de esto se ha escrito**: **se para aquí para no dejar la composición a medias**, que es la que
corrige todos los modos de sesión.

## Estado al parar esta tanda

```
punto 1  HECHO y medido en la base real
punto 2  HECHO y medido en la app que arranca scripts\api.ps1 (9 tarjetas reales)
punto 3  HECHO (tsc 0 · vitest 54 ficheros, 486 pruebas)
punto 4  diseñado, sin empezar
puntos 5 a 9  pendientes
main = 77ea71a · árbol limpio
```

---

## Punto 4 · El hallazgo que lo explica todo: **los supuestos no tienen clave**

### Lo medido, en la base real

```
preguntas de supuesto (18 supuestos × 25)     450
con entrada de plantilla                         0
con clave derivada                               0
key_reliability de sus conjuntos        'dudosa' en todos
```

**Las 450 preguntas de los 18 supuestos no se pueden corregir**: tienen enunciado y cuatro opciones,
**y ninguna letra guardada**. Por eso el simulacro «sale con 85 preguntas y sin supuesto»: la
composición pide el supuesto, **la política de claves lo descarta entero** —con razón: una pregunta
que no se puede corregir no se pone en un examen— **y la segunda parte se queda en cero**.

### La causa, en el código

`tools/supuestos.py` creaba `QuestionVersionRecord` y sus `OptionVersionRecord`, **y tiraba
`pregunta.clave`**, que el dominio **sí trae** (`PreguntaPropuesta.clave`). **El generador acertó y el
guardado no lo apuntó.**

### Lo que se ha hecho

- **`PartSpec.question_version_ids`** y **`_candidatas`** los respeta: **una parte puede traer sus
  preguntas exactas** (el supuesto), en su orden, sin repartir por nodo. Todo lo demás —política de
  claves, lectura por lotes, reparto, reservas— sigue igual, y **no hay un segundo camino de
  composición**.
- **`practical_case_for_block`**: el supuesto del bloque, **el oficial primero**, con sus preguntas en
  el orden del enunciado.
- **`create_mock_exam`**: si hay supuesto con preguntas, la segunda parte son **sus 25**, **sin
  reservas**; si no, se cae a las 20 del bloque y **la sesión lo declara** (`bloque`).
- **`tools/supuestos.py` guarda la clave**: una plantilla `active` por supuesto y una entrada por
  pregunta con su letra. **Las próximas generaciones nacerán corregibles.**

### Lo que falta, y es un dato, no código

**Las 450 preguntas ya guardadas siguen sin letra**, y el dato **no está en la base**. La vía es
**pedírselas al modelo** —el mismo segundo pase que ya existe, `responder_a_ciegas`, que contesta sin
ver la clave— y escribir la plantilla con lo que devuelva. **Coste estimado: 18 llamadas, del orden de
0,05 $.**

**No se ha ejecutado en esta tanda**: se acaba el margen. **Es lo primero de la siguiente**, y hasta
entonces **el simulacro sigue cayendo a las 20 preguntas del bloque, diciéndolo**.

### Las 450 claves, recuperadas — y el simulacro ya lleva el supuesto

**`tools/claves_de_supuestos.py`**: a cada supuesto sin plantilla se le piden las letras al modelo con
**el pase a ciegas que ya existía** (`responder_a_ciegas`), **mandándole los apuntes del bloque como
material y nunca una clave**. Con lo que contesta se escribe la plantilla: **una versión `active` por
conjunto —con su `approved_at`, que `ck_key_approved` exige— y una entrada `keyed` por pregunta**.

```
antes:   0 de 450 con clave
después: 450 de 450 · 18 plantillas activas
```

**Y el fallo que salió por el camino**: `status = 'active'` **exige `approved_at`**. **La herramienta
de los supuestos nuevos habría fallado igual**, así que se arregló en las dos.

**El simulacro, en la app real (`scripts\api.ps1`) y sobre la base real:**

```
POST /api/v1/student/mock-exams  {"variant":"full","case_block":"IV"}

practical_case_origin: supuesto
total_questions:       110
por parte:  primera_parte 85 (5 de reserva)  ·  segunda_parte 25 (5 de reserva)
de la segunda parte, del supuesto:  25 de 25
```

**Antes de las claves, la segunda parte se quedaba en cero y el simulacro caía a veinte preguntas de
tema.** **Ahora son las veinticinco del caso, con sus cinco reservas.** **Queda la pantalla**: el
enunciado a la izquierda y las 25 preguntas a la derecha.

### La pantalla: el caso con sus preguntas

**El enunciado viaja con la sesión** (`SessionConfiguration.practical_case_statement`, congelado como
todo lo demás) **y no se busca después**: sus veinticinco preguntas dicen «con los datos del caso,
conteste», y **sin el caso delante no se pueden contestar**. Se sirve en la respuesta y se pinta en el
runner, antes de la pregunta, en un recuadro con su propio desplazamiento; **en pantalla ancha va a la
izquierda con la pregunta a la derecha** y en estrecha encima.

**Lo que no se ha hecho**: la nota por parte ya existe en el resultado (`StudentMockExamPartSchema`),
pero **no se ha tocado la pantalla del resultado** para destacarla. Se anota como pendiente.

```
tsc --noEmit  0  ·  vitest  54 ficheros en verde
```
