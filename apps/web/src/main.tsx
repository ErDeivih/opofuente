import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import { App } from './app/App';
import { installGlobalErrorTelemetry } from './telemetry';
import './styles/global.css';

const container = document.getElementById('root');

if (container === null) {
  throw new Error('Falta el contenedor #root en index.html');
}

// Captura `error` y `unhandledrejection` desde el arranque, antes de montar React. Si la
// telemetría está apagada (desarrollo y pruebas) esta llamada no hace nada.
installGlobalErrorTelemetry();

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
