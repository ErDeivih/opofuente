# DEBT-018 — Revisión con material real: la mitad de la máquina, medida

**Fecha:** 21 de septiembre de 2026.
**Estado de la deuda: abierta.** Este documento entrega la **primera mitad** de lo que pide DEBT-018
—medir sobre material real— y deja escrito, con esas medidas delante, lo que falta y por qué no lo puedo
cerrar yo: el tiempo de revisión es una medición **humana** y el criterio 3 exige que la confirme el
propietario.

## Qué pidió la puerta (11_IMPLEMENTATION-SLICES, S04)

> Importar copia de 20–50 archivos TAI y medir revisión. **Si no ahorra tiempo, no iniciar S05 sin
> rediseño aprobado.**

DEBT-018 nació de que esa puerta se abrió sin ejecutarla: S04 inventarió en lectura y dio S05 por
desbloqueado. Los criterios de cierre son: un informe versionado con el tiempo de revisión medido sobre
material real —con las propuestas revisadas, aceptadas, corregidas y descartadas—, la decisión escrita, y
la confirmación del propietario.

## Qué se ha hecho aquí

**Material.** Una **copia** de 30 ficheros (29 PDF y 1 DOCX, 11,8 MB) de la carpeta de apuntes del
propietario, elegidos por nombre. **Los originales solo se han leído**: la copia se hizo con `Copy-Item`
y la importación volvió a copiar por contenido. El material es suyo y **no entra en el repositorio**: aquí
solo hay recuentos y tiempos.

**Dónde quedó**, para poder continuar la revisión:

| Qué | Dónde |
|---|---|
| Datos de la aplicación con el material importado | `F:\temp-opofuente\datos-apuntes-tai` (fuera del repositorio) |
| La copia de los 30 ficheros que se inventarió | `F:\temp-opofuente\apuntes-tai-copia` |
| Informe del lote (JSON) | `F:\temp-opofuente\informe-lote-apuntes.json` |

Para abrir esa base con las propuestas dentro, la aplicación se arranca con
`OPOFUENTE_DATA_DIR=F:\temp-opofuente\datos-apuntes-tai`. La copia de los 30 ficheros se puede borrar
después de la importación: lo que la aplicación guarda es su propia copia por contenido.

## Lo que mide la máquina (medido, no estimado)

| Paso | Qué se hizo | Tiempo |
|---|---|---|
| Inventario en lectura | `POST /inventories` sobre la copia: 30 descubiertos, 25 en la muestra, **0 incidencias** | 1,4 s |
| Confirmar importación | `POST /inventories/{id}/confirm-import`: copia por contenido y pipeline | 0,11 s (encolar) |
| Copia + extracción | el worker sobre los 30 ficheros: 12.372.456 bytes | 2,8 s |
| Clasificación determinista | `POST /classification-runs` | 46,7 s |

**Cuadre del lote** (contadores obligatorios de 04_INGESTION §11, `balanced: true`):

- descubiertos 30 · copiados 30 · pendientes 0 · fallidos 0 · cancelados 0 · conservados sin extractor 0 ·
  fuente cambiada 0;
- extraídos **30 de 30** (ninguno con avisos ni fallido), 0 duplicados exactos, 0 incidencias.

**Propuestas de clasificación** (el trabajo que hay que revisar):

| Eje | Propuestas | Aplicadas provisionalmente | Pendientes de revisar |
|---|---|---|---|
| `topic` (tema del programa) | 60 | 50 | 10 |
| `document_type` (tipo documental) | 28 | 2 | 26 |
| `authority` (autoridad) | 2 | 0 | 2 |
| **Total** | **90** | **52** | **38** |

Las 38 pendientes tienen confianza entre 0,5 y 0,72 (banda media) y cada una trae su evidencia textual.
Los sujetos con propuestas son 60 (cada fichero deja artefacto y representación).

**Lo que estos números dicen del diseño, sin adornos:** para 30 ficheros reales, la máquina deja **38
propuestas que alguien tiene que mirar una a una** y 52 aplicadas de forma provisional que conviene
confirmar. El coste de la revisión no es despreciable ni se reparte solo: se concentra en
`document_type` (26 de 38). Un rediseño que ahorre tiempo tiene ahí su primer objetivo.

## Lo que falta, y no puedo hacer yo

1. **El tiempo de revisión**, medido de verdad mientras el propietario revisa esas 38 propuestas (y
   confirma o descarta las 52 provisionales) en la pantalla de Revisión.
2. **Los cuatro recuentos humanos**: revisadas, aceptadas, corregidas y descartadas. La API los dará sin
   trampa en cuanto se decidan, pero decidirlos es el trabajo que se está midiendo.
3. **La decisión**: «el diseño se sostiene» o «se rediseña así», con su ADR si toca rediseñar.
4. **La confirmación del propietario** (criterio 3): es una puerta humana, no una medición automática.

Sin esos cuatro puntos, DEBT-018 sigue **abierta**: lo que hay aquí es la mitad que la máquina puede
medir, y la mitad que decide si el producto ahorra tiempo sigue pendiente de una persona.

## Método, para que se pueda repetir

```powershell
# 1. Copia de 20–50 ficheros (nunca se toca el origen)
$origen  = 'C:\Users\David\OneDrive\Escritorio\Apuntes TAI'
$destino = 'F:\temp-opofuente\apuntes-tai-copia'
Get-ChildItem -LiteralPath $origen -Recurse -File |
  Where-Object { $_.Extension -in '.pdf', '.docx', '.txt' } |
  Sort-Object Name | Select-Object -First 30 |
  ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $destino -Force }

# 2. Base de datos aparte, nunca la real
$env:OPOFUENTE_DATA_DIR = 'F:\temp-opofuente\datos-apuntes-tai'
uv run alembic upgrade head
uv run python -m opofuente.tools.seed_profiles
uv run python -m uvicorn opofuente.main:app --host 127.0.0.1 --port 8799
```

Después, por la API y con `Origin` permitido: `POST /inventories` → `POST /inventories/{id}/confirm-import`
→ esperar el lote → `POST /classification-runs` → contar con
`GET /classification-proposals?status=pending`.
