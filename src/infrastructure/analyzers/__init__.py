"""
Módulo de analizadores de código e infraestructura de análisis estático.
"""
from src.infrastructure.analyzers.base import BaseAnalyzer
from src.infrastructure.analyzers.dart_analyzer import DartAnalyzer
from src.infrastructure.analyzers.go_analyzer import GoAnalyzer
from src.infrastructure.analyzers.registry import (
    AnalyzerRegistry,
    crear_registro_por_defecto,
)

__all__ = [
    "BaseAnalyzer",
    "GoAnalyzer",
    "DartAnalyzer",
    "AnalyzerRegistry",
    "crear_registro_por_defecto",
]
