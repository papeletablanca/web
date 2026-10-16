// Qué pasa hoy en el calendario electoral. Sirve al construir la web y en el navegador (recuadro «Hoy en las
// elecciones» de la portada), para que se actualice solo al cambiar de día aunque la web no se reconstruya.

export interface Hito { fecha: string; hasta: string; texto: string; aproximada: boolean; fuente?: string }
export type Estado =
  | { tipo: 'abierto'; hito: Hito }
  | { tipo: 'proximo'; hito: Hito; dias: number }
  | { tipo: 'fin' };

/** Fecha de hoy en Madrid, en formato AAAA-MM-DD. */
export const hoyMadrid = (ahora = new Date()) => ahora.toLocaleDateString('sv-SE', { timeZone: 'Europe/Madrid' });

const dia = (f: string) => Date.parse(`${f}T00:00:00Z`) / 864e5;

/** «19 de octubre» */
export const fechaLarga = (f: string) => new Date(`${f}T00:00:00Z`).toLocaleDateString('es-ES', { day: 'numeric', month: 'long', timeZone: 'UTC' });

/** Lo que está en marcha hoy (si hay varias cosas, la más concreta: un día suelto antes que un plazo largo) o, si no, lo próximo. */
export function estado(hitos: Hito[], hoy: string): Estado {
  const enMarcha = hitos.filter((h) => h.fecha <= hoy && hoy <= h.hasta).sort((a, b) => dia(a.hasta) - dia(a.fecha) - (dia(b.hasta) - dia(b.fecha)));
  if (enMarcha.length) return { tipo: 'abierto', hito: enMarcha[0] };
  const proximo = [...hitos].sort((a, b) => a.fecha.localeCompare(b.fecha)).find((h) => h.fecha > hoy);
  return proximo ? { tipo: 'proximo', hito: proximo, dias: dia(proximo.fecha) - dia(hoy) } : { tipo: 'fin' };
}

/** Etiqueta y frase en lenguaje llano para el recuadro. */
export function describir(e: Estado): { etiqueta: string; frase: string } {
  if (e.tipo === 'fin') return { etiqueta: 'Calendario', frase: 'Ya han pasado todas las fechas del calendario electoral.' };
  const { hito } = e;
  const aprox = hito.aproximada ? ' (fecha aproximada)' : '';
  if (e.tipo === 'abierto') {
    return hito.fecha === hito.hasta
      ? { etiqueta: 'Hoy', frase: `${hito.texto}${aprox}.` }
      : { etiqueta: 'Plazo abierto', frase: `${hito.texto}, hasta el ${fechaLarga(hito.hasta)}.` };
  }
  const cuando = e.dias === 1 ? 'mañana' : `dentro de ${e.dias} días`;
  return { etiqueta: 'Lo próximo', frase: `${hito.texto}: el ${fechaLarga(hito.fecha)}${aprox}, ${cuando}.` };
}
