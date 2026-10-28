"""Pruebas del radar y de las candidaturas. Ejecutar con:  python -m unittest discover tests

Todas usan datos reales del BOE guardados en tests/fixtures/, sin conexión.
"""

import gzip
import io
import json
import sys
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import candidaturas  # noqa: E402
import radar  # noqa: E402

FIXTURES = RAIZ / "tests" / "fixtures"
SUMARIO = FIXTURES / "sumario_2026-10-06.json"
CANDIDATURAS_2023 = FIXTURES / "candidaturas_2023_extracto.xml"
PROCLAMADAS_2023 = FIXTURES / "candidaturas_2023_proclamadas.xml.gz"  # la disposición completa: 52 circunscripciones
PRESENTADAS_2026 = FIXTURES / "candidaturas_2026_presentadas.xml.gz"  # BOE-A-2026-22607
CORRECCIONES_2023 = {"BOE-A-2023-15548": FIXTURES / "correccion_2023_15548.xml", "BOE-A-2023-15828": FIXTURES / "correccion_2023_15828.xml"}


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

    def test_junta_desconocida_no_tiene_id(self):
        self.assertIsNone(candidaturas.id_junta("Narnia"))


class TestDisposicionCompleta2023(unittest.TestCase):
    """Las listas proclamadas del 23J completas: todas las juntas tienen que reconocerse."""

    @classmethod
    def setUpClass(cls):
        cls.xml = gzip.decompress(PROCLAMADAS_2023.read_bytes())
        cls.datos = candidaturas.analizar_xml(cls.xml)

    def test_todas_las_circunscripciones(self):
        self.assertEqual(self.datos["juntas_desconocidas"], [])
        ids = {c["id"] for c in json.loads((RAIZ / "datos" / "circunscripciones.json").read_text(encoding="utf-8"))["circunscripciones"]}
        self.assertEqual({c["provincia"] for c in self.datos["candidaturas"]}, ids)

    def test_ninguna_lista_proclamada_vacia(self):
        vacias = [(c["provincia"], c["nombre"]) for c in self.datos["candidaturas"] if c["proclamada"] and not c["candidatos"]]
        self.assertEqual(vacias, [])

    def test_junta_desconocida_avisa_y_sigue(self):
        xml = self.xml.replace("JUNTA ELECTORAL DE TERUEL".encode(), "JUNTA ELECTORAL DE NARNIA".encode())
        with redirect_stdout(io.StringIO()) as salida:
            datos = candidaturas.analizar_xml(xml)
        self.assertIn("NARNIA", salida.getvalue())
        self.assertEqual(datos["juntas_desconocidas"], ["JUNTA ELECTORAL DE NARNIA"])
        provincias = {c["provincia"] for c in datos["candidaturas"]}
        self.assertNotIn("teruel", provincias)
        self.assertEqual(len(provincias), 51)  # las demás se cargan igual


class TestPresentadas2026(unittest.TestCase):
    """Las listas presentadas del 29N: formas de escribir que no salían en 2023."""

    @classmethod
    def setUpClass(cls):
        cls.datos = candidaturas.analizar_xml(gzip.decompress(PRESENTADAS_2026.read_bytes()))
        cls.lista = cls.datos["candidaturas"]

    def buscar(self, provincia, camara, orden):
        return next(c for c in self.lista if c["provincia"] == provincia and c["camara"] == camara and c["orden"] == orden)

    def test_todas_las_circunscripciones(self):
        self.assertEqual(self.datos["juntas_desconocidas"], [])
        self.assertEqual(len({c["provincia"] for c in self.lista}), 52)

    def test_suplente_en_singular(self):
        pp = self.buscar("ceuta", "congreso", 1)
        self.assertEqual([c["nombre"] for c in pp["candidatos"]], ["Rafael Martínez Peñalver Mateos"])
        self.assertEqual(pp["suplentes"], ["Nabila Benzina Pavón"])

    def test_inadmitida_y_sin_candidatos(self):
        self.assertFalse(self.buscar("burgos", "congreso", 7)["proclamada"])  # «Candidatura inadmitida por acuerdo…»
        self.assertFalse(self.buscar("burgos", "senado", 3)["proclamada"])  # «La candidatura no tiene candidatos asociados»

    def test_ninguna_lista_proclamada_vacia(self):
        vacias = [(c["provincia"], c["nombre"]) for c in self.lista if c["proclamada"] and not c["candidatos"]]
        self.assertEqual(vacias, [])

    def test_sin_cabecera_de_suplentes(self):
        fa = self.buscar("badajoz", "congreso", 7)  # 9 nombres seguidos; Badajoz elige 5
        self.assertEqual(len(fa["candidatos"]), 5)
        self.assertEqual(fa["suplentes"], ["Juan Eugenio Mena Cabezas", "Andrea Macías Rodríguez", "Jesús Merino González",
                                           "María Arenas Lopera"])

    def test_lista_corta_se_deja_como_esta(self):
        self.assertEqual(len(self.buscar("madrid", "congreso", 10)["candidatos"]), 37)  # Madrid elige 38


