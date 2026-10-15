import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import {
  closeAccount,
  confirmPasswordReset,
  getMe,
  loginAccount,
  logoutAccount,
  registerAccount,
  requestPasswordReset,
} from '../../api/platform';
import { ErrorState } from '../../components/ErrorState';
import { LoadingState } from '../../components/LoadingState';
import { describeError } from '../../features/system/labels';
import { Button } from '../../ui/Button';

/**
 * El acceso y el alta (§8 del objetivo vivo), en una sola pantalla.
 *
 * **Las dos mitades dicen lo mismo y no dicen de más.** El alta contesta siempre lo mismo —exista o no
 * la dirección— y por eso la pantalla no puede prometer «te hemos creado la cuenta»: dice lo que el
 * servidor dice, que es que se puede entrar. El acceso contesta lo mismo para una contraseña mala y
 * para una dirección desconocida, y la pantalla tampoco lo adivina.
 *
 * **Sin cuenta se sigue estudiando**, y se dice en la propia pantalla: si alguien llega aquí sin
 * querer, tiene que poder volver al temario sin crear nada.
 */
export function AccessPage() {
  const [modo, setModo] = useState<'entrar' | 'alta'>('entrar');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navegar = useNavigate();
  const cliente = useQueryClient();

  const entrar = useMutation({
    mutationFn: () => loginAccount(email, password),
    onSuccess: () => {
      void cliente.invalidateQueries();
      void navegar('/cuenta');
    },
  });

  const alta = useMutation({
    mutationFn: () => registerAccount(email, password),
  });

  const enviar = (evento: FormEvent) => {
    evento.preventDefault();
    if (modo === 'entrar') {
      entrar.mutate();
    } else {
      alta.mutate();
    }
  };

  return (
    <>
      <header className="pagina__cabecera">
        <h1 className="pagina__titulo">{modo === 'entrar' ? 'Entrar' : 'Crear cuenta'}</h1>
        <p className="pagina__entrada">
          La cuenta sirve para guardar tu progreso y poder verlo desde otro sitio. Para estudiar en este
          ordenador no hace falta ninguna cuenta.
        </p>
      </header>

      <form className="cuenta__formulario" onSubmit={enviar}>
        <p className="campo">
          <label htmlFor="email">Tu dirección de correo</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(evento) => {
              setEmail(evento.target.value);
            }}
          />
        </p>
        <p className="campo">
          <label htmlFor="password">Tu contraseña</label>
          <input
            id="password"
            type="password"
            autoComplete={modo === 'entrar' ? 'current-password' : 'new-password'}
            required
            minLength={1}
            value={password}
            onChange={(evento) => {
              setPassword(evento.target.value);
            }}
          />
          {modo === 'alta' && (
            <span className="campo__ayuda">
              Doce caracteres como mínimo. No puede ser tu propia dirección de correo.
            </span>
          )}
        </p>

        <p className="acciones">
          <Button type="submit" variant="primary" disabled={entrar.isPending || alta.isPending}>
            {modo === 'entrar' ? 'Entrar' : 'Crear la cuenta'}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              setModo(modo === 'entrar' ? 'alta' : 'entrar');
            }}
          >
            {modo === 'entrar' ? 'Quiero crear una cuenta' : 'Ya tengo cuenta'}
          </Button>
        </p>
      </form>

      {(entrar.isError || alta.isError) && (
        <ErrorState
          title={modo === 'entrar' ? 'No se pudo entrar' : 'No se pudo crear la cuenta'}
          message={describeError(entrar.error ?? alta.error)}
        />
      )}

      {alta.isSuccess && (
        <section className="bloque" aria-labelledby="alta-hecha">
          <h2 className="bloque__titulo" id="alta-hecha">
            {alta.data.message}
          </h2>
          <p className="bloque__texto">
            Si la dirección ya estaba registrada, no se ha creado nada nuevo: entra con la contraseña
            que ya tenías.
          </p>
          <p className="acciones">
            <Button
              type="button"
              variant="primary"
              onClick={() => {
                setModo('entrar');
              }}
            >
              Entrar ahora
            </Button>
          </p>
        </section>
      )}

      <p className="bloque__texto">
        ¿No te acuerdas de la contraseña? <Link to="/recuperar">Puedes cambiarla</Link>. También puedes{' '}
        <Link to="/temario">seguir estudiando sin cuenta</Link>.
      </p>
    </>
  );
}

