import { Fragment } from 'react';

import type { StudentSheetRow } from '../../api/studentTests';
import { estadoDeCasilla } from './answerSheetModel';

/**
 * La hoja de respuestas del test en curso (diseño v0, concepto «la hoja de respuestas»).
 *
 * Es la rejilla numerada con sus casillas A B C D, como la plantilla oficial: la fila que se está
 * contestando se resalta, la marcada en azul está respondida, la marcada como dudosa lleva el
 * contorno ámbar y, cuando la corrección se puede enseñar, la casilla correcta se pone verde y la
 * fallada roja. La hoja **no** decide nada: recibe las filas ya calculadas y las pinta.
 *
 * Accesibilidad: es una lista de filas, cada casilla lleva su `aria-label` (`Fila 12, opción B`) y la
 * fila actual se marca con `aria-current`. Sin eso, la hoja sería un dibujo: se puede ver, no se
 * puede usar con un lector de pantalla.
 */

export interface AnswerSheetProps {
  readonly filas: readonly StudentSheetRow[];
  readonly actual: number | null;
  /** Con qué letras se dibuja la hoja. Requerido: la hoja no adivina las alternativas. */
  readonly letras: readonly string[];
  readonly onIr?: (position: number) => void;
}

export function AnswerSheet({ filas, actual, letras, onIr }: AnswerSheetProps) {
  if (filas.length === 0) {
    return <p className="hoja__vacia">La hoja de respuestas aparecerá al empezar el test.</p>;
  }
  return (
    <ol className="hoja" aria-label="Hoja de respuestas">
      {filas.map((fila, indice) => {
        // **La hoja se parte en dos cuando cambia la parte**: el simulacro es un examen de dos
        // partes y la hoja las enseñaba seguidas, sin decir dónde acaba una y empieza la otra.
        const anterior = indice === 0 ? null : (filas[indice - 1]?.part_code ?? null);
        const empiezaParte = fila.part_code !== null && fila.part_code !== anterior;
        return (
          <Fragment key={fila.position}>
            {empiezaParte && (
              // **No es una fila**: es un separador, y por eso no cuenta como fila de la hoja.
              <li className="hoja__parte" role="presentation">
                {fila.part_code === 'segunda_parte'
                  ? 'Segunda parte · Supuesto'
                  : 'Primera parte'}
              </li>
            )}
        <li
          key={fila.position}
          className="hoja__fila"
          aria-current={fila.position === actual ? 'true' : undefined}
          data-actual={fila.position === actual ? 'si' : undefined}
        >
          <button
            type="button"
            className="hoja__numero"
            onClick={onIr === undefined ? undefined : () => onIr(fila.position)}
            aria-label={`Ir a la pregunta ${String(fila.position)}`}
          >
            {fila.position}
          </button>
          <span className="hoja__casillas">
            {letras.map((letra) => {
              const estado = estadoDeCasilla(fila, letra);
              return (
                <span
                  key={letra}
                  className={`hoja__casilla hoja__casilla--${estado}`}
                  data-estado={estado}
                  aria-label={`Fila ${String(fila.position)}, opción ${letra.toUpperCase()}`}
                >
                  {letra.toUpperCase()}
                </span>
              );
            })}
          </span>
        </li>
          </Fragment>
        );
      })}
    </ol>
  );
}
