"""
Fórmulas matemáticas y de ingeniería financiera de deuda técnica.
Dominio puro: sin dependencias de I/O, subprocess ni archivos externos.
"""
from __future__ import annotations

import math
from typing import Optional

from src.domain.models import (
    DebtReport,
    FileMetric,
    FinancialParams,
)

DEFAULT_PARAMS = FinancialParams()


def calcular_mi(loc: int, complejidad_ciclomatica: int) -> float:
    """
    Índice de Mantenibilidad (fórmula clásica de Microsoft/Visual Studio):
    MI = max(0, (171 - 25*ln(LOC) - 0.23*CC) / 171 * 100)

    Si LOC es 0, devuelve 100 (no hay código que mantener).
    """
    if loc <= 0:
        return 100.0
    valor = (171 - 25 * math.log(loc) - 0.23 * complejidad_ciclomatica) / 171 * 100
    return max(0.0, valor)


def calcular_deuda_horas(
    mi: float, loc: int, mi_referencia: float, factor_k: float = DEFAULT_PARAMS.factor_correccion_k
) -> float:
    """Deuda = max(0, (MI_referencia - MI) * LOC * K)"""
    return max(0.0, (mi_referencia - mi) * loc * factor_k)


def calcular_costo_reparacion(
    deuda_horas: float, costo_hora_usd: float = DEFAULT_PARAMS.costo_hora_usd
) -> float:
    """Costo Reparación ($) = Deuda (horas) * Tarifa/hora ($)"""
    return deuda_horas * costo_hora_usd


def calcular_interes_anual(
    cambios_anuales: int, delta_t_horas: float, costo_hora_usd: float = DEFAULT_PARAMS.costo_hora_usd
) -> float:
    """Interés Anual ($) = Cambios * Δt * Tarifa/hora ($)"""
    return cambios_anuales * delta_t_horas * costo_hora_usd


def calcular_payback_anios(costo_reparacion: float, interes_anual: float) -> Optional[float]:
    """
    Período de Recuperación (Payback) = Costo / Interés Anual.
    Si el interés anual es 0, no hay recupero (o 0 si no hay costo).
    """
    if interes_anual <= 0:
        return 0.0 if costo_reparacion <= 0 else None
    return costo_reparacion / interes_anual


def calcular_roi_4_anios(
    costo_reparacion: float, interes_anual: float, anios: int = DEFAULT_PARAMS.anios_proyeccion
) -> Optional[float]:
    """ROI (%) = 100 * ((Interés Anual * Años) - Costo) / Costo"""
    if costo_reparacion <= 0:
        return 0.0
    return 100 * ((interes_anual * anios) - costo_reparacion) / costo_reparacion


def metrica_go_desde_raw(ruta: str, loc: int, complejidades_funciones: list[int]) -> FileMetric:
    """Construye un FileMetric para Go sumando complejidades y calculando MI."""
    cc_total = sum(complejidades_funciones) if complejidades_funciones else 0
    mi = calcular_mi(loc, cc_total)
    return FileMetric(
        ruta=ruta,
        lenguaje="go",
        loc=loc,
        complejidad_ciclomatica=cc_total,
        complejidad_por_funcion=complejidades_funciones,
        mi=mi,
    )


def metrica_dart_desde_dcm(ruta: str, loc: int, cc_total: int, mi_reportado: float) -> FileMetric:
    """Construye un FileMetric para Dart utilizando el MI reportado por dcm."""
    return FileMetric(
        ruta=ruta,
        lenguaje="dart",
        loc=loc,
        complejidad_ciclomatica=cc_total,
        mi=mi_reportado,
    )


def construir_reporte_archivo(
    metrica: FileMetric,
    mi_referencia: float,
    cambios_anuales: Optional[int],
    delta_t_horas: Optional[float],
    fuente_interes: str = "ninguna",
    params: Optional[FinancialParams] = None,
) -> DebtReport:
    """
    Construye el reporte técnico y financiero de un archivo evaluando
    sus umbrales de mantenibilidad y aplicando las fórmulas de deuda.
    """
    p = params or DEFAULT_PARAMS
    mi = metrica.mi if metrica.mi is not None else calcular_mi(metrica.loc, metrica.complejidad_ciclomatica)
    deuda = calcular_deuda_horas(mi, metrica.loc, mi_referencia, factor_k=p.factor_correccion_k)
    costo = calcular_costo_reparacion(deuda, costo_hora_usd=p.costo_hora_usd)

    mi_redondeado = round(mi, 2)
    if mi_redondeado < p.mi_umbral_critico:
        estado = "CRITICO"
    elif mi_redondeado < p.mi_umbral_excelente:
        estado = "APROBADO"
    else:
        estado = "EXCELENTE"

    reporte = DebtReport(
        ruta=metrica.ruta,
        lenguaje=metrica.lenguaje,
        loc=metrica.loc,
        complejidad_ciclomatica=metrica.complejidad_ciclomatica,
        mi=mi_redondeado,
        estado_mi=estado,
        deuda_horas=round(deuda, 2),
        costo_reparacion_usd=round(costo, 2),
    )

    # Si el archivo no tiene deuda técnica y no proviene de configuración explícita, no sufre fricción
    if deuda <= 0.0 and fuente_interes not in ("yaml", "ninguna"):
        reporte.interes_anual_usd = 0.0
        reporte.payback_anios = 0.0
        reporte.roi_4_anios_porc = 0.0
        reporte.tiene_datos_interes = True
        reporte.fuente_interes = "sin_deuda"
    elif cambios_anuales is not None and delta_t_horas is not None:
        interes = calcular_interes_anual(cambios_anuales, delta_t_horas, costo_hora_usd=p.costo_hora_usd)
        payback = calcular_payback_anios(costo, interes)
        roi = calcular_roi_4_anios(costo, interes, anios=p.anios_proyeccion)

        reporte.interes_anual_usd = round(interes, 2)
        reporte.payback_anios = round(payback, 2) if payback is not None else None
        reporte.roi_4_anios_porc = round(roi, 2) if roi is not None else None
        reporte.tiene_datos_interes = True
        reporte.fuente_interes = fuente_interes

    return reporte
