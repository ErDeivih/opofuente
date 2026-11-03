// Puerta de contrato: valida el manifiesto de importación C1 Informática.
// Solo forma y coherencia interna. NO importa nada, NO toca la base real y NO
// acredita que los 40 temas oficiales estén verificados: el manifiesto es
// sintético y sus fuentes son huecos con sha256 pendiente.
import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(scriptDir, "..", "..", "..", "..");
const manifestRel = "apps/api/opofuente/resources/c1-informatica-manifest.json";
const manifestPath = join(repoRoot, manifestRel);

const errors = [];
const warnings = [];
let checks = 0;

function ok(condition, message) {
  checks += 1;
  if (!condition) errors.push(message);
  return condition;
}

function warn(message) {
  warnings.push(message);
}

function sha256(buf) {
  return createHash("sha256").update(buf).digest("hex");
}

const isObject = (value) => value !== null && typeof value === "object" && !Array.isArray(value);
const isNonEmptyString = (value) => typeof value === "string" && value.trim().length > 0;
const CODE_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const SHA256_PATTERN = /^[0-9a-f]{64}$/;

function requireKeys(value, allowed, where) {
  if (!isObject(value)) {
    errors.push(`${where}: se esperaba un objeto`);
    checks += 1;
    return false;
  }
  const extra = Object.keys(value).filter((key) => !allowed.includes(key));
  ok(extra.length === 0, `${where}: claves no permitidas ${JSON.stringify(extra)}`);
  const missing = allowed.filter((key) => !(key in value));
  ok(missing.length === 0, `${where}: faltan claves ${JSON.stringify(missing)}`);
  return true;
}

if (!existsSync(manifestPath)) {
  errors.push(`No existe el manifiesto esperado: ${manifestRel}`);
  console.log(JSON.stringify({ ok: false, manifest: manifestPath, checks, errors, warnings }, null, 2));
  process.exit(1);
}

const raw = readFileSync(manifestPath, "utf8");
let manifest;
try {
  manifest = JSON.parse(raw);
} catch (error) {
  errors.push(`JSON inválido en ${manifestRel}: ${error.message}`);
  console.log(JSON.stringify({ ok: false, manifest: manifestPath, checks, errors, warnings }, null, 2));
  process.exit(1);
}

// --- Raíz ---
requireKeys(
  manifest,
  [
    "schema_version",
    "kind",
    "synthetic",
    "generated_at",
    "statement",
    "opposition",
    "curriculum",
    "common_blocks",
    "local_topics",
    "convocation_scopes",
    "sources",
    "import_rules",
    "panel",
  ],
  "raíz",
);
ok(manifest.schema_version === 1, "raíz: schema_version debe ser 1");
ok(manifest.kind === "opofuente.import-contract", "raíz: kind inesperado");
ok(typeof manifest.synthetic === "boolean", "raíz: synthetic debe ser booleano");
ok(
  isNonEmptyString(manifest.generated_at) && !Number.isNaN(Date.parse(manifest.generated_at)),
  "raíz: generated_at debe ser una fecha ISO válida",
);
ok(
  isNonEmptyString(manifest.statement) && manifest.statement.length >= 80,
  "raíz: statement debe explicar el alcance sintético (>=80 caracteres)",
);

// --- Oposición ---
const opposition = manifest.opposition;
requireKeys(opposition, ["code", "name", "group", "family", "notes"], "opposition");
if (isObject(opposition)) {
  ok(CODE_PATTERN.test(String(opposition.code)), "opposition.code no cumple el patrón de código");
  ok(isNonEmptyString(opposition.name), "opposition.name vacío");
  ok(["A1", "A2", "C1"].includes(opposition.group), "opposition.group debe ser A1, A2 o C1");
  ok(isNonEmptyString(opposition.family), "opposition.family vacío");
  ok(isNonEmptyString(opposition.notes), "opposition.notes vacío");
}

