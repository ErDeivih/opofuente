import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { getStudentMistakes, type StudentMistake } from '../../api/studentStudy';
import { createStudentTest } from '../../api/studentTests';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { describeError } from '../../features/system/labels';
import { fechaLegible } from '../../lib/fechas';

/**
 * Los fallos (F14, paso 6 del §3 del objetivo).
 *
 * Es la lista de lo que se te resiste, y —esto es lo que la convierte en algo que se usa— **de aquí
 * sale un test**: con todos los fallos o con los de un tema.
 *
 * Dos decisiones que se ven en el código:
 *
 * 1. **el test lo compone el motor, no esta lista.** Se pide un test con el filtro de falladas y los
 *    temas que aparecen; el motor vuelve a mirar los intentos de verdad. Copiar aquí las preguntas
 *    sería tener dos verdades sobre qué está fallado, y la de la pantalla se quedaría vieja en cuanto
 *    se contestara una;
 * 2. **un fallo lleva su tema o no se puede repasar.** Una pregunta sin tema del programa sale con lo
 *    que se sabe (su enunciado, su fecha y sus fallos) pero sin botón de repaso por tema: el filtro de
 *    falladas necesita temas, y ofrecer un botón que no lleva a ninguna parte es peor que no ponerlo.
 */
export function MistakesPage() {
  const navegar = useNavigate();
  const cliente = useQueryClient();
  // `?tema=IV.7` (O2): el mismo enlace que ofrece el índice del temario. Filtra en el cliente porque
  // la API ya sirve los fallos con su tema y pedir otra vez lo mismo por tema sería gastar dos
  // lecturas para pintar una lista más corta.
  const [parametros, setParametros] = useSearchParams();
  const filtro = (parametros.get('tema') ?? '').trim();

  const consulta = useQuery({ queryKey: ['student-mistakes'], queryFn: getStudentMistakes });

  const montar = useMutation({
    mutationFn: (temas: string[]) =>
      createStudentTest({
        nodes: temas,
        count: Math.max(1, cuentaDeFallos(consulta.data?.total ?? 0)),
        filter: 'failed',
        feedback: 'immediate',
      }),
    onSuccess: (sesion) => {
      void cliente.invalidateQueries({ queryKey: ['student-overview'] });
      void navegar(`/test/${sesion.id}`);
    },
  });

  if (consulta.isPending) {
    return (
      <>
        <h1 className="pagina__titulo">Fallos</h1>
        <LoadingState label="Mirando qué se te resiste…" />
      </>
    );
  }
  if (consulta.isError) {
    return (
      <>
        <h1 className="pagina__titulo">Fallos</h1>
        <ErrorState
          title="No se pudieron cargar tus fallos"
          message={describeError(consulta.error)}
          onRetry={() => {
            void consulta.refetch();
          }}
        />
      </>
    );
  }

  const fallos = consulta.data;
  // El filtro se compara sin distinguir mayúsculas: la dirección la escribe una pantalla, pero puede
  // llegar tecleada a mano y `iv.7` es el mismo tema que `IV.7`.
  const coincide = (codigo: string) => codigo.toLowerCase() === filtro.toLowerCase();
  const temasVisibles = filtro.length === 0 ? fallos.topics : fallos.topics.filter((tema) => coincide(tema.code));
  const preguntasVisibles =
    filtro.length === 0
      ? fallos.questions
      : fallos.questions.filter((fallo) => fallo.topics.some((tema) => coincide(tema.code)));
  // Los temas con los que se puede montar el test: los de los fallos que **se pueden corregir**.
  // Montar el test con un tema cuyas preguntas falladas no tienen clave acaba en un 409, y ofrecer
  // un botón que revienta es peor que decir por qué no hay nada que montar.
  const hayAlgoQueRepasar = fallos.servable_total > 0;
  const temas = hayAlgoQueRepasar ? temasVisibles.map((tema) => tema.code) : [];
  // Con filtro y sin fallos de ese tema no hay nada que enseñar: se dice y se ofrece quitarlo, en vez
  // de dejar una pantalla vacía que parece rota.
  const vacioPorElFiltro = filtro.length > 0 && temasVisibles.length === 0;

  return (
    <>
      <header className="pagina__cabecera">
        <h1 className="pagina__titulo">Fallos</h1>
        <p className="pagina__entrada">
          {fallos.total === 0
            ? 'No tienes ninguna pregunta fallada.'
            : `${String(fallos.total)} ${fallos.total === 1 ? 'pregunta fallada' : 'preguntas falladas'} · ${String(fallos.due_total)} ${fallos.due_total === 1 ? 'para repasar hoy' : 'para repasar hoy'}`}
        </p>
        {filtro.length > 0 && (
          <p className="acciones">
            <span className="etiqueta">{`Solo el tema ${filtro}`}</span>{' '}
            <button
              type="button"
              className="ui-button ui-button--secondary"
              onClick={() => {
                setParametros({});
              }}
            >
              Quitar el filtro del tema
            </button>
          </p>
        )}
      </header>

      {vacioPorElFiltro ? (
        <section className="bloque" aria-labelledby="sin-fallos-en-el-tema">
          <h2 className="bloque__titulo" id="sin-fallos-en-el-tema">
            Sin fallos en ese tema
          </h2>
          <p className="bloque__texto">
            {`No tienes ninguna pregunta fallada del tema ${filtro}. Las demás siguen en la lista completa.`}
          </p>
          <p className="acciones">
            <button
              type="button"
              className="ui-button ui-button--primary"
              onClick={() => {
                setParametros({});
              }}
            >
              Ver todos mis fallos
            </button>
          </p>
        </section>
      ) : fallos.total === 0 ? (
        <section className="bloque" aria-labelledby="sin-fallos">
          <h2 className="bloque__titulo" id="sin-fallos">
            Sin fallos por ahora
          </h2>
          <p className="bloque__texto">
            Cuando falles una pregunta en un test, aparecerá aquí con su tema y la fecha, y podrás
            montar un test solo con ella para repasarla hasta dominarla.
          </p>
          <p className="acciones">
            <Link className="ui-button ui-button--primary" to="/temario">
              Ir al temario
            </Link>
          </p>
        </section>
      ) : (
        <>
          <p className="acciones">
            <button
              type="button"
              className="ui-button ui-button--primary"
              onClick={() => {
                montar.mutate(temas);
              }}
              disabled={montar.isPending || !hayAlgoQueRepasar || temas.length === 0}
            >
              Test con mis fallos
            </button>
          </p>
          {temasVisibles.length === 0 && (
            <p className="bloque__texto">
              Ninguna de estas preguntas está catalogada en un tema del programa, así que todavía no se
              puede montar un test con ellas. El propietario las tiene en su bandeja.
            </p>
          )}
          {temasVisibles.length > 0 && !hayAlgoQueRepasar && (
            <p className="bloque__texto">
              {`Todavía no se puede montar un test con ${fallos.total === 1 ? 'esta pregunta' : 'estas preguntas'}: no hay con qué corregirlas. Su conjunto no tiene una plantilla activa que diga la respuesta, o la que tiene no la incluye. Se arregla en el panel, y entonces vuelven.`}
            </p>
          )}

          <section className="bloque" aria-labelledby="por-tema">
            <h2 className="bloque__titulo" id="por-tema">
              Por tema
            </h2>
            <ul className="fallos__temas" aria-label="Fallos por tema">
              {temasVisibles.map((tema) => (
                <li className="fallos__tema" key={tema.code}>
                  <span className="fallos__tema-codigo">{tema.code}</span>
                  <span className="fallos__tema-titulo" data-contenido>
                    {tema.title}
                  </span>
                  <span className="fallos__tema-cifras">
                    {`${String(tema.failed)} ${tema.failed === 1 ? 'fallo' : 'fallos'}`}
                    {tema.due === 0 ? '' : ` · ${String(tema.due)} para hoy`}
                  </span>
                  <button
                    type="button"
                    className="ui-button ui-button--secondary"
                    onClick={() => {
                      montar.mutate([tema.code]);
                    }}
                    disabled={montar.isPending}
                  >
                    Solo los de {tema.code}
                  </button>
                </li>
              ))}
            </ul>
          </section>

          <section className="bloque" aria-labelledby="las-preguntas">
            <h2 className="bloque__titulo" id="las-preguntas">
              Las preguntas
            </h2>
            <ul className="fallos__preguntas" aria-label="Preguntas falladas">
              {preguntasVisibles.map((fallo) => (
                <Fallo key={`${fallo.stem}-${fallo.last_failed_at}`} fallo={fallo} />
              ))}
            </ul>
          </section>
        </>
      )}

      {montar.isError && <ErrorState title="No se pudo montar" message={describeError(montar.error)} />}
    </>
  );
}