/**
 * La recuperación (§8): pedir el enlace y usarlo.
 *
 * Aquí se ve de frente el hueco que este bloque **no** tapa: no hay ningún servicio de correo
 * contratado, así que el enlace no se manda a ninguna parte —queda en el equipo del titular— y la
 * pantalla lo dice en vez de prometer un mensaje que no va a llegar.
 */
export function RecoverPage() {
  const [email, setEmail] = useState('');
  const [token, setToken] = useState('');
  const [password, setPassword] = useState('');
  const [hecho, setHecho] = useState<string | null>(null);

  const pedir = useMutation({
    mutationFn: () => requestPasswordReset(email),
    onSuccess: (respuesta) => {
      setHecho(respuesta.message);
    },
  });
  const confirmar = useMutation({
    mutationFn: () => confirmPasswordReset(tokenDeEnlace(token), password),
    onSuccess: () => {
      setHecho('Contraseña cambiada. Ya puedes entrar con ella; las demás sesiones se han cerrado.');
    },
  });

  return (
    <>
      <header className="pagina__cabecera">
        <h1 className="pagina__titulo">Cambiar la contraseña</h1>
        <p className="pagina__entrada">
          Esta instalación no manda correos. El enlace queda en el equipo del titular, y él te lo pasa.
        </p>
      </header>

      <form
        className="cuenta__formulario"
        onSubmit={(evento) => {
          evento.preventDefault();
          pedir.mutate();
        }}
      >
        <p className="campo">
          <label htmlFor="recuperar-email">Tu dirección de correo</label>
          <input
            id="recuperar-email"
            type="email"
            required
            value={email}
            onChange={(evento) => {
              setEmail(evento.target.value);
            }}
          />
        </p>
        <p className="acciones">
          <Button type="submit" variant="primary" disabled={pedir.isPending}>
            Pedir el enlace
          </Button>
        </p>
      </form>

      {pedir.isError && (
        <ErrorState title="No se pudo pedir" message={describeError(pedir.error)} />
      )}

      <form
        className="cuenta__formulario"
        onSubmit={(evento) => {
          evento.preventDefault();
          confirmar.mutate();
        }}
      >
        <p className="campo">
          <label htmlFor="recuperar-token">El enlace que te han pasado</label>
          <input
            id="recuperar-token"
            type="text"
            required
            value={token}
            onChange={(evento) => {
              setToken(evento.target.value);
            }}
          />
          <span className="campo__ayuda">
            Pega el enlace entero o solo la parte que va después de «token=».
          </span>
        </p>
        <p className="campo">
          <label htmlFor="recuperar-password">La contraseña nueva</label>
          <input
            id="recuperar-password"
            type="password"
            autoComplete="new-password"
            required
            value={password}
            onChange={(evento) => {
              setPassword(evento.target.value);
            }}
          />
        </p>
        <p className="acciones">
          <Button type="submit" variant="primary" disabled={confirmar.isPending}>
            Cambiar la contraseña
          </Button>
        </p>
      </form>

      {confirmar.isError && (
        <ErrorState title="No se pudo cambiar" message={describeError(confirmar.error)} />
      )}

      {hecho !== null && (
        <section className="bloque" aria-labelledby="recuperar-hecho">
          <h2 className="bloque__titulo" id="recuperar-hecho">
            {hecho}
          </h2>
          <p className="acciones">
            <Link className="ui-button ui-button--primary" to="/acceso">
              Ir a entrar
            </Link>
          </p>
        </section>
      )}
    </>
  );
}

