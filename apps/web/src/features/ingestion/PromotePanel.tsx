import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import type { Representation } from '../../api/ingestion';
import { useRepresentations, usePromoteArtifacts } from '../../api/queries';
import type { PromoteArtifactsResult } from '../../api/queries';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { StatusBadge } from '../../components/StatusBadge';
import type { StatusTone } from '../../components/StatusBadge';

const QUALITY_TONE: Record<string, StatusTone> = {
  good: 'ok',
  usable_with_warnings: 'warning',
  ocr_unreviewed: 'warning',
  poor: 'blocked',
  failed: 'blocked',
};

/**
 * A partir de cuántos artefactos **no** se marca nada por defecto.
 *
 * Medido con el material real del propietario: su lote de TAI tiene **1.191 artefactos, 1.090 con
 * texto**. Marcar por defecto «todo lo que tiene texto» está bien en una carpeta de apuntes (tres o
 * cuatro ficheros que sí son documentos), pero en un lote así convierte un clic en 1.090 versiones
 * candidatas que después habría que aceptar una a una. A partir de este número no se marca nada, se
 * dice por qué y se ofrecen los botones para marcar en bloque: elegir qué es un documento es una
 * decisión de quien estudia, y a esa escala no la puede tomar la pantalla.
 */
const MAXIMO_MARCADO_POR_DEFECTO = 25;

/**
 * Pasar a la biblioteca lo que ya está en la bandeja (el paso que faltaba).
 *
 * La bandeja copia el material y saca su texto; la biblioteca lo lista, lo cita y lo deja aceptar
 * versión a versión. Entre las dos no había nada: la promoción existía en la API desde el principio
 * (`POST /documents`, ADR-009) pero **no en la interfaz**, así que el material se quedaba en la
 * bandeja y la biblioteca salía siempre vacía por mucho que se hubiera importado.
 *
 * Aquí está ese paso, y solo ese paso:
 *
 * - **Promocionar no es aceptar.** Lo que sale de aquí son versiones **candidatas**: se pueden ver,
 *   citar y marcar, pero **no cuentan para estudiar** hasta que alguien las acepta una a una en la
 *   biblioteca. Este panel no acepta nada y lo dice.
 * - **Se elige, no se promociona todo.** De una carpeta de 1.200 ficheros no todos merecen ser un
 *   documento de la biblioteca. Vienen marcadas **las que tienen texto**, que es el material que se
 *   puede leer y citar; las que no lo tienen se pueden marcar a mano (un escaneo sigue siendo un
 *   documento, aunque hoy no tenga texto).
 * - **Un artefacto, una vez.** Varias entradas pueden traer los **mismos bytes** (el mismo fichero en
 *   dos carpetas, un ZIP y su contenido): comparten representación y comparten artefacto, así que se
 *   muestran juntas y se promocionan una sola vez.
 */
