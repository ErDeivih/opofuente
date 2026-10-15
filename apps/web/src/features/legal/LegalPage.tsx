import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Fragment, useState, type ReactNode } from 'react';
import { Link, useParams } from 'react-router-dom';

import {
  decideConsent,
  getCookiesDocument,
  getDataInventory,
  getLegalDocument,
  type CookiesDocument,
  type DataInventory,
} from '../../api/platform';
import { usePolicy } from '../../app/policyContext';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { describeError } from '../../features/system/labels';
import { readConsent, writeConsent } from '../../lib/consent';
import { Button } from '../../ui/Button';
import { renderInline } from '../../ui/inlineMarkdown';

/**
 * Las páginas legales (§9 del objetivo vivo): aviso legal, privacidad y cookies.
 * **El texto lo sirve el servidor**, no esta pantalla: hay una sola redacción, la que el propio
 * programa puede comprobar contra su esquema, y la pantalla no puede decir algo distinto de lo que la
 * aplicación hace. Aquí solo se pinta.
 *
 * **En la página de cookies está el control de la decisión**, con las dos casillas por separado: lo
 * necesario no se puede apagar y lo demás sí. Es el sitio donde se puede cambiar de idea, y por eso
 * está también aquí y no solo en el aviso.
 *
 * Si falta algún dato del titular (su nombre, su NIF, su contacto) se dice **arriba y con el color de
 * aviso**: es lo único de esta pantalla que no se puede inventar, y ponerlo de mentira sería peor que
 * dejar la marca a la vista.
 */
export function LegalPage() {
  const { documento } = useParams<{ documento: string }>();
  const clave = documento ?? 'aviso-legal';
  const politica = usePolicy();

  const consulta = useQuery({
    queryKey: ['legal-document', clave],
    queryFn: () => getLegalDocument(clave),
    retry: 0,
  });

  if (politica !== null && !politica.legal.enabled) {
    return (
      <>
        <h1 className="pagina__titulo">No hay páginas legales</h1>
        <p className="bloque__texto">
          Esta instalación no las tiene activadas, así que no hay nada que leer aquí.{' '}
          <Link to="/">Volver al inicio</Link>
        </p>
      </>
    );
  }

  if (consulta.isPending) {
    return <LoadingState label="Leyendo…" />;
  }
  if (consulta.isError) {
    return (
      <ErrorState
        title="No se pudo abrir la página"
        message={describeError(consulta.error)}
        onRetry={() => {
          void consulta.refetch();
        }}
      />
    );
  }

  const texto = consulta.data;

  return (
    <article className="legal">
      <header className="pagina__cabecera">
        <h1 className="pagina__titulo">{texto.title}</h1>
        <p className="pagina__entrada">{texto.summary}</p>
        {politica?.legal.owner_fields_pending && (
          <p className="legal__pendiente" role="note">
            Faltan datos del titular (nombre, NIF y contacto). Están marcados en el texto con
            «PENDIENTE» y hay que rellenarlos antes de publicar esto en internet.
          </p>
        )}
      </header>

      <Markdown text={texto.body_markdown} />

      {clave === 'cookies' && <CookiesTables />}
    </article>
  );
}

/** El markdown de los textos legales: títulos, párrafos y listas. Nada más hace falta. */
function Markdown({ text }: { text: string }) {
  const lineas = text.split('\n');
  const bloques: ReactNode[] = [];
  let lista: string[] = [];

  const cerrarLista = (indice: number) => {
    if (lista.length === 0) {
      return;
    }
    bloques.push(
      <ul key={`ul-${String(indice)}`} className="legal__lista">
        {lista.map((elemento) => (
          <li key={elemento}>{renderInline(elemento)}</li>
        ))}
      </ul>,
    );
    lista = [];
  };

  for (const [indice, linea] of lineas.entries()) {
    const limpia = linea.trimEnd();
    if (limpia.startsWith('- ')) {
      lista.push(limpia.slice(2));
      continue;
    }
    cerrarLista(indice);
    if (limpia.startsWith('### ')) {
      bloques.push(
        <h3 key={`h3-${String(indice)}`} className="legal__subtitulo">
          {renderInline(limpia.slice(4))}
        </h3>,
      );
    } else if (limpia.startsWith('## ')) {
      bloques.push(
        <h2 key={`h2-${String(indice)}`} className="legal__seccion">
          {renderInline(limpia.slice(3))}
        </h2>,
      );
    } else if (limpia.trim().length > 0) {
      bloques.push(
        <p key={`p-${String(indice)}`} className="legal__parrafo">
          {renderInline(limpia)}
        </p>,
      );
    }
  }
  cerrarLista(lineas.length);

  return <Fragment>{bloques}</Fragment>;
}

