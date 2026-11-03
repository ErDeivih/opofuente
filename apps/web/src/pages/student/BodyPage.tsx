import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';

import type { ConvocationDetail, ExamPart } from '../../api/profiles';
import { useConvocation, useOppositions } from '../../api/queries';
import { getStudentSyllabus, type StudentSyllabus } from '../../api/studentStudy';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { describeError } from '../../features/system/labels';
import { diaLegible } from '../../lib/fechas';

/**
 * La ficha del cuerpo (O2): qué es este cuerpo, qué convocatoria lo rige y qué se sabe de ella.
 *
 * Tres decisiones que se ven en el código:
 *
 * 1. **solo se enseña lo que está publicado.** Los datos salen de la oposición y de su convocatoria
 *    vigente, que ya sirve la API pública. Cuando el perfil no publica un dato llega `null` (o no
 *    llega), y aquí se dice «no consta»: no se rellena con lo que suele pasar en otras convocatorias;
 * 2. **las plazas y los requisitos no se inventan.** El perfil de esta versión no guarda esos campos,
 *    así que la ficha lo declara y enlaza a la fuente oficial. Es la verdad disponible hoy, y se
 *    corrige cuando el perfil los publique, no antes;
 * 3. **el enlace oficial va con la convocatoria, no con una dirección escrita a mano.** Si mañana se
 *    carga otra convocatoria, la ficha apunta a la suya sin tocar este fichero.
 */
