# O2 — Ficha del cuerpo y estado de estudio por tema

## Qué he construido

- **La ficha del cuerpo** (`/cuerpo/:code`): una pantalla por cuerpo que enseña su código y su
  descripción, la convocatoria que lo rige (título, fecha de publicación, fecha de examen —o «No
  consta»—, estado y enlace a la fuente oficial), la lista de ejercicios con lo que el perfil publica
  de cada parte, las reglas de puntuación tal y como están cargadas, y las cifras del temario (bloques,
  temas y preguntas disponibles) con salida al temario completo.
- **El enlace desde el índice** (`/temario`): la cabecera ofrece «Ver la ficha del cuerpo» y cada tema
  con fallos ofrece su atajo a `/fallos?tema=CODIGO`.
- **El estado de estudio por tema** en el índice: «Sin empezar», «En curso» o «Afianzado», calculado en
  un solo sitio (`features/student/estadoDeEstudio.ts`).
- **El filtro por tema en los fallos** (`/fallos?tema=IV.7`): filtra en el cliente los temas y las
  preguntas, restringe el test al tema cuando se pide, y ofrece quitar el filtro (también cuando no hay
  fallos de ese tema, en vez de dejar una pantalla vacía).

## Cómo fluye la información

1. `useOppositions()` → `/api/v1/oppositions` → lista con `code`, `name`, `description` y
   `active_convocation`. La ficha busca el cuerpo por `code` sin distinguir mayúsculas.
2. Si hay `active_convocation.id`, `useConvocation(id)` → `/api/v1/convocations/{id}` → título,
   `published_at`, `exam_date`, `exam_date_note`, `status`, `official_url`, `parts[]` y `rules[]`.
3. `getStudentSyllabus()` → `/api/v1/student/syllabus` → bloques y temas con `available_questions`.
4. En el índice, `getStudentMistakes()` (misma clave de caché que la pantalla de fallos) da los fallos
   por tema; si falla, el índice sigue leyéndose y solo desaparecen los atajos.
5. Desde `/fallos?tema=`, el parámetro de la dirección filtra las listas ya cargadas: no hay ninguna
   lectura nueva.

## Ficheros y migraciones

- `apps/web/src/pages/student/BodyPage.tsx` (nuevo).
- `apps/web/src/features/student/estadoDeEstudio.ts` (nuevo).
- `apps/web/src/app/routes.tsx`: ruta `/cuerpo/:code` dentro de la zona del alumno.
- `apps/web/src/pages/student/SyllabusPage.tsx`: enlace a la ficha, estado por tema y atajo a fallos.
- `apps/web/src/pages/student/MistakesPage.tsx`: filtro `?tema=`.
- `apps/web/src/styles/global.css`: `.ficha__*`, `.tema-fila__estado`, `.tema-fila__fallos`,
  `.pagina__enlace`, `.etiqueta`.
- **Sin migraciones.** No se añaden campos ni endpoints.

## Patrones y decisiones aplicadas

- **Solo se publica lo que está publicado.** Plazas, requisitos y titulación **no existen** en el perfil
  de esta versión (`OppositionRecord` solo guarda `code`, `name`, `description`, `active`). La ficha lo
  dice con un «no consta» explícito y enlaza al enunciado oficial, en vez de rellenar con lo que suele
  pasar en otras convocatorias.
- **La fuente oficial viaja con la convocatoria** (`official_url`), no escrita a mano en el componente.
- **Reutilizar la API existente**: se usan los endpoints públicos y de alumno ya presentes; no se toca
  `packages/contracts` (regenerar el contrato exige shell y no está disponible en este turno).
- **Un umbral de interfaz, en un módulo.** `estadoDeEstudio` es una etiqueta de lectura, no una nota ni
  un pronóstico; su comentario lo dice y el test solo comprueba la transición.
- **Aditivo en el índice.** Los textos existentes se conservan; cuando `accuracy` es `null` se sigue
  mostrando una etiqueta («Sin empezar» / «En curso»), no una cifra.

