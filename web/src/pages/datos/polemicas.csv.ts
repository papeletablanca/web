// Acuerdos de la Junta Electoral Central que cumplen la regla de jec.py, copiados tal cual.
import type { APIRoute } from 'astro';
import { polemicasJec } from '../../lib/datos';
import { csv } from '../../lib/csv';

export const GET: APIRoute = async () =>
  csv(
    ['fecha_sesion', 'acuerdo', 'expediente', 'autor', 'objeto', 'texto_acuerdo', 'materias', 'url'],
    (await polemicasJec()).map((p) => [p.fecha, p.numero, p.expediente, p.autor, p.objeto, p.acuerdo.join('\n'), p.materias.join(', '), p.url]),
    'papeletablanca-polemicas-jec.csv',
  );
