# Papeleta Blanca

**[papeletablanca.es](https://papeletablanca.es)** · Web ciudadana y apolítica para seguir las elecciones generales del **29 de noviembre de 2026**: calendario, qué se vota en cada provincia, quién se presenta y qué publica el BOE cada día. No opina, no resume programas y no publica encuestas. Cada dato enlaza a su fuente.

> **Desvinculación.** Papeleta Blanca no está vinculada a ningún partido, coalición, candidatura ni organización política, ni a ninguna ideología u orientación política. El nombre se refiere solo al color de la papeleta del Congreso: no tiene relación con el voto en blanco ni con ninguna formación que use esa palabra en su nombre. No promovemos ninguna opción de voto.

Las reglas de neutralidad están en la propia web, en la página **Cómo funciona** ([web/src/pages/metodologia.astro](web/src/pages/metodologia.astro)).

## Cómo está hecho

```
radar.py            Lee el sumario diario del BOE y aparta lo electoral   → datos/boe/
candidaturas.py     Copia las listas de candidatos que publica el BOE     → datos/candidaturas/
datos/              Todo lo que muestra la web. Lo que se edita a mano:
  formaciones/        una ficha por formación (.yaml)  ← aquí trabajas tú
  calendario.yaml     fechas clave
  debates.yaml        agenda de debates
  circunscripciones.json  escaños por provincia (Real Decreto 806/2026; no tocar)
web/                La web (Astro). Lee datos/ y genera páginas estáticas.
tests/              Pruebas con datos reales del BOE.
.github/workflows/  GitHub lo ejecuta todo solo cada día y publica la web.
```

Coste: 0 €. Sin servidor ni base de datos: GitHub Actions revisa el BOE dos veces al día, guarda los datos y publica la web en GitHub Pages.

## Ver la web en tu ordenador

Necesitas Node.js 22.22 o superior (ya lo tienes) y Python 3.10 o superior (también).

```
cd web
npm install        # solo la primera vez
npm run dev        # abre http://localhost:4321 y se recarga sola al guardar cambios
```

El buscador solo funciona tras `npm run build` y `npm run preview`.

## Editar una ficha de formación

1. Abre `datos/formaciones/` en VS Code. Las instrucciones están en `_plantilla.yaml`.
2. Cambia un dato. Ejemplo, cuando una formación confirma su candidatura:
   ```yaml
   candidatura_presidencia:
     valor: Nombre Apellido
     estado: confirmado
     fuente: https://enlace-a-la-nota-oficial
     fecha: 2026-10-20
   ```
3. Mira cómo queda con `npm run dev`. Si te equivocas (por ejemplo, falta la fuente), la web te dice qué fichero y qué campo hay que corregir.
4. Súbelo:
   ```
   git add datos
   git commit -m "Ficha de X: candidatura confirmada"
   git push
   ```
   En unos minutos la web pública se actualiza sola.

**Regla de oro:** sin fuente no hay dato. Lo que no esté confirmado por la formación o por el BOE, o publicado en prensa con enlace, se queda en `pendiente`.

## Ponerlo en GitHub la primera vez

1. En la organización `papeletablanca` de GitHub, crea un repositorio **público** vacío llamado `web` (sin README ni licencia: ya están aquí).
2. Desde esta carpeta:
   ```
   git remote add origin https://github.com/papeletablanca/web.git
   git push -u origin main
   ```
3. En el repositorio: **Settings → Pages → Source: GitHub Actions**.
4. **Settings → Actions → General → Workflow permissions → Read and write permissions**.
5. Pestaña **Actions → Papeleta Blanca → Run workflow**. En «desde» escribe `2026-10-06` para revisar todo el BOE desde la convocatoria.
6. **Dominio propio:** en **Settings → Pages → Custom domain** escribe `papeletablanca.es`. En Hostinger, en la zona DNS del dominio, borra los registros de aparcamiento y añade los cuatro registros `A` de GitHub Pages (185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153) y un `CNAME` de `www` a `papeletablanca.github.io`. Cuando GitHub lo verifique, marca **Enforce HTTPS**.

La configuración de git de esta carpeta firma los cambios como «Papeleta Blanca» (`git config --local`), sin tu nombre.

## Comandos de los datos

```
python radar.py                         # BOE de hoy
python radar.py --desde 2026-10-06      # desde la convocatoria hasta hoy
python candidaturas.py --desde 2026-10-26   # busca las listas de candidatos en esos días
python candidaturas.py --id BOE-A-...   # procesa una disposición concreta
python -m unittest discover tests       # pruebas, sin conexión
```

Para ver las páginas de provincia con listas antes de que el BOE publique las de 2026, puedes probar con las de 2023 (no las subas a `datos/`):

```
python candidaturas.py --id BOE-A-2023-15066 --salida ../prueba-2023
cd web && CANDIDATURAS_PRUEBA=../../prueba-2023 npm run dev
```

## Cómo decide el radar qué es «electoral»

Las reglas están al principio de `radar.py` (`REGLAS` y `EXCLUSIONES`), en expresiones legibles, y se aplican igual a todo lo que publica el BOE. Las pruebas de `tests/test_radar.py` incluyen títulos reales que sí y que no deben aparecer. Si algo falta o sobra, se cambia ahí y queda en el historial público.

Limitaciones: el radar solo lee los títulos. Los boletines provinciales y autonómicos no se revisan.

## Fechas clave del proyecto

| Fecha | Qué pasa |
|---|---|
| hasta el 27 oct | Rellenar las fichas de las formaciones, con fuente |
| ≈28 oct | El BOE publica las candidaturas presentadas: se cargan solas |
| ≈3 nov | El BOE publica las proclamadas: páginas de provincia completas. **Lanzamiento** |
| 13–27 nov | Campaña: agenda de debates, novedades de la Junta Electoral |
| 29 nov | Enlace a los resultados oficiales de Interior |

## Licencias

| Qué | Licencia |
|---|---|
| Código (Python y web) | [MIT](LICENSE) |
| Textos propios y fichas de `datos/formaciones/` | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.es): se pueden reutilizar citando a Papeleta Blanca |
| Datos del BOE (`datos/boe/`, `datos/candidaturas/`, escaños) | Los del BOE, según sus [condiciones de reutilización](https://www.boe.es/datosabiertos/). Se citan siempre con su identificador |

Este proyecto no está afiliado al BOE, a ningún organismo público ni a ninguna formación política.

## Créditos

El código y los textos generales los ha escrito **Claude** (Anthropic), con dirección y revisión del equipo de Papeleta Blanca. Los commits hechos con Claude lo indican con `Co-Authored-By`. Los datos de las fichas los revisa una persona, uno a uno, con su fuente.
