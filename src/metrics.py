"""
Modelo de datos de métricas crudas por archivo, y cálculo del Índice de
Mantenibilidad (MI) para Go a partir de LOC + complejidad ciclomática
(la fórmula clásica de Microsoft/Visual Studio, la misma que usaron a
mano en el documento de clase).

Para Dart no recalculamos MI a mano: dcm ya lo reporta directamente,
así que lo tomamos tal cual venga de la herramienta.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class MetricasArchivo:
    ruta: str
    lenguaje: str  # "go" | "dart"
    loc: int
    complejidad_ciclomatica: int  # si el archivo tiene varias funciones, es la SUMA
    complejidad_por_funcion: list[int] = field(default_factory=list)
    mi: float | None = None  # si ya viene calculado por la herramienta (dcm), se usa tal cual


def calcular_mi(loc: int, complejidad_ciclomatica: int) -> float:
    """
    MI = max(0, (171 - 25*ln(LOC) - 0.23*CC) / 171 * 100)

    Misma fórmula que se usó a mano en el documento de clase para los
    archivos .go. Si LOC es 0, devolvemos 100 (no hay nada que mantener).
    """
    if loc <= 0:
        return 100.0
    valor = (171 - 25 * math.log(loc) - 0.23 * complejidad_ciclomatica) / 171 * 100
    return max(0.0, valor)


def metrica_go_desde_raw(ruta: str, loc: int, complejidades_funciones: list[int]) -> MetricasArchivo:
    cc_total = sum(complejidades_funciones) if complejidades_funciones else 0
    mi = calcular_mi(loc, cc_total)
    return MetricasArchivo(
        ruta=ruta,
        lenguaje="go",
        loc=loc,
        complejidad_ciclomatica=cc_total,
        complejidad_por_funcion=complejidades_funciones,
        mi=mi,
    )


def metrica_dart_desde_dcm(ruta: str, loc: int, cc_total: int, mi_reportado: float) -> MetricasArchivo:
    return MetricasArchivo(
        ruta=ruta,
        lenguaje="dart",
        loc=loc,
        complejidad_ciclomatica=cc_total,
        mi=mi_reportado,
    )
