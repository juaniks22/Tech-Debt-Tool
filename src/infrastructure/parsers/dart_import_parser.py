"""
Parser estático para archivos Dart (.dart).
Extrae sentencias import, clases abstractas, clases concretas, funciones extensas
y métodos Widget build sobredimensionados en Flutter.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Set, Tuple


RE_DART_IMPORT = re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]")
RE_ABSTRACT_CLASS = re.compile(r'^\s*abstract\s+(?:base\s+|interface\s+|final\s+)?class\s+([A-Z][a-zA-Z0-9_]*)')
RE_CONCRETE_CLASS = re.compile(r'^\s*(?:base\s+|final\s+|sealed\s+)?class\s+([A-Z][a-zA-Z0-9_]*)')
RE_DART_FUNC = re.compile(r'^\s*(?:[a-zA-Z0-9_<>,]+\s+)?([a-zA-Z0-9_]+)\s*\([^)]*\)\s*(?:async\s*)?\{')
RE_BUILD_METHOD = re.compile(r'(?:^|\s)(?:Widget\s+)?build\s*\(')

DART_GENERATED_SUFFIXES = (
    ".g.dart",
    ".freezed.dart",
    ".mocks.dart",
    ".config.dart",
    ".gen.dart",
    ".gr.dart",
    ".reflectable.dart",
)


def es_archivo_generado_dart(path_str: str | Path) -> bool:
    """Verifica si un archivo o ruta corresponde a código autogenerado en Dart/Flutter."""
    norm = str(path_str).replace("\\", "/").lower()
    if any(norm.endswith(suffix) for suffix in DART_GENERATED_SUFFIXES):
        return True
    if "/.dart_tool/" in norm or norm.startswith(".dart_tool/"):
        return True
    return False


class DartFileParseResult:
    def __init__(self) -> None:
        self.imports: set[str] = set()
        self.abstract_classes_count: int = 0
        self.concrete_classes_count: int = 0
        self.long_functions: list[tuple[str, int]] = []
        self.build_methods_oversized: list[tuple[int, int]] = []  # (start_line, loc)


def parse_dart_file(
    file_path: Path, max_func_loc: int = 50, max_build_loc: int = 35
) -> DartFileParseResult:
    result = DartFileParseResult()
    if not file_path.is_file():
        return result

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return result

    lines = content.splitlines()

    current_func_name = None
    current_func_lines = 0
    brace_depth = 0

    in_build_signature = False
    in_build_body = False
    build_start_line = 0
    build_lines = 0
    build_brace_depth = 0

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()

        # Detección de import
        m_imp = RE_DART_IMPORT.match(stripped)
        if m_imp:
            result.imports.add(m_imp.group(1))

        # Detección de clases abstractas vs concretas
        if RE_ABSTRACT_CLASS.match(stripped):
            result.abstract_classes_count += 1
        elif RE_CONCRETE_CLASS.match(stripped):
            result.concrete_classes_count += 1

        # Detección de funciones largas generales
        if current_func_name is None:
            m_func = RE_DART_FUNC.match(stripped)
            if m_func and not stripped.startswith("class ") and not stripped.startswith("abstract "):
                current_func_name = m_func.group(1)
                current_func_lines = 0
                brace_depth = 0

        if current_func_name is not None:
            if stripped and not stripped.startswith("//"):
                current_func_lines += 1
            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0 and current_func_lines > 0:
                if current_func_lines > max_func_loc:
                    result.long_functions.append((current_func_name, current_func_lines))
                current_func_name = None
                current_func_lines = 0
                brace_depth = 0

        # Detección de métodos build sobredimensionados (Flutter)
        if not in_build_body and not in_build_signature:
            if RE_BUILD_METHOD.search(line):
                in_build_signature = True
                build_start_line = idx

        if in_build_signature and not in_build_body:
            if "{" in line:
                in_build_body = True
                in_build_signature = False
                build_brace_depth = line.count("{") - line.count("}")
                build_lines = 1 if stripped and not stripped.startswith("//") else 0
                if build_brace_depth <= 0:
                    in_build_body = False
                    build_lines = 0
        elif in_build_body:
            if stripped and not stripped.startswith("//"):
                build_lines += 1
            build_brace_depth += line.count("{") - line.count("}")
            if build_brace_depth <= 0:
                if build_lines > max_build_loc:
                    result.build_methods_oversized.append((build_start_line, build_lines))
                in_build_body = False
                build_lines = 0
                build_brace_depth = 0

    return result
