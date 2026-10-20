// Todas las candidaturas del BOE (proclamadas si ya existen; si no, presentadas), una fila por persona.
import type { APIRoute } from 'astro';
import { candidaturasBoe, circunscripciones } from '../../lib/datos';
import { CABECERA_CANDIDATURAS, csv, filasCandidaturas } from '../../lib/csv';

export const GET: APIRoute = async () => {
  const cand = await candidaturasBoe();
  const provincias = new Map((await circunscripciones()).map((c) => [c.id, c.data.nombre]));
  const filas = cand ? filasCandidaturas(cand.candidaturas, provincias, cand.fase, cand.fuente) : [];
  return csv(CABECERA_CANDIDATURAS, filas, 'papeletablanca-candidaturas.csv');
};
