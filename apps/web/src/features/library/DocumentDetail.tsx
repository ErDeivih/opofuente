import { useRef, useState, type KeyboardEvent } from 'react';

import { isApiError } from '../../api/client';
import type { CoverageType, PromotionOutcome, Version } from '../../api/library';
import { isCandidate, isRestricted, versionName } from '../../api/library';
import {
  useAcceptVersion,
  useAssignMapping,
  useCreateSummary,
  useCurriculum,
  useDocumentDetail,
  useDocumentMappings,
  useEvidence,
  useMarkSupersedes,
  useOppositions,
  useRemoveMapping,
  useSections,
  useVersionDiff,
  useVersions,
} from '../../api/queries';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';
import { AssignmentsTab } from './AssignmentsTab';
import { MetadataTab } from './MetadataTab';
import { ReaderTab } from './ReaderTab';
import { StructureTab } from './StructureTab';
import { VersionsTab } from './VersionsTab';
import {
  authorityLabel,
  documentTypeLabel,
  OWNER_SCOPE_LABEL,
  versionStatusLabel,
  versionStatusTone,
} from './labels';

type TabId = 'lector' | 'estructura' | 'asignaciones' | 'versiones' | 'metadatos';

const TABS: readonly { id: TabId; label: string }[] = [
  { id: 'lector', label: 'Lector' },
  { id: 'estructura', label: 'Estructura' },
  { id: 'asignaciones', label: 'Asignaciones' },
  { id: 'versiones', label: 'Versiones y diff' },
  { id: 'metadatos', label: 'Metadatos' },
];

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Error desconocido';
}

/**
 * Qué contar de lo que la aplicación hizo sola al aceptar una versión (S12.5).
 *
 * Tres casos, y los tres se dicen: importó preguntas, no importó nada **y por qué**, o el servidor
 * no lo cuenta (una versión antigua del backend). Callar el tercero haría creer que no pasó nada.
 */
function describeImportacionAutomatica(resultado: PromotionOutcome): string {
  const importadas = resultado.questions_imported ?? 0;
  if (importadas > 0) {
    return `Se importaron ${String(importadas)} preguntas de este documento al banco, con su cita. Ya se pueden estudiar.`;
  }
  const motivo = resultado.questions_note ?? null;
  if (motivo === null) {
    return 'No se importaron preguntas de este documento.';
  }
  return `No se importaron preguntas: ${motivo}.`;
}

export interface DocumentDetailProps {
  documentId: string;
  onClose: () => void;
}

/**
 * Ficha del documento (07_UI-UX §6): cabecera con la versión activa, la autoridad, la vigencia, la
 * procedencia y los derechos, y las cinco pestañas de trabajo.
 *
 * Dos avisos van siempre en la cabecera, antes de cualquier pestaña: si la versión activa es una
 * **candidata** (una propuesta de cambio que nadie ha aceptado, que no es la versión buena) y si
 * sus **derechos están restringidos** (no se puede compartir). Los dos salen del servidor; la
 * pantalla no los deduce ni los suaviza.
 */
