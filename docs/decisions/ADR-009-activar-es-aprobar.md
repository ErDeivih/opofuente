# ADR-009 — Activar una plantilla es aprobarla

- **Estado:** aceptada (decisión tomada al implementar el contrato §9 durante S06 y registrada al
  cerrar la fase; el propietario pidió continuar sin consultas intermedias)
- **Fecha:** 17 de septiembre de 2026
- **Ámbito:** autoridad de las claves (03_DATA-MODEL §6, invariante 4) y banco de preguntas (S06)
- **Asunto:** cómo se cumple «una clave activa necesita aprobación» si el contrato no tiene ruta de
  aprobación

## Contexto

La base impone, con un `CHECK`, que una plantilla `active` tenga `approved_at` (0014), y la invariante 4
añade que una clave **oficial** necesita además su plantilla oficial enlazada. El contrato §9 ofrece una
sola ruta para decidir sobre una plantilla:

```text
GET  /question-sets/{id}/answer-keys
POST /question-sets/{id}/answer-keys/{key_id}/activate
POST /answer-keys/{id}/mark-supersedes
```

No hay ruta de aprobación. Con la lectura literal, **ninguna clave podría activarse nunca**: el
`CHECK` exigiría una aprobación que nadie puede dar por la API. Eso deja tres salidas: inventar una ruta
de aprobación fuera del contrato, aprobar por debajo (rellenar `approved_at` al guardar la plantilla,
que sería fingir una revisión) o decidir que **activar es aprobar**.

## Decisión

**Activar una plantilla es aprobarla**: la acción de una persona que pide activar esa clave es
exactamente la aprobación que la invariante exige, así que el servicio registra `approved_at` con la
fecha de la activación y el actor que la pidió, y **después** la activa (el orden importa: el `CHECK`
de la base no admite un estado intermedio activo sin aprobación).

Consecuencias de la decisión, explícitas:

- **No se pierde la invariante**: ninguna plantilla queda activa sin una acción humana registrada; lo que
  cambia es que esa acción es una sola y no dos.
- **Queda auditable**: la activación escribe su evento (`answer_key.activated`) y, cuando hacía falta,
  también el de aprobación (`answer_key.approved`), así que se puede leer quién lo hizo y cuándo.
- **Aprobar sin activar sigue siendo posible** por dentro: `approve_key` existe y se usa antes de
  activar cuando una prueba o un flujo previo lo pide. La regla de la base se sigue cumpliendo en los
  dos caminos.
- **Lo que no se puede aprobar es lo que no es oficial**: si el conjunto es `official_exam` y la
  plantilla no tiene enlazada la plantilla oficial, la activación responde 409 con el motivo y no
  cambia nada. Una aprobación no convierte en oficial un documento que no lo es.

## Alternativas descartadas

1. **Ruta nueva `POST …/answer-keys/{id}/approve`**: fuera del contrato, que es fuente de verdad. Si
   algún día hacen falta dos actos separados (revisar y publicar), será una decisión de contrato y se
   pedirá como tal.
2. **Rellenar `approved_at` al guardar la plantilla**: sería afirmar una revisión que nadie ha hecho,
   justo lo que el proyecto prohíbe.
3. **Quitar el `CHECK` de aprobación**: debilitar la base para que quepa el flujo es al revés de como se
   arreglan estas cosas.

## Reversión

Si el propietario decide separar aprobación y activación, el cambio es pequeño y localizado: una ruta
nueva en el contrato, `activate_key(..., approve: bool = False)` para el camino nuevo y su prueba. Nada
de lo guardado cambia: `approved_at` ya está en la base y es la misma marca que usaría la ruta nueva.
