// Novedades electorales del BOE que ha apartado el radar, de la más reciente a la más antigua.
import type { APIRoute } from 'astro';
import { hallazgosBoe } from '../../lib/datos';
import { csv } from '../../lib/csv';

export const GET: APIRoute = async () =>
  csv(
    ['fecha', 'boe_id', 'titulo', 'departamento', 'seccion', 'etiquetas', 'url', 'url_pdf'],
    (await hallazgosBoe()).map((h) => [h.fecha, h.id, h.titulo, h.departamento, h.seccion, h.etiquetas.join(', '), h.url_html, h.url_pdf]),
    'papeletablanca-novedades-boe.csv',
  );
