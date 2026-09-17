"""
Proveedor de estimaciones fijas por defecto para archivos sin configuración explícita.
"""
from __future__ import annotations

from src.domain.models import FileMetric, FrictionEstimate


class FixedDefaultFrictionProvider:
    """Provee valores fijos predeterminados (cambios y delta_t) como última instancia."""

    def __init__(self, cambios_anuales: int = 10, delta_t_horas: float = 2.0) -> None:
        self.cambios_anuales = cambios_anuales
        self.delta_t_horas = delta_t_horas

    def get_friction(
        self, ruta_archivo: str, metrica: FileMetric, deuda_horas: float
    ) -> FrictionEstimate:
        return FrictionEstimate(
            cambios_anuales=self.cambios_anuales,
            delta_t_horas=self.delta_t_horas,
            fuente="fijo",
        )
