# OpoFuente

Biblioteca personal **local** para organizar y estudiar material de oposiciones (TAI y Guardia
Civil). Convierte una carpeta desordenada de documentos y preguntas en un sistema de estudio
trazable, sin mover ni borrar ningún original y sin depender de servicios en la nube.

- Especificación completa: [`docs/product-spec/`](docs/product-spec/00_START-HERE.md) (17 documentos).
- Contrato de implementación para agentes: [`AGENTS.md`](AGENTS.md).
- Estado de implementación: [`docs/slices/`](docs/slices/).

> **Estado actual: S11 completado** (importador y banco de preguntas, sesiones y puntuación exacta
> TAI y Guardia Civil, búsqueda léxica con respuestas extractivas citadas, revisión de errores y
> exportación, y cambio de material con evaluación de lo que queda pendiente de revisar), además de
> S00–S10. Lo que **todavía no** existe se declara en `/api/v1/capabilities` y en la interfaz en lugar
> de simularse: OCR no ejecutado (una imagen queda pendiente con su aviso), sin modelo de lenguaje ni
> índice vectorial (la búsqueda es léxica y la respuesta se compone del corpus), sin dataset RAG
> medido, sin baremo oficial importado (no se inventa la calificación 0–50 ni el apto) y sin
> simulacro ni examen diagnóstico (responden 409 con el motivo). El detalle de cada ausencia está en
> [`docs/DEBT.md`](docs/DEBT.md).
>
> Desde la pantalla **Bandeja** puedes inventariar una carpeta en modo lectura, soltar ficheros, pegar
> texto o traer una URL, y leer el texto extraído por trozos con su calidad y sus avisos a la vista.
> OpoFuente **nunca** mueve, renombra ni borra tus originales: la copia va a un almacén por contenido
> (`data/artifacts/sha256/ab/cd/<hash>`), así que dos ficheros idénticos son un solo artefacto con dos
> orígenes. Una URL se descarga solo si es `http`/`https` pública (cada redirección se revalida) y un
> ZIP se expande con límites de entradas, bytes, ratio y profundidad. Ver
> [`docs/slices/`](docs/slices/) para el recorrido completo, slice a slice.
>
> Los perfiles TAI 2025 y Guardia Civil 2026 se siembran desde fuentes oficiales verificadas por
> hash y por cita literal. Ver [`fixtures/profiles/manifest.json`](fixtures/profiles/manifest.json)
> y [`docs/decisions/ADR-006`](docs/decisions/ADR-006-fixtures-desde-fuentes-oficiales.md).

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

`install.ps1` sincroniza el entorno de Python con `uv sync --locked`, instala las dependencias de
Node con `npm ci` (ambos respetan los ficheros de bloqueo versionados) y comprueba que las dos
herramientas responden. Si las políticas de PowerShell bloquean los scripts, usa
`pwsh -ExecutionPolicy Bypass -File ./scripts/install.ps1`.

## 3. Comandos

| Acción | Comando |
|---|---|
| Instalar todo | `./scripts/install.ps1` |
| Migrar la base de datos | `./scripts/migrate.ps1` |
| Sembrar los perfiles oficiales | `./scripts/seed.ps1` |
| Descargar y verificar las fuentes oficiales | `./scripts/fetch-sources.ps1` |
| Arrancar API + web en desarrollo | `./scripts/dev.ps1` |
| API sola | `./scripts/api.ps1` |
| Web sola | `./scripts/web.ps1` |
| Todas las puertas de calidad | `./scripts/gates.ps1` |
| Pruebas backend | `./scripts/test.ps1 -Api` (o `uv run pytest`) |
| Pruebas frontend | `./scripts/test.ps1 -Web` (o `npm run test:web`) |
| E2E (Playwright) | `./scripts/e2e.ps1` |
| Build de producción local | `./scripts/build.ps1` |
| Exportar OpenAPI y tipos | `./scripts/export-openapi.ps1` |
| Ver los bancos con preguntas sin tema | `uv run python -m opofuente.tools.clasificar_preguntas --listar` |
| Clasificar por tema y epígrafe | `uv run python -m opofuente.tools.clasificar_preguntas --bancos 2` |

### Clasificar preguntas por tema y epígrafe (F4)

El clasificador pide a DeepSeek un tema (y un epígrafe, si lo tiene claro) para cada pregunta **sin
tema**, banco a banco y de mayor a menor, y escribe por el servicio auditado del banco. La clave se
lee de la variable de entorno y **no** se guarda en ningún sitio; sin ella, el comando para:

```powershell
$env:DEEPSEEK_API_KEY = "…"                        # jamás en un fichero del repositorio
uv run python -m opofuente.tools.clasificar_preguntas --bancos 2 --dry-run   # ensayo: no escribe
uv run python -m opofuente.tools.clasificar_preguntas --bancos 2             # los dos primeros
```

Lo de confianza alta entra (`accepted`), lo dudoso queda como propuesta provisional en la cola de
revisión (`GET /api/v1/question-exclusions` lista lo que se declaró fuera de temario) y lo que no es
materia del programa se marca fuera de temario, que lo deja fuera de simulacros y exámenes oficiales.

