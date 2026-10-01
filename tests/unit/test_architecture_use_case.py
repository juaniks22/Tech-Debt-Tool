"""
Tests unitarios para el caso de uso de arquitectura y penalización por distancia D.
"""
import tempfile
import unittest
from pathlib import Path

from src.application.architecture_use_case import ArchitectureAnalysisUseCase
from src.domain.models import DebtReport, FileMetric


class TestArchitectureUseCase(unittest.TestCase):
    def test_architecture_use_case_execution_and_d_penalty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            backend = root / "backend"
            repo_dir = backend / "repository"
            repo_dir.mkdir(parents=True)

            # Archivo Go en repository
            repo_file = repo_dir / "order_repo.go"
            repo_file.write_text(
                """package repository
type OrderRepo struct {}
""",
                encoding="utf-8",
            )

            file_metrics = [
                FileMetric(
                    ruta="backend/repository/order_repo.go",
                    lenguaje="go",
                    loc=200,
                    complejidad_ciclomatica=6,
                )
            ]

            debt_reports = [
                DebtReport(
                    ruta="backend/repository/order_repo.go",
                    lenguaje="go",
                    loc=200,
                    complejidad_ciclomatica=6,
                    mi=25.0,
                    deuda_horas=10.0,
                    costo_reparacion_usd=300.0,
                )
            ]

            use_case = ArchitectureAnalysisUseCase(
                tarifa_usd=30.0,
                alpha_l=1.0,
                beta_l=1.0,
                costo_linea_base=1.0,
                peso_penalizacion_d=0.3,
            )

            report = use_case.execute(
                repo_path=root,
                subpath_map={"go": "backend"},
                file_metrics=file_metrics,
                debt_reports=debt_reports,
            )

            self.assertEqual(len(report.modulos), 1)
            modulo = report.modulos[0]
            self.assertEqual(modulo.nombre, "repository")
            # repository: Na=0, Nc=1 -> A=0. Ca=0, Ce=0 -> I=0.
            # D = |0 + 0 - 1| = 1.0 (Zona de dolor si I<0.5 y A<0.5)
            self.assertEqual(modulo.distancia_d, 1.0)
            self.assertEqual(modulo.zona, "ZONA_DOLOR")

            # Penalización D = 1.0 + (1.0 * 0.3) = 1.30 (+30%)
            # Deuda original 10.0h -> 13.0h
            # Costo original $300 -> $390
            self.assertAlmostEqual(debt_reports[0].deuda_horas, 13.0, places=2)
            self.assertAlmostEqual(debt_reports[0].costo_reparacion_usd, 390.0, places=2)

            # SQALE calculations
            self.assertGreater(report.total_violaciones, 0)
            self.assertGreater(report.l_td, 0.0)
            self.assertIsNotNone(report.tdr)
            self.assertIn(report.estado_tdr, ["EXCELENTE", "MODERADO", "CRITICO"])


if __name__ == "__main__":
    unittest.main()
