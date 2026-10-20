"""Pruebas de las polémicas ante la Junta Electoral Central. Ejecutar con:  python -m unittest discover tests

Usan páginas reales de la JEC (sesión del 15 de octubre de 2026) guardadas en tests/fixtures/jec/, sin conexión.
"""

import json
import re
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import jec  # noqa: E402

FIXTURES = RAIZ / "tests" / "fixtures" / "jec"
SESION = FIXTURES / "sesion_2026-10-15.html"


def ficha(url: str) -> str:
    return (FIXTURES / f"{re.search(r'idacuerdoinstruccion=(\d+)', url).group(1)}.html").read_text(encoding="utf-8")


class TestConflicto(unittest.TestCase):
    def test_entran(self):
        for objeto in (
            "Denuncia contra don Pedro Sánchez Pérez-Castejón, Presidente del Gobierno, por vulneración del art. 50.2 LOREG",
            "Recurso potestativo de reposición interpuesto por el partido Valores contra el Acuerdo 230/2026",
            "Escritos relativos a la ejecución de los Autos de la Sala de lo Contencioso-Administrativo del Tribunal Supremo",
            "Queja por la cobertura informativa de un debate",
            "Reclamación contra el acuerdo de la Junta Electoral Provincial",
        ):
            self.assertTrue(jec.es_conflicto(objeto), objeto)

    def test_no_entran(self):
        for objeto in (
            "Constitución de las Juntas Electorales Provinciales con motivo de la celebración de las elecciones generales",
            "Designación de representantes generales por las formaciones políticas",
            "Comunicación de la realización del Estudio 3582 Barómetro octubre 2026",
            "Consulta del autor del escrito sobre el sorteo automático de las mesas",  # «autor» y «automático» no son «auto»
        ):
            self.assertFalse(jec.es_conflicto(objeto), objeto)


class TestPaginas(unittest.TestCase):
    def test_sesiones(self):
        s = jec.sesiones(SESION.read_text(encoding="utf-8"))
        self.assertEqual(s[0], ("1116", date(2026, 10, 15)))
        self.assertIn(("1115", date(2026, 9, 24)), s)
        self.assertEqual(len(s), 17)  # el selector de años no se confunde con el de sesiones

    def test_listado(self):
        acuerdos = jec.acuerdos_de_sesion(SESION.read_text(encoding="utf-8"))
        self.assertEqual(len(acuerdos), 30)
        primero = acuerdos[0]
        self.assertEqual((primero["numero"], primero["expediente"]), ("271/2026", "321/671"))
        self.assertTrue(primero["url"].startswith("https://www.juntaelectoralcentral.es/cs/jec/doctrina/acuerdos?"))
        self.assertNotIn("&amp;", primero["url"])

    def test_detalle(self):
        d = jec.detalle((FIXTURES / "154396.html").read_text(encoding="utf-8"))
        self.assertEqual(d["autor"], "Sr. Representante General del Partido Socialista Obrero Español")
        self.assertTrue(d["objeto"].startswith("Denuncia contra D. Fernando López Miras"))
        self.assertEqual(d["acuerdo"], ["Al estar constituidas las Juntas Electorales, trasladar la denuncia a la Junta Electoral Provincial de Murcia por ser la competente para conocer del asunto."])
        self.assertEqual(d["proceso"], "Elecciones Generales 2026 (Cortes Generales)")
        self.assertEqual(d["materias"], ["JUNTAS ELECTORALES - Competencias", "JUNTAS ELECTORALES PROVINCIALES"])

    def test_varios_autores(self):
        self.assertEqual(jec.detalle((FIXTURES / "154384.html").read_text(encoding="utf-8"))["autor"], "Asociación, Formaciones políticas")

    def test_parrafos_del_acuerdo(self):
        d = jec.detalle((FIXTURES / "154418.html").read_text(encoding="utf-8"))
        self.assertGreater(len(d["acuerdo"]), 5)
        self.assertTrue(d["acuerdo"][0].startswith("1.- Con fecha 5 de octubre de 2026"))
        self.assertNotIn("\xa0", " ".join(d["acuerdo"]))


class TestRegla(unittest.TestCase):
    def setUp(self):
        self.informe = jec.analizar(SESION.read_text(encoding="utf-8"), date(2026, 10, 15), "1116", ficha)

    def test_entran_los_conflictos_de_estas_elecciones(self):
        self.assertEqual(self.informe["acuerdos_revisados"], 30)
        self.assertEqual([a["numero"] for a in self.informe["acuerdos"]], ["246/2026", "247/2026", "248/2026", "249/2026", "265/2026", "270/2026"])

    def test_no_entra_lo_que_la_jec_no_asocia_a_estas_elecciones(self):
        numeros = {a["numero"] for a in self.informe["acuerdos"]}
        self.assertNotIn("245/2026", numeros)  # recurso de Valores: la JEC no lo asocia a ningún proceso
        self.assertNotIn("264/2026", numeros)  # sentencia penal en la Diputación de Badajoz

    def test_no_entra_lo_que_no_es_conflicto(self):
        numeros = {a["numero"] for a in self.informe["acuerdos"]}
        self.assertNotIn("257/2026", numeros)  # designación de representantes generales
        self.assertNotIn("271/2026", numeros)  # adelanto del envío del voto CERA a Argentina

    def test_sin_red(self):
        with tempfile.TemporaryDirectory() as tmp:
            jec.main(["--fichero", str(SESION), "--fecha", "2026-10-15", "--detalles", str(FIXTURES), "--salida", tmp])
            datos = json.loads((Path(tmp) / "2026-10-15.json").read_text(encoding="utf-8"))
        self.assertEqual(len(datos["acuerdos"]), 6)
        self.assertEqual(set(datos["acuerdos"][0]), {"numero", "expediente", "autor", "objeto", "acuerdo", "materias", "url"})


if __name__ == "__main__":
    unittest.main()
