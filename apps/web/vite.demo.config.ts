import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import react from '@vitejs/plugin-react';
import { defineConfig, type Plugin } from 'vite';

const here = path.dirname(fileURLToPath(import.meta.url));

/** Publica `data.json` junto al bundle para que se pueda inspeccionar y verificar desde fuera. */
const emitDemoData: Plugin = {
  name: 'opofuente-demo-data',
  generateBundle() {
    this.emitFile({
      type: 'asset',
      fileName: 'data.json',
      source: readFileSync(path.join(here, 'demo', 'data.json'), 'utf8'),
    });
  },
};

/**
 * Build de la demo estática para GitHub Pages.
 *
 * Entrada propia (`demo/index.html`), salida `dist-demo/` con rutas relativas (`base: './'`) para que
 * funcione bajo `/<repositorio>/` sin configurar nada en el host. No comparte el build de la app:
 * la demo no hace ninguna llamada a la API.
 */
export default defineConfig({
  root: path.join(here, 'demo'),
  base: './',
  plugins: [react(), emitDemoData],
  server: { fs: { allow: [here] } },
  build: {
    outDir: path.join(here, 'dist-demo'),
    emptyOutDir: true,
    target: 'es2022',
  },
});
