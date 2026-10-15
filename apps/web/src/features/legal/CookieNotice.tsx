import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';

import { decideConsent } from '../../api/platform';
import { usePolicy } from '../../app/policy';
import { Button } from '../../ui/Button';
import { clearNonEssentialCookie, readConsent, writeConsent } from '../../lib/consent';

/**
 * El aviso de cookies (§9 del objetivo vivo).
 *
 * **Antes de decidir no se pone ninguna cookie que no sea necesaria**, y eso no lo garantiza este
 * componente: lo garantiza `lib/consent.ts`, que es la única puerta por la que se puede escribir una
 * cookie no necesaria y que no escribe nada sin permiso. Aquí solo se pregunta.
 *
 * Tres decisiones que se ven en el código:
 *
 * 1. **aceptar y rechazar son el mismo botón por dentro**: la misma llamada, el mismo tamaño, el mismo
 *    número de pulsaciones. La única diferencia es el valor de dos booleanos;
 * 2. **la decisión se guarda en una cookie propia** —la misma que lee el servidor para no contar nada
 *    sin permiso— y no en el estado del componente: quien cierre el navegador y vuelva no tiene que
 *    contestar otra vez;
 * 3. **rechazar borra lo que hubiera puesto antes**: cambiar de idea tiene que servir de algo.
 */
export function CookieNotice() {
  const politica = usePolicy();
  const cliente = useQueryClient();

  const consulta = useQuery({
    queryKey: ['consent'],
    queryFn: () => Promise.resolve(readConsent()),
    staleTime: Infinity,
  });

  const decidir = useMutation({
    mutationFn: (eleccion: { analytics: boolean; preferences: boolean }) =>
      decideConsent(eleccion),
    onSuccess: (estado) => {
      writeConsent({
        policyVersion: estado.policy_version,
        analytics: estado.analytics,
        preferences: estado.preferences,
      });
      if (!estado.preferences) {
        // Se borra la cookie de preferencias: si se rechazó, no puede quedarse lo de antes.
        clearNonEssentialCookie('opofuente_prefs');
      }
      // La decisión cambia lo que la aplicación puede hacer: se vuelve a preguntar todo lo que
      // dependa de ella.
      void cliente.invalidateQueries({ queryKey: ['consent'] });
    },
  });

  if (politica === null || !politica.legal.enabled) {
    // Sin las páginas legales no hay nada que preguntar y no se pone nada: es la configuración de
    // siempre.
    return null;
  }
  if (consulta.data !== null) {
    return null;
  }

  const decidirCon = (analytics: boolean, preferences: boolean) => {
    decidir.mutate({ analytics, preferences });
  };

  return (
    <section className="aviso-cookies" aria-labelledby="aviso-cookies-titulo">
      <div className="aviso-cookies__texto">
        <h2 className="aviso-cookies__titulo" id="aviso-cookies-titulo">
          Cookies
        </h2>
        <p>
          Antes de que decidas no se pone ninguna cookie que no sea necesaria. Las necesarias hacen que
          la aplicación funcione; las otras dos son para recordar el tamaño del texto y para contar qué
          pantallas se usan. Se estudia igual si las rechazas.
        </p>
        <p>
          <Link to="/legal/cookies">Leer la política de cookies</Link>
        </p>
      </div>
      <div className="aviso-cookies__acciones">
        <Button
          type="button"
          variant="primary"
          onClick={() => {
            decidirCon(true, true);
          }}
          disabled={decidir.isPending}
        >
          Aceptar
        </Button>
        <Button
          type="button"
          variant="secondary"
          onClick={() => {
            decidirCon(false, false);
          }}
          disabled={decidir.isPending}
        >
          Rechazar
        </Button>
      </div>
    </section>
  );
}
