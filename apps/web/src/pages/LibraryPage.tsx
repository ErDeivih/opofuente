import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { isRestricted, DOCUMENT_PAGE_LIMIT } from '../api/library';
import { useDocuments } from '../api/queries';
import { EmptyState } from '../components/EmptyState';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { DocumentDetail } from '../features/library/DocumentDetail';
import { DocumentList } from '../features/library/DocumentList';
import { LibraryFilters, type RightsFilter } from '../features/library/LibraryFilters';

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/**
 * Biblioteca (07_UI-UX §6): el listado de documentos con sus filtros y la ficha del documento.
 *
 * La lista enseña la **versión activa** con su estado, y no esconde los dos avisos que importan:
 * que la versión activa sea una candidata (una propuesta de cambio sin aceptar) y que los derechos
 * estén restringidos. El estado, la criticidad y los derechos vienen del servidor: la pantalla no
 * los calcula, solo los cuenta y los pone delante.
 *
 * El documento abierto vive en la dirección (`?documento=…`), así que la ficha se puede enlazar y
 * no se pierde al recargar.
 */
export function LibraryPage() {
  const [params, setParams] = useSearchParams();
  const documentId = params.get('documento');

  const [documentType, setDocumentType] = useState('');
  const [ownerScope, setOwnerScope] = useState('');
  const [rights, setRights] = useState<RightsFilter>('todos');

  const documents = useDocuments(documentType, ownerScope);

  const visibles = useMemo(() => {
    const lista = documents.data?.documents ?? [];
    if (rights === 'todos') {
      return lista;
    }
    const restringidos = rights === 'restringidos';
    return lista.filter((document) => {
      const active = document.active_version ?? null;
      // Sin versión activa no consta ningún derecho: se cuenta como restringido, que es lo que el
      // dominio hace con lo desconocido (no hay permiso que mostrar).
      const estaRestringido = active === null || isRestricted(active);
      return estaRestringido === restringidos;
    });
  }, [documents.data, rights]);

  function abrir(id: string) {
    params.set('documento', id);
    setParams(params);
  }

  function cerrar() {
    params.delete('documento');
    setParams(params);
  }

  return (
    <>
      <header className="page__header">
        <h1>Biblioteca</h1>
        <p className="page__lead">
          Tus documentos con sus versiones, sus derechos y su procedencia. Un documento privado no
          se hace público por promocionarlo, y una versión candidata no es la versión buena hasta
          que alguien la acepta.
        </p>
      </header>

      <section className="card" aria-labelledby="filtros-biblioteca">
        <h2 id="filtros-biblioteca">Filtros</h2>
        <LibraryFilters
          documentType={documentType}
          ownerScope={ownerScope}
          rights={rights}
          onDocumentType={setDocumentType}
          onOwnerScope={setOwnerScope}
          onRights={setRights}
          onClear={() => {
            setDocumentType('');
            setOwnerScope('');
            setRights('todos');
          }}
        />
      </section>

      <section className="card" aria-labelledby="lista-biblioteca">
        <h2 id="lista-biblioteca">Documentos</h2>
        {documents.isPending && <LoadingState label="Cargando la biblioteca…" />}
        {documents.isError && (
          <ErrorState
            title="No se pudo cargar la biblioteca"
            message={describeError(documents.error)}
            onRetry={() => {
              void documents.refetch();
            }}
          />
        )}
        {documents.isSuccess &&
          (documents.data.total === 0 ? (
            <EmptyState
              title="Todavía no hay ningún documento"
              description="Un documento nace al promocionar material ya copiado: la biblioteca no crea obras."
              hint="Copia el material en la Bandeja y promociónalo: aparecerá aquí con su versión."
            />
          ) : (
            <>
              <p className="hint">
                {visibles.length} de {documents.data.total} documentos
                {rights !== 'todos' && ' (el filtro de derechos se aplica sobre lo cargado)'}
                {documents.data.total > DOCUMENT_PAGE_LIMIT &&
                  ` · se leen los primeros ${DOCUMENT_PAGE_LIMIT}`}
              </p>
              <DocumentList
                documents={visibles}
                selectedId={documentId}
                onOpen={(id) => {
                  abrir(id);
                }}
              />
            </>
          ))}
      </section>

      {documentId !== null && (
        <DocumentDetail documentId={documentId} onClose={cerrar} />
      )}
    </>
  );
}
