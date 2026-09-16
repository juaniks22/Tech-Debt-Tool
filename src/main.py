#!/usr/bin/env python3
"""
Herramienta de deuda técnica para SGA-practicas.

Analiza archivos Go y Dart de un repo con herramientas estándar de la
industria (gocloc, gocyclo, dcm), calcula Índice de Mantenibilidad,
deuda técnica en horas, costo de reparación, interés anual, payback y
ROI a 4 años -- replicando el cálculo manual validado en clase.

Uso típico:
    python main.py --repo /ruta/al/repo --init-config
    # completar intereses.yaml con los datos del equipo
    python main.py --repo /ruta/al/repo
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config import (
    InteresArchivo,
    MI_REFERENCIA_DEFAULT,
    cargar_intereses,
    generar_config_ejemplo,
)
from debt_calculator import construir_reporte_archivo
from metrics import metrica_dart_desde_dcm, metrica_go_desde_raw
from report import exportar_csv, exportar_json, imprimir_tabla_consola
from tool_runner import (
    HerramientaFaltanteError,
    asegurar_dcm,
    asegurar_gocloc,
    asegurar_gocyclo,
    correr_dcm,
    correr_gocloc,
    correr_gocyclo,
)


def analizar_go(repo_path: Path, subpath: str):
    asegurar_gocloc()
    asegurar_gocyclo()

    loc_data = correr_gocloc(repo_path, subpath)
    cc_data = correr_gocyclo(repo_path, subpath)

    loc_por_archivo: dict[str, int] = {}
    for f in loc_data.get("files", []):
        if f["filename"].endswith(".go"):
            loc_por_archivo[f["filename"]] = f["code"]

    cc_por_archivo: dict[str, list[int]] = {}
    for item in cc_data:
        cc_por_archivo.setdefault(item["archivo"], []).append(item["complejidad"])

    metricas = []
    for archivo, loc in loc_por_archivo.items():
        complejidades = cc_por_archivo.get(archivo, [])
        metricas.append(metrica_go_desde_raw(archivo, loc, complejidades))
    return metricas


def analizar_dart(repo_path: Path, subpath: str):
    asegurar_dcm()
    data = correr_dcm(repo_path, subpath)

    metricas = []
    # Estructura real del JSON de dcm puede variar entre versiones;
    # este parseo cubre el formato "records" documentado. Si tu versión
    # difiere, avisame el JSON real y ajusto el parser.
    for record in data.get("records", []):
        ruta = record.get("file-path") or record.get("filePath")
        if not ruta:
            continue
        metrics = record.get("metrics", {})
        loc = int(metrics.get("source-lines-of-code", 0))
        cc = int(metrics.get("cyclomatic-complexity", 0))
        mi = float(metrics.get("maintainability-index", 0))
        metricas.append(metrica_dart_desde_dcm(ruta, loc, cc, mi))
    return metricas


def main() -> int:
    parser = argparse.ArgumentParser(description="Análisis de deuda técnica para SGA-practicas")
    parser.add_argument("--repo", type=Path, help="Ruta a la raíz del repo")
    parser.add_argument("--go-path", default=".", help="Subcarpeta con código Go (default: raíz)")
    parser.add_argument("--dart-path", default="lib", help="Subcarpeta con código Dart (default: lib)")
    parser.add_argument("--config", type=Path, default=Path("intereses.yaml"),
                         help="YAML con cambios_anuales/delta_t por archivo")
    parser.add_argument("--init-config", action="store_true",
                         help="Genera una plantilla de --config y sale")
    parser.add_argument("--mi-referencia", type=float, default=MI_REFERENCIA_DEFAULT,
                         help=f"MI de referencia para calcular deuda (default: {MI_REFERENCIA_DEFAULT})")
    parser.add_argument("--out-json", type=Path, default=Path("reporte_deuda.json"))
    parser.add_argument("--out-csv", type=Path, default=Path("reporte_deuda.csv"))
    parser.add_argument("--skip-go", action="store_true", help="No analizar archivos Go")
    parser.add_argument("--skip-dart", action="store_true", help="No analizar archivos Dart")
    args = parser.parse_args()

    if args.init_config:
        generar_config_ejemplo(args.config)
        return 0

    if not args.repo:
        parser.error("--repo es obligatorio (o usá --init-config primero)")

    if not args.repo.exists():
        print(f"Error: no existe la ruta {args.repo}", file=sys.stderr)
        return 1

    intereses = cargar_intereses(args.config)

    todas_metricas = []
    try:
        if not args.skip_go:
            print("[main] Analizando archivos Go (gocloc + gocyclo)...", file=sys.stderr)
            todas_metricas += analizar_go(args.repo, args.go_path)
        if not args.skip_dart:
            print("[main] Analizando archivos Dart (dcm)...", file=sys.stderr)
            todas_metricas += analizar_dart(args.repo, args.dart_path)
    except HerramientaFaltanteError as e:
        print(f"\nError de setup: {e}", file=sys.stderr)
        return 1

    reportes = []
    for m in todas_metricas:
        interes: InteresArchivo | None = intereses.get(m.ruta)
        reportes.append(
            construir_reporte_archivo(
                m,
                mi_referencia=args.mi_referencia,
                cambios_anuales=interes.cambios_anuales if interes else None,
                delta_t_horas=interes.delta_t_horas if interes else None,
            )
        )

    # Ordenar por deuda descendente, como la tabla de prioridades del documento
    reportes.sort(key=lambda r: r.deuda_horas or 0, reverse=True)

    imprimir_tabla_consola(reportes)
    exportar_json(reportes, args.out_json)
    exportar_csv(reportes, args.out_csv)
    print(f"Exportado: {args.out_json} / {args.out_csv}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
