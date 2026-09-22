# ADR-015 — Tercera oposición: Celador/a del SACYL

**Estado:** aceptada (22 de septiembre de 2026, por decisión del propietario)
**Contexto de la decisión:** `11_IMPLEMENTATION-SLICES` §2 decía que «comercialización, nube y
**tercera oposición** requieren una decisión nueva». Esta es esa decisión.

## Contexto

El producto se construyó con **dos** perfiles oficiales: TAI AGE 2025 (BOE) y Guardia Civil Cabos y
Guardias 2026 (BOE). La especificación no prohibía un tercero: exigía decidirlo antes de hacerlo,
porque un perfil nuevo no es «más datos», es un caso más del modelo (`ADR-005`), de los fixtures
(`ADR-006`) y de la interfaz.

El propietario pidió expresamente preparar la oposición de **Celador/a de Castilla y León**, para el
tribunal de **Salamanca**, y pidió que la fuente fuera la última convocatoria oficial publicada y, si
ya se había examinado, la siguiente.

## Decisión

**1. Se añade el perfil `celador-sacyl-2022`, y solo con fuentes oficiales.**

- Oposición: `celador-sacyl` — Celador/a del Servicio de Salud de Castilla y León.
- Convocatoria: `celador-sacyl-2022` — ORDEN SAN/1828/2022, de 12 de diciembre (BOCYL de 22 de
  diciembre de 2022), `BOCYL-D-22122022-7`.
- Fuente de las citas y del programa: la **edición electrónica del BOCYL en HTML** del propio acto.
  El PDF se guarda como copia de verificación, igual que en TAI.
- La fecha del ejercicio y el lugar (Universidad de Salamanca) salen de la resolución de la Gerencia
  de Salud de Área de Salamanca publicada en el BOCYL el 2 de octubre de 2023
  (`BOCYL-D-02102023-6`), no de la orden de convocatoria, que no fija fecha.

**2. Es la última convocatoria con examen, y se declara por qué.**

La de 2022 ya se resolvió: ejercicio el 12 de noviembre de 2023, aprobados de la fase de oposición en
enero de 2024, aprobados del proceso y oferta de vacantes en noviembre de 2024 (ORDEN SAN/1445/2024)
y nombramientos en 2025.

Existe **otra** convocatoria de Celador posterior en el tiempo y todavía sin ejercicio: el proceso
excepcional de estabilización de la Ley 20/2021 (ORDEN SAN/1917/2022, de 23 de diciembre, BOCYL de 28
de diciembre de 2022), que convoca Celador por **concurso-oposición** con su propio programa (catorce
temas, parte general y parte específica), 44 preguntas incluidas las de reserva, tres alternativas y
error penalizado con 1/9, en 60 minutos. Sus listas provisionales de admitidos se publicaron el 21 de
octubre de 2025 y **el ejercicio aún no se ha convocado**, así que no hay examen que estudiar de él.
Además, su plazo de solicitudes cerró el 27 de enero de 2023: quien no se presentó entonces no puede
incorporarse a ese proceso.

Por eso el perfil de estudio es el de la convocatoria ordinaria de 2022, la última con examen
celebrado. La de estabilización queda documentada en `15_OFFICIAL-PROFILES-AND-SOURCE-MANIFEST` §4 y
se incorporará como segunda convocatoria de la misma oposición cuando su programa se extraiga con sus
citas (S12.2), no antes.

La estabilización 2023–2026 por **concurso de méritos** (la otra vía de la misma Ley 20/2021, resuelta
por la ORDEN SAN/1530/2024) también incluye Celador, y tampoco tiene ejercicio: no sirve como perfil
de examen.

Eso **no** se traduce en `status: archived`. En esta aplicación, «la convocatoria activa» de una
oposición es la convocatoria con la que se trabaja: las pantallas de Programa, Estudio, Repaso y
Banco resuelven el temario con `active_convocation`, y una convocatoria archivada deja la aplicación
sin nada que estudiar. Celador 2022 es la convocatoria vigente de su oposición —no hay otra que la
sustituya—, así que queda `active`, y que el proceso ya haya pasado se ve donde se ve de verdad: en
su `exam_date`, que está en el pasado, y en la documentación de este ADR. Hay una prueba que activa
la oposición y comprueba que la convocatoria con la que trabajar sigue ahí.

**3. El perfil **no** queda activo.**

`opposition.active` sigue siendo TAI: el fixture decide qué oposición está activa (`ADR-009`), y
añadir un perfil no puede cambiar, de paso, lo que el propietario está estudiando. Celador se activa
desde la interfaz cuando él quiera.

**4. Nada nuevo en el modelo, el contrato ni la interfaz.**

El programa de Celador tiene una forma que el modelo ya admitía: **dieciséis temas que cuelgan de la
raíz**, sin bloques ni epígrafes (`counts: 0 / 16 / 0`). No se ha inventado un cuarto nivel ni se han
fabricado bloques para rellenar. Tampoco se añaden campos: las cifras que importan (plazas,
titulación, umbral de aprobado) entran como **reglas con cita**, que es el sitio que el contrato ya
tiene para lo que la convocatoria publica en prosa.

**5. Lo que el perfil no puede calcular, no lo calcula.**

El aprobado de Celador no es una nota fija: es el 60 % de la media de las diez puntuaciones más
altas del ejercicio. Sin las puntuaciones de los demás, ese umbral **no existe**, así que
`pass_score` queda a nulo y el umbral se declara como regla con su cita («sin las puntuaciones del
ejercicio, la aplicación no puede calcular el umbral y no lo estima»).

**6. Derechos de las fuentes nuevas: `unknown`, y se explica por qué.**

El aviso legal del BOCYL garantiza autenticidad y acceso «universal, público y gratuito», pero **no
publica condiciones de reutilización**; el aviso legal del portal de Salud regula el uso de su
aplicación móvil, no los ficheros de los procesos selectivos. Un permiso que nadie ha concedido no se
supone: las fuentes del BOCYL y del portal quedan con estado `unknown`, con la cita de lo que sí
dicen y con la nota que lo explica. El proyecto sigue siendo local, de un solo usuario y sin
redistribución (DEBT-003).

## Consecuencias

- La aplicación pasa a tener tres oposiciones y cuatro convocatorias; las pruebas que contaban
  «dos» se han actualizado a tres, con el número escrito, no con un `len()` genérico.
- `path` es único **dentro de su convocatoria** (`uq_curriculum_path`). Guardia Civil ya numeraba sus
  temas «1»…«25» desde la raíz y Celador numera «1»…«16»: la prueba que exigía unicidad global
  exigía de más y se ha corregido para comprobar la restricción que existe de verdad.
- La plantilla oficial de respuestas correctas de este ejercicio es un **escaneo sin capa de texto**:
  la clave oficial existe y no se puede importar sin OCR o lectura manual (DEBT-020).
- Un cuarto perfil volverá a exigir decisión: esto no convierte «añadir oposiciones» en rutina.

## Reversión

Quitar el perfil es borrar tres ficheros (`celador-sacyl-2022.profile.json`,
`celador-sacyl-2022.curriculum.json` y sus entradas del manifiesto) y volver a sembrar: `seed_profiles`
retira los nodos que ya no están en el fixture, siempre que no tengan material asignado (`ADR-007`).
Ninguna tabla, columna ni ruta de la API se ha tocado para este perfil, así que no hay migración que
deshacer.
