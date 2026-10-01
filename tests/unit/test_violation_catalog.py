"""
Tests unitarios para el catálogo interno de violaciones SQALE.
"""
import unittest

from src.domain.architecture import ModuleMetrics
from src.domain.models import FileMetric
from src.domain.violation_catalog import (
    evaluar_violaciones_archivo,
    evaluar_violaciones_modulos,
)


class TestViolationCatalog(unittest.TestCase):
    def test_violaciones_archivo_largo(self):
        # Archivo > 300 LOC dispara ARCHIVO_LARGO
        m = FileMetric(ruta="large.go", lenguaje="go", loc=350, complejidad_ciclomatica=5)
        viols = evaluar_violaciones_archivo(m)
        reglas = [v.regla for v in viols]
        self.assertIn("ARCHIVO_LARGO", reglas)

    def test_violaciones_cc_alta_por_lenguaje(self):
        # Go umbral CC = 7
        m_go = FileMetric(ruta="repo.go", lenguaje="go", loc=100, complejidad_ciclomatica=8, complejidad_por_funcion=[8])
        viols_go = evaluar_violaciones_archivo(m_go)
        self.assertTrue(any(v.regla == "CC_ALTA" for v in viols_go))

        # Go CC = 6 (no supera 7)
        m_go_ok = FileMetric(ruta="repo_ok.go", lenguaje="go", loc=100, complejidad_ciclomatica=6, complejidad_por_funcion=[6])
        viols_go_ok = evaluar_violaciones_archivo(m_go_ok)
        self.assertFalse(any(v.regla == "CC_ALTA" for v in viols_go_ok))

        # Dart umbral CC = 4
        m_dart = FileMetric(ruta="screen.dart", lenguaje="dart", loc=100, complejidad_ciclomatica=5, complejidad_por_funcion=[5])
        viols_dart = evaluar_violaciones_archivo(m_dart)
        self.assertTrue(any(v.regla == "CC_ALTA" for v in viols_dart))

    def test_violaciones_modulos_y_ciclos(self):
        m_dolor = ModuleMetrics(
            nombre="data",
            ruta="internal/data",
            ca=5,
            ce=0,
            inestabilidad=0.0,
            na=0,
            nc=10,
            abstraccion=0.0,
            distancia_d=1.0,
            zona="ZONA_DOLOR",
        )
        ciclos = [["domain", "presentation", "domain"]]
        viols = evaluar_violaciones_modulos([m_dolor], ciclos)

        reglas = [v.regla for v in viols]
        self.assertIn("ZONA_DOLOR", reglas)
        self.assertIn("IMPORT_CIRCULAR", reglas)


if __name__ == "__main__":
    unittest.main()
