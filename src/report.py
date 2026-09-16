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

from config import CC_UMBRAL_POR_LENGUAJE, DEUDA_TECNICA_UMBRAL_PORC, MI_UMBRAL_ACEPTABLE
from debt_calculator import ReporteFinancieroArchivo


def _fmt_usd(v: float | None) -> str:
    return f"${v:,.2f}" if v is not None else "s/d"


def _fmt_anios(v: float | None) -> str:
    return f"{v:.2f} años" if v is not None else "s/d"


def _fmt_porc(v: float | None) -> str:
    return f"{v:+.2f}%" if v is not None else "s/d"


def _semaforo_mi(mi: float) -> str:
    return "🟢" if mi >= MI_UMBRAL_ACEPTABLE else "🔴"


def _semaforo_cc(cc: int, lenguaje: str) -> str:
    umbral = CC_UMBRAL_POR_LENGUAJE.get(lenguaje)
    if umbral is None:
        return "⚪"
    return "🟢" if cc <= umbral else "🔴"


def imprimir_tabla_consola(reportes: list[ReporteFinancieroArchivo]) -> None:
    if not reportes:
        print("No hay archivos analizados.")
        return

    print()
    print("=" * 118)
    print("REPORTE DE DEUDA TÉCNICA")
    print("=" * 118)
    print(
        f"{'Archivo':<38} {'Lang':<5} {'LOC':>6} {'CC':>5} {'MI':>7}  "
        f"{'Deuda(h)':>9} {'Costo':>12} {'Interés/año':>12} {'Payback':>12} {'ROI 4a':>9}"
    )
    print("-" * 118)

    for r in reportes:
        cc_flag = _semaforo_cc(r.complejidad_ciclomatica, r.lenguaje)
        mi_flag = _semaforo_mi(r.mi)
        nombre = r.ruta if len(r.ruta) <= 38 else "…" + r.ruta[-37:]
        interes = _fmt_usd(r.interes_anual_usd) if r.tiene_datos_interes else "sin config"
        payback = _fmt_anios(r.payback_anios) if r.tiene_datos_interes else "-"
        roi = _fmt_porc(r.roi_4_anios_porc) if r.tiene_datos_interes else "-"

        print(
            f"{nombre:<38} {r.lenguaje:<5} {r.loc:>6} {cc_flag}{r.complejidad_ciclomatica:>3} "
            f"{mi_flag}{r.mi:>5.2f}  {r.deuda_horas:>9.2f} {_fmt_usd(r.costo_reparacion_usd):>12} "
            f"{interes:>12} {payback:>12} {roi:>9}"
        )

    print("-" * 118)
    sin_config = [r.ruta for r in reportes if not r.tiene_datos_interes]
    if sin_config:
        print(
            f"⚠️  Sin datos de interés anual (faltan en el YAML de config) para: "
            f"{', '.join(sin_config)}"
        )
        print("    -> Interés/Payback/ROI no calculados para esos archivos.")

    print(
        f"\nReferencia: MI aceptable según la cátedra >= {MI_UMBRAL_ACEPTABLE}% | "
        f"Deuda técnica relativa objetivo <= {DEUDA_TECNICA_UMBRAL_PORC}% | "
        f"CC max Dart <= {CC_UMBRAL_POR_LENGUAJE['dart']}, Go <= {CC_UMBRAL_POR_LENGUAJE['go']}"
    )
    print(
        "Nota: qué MI_referencia usar para el cálculo de deuda (fijo vs. por "
        "lenguaje) quedó pendiente de definir -> ajustable con --mi-referencia.\n"
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
