# Papeleta Blanca

**[papeletablanca.es](https://papeletablanca.es)** reúne en un solo sitio la información oficial sobre las elecciones generales del **29 de noviembre de 2026**: el calendario, los escaños que se eligen en cada provincia, las candidaturas que se presentan y lo que publica el BOE cada día.

No opina, no resume programas y no publica encuestas. Cada dato enlaza a su fuente.

> **Sin vínculos políticos.** Papeleta Blanca es un proyecto ciudadano independiente. No está vinculada a ningún partido, coalición, candidatura u organización política, ni a ninguna ideología. El nombre alude al color de la papeleta del Congreso: no tiene relación con el voto en blanco ni con ninguna formación que use esa palabra en su nombre, y no promueve ninguna opción de voto.

## Reglas de neutralidad

- **Quién aparece.** Hasta la proclamación de candidaturas, las formaciones con escaño en la legislatura saliente y las que anuncien públicamente que se presentan. Después, todas las candidaturas que proclame el BOE, sin excepción.
- **En qué orden.** Alfabético en las listas generales; en cada provincia, el orden en que las publica el BOE. Nunca por votos ni por encuestas.
- **Con qué aspecto.** El mismo para todas: sin logos ni colores de partido.
- **Sin fuente no hay dato.** Cada dato de una ficha lleva su enlace. Ninguno lo redacta una inteligencia artificial.

La versión completa está en la página [Cómo funciona](https://papeletablanca.es/metodologia/).

## De dónde salen los datos

| Dato | Origen | Cómo se actualiza |
|---|---|---|
| Novedades del BOE | [API de datos abiertos del BOE](https://www.boe.es/datosabiertos/) | Automático, dos veces al día |
| Candidaturas y listas por provincia | Disposiciones del BOE de las Juntas Electorales Provinciales | Automático, en cuanto se publican |
| Escaños por provincia y calendario | [Real Decreto 806/2026](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-20742) y [LOREG](https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672) | A mano |
| Fichas de las formaciones | Fuentes oficiales de cada formación, el BOE o prensa enlazada | A mano, dato a dato |

Todo se ejecuta en GitHub Actions y se publica en GitHub Pages, sin servidor ni base de datos. El historial de este repositorio registra cada cambio en los datos.

## ¿Has visto un error?

[Abre una incidencia](https://github.com/papeletablanca/web/issues) con el enlace a la fuente correcta. Las correcciones se hacen a la vista de todos.

## Estructura del repositorio

```
radar.py              Lee el sumario diario del BOE y aparta lo electoral   → datos/boe/
candidaturas.py       Convierte las listas de candidatos del BOE en datos   → datos/candidaturas/
datos/
  formaciones/        Una ficha por formación (.yaml). Se editan a mano
  calendario.yaml     Fechas clave
  debates.yaml        Agenda de debates
  circunscripciones.json  Escaños por provincia (Real Decreto 806/2026)
web/                  La web (Astro). Lee datos/ y genera páginas estáticas
tests/                Pruebas con datos reales del BOE
.github/workflows/    Revisión diaria del BOE y publicación de la web
```

## Ejecutarlo en local

Requisitos: Node.js 22.22 o superior y Python 3.10 o superior. Los scripts de Python solo usan la biblioteca estándar.

```
cd web
npm install
npm run dev        # http://localhost:4321, se recarga al guardar
```

El buscador solo funciona con la web construida: `npm run build` y después `npm run preview`.

### Comandos de datos

```
python radar.py                             # BOE de hoy
python radar.py --desde 2026-10-06          # desde la convocatoria hasta hoy
python candidaturas.py --desde 2026-10-26   # busca las listas de candidatos en ese rango
python candidaturas.py --id BOE-A-...       # procesa una disposición concreta
python -m unittest discover tests           # pruebas, sin conexión
```

Para ver las páginas de provincia con listas antes de que el BOE publique las de 2026 se pueden usar las de 2023, guardadas fuera de `datos/`:

```
python candidaturas.py --id BOE-A-2023-15066 --salida ../prueba-2023
cd web
CANDIDATURAS_PRUEBA=../../prueba-2023 npm run dev
```

En PowerShell, la última línea es `$env:CANDIDATURAS_PRUEBA="../../prueba-2023"; npm run dev`.

## Editar una ficha de formación

Las fichas están en `datos/formaciones/`. La plantilla, con instrucciones, es `_plantilla.yaml`. Cada dato tiene un estado:

- `confirmado`: lo dice la propia formación o el BOE.
- `anunciado`: lo ha publicado la prensa (se enlaza la noticia).
- `pendiente`: todavía no se sabe.

Todo dato que no esté `pendiente` necesita `fuente` y `fecha`. Por ejemplo:

```yaml
candidatura_presidencia:
  valor: Nombre Apellido
  estado: confirmado
  fuente: https://enlace-a-la-nota-oficial
  fecha: 2026-10-20
```

Si una ficha está mal escrita (por ejemplo, falta la fuente), `npm run dev` y `npm run build` indican qué fichero y qué campo hay que corregir. Al subir el cambio a `main`, la web se regenera sola en unos minutos.

## Cómo decide el radar qué es «electoral»

Las reglas están al principio de [radar.py](radar.py), en `REGLAS` y `EXCLUSIONES`, como expresiones legibles que se aplican igual a todo lo que publica el BOE. [tests/test_radar.py](tests/test_radar.py) incluye títulos reales que deben aparecer y otros que no. Si algo falta o sobra, se corrige ahí y el cambio queda en el historial público.

Limitaciones: el radar solo lee los títulos de las disposiciones y no revisa los boletines autonómicos ni provinciales.

## Calendario

| Fecha | Qué cambia en la web |
|---|---|
| hasta el 27 oct | Se completan las fichas de las formaciones |
| ≈28 oct | El BOE publica las candidaturas presentadas y aparecen las listas |
| ≈3 nov | El BOE publica las candidaturas proclamadas y se completan las páginas de provincia |
| 13–27 nov | Campaña: agenda de debates y novedades de la Junta Electoral |
| 29 nov | Enlace a los resultados oficiales del Ministerio del Interior |

## Licencias

| Qué | Licencia |
|---|---|
| Código (Python y web) | [MIT](LICENSE) |
| Textos propios y fichas de `datos/formaciones/` | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.es): se pueden reutilizar citando a Papeleta Blanca |
| Datos del BOE (`datos/boe/`, `datos/candidaturas/`, escaños) | Sujetos a las [condiciones de reutilización del BOE](https://www.boe.es/datosabiertos/). Se citan siempre con su identificador |

Papeleta Blanca no está afiliada al BOE ni a ningún organismo público.

## Créditos

El código y los textos generales se han escrito con ayuda de inteligencia artificial (Claude, de Anthropic) y se revisan a mano. Los commits hechos con Claude lo indican con `Co-Authored-By`. Los datos de las fichas los revisa una persona, uno a uno, con su fuente.
