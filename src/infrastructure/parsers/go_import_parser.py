"""
Parser estático para archivos Go (.go).
Extrae sentencias import, interfaces (abstractas), structs (concretas) y funciones largas.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Set


RE_SINGLE_IMPORT = re.compile(r'^\s*import\s+(?:[a-zA-Z0-9_]+\s+)?"([^"]+)"')
RE_IMPORT_BLOCK_START = re.compile(r'^\s*import\s*\(')
RE_IMPORT_LINE_IN_BLOCK = re.compile(r'^\s*(?:[a-zA-Z0-9_.]+\s+)?"([^"]+)"')
RE_INTERFACE = re.compile(r'^\s*type\s+([A-Z][a-zA-Z0-9_]*)\s+interface\s*\{')
RE_STRUCT = re.compile(r'^\s*type\s+([A-Z][a-zA-Z0-9_]*)\s+struct\s*\{')
RE_FUNC_START = re.compile(r'^\s*func\s+(?:\([^)]+\)\s+)?([a-zA-Z0-9_]+)\s*\(')


class GoFileParseResult:
    def __init__(self) -> None:
        self.imports: set[str] = set()
        self.interfaces_count: int = 0
        self.structs_count: int = 0
        self.long_functions: list[tuple[str, int]] = []  # (func_name, loc)


def parse_go_file(file_path: Path, max_func_loc: int = 50) -> GoFileParseResult:
    result = GoFileParseResult()
    if not file_path.is_file():
        return result

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return result

    lines = content.splitlines()
    in_import_block = False

    current_func_name = None
    current_func_lines = 0
    brace_depth = 0

    for line in lines:
        stripped = line.strip()

        # Manejo de bloque import (...)
        if RE_IMPORT_BLOCK_START.match(stripped):
            in_import_block = True
            continue

        if in_import_block:
            if stripped.startswith(")"):
                in_import_block = False
            else:
                m = RE_IMPORT_LINE_IN_BLOCK.search(stripped)
                if m:
                    result.imports.add(m.group(1))
            continue

        # Import de línea simple: import "..."
        m_single = RE_SINGLE_IMPORT.match(stripped)
        if m_single:
            result.imports.add(m_single.group(1))

        # Detección de interfaces y structs
        if RE_INTERFACE.match(stripped):
            result.interfaces_count += 1
        elif RE_STRUCT.match(stripped):
            result.structs_count += 1

        # Detección de longitud de funciones
        m_func = RE_FUNC_START.match(stripped)
        if m_func and current_func_name is None:
            current_func_name = m_func.group(1)
            current_func_lines = 0
            brace_depth = 0

        if current_func_name is not None:
            # Contar líneas no vacías y no comentarios
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