// --- Currículo ---
const curriculum = manifest.curriculum;
requireKeys(
  curriculum,
  [
    "blocks",
    "common_topics",
    "topics_per_block",
    "epigraphs_per_topic_min",
    "structure_parts",
    "questions_per_topic",
    "code_pattern",
    "existing_nodes_observation",
  ],
  "curriculum",
);
let topicCodePattern = null;
if (isObject(curriculum)) {
  ok(curriculum.blocks === 5, "curriculum.blocks debe ser 5");
  ok(curriculum.common_topics === 40, "curriculum.common_topics debe ser 40");
  ok(curriculum.topics_per_block === 8, "curriculum.topics_per_block debe ser 8");
  ok(
    Number.isInteger(curriculum.epigraphs_per_topic_min) && curriculum.epigraphs_per_topic_min >= 1,
    "curriculum.epigraphs_per_topic_min debe ser entero >= 1",
  );
  const parts = curriculum.structure_parts;
  ok(
    Array.isArray(parts) && parts.length === 6 && new Set(parts).size === 6,
    "curriculum.structure_parts debe tener 6 partes únicas",
  );
  ok(
    ["indice", "normativa", "resumen", "mapa_conceptual", "desarrollo", "preguntas"].every((part) =>
      Array.isArray(parts) ? parts.includes(part) : false,
    ),
    "curriculum.structure_parts no contiene las 6 partes acordadas",
  );
  const q = curriculum.questions_per_topic;
  ok(
    isObject(q) && Number.isInteger(q.min) && Number.isInteger(q.max) && q.min > 0 && q.min <= q.max,
    "curriculum.questions_per_topic inválido",
  );
  try {
    topicCodePattern = new RegExp(curriculum.code_pattern);
    checks += 1;
  } catch {
    errors.push("curriculum.code_pattern no compila");
    checks += 1;
  }
  const obs = curriculum.existing_nodes_observation;
  ok(
    isObject(obs) && Number.isInteger(obs.count) && obs.count >= 0,
    "curriculum.existing_nodes_observation.count inválido",
  );
  if (isObject(obs)) {
    ok(
      obs.checked_by_this_gate === false,
      "existing_nodes_observation.checked_by_this_gate debe ser false (esta puerta no abre la base real)",
    );
    ok(isNonEmptyString(obs.action), "existing_nodes_observation.action vacío");
  }
}

// --- Bloques y temas comunes ---
const blocks = manifest.common_blocks;
const commonTopics = [];
ok(Array.isArray(blocks) && blocks.length === 5, "common_blocks debe tener 5 bloques");
if (Array.isArray(blocks)) {
  const blockCodes = new Set();
  const blockPositions = new Set();
  const topicCodes = new Set();
  const topicPositions = new Set();
  for (const [index, block] of blocks.entries()) {
    const where = `common_blocks[${index}]`;
    if (!requireKeys(block, ["code", "position", "title", "topics"], where)) continue;
    ok(isNonEmptyString(block.code) && block.code.startsWith("C1-I-B"), `${where}.code debe empezar por C1-I-B`);
    ok(!blockCodes.has(block.code), `${where}.code duplicado`);
    blockCodes.add(block.code);
    ok(
      Number.isInteger(block.position) && block.position >= 1 && block.position <= 5,
      `${where}.position fuera de 1..5`,
    );
    ok(!blockPositions.has(block.position), `${where}.position duplicada`);
    blockPositions.add(block.position);
    ok(isNonEmptyString(block.title), `${where}.title vacío`);
    if (manifest.synthetic === true) {
      ok(block.title.includes("[SINTÉTICO]"), `${where}.title debe marcar [SINTÉTICO]`);
    }
    ok(Array.isArray(block.topics) && block.topics.length === 8, `${where}.topics debe tener 8 temas`);
    if (!Array.isArray(block.topics)) continue;
    for (const [topicIndex, topic] of block.topics.entries()) {
      const topicWhere = `${where}.topics[${topicIndex}]`;
      if (!requireKeys(topic, ["code", "position", "title", "epigraphs"], topicWhere)) continue;
      ok(isNonEmptyString(topic.code), `${topicWhere}.code vacío`);
      ok(!topicCodes.has(topic.code), `${topicWhere}.code duplicado`);
      topicCodes.add(topic.code);
      if (topicCodePattern) {
        ok(topicCodePattern.test(topic.code), `${topicWhere}.code no cumple curriculum.code_pattern`);
      }
      ok(
        Number.isInteger(topic.position) && topic.position >= 1 && topic.position <= 40,
        `${topicWhere}.position fuera de 1..40`,
      );
      ok(!topicPositions.has(topic.position), `${topicWhere}.position duplicada`);
      topicPositions.add(topic.position);
      ok(isNonEmptyString(topic.title), `${topicWhere}.title vacío`);
      if (manifest.synthetic === true) {
        ok(topic.title.includes("[SINTÉTICO]"), `${topicWhere}.title debe marcar [SINTÉTICO]`);
      }
      ok(
        Array.isArray(topic.epigraphs) &&
          topic.epigraphs.length >= (isObject(curriculum) ? curriculum.epigraphs_per_topic_min : 1) &&
          topic.epigraphs.every(isNonEmptyString),
        `${topicWhere}.epigraphs insuficientes o vacíos`,
      );
      commonTopics.push(topic);
    }
  }
  ok(commonTopics.length === 40, `deben declararse 40 temas comunes, hay ${commonTopics.length}`);
  ok(topicPositions.size === 40, "las posiciones de temas comunes deben cubrir 1..40 sin huecos ni duplicados");
}

