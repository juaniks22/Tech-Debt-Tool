"""
Exportador de reporte en formato Markdown (GitHub Flavored Markdown), ideal para CI/CD y PRs.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from src.application.ports import ReportExporter
from src.domain.models import AnalysisSummary, DebtReport


class MarkdownReporter(ReportExporter):
    """Genera un reporte legible y visualmente estructurado en Markdown."""

    def export(self, summary: AnalysisSummary, destination: Optional[Path] = None) -> None:
        target = destination or Path("reporte_deuda.md")
        contenido = self.generar_markdown(summary)
        target.write_text(contenido, encoding="utf-8")

    @classmethod
    def generar_markdown(cls, summary: AnalysisSummary) -> str:
        lines: list[str] = [
            "# 📊 Reporte Financiero de Deuda Técnica",
            "",
            f"**Repositorio:** `{summary.repo_path}`  ",
            f"**Fecha de Análisis:** `{summary.fecha}`  ",
            "",
            "## 📈 Resumen Ejecutivo",
            "",
            "| Métrica | Valor |",
            "|---|---|",
            f"| **Total Archivos Analizados** | `{len(summary.reportes)}` |",
            f"| **Líneas de Código Totales (LOC)** | `{summary.total_loc:,}` |",
            f"| **🔴 Archivos en Estado Crítico** | `{summary.archivos_criticos}` |",
            f"| **🟢 Archivos Aprobados** | `{summary.archivos_aprobados}` |",
            f"| **🟢 Archivos Excelentes** | `{summary.archivos_excelentes}` |",
            f"| **Horas de Deuda Técnica Total** | `{summary.total_deuda_horas:,.2f} h` |",
            f"| **Costo Total Estimado de Reparación** | `${summary.total_costo_reparacion_usd:,.2f} USD` |",
            f"| **Interés Anual por Fricción (Costo Anual)** | `${summary.total_interes_anual_usd:,.2f} USD/año` |",
            "",
            "## 📋 Detalle por Archivo (Ordenado por Deuda)",
            "",
            "| Estado | Archivo | Lenguaje | LOC | CC | MI | Deuda (h) | Costo ($) | Interés/año ($) | Payback (años) | ROI (4 años) |",
            "|:---:|---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]

        for r in summary.reportes:
            icono = "🔴" if r.estado_mi == "CRITICO" else "🟢"
            costo_str = f"${r.costo_reparacion_usd:,.2f}" if r.costo_reparacion_usd is not None else "-"
            interes_str = f"${r.interes_anual_usd:,.2f}" if r.interes_anual_usd is not None else "s/d"
            payback_str = f"{r.payback_anios:.2f}" if r.payback_anios is not None else "-"
            roi_str = f"{r.roi_4_anios_porc:+.1f}%" if r.roi_4_anios_porc is not None else "-"
            deuda_str = f"{r.deuda_horas:.2f}" if r.deuda_horas is not None else "0.00"

            lines.append(
                f"| {icono} | `{r.ruta}` | {r.lenguaje} | {r.loc} | {r.complejidad_ciclomatica} | "
                f"{r.mi:.2f} | {deuda_str} | {costo_str} | {interes_str} | {payback_str} | {roi_str} |"
            )

        lines.extend([
            "",
            "---",
            "### 📌 Criterios de Evaluación",
            "- 🔴 **Crítico ($MI < 20$):** Requiere refactorización prioritaria por alta fricción de desarrollo.",
            "- 🟢 **Aprobado ($20 \\le MI < 60$):** Calidad aceptable para operación.",
            "- 🟢 **Excelente ($MI \\ge 60$):** Código altamente modular y mantenible.",
            "",
            "_Reporte generado automáticamente por Tech-Debt-Tool_",
        ])

        return "\n".join(lines) + "\n"
