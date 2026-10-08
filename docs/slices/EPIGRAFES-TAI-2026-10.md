# Epígrafes de TAI (F3, primera pieza) — 8 de octubre de 2026

Rama `f3-epigrafes-tai` sobre `main = 47c1399`. Sin fusionar.

## Qué he construido

Los **134 epígrafes** de la convocatoria de TAI (`tai-age-2025`) como nodos `epigraph` hijos de sus 33
temas, **derivados del título oficial** dentro del constructor de fixtures
(`apps/api/opofuente/tools/build_profile_fixtures.py`) y no escritos a mano en el JSON: así la puerta
17 sigue comprobando que el programa sale del documento descargado. He actualizado las pruebas que
fijaban los recuentos, he sembrado los nodos en los datos reales con el camino de la aplicación
(copia de seguridad previa) y he arreglado dos cosas de la suite E2E que la convocatoria nueva dejó a
la vista. No hay migración de esquema: `curriculum_nodes` ya admitía `epigraph` (lo usa Guardia Civil
desde S01).

## Cómo fluye la información

```
data/sources/tai-2025-boe.xml  (BOE-A-2025-26262, ANEXO V)
  └─ xml_paragraphs()            párrafos con su clase CSS
      └─ annex_range("ANEXO V")  solo el anexo del programa (los demás convocan otros cuerpos)
          └─ «3. Programa.»      apartado
              ├─ bloques   `centro_cursiva` «I. …» «IV. …»            → nodos block
              └─ temas     párrafo «N. …»                             → nodos topic
                  └─ tai_epigraphs(título)  corte por punto + espacio → nodos epigraph
fixtures/profiles/tai-age-2025.curriculum.json   (4 / 33 / 134)
  └─ puerta 17: build_profile_fixtures --check  regenera y compara
tools/seed_profiles → ProfilesService.seed → upsert_profile → _sync_curriculum (empareja por `path`)
  └─ curriculum_nodes  →  GET /api/v1/convocations/{id}/curriculum
      └─ curriculum_order() en SQL ordena por número de cada segmento: IV.9 antes de IV.10 y
         IV.10.3 antes de IV.10.4 (no por el texto de la ruta)
```

La regla de corte es una sola: `_SENTENCE_BREAK = re.compile(r"(?<=\.)\s+")`, es decir **punto seguido
de espacio**. El punto se conserva en el epígrafe, así que los epígrafes de un tema, unidos por un
espacio, reproducen su título oficial sin perder un carácter; el constructor lo comprueba y no escribe
el fixture si no se cumple. Con `plataforma.NET` (tema III.5) el punto va pegado a la palabra, así que
no corta: es el caso que el propietario señaló al revisar la partición, y tiene prueba propia.

## Ficheros y migraciones

- `apps/api/opofuente/tools/build_profile_fixtures.py`: `_SENTENCE_BREAK`, `tai_epigraphs()` y los
  epígrafes en `tai_curriculum()`; `TRANSFORMATIONS["tai-age-2025"]` dice ahora qué se ha hecho con el
  texto oficial.
- `fixtures/profiles/tai-age-2025.curriculum.json`: regenerado (los otros tres no cambian ni un byte).
- `apps/api/tests/unit/test_profile_fixtures.py`: recuentos 4/33/134, reparto por tema (33 cifras),
  invariante de reconstrucción, `.NET` y prueba de la regla de corte.
- `apps/api/tests/integration/test_profile_seeding.py` y `test_profile_api.py` y
  `apps/api/tests/contract/test_openapi_contract.py`: recuentos sembrados (171 nodos de TAI, 401 en
  total) y una prueba nueva de orden numérico y `.NET` contra la base sembrada.
- `apps/web/tests/e2e/review.spec.ts`: el texto sintético de `revision-1` cita el temario **sin
  completar ningún epígrafe** (ver «decisiones»).
- `apps/web/playwright.config.ts` + borrado de `apps/web/tests/e2e/globalSetup.ts`: el directorio de
  datos del E2E se borra antes de migrarlo, en el servidor de la API.
- `apps/web/tests/e2e/program.spec.ts`: el localizador del `<h2>` «El tema» lleva `exact: true` (en
  Playwright el `name` de un rol casa por subcadena y también casaba con «Preguntas del tema»).
- `README.md`: las trampas de las puertas, donde se buscan.
- **Sin migración de Alembic**: no hay cambio de esquema.

