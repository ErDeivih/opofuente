# OpoFuente

Biblioteca personal **local** para organizar y estudiar material de oposiciones (TAI y Guardia
Civil). Convierte una carpeta desordenada de documentos y preguntas en un sistema de estudio
trazable, sin mover ni borrar ningún original y sin depender de servicios en la nube.

- Especificación completa: [`docs/product-spec/`](docs/product-spec/00_START-HERE.md) (17 documentos).
- Contrato de implementación para agentes: [`AGENTS.md`](AGENTS.md).
- Estado de implementación: [`docs/slices/`](docs/slices/).

> **Estado actual: S00 completado** (repositorio, puertas de calidad, esqueleto de backend y
> frontend, migración inicial, health/capabilities). Todavía **no** hay entidades de negocio,
> ingestión, OCR, IA ni pantallas de producto: cada ausencia se declara explícitamente en la API
> (`/api/v1/capabilities`) y en la interfaz.

## 1. Requisitos (Windows 11)

| Herramienta | Versión usada | Comprobación |
|---|---|---|
| Python | 3.12.x | `python --version` |
| uv | 0.12.x | `uv --version` |
| Node.js | ≥ 20 (probado con 24.19) | `node --version` |
| npm | ≥ 10 (probado con 11.2) | `npm --version` |
| Git | ≥ 2.40 | `git --version` |

Tesseract, Qdrant y cualquier proveedor de IA son **opcionales** y no se instalan solos.

## 2. Instalación limpia

```powershell
git clone <url-del-repositorio> F:\EspacioCodigo\opofuente
cd F:\EspacioCodigo\opofuente
./scripts/install.ps1
```

`install.ps1` sincroniza el entorno de Python con `uv sync`, instala las dependencias de Node con
`npm install` y comprueba que ambas herramientas responden. Si las políticas de PowerShell bloquean
los scripts, usa `pwsh -ExecutionPolicy Bypass -File ./scripts/install.ps1`.

## 3. Comandos

| Acción | Comando |
|---|---|
| Instalar todo | `./scripts/install.ps1` |
| Migrar la base de datos | `./scripts/migrate.ps1` |
| Arrancar API + web en desarrollo | `./scripts/dev.ps1` |
| API sola | `./scripts/api.ps1` |
| Web sola | `./scripts/web.ps1` |
| Todas las puertas de calidad | `./scripts/gates.ps1` |
| Pruebas backend | `./scripts/test.ps1 -Api` (o `uv run pytest`) |
| Pruebas frontend | `./scripts/test.ps1 -Web` (o `npm run test:web`) |
| E2E (Playwright) | `./scripts/e2e.ps1` |
| Build de producción local | `./scripts/build.ps1` |
| Exportar OpenAPI y tipos | `./scripts/export-openapi.ps1` |

Direcciones por defecto: API en `http://127.0.0.1:8765` (documentación en
`http://127.0.0.1:8765/api/v1/docs`), web de desarrollo en `http://127.0.0.1:5173`.

## 4. Estructura

```text
opofuente/
  AGENTS.md                 contrato de implementación
  pyproject.toml            backend + configuración de Ruff, mypy y pytest
  alembic.ini               migraciones (la URL se resuelve desde la app)
  package.json              workspaces npm (apps/web, packages/contracts)
  apps/api/opofuente/       backend FastAPI por capas (api/domain/application/infrastructure)
  apps/api/alembic/         migraciones
  apps/api/tests/           unitarias, integración y contrato
  apps/web/                 React + TypeScript + Vite (shell, páginas, componentes)
  packages/contracts/       OpenAPI generado y tipos TypeScript derivados
  scripts/                  scripts PowerShell de instalación, desarrollo y puertas
  fixtures/synthetic/       material de prueba creado para tests (nunca material comercial)
  docs/product-spec/        especificación de producto
  docs/decisions/           ADR
  docs/slices/              explicación de cada slice
  data/                     datos locales (ignorado por git)
```

## 5. Datos y privacidad

- Todo vive en `OPOFUENTE_DATA_DIR` (por defecto `./data`, ignorado por git):
  `opofuente.sqlite3`, `artifacts/sha256/`, `extracted/`, `qdrant/`, `logs/`, `exports/`,
  `backups/`, `tmp/`.
- El servidor escucha **solo** en loopback. Configurar un host público provoca un error de arranque.
- No hay telemetría. Los logs son JSON rotativos y no registran contenido importado, preguntas
  privadas, prompts ni claves.
- Las claves de proveedores de IA se leen del entorno (`.env`), nunca se devuelven por la API y
  nunca se escriben en el repositorio.
- `.env.example` documenta todas las variables; copia a `.env` solo si necesitas cambiarlas.

## 6. Licencia

Sin decidir todavía (ver `docs/product-spec/13_DECISIONS-AND-OPEN-QUESTIONS.md`). No se distribuye
material de terceros con el repositorio.
