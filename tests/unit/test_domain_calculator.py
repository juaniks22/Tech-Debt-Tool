"""
Tests unitarios para el dominio puro (src.domain.calculator).
"""
import sys
import unittest
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Configurar sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.domain.calculator import (
    calcular_costo_reparacion,
    calcular_deuda_horas,
    calcular_interes_anual,
    calcular_mi,
    calcular_payback_anios,
    calcular_roi_4_anios,
    construir_reporte_archivo,
)
from src.domain.models import FileMetric, FinancialParams


class TestDomainCalculator(unittest.TestCase):
    def test_calcular_mi_base(self):
        # Si LOC es 0 o negativo, MI es 100
        self.assertEqual(calcular_mi(0, 10), 100.0)
        self.assertEqual(calcular_mi(-5, 0), 100.0)

        # Archivo con LOC y complejidad conocida
        mi = calcular_mi(422, 68)
        self.assertAlmostEqual(mi, 2.48, delta=0.05)

    def test_calcular_deuda_horas(self):
        # Si MI >= referencia, deuda es 0
        self.assertEqual(calcular_deuda_horas(mi=25.0, loc=1000, mi_referencia=20.0), 0.0)

        # Si MI < referencia, deuda = (ref - mi) * loc * k (k=0.01)
        deuda = calcular_deuda_horas(mi=10.0, loc=500, mi_referencia=20.0, factor_k=0.01)
        self.assertAlmostEqual(deuda, 50.0, places=2)

    def test_calcular_costo_reparacion(self):
        # deuda * 30 USD
        self.assertEqual(calcular_costo_reparacion(10.0, costo_hora_usd=30.0), 300.0)

    def test_calcular_interes_anual(self):
        # 10 cambios * 2 horas * 30 USD = 600 USD
        self.assertEqual(calcular_interes_anual(10, 2.0, costo_hora_usd=30.0), 600.0)

    def test_calcular_payback_y_roi(self):
        costo = 1000.0
        interes = 500.0
        payback = calcular_payback_anios(costo, interes)
        self.assertEqual(payback, 2.0)

        # ROI 4 años = 100 * ((500*4) - 1000) / 1000 = 100%
        roi = calcular_roi_4_anios(costo, interes, anios=4)
        self.assertEqual(roi, 100.0)

        # Casos borde sin interés
        self.assertIsNone(calcular_payback_anios(1000.0, 0.0))
        self.assertEqual(calcular_payback_anios(0.0, 0.0), 0.0)

    def test_construir_reporte_archivo(self):
        m = FileMetric(ruta="archivo.go", lenguaje="go", loc=300, complejidad_ciclomatica=20, mi=15.0)
        params = FinancialParams(costo_hora_usd=30.0, factor_correccion_k=0.01, mi_referencia_default=20.0)

        reporte = construir_reporte_archivo(
            metrica=m,
            mi_referencia=20.0,
            cambios_anuales=5,
            delta_t_horas=2.0,
            fuente_interes="yaml",
            params=params,
        )

        self.assertEqual(reporte.estado_mi, "CRITICO")
        self.assertEqual(reporte.deuda_horas, 15.0)  # (20 - 15) * 300 * 0.01
        self.assertEqual(reporte.costo_reparacion_usd, 450.0)  # 15 * 30
        self.assertEqual(reporte.interes_anual_usd, 300.0)  # 5 * 2 * 30
        self.assertEqual(reporte.payback_anios, 1.5)  # 450 / 300
        self.assertAlmostEqual(reporte.roi_4_anios_porc, 166.67, places=2)
        self.assertEqual(reporte.fuente_interes, "yaml")


if __name__ == "__main__":
    unittest.main()