export function PromotePanel({ batchId }: { batchId: string }) {
  const representations = useRepresentations(batchId);
  const promover = usePromoteArtifacts();

  //: La selección es **explícita**: `null` significa «todavía no se ha tocado» y entonces se aplica
  //: el criterio por defecto —las que tienen texto—. Guardar el conjunto ya materializado obligaba a
  //: un efecto para decidirlo cuando llegan los datos, y con el filtro quitado marcaba de más: los
  //: escaneos sin texto salían marcados sin que nadie los hubiera elegido.
  const [seleccion, setSeleccion] = useState<ReadonlySet<string> | null>(null);
  const [resultado, setResultado] = useState<PromoteArtifactsResult | null>(null);
  const [progreso, setProgreso] = useState<{ hechos: number; total: number } | null>(null);
  const [soloConTexto, setSoloConTexto] = useState(true);

  const porArtefacto = useMemo(() => {
    const mapa = new Map<string, { representation: Representation; procedencias: string[] }>();
    for (const representation of representations.data ?? []) {
      const procedencias = (representation.sources ?? []).map((source) => source.location);
      const previa = mapa.get(representation.artifact_id);
      if (previa === undefined) {
        mapa.set(representation.artifact_id, { representation, procedencias });
        continue;
      }
      // El mismo artefacto desde dos entradas: se queda el texto de mejor calidad y se suman las
      // procedencias, para no enseñar dos veces lo mismo ni perder de dónde salió.
      const ganadora = representation.char_count > previa.representation.char_count ? representation : previa.representation;
      mapa.set(representation.artifact_id, {
        representation: ganadora,
        procedencias: [...new Set([...previa.procedencias, ...procedencias])],
      });
    }
    return [...mapa.entries()];
  }, [representations.data]);

  const visibles = useMemo(
    () => porArtefacto.filter(([, dato]) => !soloConTexto || dato.representation.has_text),
    [porArtefacto, soloConTexto],
  );

  /** ¿Está marcado? Sin haber tocado nada, lo que tiene texto… salvo en un lote grande (ver arriba). */
  const marcado = (artifactId: string, dato: { representation: Representation }): boolean =>
    seleccion === null
      ? dato.representation.has_text && porArtefacto.length <= MAXIMO_MARCADO_POR_DEFECTO
      : seleccion.has(artifactId);

  const marcados = useMemo(
    () => visibles.filter(([artifactId, dato]) => marcado(artifactId, dato)).map(([artifactId]) => artifactId),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `marcado` solo depende de `seleccion` y del tamaño.
    [visibles, seleccion, porArtefacto.length],
  );

  /** Marca o desmarca uno sin perder el resto: se materializa la selección antes de cambiarla. */
  const alternar = (artifactId: string, marcar: boolean) => {
    const actual = new Set(
      seleccion ??
        porArtefacto
          .filter(([, d]) => d.representation.has_text && porArtefacto.length <= MAXIMO_MARCADO_POR_DEFECTO)
          .map(([id]) => id),
    );
    if (marcar) {
      actual.add(artifactId);
    } else {
      actual.delete(artifactId);
    }
    setSeleccion(actual);
  };

  if (representations.isPending) {
    return <LoadingState label="Consultando lo que se puede pasar a la biblioteca…" />;
  }
  if (representations.isError) {
    return (
      <ErrorState
        title="No se pudo consultar el material de este lote"
        message={
          representations.error instanceof Error
            ? representations.error.message
            : 'Error desconocido'
        }
        onRetry={() => {
          void representations.refetch();
        }}
      />
    );
  }

  const conTexto = porArtefacto.filter(([, dato]) => dato.representation.has_text).length;
  const sinTexto = porArtefacto.length - conTexto;

  return (
    <>
      <p className="hint">
        Pasar a la biblioteca crea el documento y su versión <strong>candidata</strong>: todavía no
        cuenta para estudiar. Aceptarla es el paso siguiente, y lo das tú en la biblioteca.
      </p>

      {porArtefacto.length === 0 ? (
        <p className="hint">
          Este lote no tiene artefactos con representación. Si el trabajo de copia sigue en marcha, el
          material aparece aquí al terminar.
        </p>
      ) : (
        <>
          <dl className="facts">
            <dt>Artefactos del lote</dt>
            <dd>{porArtefacto.length}</dd>
            <dt>Con texto extraído</dt>
            <dd>{conTexto}</dd>
            <dt>Sin texto (escaneos, imágenes)</dt>
            <dd>{sinTexto}</dd>
          </dl>

          {/* En un lote grande no se marca nada por defecto, y se dice por qué: marcar 1.090
              artefactos de una vez crearía 1.090 versiones que habría que aceptar una a una. */}
          {porArtefacto.length > MAXIMO_MARCADO_POR_DEFECTO && seleccion === null && (
            <p className="hint">
              Este lote trae {porArtefacto.length} artefactos, así que <strong>no hay nada marcado</strong>:
              de una carpeta así no todos son documentos de la biblioteca. Marca los que sí lo sean
              —con «Marcar los visibles» o de uno en uno— y pasa solo esos.
            </p>
          )}

          <div className="form__row">
            <label className="form__label" htmlFor="solo-con-texto">
              <input
                id="solo-con-texto"
                type="checkbox"
                checked={soloConTexto}
                onChange={(event) => {
                  setSoloConTexto(event.target.checked);
                }}
              />{' '}
              Enseñar solo los que tienen texto
            </label>
            <button
              className="button"
              type="button"
              onClick={() => {
                setSeleccion(new Set(visibles.map(([artifactId]) => artifactId)));
              }}
            >
              Marcar los visibles ({visibles.length})
            </button>
            <button
              className="button"
              type="button"
              onClick={() => {
                setSeleccion(new Set());
              }}
            >
              Desmarcar todos
            </button>
          </div>

          <table className="table">
            <caption className="table__caption">
              {visibles.length} artefacto(s) a la vista · {marcados.length} marcado(s)
            </caption>
            <thead>
              <tr>
                <th scope="col">Pasar</th>
                <th scope="col">Fichero</th>
                <th scope="col">Texto</th>
                <th scope="col">Calidad</th>
              </tr>
            </thead>
            <tbody>
              {visibles.map(([artifactId, dato]) => {
                const titulo = dato.procedencias[0] ?? artifactId;
                const otras = dato.procedencias.length - 1;
                return (
                  <tr key={artifactId}>
                    <td>
                      <input
                        type="checkbox"
                        aria-label={`Pasar a la biblioteca: ${titulo}`}
                        checked={marcado(artifactId, dato)}
                        onChange={(event) => {
                          alternar(artifactId, event.target.checked);
                        }}
                      />
                    </td>
                    <th scope="row" className="sample__path">
                      {titulo}
                      {otras > 0 && (
                        <span className="hint"> (y {otras} entrada(s) más con el mismo contenido)</span>
                      )}
                    </th>
                    <td>
                      {dato.representation.has_text ? (
                        `${dato.representation.char_count.toLocaleString('es-ES')} caracteres`
                      ) : (
                        <span className="hint">sin texto</span>
                      )}
                    </td>
                    <td>
                      <StatusBadge
                        tone={QUALITY_TONE[dato.representation.quality] ?? 'info'}
                      >
                        {dato.representation.quality}
                      </StatusBadge>
                      {dato.representation.ocr_candidate && (
                        <span className="hint"> pendiente de OCR</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          <div className="form__row">
            <button
              className="button button--primary"
              type="button"
              disabled={promover.isPending || marcados.length === 0}
              onClick={() => {
                setResultado(null);
                setProgreso({ hechos: 0, total: marcados.length });
                promover.mutate(
                  {
                    artifacts: marcados.map((artifactId) => ({ artifactId })),
                    onProgress: (hechos, total) => {
                      setProgreso({ hechos, total });
                    },
                  },
                  {
                    onSuccess: (salida) => {
                      setResultado(salida);
                      // Lo promocionado sigue estando promocionado: volver a ofrecerlo invitaría a
                      // repetir la operación. La promoción es idempotente, pero la pantalla no debe
                      // empujar a hacerla dos veces sin querer.
                      setSeleccion(new Set());
                    },
                    onSettled: () => {
                      setProgreso(null);
                    },
                  },
                );
              }}
            >
              {promover.isPending
                ? `Pasando… ${progreso?.hechos ?? 0}/${progreso?.total ?? marcados.length}`
                : `Pasar a la biblioteca (${marcados.length})`}
            </button>
            <Link className="button" to="/biblioteca">
              Ir a la biblioteca a aceptar versiones
            </Link>
          </div>

          {/* Lo que ha pasado, tal cual: cuántos documentos han salido, cuántos ya estaban (la
              promoción es idempotente) y cuáles han fallado con su motivo. Nada de «hecho» a secas. */}
          {resultado !== null && (
            <div className="status-summary" aria-live="polite">
              <StatusBadge tone={resultado.fallos.length === 0 ? 'ok' : 'warning'}>
                {resultado.creados} documento(s) nuevo(s)
              </StatusBadge>
              <span className="hint">
                {resultado.yaEstaban} ya estaban en la biblioteca (no se han duplicado)
                {resultado.fallos.length > 0 && ` · ${resultado.fallos.length} con fallo`}
              </span>
            </div>
          )}
          {resultado !== null && resultado.creados > 0 && (
            <p className="hint">
              Están en la biblioteca como <strong>versiones candidatas</strong>: se ven, pero no
              cuentan para estudiar hasta que las aceptes una a una.
            </p>
          )}
          {resultado !== null && resultado.fallos.length > 0 && (
            <ul className="issues">
              {resultado.fallos.map((fallo) => (
                <li key={fallo.artifactId} className="issues__item">
                  <StatusBadge tone="blocked">no promocionado</StatusBadge>
                  <span>{fallo.motivo}</span>
                  <span className="hint sample__path">{fallo.artifactId}</span>
                </li>
              ))}
            </ul>
          )}
          {promover.isError && (
            <ErrorState
              title="No se pudo pasar el material a la biblioteca"
              message={
                promover.error instanceof Error ? promover.error.message : 'Error desconocido'
              }
            />
          )}
        </>
      )}
    </>
  );
}
