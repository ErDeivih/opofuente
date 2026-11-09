# Plan de despliegue — fase 2 (qué infraestructura, qué es gratis de verdad y qué falta)

**Fecha:** 09/11/2026 · **Autor:** teammate `despliegue` (equipo de David, sesión Team Lead `lead`) ·
**Origen:** encargo de David — «preparar el despliegue (fase 2): qué infraestructura necesita
(Postgres, API, web), opciones gratuitas y qué falta para que se pueda usar de verdad».

**Estado:** propuesta documental. **No se ha desplegado nada, no se ha abierto ningún servidor y no se
ha creado ninguna cuenta.** Este documento no autoriza nada: las decisiones de seguridad, licencia y
derechos que aparecen en §5 las toma David con ADR (§5, tabla final).

Convención de honestidad usada en todo el documento:

| Marca | Significado |
|---|---|
| **[V]** | Verificado en la fuente citada, consultada el **09/11/2026**. Se cita URL y, cuando la página lo publica, su fecha de última actualización. |
| **[A]** | Asumido por quien escribe a partir del código o del comportamiento documentado; **no** comprobado contra el proveedor. |
| **[NV]** | **No verificado**: la página no se pudo leer (mantenimiento, contenido truncado, 404, muro de JS) o el dato no existe. No se inventa la cifra. |

---

## 0. Resumen para decidir en dos minutos

1. **La aplicación no está lista para hospedarse en un PaaS "de verdad" sin trabajo**: no hay
   `Dockerfile` ni `docker-compose` (verificado: no existe ese fichero en el repo), la base es SQLite
   con FTS5, los artefactos van a disco local, el worker vive dentro del proceso de la API y el
   frontend tiene la URL de la API y el CSP **fijados al loopback en el propio HTML**
   (`apps/web/index.html:31-32`). Nada de eso es un impedimento técnico grave; es trabajo, y hay que
   contarlo antes de prometer una URL pública.
2. **El plan gratuito de Postgres gestionado no cabe con los datos reales.** La base medida de
   OpoFuente es de **2.656 MB** (`docs/encargos/2026-11-02-temario-c1-y-panel-oposiciones.md:14`). Los
   planes gratuitos de 2026 dan **500 MB** (Supabase), **1 GB** por proyecto (Neon, Aiven, Render) —
   [V]. Un Postgres de 0 € para *el corpus de David* no existe; un Postgres de 0 € para *un corpus
   pequeño de demostración* sí (cabe de sobra en 1 GB).
3. **La fase 1 (demo privada de un solo usuario) no necesita Postgres ni almacén S3.** Con una máquina
   gratuita, Docker Compose, SQLite en un volumen y el worker como servicio aparte se tiene lo mismo
   que hay hoy, servido por HTTPS. Coste 0 € **si** hay capacidad en Oracle Cloud Always Free (§3.3),
   con el riesgo real de reclamación por inactividad.
4. **La regla de loopback no hay que romperla para publicar.** Basta poner un proxy en la **misma
   máquina** (`cloudflared`, Caddy o WireGuard): la app sigue escuchando en `127.0.0.1` y
   `config.py:197-208` sigue cumpliéndose. Cambiar la guardia para escuchar en `0.0.0.0` sí es cambio
   de seguridad (Nivel 3) y requiere ADR; **no lo propongo**.
5. **Mientras DEBT-003 siga abierta, no se da acceso a terceros.** El temario de Guardia Civil está en
   los fixtures y su licencia es de uso privado (`docs/DEBT.md:158-180`). Eso incluye una "demo
   privada": un demo con un tercero ya es dar acceso. Y descarta GitHub Pages en su plan gratuito,
   porque exige repositorio **público** (§3.4).

Las tres decisiones que David debe tomar antes de que este plan avance están en §5.6.

---

## 1. Lo que hay hoy, medido en el código

No es una descripción de la idea del producto: es lo que el proceso hace hoy, con la línea donde se ve.

| Pieza | Cómo está hoy | Dónde |
|---|---|---|
| Servidor | Uvicorn + FastAPI, host y puerto desde configuración | `apps/api/opofuente/main.py:433-444` |
| Guardia de red | Solo `127.0.0.1`, `::1`, `localhost`; cualquier otro host **falla al arrancar** | `apps/api/opofuente/config.py:28`, `:197-208` |
| Base de datos | SQLite (WAL, `foreign_keys=ON`, `busy_timeout`) vía SQLAlchemy 2 | `apps/api/opofuente/infrastructure/db.py:43-63` |
| Búsqueda | **FTS5** con tabla externa `evidence_fts`, disparadores y `bm25()` | `apps/api/alembic/versions/0018_search_and_rag.py:48-77`, `apps/api/opofuente/infrastructure/search_repository.py:79-137` |
| Artefactos | Ficheros por SHA-256 en `data/artifacts/sha256/ab/cd/<hash>`, escritura atómica y `fsync` | `apps/api/opofuente/infrastructure/artifact_store.py:51-96` |
| Representaciones (texto extraído) | Ficheros en `data/extracted/` | `apps/api/opofuente/infrastructure/representation_store.py:70-135` |
| Worker | Tarea `asyncio` **dentro del proceso de la API**, cola en SQLite con lease | `apps/api/opofuente/main.py:321-338`, `:350-357`, `apps/api/opofuente/workers/job_worker.py:1-13` |
| Cola | `claim_next` por `UPDATE` condicional + relectura: **soporta varios procesos** sobre la misma base | `apps/api/opofuente/infrastructure/job_repository.py:101-149` |
| Copias | Instantánea con la API de respaldo de SQLite + ZIP con manifiesto y hashes | `apps/api/opofuente/infrastructure/backup_archive.py:61-86`, `:115-174` |
| Migraciones | Alembic con `render_as_batch=True` (reconstrucción de tablas propia de SQLite) | `apps/api/alembic/env.py:33-55` |
| Salud | `GET /api/v1/health/live` y `/health/ready` (503 si falta migrar) | `apps/api/opofuente/api/routes/system.py:40-86` |
| Logs | JSON a stderr **y** a fichero rotativo en `data/logs/` | `apps/api/opofuente/infrastructure/observability.py:74-105` |
| Seguridad de respuestas | CSP/`x-frame-options`/`nosniff` + comprobación de `Origin` para escrituras | `apps/api/opofuente/api/middleware.py:26-34`, `:61-84` |
| Frontend | React 19 + Vite; `VITE_API_BASE_URL` resuelto **en el build** | `apps/web/src/api/client.ts:3`, `:38-41` |
| CSP del frontend | `connect-src 'self' http://127.0.0.1:8765 …` escrito a mano en el HTML | `apps/web/index.html:31-32` |
| Autenticación | **No hay**. No hay tabla de usuarios; la sesión de estudio es global | `apps/api/opofuente/infrastructure/db_models.py:389` (comentario: «no hay `user_id`») |
| Empaquetado de despliegue | **No hay** `Dockerfile`, `docker-compose*`, `_headers`, `_redirects` (verificado por búsqueda en el repo) | — |
| Datos reales | `opofuente.sqlite3` ≈ **2.656 MB**, 76 tablas, 18.889 versiones de pregunta, 6.259 artefactos | `docs/encargos/2026-11-02-temario-c1-y-panel-oposiciones.md:14` |

Consecuencia que ordena todo el plan: **el producto de hoy es correcto para loopback y un usuario, y
está explícitamente diseñado para no salir de ahí** (`09_SECURITY-PRIVACY-AND-RIGHTS.md:26-27`: «antes
de cualquier despliegue en LAN o nube, autenticación, autorización y aislamiento multiusuario son un
proyecto separado»).

---

## 2. Arquitectura objetivo mínima

### 2.1 Diagrama (objetivo de fase 2)

