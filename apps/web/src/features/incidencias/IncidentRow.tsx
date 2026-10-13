import { useState } from 'react';

import {
  INCIDENT_CATEGORY_LABELS,
  INCIDENT_REASON_LABELS,
  INCIDENT_STATUSES,
  INCIDENT_STATUS_HELP,
  INCIDENT_STATUS_LABELS,
  incidentQuestionHref,
  incidentSectionHref,
  incidentSourceHref,
  incidentVersionText,
  type IncidentStatus,
  type NotesIncident,
} from '../../api/notesIncidents';
import { StatusBadge, type StatusTone } from '../../components/StatusBadge';
import { Button } from '../../ui/Button';

/** El tono de cada estado: pendiente avisa, en curso es información, resuelta y descartada cierran. */
const TONO: Record<IncidentStatus, StatusTone> = {
  open: 'warning',
  in_progress: 'info',
  reviewed: 'ok',
  dismissed: 'info',
};

/** El día, sin la hora: en una bandeja de texto largo la hora no cambia ninguna decisión. */
function dia(fecha: string): string {
  return fecha.slice(0, 10);
}

export interface IncidentRowProps {
  incidencia: NotesIncident;
  /** Si hay una escritura en vuelo, los botones se apagan: dos despachos a la vez no tienen sentido. */
  busy: boolean;
  onDispatch: (status: IncidentStatus, note: string) => void;
}

/**
 * Una incidencia del motor, con lo que hace falta para decidir sin abrir nada más.
 *
 * Se enseña en cuatro bloques, y cada uno está por algo:
 *
 * 1. **qué es**: la categoría —quién tiene que arreglarlo—, el motivo exacto y el párrafo del dominio
 *    que dice por qué el motor la señaló (`category_help`, que lo manda el servidor: aquí no se
 *    copia). Debajo, plegado, lo que anotó la corrida;
 * 2. **lo que la provoca**: el enunciado de la pregunta, de dónde salió (su banco o su examen) y el
 *    enlace para abrirla en el banco. Si hay frase verificada, se enseña con la raya del margen: es
 *    una cita de los apuntes, no un párrafo nuestro;
 * 3. **dónde mirar**: el apartado de los apuntes, con su enlace al punto exacto del texto, y el
 *    material del que salió la clave con el estado de su versión. Cuando la pregunta no se pudo
 *    situar en ninguna materia se dice y **no** se enlaza a un ancla que no está;
 * 4. **qué se hace con ella**: los cuatro estados del dominio y la nota de lo decidido, que se
 *    escribe **antes** de pulsar y viaja con el estado en la misma llamada auditada.
 *
 * La nota vive en el componente y no en la pantalla porque es de esta incidencia: al despachar se
 * manda lo que haya escrito y se limpia, para que la siguiente no herede el texto de la anterior.
 */
