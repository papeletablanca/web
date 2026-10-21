#!/usr/bin/env python3
"""Polémicas ante la Junta Electoral Central (Papeleta Blanca).

Lee los acuerdos de la Junta Electoral Central (JEC) desde la convocatoria y aparta los que cumplen
las dos condiciones de la regla, sin que nadie elija caso a caso:

  1. La propia JEC los asocia al proceso «Elecciones Generales 2026 (Cortes Generales)».
  2. Su objeto es un conflicto: una denuncia, queja, recurso, reclamación o impugnación,
     o tiene que ver con una resolución de un tribunal (CONFLICTO, más abajo).

Uso:
    python jec.py                                   # sesiones de la JEC desde la convocatoria
    python jec.py --fichero sesion.html --detalles carpeta/   # sin red, para pruebas

Escribe un JSON por sesión en datos/jec/. La web (carpeta web/) los lee.
Fuente: https://www.juntaelectoralcentral.es/cs/jec/doctrina/acuerdos

También guarda en datos/coaliciones.json la relación oficial de coaliciones válidamente constituidas ante la JEC
(nombre, siglas, ámbito y enlace al pacto), tal cual la publica. La web la usa para enlazar cada ficha con las listas
de las coaliciones de las que forma parte.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import socket
import sys
from datetime import date
from pathlib import Path

import radar

WEB = "https://www.juntaelectoralcentral.es"
LISTADO = WEB + "/cs/jec/doctrina/acuerdos"
CONVOCATORIA = date(2026, 10, 5)  # Real Decreto 806/2026: antes no hay acuerdos de este proceso
PROCESO = r"elecciones generales 2026"
# Sobre el objeto del acuerdo, sin tildes y en minúsculas. "auto" con \b para no encajar en "autor" o "automático".
CONFLICTO = [
    r"\bdenuncia", r"\bqueja", r"\brecurso", r"\breclamacion", r"\bimpugnacion",
    r"tribunal (supremo|constitucional)", r"\bautos?\b", r"\bsentencia",
]

COALICIONES = WEB + "/cs/jec/elecciones/coalicionesJEC?fechaeleccion=2026-11-29&tipoeleccion=Elecciones%20Generales"
RE_COALICION = re.compile(
    r'<p>\s*(C\d+)\.\s*COALICI[ÓO]N ELECTORAL\s*"(.*?)"\s*</p>\s*'
    r'<p[^>]*>\s*Siglas:\s*(.*?)</p>\s*'
    r'(?:<p[^>]*>\s*(?:&Aacute;|Á)mbito:\s*(.*?)</p>)?'
    r'(?:.*?href=\'([^\']*descargarFichero[^\']*)\')?',
    re.S,
)

RE_SESION = re.compile(r'<option value="(\d+)"[^>]*>(\d\d)/(\d\d)/(\d{4})</option>')
RE_ACUERDO = re.compile(
    r'href="([^"]*idacuerdoinstruccion=(\d+)[^"]*)"[^>]*>Nº Ac: ([\d/]+) Expte\.:\s*([\d/]+)</a><br>(.*?)</li>', re.S
)


def texto(fragmento: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragmento))).strip()


def parrafos(fragmento: str) -> list[str]:
    trozos = re.split(r"</p>|<br\s*/?>", fragmento)
    return [t for t in (texto(x) for x in trozos) if t]


def entre(pagina: str, inicio: str, fin: str) -> str:
    m = re.search(re.escape(inicio) + r"(.*?)" + re.escape(fin), pagina, re.S)
    return m.group(1) if m else ""


def es_conflicto(objeto: str) -> bool:
    o = radar.normalizar(objeto)
    return any(re.search(p, o) for p in CONFLICTO)


def sesiones(pagina: str) -> list[tuple[str, date]]:
    """Sesiones del año que ofrece el selector del listado: (id, fecha)."""
    return [(i, date(int(a), int(m), int(d))) for i, d, m, a in RE_SESION.findall(pagina)]


def acuerdos_de_sesion(pagina: str) -> list[dict]:
    return [
        {"id_web": i, "numero": n, "expediente": e, "objeto": texto(o), "url": WEB + html.unescape(u)}
        for u, i, n, e, o in RE_ACUERDO.findall(pagina)
    ]


def detalle(pagina: str) -> dict:
    """Autor, objeto, texto del acuerdo, proceso electoral y materias de la ficha de un acuerdo."""
    otros = entre(pagina, '<div class="detalle-acuerdoinstruccion">', "</div>")
    return {
        "autor": ", ".join(t for t in map(texto, re.findall(r"<td>(.*?)</td>", entre(pagina, "<strong>Autor:</strong>", "</table>"), re.S)) if t),
        "objeto": texto(entre(pagina, "<strong>Objeto:</strong></p>", "<strong>Acuerdo:</strong>")),
        "acuerdo": parrafos(entre(pagina, "<strong>Acuerdo:</strong></p>", '<div class="detalle-acuerdoinstruccion">')),
        "proceso": texto(entre(otros, "Proceso electoral asociado: </strong>", "<strong>")),
        "materias": parrafos(otros.split("Descriptores de materia: </strong></p>", 1)[1]) if "Descriptores de materia" in otros else [],
    }


def analizar(listado: str, fecha: date, sesion: str, leer_detalle) -> dict:
    """Aplica la regla a una sesión. leer_detalle(url) devuelve el HTML de la ficha de un acuerdo."""
    acuerdos = acuerdos_de_sesion(listado)
    elegidos = []
    for a in acuerdos:
        if not es_conflicto(a["objeto"]):
            continue
        d = detalle(leer_detalle(a["url"]))
        if not re.search(PROCESO, radar.normalizar(d["proceso"])):
            continue
        elegidos.append({
            "numero": a["numero"], "expediente": a["expediente"], "autor": d["autor"],
            "objeto": d["objeto"] or a["objeto"], "acuerdo": d["acuerdo"], "materias": d["materias"], "url": a["url"],
        })
    elegidos.sort(key=lambda a: int(a["numero"].split("/")[0]))
    return {"fecha": fecha.isoformat(), "sesion": sesion, "acuerdos_revisados": len(acuerdos), "acuerdos": elegidos}


def coaliciones(pagina: str) -> list[dict]:
    """Coaliciones de la página oficial de la JEC, en su orden de presentación. Cada bloque se lee por separado
    para que el enlace al pacto de una coalición no se atribuya a la siguiente."""
    bloques = re.split(r'<div class="nueva_fila">\s*(?=<p>\s*C\d+\.)', pagina)
    salida = []
    for b in bloques:
        m = RE_COALICION.search(b)
        if not m:
            continue
        codigo, nombre, siglas, ambito, pacto = m.groups()
        salida.append({
            "codigo": codigo, "nombre": texto(nombre), "siglas": texto(siglas),
            "ambito": texto(ambito or ""), "pacto": html.unescape(pacto) if pacto else None,
        })
    return salida


def guardar_coaliciones(pagina: str, destino: Path) -> list[dict]:
    lista = coaliciones(pagina)
    hay = len(re.findall(r"<p>\s*C\d+\.\s*COALICI", pagina))
    if "constituidas ante la Junta Electoral Central" not in pagina or len(lista) != hay:
        radar.aviso(f"JEC: la relación de coaliciones no se ha podido leer bien ({len(lista)} de {hay}). ¿Ha cambiado su formato? No se ha tocado datos/coaliciones.json.")
        return lista
    datos = {"fuente": COALICIONES, "coaliciones": lista}
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return lista


def ipv4_primero() -> None:
    """La JEC anuncia direcciones IPv6 que no responden: sin esto, cada petición espera ~40 s antes de usar IPv4."""
    original = socket.getaddrinfo

    def ordenado(*args, **kwargs):
        return sorted(original(*args, **kwargs), key=lambda r: r[0] != socket.AF_INET)

    socket.getaddrinfo = ordenado


def resumen_texto(informe: dict) -> str:
    lineas = [f"JEC, sesión del {informe['fecha']}: {len(informe['acuerdos'])} polémicas de {informe['acuerdos_revisados']} acuerdos"]
    for a in informe["acuerdos"]:
        lineas.append(f"  - {a['numero']} ({a['autor']}) {a['objeto'][:120]}")
    return "\n".join(lineas)


def leer(url: str) -> str:
    return radar.descargar(url, accept="text/html").decode("utf-8", "replace")


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fichero", type=Path, help="listado de una sesión guardado (sin red)")
    p.add_argument("--fecha", type=date.fromisoformat, help="fecha de la sesión del --fichero (AAAA-MM-DD)")
    p.add_argument("--detalles", type=Path, help="carpeta con las fichas guardadas como <idacuerdoinstruccion>.html")
    p.add_argument("--salida", type=Path, default=Path("datos/jec"), help="carpeta de resultados (por defecto datos/jec)")
    p.add_argument("--coaliciones", type=Path, default=Path("datos/coaliciones.json"), help="relación de coaliciones (por defecto datos/coaliciones.json)")
    args = p.parse_args(argv)
    args.salida.mkdir(parents=True, exist_ok=True)

    if args.fichero:
        local = lambda url: (args.detalles / f"{re.search(r'idacuerdoinstruccion=(\d+)', url).group(1)}.html").read_text(encoding="utf-8")
        informe = analizar(args.fichero.read_text(encoding="utf-8"), args.fecha or radar.hoy_madrid(), "local", local)
        (args.salida / f"{informe['fecha']}.json").write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        print(resumen_texto(informe))
        return 0

    ipv4_primero()
    try:
        portada = leer(LISTADO)
    except Exception as error:
        radar.aviso(f"Junta Electoral Central: no se pudo leer el listado de acuerdos ({error}). Se volverá a intentar en la próxima ejecución.")
        return 0
    for sesion, fecha in sesiones(portada):
        if fecha < CONVOCATORIA:
            continue
        destino = args.salida / f"{fecha.isoformat()}.json"
        try:
            listado = leer(f"{LISTADO}?anyosesion={fecha.year}&idsesion={sesion}")
            previo = json.loads(destino.read_text(encoding="utf-8")) if destino.exists() else None
            if previo and previo["acuerdos_revisados"] == len(acuerdos_de_sesion(listado)):
                continue  # sesión ya revisada y sin acuerdos nuevos
            informe = analizar(listado, fecha, sesion, leer)
        except Exception as error:  # una sesión que falla no impide revisar las demás ni publicar la web
            radar.aviso(f"JEC, sesión del {fecha}: no se pudo leer ({error}). Se volverá a intentar en la próxima ejecución.")
            continue
        if not informe["acuerdos_revisados"]:
            radar.aviso(f"JEC, sesión del {fecha}: el listado no tiene acuerdos. ¿Ha cambiado la web de la Junta?")
            continue
        destino.write_text(json.dumps(informe, ensure_ascii=False, indent=2), encoding="utf-8")
        print(resumen_texto(informe))

    try:
        lista = guardar_coaliciones(leer(COALICIONES), args.coaliciones)
        print(f"JEC, coaliciones: {len(lista)} ({', '.join(c['siglas'] for c in lista)})")
    except Exception as error:
        radar.aviso(f"JEC: no se pudo leer la relación de coaliciones ({error}). Se volverá a intentar en la próxima ejecución.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
