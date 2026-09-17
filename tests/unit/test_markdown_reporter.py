"""
Tests unitarios para MarkdownReporter.
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

from src.domain.models import AnalysisSummary, DebtReport
from src.infrastructure.reporters.markdown_reporter import MarkdownReporter


class TestMarkdownReporter(unittest.TestCase):
    def test_markdown_reporter_generacion(self):
        reporte = DebtReport(
            ruta="internal/repo/academic_repo.go",
            lenguaje="go",
            loc=422,
            complejidad_ciclomatica=68,
            mi=2.48,
            estado_mi="CRITICO",
            deuda_horas=73.95,
            costo_reparacion_usd=2218.47,
            interes_anual_usd=1050.00,
            payback_anios=2.11,
            roi_4_anios_porc=89.32,
            tiene_datos_interes=True,
            fuente_interes="yaml",
        )
        summary = AnalysisSummary(
            repo_path="/test/repo",
            fecha="2026-09-17T00:00:00Z",
            reportes=[reporte],
            total_loc=422,
            archivos_criticos=1,
            archivos_aprobados=0,
            archivos_excelentes=0,
            total_deuda_horas=73.95,
            total_costo_reparacion_usd=2218.47,
            total_interes_anual_usd=1050.00,
        )

        md = MarkdownReporter.generar_markdown(summary)

        self.assertIn("# 📊 Reporte Financiero de Deuda Técnica", md)
        self.assertIn("`/test/repo`", md)
        self.assertIn("| **🔴 Archivos en Estado Crítico** | `1` |", md)
        self.assertIn("`internal/repo/academic_repo.go`", md)
        self.assertIn("🔴", md)
        self.assertIn("$2,218.47", md)
        self.assertIn("+89.3%", md)


if __name__ == "__main__":
    unittest.main()