/**
 * Las dos tablas del §9: la de cookies y la de «qué datos se recogen».
 *
 * La de datos se sirve por su propia ruta (`/legal/data-inventory`) porque es la que se puede
 * **comprobar** contra el esquema; aquí se enseña entera, incluido lo que **no** se recoge, que es la
 * mitad que casi nunca se escribe.
 */
function CookiesTables() {
  const cliente = useQueryClient();
  const cookies = useQuery({ queryKey: ['legal-cookies'], queryFn: getCookiesDocument, retry: 0 });
  const inventario = useQuery({ queryKey: ['data-inventory'], queryFn: getDataInventory, retry: 0 });
  const [decision, setDecision] = useState(() => readConsent());

  const decidir = useMutation({
    mutationFn: (eleccion: { analytics: boolean; preferences: boolean }) =>
      decideConsent(eleccion),
    onSuccess: (estado) => {
      writeConsent({
        policyVersion: estado.policy_version,
        analytics: estado.analytics,
        preferences: estado.preferences,
      });
      setDecision(readConsent());
      void cliente.invalidateQueries({ queryKey: ['consent'] });
    },
  });

  if (cookies.isPending || inventario.isPending) {
    return <LoadingState label="Leyendo las tablas…" />;
  }
  if (cookies.isError || inventario.isError) {
    return (
      <ErrorState
        title="No se pudieron leer las tablas"
        message={describeError(cookies.error ?? inventario.error)}
      />
    );
  }

  return (
    <>
      <section className="bloque" aria-labelledby="mi-decision">
        <h2 className="bloque__titulo" id="mi-decision">
          Mi decisión
        </h2>
        <p className="bloque__texto">
          Las cookies necesarias no se pueden apagar: sin ellas la aplicación no funciona. Las otras
          dos se pueden elegir por separado.
        </p>
        <DecisionControls
          cookies={cookies.data}
          analytics={decision?.analytics ?? false}
          preferences={decision?.preferences ?? false}
          onDecide={(analytics, preferences) => {
            decidir.mutate({ analytics, preferences });
          }}
          pending={decidir.isPending}
        />
        {decidir.isError && (
          <ErrorState
            title="No se pudo guardar la decisión"
            message={describeError(decidir.error)}
          />
        )}
      </section>

      <CookieTable cookies={cookies.data} />
      <InventoryTable inventory={inventario.data} />
    </>
  );
}

/** Las dos casillas de la decisión, con la necesaria apagada y explicada. */
function DecisionControls({
  cookies,
  analytics,
  preferences,
  onDecide,
  pending,
}: {
  cookies: CookiesDocument;
  analytics: boolean;
  preferences: boolean;
  onDecide: (analytics: boolean, preferences: boolean) => void;
  pending: boolean;
}) {
  const [elegido, setElegido] = useState({ analytics, preferences });
  const [aviso, setAviso] = useState<string | null>(null);

  return (
    <div className="legal__decision">
      <ul className="legal__fines">
        <li>
          <label>
            <input type="checkbox" checked disabled /> Necesarias (siempre)
          </label>
        </li>
        {cookies.purposes
          .filter((fin) => fin !== 'necessary')
          .map((fin) => (
            <li key={fin}>
              <label>
                <input
                  type="checkbox"
                  checked={fin === 'analytics' ? elegido.analytics : elegido.preferences}
                  onChange={(evento) => {
                    const marcado = evento.target.checked;
                    setElegido(
                      fin === 'analytics'
                        ? { ...elegido, analytics: marcado }
                        : { ...elegido, preferences: marcado },
                    );
                  }}
                />
                {fin === 'analytics' ? 'Analítica' : 'Preferencias'}
              </label>
            </li>
          ))}
      </ul>
      <p className="acciones">
        <Button
          type="button"
          variant="primary"
          disabled={pending}
          onClick={() => {
            onDecide(elegido.analytics, elegido.preferences);
            setAviso('Guardado. Puedes cambiarlo cuando quieras.');
          }}
        >
          Guardar mi elección
        </Button>
        <Button
          type="button"
          variant="secondary"
          disabled={pending}
          onClick={() => {
            setElegido({ analytics: false, preferences: false });
            onDecide(false, false);
            setAviso('Guardado: no se pone ninguna cookie que no sea necesaria.');
          }}
        >
          Rechazar todas
        </Button>
      </p>
      {aviso !== null && <p className="legal__aviso">{aviso}</p>}
    </div>
  );
}