## Patrones y decisiones aplicadas

- **Una sola fuente de verdad.** La partición no vive en el JSON ni en la base: vive en el constructor,
  y la puerta 17 detecta cualquier fixture que no salga del documento.
- **La partición es verificable.** El invariante «unir los epígrafes devuelve el título» convierte un
  cambio de la regla de corte en un fallo del constructor, no en 134 títulos raros.
- **`official_code` = `path` = `I.1.1`** (lo pedía la decisión del propietario). En los temas,
  `official_code` sigue siendo el número dentro del bloque («1», «2»…), como estaba; la ruta no cambia
  para nadie, así que ningún mapeo de pregunta se mueve.
- **La siembra, no SQL suelto.** Se usó el camino de la aplicación (`seed_profiles`, idempotente)
  apuntando a `OPOFUENTE_DATA_DIR=F:\OpoFuente\datos`, con copia previa de la base.
- **No se toca el motor de clasificación.** Que el motor de temas proponga epígrafes es el
  comportamiento que Guardia Civil ya tiene en los datos reales (7.440 propuestas a epígrafes, 6.083
  automáticas); cambiarlo habría sido alterar en silencio un motor que lleva meses funcionando.

## Seguridad y privacidad

La fuente es el BOE (documento público) y los fixtures ya estaban versionados; no entra material
privado ni comercial. No se toca autenticación, autorización, derechos ni claves. La copia de
seguridad y la siembra se hacen sobre `OPOFUENTE_DATA_DIR`, nunca sobre los originales.

## Puertas ejecutadas y resultado

`.\scripts\gates.ps1` (sin `-SkipE2e`), corrida completa del 8 de octubre de 2026, registro con
`Start-Process` en `F:\temp-opofuente\gates-f3-epigrafes.txt` (**18/18, 29:44 minutos**):

| # | Puerta | Resultado |
|---|---|---|
| 1–2 | ruff format / ruff check | OK |
| 3 | mypy estricto | OK |
| 4–5 | eslint / typecheck TypeScript | OK |
| 6 | unitarias backend | 593 passed |
| 7 | integración backend | 535 passed (22:40) |
| 8 | contrato | 29 passed |
| 9 | componentes (Vitest) | 257 passed (23 ficheros) |
| 10 | contrato OpenAPI y tipos | OK |
| 11–12 | build backend / frontend | OK |
| 13–16 | migración desde base vacía y siembra idempotente | OK |
| 17 | fixtures frente a las fuentes oficiales | OK (4 / 33 / **134**) |
| 18 | E2E (Playwright) | 57 passed (2:36) |

Nota de dos corridas anteriores, para que no se confundan con defectos de esta pieza: la primera tuvo
la 18 en rojo (el texto sintético de `review.spec.ts` y el directorio de datos acumulado, contados
arriba) y la segunda, la 7 con **un** fallo intermitente en
`test_readiness.py::test_con_material_asignado_preguntas_con_tema_y_clave_activa_esta_listo`, que
pasaba 3 de 3 ejecutado aislado y volvió a pasar en la corrida verde: es una espera del estado del
lote tras tres pasadas del worker, no algo del temario.

## Prueba manual

1. `uv run python -m opofuente.tools.build_profile_fixtures` → `tai-age-2025: 4 bloques, 33 temas, 134
   epígrafes`; `git status` solo muestra el fixture de TAI.
2. Copia previa con el mecanismo del repositorio (`backup_archive.snapshot_database`) a
   `F:\OpoFuente\datos\_copias\opofuente-antes-epigrafes-tai-20261008000930.sqlite3` (2.649.796.608
   bytes) y comprobación de que reproduce la base (misma revisión `0027_owner_id`, 267 nodos, 17.424
   preguntas, 39.242 mapeos, 106.863 eventos de auditoría).
3. `OPOFUENTE_DATA_DIR=F:\OpoFuente\datos uv run python -m opofuente.tools.seed_profiles` →
   `tai-age-2025: 134 nuevas, 0 actualizadas, 50 sin cambios`; los otros tres perfiles, sin cambios.
4. Foto antes/después de la base real (17 tablas con su hash, volcado de `curriculum_nodes`): 134
   altas, **0 bajas, 0 cambios**, todas en `tai-age-2025` y de tipo `epigraph`; `question_versions`,
   `curriculum_mappings`, `audit_events`, sesiones, intentos, partes y reglas **con el mismo hash**.
