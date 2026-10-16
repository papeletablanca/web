// Qué datos lee la web y qué forma deben tener. Si una ficha está mal escrita,
// `npm run build` falla diciendo qué fichero y qué campo hay que corregir.
import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { file, glob } from 'astro/loaders';
import { parse } from 'yaml';
import { isAbsolute } from 'node:path';
import { pathToFileURL } from 'node:url';

const DATOS = '../datos';
// Para probar las páginas con las listas de 2023: CANDIDATURAS_PRUEBA=/ruta/a/carpeta npm run dev
const prueba = process.env.CANDIDATURAS_PRUEBA;
const CANDIDATURAS = prueba ? (isAbsolute(prueba) ? pathToFileURL(prueba + '/') : prueba) : `${DATOS}/candidaturas`;
const CORRECCIONES = prueba ? (isAbsolute(prueba) ? pathToFileURL(prueba + '/correcciones/') : `${prueba}/correcciones`) : `${DATOS}/candidaturas/correcciones`;

const enlace = z.url({ error: 'tiene que ser un enlace completo, que empiece por https://' });
const fecha = z.coerce.date({ error: 'tiene que ser una fecha AAAA-MM-DD' });

// Un dato de ficha: valor + estado + fuente. Sin fuente no se publica nada que no esté pendiente.
const dato = z
  .object({
    valor: z.string().default(''),
    estado: z.enum(['confirmado', 'anunciado', 'pendiente'], {
      error: 'el estado tiene que ser confirmado, anunciado o pendiente',
    }),
    fuente: enlace.optional(),
    fecha: fecha.optional(),
  })
  .superRefine((d, ctx) => {
    if (d.estado === 'pendiente') return;
    if (!d.valor) ctx.addIssue({ code: 'custom', path: ['valor'], message: `está "${d.estado}" pero "valor" está vacío` });
    if (!d.fuente) ctx.addIssue({ code: 'custom', path: ['fuente'], message: `está "${d.estado}" y necesita "fuente" (un enlace)` });
    if (!d.fecha) ctx.addIssue({ code: 'custom', path: ['fecha'], message: `está "${d.estado}" y necesita "fecha"` });
  });

const formaciones = defineCollection({
  loader: glob({ pattern: ['*.yaml', '!_*.yaml'], base: `${DATOS}/formaciones` }),
  schema: z.object({
    nombre: z.string().min(1),
    corto: z.string().optional(),
    siglas: z.array(z.string()).min(1, { error: 'pon al menos unas siglas' }),
    tipo: z.enum(['partido', 'coalición', 'federación', 'agrupación']).optional(),
    inclusion: z.object({ motivo: z.string().min(1), fuente: enlace }),
    escanos_23j: z.object({ valor: z.number().int().min(0), nota: z.string().optional() }).optional(),
    integrantes: z.array(z.string()).default([]),
    marcas_territoriales: z
      .array(z.object({ nombre: z.string(), ambito: z.string(), siglas: z.array(z.string()).default([]) }))
      .default([]),
    candidatura_presidencia: dato,
    web: dato,
    programa: dato,
    redes: z.array(z.object({ red: z.string(), url: enlace })).default([]),
  }),
});

const hallazgo = z.object({
  id: z.string(),
  titulo: z.string(),
  seccion: z.string().nullable(),
  departamento: z.string().nullable(),
  url_html: z.string(),
  url_pdf: z.string().nullable(),
  etiquetas: z.array(z.string()),
});

const boe = defineCollection({
  loader: glob({ pattern: '*.json', base: `${DATOS}/boe` }),
  schema: z.object({ fecha: z.string(), disposiciones_revisadas: z.number(), hallazgos: z.array(hallazgo) }),
});

const persona = z.object({ nombre: z.string(), suplentes: z.array(z.string()).optional() });
const candidaturas = defineCollection({
  loader: glob({ pattern: '*.json', base: CANDIDATURAS }),
  schema: z.object({
    fase: z.enum(['presentadas', 'proclamadas']),
    fuente: z.object({ id: z.string(), titulo: z.string(), fecha_publicacion: z.string(), url: z.string(), url_pdf: z.string() }),
    candidaturas: z.array(
      z.object({
        provincia: z.string(),
        camara: z.enum(['congreso', 'senado']),
        isla: z.string().nullable(),
        orden: z.number(),
        nombre: z.string(),
        siglas: z.string(),
        proclamada: z.boolean(),
        candidatos: z.array(persona),
        suplentes: z.array(z.string()),
      }),
    ),
  }),
});

// Correcciones de errores de las candidaturas: no se aplican solas, se enlazan en cada provincia afectada.
const correcciones = defineCollection({
  loader: glob({ pattern: '*.json', base: CORRECCIONES }),
  schema: z.object({
    fase: z.enum(['presentadas', 'proclamadas']),
    fuente: z.object({ id: z.string(), titulo: z.string(), fecha_publicacion: z.string(), url: z.string() }),
    provincias: z.array(z.string()),
  }),
});

const circunscripciones = defineCollection({
  loader: file(`${DATOS}/circunscripciones.json`, { parser: (t) => JSON.parse(t).circunscripciones }),
  schema: z.object({
    nombre: z.string(),
    abreviatura: z.string(),
    diputados: z.number(),
    senadores: z.number(),
    senado_islas: z.array(z.object({ isla: z.string(), senadores: z.number() })),
    mapa: z.object({ columna: z.number(), fila: z.number() }),
  }),
});

// Las listas YAML (calendario, debates) no llevan id: se numeran al leerlas.
const lista = (texto: string) =>
  ((parse(texto) as Record<string, unknown>[] | null) ?? []).map((e, i) => ({ id: String(i).padStart(3, '0'), ...e }));

const calendario = defineCollection({
  loader: file(`${DATOS}/calendario.yaml`, { parser: lista }),
  schema: z.object({
    fecha,
    hasta: fecha.optional(),
    texto: z.string(),
    aproximada: z.boolean().default(false),
    destacada: z.boolean().default(false),
    fuente: enlace.optional(),
  }),
});

const debates = defineCollection({
  loader: file(`${DATOS}/debates.yaml`, { parser: lista }),
  schema: z.object({
    fecha,
    hora: z.string().optional(),
    titulo: z.string(),
    medio: z.string(),
    participantes: z.array(z.string()).default([]),
    fuente: enlace,
  }),
});

// Glosario: cada término con su id fijo (para /glosario#id y <Termino id="..."/>) y su fuente.
const glosario = defineCollection({
  loader: file(`${DATOS}/glosario.yaml`, { parser: (texto: string) => (parse(texto) as Record<string, unknown>[] | null) ?? [] }),
  schema: z.object({ termino: z.string().min(1), definicion: z.string().min(1), fuente: enlace }),
});

export const collections = { formaciones, boe, candidaturas, correcciones, circunscripciones, calendario, debates, glosario };
