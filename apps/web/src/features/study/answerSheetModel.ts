import type { StudentOutcome, StudentResultQuestion, StudentSheetRow } from '../../api/studentTests';

/**
 * Lo que la hoja de respuestas y la pantalla del test necesitan **sin ser componentes**: las letras
 * con las que se dibuja la hoja, el estado de una casilla y la frase con la que se cuenta cómo
 * quedó una fila.
 *
 * Vive aparte del componente a propósito: un módulo que exporta componentes y además constantes y
 * funciones obliga a recargar la pantalla entera cada vez que cambia la constante (`react-refresh`).
 */

/** Las cuatro letras de la hoja oficial. Se usan cuando no hay pregunta a la vista (test terminado),
 * porque la de TAI no publica cuántas alternativas tiene cada pregunta y la hoja no las adivina. */
export const LETRAS_POR_DEFECTO: readonly string[] = ['a', 'b', 'c', 'd'];

export type EstadoCasilla = 'vacia' | 'marcada' | 'correcta' | 'fallada' | 'dudosa';

/** El estado de una casilla, según lo que se marcó y lo que se pudo corregir. */
export function estadoDeCasilla(fila: StudentSheetRow, letra: string): EstadoCasilla {
  const marcada = fila.chosen.includes(letra);
  if (fila.outcome !== null) {
    if (fila.correct.includes(letra)) {
      return 'correcta';
    }
    return marcada ? 'fallada' : 'vacia';
  }
  if (marcada) {
    return fila.confidence === 'low' ? 'dudosa' : 'marcada';
  }
  return 'vacia';
}

/** Cómo quedó una fila, en palabras, para el resumen del resultado. */
export function textoDeOutcome(outcome: StudentOutcome | null): string {
  if (outcome === 'correct') {
    return 'bien';
  }
  if (outcome === 'wrong') {
    return 'mal';
  }
  if (outcome === 'blank') {
    return 'en blanco';
  }
  return 'sin corregir';
}

/**
 * Las filas de la hoja a partir de las preguntas **ya corregidas** de un resultado (§2.4).
 *
 * La hoja del resultado es la misma que la del test en curso, con dos diferencias que no son de dibujo:
 *
 * 1. `outcome` deja de ser `null`: el desenlace del resultado (`void` incluido) se traduce al de la
 *    hoja, y eso es lo que hace que la casilla correcta se pinte verde y la fallada roja;
 * 2. no hay `confidence`: la duda se marca mientras se contesta, no cuando ya está corregido.
 *
 * Un desenlace que la plantilla no corrige (`void`) se queda **sin corregir** en la hoja —`outcome`
 * `null`— a propósito: pintar sus casillas sería decir que hay una respuesta correcta que nadie ha
 * calculado.
 */
export function filasDeResultado(
  preguntas: readonly StudentResultQuestion[],
): readonly StudentSheetRow[] {
  return preguntas.map((pregunta) => ({
    position: pregunta.position,
    answered: pregunta.chosen.length > 0,
    chosen: pregunta.chosen,
    confidence: null,
    outcome: pregunta.outcome === 'void' ? null : pregunta.outcome,
    correct: pregunta.correct,
  }));
}

/**
 * Las letras con las que se dibuja la hoja de un resultado.
 *
 * No se adivinan: se toman de las opciones que **de verdad** tienen las preguntas de este test. La TAI
 * no publica cuántas alternativas tiene cada pregunta, y dibujar cuatro casillas cuando la pregunta
 * tiene dos sería enseñar una hoja que no es la suya. Si no hay ninguna opción, se cae a las cuatro de
 * la hoja oficial, que es lo que hace la hoja del test en curso.
 */
export function letrasDeLaHoja(preguntas: readonly StudentResultQuestion[]): readonly string[] {
  const letras = new Set<string>();
  for (const pregunta of preguntas) {
    for (const opcion of pregunta.options) {
      letras.add(opcion.key);
    }
  }
  if (letras.size === 0) {
    return LETRAS_POR_DEFECTO;
  }
  return [...letras].sort();
}