/** Una pregunta fallada: qué decía, de qué era, cuándo y cuántas veces. */
function Fallo({ fallo }: { fallo: StudentMistake }) {
  return (
    <li className="fallos__pregunta">
      <p className="fallos__enunciado" data-contenido>
        {fallo.stem}
      </p>
      <p className="fallos__datos">
        {fallo.topics.map((tema) => (
          <Link className="fallos__etiqueta-tema" key={tema.code} to={`/temario/${tema.code}`}>
            {tema.code}
          </Link>
        ))}
        <span>{`La has fallado ${String(fallo.times_failed)} ${fallo.times_failed === 1 ? 'vez' : 'veces'}`}</span>
        <span>{fechaLegible(fallo.last_failed_at)}</span>
        {fallo.due && <span className="fallos__vence">Toca repasar</span>}
      </p>
      {fallo.topics.length > 0 && (
        <p className="acciones">
          {fallo.topics.map((tema) => (
            <Link
              className="ui-button ui-button--secondary"
              key={tema.code}
              to={`/temario/${tema.code}`}
            >
              Repasar {tema.code}
            </Link>
          ))}
        </p>
      )}
    </li>
  );
}

/** Cuántas preguntas se piden para el test de fallos: las que hay, con el tope del formulario. */
function cuentaDeFallos(total: number): number {
  return Math.min(total, 200);
}
