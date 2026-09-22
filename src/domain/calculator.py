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


def calcular_k_dinamico(ef: float = 0.0, tcf: float = 1.0) -> float:
    """
    Factor de Velocidad Base K dinámico:
    K_dinamico = [0.01 - (EF / 5.0) * 0.0067] * TCF

    - EF = 0.0 (equipo inexperto, 6 min/línea): K = 0.01
    - EF = 5.0 (equipo de alto rendimiento, 2 min/línea): K = 0.0033
    """
    ef_clamped = max(0.0, min(5.0, ef))
    k_base = 0.01 - (ef_clamped / 5.0) * 0.0067
    return max(0.0, k_base * tcf)


def calcular_factor_friccion(mi: float, mi_umbral: float = 75.0, c: float = 3.0) -> float:
    """
    Modelo de Fricción Operativa F(MI):
    F(MI) = 1 + ((MI_umbral - MI) / MI_umbral)^2 * C
    Si MI >= MI_umbral, se anula la brecha y F(MI) = 1.0.
    """
    if mi_umbral <= 0:
        return 1.0
    if mi >= mi_umbral:
        return 1.0
    brecha = (mi_umbral - mi) / mi_umbral
    return 1.0 + (brecha ** 2) * c


def calcular_friccion_operativa(
    mi: float, t_clean: float, mi_umbral: float = 75.0, c: float = 3.0
) -> tuple[float, float, float]:
    """
    Calcula (F(MI), T_real, Delta_t_horas):
    T_real = T_clean * F(MI)
    Delta_t = T_real - T_clean
    """
    f = calcular_factor_friccion(mi, mi_umbral=mi_umbral, c=c)
    t_real = t_clean * f
    delta_t = max(0.0, t_real - t_clean)
    return (f, t_real, delta_t)


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
    """ROI Nominal (%) = 100 * ((Interés Anual * Años) - Costo) / Costo"""
    if costo_reparacion <= 0:
        return 0.0
    return 100 * ((interes_anual * anios) - costo_reparacion) / costo_reparacion


def calcular_roi_ajustado_riesgo(
    costo_reparacion: float,
    interes_anual: float,
    anios: int = DEFAULT_PARAMS.anios_proyeccion,
    tasa_exito: float = DEFAULT_PARAMS.tasa_exito_roi,
) -> Optional[float]:
    """
    ROI Ajustado por Riesgo (%) = 100 * ((Interés Anual * Años * Tasa_Éxito) - Costo) / Costo
    Aplica la probabilidad empírica de éxito de refactorización incremental (default 65%).
    """
    if costo_reparacion <= 0:
        return 0.0
    beneficio_esperado = (interes_anual * anios) * tasa_exito
    return 100 * (beneficio_esperado - costo_reparacion) / costo_reparacion


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
    t_clean_horas: Optional[float] = None,
) -> DebtReport:
    """
    Construye el reporte técnico y financiero de un archivo evaluando
    sus umbrales de mantenibilidad y aplicando las fórmulas de deuda
    (dinámica o clásica según params.modelo).
    """
    p = params
    if p is None:
        if mi_referencia <= 20.0:
            p = FinancialParams.clasico(mi_referencia_default=mi_referencia)
        else:
            p = DEFAULT_PARAMS

    mi = metrica.mi if metrica.mi is not None else calcular_mi(metrica.loc, metrica.complejidad_ciclomatica)

    # Selección de factor K
    if p.modelo == "dinamico":
        factor_k = calcular_k_dinamico(ef=p.ef_experiencia, tcf=p.tcf)
    else:
        factor_k = p.factor_correccion_k

    deuda = calcular_deuda_horas(mi, metrica.loc, mi_referencia, factor_k=factor_k)
    costo = calcular_costo_reparacion(deuda, costo_hora_usd=p.costo_hora_usd)

    mi_redondeado = round(mi, 2)
    if mi_redondeado < p.mi_umbral_critico:
        estado = "CRITICO"
    elif mi_redondeado < p.mi_umbral_excelente:
        estado = "APROBADO"
    else:
        estado = "EXCELENTE"

    # Resolución de F(MI), T_clean, T_real y Delta_t
    factor_friccion: Optional[float] = None
    t_clean: Optional[float] = None
    t_real: Optional[float] = None
    delta_t_resuelto: Optional[float] = delta_t_horas

    if p.modelo == "dinamico":
        if t_clean_horas is not None:
            t_clean = t_clean_horas
        elif metrica.lenguaje.lower() in ("dart", "flutter"):
            t_clean = p.t_clean_frontend
        else:
            t_clean = p.t_clean_backend

        if deuda <= 0.0 and fuente_interes not in ("yaml", "ninguna"):
            factor_friccion = 1.0
            t_real = t_clean
            delta_t_resuelto = 0.0
        else:
            f_calc, t_real_calc, dt_calc = calcular_friccion_operativa(
                mi, t_clean=t_clean, mi_umbral=mi_referencia, c=p.factor_c
            )
            factor_friccion = round(f_calc, 2)
            if delta_t_horas is not None:
                # Override manual / yaml
                delta_t_resuelto = delta_t_horas
                t_real = round(t_clean + delta_t_resuelto, 2)
            else:
                delta_t_resuelto = round(dt_calc, 2)
                t_real = round(t_real_calc, 2)

    reporte = DebtReport(
        ruta=metrica.ruta,
        lenguaje=metrica.lenguaje,
        loc=metrica.loc,
        complejidad_ciclomatica=metrica.complejidad_ciclomatica,
        mi=mi_redondeado,
        estado_mi=estado,
        deuda_horas=round(deuda, 2),
        costo_reparacion_usd=round(costo, 2),
        factor_friccion=factor_friccion,
        t_clean_horas=round(t_clean, 2) if t_clean is not None else None,
        t_real_horas=round(t_real, 2) if t_real is not None else None,
        delta_t_horas=round(delta_t_resuelto, 2) if delta_t_resuelto is not None else None,
        modelo_calculo=p.modelo,
    )

    # Cálculos de interés y retorno
    if deuda <= 0.0 and fuente_interes not in ("yaml", "ninguna"):
        reporte.interes_anual_usd = 0.0
        reporte.payback_anios = 0.0
        reporte.roi_4_anios_porc = 0.0
        reporte.roi_ajustado_porc = 0.0 if p.modelo == "dinamico" else None
        reporte.tiene_datos_interes = True
        reporte.fuente_interes = "sin_deuda"
    elif cambios_anuales is not None and delta_t_resuelto is not None:
        interes = calcular_interes_anual(cambios_anuales, delta_t_resuelto, costo_hora_usd=p.costo_hora_usd)
        payback = calcular_payback_anios(costo, interes)
        roi = calcular_roi_4_anios(costo, interes, anios=p.anios_proyeccion)
        roi_ajustado = (
            calcular_roi_ajustado_riesgo(costo, interes, anios=p.anios_proyeccion, tasa_exito=p.tasa_exito_roi)
            if p.modelo == "dinamico"
            else None
        )

        reporte.interes_anual_usd = round(interes, 2)
        reporte.payback_anios = round(payback, 2) if payback is not None else None
        reporte.roi_4_anios_porc = round(roi, 2) if roi is not None else None
        reporte.roi_ajustado_porc = round(roi_ajustado, 2) if roi_ajustado is not None else None
        reporte.tiene_datos_interes = True
        reporte.fuente_interes = fuente_interes

    return reporte
