// Lectura y cruce de datos para las páginas.
import { getCollection, type CollectionEntry } from 'astro:content';

export const ELECCION = '2026-11-29';

export type Formacion = CollectionEntry<'formaciones'>;
export type Circunscripcion = CollectionEntry<'circunscripciones'>;
export type Candidatura = CollectionEntry<'candidaturas'>['data']['candidaturas'][number];

/** Enlace interno que respeta la carpeta base de GitHub Pages. */
export function ruta(p = ''): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return `${base}/${p.replace(/^\//, '')}`;
}

/** Las fechas se guardan a medianoche UTC; se muestran en UTC para no cambiar de día. */
export function fecha(d: Date | string, opciones: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short' }): string {
  return new Date(d).toLocaleDateString('es-ES', { timeZone: 'UTC', ...opciones }).replace('.', '');
}

export const plural = (n: number, uno: string, varios: string) => `${n} ${n === 1 ? uno : varios}`;

// Siglas comparables: sin tildes, espacios ni signos (el BOE escribe a veces «B.N.G.» y otras «BNG»)
const clave = (s: string) => s.normalize('NFKD').replace(/[̀-ͯ]/g, '').toUpperCase().replace(/[^A-Z0-9]/g, '');
const es = (a: string, b: string) => a.localeCompare(b, 'es', { sensitivity: 'base' });

export const corto = (f: Formacion) => f.data.corto ?? f.data.siglas[0];

export async function formaciones(): Promise<Formacion[]> {
  return (await getCollection('formaciones')).sort((a, b) => es(corto(a), corto(b)));
}

export async function circunscripciones(): Promise<Circunscripcion[]> {
  return (await getCollection('circunscripciones')).sort((a, b) => es(a.data.nombre, b.data.nombre));
}

/** Las candidaturas más avanzadas que haya publicado el BOE: proclamadas si existen, si no presentadas. */
let candidaturasCache: ReturnType<typeof leerCandidaturas> | undefined;
export const candidaturasBoe = () => (candidaturasCache ??= leerCandidaturas());
async function leerCandidaturas() {
  const todas = await getCollection('candidaturas');
  return todas.find((c) => c.data.fase === 'proclamadas')?.data ?? todas.find((c) => c.data.fase === 'presentadas')?.data ?? null;
}

/** Correcciones de errores del BOE que afectan a las listas mostradas en una provincia. */
export async function correccionesDe(provincia: string, fase: string) {
  return (await getCollection('correcciones'))
    .map((c) => c.data)
    .filter((c) => c.fase === fase && c.provincias.includes(provincia))
    .sort((a, b) => a.fuente.fecha_publicacion.localeCompare(b.fuente.fecha_publicacion));
}

/** Ficha que corresponde a una candidatura del BOE, por sus siglas (también las de marcas territoriales). */
export function fichaDe(c: Candidatura, fichas: Formacion[]): Formacion | undefined {
  const s = clave(c.siglas);
  if (!s) return undefined;
  return fichas.find(
    (f) => f.data.siglas.some((x) => clave(x) === s) || f.data.marcas_territoriales.some((m) => m.siglas.some((x) => clave(x) === s)),
  );
}

export type Hallazgo = CollectionEntry<'boe'>['data']['hallazgos'][number] & { fecha: string };

export async function hallazgosBoe(): Promise<Hallazgo[]> {
  const dias = await getCollection('boe');
  return dias
    .flatMap((d) => d.data.hallazgos.map((h) => ({ ...h, fecha: d.data.fecha })))
    .sort((a, b) => b.fecha.localeCompare(a.fecha) || b.id.localeCompare(a.id));
}

/** Nombre corto del departamento para las tarjetas ("MINISTERIO DE HACIENDA" -> "Hacienda"). */
export function departamento(d: string | null): string {
  if (!d) return '';
  const menores = new Set(['de', 'del', 'la', 'las', 'el', 'los', 'y', 'e', 'con', 'para', 'a']);
  return d
    .toLowerCase()
    .replace(/^ministerio (de |del |para la |para el )?/, '')
    .split(' ')
    .map((p, i) => (i > 0 && menores.has(p) ? p : p.charAt(0).toUpperCase() + p.slice(1)))
    .join(' ');
}

/** Estado global de una ficha, para la rejilla. */
export function progreso(f: Formacion) {
  const datos = [f.data.candidatura_presidencia, f.data.web, f.data.programa];
  const conFuente = datos.filter((d) => d.estado !== 'pendiente').length;
  return { conFuente, total: datos.length };
}
