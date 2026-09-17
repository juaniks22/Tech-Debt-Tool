"""
Entidades y modelos del dominio para el análisis de deuda técnica.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FileMetric:
    """Métricas técnicas de código fuente de un archivo individual."""
    ruta: str
    lenguaje: str  # "go" | "dart" | "python" | etc.
    loc: int
    complejidad_ciclomatica: int
    complejidad_por_funcion: list[int] = field(default_factory=list)
    mi: Optional[float] = None  # MI reportado directamente o precalculado


# Alias para retrocompatibilidad
MetricasArchivo = FileMetric


@dataclass(frozen=True)
class FinancialParams:
    """Parámetros financieros y coeficientes de cálculo de deuda técnica."""
    costo_hora_usd: float = 30.0
    factor_correccion_k: float = 0.01
    mi_referencia_default: float = 20.0
    mi_umbral_critico: float = 20.0
    mi_umbral_excelente: float = 60.0
    anios_proyeccion: int = 4


@dataclass
class FrictionEstimate:
    """Estimación de fricción de desarrollo debida a mala calidad o deuda técnica."""
    cambios_anuales: Optional[int] = None
    delta_t_horas: Optional[float] = None
    fuente: str = "ninguna"  # "yaml", "git", "fijo", "sin_deuda", "ninguna"


@dataclass
class DebtReport:
    """Reporte de análisis técnico y financiero de un archivo."""
    ruta: str
    lenguaje: str
    loc: int
    complejidad_ciclomatica: int
    mi: float
    estado_mi: str = "CRITICO"  # "CRITICO" (<20), "APROBADO" (20..59), "EXCELENTE" (>=60)
    deuda_horas: Optional[float] = None
    costo_reparacion_usd: Optional[float] = None
    interes_anual_usd: Optional[float] = None
    payback_anios: Optional[float] = None
    roi_4_anios_porc: Optional[float] = None
    tiene_datos_interes: bool = False
    fuente_interes: str = "ninguna"  # "yaml", "git", "fijo", "sin_deuda", "ninguna"


# Alias para retrocompatibilidad con tests existentes
ReporteFinancieroArchivo = DebtReport


@dataclass
class AnalysisSummary:
    """Resumen consolidado del análisis de un repositorio."""
    repo_path: str
    fecha: str
    reportes: list[DebtReport] = field(default_factory=list)
    total_loc: int = 0
    archivos_criticos: int = 0
    archivos_aprobados: int = 0
    archivos_excelentes: int = 0
    total_deuda_horas: float = 0.0
    total_costo_reparacion_usd: float = 0.0
    total_interes_anual_usd: float = 0.0
