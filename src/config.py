"""
Configuración global de la herramienta de deuda técnica.

Los valores de "cambios_anuales" y "delta_t_horas" NO se pueden calcular
por análisis estático de código: son estimaciones humanas del equipo
(cuántas veces al año se toca un archivo, y cuánto tiempo extra tarda
cada cambio por la mala calidad del código). Van en un YAML aparte.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

# --- Constantes y parámetros del modelo dinámico de fricción (nuevo estándar) ---
MODELO_DEFAULT = "dinamico"
FACTOR_C_DEFAULT = 3.0
MI_UMBRAL_DINAMICO = 75.0
MI_UMBRAL_AMARILLO_DINAMICO = 50.0
TASA_EXITO_ROI_DEFAULT = 0.65
T_CLEAN_BACKEND_DEFAULT = 7.0
T_CLEAN_FRONTEND_DEFAULT = 4.0
INTERVENCIONES_BACKEND_DEFAULT = 10
INTERVENCIONES_FRONTEND_DEFAULT = 30
EF_EXPERIENCIA_DEFAULT = 0.0
TCF_DEFAULT = 1.0

# --- Constantes y parámetros globales clásicos (retrocompatibilidad) ---
FACTOR_CORRECCION_K = 0.01
COSTO_HORA_DESARROLLO_USD = 30.0

# MI de referencia para el cálculo clásico de deuda técnica.
MI_REFERENCIA_DEFAULT = 75.0
MI_REFERENCIA_CLASICA = 20.0

# Umbrales clásicos de Maintainability Index (MI)
MI_UMBRAL_CRITICO = 20.0    # < 20: Crítico / No aprobado (Rojo)
MI_UMBRAL_EXCELENTE = 60.0  # >= 60: Excelente (Verde oscuro). Entre 20 y 59: Aprobado (Verde claro)

# Umbrales de complejidad ciclomática dados en clase, por lenguaje.
CC_UMBRAL_POR_LENGUAJE = {
    "dart": 4,
    "go": 10,
}

# Umbral de deuda técnica relativa dado en clase (informativo)
DEUDA_TECNICA_UMBRAL_PORC = 6.0

# Estimaciones por defecto para archivos sin configuración explícita en intereses.yaml
DEFAULT_CAMBIOS_ANUALES = 10
DEFAULT_DELTA_T_HORAS = 2.0


@dataclass
class InteresArchivo:
    """Estimación humana de fricción anual para un archivo puntual."""
    ruta: str
    cambios_anuales: int
    delta_t_horas: Optional[float] = None
    t_clean_horas: Optional[float] = None


def cargar_intereses(path_yaml: Path) -> dict[str, InteresArchivo]:
    """
    Carga el YAML de intereses por archivo.

    Formato esperado:

        archivos:
          - ruta: "internal/repository/academic_repo.go"
            cambios_anuales: 14
            delta_t_horas: 2.5
          - ruta: "lib/screens/cursos_screen.dart"
            cambios_anuales: 24
            delta_t_horas: 5.0

    Si un archivo analizado no aparece en este YAML, se reporta igual
    con las métricas crudas (LOC/CC/MI) pero sin deuda/costo/ROI,
    dejando claro que falta el dato humano.
    """
    if not path_yaml.exists():
        print(
            f"[config] No encontré '{path_yaml}'. Generá uno con "
            f"'--init-config' o cargalo a mano. Sigo sin datos de interés.",
            file=sys.stderr,
        )
        return {}

    with open(path_yaml, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    resultado: dict[str, InteresArchivo] = {}
    for entry in data.get("archivos", []):
        try:
            ruta_norm = Path(entry["ruta"]).as_posix()
            delta_t_raw = entry.get("delta_t_horas")
            delta_t = float(delta_t_raw) if delta_t_raw is not None else None
            t_clean_raw = entry.get("t_clean_horas")
            t_clean = float(t_clean_raw) if t_clean_raw is not None else None
            item = InteresArchivo(
                ruta=ruta_norm,
                cambios_anuales=int(entry["cambios_anuales"]),
                delta_t_horas=delta_t,
                t_clean_horas=t_clean,
            )
            resultado[item.ruta] = item
        except (KeyError, ValueError, TypeError) as e:
            print(f"[config] Entrada inválida en {path_yaml}: {entry} ({e})", file=sys.stderr)
    return resultado


def generar_config_ejemplo(path_yaml: Path) -> None:
    """Escribe un YAML de ejemplo para que el usuario lo complete."""
    contenido = """\
# Estimaciones humanas de fricción anual por archivo.
# Estos NO salen de analizar el código - son juicio del equipo:
#
#   cambios_anuales: cuántas veces al año se toca este archivo
#                     (features, bugfixes, refactors)
#   delta_t_horas:   cuánto tiempo EXTRA tarda cada cambio por la mala
#                     calidad del código, vs. si estuviera limpio
#                     (Tiempo Real - Eficiencia Ideal)
#
# Completá la ruta tal como la reporta gocloc/dcm (relativa a la raíz
# del repo).

archivos:
  - ruta: "path/al/archivo.go"
    cambios_anuales: 10
    delta_t_horas: 2.0
"""
    path_yaml.write_text(contenido, encoding="utf-8")
    print(f"[config] Generé plantilla en {path_yaml}. Completala con los datos reales del equipo.")
