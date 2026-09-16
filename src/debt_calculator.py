"""
Fórmulas financieras de deuda técnica, replicando exactamente el cálculo
manual validado en clase para course_handler.go / academic_repo.go /
cursos_screen.dart.
"""
from __future__ import annotations

from dataclasses import dataclass

from config import (
    COSTO_HORA_DESARROLLO_USD,
    FACTOR_CORRECCION_K,
    MI_UMBRAL_CRITICO,
    MI_UMBRAL_EXCELENTE,
)
from metrics import MetricasArchivo


@dataclass
class ReporteFinancieroArchivo:
    ruta: str
    lenguaje: str
    loc: int
    complejidad_ciclomatica: int
    mi: float
    estado_mi: str = "CRITICO"  # "CRITICO" (<20), "APROBADO" (20..59), "EXCELENTE" (>=60)
    deuda_horas: float | None = None
    costo_reparacion_usd: float | None = None
    interes_anual_usd: float | None = None
    payback_anios: float | None = None
    roi_4_anios_porc: float | None = None
    tiene_datos_interes: bool = False


def calcular_deuda_horas(mi: float, loc: int, mi_referencia: float) -> float:
    """Deuda = max(0, (MI_referencia - MI) * LOC * K)"""
    return max(0.0, (mi_referencia - mi) * loc * FACTOR_CORRECCION_K)


def calcular_costo_reparacion(deuda_horas: float) -> float:
    return deuda_horas * COSTO_HORA_DESARROLLO_USD


def calcular_interes_anual(cambios_anuales: int, delta_t_horas: float) -> float:
    return cambios_anuales * delta_t_horas * COSTO_HORA_DESARROLLO_USD


def calcular_payback_anios(costo_reparacion: float, interes_anual: float) -> float | None:
    if interes_anual <= 0:
        return None  # sin fricción anual, no hay payback definido
    return costo_reparacion / interes_anual


def calcular_roi_4_anios(costo_reparacion: float, interes_anual: float) -> float | None:
    if costo_reparacion <= 0:
        return None
    return 100 * ((interes_anual * 4) - costo_reparacion) / costo_reparacion


def construir_reporte_archivo(
    metrica: MetricasArchivo,
    mi_referencia: float,
    cambios_anuales: int | None,
    delta_t_horas: float | None,
) -> ReporteFinancieroArchivo:
    deuda = calcular_deuda_horas(metrica.mi, metrica.loc, mi_referencia)
    costo = calcular_costo_reparacion(deuda)

    mi_redondeado = round(metrica.mi, 2)
    if mi_redondeado < MI_UMBRAL_CRITICO:
        estado = "CRITICO"
    elif mi_redondeado < MI_UMBRAL_EXCELENTE:
        estado = "APROBADO"
    else:
        estado = "EXCELENTE"

    reporte = ReporteFinancieroArchivo(
        ruta=metrica.ruta,
        lenguaje=metrica.lenguaje,
        loc=metrica.loc,
        complejidad_ciclomatica=metrica.complejidad_ciclomatica,
        mi=mi_redondeado,
        estado_mi=estado,
        deuda_horas=round(deuda, 2),
        costo_reparacion_usd=round(costo, 2),
    )

    if cambios_anuales is not None and delta_t_horas is not None:
        interes = calcular_interes_anual(cambios_anuales, delta_t_horas)
        payback = calcular_payback_anios(costo, interes)
        roi = calcular_roi_4_anios(costo, interes)
        reporte.interes_anual_usd = round(interes, 2)
        reporte.payback_anios = round(payback, 2) if payback is not None else None
        reporte.roi_4_anios_porc = round(roi, 2) if roi is not None else None
        reporte.tiene_datos_interes = True

    return reporte
