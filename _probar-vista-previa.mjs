// Diagnóstico de solo lectura: huellas de las fuentes locales frente al manifiesto.
// No imprime contenido; solo existencia, tamaño y hashes.
import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

function sha256(buf) {
  return createHash("sha256").update(buf).digest("hex");
}

function unescapeHtml(value) {
  return value
    .replace(/&#x([0-9a-f]+);/gi, (_, hex) => String.fromCodePoint(parseInt(hex, 16)))
    .replace(/&#(\d+);/g, (_, dec) => String.fromCodePoint(Number(dec)))
    .replace(/&nbsp;/gi, " ")
    .replace(/&quot;/gi, '"')
    .replace(/&apos;/gi, "'")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&amp;/gi, "&");
}

function contentFingerprint(text) {
  const sinComentarios = text.replace(/<!--[\s\S]*?-->/g, " ");
  const sinRuido = sinComentarios.replace(
    /<(script|style|noscript)\b[^>]*>[\s\S]*?<\/\1>/gi,
    " ",
  );
  const sinEtiquetas = sinRuido.replace(/<[^>]+>/g, " ");
  return sha256(Buffer.from(unescapeHtml(sinEtiquetas).replace(/\s+/g, " ").trim(), "utf8"));
}

function buscarManifiesto(inicio) {
  let actual = resolve(inicio);
  for (let i = 0; i < 6; i += 1) {
    const candidato = join(actual, "fixtures", "profiles", "manifest.json");
    if (existsSync(candidato)) return candidato;
    const padre = dirname(actual);
    if (padre === actual) break;
    actual = padre;
  }
  return null;
}

const cwd = process.cwd();
const manifiesto = buscarManifiesto(cwd);
const salida = { cwd, manifiesto, raiz: null, fuentes: [] };
if (manifiesto) {
  const raiz = dirname(dirname(dirname(manifiesto)));
  salida.raiz = raiz;
  salida.entradasRaiz = readdirSync(raiz).sort();
  const datos = JSON.parse(readFileSync(manifiesto, "utf8"));
  for (const fuente of datos.sources) {
    const ruta = join(raiz, fuente.local_path);
    const existe = existsSync(ruta);
    const fila = {
      id: fuente.id,
      local_path: fuente.local_path,
      existe,
      declarado: fuente.sha256,
      volatile: Boolean(fuente.volatile),
      content_sha256: fuente.content_sha256 ?? null,
    };
    if (existe) {
      const bytes = readFileSync(ruta);
      fila.size = bytes.length;
      fila.sha256 = sha256(bytes);
      fila.content_fingerprint = contentFingerprint(bytes.toString("utf8"));
    }
    salida.fuentes.push(fila);
  }
}
console.log(JSON.stringify(salida, null, 2));
