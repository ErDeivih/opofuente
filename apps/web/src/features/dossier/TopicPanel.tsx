import { useState } from 'react';

import { fetchDossierVersion } from '../../api/dossier';
import type { Dossier } from '../../api/dossier';
import { useArchiveDossier, useDossier, useDossierVersions } from '../../api/queries';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { DossierVersionList } from './DossierVersionList';
import { TopicDossier } from './TopicDossier';

export interface TopicPanelProps {
  nodeId: string;
}

/**
 * La ficha de un tema (S13, parte 2): su dossier y su historial.
 *
 * Sustituye al «nodo seleccionado», que solo decía la ruta, la procedencia y unos recuentos. Lo que
 * se lee ahora es **el tema**: las fuentes que lo sostienen con sus pasajes citados y lo que falta.
 *
 * Dos decisiones de la pantalla:
 *
 * 1. **el dossier se pide al abrirlo**, no se cachea: se calcula desde el corpus, y una lectura vieja
 *    sería exactamente lo que esta pantalla existe para no enseñar;
 * 2. **leer una versión guardada es una acción explícita** y la pantalla dice que estás leyendo una
 *    versión anterior, con la salida a la lectura de hoy a un clic. Un histórico que se confunde con
 *    el presente es peor que no tenerlo.
 */
export function TopicPanel({ nodeId }: TopicPanelProps) {
  const dossier = useDossier(nodeId);
  const versions = useDossierVersions(nodeId);
  const archive = useArchiveDossier(nodeId);
  const [guardada, setGuardada] = useState<Dossier | null>(null);
  const [versionAbierta, setVersionAbierta] = useState<string | null>(null);
  const [cargandoVersion, setCargandoVersion] = useState(false);
  const [errorVersion, setErrorVersion] = useState<string | null>(null);
  const [mensaje, setMensaje] = useState<string | null>(null);

  if (dossier.isPending) {
    return <LoadingState label="Leyendo el tema…" />;
  }
  if (dossier.isError) {
    return (
      <ErrorState
        title="No se pudo leer el tema"
        message="El nodo ya no existe o la API no responde."
        onRetry={() => {
          void dossier.refetch();
        }}
      />
    );
  }

  const enPantalla = guardada ?? dossier.data;
  const esVersionGuardada = guardada !== null;

  const abrirVersion = (versionId: string) => {
    setCargandoVersion(true);
    setErrorVersion(null);
    void fetchDossierVersion(nodeId, versionId)
      .then((cargado) => {
        setGuardada(cargado);
        setVersionAbierta(versionId);
        setMensaje(null);
      })
      .catch((error: unknown) => {
        setErrorVersion(error instanceof Error ? error.message : 'No se pudo leer esa versión');
      })
      .finally(() => {
        setCargandoVersion(false);
      });
  };

  const volverAHoy = () => {
    setGuardada(null);
    setVersionAbierta(null);
    setErrorVersion(null);
    void dossier.refetch();
    void versions.refetch();
  };

  const archivar = () => {
    setMensaje(null);
    archive.mutate(undefined, {
      onSuccess: (resultado) => {
        setMensaje(
          resultado.created
            ? 'Lectura guardada como versión nueva.'
            : 'Esa lectura ya estaba guardada: no se ha creado otra versión.',
        );
      },
      onError: (error: unknown) => {
        setMensaje(error instanceof Error ? error.message : 'No se pudo guardar la lectura');
      },
    });
  };

  return (
    // Sin tarjeta ni encabezado propios: esto es el contenido de la ficha del tema que abre Programa,
    // y la ficha ya tiene su tarjeta y su título. Dos tarjetas anidadas se leen como dos cosas.
    <section aria-label="Dossier del tema">
      {esVersionGuardada && (
        <p className="hint">
          Estás leyendo lo que este tema decía el {enPantalla.generated_at.slice(0, 10)}: no es lo que
          dice hoy.
        </p>
      )}
      <TopicDossier
        dossier={enPantalla}
        onArchive={archivar}
        archiving={archive.isPending}
        archiveMessage={mensaje}
        archiveError={archive.isError ? 'No se pudo guardar la lectura.' : null}
        readOnly={esVersionGuardada}
      />

      <section aria-labelledby="dossier-versiones">
        <h3 id="dossier-versiones">Versiones guardadas</h3>
        {cargandoVersion && <LoadingState label="Leyendo esa versión…" />}
        {errorVersion !== null && <p className="error">{errorVersion}</p>}
        <DossierVersionList
          versions={versions.data ?? []}
          isPending={versions.isPending}
          isError={versions.isError}
          onRetry={() => {
            void versions.refetch();
          }}
          onOpen={abrirVersion}
          onShowToday={volverAHoy}
          openVersionId={versionAbierta}
        />
      </section>
    </section>
  );
}
