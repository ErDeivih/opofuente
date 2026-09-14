import { Route, Routes } from 'react-router-dom';

import { HomePage } from '../pages/HomePage';
import { NotFoundPage } from '../pages/NotFoundPage';
import { PendingPage } from '../pages/PendingPage';
import { ProgramPage } from '../pages/ProgramPage';
import { NAV_ITEMS } from './navigation';

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/programa" element={<ProgramPage />} />
      {NAV_ITEMS.filter((item) => item.slice !== null).map((item) => (
        <Route key={item.path} path={item.path} element={<PendingPage item={item} />} />
      ))}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
