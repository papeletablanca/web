#!/usr/bin/env python3
"""Radar del BOE (Papeleta Blanca): lee el sumario diario del BOE y extrae lo relacionado con elecciones.

Uso:
    python radar.py                    # sumario de hoy (hora de Madrid)
    python radar.py --fecha 2026-10-06 # un dia concreto
    python radar.py --desde 2026-10-06 --hasta 2026-10-16   # un rango
    python radar.py --fichero sumario.json --fecha 2026-10-06  # sin red, desde un fichero

Escribe un JSON por dia en datos/boe/. La web (carpeta web/) los lee.
Solo usa la biblioteca estandar de Python (3.10 o superior). No necesita instalar nada.
Fuente: API de datos abiertos del BOE (https://www.boe.es/datosabiertos/).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

API_SUMARIO = "https://www.boe.es/datosabiertos/api/boe/sumario/{aaaammdd}"
USER_AGENT = "papeletablanca/0.2 (proyecto ciudadano de datos abiertos; https://papeletablanca.es)"

# Cada regla: etiqueta legible -> patrones (sobre texto sin tildes y en minusculas).
# Usa \b (limite de palabra) en los patrones cortos: "cera" sin \b tambien encaja en "tercera" o "acera".
REGLAS: dict[str, list[str]] = {
    "Convocatoria": [r"disolucion del congreso", r"convocatoria de elecciones"],
    "Junta Electoral": [r"junta electoral", r"juntas electorales"],
    "Candidaturas": [r"candidaturas (presentadas|proclamadas)", r"candidatos? electos?"],
    "Censo y voto": [r"censo electoral", r"voto por correo", r"voto de los espanoles", r"\bcera\b", r"mesas electorales", r"voto en urna"],
    "Ley electoral": [r"regimen electoral general", r"\bloreg\b", r"ley organica 5/1985"],
    "Financiación": [r"financiacion de los partidos", r"subvenciones? (electorales|por gastos electorales|a los gastos)", r"gastos electorales", r"actividades electorales"],
    "Resultados": [r"escrutinio", r"resultados? de las elecciones", r"diputados electos", r"senadores electos"],
    "Elecciones": [r"\belecciones (generales|a cortes generales|al congreso)", r"proceso electoral", r"\belectoral(es)?\b"],
}
# Coincidencias que no tienen que ver con el 29N.
EXCLUSIONES = [
    r"sindical", r"elecciones? a (organos|representantes) de", r"colegio (oficial|profesional)", r"universidad",
    r"designacion de concejal",  # sustituciones en ayuntamientos: son municipales
    r"\boposicion\b", r"\bprocesos? selectivos?\b",  # oposiciones de las Cortes Generales
]


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", sin_tildes.lower())


def clasificar(titulo: str) -> list[str]:
    t = normalizar(titulo)
    if any(re.search(p, t) for p in EXCLUSIONES):
        return []
    etiquetas = [nombre for nombre, patrones in REGLAS.items() if any(re.search(p, t) for p in patrones)]
    # "Elecciones" solo si no hay ninguna etiqueta mas concreta.
    if len(etiquetas) > 1 and "Elecciones" in etiquetas:
        etiquetas.remove("Elecciones")
    return etiquetas


def _url(valor) -> str | None:
    if isinstance(valor, str):
        return valor
    if isinstance(valor, dict):
        return valor.get("texto") or valor.get("#text")
    return None


def recorrer(nodo, contexto: dict | None = None):
    """Recorre el JSON del sumario sin depender de su forma exacta.

    Devuelve cada disposicion (un dict con 'identificador' y 'titulo') junto con
    la seccion y el departamento en que aparece.
    """
    contexto = dict(contexto or {})
    if isinstance(nodo, dict):
        if "identificador" in nodo and "titulo" in nodo:
            yield {
                "id": nodo["identificador"],
                "titulo": str(nodo["titulo"]).strip(),
                "seccion": contexto.get("seccion"),
                "departamento": contexto.get("departamento"),
                "url_html": _url(nodo.get("url_html")),
                "url_pdf": _url(nodo.get("url_pdf")),
            }
            return
        for clave, valor in nodo.items():
            elementos = valor if isinstance(valor, list) else [valor]
            for elem in elementos:
                if not isinstance(elem, (dict, list)):
                    continue
                sub = dict(contexto)
                if clave in ("seccion", "departamento") and isinstance(elem, dict) and elem.get("nombre"):
                    sub[clave] = elem["nombre"]
                yield from recorrer(elem, sub)
    elif isinstance(nodo, list):
        for elem in nodo:
            yield from recorrer(elem, contexto)


def descargar(url: str, accept: str = "application/json") -> bytes:
    peticion = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": USER_AGENT})
    with urllib.request.urlopen(peticion, timeout=60) as respuesta:
        return respuesta.read()


def descargar_sumario(dia: date) -> dict | None:
    try:
        return json.loads(descargar(API_SUMARIO.format(aaaammdd=dia.strftime("%Y%m%d"))))
    except urllib.error.HTTPError as error:
        if error.code == 404:  # no hay BOE ese dia (domingos y algunos festivos)
            return None
        raise


def analizar(sumario: dict, dia: date) -> dict:
    vistos: set[str] = set()
    hallazgos = []
    total = 0
    for disp in recorrer(sumario):
        if disp["id"] in vistos:
            continue
        vistos.add(disp["id"])
        total += 1
        etiquetas = clasificar(disp["titulo"])
        if etiquetas:
            disp["etiquetas"] = etiquetas
            disp["url_html"] = disp["url_html"] or f"https://www.boe.es/diario_boe/txt.php?id={disp['id']}"
            hallazgos.append(disp)
    return {"fecha": dia.isoformat(), "disposiciones_revisadas": total, "hallazgos": hallazgos}


def resumen_texto(informe: dict) -> str:
    lineas = [f"BOE del {informe['fecha']}: {len(informe['hallazgos'])} novedades de {informe['disposiciones_revisadas']} disposiciones"]
    for h in informe["hallazgos"]:
        lineas.append(f"  - [{', '.join(h['etiquetas'])}] {h['titulo'][:140]} ({h['id']})")
    return "\n".join(lineas)


def hoy_madrid() -> date:
    # Aproximacion sin dependencias: Madrid es UTC+1 en invierno y UTC+2 en verano.
    ahora = datetime.now(timezone.utc)
    ultimo_domingo = lambda y, m: max(date(y, m, d) for d in range(25, 32) if date(y, m, d).weekday() == 6)
    verano = ultimo_domingo(ahora.year, 3) <= ahora.date() < ultimo_domingo(ahora.year, 10)
    return (ahora + timedelta(hours=2 if verano else 1)).date()


def dias_pedidos(args) -> list[date]:
    if args.desde:
        fin = args.hasta or hoy_madrid()
        return [args.desde + timedelta(n) for n in range((fin - args.desde).days + 1)]
    return [args.fecha or hoy_madrid()]


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fecha", type=date.fromisoformat, help="día del BOE (AAAA-MM-DD); por defecto, hoy")
    p.add_argument("--desde", type=date.fromisoformat, help="primer día de un rango")
    p.add_argument("--hasta", type=date.fromisoformat, help="último día de un rango (por defecto, hoy)")
    p.add_argument("--fichero", type=Path, help="leer el sumario de un fichero JSON en vez de la API")
    p.add_argument("--salida", type=Path, default=Path("datos/boe"), help="carpeta de resultados (por defecto datos/boe)")
    args = p.parse_args(argv)

    args.salida.mkdir(parents=True, exist_ok=True)
    for dia in dias_pedidos(args):
        if args.fichero:
            sumario = json.loads(args.fichero.read_text(encoding="utf-8"))
        else:
            sumario = descargar_sumario(dia)
        if sumario is None:
            print(f"{dia}: no hay BOE ese día")
            continue
        informe = analizar(sumario, dia)
        (args.salida / f"{dia.isoformat()}.json").write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        print(resumen_texto(informe))
    return 0


if __name__ == "__main__":
    sys.exit(main())
