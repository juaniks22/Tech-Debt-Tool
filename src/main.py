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
    DEFAULT_CAMBIOS_ANUALES,
    DEFAULT_DELTA_T_HORAS,
    InteresArchivo,
    MI_REFERENCIA_DEFAULT,
    cargar_intereses,
    generar_config_ejemplo,
)
from debt_calculator import construir_reporte_archivo
from metrics import calcular_mi, metrica_dart_desde_dcm, metrica_go_desde_raw
from report import exportar_csv, exportar_json, imprimir_tabla_consola
from tool_runner import (
    HerramientaFaltanteError,
    asegurar_dcm,
    asegurar_gocloc,
    asegurar_gocyclo,
    contar_commits_git_todos,
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
        nombre = f.get("name") or f.get("filename") or ""
        if nombre.endswith(".go"):
            ruta_norm = Path(nombre).as_posix()
            loc_por_archivo[ruta_norm] = f.get("code", 0)

    cc_por_archivo: dict[str, list[int]] = {}
    for item in cc_data:
        ruta_norm = Path(item["archivo"]).as_posix()
        cc_por_archivo.setdefault(ruta_norm, []).append(item["complejidad"])

    metricas = []
    for archivo, loc in loc_por_archivo.items():
        complejidades = cc_por_archivo.get(archivo, [])
        metricas.append(metrica_go_desde_raw(archivo, loc, complejidades))
    return metricas


def analizar_dart(repo_path: Path, subpath: str):
    asegurar_dcm()
    asegurar_gocloc()

    # 1. Obtener LOC por archivo Dart usando gocloc
    loc_data = correr_gocloc(repo_path, subpath)
    loc_por_archivo: dict[str, int] = {}
    for f in loc_data.get("files", []):
        nombre = f.get("name") or f.get("filename") or ""
        if nombre.endswith(".dart"):
            ruta_norm = Path(nombre).as_posix()
            loc_por_archivo[ruta_norm] = f.get("code", 0)

    # 2. Obtener métricas y complejidad ciclomática usando dcm
    data = correr_dcm(repo_path, subpath)

    metricas = []
    for record in data.get("records", []):
        ruta_raw = record.get("path") or record.get("file-path") or record.get("filePath") or ""
        if not ruta_raw:
            continue
        ruta_norm = Path(ruta_raw).as_posix()

        # Sumar complejidad ciclomática de todas las funciones/métodos
        complejidades_funciones: list[int] = []
        for fname, fval in record.get("functions", {}).items():
            for m in fval.get("metrics", []):
                if m.get("metricsId") == "cyclomatic-complexity":
                    complejidades_funciones.append(int(m.get("value", 0)))

        cc_total = sum(complejidades_funciones)

        # LOC de gocloc
        loc = loc_por_archivo.get(ruta_norm)
        if loc is None:
            for fpath, fcode in loc_por_archivo.items():
                if fpath.endswith(ruta_norm) or ruta_norm.endswith(fpath):
                    loc = fcode
                    break
        if loc is None:
            loc = 0

        mi = calcular_mi(loc, cc_total)
        metricas.append(metrica_dart_desde_dcm(ruta=ruta_norm, loc=loc, cc_total=cc_total, mi_reportado=round(mi, 2)))
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
    parser.add_argument("--solo-config", action="store_true",
                         help="Mostrar únicamente los archivos que tengan estimaciones en el archivo de configuración")
    parser.add_argument("--metodo-estimacion", choices=["git", "fijo"], default="git",
                         help="Método de estimación para archivos sin config: 'git' (default, cuenta commits) o 'fijo'")
    parser.add_argument("--default-cambios", type=int, default=DEFAULT_CAMBIOS_ANUALES,
                         help=f"Cambios anuales fijos si no están en config ni en git (default: {DEFAULT_CAMBIOS_ANUALES})")
    parser.add_argument("--default-delta-t", type=float, default=DEFAULT_DELTA_T_HORAS,
                         help=f"Delta T en horas por cambio para archivos con deuda sin config (default: {DEFAULT_DELTA_T_HORAS}h)")
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

    # Auto-detección de subcarpetas en SGA-practicas
    go_path = args.go_path
    if go_path == "." and (args.repo / "backend").is_dir():
        go_path = "backend"
        print(f"[main] Auto-detectado código Go en '{go_path}'", file=sys.stderr)

    dart_path = args.dart_path
    if dart_path == "lib":
        if (args.repo / "frontend" / "lib").is_dir():
            dart_path = "frontend/lib"
            print(f"[main] Auto-detectado código Dart en '{dart_path}'", file=sys.stderr)
        elif (args.repo / "lib").is_dir():
            dart_path = "lib"

    intereses = cargar_intereses(args.config)

    todas_metricas = []
    try:
        if not args.skip_go:
            print("[main] Analizando archivos Go (gocloc + gocyclo)...", file=sys.stderr)
            todas_metricas += analizar_go(args.repo, go_path)
        if not args.skip_dart:
            print("[main] Analizando archivos Dart (dcm)...", file=sys.stderr)
            todas_metricas += analizar_dart(args.repo, dart_path)
    except HerramientaFaltanteError as e:
        print(f"\nError de setup: {e}", file=sys.stderr)
        return 1

    # Si se usa método git, precargamos el conteo de commits para todos los archivos
    commits_git: dict[str, int] = {}
    if args.metodo_estimacion == "git" and (args.repo / ".git").is_dir():
        try:
            commits_git = contar_commits_git_todos(args.repo)
        except Exception as e:
            print(f"[main] Aviso: no se pudo leer historial git ({e}). Usando valores fijos.", file=sys.stderr)

    reportes = []
    for m in todas_metricas:
        interes: InteresArchivo | None = intereses.get(m.ruta)
        if interes:
            cambios = interes.cambios_anuales
            delta_t = interes.delta_t_horas
            fuente = "yaml"
        else:
            # Archivo sin configuración explícita en intereses.yaml
            if args.metodo_estimacion == "git" and commits_git:
                c_git = commits_git.get(m.ruta)
                if c_git is None:
                    for gpath, gcount in commits_git.items():
                        if gpath.endswith(m.ruta) or m.ruta.endswith(gpath):
                            c_git = gcount
                            break
                cambios = c_git if c_git else args.default_cambios
                delta_t = args.default_delta_t
                fuente = "git"
            else:
                cambios = args.default_cambios
                delta_t = args.default_delta_t
                fuente = "fijo"

        reportes.append(
            construir_reporte_archivo(
                m,
                mi_referencia=args.mi_referencia,
                cambios_anuales=cambios,
                delta_t_horas=delta_t,
                fuente_interes=fuente,
            )
        )

    if args.solo_config:
        reportes = [r for r in reportes if r.fuente_interes == "yaml"]

    # Ordenar por deuda descendente, como la tabla de prioridades del documento
    reportes.sort(key=lambda r: r.deuda_horas or 0, reverse=True)

    imprimir_tabla_consola(reportes)
    exportar_json(reportes, args.out_json)
    exportar_csv(reportes, args.out_csv)
    print(f"Exportado: {args.out_json} / {args.out_csv}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
