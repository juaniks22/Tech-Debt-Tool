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

# --- Constantes y parámetros globales (del documento de clase) ---
FACTOR_CORRECCION_K = 0.01
COSTO_HORA_DESARROLLO_USD = 30.0

# MI de referencia para el cálculo de deuda técnica.
# Es un parámetro, no un valor fijo escondido en la fórmula: la clase dio
# "MI >= 60% aceptable" y por separado el ejemplo usa 20 como referencia.
# Cuál usar (y si debería variar por lenguaje) quedó como pregunta abierta
# de Juani -> lo dejamos configurable, con 20 de default para no romper
# el ejemplo que ya validaron a mano.
MI_REFERENCIA_DEFAULT = 20.0

# Umbrales de complejidad ciclomática dados en clase, por lenguaje.
# El script NO los usa para alterar el cálculo de deuda (eso se dejó
# explícitamente sin decidir) - solo se muestran en el reporte para
# que la interpretación quede en manos del usuario.
CC_UMBRAL_POR_LENGUAJE = {
    "dart": 4,
    "go": 10,
}

# Umbral de MI dado en clase (informativo, ver mismo comentario que arriba)
MI_UMBRAL_ACEPTABLE = 60.0

# Umbral de deuda técnica relativa dado en clase (informativo)
DEUDA_TECNICA_UMBRAL_PORC = 6.0


@dataclass
class InteresArchivo:
    """Estimación humana de fricción anual para un archivo puntual."""
    ruta: str
    cambios_anuales: int
    delta_t_horas: float


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
            item = InteresArchivo(
                ruta=entry["ruta"],
                cambios_anuales=int(entry["cambios_anuales"]),
                delta_t_horas=float(entry["delta_t_horas"]),
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
