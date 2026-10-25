# Lo que ve el alumno, punto por punto

**Documento que manda:** `docs/FASE-3-LO-QUE-VE-EL-ALUMNO-2026-10-25.md`
**Base de partida:** `main = 65eba2e` (el documento commiteado).

Aquí se apunta **lo que se decide, lo que se mide y lo que se para**, para que se pueda revisar sin
reconstruirlo. **Un punto solo está hecho cuando se cumple en la base real y en la app que arranca
`scripts\api.ps1`.** **Y una captura solo vale si su texto sale de la base real**, comprobado por
programa.

---

## Punto 1 · Las tarjetas al alumno — **PARADO por su propio criterio**

### Lo que se construyó

- **`0048_motivo_de_borrador`**: una columna `draft_reason` en `cards`. **Una tarjeta que no se sirve
  sin decir por qué es una tarjeta que nadie va a arreglar.**
- **`tools/activar_tarjetas.py`**: comprueba **las cuatro condiciones del documento, por programa** —
  la respuesta aparece literalmente en el hecho (normalizando tildes y espacios), tiene **25 palabras o
  menos**, **la pregunta no la contiene**, y **no hay otra tarjeta del mismo tema con la misma
  pregunta**—. Las que pasan van a `active`; las que no, **se quedan en `draft` con su motivo**.
- **El tope de nuevas al día**: `--limite` (20 por defecto) o `OPOFUENTE_TARJETAS_NUEVAS_AL_DIA`, para
  que el primer día no salgan cinco mil. **No se pierde ninguna**: se sirven poco a poco.
- **El contraste a ciegas**: la herramienta saca **50 tarjetas al azar**, y **el modelo las contesta con
  el hecho delante y sin ver el reverso**.

### Lo que se midió, en la base real

```
tarjetas generadas en borrador      5.274
cumplen las cuatro condiciones      5.073
se quedan en borrador con motivo      201
```

**Y el contraste**:

```
coinciden 40 de 50  (80 %)
POR DEBAJO DEL 90 %: se para y no se activa nada
```

**Las diez que no coinciden son preguntas que el hecho no contesta del todo** —«¿Cuáles son los
lenguajes de un SGBD?» con una respuesta enumerativa, «¿Qué dimensiones recoge el artículo 6 del
ENI?»—: **el reverso está en el hecho, pero contestar la pregunta pide más de lo que el hecho dice.**

### La decisión, que es la del documento

**El documento dice: «Si coincide < 90 %, para y apúntalo.»** **80 % es menos de 90, así que se para.**

**Nada se ha activado.** El alumno sigue viendo **9 tarjetas**, y las 5.274 siguen en `draft`. **Lo que
sí queda es el instrumento**: la comprobación, el motivo y el contraste, listos para cuando la decisión
sea otra.

**Copia verificada antes de tocar nada**:
`base-real-20261025-143435-antes-de-tarjetas.sqlite3`, `integrity_check ok`.

### Lo que esto significa para el punto 2

**El punto 2 (la pantalla de repaso) sigue teniendo sentido** —la respuesta se enseña antes de tiempo y
las etiquetas salen pegadas—, **pero con 9 tarjetas el repaso no es un repaso**. **No se ha empezado**:
arreglar la pantalla para servir nueve tarjetas es arreglar el marco de un cuadro que no está.

### Lo que queda por decidir, y no es mío

**El listón del 90 % lo puso el documento.** Con estos hechos, **el modelo acierta 80 %** — y eso no es
un fallo de la herramienta: es que **muchas de las 5.073 tarjetas preguntan más de lo que su hecho
contesta**. Las salidas posibles, para quien decida:

1. **bajar el listón** y servir tarjetas con un 80 % de coincidencia — **no se ha hecho**: sería cambiar
   el criterio que el documento fija, no el código;
2. **regenerar las tarjetas** con la pregunta ceñida al hecho;
3. **activar solo las que el contraste acierta**, y dejar el resto en borrador con ese motivo.

**Las tres son decisiones de producto, y la primera y la segunda cuestan dinero de API.**

---

## Punto 2 · La pantalla de repaso

### Lo que estaba mal, y por qué

**Las clases estaban en el JSX y ninguna en el CSS.** `.repaso`, `.tarjeta`, `.tarjeta__anverso`,
`.tarjeta__reverso`, `.repaso__boton`… **no tenían ni una regla**, así que la nota del botón salía
pegada a su etiqueta —«Otra vezno me salía»— porque `<kbd>`, el texto y el `<span>` caían en la misma
línea. **No era un fallo de la tarjeta: era que la pantalla no se había escrito nunca.**

### Lo que se hizo

- **Los estilos, con los tokens del diseño**: la tarjeta con su borde y su relleno, el reverso en
  verde de acierto, la cita con su filete, y **la pista de cada nota en su propia línea**
  (`display: block`), que es lo que la pone en dos: «Otra vez» / «no me salía». **Cuatro notas en
  fila, dos en el móvil.**
- **El botón «Ver la respuesta»**: la respuesta se daba solo con el espacio, **y en el móvil no hay
  espacio**. Ahora se da con el botón o con la tecla, y **las cuatro notas siguen deshabilitadas hasta
  entonces**.
- **El resumen al terminar**: cuántas has repasado, **cuántas vuelven mañana** y **«Volver a Hoy»**. Antes
  decía «hecho» y dejaba al alumno sin saber qué había pasado.

### Cómo se comprobó, y por qué así

