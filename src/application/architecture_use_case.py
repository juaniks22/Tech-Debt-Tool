"""
Caso de uso: Análisis Arquitectónico (Robert C. Martin) y Valoración SQALE (ISO/IEC 25010).
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from src.domain.architecture import ModuleMetrics, SQALEReport, Violation
from src.domain.architecture_calculator import (
    calcular_costo_reemplazo,
    calcular_l_td,
    calcular_tdr,
    calcular_valor_activo,
    clasificar_tdr,
    factor_penalizacion_d,
)
from src.domain.models import DebtReport, FileMetric, FinancialParams
from src.domain.violation_catalog import evaluar_violaciones_archivo
from src.infrastructure.analyzers.module_analyzer import ModuleAnalyzer


class ArchitectureAnalysisUseCase:
    """Orquesta el cálculo de métricas de acoplamiento, catálogo de violaciones y balance SQALE."""

    def __init__(
        self,
        tarifa_usd: float = 30.0,
        alpha_l: float = 1.0,
        beta_l: float = 1.0,
        costo_linea_base: float = 1.0,
        peso_penalizacion_d: float = 0.3,
    ) -> None:
        self.tarifa_usd = tarifa_usd
        self.alpha_l = alpha_l
        self.beta_l = beta_l
        self.costo_linea_base = costo_linea_base
        self.peso_penalizacion_d = peso_penalizacion_d

    def execute(
        self,
        repo_path: Path,
        subpath_map: dict[str, str],
        file_metrics: list[FileMetric],
        debt_reports: list[DebtReport],
    ) -> SQALEReport:
        # 1. Analizar módulos, límites lógicos y dependencias
        analyzer = ModuleAnalyzer(repo_path, subpath_map)
        modulos, violaciones_arch, ciclos = analyzer.analyze()

        # 2. Evaluar violaciones SQALE sobre los archivos individuales
        todas_violaciones: list[Violation] = list(violaciones_arch)
        for fm in file_metrics:
            viols_archivo = evaluar_violaciones_archivo(fm)
            todas_violaciones.extend(viols_archivo)

        # 3. Mapear penalización D de módulo hacia los reportes de archivo si corresponde
        modulo_d_map = {m.nombre.lower(): m.distancia_d for m in modulos}
        for dr in debt_reports:
            # Identificar a qué módulo pertenece este archivo
            ruta_norm = dr.ruta.replace("\\", "/").lower()
            d_modulo = 0.0
            for mod_name, d_val in modulo_d_map.items():
                if f"/{mod_name}/" in ruta_norm or ruta_norm.startswith(f"{mod_name}/"):
                    d_modulo = d_val
                    break

            if d_modulo > 0.0 and dr.deuda_horas and dr.deuda_horas > 0:
                penalizacion = factor_penalizacion_d(d_modulo, self.peso_penalizacion_d)
                dr.deuda_horas = round(dr.deuda_horas * penalizacion, 2)
                if dr.costo_reparacion_usd is not None:
                    dr.costo_reparacion_usd = round(dr.deuda_horas * self.tarifa_usd, 2)

        # 4. Calcular métricas financieras SQALE
        total_loc = sum(fm.loc for fm in file_metrics)
        l_td = calcular_l_td(todas_violaciones, self.alpha_l, self.tarifa_usd)
        v_a = calcular_valor_activo(total_loc, self.costo_linea_base, self.beta_l, l_td)
        costo_reemplazo = calcular_costo_reemplazo(total_loc, self.costo_linea_base, self.beta_l)
        tdr = calcular_tdr(l_td, costo_reemplazo)
        estado_tdr = clasificar_tdr(tdr)

        return SQALEReport(
            modulos=modulos,
            violaciones=todas_violaciones,
            total_violaciones=len(todas_violaciones),
            l_td=l_td,
            v_a=v_a,
            costo_reemplazo=costo_reemplazo,
            tdr=tdr,
            estado_tdr=estado_tdr,
            alpha_l=self.alpha_l,
            beta_l=self.beta_l,
        )