// --- Temas locales ---
const localTopics = manifest.local_topics;
ok(Array.isArray(localTopics), "local_topics debe ser una lista");
if (Array.isArray(localTopics)) {
  const codes = new Set();
  const commonCodes = new Set(commonTopics.map((topic) => topic.code));
  for (const [index, topic] of localTopics.entries()) {
    const where = `local_topics[${index}]`;
    if (!requireKeys(topic, ["code", "position", "title", "scope", "epigraphs"], where)) continue;
    ok(isNonEmptyString(topic.code), `${where}.code vacío`);
    ok(!codes.has(topic.code), `${where}.code duplicado`);
    codes.add(topic.code);
    ok(!commonCodes.has(topic.code), `${where}.code colisiona con un tema común`);
    if (topicCodePattern) {
      ok(topicCodePattern.test(topic.code), `${where}.code no cumple curriculum.code_pattern`);
    }
    ok(Number.isInteger(topic.position) && topic.position >= 1, `${where}.position inválida`);
    ok(isNonEmptyString(topic.title), `${where}.title vacío`);
    if (manifest.synthetic === true) {
      ok(topic.title.includes("[SINTÉTICO]"), `${where}.title debe marcar [SINTÉTICO]`);
    }
    ok(isNonEmptyString(topic.scope), `${where}.scope vacío`);
    ok(
      Array.isArray(topic.epigraphs) && topic.epigraphs.length > 0 && topic.epigraphs.every(isNonEmptyString),
      `${where}.epigraphs inválidos`,
    );
  }
}

// --- Fuentes ---
const sources = manifest.sources;
const sourceIds = new Set();
ok(Array.isArray(sources) && sources.length > 0, "sources debe declarar al menos una fuente");
if (Array.isArray(sources)) {
  for (const [index, source] of sources.entries()) {
    const where = `sources[${index}]`;
    if (
      !requireKeys(
        source,
        [
          "id",
          "kind",
          "bulletin",
          "authority_tier",
          "rights_status",
          "rights_source_url",
          "expected_relative_path",
          "expected_sha256",
          "required",
          "status",
          "notes",
        ],
        where,
      )
    ) {
      continue;
    }
    ok(isNonEmptyString(source.id) && CODE_PATTERN.test(source.id), `${where}.id inválido`);
    ok(!sourceIds.has(source.id), `${where}.id duplicado`);
    sourceIds.add(source.id);
    ok(isNonEmptyString(source.kind), `${where}.kind vacío`);
    ok(["boe", "bocyl"].includes(source.bulletin), `${where}.bulletin debe ser boe o bocyl`);
    ok(["A", "B", "C", "D", "unknown"].includes(source.authority_tier), `${where}.authority_tier fuera del enum`);
    ok(
      ["reuse_with_conditions", "private_use_only", "rights_document", "unknown"].includes(source.rights_status),
      `${where}.rights_status fuera del enum`,
    );
    ok(
      source.rights_source_url === null || isNonEmptyString(source.rights_source_url),
      `${where}.rights_source_url inválido`,
    );
    const rel = source.expected_relative_path;
    ok(
      isNonEmptyString(rel) &&
        !isAbsolute(rel) &&
        !/^[a-zA-Z]:/.test(rel) &&
        !rel.split(/[\\/]/).includes("..") &&
        !rel.startsWith("/") &&
        !rel.startsWith("\\"),
      `${where}.expected_relative_path debe ser relativa, sin unidad ni ".."`,
    );
    ok(
      source.expected_sha256 === null || SHA256_PATTERN.test(String(source.expected_sha256)),
      `${where}.expected_sha256 debe ser null o 64 hex`,
    );
    ok(typeof source.required === "boolean", `${where}.required debe ser booleano`);
    ok(["placeholder", "verified"].includes(source.status), `${where}.status inválido`);
    ok(isNonEmptyString(source.notes), `${where}.notes vacío`);
    if (manifest.synthetic === false && source.required === true) {
      ok(source.status === "verified", `${where}: con synthetic=false toda fuente obligatoria debe estar verified`);
      ok(source.expected_sha256 !== null, `${where}: con synthetic=false toda fuente obligatoria fija sha256`);
    }
  }
}

