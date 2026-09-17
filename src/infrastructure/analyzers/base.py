"""
Clase base o interfaz para los analizadores de código.
"""
from __future__ import annotations

from pathlib import Path
from typing import Set

from src.application.ports import CodeAnalyzer
from src.domain.models import FileMetric


class BaseAnalyzer:
    """Implementación base que provee utilidades comunes para los analizadores."""

    name: str = "base"
    supported_extensions: Set[str] = set()

    def can_analyze(self, repo_path: Path, subpath: str = "") -> bool:
        target = repo_path / subpath if subpath else repo_path
        if not target.exists():
            return False
        if target.is_file():
            return target.suffix in self.supported_extensions
        # Buscar al menos un archivo con las extensiones soportadas
        for ext in self.supported_extensions:
            if any(target.glob(f"**/*{ext}")):
                return True
        return False
