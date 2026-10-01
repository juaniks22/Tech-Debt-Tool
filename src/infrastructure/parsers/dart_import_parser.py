"""
Parser estático para archivos Dart (.dart).
Extrae sentencias import, clases abstractas, clases concretas y funciones extensas.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Set


RE_DART_IMPORT = re.compile(r"^\s*import\s+['\"]([^'\"]+)['\"]")
RE_ABSTRACT_CLASS = re.compile(r'^\s*abstract\s+(?:base\s+|interface\s+|final\s+)?class\s+([A-Z][a-zA-Z0-9_]*)')
RE_CONCRETE_CLASS = re.compile(r'^\s*(?:base\s+|final\s+|sealed\s+)?class\s+([A-Z][a-zA-Z0-9_]*)')
RE_DART_FUNC = re.compile(r'^\s*(?:[a-zA-Z0-9_<>,]+\s+)?([a-zA-Z0-9_]+)\s*\([^)]*\)\s*(?:async\s*)?\{')


class DartFileParseResult:
    def __init__(self) -> None:
        self.imports: set[str] = set()
        self.abstract_classes_count: int = 0
        self.concrete_classes_count: int = 0
        self.long_functions: list[tuple[str, int]] = []


def parse_dart_file(file_path: Path, max_func_loc: int = 50) -> DartFileParseResult:
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

    for line in lines:
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

        # Detección de funciones largas
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

    return result
