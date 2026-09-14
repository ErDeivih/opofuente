# ADR-001 — Herramientas y lockfiles de Python y Node

- **Estado:** aceptada (S00)
- **Fecha:** 2026-09-14
- **Ámbito:** tooling de desarrollo; no cambia arquitectura ni producto

## Contexto

`00_START-HERE.md` §3 fija el stack (Python 3.12, FastAPI, SQLAlchemy, Alembic; React,
TypeScript, Vite) y añade que «las dependencias exactas se fijarán en el lockfile del primer
slice». `02_ARCHITECTURE.md` §2 exige `pyproject.toml` + `uv.lock` y `package.json` +
`package-lock.json` en la raíz. Faltaba decidir con qué se gestiona el entorno de Python, cómo se
instala el paquete importable y cómo se organizan los paquetes de Node.

## Opciones

| Opción | A favor | En contra |
|---|---|---|
| `pip` + `requirements.txt` + `venv` | universal, cero dependencias nuevas | sin lockfile real ni resolución reproducible; entorno manual |
| Poetry | lockfile y gestión integrada | proyecto Python no-estándar, más pesado, otra herramienta que mantener |
| **uv + `pyproject.toml` + `uv.lock`** | resolución y lockfile reproducibles, rápido, respeta PEP 621, instala el paquete en editable | herramienta adicional (de código abierto, Apache-2.0/MIT, muy mantenida por Astral) |
| npm workspaces + `package-lock.json` | un solo `npm install`, una sola instalación para web y contratos | obliga a nombrar los paquetes y a declarar dependencias cruzadas explícitas |
| Repos npm separados | aislamiento | dos instalaciones, dos lockfiles, versiones divergentes |

## Datos

- Python instalado: 3.12.10 (`C:\Python312`), uv 0.12.12, Node 24.19.0, npm 11.2.0.
- `uv sync` instala el proyecto raíz en modo editable usando `hatchling` con
  `packages = ["apps/api/opofuente"]`, lo que mantiene una sola declaración de dependencias y
  respeta la estructura obligatoria (`apps/api/...`) sin duplicar `pyproject.toml`.
- `uv.lock` fija versiones exactas de las 41 dependencias resueltas; `package-lock.json` hace lo
  propio en Node.

## Decisión

Usar **uv** con `pyproject.toml`/`uv.lock` en la raíz y **npm workspaces** con
`apps/web` (`@opofuente/web`) y `packages/contracts` (`@opofuente/contracts`). Alembic vive en la
raíz (`alembic.ini`) y apunta a `apps/api/alembic`, resolviendo la URL desde `Settings` para que
las pruebas puedan usar un directorio temporal.

## Consecuencias

- Instalación limpia = `./scripts/install.ps1` (`uv sync` + `npm install`).
- Cualquier dependencia nueva exige propuesta con licencia, mantenimiento y alternativa
  (`12_HANDOFF-DEEPSEEK.md`), y una ADR si afecta a arquitectura.
- El grupo `dev` de uv incluye Ruff, mypy, pytest y httpx; no se instalan herramientas por script.
- Riesgo asumido: uv es una herramienta externa al ecosistema estándar. Reversión: al ser PEP 621,
  el mismo `pyproject.toml` funciona con `pip install -e .` y `pip-compile`.

## Reversión

Sustituir uv por pip/pip-tools no afecta al código: solo a `scripts/*.ps1` y al lockfile. Igual en
Node: los workspaces se pueden separar en dos `package.json` independientes sin tocar el código.
