import { Link, NavLink } from 'react-router-dom';

import { ApiUnavailableNotice } from '../components/ApiUnavailableNotice';
import { STUDENT_NAV_ITEMS } from './navigation';
import type { ReactNode } from 'react';

export interface AppShellProps {
  children: ReactNode;
}

/**
 * El marco de la **zona del alumno** (F1 del rediseño, 6 de octubre de 2026).
 *
 * Es la zona de estudiar: siete entradas —Inicio, Temario, Tests, Simulacros, Exámenes, Fallos y
 * Progreso— y nada de la trastienda. Aquí **no** hay selector de oposición (el alumno prepara TAI y
 * punto: fijarlo es cosa de la configuración, no de esta pantalla) ni caja de «Buscar en el corpus»
 * (eso es buscar en el material, que es trabajo del panel), ni indicadores de capacidades ni
 * contadores de importaciones: todo eso se fue con el panel a `AdminShell`.
 *
 * Queda lo que sirve para estudiar y una sola salida discreta al panel, en el pie, para el
 * propietario: quitar la puerta no la esconde, la hace incómoda de encontrar a quien la necesita.
 */
export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app">
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>
      <header className="app__header">
        <div className="app__brand">
          <span className="app__brand-name">OpoFuente</span>
          <span className="app__brand-note">Preparación de TAI</span>
        </div>
      </header>
      <div className="app__body">
        <nav className="app__nav" aria-label="Secciones de la aplicación">
          <ul className="nav">
            {STUDENT_NAV_ITEMS.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) =>
                    isActive ? 'nav__link nav__link--active' : 'nav__link'
                  }
                >
                  <span className="nav__label">{item.label}</span>
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <main id="contenido" className="app__main" tabIndex={-1}>
          <ApiUnavailableNotice />
          {children}
        </main>
      </div>
      <footer className="app__footer">
        <p>
          <Link to="/admin">Administrar</Link>
        </p>
      </footer>
    </div>
  );
}
