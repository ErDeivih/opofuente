import { Navigate, Outlet, Route, Routes, useLocation, useSearchParams } from 'react-router-dom';

import { AdminUiPage } from '../pages/AdminUiPage';
import { ChangesPage } from '../pages/ChangesPage';
import { ErrorsPage } from '../pages/ErrorsPage';
import { ExplanationTrayPage } from '../pages/ExplanationTrayPage';
import { IncidentsPage } from '../pages/IncidentsPage';
import { LibraryPage } from '../pages/LibraryPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { NoSonPreguntasPage } from '../pages/NoSonPreguntasPage';
import { NoteReportsPage } from '../pages/NoteReportsPage';
import { NotesReviewPage } from '../pages/NotesReviewPage';
import { NotesReviewTopicPage } from '../pages/NotesReviewTopicPage';
import { ProgramPage } from '../pages/ProgramPage';
import { QuestionFilePage } from '../pages/QuestionFilePage';
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
import { TestsPage } from '../pages/student/TestsPage';
import { TopicNotesPage } from '../pages/student/TopicNotesPage';
import { TopicReviewPage } from '../pages/TopicReviewPage';
import { TrayPage } from '../pages/TrayPage';
import { StudentTestRunner } from '../features/study/StudentTestRunner';
import { AccountPage, AccessPage, RecoverPage } from '../features/accounts/AccountPages';
import { RequireSession } from '../features/accounts/RequireSession';
import { LegalPage } from '../features/legal/LegalPage';
import { AdminShell } from './AdminShell';
import { AppShell } from './AppShell';
import { ROUTE_REDIRECTS } from './navigation';
import { useApartadoDeLaDireccion } from './apartadoDeLaDireccion';

/**
 * El marco de cada zona (F1 del rediseño, 6 de octubre de 2026).
 *
 * Cada zona trae el suyo y se decide **por la dirección**, no por una bandera: quien entra en
 * `/admin/…` está administrando y ve el panel; quien entra en cualquier otra, estudia y ve la barra
 * del alumno. Así una pantalla nueva no puede quedarse sin marco ni coger el de la otra zona.
 *
 * El marco del alumno además **lleva la vista al apartado que dice la dirección** cuando hay ancla
 * (`useApartadoDeLaDireccion`): es lo que hace que el enlace de la bandeja del panel —«Ver el
 * apartado en los apuntes»— deje el apartado a la vista, en lugar de la página por su principio.
 * Los apuntes llegan por la API después del primer pintado, así que el ancla del navegador sola no
 * basta; se mide en la prueba de extremo a extremo del aviso.
 */
function StudentZone() {
  useApartadoDeLaDireccion();
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
 * Las preguntas del banco, con las dos cosas que cuelgan de esa dirección.
 *
 * 1. `?revisar_tema=1` lleva a la cola de clasificación, como manda
 *    `docs/DECISIONES-Y-SIGUIENTE-TANDA-2026-10.md` §2;
 * 2. `?pregunta=<id>` abre la **ficha** de esa pregunta (F20): es la dirección que la bandeja del
 *    motor y el banco ya usaban para «abrir la pregunta», y hasta ahora caía en la tabla del banco,
 *    que la enseña pero no tiene dónde arreglarla. La ficha es otra pantalla porque contesta otra
 *    pregunta: de dónde sale la respuesta correcta, qué dicen los apuntes, qué ha señalado el motor y
 *    qué se puede hacer con ella.
 *
 * Sin consulta, la pantalla sigue siendo el banco de preguntas de siempre.
 */
function QuestionsRoute() {
  const [params] = useSearchParams();
  if (params.get('revisar_tema') === '1') {
    return <Navigate to="/admin/clasificacion" replace />;
  }
  if (params.get('pregunta') !== null) {
    return <QuestionFilePage />;
  }
  return <QuestionsPage />;
}

/*
 * Las secciones del alumno **ya no tienen ninguna pendiente**.
 *
 * F22 cerró la última —Tests, la que deja elegir temas, cuántas preguntas y cómo se corrigen—, y con
 * ella desaparece el recurso de «esta sección todavía no está»: las siete entradas del menú llevan a
 * una pantalla que hace lo suyo, así que no queda ninguna lista de «lo que falta» que pueda divergir
 * del menú. Si algún día se añade una sección sin pantalla, se declara aquí y se pinta con el recurso
 * de siempre.
 */

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
        <Route path="/tests" element={<TestsPage />} />
        <Route path="/simulacros" element={<MockExamPage />} />
        <Route path="/examenes" element={<OfficialExamsPage />} />
        <Route path="/fallos" element={<MistakesPage />} />
        <Route path="/progreso" element={<ProgressPage />} />
        {/*
          La plataforma desplegable (§8 y §9 del objetivo vivo). Va **dentro** del marco del alumno
          porque es suyo: la cuenta es de quien estudia y los textos legales se leen desde donde se
          estudia.

          Ninguna de estas rutas cierra el estudio: `/acceso`, `/recuperar` y `/legal/…` se ven sin
          sesión, y solo `/cuenta` —que es «lo mío»— pasa por la guarda. Cerrar el temario con una
          guarda sería romper la regla que manda en todo el bloque: quien estudiaba sin cuenta tiene
          que seguir estudiando igual.
        */}
        <Route path="/acceso" element={<AccessPage />} />
        <Route path="/recuperar" element={<RecoverPage />} />
        <Route
          path="/cuenta"
          element={
            <RequireSession>
              <AccountPage />
            </RequireSession>
          }
        />
        <Route path="/legal/:documento" element={<LegalPage />} />
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
        {/* M1 de la fase 3: la cola de las explicaciones que escribe el modelo y revisa el
            propietario. Solo lectura por ahora: aprobar, editar y regenerar necesitan sus rutas
            de escritura, y están apuntadas en `docs/hitos/M1.md`. */}
        <Route path="explicaciones" element={<ExplanationTrayPage />} />
        {/* El bloque C del objetivo (F16): la bandeja de lo que avisa el alumno y lo que el motor
            dejó fuera de los tests (D6). Se separan a propósito: una se **despacha**, la otra se
            **mira**, y mezclarlas invitaría a tocar desde ahí lo que solo se consulta. */}
        <Route path="avisos" element={<NoteReportsPage />} />
        {/* La bandeja del **motor** (F18): la otra mitad del §4.1 del objetivo. Va al lado de la del
            alumno porque son las dos bandejas del panel y se leen juntas, pero son dos pantallas
            distintas: una es lo que avisa quien estudia y la otra lo que no pudo cerrar el sistema. */}
        <Route path="incidencias" element={<IncidentsPage />} />
        {/* La revisión de los apuntes (F24, §4.3 del objetivo): la tabla de los temas con su motivo
            medido y, detrás, la ficha donde se lee un borrador y se aprueba o se rechaza. El código
            legible (`I.4`) es la dirección de la ficha, como en la zona del alumno: nunca un
            identificador de nodo. */}
        <Route path="apuntes" element={<NotesReviewPage />} />
        <Route path="apuntes/:codigo" element={<NotesReviewTopicPage />} />
        <Route path="no-son-preguntas" element={<NoSonPreguntasPage />} />
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
