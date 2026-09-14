/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL base de la API local. Por defecto http://127.0.0.1:8765 */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
