// Feed RSS con las últimas novedades del BOE.
import type { APIRoute } from 'astro';
import { hallazgosBoe, ruta } from '../lib/datos';

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

export const GET: APIRoute = async ({ site }) => {
  const items = (await hallazgosBoe()).slice(0, 100);
  const web = new URL(ruta(), site).href;
  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>Papeleta Blanca · novedades electorales del BOE</title>
<link>${esc(web)}</link>
<description>Disposiciones del BOE relacionadas con las elecciones generales del 29 de noviembre de 2026.</description>
<language>es</language>
${items
  .map(
    (h) => `<item><title>${esc(h.titulo)}</title><link>${esc(h.url_html)}</link><guid isPermaLink="false">${esc(h.id)}</guid><category>${esc(h.etiquetas.join(', '))}</category><pubDate>${new Date(`${h.fecha}T08:00:00Z`).toUTCString()}</pubDate></item>`,
  )
  .join('\n')}
</channel></rss>
`;
  return new Response(xml, { headers: { 'Content-Type': 'application/rss+xml; charset=utf-8' } });
};
