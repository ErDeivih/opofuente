import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, type ReactNode } from 'react';

import { getPlatformPolicy } from '../api/platform';
import { setApiCredentials } from '../api/client';
import { PolicyContext } from './policyContext';

/**
 * Qué está encendido en esta instalación, preguntado **al servidor** (§8 a §11 del objetivo vivo).
 *
 * Existe por un motivo concreto y no por elegancia: la web se construye una vez y se sirve en varias
 * configuraciones —con cuentas y sin ellas, con las páginas legales y sin ellas—. Si las banderas se
 * hornearan en el paquete, probar los dos casos exigiría dos compilaciones distintas de la misma
 * aplicación, y las dos acabarían diciendo cosas diferentes. Se pregunta una vez al arrancar, se
 * guarda, y lo que diga el servidor es lo que hay.
 *
 * Los ganchos para leerla viven en `policyContext.ts`, aparte, para que este fichero exporte solo el
 * componente.
 */
export function PolicyProvider({ children }: { children: ReactNode }) {
  const consulta = useQuery({
    queryKey: ['platform-policy'],
    queryFn: getPlatformPolicy,
    // La configuración de una instalación no cambia mientras se navega: no tiene sentido volver a
    // preguntarla en cada pantalla.
    staleTime: Infinity,
    retry: 0,
  });

  const hayCuentas = consulta.data?.accounts.enabled ?? false;

  useEffect(() => {
    // La cookie de sesión viaja entre la web (otro puerto, **mismo sitio**) y la API. Con las cuentas
    // apagadas se deja como estaba —`same-origin`, que es el valor por defecto del navegador— para no
    // cambiar el comportamiento de ninguna petición de hoy.
    setApiCredentials(hayCuentas ? 'include' : 'same-origin');
  }, [hayCuentas]);

  const valor = useMemo(() => consulta.data ?? null, [consulta.data]);

  return <PolicyContext.Provider value={valor}>{children}</PolicyContext.Provider>;
}
