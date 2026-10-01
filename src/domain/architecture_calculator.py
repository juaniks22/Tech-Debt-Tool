"""
Fórmulas matemáticas para métricas arquitectónicas de Robert C. Martin
y modelo de valoración financiera SQALE (ISO/IEC 25010).
Dominio puro: sin I/O ni dependencias externas.
"""
from __future__ import annotations

from typing import List
from src.domain.architecture import Violation


def calcular_inestabilidad(ca: int, ce: int) -> float:
    """
    Calcula la Inestabilidad (I) de un módulo:
    I = Ce / (Ca + Ce)
    Rango [0, 1]. Si Ca + Ce == 0, se define I = 0.0 (estable por defecto / aislado).
    """
    total = ca + ce
    if total <= 0:
        return 0.0
    return round(float(ce) / float(total), 4)


def calcular_abstraccion(na: int, nc: int) -> float:
    """
    Calcula la Abstracción (A) de un módulo:
    A = Na / Nc
    Donde Na = interfaces o clases abstractas, Nc = total de clases/estructuras.
    Rango [0, 1]. Si Nc == 0, A = 0.0.
    """
    if nc <= 0:
        return 0.0
    return round(float(na) / float(nc), 4)


def calcular_distancia_d(abstraccion: float, inestabilidad: float) -> float:
    """
    Calcula la Distancia a la Secuencia Principal (D):
    D = |A + I - 1|
    Rango [0, 1]. Rango ideal: D -> 0.
    """
    return round(abs(abstraccion + inestabilidad - 1.0), 4)


def clasificar_zona(abstraccion: float, inestabilidad: float, distancia_d: float, umbral_d: float = 0.5) -> str:
    """
    Clasifica el balance arquitectónico del módulo:
    - Zona de Dolor: Alta estabilidad (I baja), poca abstracción (A baja), D alta.
    - Zona de Inutilidad: Alta inestabilidad (I alta), alta abstracción (A alta), D alta.
    - Secuencia Principal: D balanceada (<= umbral_d).
    """
    if distancia_d > umbral_d:
        if abstraccion < 0.5 and inestabilidad < 0.5:
            return "ZONA_DOLOR"
        if abstraccion >= 0.5 and inestabilidad >= 0.5:
            return "ZONA_INUTILIDAD"
    return "SECUENCIA_PRINCIPAL"


def factor_penalizacion_d(distancia_d: float, peso: float = 0.3) -> float:
    """
    Factor de amplificación de deuda técnica por desbalance arquitectónico:
    Factor = 1.0 + (D * peso).
    Si D = 0 -> factor 1.0 (sin penalización).
    Si D = 0.8 y peso = 0.3 -> factor 1.24 (+24% de deuda por riesgo de acoplamiento).
    """
    return max(1.0, 1.0 + (distancia_d * peso))


def calcular_l_td(violaciones: list[Violation], alpha_l: float, tarifa_usd: float) -> float:
    """
    Costo de Remediación de Deuda Técnica SQALE (L_TD):
    L_TD = sum(Violaciones_i * TiempoRemediacion_i_horas * alpha_L) * CostoHoraDev
    """
    horas_totales = sum((v.remediacion_minutos / 60.0) for v in violaciones) * alpha_l
    return round(horas_totales * tarifa_usd, 2)


def calcular_valor_activo(loc_total: int, costo_linea_base: float, beta_l: float, l_td: float) -> float:
    """
    Valor Numérico del Activo (V_A):
    V_A = (LOC * CostoPorLineaBase * beta_L) - L_TD
    """
    costo_bruto = loc_total * costo_linea_base * beta_l
    return round(costo_bruto - l_td, 2)


def calcular_costo_reemplazo(loc_total: int, costo_linea_base: float, beta_l: float) -> float:
    """
    Costo estimado de reposición del software:
    CostoReemplazo = LOC * CostoPorLineaBase * beta_L
    """
    return round(loc_total * costo_linea_base * beta_l, 2)


def calcular_tdr(l_td: float, costo_reemplazo: float) -> float:
    """
    Ratio de Deuda Técnica (TDR %):
    TDR = (L_TD / CostoReemplazo) * 100
    """
    if costo_reemplazo <= 0.0:
        return 0.0
    return round((l_td / costo_reemplazo) * 100.0, 2)


def clasificar_tdr(tdr_porcentaje: float) -> str:
    """
    Evaluación cualitativa según modelo SQALE:
    TDR <= 5%: Excelente (Bajo riesgo)
    5% < TDR <= 20%: Moderado (Refactorización planificada)
    TDR > 20%: Crítico (Inviable de mantener; considerar reemplazo)
    """
    if tdr_porcentaje <= 5.0:
        return "EXCELENTE"
    if tdr_porcentaje <= 20.0:
        return "MODERADO"
    return "CRITICO"