export function BodyPage() {
  const { code = '' } = useParams();
  const oposiciones = useOppositions();
  const oposicion = oposiciones.data?.find(
    (candidata) => candidata.code.toLowerCase() === code.toLowerCase(),
  );
  const convocatoria = useConvocation(oposicion?.active_convocation?.id ?? null);
  const temario = useQuery({ queryKey: ['student-syllabus'], queryFn: getStudentSyllabus });

  if (oposiciones.isPending) {
    return (
      <>
        <h1 className="pagina__titulo">El cuerpo</h1>
        <LoadingState label="Buscando el cuerpo…" />
      </>
    );
  }
  if (oposiciones.isError) {
    return (
      <>
        <h1 className="pagina__titulo">El cuerpo</h1>
        <ErrorState
          title="No se pudo cargar el cuerpo"
          message={describeError(oposiciones.error)}
          onRetry={() => {
            void oposiciones.refetch();
          }}
        />
      </>
    );
  }
  if (!oposicion) {
    return (
      <>
        <h1 className="pagina__titulo">El cuerpo</h1>
        <ErrorState
          title="Ese cuerpo no está en el catálogo"
          message={`No hay ningún cuerpo con el código «${code}». El catálogo es el que sirve la aplicación; no se inventa una ficha para un código desconocido.`}
        />
        <p className="acciones">
          <Link className="ui-button ui-button--primary" to="/temario">
            Volver al temario
          </Link>
        </p>
      </>
    );
  }

  return (
    <>
      <header className="pagina__cabecera">
        <h1 className="pagina__titulo" data-contenido>
          {oposicion.name}
        </h1>
        <p className="pagina__entrada">
          <span className="ficha__codigo">{oposicion.code}</span>{' '}
          {oposicion.description ?? 'El catálogo no describe este cuerpo.'}
        </p>
      </header>

      <section className="bloque" aria-labelledby="convocatoria">
        <h2 className="bloque__titulo" id="convocatoria">
          La convocatoria
        </h2>
        <DatosDeLaConvocatoria
          consulta={convocatoria}
          hayConvocatoria={Boolean(oposicion.active_convocation)}
        />
      </section>

      <section className="bloque" aria-labelledby="requisitos">
        <h2 className="bloque__titulo" id="requisitos">
          Requisitos y plazas
        </h2>
        <p className="bloque__texto">
          El perfil de esta convocatoria no publica los requisitos de acceso ni el número de plazas,
          así que aquí no constan. No se copian de otras convocatorias: se leerán de la fuente
          oficial mientras el perfil no los sirva.
        </p>
      </section>

      <section className="bloque" aria-labelledby="ejercicios">
        <h2 className="bloque__titulo" id="ejercicios">
          Los ejercicios
        </h2>
        {convocatoria.data && convocatoria.data.parts.length > 0 ? (
          <ul className="simulacro__partes" aria-label="Ejercicios de la convocatoria">
            {convocatoria.data.parts.map((parte) => (
              <li className="simulacro__parte" key={parte.code}>
                <p className="simulacro__parte-nombre">{parte.name}</p>
                <p className="simulacro__parte-datos">{resumenDeLaParte(parte)}</p>
                {parte.structure_note !== null && parte.structure_note !== undefined && (
                  <p className="bloque__texto">{parte.structure_note}</p>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="bloque__texto">
            La convocatoria no publica la estructura de sus ejercicios en el perfil cargado, así que no
            consta.
          </p>
        )}
      </section>

      <section className="bloque" aria-labelledby="puntuacion">
        <h2 className="bloque__titulo" id="puntuacion">
          Cómo se puntúa
        </h2>
        {convocatoria.data && convocatoria.data.rules.length > 0 ? (
          <ul className="ficha__reglas" aria-label="Reglas de puntuación">
            {convocatoria.data.rules.map((regla) => (
              <li className="ficha__regla" key={regla.code}>
                <span className="ficha__valor">{regla.value_text}</span>{' '}
                <span data-contenido>{regla.description}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="bloque__texto">
            La convocatoria no publica reglas de puntuación en el perfil cargado, así que no constan.
          </p>
        )}
      </section>

      <section className="bloque" aria-labelledby="temario-del-cuerpo">
        <h2 className="bloque__titulo" id="temario-del-cuerpo">
          El temario de este cuerpo
        </h2>
        <TemarioDelCuerpo consulta={temario} codigo={oposicion.code} />
      </section>

      <p className="acciones">
        <Link className="ui-button ui-button--secondary" to="/temario">
          Ver el temario completo
        </Link>
      </p>
    </>
  );
}

/** Título, fechas, estado y enlace oficial de la convocatoria vigente del cuerpo. */
function DatosDeLaConvocatoria({
  consulta,
  hayConvocatoria,
}: {
  consulta: {
    isPending: boolean;
    isError: boolean;
    error: unknown;
    data: ConvocationDetail | undefined;
    refetch: () => unknown;
  };
  hayConvocatoria: boolean;
}) {
  if (!hayConvocatoria) {
    return (
      <p className="bloque__texto">
        Este cuerpo no tiene una convocatoria elegida para estudiar, así que no hay datos que enseñar.
        Se elige en el panel cuando la convocatoria está publicada y tiene programa.
      </p>
    );
  }
  if (consulta.isPending) {
    return <LoadingState label="Leyendo la convocatoria…" />;
  }
  if (consulta.isError) {
    return (
      <ErrorState
        title="No se pudo cargar la convocatoria"
        message={describeError(consulta.error)}
        onRetry={() => {
          void consulta.refetch();
        }}
      />
    );
  }
  const convocatoria = consulta.data;
  return (
    <>
      <p className="bloque__texto" data-contenido>
        {convocatoria.title}
      </p>
      <ul className="ficha__datos" aria-label="Datos de la convocatoria">
        <li className="ficha__dato">
          <span className="ficha__etiqueta">Publicada</span>
          <span>{diaLegible(convocatoria.published_at)}</span>
        </li>
        <li className="ficha__dato">
          <span className="ficha__etiqueta">Fecha del examen</span>
          <span>
            {convocatoria.exam_date === null || convocatoria.exam_date === undefined
              ? 'No consta'
              : diaLegible(convocatoria.exam_date)}
          </span>
        </li>
        <li className="ficha__dato">
          <span className="ficha__etiqueta">Estado</span>
          <span>{estadoDeLaConvocatoria(convocatoria.status)}</span>
        </li>
      </ul>
      {convocatoria.exam_date_note !== null && convocatoria.exam_date_note !== undefined && (
        <p className="bloque__texto">{convocatoria.exam_date_note}</p>
      )}
      <p className="acciones">
        <a
          className="ui-button ui-button--secondary"
          href={convocatoria.official_url}
          target="_blank"
          rel="noreferrer noopener"
        >
          Fuente oficial
        </a>
      </p>
      <p className="ficha__nota">
        Los requisitos y las plazas son los del texto oficial enlazado; esta ficha solo repite lo que el
        perfil cargado publica.
      </p>
    </>
  );
}

/** Cuántos bloques y temas tiene el cuerpo, y cuántas preguntas se pueden contestar hoy. */
function TemarioDelCuerpo({
  consulta,
  codigo,
}: {
  consulta: { isPending: boolean; isError: boolean; data: StudentSyllabus | undefined };
  codigo: string;
}) {
  if (consulta.isPending) {
    return <LoadingState label="Contando el temario…" />;
  }
  if (consulta.isError || !consulta.data) {
    return (
      <p className="bloque__texto">
        No se pudo leer el temario del alumno, así que no se pueden dar sus cifras. El enlace de abajo
        sigue disponible.
      </p>
    );
  }
  const temario = consulta.data;
  const esElMismoCuerpo = temario.opposition.code.toLowerCase() === codigo.toLowerCase();
  const temas = temario.blocks.reduce((total, bloque) => total + bloque.topics.length, 0);
  const preguntas = temario.blocks.reduce((total, bloque) => total + bloque.available_questions, 0);
  return (
    <>
      <p className="bloque__texto">
        {`${String(temario.blocks.length)} ${temario.blocks.length === 1 ? 'bloque' : 'bloques'} · ${String(temas)} ${temas === 1 ? 'tema' : 'temas'} · ${String(preguntas)} ${preguntas === 1 ? 'pregunta disponible' : 'preguntas disponibles'}`}
      </p>
      {!esElMismoCuerpo && (
        <p className="bloque__texto">
          {`Las cifras son del cuerpo que la aplicación tiene elegido para estudiar (${temario.opposition.name}), no de este. El temario completo se lee en su pantalla.`}
        </p>
      )}
    </>
  );
}

/** Una parte del examen en una frase; lo que no publica el perfil se dice, no se rellena. */
function resumenDeLaParte(parte: ExamPart): string {
  const piezas: string[] = [];
  if (parte.ordinary_items !== null && parte.ordinary_items !== undefined) {
    piezas.push(`${String(parte.ordinary_items)} preguntas`);
  } else {
    piezas.push('el perfil no publica cuántas preguntas tiene');
  }
  if (parte.reserve_items !== null && parte.reserve_items !== undefined) {
    piezas.push(`${String(parte.reserve_items)} de reserva`);
  }
  if (parte.time_minutes !== null && parte.time_minutes !== undefined) {
    piezas.push(`${String(parte.time_minutes)} minutos`);
  }
  if (parte.options_per_question !== null && parte.options_per_question !== undefined) {
    piezas.push(`${String(parte.options_per_question)} opciones por pregunta`);
  }
  return piezas.join(' · ');
}

/** El estado de la convocatoria en palabras; nunca «activa» a secas, que se confunde con publicada. */
function estadoDeLaConvocatoria(estado: ConvocationDetail['status']): string {
  switch (estado) {
    case 'draft':
      return 'En borrador';
    case 'active':
      return 'Vigente para estudiar';
    case 'available':
      return 'Publicada, sin elegir para estudiar';
    case 'superseded':
      return 'Sustituida por otra publicación del mismo proceso';
    case 'archived':
      return 'Archivada';
  }
}