## Seguridad y privacidad

- Nada nuevo viaja a la API: la ficha solo lee. No se registran datos del alumno ni se envían a
  terceros; el enlace oficial sale con `target="_blank"` y `rel="noreferrer noopener"`.
- Los datos del alumno (acierto, fallos) siguen saliendo de `/api/v1/student/*` con su sesión; el
  filtro `?tema=` es una dirección de la propia pantalla, no un identificador interno.

## Puertas ejecutadas y resultado

- **NO se declara ninguna puerta verde en este árbol.** Motivo real, reproducido:
  - `uv run --frozen pytest apps/api/tests/unit -q` (puerta `648dc9aeae21`) queda **roja por entorno**:
    al importar la app salta `ModuleNotFoundError` de `argon2-cffi` (`argon2-cffi>=25.1.0` no está en el
    venv del sandbox), antes de colectar nada. No es atribuible al cambio: este slice no toca Python.
  - `scripts/gates.ps1` (puerta `9df85043f3a0`) no se ha ejecutado: sin la puerta anterior en verde y
    sin shell, ejecutarla no daría evidencia válida.
  - Consecuencia honesta: el slice está **implementado, NO verificado**. Se ha pedido al coordinador
    `uv sync --frozen` en el venv del sandbox para reejecutar `648dc9aeae21` sobre el árbol final.

## Prueba manual

1. Abrir `/temario`, pulsar «Ver la ficha del cuerpo»: llega a `/cuerpo/A2`.
2. Comprobar que la convocatoria muestra publicada, fecha o «No consta», estado y «Fuente oficial», y que
   «Requisitos y plazas» dice que no constan en el perfil.
3. Un tema con fallos enseña «N fallos»; al pulsarlo se llega a `/fallos?tema=CODIGO` con la lista ya
   filtrada y el botón «Quitar el filtro del tema».
4. `/cuerpo/NOEXISTE` responde «Ese cuerpo no está en el catálogo» con salida al temario.

## Limitaciones conocidas

- **Plazas, requisitos y titulación no se enseñan** porque el perfil no los guarda: hace falta un slice
  de datos (`vacancies`, `requirements`, `authority`/`source_url` por convocatoria) con su migración.
- El estado de estudio es una **etiqueta de interfaz** con umbral fijo (acierto ≥ 80 % y sin repasos
  vencidos), no una medida oficial ni un pronóstico.
- El filtro de fallos se resuelve en el cliente: si el volumen de fallos creciera mucho, convendría un
  filtro en servidor con su medición.
- No se han podido ejecutar ni leer las pruebas web (`apps/web/tests/**` queda fuera de las fuentes
  autorizadas de este turno); los cambios en el índice y en fallos se han escrito para ser aditivos.

## Qué se rompe si cambias X

- Si `OppositionRecord` publica algún día `vacancies`/`requirements`, la ficha debe dejar de decir «no
  consta» y leerlos: hoy no hay campo, y añadir un endpoint nuevo exige contrato.
- Si `official_url` dejara de venir en la convocatoria, el botón «Fuente oficial» apuntaría a vacío: el
  contrato lo declara obligatorio, así que su ausencia sería un fallo de datos, no de interfaz.
- Si cambia la forma de `StudentSyllabus.topics`, `estadoDeEstudio` recibe datos incompletos y todas las
  filas caerían en «En curso».
- Si `/fallos` dejara de aceptar `?tema=`, los atajos del temario llevarían a la lista completa sin
  avisar.

## Qué criticaría un revisor senior

- Que la ficha dedica media pantalla a decir lo que **no** consta: es honesto, pero conviene que el
  slice de datos llegue pronto o que esos bloques se colapsan.
- Que el umbral del estado de estudio está escrito en el código sin configuración: es deliberado (una
  sola definición), pero debería documentarse en la spec de UI.
- Que no hay prueba automática de este slice en el árbol: la cobertura de `BodyPage`, del helper y del
  filtro depende de una puerta que hoy no se puede ejecutar; mientras siga así, la garantía es manual.
