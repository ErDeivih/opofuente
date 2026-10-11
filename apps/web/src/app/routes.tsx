import { Navigate, Outlet, Route, Routes, useLocation, useSearchParams } from 'react-router-dom';

import { AdminUiPage } from '../pages/AdminUiPage';
import { ChangesPage } from '../pages/ChangesPage';
import { ComingSoonPage } from '../pages/ComingSoonPage';
import { ErrorsPage } from '../pages/ErrorsPage';
import { LibraryPage } from '../pages/LibraryPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { ProgramPage } from '../pages/ProgramPage';
import { QuestionsPage } from '../pages/QuestionsPage';
import { ReviewPage } from '../pages/ReviewPage';
import { SearchPage } from '../pages/SearchPage';
import { SettingsPage } from '../pages/SettingsPage';
import { StudyPage } from '../pages/StudyPage';
import { StudentHomePage } from '../pages/student/StudentHomePage';
import { MistakesPage } from '../pages/student/MistakesPage';
import { MockExamPage } from '../pages/student/MockExamPage';
import { OfficialExamsPage } from '../pages/student/OfficialExamsPage';
import { ProgressPage } from '../pages/student/ProgressPage';
import { ResultPage } from '../pages/student/ResultPage';
import { SyllabusPage } from '../pages/student/SyllabusPage';
import { TopicNotesPage } from '../pages/student/TopicNotesPage';
import { TopicReviewPage } from '../pages/TopicReviewPage';
import { TrayPage } from '../pages/TrayPage';
import { StudentTestRunner } from '../features/study/StudentTestRunner';
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

/**
 * Las preguntas del banco, con la puerta que la decisión del propietario ya tenía escrita.
 *
 * `docs/DECISIONES-Y-SIGUIENTE-TANDA-2026-10.md` §2 manda la cola de temas a
 * `/admin/preguntas?revisar_tema=1`, y esa dirección tiene que llevar a la cola: la pantalla del
 * banco sigue siendo `/admin/preguntas` a secas, y con la consulta se va a Clasificación, que es
 * donde se revisa. Se conserva la dirección documentada en lugar de dejar que dé una pantalla que
 * no es.
 */
function QuestionsRoute() {
  const [params] = useSearchParams();
  if (params.get('revisar_tema') === '1') {
    return <Navigate to="/admin/clasificacion" replace />;
  }
  return <QuestionsPage />;
}

/**
 * La única sección del alumno que todavía no tiene pantalla: **Tests**.
 *
 * Simulacros, Exámenes, Fallos y Progreso ya la tienen desde F14, y cada una dice lo suyo; lo que
 * queda —elegir temas, cuántas preguntas y cómo se corrigen— llegará con su bloque, y hasta entonces
 * esa entrada dice qué hará en lugar de quedarse en blanco. La lista sale del mapa de navegación para
 * que no haya dos listas de «lo que falta» que puedan divergir.
 */
const SECCIONES_PENDIENTES = STUDENT_NAV_ITEMS.filter(
  (item) =>
    item.path !== '/' &&
    item.path !== '/temario' &&
    item.path !== '/simulacros' &&
    item.path !== '/examenes' &&
    item.path !== '/fallos' &&
    item.path !== '/progreso',
);

export function AppRoutes() {
  return (
    <Routes>
      {/* --- El test en curso: modo examen ------------------------------------ */}
      {/*
        Va **fuera** del marco del alumno a propósito: en modo test desaparece la navegación (el
        diseño lo pide: «modo test = modo examen»), y el marco es justo lo que la pinta. Colgarlo de
        `StudentZone` habría dejado el carril a la vista o habría obligado a esconderlo con una
        bandera dentro del marco, que es una segunda forma de decidir lo mismo.
      */}
      <Route path="/test/:id" element={<StudentTestRunner />} />

      {/* --- Zona del alumno -------------------------------------------------- */}
      <Route element={<StudentZone />}>
        <Route path="/" element={<StudentHomePage />} />
        <Route path="/temario" element={<SyllabusPage />} />
        {/*
          La ficha del tema con sus apuntes: el código legible (`IV.7`) es la dirección, como en toda
          la zona del alumno. Nunca un identificador de nodo.
        */}
        <Route path="/temario/:codigo" element={<TopicNotesPage />} />
        {/*
          El cierre del ciclo de estudio (F14): el resultado de un test, el simulacro, los exámenes
          oficiales, los fallos y el progreso. El resultado se abre por el identificador de la sesión
          —es la dirección del propio test— y todo lo demás por su nombre.
        */}
        <Route path="/resultado/:id" element={<ResultPage />} />
        <Route path="/simulacros" element={<MockExamPage />} />
        <Route path="/examenes" element={<OfficialExamsPage />} />
        <Route path="/fallos" element={<MistakesPage />} />
        <Route path="/progreso" element={<ProgressPage />} />
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
        <Route path="clasificacion" element={<TopicReviewPage />} />
        <Route path="cambios" element={<ChangesPage />} />
        <Route path="errores" element={<ErrorsPage />} />
        <Route path="preguntas" element={<QuestionsRoute />} />
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
