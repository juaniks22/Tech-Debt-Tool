"""
Analizador de código Go usando gocloc (LOC) y gocyclo (Complejidad ciclomática).
"""
from __future__ import annotations

import json
from pathlib import Path

from src.domain.calculator import metrica_go_desde_raw
from src.domain.models import FileMetric
from src.infrastructure.analyzers.base import BaseAnalyzer
from src.infrastructure.tools.process_runner import (
    asegurar_gocloc,
    asegurar_gocyclo,
    correr_comando,
)


class GoAnalyzer(BaseAnalyzer):
    """Analiza archivos de código fuente Go (.go)."""

    name: str = "go"
    supported_extensions: set[str] = {".go"}

    def analyze(self, repo_path: Path, subpath: str = ".") -> list[FileMetric]:
        asegurar_gocloc()
        asegurar_gocyclo()

        sub = subpath or "."
        loc_data = self._correr_gocloc(repo_path, sub)
        cc_data = self._correr_gocyclo(repo_path, sub)

        loc_por_archivo: dict[str, int] = {}
        for f in loc_data.get("files", []):
            nombre = f.get("name") or f.get("filename") or ""
            if nombre.endswith(".go"):
                ruta_norm = Path(nombre).as_posix()
                loc_por_archivo[ruta_norm] = f.get("code", 0)

        cc_por_archivo: dict[str, list[int]] = {}
        for item in cc_data:
            ruta_norm = Path(item["archivo"]).as_posix()
            cc_por_archivo.setdefault(ruta_norm, []).append(item["complejidad"])

        metricas: list[FileMetric] = []
        for archivo, loc in loc_por_archivo.items():
            complejidades = cc_por_archivo.get(archivo, [])
            metricas.append(metrica_go_desde_raw(archivo, loc, complejidades))
        return metricas

    def _correr_gocloc(self, repo_path: Path, subpath: str) -> dict:
        r = correr_comando(["gocloc", "--by-file", "--output-type=json", subpath], cwd=repo_path)
        if r.returncode != 0:
            raise RuntimeError(f"gocloc falló: {r.stderr}")
        return json.loads(r.stdout)

    def _correr_gocyclo(self, repo_path: Path, subpath: str) -> list[dict]:
        r = correr_comando(["gocyclo", "-avg", subpath], cwd=repo_path)
        if r.returncode not in (0, 1):  # gocyclo devuelve 1 si hay funciones sobre el umbral
            raise RuntimeError(f"gocyclo falló: {r.stderr}")
        return self._parsear_texto_gocyclo(r.stdout)

    @staticmethod
    def _parsear_texto_gocyclo(output: str) -> list[dict]:
        resultados = []
        for linea in output.strip().splitlines():
            if not linea.strip() or linea.startswith("Average:"):
                continue
            partes = linea.split()
            if len(partes) < 4:
                continue
            try:
                complejidad = int(partes[0])
            except ValueError:
                continue
            ubicacion = partes[-1]
            archivo = ubicacion.rsplit(":", 2)[0]
            resultados.append({"complejidad": complejidad, "archivo": archivo, "raw": linea})
        return resultados
