import { createContext, useContext } from 'react';

import type { PlatformPolicy } from '../api/platform';

/**
 * El contexto de la política de la instalación, **separado del componente que lo provee**.
 *
 * Está en su propio fichero por una razón mecánica y otra de fondo: el recargado en caliente de Vite
 * solo funciona en un fichero que exporta componentes, y avisa —con razón— si el mismo fichero exporta
 * además funciones; y de fondo, que un módulo que exporta un componente y cuatro ganchos invita a
 * importar el componente para usar un gancho. Aquí no hay nada que pintar: solo el contexto y cómo se
 * lee.
 *
 * **La política no decide permisos.** La puerta de las rutas de administración y el 401 de la cuenta
 * los decide el servidor; esto solo decide **qué se enseña**, que es lo único que una pantalla puede
 * decidir sin mentir.
 */
export const PolicyContext = createContext<PlatformPolicy | null>(null);

/** La política, o `null` mientras se pregunta (o si la API no contesta). */
export function usePolicy(): PlatformPolicy | null {
  return useContext(PolicyContext);
}

/** ¿Se puede estudiar sin cuenta? Siempre, y el servidor lo declara: es la regla que manda. */
export function useAnonymousStudy(): boolean {
  return usePolicy()?.accounts.anonymous_study ?? true;
}
