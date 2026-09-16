"""
Verificación, instalación y ejecución de las herramientas externas
estándar de la industria que hacen el trabajo pesado de análisis estático:

- gocloc   -> LOC para Go (y otros lenguajes, pero acá lo usamos para Go)
- gocyclo  -> Complejidad ciclomática para Go
- dcm      -> dart_code_metrics: LOC + complejidad ciclomática para Dart

No reinventamos parsers de AST: son las herramientas que se usan en
pipelines de CI reales.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


class HerramientaFaltanteError(RuntimeError):
    pass


def _correr(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", **kwargs)


def _tiene_binario(nombre: str) -> bool:
    return shutil.which(nombre) is not None


def asegurar_gocloc() -> None:
    if _tiene_binario("gocloc"):
        return
    print("[setup] 'gocloc' no encontrado. Instalando con 'go install'...", file=sys.stderr)
    if not _tiene_binario("go"):
        raise HerramientaFaltanteError(
            "Necesito el toolchain de Go instalado (https://go.dev/dl/) para "
            "instalar gocloc automáticamente."
        )
    r = _correr(["go", "install", "github.com/hhatto/gocloc/cmd/gocloc@latest"])
    if r.returncode != 0:
        raise HerramientaFaltanteError(f"Falló instalación de gocloc:\n{r.stderr}")
    if not _tiene_binario("gocloc"):
        raise HerramientaFaltanteError(
            "gocloc se instaló pero no está en PATH. Agregá $(go env GOPATH)/bin a tu PATH."
        )


def asegurar_gocyclo() -> None:
    if _tiene_binario("gocyclo"):
        return
    print("[setup] 'gocyclo' no encontrado. Instalando con 'go install'...", file=sys.stderr)
    if not _tiene_binario("go"):
        raise HerramientaFaltanteError(
            "Necesito el toolchain de Go instalado (https://go.dev/dl/) para "
            "instalar gocyclo automáticamente."
        )
    r = _correr(["go", "install", "github.com/fzipp/gocyclo/cmd/gocyclo@latest"])
    if r.returncode != 0:
        raise HerramientaFaltanteError(f"Falló instalación de gocyclo:\n{r.stderr}")
    if not _tiene_binario("gocyclo"):
        raise HerramientaFaltanteError(
            "gocyclo se instaló pero no está en PATH. Agregá $(go env GOPATH)/bin a tu PATH."
        )


def _obtener_binario_dcm() -> str | None:
    return shutil.which("dcm") or shutil.which("metrics")


def asegurar_dcm() -> None:
    if _obtener_binario_dcm():
        return
    print("[setup] 'dcm'/'metrics' (dart_code_metrics) no encontrado. Instalando con 'dart pub global'...", file=sys.stderr)
    if not _tiene_binario("dart"):
        raise HerramientaFaltanteError(
            "Necesito el SDK de Dart instalado (https://dart.dev/get-dart) para "
            "instalar dcm automáticamente."
        )
    r = _correr(["dart", "pub", "global", "activate", "dart_code_metrics"])
    if r.returncode != 0:
        raise HerramientaFaltanteError(f"Falló instalación de dcm:\n{r.stderr}")
    if not _obtener_binario_dcm():
        raise HerramientaFaltanteError(
            "dcm/metrics se instaló pero no está en PATH. Agregá el pub cache bin al PATH "
            "(ver: dart pub global activate --help)."
        )


def correr_gocloc(repo_path: Path, subpath: str = ".") -> dict:
    """Devuelve el LOC por archivo, vía JSON de gocloc con --by-file."""
    r = _correr(["gocloc", "--by-file", "--output-type=json", subpath], cwd=str(repo_path))
    if r.returncode != 0:
        raise RuntimeError(f"gocloc falló: {r.stderr}")
    return json.loads(r.stdout)


def correr_gocyclo(repo_path: Path, subpath: str = ".") -> list[dict]:
    """
    Devuelve complejidad ciclomática por función, vía gocyclo -avg -json
    (si tu versión no soporta -json, cae a texto parseado manualmente).
    """
    r = _correr(["gocyclo", "-avg", subpath], cwd=str(repo_path))
    if r.returncode not in (0, 1):  # gocyclo devuelve 1 si hay funciones sobre el umbral
        raise RuntimeError(f"gocyclo falló: {r.stderr}")
    return _parsear_texto_gocyclo(r.stdout)


def _parsear_texto_gocyclo(output: str) -> list[dict]:
    """
    Formato de línea típico de gocyclo:
        <complejidad> <paquete> <función> <archivo>:<línea>:<columna>
    Ejemplo:
        12 main (*Server).Handle server.go:42:1
    """
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


def correr_dcm(repo_path: Path, subpath: str = "lib") -> dict:
    """
    Devuelve métricas de dart_code_metrics en JSON.
    """
    binario = _obtener_binario_dcm()
    if not binario:
        raise HerramientaFaltanteError("No se encontró el binario 'dcm' ni 'metrics'.")
    r = _correr(
        [binario, "analyze", subpath, "--reporter=json"],
        cwd=str(repo_path),
    )
    # dcm devuelve !=0 si encuentra issues; no es un error de ejecución
    stdout = r.stdout.strip()
    if not stdout:
        raise RuntimeError(f"dcm/metrics no devolvió salida. stderr: {r.stderr}")
    json_start = stdout.find("{")
    if json_start == -1:
        raise RuntimeError(f"dcm/metrics no devolvió un JSON válido. stdout: {stdout}")
    return json.loads(stdout[json_start:])
