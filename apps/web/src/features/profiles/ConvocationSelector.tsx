import { isApiError } from '../../api/client';
import type { ConvocationReference } from '../../api/profiles';
import { useActivateConvocation, useConvocations } from '../../api/queries';
import { StatusBadge } from '../../components/StatusBadge';

export interface ConvocationSelectorProps {
  oppositionId: string;
}

/**
 * Selector de convocatoria vigente (S12.2, 07_UI-UX §5).
 *
 * Una oposición puede tener publicadas varias convocatorias —Celador tiene la de acceso libre de
 * 2022 y la de estabilización— y cada una trae su propio programa y sus propias reglas de examen.
 * Sin este selector, la aplicación solo dejaría ver la vigente y el temario de la otra quedaría
 * invisible aunque estuviera sembrado.
 *
 * Con una sola convocatoria no se pinta nada: un desplegable de una opción es ruido. Si la lista no
 * se puede leer, tampoco: el programa y sus reglas —lo importante de la pantalla— tienen su propio
 * mensaje de error y no se tapa con un control secundario roto.
 */
export function ConvocationSelector({ oppositionId }: ConvocationSelectorProps) {
  const convocations = useConvocations(oppositionId);
  const activate = useActivateConvocation();

  if (convocations.isPending || convocations.isError) {
    return null;
  }

  const filas = convocations.data;
  if (filas.length < 2) {
    return null;
  }

  const vigente = filas.find((row) => row.status === 'active') ?? null;

  return (
    <div className="selector">
      <label className="selector__label" htmlFor="selector-convocatoria">
        Convocatoria
      </label>
      <select
        id="selector-convocatoria"
        className="selector__select"
        value={vigente?.id ?? ''}
        onChange={(event) => {
          activate.mutate(event.target.value);
        }}
        disabled={activate.isPending}
      >
        {filas.map((row) => (
          <option key={row.id} value={row.id} title={row.title}>
            {etiqueta(row)}
          </option>
        ))}
      </select>
      {activate.isError && (
        <StatusBadge tone="blocked">
          {isApiError(activate.error) && activate.error.status === 409
            ? activate.error.message
            : 'no se pudo cambiar de convocatoria'}
        </StatusBadge>
      )}
      {activate.isPending && <span className="hint">Cambiando de convocatoria…</span>}
      <p className="hint">
        Al cambiar de convocatoria cambian el programa y las reglas del examen. La anterior no se
        borra: sigue disponible y se puede volver a ella.
      </p>
    </div>
  );
}

/**
 * Etiqueta corta de una convocatoria: el acto que la publica (lo que va antes de la primera coma),
 * su fecha de publicación y lo que hace falta saber para elegir —si es la vigente y si su ejercicio
 * tiene fecha—. El título completo sigue en el `title` de la opción.
 *
 * Esa segunda marca importa: una convocatoria publicada sin fecha de ejercicio está pendiente, y no
 * es lo mismo estudiar para un examen ya celebrado que para uno que todavía no se ha convocado.
 */
function etiqueta(row: ConvocationReference): string {
  if (row.status === 'active') {
    return `${etiquetaCorta(row)} · vigente`;
  }
  if (row.exam_date === null || row.exam_date === undefined) {
    return `${etiquetaCorta(row)} · sin fecha de ejercicio`;
  }
  return etiquetaCorta(row);
}

function etiquetaCorta(row: ConvocationReference): string {
  const acto = row.title.split(',')[0] ?? row.code;
  return `${acto} · ${row.published_at}`;
}
