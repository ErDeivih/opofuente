/**
 * La opción de una pregunta (F3 del rediseño).
 *
 * Dos reglas que se ven en el componente:
 *
 * 1. **el color no es la única señal**: «Correcta» y «Tu respuesta» van escritos, con su ✓ y su ✗, así
 *    que se entiende también sin distinguir el verde del rojo;
 * 2. **la letra va en un círculo a la izquierda** (A–D), que es lo que se teclea para contestar.
 */

export type OptionState = 'idle' | 'chosen' | 'correct' | 'wrong' | 'disabled';

export interface OptionButtonProps {
  optionKey: string;
  text: string;
  state: OptionState;
  onChoose?: () => void;
}

export function OptionButton({ optionKey, text, state, onChoose }: OptionButtonProps) {
  const clases = ['ui-option'];
  if (state === 'chosen') {
    clases.push('ui-option--chosen');
  }
  if (state === 'correct') {
    clases.push('ui-option--correct');
  }
  if (state === 'wrong') {
    clases.push('ui-option--wrong');
  }
  const marca =
    state === 'correct' ? (
      <span className="ui-option__mark">
        <span aria-hidden="true">✓ </span>Correcta
      </span>
    ) : state === 'wrong' ? (
      <span className="ui-option__mark">
        <span aria-hidden="true">✗ </span>Tu respuesta
      </span>
    ) : state === 'chosen' ? (
      <span className="ui-option__mark">Elegida</span>
    ) : null;

  // Una opción ya corregida no se vuelve a pulsar, pero sigue leyéndose: se deshabilita, no se esconde.
  const corregida = state === 'correct' || state === 'wrong' || state === 'disabled';

  return (
    <button
      type="button"
      className={clases.join(' ')}
      onClick={corregida ? undefined : onChoose}
      disabled={corregida}
      aria-pressed={state === 'chosen' ? true : undefined}
    >
      <span className="ui-option__key" aria-hidden="true">
        {optionKey}
      </span>
      <span>{text}</span>
      {marca}
    </button>
  );
}
