# Encargo: temario C1 (TAI) completo + panel de oposiciones C1 informática

**Fecha:** 02/11/2026 · **Para:** agente de Orca del equipo *OpoFuente* · **Origen:** encargo del usuario

---

## 0. Estado medido (lo que hay hoy)

> **CORRECCIÓN IMPORTANTE (02/11/2026, tarde).** La primera versión de este encargo miraba la base del
> worktree `fase0` (0 MB, vacía). **La base real no está en el repo**:
>
> | Qué | Dónde de verdad |
> |---|---|
> | **Datos reales** | `F:\OpoFuente\datos\opofuente.sqlite3` — **2.656 MB**, 76 tablas: `curriculum_nodes` **401**, `exam_parts` 12, `exam_rules` 59, `oppositions` **3**, `convocation_versions` 4, `question_versions` **18.889**, `cards` 5.283, `source_artifacts` **6.259** |
> | **Copias verificadas** | `F:\OpoFuente\datos\backups` (6) |
> | **Código bueno** | `F:\temp-opofuente\opofuente-restaurado` y `C:\Users\David\orca\workspaces\opofuente\equipo-ia`, ambos en **main = 6483111** |
> | **Worktree viejo** | `F:\EspacioCodigo\opofuente` (rama `fase0…`, 98d8e60) — su base de 0 MB es un esqueleto, **no usar para medir** |

**Consecuencia**: el temario ya tiene **401 nodos y 3 oposiciones** cargadas. Lo que este encargo añade es
**la oposición nueva «C1 Informática»** (40 temas del común + locales) y el **panel de convocatorias**,
sin duplicar lo que ya existe ni tocar los datos del propietario (archivar, nunca borrar).

