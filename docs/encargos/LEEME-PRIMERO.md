# LEEME PRIMERO — corrección del encargo (02/11/2026)

Si estás trabajando en `docs/encargos/2026-11-02-temario-c1-y-panel-oposiciones.md`, **lee su sección 0
otra vez**: se corrigió a las 16:xx y antes decía una ruta de base equivocada.

## Lo que estaba mal y lo que es verdad

- ❌ `F:\EspacioCodigo\opofuente\data\opofuente.sqlite3` (0 MB) **no** es la base buena: es el worktree
  viejo de la rama `fase0-reconciliacion-artefacto-representacion` (98d8e60).
- ✅ **La base real es `F:\OpoFuente\datos\opofuente.sqlite3`** — 2.656 MB, 76 tablas:
  `curriculum_nodes` **401**, `exam_parts` 12, `exam_rules` 59, `oppositions` **3**,
  `convocation_versions` 4, `question_versions` **18.889**, `cards` 5.283, `source_artifacts` **6.259**.
- ✅ **Copias verificadas**: `F:\OpoFuente\datos\backups` (6).
- ✅ **Código bueno**: `main = 6483111`, presente en `F:\temp-opofuente\opofuente-restaurado` y en este
  worktree (`equipo-ia`).

## Reglas que no se rompen (del propio proyecto)

1. Los datos del propietario **no se borran ni se sustituyen**: se archivan.
2. Antes de tocar la base real: **copia verificada con `integrity_check`**.
3. Un punto está hecho si se cumple **en la base real y en la app que arranca `scripts\api.ps1`**, no en
   una siembra.
4. Las capturas se hacen **sobre una copia** y con el paquete construido en ese momento.

## Qué aporta el encargo (y qué NO hay que repetir)

- **NO** rehacer temario, tests, simulacros, repaso ni el panel de administración: ya están.
- **SÍ** añadir la **oposición C1 Informática** (40 temas del común en 5 bloques + locales por
  convocatoria) sobre el esquema existente, sin duplicar los 401 nodos actuales.
- **SÍ** construir el **panel de convocatorias C1 informática** (ingesta oficial BOE/PAG/BOCYL/BOP,
  plazos en días hábiles con festivos, filtros C1+informática): eso no existe todavía.