```text
                        ┌──────────────────────────┐
   David / usuario      │  Cloudflare Pages        │   dist/ estático (HTML+JS+CSS)
   con permiso ────────▶│  (o Caddy en la VM)      │   sin secretos, sin datos
                        └────────────┬─────────────┘
                                     │  fetch JSON  https://api.<dominio>
                                     ▼
                        ┌──────────────────────────┐
                        │  Entrada / TLS           │   cloudflared (túnel, sin abrir puertos)
                        │  + autenticación de      │   o Caddy + Let's Encrypt
                        │    borde (Access/VPN)    │
                        └────────────┬─────────────┘
                                     │  127.0.0.1:8765   ← la app NO sale de loopback
                                     ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │  VM (Oracle Always Free, 2 OCPU / 12 GB A1)   ·  Docker Compose  │
   │                                                                  │
   │  ┌─────────────┐   SQLAlchemy   ┌──────────────────────────────┐ │
   │  │ API FastAPI │───────────────▶│  Postgres (fase 2)           │ │
   │  │ uvicorn     │                │  o SQLite en volumen (fase 1)│ │
   │  └──────┬──────┘                └──────────────▲───────────────┘ │
   │         │ cola `jobs` (lease)                  │                 │
   │  ┌──────▼──────┐   mismos handlers             │                 │
   │  │ Worker      │───────────────────────────────┘                 │
   │  │ proceso     │                                                 │
   │  │ aparte      │   ┌──────────────────────────────────────────┐  │
   │  └─────────────┘   │ Artefactos + representaciones            │  │
   │                    │ fase 1: volumen disco (200 GB)           │  │
   │                    │ fase 2: bucket S3-compatible (R2)        │  │
   │                    └──────────────────────────────────────────┘  │
   │  systemd timer ──▶ copia verificada ──▶ fuera de la VM (R2/disco)│
   └──────────────────────────────────────────────────────────────────┘
```

### 2.2 Qué habla con qué, y por qué

| Enlace | Protocolo | Nota de diseño |
|---|---|---|
| Navegador → web estática | HTTPS | Ningún dato del usuario; el bundle no lleva claves (`09_SECURITY §2`) |
| Navegador → API | HTTPS/JSON | CORS y `Origin` acotados a la URL pública (`config.py:31-36`, `middleware.py:61-84`) |
| Entrada → API | HTTP a `127.0.0.1:8765` | **Así se conserva la guardia de loopback** sin bajar seguridad |
| API → base de datos | TCP 5432 (Postgres) o fichero (SQLite) | En fase 1, mismo host; en fase 2, Postgres gestionado |
| API/Worker → almacén | Disco o S3 | En fase 1, disco; S3 solo cuando haya más de un nodo |
| Worker → cola | Misma base (`jobs`) | El lease ya es multi-proceso; ver §4.5 |
| Copias → destino | S3/rsync | Fuera de la máquina que se copia; verificación obligatoria |
| TLS/dominio | Let's Encrypt (Caddy) o Cloudflare | Cloudflare = tercero que ve metadatos y tráfico (§5.4) |

### 2.3 Dos variantes, y por qué recomiendo la primera ahora

| | **Variante A — fase 1 (recomendada ya)** | **Variante B — objetivo fase 2** |
|---|---|---|
| Base de datos | SQLite en volumen del host | Postgres gestionado o autoalojado |
| Artefactos | Disco del host (200 GB) | Bucket S3-compatible |
| Usuarios | 1 (David) o 2-3 con acceso de red | Multiusuario con cuentas |
| Trabajo previo | 3 slices (§6.2) | 6-10 slices de datos + 3 de producto (§6.3) |
| Coste | 0 € | 0 € hasta ~20 GB de Postgres y ~10 GB de objetos; después, céntimos |

La variante B es la que pide el encargo y está dibujada arriba; **la A es la que se puede tener en
semanas sin tocar la capa de datos**. Empezar por B es gastar 6-10 slices en migrar FTS5, defaults
booleanos y `batch_alter_table` antes de que exista un solo usuario remoto.

---

## 3. Opciones gratuitas en 2026 (verificado pieza a pieza)

### 3.1 Método

Búsqueda web y lectura directa de las páginas de precios/documentación de cada proveedor el
**09/11/2026**. Cuando la página publica su propia fecha de actualización, se copia. Lo que no se pudo
leer va marcado [NV] y **sin cifras**. No se han creado cuentas: los límites son los que el proveedor
publica, no los que se hayan comprobado en una cuenta real (eso queda como paso de verificación, §10).

### 3.2 Postgres gestionado

