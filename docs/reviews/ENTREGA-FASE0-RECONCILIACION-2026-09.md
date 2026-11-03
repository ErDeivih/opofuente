# Fase 0 — la cola de revisión deja de preguntar dos veces lo mismo

**Fecha:** 23 de septiembre de 2026
**Rama:** `fase0-reconciliacion-artefacto-representacion` (creada desde `main` en `98d8e60`)
**Naturaleza:** trabajo **fuera de slice**, autorizado por el propietario; **sin commit**. No añade
dependencias, no cambia el contrato OpenAPI y no toca la base de datos.
**Origen:** `ESTUDIO-JEV-VIABILIDAD-2026-09.md` §1.4b y `PLAN-POC-JEV-2026-09.md` §1.1 (Fase 0).

---

## Qué he construido

Una regla determinista que convierte la cola de revisión en **decisiones** en lugar de filas: cuando el
motor propone **lo mismo** —mismo eje, valor, confianza y motor— sobre un material y sobre su texto
extraído, eso es **una** decisión y no dos.

Medido en la base real de DEBT-018 (solo lectura):

| Eje | Pendientes antes | Decisiones después |
|---|---|---|
| `document_type` | 122 | 61 |
| `topic` | 106 | 53 |
| `authority` | 72 | 36 |
| `rights` | 48 | 24 |
| **TOTAL** | **348** | **174** |

Y dos piezas más, que son la misma idea aplicada a los sitios donde el número se enseña o se mide:

1. **El contador de Inicio cuenta decisiones**, no filas: `/api/v1/pending-actions` decía 348 propuestas
   donde Revisión enseña 174 filas. Dos pantallas con dos números distintos del mismo trabajo es una
   contradicción que el producto no puede permitirse.
2. **El arnés de métricas admite motor elegible** (`--engine`), con el motor inyectado tipado contra
   `ClassifierPort`. Hoy solo hay uno, el determinista; el PoC registra el suyo en su propia rama y el
   informe **dice de quién son los números**.

## Cómo fluye la información

```
motor propone sobre el artefacto  ─┐
motor propone sobre su texto      ─┴─→ reconcile_pending_proposals (regla pura, dominio)
                                            │
                     ┌──────────────────────┴───────────────────────┐
                     ▼                                              ▼
        /review-groups (la cola)                    pending-actions (Inicio)
        una fila con las dos propuestas             «N decisiones sin tomar»
                     │
                     ▼
        decidir la fila decide **las dos** propuestas
        (el material y su texto quedan clasificados)
```

Nada se borra y nada se esconde: las dos propuestas siguen en `classification_proposals`, con su
estado, y viajan juntas en el grupo. La decisión es una; las filas siguen siendo dos.

## Ficheros y migraciones

Diez ficheros, **ninguna migración** (no hay cambio de esquema ni de contrato):

| Fichero | Qué cambia |
|---|---|
| `apps/api/opofuente/domain/classification.py` | `PendingProposal`, `decision_signature` y `reconcile_pending_proposals`: la regla, pura y sin base de datos |
| `apps/api/opofuente/infrastructure/classification_repository.py` | `pending_groups` agrupa por decisión; `_artifact_of_representations` da el enlace artefacto↔texto |
| `apps/api/opofuente/infrastructure/readiness_repository.py` | `_pending_decisions` cuenta decisiones **con la misma regla** |
| `apps/api/opofuente/application/readiness_models.py` | `pending_proposals` → `pending_decisions`, con el porqué |
| `apps/api/opofuente/application/readiness_service.py` | la cifra y su frase: «decisiones sin tomar» |
| `apps/api/opofuente/tools/classification_metrics.py` | `ENGINES`, `build_engine`, `--engine`, y el motor en el informe; las opciones se leen todas |
| `apps/api/tests/unit/test_classification_domain.py` | seis pruebas de la regla |
| `apps/api/tests/unit/test_classification_metrics.py` | tres pruebas del arnés |
| `apps/api/tests/integration/test_classification.py` | dos pruebas: el grupo decide los dos sujetos e Inicio cuadra con Revisión |
| `apps/api/tests/integration/test_readiness.py` | la cifra se compara con la pantalla que nombra (`/revision`), no con el listado de filas |

## Patrones y decisiones aplicadas

