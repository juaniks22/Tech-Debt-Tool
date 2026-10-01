"""
Tests unitarios para las fórmulas de métricas arquitectónicas de Robert C. Martin y SQALE.
"""
import unittest

from src.domain.architecture import Violation
from src.domain.architecture_calculator import (
    calcular_abstraccion,
    calcular_costo_reemplazo,
    calcular_distancia_d,
    calcular_inestabilidad,
    calcular_l_td,
    calcular_tdr,
    calcular_valor_activo,
    clasificar_tdr,
    clasificar_zona,
    factor_penalizacion_d,
)


class TestArchitectureCalculator(unittest.TestCase):
    def test_inestabilidad_casos_borde_y_calculo(self):
        # Módulo completamente estable (I = 0)
        self.assertEqual(calcular_inestabilidad(ca=5, ce=0), 0.0)
        # Módulo completamente inestable (I = 1)
        self.assertEqual(calcular_inestabilidad(ca=0, ce=5), 1.0)
        # Módulo balanceado (I = 0.5)
        self.assertEqual(calcular_inestabilidad(ca=3, ce=3), 0.5)
        # Caso aislado (Ca=0, Ce=0) -> 0.0
        self.assertEqual(calcular_inestabilidad(ca=0, ce=0), 0.0)

    def test_abstraccion(self):
        # 2 interfaces de 10 clases -> A = 0.2
        self.assertEqual(calcular_abstraccion(na=2, nc=10), 0.2)
        # Módulo 100% abstracto -> A = 1.0
        self.assertEqual(calcular_abstraccion(na=5, nc=5), 1.0)
        # Sin clases -> A = 0.0
        self.assertEqual(calcular_abstraccion(na=0, nc=0), 0.0)

    def test_distancia_d_y_clasificacion_zona(self):
        # Balance perfecto en la secuencia principal: A=0.2, I=0.8 -> A+I-1 = 0 -> D = 0
        d_perfecto = calcular_distancia_d(0.2, 0.8)
        self.assertAlmostEqual(d_perfecto, 0.0)
        self.assertEqual(clasificar_zona(0.2, 0.8, d_perfecto), "SECUENCIA_PRINCIPAL")

        # Zona de Dolor: muy estable (I=0.1), concreto (A=0.1) -> D = |0.1 + 0.1 - 1| = 0.8
        d_dolor = calcular_distancia_d(0.1, 0.1)
        self.assertAlmostEqual(d_dolor, 0.8)
        self.assertEqual(clasificar_zona(0.1, 0.1, d_dolor), "ZONA_DOLOR")

        # Zona de Inutilidad: muy inestable (I=0.9), muy abstracto (A=0.9) -> D = |0.9 + 0.9 - 1| = 0.8
        d_inutil = calcular_distancia_d(0.9, 0.9)
        self.assertAlmostEqual(d_inutil, 0.8)
        self.assertEqual(clasificar_zona(0.9, 0.9, d_inutil), "ZONA_INUTILIDAD")

    def test_factor_penalizacion_d(self):
        # Si D=0, no hay penalización (factor 1.0)
        self.assertEqual(factor_penalizacion_d(0.0, peso=0.3), 1.0)
        # Si D=0.8 y peso=0.3 -> 1 + 0.24 = 1.24 (+24%)
        self.assertAlmostEqual(factor_penalizacion_d(0.8, peso=0.3), 1.24)

    def test_sqale_l_td_y_tdr(self):
        viols = [
            Violation(regla="CC_ALTA", categoria_sqale="Mantenibilidad", archivo="a.go", remediacion_minutos=30.0),
            Violation(regla="FUNCION_LARGA", categoria_sqale="Mantenibilidad", archivo="b.go", remediacion_minutos=30.0),
        ]
        # Total minutos = 60 min = 1.0 hora
        # Con tarifa 30 USD/h y alpha_l=1.0 -> L_TD = 30.0 USD
        l_td = calcular_l_td(viols, alpha_l=1.0, tarifa_usd=30.0)
        self.assertEqual(l_td, 30.0)

        # LOC = 1000, costo linea = 1.0, beta_l = 1.0 -> Costo Reemplazo = 1000 USD
        reemplazo = calcular_costo_reemplazo(1000, 1.0, 1.0)
        self.assertEqual(reemplazo, 1000.0)

        # Valor activo: 1000 - 30 = 970 USD
        va = calcular_valor_activo(1000, 1.0, 1.0, l_td)
        self.assertEqual(va, 970.0)

        # TDR = (30 / 1000) * 100 = 3.0% (Excelente <= 5%)
        tdr = calcular_tdr(l_td, reemplazo)
        self.assertEqual(tdr, 3.0)
        self.assertEqual(clasificar_tdr(tdr), "EXCELENTE")

        # TDR moderado y crítico
        self.assertEqual(clasificar_tdr(15.0), "MODERADO")
        self.assertEqual(clasificar_tdr(25.0), "CRITICO")


if __name__ == "__main__":
    unittest.main()
