import { useState } from 'react';

import { buildCitation, copyToClipboard, type CitationInput } from './citation';

export interface CopyCitationButtonProps extends CitationInput {
  /** Qué se cita, para que el nombre accesible distinga un botón de otro en la misma lista. */
  label: string;
}

/**
 * «Copiar cita»: lleva al portapapeles el título, la versión, la sección o página y la URL.
 *
 * El aviso de copiado es explícito y con `role="status"` para que se anuncie: un botón que no dice
 * nada deja al usuario sin saber si la cita está copiada o hay que volver a intentarlo.
 */
export function CopyCitationButton({ title, version, place, label }: CopyCitationButtonProps) {
  const [state, setState] = useState<'quieto' | 'copiado' | 'fallo'>('quieto');

  return (
    <span className="citation">
      <button
        className="button"
        type="button"
        aria-label={`Copiar la cita: ${label}`}
        onClick={() => {
          void copyToClipboard(buildCitation({ title, version, place })).then((copiada) => {
            setState(copiada ? 'copiado' : 'fallo');
          });
        }}
      >
        Copiar cita
      </button>
      {state === 'copiado' && (
        <span className="hint" role="status">
          copiado: título, versión, {place} y URL
        </span>
      )}
      {state === 'fallo' && (
        <span className="hint" role="status">
          El navegador no dejó copiar: selecciona el texto y cópialo a mano.
        </span>
      )}
    </span>
  );
}