- **La regla vive en el dominio, no en el repositorio.** El módulo ya lo dice de sí mismo: «todo lo que
  decide qué se propone, qué se puede aceptar y qué cuenta como cobertura vive aquí, para poder probarlo
  sin motor de base de datos». La cola y el contador de Inicio la comparten en vez de escribirla dos
  veces en dos lenguajes.
- **Conservador por defecto.** Solo se junta lo **idéntico** (valor *y* confianza *y* motor). Dos valores
  distintos, o el mismo valor con otra confianza, son dos decisiones: el motor no se repite, se
  contradice, y eso hay que verlo.
- **El sujeto que manda es el artefacto**, que es lo que el usuario ve y nombra. La clave del grupo sigue
  siendo la del material, así que las claves que ya conocía la interfaz no cambian.
- **Ninguna opción se ignora en silencio.** El lector de argumentos recorría la lista y volvía en cuanto
  veía `--dataset`: un `--engine` detrás se perdía y el informe salía con los números de otro motor.
  Ahora se leen todas y lo que no se reconoce se rechaza.
- **El informe dice su motor y su versión.** Dos informes sin autor no se pueden comparar, y el PoC va a
  comparar tres.

## Seguridad y privacidad

- **No añade ninguna llamada saliente.** El producto sigue sin hablar con nada; el arnés sigue midiendo
  en local.
- **No toca originales** ni el material del propietario: la reconciliación es de lectura y de
  presentación.
- **No borra historia**: las propuestas siguen ahí y la auditoría de cada decisión no cambia de forma.
- Las pruebas de integración usan su propio directorio de datos (`.gates-data` / `.pytest-tmp`), nunca el
  del propietario, como dejó escrito DEBT-026.

## Puertas ejecutadas y resultado

| Puerta (10_TEST-PLAN §10) | Comando | Resultado |
|---|---|---|
| 1. formato | `uv run ruff format --check <mis 10 ficheros>` | **10 files already formatted** |
| 2. lint | `uv run ruff check <mis 10 ficheros>` | **All checks passed!** |
| 3. typecheck | `uv run mypy` | **Success: no issues found in 146 source files** |
| 6/7/8. unitarias, integración y contrato | `uv run pytest apps/api/tests -q` | **956 passed** en 840 s |
| 10. contrato OpenAPI y tipos | `uv run python -m opofuente.tools.export_openapi --check` | **Contrato sincronizado: `openapi.json`** (no cambia) |

**No ejecutadas, y por qué:** 4 (`eslint`), 5 (`typecheck` de TypeScript), 9 (Vitest), 11/12 (builds),
13–16 (migración desde cero y siembra), 17 (fixtures frente a las fuentes) y 18 (E2E). El cambio es de
backend y no toca esquema ni contrato, pero **no se declaran ejecutadas**. Además, el árbol de trabajo
tiene cambios de **otro agente** en curso (§Aviso), así que las puertas 4, 5 y 9 no serían atribuibles a
este trabajo aunque se ejecutaran.

## Prueba manual

```bash
# 1. El arnés sigue midiendo el motor de siempre y lo dice.
uv run python -m opofuente.tools.classification_metrics | head -2
#    Motor: determinista 1

# 2. Un motor que no existe no cae en silencio al de siempre: error y lista de los que hay.
uv run python -m opofuente.tools.classification_metrics --engine jev
#    ValueError: Motor desconocido: «jev». Disponibles: determinista   (código 1)

# 3. La opción se lee aunque vaya detrás de `--dataset` (antes se ignoraba).
uv run python -m opofuente.tools.classification_metrics \
  --dataset fixtures/synthetic/classification/dataset.json --engine determinista | head -2

# 4. La cola, con el material real: la fila del tipo documental lleva dentro las dos propuestas
#    (el material y su texto) y su tamaño es el doble de sujetos que antes tenía.
curl -s 127.0.0.1:8000/api/v1/review-groups | grep -o '"size":[0-9]*' | sort | uniq -c
```

## Limitaciones conocidas

1. **Queda un hueco, y es aparte.** `auto_study_service.py:316-326` promete en su comentario mirar la
   representación cuando el artefacto no tiene tipo, y luego hace `return None`. La reconciliación
   **reduce** el efecto —al aceptar el grupo se deciden las dos propuestas y el artefacto recupera su
   tipo—, pero un artefacto sin **ninguna** propuesta (2 de 96 en la base real) sigue sin tipo vigente y
   no dispara ADR-017. El arreglo (mirar las representaciones del artefacto) **no entra aquí**.
