"""
Analizador de código Dart / Flutter usando dart_code_metrics (dcm) y gocloc.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.domain.calculator import calcular_mi, metrica_dart_desde_dcm
from src.domain.models import FileMetric
from src.infrastructure.analyzers.base import BaseAnalyzer
from src.infrastructure.tools.process_runner import (
    HerramientaFaltanteError,
    asegurar_dcm,
    asegurar_gocloc,
    correr_comando,
    obtener_binario_dcm,
)


class DartAnalyzer(BaseAnalyzer):
    """Analiza archivos de código fuente Dart (.dart)."""

    name: str = "dart"
    supported_extensions: set[str] = {".dart"}

    def analyze(self, repo_path: Path, subpath: str = "lib") -> list[FileMetric]:
        asegurar_dcm()
        asegurar_gocloc()

        sub = subpath or "lib"

        # 1. Obtener LOC por archivo Dart usando gocloc
        loc_data = self._correr_gocloc(repo_path, sub)
        loc_por_archivo: dict[str, int] = {}
        for f in loc_data.get("files", []):
            nombre = f.get("name") or f.get("filename") or ""
            if nombre.endswith(".dart"):
                ruta_norm = Path(nombre).as_posix()
                loc_por_archivo[ruta_norm] = f.get("code", 0)

        # 2. Obtener métricas y complejidad ciclomática usando dcm
        data = self._correr_dcm(repo_path, sub)

        metricas: list[FileMetric] = []
        for record in data.get("records", []):
            ruta_raw = (
                record.get("path")
                or record.get("file-path")
                or record.get("filePath")
                or ""
            )
            if not ruta_raw:
                continue
            ruta_norm = Path(ruta_raw).as_posix()

            # Sumar complejidad ciclomática de todas las funciones/métodos
            complejidades_funciones: list[int] = []
            for fname, fval in record.get("functions", {}).items():
                for m in fval.get("metrics", []):
                    if m.get("metricsId") == "cyclomatic-complexity":
                        complejidades_funciones.append(int(m.get("value", 0)))

            cc_total = sum(complejidades_funciones)

            # LOC de gocloc
            loc = loc_por_archivo.get(ruta_norm)
            if loc is None:
                for fpath, fcode in loc_por_archivo.items():
                    if fpath.endswith(ruta_norm) or ruta_norm.endswith(fpath):
                        loc = fcode
                        break
            if loc is None:
                loc = 0

            mi = calcular_mi(loc, cc_total)
            metricas.append(
                metrica_dart_desde_dcm(
                    ruta=ruta_norm,
                    loc=loc,
                    cc_total=cc_total,
                    mi_reportado=round(mi, 2),
                )
            )
        return metricas

    def _correr_gocloc(self, repo_path: Path, subpath: str) -> dict:
        r = correr_comando(["gocloc", "--by-file", "--output-type=json", subpath], cwd=repo_path)
        if r.returncode != 0:
            raise RuntimeError(f"gocloc falló: {r.stderr}")
        return json.loads(r.stdout)

    def _correr_dcm(self, repo_path: Path, subpath: str) -> dict:
        binario = obtener_binario_dcm()
        if not binario:
            raise HerramientaFaltanteError("No se encontró el binario 'dcm' ni 'metrics'.")
        r = correr_comando(
            [binario, "analyze", subpath, "--reporter=json"],
            cwd=repo_path,
        )
        stdout = r.stdout.strip()
        if not stdout:
            raise RuntimeError(f"dcm/metrics no devolvió salida. stderr: {r.stderr}")
        json_start = stdout.find("{")
        if json_start == -1:
            raise RuntimeError(f"dcm/metrics no devolvió un JSON válido. stdout: {stdout}")
        return json.loads(stdout[json_start:])
