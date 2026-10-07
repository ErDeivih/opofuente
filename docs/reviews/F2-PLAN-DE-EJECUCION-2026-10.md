# F2 — La capa del alumno: plan de ejecución (7 de octubre de 2026)

Preparado mientras corren las puertas de F1, para empezar F2 en cuanto se fusione. Sustituye a lo que
diga el plan general en esta fase; los requisitos salen de
`docs/REDISENO-ALUMNO-TAI-Y-PANEL-ADMIN-2026-10.md` §3-§5 y de
`docs/RESPUESTAS-F0-Y-ARRANQUE-F1-2026-10.md` §2.

Rama: `f2-api-alumno`, desde el `main` que salga de F1. Una fase, un commit por pieza, puertas enteras
al final.

## 1. Configuración (dos variables, con prueba)

| variable | por defecto | qué hace |
| --- | --- | --- |
| `OPOFUENTE_STUDENT_OPPOSITION` | `tai-age` | la oposición que sirve la zona del alumno; el filtro vive **en el servidor**, no en la pantalla |
| `OPOFUENTE_PUBLIC_MODE` | `0` | con `1`, la API del alumno sirve solo conjuntos `public` |

Prueba: con dos oposiciones sembradas (TAI y otra), ninguna respuesta de `/api/v1/student/*` contiene
nada de la otra —ni nombre, ni identificador— y con `OPOFUENTE_PUBLIC_MODE=1` no aparece ningún conjunto
marcado `personal`.

## 2. Migración: `distribution` en los conjuntos

- Columna `distribution` en `question_sets`: `personal` | `public`, **por defecto `personal`**.
- Los cuatro conjuntos de examen oficial del INAP pasan a `public` (son publicables: los publica el
  INAP). Los 227 bancos privados se quedan en `personal`.
- Migración de Alembic con su prueba de ida y vuelta, y `alembic downgrade` verificado (la puerta 13
  migra desde base vacía y la 14 comprueba el esquema con `sqlite3`).

## 3. Preparado para cuentas, sin cuentas todavía

Añadir `owner_id` (texto, no nulo, por defecto `'local'`) a las tablas donde vive el progreso de una
persona: `study_sessions` y las tablas de intentos/errores que cuelgan de ella. Nada de login: la
aplicación sigue siendo de un solo usuario y local; lo que se gana es que **el progreso ya sabe de quién
es** el día que existan cuentas, sin rehacer los datos de nadie.

Prueba: una sesión creada por la API queda con `owner_id = 'local'` y el listado de sesiones filtra por
ese campo (que hoy es un valor único, pero el filtro ya está).

## 4. La API del alumno

`/api/v1/student/*`, en un paquete aparte (`api/routes/student.py` + `api/student_schemas.py`), que **solo
devuelve lo que se pinta**:

| ruta | qué devuelve |
| --- | --- |
| `GET /student/overview` | el test a medias, los fallos vencidos y el progreso por bloque |
| `GET /student/syllabus` | bloques y temas **en orden numérico** (IV.1, IV.2, … IV.10), con preguntas disponibles y % de acierto |
| `GET /student/topics/{codigo}` | un tema por su código legible (`IV.10`): título, epígrafes, recuentos y progreso |
| `POST /student/tests` | monta un test (bloques y/o temas, cuántas, filtros, corrección, tiempo) reutilizando `StudyService` |
| `POST /student/mock-exams` | simulacro con las reglas de la convocatoria (`exam_parts`, `exam_rules`): 80 + 20, 120 min, −1/3 |
| `GET /student/official-exams` | los exámenes del INAP disponibles y la nota del alumno si ya los hizo |
| `GET /student/progress` | acierto por bloque y por tema, los cinco más flojos e historial |

Reglas del contrato:

- **Nada de evidencias, conjuntos, claves, versiones ni rutas** en ninguna respuesta. Se consigue con
  esquemas propios (`StudentQuestionView`, `StudentSessionView`…) que **no tienen esos campos**, no
  filtrando al final.
- **El orden de los temas es numérico**, no por texto de `path`: hoy IV.10 sale después de IV.1. Se
  arregla ordenando por (bloque romano, número de tema) en la consulta del programa, y esa consulta la
  usa también el panel, así que se arregla en los dos sitios a la vez.
- El código del tema (`IV.10`) viaja en las direcciones del alumno; **ningún UUID** a la vista.

Pruebas (antes de la E2E):

1. **Contrato**: los esquemas del alumno no tienen campos prohibidos, y una prueba que recorre cada
   respuesta de `/student/*` con datos sembrados y falla si aparece una clave o un valor de la lista
   (`evidence`, `source`, `question_set_id`, `key_`, `document`, `F:\`, `.pdf`, títulos de bancos…).
2. **Orden**: con el programa real sembrado, `GET /student/syllabus` devuelve IV.1 antes de IV.10 y I.1
   antes de I.2.
3. **Aislamiento**: con la oposición de Celador sembrada, nada de ella aparece por `/student/*`.
4. **Composición**: un test de 10 preguntas de un tema y un simulacro 80+20 con elección de bloque III
   o IV, con el tiempo límite de la convocatoria.

## 5. Lo que NO hace F2

- No construye pantallas: el prototipo portado es la fase siguiente (F3), con los diseños ya elegidos.
- No añade cuentas ni servidor: sigue local y de un usuario.
- No toca el panel: sus pantallas son F6-F8.

## 6. Orden de trabajo y aceptación

1. Migración (`distribution`, `owner_id`) + pruebas.
2. Orden numérico del programa (con su prueba, que hoy fallaría).
3. Los cuatro endpoints de lectura (`overview`, `syllabus`, `topics`, `progress`).
4. Los dos de escritura (`tests`, `mock-exams`) reutilizando `StudyService`, con sus esquemas de alumno.
5. La prueba de contrato que recorre todas las respuestas del alumno buscando lo prohibido.

Aceptación: `.\scripts\gates.ps1` **18/18**, contrato OpenAPI regenerado y tipos sincronizados, y la
prueba de "nada prohibido" en verde. Se documenta en `docs/reviews/F2-API-DEL-ALUMNO-<fecha>.md` con las
mediciones (qué respuestas se han recorrido, cuántas claves se comprueban, qué rutas del programa).