export function IncidentRow({ incidencia, busy, onDispatch }: IncidentRowProps) {
  const [nota, setNota] = useState('');
  const apartadoHref = incidentSectionHref(incidencia);
  const fuentesHref = incidentSourceHref(incidencia);
  // La versión del material, dicha con lo que conste: su etiqueta («v2.1») y su estado («aceptada»,
  // «sustituida»). Una versión **sustituida** es justo lo que hay que mirar cuando la categoría es
  // «norma cambiada», así que el estado no se esconde.
  const version = [incidencia.source_version_label, incidentVersionText(incidencia.source_version_status)]
    .filter((parte): parte is string => parte !== null && parte !== undefined && parte !== '');

  return (
    <li className="avisos__fila">
      <div className="avisos__cabecera">
        <p className="avisos__origen">
          <span className="avisos__tema">{incidencia.topic_code}</span>
          <span data-contenido>{incidencia.topic_title}</span>
        </p>
        <StatusBadge tone={TONO[incidencia.status]}>
          {INCIDENT_STATUS_LABELS[incidencia.status]}
        </StatusBadge>
      </div>

      <p className="incidencias__categoria">
        {/* El nombre de la categoría es el del dominio, fijado por el §2.1.4 del objetivo: viaja como
            contenido, igual que los títulos del programa oficial en la bandeja del alumno (f16). */}
        <span className="incidencias__etiqueta" data-contenido>
          {INCIDENT_CATEGORY_LABELS[incidencia.category]}
        </span>
        <span className="hint"> · {INCIDENT_REASON_LABELS[incidencia.reason]}</span>
      </p>

      <p className="incidencias__porque" data-contenido>
        {incidencia.category_help}
      </p>

      <div className="incidencias__provoca">
        <p className="hint">La pregunta que la provoca</p>
        <blockquote className="incidencias__enunciado" data-contenido>
          {incidencia.stem}
        </blockquote>
        <p className="incidencias__origen-pregunta hint">
          De: <span data-contenido>{incidencia.set_title}</span> ·{' '}
          <a className="avisos__enlace" href={incidentQuestionHref(incidencia)}>
            Ver la pregunta en el banco
          </a>
        </p>
      </div>

      {incidencia.phrase !== null && incidencia.phrase !== undefined && (
        <blockquote className="avisos__motivo" data-contenido>
          {incidencia.phrase}
        </blockquote>
      )}

      {/*
        Una clave sospechosa **sin** la frase que la demuestra es una sospecha más débil: el motor
        vio que la letra de los apuntes no está en la clave, pero no pudo verificar la cita que lo
        sostiene. Se dice, porque cambia lo que hay que hacer: abrir la pregunta en lugar de leer la
        frase.
      */}
      {incidencia.category === 'clave_sospechosa' &&
        (incidencia.phrase === null || incidencia.phrase === undefined) && (
          <p className="incidencias__sin-frase">
            Sin la frase que lo demuestra: no se pudo verificar una cita de los apuntes para esta
            contradicción, así que hay que abrir la pregunta.
          </p>
        )}

      <p className="avisos__apartado">
        {apartadoHref === null ? (
          <span className="avisos__apartado-perdido">
            La pregunta no se pudo situar en ninguna materia del tema: no hay apartado de apuntes en
            el que contestarla, así que hay que reescribirla o asignarle un tema a mano.
          </span>
        ) : (
          <>
            <span className="hint">Apartado</span>{' '}
            <span data-contenido>{incidencia.section_title}</span>
            {apartadoHref !== null && (
              <>
                {' · '}
                <a className="avisos__enlace" href={apartadoHref}>
                  Ver el apartado en los apuntes
                </a>
              </>
            )}
          </>
        )}
      </p>

      {incidencia.source_document_title !== null &&
        incidencia.source_document_title !== undefined && (
          <p className="incidencias__origen-material hint">
            De dónde sale la respuesta correcta:{' '}
            {fuentesHref === null ? (
              <span data-contenido>{incidencia.source_document_title}</span>
            ) : (
              <a className="avisos__enlace" href={fuentesHref}>
                <span data-contenido>{incidencia.source_document_title}</span>
              </a>
            )}
            {version.length > 0 && (
              <>
                {' ('}
                <span data-contenido>{version.join(', ')}</span>
                {')'}
              </>
            )}
          </p>
        )}

      <details className="incidencias__detalle">
        <summary>Lo que anotó la corrida</summary>
        <p data-contenido>{incidencia.detail}</p>
      </details>

      <p className="avisos__meta hint">
        Lo señaló el motor el {dia(incidencia.created_at)} · {incidencia.attempts} vuelta(s) de
        comprobación
        {incidencia.reviewed_at !== null && incidencia.reviewed_at !== undefined
          ? ` · la despachaste el ${dia(incidencia.reviewed_at)}`
          : ''}
      </p>

      {incidencia.resolution_note !== null && incidencia.resolution_note !== undefined && (
        <p className="avisos__nota">
          <span className="hint">Lo que decidiste:</span>{' '}
          <span data-contenido>{incidencia.resolution_note}</span>
        </p>
      )}

      <div className="avisos__acciones">
        <label className="form__label" htmlFor={`nota-${incidencia.id}`}>
          Qué has decidido (una línea, se puede dejar en blanco)
        </label>
        <input
          id={`nota-${incidencia.id}`}
          className="form__input"
          type="text"
          value={nota}
          maxLength={300}
          placeholder="la respuesta correcta está bien: los apuntes son los que sobran"
          onChange={(evento) => {
            setNota(evento.target.value);
          }}
        />
        <div className="avisos__botones" role="group" aria-label="Cambiar el estado de la incidencia">
          {INCIDENT_STATUSES.map((estado) => (
            <Button
              key={estado}
              variant="secondary"
              // El estado en el que ya está no se puede volver a poner: no habría nada que cambiar y
              // dejaría un evento de auditoría diciendo que se despachó dos veces lo mismo.
              disabled={busy || incidencia.status === estado}
              aria-pressed={incidencia.status === estado}
              aria-label={`${INCIDENT_STATUS_LABELS[estado]}: ${INCIDENT_STATUS_HELP[estado]} Cambia el estado de esta incidencia.`}
              onClick={() => {
                onDispatch(estado, nota);
              }}
            >
              {INCIDENT_STATUS_LABELS[estado]}
            </Button>
          ))}
        </div>
      </div>
    </li>
  );
}
