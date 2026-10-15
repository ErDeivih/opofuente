import { Link, NavLink } from 'react-router-dom';

import { ApiUnavailableNotice } from '../components/ApiUnavailableNotice';
import { CookieNotice } from '../features/legal/CookieNotice';
import { usePageView } from '../lib/analytics';
import { usePolicy } from './policy';
import {
  IconExamenes,
  IconFallos,
  IconInicio,
  IconProgreso,
  IconSimulacros,
  IconTemario,
  IconTests,
} from '../ui/Icons';
import { STUDENT_NAV_ITEMS } from './navigation';
import type { ReactNode } from 'react';

export interface AppShellProps {
  children: ReactNode;
}

/**
 * El marco de la **zona del alumno** (F1 del rediseño; carril y barra inferior desde F13).
 *
 * Es la zona de estudiar: siete entradas —Inicio, Temario, Tests, Simulacros, Exámenes, Fallos y
 * Progreso— y nada de la trastienda. Aquí **no** hay selector de oposición ni caja de «Buscar en el
 * corpus» ni indicadores de capacidades: eso es del panel.
 *
 * Dos formas del mismo mapa, como pide el diseño:
 *
 * - **escritorio**: carril a la izquierda con las siete entradas, icono y texto, ancho máximo de
 *   contenido 1080 px alineado a la izquierda;
 * - **móvil**: barra inferior con cinco (Inicio, Temario, Tests, Fallos y Progreso). Las dos que se
 *   caen en el móvil —Simulacros y Exámenes— siguen teniendo su dirección y se llega a ellas desde
 *   Inicio; la barra no es el único camino, es el atajo.
 *
 * Las dos listas llevan `aria-label` distinto a propósito: son dos navegaciones y un lector de
 * pantalla tiene que poder decir cuál es cuál (y las pruebas, también).
 */
export function AppShell({ children }: AppShellProps) {
  const carril = STUDENT_NAV_ITEMS;
  const barra = STUDENT_NAV_ITEMS.filter((item) => ATAJOS_MOVIL.has(item.path));
  const politica = usePolicy();
  // La analítica propia (§10): cuenta la pantalla vista. Si está apagada o no hay permiso, el
  // servidor lo rechaza y aquí no pasa nada.
  usePageView();

  return (
    <div className="marco-alumno">
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>

      <div className="marco-alumno__cuerpo">
        <aside className="carril">
          <div>
            <p className="carril__marca">
              <span className="carril__punto" aria-hidden="true" />
              <span className="carril__nombre">OpoFuente</span>
              <span className="carril__etiqueta">TAI</span>
            </p>
            <nav className="carril__navegacion" aria-label="Secciones de la aplicación">
              <ul className="carril__lista">
                {carril.map((item) => (
                  <li key={item.path}>
                    <NavLink
                      to={item.path}
                      end={item.path === '/'}
                      className={({ isActive }) =>
                        isActive ? 'carril__enlace carril__enlace--activo' : 'carril__enlace'
                      }
                    >
                      <IconoDe ruta={item.path} />
                      <span className="carril__texto">{item.label}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            </nav>
          </div>
        </aside>

        <div className="marco-alumno__columna">
          <header className="marco-alumno__cabecera">
            <span className="carril__punto" aria-hidden="true" />
            <span className="carril__nombre">OpoFuente</span>
            <span className="carril__etiqueta">TAI</span>
          </header>
          <main id="contenido" className="marco-alumno__contenido" tabIndex={-1}>
            <div className="marco-alumno__lienzo">
              <ApiUnavailableNotice />
              {children}
            </div>
          </main>
          {/*
            Una sola puerta al panel, en el pie y discreta: quitarla la escondería, y ponerla dos
            veces (en el carril y aquí) dejaría dos enlaces con el mismo nombre en la página.

            Desde S28 (§8 y §9) el pie lleva además lo que tiene que poder encontrarse **desde
            cualquier pantalla**: los textos legales y —solo si esta instalación tiene cuentas— el
            acceso. Con las cuentas apagadas no se enseña el enlace, porque no hay nada al otro lado:
            es la diferencia entre no ofrecer algo y ofrecer algo que no existe.
          */}
          <footer className="marco-alumno__pie">
            <nav aria-label="Información y cuenta">
              <ul className="pie__lista">
                {politica?.legal.enabled && (
                  <>
                    <li>
                      <Link to="/legal/aviso-legal">Aviso legal</Link>
                    </li>
                    <li>
                      <Link to="/legal/privacidad">Privacidad</Link>
                    </li>
                    <li>
                      <Link to="/legal/cookies">Cookies</Link>
                    </li>
                  </>
                )}
                {politica?.accounts.enabled && (
                  <>
                    <li>
                      <Link to="/acceso">Entrar</Link>
                    </li>
                    <li>
                      <Link to="/cuenta">Mi cuenta</Link>
                    </li>
                  </>
                )}
                <li>
                  <Link to="/admin">Administrar</Link>
                </li>
              </ul>
            </nav>
          </footer>
        </div>
      </div>

      <CookieNotice />

      <nav className="barra-inferior" aria-label="Secciones principales">
        <ul className="barra-inferior__lista">
          {barra.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  isActive
                    ? 'barra-inferior__enlace barra-inferior__enlace--activo'
                    : 'barra-inferior__enlace'
                }
              >
                <IconoDe ruta={item.path} />
                <span className="barra-inferior__texto">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}

/** Las cinco entradas que caben en la barra del móvil (diseño §1: «barra inferior con 5»). */
const ATAJOS_MOVIL: ReadonlySet<string> = new Set([
  '/',
  '/temario',
  '/tests',
  '/fallos',
  '/progreso',
]);

/** El dibujo de cada sección. Vive aquí y no en `navigation.ts` porque son componentes. */
function IconoDe({ ruta }: { ruta: string }) {
  switch (ruta) {
    case '/':
      return <IconInicio />;
    case '/temario':
      return <IconTemario />;
    case '/tests':
      return <IconTests />;
    case '/simulacros':
      return <IconSimulacros />;
    case '/examenes':
      return <IconExamenes />;
    case '/fallos':
      return <IconFallos />;
    default:
      return <IconProgreso />;
  }
}