class TestCorrecciones(unittest.TestCase):
    def test_provincias_afectadas(self):
        esperado = {"BOE-A-2023-15548": ["baleares", "bizkaia", "cuenca"], "BOE-A-2023-15828": ["teruel"]}
        for identificador, fichero in CORRECCIONES_2023.items():
            datos = candidaturas.analizar_correccion(fichero.read_bytes())
            self.assertEqual(datos["fase"], "proclamadas")
            self.assertEqual(datos["fuente"]["id"], identificador)
            self.assertEqual(datos["provincias"], esperado[identificador])

    def test_se_guarda_aparte_y_no_pisa_las_listas(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            candidaturas.procesar(CANDIDATURAS_2023.read_bytes(), Path(tmp))
            candidaturas.procesar(CORRECCIONES_2023["BOE-A-2023-15828"].read_bytes(), Path(tmp))
            self.assertTrue((Path(tmp) / "proclamadas.json").exists())
            self.assertTrue((Path(tmp) / "correcciones" / "BOE-A-2023-15828.json").exists())
            self.assertTrue(candidaturas.ya_guardada("BOE-A-2023-15066", Path(tmp)))
            self.assertTrue(candidaturas.ya_guardada("BOE-A-2023-15828", Path(tmp)))
            self.assertFalse(candidaturas.ya_guardada("BOE-A-2023-14733", Path(tmp)))

    def test_el_sumario_encuentra_listas_y_correcciones(self):
        sumario = {"diario": [{"identificador": i, "titulo": t} for i, t in [
            ("A", "Candidaturas proclamadas para la elecciones al Congreso de los Diputados y al Senado, convocadas por Real Decreto 400/2023, de 29 de mayo."),
            ("B", "Corrección de errores de las candidaturas proclamadas para las elecciones al Congreso de los Diputados y al Senado, convocadas por Real Decreto 400/2023, de 29 de mayo."),
            ("C", "Corrección de errores de la Orden HAC/1062/2026, sobre gastos electorales."),
        ]]}
        self.assertEqual(candidaturas.buscar_en_sumario(sumario), ["A", "B"])


class TestFallosDelBoe(unittest.TestCase):
    """Un fallo del BOE no puede impedir que se revisen los demás días ni que se publique la web."""

    def test_reintenta_los_errores_del_servidor(self):
        error = urllib.error.HTTPError("https://www.boe.es", 503, "Service Unavailable", {}, None)
        respuesta = mock.MagicMock()
        respuesta.__enter__.return_value.read.return_value = b"{}"
        with mock.patch("urllib.request.urlopen", side_effect=[error, error, respuesta]) as urlopen, mock.patch("time.sleep") as espera:
            self.assertEqual(radar.descargar("https://www.boe.es/x"), b"{}")
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(espera.call_count, 2)

    def test_no_reintenta_un_404(self):
        error = urllib.error.HTTPError("https://www.boe.es", 404, "Not Found", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=error) as urlopen, mock.patch("time.sleep"):
            with self.assertRaises(urllib.error.HTTPError):
                radar.descargar("https://www.boe.es/x")
        self.assertEqual(urlopen.call_count, 1)

    def test_un_dia_que_falla_no_para_los_demas(self):
        sumario = json.loads(SUMARIO.read_text(encoding="utf-8"))

        def boe(dia):
            if dia == date(2026, 10, 7):
                raise urllib.error.URLError("sin conexión")
            return sumario

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(radar, "descargar_sumario", side_effect=boe), \
                mock.patch.object(radar, "aviso") as aviso:
            codigo = radar.main(["--desde", "2026-10-06", "--hasta", "2026-10-08", "--salida", tmp])
            guardados = sorted(f.name for f in Path(tmp).glob("*.json"))
        self.assertEqual(codigo, 0)
        self.assertEqual(guardados, ["2026-10-06.json", "2026-10-08.json"])
        self.assertIn("2026-10-07", aviso.call_args.args[0])

    def test_recupera_los_dias_que_faltan(self):
        with tempfile.TemporaryDirectory() as tmp:
            for d in ("2026-10-13", "2026-10-15"):
                (Path(tmp) / f"{d}.json").write_text("{}", encoding="utf-8")
            dias = radar.dias_recientes(Path(tmp), hoy=date(2026, 10, 16))
        self.assertEqual([d.isoformat() for d in dias], ["2026-10-10", "2026-10-11", "2026-10-12", "2026-10-14", "2026-10-16"])


if __name__ == "__main__":
    unittest.main()
