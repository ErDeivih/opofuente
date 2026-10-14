import type { StudentOutcome, StudentSheetRow } from '../../api/studentTests';

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
