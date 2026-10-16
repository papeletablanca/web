// @ts-check
import { defineConfig } from 'astro/config';

// En GitHub Pages el workflow pasa SITE_URL y BASE_PATH (con dominio propio, https://papeletablanca.es y una base vacía).
// En local no hace falta nada: la web se sirve en http://localhost:4321/
export default defineConfig({
  site: process.env.SITE_URL || 'http://localhost:4321',
  base: process.env.BASE_PATH || '/',
  trailingSlash: 'ignore',
  build: { format: 'directory' },
});