| Proveedor | Plan gratuito [V] | Letra pequeña que importa aquí | ¿Cabe la base real (2.656 MB)? | URL |
|---|---|---|---|---|
| **Neon** | 100 proyectos, 10 ramas/proyecto, **100 CU-horas/proyecto/mes**, **1 GB de storage por proyecto** (20 GB por cuenta), 5 GB de tráfico público/proyecto/mes, autoescalado hasta 2 CU (~8 GB RAM), **scale-to-zero a los 5 min** (no se puede desactivar), restauración instantánea de 6 h, 1 snapshot manual, Object Storage 5 GB/proyecto y Better Auth gestionado hasta 60.000 MAU incluidos | Al agotar CU-horas o tráfico, **el cómputo se suspende hasta el mes siguiente**; al pasar de 1 GB, fallan las escrituras que aumenten almacenamiento (no se factura exceso en Free); el cómputo suspendido no consume CU-horas pero el storage cuenta | **No** (1 GB < 2,6 GB). Sí cabe un corpus de demo | [neon.com/faqs/free-plan-limits-and-quotas](https://neon.com/faqs/free-plan-limits-and-quotas) (actualizada 03/11/2026) · [neon.com/blog/neon-free-plan-1-gb-per-project](https://neon.com/blog/neon-free-plan-1-gb-per-project) (02/10/2026) |
| **Supabase** | 500 MB de base (CPU compartida, 500 MB RAM), 5 GB de egress, 1 GB de ficheros, 50.000 MAU, 2 proyectos activos, **sin copias automáticas** en Free | **Los proyectos Free se pausan tras una semana de inactividad**; sin PITR ni backups; subida máxima 50 MB por fichero; retención de logs 1 día | **No** (500 MB) | [supabase.com/pricing.md](https://supabase.com/pricing.md) |
| **Aiven for PostgreSQL** | Nodo único, **1 CPU, 1 GB RAM, 1 GB de disco**, copias incluidas, extensiones, sin tarjeta, **sin límite temporal** | `max_connections=20`, sin pooling, sin IP estática, sin integraciones, un servicio Free por tipo y organización; **pueden apagar el servicio si no hay actividad continuada** (con aviso) y no cubre SLA | **No** (1 GB) | [aiven.io/docs/products/postgresql/concepts/pg-free-tier](https://aiven.io/docs/products/postgresql/concepts/pg-free-tier) (actualizada 08/09/2026) |
| **CockroachDB Basic** | **[NV]** — la página de planificación se sirvió truncada; no reproduzco cifras de memoria | — | — | [docs.cockroachlabs.com/…/plan-your-cluster-basic](https://docs.cockroachlabs.com/docs/cockroachcloud/plan-your-cluster-basic) |
| **Render Postgres free** | **1 GB fijo**, una sola base Free por workspace, **sin copias**, sin pooling | **Caduca a los 30 días de crearse**; 14 días de gracia para subir a pago y después se borra con los datos. No sirve ni para demo duradera | **No** | [render.com/docs/free](https://render.com/docs/free) |
| **Koyeb Postgres** | Instancia «Free 5h»: 0,25 vCPU / 1 GB RAM / **1 GB storage**, solo 5 h | El resto de cómputo de Koyeb es de pago (§3.3) | **No** | [koyeb.com/pricing](https://www.koyeb.com/pricing) |
| **Postgres autoalojado en la VM** | 0 € (entra en la VM gratuita), **sin límite de tamaño** salvo el disco (200 GB Always Free) | Lo operas tú: copias con `pg_dump`/`pg_basebackup`, parches, versiones. Es la única opción de 0 € que cabe con 2,6 GB | **Sí** | [docs.oracle.com — Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) |

**Lectura honesta:** los planes gratuitos de Postgres están pensados para proyectos pequeños y para
agentes que crean y tiran entornos. OpoFuente, con el corpus real, no cabe; con un corpus de
demostración, sí. Además, tres de ellos (Supabase, Aiven, Render) tienen cláusulas de pausa, apagado o
caducidad que chocan con «una app que quiero abrir en tres semanas y que responda».

### 3.3 Hosting para la API Python (proceso siempre encendido, con disco)

| Proveedor | Plan gratuito [V] | Letra pequeña | ¿Sirve para OpoFuente tal cual? | URL |
|---|---|---|---|---|
| **Oracle Cloud Always Free** | **2 VM AMD `VM.Standard.E2.1.Micro`** (1/8 OCPU, 1 GB RAM cada una) **+ 2 OCPU / 12 GB** repartibles en `VM.Standard.A1.Flex` (1.500 OCPU-h y 9.000 GB-h/mes), **200 GB** de bloque, 20 GB de Object Storage (50.000 peticiones/mes), 10 TB/mes de salida, 1 balanceador flexible de 10 Mbps, 2 VCN | **Reclamación por inactividad**: si en 7 días el percentil 95 de CPU < 20 %, red < 20 % y (en A1) memoria < 20 %, Oracle **puede recuperar** la instancia; puede aparecer «out of host capacity» al crearla; las cuentas gratuitas no pueden enviar correo por el puerto 25 | **Sí, con matices**: sobra RAM para extraer PDFs y sobra disco; el riesgo es la reclamación y que la capacidad A1 no esté disponible en la región | [docs.oracle.com — Always Free Resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) |
| **Render (web service free)** | **0,1 CPU / 512 MB RAM**, 750 horas-instancia/mes por workspace, dominio propio y TLS gestionado | **Se duerme a los 15 min sin tráfico** (~1 min en despertar); **sistema de ficheros efímero** (se pierde en cada despliegue, reinicio o siesta); puede reiniciarse cuando quiera; sin discos persistentes, sin SSH, sin escalado, sin recibir tráfico de red privada; SMTP bloqueado; puede suspenderse por tráfico saliente alto | **No sin cambios**: 512 MB no aguanta los límites actuales de extracción (`max_file_bytes` 512 MiB, `config.py:132`) y el disco efímero se lleva artefactos y SQLite | [render.com/docs/free](https://render.com/docs/free) |
| **Railway (plan Free)** | **1 $/mes de crédito de uso**, máximo **1 vCPU / 0,5 GB** por servicio, **1 proyecto, 3 servicios, 1 miembro**, **0 dominios propios**, volumen máximo **500 MB**, logs 3 días | Es un plan real en 2026 (existe además un *Free Trial* de 5 $/30 días); sin dominio propio no hay TLS con nombre propio; 500 MB de volumen no caben el corpus | **No tal cual**; útil para prototipos | [railway.com/pricing.md](https://railway.com/pricing.md) |
| **Fly.io** | **No hay plan gratuito**: *Free Trial* de **1 $** de crédito, **7 días**, máquinas de prueba que se paran a los 5 min, hasta 10 máquinas, volúmenes ≤ 20 GB; al agotarse el crédito las máquinas quedan paradas hasta añadir tarjeta | Sin tarjeta no hay continuidad; extensiones (Tigris, etc.) no disponibles en prueba | **No** | [docs.fly.io/about/free-trial.md](https://docs.fly.io/about/free-trial.md) |
| **Koyeb** | **Sin plan de cómputo gratuito**: Pro 29 $/mes + uso, Scale 299 $/mes, Enterprise | En la página de precios no aparece plan Free de cómputo; solo la instancia «Free 5h» de Postgres. Además, Koyeb anunció su incorporación a Mistral AI | **No** | [koyeb.com/pricing](https://www.koyeb.com/pricing) |
| **PythonAnywhere** | **[NV]** — no verificado en esta consulta; su plan gratuito se ha caracterizado históricamente por no ofrecer Postgres y por restringir el dominio propio y las llamadas salientes | — | Probablemente **no** para este caso | (sin cita verificada) |
| **VPS de pago (referencia de salida)** | — | **[NV]**: no cito precios de 2026 sin verificarlos. Es la salida si Oracle no da capacidad: una VM de 2 GB / 40 GB debería costar del orden de 4-6 €/mes **[A]** | Sí | — |

**Lectura honesta:** de todos los gratuitos, **solo Oracle Always Free** ofrece una máquina que puede
correr el producto tal cual (con RAM y disco para extraer PDFs y guardar artefactos). Los PaaS
gratuitos están dimensionados para funciones pequeñas y sin estado; OpoFuente es lo contrario: estado
en disco, ficheros grandes y trabajos largos.

### 3.4 Web estática (`dist/` de Vite)

| Opción | Plan gratuito [V] | Letra pequeña | Veredicto para OpoFuente | URL |
|---|---|---|---|---|
| **Cloudflare Pages** | **500 builds/mes**, 1 build concurrente, **100 dominios propios por proyecto**, **20.000 ficheros** por sitio, **25 MiB por fichero**, 100 proyectos/cuenta, 20 min por build | Ancho de banda y peticiones: **no figura en la página de límites**; **[NV]** el «ancho de banda ilimitado» que anuncia Cloudflare en su página de precios (no verificada aquí). La integración con Git puede ser con repo privado o subida directa; CSP y cabeceras van en un fichero `_headers` (hoy **no existe** en el repo) | **Sí**, la mejor opción | [developers.cloudflare.com/pages/platform/limits](https://developers.cloudflare.com/pages/platform/limits/) (actualizada 05/09/2026) |
| **GitHub Pages** | 1 GB de sitio, **100 GB/mes de ancho de banda (límite blando)**, 10 builds/hora (blando), 1 GB recomendado para el repo fuente; **con GitHub Free solo funciona en repositorios públicos** (privados exigen GitHub Pro/Team/Enterprise) | Su política prohíbe usarlo como hosting comercial o para transacciones sensibles | **No mientras DEBT-003 esté abierta**: hospedar el sitio desde un repo público publicaría también los fixtures con el temario de GC. Además no es hosting pensado para una app privada. Como hosting **estático** es técnicamente una opción; el problema es la condición de repo público | [docs.github.com — GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) |
| **Render static site** | Gratis; consume ancho de banda y minutos de build compartidos del workspace | Sin cifras propias de ancho de banda en la página de Free: **[NV]** el importe incluido | Correcto como alternativa; ya se usa Render para la API si se elige esa vía | [render.com/docs/free](https://render.com/docs/free) |
| **Vercel / Netlify** | **[NV]** — no verificados en esta consulta. No cito cuotas de ancho de banda, builds ni condición de uso comercial | — | Alternativas razonables; verificar antes de elegir | (sin cita verificada) |

**Nota sobre GitHub Actions (regla de David):** el repo **tiene** un flujo de CI que ejecuta las
puertas en GitHub Actions (`…/.github/workflows/ci.yml`). La instrucción actual del equipo es **no usar
GitHub Actions para tests**; eso abre dos frentes que no me corresponde resolver: (a) si ese `ci.yml`
se queda, se pausa o se migra; (b) si se acepta «Actions como cron de copias». Mi recomendación es
**no depender de Actions en el camino crítico**: ni tests ni copias. GitHub Pages se menciona solo
como *hosting estático* —que es otra cosa—, y aun así queda descartado por el repo público (§arriba).

### 3.5 Almacén de objetos S3-compatible (artefactos y copias)

| Opción | Plan gratuito [V] | Letra pequeña | Encaje | URL |
|---|---|---|---|---|
| **Cloudflare R2** | **10 GB-mes de almacenamiento**, **1 millón** de operaciones clase A/mes, **10 millones** de clase B/mes, **egress gratuito**, 100.000 buckets incluidos | Buckets y objetos de clase Infrequent Access **no** tienen free tier y tienen mínimo de 30 días; el redondeo de facturación es por unidad; los fallos de autenticación no se cobran | **Sí**: artefactos pequeños + copias; 10 GB no cubren el corpus completo (63 GB de material, aunque al almacén solo entra lo importado) | [developers.cloudflare.com/r2/pricing](https://developers.cloudflare.com/r2/pricing/) (actualizada 30/10/2026) |
| **Neon Object Storage** | **5 GB/proyecto**, S3-compatible, y «ramifica» con el proyecto | Va atado al proyecto de Neon; el free tier de R2 es mayor y no obliga a usar Neon | Alternativa si ya se usa Neon | [neon.com/blog/neon-free-plan-1-gb-per-project](https://neon.com/blog/neon-free-plan-1-gb-per-project) (02/10/2026) |
| **Supabase Storage** | **1 GB**, egress cacheado 5 GB, subida máxima 50 MB | 1 GB es poco y la pausa por inactividad del proyecto afecta también al storage | Solo para demos mínimas | [supabase.com/pricing.md](https://supabase.com/pricing.md) |
| **Backblaze B2** | **[NV]** — la página de precios estaba en mantenimiento el 09/11/2026; no reproduzco sus 10 GB ni su límite de descarga diaria porque no los he podido leer | — | Candidato a verificar | [backblaze.com/cloud-storage/pricing](https://www.backblaze.com/cloud-storage/pricing) (mantenimiento) |
| **MinIO en la VM** | 0 € (disco de la VM), S3-compatible | Lo operas tú; un solo nodo no da durabilidad real; no tiene sentido si los artefactos ya están en el disco de esa misma VM | Útil solo para probar el adaptador S3 antes de contratar nada | — |
| **Disco de la VM (sin S3)** | 0 €, 200 GB Always Free | Se pierde si se pierde la VM; hay que copiarlo fuera sí o sí | **Lo recomendable en fase 1** | [docs.oracle.com — Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm) |

### 3.6 Worker y tareas programadas

| Opción | Coste [V] | Nota |
|---|---|---|
| **Segundo proceso en la misma VM (systemd)** | 0 € | Es lo natural: los *handlers* son los mismos (`main.py:321-338`) y el lease de la cola ya tolera varios procesos (`job_repository.py:101-149`). |
| **`systemd timer` / `cron` en la VM** para copias y mantenimiento | 0 € | Sin dependencias externas; el fallo se ve en `journalctl` y en el estado del backup. |
| **Cloudflare Workers Cron Triggers** | **[NV]** límites del plan gratuito de Workers no verificados en esta consulta | Solo tendría sentido para tareas sin estado; las copias necesitan tocar disco/DB. |
| **GitHub Actions como cron** | **[NV]** minutos gratuitos según plan y repo (privado/ público) | **No recomendado** por la regla de David sobre Actions y porque un cron de copias en un tercero que ya no tiene acceso al disco no aporta. |
| **Cola externa (Redis/Celery, Upstash, etc.)** | — | **No hace falta**: `02_ARCHITECTURE §6` y la implementación ya resuelven la cola en la propia base. Añadir Redis es una dependencia nueva y exigiría ADR (`AGENTS.md`: dependencia nueva requiere ADR aceptada). |

### 3.7 TLS, dominio y forma de exponerlo

| Pieza | Opción | Coste | Nota |
|---|---|---|---|
| **Túnel** | **Cloudflare Tunnel (`cloudflared`)**: conexión **solo saliente**, sin IP pública ni puertos abiertos; el tráfico entra por la red de Cloudflare | Plan gratuito de Cloudflare Tunnel: **[NV]** el detalle de asientos del plan Zero Trust Free no se pudo leer (la página de precios devolvió 404 y la de documentación se sirvió sin el cuerpo útil). El **funcionamiento** sí está verificado | [developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/) (actualizada 04/08/2026) |
| **TLS** | **Caddy** con Let's Encrypt en la misma VM | 0 € | Requiere abrir 80/443 o usar DNS-01 |
| **Dominio** | Subdominio gratuito (DuckDNS, `sslip.io`) o un dominio propio | 0 € / ~10 €/año **[NV]** | El nombre definitivo está sin decidir (Q001 en `13_DECISIONS`) |
| **Acceso privado sin exponer** | **WireGuard** autoalojado, o **Tailscale** (plan personal) | 0 € | Es la opción que mejor respeta DEBT-003 y la regla de loopback: no hay URL pública. Plan gratuito de Tailscale: **[NV]** |

### 3.8 Tabla resumen de coste 0 € (fase 1 y fase 2)

| Pieza | Fase 1 (mono-usuario) | Fase 2 (multiusuario) | Coste | Cuándo deja de ser gratis |
|---|---|---|---|---|
| Cómputo API + worker | Oracle Always Free A1 (2 OCPU/12 GB) **[V]** | Igual o mayor | 0 € | Si Oracle reclama la instancia por inactividad o no hay capacidad → VPS de pago **[NV]** |
| Base de datos | SQLite en el disco de la VM **[V]** | Postgres **autoalojado** en la VM (cabe 2,6 GB) **[V]** o Neon Launch si se quiere gestionado | 0 € | Neon/otros gestionados gratuitos **no caben** (1 GB) → pago por GB **[V]** |
| Web estática | Cloudflare Pages **[V]** | Igual | 0 € | > 500 builds/mes o > 20.000 ficheros (improbable) |
| Artefactos | Disco de la VM (200 GB) **[V]** | R2 (10 GB) **[V]** o disco | 0 € | R2 > 10 GB (0,015 $/GB-mes) **[V]** |
| Copias | Disco local + copia a R2 | R2 | 0 € | > 10 GB en R2 |
| TLS | Let's Encrypt | Igual | 0 € | — |
| Entrada | Cloudflare Tunnel o WireGuard | Igual | 0 € | **[NV]** el límite del plan Free de Zero Trust |
| Dominio | Subdominio gratuito | Dominio propio | 0 € | ~10 €/año **[NV]** |
| **Total** | **0 €/mes** | **0 €/mes** hasta ~10 GB de objetos | | |

**El «0 €» tiene un coste que no es dinero:** operación. Parchear la VM, vigilar discos, probar
restauraciones, rotar copias. Ese coste es de horas, y es el que hace que un PaaS de 7 $/mes sea a veces
más barato que un gratuito.

---

## 4. Huecos concretos del código para pasar de local a servible

Ordenados por lo que **bloquea** primero. Cada uno con su sitio.

### 4.1 SQLite → Postgres: el hueco grande

No es «cambiar la URL de SQLAlchemy». Es un proyecto de datos con cinco frentes:

| # | Hueco | Dónde | Por qué duele |
|---|---|---|---|
| 1 | **Búsqueda en FTS5**: tabla virtual externa `evidence_fts`, disparadores `AFTER INSERT/UPDATE/DELETE` y `bm25()` | `apps/api/alembic/versions/0018_search_and_rag.py:48-77`; consulta completa en `apps/api/opofuente/infrastructure/search_repository.py:79-137` (`bm25(evidence_fts)`, `MATCH`), reconstrucción con `INSERT INTO evidence_fts(evidence_fts) VALUES('rebuild')` en `:182`, recuento en `:201` | En Postgres no existe FTS5 ni `bm25()` ni `MATCH` con esa sintaxis. Hay que reescribir el índice (`tsvector` + GIN), la consulta (`websearch_to_tsquery`/`ts_rank_cd`), los disparadores y **todos** los tests que hoy comprueban FTS5 (`tests/integration/test_migrations_0018.py:103-147`, `tests/unit/test_search_index_health.py:3`, `tests/integration/test_health.py:120-122`). Es 1-2 slices solo para búsqueda |
| 2 | **Sondas y capacidades atadas a SQLite** | `apps/api/opofuente/infrastructure/probes.py:45-64` (`PRAGMA foreign_keys`, `PRAGMA journal_mode='wal'`), `apps/api/opofuente/infrastructure/capabilities.py:229-281` (`CREATE VIRTUAL TABLE temp.fts5_probe`, `sqlite_master`) | En Postgres `/health/ready` diría «journal_mode ≠ wal → FAILED» y `/api/v1/capabilities` declararía la búsqueda no disponible. Son mentiras del propio producto: hay que partir las sondas por motor |
| 3 | **Índices parciales solo declarados para SQLite** | `apps/api/opofuente/infrastructure/db_models.py:168`, `:211`, `:217`, `:1358`, `:1462` (`sqlite_where=…`), y en migraciones `0006:121`, `0014:218`, `:308` | En Postgres esos índices se crean **completos** (o no se crean), con lo que la unicidad parcial deja de cumplirse: dos claves «activas» o dos opciones «sin clave estable» podrían colarse. Además `autogenerate` no los ve |
| 4 | **Defaults de Booleano con `text("0")`** | `db_models.py:62`, `:765`, `:940`, `:986`, `:989`, `:1293`, `:1606`, `:1762`, `:2016` (patrón `server_default=text("0")`) | Postgres rechaza `DEFAULT 0` en una columna `boolean`. Hay que pasar a `text("false")` o `sa.false()` **en las migraciones también** |
| 5 | **Migraciones con `batch_alter_table` y `render_as_batch`** | `apps/api/alembic/env.py:41`, `:55`; `0006:125-132`, `0007:50-105`, `0008:59-64`, `0011:47-95`, `0013:273-281`, `0015:62-114`, `0017:32-38`, `0021:443-523`, `0023:34-50`; `sqlite_where` en `0006:121`, `0014:218`, `:308` | `batch_alter_table` reconstruye la tabla: está pensado para SQLite y en Postgres es un rodeo caro. Hay que decidir si se mantienen dos caminos o se reescriben las migraciones antes de crear la base nueva (una base nueva permite «migración inicial limpia», pero **rompe la trazabilidad** de 23 migraciones y la prueba de migración desde cero) |
| 6 | **Código que habla `sqlite3` directamente** | `apps/api/opofuente/infrastructure/backup_archive.py:76-86` (instantánea con `sqlite3.connect(...).backup(...)`), y `apps/api/opofuente/infrastructure/extractors/anki.py:251-283` (lee el `.apkg` con `sqlite3`; este **no** cambia: el fichero es SQLite por definición del formato) | Las copias hay que rehacerlas con `pg_dump`/`pg_basebackup`; el flujo de restauración actual **intercambia ficheros** (`docs/OPERACION.md:62-78`) y eso no existe en un Postgres gestionado |
| 7 | **SQL crudo con sintaxis propia** | `housekeeping_repository.py:73-98` (`NOT EXISTS` con nombres de tabla, portable), `search_repository.py:182` (`INSERT INTO evidence_fts … 'rebuild'`), `migrations.py:44` (`alembic_version`), `probes.py:38-46` | El `NOT EXISTS` es portable; el `rebuild` y los `PRAGMA` no. Hay que revisar cada `text(...)` del repo (hay ~10) |
| 8 | **Fechas ingenuas asumidas** | `db.py:25-35` (`as_utc` justifica que SQLite devuelve `DateTime(timezone=True)` sin zona) | Con Postgres llegan con zona: `as_utc` lo tolera, pero cualquier comparación nueva debe pasar por él. Riesgo de bugs silenciosos de horas |
| 9 | **Migraciones atadas a una ruta** | `apps/api/opofuente/infrastructure/migrations.py:21-25` (la URL se construye con `sqlite_url(settings.data_paths.database)`) | Hay que aceptar `OPOFUENTE_DATABASE_URL` (o equivalente) y **no** derivarla del directorio de datos |

**Coste estimado [A]:** 6-10 slices: búsqueda (1-2), índices parciales y defaults (1), migraciones y
sembrado (1-2), copias/restauración (1-2), sondas/capacidades (1), pruebas y migración desde cero (1-2).

### 4.2 La guardia de loopback (y cómo publicar sin tocarla)

- Hoy: `apps/api/opofuente/config.py:197-208` rechaza cualquier host que no sea loopback, con un mensaje
  que remite a `09_SECURITY §2`. El arranque por consola pasa `settings.host` a Uvicorn
  (`main.py:433-444`).
- **No propongo quitarla.** Con el proxy en la misma máquina (§2.2) la app sigue en `127.0.0.1` y la
  guardia se mantiene. Esto es una ventaja, no un rodeo: el producto no cambia de modelo de seguridad.
- Lo que **sí** hay que cambiar para servir fuera: `OPOFUENTE_CORS_ORIGINS` (hoy solo loopback,
  `config.py:31-36`) y el `Origin` de escrituras (`middleware.py:61-84`). Eso es configuración, no
  código nuevo.
- Si algún día se quiere escuchar en `0.0.0.0` (p. ej. detrás de un balanceador de red), es **cambio de
  seguridad de Nivel 3**: ADR previa, con modelo de amenaza y autenticación. `AGENTS.md` obliga a
  detenerse y proponer ADR; no lo decide un agente.

### 4.3 Sin autenticación, sin sesiones, sin multiusuario

- No hay tabla de usuarios: el modelo lo dice explícitamente en `db_models.py:389` («la aplicación es de
  un solo usuario, así que no hay `user_id`»). La sesión de estudio, los intentos, los errores y las
  marcas de estudio no tienen dueño.
- `owner_scope` (`db_models.py:1012-1021`) **no** es tenencia: es ámbito de derechos del documento
  (`public` / `private_user` / `generated`).
- El `Origin` check es la única defensa CSRF y solo sirve sin login (`middleware.py:1-10`).
- **Consecuencia:** dar acceso a un tercero hoy = dar acceso a *todo* (material, progreso, claves de
  respuesta, ajustes, copias, diagnóstico). Para fase 1 solo es aceptable si el acceso es de red
  (VPN) o está autenticado **fuera** de la app (Cloudflare Access / Caddy basic auth) y el usuario es
  de confianza. Para fase 2 hace falta: cuentas, sesiones, propiedad en cada tabla de progreso,
  autorización por recurso y pruebas de aislamiento.
- Multiusuario trae RGPD (§5.4): datos de alumnos (progreso, errores) son datos personales.

### 4.4 CORS, CSP y `VITE_API_BASE_URL` en el build

- `apps/web/index.html:31-32`: el CSP fija `connect-src 'self' http://127.0.0.1:8765 http://localhost:8765
  ws://127.0.0.1:5173 ws://localhost:5173`. **Un bundle desplegado no podrá llamar a
  `https://api.dominio`**: el navegador bloqueará la petición. Es el bloqueo más tonto y el más seguro
  de encontrar en una demo.
- `apps/web/src/api/client.ts:3`, `:38-41`: la URL base se resuelve con `import.meta.env.VITE_API_BASE_URL`
  y, si falta, cae a `http://127.0.0.1:8765`. **Se hornea en el build**: el mismo `dist/` no vale para
  dos entornos, y un build mal hecho apunta a la máquina del visitante (fallo confuso, no error claro).
- No hay rutas relativas: no se puede desplegar web y API en el mismo origen sin poner la URL absoluta
  en `VITE_API_BASE_URL`.
- El API manda sus cabeceras (`middleware.py:26-34`), pero el sitio estático necesita su propio fichero
  `_headers` (Pages) o configuración de Caddy; **no existe** en el repo.
- CORS del API: `allow_credentials=False` y métodos explícitos (`main.py:410-417`). Al añadir login por
  cookie habría que revisarlo (hoy no hay cookies, así que no hay nada que romper todavía).

### 4.5 Worker

- Hoy es una tarea `asyncio` del proceso de la API que arranca en el `lifespan` **solo si la base está
  migrada** (`main.py:340-362`). Cerrar la API deja el worker sin proceso.
- Buena noticia: la cola ya está diseñada para varios procesos — `claim_next` reclama con un `UPDATE`
  condicional y relee la fila para confirmar que el lease es suyo
  (`job_repository.py:101-149`), y el lease se renueva desde el handler (`job_worker.py:159-162`). Un
  **segundo proceso** con los mismos *handlers* es viable **sobre la misma base**.
- Lo que **no** está resuelto para separarlo:
  - `WorkerLiveness` es un objeto en memoria del proceso (`main.py:146`, pasado en `:321-338`), así que
    `/capabilities` seguiría diciendo «worker desactivado» si el worker corre en otro proceso: hace
    falta una señal compartida (latido en la base o en un fichero).
  - Con **SQLite y varias réplicas** el modelo se rompe (WAL sobre volúmenes de red, bloqueos). Con
    Postgres y un solo worker, va bien; con varios, hay que revisar el `claim_next` (en Postgres lo
    idiomático es `SELECT … FOR UPDATE SKIP LOCKED`).
  - El worker ejecuta los *handlers* en un hilo (`asyncio.to_thread`, `job_worker.py:132`): la memoria
    del proceso es la del worker, no la de la API. Eso significa que **el worker es quien necesita RAM**
    (PDFs, ZIPs, imágenes), y en un PaaS de 512 MB no cabe.

### 4.6 Rutas, Windows y `OPOFUENTE_DATA_DIR`

- `config.py:39-44` (`project_root`): sube tres niveles desde `config.py` y comprueba que existe
  `pyproject.toml`; si no, usa `cwd`. En un despliegue con `pip install`/wheel, `parents[3]` ya no es el
  repo y las rutas relativas dejan de resolverse como en desarrollo. En Docker con el código copiado
  funciona; con el paquete instalado, no está claro.
- `config.py:160-171`: `OPOFUENTE_DATA_DIR` relativa se resuelve contra la raíz del proyecto y se
  comprueba que no sea un fichero. En contenedor hay que montar un volumen y apuntar ahí.
- `filesystem_inventory.py:328-337`: código específico de Windows (puntos de reanálisis/junctions) con
  `# pragma: no cover`. En Linux devuelve `False`; **no rompe**, pero la cobertura de esa rama es cero
  en el servidor.
- `backup_archive.py:89-112`: rutas relativas en `posix` dentro del ZIP — bien para portabilidad.
- Escritura atómica con `os.replace` asume **mismo volumen** (`artifact_store.py:90`): en Docker, el
  temporal y el almacén deben estar en el mismo montaje, o el renombrado falla.
- Nada usa `fcntl`, `msvcrt` ni rutas absolutas `F:\` en producción (verificado por búsqueda); lo que hay
  es lo anterior. Riesgo bajo, pero hay que probarlo en Linux **antes** de desplegar (hoy las puertas
  corren en Windows, y el CI en `ubuntu-latest`).

### 4.7 Copias y restauración

- El diseño actual es **de aplicación local**: instantánea SQLite + ZIP con todo el árbol + intercambio
  de ficheros con `.restore-old` para deshacer (`docs/OPERACION.md:46-78`).
- En la nube: (a) con Postgres gestionado no hay fichero que intercambiar; (b) con almacén S3 no hay
  árbol que recorrer; (c) el ZIP completo de artefactos puede pesar decenas de GB. Hace falta:
  copia de base por herramienta del motor, copia incremental de objetos, verificación al restaurar
  (hoy se verifica hash por entrada: `backup_archive.py:115-174`), y un **ensayo de restauración**
  documentado en el runbook.
- `09_SECURITY §10` exige «prueba de restauración obligatoria antes de considerar datos personales
  seguros»: eso es parte del criterio de «usable de verdad» (§6.2).

### 4.8 Límites de subida y memoria

- Los topes por fichero son generosos por diseño: `max_file_bytes` 512 MiB, `max_url_bytes` 64 MiB,
  `max_paste_bytes` 4 MiB, ZIP hasta 1 GiB descomprimido (`config.py:132-158`, `.env.example:46-76`).
- En un PaaS de 512 MB (Render free) eso no es un límite que se pueda mantener: **el proceso moriría**.
  En la VM de Oracle (12 GB) cabe sin tocar configuración. Si se elige PaaS, hay que **bajar** los topes
  y decirlo (cambio de comportamiento del producto, no de infraestructura).
- No hay límite global de cuerpo de petición en el servidor: el proxy debe acotarlo (Caddy
  `request_body max_size`, Cloudflare tiene límites de subida **[NV]** según plan). Ojo: el repo no
  documenta ese límite en ningún sitio.

### 4.9 Secretos

- Hoy: `.env` local, `OPOFUENTE_LLM_API_KEY` como `SecretStr` (`config.py:111-122`), nunca devuelta ni
  registrada (`observability.py:22-38`), proveedor de IA **desactivado por defecto**.
- En despliegue: variables de entorno del proveedor (o `docker secrets`). **No** copiar `.env` al repo ni
  a la imagen; `.gitignore` ya lo cubre. Si se usa Cloudflare con un token de túnel o de R2, ese token
  vive en la máquina, con permisos mínimos, y no en el repo.
- La aplicación **no tiene** cifrado en reposo propio: los artefactos son ficheros. La confidencialidad
  la dan el disco del proveedor y el acceso. Si en fase 2 hay terceros, hay que decirlo y decidir
  (§5.4).

### 4.10 Observabilidad

- Logs JSON saneados a stderr **y** fichero rotativo de 2 MB × 5 (`observability.py:74-105`): en un
  contenedor, el fichero es efímero y el destino útil es stdout, que ya está. El rotativo sirve en la VM
  con volumen.
- `/health/live` y `/health/ready` existen y son honestos (503 con el detalle). Sirven como
  `healthCheckPath` de Render/Caddy: usar `/api/v1/health/ready`.
- **No hay** métricas Prometheus ni trazas ([A]: solo logs y el diagnóstico). Para una app de un usuario
  es correcto; para fase 2, `02_ARCHITECTURE §9` sigue diciendo «sin telemetría remota», lo que choca con
  cualquier APM externo: decisión de David.
- El diagnóstico (`/api/v1/diagnostics`) está pensado para pegar en una incidencia y es sanitizado; en un
  servidor, conviene restringirlo por red (VPN) porque expone versión y configuración.

### 4.11 Empaquetado: no hay nada de despliegue

- No hay `Dockerfile`, ni `docker-compose.yml`, ni `fly.toml`, ni `render.yaml`, ni `_headers`
  (verificado). `scripts/build.ps1` construye wheel y `dist/`; `scripts/release.ps1` empaqueta una
  **release local privada** y lo dice en su manifiesto.
- Todo el arranque está en PowerShell (`scripts/api.ps1`: migra y luego `uv run uvicorn … --host`). En el
  servidor no habrá PowerShell.
- Hace falta como mínimo: imagen (o `compose`) con Python 3.12, entrypoint que migre **una vez** y luego
  arranque, healthcheck, volumen de datos, y un servicio de worker **separado** con el mismo código.

---

## 5. Derechos y decisiones: qué se puede hacer y qué requiere a David

### 5.1 DEBT-003 — temario de la Guardia Civil (bloquea la fase 1 con terceros)

- Situación: las condiciones del portal de la GC limitan sus contenidos a descarga y uso privado; el
  temario de los 25 temas está versionado en `fixtures/profiles/gc-cabos-guardias-2026.curriculum.json`
  (`docs/DEBT.md:158-180`).
- Obligación registrada: antes de publicar el repositorio, distribuirlo, alojarlo accesible a terceros
  **o dar acceso a cualquier tercero**, hay que retirar el temario de los fixtures y cargarlo desde la
  copia privada (importación manual del PDF) o tener autorización expresa de la Dirección General
  (`sugerencias-intranet@guardiacivil.org`).
- **«Demo privada con un amigo» es dar acceso a un tercero.** Por tanto la fase 1, si hay alguien más
  que David, exige cerrar DEBT-003 **antes**, no después.
- Cierre posible sin autorización: sustituir el fixture por importación manual. Tiene coste: hoy el
  arranque siembra perfiles desde fuentes verificadas por hash (ADR-006); quitarlo cambia el arranque y
  las pruebas de siembra.
- Cierre con autorización: es una gestión externa, sin plazo garantizado.

### 5.2 Licencia del repositorio y de las dependencias

- **La licencia del repo está sin decidir** (`README.md:131-134`; `13_DECISIONS` §Q001 y «requieren
  decisión futura»). Sin licencia, «publicar» no significa nada jurídicamente.
- Dependencia con consecuencia: **PyMuPDF es AGPL-3.0** y el propio `pyproject.toml:14-16` lo advierte:
  «uso local y privado cubierto por DEBT-003; **distribuir la aplicación obligaría a revisar la
  licencia**». Distribuir la app (no el repo: la app) obliga a resolver esto.
- Otras: `zstandard` BSD-3 (compatible, `pyproject.toml:22-25`); FastAPI/SQLAlchemy/Alembic con licencias
  permisivas **[A]**, sin revisión formal aquí.
- Consecuencia práctica: **fase 1 sin distribución** (solo servicio para David, eventualmente un tercero
  invitado) no dispara el problema AGPL; **fase 2 con cuentas de pago o distribución sí**.

### 5.3 Material de terceros y material del usuario

- El corpus que importe David (PDFs de academia, temarios de terceros) tiene sus propias condiciones.
  `09_SECURITY §8` ya prohíbe compartir material privado y obliga a conservar atribución/licencia.
- Un despliegue multiusuario **no puede** mezclar el material privado de David con cuentas de otros:
  la propia clasificación (`owner_scope='private_user'`) tendría que convertirse en frontera real de
  datos, no en una etiqueta.
- Antes de SaaS, `09_SECURITY §8` exige revisión jurídica profesional.

### 5.4 Datos personales (RGPD básico) si hay multiusuario

Si la fase 2 da cuentas a otras personas, la app trata datos personales (identidad, progreso, errores,
notas). Mínimos que habría que resolver, sin pretender sustituir a un abogado:

1. **Base jurídica y finalidad** documentadas; información al usuario.
2. **Minimización**: hoy los logs están saneados (bien), pero no hay política de retención de intentos,
   errores ni diagnósticos.
3. **Derecho de acceso y supresión**: el producto **no borra** (archiva y excluye, `docs/OPERACION.md:110-124`);
   un derecho de supresión necesita diseño (y hoy choca con «no implementar `rm -rf` sobre rutas
   construidas», `09_SECURITY §9`).
4. **Encargados de tratamiento**: elegir Cloudflare/Oracle/Neon implica terceros y transferencias;
   hay que mirar sus condiciones **[NV]** para este uso.
5. **Seguridad del tratamiento**: autenticación real, aislamiento por usuario y copias probadas.
6. **Registro de actividades** y, si aplica, evaluación de impacto (poco probable para este tamaño).

Nada de esto es un obstáculo para la fase 1 con un solo usuario y acceso privado; todo lo es para la
fase 2.

### 5.5 La regla de loopback es seguridad de Nivel 3

- `config.py:197-208` y `09_SECURITY §2` la definen como frontera. `AGENTS.md` («Bloqueo») obliga a
  detenerse si hay que bajar seguridad o tocar fuera del alcance.
- **No proposición de este documento:** abrir el host al público cambiando esa guardia. La alternativa
  de §4.2 (proxy en la misma máquina) permite servir la app sin modificar la frontera.
- Si algún día se decide lo contrario, es **ADR nueva** con modelo de amenaza, autenticación, y el
  visto bueno explícito de David. Un agente no puede hacerlo.

### 5.6 Las tres (más una) decisiones que hacen falta

| # | Decisión | Opciones | Qué desbloquea | ADR propuesta |
|---|---|---|---|---|
| **D1** | **DEBT-003 y licencia**: ¿el producto sigue siendo privado de un solo usuario, o se retira el temario de GC y se decide licencia para poder invitar a terceros? | (a) privado + VPN, sin terceros; (b) retirar fixture GC e importación manual + decidir licencia; (c) pedir autorización a la DGGC | Cualquier acceso de terceros. Sin D1, la fase 1 es «David desde otro equipo», no una demo | `ADR-019-alcance-de-publicacion-y-licencia` |
| **D2** | **Forma de exposición**: ¿VPN privada (WireGuard/Tailscale) o URL pública con autenticación de borde (Cloudflare Access/Caddy)? ¿Se acepta que un tercero (Cloudflare) vea metadatos y tráfico del material de estudio? | (a) VPN, 0 terceros en el camino; (b) Cloudflare Tunnel + Access, más cómodo; (c) VPS con 443 y Caddy, control total, más operación | La §3.7 y la configuración de CORS/CSP | `ADR-020-forma-de-exposicion-y-autenticacion-de-borde` |
| **D3** | **Postgres ahora o después**: ¿se acepta que la fase 1 mantenga SQLite en el disco de la VM (0 slices de datos) o se invierten 6-10 slices en Postgres/S3 antes de invitar a nadie? | (a) SQLite en volumen (recomendado en fase 1); (b) Postgres autoalojado en la VM desde el principio; (c) Postgres gestionado (no cabe con 2,6 GB gratis) | El orden de §6 y el calendario | `ADR-021-motor-de-datos-y-almacen` |
| D4 (menor) | **Operación de copias**: ¿dónde vive la copia fuera de la máquina (R2, disco externo, otra VM) y quién la prueba? | — | Criterio de «usable de verdad» (§6.2) | puede ir dentro de ADR-021 |

---

## 6. Camino por fases

### 6.1 Fase 0 — seguir como está (hoy hasta D1/D2/D3)

**Qué es:** la app local en el equipo de David, loopback, un usuario, release local privada
(`docs/OPERACION.md`). Sigue siendo lo correcto mientras no haya decisión.

**Coste:** 0 € · **Trabajo:** 0 slices (lo que ya existe).

**Criterio de salida:** existe un ADR aceptado para D1 y D2 y un runbook de despliegue escrito.
Sin eso, pasar a fase 1 es improvisar.

### 6.2 Fase 1 — demo privada mono-usuario, servida por HTTPS (recomendada)

**Qué es:** la misma app, en una máquina, con el worker en un proceso aparte, acceso privado, copias
programadas y un `dist/` servido por CDN. **Sin Postgres ni S3.** Sin cambios de modelo de datos.

**Trabajo [A] (3 slices):**

| Slice | Contenido | Por qué |
|---|---|---|
| **S-DEPLOY-01** | `Dockerfile` + `docker-compose.yml` (API y worker, mismo código, proceso distinto), entrypoint que migra y arranca, volumen de datos, `healthcheck` a `/api/v1/health/ready` | Hoy no hay nada de eso y el arranque es PowerShell |
| **S-DEPLOY-02** | Configuración de despliegue: `OPOFUENTE_CORS_ORIGINS`, CSP del frontend parametrizada (o cabecera `_headers`), `VITE_API_BASE_URL` documentada y **comprobada en build**, `OPOFUENTE_DATA_DIR` al volumen, topes de subida coherentes con la RAM, `worker_enabled=false` en la API y worker aparte con liveness compartida | `index.html:28` y `client.ts:38-41` rompen cualquier despliegue tal cual; la liveness del worker es falsa si corre fuera |
| **S-DEPLOY-03** | Operación: timer de copias + copia fuera de la máquina, verificación, ensayo de restauración documentado, runbook de arranque/parada/migración, y `docs/OPERACION.md` con la sección de servidor | `09_SECURITY §10` exige prueba de restauración |

**Infraestructura concreta (0 €):** Oracle Always Free A1 (2 OCPU/12 GB, 200 GB de bloque) **[V]** +
Docker Compose + Caddy o `cloudflared` + SQLite en el disco + Cloudflare Pages para `dist/` **[V]** +
subdominio gratuito. Copias a R2 (10 GB) **[V]** o a un disco externo.

**Riesgos de esta fase, dichos:** reclamación de la instancia por inactividad **[V]**; capacidad A1 no
disponible al crear **[V]**; una sola máquina = un solo punto de fallo; Cloudflare en el camino si se
elige túnel (D2).

**Criterio observable de «usable de verdad» para la fase 1** (esto es lo que hay que poder demostrar,
no «funciona»):

1. Desde **otro equipo**, por la URL/VPN, se importan **20 PDFs reales de hasta 50 MB** en un lote: la
   UI muestra progreso, los trabajos terminan y el texto extraído se puede leer.
2. Se lanza una **sesión de 20 preguntas**, se corrige al terminar y la puntuación coincide con la
   calculada en local con el mismo material.
3. La búsqueda devuelve citas **de los documentos recién importados** (es decir, el índice léxico está
   sano tras la importación).
4. Se crea una **copia**, se saca de la máquina, se **verifica** y se **restaura** en una máquina
   distinta; el resultado se ve en la UI.
5. Se **reinicia el servidor**: la app vuelve sola, `/api/v1/health/ready` = 200 en < 60 s, y un trabajo
   interrumpido se recupera (lease vencido → cola).
6. **No hay ningún puerto público** salvo el del túnel/443, la app sigue en `127.0.0.1` y un escaneo
   desde fuera no encuentra nada más.
7. En 200 líneas de log **no aparece** texto de documentos, rutas absolutas ni claves.
8. Un acceso sin credenciales (si D2 = pública) devuelve 401/403; si D2 = VPN, sin VPN no hay respuesta.

**Coste:** 0 €/mes, ~1-2 semanas de trabajo del agente + una tarde de altas.

### 6.3 Fase 2 — multiusuario real

**Qué es:** cuentas, datos por usuario, Postgres, almacén de objetos, worker y copias con garantías,
y las decisiones legales cerradas. Aquí sí entra el «objetivo mínimo» de §2.1 con Postgres y S3.

**Trabajo [A] (orden sugerido):**

| Bloque | Slices [A] | Depende de |
|---|---|---|
| Autenticación + cuentas + propiedad en datos de progreso | 2-3 | D1, D2 |
| Postgres (búsqueda incluida, §4.1) | 5-8 | D3 |
| Almacén S3 para artefactos y representaciones (adaptador + rangos + URLs firmadas) | 2-3 | Postgres o al menos base con migración |
| Worker separado con liveness y escalado de lease | 1 | S-DEPLOY-01 |
| Copias por motor + restauración de base gestionada + ensayo periódico | 1-2 | Postgres |
| RGPD: información, retención, supresión, registro | 1 + revisión externa | D1 |

**Coste:** 0 € hasta ~10 GB de objetos y mientras el Postgres autoalojado quepa en la VM; si se quiere
Postgres gestionado, **deja de ser gratis** porque el corpus no cabe en 1 GB **[V]** (Neon Launch cobra
por CU-hora y GB-mes **[V]**; el importe depende del uso, no lo estimo sin medirlo).

**Criterio observable para la fase 2:** dos cuentas distintas no ven **ni un** documento, pregunta,
intento ni copia de la otra (prueba de aislamiento); una cuenta puede borrar/exportar sus datos; el
sistema aguanta un reinicio con trabajos en cola; las copias se prueban cada mes.

### 6.4 Recomendación y orden

1. **Cerrar D1 y D2 por escrito** (ADR) antes de tocar infraestructura. Sin D1 no hay terceros; sin D2 no
   se sabe si hay URL pública.
2. **Fase 1 en una VM, con SQLite, worker aparte, copias probadas y `dist/` en Pages.** No tocar la capa
   de datos. Es lo que más rápido demuestra «usable de verdad» con 0 €.
3. **No migrar a Postgres hasta que haya una razón**: la razón será multiusuario, concurrencia de
   escritura o una base gestionada; no «porque suena a producción».
4. **Antes de invitar a un tercero**, cerrar DEBT-003 y la licencia.
5. **Ensayo de restauración mensual** desde el primer día: es el único criterio de esta lista que, si
   falta, convierte todo lo demás en frágil.

---

## 7. Qué falta para que se pueda usar de verdad (lista priorizada)

No es una lista de deseos: cada punto dice **qué**, **cuánto** [A] y **qué bloquea**.

### 7.1 Producto

| # | Falta | Coste [A] | Bloquea |
|---|---|---|---|
| P1 | Autenticación de borde (VPN o Access) para fase 1; **cuentas** de verdad para fase 2 | 0 (borde) / 2-3 slices (app) | Cualquier tercero |
| P2 | Propiedad por usuario en progreso, intentos, errores, notas y copias | 1-2 slices (con P1) | Multiusuario |
| P3 | Pantalla y flujo de «mi cuenta / mis datos / exportar / borrar» | 1 slice | RGPD, confianza del usuario |
| P4 | Bajar los topes de subida **si** se elige PaaS pequeño (hoy 512 MiB por fichero) | configuración + decisión | Que la app no muera por memoria |
| P5 | Capacidades honestas en Postgres (hoy dirían que la búsqueda no existe, §4.1) | incluido en Postgres | Que la UI no mienta |

### 7.2 Infraestructura y datos

| # | Falta | Coste [A] | Bloquea |
|---|---|---|---|
| I1 | `Dockerfile` + compose (API y worker) y entrypoint con migración | 1 slice (S-DEPLOY-01) | Salir de Windows |
| I2 | Worker como proceso propio con liveness compartida | 0,5 slice | Que `/capabilities` diga la verdad |
| I3 | Postgres (motor, búsqueda, índices parciales, defaults, migraciones, copias) | 5-8 slices | Fase 2 y cualquier PaaS con disco efímero |
| I4 | Almacén S3 para artefactos/representaciones | 2-3 slices | Más de una réplica o disco efímero |
| I5 | Volumen persistente bien montado y `os.replace` en el mismo volumen | 0 (configuración) | Pérdida de datos |

### 7.3 Operación

| # | Falta | Coste [A] | Bloquea |
|---|---|---|---|
| O1 | Copias programadas **fuera** de la máquina + verificación + retención | 1 slice (S-DEPLOY-03) | Cualquier pérdida evitable |
| O2 | Ensayo de restauración documentado y ejecutado (no solo el botón) | 0,5 slice + 1 h/mes | `09_SECURITY §10` |
| O3 | Migraciones en el despliegue: migrar antes de arrancar, con copia previa, y una sola instancia migrando | 0,5 slice | Bases rotas en producción |
| O4 | Healthchecks conectados al proveedor (`/api/v1/health/ready`) y alerta de caída | 0,5 slice | Saber que está roto antes de que lo diga David |
| O5 | Logs del servidor recolectados y rotados (stdout + fichero) sin contenido sensible | 0 (ya saneados) | Diagnóstico |
| O6 | Runbook: arrancar, parar, restaurar, rotar copias, actualizar versión, qué hacer si el disco se llena | 1 doc | Que no dependa de un agente |
| O7 | Revisar `ci.yml` y la regla «sin GitHub Actions para tests»: decidir qué se ejecuta y dónde | decisión de David | Puertas del repo |

### 7.4 Legal

| # | Falta | Coste | Bloquea |
|---|---|---|---|
| L1 | **DEBT-003** cerrada (retirar temario o autorización) | decisión + 1 slice si se retira | Terceros |
| L2 | Licencia del repo decidida | decisión | Publicar |
| L3 | Revisión de AGPL de PyMuPDF si se distribuye la app | decisión + posible cambio de extractor | Distribución |
| L4 | RGPD básico (información, retención, supresión, encargados) si hay cuentas | 1 slice + revisión | Fase 2 |
| L5 | Condiciones de los proveedores elegidos (Oracle, Cloudflare, Neon) para este uso | lectura + decisión | Fase 1/2 |

---

## 8. Anexo A — verificado vs asumido (resumen)

**Verificado el 09/11/2026 en la fuente del proveedor:** Neon (límites Free, storage 1 GB, CU-horas,
scale-to-zero, object storage 5 GB, auth 60k MAU); Supabase (500 MB, pausa tras 1 semana, 1 GB storage,
sin backups en Free, 50 MB por fichero); Aiven (1 GB disco, `max_connections=20`, apagado por
inactividad, sin SLA); Render (0,1 CPU/512 MB, siesta 15 min, 750 h/mes, FS efímero, Postgres Free 1 GB
que caduca a los 30 días, sin backups); Railway (1 $/mes de crédito, 1 vCPU/0,5 GB, sin dominio propio,
volumen 500 MB); Fly.io (sin plan gratuito: 1 $/7 días de prueba); Koyeb (sin plan Free de cómputo);
Oracle Always Free (2 AMD micro, A1 2 OCPU/12 GB, 200 GB de bloque, 20 GB de objetos, 10 TB de salida,
reclamación por inactividad, «out of host capacity»); Cloudflare R2 (10 GB, 1 M/10 M operaciones,
egress gratis); Cloudflare Pages (500 builds, 20.000 ficheros, 25 MiB por fichero, 100 dominios);
GitHub Pages (solo repo público en Free, 1 GB, 100 GB/mes blando); Cloudflare Tunnel (funcionamiento solo
saliente, sin IP pública).

**No verificado (y por eso sin cifras):** límites del plan gratuito de CockroachDB Basic; Backblaze B2
(página en mantenimiento); Vercel y Netlify; PythonAnywhere; plan gratuito de Cloudflare Zero Trust
(asientos) y ancho de banda «ilimitado» de Pages; límites de subida de Cloudflare; Tailscale; precio de
un VPS de 2026; minutos de GitHub Actions en repo privado.

**Asumido a partir del código o de la documentación del repo:** estimaciones de slices; que un VPS de
2 GB cuesta 4-6 €/mes; que un Postgres autoalojado en la VM soporta este corpus; que el worker aparte
funciona sobre la misma base (el lease está diseñado para eso, pero **no se ha probado con dos
procesos**).

---

## 9. Anexo B — URLs consultadas (09/11/2026)

- Neon — límites del plan Free: https://neon.com/faqs/free-plan-limits-and-quotas (página: 03/11/2026)
- Neon — 1 GB por proyecto: https://neon.com/blog/neon-free-plan-1-gb-per-project (02/10/2026)
- Supabase — precios: https://supabase.com/pricing.md
- Aiven — free tier de PostgreSQL: https://aiven.io/docs/products/postgresql/concepts/pg-free-tier (08/09/2026)
- CockroachDB — planificación de Basic: https://docs.cockroachlabs.com/docs/cockroachcloud/plan-your-cluster-basic (contenido no legible)
- Render — despliegue gratuito: https://render.com/docs/free
- Railway — precios: https://railway.com/pricing.md
- Fly.io — free trial: https://docs.fly.io/about/free-trial.md
- Koyeb — precios: https://www.koyeb.com/pricing
- Oracle Cloud — Always Free Resources: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
- Cloudflare R2 — precios: https://developers.cloudflare.com/r2/pricing/ (30/10/2026)
- Cloudflare Pages — límites: https://developers.cloudflare.com/pages/platform/limits/ (05/09/2026)
- Cloudflare Tunnel — funcionamiento: https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/ (04/08/2026)
- GitHub Pages — límites: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- Backblaze B2 — precios: https://www.backblaze.com/cloud-storage/pricing (mantenimiento)

Referencias internas del repo usadas como dato: `docs/DEBT.md:158-180` (DEBT-003),
`docs/encargos/2026-11-02-temario-c1-y-panel-oposiciones.md:14` (tamaño real de la base),
`docs/OPERACION.md:46-135` (copias, restauración, release local),
`docs/product-spec/09_SECURITY-PRIVACY-AND-RIGHTS.md` (§2, §8, §9, §10),
`docs/product-spec/02_ARCHITECTURE.md` (§5, §6, §9), `docs/product-spec/01_PRODUCT-SPEC.md:175-178`
(fuera de alcance), `docs/product-spec/13_DECISIONS-AND-OPEN-QUESTIONS.md` (Q001, Q008 y decisiones
futuras), `AGENTS.md`, `README.md:103-134`, `.env.example`, `scripts/*.ps1`.

---

## 10. Anexo C — cómo comprobar este plan sin creerme (checklist antes de firmar nada)

1. Entrar en cada panel y **leer el límite en la cuenta real** (los planes cambian: Neon pasó de 0,5 GB a
   1 GB el 02/10/2026 [V]).
2. Medir la base real (`opofuente.sqlite3`) y los artefactos importados **en el momento** de decidir: el
   número de este documento (2.656 MB) es de un encargo anterior.
3. Probar `docker compose up` en un portátil Linux/WSL antes de tocar el servidor: hoy no existe el
   fichero y el arranque es PowerShell.
4. Medir la memoria real de un lote de 20 PDFs de 50 MB en el worker (es lo que decide si un PaaS de
   512 MB es posible).
5. Hacer **una** importación con el CSP actual y ver el error de `connect-src` para confirmar §4.4.
6. Crear una instancia A1 y ver si la región tiene capacidad; comprobar la política de reclamación por
   inactividad en la consola antes de confiar datos.
7. Ensayar la restauración de una copia en otra máquina y cronometrarla.
8. Solo entonces, escribir el ADR de D1/D2/D3 y desplegar.

---

*Documento preparado por el teammate `despliegue` para David. No se ha ejecutado ningún despliegue ni se
ha abierto ningún servidor. Lo que aquí no lleva [V] es una suposición y está dicho como tal.*
