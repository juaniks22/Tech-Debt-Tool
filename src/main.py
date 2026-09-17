#!/usr/bin/env python3
"""
Punto de entrada CLI y Composition Root para Tech-Debt-Tool.
Orquesta la inyección de dependencias siguiendo la Arquitectura Hexagonal (Ports & Adapters).

Uso típico:
    python src/main.py --repo /ruta/al/repo --init-config
    python src/main.py --repo /ruta/al/repo
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Asegurar encoding UTF-8 en consola Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Asegurar sys.path
_repo_root = str(Path(__file__).resolve().parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from src.application.analyze_use_case import AnalyzeRepositoryUseCase
from src.config import (
    DEFAULT_CAMBIOS_ANUALES,
    DEFAULT_DELTA_T_HORAS,
    MI_REFERENCIA_DEFAULT,
    generar_config_ejemplo,
)
from src.domain.models import FinancialParams
from src.infrastructure.analyzers.dart_analyzer import DartAnalyzer
from src.infrastructure.analyzers.go_analyzer import GoAnalyzer
from src.infrastructure.analyzers.registry import AnalyzerRegistry
from src.infrastructure.friction.composite_provider import CompositeFrictionProvider
from src.infrastructure.friction.fixed_provider import FixedDefaultFrictionProvider
from src.infrastructure.friction.git_provider import GitCommitFrictionProvider
from src.infrastructure.friction.yaml_provider import YamlFrictionProvider
from src.infrastructure.reporters.console_reporter import ConsoleReporter
from src.infrastructure.reporters.file_reporters import CsvReporter, JsonReporter
from src.infrastructure.reporters.markdown_reporter import MarkdownReporter
from src.infrastructure.tools.process_runner import HerramientaFaltanteError


def construir_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Análisis técnico y financiero de deuda técnica (Arquitectura Hexagonal)"
    )
    parser.add_argument("--repo", type=Path, help="Ruta a la raíz del repositorio a analizar")
    parser.add_argument("--go-path", default=".", help="Subcarpeta con código Go (default: raíz)")
    parser.add_argument("--dart-path", default="lib", help="Subcarpeta con código Dart (default: lib)")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("intereses.yaml"),
        help="Archivo YAML con estimaciones humanas de cambios_anuales/delta_t por archivo",
    )
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Genera una plantilla de configuración de intereses.yaml y sale",
    )
    parser.add_argument(
        "--mi-referencia",
        type=float,
        default=MI_REFERENCIA_DEFAULT,
        help=f"MI de referencia para calcular deuda (default: {MI_REFERENCIA_DEFAULT})",
    )
    parser.add_argument(
        "--solo-config",
        action="store_true",
        help="Mostrar únicamente los archivos que tengan estimaciones en el archivo de configuración",
    )
    parser.add_argument(
        "--metodo-estimacion",
        choices=["git", "fijo"],
        default="git",
        help="Método de estimación para archivos con deuda sin config: 'git' (default, cuenta commits) o 'fijo'",
    )
    parser.add_argument(
        "--default-cambios",
        type=int,
        default=DEFAULT_CAMBIOS_ANUALES,
        help=f"Cambios anuales fijos si no están en config ni en git (default: {DEFAULT_CAMBIOS_ANUALES})",
    )
    parser.add_argument(
        "--default-delta-t",
        type=float,
        default=DEFAULT_DELTA_T_HORAS,
        help=f"Delta T en horas por cambio para archivos con deuda sin config (default: {DEFAULT_DELTA_T_HORAS}h)",
    )
    parser.add_argument("--out-json", type=Path, default=Path("reporte_deuda.json"), help="Ruta de exportación JSON")
    parser.add_argument("--out-csv", type=Path, default=Path("reporte_deuda.csv"), help="Ruta de exportación CSV")
    parser.add_argument("--out-md", type=Path, default=None, help="Ruta de exportación Markdown (opcional)")
    parser.add_argument("--skip-go", action="store_true", help="No analizar archivos Go")
    parser.add_argument("--skip-dart", action="store_true", help="No analizar archivos Dart")
    return parser


def main() -> int:
    parser = construir_cli_parser()
    args = parser.parse_args()

    if args.init_config:
        generar_config_ejemplo(args.config)
        return 0

    if not args.repo:
        parser.error("--repo es obligatorio (o usá --init-config primero)")

    if not args.repo.exists():
        print(f"Error: no existe la ruta {args.repo}", file=sys.stderr)
        return 1

    # Auto-detección de subcarpetas (ej. SGA-practicas)
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

    # 1. Configurar registro de analizadores (Strategy)
    registry = AnalyzerRegistry()
    if not args.skip_go:
        registry.register(GoAnalyzer())
    if not args.skip_dart:
        registry.register(DartAnalyzer())

    active_analyzers = registry.get_all()

    # 2. Configurar proveedores de fricción (Composite / Chain of Responsibility)
    yaml_provider = YamlFrictionProvider(args.config)
    git_provider = (
        GitCommitFrictionProvider(
            repo_path=args.repo,
            default_delta_t_horas=args.default_delta_t,
            default_cambios=args.default_cambios,
        )
        if args.metodo_estimacion == "git"
        else None
    )
    fixed_provider = FixedDefaultFrictionProvider(
        cambios_anuales=args.default_cambios,
        delta_t_horas=args.default_delta_t,
    )
    composite_provider = CompositeFrictionProvider(
        yaml_provider=yaml_provider,
        git_provider=git_provider,
        fixed_provider=fixed_provider,
        metodo_estimacion=args.metodo_estimacion,
    )

    # 3. Instanciar Caso de Uso
    params = FinancialParams(mi_referencia_default=args.mi_referencia)
    use_case = AnalyzeRepositoryUseCase(
        analyzers=active_analyzers,
        friction_provider=composite_provider,
        params=params,
    )

    subpaths = {"go": go_path, "dart": dart_path}

    try:
        summary = use_case.execute(
            repo_path=args.repo,
            subpath_map=subpaths,
            solo_config=args.solo_config,
            mi_referencia=args.mi_referencia,
        )
    except HerramientaFaltanteError as e:
        print(f"\nError de setup de herramienta externa: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"\nError durante el análisis: {e}", file=sys.stderr)
        return 1

    # 4. Despachar a exportadores
    ConsoleReporter().export(summary)
    JsonReporter().export(summary, args.out_json)
    CsvReporter().export(summary, args.out_csv)
    print(f"Exportado: {args.out_json} / {args.out_csv}", file=sys.stderr)

    if args.out_md:
        MarkdownReporter().export(summary, args.out_md)
        print(f"Exportado Markdown: {args.out_md}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
