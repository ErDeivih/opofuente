import { Link } from 'react-router-dom';

import type { Dossier, DossierPassage, DossierSource } from '../../api/dossier';
import { holeText, mappingText, passageCitation, sourceHref, versionStatusText } from '../../api/dossier';
import { StatusBadge } from '../../components/StatusBadge';

export interface TopicDossierProps {
  dossier: Dossier;
  /** Archiva la lectura actual. */
  onArchive: () => void;
  archiving?: boolean;
  /** Lo que ha contestado el servidor al archivar: «guardada» o «ya estaba». */
  archiveMessage?: string | null;
  archiveError?: string | null;
  /** Una versión guardada se lee, no se archiva: se esconde lo que la cambiaría. */
  readOnly?: boolean;
}

/**
 * El dossier del tema (07_UI-UX §5, S13): lo que el corpus dice de este tema, **citado**.
 *
 * Tres reglas de la pantalla, y son las que la hacen honesta:
 *
 * 1. **toda frase que se enseña es una cita literal** de una fuente, con su procedencia (documento,
 *    versión y página). No hay resumen generado ni texto que no esté en el corpus: redactar necesita
 *    un modelo y no hay ninguno conectado (ADR-019);
 * 2. **lo que falta se dice**. Un tema sin material no enseña un panel vacío: enseña el hueco con su
 *    nombre y el camino para llenarlo (la bandeja). Un tema con material sin aceptar dice que lo tiene
 *    y que no se cita;
 * 3. **nada se presenta como confirmado sin serlo**: una fuente sostenida por una asignación sin
 *    confirmar lleva su etiqueta, y el repaso del conjunto lo dice también.
 */
export function TopicDossier({
  dossier,
  onArchive,
  archiving = false,
  archiveMessage = null,
  archiveError = null,
  readOnly = false,
}: TopicDossierProps) {
  const vacio = dossier.empty;

  return (
    <>
      <p className="hint">
        {vacio
          ? 'Este tema todavía no tiene nada que citar de tu material.'
          : `${String(dossier.sources_total)} ${dossier.sources_total === 1 ? 'fuente' : 'fuentes'} · ${String(dossier.passages_total)} ${dossier.passages_total === 1 ? 'pasaje citado' : 'pasajes citados'}`}
        {` · leído el ${dossier.generated_at.slice(0, 10)}`}
        {dossier.provisional && ' · con asignaciones sin confirmar'}
      </p>

      {dossier.holes.length > 0 && (
        <section aria-labelledby="dossier-huecos">
          <h3 id="dossier-huecos">Lo que falta</h3>
          <ul className="dossier__holes">
            {dossier.holes.map((hueco) => (
              <li key={`${hueco.code}-${hueco.reason ?? ''}`}>
                <StatusBadge tone={hueco.code === 'mapeo_provisional' ? 'warning' : 'info'}>
                  {hueco.code}
                </StatusBadge>{' '}
                {holeText(hueco)}
                {hueco.reason !== null && hueco.reason !== undefined && (
                  <span className="hint"> Motivo: {hueco.reason}.</span>
                )}
              </li>
            ))}
          </ul>
          {vacio && (
            <p>
              <Link className="button" to="/bandeja">
                Subir material a la bandeja
              </Link>
            </p>
          )}
        </section>
      )}

      {dossier.sources.map((fuente) => (
        <SourceBlock key={fuente.version_id} source={fuente} />
      ))}

      <section aria-labelledby="dossier-lectura">
        <h3 id="dossier-lectura">Esta lectura</h3>
        {readOnly ? (
          <p className="hint">
            Es una versión guardada: se lee, no se cambia. Para seguir el tema, vuelve a la lectura de
            hoy.
          </p>
        ) : (
          <>
            <p className="hint">
              El dossier se calcula cada vez que se abre: cuando entra material nuevo, cambia.
              Guardarlo deja una versión para poder comparar lo que sabía antes con lo que sabe ahora.
            </p>
            <p>
              <button type="button" className="button" onClick={onArchive} disabled={archiving}>
                {archiving ? 'Guardando…' : 'Guardar esta lectura'}
              </button>
            </p>
          </>
        )}
        {archiveMessage !== null && <p className="hint">{archiveMessage}</p>}
        {archiveError !== null && <p className="error">{archiveError}</p>}
      </section>
    </>
  );
}

/** Una fuente del tema: su procedencia, cómo sostiene al tema y sus pasajes citados. */
function SourceBlock({ source }: { source: DossierSource }) {
  return (
    <section className="dossier__source" aria-label={`Fuente: ${source.document_title}`}>
      <h3>
        <Link to={sourceHref(source.document_id)}>{source.document_title}</Link>
      </h3>
      <p className="hint">
        versión {source.version_label ?? 'sin etiqueta'} · {versionStatusText(source.version_status)}
        {source.quality !== null && source.quality !== undefined && ` · calidad: ${source.quality}`}
        {' · '}
        {mappingText(source.mappings, source.provisional)}
      </p>
      {source.provisional && (
        <p>
          <StatusBadge tone="warning">asignación sin confirmar</StatusBadge>{' '}
          <span className="hint">
            Esta fuente llega a este tema por una asignación que nadie ha revisado todavía.
          </span>
        </p>
      )}
      <ul className="dossier__passages">
        {source.passages.map((pasaje) => (
          <li key={pasaje.evidence_id}>
            <Passage passage={pasaje} documentTitle={source.document_title} />
          </li>
        ))}
      </ul>
    </section>
  );
}

/** Un pasaje: la cita literal, su procedencia y, si está repetido, dónde más aparece. */
function Passage({ passage, documentTitle }: { passage: DossierPassage; documentTitle: string }) {
  return (
    <>
      <p className="hint">
        {passageCitation(passage, documentTitle)}
        {passage.section_title !== null &&
          passage.section_title !== undefined &&
          ` · ${passage.section_title}`}
        {passage.quality !== null && passage.quality !== undefined && ` · ${passage.quality}`}
      </p>
      <blockquote className="reader">{passage.text}</blockquote>
      {passage.repeated_in.length > 0 && (
        <p className="hint">
          El mismo texto también está en: {passage.repeated_in.join(', ')}.
        </p>
      )}
    </>
  );
}
