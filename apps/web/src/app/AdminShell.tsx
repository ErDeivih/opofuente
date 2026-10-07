import { Link, NavLink } from 'react-router-dom';

import { ApiUnavailableNotice } from '../components/ApiUnavailableNotice';
import { OppositionSelector } from '../features/profiles/OppositionSelector';
import { GlobalSearch } from '../features/search/GlobalSearch';
import { SystemIndicators } from '../features/system/SystemIndicators';
import { ADMIN_NAV_ITEMS } from './navigation';
import { useSectionCounts } from './sectionCounts';
import type { ReactNode } from 'react';

export interface AdminShellProps {
  children: ReactNode;
}

/**
 * El marco de la **zona de administración** (F1 del rediseño, 6 de octubre de 2026).
 *
 * Es la trastienda y aquí sí vive la cocina: el selector de oposición activa, la búsqueda en el
 * material recopilado, los indicadores de capacidades y los contadores de lo que espera una decisión.
 * El menú lateral es propio, con las pantallas que ya existían más las que se administran.
 *
 * El aviso de arriba no es decoración: este panel **no es una frontera de seguridad**, es un
 * interruptor. Lo dijo la revisión de F0 y se escribe en la propia pantalla para que nadie lo confunda
 * con un control de acceso (§2.2). La API sigue escuchando solo en `127.0.0.1`.
 */
export function AdminShell({ children }: AdminShellProps) {
  // Los contadores: dónde espera trabajo. Es información de administración, así que vive aquí y no en
  // la barra del alumno, que no tiene por qué enterarse de importaciones ni de conflictos.
  const counts = useSectionCounts();

  return (
    <div className="app">
      <a className="skip-link" href="#contenido">
        Saltar al contenido
      </a>
      <p className="app__aviso-modo">
        <strong>Modo administración</strong> · sin contraseña: solo en este ordenador
      </p>
      <header className="app__header">
        <div className="app__brand">
          <span className="app__brand-name">OpoFuente</span>
          <span className="app__brand-note">panel de administración</span>
        </div>
        <GlobalSearch />
        <OppositionSelector />
        <SystemIndicators />
      </header>
      <div className="app__body">
        <nav className="app__nav" aria-label="Secciones de administración">
          <ul className="nav">
            {ADMIN_NAV_ITEMS.map((item) => {
              const count = counts[item.path];
              return (
                <li key={item.path}>
                  <NavLink
                    to={item.path}
                    // El nombre del enlace dice el número **y** qué es: quien no ve la insignia —o no
                    // distingue el color— oye «Importaciones: 7 avisos o errores de importación».
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
          <Link to="/">Volver a la zona de estudio</Link>
        </p>
      </footer>
    </div>
  );
}
