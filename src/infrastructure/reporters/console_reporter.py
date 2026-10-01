"""
Exportador de consola para visualización en terminal con formato de semáforo y tabla.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src.application.ports import ReportExporter
from src.config import (
    CC_UMBRAL_POR_LENGUAJE,
    DEUDA_TECNICA_UMBRAL_PORC,
    MI_UMBRAL_AMARILLO_DINAMICO,
    MI_UMBRAL_CRITICO,
    MI_UMBRAL_DINAMICO,
    MI_UMBRAL_EXCELENTE,
)
from src.domain.models import AnalysisSummary, DebtReport

COLOR_ROJO = "\033[91m"
COLOR_AMARILLO = "\033[93m"
COLOR_VERDE_CLARO = "\033[92m"
COLOR_VERDE_OSCURO = "\033[32m"
COLOR_RESET = "\033[0m"


def _fmt_usd(v: Optional[float]) -> str:
    return f"${v:,.2f}" if v is not None else "s/d"


def _fmt_anios(v: Optional[float]) -> str:
    return f"{v:.2f} años" if v is not None else "s/d"


def _fmt_porc(v: Optional[float]) -> str:
    return f"{v:+.1f}%" if v is not None else "s/d"


def _semaforo_cc(cc: int, lenguaje: str) -> str:
    umbral = CC_UMBRAL_POR_LENGUAJE.get(lenguaje)
    if umbral is None:
        return "⚪"
    return "🟢" if cc <= umbral else "🔴"


def _fmt_mi_consola(mi: float, modelo: str = "dinamico") -> str:
    if modelo == "dinamico":
        if mi < MI_UMBRAL_AMARILLO_DINAMICO:
            return f"🔴{COLOR_ROJO}{mi:>5.2f}{COLOR_RESET}"
        elif mi < MI_UMBRAL_DINAMICO:
            return f"🟡{COLOR_AMARILLO}{mi:>5.2f}{COLOR_RESET}"
        else:
            return f"🟢{COLOR_VERDE_OSCURO}{mi:>5.2f}{COLOR_RESET}"
    else:
        if mi < MI_UMBRAL_CRITICO:
            return f"🔴{COLOR_ROJO}{mi:>5.2f}{COLOR_RESET}"
        elif mi < MI_UMBRAL_EXCELENTE:
            return f"🟢{COLOR_VERDE_CLARO}{mi:>5.2f}{COLOR_RESET}"
        else:
            return f"🟢{COLOR_VERDE_OSCURO}{mi:>5.2f}{COLOR_RESET}"


def _fmt_estado_consola(estado: str, modelo: str = "dinamico") -> str:
    if estado == "CRITICO":
        return f"{COLOR_ROJO}CRÍTICO  {COLOR_RESET}"
    elif estado == "APROBADO":
        col = COLOR_AMARILLO if modelo == "dinamico" else COLOR_VERDE_CLARO
        return f"{col}APROBADO {COLOR_RESET}"
    else:
        return f"{COLOR_VERDE_OSCURO}EXCELENTE{COLOR_RESET}"


class ConsoleReporter(ReportExporter):
    """Exportador para terminal / consola."""

    def export(self, summary: AnalysisSummary, destination: Optional[Path] = None) -> None:
        self.imprimir_tabla(summary.reportes, modelo=summary.modelo_calculo)
        if summary.sqale_report:
            self.imprimir_arquitectura_y_sqale(summary.sqale_report)

    @staticmethod
    def imprimir_arquitectura_y_sqale(sqale_report: any) -> None:
        modulos = getattr(sqale_report, "modulos", [])
        ancho = 120
        print()
        print("=" * ancho)
        print("ANÁLISIS ARQUITECTÓNICO DE LÍMITES LÓGICOS (Robert C. Martin - SDP / SAP)")
        print("=" * ancho)
        print(
            f"{'Módulo':<20} {'Archivos':>8} {'Ca':>4} {'Ce':>4} {'I':>6} "
            f"{'Na':>4} {'Nc':>4} {'A':>6} {'D':>6}  {'Zona':<22} {'Depende de':<25}"
        )
        print("-" * ancho)

        for m in modulos:
            zona_icon = "🟢" if m.zona == "SECUENCIA_PRINCIPAL" else ("🔴" if m.zona == "ZONA_DOLOR" else "🟡")
            zona_str = f"{zona_icon} {m.zona}"
            deps_out_str = ", ".join(m.dependencias_out) if m.dependencias_out else "-"
            if len(deps_out_str) > 25:
                deps_out_str = deps_out_str[:22] + "..."

            print(
                f"{m.nombre:<20} {m.archivos:>8} {m.ca:>4} {m.ce:>4} {m.inestabilidad:>6.2f} "
                f"{m.na:>4} {m.nc:>4} {m.abstraccion:>6.2f} {m.distancia_d:>6.2f}  "
                f"{zona_str:<22} {deps_out_str:<25}"
            )

        print("-" * ancho)
        print("Métricas: Ca=Acoplamiento Aferente | Ce=Eferente | I=Inestabilidad (Ce/(Ca+Ce)) | A=Abstracción (Na/Nc) | D=|A+I-1|")
        print("Invariancia lógica: Conteo por relación única entre módulos de capas independientes.")

        print()
        print("=" * ancho)
        print("VALORACIÓN FINANCIERA DE SOFTWARE Y DEUDA TÉCNICA SQALE (ISO/IEC 25010)")
        print("=" * ancho)

        # Semáforo de TDR
        tdr = sqale_report.tdr
        if tdr <= 5.0:
            tdr_str = f"🟢 {tdr:.2f}% (Excelente - Bajo riesgo)"
        elif tdr <= 20.0:
            tdr_str = f"🟡 {tdr:.2f}% (Moderado - Refactorización planificada)"
        else:
            tdr_str = f"🔴 {tdr:.2f}% (Crítico - Inviable de mantener; evaluar reemplazo)"

        print(f"Total de Violaciones Detectadas: {sqale_report.total_violaciones}")
        print(f"Costo de Remediación SQALE (L_TD): {_fmt_usd(sqale_report.l_td)}")
        print(f"Valor Numérico del Activo (V_A):    {_fmt_usd(sqale_report.v_a)}")
        print(f"Costo Base de Reemplazo Estimado:  {_fmt_usd(sqale_report.costo_reemplazo)}")
        print(f"Technical Debt Ratio (TDR):        {tdr_str}")
        print(f"Factores de Calibración:           α_L={sqale_report.alpha_l:.2f}, β_L={sqale_report.beta_l:.2f}")

        # Desglose de violaciones si existen
        violaciones = getattr(sqale_report, "violaciones", [])
        if violaciones:
            conteo_reglas: dict[str, int] = {}
            for v in violaciones:
                conteo_reglas[v.regla] = conteo_reglas.get(v.regla, 0) + 1

            desglose = ", ".join(f"{regla}: {cnt}" for regla, cnt in sorted(conteo_reglas.items()))
            print(f"Desglose de violaciones:           {desglose}")

        print("=" * ancho)
        print()


    @staticmethod
    def imprimir_tabla(reportes: list[DebtReport], modelo: Optional[str] = None) -> None:
        if not reportes:
            print("No hay archivos analizados.")
            return

        modelo_efectivo = modelo or (reportes[0].modelo_calculo if reportes else "dinamico")
        es_dinamico = modelo_efectivo == "dinamico"
        ancho_linea = 150 if es_dinamico else 130

        print()
        print("=" * ancho_linea)
        titulo = (
            "REPORTE DE DEUDA TÉCNICA Y FRICCIÓN OPERATIVA (MODELO DINÁMICO)"
            if es_dinamico
            else "REPORTE DE DEUDA TÉCNICA (MODELO CLÁSICO)"
        )
        print(titulo)
        print("=" * ancho_linea)

        if es_dinamico:
            print(
                f"{'Archivo':<32} {'Lang':<5} {'LOC':>5} {'CC':>5} {'MI':>8}  "
                f"{'Estado':<9} {'F(MI)':>6} {'Δt(h)':>6} {'Deuda(h)':>8} {'Costo':>11} "
                f"{'Interés/año':>11} {'Payback':>10} {'ROI 4a':>8} {'ROI 65%':>8}"
            )
        else:
            print(
                f"{'Archivo':<36} {'Lang':<5} {'LOC':>6} {'CC':>5} {'MI':>8}  "
                f"{'Estado':<9} {'Deuda(h)':>9} {'Costo':>12} {'Interés/año':>12} {'Payback':>12} {'ROI 4a':>9}"
            )
        print("-" * ancho_linea)

        for r in reportes:
            cc_flag = _semaforo_cc(r.complejidad_ciclomatica, r.lenguaje)
            mi_str = _fmt_mi_consola(r.mi, modelo=modelo)
            estado_str = _fmt_estado_consola(r.estado_mi, modelo=modelo)
            interes = _fmt_usd(r.interes_anual_usd) if r.tiene_datos_interes else "sin config"
            payback = _fmt_anios(r.payback_anios) if r.tiene_datos_interes else "-"
            roi = _fmt_porc(r.roi_4_anios_porc) if r.tiene_datos_interes else "-"
            deuda_val = r.deuda_horas if r.deuda_horas is not None else 0.0

            if es_dinamico:
                nombre = r.ruta if len(r.ruta) <= 32 else "…" + r.ruta[-31:]
                f_str = f"{r.factor_friccion:.2f}x" if r.factor_friccion is not None else "-"
                dt_str = f"+{r.delta_t_horas:.1f}h" if r.delta_t_horas is not None else "-"
                roi_aj = _fmt_porc(r.roi_ajustado_porc) if r.tiene_datos_interes else "-"

                print(
                    f"{nombre:<32} {r.lenguaje:<5} {r.loc:>5} {cc_flag}{r.complejidad_ciclomatica:>3} "
                    f"{mi_str}  {estado_str} {f_str:>6} {dt_str:>6} {deuda_val:>8.2f} "
                    f"{_fmt_usd(r.costo_reparacion_usd):>11} {interes:>11} {payback:>10} "
                    f"{roi:>8} {roi_aj:>8}"
                )
            else:
                nombre = r.ruta if len(r.ruta) <= 36 else "…" + r.ruta[-35:]
                print(
                    f"{nombre:<36} {r.lenguaje:<5} {r.loc:>6} {cc_flag}{r.complejidad_ciclomatica:>3} "
                    f"{mi_str}  {estado_str} {deuda_val:>9.2f} {_fmt_usd(r.costo_reparacion_usd):>12} "
                    f"{interes:>12} {payback:>12} {roi:>9}"
                )

        print("-" * ancho_linea)
        en_yaml = sum(1 for r in reportes if r.fuente_interes == "yaml")
        en_git = sum(1 for r in reportes if r.fuente_interes == "git")
        en_fijo = sum(1 for r in reportes if r.fuente_interes == "fijo")
        en_sin_deuda = sum(1 for r in reportes if r.fuente_interes == "sin_deuda")
        sin_datos = [r.ruta for r in reportes if not r.tiene_datos_interes]

        resumen_fuentes = []
        if en_yaml:
            resumen_fuentes.append(f"{en_yaml} vía YAML")
        if en_git:
            resumen_fuentes.append(f"{en_git} estimados vía Git")
        if en_fijo:
            resumen_fuentes.append(f"{en_fijo} baselines fijos/capa")
        if en_sin_deuda:
            resumen_fuentes.append(f"{en_sin_deuda} aprobados/sin deuda ($0)")

        if resumen_fuentes:
            print(f"Fuentes de cálculo financiero: {', '.join(resumen_fuentes)}.")
        if sin_datos:
            print(f"⚠️  Sin datos de interés para: {', '.join(sin_datos)}")

        if es_dinamico:
            print(
                f"\nReferencia MI Dinámica: 🔴 < {MI_UMBRAL_AMARILLO_DINAMICO} (Crítico) | "
                f"🟡 {MI_UMBRAL_AMARILLO_DINAMICO} - {MI_UMBRAL_DINAMICO-0.1:.1f} (Aprobado) | "
                f"🟢 >= {MI_UMBRAL_DINAMICO} (Excelente / Limpio)"
            )
            print(
                "Fricción F(MI) = 1 + ((75 - MI)/75)^2 * 3 | Factor K = [0.01 - (EF/5)*0.0067] * TCF"
            )
            print(
                "ROI 65%: Calibrado por probabilidad empírica de éxito en refactorización incremental.\n"
            )
        else:
            print(
                f"\nReferencia MI Clásica: 🔴 < {MI_UMBRAL_CRITICO} (Crítico / No aprobado) | "
                f"🟢 {MI_UMBRAL_CRITICO} - {MI_UMBRAL_EXCELENTE-0.1:.1f} (Aprobado / Verde claro) | "
                f"🟢 >= {MI_UMBRAL_EXCELENTE} (Excelente / Verde oscuro)"
            )
            print(
                f"Deuda técnica relativa objetivo <= {DEUDA_TECNICA_UMBRAL_PORC}% | "
                f"CC max Dart <= {CC_UMBRAL_POR_LENGUAJE['dart']}, Go <= {CC_UMBRAL_POR_LENGUAJE['go']}"
            )
            print(
                "Nota: cálculo clásico con --mi-referencia 20.0 para salir de crítico.\n"
            )
