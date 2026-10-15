import { useState } from 'react';
import type { ReactElement } from 'react';

import type { NotesIncident, TrayAction, TraySet } from '../../api/notesIncidents';
import { conNumero } from '../../lib/plural';
import { Button } from '../../ui/Button';

/**
 * La acción en bloque, en imperativo: dice **qué va a pasar** si se pulsa.
 *
 * No se escribe aquí el porqué —eso lo manda el servidor en `/tray/actions`, junto al de la
 * categoría—, solo el verbo: dos versiones del mismo párrafo acaban diciendo cosas distintas.
 */
const ETIQUETA_DE_ACCION: Record<TrayAction, string> = {
  aceptar_derivadas: 'Aceptar todas las derivadas',
  dejar_fuera: 'Dejar fuera del estudio',
  no_son_preguntas: 'Marcar como «no son preguntas»',
};

export interface SetRowProps {
  conjunto: TraySet;
  /** Qué hace cada acción, en las palabras del servidor (`/tray/actions`). */
  ayuda: Record<string, string>;
  /** Si hay una escritura en vuelo, los botones se apagan: dos acciones a la vez no tienen sentido. */
  busy: boolean;
  /**
   * El despliegue de la fila: los avisos del examen, o `null` mientras no se han pedido.
   *
   * Lo pide la pantalla, que es quien tiene la consulta; la fila solo dice **qué** examen hay que
   * abrir. Así el estado de la carga —que puede tardar, son hasta 70 filas— vive donde se pide.
   */
  detalle: { cargando: boolean; error: boolean; incidencias: NotesIncident[] | null };
  onDesplegar: () => void;
  onBulk: (action: TrayAction) => void;
  /** Cómo se pinta un aviso dentro de la fila: es la misma fila que la de la lista. */
  renderIncidencia: (incidencia: NotesIncident) => ReactElement;
}

/**
 * Una **fila** de la bandeja: un conjunto y lo que espera dentro (F31, §2 del cierre del objetivo).
 *
 * Es la pieza que hace trabajable una bandeja de cientos de filas. La fila dice tres cosas y ninguna
 * más:
 *
 * 1. **qué conjunto es** y qué espera dentro, con el resumen que calcula el **servidor** —«50 claves
 *    sospechosas»—: el texto no se compone aquí, para que no haya dos versiones del mismo número;
 * 2. **qué se puede hacer con él de una vez**, con las acciones que el servidor dice que admite. Un
 *    conjunto oficial llega con la lista vacía y la fila **no las inventa**: la regla de qué es
 *    oficial vive en el dominio de la clave, no en la pantalla;
 * 3. **lo que tiene dentro**, al desplegarla, con las mismas filas de incidencia que la lista de
 *    abajo: una incidencia se decide igual desde su conjunto que desde la lista.
 *
 * Las propuestas se enseñan aparte de lo pendiente porque significan cosas distintas: una propuesta
 * se aprueba en bloque —no hay nada que averiguar— y lo pendiente sí espera criterio.
 */
export function SetRow({
  conjunto,
  ayuda,
  busy,
  detalle,
  onDesplegar,
  onBulk,
  renderIncidencia,
}: SetRowProps) {
  const [abierto, setAbierto] = useState(false);
  const acciones = conjunto.acciones ?? [];

  function alternar() {
    const siguiente = !abierto;
    setAbierto(siguiente);
    if (siguiente && detalle.incidencias === null && !detalle.cargando) {
      onDesplegar();
    }
  }

  return (
    <li
      className="conjunto"
      data-oficial={conjunto.official ? 'si' : 'no'}
      data-conjunto={conjunto.set_id}
    >
      <div className="conjunto__cabecera">
        <div className="conjunto__titulo">
          <h3 data-contenido>{conjunto.title}</h3>
          {/*
            El resumen lo compone el **servidor** (`TraySet.resumen`, en el dominio): «50 claves
            sospechosas». Escribirlo aquí sería tener dos versiones del mismo número, y la que se
            queda vieja es siempre la de la pantalla.
          */}
          <p className="conjunto__resumen" data-contenido>
            {conjunto.resumen}
          </p>
          <p className="conjunto__cifras">
            {conNumero(
              conjunto.total_pendiente,
              'aviso esperando criterio',
              'avisos esperando criterio',
            )}
            {conjunto.propuestas > 0 && (
              <>
                {' · '}
                {conNumero(
                  conjunto.propuestas,
                  'respuesta derivada, para aprobar en bloque',
                  'respuestas derivadas, para aprobar en bloque',
                )}
              </>
            )}
            <span className="hint">
              {conjunto.entradas_de_decision === 1
                ? ' · cuenta como una decisión tuya'
                : ` · cuenta como ${String(conjunto.entradas_de_decision)} decisiones tuyas`}
            </span>
          </p>
        </div>

        {conjunto.official && (
          <p className="conjunto__oficial">
            Examen oficial: su respuesta correcta es la que publicó la administración y no se cambia
            desde aquí. Sus incidencias las decides una a una.
          </p>
        )}

        <div
          className="conjunto__acciones"
          role="group"
          aria-label={`Qué hacer con ${conjunto.title}`}
        >
          {acciones.length === 0 ? (
            <p className="hint">Este banco no admite acciones en bloque.</p>
          ) : (
            acciones.map((accion) => (
              <Button
                key={accion}
                type="button"
                variant={accion === 'aceptar_derivadas' ? 'primary' : 'secondary'}
                disabled={busy || (accion === 'aceptar_derivadas' && conjunto.propuestas === 0)}
                title={ayuda[accion] ?? undefined}
                onClick={() => {
                  onBulk(accion);
                }}
              >
                {ETIQUETA_DE_ACCION[accion]}
                {accion === 'aceptar_derivadas' && conjunto.propuestas > 0
                  ? ` (${String(conjunto.propuestas)})`
                  : ''}
              </Button>
            ))
          )}
          <button
            type="button"
            className="button button--secondary conjunto__desplegar"
            aria-expanded={abierto}
            onClick={alternar}
          >
            {abierto ? 'Ocultar lo que tiene dentro' : 'Ver lo que tiene dentro'}
          </button>
        </div>
      </div>

      {abierto && (
        <div className="conjunto__detalle">
          {detalle.cargando && <p className="hint">Leyendo lo que hay dentro…</p>}
          {detalle.error && (
            <p className="hint">
              No se pudieron leer los avisos de este banco. Vuelve a intentarlo.
            </p>
          )}
          {detalle.incidencias !== null && detalle.incidencias.length === 0 && (
            <p className="hint">Aquí ya no queda nada esperando.</p>
          )}
          {detalle.incidencias !== null && detalle.incidencias.length > 0 && (
            <ul className="avisos" aria-label={`Avisos de ${conjunto.title}`}>
              {detalle.incidencias.map((incidencia) => renderIncidencia(incidencia))}
            </ul>
          )}
        </div>
      )}
    </li>
  );
}
