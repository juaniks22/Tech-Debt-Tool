"""
Caso de uso central: Análisis de repositorio y cálculo de deuda técnica.
Orquestador agnóstico de infraestructura.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.application.ports import CodeAnalyzer, FrictionProvider
from src.domain.calculator import (
    DEFAULT_PARAMS,
    calcular_deuda_horas,
    calcular_mi,
    construir_reporte_archivo,
)
from src.domain.models import (
    AnalysisSummary,
    DebtReport,
    FileMetric,
    FinancialParams,
)


class AnalyzeRepositoryUseCase:
    """Orquesta la recolección de métricas, estimación de fricción y cálculo financiero."""

    def __init__(
        self,
        analyzers: list[CodeAnalyzer],
        friction_provider: FrictionProvider,
        params: Optional[FinancialParams] = None,
    ) -> None:
        self.analyzers = analyzers
        self.friction_provider = friction_provider
        self.params = params or DEFAULT_PARAMS

    def execute(
        self,
        repo_path: Path,
        subpath_map: Optional[dict[str, str]] = None,
        solo_config: bool = False,
        mi_referencia: Optional[float] = None,
    ) -> AnalysisSummary:
        ref_mi = mi_referencia if mi_referencia is not None else self.params.mi_referencia_default
        subpaths = subpath_map or {}

        # 1. Recolectar métricas de todos los analizadores activos
        todas_metricas: list[FileMetric] = []
        for analyzer in self.analyzers:
            sub = subpaths.get(analyzer.name, "")
            if analyzer.can_analyze(repo_path, sub):
                metricas = analyzer.analyze(repo_path, sub)
                todas_metricas.extend(metricas)

        # 2. Calcular deuda técnica y fricción por archivo
        reportes: list[DebtReport] = []
        for m in todas_metricas:
            mi_actual = m.mi if m.mi is not None else calcular_mi(m.loc, m.complejidad_ciclomatica)
            k_usado = (
                self.params.factor_correccion_k
                if self.params.modelo == "clasico"
                else (0.01 - (self.params.ef_experiencia / 5.0) * 0.0067) * self.params.tcf
            )
            deuda_previa = calcular_deuda_horas(
                mi_actual, m.loc, ref_mi, factor_k=k_usado
            )

            estimacion = self.friction_provider.get_friction(m.ruta, m, deuda_previa)

            reporte = construir_reporte_archivo(
                metrica=m,
                mi_referencia=ref_mi,
                cambios_anuales=estimacion.cambios_anuales,
                delta_t_horas=estimacion.delta_t_horas,
                fuente_interes=estimacion.fuente,
                params=self.params,
                t_clean_horas=estimacion.t_clean_horas,
            )
            reportes.append(reporte)

        # 3. Filtrar si se solicitó únicamente archivos configurados en YAML
        if solo_config:
            reportes = [r for r in reportes if r.fuente_interes == "yaml"]

        # 4. Ordenar por deuda técnica descendente (archivos más críticos primero)
        reportes.sort(key=lambda r: r.deuda_horas or 0.0, reverse=True)

        # 5. Generar resumen global acumulativo
        total_loc = sum(r.loc for r in reportes)
        archivos_criticos = sum(1 for r in reportes if r.estado_mi == "CRITICO")
        archivos_aprobados = sum(1 for r in reportes if r.estado_mi == "APROBADO")
        archivos_excelentes = sum(1 for r in reportes if r.estado_mi == "EXCELENTE")
        total_deuda = round(sum(r.deuda_horas or 0.0 for r in reportes), 2)
        total_costo = round(sum(r.costo_reparacion_usd or 0.0 for r in reportes), 2)
        total_interes = round(sum(r.interes_anual_usd or 0.0 for r in reportes), 2)

        return AnalysisSummary(
            repo_path=str(repo_path),
            fecha=datetime.now(timezone.utc).isoformat(),
            reportes=reportes,
            total_loc=total_loc,
            archivos_criticos=archivos_criticos,
            archivos_aprobados=archivos_aprobados,
            archivos_excelentes=archivos_excelentes,
            total_deuda_horas=total_deuda,
            total_costo_reparacion_usd=total_costo,
            total_interes_anual_usd=total_interes,
            modelo_calculo=self.params.modelo,
        )
