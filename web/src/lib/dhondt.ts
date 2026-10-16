// Reparto de escaños por la regla D'Hondt (LOREG art. 163). Sirve al construir la página del simulador y en el
// navegador al cambiar los números.
//   a) Fuera las candidaturas con menos del 3 % de los votos válidos (votos a candidaturas + votos en blanco).
//   b-c) Se dividen los votos de cada una entre 1, 2, 3… y los escaños van a los cocientes mayores.
//   d) Empate entre cocientes: el escaño va a la candidatura con más votos en total.

export interface Reparto {
  validos: number;
  /** Por candidatura, en el mismo orden de entrada */
  filas: { votos: number; fuera: boolean; escanos: number; cocientes: { valor: number; gana: boolean }[] }[];
}

export function dhondt(votos: number[], blancos: number, escanos: number): Reparto {
  const validos = votos.reduce((a, b) => a + b, 0) + blancos;
  const fuera = votos.map((v) => validos === 0 || v < validos * 0.03);
  const cocientes = votos.flatMap((v, i) =>
    fuera[i] ? [] : [...Array(escanos)].map((_, k) => ({ i, k, valor: v / (k + 1), votos: v })),
  );
  const ganadores = new Set(
    cocientes
      .sort((a, b) => b.valor - a.valor || b.votos - a.votos)
      .slice(0, escanos)
      .map((c) => `${c.i}-${c.k}`),
  );
  return {
    validos,
    filas: votos.map((v, i) => {
      const fila = [...Array(escanos)].map((_, k) => ({ valor: v / (k + 1), gana: ganadores.has(`${i}-${k}`) }));
      return { votos: v, fuera: fuera[i], escanos: fila.filter((c) => c.gana).length, cocientes: fila };
    }),
  };
}

/** El ejemplo práctico del propio artículo 163 de la LOREG: 8 escaños y seis candidaturas. */
export const EJEMPLO_LEY = { escanos: 8, blancos: 0, votos: [168000, 104000, 72000, 64000, 40000, 32000] };
