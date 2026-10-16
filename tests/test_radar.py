"""Pruebas del radar y de las candidaturas. Ejecutar con:  python -m unittest discover tests

Todas usan datos reales del BOE guardados en tests/fixtures/, sin conexión.
"""

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import candidaturas  # noqa: E402
import radar  # noqa: E402

FIXTURES = RAIZ / "tests" / "fixtures"
SUMARIO = FIXTURES / "sumario_2026-10-06.json"
CANDIDATURAS_2023 = FIXTURES / "candidaturas_2023_extracto.xml"


class TestClasificar(unittest.TestCase):
    def test_convocatoria(self):
        self.assertIn("Convocatoria", radar.clasificar(
            "Real Decreto 806/2026, de 5 de octubre, de disolución del Congreso de los Diputados y del Senado y de convocatoria de elecciones."))

    def test_junta_electoral_y_voto(self):
        etiquetas = radar.clasificar("Instrucción de la Junta Electoral Central sobre el voto por correo")
        self.assertIn("Junta Electoral", etiquetas)
        self.assertIn("Censo y voto", etiquetas)

    def test_titulos_reales_que_si_son_electorales(self):
        for titulo in [
            "Orden HAC/1062/2026, de 7 de octubre, por la que se fijan las cantidades de las subvenciones a los gastos originados por actividades electorales para las elecciones generales de 29 de noviembre de 2026.",
            "Resolución de 9 de octubre de 2026, de la Subsecretaría, por la que se determina la relación de centros habilitados en el extranjero para el depósito de voto en urna en las elecciones al Congreso de los Diputados y al Senado de 29 de noviembre de 2026.",
            "Candidaturas proclamadas para la elecciones al Congreso de los Diputados y al Senado, convocadas por Real Decreto 400/2023, de 29 de mayo.",
            "Resolución de 30 de agosto de 2023, de la Presidencia de la Junta Electoral Central, por la que se publica el resumen de los resultados de las elecciones al Congreso de los Diputados y al Senado",
        ]:
            self.assertTrue(radar.clasificar(titulo), titulo)

    def test_titulos_reales_que_no_son_electorales(self):
        # Falsos positivos que daba la primera versión del radar en octubre de 2026.
        for titulo in [
            "Anuncio de licitación de: División Económica y Técnica (Cuerpo Nacional de Policía). Objeto: adquisición de consumibles, pago por uso multifuncionales kyocera 2027-2028.",
            "Resolución de 23 de septiembre de 2026, de la Secretaría de Estado de Comercio, por la que se publica la tercera Adenda del Convenio con la Cámara Oficial de Comercio",
            "Sentencia de 17 de septiembre de 2026, de la Sala Tercera del Tribunal Supremo, que estima parcialmente el recurso contencioso-administrativo 425/2023",
            "Resolución de 29 de septiembre de 2026, conjunta de las Presidencias del Congreso de los Diputados y del Senado, por la que se convoca oposición para el Cuerpo de Letrados de las Cortes Generales.",
            "Resolución de 5 de octubre de 2026, de la Presidencia de la Junta Electoral Central, por la que se anuncia propuesta de designación de concejal del Ayuntamiento de Alcolea, en sustitución de un concejal, en aplicación de la Ley Orgánica 5/1985",
            "Calendario de elecciones sindicales",
            "Ayudas al sector del arroz",
        ]:
            self.assertEqual(radar.clasificar(titulo), [], titulo)


class TestSumarioReal(unittest.TestCase):
    def setUp(self):
        self.sumario = json.loads(SUMARIO.read_text(encoding="utf-8"))

    def test_recorre_todas_las_disposiciones(self):
        ids = {d["id"] for d in radar.recorrer(self.sumario)}
        self.assertGreater(len(ids), 200)

    def test_contexto_de_departamento(self):
        disp = {d["id"]: d for d in radar.recorrer(self.sumario)}
        self.assertEqual(disp["BOE-A-2026-20742"]["departamento"], "JEFATURA DEL ESTADO")

    def test_solo_detecta_la_convocatoria(self):
        informe = radar.analizar(self.sumario, date(2026, 10, 6))
        self.assertEqual([h["id"] for h in informe["hallazgos"]], ["BOE-A-2026-20742"])

    def test_extremo_a_extremo(self):
        with tempfile.TemporaryDirectory() as tmp:
            radar.main(["--fichero", str(SUMARIO), "--fecha", "2026-10-06", "--salida", tmp])
            informe = json.loads((Path(tmp) / "2026-10-06.json").read_text(encoding="utf-8"))
            self.assertEqual(informe["hallazgos"][0]["etiquetas"], ["Convocatoria"])


