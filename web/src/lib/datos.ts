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

/**
 * Cuántos nombres se pueden marcar en la papeleta del Senado según los senadores que elige la circunscripción
 * (LOREG art. 166.1.a): 3 en las provincias (4 senadores), 2 en Gran Canaria, Mallorca y Tenerife (3) y en Ceuta y
 * Melilla (2), y 1 en el resto de las islas (1). Marcar más anula el voto (art. 96.3).
 */
export const marcasSenado = (senadores: number) => (senadores >= 4 ? 3 : senadores >= 2 ? 2 : 1);

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

export type Coalicion = CollectionEntry<'coaliciones'>['data'];

export const coaliciones = async (): Promise<Coalicion[]> => (await getCollection('coaliciones')).map((c) => c.data);

// Piezas de un nombre y unas siglas oficiales: lo que va entre guiones, comas, dos puntos o paréntesis.
// «ERC-EH BILDU» → ERC, EH BILDU; «SDP (PSOE, IU, MS…)» → SDP, PSOE, IU, MS…
const piezas = (c: { nombre: string; siglas: string }) =>
  new Set([c.nombre, c.siglas].flatMap((t) => t.split(/[-–,:;()]+/)).map(clave).filter(Boolean));
const enPiezas = (f: Formacion, p: Set<string>) => [f.data.nombre, ...f.data.siglas].map(clave).some((s) => p.has(s));

/**
 * Coaliciones de las que forma parte una ficha. Regla: alguna de sus siglas, o su nombre, aparece tal cual como pieza
 * del nombre o de las siglas que publica la Junta Electoral Central. No se lee el pacto (es un PDF escaneado).
 */
export function coalicionesDe(f: Formacion, todas: Coalicion[]): Coalicion[] {
  return todas.filter((c) => enPiezas(f, piezas(c)));
}

/** Coalición a la que corresponde una candidatura del BOE: por siglas completas, por la primera pieza o por nombre. */
function coalicionDe(c: Candidatura, todas: Coalicion[]): Coalicion | undefined {
  const s = clave(c.siglas);
  const n = clave(c.nombre);
  return todas.find((x) => {
    const primera = clave(x.siglas.split(/[-–,:;()]+/)[0] ?? '');
    return (s && (clave(x.siglas) === s || primera === s)) || (n && clave(x.nombre) === n);
  });
}

/**
 * Fichas de una candidatura, por este orden:
 * 1. la suya, si las siglas coinciden;
 * 2. las de las formaciones de la coalición de la JEC que la presenta (la lista «SDP» del Senado → ficha del PSOE);
 * 3. las que aparecen como pieza del nombre o las siglas que publica el BOE para esa lista. Así entran las
 *    coaliciones inscritas solo en una Junta Provincial, que no están en la relación de la JEC («UPN-PP» → UPN y PP).
 */
export function fichasDe(c: Candidatura, fichas: Formacion[], todas: Coalicion[]): Formacion[] {
  const propia = fichaDe(c, fichas);
  if (propia) return [propia];
  const coal = coalicionDe(c, todas);
  const p = coal ? piezas(coal) : piezas(c);
  return fichas.filter((f) => enPiezas(f, p));
}

export type Hallazgo = CollectionEntry<'boe'>['data']['hallazgos'][number] & { fecha: string };

export async function hallazgosBoe(): Promise<Hallazgo[]> {
  const dias = await getCollection('boe');
  return dias
    .flatMap((d) => d.data.hallazgos.map((h) => ({ ...h, fecha: d.data.fecha })))
    .sort((a, b) => b.fecha.localeCompare(a.fecha) || b.id.localeCompare(a.id));
}

/**
 * Novedades que afectan a quien vota (recuadro «Hoy» de la portada): por etiqueta del radar, nunca correcciones de
 * errores. Los nombramientos, la financiación y el resto de trámites siguen en «Novedades», completos.
 */
const PARA_VOTANTES = new Set(['Convocatoria', 'Candidaturas', 'Censo y voto', 'Ley electoral', 'Resultados']);
export const afectaAlVotante = (h: Hallazgo) => h.etiquetas.some((e) => PARA_VOTANTES.has(e)) && !/^correcci[oó]n de errores/i.test(h.titulo);

/** Novedades del BOE que publican una resolución de un tribunal (la regla de «En los tribunales», en Polémicas). */
const TRIBUNAL = /\b(autos?|sentencias?|recursos?)\b|tribunal (supremo|constitucional)/i;
export const enTribunales = (hallazgos: Hallazgo[]) => hallazgos.filter((h) => TRIBUNAL.test(h.titulo));

export type Polemica = CollectionEntry<'jec'>['data']['acuerdos'][number] & { fecha: string };

/** Acuerdos de la Junta Electoral Central que cumplen la regla de jec.py, del más reciente al más antiguo. */
export async function polemicasJec(): Promise<Polemica[]> {
  const sesiones = await getCollection('jec');
  const numero = (p: Polemica) => Number(p.numero.split('/')[0]);
  return sesiones
    .flatMap((s) => s.data.acuerdos.map((a) => ({ ...a, fecha: s.data.fecha })))
    .sort((a, b) => b.fecha.localeCompare(a.fecha) || numero(b) - numero(a));
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
