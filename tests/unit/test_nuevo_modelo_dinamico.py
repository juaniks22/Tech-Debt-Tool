"""
Tests unitarios y de validación para el Nuevo Modelo de Deuda Técnica y Fricción Operativa
basados en el documento de especificación técnica:
c_lculo_de_deuda_t_cnica_y_modelo_de_fricci_n_operativa.md
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
    calcular_factor_friccion,
    calcular_friccion_operativa,
    calcular_k_dinamico,
    calcular_mi,
    calcular_roi_4_anios,
    calcular_roi_ajustado_riesgo,
    construir_reporte_archivo,
    metrica_go_desde_raw,
)
from src.domain.models import FileMetric, FinancialParams


class TestNuevoModeloDinamico(unittest.TestCase):
    def test_condiciones_de_contorno_friccion(self):
        """
        Pág. 18-19:
        - Si MI = 75 (límite óptimo), la brecha se anula: F(MI) = 1.0
        - Si MI = 0 (caos total), F(MI) = 1 + 3 = 4.0 (límite empírico de Capers Jones)
        - Si MI >= 75, F(MI) = 1.0
        """
        self.assertEqual(calcular_factor_friccion(75.0, mi_umbral=75.0, c=3.0), 1.0)
        self.assertEqual(calcular_factor_friccion(85.0, mi_umbral=75.0, c=3.0), 1.0)
        self.assertEqual(calcular_factor_friccion(100.0, mi_umbral=75.0, c=3.0), 1.0)
        self.assertAlmostEqual(calcular_factor_friccion(0.0, mi_umbral=75.0, c=3.0), 4.0, places=4)

    def test_factor_velocidad_k_dinamico(self):
        """
        Pág. 2 (Sección 2):
        K = [0.01 - (EF / 5) * 0.0067] * TCF
        - EF = 0 (inexperto): 6 min/línea -> K = 0.01
        - EF = 5 (alto rendimiento): 2 min/línea -> K = 0.0033
        """
        self.assertAlmostEqual(calcular_k_dinamico(ef=0.0, tcf=1.0), 0.01, places=4)
        self.assertAlmostEqual(calcular_k_dinamico(ef=5.0, tcf=1.0), 0.0033, places=4)
        self.assertAlmostEqual(calcular_k_dinamico(ef=2.5, tcf=1.0), 0.00665, places=5)
        # Con TCF complejidad técnica
        self.assertAlmostEqual(calcular_k_dinamico(ef=0.0, tcf=1.2), 0.012, places=4)

    def test_caso_practico_golang_documento_pag_19_20(self):
        """
        Valida EXACTAMENTE los números del caso práctico de Go detallado en la Pág. 19-20:
        - LOC = 166, G = 25 -> MI = 21.90
        - T_clean = 6h, N = 10 intervenciones, Tarifa = 35 USD/h
        - F(MI) = 1 + ((75 - 21.90)/75)^2 * 3 = 2.50
        - T_real = 6 * 2.5 = 15h, Fricción Pura = 9h
        - Interés Anual = 10 * 9 * 35 = 3,150 USD
        - Deuda Horas = (75 - 21.90) * 166 * 0.01 = 88.15 h
        - Capital de la Deuda (Costo Reparación) = 88.146 * 35 = 3,085.11 USD
        """
        # 1. MI
        mi = calcular_mi(loc=166, complejidad_ciclomatica=25)
        self.assertAlmostEqual(mi, 21.90, places=1)

        # 2. Fricción Operativa
        f_mi, t_real, delta_t = calcular_friccion_operativa(mi=mi, t_clean=6.0, mi_umbral=75.0, c=3.0)
        self.assertAlmostEqual(f_mi, 2.50, places=1)
        self.assertAlmostEqual(t_real, 15.0, places=0)
        self.assertAlmostEqual(delta_t, 9.0, places=0)

        # 3. Reporte completo con FinancialParams calibrado
        params = FinancialParams(
            modelo="dinamico",
            costo_hora_usd=35.0,
            mi_referencia_default=75.0,
            factor_c=3.0,
            ef_experiencia=0.0,
            tcf=1.0,
            tasa_exito_roi=0.65,
        )
        metrica = metrica_go_desde_raw("main.go", loc=166, complejidades_funciones=[25])
        rep = construir_reporte_archivo(
            metrica=metrica,
            mi_referencia=75.0,
            cambios_anuales=10,
            delta_t_horas=None,  # Para que se calcule vía F(MI)
            fuente_interes="fijo",
            params=params,
            t_clean_horas=6.0,
        )

        self.assertEqual(rep.estado_mi, "CRITICO")  # 21.90 < 50
        self.assertAlmostEqual(rep.factor_friccion, 2.50, delta=0.02)
        self.assertAlmostEqual(rep.t_real_horas, 15.02, delta=0.1)
        self.assertAlmostEqual(rep.delta_t_horas, 9.02, delta=0.1)
        self.assertAlmostEqual(rep.deuda_horas, 88.15, delta=0.1)
        self.assertAlmostEqual(rep.costo_reparacion_usd, 3085.11, delta=5.0)
        self.assertAlmostEqual(rep.interes_anual_usd, 3157.0, delta=10.0)
        self.assertAlmostEqual(rep.payback_anios, 0.98, delta=0.05)

        # 4. Calibración de ROI
        # Nominal: 100 * ((3157 * 4) - 3085) / 3085 ~ 309%
        self.assertGreater(rep.roi_4_anios_porc, 300.0)
        # Ajustado por 65% de probabilidad de éxito:
        # Beneficio = 3157 * 4 * 0.65 = 8208.2. ROI = (8208.2 - 3085) / 3085 * 100 ~ 166%
        self.assertGreater(rep.roi_ajustado_porc, 160.0)
        self.assertLess(rep.roi_ajustado_porc, rep.roi_4_anios_porc)

    def test_baselines_automaticos_por_capa(self):
        """
        Pág. 21:
        - Backend: T_clean = 7h, N = 10
        - Frontend: T_clean = 4h, N = 30
        """
        params = FinancialParams(modelo="dinamico")
        m_go = FileMetric(ruta="service.go", lenguaje="go", loc=200, complejidad_ciclomatica=15, mi=40.0)
        m_dart = FileMetric(ruta="widget.dart", lenguaje="dart", loc=200, complejidad_ciclomatica=15, mi=40.0)

        rep_go = construir_reporte_archivo(
            metrica=m_go,
            mi_referencia=75.0,
            cambios_anuales=params.intervenciones_backend,
            delta_t_horas=None,
            fuente_interes="fijo",
            params=params,
        )
        rep_dart = construir_reporte_archivo(
            metrica=m_dart,
            mi_referencia=75.0,
            cambios_anuales=params.intervenciones_frontend,
            delta_t_horas=None,
            fuente_interes="fijo",
            params=params,
        )

        self.assertEqual(rep_go.t_clean_horas, 7.0)
        self.assertEqual(rep_dart.t_clean_horas, 4.0)
        self.assertGreater(rep_go.t_real_horas, 7.0)
        self.assertGreater(rep_dart.t_real_horas, 4.0)

    def test_retrocompatibilidad_modelo_clasico(self):
        """Valida que el modelo clásico mantenga el cálculo histórico sin F(MI)."""
        params = FinancialParams.clasico()
        m = FileMetric(ruta="legacy.go", lenguaje="go", loc=100, complejidad_ciclomatica=10, mi=15.0)
        rep = construir_reporte_archivo(
            metrica=m,
            mi_referencia=20.0,
            cambios_anuales=10,
            delta_t_horas=2.0,
            fuente_interes="fijo",
            params=params,
        )
        self.assertEqual(rep.modelo_calculo, "clasico")
        self.assertIsNone(rep.factor_friccion)
        self.assertIsNone(rep.roi_ajustado_porc)
        self.assertEqual(rep.deuda_horas, 5.0)  # (20 - 15) * 100 * 0.01


if __name__ == "__main__":
    unittest.main()
