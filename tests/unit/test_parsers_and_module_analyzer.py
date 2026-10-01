"""
Tests unitarios para parsers de imports y analizador de módulos con reglas de límites lógicos.
"""
import tempfile
import unittest
from pathlib import Path

from src.infrastructure.analyzers.module_analyzer import ModuleAnalyzer
from src.infrastructure.parsers.dart_import_parser import parse_dart_file
from src.infrastructure.parsers.go_import_parser import parse_go_file


class TestParsersAndModuleAnalyzer(unittest.TestCase):
    def test_parse_go_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "sample.go"
            file_path.write_text(
                """package sample

import (
    "fmt"
    "github.com/myorg/myapp/internal/domain"
)

type Repository interface {
    Get(id int) error
}

type SqlRepo struct {
    db string
}

func LongFunc() {
"""
                + "\n".join([f"    x := {i}" for i in range(55)])
                + "\n}\n",
                encoding="utf-8",
            )

            res = parse_go_file(file_path)
            self.assertIn("github.com/myorg/myapp/internal/domain", res.imports)
            self.assertEqual(res.interfaces_count, 1)
            self.assertEqual(res.structs_count, 1)
            self.assertEqual(len(res.long_functions), 1)
            self.assertEqual(res.long_functions[0][0], "LongFunc")

    def test_parse_dart_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "sample.dart"
            file_path.write_text(
                """import 'package:app/domain/user_model.dart';
import 'package:flutter/material.dart';

abstract class AuthGateway {
  Future<void> login();
}

class FirebaseAuthGateway implements AuthGateway {
  Future<void> login() async {}
}
""",
                encoding="utf-8",
            )

            res = parse_dart_file(file_path)
            self.assertIn("package:app/domain/user_model.dart", res.imports)
            self.assertEqual(res.abstract_classes_count, 1)
            self.assertEqual(res.concrete_classes_count, 1)

    def test_invarianza_por_volumen_en_module_analyzer(self):
        """
        Regla de clase:
        Si la carpeta presentation contiene múltiples archivos y todos importan
        el dominio, el acoplamiento sigue contabilizándose como 1 enlace lógico.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            backend = root / "backend"
            domain_dir = backend / "domain"
            pres_dir = backend / "presentation"
            domain_dir.mkdir(parents=True)
            pres_dir.mkdir(parents=True)

            # Dominio tiene una interfaz (Na=1, Nc=1)
            (domain_dir / "user.go").write_text(
                """package domain
type UserRepository interface {
    Find(id int) error
}
""",
                encoding="utf-8",
            )

            # Presentation tiene 3 archivos que todos importan domain
            for i in range(3):
                (pres_dir / f"screen_{i}.go").write_text(
                    f"""package presentation
import "myapp/backend/domain"

type Screen{i} struct {{}}
""",
                    encoding="utf-8",
                )

            analyzer = ModuleAnalyzer(root, {"go": "backend"})
            modulos, violaciones, ciclos = analyzer.analyze()

            mod_map = {m.nombre: m for m in modulos}
            self.assertIn("domain", mod_map)
            self.assertIn("presentation", mod_map)

            # Presentation depende de domain: Ce=1, Ca=0 -> I=1.0
            pres_m = mod_map["presentation"]
            self.assertEqual(pres_m.ce, 1)
            self.assertEqual(pres_m.ca, 0)
            self.assertEqual(pres_m.inestabilidad, 1.0)
            self.assertEqual(pres_m.dependencias_out, ["domain"])

            # Domain es dependido por presentation: Ca=1, Ce=0 -> I=0.0
            dom_m = mod_map["domain"]
            self.assertEqual(dom_m.ca, 1)
            self.assertEqual(dom_m.ce, 0)
            self.assertEqual(dom_m.inestabilidad, 0.0)
            self.assertEqual(dom_m.abstraccion, 1.0)  # Na=1, Nc=1 -> A=1.0
            # Distancia D = |1.0 + 0.0 - 1| = 0.0 (Secuencia principal)
            self.assertEqual(dom_m.distancia_d, 0.0)
            self.assertEqual(dom_m.zona, "SECUENCIA_PRINCIPAL")


if __name__ == "__main__":
    unittest.main()