// --- Ámbitos de convocatoria ---
const scopes = manifest.convocation_scopes;
const scopeCodes = new Set();
const referencedLocalTopics = new Map();
const localByCode = new Map((Array.isArray(localTopics) ? localTopics : []).map((topic) => [topic.code, topic]));
ok(Array.isArray(scopes) && scopes.length > 0, "convocation_scopes debe declarar al menos un ámbito");
if (Array.isArray(scopes)) {
  for (const [index, scope] of scopes.entries()) {
    const where = `convocation_scopes[${index}]`;
    if (
      !requireKeys(scope, ["code", "name", "administration", "bulletin", "source_ids", "local_topics", "deadline"], where)
    ) {
      continue;
    }
    ok(isNonEmptyString(scope.code) && CODE_PATTERN.test(scope.code), `${where}.code inválido`);
    ok(!scopeCodes.has(scope.code), `${where}.code duplicado`);
    scopeCodes.add(scope.code);
    ok(isNonEmptyString(scope.name), `${where}.name vacío`);
    ok(isNonEmptyString(scope.administration), `${where}.administration vacío`);
    ok(["boe", "bocyl"].includes(scope.bulletin), `${where}.bulletin debe ser boe o bocyl`);
    ok(Array.isArray(scope.source_ids) && scope.source_ids.length > 0, `${where}.source_ids vacío`);
    if (Array.isArray(scope.source_ids)) {
      for (const id of scope.source_ids) {
        ok(sourceIds.has(id), `${where}.source_ids referencia una fuente inexistente: ${id}`);
        const source = (Array.isArray(sources) ? sources : []).find((item) => item.id === id);
        if (source && source.bulletin !== scope.bulletin) {
          errors.push(`${where}.source_ids: la fuente ${id} es de boletín ${source.bulletin}, no ${scope.bulletin}`);
          checks += 1;
        }
      }
    }
    ok(Array.isArray(scope.local_topics), `${where}.local_topics debe ser una lista`);
    if (Array.isArray(scope.local_topics)) {
      for (const code of scope.local_topics) {
        const topic = localByCode.get(code);
        ok(Boolean(topic), `${where}.local_topics referencia un tema local inexistente: ${code}`);
        if (topic) ok(topic.scope === scope.code, `${where}: el tema local ${code} declara scope ${topic.scope}`);
        referencedLocalTopics.set(code, (referencedLocalTopics.get(code) ?? 0) + 1);
      }
    }
    const deadline = scope.deadline;
    if (
      requireKeys(
        deadline,
        ["start", "business_days", "holidays", "label", "official_overrides_estimate"],
        `${where}.deadline`,
      )
    ) {
      ok(["day_after_publication", "publication"].includes(deadline.start), `${where}.deadline.start inválido`);
      ok(
        Number.isInteger(deadline.business_days) && deadline.business_days > 0,
        `${where}.deadline.business_days inválido`,
      );
      ok(
        Array.isArray(deadline.holidays) &&
          deadline.holidays.length > 0 &&
          deadline.holidays.every((h) => ["nacional", "autonomico", "local"].includes(h)),
        `${where}.deadline.holidays inválido`,
      );
      ok(deadline.label === "estimado", `${where}.deadline.label debe ser "estimado"`);
      ok(deadline.official_overrides_estimate === true, `${where}.deadline.official_overrides_estimate debe ser true`);
    }
  }
  for (const [code, topic] of localByCode.entries()) {
    const count = referencedLocalTopics.get(code) ?? 0;
    ok(
      count === 1,
      `el tema local ${code} debe estar referenciado exactamente por un ámbito (referencias: ${count}, scope: ${topic.scope})`,
    );
  }
}

// --- Reglas de importación ---
const rules = manifest.import_rules;
if (
  requireKeys(
    rules,
    [
      "target_data_dir",
      "write_scope",
      "backup_before_write",
      "integrity_check_before_write",
      "dry_run_default",
      "confirmation_required",
      "never_delete",
      "originals_read_only",
      "idempotency",
      "abort_on_code_conflict",
      "report_required",
      "notes",
    ],
    "import_rules",
  )
) {
  ok(isNonEmptyString(rules.target_data_dir), "import_rules.target_data_dir vacío");
  const target = String(rules.target_data_dir).replaceAll("\\", "/").toLowerCase();
  checks += 1;
  if (!/^[a-z]:\//.test(target) && !target.startsWith("//")) {
    errors.push("import_rules.target_data_dir debe ser una ruta absoluta de unidad o UNC");
  }
  if (target.includes("/equipo-ia/") || target.includes("/workspace/")) {
    errors.push("import_rules.target_data_dir no puede apuntar al workspace del producto");
  }
  ok(rules.write_scope === "data_dir_only", "import_rules.write_scope debe ser data_dir_only");
  for (const key of [
    "backup_before_write",
    "integrity_check_before_write",
    "dry_run_default",
    "confirmation_required",
    "never_delete",
    "originals_read_only",
    "abort_on_code_conflict",
    "report_required",
  ]) {
    ok(rules[key] === true, `import_rules.${key} debe ser true`);
  }
  ok(rules.idempotency === "upsert_by_code", "import_rules.idempotency debe ser upsert_by_code");
  ok(isNonEmptyString(rules.notes), "import_rules.notes vacío");
}

