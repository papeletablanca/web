// Descargas en CSV para medios y para quien quiera reutilizar los datos.
// Separadas por punto y coma y con marca BOM: así las abre bien Excel en español, con tildes y en columnas.
import type { Candidatura } from './datos';

type Celda = string | number | boolean | null | undefined;

const celda = (v: Celda) => {
  const s = v === null || v === undefined ? '' : typeof v === 'boolean' ? (v ? 'sí' : 'no') : String(v);
  return /[;"\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};

export function csv(cabecera: string[], filas: Celda[][], nombre: string): Response {
  const texto = '﻿' + [cabecera, ...filas].map((f) => f.map(celda).join(';')).join('\r\n') + '\r\n';
  return new Response(texto, {
    headers: { 'Content-Type': 'text/csv; charset=utf-8', 'Content-Disposition': `attachment; filename="${nombre}"` },
  });
}

/** Una fila por persona: titulares y suplentes, en el orden del BOE. */
export const CABECERA_CANDIDATURAS = [
  'provincia_id', 'provincia', 'camara', 'isla', 'orden_candidatura', 'candidatura', 'siglas', 'proclamada',
  'tipo', 'puesto', 'nombre', 'suplente_de', 'fase', 'boe_id', 'boe_url',
];

export function filasCandidaturas(lista: Candidatura[], provincias: Map<string, string>, fase: string, boe: { id: string; url: string }): Celda[][] {
  return lista.flatMap((c) => {
    const base = [c.provincia, provincias.get(c.provincia) ?? c.provincia, c.camara, c.isla, c.orden, c.nombre, c.siglas, c.proclamada];
    const fin = [fase, boe.id, boe.url];
    return [
      ...c.candidatos.flatMap((p, i) => [
        [...base, 'titular', i + 1, p.nombre, '', ...fin],
        ...(p.suplentes ?? []).map((s) => [...base, 'suplente', i + 1, s, p.nombre, ...fin]),  // Senado: suplente de cada candidato
      ]),
      ...c.suplentes.map((s, j) => [...base, 'suplente', j + 1, s, '', ...fin]),  // Congreso: lista de suplentes
    ];
  });
}
