import { NavLink } from 'react-router-dom';

import { OppositionSelector } from '../features/profiles/OppositionSelector';
import { SystemIndicators } from '../features/system/SystemIndicators';
import { NAV_ITEMS } from './navigation';
import type { ReactNode } from 'react';

export interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app">
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>
      <header className="app__header">
        <div className="app__brand">
          <span className="app__brand-name">OpoFuente</span>
          <span className="app__brand-note">biblioteca personal de oposiciones</span>
        </div>
        <OppositionSelector />
        <SystemIndicators />
      </header>
      <div className="app__body">
        <nav className="app__nav" aria-label="Secciones de la aplicación">
          <ul className="nav">
            {NAV_ITEMS.map((item) => (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) => (isActive ? 'nav__link nav__link--active' : 'nav__link')}
                >
                  <span className="nav__label">{item.label}</span>
                  {item.slice !== null && (
                    <span className="nav__slice">
                      <span aria-hidden="true">·</span> {item.slice}
                    </span>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
        <main id="contenido" className="app__main" tabIndex={-1}>
          {children}
        </main>
      </div>
      <footer className="app__footer">
        <p>
          Aplicación local de un solo usuario. Los originales nunca se mueven ni se borran: OpoFuente
          trabaja siempre sobre copias.
        </p>
      </footer>
    </div>
  );
}
