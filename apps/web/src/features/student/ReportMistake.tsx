import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';

import { reportNotesMistake } from '../../api/studentStudy';
import { Button } from '../../ui/Button';
import { describeError } from '../system/labels';

/**
 * El botón «Esto está mal» de un apartado de los apuntes (decisión D2).
 *
 * Quién lo usa: el alumno que está leyendo y ve un error. Qué hace falta para que sirva de algo:
 *
 * 1. **el motivo, en una línea**: sin él, el aviso no se puede arreglar. El campo no deja mandarlo
 *    vacío (el botón está apagado hasta que hay algo escrito) y el servidor lo vuelve a comprobar;
 * 2. **el apartado, no el párrafo suelto**: se manda su clave y el anclaje lo pone el servidor, así
 *    que el aviso apunta al sitio donde vive el texto de hoy;
 * 3. **guardarlo de verdad**: la escritura entra en la API por su ruta auditada (`POST
 *    /student/topics/{codigo}/reports`). No hay ningún `console.log` por medio, y si la API falla se
 *    dice con su motivo en lugar de dar el aviso por enviado.
 *
 * Lo que **no** promete: ni cuándo se corrige ni quién lo hace. Lo que se puede afirmar es que queda
 * apuntado con el apartado delante.
 */

export interface ReportMistakeProps {
  /** El código legible del tema (`IV.7`), que es la dirección de estas rutas. */
  code: string;
  /** La clave del apartado: es lo único que hace falta para saber de qué texto se habla. */
  sectionKey: string;
  /** El título del apartado, para que el formulario diga dónde se está avisando. */
  sectionTitle: string;
}

export function ReportMistake({ code, sectionKey, sectionTitle }: ReportMistakeProps) {
  const [abierto, setAbierto] = useState(false);
  const [motivo, setMotivo] = useState('');

  const envio = useMutation({
    mutationFn: (razon: string) => reportNotesMistake(code, { section_key: sectionKey, reason: razon }),
    onSuccess: () => {
      setAbierto(false);
      setMotivo('');
    },
  });

  const titulo = `Esto está mal en «${sectionTitle}»`;

  if (envio.isSuccess) {
    return (
      <p className="aviso-enviado" role="status">
        Queda apuntado. Se mirará con este apartado delante.
      </p>
    );
  }

  if (!abierto) {
    return (
      <p className="apartado__aviso">
        <Button variant="secondary" onClick={() => setAbierto(true)} aria-label={titulo}>
          Esto está mal
        </Button>
      </p>
    );
  }

  return (
    <form
      className="aviso-form"
      aria-label={titulo}
      onSubmit={(evento) => {
        evento.preventDefault();
        envio.mutate(motivo.trim());
      }}
    >
      <label className="aviso-form__etiqueta" htmlFor={`motivo-${sectionKey}`}>
        Motivo (una línea)
      </label>
      <input
        id={`motivo-${sectionKey}`}
        className="aviso-form__campo"
        value={motivo}
        maxLength={300}
        onChange={(evento) => setMotivo(evento.target.value)}
      />
      <div className="aviso-form__acciones">
        <Button variant="primary" type="submit" disabled={motivo.trim().length === 0 || envio.isPending}>
          {envio.isPending ? 'Enviando…' : 'Enviar el aviso'}
        </Button>
        <Button
          variant="ghost"
          onClick={() => {
            setAbierto(false);
            setMotivo('');
          }}
        >
          Cancelar
        </Button>
      </div>
      {envio.isError && (
        <p className="aviso-form__error" role="alert">
          {describeError(envio.error)}
        </p>
      )}
    </form>
  );
}
