"""
Registro extensible de analizadores de código fuente (Patrón Strategy + Registry).
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set

from src.application.ports import CodeAnalyzer
from src.infrastructure.analyzers.dart_analyzer import DartAnalyzer
from src.infrastructure.analyzers.go_analyzer import GoAnalyzer


class AnalyzerRegistry:
    """Gestiona los analizadores disponibles y resuelve cuáles deben ejecutarse."""

    def __init__(self) -> None:
        self._analyzers: Dict[str, CodeAnalyzer] = {}

    def register(self, analyzer: CodeAnalyzer) -> None:
        """Registra un nuevo analizador de lenguaje."""
        self._analyzers[analyzer.name] = analyzer

    def get(self, name: str) -> Optional[CodeAnalyzer]:
        """Obtiene un analizador por nombre."""
        return self._analyzers.get(name)

    def get_all(self) -> List[CodeAnalyzer]:
        """Retorna todos los analizadores registrados."""
        return list(self._analyzers.values())

    def get_active_analyzers(
        self,
        repo_path: Path,
        subpaths: Optional[Dict[str, str]] = None,
        enabled_names: Optional[Set[str]] = None,
    ) -> List[CodeAnalyzer]:
        """
        Filtra y devuelve los analizadores activos para el repositorio dado,
        respetando filtros de nombres habilitados y capacidad de análisis.
        """
        sub = subpaths or {}
        activos: List[CodeAnalyzer] = []
        for name, analyzer in self._analyzers.items():
            if enabled_names is not None and name not in enabled_names:
                continue
            subpath = sub.get(name, "")
            if analyzer.can_analyze(repo_path, subpath):
                activos.append(analyzer)
        return activos


def crear_registro_por_defecto() -> AnalyzerRegistry:
    """Crea y pre-registra los analizadores oficiales del proyecto (Go y Dart)."""
    registry = AnalyzerRegistry()
    registry.register(GoAnalyzer())
    registry.register(DartAnalyzer())
    return registry
