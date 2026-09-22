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
        es_dinamico = summary.modelo_calculo == "dinamico"
        titulo_modelo = (
            "Modelo de Fricción Operativa Dinámica (F(MI), C=3, MI=75)"
            if es_dinamico
            else "Modelo Clásico de Deuda Técnica (MI=20)"
        )

        lines: list[str] = [
            "# 📊 Reporte Financiero de Deuda Técnica",
            "",
            f"**Repositorio:** `{summary.repo_path}`  ",
            f"**Fecha de Análisis:** `{summary.fecha}`  ",
            f"**Modelo de Cálculo:** `{titulo_modelo}`  ",
            "",
            "## 📈 Resumen Ejecutivo",
            "",
            "| Métrica | Valor |",
            "|---|---|",
            f"| **Total Archivos Analizados** | `{len(summary.reportes)}` |",
            f"| **Líneas de Código Totales (LOC)** | `{summary.total_loc:,}` |",
            f"| **🔴 Archivos en Estado Crítico** | `{summary.archivos_criticos}` |",
            f"| **{'🟡' if es_dinamico else '🟢'} Archivos Aprobados** | `{summary.archivos_aprobados}` |",
            f"| **🟢 Archivos Excelentes** | `{summary.archivos_excelentes}` |",
            f"| **Horas de Deuda Técnica Total** | `{summary.total_deuda_horas:,.2f} h` |",
            f"| **Costo Total Estimado de Reparación** | `${summary.total_costo_reparacion_usd:,.2f} USD` |",
            f"| **Interés Anual por Fricción (Costo Anual)** | `${summary.total_interes_anual_usd:,.2f} USD/año` |",
            "",
            "## 📋 Detalle por Archivo (Ordenado por Deuda)",
            "",
        ]

        if es_dinamico:
            lines.extend([
                "| Estado | Archivo | Lenguaje | LOC | CC | MI | F(MI) | Δt (h) | Deuda (h) | Costo ($) | Interés/año ($) | Payback (años) | ROI (4 años) | ROI Ajustado (65%) |",
                "|:---:|---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ])
            for r in summary.reportes:
                icono = "🔴" if r.estado_mi == "CRITICO" else ("🟡" if r.estado_mi == "APROBADO" else "🟢")
                costo_str = f"${r.costo_reparacion_usd:,.2f}" if r.costo_reparacion_usd is not None else "-"
                interes_str = f"${r.interes_anual_usd:,.2f}" if r.interes_anual_usd is not None else "s/d"
                payback_str = f"{r.payback_anios:.2f}" if r.payback_anios is not None else "-"
                roi_str = f"{r.roi_4_anios_porc:+.1f}%" if r.roi_4_anios_porc is not None else "-"
                roi_aj_str = f"{r.roi_ajustado_porc:+.1f}%" if r.roi_ajustado_porc is not None else "-"
                deuda_str = f"{r.deuda_horas:.2f}" if r.deuda_horas is not None else "0.00"
                f_str = f"{r.factor_friccion:.2f}x" if r.factor_friccion is not None else "-"
                dt_str = f"+{r.delta_t_horas:.1f}h" if r.delta_t_horas is not None else "-"

                lines.append(
                    f"| {icono} | `{r.ruta}` | {r.lenguaje} | {r.loc} | {r.complejidad_ciclomatica} | "
                    f"{r.mi:.2f} | {f_str} | {dt_str} | {deuda_str} | {costo_str} | {interes_str} | "
                    f"{payback_str} | {roi_str} | {roi_aj_str} |"
                )

            lines.extend([
                "",
                "---",
                "### 📌 Criterios de Evaluación y Fundamentos Matemáticos",
                "- 🔴 **Crítico ($MI < 50$):** Fuerte degradación arquitectural, factor de fricción severo ($F(MI) > 1.33x$).",
                "- 🟡 **Aprobado ($50 \\le MI < 75$):** Operación aceptable pero con margen de optimización ($1.0x \\le F(MI) \\le 1.33x$).",
                "- 🟢 **Excelente ($MI \\ge 75$):** Eficiencia óptima, código limpio ($F(MI) = 1.0x$, cero fricción pura).",
                "",
                "**Modelo de Fricción Elástica:**",
                "$$F(MI) = 1 + \\left(\\frac{75 - MI}{75}\\right)^2 \\cdot 3$$",
                "**Factor de Velocidad Base Dinámico:**",
                "$$K_{\\text{Dinámico}} = \\left[ 0.01 - \\left(\\frac{EF}{5}\\right) \\cdot 0.0067 \\right] \\cdot TCF$$",
                "- **ROI Ajustado por Riesgo:** Aplica el 65% de probabilidad empírica de éxito en refactorizaciones incrementales.",
                "",
                "_Reporte generado automáticamente por Tech-Debt-Tool_",
            ])
        else:
            lines.extend([
                "| Estado | Archivo | Lenguaje | LOC | CC | MI | Deuda (h) | Costo ($) | Interés/año ($) | Payback (años) | ROI (4 años) |",
                "|:---:|---|:---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ])
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
