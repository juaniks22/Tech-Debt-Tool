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
    modelo: str = "dinamico"  # "dinamico" | "clasico"
    costo_hora_usd: float = 30.0
    factor_correccion_k: float = 0.01
    mi_referencia_default: float = 75.0
    mi_umbral_critico: Optional[float] = None
    mi_umbral_excelente: Optional[float] = None
    anios_proyeccion: int = 4
    # Coeficientes del modelo dinámico de fricción y calibración
    factor_c: float = 3.0
    ef_experiencia: float = 0.0  # 0 (inexperto, 6 min/loc) a 5 (alto rendimiento, 2 min/loc)
    tcf: float = 1.0             # Technical Complexity Factor
    tasa_exito_roi: float = 0.65 # Tasa de éxito de refactorización incremental (65%)
    t_clean_backend: float = 7.0 # Horas en código limpio para backend (Go)
    t_clean_frontend: float = 4.0 # Horas en código limpio para frontend (Dart)
    intervenciones_backend: int = 10 # Cambios anuales base para backend
    intervenciones_frontend: int = 30 # Cambios anuales base para frontend

    def __post_init__(self) -> None:
        if self.mi_umbral_critico is None:
            if self.modelo == "clasico" or self.mi_referencia_default <= 20.0:
                object.__setattr__(self, "mi_umbral_critico", 20.0)
            else:
                object.__setattr__(self, "mi_umbral_critico", 50.0)

        if self.mi_umbral_excelente is None:
            if self.modelo == "clasico" or self.mi_referencia_default <= 20.0:
                object.__setattr__(self, "mi_umbral_excelente", 60.0)
            else:
                object.__setattr__(self, "mi_umbral_excelente", 75.0)

    @classmethod
    def clasico(
        cls,
        costo_hora_usd: float = 30.0,
        factor_correccion_k: float = 0.01,
        mi_referencia_default: float = 20.0,
        mi_umbral_critico: float = 20.0,
        mi_umbral_excelente: float = 60.0,
        anios_proyeccion: int = 4,
    ) -> FinancialParams:
        """Crea parámetros con los valores del modelo clásico de clase."""
        return cls(
            modelo="clasico",
            costo_hora_usd=costo_hora_usd,
            factor_correccion_k=factor_correccion_k,
            mi_referencia_default=mi_referencia_default,
            mi_umbral_critico=mi_umbral_critico,
            mi_umbral_excelente=mi_umbral_excelente,
            anios_proyeccion=anios_proyeccion,
        )


@dataclass
class FrictionEstimate:
    """Estimación de fricción de desarrollo debida a mala calidad o deuda técnica."""
    cambios_anuales: Optional[int] = None
    delta_t_horas: Optional[float] = None
    fuente: str = "ninguna"  # "dinamico", "yaml", "git", "fijo", "sin_deuda", "ninguna"
    factor_friccion: Optional[float] = None
    t_clean_horas: Optional[float] = None
    t_real_horas: Optional[float] = None


@dataclass
class DebtReport:
    """Reporte de análisis técnico y financiero de un archivo."""
    ruta: str
    lenguaje: str
    loc: int
    complejidad_ciclomatica: int
    mi: float
    estado_mi: str = "CRITICO"
    deuda_horas: Optional[float] = None
    costo_reparacion_usd: Optional[float] = None
    interes_anual_usd: Optional[float] = None
    payback_anios: Optional[float] = None
    roi_4_anios_porc: Optional[float] = None
    # Nuevas métricas del modelo de fricción y ROI calibrado
    factor_friccion: Optional[float] = None
    t_clean_horas: Optional[float] = None
    t_real_horas: Optional[float] = None
    delta_t_horas: Optional[float] = None
    roi_ajustado_porc: Optional[float] = None
    modelo_calculo: str = "dinamico"
    tiene_datos_interes: bool = False
    fuente_interes: str = "ninguna"


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
    modelo_calculo: str = "dinamico"
