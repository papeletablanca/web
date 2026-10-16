// Mapa del sitio para los buscadores. Las páginas fijas se descubren solas (cualquier .astro de esta carpeta,
// salvo la 404); las de provincia y formación salen de sus colecciones.
import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { ruta } from '../lib/datos';

const fijas = Object.keys(import.meta.glob('./*.astro'))
  .map((f) => f.replace(/^\.\//, '').replace(/\.astro$/, ''))
  .filter((p) => p !== '404')
  .map((p) => (p === 'index' ? '' : p));

export const GET: APIRoute = async ({ site }) => {
  const rutas = [
    ...fijas,
    ...(await getCollection('circunscripciones')).map((c) => `provincia/${c.id}`),
    ...(await getCollection('formaciones')).map((f) => `formacion/${f.id}`),
  ];
  const urls = rutas.map((p) => `<url><loc>${new URL(ruta(p ? `${p}/` : ''), site).href}</loc></url>`).join('\n');
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urls}
</urlset>
`;
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
};