class TestCandidaturas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.datos = candidaturas.analizar_xml(CANDIDATURAS_2023.read_bytes())
        cls.lista = cls.datos["candidaturas"]

    def buscar(self, provincia, camara, siglas, isla=None):
        return next(c for c in self.lista if c["provincia"] == provincia and c["camara"] == camara
                    and c["siglas"] == siglas and c["isla"] == isla)

    def test_metadatos(self):
        self.assertEqual(self.datos["fase"], "proclamadas")
        self.assertEqual(self.datos["fuente"]["id"], "BOE-A-2023-15066")
        self.assertEqual(self.datos["fuente"]["fecha_publicacion"], "2023-06-27")

    def test_provincias_y_camaras(self):
        self.assertEqual({c["provincia"] for c in self.lista}, {"albacete", "baleares"})
        self.assertEqual({c["camara"] for c in self.lista}, {"congreso", "senado"})

    def test_lista_congreso(self):
        psoe = self.buscar("albacete", "congreso", "PSOE")
        self.assertEqual(psoe["orden"], 1)
        self.assertEqual(psoe["nombre"], "PARTIDO SOCIALISTA OBRERO ESPAÑOL")
        self.assertEqual([c["nombre"] for c in psoe["candidatos"]][:2], ["Emilio Sáez Cruz", "Isabel Belén Iniesta Egido"])
        self.assertEqual(len(psoe["candidatos"]), 4)  # Albacete elige 4 diputados
        self.assertEqual(psoe["suplentes"], ["María Pilar Sierra Morcillo", "Javier Losa Serrano", "Patricia Moreno Serrano"])

    def test_lista_senado_con_suplentes_por_candidato(self):
        psoe = self.buscar("albacete", "senado", "PSOE")
        self.assertEqual(psoe["candidatos"][0], {"nombre": "Amparo Torres Valencoso",
                                                 "suplentes": ["Diego Aroca Rodas", "María Victoria Leal Utiel"]})

    def test_senado_por_islas(self):
        islas = {c["isla"] for c in self.lista if c["provincia"] == "baleares" and c["camara"] == "senado"}
        self.assertEqual(islas, {"Mallorca", "Menorca", "Eivissa-Formentera"})
        congreso = {c["isla"] for c in self.lista if c["provincia"] == "baleares" and c["camara"] == "congreso"}
        self.assertEqual(congreso, {None})

    def test_ninguna_lista_proclamada_vacia(self):
        vacias = [c["nombre"] for c in self.lista if c["proclamada"] and not c["candidatos"]]
        self.assertEqual(vacias, [])


class TestSiglas(unittest.TestCase):
    def test_simples(self):
        self.assertEqual(candidaturas.separar_siglas("PARTIDO POPULAR (PP)"), ("PARTIDO POPULAR", "PP"))

    def test_anidadas(self):
        self.assertEqual(candidaturas.separar_siglas("PARTIDO SOCIALISTA DE EUSKADI-EUSKADIKO EZKERRA (PSOE) [PSE-EE (PSOE)]"),
                         ("PARTIDO SOCIALISTA DE EUSKADI-EUSKADIKO EZKERRA (PSOE)", "PSE-EE (PSOE)"))

    def test_sin_siglas(self):
        self.assertEqual(candidaturas.separar_siglas("ESQUERRA REPUBLICANA DE CATALUNYA-ESQUERRES PER LA INDEPENDÈNCIA"),
                         ("ESQUERRA REPUBLICANA DE CATALUNYA-ESQUERRES PER LA INDEPENDÈNCIA", ""))

    def test_junta_desconocida_da_error_claro(self):
        with self.assertRaises(ValueError):
            candidaturas.id_junta("Narnia")


if __name__ == "__main__":
    unittest.main()