5. Consulta al programa de TAI por el repositorio: 4 bloques, 33 temas, 134 epígrafes, `IV.9` antes de
   `IV.10`, `IV.10.1…IV.10.5` en orden y `plataforma.NET` entero.

## Limitaciones conocidas

- **No hay léxico de abreviaturas.** El programa de TAI no tiene ninguna con punto interno (el único
  punto que no cierra enunciado es el de `plataforma.NET`), así que la regla es «punto + espacio» y no
  lleva lista de abreviaturas. Si una convocatoria futura trajera `EE. UU.` o `art. 5`, el corte lo
  partiría; lo cazarían el invariante de reconstrucción y las 33 cifras por tema, y habría que añadir
  la lista entonces (no antes, inventando).
- **Efecto colateral en el motor de temas.** El motor de material propone ahora epígrafes de TAI
  (confianza alta si el texto reproduce un epígrafe corto, como «Algoritmos.»), igual que ya hacía con
  Guardia Civil. Queda fuera de esta pieza decidir si eso es lo que se quiere; la prueba de E2E que lo
  detectó se ha ajustado **solo en su material sintético**, no en su aserción.
- **La siembra no deja evento de auditoría.** `seed_profiles` no escribe en `audit_events` (la decisión
  del propietario pedía «migración de datos idempotente con auditoría»; el encargo de esta pieza pidió
  el camino de siembra que ya usa la aplicación). El rastro queda en el informe de la siembra y en la
  copia previa, no en la tabla de auditoría.
- **El comentario de `ProposalList.tsx`** («en el eje de tema lo único que se puede proponer son
  temas») es falso desde que el temario tiene epígrafes. Es texto de interfaz y va con el panel de
  administración.
- **`program.spec.ts` y otros** siguen midiendo la pantalla de Revisión en ~30 s cuando su directorio de
  datos se deja crecer; el arreglo de la limpieza lo evita, pero la pantalla sigue siendo pesada.
- **El localizador «El tema» era ambiguo de nacimiento.** Con el directorio de datos limpio, el dossier
  de I.1 responde tan rápido que el `<h3>` «Preguntas del tema» ya está en el DOM cuando la prueba
  comprueba el `<h2>` «El tema», y Playwright casa por subcadena: la prueba pasaba solo porque la
  respuesta llegaba tarde. Se ha arreglado el localizador, no la aserción.

## Qué se rompe si cambias X

- **La regla de corte** (`_SENTENCE_BREAK`): se rompe el invariante de reconstrucción y cambian las 33
  cifras por tema → puerta 17 en rojo y pruebas unitarias en rojo. Es el freno que se quiere.
- **El `official_code` de los epígrafes**: hay pruebas que lo fijan (`I.1.1`) y la corrección de tema de
  la pantalla de revisión lo usa como valor del desplegable.
- **Quitar los epígrafos del fixture**: vuelven los recuentos 4/33/0 y la siembra retiraría 134 nodos
  (los que no tengan material asignado).
- **La limpieza del directorio de datos del E2E**: sin ella, la cola de revisión acumulada hace que la
  prueba de accesibilidad tarde 39 s y se quede sin tiempo (medido), y el fallo parece de la aplicación.

## Qué criticaría un revisor senior

1. **Cambié el fixture antes de mirar quién lo consume.** El motor de clasificación de material usa
  *todos* los nodos de la convocatoria (`classification_repository._nodes_of`), así que añadir 134
  epígrafes cambió la clasificación de TAI (de bloque/tema a epígrafe, y con aplicación automática en
  los textos que reproducen un epígrafe). Lo encontré porque la puerta 18 se puso roja, no porque lo
  buscara: el inventario de consumidores del temario debería haber sido el paso 0.
2. **Toqué `playwright.config.ts`**, que es justo el fichero que el proyecto prohíbe tocar para que las
  puertas pasen. La justificación es una medición (la prueba de accesibilidad pasa de 39 s a 1,5 s con
  el directorio limpio; los epígrafos solo aportan ~2,6 s y cero violaciones) y el efecto es cumplir lo
  que la propia suite documentaba («datos nuevos en cada corrida»), pero un revisor tiene razón en
  mirarlo con lupa: la limpieza se movió de `globalSetup` al `webServer` porque Playwright arranca los
  servidores **antes** de `globalSetup` y la limpieza allí fallaba con `EPERM` con la base abierta.
