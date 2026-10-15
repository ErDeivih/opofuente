import { useQuery } from '@tanstack/react-query';
import { createContext, useContext, useEffect, useMemo, type ReactNode } from 'react';

import { getPlatformPolicy, type PlatformPolicy } from '../api/platform';
import { setApiCredentials } from '../api/client';

/**
 * Qué está encendido en esta instalación, preguntado **al servidor** (§8 a §11).
 *
 * Existe por un motivo concreto y no por elegancia: la web se construye una vez y se sirve en varias
 * configuraciones —con cuentas y sin ellas, con las páginas legales y sin ellas—. Si las banderas se
 * hornearan en el paquete, probar los dos casos exigiría dos compilaciones distintas de la misma
 * aplicación, y las dos acabarían diciendo cosas diferentes. Se pregunta una vez al arrancar, se
 * guarda, y lo que diga el servidor es lo que hay.
 *
 * **La política no decide permisos**: la puerta de las rutas de administración y el 401 de la cuenta
 * los decide el servidor. Esto solo decide **qué se enseña**, que es lo único que una pantalla puede
 * decidir sin mentir.
 */
const PolicyContext = createContext<PlatformPolicy | null>(null);

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

/** La política, o `null` mientras se pregunta (o si la API no contesta). */
export function usePolicy(): PlatformPolicy | null {
  return useContext(PolicyContext);
}

/** ¿Se puede estudiar sin cuenta? Siempre, y el servidor lo declara: es la regla que manda. */
export function useAnonymousStudy(): boolean {
  return usePolicy()?.accounts.anonymous_study ?? true;
}