### La cola de revisión de la clasificación (F5)

En el panel, **Clasificación** (`/admin/clasificacion`, y también la dirección documentada
`/admin/preguntas?revisar_tema=1`) despacha con el teclado las propuestas que dejó el clasificador:
una tarjeta por pregunta, con el enunciado, sus opciones, el tema y el epígrafe propuestos, la
confianza y el motivo del modelo. `A` acepta, `C` cambia de tema o epígrafe, `F`/`X` marcan fuera de
temario, `S` salta, `R` retira lo que sobra y `G` guarda **en una sola llamada** todo lo decidido
(`POST /api/v1/questions/topics/bulk`). Aceptar un tema **retira** las demás propuestas de esa
pregunta: una pregunta no puede acabar con dos temas.

El clasificador toma una **marca de corrida** en `app_metadata` (`clasificacion_en_curso`) antes de
empezar y la suelta al terminar, pase lo que pase: dos corridas a la vez sobre la misma base calculan
sus pendientes antes de que la otra escriba y acaban proponiendo dos temas a la misma pregunta (pasó
el 8 de octubre de 2026). La segunda se niega y dice desde cuándo corre la primera; si el proceso
murió de golpe, la marca se puede retirar a mano o se da por muerta a las 12 h.

Las puertas 17 y 18 necesitan las fuentes oficiales ya descargadas (`fetch-sources.ps1`) y el
navegador de Playwright (`npx playwright install chromium`).

Tres cosas que ya han costado una corrida entera, dichas donde se buscan:

- **no** las metas en una tubería de PowerShell (`./scripts/gates.ps1 2>&1 | Tee-Object …`): el
  `stderr` de `uv` se vuelve error terminante y la puerta 11 falla con código −1 sin estar rota. Para
  guardar el registro, redirige con `Start-Process -RedirectStandardOutput`/`-RedirectStandardError`
  —los `OK:` van por `Write-Host`— y **nunca** con `>`;
- la puerta 17 necesita `data/sources/` en **ese** árbol: está ignorado por git, así que un clon
  nuevo no lo trae y la puerta falla con «faltan fuentes locales» pareciendo un fallo del código
  (`./scripts/fetch-sources.ps1`);
- la puerta 18 necesita el puerto **8765 libre**: Playwright no reutiliza un servidor que ya escuche
  (DEBT-021), así que con una API arrancada la suite aborta. Compruébalo con
  `Get-NetTCPConnection -State Listen -LocalPort 8765` antes de lanzarlas.

Direcciones por defecto: API en `http://127.0.0.1:8765` (documentación en
`http://127.0.0.1:8765/api/v1/docs`), web de desarrollo en `http://127.0.0.1:5173`.

## 4. Estructura

```text
opofuente/
  AGENTS.md                 contrato de implementación
  pyproject.toml            backend + configuración de Ruff, mypy y pytest
  alembic.ini               migraciones (la URL se resuelve desde la app)
  package.json              workspaces npm (apps/web, packages/contracts)
  apps/api/opofuente/       backend FastAPI por capas (api/domain/application/infrastructure + workers)
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
  `backups/`, `tmp/`, y `sources/` (documentos oficiales descargados para construir los fixtures).
- **Tus originales no se tocan.** Inventariar una carpeta solo la lee; importar copia el contenido
  al almacén por hash. OpoFuente nunca mueve, renombra ni borra nada del origen, y la ruta real de
  la carpeta de origen no se publica por la API (solo una versión abreviada).
- El servidor escucha **solo** en loopback. Configurar un host público provoca un error de arranque.
- No hay telemetría. Los logs son JSON rotativos y no registran contenido importado, preguntas
  privadas, prompts ni claves.
- Las claves de proveedores de IA se leen del entorno (`.env`), nunca se devuelven por la API y
  nunca se escriben en el repositorio.
- `.env.example` documenta todas las variables; copia a `.env` solo si necesitas cambiarlas.

### Procedencia del programa oficial

Los perfiles se construyen desde los documentos oficiales y cada cifra lleva su cita:

- el texto del BOE se reutiliza con las condiciones de su
  [aviso legal](https://www.boe.es/informacion/aviso_legal/index.php) (citar la fuente, no alterar
  el sentido, no sugerir carácter oficial);
- el temario de la Guardia Civil está limitado a **uso privado**: OpoFuente es local y no
  redistribuye, y por eso el repositorio y la aplicación deben seguir siendo privados (DEBT-003 en
  [`docs/DEBT.md`](docs/DEBT.md));
- los documentos descargados **no** se versionan: se guardan en `data/sources/` y se verifican por
  `sha256` contra `fixtures/profiles/manifest.json` con `scripts/fetch-sources.ps1`.

## 6. Licencia

Sin decidir todavía (ver `docs/product-spec/13_DECISIONS-AND-OPEN-QUESTIONS.md`). No se distribuye
material de terceros con el repositorio.
