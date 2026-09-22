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
        "--modelo",
        choices=["dinamico", "clasico"],
        default="dinamico",
        help="Modelo de cálculo: 'dinamico' (default, fricción elástica F(MI), MI=75) o 'clasico' (MI=20)",
    )
    parser.add_argument(
        "--mi-referencia",
        type=float,
        default=None,
        help="MI de referencia para calcular deuda (default: 75.0 en modo dinámico, 20.0 en modo clásico)",
    )
    parser.add_argument(
        "--team-experience",
        "--ef",
        type=float,
        default=0.0,
        help="Factor de experiencia del equipo EF (0=inexperto/6min/loc, 5=alto rendimiento/2min/loc. Default: 0.0)",
    )
    parser.add_argument(
        "--tcf",
        type=float,
        default=1.0,
        help="Technical Complexity Factor multiplicador de K (default: 1.0)",
    )
    parser.add_argument(
        "--tasa-exito",
        type=float,
        default=0.65,
        help="Tasa de éxito para calibración de ROI por riesgo (default: 0.65)",
    )
    parser.add_argument(
        "--tarifa-usd",
        type=float,
        default=30.0,
        help="Costo por hora de desarrollo en USD (default: 30.0)",
    )
    parser.add_argument(
        "--t-clean-backend",
        type=float,
        default=7.0,
        help="Horas base sobre código limpio para Backend (default: 7.0h)",
    )
    parser.add_argument(
        "--t-clean-frontend",
        type=float,
        default=4.0,
        help="Horas base sobre código limpio para Frontend (default: 4.0h)",
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
        default=None,
        help="Cambios anuales si no están en config ni en git (default: 10 en backend, 30 en frontend)",
    )
    parser.add_argument(
        "--default-delta-t",
        type=float,
        default=None,
        help="Delta T forzado en horas (si no se indica, en modo dinámico se calcula vía F(MI))",
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

    # Resolución de MI de referencia según modelo si no fue explícito
    if args.mi_referencia is not None:
        mi_ref = args.mi_referencia
    else:
        mi_ref = 75.0 if args.modelo == "dinamico" else 20.0

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
            modelo=args.modelo,
            t_clean_backend=args.t_clean_backend,
            t_clean_frontend=args.t_clean_frontend,
        )
        if args.metodo_estimacion == "git"
        else None
    )
    fixed_provider = FixedDefaultFrictionProvider(
        cambios_anuales=args.default_cambios,
        delta_t_horas=args.default_delta_t,
        modelo=args.modelo,
        t_clean_backend=args.t_clean_backend,
        t_clean_frontend=args.t_clean_frontend,
    )
    composite_provider = CompositeFrictionProvider(
        yaml_provider=yaml_provider,
        git_provider=git_provider,
        fixed_provider=fixed_provider,
        metodo_estimacion=args.metodo_estimacion,
    )

    # 3. Instanciar Parámetros y Caso de Uso
    if args.modelo == "clasico":
        params = FinancialParams.clasico(
            costo_hora_usd=args.tarifa_usd,
            mi_referencia_default=mi_ref,
            factor_correccion_k=0.01,
        )
    else:
        params = FinancialParams(
            modelo="dinamico",
            costo_hora_usd=args.tarifa_usd,
            mi_referencia_default=mi_ref,
            ef_experiencia=args.team_experience,
            tcf=args.tcf,
            tasa_exito_roi=args.tasa_exito,
            t_clean_backend=args.t_clean_backend,
            t_clean_frontend=args.t_clean_frontend,
        )

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
            mi_referencia=mi_ref,
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
