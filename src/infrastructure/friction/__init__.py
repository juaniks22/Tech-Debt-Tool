"""
Módulo de proveedores de fricción y cambios anuales para el cálculo financiero.
"""
from src.infrastructure.friction.composite_provider import CompositeFrictionProvider
from src.infrastructure.friction.fixed_provider import FixedDefaultFrictionProvider
from src.infrastructure.friction.git_provider import GitCommitFrictionProvider
from src.infrastructure.friction.yaml_provider import YamlFrictionProvider

__all__ = [
    "YamlFrictionProvider",
    "GitCommitFrictionProvider",
    "FixedDefaultFrictionProvider",
    "CompositeFrictionProvider",
]
