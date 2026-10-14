import { useState } from 'react';

import {
  NOTE_REPORT_STATUSES,
  NOTE_REPORT_STATUS_HELP,
  NOTE_REPORT_STATUS_LABELS,
  notesSectionHref,
  type NoteReport,
  type NoteReportStatus,
} from '../../api/notesReports';
import { StatusBadge, type StatusTone } from '../../components/StatusBadge';
import { Button } from '../../ui/Button';

/** El tono de cada estado: pendiente avisa, en curso es información, resuelto y descartado cierran. */
const TONO: Record<NoteReportStatus, StatusTone> = {
  open: 'warning',
  in_progress: 'info',
  reviewed: 'ok',
  dismissed: 'info',
};

/** El día, sin la hora: en una bandeja de texto largo la hora no cambia ninguna decisión. */
function dia(fecha: string): string {
  return fecha.slice(0, 10);
}

export interface NoteReportRowProps {
  aviso: NoteReport;
  /** Si hay una escritura en vuelo, los botones se apagan: dos despachos a la vez no tienen sentido. */
  busy: boolean;
  onDispatch: (status: NoteReportStatus, note: string) => void;
}

/**
 * Un aviso del alumno, con lo que hace falta para despacharlo sin abrir nada más.
 *
 * Lo que se enseña es lo que el propietario necesita para decidir: **dónde** (tema y apartado, con
 * el enlace al punto exacto de los apuntes), **qué** dijo el alumno (su motivo, en su texto) y
 * cuándo. Y lo que se puede hacer es lo único que el modelo tiene: los cuatro estados y la nota de
 * lo que se ha hecho, que se escribe **antes** de pulsar el estado y viaja con él en la misma
 * llamada auditada.
 *
 * La nota vive en el componente y no en la pantalla porque es de este aviso: al despachar se manda
 * lo que haya escrito y se limpia, para que el siguiente aviso no herede el texto del anterior.
 */
export function NoteReportRow({ aviso, busy, onDispatch }: NoteReportRowProps) {
  const [nota, setNota] = useState('');
  const href = notesSectionHref(aviso);
  const donde = aviso.section_title ?? null;

  return (
    <li className="avisos__fila">
      <div className="avisos__cabecera">
        <p className="avisos__origen">
          <span className="avisos__tema">{aviso.topic_code}</span>
          <span data-contenido>{aviso.topic_title}</span>
        </p>
        <StatusBadge tone={TONO[aviso.status]}>{NOTE_REPORT_STATUS_LABELS[aviso.status]}</StatusBadge>
      </div>

      <p className="avisos__apartado">
        {donde === null ? (
          <span className="avisos__apartado-perdido">
            El apartado ya no existe en los apuntes: el texto se ha reescrito debajo del aviso.
          </span>
        ) : (
          <>
            <span className="hint">Apartado</span> <span data-contenido>{donde}</span>
            {href !== null && (
              <>
                {' · '}
                <a className="avisos__enlace" href={href}>
                  Ver el apartado en los apuntes
                </a>
              </>
            )}
          </>
        )}
      </p>

      <blockquote className="avisos__motivo" data-contenido>
        {aviso.reason}
      </blockquote>

      <p className="avisos__meta hint">
        Lo mandó el alumno el {dia(aviso.created_at)}
        {aviso.reviewed_at !== null && aviso.reviewed_at !== undefined
          ? ` · lo despachaste el ${dia(aviso.reviewed_at)}`
          : ''}
      </p>

      {aviso.resolution_note !== null && aviso.resolution_note !== undefined && (
        <p className="avisos__nota">
          <span className="hint">Lo que se hizo:</span>{' '}
          <span data-contenido>{aviso.resolution_note}</span>
        </p>
      )}

      <div className="avisos__acciones">
        <label className="form__label" htmlFor={`nota-${aviso.id}`}>
          Qué has hecho (una línea, se puede dejar en blanco)
        </label>
        <input
          id={`nota-${aviso.id}`}
          className="form__input"
          type="text"
          value={nota}
          maxLength={300}
          placeholder="arreglado en la versión del 12-oct"
          onChange={(evento) => {
            setNota(evento.target.value);
          }}
        />
        <div className="avisos__botones" role="group" aria-label="Cambiar el estado del aviso">
          {NOTE_REPORT_STATUSES.map((estado) => (
            <Button
              key={estado}
              variant="secondary"
              // El estado en el que ya está no se puede volver a poner: no habría nada que cambiar y
              // dejaría un evento de auditoría diciendo que se despachó dos veces lo mismo.
              disabled={busy || aviso.status === estado}
              aria-pressed={aviso.status === estado}
              aria-label={`${NOTE_REPORT_STATUS_LABELS[estado]}: ${NOTE_REPORT_STATUS_HELP[estado]} Cambia el estado de este aviso.`}
              onClick={() => {
                onDispatch(estado, nota);
              }}
            >
              {NOTE_REPORT_STATUS_LABELS[estado]}
            </Button>
          ))}
        </div>
      </div>
    </li>
  );
}
