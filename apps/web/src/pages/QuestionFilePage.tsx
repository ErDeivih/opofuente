import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';

import { isApiError } from '../api/client';
import { useMarkCorrectOption, useQuestionFile, useRepairQuestion } from '../api/queries';
import { ErrorState } from '../components/ErrorState';
import { LoadingState } from '../components/LoadingState';
import { QuestionFile } from '../features/preguntas/QuestionFile';
import { describeError } from '../features/system/labels';

/**
 * La ficha de una pregunta, en `/admin/preguntas?pregunta=<id>` (F20, §4.2 del objetivo).
 *
 * La dirección no es nueva: la bandeja del motor la usa desde F18 para «abrir la pregunta que
 * provoca esta incidencia» y el banco la usa para abrir una pregunta de su tabla. Lo que faltaba era
 * la pantalla: hasta ahora esa dirección caía en el banco, que **enseña** la pregunta pero no tiene
 * dónde arreglarla. Aquí sí: se cambia la respuesta correcta por la ruta auditada y se repara el
 * texto importado por la suya.
 *
 * La pregunta se elige por la **dirección** y no por un estado interno: la ficha se enlaza —«mira
 * esta»— y volver a la pantalla abre la misma. Sin `?pregunta=` no hay ficha que enseñar, y esta
 * página lo dice en vez de quedarse en blanco.
 */
export function QuestionFilePage() {
  const [params, setParams] = useSearchParams();
  const pregunta = params.get('pregunta');
  const ficha = useQuestionFile(pregunta);
  const marcar = useMarkCorrectOption();
  const reparar = useRepairQuestion();
  const [aviso, setAviso] = useState<string | null>(null);

  if (pregunta === null) {
    return (
      <ErrorState
        title="Falta la pregunta"
        message="Esta pantalla abre la ficha de **una** pregunta. Se llega desde el listado de incidencias o desde el banco de preguntas, y la dirección lleva el identificador (`?pregunta=…`)."
      />
    );
  }

  if (ficha.isPending) {
    return <LoadingState label="Leyendo la ficha de la pregunta…" />;
  }

  if (ficha.isError || ficha.data === undefined) {
    return (
      <ErrorState
        title="No se pudo leer la pregunta"
        message={describeError(ficha.error)}
        onRetry={() => {
          void ficha.refetch();
        }}
      />
    );
  }

  // El rechazo del servidor se enseña **con su motivo**: un 409 aquí no es un fallo, es la regla
  // —una respuesta correcta oficial no se cambia— y la ficha tiene que decirla, no esconderla.
  const fallo = marcar.error ?? reparar.error;
  const conflicto = isApiError(fallo, 409) ? describeError(fallo) : null;
  const error = fallo === null || conflicto !== null ? null : describeError(fallo);

  return (
    <QuestionFile
      file={ficha.data}
      busy={marcar.isPending || reparar.isPending}
      conflict={conflicto}
      error={error}
      notice={aviso}
      onMarkCorrect={({ correctOptionKeys, note }) => {
        setAviso(null);
        marcar.mutate(
          { questionId: ficha.data.question_version_id, correctOptionKeys, note },
          {
            onSuccess: (resultado) => {
              const antes = resultado.previous_option_keys
                .map((letra) => letra.toUpperCase())
                .join(', ');
              setAviso(
                `Respuesta correcta guardada: ${resultado.correct_option_keys
                  .map((letra) => letra.toUpperCase())
                  .join(', ')}` +
                  (antes === '' ? '.' : ` (antes ${antes}; la lista anterior se conserva).`) +
                  ' Queda en la auditoría con lo que había y lo que hay.',
              );
            },
          },
        );
      }}
      onRepair={({ note }) => {
        setAviso(null);
        reparar.mutate(
          { questionId: ficha.data.question_version_id, note },
          {
            onSuccess: (resultado) => {
              setAviso(
                `Reparada: se escribió la vista ${resultado.file.version_no} con ` +
                  `${resultado.reglas.length} arreglo(s), se llevaron ${resultado.moved_topics} ` +
                  `tema(s) y ${resultado.moved_anchors} enlace(s) con la pregunta y se cerraron ` +
                  `${resultado.dispatched_incidents} incidencia(s) del listado.`,
              );
              // La ficha se muda a la versión que acaba de escribir: quedarse en la sustituida
              // enseñaría la de antes —con su texto y su oferta de reparar— justo después de
              // arreglarla, y el propietario estaría mirando lo que ya no manda.
              setParams({ pregunta: resultado.new_question_version_id }, { replace: true });
            },
          },
        );
      }}
    />
  );
}
