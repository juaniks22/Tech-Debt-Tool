import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.domain.calculator import (
    construir_reporte_archivo,
    metrica_dart_desde_dcm,
    metrica_go_desde_raw,
)
from src.infrastructure.reporters.console_reporter import ConsoleReporter
from src.infrastructure.reporters.file_reporters import CsvReporter, JsonReporter

MI_REF = 20.0

metricas = [
    metrica_dart_desde_dcm("lib/screens/cursos_screen.dart", 2671, 383, 0.00),
    metrica_go_desde_raw("internal/repo/academic_repo.go", 422, [68]),
    metrica_go_desde_raw("internal/handler/course_handler.go", 338, [38]),
    metrica_go_desde_raw("internal/handler/sin_datos.go", 100, [3]),  # sin config -> debe avisar
]

intereses = {
    "lib/screens/cursos_screen.dart": (24, 5.0),
    "internal/repo/academic_repo.go": (14, 2.5),
    "internal/handler/course_handler.go": (10, 2.0),
}

reportes = []
for m in metricas:
    datos = intereses.get(m.ruta)
    cambios, delta_t = datos if datos else (None, None)
    reportes.append(construir_reporte_archivo(m, MI_REF, cambios, delta_t))

reportes.sort(key=lambda r: r.deuda_horas or 0, reverse=True)

ConsoleReporter.imprimir_tabla(reportes)

out_dir = Path(__file__).parent / "_out"
out_dir.mkdir(exist_ok=True)
JsonReporter.exportar(reportes, out_dir / "reporte_deuda.json")
CsvReporter.exportar(reportes, out_dir / "reporte_deuda.csv")
print(f"Exportado a {out_dir}/")
