# P0.1 — Las fechas con zona: el cronómetro deja de ir dos horas adelantado (5 de octubre de 2026)

Bloque 1 del plan `PLAN-PARA-DEEPSEEK-2026-10.md`. Rama `fechas-con-zona`, sacada de `main`
(`41e5319`).

## Lo que se veía

Al empezar una práctica, el cronómetro marcaba **`2:00:03`**; una sesión antigua mostraba
`94:53:57 · queda 00:00`. Un **examen oficial de 120 minutos nacía con el tiempo agotado**.

## La causa, medida

- La API servía las fechas **sin zona**: `"2026-10-03T06:03:03.128785"` (que es UTC).
- El navegador las interpreta como hora local (Madrid, UTC+2) → dos horas de más.
- El origen estaba en la base: las columnas `DateTime(timezone=True)` de **SQLite** no guardan la
  zona. Se escribe un `datetime` *aware* y se lee *naive*. Comprobado leyendo por el repositorio:

```
started_at leído: None
created_at leído: datetime.datetime(2026, 10, 3, 6, 3, 3, 128785) · tzinfo: None
```

- En la web solo había **un sitio** que leyera fechas (`features/study/labels.ts → elapsedSeconds`),
  así que el fallo se veía en el cronómetro y en ningún sitio más.

## El arreglo

1. **En la base, en un solo sitio**: un tipo de columna `UtcDateTime` (`infrastructure/db_models.py`)
   que al **leer** le vuelve a poner UTC y al **escribir** normaliza a UTC (y sigue guardando sin
   zona, para no cambiar el formato de los datos que ya hay). Se aplicó a las **79** columnas de
   fecha del modelo.
2. **En la web, defensivo**: `elapsedSeconds` toma por UTC cualquier fecha que llegue **sin** zona
   (datos antiguos, una copia restaurada), en vez de leerla como hora local.

## Cómo se comprueba (y con qué)

- `apps/api/tests/unit/test_db_datetime.py` (3 pruebas): una fecha escrita se lee **con UTC**; una
  fecha en Madrid se guarda en UTC y el fichero sigue sin zona; una fecha heredada sin zona se lee
  como UTC.
- `apps/api/tests/integration/test_study_api.py::test_las_fechas_de_la_sesion_vienen_con_su_zona`:
  las cinco fechas que sirve la API (`created_at`, `started_at`, en crear, arrancar, detalle y
  listado) terminan en `+00:00`.
- `apps/web/tests/unit/labels.test.ts` (5 pruebas): con una fecha `+00:00` el cronómetro cuenta los
  segundos reales (`30`), con una sin zona también, sin fecha devuelve `0`, y una fecha futura no
  cuenta hacia atrás.

## Medición antes / después (contra la API, con los datos del propietario)

| | antes | después |
| --- | --- | --- |
| `GET /study-sessions` → `created_at` | `2026-10-03T06:03:03.128785` | `2026-10-03T06:03:03.128785Z` |
| Cronómetro de la práctica en marcha (arrancada a las 10:43:52 UTC) | habría dicho `3:23:19` | dice **`1:23:19`** (los segundos reales) |
| Examen oficial TAI (120 min) | nace agotado | quedan `120:00` |

Medido con la API en marcha sobre los datos del propietario: la sesión de práctica que quedó en marcha
se arrancó a las `10:43:52.793645Z` y el cronómetro cuenta **4999 s** reales; antes de este arreglo, el
mismo dato daba 4999 + 7200 = 12199 s (las dos horas de Madrid), que es el `2:00:03` que se veía al
empezar.

## Riesgo que se vigiló

Cambiar la zona de lo que se **lee** puede romper comparaciones entre fechas (una *aware* contra una
*naive* lanza `TypeError`). El reloj de la aplicación ya devolvía `datetime.now(UTC)` (*aware*), así
que la comparación correcta era justamente la de ahora. Lo comprueba la suite de integración entera
(497 pruebas), que es donde están las comparaciones de tiempos, repasos vencidos y «hoy».

## Lo que queda del plan

Siguiente bloque: **P0.5 + P0.6** (descartar las sesiones de prueba, decir en la lista de qué examen es
cada una, y un aviso único si la API no responde).
