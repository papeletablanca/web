#!/usr/bin/env python3
"""Candidaturas 29N: convierte las listas que publica el BOE en datos para la web.

Las Juntas Electorales Provinciales publican en el BOE, en una sola disposicion, todas las
candidaturas al Congreso y al Senado: primero las presentadas y unos dias despues las proclamadas.

Uso:
    python candidaturas.py                         # busca en el BOE de hoy
    python candidaturas.py --desde 2026-10-26      # busca en un rango de dias
    python candidaturas.py --id BOE-A-2023-15066   # procesa una disposicion concreta
    python candidaturas.py --fichero lista.xml     # sin red, desde un XML ya descargado

Escribe datos/candidaturas/{presentadas,proclamadas}.json. Solo biblioteca estandar.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import radar

URL_XML = "https://www.boe.es/diario_boe/xml.php?id={id}"
TITULO = re.compile(r"^candidaturas (presentadas|proclamadas) para las? elecciones al congreso")

# Nombre con el que cada junta aparece en el BOE (sin tildes, minusculas) -> id de circunscripcion.
# Los ids son los de datos/circunscripciones.json.
JUNTAS = {
    "albacete": "albacete", "alicante": "alicante", "alicante/alacant": "alicante", "almeria": "almeria",
    "alava": "araba", "araba": "araba", "araba/alava": "araba", "asturias": "asturias", "avila": "avila",
    "badajoz": "badajoz", "baleares": "baleares", "illes balears": "baleares", "balears": "baleares",
    "barcelona": "barcelona", "bizkaia": "bizkaia", "vizcaya": "bizkaia", "burgos": "burgos",
    "caceres": "caceres", "cadiz": "cadiz", "cantabria": "cantabria", "castellon": "castellon",
    "castellon/castello": "castellon", "ciudad real": "ciudadreal", "cordoba": "cordoba",
    "a coruna": "coruna", "la coruna": "coruna", "coruna": "coruna", "cuenca": "cuenca",
    "gipuzkoa": "gipuzkoa", "guipuzcoa": "gipuzkoa", "girona": "girona", "granada": "granada",
    "guadalajara": "guadalajara", "huelva": "huelva", "huesca": "huesca", "jaen": "jaen", "leon": "leon",
    "lleida": "lleida", "lugo": "lugo", "madrid": "madrid", "malaga": "malaga", "murcia": "murcia",
    "region de murcia": "murcia", "navarra": "navarra", "ourense": "ourense", "palencia": "palencia",
    "las palmas": "laspalmas", "pontevedra": "pontevedra", "la rioja": "rioja", "salamanca": "salamanca",
    "santa cruz de tenerife": "tenerife", "segovia": "segovia", "sevilla": "sevilla", "soria": "soria",
    "tarragona": "tarragona", "teruel": "teruel", "toledo": "toledo", "valencia": "valencia",
    "valencia/valencia": "valencia", "valladolid": "valladolid", "zamora": "zamora", "zaragoza": "zaragoza",
    "ceuta": "ceuta", "melilla": "melilla",
}

RE_JUNTA = re.compile(r"^junta electoral (?:provincial )?de (.+)$")
RE_ISLA = re.compile(r"^circunscripcion electoral:\s*(.+)$")
RE_CANDIDATURA = re.compile(r"^(\d+)\.\s*(.+?)\s*\.?$")
RE_PERSONA = re.compile(r"^(\d+)\.\s*(.+?)\.?$")
RE_SUPLENTE_SENADO = re.compile(r"^suplente\s*\d*\s*:\s*(.+?)\.?$", re.IGNORECASE)


def texto(p: ET.Element) -> str:
    return " ".join("".join(p.itertext()).split())


def separar_siglas(rotulo: str) -> tuple[str, str]:
    """'PARTIDO X (PSOE) [PSE-EE (PSOE)]' -> ('PARTIDO X (PSOE)', 'PSE-EE (PSOE)').

    Las siglas son el ultimo grupo entre parentesis o corchetes, que puede llevar otros dentro.
    """
    rotulo = rotulo.strip()
    pares = {")": "(", "]": "["}
    if not rotulo or rotulo[-1] not in pares:
        return rotulo, ""
    profundidad = 0
    for i in range(len(rotulo) - 1, -1, -1):
        if rotulo[i] in pares:
            profundidad += 1
        elif rotulo[i] in pares.values():
            profundidad -= 1
            if profundidad == 0:
                return rotulo[:i].strip(), rotulo[i + 1:-1].strip()
    return rotulo, ""


def id_junta(nombre: str) -> str:
    clave = radar.normalizar(nombre).strip(" .")
    if clave not in JUNTAS:
        raise ValueError(f"Junta electoral desconocida en el BOE: {nombre!r}. Añádela a JUNTAS en candidaturas.py")
    return JUNTAS[clave]


def analizar_xml(contenido: bytes | str) -> dict:
    """Lee el XML de una disposicion de candidaturas y devuelve su contenido estructurado."""
    raiz = ET.fromstring(contenido)
    meta = raiz.find("metadatos")
    titulo = meta.findtext("titulo", "").strip()
    fase = TITULO.search(radar.normalizar(titulo))
    if not fase:
        raise ValueError(f"La disposición no parece de candidaturas: {titulo!r}")
    publicada = meta.findtext("fecha_publicacion", "")
    identificador = meta.findtext("identificador", "")

    candidaturas: list[dict] = []
    provincia = camara = isla = None
    actual: dict | None = None
    en_suplentes = False

    for p in raiz.find("texto").iter("p"):
        clase, t = p.get("class", ""), texto(p)
        if not t:
            continue
        tn = radar.normalizar(t)
        if clase == "centro_negrita":
            if m := RE_JUNTA.match(tn):
                provincia, camara, isla, actual = id_junta(m.group(1)), None, None, None
            elif RE_ISLA.match(tn):
                isla, actual = t.split(":", 1)[1].strip(), None
            continue
        if clase == "centro_cursiva":
            camara = "senado" if tn.startswith("senado") else "congreso" if tn.startswith("congreso") else camara
            actual = None
            continue
        if provincia is None or camara is None:
            continue  # texto del acuerdo de la junta, antes de las listas
        if clase == "centro_redonda" and (m := RE_CANDIDATURA.match(t)):
            nombre, siglas = separar_siglas(m.group(2))
            actual = {
                "provincia": provincia,
                "camara": camara,
                "isla": isla if camara == "senado" else None,
                "orden": int(m.group(1)),
                "nombre": nombre,
                "siglas": siglas,
                "proclamada": True,
                "candidatos": [],
                "suplentes": [],
            }
            candidaturas.append(actual)
            en_suplentes = False
            continue
        if actual is None:
            continue
        if tn.rstrip(":") == "suplentes":
            en_suplentes = True
        elif tn.rstrip(".") == "no proclamada":
            actual["proclamada"] = False
        elif m := RE_SUPLENTE_SENADO.match(t):
            if actual["candidatos"]:
                actual["candidatos"][-1].setdefault("suplentes", []).append(m.group(1).strip())
        elif m := RE_PERSONA.match(t):
            persona = m.group(2).strip()
            if en_suplentes:
                actual["suplentes"].append(persona)
            else:
                actual["candidatos"].append({"nombre": persona})

    return {
        "fase": fase.group(1),
        "fuente": {
            "id": identificador,
            "titulo": titulo,
            "fecha_publicacion": f"{publicada[:4]}-{publicada[4:6]}-{publicada[6:8]}" if len(publicada) == 8 else publicada,
            "url": f"https://www.boe.es/diario_boe/txt.php?id={identificador}",
            "url_pdf": meta.findtext("url_pdf", ""),
        },
        "candidaturas": candidaturas,
    }


def buscar_en_sumario(sumario: dict) -> list[str]:
    return [d["id"] for d in radar.recorrer(sumario) if TITULO.search(radar.normalizar(d["titulo"]))]


def guardar(datos: dict, carpeta: Path) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    destino = carpeta / f"{datos['fase']}.json"
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    return destino


def resumen(datos: dict) -> str:
    provincias = {c["provincia"] for c in datos["candidaturas"]}
    congreso = sum(c["camara"] == "congreso" for c in datos["candidaturas"])
    senado = sum(c["camara"] == "senado" for c in datos["candidaturas"])
    return (f"{datos['fuente']['id']} ({datos['fase']}): {len(provincias)} circunscripciones, "
            f"{congreso} candidaturas al Congreso y {senado} al Senado")


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fecha", type=date.fromisoformat, help="día del BOE (AAAA-MM-DD); por defecto, hoy")
    p.add_argument("--desde", type=date.fromisoformat, help="primer día de un rango")
    p.add_argument("--hasta", type=date.fromisoformat, help="último día de un rango (por defecto, hoy)")
    p.add_argument("--id", help="identificador BOE de la disposición (p. ej. BOE-A-2023-15066)")
    p.add_argument("--fichero", type=Path, help="XML ya descargado")
    p.add_argument("--salida", type=Path, default=Path("datos/candidaturas"), help="carpeta de resultados")
    args = p.parse_args(argv)

    if args.fichero:
        contenidos = [args.fichero.read_bytes()]
    elif args.id:
        contenidos = [radar.descargar(URL_XML.format(id=args.id), accept="application/xml")]
    else:
        ids = []
        for dia in radar.dias_pedidos(args):
            sumario = radar.descargar_sumario(dia)
            if sumario:
                ids += buscar_en_sumario(sumario)
        if not ids:
            print("Sin candidaturas en el BOE de los días revisados.")
            return 0
        contenidos = [radar.descargar(URL_XML.format(id=i), accept="application/xml") for i in ids]

    for contenido in contenidos:
        datos = analizar_xml(contenido)
        print(f"{resumen(datos)} → {guardar(datos, args.salida)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
