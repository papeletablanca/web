"""Pruebas de los enlaces que se escriben a mano en datos/ y en las páginas de la web. Sin conexión."""

import re
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FICHEROS = [*(RAIZ / "datos").glob("*.yaml"), *(RAIZ / "datos" / "formaciones").glob("*.yaml"), *(RAIZ / "web" / "src").rglob("*.astro")]

# Textos consolidados del BOE (buscar/act.php): los artículos se enlazan con el número en letra,
# p. ej. #asetentaydos para el artículo 72. Un ancla como #a72 no existe y lleva al principio de la ley.
ANCLA_BOE = re.compile(r"boe\.es/buscar/act\.php\?id=([A-Z0-9-]+)#([A-Za-z0-9]+)")
# Excepciones comprobadas a mano: el Reglamento del Congreso sí usa cifras (#art207).
ANCLAS_CON_CIFRAS = {"BOE-A-1982-5196"}


class TestAnclasBoe(unittest.TestCase):
    def test_articulos_con_numero_en_letra(self):
        mal = [
            f"{f.relative_to(RAIZ)}: #{m.group(2)}"
            for f in FICHEROS
            for m in ANCLA_BOE.finditer(f.read_text(encoding="utf-8"))
            if re.search(r"\d", m.group(2)) and m.group(1) not in ANCLAS_CON_CIFRAS
        ]
        self.assertEqual(mal, [], "anclas con cifras; el BOE usa el número en letra (#asetentaydos, no #a72)")

    def test_detecta_el_error(self):
        texto = "https://www.boe.es/buscar/act.php?id=BOE-A-1985-11672#a72"
        self.assertEqual(ANCLA_BOE.search(texto).group(2), "a72")


if __name__ == "__main__":
    unittest.main()
