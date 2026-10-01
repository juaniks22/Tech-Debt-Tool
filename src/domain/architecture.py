"""
Modelos y entidades del dominio para análisis arquitectónico (Robert C. Martin)
y valoración financiera de deuda técnica SQALE (ISO/IEC 25010).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ModuleMetrics:
    """Métricas arquitectónicas de Robert C. Martin para un límite lógico (carpeta/módulo)."""
    nombre: str                  # Nombre del módulo (ej: "domain", "handler", "presentation")
    ruta: str                    # Ruta relativa dentro del proyecto
    ca: int = 0                  # Acoplamiento Aferente (módulos externos que dependen de este)
    ce: int = 0                  # Acoplamiento Eferente (módulos externos de los que depende)
    inestabilidad: float = 0.0   # I = Ce / (Ca + Ce)
    na: int = 0                  # Clases abstractas o interfaces en el módulo
    nc: int = 0                  # Total de clases/estructuras en el módulo
    abstraccion: float = 0.0     # A = Na / Nc
    distancia_d: float = 0.0     # D = |A + I - 1|
    zona: str = "SECUENCIA_PRINCIPAL"  # "SECUENCIA_PRINCIPAL" | "ZONA_DOLOR" | "ZONA_INUTILIDAD"
    archivos: int = 0            # Total de archivos de código en el módulo
    dependencias_in: list[str] = field(default_factory=list)   # Nombres de módulos que importan a este
    dependencias_out: list[str] = field(default_factory=list)  # Nombres de módulos importados por este


@dataclass
class Violation:
    """Violación detectada por el catálogo de reglas técnicas SQALE."""
    regla: str                     # Identificador de regla (ej: "CC_ALTA", "IMPORT_CIRCULAR")
    categoria_sqale: str           # Dimensión ISO 25010 (ej: "Mantenibilidad", "Fiabilidad")
    archivo: str                   # Ruta relativa del archivo o módulo
    linea: Optional[int] = None    # Línea donde se detectó (opcional)
    detalle: str = ""              # Detalle contextual
    remediacion_minutos: float = 0.0  # Tiempo estimado de corrección en minutos


@dataclass
class SQALEReport:
    """Consolidado del análisis arquitectónico y de valoración SQALE."""
    modulos: list[ModuleMetrics] = field(default_factory=list)
    violaciones: list[Violation] = field(default_factory=list)
    total_violaciones: int = 0
    l_td: float = 0.0              # Costo de remediación de deuda técnica SQALE en USD
    v_a: float = 0.0               # Valor numérico del activo en USD
    costo_reemplazo: float = 0.0   # Costo base de reemplazo estimado
    tdr: float = 0.0               # Technical Debt Ratio (%)
    estado_tdr: str = "EXCELENTE"  # "EXCELENTE" (<=5%) | "MODERADO" (5-20%) | "CRITICO" (>20%)
    alpha_l: float = 1.0           # Factor de calibración de complejidad de lenguaje
    beta_l: float = 1.0            # Factor de productividad relativa por lenguaje
