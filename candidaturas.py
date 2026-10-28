#!/usr/bin/env python3
"""Candidaturas 29N: convierte las listas que publica el BOE en datos para la web.

Las Juntas Electorales Provinciales publican en el BOE, en una sola disposicion, todas las
candidaturas al Congreso y al Senado: primero las presentadas y unos dias despues las proclamadas.

Uso:
    python candidaturas.py                         # busca en el BOE de esta semana (lo ya guardado no se repite)
    python candidaturas.py --desde 2026-10-26      # busca en un rango de dias
    python candidaturas.py --id BOE-A-2023-15066   # procesa una disposicion concreta
    python candidaturas.py --fichero lista.xml     # sin red, desde un XML ya descargado

Escribe datos/candidaturas/{presentadas,proclamadas}.json. Las correcciones de errores no se aplican solas
(son texto libre: "donde dice... debe decir..."): se guardan en datos/candidaturas/correcciones/ con las
provincias afectadas, la web las enlaza en cada provincia y el workflow avisa para revisarlas a mano.
Solo biblioteca estandar.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

import radar

URL_XML = "https://www.boe.es/diario_boe/xml.php?id={id}"
TITULO = re.compile(r"^candidaturas (presentadas|proclamadas) para las? elecciones al congreso")
TITULO_CORRECCION = re.compile(r"^correccion de errores de las candidaturas (presentadas|proclamadas) para las? elecciones al congreso")

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

# Diputados que elige cada circunscripcion (Real Decreto de convocatoria).
DIPUTADOS = {c["id"]: c["diputados"] for c in json.loads(
    (Path(__file__).resolve().parent / "datos" / "circunscripciones.json").read_text(encoding="utf-8"))["circunscripciones"]}


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


def id_junta(nombre: str) -> str | None:
    """Id de circunscripción de una junta, o None si el BOE la escribe de una forma que no está en JUNTAS."""
    return JUNTAS.get(radar.normalizar(nombre).strip(" ."))


def leer_juntas(raiz: ET.Element) -> tuple[list[str], list[str]]:
    """Provincias que nombra una disposición (en orden y sin repetir) y nombres de junta no reconocidos."""
    provincias, desconocidas = [], []
    for p in raiz.find("texto").iter("p"):
        if p.get("class") == "centro_negrita" and (m := RE_JUNTA.match(radar.normalizar(texto(p)))):
            if (prov := id_junta(m.group(1))) is None:
                desconocidas.append(texto(p))
            elif prov not in provincias:
                provincias.append(prov)
    return provincias, desconocidas


def fuente(meta: ET.Element) -> dict:
    publicada, identificador = meta.findtext("fecha_publicacion", ""), meta.findtext("identificador", "")
    return {
        "id": identificador,
        "titulo": meta.findtext("titulo", "").strip(),
        "fecha_publicacion": f"{publicada[:4]}-{publicada[4:6]}-{publicada[6:8]}" if len(publicada) == 8 else publicada,
        "url": f"https://www.boe.es/diario_boe/txt.php?id={identificador}",
        "url_pdf": meta.findtext("url_pdf", ""),
    }


def analizar_xml(contenido: bytes | str) -> dict:
    """Lee el XML de una disposicion de candidaturas y devuelve su contenido estructurado."""
    raiz = ET.fromstring(contenido)
    meta = raiz.find("metadatos")
    titulo = meta.findtext("titulo", "").strip()
    fase = TITULO.search(radar.normalizar(titulo))
    if not fase:
        raise ValueError(f"La disposición no parece de candidaturas: {titulo!r}")
    _, desconocidas = leer_juntas(raiz)
    for junta in desconocidas:
        radar.aviso(f"{titulo[:60]}: «{junta}» no está en JUNTAS de candidaturas.py; sus listas no se cargan hasta añadirla.")

    candidaturas: list[dict] = []
    provincia = camara = isla = None
    actual: dict | None = None
    en_suplentes = False
    sin_cabecera: list[dict] = []  # listas en las que el BOE no escribe «Suplentes:»

    for p in raiz.find("texto").iter("p"):
        clase, t = p.get("class", ""), texto(p)
        if not t:
            continue
        tn = radar.normalizar(t)
        if clase == "centro_negrita":
            if m := RE_JUNTA.match(tn):  # una junta desconocida deja provincia en None y sus listas se saltan
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
            sin_cabecera.append(actual)
            en_suplentes = False
            continue
        if actual is None:
            continue
        if tn.rstrip(":") in ("suplentes", "suplente"):  # «Suplente:» en Ceuta y Melilla, que eligen un diputado
            en_suplentes = True
            sin_cabecera = [c for c in sin_cabecera if c is not actual]
        elif tn.rstrip(".") == "no proclamada" or tn.startswith("candidatura inadmitida"):
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

    for c in candidaturas:
        if not c["candidatos"]:  # «La candidatura no tiene candidatos asociados»: no puede ir en la papeleta
            c["proclamada"] = False
    # Algunas juntas no escriben «Suplentes:». LOREG 46.3: tantos titulares como escaños y, después, los suplentes.
    for c in sin_cabecera:
        if c["camara"] == "congreso" and len(c["candidatos"]) > (n := DIPUTADOS[c["provincia"]]):
            c["suplentes"] = [p["nombre"] for p in c["candidatos"][n:]]
            del c["candidatos"][n:]

    return {"fase": fase.group(1), "fuente": fuente(meta), "juntas_desconocidas": desconocidas, "candidaturas": candidaturas}


def analizar_correccion(contenido: bytes | str) -> dict:
    """Corrección de errores de unas candidaturas: qué fase corrige y a qué provincias afecta."""
    raiz = ET.fromstring(contenido)
    meta = raiz.find("metadatos")
    fase = TITULO_CORRECCION.search(radar.normalizar(meta.findtext("titulo", "")))
    if not fase:
        raise ValueError(f"La disposición no es una corrección de candidaturas: {meta.findtext('titulo', '')!r}")
    provincias, desconocidas = leer_juntas(raiz)
    return {"fase": fase.group(1), "fuente": fuente(meta), "provincias": provincias, "juntas_desconocidas": desconocidas}


def es_correccion(titulo: str) -> bool:
    return bool(TITULO_CORRECCION.search(radar.normalizar(titulo)))


def buscar_en_sumario(sumario: dict) -> list[str]:
    return [d["id"] for d in radar.recorrer(sumario)
            if TITULO.search(t := radar.normalizar(d["titulo"])) or TITULO_CORRECCION.search(t)]


def guardar(datos: dict, carpeta: Path) -> Path:
    destino = carpeta / "correcciones" / f"{datos['fuente']['id']}.json" if "provincias" in datos else carpeta / f"{datos['fase']}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    return destino


def ya_guardada(identificador: str, carpeta: Path) -> bool:
    if (carpeta / "correcciones" / f"{identificador}.json").exists():
        return True
    for f in carpeta.glob("*.json"):
        try:
            if json.loads(f.read_text(encoding="utf-8"))["fuente"]["id"] == identificador:
                return True
        except (ValueError, KeyError):
            pass
    return False


def procesar(contenido: bytes, carpeta: Path) -> None:
    raiz = ET.fromstring(contenido)
    if es_correccion(raiz.find("metadatos").findtext("titulo", "")):
        datos = analizar_correccion(contenido)
        provincias = ", ".join(datos["provincias"]) or "ninguna reconocida"
        print(f"{datos['fuente']['id']} (corrección de las {datos['fase']}): {provincias} → {guardar(datos, carpeta)}")
        radar.aviso(f"El BOE corrige las candidaturas {datos['fase']} ({datos['fuente']['id']}, provincias: {provincias}). "
                    "La web enlaza la corrección; revísala por si hay que cambiar algo a mano.")
    else:
        datos = analizar_xml(contenido)
        print(f"{resumen(datos)} → {guardar(datos, carpeta)}")


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
        procesar(args.fichero.read_bytes(), args.salida)
        return 0
    if args.id:
        procesar(radar.descargar(URL_XML.format(id=args.id), accept="application/xml"), args.salida)
        return 0

    # Sin fechas se mira toda la semana: si un día falló la ejecución, las listas se recogen al siguiente.
    hoy = radar.hoy_madrid()
    dias = radar.dias_pedidos(args) if (args.desde or args.fecha) else [hoy - timedelta(n) for n in range(radar.DIAS_RECIENTES - 1, -1, -1)]
    ids = []
    for dia in dias:
        try:
            ids += buscar_en_sumario(radar.descargar_sumario(dia) or {})
        except Exception as error:
            radar.aviso(f"BOE del {dia}: no se pudo leer ({error}). Se volverá a intentar en la próxima ejecución.")
    nuevos = [i for i in dict.fromkeys(ids) if not ya_guardada(i, args.salida)]
    if not nuevos:
        print("Sin candidaturas nuevas en el BOE de los días revisados.")
    for identificador in nuevos:
        try:
            procesar(radar.descargar(URL_XML.format(id=identificador), accept="application/xml"), args.salida)
        except Exception as error:  # una disposición que falla no impide procesar las demás ni publicar la web
            radar.aviso(f"{identificador}: no se pudo procesar ({error}). Se volverá a intentar en la próxima ejecución.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
