"""
Tests unitarios para el caso de uso AnalyzeRepositoryUseCase usando mocks aislados de I/O.
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

from src.application.analyze_use_case import AnalyzeRepositoryUseCase
from src.application.ports import CodeAnalyzer, FrictionProvider
from src.domain.models import FileMetric, FinancialParams, FrictionEstimate


class MockAnalyzer(CodeAnalyzer):
    name: str = "mock"
    supported_extensions: set[str] = {".mock"}

    def can_analyze(self, repo_path: Path, subpath: str = "") -> bool:
        return True

    def analyze(self, repo_path: Path, subpath: str = "") -> list[FileMetric]:
        return [
            FileMetric(ruta="pkg/critico.mock", lenguaje="mock", loc=500, complejidad_ciclomatica=50, mi=10.0),
            FileMetric(ruta="pkg/aprobado.mock", lenguaje="mock", loc=200, complejidad_ciclomatica=5, mi=40.0),
        ]


class MockFrictionProvider(FrictionProvider):
    def get_friction(self, ruta_archivo: str, metrica: FileMetric, deuda_horas: float) -> FrictionEstimate:
        if "critico" in ruta_archivo:
            return FrictionEstimate(cambios_anuales=12, delta_t_horas=2.0, fuente="yaml")
        return FrictionEstimate(cambios_anuales=0, delta_t_horas=0.0, fuente="sin_deuda")


class TestAnalyzeUseCase(unittest.TestCase):
    def test_analyze_use_case(self):
        analyzer = MockAnalyzer()
        friction_provider = MockFrictionProvider()
        params = FinancialParams(costo_hora_usd=30.0, factor_correccion_k=0.01, mi_referencia_default=20.0)

        use_case = AnalyzeRepositoryUseCase(
            analyzers=[analyzer],
            friction_provider=friction_provider,
            params=params,
        )

        summary = use_case.execute(repo_path=Path("/fake/repo"))

        self.assertEqual(len(summary.reportes), 2)
        # El archivo crítico debe estar primero (ordenado por deuda descendente)
        critico = summary.reportes[0]
        self.assertEqual(critico.ruta, "pkg/critico.mock")
        self.assertEqual(critico.estado_mi, "CRITICO")
        self.assertEqual(critico.deuda_horas, 50.0)  # (20 - 10) * 500 * 0.01 = 50
        self.assertEqual(critico.costo_reparacion_usd, 1500.0)  # 50 * 30 = 1500
        self.assertEqual(critico.interes_anual_usd, 720.0)  # 12 * 2 * 30 = 720
        self.assertEqual(critico.fuente_interes, "yaml")

        aprobado = summary.reportes[1]
        self.assertEqual(aprobado.ruta, "pkg/aprobado.mock")
        self.assertEqual(aprobado.estado_mi, "APROBADO")
        self.assertEqual(aprobado.deuda_horas, 0.0)
        self.assertEqual(aprobado.fuente_interes, "sin_deuda")

        # Verificar totales acumulados
        self.assertEqual(summary.total_loc, 700)
        self.assertEqual(summary.archivos_criticos, 1)
        self.assertEqual(summary.archivos_aprobados, 1)
        self.assertEqual(summary.total_deuda_horas, 50.0)
        self.assertEqual(summary.total_costo_reparacion_usd, 1500.0)
        self.assertEqual(summary.total_interes_anual_usd, 720.0)


if __name__ == "__main__":
    unittest.main()
