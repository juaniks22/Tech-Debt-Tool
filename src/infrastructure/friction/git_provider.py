"""
Proveedor de estimaciones de fricción basado en el historial de commits de Git.
"""
from __future__ import annotations

import collections
from pathlib import Path
from typing import Dict, Optional

from src.domain.models import FileMetric, FrictionEstimate
from src.infrastructure.tools.process_runner import correr_comando


class GitCommitFrictionProvider:
    """Extrae el conteo de cambios en el último año a partir de git log y soporta baselines de capa."""

    def __init__(
        self,
        repo_path: Path,
        default_delta_t_horas: Optional[float] = None,
        default_cambios: Optional[int] = None,
        modelo: str = "dinamico",
        t_clean_backend: float = 7.0,
        t_clean_frontend: float = 4.0,
        intervenciones_backend: int = 10,
        intervenciones_frontend: int = 30,
    ) -> None:
        self.repo_path = repo_path
        self.default_delta_t = default_delta_t_horas
        self.default_cambios = default_cambios
        self.modelo = modelo
        self.t_clean_backend = t_clean_backend
        self.t_clean_frontend = t_clean_frontend
        self.intervenciones_backend = intervenciones_backend
        self.intervenciones_frontend = intervenciones_frontend
        self._commits_por_archivo: Optional[Dict[str, int]] = None

    def _cargar_commits(self) -> None:
        if self._commits_por_archivo is not None:
            return
        self._commits_por_archivo = {}
        if not (self.repo_path / ".git").is_dir():
            return

        try:
            r = correr_comando(
                ["git", "log", "--name-only", "--format=", "--since=1 year ago", "HEAD"],
                cwd=self.repo_path,
            )
            lineas = [
                Path(line.strip()).as_posix()
                for line in r.stdout.splitlines()
                if line.strip()
            ]
            if not lineas:
                r_todo = correr_comando(
                    ["git", "log", "--name-only", "--format=", "HEAD"],
                    cwd=self.repo_path,
                )
                lineas = [
                    Path(line.strip()).as_posix()
                    for line in r_todo.stdout.splitlines()
                    if line.strip()
                ]
            self._commits_por_archivo = dict(collections.Counter(lineas))
        except Exception:
            self._commits_por_archivo = {}

    def get_friction(
        self, ruta_archivo: str, metrica: FileMetric, deuda_horas: float
    ) -> Optional[FrictionEstimate]:
        self._cargar_commits()
        if not self._commits_por_archivo:
            return None

        ruta_norm = Path(ruta_archivo).as_posix()
        c_git = self._commits_por_archivo.get(ruta_norm)
        if c_git is None:
            for gpath, gcount in self._commits_por_archivo.items():
                if gpath.endswith(ruta_norm) or ruta_norm.endswith(gpath):
                    c_git = gcount
                    break

        es_frontend = metrica.lenguaje.lower() in ("dart", "flutter")
        t_clean = self.t_clean_frontend if es_frontend else self.t_clean_backend

        if c_git is not None:
            cambios = c_git
        elif self.default_cambios is not None:
            cambios = self.default_cambios
        else:
            cambios = self.intervenciones_frontend if es_frontend else self.intervenciones_backend

        return FrictionEstimate(
            cambios_anuales=cambios,
            delta_t_horas=self.default_delta_t,
            t_clean_horas=t_clean if self.modelo == "dinamico" else None,
            fuente="git",
        )
