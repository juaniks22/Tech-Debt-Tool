"""
Dominio de Tech-Debt-Tool: Modelos de datos inmutables y reglas de negocio puras.
"""
from src.domain.calculator import (
    calcular_costo_reparacion,
    calcular_deuda_horas,
    calcular_interes_anual,
    calcular_mi,
    calcular_payback_anios,
    calcular_roi_4_anios,
    construir_reporte_archivo,
)
from src.domain.models import (
    AnalysisSummary,
    DebtReport,
    FileMetric,
    FinancialParams,
    FrictionEstimate,
    MetricasArchivo,
    ReporteFinancieroArchivo,
)

__all__ = [
    "FileMetric",
    "MetricasArchivo",
    "DebtReport",
    "ReporteFinancieroArchivo",
    "FinancialParams",
    "FrictionEstimate",
    "AnalysisSummary",
    "calcular_mi",
    "calcular_deuda_horas",
    "calcular_costo_reparacion",
    "calcular_interes_anual",
    "calcular_payback_anios",
    "calcular_roi_4_anios",
    "construir_reporte_archivo",
]