function CookieTable({ cookies }: { cookies: CookiesDocument }) {
  return (
    <section className="bloque" aria-labelledby="tabla-cookies">
      <h2 className="bloque__titulo" id="tabla-cookies">
        Las cookies de esta aplicación
      </h2>
      <TablaDesplazable>
        <table className="legal__tabla">
          <caption className="legal__leyenda">
            Todas las cookies que puede poner esta aplicación, con su finalidad y lo que duran. No hay
            ninguna de otro sitio.
          </caption>
          <thead>
            <tr>
              <th scope="col">Cookie</th>
              <th scope="col">Para qué</th>
              <th scope="col">¿Necesaria?</th>
              <th scope="col">Cuánto dura</th>
              <th scope="col">Quién la pone</th>
            </tr>
          </thead>
          <tbody>
            {cookies.cookies.map((cookie) => (
              <tr key={cookie.name}>
                <th scope="row">{cookie.name}</th>
                <td>{cookie.purpose}</td>
                <td>{cookie.essential ? 'Sí' : 'No'}</td>
                <td>{cookie.duration}</td>
                <td>{cookie.set_by}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TablaDesplazable>
    </section>
  );
}

/**
 * Un carril para la tabla. En pantalla estrecha **no hace falta desplazarse** (ver `global.css`: la
 * tabla se reparte el ancho y parte las palabras largas), y así no hay una zona que se desplace a la
 * que quien no usa ratón no pueda llegar. Axe lo exigía (`scrollable-region-focusable`) y eslint
 * prohíbe poner el foco en un elemento no interactivo: en vez de elegir entre los dos, se quita la
 * causa —una tabla que no cabe— y los dos quedan satisfechos.
 */
function TablaDesplazable({ children }: { children: ReactNode }) {
  return <div className="tabla-scroll">{children}</div>;
}

function InventoryTable({ inventory }: { inventory: DataInventory }) {
  return (
    <>
      <section className="bloque" aria-labelledby="tabla-datos">
        <h2 className="bloque__titulo" id="tabla-datos">
          Qué datos se recogen, para qué y cuánto tiempo
        </h2>
        <p className="bloque__texto">{inventory.notice}</p>
        <TablaDesplazable>
          <table className="legal__tabla">
            <caption className="legal__leyenda">
              Una fila por dato. «Dónde» dice en qué parte de la aplicación está, y la aplicación
              comprueba esta tabla contra su propia base de datos.
            </caption>
            <thead>
              <tr>
                <th scope="col">Qué</th>
                <th scope="col">Para qué</th>
                <th scope="col">Dónde</th>
                <th scope="col">Cuánto tiempo</th>
                <th scope="col">Con qué base</th>
              </tr>
            </thead>
            <tbody>
              {inventory.uses.map((uso) => (
                <tr key={uso.what}>
                  <th scope="row">{uso.what}</th>
                  <td>{uso.why}</td>
                  <td>{uso.where}</td>
                  <td>{uso.retention}</td>
                  <td>{uso.lawful_basis}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TablaDesplazable>
      </section>

      <section className="bloque" aria-labelledby="lo-que-no">
        <h2 className="bloque__titulo" id="lo-que-no">
          Lo que no se recoge
        </h2>
        <ul className="legal__lista">
          {inventory.not_collected.map((promesa) => (
            <li key={promesa.claim}>{promesa.claim}</li>
          ))}
        </ul>
      </section>
    </>
  );
}
