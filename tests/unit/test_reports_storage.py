"""
Tests unitarios para la exportación y guardado de reportes versionados por proyecto y fecha.
"""
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from src.domain.models import AnalysisSummary, DebtReport
from src.infrastructure.reporters.file_reporters import CsvReporter, JsonReporter
from src.infrastructure.reporters.markdown_reporter import MarkdownReporter


class TestReportsStorage(unittest.TestCase):
    def test_exportar_reportes_con_timestamp_y_proyecto(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out_base = Path(tmpdir) / "reportes"
            nombre_proyecto = "SGA-practicas"
            dir_proyecto = out_base / nombre_proyecto
            dir_proyecto.mkdir(parents=True, exist_ok=True)

            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_json = dir_proyecto / f"reporte_{timestamp_str}.json"
            target_csv = dir_proyecto / f"reporte_{timestamp_str}.csv"
            target_md = dir_proyecto / f"reporte_{timestamp_str}.md"

            reporte = DebtReport(
                ruta="internal/repo/academic_repo.go",
                lenguaje="go",
                loc=200,
                complejidad_ciclomatica=10,
                mi=35.0,
                deuda_horas=5.0,
                costo_reparacion_usd=150.0,
            )

            summary = AnalysisSummary(
                repo_path=f"C:/projects/{nombre_proyecto}",
                fecha="2026-10-01T12:00:00Z",
                reportes=[reporte],
                total_loc=200,
                total_deuda_horas=5.0,
                total_costo_reparacion_usd=150.0,
            )

            JsonReporter().export(summary, target_json)
            CsvReporter().export(summary, target_csv)
            MarkdownReporter().export(summary, target_md)

            # Verificar existencia de los 3 archivos
            self.assertTrue(target_json.is_file())
            self.assertTrue(target_csv.is_file())
            self.assertTrue(target_md.is_file())

            # Verificar que el nombre cumple el patrón de timestamp
            self.assertTrue(target_json.name.startswith("reporte_"))
            self.assertTrue(target_json.name.endswith(".json"))
            self.assertEqual(len(target_json.stem.replace("reporte_", "")), 15)  # YYYYMMDD_HHMMSS es 15 chars


if __name__ == "__main__":
    unittest.main()
