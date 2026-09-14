import { useOppositions, useActivateOpposition } from '../../api/queries';
import { StatusBadge } from '../../components/StatusBadge';

/**
 * Selector de oposición activa (07_UI-UX §2). Cambiar de oposición es una escritura: se envía al
 * servidor y la propia API desactiva las demás, que es donde está la restricción real.
 */
export function OppositionSelector() {
  const oppositions = useOppositions();
  const activate = useActivateOpposition();

  if (oppositions.isPending) {
    return <p className="indicators--unknown">Cargando oposiciones…</p>;
  }

  if (oppositions.isError) {
    return <p className="indicators--unknown">No se pudieron cargar las oposiciones.</p>;
  }

  if (oppositions.data.length === 0) {
    return <p className="indicators--unknown">No hay oposiciones sembradas.</p>;
  }

  const active = oppositions.data.find((item) => item.active);

  return (
    <div className="selector">
      <label className="selector__label" htmlFor="selector-oposicion">
        Oposición
      </label>
      <select
        id="selector-oposicion"
        className="selector__select"
        value={active?.id ?? ''}
        onChange={(event) => {
          activate.mutate(event.target.value);
        }}
        disabled={activate.isPending}
      >
        {oppositions.data.map((opposition) => (
          <option key={opposition.id} value={opposition.id}>
            {opposition.name}
          </option>
        ))}
      </select>
      {activate.isError && (
        <StatusBadge tone="blocked">no se pudo cambiar de oposición</StatusBadge>
      )}
    </div>
  );
}
