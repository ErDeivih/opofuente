/**
 * Lo que **nunca** debe aparecer en la zona del alumno (REDISENO-ALUMNO-TAI-Y-PANEL-ADMIN §3.11).
 *
 * El alumno ve un temario, unos apuntes, unos tests y su progreso. No ve de dónde sale cada pregunta,
 * ni los ficheros del propietario, ni las otras oposiciones, ni la jerga con la que está hecha la
 * aplicación por dentro. Esta lista es la que comprueban las capturas de pantalla y —en F9— la prueba
 * que bloquea las puertas; se amplía aquí y no en cada prueba.
 *
 * Criterio para añadir una palabra: si al alumno no le dice nada útil y solo existe porque el material
 * viene de ficheros, va a la lista.
 */

/** Rutas de fichero y carpetas del propietario. */
export const RUTAS_PROHIBIDAS: readonly string[] = [':\\', 'Users', 'F:\\', '.pdf', '.docx', '.zip'];

/** Oposiciones que no son TAI: esta zona es solo de TAI. */
export const OPOSICIONES_PROHIBIDAS: readonly string[] = [
  'Celador',
  'Guardia Civil',
  'SAS',
  'BOCYL',
];

/** Nombres de bancos privados y de ficheros del propietario que no se pueden ofrecer. */
export const BANCOS_PROHIBIDOS: readonly string[] = ['Rojo', 'GSI', 'Test GSI', 'Preparatic'];

/** La cocina de la aplicación: cómo se importa, se clasifica y se revisa el material. */
export const JERGA_PROHIBIDA: readonly string[] = [
  'revisión',
  'revision',
  'bandeja',
  'fuente',
  'fuentes',
  'tramo',
  'mapeo',
  'representación',
  'conjunto',
  'clave',
  'versión',
  'evidencia',
  'artefacto',
];

/** Todo junto, para recorrerlo de una vez. */
export const PALABRAS_PROHIBIDAS: readonly string[] = [
  ...RUTAS_PROHIBIDAS,
  ...OPOSICIONES_PROHIBIDAS,
  ...BANCOS_PROHIBIDOS,
  ...JERGA_PROHIBIDA,
];

/** Un UUID visible: en la zona del alumno las direcciones llevan `I-1`, `IV-10`, no identificadores. */
export const UUID_VISIBLE = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;

export interface Encontrado {
  /** La palabra o el patrón que aparece. */
  palabra: string;
  /** Dónde aparece, con un poco de contexto para poder buscarlo. */
  contexto: string;
}

/** Busca en un texto las palabras prohibidas y los UUID, y devuelve lo que encuentre. */
export function palabrasEnElTexto(texto: string): Encontrado[] {
  const encontrados: Encontrado[] = [];
  const sinEtiquetas = texto.replace(/<[^>]*>/g, ' ');
  for (const palabra of PALABRAS_PROHIBIDAS) {
    const indice = sinEtiquetas.toLowerCase().indexOf(palabra.toLowerCase());
    if (indice >= 0) {
      encontrados.push({
        palabra,
        contexto: sinEtiquetas.slice(Math.max(0, indice - 40), indice + 40).trim(),
      });
    }
  }
  const uuid = UUID_VISIBLE.exec(sinEtiquetas);
  if (uuid !== null) {
    encontrados.push({ palabra: 'uuid visible', contexto: uuid[0] });
  }
  return encontrados;
}
