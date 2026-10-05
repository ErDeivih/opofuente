import { NavLink } from 'react-router-dom';

import { ApiUnavailableNotice } from '../components/ApiUnavailableNotice';
import { OppositionSelector } from '../features/profiles/OppositionSelector';
import { GlobalSearch } from '../features/search/GlobalSearch';
import { SystemIndicators } from '../features/system/SystemIndicators';
import { NAV_ITEMS } from './navigation';
import { useSectionCounts } from './sectionCounts';
import type { ReactNode } from 'react';

export interface AppShellProps {
  children: ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  // Los contadores de §2: dónde espera trabajo. Los compone `useSectionCounts` a partir de lo que ya
  // cuenta el servidor; aquí solo se pintan.
  const counts = useSectionCounts();

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
        <GlobalSearch />
        <OppositionSelector />
        <SystemIndicators />
      </header>
      <div className="app__body">
        <nav className="app__nav" aria-label="Secciones de la aplicación">
          <ul className="nav">
            {NAV_ITEMS.map((item) => {
              const count = counts[item.path];
              return (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    end={item.path === '/'}
                    // El nombre del enlace dice el número **y** qué es: quien no ve la insignia
                    // —o no distingue el color— oye «Errores: 5 repasos vencidos».
                    aria-label={count === undefined ? undefined : `${item.label}: ${count.label}`}
                    className={({ isActive }) =>
                      isActive ? 'nav__link nav__link--active' : 'nav__link'
                    }
                  >
                    <span className="nav__label">{item.label}</span>
                    {count !== undefined && (
                      <span className="nav__count" aria-hidden="true">
                        {count.count}
                      </span>
                    )}
                    {item.slice !== null && (
                      <span className="nav__slice">
                        <span aria-hidden="true">·</span> {item.slice}
                      </span>
                    )}
                  </NavLink>
                </li>
              );
            })}
          </ul>
        </nav>
        <main id="contenido" className="app__main" tabIndex={-1}>
          <ApiUnavailableNotice />
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