/** Mi cuenta: quién soy, mis sesiones abiertas y la baja. */
export function AccountPage() {
  const cliente = useQueryClient();
  const navegar = useNavigate();
  const consulta = useQuery({ queryKey: ['account-me'], queryFn: getMe, retry: 0 });

  const salir = useMutation({
    mutationFn: logoutAccount,
    onSuccess: () => {
      void cliente.invalidateQueries();
      void navegar('/');
    },
  });
  const baja = useMutation({
    mutationFn: closeAccount,
    onSuccess: () => {
      void cliente.invalidateQueries();
      void navegar('/');
    },
  });

  if (consulta.isPending) {
    return <LoadingState label="Mirando tu cuenta…" />;
  }
  if (consulta.isError) {
    return (
      <ErrorState
        title="No se pudo leer tu cuenta"
        message={describeError(consulta.error)}
        onRetry={() => {
          void consulta.refetch();
        }}
      />
    );
  }

  const cuenta = consulta.data;
  const eventos = cuenta.events;

  return (
    <>
      <header className="pagina__cabecera">
        <h1 className="pagina__titulo">Mi cuenta</h1>
        <p className="pagina__entrada">
          {cuenta.account.email} · esta sesión dura hasta el{' '}
          {new Date(cuenta.session_expires_at).toLocaleDateString('es-ES')}
        </p>
      </header>

      <section className="bloque" aria-labelledby="lo-que-ha-pasado">
        <h2 className="bloque__titulo" id="lo-que-ha-pasado">
          Lo que ha pasado con tu cuenta
        </h2>
        <ul className="cuenta__eventos">
          {eventos.map((evento) => (
            <li key={`${evento.kind}-${evento.occurred_at}`}>
              <span>{etiquetaDeEvento(evento.kind)}</span>
              <time dateTime={evento.occurred_at}>
                {new Date(evento.occurred_at).toLocaleString('es-ES')}
              </time>
            </li>
          ))}
        </ul>
      </section>

      <section className="bloque" aria-labelledby="cerrar">
        <h2 className="bloque__titulo" id="cerrar">
          Cerrar la sesión o la cuenta
        </h2>
        <p className="bloque__texto">
          Cerrar la sesión te saca de este navegador. Cerrar la cuenta borra la cuenta, sus sesiones y
          tu progreso, y no se puede deshacer.
        </p>
        <p className="acciones">
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              salir.mutate();
            }}
            disabled={salir.isPending}
          >
            Cerrar la sesión
          </Button>
          <Button
            type="button"
            variant="ghost"
            onClick={() => {
              baja.mutate();
            }}
            disabled={baja.isPending}
          >
            Cerrar mi cuenta y borrar mis datos
          </Button>
        </p>
        {baja.isSuccess && (
          <p className="legal__aviso" role="status">
            Cuenta cerrada: {String(baja.data.study_rows)} filas de progreso y{' '}
            {String(baja.data.sessions)} sesiones borradas.
          </p>
        )}
        {(salir.isError || baja.isError) && (
          <ErrorState
            title="No se pudo hacer"
            message={describeError(salir.error ?? baja.error)}
          />
        )}
      </section>

      <p className="bloque__texto">
        <Link to="/legal/privacidad">Qué datos se recogen y cuánto tiempo se guardan</Link>
      </p>
    </>
  );
}

/**
 * El nombre legible de un movimiento auditado. El servidor manda el código; la frase la pone aquí.
 */
function tokenDeEnlace(pegado: string): string {
  const limpio = pegado.trim();
  const marca = 'token=';
  const posicion = limpio.indexOf(marca);
  if (posicion < 0) {
    return limpio;
  }
  // Se acepta el enlace entero o solo el testigo: quien lo copia del fichero del titular suele
  // copiar la línea completa, y obligarle a recortarla a mano sería una tontería.
  return limpio.slice(posicion + marca.length).split('&')[0]?.trim() ?? limpio;
}

function etiquetaDeEvento(kind: string): string {  switch (kind) {
    case 'account.registered':
      return 'Se creó la cuenta';
    case 'account.login':
      return 'Entraste';
    case 'account.login_failed':
      return 'Alguien intentó entrar y no pudo';
    case 'account.login_throttled':
      return 'Se frenaron los intentos seguidos';
    case 'account.logout':
      return 'Cerraste la sesión';
    case 'account.password_reset_requested':
      return 'Se pidió cambiar la contraseña';
    case 'account.password_reset_completed':
      return 'Se cambió la contraseña';
    case 'account.closed':
      return 'Se cerró la cuenta';
    default:
      return kind;
  }
}
