"""
Proveedor de estimaciones fijas por defecto para archivos sin configuración explícita.
"""
from __future__ import annotations

from typing import Optional

from src.domain.models import FileMetric, FrictionEstimate


class FixedDefaultFrictionProvider:
    """Provee valores por defecto o baselines arquitecturales según el modelo."""

    def __init__(
        self,
        cambios_anuales: Optional[int] = None,
        delta_t_horas: Optional[float] = None,
        modelo: str = "dinamico",
        t_clean_backend: float = 7.0,
        t_clean_frontend: float = 4.0,
        intervenciones_backend: int = 10,
        intervenciones_frontend: int = 30,
    ) -> None:
        self.cambios_anuales = cambios_anuales
        self.delta_t_horas = delta_t_horas
        self.modelo = modelo
        self.t_clean_backend = t_clean_backend
        self.t_clean_frontend = t_clean_frontend
        self.intervenciones_backend = intervenciones_backend
        self.intervenciones_frontend = intervenciones_frontend

    def get_friction(
        self, ruta_archivo: str, metrica: FileMetric, deuda_horas: float
    ) -> FrictionEstimate:
        if self.modelo == "dinamico":
            es_frontend = metrica.lenguaje.lower() in ("dart", "flutter")
            t_clean = self.t_clean_frontend if es_frontend else self.t_clean_backend
            n = (
                self.cambios_anuales
                if self.cambios_anuales is not None
                else (self.intervenciones_frontend if es_frontend else self.intervenciones_backend)
            )
            return FrictionEstimate(
                cambios_anuales=n,
                delta_t_horas=self.delta_t_horas,
                t_clean_horas=t_clean,
                fuente="fijo",
            )
        else:
            n = self.cambios_anuales if self.cambios_anuales is not None else 10
            dt = self.delta_t_horas if self.delta_t_horas is not None else 2.0
            return FrictionEstimate(
                cambios_anuales=n,
                delta_t_horas=dt,
                fuente="fijo",
            )
