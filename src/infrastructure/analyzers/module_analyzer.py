"""
Analizador arquitectónico a nivel de límites lógicos (carpetas/módulos).
Aplica el principio de invariancia por volumen de archivos e imports,
y calcula Ca, Ce, Inestabilidad, Abstracción y Distancia D (Robert C. Martin).
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set, Tuple

from src.domain.architecture import ModuleMetrics, Violation
from src.domain.architecture_calculator import (
    calcular_abstraccion,
    calcular_distancia_d,
    calcular_inestabilidad,
    clasificar_zona,
)
from src.domain.violation_catalog import (
    TIEMPO_REMEDIACION,
    evaluar_violaciones_modulos,
)
from src.infrastructure.parsers.dart_import_parser import parse_dart_file
from src.infrastructure.parsers.go_import_parser import parse_go_file


def _detectar_modulos_en_directorio(base_dir: Path) -> dict[str, Path]:
    """
    Detecta carpetas de módulos dentro de un directorio base.
    Si existe 'internal/', inspecciona sus subcarpetas; si no, inspecciona
    las subcarpetas directas de base_dir (ignorando carpetas ocultas, tests, etc.).
    """
    modulos: dict[str, Path] = {}
    if not base_dir.is_dir():
        return modulos

    carpetas_a_escanear = [base_dir]
    internal_dir = base_dir / "internal"
    if internal_dir.is_dir():
        carpetas_a_escanear.append(internal_dir)

    for scan_dir in carpetas_a_escanear:
        for item in scan_dir.iterdir():
            if item.is_dir() and not item.name.startswith((".", "_", "test", "vendor")):
                if item.name == "internal":
                    continue
                nombre_modulo = item.name
                if nombre_modulo not in modulos:
                    modulos[nombre_modulo] = item

    return modulos


def _encontrar_ciclos_dfs(grafo: dict[str, set[str]]) -> list[list[str]]:
    """Detecta ciclos en el grafo de dependencias de módulos usando DFS."""
    ciclos: list[list[str]] = []
    visitados: set[str] = set()
    en_pila: list[str] = []

    def dfs(nodo: str) -> None:
        visitados.add(nodo)
        en_pila.append(nodo)

        for vecino in sorted(grafo.get(nodo, set())):
            if vecino not in visitados:
                dfs(vecino)
            elif vecino in en_pila:
                idx = en_pila.index(vecino)
                ciclo = en_pila[idx:] + [vecino]
                # Evitar duplicados equivalentes rotados
                if not any(set(ciclo) == set(c) for c in ciclos):
                    ciclos.append(ciclo)

        en_pila.pop()

    for n in sorted(grafo.keys()):
        if n not in visitados:
            dfs(n)

    return ciclos


class ModuleAnalyzer:
    """Analiza dependencias lógicas entre módulos de un repositorio."""

    def __init__(self, repo_path: Path, subpath_map: dict[str, str]) -> None:
        self.repo_path = repo_path
        self.subpath_map = subpath_map

    def analyze(self) -> tuple[list[ModuleMetrics], list[Violation], list[list[str]]]:
        modulos_detectados: dict[str, dict] = {}

        # 1. Escanear módulos para Go y Dart
        for lang, sub in self.subpath_map.items():
            base_dir = self.repo_path / sub if sub else self.repo_path
            carpetas = _detectar_modulos_en_directorio(base_dir)

            for mod_name, mod_path in carpetas.items():
                if mod_name not in modulos_detectados:
                    modulos_detectados[mod_name] = {
                        "path": mod_path,
                        "rel_path": str(mod_path.relative_to(self.repo_path)).replace("\\", "/"),
                        "lang": lang,
                        "files": [],
                        "na": 0,
                        "nc": 0,
                        "long_functions": [],
                        "raw_imports": set(),
                    }

        # 2. Recolectar archivos y parsear clases/interfaces/imports
        for mod_name, data in modulos_detectados.items():
            mod_path: Path = data["path"]
            lang = data["lang"]
            extension = ".go" if lang == "go" else ".dart"

            for file_path in mod_path.rglob(f"*{extension}"):
                if file_path.is_file():
                    data["files"].append(file_path)
                    if lang == "go":
                        parsed = parse_go_file(file_path)
                        data["na"] += parsed.interfaces_count
                        data["nc"] += parsed.interfaces_count + parsed.structs_count
                        data["raw_imports"].update(parsed.imports)
                        for f_name, loc in parsed.long_functions:
                            data["long_functions"].append((str(file_path.relative_to(self.repo_path)), f_name, loc))
                    elif lang == "dart":
                        parsed = parse_dart_file(file_path)
                        data["na"] += parsed.abstract_classes_count
                        data["nc"] += parsed.abstract_classes_count + parsed.concrete_classes_count
                        data["raw_imports"].update(parsed.imports)
                        for f_name, loc in parsed.long_functions:
                            data["long_functions"].append((str(file_path.relative_to(self.repo_path)), f_name, loc))

        # 3. Construir grafo de enlaces lógicos únicos entre módulos (Invarianza por volumen)
        grafo_eferente: dict[str, set[str]] = {m: set() for m in modulos_detectados}
        grafo_aferente: dict[str, set[str]] = {m: set() for m in modulos_detectados}

        todos_nombres_modulos = set(modulos_detectados.keys())

        for mod_origen, data in modulos_detectados.items():
            for imp in data["raw_imports"]:
                imp_norm = imp.replace("\\", "/").lower()
                for mod_destino in todos_nombres_modulos:
                    if mod_destino == mod_origen:
                        continue
                    # Si el import referencia al módulo destino
                    # ej: "github.com/.../internal/domain/user" o "package:app/domain/user.dart"
                    mod_pattern = f"/{mod_destino.lower()}"
                    if mod_pattern in imp_norm or imp_norm.endswith(mod_destino.lower()) or imp_norm.startswith(mod_destino.lower() + "/"):
                        # Se cuenta exactamente 1 enlace lógico
                        grafo_eferente[mod_origen].add(mod_destino)
                        grafo_aferente[mod_destino].add(mod_origen)

        # 4. Detectar ciclos
        ciclos = _encontrar_ciclos_dfs(grafo_eferente)

        # 5. Generar métricas de Martin por cada módulo
        metricas_modulos: list[ModuleMetrics] = []
        for mod_name, data in sorted(modulos_detectados.items()):
            ca = len(grafo_aferente[mod_name])
            ce = len(grafo_eferente[mod_name])
            inestabilidad = calcular_inestabilidad(ca, ce)
            abstraccion = calcular_abstraccion(data["na"], data["nc"])
            distancia_d = calcular_distancia_d(abstraccion, inestabilidad)
            zona = clasificar_zona(abstraccion, inestabilidad, distancia_d)

            m_metric = ModuleMetrics(
                nombre=mod_name,
                ruta=data["rel_path"],
                ca=ca,
                ce=ce,
                inestabilidad=inestabilidad,
                na=data["na"],
                nc=data["nc"],
                abstraccion=abstraccion,
                distancia_d=distancia_d,
                zona=zona,
                archivos=len(data["files"]),
                dependencias_in=sorted(grafo_aferente[mod_name]),
                dependencias_out=sorted(grafo_eferente[mod_name]),
            )
            metricas_modulos.append(m_metric)

        # 6. Violaciones arquitectónicas y de funciones largas
        violaciones_arquitectura = evaluar_violaciones_modulos(metricas_modulos, ciclos)

        # Violaciones por funciones largas detectadas
        for mod_name, data in modulos_detectados.items():
            for f_path, f_name, loc in data["long_functions"]:
                violaciones_arquitectura.append(
                    Violation(
                        regla="FUNCION_LARGA",
                        categoria_sqale="Mantenibilidad",
                        archivo=f_path,
                        detalle=f"Función '{f_name}' tiene {loc} LOC (umbral: 50)",
                        remediacion_minutos=TIEMPO_REMEDIACION["FUNCION_LARGA"],
                    )
                )

        return metricas_modulos, violaciones_arquitectura, ciclos
