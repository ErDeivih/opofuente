import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

// Las dos familias del diseño, **autoalojadas**: la CSP del proyecto no deja cargar fuentes de fuera
// (`font-src 'self' data:`), así que se sirven desde el propio paquete. Solo los pesos que se usan
// —400 y 700 de la de interfaz, y el eje de peso de la serif— y solo el subconjunto latino.
import '@fontsource/atkinson-hyperlegible-next/latin-400.css';
import '@fontsource/atkinson-hyperlegible-next/latin-700.css';
import '@fontsource-variable/source-serif-4/wght.css';

import { App } from './app/App';
import './styles/tokens.css';
import './styles/global.css';

const container = document.getElementById('root');

if (container === null) {
  throw new Error('Falta el contenedor #root en index.html');
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
