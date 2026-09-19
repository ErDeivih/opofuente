# ADR-013 — Rutas añadidas al contrato de la API

**Estado:** propuesto (pendiente de ratificación del propietario)
**Fecha:** 19 de septiembre de 2026
**Contexto de la decisión:** cierre de cada slice, recogido aquí en la revisión de S00–S11.

## Contexto

`08_API-CONTRACT.md` fija las rutas de la API **por sección**, y cada slice implementa las suyas. Al
construir la interfaz y las pruebas aparecieron rutas que el contrato no lista pero que el producto
necesita para no hacer algo peor: por ejemplo, listar las sesiones de estudio abiertas, o comparar dos
versiones de un documento. En todos los casos la alternativa era peor que la ruta:

- **no tenerla** dejaba la pantalla sin datos que sí existen (una sesión en marcha invisible, una lista
  de decisiones que no se puede recorrer);
- **deducirla en el cliente** habría puesto lógica de negocio en el navegador, contra la arquitectura
  del proyecto;
- **meterla en una ruta existente** habría cambiado el significado de una ruta ya documentada.

Cada slice las declaró en su ficha y en el propio código (`summary` de la ruta), así que no son rutas
escondidas: son rutas **fuera del contrato y señaladas**. Lo que faltaba era una decisión única que las
recogiera, porque estaban repartidas en siete documentos y se leían como «pendiente de ratificación»
siete veces, sin una lista que se pudiera aprobar de una vez.

## Decisión

Se mantienen las rutas añadidas, todas bajo `/api/v1`, con esta tabla como registro único. Ratificarlas
significa aceptar que el contrato tiene una lista adicional a la que él mismo fija; rechazar alguna
significa retirarla y asumir la consecuencia escrita en la última columna.

| Ruta | Slice | Por qué existe | Qué se pierde si se retira |
|---|---|---|---|
| `POST /classification-runs` | S04 | Lanzar el motor determinista sobre un lote y ver su informe; sin ella, clasificar no se puede pedir desde la interfaz | la pantalla de Revisión no puede pedir una clasificación nueva |
| `GET /documents/{id}/diff` | S05 | Comparar dos versiones del mismo documento y decir qué sección cambió | la pestaña «Versiones y diff» se queda sin diff |
| `GET /study-sessions` | S07 | Listar las sesiones (en marcha y terminadas) de una oposición | no se puede retomar una sesión sin recordar su id |
| `POST /study-sessions/{id}/recalculate` | S08 | Recalcular con una clave corregida y conservar el resultado anterior | una clave mal importada cambiaría notas a escondidas o no se podría corregir |
| Cinco rutas de §8 (búsqueda y RAG) | S09 | El contrato de §8 fija el comportamiento; la interfaz necesita además leer una consulta guardada con su recuperación completa | la vista «Preguntar» no podría auditar de dónde salió una afirmación |
| Seis rutas | S10 | Cola de errores, conceptos, exportación y su historial | la pantalla de Errores no tendría con qué trabajar |
| Cinco rutas | S11 | Cambios pendientes, confirmar, descartar, derivados y su resolución | la pantalla de Cambios no existiría como tal |

Las rutas concretas de S09, S10 y S11 están enumeradas en las fichas de sus slices
(`docs/slices/S09.md`, `S10.md`, `S11.md`), cada una con lo que aporta; esta tabla no las repite una a
una para no duplicar lo que ya está escrito donde se decidió.

## Consecuencias

- **El contrato deja de ser la lista completa de rutas.** Quien lea `08_API-CONTRACT.md` y compare con
  el OpenAPI verá diferencias, y esta es la lista que las explica. Las alternativas eran peores: o
  rutas escondidas, o un producto al que le falta lo que ya tiene.
- **Las rutas añadidas siguen el mismo contrato de errores** (`ProblemDetail` con `code` y
  `correlation_id`), la misma comprobación de `Origin` en escrituras y la misma validación de esquema
  que las rutas del contrato: no hay dos calidades de API.
- **El OpenAPI es la verdad ejecutable.** Estas rutas están en `packages/contracts/openapi.json` con su
  esquema y sus respuestas de error, así que un cliente generado las ve; lo que no están es en el
  documento §8/§10/§11 escrito a mano.
- **Si el propietario retira una**, la retirada es un cambio de producto y va con su slice: no se
  dejan rutas a medias ni pantallas que las llamen.

## Alternativas descartadas

1. **Ampliar `08_API-CONTRACT.md`.** Se descartó porque ese documento es el contrato **de partida** y
   reescribirlo borraría la trazabilidad de qué se pidió y qué se añadió después. La lista de añadidos
   tiene que ser un añadido, no una edición del original.
2. **No añadirlas y forzar el producto a lo que hay.** Se descartó porque en cada caso la consecuencia
   es una pantalla que no puede hacer su trabajo, o peor: deducir en el cliente lo que decide el
   servidor.
3. **Añadirlas en silencio.** Se descartó desde el primer slice: cada una se declara en su ficha y en el
   `summary` de la ruta, y ahora también aquí.
