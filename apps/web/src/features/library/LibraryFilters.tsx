import { OWNER_SCOPES, OWNER_SCOPE_LABEL, DOCUMENT_TYPES, documentTypeLabel } from './labels';

/** Filtro de derechos: el servidor no filtra por ellos, así que se aplica sobre lo cargado. */
export type RightsFilter = 'todos' | 'restringidos' | 'reutilizables';

export interface LibraryFiltersProps {
  documentType: string;
  ownerScope: string;
  rights: RightsFilter;
  onDocumentType: (value: string) => void;
  onOwnerScope: (value: string) => void;
  onRights: (value: RightsFilter) => void;
  onClear: () => void;
}

/**
 * Filtros del listado (07_UI-UX §6).
 *
 * Tipo documental y ámbito se filtran **en el servidor** (`/documents` los admite). El de derechos
 * se aplica sobre los documentos ya cargados y se dice en la propia pantalla: la API todavía no
 * filtra por derechos, y callarlo haría creer que lo que no se ve no existe.
 */
export function LibraryFilters({
  documentType,
  ownerScope,
  rights,
  onDocumentType,
  onOwnerScope,
  onRights,
  onClear,
}: LibraryFiltersProps) {
  return (
    <div className="form">
      <div className="form__row">
        <label className="form__label" htmlFor="filtro-tipo">
          Tipo documental
        </label>
        <select
          id="filtro-tipo"
          className="selector__select"
          value={documentType}
          onChange={(event) => {
            onDocumentType(event.target.value);
          }}
        >
          <option value="">cualquier tipo</option>
          {DOCUMENT_TYPES.map((code) => (
            <option key={code} value={code}>
              {documentTypeLabel(code)}
            </option>
          ))}
        </select>

        <label className="form__label" htmlFor="filtro-ambito">
          Ámbito
        </label>
        <select
          id="filtro-ambito"
          className="selector__select"
          value={ownerScope}
          onChange={(event) => {
            onOwnerScope(event.target.value);
          }}
        >
          <option value="">cualquier ámbito</option>
          {OWNER_SCOPES.map((scope) => (
            <option key={scope} value={scope}>
              {OWNER_SCOPE_LABEL[scope]}
            </option>
          ))}
        </select>

        <label className="form__label" htmlFor="filtro-derechos">
          Derechos
        </label>
        <select
          id="filtro-derechos"
          className="selector__select"
          value={rights}
          onChange={(event) => {
            onRights(event.target.value as RightsFilter);
          }}
        >
          <option value="todos">cualquier derecho</option>
          <option value="restringidos">solo restringidos (no se pueden compartir)</option>
          <option value="reutilizables">solo con derechos revisados</option>
        </select>

        <button className="button" type="button" onClick={onClear}>
          Limpiar filtros
        </button>
      </div>
      <p className="hint">
        Tipo documental y ámbito los filtra el servidor. El de derechos se aplica sobre los
        documentos ya cargados, porque la API todavía no filtra por derechos: el recuento que se ve
        es el de esta pantalla, no el de toda la biblioteca.
      </p>
    </div>
  );
}
