import { Route, Routes } from 'react-router-dom';

import { HomePage } from '../pages/HomePage';
import { ChangesPage } from '../pages/ChangesPage';
import { ErrorsPage } from '../pages/ErrorsPage';
import { LibraryPage } from '../pages/LibraryPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { PendingPage } from '../pages/PendingPage';
import { ProgramPage } from '../pages/ProgramPage';
import { QuestionsPage } from '../pages/QuestionsPage';
import { ReviewPage } from '../pages/ReviewPage';
import { SearchPage } from '../pages/SearchPage';
import { SettingsPage } from '../pages/SettingsPage';
import { StudyPage } from '../pages/StudyPage';
import { TrayPage } from '../pages/TrayPage';
import { NAV_ITEMS } from './navigation';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/programa" element={<ProgramPage />} />
      <Route path="/bandeja" element={<TrayPage />} />
      <Route path="/biblioteca" element={<LibraryPage />} />
      <Route path="/preguntas" element={<QuestionsPage />} />
      <Route path="/estudiar" element={<StudyPage />} />
      <Route path="/errores" element={<ErrorsPage />} />
      <Route path="/cambios" element={<ChangesPage />} />
      <Route path="/ajustes" element={<SettingsPage />} />
      {/* La revisión es la continuación de la bandeja (07_UI-UX §4), no una sección de la barra
          lateral: la navegación del producto la fija y no incluye «Revisión» entre sus secciones. */}
      <Route path="/revision" element={<ReviewPage />} />
      {/* La búsqueda global de la cabecera tampoco es una sección de la barra lateral: se entra por
          el buscador o por un enlace directo a `/buscar?q=…` (07_UI-UX §2). */}
      <Route path="/buscar" element={<SearchPage />} />
      {NAV_ITEMS.filter((item) => item.slice !== null).map((item) => (
        <Route key={item.path} path={item.path} element={<PendingPage item={item} />} />
      ))}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