| Sitio | Qué hay |
|---|---|
| `F:\OpoFuente\datos\opofuente.sqlite3` | **Los datos buenos** (2,6 GB, 18.889 versiones de preguntas, 401 nodos de temario, 6.259 artefactos de origen) |
| `F:\temp-opofuente\opofuente-restaurado` | **Código main @ 6483111**: 48 migraciones, 18 puertas, 32 herramientas, guardián de capturas |
| `C:\Users\David\orca\workspaces\opofuente\equipo-ia` | Mismo main @ 6483111 (aquí trabaja el equipo) |
| `F:\EspacioCodigo\opofuente` | Rama `fase0-reconciliacion…` (98d8e60): **estado antiguo**; su `data\opofuente.sqlite3` es un esqueleto de 0 MB |
| `C:\Users\David\orca\workspaces\opofuente\equipo-ia\data\sources` | 18 fuentes descargadas |
| `C:\Users\David\OneDrive\Escritorio` | **81 ficheros** de material TAI: `000 - TESTS PRIMER EXAMEN.pdf` (4,2 MB), carpeta **`Apuntes TAI\`** (leyes ESTAILIBLI, tests, resúmenes), APK `EstudiaTAI` |

**Conclusión:** el *software* y **los datos del temario** ya están; lo que falta es (a) la oposición
**C1 Informática** con su temario común/local y (b) el **panel de convocatorias**. No hay que rehacer lo
que ya existe.

---

## 1. Objetivo A — Temario C1 de informática completo, con apuntes

### 1.1 Estructura pedida

- **Temario COMÚN** (lo que se repite en las convocatorias): 40 temas en 5 bloques. Es la base que sirve
  para cualquier C1 de informática.
- **Temario LOCAL, separado por convocatoria** (NO en el común): leyes autonómicas, ordenanzas, régimen
  local específico de cada ayuntamiento, pruebas de lengua cooficial, etc. Cada convocatoria tiene su
  propio conjunto de «extras» que se añaden sobre el común.

### 1.2 Los 40 temas del común (base ya validada con bases reales de 2026)

**Bloque I — Administración y normativa (1-12):** Constitución · UE · régimen local (Ley 7/1985) ·
organización municipal · procedimiento administrativo (39/2015) · régimen jurídico (40/2015) · TREBEP ·
función pública local · haciendas locales y presupuesto · contratación (9/2017) · igualdad y violencia de
género · transparencia y protección de datos.

**Bloque II — Informática básica y ofimática (13-17):** arquitectura de ordenadores · SO de usuario
(Windows/Linux) · ofimática · correo y colaboración · licencias y software libre.

**Bloque III — Sistemas, redes y comunicaciones (18-26):** SO de servidor · virtualización y contenedores ·
almacenamiento y copias/continuidad · redes (OSI/TCP-IP, IPv4-IPv6, VLAN) · comunicaciones (WiFi, VPN,
MPLS, VoIP) · servicios de red (DNS, DHCP, AD/LDAP) · monitorización e incidencias (ITIL, SLA, ticketing) ·
cloud y CPD · soporte al puesto de trabajo.

**Bloque IV — Datos y desarrollo (27-33):** bases de datos relacionales · SQL · gestores (Oracle, SQL
Server, PostgreSQL, MySQL) · programación y Git · desarrollo web y APIs REST · interoperabilidad (XML,
JSON, servicios) · informes y BI.

**Bloque V — Seguridad y administración electrónica (34-40):** seguridad de la información (ISO 27001,
MAGERIT) · **ENS (RD 311/2022)** · criptografía y firma electrónica · protección de datos aplicada ·
ciberseguridad e incidentes (CCN-CERT/INCIBE) · administración electrónica práctica · accesibilidad.

### 1.3 Trabajo de contenido (esto es lo que falta)

1. **Cargar el material del Escritorio** en la BD (`curriculum_nodes`, `ingestion_*`):
   - `Apuntes TAI\` (PDFs y DOCX de leyes y tests),
   - `000 - TESTS PRIMER EXAMEN.pdf` (4,2 MB de tests),
   - cualquier otro test/supuesto que encuentres.
2. **Mapear** cada documento a su tema del común (o a «local» si es de una convocatoria concreta).
3. **Detectar huecos**: temas sin apuntes y temas sin tests. Entregar un informe `falta.md` con:
   lista de los 40 temas, estado (apuntes ✅/❌, tests ✅/❌, nº preguntas), y qué falta exactamente.
4. **Revisar los exámenes** (los tests cargados) y **detectar materias que aparezcan y no estén** en el
   común: añadirlas como tema 41+ o como «local» según corresponda. Guardar la justificación (de qué
   examen sale).
5. **Apuntes**: cada tema debe tener su nota (resumen + desarrollo) y, si existe en el material, enlace al
   PDF de origen. No inventar contenido legal: si falta, marcar como «pendiente de fuente».

---

## 2. Objetivo B — Panel de oposiciones C1 informática

Referencias del usuario (estudiadas): `boletindeoposiciones.es` y `redopositor.com/empleo-publico/`.
Lo que hacen: **ingieren BOE + boletines autonómicos + locales**, calculan el plazo (días hábiles,
festivos), agrupan por puesto y comunidad, y muestran ficha con plazas, grupo, temario, tasa, enlaces.

### 2.1 Modelo (reutilizar lo existente: `oppositions`, `convocation_versions`, `exam_parts`)

Campos mínimos por convocatoria: `id`, `organismo`, `ámbito` (estatal/autonómico/local), `comunidad`,
`provincia`, `municipio`, `cuerpo/puesto`, `grupo` (A1/A2/B/C1/C2), `sistema` (oposición/concurso-
oposición), `plazas`, `turno` (libre/PI), `titulación`, `tasa`, `temario_ref` (común + local), `fecha_publicacion`,
`fuente_boletín`, `url_boletín`, `url_bases`, `plazo_inicio`, `plazo_fin` (calculado, no estimado si la
base lo dice), `estado` (abierto/cerrado/pendiente), `observaciones`, `hash_fuente` (para deduplicar).

### 2.2 Ingesta (prioridad: fuentes oficiales, no scrapear agregadores)

1. **BOE**: API de datos abiertos (XML/JSON) — sección de oposiciones. Ya hay ayudante en el repo si existe.
2. **Punto de Acceso General** (`administracion.gob.es/empleopublico`): convocatorias + bolsas.
3. **BOCYL** (Castilla y León) y **BOP de Salamanca**: convocatorias locales y bolsas.
4. **Boletines autonómicos** de las comunidades con más C1 de informática (Cataluña, Valencia, Andalucía,
   Madrid, Castilla-La Mancha, Extremadura).
5. **Regla de oro**: guardar el **artefacto original** (`source_artifacts`) + `artifact_origins` con URL,
   fecha de captura y hash. Nunca mostrar datos sin origen.

### 2.3 Cálculo de plazos (lo que más valor da)

- Días **hábiles**, excluyendo sábados, domingos y **festivos nacionales + de la comunidad + del
  municipio** (tabla de festivos).
- Si la base no fija fecha, marcar **«estimado»** en la UI (como hace boletindeoposiciones).
- Recalcular al cambiar el año/festivos.

### 2.4 UI

- Listado con filtros: **grupo = C1**, **puesto = informática**, comunidad, provincia, «abiertas hoy»,
  «cierran esta semana».
- Ficha con: plazas, grupo, temario (común + local), tasa, enlaces al boletín y a las bases, plazo con
  cuenta atrás y estado.
- Vista «mi temario»: qué temas del común cubren esa convocatoria y cuáles son sus extras locales.

---

## 3. Criterios de aceptación

- [ ] `SELECT count(*) FROM curriculum_nodes` > 400 (40 temas con subnodos y apuntes).
- [ ] `falta.md` generado: 40 temas con estado apuntes/tests y lista de huecos.
- [ ] Cada tema del común tiene al menos un material asociado (apunte) o marca explícita de pendiente.
- [ ] Lo local está separado: ninguna ley autonómica/metropolitana dentro del común.
- [ ] `oppositions` con ≥ 20 convocatorias C1 informática reales cargadas, todas con `url_boletín`.
- [ ] Plazo calculado en hábiles con festivos y marca «estimado» cuando proceda.
- [ ] Panel con filtro C1 + informática funcionando y probado (test o e2e).
- [ ] Sin regresiones: `npm test`, `npm run typecheck`, `pytest` en verde.

## 4. Fuera de alcance

- No scrapear agregadores de terceros como fuente principal (solo como referencia de UX).
- No inventar contenido legal: si no hay fuente, se marca pendiente.
- No tocar los ADRs sin justificarlo.

## 5. Material de partida (rutas exactas)

- `C:\Users\David\OneDrive\Escritorio\Apuntes TAI\` (leyes, tests, resúmenes)
- `C:\Users\David\OneDrive\Escritorio\000 - TESTS PRIMER EXAMEN.pdf`
- `F:\EspacioCodigo\opofuente\docs\REDISENO-ALUMNO-TAI-Y-PANEL-ADMIN-2026-10.md`
- `F:\EspacioCodigo\opofuente\docs\DEBT.md` (deuda y decisiones previas)
- `C:\Users\David\orca\workspaces\opofuente\equipo-ia\data\sources\` (18 fuentes ya descargadas)

## 6. Entregables

1. `docs/encargos/informe-temario-c1.md`: los 40 temas con estado, huecos y qué se ha cargado.
2. `docs/encargos/informe-panel-oposiciones.md`: fuentes, modelo, ingesta, plazos, UI y pruebas.
3. Datos cargados en la BD (temario + convocatorias) y `falta.md`.
4. Tests/e2e del panel.
