"""
Salida del reporte: tabla en consola (igual formato al documento de
clase) + export a CSV y JSON para trackear histórico entre corridas.
"""
from __future__ import annotations

import csv
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import (
    CC_UMBRAL_POR_LENGUAJE,
    DEUDA_TECNICA_UMBRAL_PORC,
    MI_UMBRAL_CRITICO,
    MI_UMBRAL_EXCELENTE,
)
from debt_calculator import ReporteFinancieroArchivo

# Códigos de color ANSI para consola
COLOR_ROJO = "\033[91m"
COLOR_VERDE_CLARO = "\033[92m"
COLOR_VERDE_OSCURO = "\033[32m"
COLOR_RESET = "\033[0m"


def _fmt_usd(v: float | None) -> str:
    return f"${v:,.2f}" if v is not None else "s/d"


def _fmt_anios(v: float | None) -> str:
    return f"{v:.2f} años" if v is not None else "s/d"


def _fmt_porc(v: float | None) -> str:
    return f"{v:+.2f}%" if v is not None else "s/d"


def _semaforo_cc(cc: int, lenguaje: str) -> str:
    umbral = CC_UMBRAL_POR_LENGUAJE.get(lenguaje)
    if umbral is None:
        return "⚪"
    return "🟢" if cc <= umbral else "🔴"


def _fmt_mi_consola(mi: float) -> str:
    """Formatea el valor de MI con emoji y color según su rango."""
    if mi < MI_UMBRAL_CRITICO:
        return f"🔴{COLOR_ROJO}{mi:>5.2f}{COLOR_RESET}"
    elif mi < MI_UMBRAL_EXCELENTE:
        return f"🟢{COLOR_VERDE_CLARO}{mi:>5.2f}{COLOR_RESET}"
    else:
        return f"🟢{COLOR_VERDE_OSCURO}{mi:>5.2f}{COLOR_RESET}"


def _fmt_estado_consola(estado: str) -> str:
    """Formatea la etiqueta de estado de mantenibilidad con color."""
    if estado == "CRITICO":
        return f"{COLOR_ROJO}CRÍTICO  {COLOR_RESET}"
    elif estado == "APROBADO":
        return f"{COLOR_VERDE_CLARO}APROBADO {COLOR_RESET}"
    else:
        return f"{COLOR_VERDE_OSCURO}EXCELENTE{COLOR_RESET}"


def imprimir_tabla_consola(reportes: list[ReporteFinancieroArchivo]) -> None:
    if not reportes:
        print("No hay archivos analizados.")
        return

    print()
    print("=" * 130)
    print("REPORTE DE DEUDA TÉCNICA")
    print("=" * 130)
    print(
        f"{'Archivo':<36} {'Lang':<5} {'LOC':>6} {'CC':>5} {'MI':>8}  "
        f"{'Estado':<9} {'Deuda(h)':>9} {'Costo':>12} {'Interés/año':>12} {'Payback':>12} {'ROI 4a':>9}"
    )
    print("-" * 130)

    for r in reportes:
        cc_flag = _semaforo_cc(r.complejidad_ciclomatica, r.lenguaje)
        mi_str = _fmt_mi_consola(r.mi)
        estado_str = _fmt_estado_consola(r.estado_mi)
        nombre = r.ruta if len(r.ruta) <= 36 else "…" + r.ruta[-35:]
        interes = _fmt_usd(r.interes_anual_usd) if r.tiene_datos_interes else "sin config"
        payback = _fmt_anios(r.payback_anios) if r.tiene_datos_interes else "-"
        roi = _fmt_porc(r.roi_4_anios_porc) if r.tiene_datos_interes else "-"

        print(
            f"{nombre:<36} {r.lenguaje:<5} {r.loc:>6} {cc_flag}{r.complejidad_ciclomatica:>3} "
            f"{mi_str}  {estado_str} {r.deuda_horas:>9.2f} {_fmt_usd(r.costo_reparacion_usd):>12} "
            f"{interes:>12} {payback:>12} {roi:>9}"
        )

    print("-" * 130)
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
        resumen_fuentes.append(f"{en_fijo} estimados fijos")
    if en_sin_deuda:
        resumen_fuentes.append(f"{en_sin_deuda} aprobados/sin deuda ($0)")

    if resumen_fuentes:
        print(f"Fuentes de cálculo financiero: {', '.join(resumen_fuentes)}.")
    if sin_datos:
        print(f"⚠️  Sin datos de interés para: {', '.join(sin_datos)}")

    print(
        f"\nReferencia MI: 🔴 < {MI_UMBRAL_CRITICO} (Crítico / No aprobado) | "
        f"🟢 {MI_UMBRAL_CRITICO} - {MI_UMBRAL_EXCELENTE-0.1:.1f} (Aprobado / Verde claro) | "
        f"🟢 >= {MI_UMBRAL_EXCELENTE} (Excelente / Verde oscuro)"
    )
    print(
        f"Deuda técnica relativa objetivo <= {DEUDA_TECNICA_UMBRAL_PORC}% | "
        f"CC max Dart <= {CC_UMBRAL_POR_LENGUAJE['dart']}, Go <= {CC_UMBRAL_POR_LENGUAJE['go']}"
    )
    print(
        "Nota: el cálculo de deuda(h) usa --mi-referencia (default: "
        "20.0 para salir de crítico / aprobado; usar 60.0 para excelencia).\n"
    )


def exportar_json(reportes: list[ReporteFinancieroArchivo], path: Path) -> None:
    data = {
        "generado_en": datetime.now(timezone.utc).isoformat(),
        "archivos": [asdict(r) for r in reportes],
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def exportar_csv(reportes: list[ReporteFinancieroArchivo], path: Path) -> None:
    if not reportes:
        return
    campos = list(asdict(reportes[0]).keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for r in reportes:
            writer.writerow(asdict(r))
