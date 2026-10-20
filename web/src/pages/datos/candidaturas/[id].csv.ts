// Las candidaturas de una provincia, con las mismas columnas que el fichero completo.
import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { candidaturasBoe, circunscripciones } from '../../../lib/datos';
import { CABECERA_CANDIDATURAS, csv, filasCandidaturas } from '../../../lib/csv';

export async function getStaticPaths() {
  return (await getCollection('circunscripciones')).map((c) => ({ params: { id: c.id } }));
}

export const GET: APIRoute = async ({ params }) => {
  const cand = await candidaturasBoe();
  const provincias = new Map((await circunscripciones()).map((c) => [c.id, c.data.nombre]));
  const aqui = (cand?.candidaturas ?? []).filter((c) => c.provincia === params.id);
  const filas = cand ? filasCandidaturas(aqui, provincias, cand.fase, cand.fuente) : [];
  return csv(CABECERA_CANDIDATURAS, filas, `papeletablanca-candidaturas-${params.id}.csv`);
};
