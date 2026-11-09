/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL base de la API local. Por defecto http://127.0.0.1:8765 */
  readonly VITE_API_BASE_URL?: string;
  /**
   * Fuerza la telemetría propia: `on` la enciende también fuera del build de producción. En
   * producción está activa por defecto; en desarrollo y en las pruebas, apagada.
   */
  readonly VITE_TELEMETRY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
