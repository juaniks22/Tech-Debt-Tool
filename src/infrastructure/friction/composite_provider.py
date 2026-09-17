"""
Proveedor compuesto de fricción que aplica la cadena de resolución (YAML > Sin Deuda > Git > Fijo).
"""
from __future__ import annotations

from typing import Optional

from src.application.ports import FrictionProvider
from src.domain.models import FileMetric, FrictionEstimate
from src.infrastructure.friction.fixed_provider import FixedDefaultFrictionProvider
from src.infrastructure.friction.git_provider import GitCommitFrictionProvider
from src.infrastructure.friction.yaml_provider import YamlFrictionProvider


class CompositeFrictionProvider(FrictionProvider):
    """
    Cadena de responsabilidad y fallback:
    1. Archivos configurados explícitamente en el YAML (máxima prioridad humana).
    2. Archivos con MI aprobado y sin deuda técnica (MI >= referencia) -> fricción 0.
    3. Conteo de cambios en el último año vía Git (si está habilitado y disponible).
    4. Valores fijos por defecto (último recurso).
    """

    def __init__(
        self,
        yaml_provider: Optional[YamlFrictionProvider] = None,
        git_provider: Optional[GitCommitFrictionProvider] = None,
        fixed_provider: Optional[FixedDefaultFrictionProvider] = None,
        metodo_estimacion: str = "git",
    ) -> None:
        self.yaml_provider = yaml_provider
        self.git_provider = git_provider
        self.fixed_provider = fixed_provider or FixedDefaultFrictionProvider()
        self.metodo_estimacion = metodo_estimacion

    def get_friction(
        self, ruta_archivo: str, metrica: FileMetric, deuda_horas: float
    ) -> FrictionEstimate:
        # 1. Configuración explícita en YAML
        if self.yaml_provider:
            est_yaml = self.yaml_provider.get_friction(ruta_archivo, metrica, deuda_horas)
            if est_yaml is not None:
                return est_yaml

        # 2. Archivos sin deuda técnica: no sufren fricción por mala calidad
        if deuda_horas <= 0.0:
            return FrictionEstimate(
                cambios_anuales=0,
                delta_t_horas=0.0,
                fuente="sin_deuda",
            )

        # 3. Estimación por Git si está seleccionada
        if self.metodo_estimacion == "git" and self.git_provider:
            est_git = self.git_provider.get_friction(ruta_archivo, metrica, deuda_horas)
            if est_git is not None:
                return est_git

        # 4. Fallback a valores fijos
        return self.fixed_provider.get_friction(ruta_archivo, metrica, deuda_horas)
