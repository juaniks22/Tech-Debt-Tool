"""
Tests unitarios para parsers de imports y analizador de módulos con reglas de límites lógicos.
"""
import tempfile
import unittest
from pathlib import Path

from src.infrastructure.analyzers.module_analyzer import ModuleAnalyzer
from src.infrastructure.parsers.dart_import_parser import (
    es_archivo_generado_dart,
    parse_dart_file,
)
from src.infrastructure.parsers.go_import_parser import parse_go_file
from src.infrastructure.parsers.lcov_parser import (
    obtener_cobertura_para_archivo,
    parse_lcov_file,
)


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

    def test_es_archivo_generado_dart(self):
        self.assertTrue(es_archivo_generado_dart("user_provider.g.dart"))
        self.assertTrue(es_archivo_generado_dart("user_state.freezed.dart"))
        self.assertTrue(es_archivo_generado_dart("api_client.mocks.dart"))
        self.assertTrue(es_archivo_generado_dart(".dart_tool/package_config.json"))
        self.assertFalse(es_archivo_generado_dart("anotador_screen.dart"))
        self.assertFalse(es_archivo_generado_dart("lib/domain/models/partido.dart"))

    def test_parse_dart_build_method_oversized(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "large_screen.dart"
            body_statements = "\n".join([f"    final v{i} = {i};" for i in range(40)])
            file_path.write_text(
                f"""import 'package:flutter/material.dart';

class BigScreen extends StatelessWidget {{
  @override
  Widget build(
    BuildContext context,
  ) {{
{body_statements}
    return Container();
  }}
}}
""",
                encoding="utf-8",
            )
            res = parse_dart_file(file_path, max_build_loc=35)
            self.assertEqual(len(res.build_methods_oversized), 1)
            line, loc = res.build_methods_oversized[0]
            self.assertEqual(line, 5)
            self.assertGreater(loc, 35)

    def test_parse_lcov_file_y_match(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            lcov_path = Path(tmpdir) / "lcov.info"
            lcov_path.write_text(
                """TN:
SF:lib/features/anotador/anotador_controller.dart
DA:1,1
DA:2,1
DA:3,0
DA:4,1
LF:4
LH:3
end_of_record
SF:lib/features/anotador/tablero_view.dart
DA:1,0
DA:2,0
LF:2
LH:0
end_of_record
""",
                encoding="utf-8",
            )
            cov_map = parse_lcov_file(lcov_path)
            self.assertEqual(cov_map.get("lib/features/anotador/anotador_controller.dart"), 75.0)
            self.assertEqual(cov_map.get("lib/features/anotador/tablero_view.dart"), 0.0)

            # Match tolerante
            val = obtener_cobertura_para_archivo("frontend\\lib\\features\\anotador\\anotador_controller.dart", cov_map)
            self.assertEqual(val, 75.0)


if __name__ == "__main__":
    unittest.main()
