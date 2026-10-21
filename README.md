# Papeleta Blanca

[![Papeleta Blanca](https://github.com/papeletablanca/web/actions/workflows/radar.yml/badge.svg)](https://github.com/papeletablanca/web/actions/workflows/radar.yml)

[![RSS](https://img.shields.io/badge/rss-%23F88900.svg?style=for-the-badge&logo=rss&logoColor=white)](https://papeletablanca.es/feed.xml)
![Python](https://img.shields.io/badge/python-%233776AB.svg?style=for-the-badge&logo=python&logoColor=white)
![Astro](https://img.shields.io/badge/astro-%232C2052.svg?style=for-the-badge&logo=astro&logoColor=white)
![NPM](https://img.shields.io/badge/NPM-%23CB3837.svg?style=for-the-badge&logo=npm&logoColor=white)
![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)
![GitHub Pages](https://img.shields.io/badge/github_pages-%23222222.svg?style=for-the-badge&logo=githubpages&logoColor=white&logoSize=auto)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-%23D97757.svg?style=for-the-badge&logo=claudecode&logoColor=white)](#créditos)
![TypeScript](https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white)

**[papeletablanca.es](https://papeletablanca.es)** reúne en un solo sitio la información oficial sobre las elecciones generales del **29 de noviembre de 2026**: el calendario, los escaños que se eligen en cada provincia, las candidaturas que se presentan y lo que publica el BOE cada día.

No opina, no resume programas y no publica encuestas. Cada dato enlaza a su fuente.

> **Sin vínculos políticos.** Papeleta Blanca es un proyecto ciudadano independiente. No está vinculada a ningún partido, coalición, candidatura u organización política, ni a ninguna ideología. El nombre alude al color de la papeleta del Congreso: no tiene relación con el voto en blanco ni con ninguna formación que use esa palabra en su nombre, y no promueve ninguna opción de voto.

## Reglas de neutralidad

- **Quién aparece.** Hasta la proclamación de candidaturas, las formaciones que obtuvieron diputado en el Congreso el 23 de julio de 2023 y las que anuncien públicamente que se presentan. Después, todas las candidaturas que proclame el BOE, sin excepción.
- **En qué orden.** Alfabético en las listas generales; en cada provincia, el orden en que las publica el BOE. Nunca por votos ni por encuestas.
- **Con qué aspecto.** El mismo para todas: sin logos ni colores de partido.
- **Sin fuente no hay dato.** Cada dato de una ficha lleva su enlace. Ninguno lo redacta una inteligencia artificial.

La versión completa está en la página [Cómo funciona](https://papeletablanca.es/metodologia/).

## De dónde salen los datos

| Dato | Origen | Cómo se actualiza |
|---|---|---|
| Novedades del BOE | [API de datos abiertos del BOE](https://www.boe.es/datosabiertos/) | Automático, dos veces al día |
| Polémicas en curso | [Acuerdos de la Junta Electoral Central](https://www.juntaelectoralcentral.es/cs/jec/doctrina/acuerdos) y novedades del BOE sobre tribunales | Automático, dos veces al día |
| Candidaturas y listas por provincia | Disposiciones del BOE de las Juntas Electorales Provinciales | Automático, en cuanto se publican |
| Escaños por provincia y calendario | [Real Decreto 806/2026](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-20742) y [LOREG](https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672) | A mano |
| Fichas de las formaciones | Fuentes oficiales de cada formación, el BOE o prensa enlazada | A mano, dato a dato |

Las candidaturas (completas y por provincia), las novedades, las polémicas y los escaños se pueden descargar en CSV desde [Para medios y datos](https://papeletablanca.es/para-medios/). Se generan en cada publicación con [web/src/pages/datos/](web/src/pages/datos/).

Todo se ejecuta en GitHub Actions y se publica en GitHub Pages, sin servidor ni base de datos. El historial de este repositorio registra cada cambio en los datos.

## ¿Has visto un error?

[Abre una incidencia](https://github.com/papeletablanca/web/issues) con el enlace a la fuente correcta. Las correcciones se hacen a la vista de todos.

## Accesibilidad

La información electoral es de todo el mundo. Una web que cuenta qué se vota, quién se presenta y cómo votar no es neutral si una parte del electorado no puede usarla. Por eso la accesibilidad sigue la misma regla que los datos: lo que se afirma aquí se puede comprobar, y lo que falta se dice.

**Objetivo:** cumplir el nivel AA de las [Pautas de Accesibilidad WCAG 2.2](https://www.w3.org/TR/WCAG22/). No hay una auditoría externa: las comprobaciones de esta sección las hace el propio proyecto y se repiten cuando cambia el diseño.

### Lo que hace la web

- **Contraste medido, no estimado.** El texto principal tiene un contraste de 15:1 o más con el fondo, y el secundario, de 6:1 o más. El texto de las casillas del mapa nunca baja de 4,8:1, en ningún tema. Los colores están en [web/src/styles/global.css](web/src/styles/global.css).
- **Nada depende solo del color.** El mapa lleva escrito el número de diputados de cada provincia. Los estados de las fichas (confirmado, anunciado, pendiente) se distinguen por el texto y la forma del borde. Las fechas pasadas del calendario tienen un círculo relleno y las futuras, hueco. Los enlaces del texto están subrayados; las tarjetas, las casillas del mapa y el menú se reconocen por su forma. Se ha comprobado con simulaciones de protanopia, deuteranopia, tritanopia y visión sin color.
- **Sin colores de partido.** Todas las formaciones tienen el mismo aspecto. Es una regla de neutralidad, y además evita las combinaciones de colores que más confunden (rojo y verde, azul y morado).
- **Se puede usar solo con teclado.** Hay un enlace «Saltar al contenido», el foco siempre está visible y el mapa de provincias responde igual al tabulador que al ratón.
- **Pensada para lectores de pantalla.** La página está marcada en español, el mapa y los gráficos tienen descripciones de texto, y la información que aparece al recorrer el mapa se anuncia en voz alta.
- **Respeta las preferencias del sistema:** tema claro u oscuro y «reducir movimiento».
- **Se adapta al móvil.** La página nunca se desplaza en horizontal; solo el menú y el calendario se deslizan dentro de su espacio.

### Panel de accesibilidad

El botón con el símbolo de accesibilidad, a la derecha del menú, abre un panel con estas opciones:

- tamaño del texto (100 %, 115 %, 130 % o 150 %);
- tema (automático, claro u oscuro);
- más contraste;
- subrayar los enlaces;
- más espacio entre letras y líneas, con los valores del criterio WCAG 1.4.12;
- tipografía sencilla;
- reducir las animaciones.

Las opciones se guardan solo en el navegador de cada persona. No se envían a ningún sitio. El panel complementa a la web, pero no la sustituye: todo lo anterior funciona sin tocarlo.

No incluye un «filtro para daltónicos». Esos filtros recolorean la página, pero no ayudan a quien ya distingue la información por algo más que el color, que es lo que esta web garantiza.

### Lo que falta o no depende de nosotros

- **Lectores de pantalla.** La web aún no se ha probado con NVDA, JAWS, VoiceOver o TalkBack. Está previsto antes del lanzamiento.
- **Documentos del BOE.** Las disposiciones y los PDF que se enlazan son del BOE, y su accesibilidad depende del BOE.
- **Nombres de las listas.** Los nombres de candidaturas y candidatos se copian tal y como los publica el BOE, sin corregirlos.
- **Calendario.** En el móvil, y en el ordenador con el texto ampliado, el calendario se desliza en horizontal para que las fechas no se monten unas sobre otras. Hay que desplazarlo para ver las últimas. No tiene barra de desplazamiento: se mueve con el dedo, arrastrando con el ratón, acercando el cursor a un borde, con las flechas de los bordes (que solo aparecen si hay más fechas) o con las flechas del teclado, porque la caja recibe el foco. Con «Reducir las animaciones», el cursor en el borde no lo mueve.

### Si algo no te funciona

[Abre una incidencia](https://github.com/papeletablanca/web/issues) contando qué página es, qué intentabas hacer y con qué lo usas: navegador, lector de pantalla, ampliador… Una barrera de accesibilidad se trata como un error en los datos: se corrige con prioridad y a la vista de todos.

## Estructura del repositorio

```
radar.py              Lee el sumario diario del BOE y aparta lo electoral   → datos/boe/
candidaturas.py       Convierte las listas de candidatos del BOE en datos   → datos/candidaturas/
jec.py                Aparta las polémicas de los acuerdos de la Junta Electoral Central → datos/jec/
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
python jec.py                               # acuerdos de la Junta Electoral Central desde la convocatoria
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
programa:
  valor: https://enlace-al-programa.pdf
  estado: confirmado
  fuente: https://enlace-a-la-nota-oficial
  fecha: 2026-10-20
```

Quién encabeza cada lista no se escribe a mano: sale del BOE cuando publica las candidaturas, igual para todas las formaciones.

Si una ficha está mal escrita (por ejemplo, falta la fuente), `npm run dev` y `npm run build` indican qué fichero y qué campo hay que corregir. Al subir el cambio a `main`, la web se regenera sola en unos minutos.

## Cómo decide el radar qué es «electoral»

Las reglas están al principio de [radar.py](radar.py), en `REGLAS` y `EXCLUSIONES`, como expresiones legibles que se aplican igual a todo lo que publica el BOE. [tests/test_radar.py](tests/test_radar.py) incluye títulos reales que deben aparecer y otros que no. Si algo falta o sobra, se corrige ahí y el cambio queda en el historial público.

Limitaciones: el radar solo lee los títulos de las disposiciones y no revisa los boletines autonómicos ni provinciales.

## Cómo decide qué es una «polémica»

[jec.py](jec.py) lee los acuerdos de la Junta Electoral Central desde la convocatoria (5 de octubre de 2026). Entra un acuerdo si cumple las dos condiciones:

1. La propia Junta lo asocia al proceso «Elecciones Generales 2026 (Cortes Generales)» (campo «Proceso electoral asociado» de cada acuerdo).
2. Su objeto es una denuncia, queja, recurso, reclamación o impugnación, o tiene que ver con la resolución de un tribunal (`CONFLICTO`, al principio de `jec.py`).

Se copian sin resumir el objeto, el autor tal como lo publica la Junta (que no da nombres de particulares) y el texto del acuerdo. La página añade las novedades del BOE cuyo título menciona un auto, una sentencia, un recurso, el Tribunal Supremo o el Constitucional.

`jec.py` también guarda en `datos/coaliciones.json` la [relación oficial de coaliciones](https://www.juntaelectoralcentral.es/cs/jec/elecciones/coalicionesJEC?fechaeleccion=2026-11-29&tipoeleccion=Elecciones%20Generales) válidamente constituidas ante la Junta (nombre, siglas, ámbito y enlace al pacto). La web la usa para enlazar las listas de una coalición con las fichas de sus integrantes. Una ficha forma parte de una coalición si sus siglas o su nombre aparecen tal cual en el nombre o las siglas oficiales, separados por guiones, comas o paréntesis (`coalicionesDe` en [web/src/lib/datos.ts](web/src/lib/datos.ts)). Las coaliciones que solo concurren en una provincia se inscriben en su Junta Provincial y no están en esa relación.

Limitación: si la Junta no asocia un acuerdo a estas elecciones, no entra aunque hable de ellas. Por ejemplo, el recurso de Valores (acuerdo 245/2026) no tiene proceso asociado. [tests/test_jec.py](tests/test_jec.py) lo comprueba con páginas reales de la Junta.

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