2. **La cifra de minutos de revisión sigue sin medirse** (DEBT-018): es del propietario y sin ella
   ninguna comparación de ahorro es concluyente.
3. **El contador de Inicio ha dejado de ser un `COUNT`** agregado, a propósito y con el porqué escrito en
   el módulo: son decenas o cientos de filas de nueve columnas, no el corpus.
4. **La reconciliación no fusiona valores distintos.** Si el motor propone `personal_notes` al material y
   `community_material` a su texto, siguen siendo dos filas: eso es un desacuerdo y merece verse.
5. **No hay prueba E2E de la pantalla de revisión** con esta regla (la suite E2E no se ha ejecutado).

## Qué se rompe si cambias X

- **Si quitas la exigencia de misma confianza**, empiezas a fusionar desacuerdos del motor y la cola deja
  de enseñar dónde se contradice: la banda alta se vuelve más fácil de alcanzar sin que nadie lo sepa.
- **Si quitas la exigencia de mismo motor**, dos motores que coincidan se leerán como uno repitiéndose, y
  con el PoC delante eso es justo la señal que quieres ver.
- **Si dejas de preferir el artefacto como sujeto canónico**, la clave del grupo cambia de forma, la
  interfaz pierde el hilo de las claves que ya conocía y el usuario ve el material nombrado por su id.
- **Si cuentas filas otra vez** en `_pending_decisions`, la pantalla de Inicio dirá el doble que la de
  Revisión: es el defecto que este cambio corrige.
- **Si la reconciliación tocara los datos** (fusionar filas en vez de agrupar) perderías la propuesta por
  sujeto y con ella la clasificación vigente del texto, que es la que sostiene la importación automática.

## Qué criticaría un revisor senior

1. **«Esto no es un slice y no hay ADR».** Cierto y a propósito: no añade dependencia ninguna y no cambia
   arquitectura. Si se acepta, el sitio natural es DEBT (una entrada que cierre el hallazgo de DEBT-018)
   y no un ADR.
2. **«La regla arregla la cola, no el dato.»** Cierto: la cola enseña decisiones, pero en la base siguen
   habiendo 348 filas. Es una decisión de diseño —no borrar historia—, y el precio es que cualquier
   consumidor nuevo tiene que usar la misma regla o contar el doble.
3. **«¿Y si el motor cambia de versión?»** Las propuestas antiguas quedan con su `engine_version`, y la
   regla exige misma versión: una propuesta vieja y otra nueva del mismo motor con el mismo valor **no**
   se juntan. Es conservador a propósito, y conviene decidir si se quiere así cuando haya dos motores.
4. **«El E2E no se ha ejecutado.»** Cierto, y la pantalla de revisión es justo lo que la regla cambia.
5. **«Hay otro agente escribiendo en el árbol.»** Ver el aviso; sin eso resuelto, ninguna puerta de este
   informe es reproducible tal cual.

---

## Aviso de proceso (importante)

Durante este trabajo, **otro agente** ha estado editando el **mismo árbol de trabajo**: hay ficheros
modificados que no son de este cambio (`apps/api/tests/integration/test_question_api.py`,
`apps/web/src/api/classification.ts`, `apps/web/src/api/queries.ts`,
`apps/web/src/features/review/ProposalList.tsx`, `apps/web/src/pages/ReviewPage.tsx`,
`apps/web/tests/e2e/questions.spec.ts`, `apps/web/tests/unit/review.test.tsx`, y un
`apps/web/tests/e2e/zz-medir.spec.ts` sin seguimiento que apareció y desapareció). Consecuencias:

- **No he commiteado nada** y no he tocado ni un fichero ajeno.
- `ruff check .` sobre el repo entero **falla por un fichero ajeno** (`test_question_api.py`, un E501 que
  está a medio escribir). Mis diez ficheros pasan limpios.
- La suite de 956 pruebas se ejecutó **con los cambios del otro agente dentro**, así que es un resultado
  bueno pero no atribuible al 100 % a este trabajo.
- La rama `fase0-reconciliacion-artefacto-representacion` la ven los dos agentes: si el otro estaba en
  `main`, ahora está en esta rama.
