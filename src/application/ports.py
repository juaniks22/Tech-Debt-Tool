"""
Puertos de entrada y salida (interfaces abstractas) para la arquitectura hexagonal.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

from src.domain.models import (
    AnalysisSummary,
    DebtReport,
    FileMetric,
    FrictionEstimate,
)


@runtime_checkable
class CodeAnalyzer(Protocol):
    """Puerto para analizadores estáticos de código de distintos lenguajes."""

    name: str
    supported_extensions: set[str]

    def can_analyze(self, repo_path: Path, subpath: str = "") -> bool:
        """Determina si el analizador puede operar sobre el repositorio o subcarpeta."""
        ...

    def analyze(self, repo_path: Path, subpath: str = "") -> list[FileMetric]:
        """Ejecuta el análisis y retorna la lista de métricas por archivo."""
        ...


@runtime_checkable
class FrictionProvider(Protocol):
    """Puerto para estimar cambios anuales y fricción (Δt) por archivo."""

    def get_friction(
        self, ruta_archivo: str, metrica: FileMetric, deuda_horas: float
    ) -> FrictionEstimate:
        """Determina los cambios anuales, delta_t y la fuente para un archivo."""
        ...


@runtime_checkable
class ReportExporter(Protocol):
    """Puerto para exportar los resultados del análisis."""

    def export(self, summary: AnalysisSummary, destination: Optional[Path] = None) -> None:
        """Exporta el reporte consolidado al destino especificado o salida estándar."""
        ...
