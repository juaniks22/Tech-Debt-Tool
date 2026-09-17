"""
Proveedor de estimaciones de fricción a partir de configuración YAML.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import yaml

from src.domain.models import FileMetric, FrictionEstimate


class YamlFrictionProvider:
    """Carga y consulta estimaciones manuales definidas por el equipo en un archivo YAML."""

    def __init__(self, yaml_path: Path) -> None:
        self.yaml_path = yaml_path
        self._intereses: Dict[str, tuple[int, float]] = {}
        self._cargar()

    def _cargar(self) -> None:
        if not self.yaml_path.exists():
            return
        try:
            with open(self.yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            for item in data.get("archivos", []):
                ruta = Path(item.get("ruta", "")).as_posix()
                cambios = item.get("cambios_anuales")
                delta_t = item.get("delta_t_horas")
                if ruta and cambios is not None and delta_t is not None:
                    self._intereses[ruta] = (int(cambios), float(delta_t))
        except Exception:
            pass

    def get_friction(
        self, ruta_archivo: str, metrica: FileMetric, deuda_horas: float
    ) -> Optional[FrictionEstimate]:
        ruta_norm = Path(ruta_archivo).as_posix()
        datos = self._intereses.get(ruta_norm)
        if datos is None:
            for ypath, yval in self._intereses.items():
                if ruta_norm.endswith(ypath) or ypath.endswith(ruta_norm):
                    datos = yval
                    break

        if datos is not None:
            cambios, delta_t = datos
            return FrictionEstimate(
                cambios_anuales=cambios,
                delta_t_horas=delta_t,
                fuente="yaml",
            )
        return None
