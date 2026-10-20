// Escaños por circunscripción (Real Decreto 806/2026).
import type { APIRoute } from 'astro';
import { circunscripciones } from '../../lib/datos';
import { csv } from '../../lib/csv';

export const GET: APIRoute = async () =>
  csv(
    ['provincia_id', 'provincia', 'diputados', 'senadores', 'senadores_por_isla'],
    (await circunscripciones()).map(({ id, data: d }) => [
      id, d.nombre, d.diputados, d.senadores, d.senado_islas.map((i) => `${i.isla}: ${i.senadores}`).join(', '),
    ]),
    'papeletablanca-escanos.csv',
  );
