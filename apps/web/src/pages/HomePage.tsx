import { Link } from 'react-router-dom';

import { LoadingState } from '../components/LoadingState';
import { useMastery, useOppositions, useReviewQueue, useStudySessions } from '../api/queries';
import { modeLabel } from '../features/study/labels';
import { Card, EmptyState, StatTile } from '../ui/Card';
import { ProgressBar } from '../ui/Progress';

/**
 * Inicio del alumno (F1 del rediseño, 6 de octubre de 2026).
 *
 * Enseña tres cosas y solo tres: **seguir donde lo dejaste**, **repasar lo que fallaste** y **cómo
 * vas**. Nada de la trastienda: ni contadores de importaciones, ni lo que espera una decisión de
 * revisión, ni de dónde sale cada pregunta, ni el estado del sistema. Eso se fue con el panel a
 * `/admin`, que es donde se administra.
 *
 * Todo lo que se ve es dato real del servidor: si no hay sesión a medias, lo dice; si no hay fallos
 * vencidos, lo dice; y sin intentos no se inventa un progreso. Un hueco sin datos es una frase
 * honesta, no un cero disfrazado de gráfico.
 */
export function HomePage() {
  const oppositions = useOppositions();
  const active = oppositions.data?.find((opposition) => opposition.active) ?? null;
  const sessions = useStudySessions(active?.id ?? null);
  const repaso = useReviewQueue(active?.id ?? null);
  const mastery = useMastery(active?.id ?? null);

  const enMarcha = sessions.data?.sessions.find((sesion) => sesion.status === 'running') ?? null;
  const ultima = sessions.data?.sessions[0] ?? null;
  const vencidos = repaso.data?.stats.due ?? 0;
  const conDatos = mastery.data?.nodes_with_estimate ?? 0;
  const totalTemas = mastery.data?.nodes_total ?? 0;

  return (
    <div style={{ display: 'grid', gap: 'var(--s5)' }}>
      <header className="page__header">
        <h1>Inicio</h1>
        <p className="page__lead">
          Lo que toca hoy: seguir el test que dejaste a medias y repasar lo que fallaste.
        </p>
      </header>

      <Card title="Continuar">
        {sessions.isPending && <LoadingState label="Mirando tus tests…" />}
        {sessions.isError && (
          <EmptyState message="No se pudieron cargar tus tests: la aplicación no responde." />
        )}
        {sessions.isSuccess && enMarcha !== null && (
          <>
            <StatTile
              label="Preguntas contestadas"
              value={`${String(enMarcha.answered_questions)} de ${String(enMarcha.total_questions)}`}
              hint={modeLabel(enMarcha.mode)}
            />
            <p style={{ marginTop: 'var(--s4)' }}>
              <Link className="ui-button ui-button--primary" to="/tests">
                Continuar el test
              </Link>
            </p>
          </>
        )}
        {sessions.isSuccess && enMarcha === null && (
          <EmptyState
            message={
              ultima === null
                ? 'Aún no has hecho ningún test.'
                : 'No tienes ningún test a medias.'
            }
            action={
              <Link className="ui-button ui-button--primary" to="/tests">
                Empezar un test
              </Link>
            }
          />
        )}
      </Card>

      <Card title="Repasar fallos">
        {repaso.isPending && <LoadingState label="Mirando lo que fallaste…" />}
        {repaso.isError && (
          <EmptyState message="No se pudieron cargar tus fallos: la aplicación no responde." />
        )}
        {repaso.isSuccess && vencidos > 0 && (
          <>
            <StatTile
              label="Preguntas para repasar hoy"
              value={vencidos}
              hint="De las que has fallado y ya toca volver a ver."
            />
            <p style={{ marginTop: 'var(--s4)' }}>
              <Link className="ui-button ui-button--primary" to="/fallos">
                Repasar mis fallos
              </Link>
            </p>
          </>
        )}
        {repaso.isSuccess && vencidos === 0 && (
          <EmptyState message="No tienes fallos pendientes de repaso." />
        )}
      </Card>

      <Card title="Tu progreso">
        {mastery.isPending && <LoadingState label="Contando lo que llevas…" />}
        {mastery.isError && (
          <EmptyState message="No se pudo cargar tu progreso: la aplicación no responde." />
        )}
        {mastery.isSuccess && totalTemas > 0 && (
          <>
            <StatTile
              label="Temas con datos suficientes"
              value={`${String(conDatos)} de ${String(totalTemas)}`}
            />
            <div style={{ marginTop: 'var(--s4)' }}>
              <ProgressBar
                percent={Math.round((conDatos / totalTemas) * 100)}
                label="Temas ya practicados"
              />
            </div>
            <p style={{ marginTop: 'var(--s4)' }}>
              <Link className="ui-button ui-button--secondary" to="/progreso">
                Ver mi progreso
              </Link>
            </p>
          </>
        )}
        {mastery.isSuccess && totalTemas === 0 && (
          <EmptyState message="Todavía no hay progreso que enseñar: aparece al hacer tu primer test." />
        )}
      </Card>
    </div>
  );
}
