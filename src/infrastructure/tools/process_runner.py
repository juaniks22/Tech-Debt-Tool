"""
Ejecución de procesos externos y gestión de binarios en el PATH.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


class HerramientaFaltanteError(RuntimeError):
    """Lanzada cuando una herramienta externa necesaria no está disponible."""
    pass


def tiene_binario(nombre: str) -> bool:
    """Comprueba si un ejecutable se encuentra en el PATH del sistema."""
    return shutil.which(nombre) is not None


def correr_comando(cmd: list[str], cwd: Optional[Path | str] = None, **kwargs) -> subprocess.CompletedProcess:
    """Ejecuta un comando en un subproceso con codificación UTF-8 segura."""
    cwd_str = str(cwd) if cwd is not None else None
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd_str,
        **kwargs,
    )


def asegurar_gocloc() -> None:
    if tiene_binario("gocloc"):
        return
    print("[setup] 'gocloc' no encontrado. Instalando con 'go install'...", file=sys.stderr)
    if not tiene_binario("go"):
        raise HerramientaFaltanteError(
            "Necesito el toolchain de Go instalado (https://go.dev/dl/) para instalar gocloc automáticamente."
        )
    r = correr_comando(["go", "install", "github.com/hhatto/gocloc/cmd/gocloc@latest"])
    if r.returncode != 0:
        raise HerramientaFaltanteError(f"Falló instalación de gocloc:\n{r.stderr}")
    if not tiene_binario("gocloc"):
        raise HerramientaFaltanteError(
            "gocloc se instaló pero no está en PATH. Agregá $(go env GOPATH)/bin a tu PATH."
        )


def asegurar_gocyclo() -> None:
    if tiene_binario("gocyclo"):
        return
    print("[setup] 'gocyclo' no encontrado. Instalando con 'go install'...", file=sys.stderr)
    if not tiene_binario("go"):
        raise HerramientaFaltanteError(
            "Necesito el toolchain de Go instalado (https://go.dev/dl/) para instalar gocyclo automáticamente."
        )
    r = correr_comando(["go", "install", "github.com/fzipp/gocyclo/cmd/gocyclo@latest"])
    if r.returncode != 0:
        raise HerramientaFaltanteError(f"Falló instalación de gocyclo:\n{r.stderr}")
    if not tiene_binario("gocyclo"):
        raise HerramientaFaltanteError(
            "gocyclo se instaló pero no está en PATH. Agregá $(go env GOPATH)/bin a tu PATH."
        )


def obtener_binario_dcm() -> Optional[str]:
    return shutil.which("dcm") or shutil.which("metrics")


def asegurar_dcm() -> None:
    if obtener_binario_dcm():
        return
    print(
        "[setup] 'dcm'/'metrics' (dart_code_metrics) no encontrado. Instalando con 'dart pub global'...",
        file=sys.stderr,
    )
    if not tiene_binario("dart"):
        raise HerramientaFaltanteError(
            "Necesito el SDK de Dart instalado (https://dart.dev/get-dart) para instalar dcm automáticamente."
        )
    r = correr_comando(["dart", "pub", "global", "activate", "dart_code_metrics"])
    if r.returncode != 0:
        raise HerramientaFaltanteError(f"Falló instalación de dcm:\n{r.stderr}")
    if not obtener_binario_dcm():
        raise HerramientaFaltanteError(
            "dcm/metrics se instaló pero no está en PATH. Agregá el pub cache bin al PATH (ver: dart pub global activate --help)."
        )