// --- Panel ---
const panel = manifest.panel;
if (requireKeys(panel, ["filters", "columns", "deadline"], "panel")) {
  for (const key of ["filters", "columns"]) {
    ok(
      Array.isArray(panel[key]) &&
        panel[key].length > 0 &&
        panel[key].every(isNonEmptyString) &&
        new Set(panel[key]).size === panel[key].length,
      `panel.${key} debe ser una lista no vacía de cadenas únicas`,
    );
  }
  if (Array.isArray(panel.columns)) {
    for (const column of [
      "code",
      "body",
      "group",
      "scope",
      "published_at",
      "deadline_estimate",
      "authority_tier",
      "rights_status",
      "source_url",
    ]) {
      ok(panel.columns.includes(column), `panel.columns debe incluir ${column}`);
    }
  }
  const deadline = panel.deadline;
  if (
    requireKeys(
      deadline,
      ["supported", "excludes_weekends", "excludes_holidays", "holidays_required", "label", "official_overrides_estimate"],
      "panel.deadline",
    )
  ) {
    ok(deadline.supported === true, "panel.deadline.supported debe ser true");
    ok(deadline.excludes_weekends === true, "panel.deadline.excludes_weekends debe ser true");
    ok(deadline.excludes_holidays === true, "panel.deadline.excludes_holidays debe ser true");
    ok(deadline.holidays_required === true, "panel.deadline.holidays_required debe ser true");
    ok(deadline.label === "estimado", "panel.deadline.label debe ser estimado");
    ok(deadline.official_overrides_estimate === true, "panel.deadline.official_overrides_estimate debe ser true");
  }
}

// --- Huellas de fuentes: rutas relativas a import_rules.target_data_dir ---
// Si el directorio de datos no está montado en el sandbox, se avisa y no se
// falla: la verificación real corresponde al custodio con acceso al host.
let checksumsVerified = 0;
const targetDir = isNonEmptyString(manifest.import_rules?.target_data_dir)
  ? String(manifest.import_rules.target_data_dir).replaceAll("\\", "/").replace(/\/+$/, "")
  : null;
if (Array.isArray(sources)) {
  for (const source of sources) {
    if (!isObject(source) || !isNonEmptyString(source.expected_relative_path)) continue;
    checks += 1;
    if (!targetDir) {
      warn(`fuente ${source.id}: sin target_data_dir no se puede resolver la ruta (external_not_verified)`);
      continue;
    }
    const externalPath = `${targetDir}/${source.expected_relative_path}`;
    if (!existsSync(externalPath)) {
      warn(
        `fuente ${source.id}: ${externalPath} no es accesible desde el sandbox; pendiente de verificación externa (external_not_verified)`,
      );
      continue;
    }
    if (source.expected_sha256 !== null) {
      const actual = sha256(readFileSync(externalPath));
      if (actual !== source.expected_sha256) {
        errors.push(`fuente ${source.id}: sha256 no coincide (${actual} != ${source.expected_sha256})`);
      } else {
        checksumsVerified += 1;
      }
    } else {
      warn(`fuente ${source.id}: la fuente existe pero no declara sha256`);
    }
  }
}

const summary = {
  ok: errors.length === 0,
  manifest: manifestPath,
  manifest_sha256: sha256(Buffer.from(raw, "utf8")),
  synthetic: manifest.synthetic ?? null,
  checks,
  topics: commonTopics.length,
  local_topics: Array.isArray(localTopics) ? localTopics.length : 0,
  scopes: scopeCodes.size,
  sources: sourceIds.size,
  checksums_verified: checksumsVerified,
  external_not_verified: warnings.filter((warning) => warning.includes("external_not_verified")).length,
  warnings,
  errors,
};
console.log(JSON.stringify(summary, null, 2));
process.exit(summary.ok ? 0 : 1);