export function DocumentDetail({ documentId, onClose }: DocumentDetailProps) {
  const [tab, setTab] = useState<TabId>('lector');
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  const detail = useDocumentDetail(documentId);
  const document = detail.data?.document ?? null;
  const active = document?.active_version ?? null;
  const versionId = active?.id ?? null;

  const versions = useVersions(documentId);
  const sections = useSections(versionId);
  const evidence = useEvidence(versionId);
  const mappings = useDocumentMappings(versionId);

  const accept = useAcceptVersion();
  const supersede = useMarkSupersedes();
  // S11: un resumen extractivo de una sección. Es un derivado de verdad: depende de los fragmentos
  // de esa sección y quedará pendiente de revisar si el material cambia.
  const resumir = useCreateSummary();
  const [avisoResumen, setAvisoResumen] = useState<string | null>(null);
  // Lo que la aplicación hizo sola al aceptar una versión (S12.5): se enseña una vez y se puede
  // descartar. Se cuenta siempre —también cuando no hizo nada— porque «no hizo nada» con su motivo
  // es información: si esperabas que importara preguntas, quieres saber por qué no lo ha hecho.
  const [avisoAutomatico, setAvisoAutomatico] = useState<string | null>(null);

  /**
   * Comparación de versiones: se eligen dos y el servidor las compara (no se compara aquí nada).
   *
   * Por defecto se comparan la penúltima con la última, que es la pregunta habitual («¿qué ha
   * cambiado respecto a lo que había?»). Con una sola versión **no se pide nada**: no hay nada que
   * comparar, y la pestaña lo explica.
   */
  const [parElegido, setParElegido] = useState<{ from: string | null; to: string | null }>({
    from: null,
    to: null,
  });
  const listaVersiones: Version[] = versions.data ?? [];
  const hayComparacion = listaVersiones.length > 1;
  const anterior = hayComparacion ? listaVersiones[listaVersiones.length - 2] : null;
  const ultima = listaVersiones[listaVersiones.length - 1] ?? null;
  const diffFrom = parElegido.from ?? anterior?.id ?? null;
  const diffTo = parElegido.to ?? ultima?.id ?? null;
  const diff = useVersionDiff(
    hayComparacion ? documentId : null,
    hayComparacion ? diffFrom : null,
    hayComparacion ? diffTo : null,
  );

  /**
   * Programa al que se asignan las versiones. Sale de la convocatoria activa de una oposición: sin
   * convocatoria no hay nodos, y la pestaña lo dice en lugar de ofrecer una lista vacía.
   */
  const oppositions = useOppositions();
  const [convocatoriaElegida, setConvocatoriaElegida] = useState<string | null>(null);
  const convocatoriaActiva =
    oppositions.data?.find((opposition) => opposition.active)?.active_convocation?.id ?? null;
  const convocatoria = convocatoriaElegida ?? convocatoriaActiva;
  const curriculum = useCurriculum(convocatoria);

  const assignMapping = useAssignMapping();
  const removeMapping = useRemoveMapping();
  const falloAsignacion = assignMapping.error ?? removeMapping.error ?? null;
  const avisoAsignacion = falloAsignacion === null ? null : describeError(falloAsignacion);
  const asignando = assignMapping.isPending || removeMapping.isPending;

  const fallo = accept.error ?? supersede.error ?? null;
  const conflict = isApiError(fallo, 409) ? describeError(fallo) : null;
  const error = fallo === null || conflict !== null ? null : describeError(fallo);
  const busy = accept.isPending || supersede.isPending;

  /**
   * Navegación entre pestañas con el teclado (flechas, Inicio y Fin).
   *
   * El manejador va en cada pestaña y no en el contenedor: la pestaña es lo que tiene el foco, y
   * así el `tablist` no necesita ser enfocable para moverse por él.
   */
  function onTabKeyDown(event: KeyboardEvent<HTMLButtonElement>, actual: number) {
    let siguiente: number | null = null;
    if (event.key === 'ArrowRight') {
      siguiente = (actual + 1) % TABS.length;
    } else if (event.key === 'ArrowLeft') {
      siguiente = (actual - 1 + TABS.length) % TABS.length;
    } else if (event.key === 'Home') {
      siguiente = 0;
    } else if (event.key === 'End') {
      siguiente = TABS.length - 1;
    }
    if (siguiente === null) {
      return;
    }
    const destino = TABS[siguiente];
    if (destino === undefined) {
      return;
    }
    event.preventDefault();
    setTab(destino.id);
    refs.current[siguiente]?.focus();
  }

  if (detail.isPending) {
    return <LoadingState label="Cargando la ficha del documento…" />;
  }

  if (detail.isError || document === null) {
    return (
      <ErrorState
        title="No se pudo cargar el documento"
        message={describeError(detail.error)}
        onRetry={() => {
          void detail.refetch();
        }}
      />
    );
  }

  const candidata = active !== null && isCandidate(active);
  const restringida = active !== null && isRestricted(active);

  return (
    <>
      <header className="page__header">
        <h2>{document.canonical_title}</h2>
        <p className="hint">
          {documentTypeLabel(document.document_type)} ·{' '}
          <span className="sample__path">{document.document_type}</span>
        </p>
        <p className="form__row">
          <button className="button" type="button" onClick={onClose}>
            Volver a la lista
          </button>
        </p>
      </header>

      <dl className="facts">
        <dt>Versión activa</dt>
        <dd>
          {active === null ? (
            <span className="hint">sin versión promocionada</span>
          ) : (
            <>
              <span className="sample__path">{versionName(active)}</span>{' '}
              <StatusBadge tone={versionStatusTone(active.status)}>
                {versionStatusLabel(active.status)}
              </StatusBadge>
            </>
          )}
        </dd>
        <dt>Autoridad</dt>
        <dd>{authorityLabel(document.authority_tier)}</dd>
        <dt>Ámbito</dt>
        <dd>
          {OWNER_SCOPE_LABEL[document.owner_scope]}{' '}
          <span className="hint">{document.is_public ? 'público' : 'no público'}</span>
        </dd>
        <dt>Vigencia</dt>
        <dd>
          {active === null || active.valid_from === null || active.valid_from === undefined
            ? 'sin fecha de vigencia declarada'
            : `desde ${active.valid_from}`}
          {active !== null && active.valid_to !== null && active.valid_to !== undefined
            ? ` hasta ${active.valid_to}`
            : ''}
        </dd>
        <dt>Procedencia</dt>
        <dd>
          {active === null ? (
            'sin artefacto de origen'
          ) : (
            <>
              artefacto <span className="sample__path">{active.artifact_id}</span>
              {active.retrieved_at !== null && active.retrieved_at !== undefined && (
                <span className="hint"> · recuperado el {active.retrieved_at}</span>
              )}
            </>
          )}
        </dd>
        <dt>Derechos</dt>
        <dd>
          {active === null ? (
            'no consta'
          ) : active.rights === null || active.rights === undefined ? (
            <span className="hint">
              no constan: se tratan como desconocidos y restringidos
            </span>
          ) : (
            <>
              {active.rights.code}{' '}
              <span className="hint">
                {active.rights.license_name ?? 'sin licencia declarada'} ·{' '}
                {active.rights.sharing ? 'se puede compartir' : 'no se puede compartir'}
              </span>
            </>
          )}
        </dd>
      </dl>

      {candidata && active !== null && (
        <section className="card notice" aria-labelledby="aviso-candidata">
          <h3 id="aviso-candidata">La versión activa es una propuesta de cambio, sin aceptar</h3>
          <p>
            «{versionName(active)}» está en estado{' '}
            <strong>{versionStatusLabel(active.status)}</strong>: es la versión que la biblioteca
            enseña porque no hay ninguna aceptada, no porque sea la versión buena. Mientras nadie la
            acepte, no sostiene cobertura aceptada ni se puede citar como vigente. Se acepta en la
            pestaña «Versiones y diff».
          </p>
        </section>
      )}

      {restringida && (
        <section className="card notice" aria-labelledby="aviso-derechos">
          <h3 id="aviso-derechos">Derechos restringidos: no se puede compartir</h3>
          <p>
            {active !== null && (active.rights === null || active.rights === undefined)
              ? 'Esta versión no trae ningún registro de derechos.'
              : 'El servidor marca los derechos de esta versión como restringidos.'}{' '}
            Los derechos desconocidos se tratan como <strong>restringidos</strong>: no se puede
            compartir ni publicar el documento, y lo que se cite de él conserva su atribución y su
            procedencia.
          </p>
        </section>
      )}

      {avisoAutomatico !== null && (
        <section className="card notice" aria-labelledby="aviso-importacion-automatica">
          <h3 id="aviso-importacion-automatica">Lo que la aplicación hizo al aceptar</h3>
          <p role="note">{avisoAutomatico}</p>
        </section>
      )}

      <section className="card" aria-labelledby="ficha-documento">
        <h3 id="ficha-documento">Ficha del documento</h3>
        <div className="tabs" role="tablist" aria-label="Partes de la ficha">
          {TABS.map((item, index) => (
            <button
              key={item.id}
              ref={(element) => {
                refs.current[index] = element;
              }}
              id={`pestana-${item.id}`}
              className={item.id === tab ? 'tabs__tab tabs__tab--active' : 'tabs__tab'}
              type="button"
              role="tab"
              aria-selected={item.id === tab}
              aria-controls={`panel-${item.id}`}
              tabIndex={item.id === tab ? 0 : -1}
              onKeyDown={(event) => {
                onTabKeyDown(event, index);
              }}
              onClick={() => {
                setTab(item.id);
              }}
            >
              {item.label}
            </button>
          ))}
        </div>

        <div
          id={`panel-${tab}`}
          role="tabpanel"
          aria-labelledby={`pestana-${tab}`}
          tabIndex={-1}
          className="tabs__panel"
        >
          {tab === 'lector' && (
            <ReaderTab
              documentTitle={document.canonical_title}
              version={active}
              sections={sections.data ?? []}
              evidence={evidence.data ?? []}
              isPending={sections.isPending || evidence.isPending}
              isError={sections.isError || evidence.isError}
              onRetry={() => {
                void sections.refetch();
                void evidence.refetch();
              }}
              summarizePending={resumir.isPending}
              summarizeNotice={
                resumir.error !== null
                  ? describeError(resumir.error)
                  : avisoResumen
              }
              onSummarize={(sectionId) => {
                if (versionId === null) {
                  return;
                }
                resumir.mutate(
                  {
                    document_version_id: versionId,
                    section_ids: [sectionId],
                    title: `${document.canonical_title}: resumen de una sección`,
                  },
                  {
                    onSuccess: (resumen) => {
                      setAvisoResumen(
                        `Resumen guardado (${resumen.sections.join(', ') || 'sus secciones'}). Si el material cambia, quedará pendiente de revisar en Cambios.`,
                      );
                    },
                  },
                );
              }}
            />
          )}

          {tab === 'estructura' && (
            <StructureTab
              documentTitle={document.canonical_title}
              version={active}
              sections={sections.data ?? []}
              evidence={evidence.data ?? []}
              isPending={sections.isPending}
            />
          )}

          {tab === 'asignaciones' && (
            <AssignmentsTab
              version={active}
              versionCount={document.version_count}
              mappings={mappings.data ?? []}
              isPending={mappings.isPending}
              isError={mappings.isError}
              onRetry={() => {
                void mappings.refetch();
              }}
              oppositions={oppositions.data ?? []}
              convocationId={convocatoria}
              onConvocationChange={(id) => {
                setConvocatoriaElegida(id);
              }}
              curriculum={curriculum.data ?? null}
              curriculumIsPending={curriculum.isPending}
              onAssign={(nodeId, coverage: CoverageType) => {
                if (versionId !== null) {
                  assignMapping.mutate({
                    versionId,
                    curriculumNodeId: nodeId,
                    coverageType: coverage,
                  });
                }
              }}
              onRemove={(mappingId) => {
                removeMapping.mutate({ mappingId });
              }}
              busy={asignando}
              actionError={avisoAsignacion}
            />
          )}

          {tab === 'versiones' && (
            <VersionsTab
              documentId={documentId}
              versions={versions.data ?? []}
              busy={busy}
              conflict={conflict}
              error={error}
              isPending={versions.isPending}
              isError={versions.isError}
              onRetry={() => {
                void versions.refetch();
              }}
              onAccept={(id) => {
                accept.mutate(
                  { documentId, versionId: id },
                  {
                    onSuccess: (resultado) => {
                      setAvisoAutomatico(describeImportacionAutomatica(resultado));
                    },
                  },
                );
              }}
              onSupersede={(versionId, supersededId) => {
                supersede.mutate({ documentId, versionId, supersededId });
              }}
              fromVersionId={diffFrom}
              toVersionId={diffTo}
              onSelectFrom={(id) => {
                setParElegido({ from: id, to: diffTo });
              }}
              onSelectTo={(id) => {
                setParElegido({ from: diffFrom, to: id });
              }}
              diff={diff.data ?? null}
              diffIsPending={diff.isPending}
              diffIsError={diff.isError}
              onRetryDiff={() => {
                void diff.refetch();
              }}
            />
          )}

          {tab === 'metadatos' && <MetadataTab document={document} version={active} />}
        </div>
      </section>
    </>
  );
}
