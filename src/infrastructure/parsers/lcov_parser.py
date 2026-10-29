"""
Parser de reportes de cobertura LCOV (coverage/lcov.info).
Extrae líneas ejecutables (LF) y líneas cubiertas (LH) por archivo,
calculando el porcentaje de cobertura real (LH / LF * 100).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional


def parse_lcov_file(lcov_path: Path, repo_path: Optional[Path] = None) -> dict[str, float]:
    """
    Parsea un archivo lcov.info y devuelve un diccionario con:
    ruta_normalizada -> porcentaje_cobertura (0.0 a 100.0).
    """
    if not lcov_path.is_file():
        return {}

    try:
        content = lcov_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}

    cobertura_por_archivo: dict[str, float] = {}
    current_sf: Optional[str] = None
    lf: int = 0
    lh: int = 0

    for line in content.splitlines():
        line = line.strip()
        if line.startswith("SF:"):
            current_sf = line[3:].strip()
            lf = 0
            lh = 0
        elif line.startswith("LF:"):
            try:
                lf = int(line[3:].strip())
            except ValueError:
                lf = 0
        elif line.startswith("LH:"):
            try:
                lh = int(line[3:].strip())
            except ValueError:
                lh = 0
        elif line == "end_of_record":
            if current_sf is not None:
                sf_path = Path(current_sf)
                if repo_path and sf_path.is_absolute():
                    try:
                        rel = sf_path.relative_to(repo_path).as_posix()
                    except ValueError:
                        rel = sf_path.as_posix()
                else:
                    rel = sf_path.as_posix()

                porc = (lh / lf * 100.0) if lf > 0 else 100.0
                cobertura_por_archivo[rel] = round(porc, 2)
            current_sf = None
            lf = 0
            lh = 0

    return cobertura_por_archivo


def obtener_cobertura_para_archivo(
    ruta_archivo: str,
    cobertura_map: dict[str, float],
) -> Optional[float]:
    """
    Busca la cobertura de un archivo en el mapa LCOV, tolerando diferencias
    de separadores de ruta (\\ vs /) o prefijos relativos/absolutos.
    """
    ruta_norm = ruta_archivo.replace("\\", "/").strip("/")
    if ruta_norm in cobertura_map:
        return cobertura_map[ruta_norm]

    ruta_lower = ruta_norm.lower()
    for k, v in cobertura_map.items():
        if k.lower() == ruta_lower:
            return v

    for k, v in cobertura_map.items():
        k_norm = k.replace("\\", "/").strip("/")
        if ruta_norm.endswith(k_norm) or k_norm.endswith(ruta_norm):
            return v

    return None