**Con una prueba, no mirando la captura** (`tests/unit/repaso.test.tsx`): monta la pantalla con un
`fetch` simulado y comprueba **que la respuesta no está en el documento**, que las cuatro notas están
deshabilitadas, que **el botón la enseña** y que entonces se habilitan. **Lo que la prueba no puede
comprobar es que la pista salga en dos líneas** —eso es estilo y se ve en la captura del punto 8—, y se
dice en el propio fichero.

```
tsc --noEmit  0  ·  vitest  486 pruebas + la nueva, todas en verde
```

**Y en la app**: copia nueva de la base real (`recorrido-3`, 2.656,1 MB, `integrity ok`, 0048) y
paquete construido a las 14:43:17; **las capturas de `/repaso` pasan** (2, escritorio y móvil).

---

## Punto 3 · Los fallos vencidos en la cola del día — **la mitad del servidor, hecha**

### Lo que se hizo

- **`CardService.cola_del_dia`**: la cola mezcla **las tarjetas vencidas y los fallos vencidos** con
  `cola_del_dia`, que **ya sabía entrelazarlos y recortar por el tope**. **El tope de 60 es de las dos
  cosas juntas**, no de cada una.
- **Los fallos se sirven enteros** —enunciado y opciones, y **la clave no viaja**: se corrige en el
  servidor—. `DueItemView` ya los traía; solo no se usaban.
- **La fábrica** pasa el repositorio de repasos al servicio (era opcional a propósito: sin él, la cola
  sigue sirviendo solo tarjetas, que es lo que hacía antes).
- **El contrato**: `CardQueueSchema` gana `fallos`, y **`total` cuenta la cola entera** —tarjetas y
  fallos—: contar solo las tarjetas mentía hacia abajo. `openapi.json` y `openapi.d.ts` regenerados.

### Lo medido, en la app que arranca `scripts\api.ps1` y sobre la base real

```
GET /api/v1/cards/queue
  tarjetas: 9  ·  fallos: 5  ·  total: 14
  primer fallo: «Indique cuál de los siguientes principios se garantiza en el artículo…» · 4 opciones
```

**Antes de este punto la cola servía 9 y los 5 fallos vencidos no aparecían en ningún sitio.**

### Lo que falta, y por qué no se ha hecho

**La pantalla**: el repaso tiene que enseñar cada fallo **como pregunta de test, con su explicación al
corregir**. **Contestar una pregunta exige hoy una sesión** —`POST /student/sessions/{id}/answers`—, y
**no hay una ruta que corrija una pregunta suelta**. Así que el fallo se sirve con su enunciado y sus
opciones, **pero el repaso todavía no lo pinta**: hacerlo bien pide **una ruta de corrección de una
pregunta**, que es contrato nuevo y no un adorno.

**Se dice en vez de pintarlo a medias**: un fallo que se enseña y no se puede corregir es peor que un
fallo que no se enseña.

### La corrección de un fallo suelto, hecha y probada

**La ruta nueva**: `POST /api/v1/cards/queue/failures/{question_version_id}` con `{"option_key": "c"}`.
**Corrige sin montar una sesión**, que era el rodeo: contestar una pregunta de la cola no necesita una
sesión entera.

- **La clave no viaja al cliente**: se compara en el servidor y **solo se devuelve al corregir**, con la
  letra que valía, **la explicación y su cita**.
- **La clave derivada manda**; si no la hay, se usa la entrada de la plantilla activa del conjunto. **La
  explicación es la viva**: las archivadas del remate no se sirven.

**Probado en la app real, sobre la base real**:

```
cola: 9 tarjetas + 5 fallos
fallo 557144f9 (el único de los cinco con clave)
  con «a» -> correcto: False · clave: c · explicación: sí · cita: sí
  con «b» -> correcto: False · clave: c · explicación: sí · cita: sí
```

### Y un hallazgo que importa más que la ruta

**De los 5 fallos vencidos, 4 no tienen ninguna clave** —ni derivada ni entrada de plantilla—:

```
227597e7: derivada=0 plantilla=0 ·  f1f56b40: 0 0 ·  03a80081: 0 0
4e689615: 0 0                        ·  557144f9: 0 1
```

**Los cinco tienen explicación**, pero **cuatro no se pueden corregir**. **La ruta lo dice con un 404 y
el motivo**: «No existe clave de la pregunta con ese identificador». **Es preferible a corregirlos con
una letra inventada.**

**Lo que eso significa**: **la cola del día le va a ofrecer al alumno cuatro preguntas que no puede
corregir**. **Antes de pintarlas hay que decidir qué se hace con ellas** —sacarlas de la cola, o
corregirlas sin nota—, y **no es una decisión de código**.

### Lo que queda del punto 3

**La pantalla**: el repaso tiene que pintar el fallo con sus opciones y su corrección. **La ruta está y
funciona**; **lo que falta es la mitad de la interfaz**, y **no se ha hecho porque los cuatro fallos sin
clave la dejarían a medias**.

### La pantalla, hecha

- **La cola deja fuera los fallos que no se pueden corregir** —4 de los 5 vencidos—, comprobado **en el
  servidor**, porque **la clave no viaja y la pantalla no puede saberlo**. **Un fallo que se enseña y no
  se puede dar por bueno es peor que uno que no se enseña.** Decisión reversible, apuntada aquí.
- **El repaso los pinta como preguntas de test**: el enunciado, sus opciones con su letra, y **al
  elegir** llegan el acierto, **la letra que valía** y **la explicación con su cita**. Antes de
  contestar no se dice nada, que es lo que hace un test.

**Medido en la app real**: `tarjetas: 9 · fallos: 1 · total: 10`. **El único fallo con clave entra; los
cuatro sin clave se quedan fuera.**

`tsc 0 · eslint 0 · 487 pruebas en verde`.
