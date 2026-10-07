import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom';

import { AdminUiPage } from '../pages/AdminUiPage';
import { ChangesPage } from '../pages/ChangesPage';
import { ComingSoonPage } from '../pages/ComingSoonPage';
import { ErrorsPage } from '../pages/ErrorsPage';
import { HomePage } from '../pages/HomePage';
import { LibraryPage } from '../pages/LibraryPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { ProgramPage } from '../pages/ProgramPage';
import { QuestionsPage } from '../pages/QuestionsPage';
import { ReviewPage } from '../pages/ReviewPage';
import { SearchPage } from '../pages/SearchPage';
import { SettingsPage } from '../pages/SettingsPage';
import { StudyPage } from '../pages/StudyPage';
import { TrayPage } from '../pages/TrayPage';
import { AdminShell } from './AdminShell';
import { AppShell } from './AppShell';
import { ROUTE_REDIRECTS, STUDENT_NAV_ITEMS } from './navigation';

/**
 * El marco de cada zona (F1 del rediseño, 6 de octubre de 2026).
 *
 * Cada zona trae el suyo y se decide **por la dirección**, no por una bandera: quien entra en
 * `/admin/…` está administrando y ve el panel; quien entra en cualquier otra, estudia y ve la barra
 * del alumno. Así una pantalla nueva no puede quedarse sin marco ni coger el de la otra zona.
 */
function StudentZone() {
  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}

function AdminZone() {
  return (
    <AdminShell>
      <Outlet />
    </AdminShell>
  );
}

/**
 * Una dirección de las de antes: se lleva a la nueva **conservando la consulta y el ancla**.
 *
 * Conservarlas no es un detalle: `/biblioteca?documento=…` abre la ficha de ese documento y
 * `/buscar?q=…` trae la búsqueda hecha, así que un redirect que las tirara dejaría al usuario en la
 * pantalla correcta pero sin lo que había pedido.
 */
function OldAddress({ to }: { to: string }) {
  const { search, hash } = useLocation();
  return <Navigate to={`${to}${search}${hash}`} replace />;
}

/** Las seis secciones del alumno que todavía no tienen pantalla, con su frase, desde el mapa. */
const SECCIONES_PENDIENTES = STUDENT_NAV_ITEMS.filter((item) => item.path !== '/');

export function AppRoutes() {
  return (
    <Routes>
      {/* --- Zona del alumno -------------------------------------------------- */}
      <Route element={<StudentZone />}>
        <Route path="/" element={<HomePage />} />
        {SECCIONES_PENDIENTES.map((item) => (
          <Route
            key={item.path}
            path={item.path}
            element={<ComingSoonPage title={item.label} summary={item.summary} />}
          />
        ))}
        <Route path="*" element={<NotFoundPage />} />
      </Route>

      {/* --- Zona de administración ------------------------------------------- */}
      <Route path="/admin" element={<AdminZone />}>
        {/* `Administrar` del pie entra aquí: no hay resumen propio todavía, así que se aterriza en la
            primera sección del menú en lugar de dejar `/admin` sin pantalla. */}
        <Route index element={<Navigate to="/admin/importar" replace />} />
        <Route path="importar" element={<TrayPage />} />
        <Route path="biblioteca" element={<LibraryPage />} />
        <Route path="revision" element={<ReviewPage />} />
        <Route path="cambios" element={<ChangesPage />} />
        <Route path="errores" element={<ErrorsPage />} />
        <Route path="preguntas" element={<QuestionsPage />} />
        <Route path="programa" element={<ProgramPage />} />
        <Route path="estudiar" element={<StudyPage />} />
        <Route path="buscar" element={<SearchPage />} />
        <Route path="ajustes" element={<SettingsPage />} />
        {/* La página de los componentes: se mira, se compara y se corrige **antes** de construir con
            ellos las pantallas de test (F3 del rediseño). Sale en `npm run screens`. */}
        <Route path="ui" element={<AdminUiPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>

      {/* --- Direcciones de antes: ninguna da 404 ----------------------------- */}
      {ROUTE_REDIRECTS.map(({ from, to }) => (
        <Route key={from} path={from} element={<OldAddress to={to} />} />
      ))}
    </Routes>
  );
}
