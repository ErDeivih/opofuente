import { Route, Routes } from 'react-router-dom';

import { HomePage } from '../pages/HomePage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { PendingPage } from '../pages/PendingPage';
import { ProgramPage } from '../pages/ProgramPage';
import { ReviewPage } from '../pages/ReviewPage';
import { TrayPage } from '../pages/TrayPage';
import { NAV_ITEMS } from './navigation';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/programa" element={<ProgramPage />} />
      <Route path="/bandeja" element={<TrayPage />} />
      {/* La revisión es la continuación de la bandeja (07_UI-UX §4), no una sección de la barra
          lateral: la navegación del producto la fija y no incluye «Revisión» entre sus secciones. */}
      <Route path="/revision" element={<ReviewPage />} />
      {NAV_ITEMS.filter((item) => item.slice !== null).map((item) => (
        <Route key={item.path} path={item.path} element={<PendingPage item={item} />} />
      ))}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
