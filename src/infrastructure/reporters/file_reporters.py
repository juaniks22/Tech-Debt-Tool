"""
Exportadores de archivos estructurados: JSON y CSV.
"""
from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.application.ports import ReportExporter
from src.domain.models import AnalysisSummary, DebtReport


class JsonReporter(ReportExporter):
    """Exporta el reporte en formato JSON con metadatos de auditoría y modelo."""

    def export(self, summary: AnalysisSummary, destination: Optional[Path] = None) -> None:
        target = destination or Path("reporte_deuda.json")
        data = {
            "generado_en": datetime.now(timezone.utc).isoformat(),
            "repo_path": summary.repo_path,
            "modelo_calculo": summary.modelo_calculo,
            "total_loc": summary.total_loc,
            "total_deuda_horas": summary.total_deuda_horas,
            "total_costo_reparacion_usd": summary.total_costo_reparacion_usd,
            "total_interes_anual_usd": summary.total_interes_anual_usd,
            "archivos": [asdict(r) for r in summary.reportes],
        }
        target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @staticmethod
    def exportar(reportes: list[DebtReport], path: Path) -> None:
        """Método helper retrocompatible."""
        data = {
            "generado_en": datetime.now(timezone.utc).isoformat(),
            "archivos": [asdict(r) for r in reportes],
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


class CsvReporter(ReportExporter):
    """Exporta el reporte en formato tabular CSV estándar."""

    def export(self, summary: AnalysisSummary, destination: Optional[Path] = None) -> None:
        target = destination or Path("reporte_deuda.csv")
        self.exportar(summary.reportes, target)

    @staticmethod
    def exportar(reportes: list[DebtReport], path: Path) -> None:
        if not reportes:
            return
        campos = list(asdict(reportes[0]).keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=campos)
            writer.writeheader()
            for r in reportes:
                writer.writerow(asdict(r))
