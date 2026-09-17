"""
Valida que las fórmulas del script reproduzcan EXACTAMENTE los números
que ya calcularon a mano en clase (documento de referencia), para los
3 archivos: cursos_screen.dart, academic_repo.go, course_handler.go.
"""
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.domain.calculator import (
    calcular_mi,
    construir_reporte_archivo,
    metrica_dart_desde_dcm,
    metrica_go_desde_raw,
)

MI_REF = 20.0


def aprox(a, b, tol=0.1):
    return abs(a - b) <= tol


def test_cursos_screen_dart():
    # MI ya viene calculado por dcm en el flujo real; acá lo pasamos tal
    # cual el documento (0.00) para validar el resto de la cadena.
    m = metrica_dart_desde_dcm("cursos_screen.dart", loc=2671, cc_total=383, mi_reportado=0.00)
    r = construir_reporte_archivo(m, MI_REF, cambios_anuales=24, delta_t_horas=5.0)

    assert aprox(r.mi, 0.00), r.mi
    assert aprox(r.deuda_horas, 534.20, tol=0.5), r.deuda_horas
    assert aprox(r.costo_reparacion_usd, 16026.00, tol=5), r.costo_reparacion_usd
    assert aprox(r.interes_anual_usd, 3600.00), r.interes_anual_usd
    assert aprox(r.payback_anios, 4.45, tol=0.05), r.payback_anios
    assert aprox(r.roi_4_anios_porc, -10.14, tol=0.2), r.roi_4_anios_porc
    print("OK cursos_screen.dart:", r)


def test_academic_repo_go():
    mi_calculado = calcular_mi(loc=422, complejidad_ciclomatica=68)
    assert aprox(mi_calculado, 2.48, tol=0.05), mi_calculado

    m = metrica_go_desde_raw("academic_repo.go", loc=422, complejidades_funciones=[68])
    r = construir_reporte_archivo(m, MI_REF, cambios_anuales=14, delta_t_horas=2.5)

    assert aprox(r.deuda_horas, 73.95, tol=0.5), r.deuda_horas
    assert aprox(r.costo_reparacion_usd, 2218.47, tol=5), r.costo_reparacion_usd
    assert aprox(r.interes_anual_usd, 1050.00), r.interes_anual_usd
    assert aprox(r.payback_anios, 2.11, tol=0.05), r.payback_anios
    assert aprox(r.roi_4_anios_porc, 89.32, tol=0.5), r.roi_4_anios_porc
    print("OK academic_repo.go:", r)


def test_course_handler_go():
    mi_calculado = calcular_mi(loc=338, complejidad_ciclomatica=38)
    assert aprox(mi_calculado, 9.76, tol=0.05), mi_calculado

    m = metrica_go_desde_raw("course_handler.go", loc=338, complejidades_funciones=[38])
    r = construir_reporte_archivo(m, MI_REF, cambios_anuales=10, delta_t_horas=2.0)

    assert aprox(r.deuda_horas, 34.62, tol=0.5), r.deuda_horas
    assert aprox(r.costo_reparacion_usd, 1038.68, tol=5), r.costo_reparacion_usd
    assert aprox(r.interes_anual_usd, 600.00), r.interes_anual_usd
    assert aprox(r.payback_anios, 1.73, tol=0.05), r.payback_anios
    assert aprox(r.roi_4_anios_porc, 131.06, tol=0.5), r.roi_4_anios_porc
    print("OK course_handler.go:", r)


def test_archivo_sin_config_de_interes():
    """Si no está en el YAML de intereses, se reportan métricas crudas
    pero SIN deuda financiera inventada."""
    m = metrica_go_desde_raw("archivo_sin_datos.go", loc=100, complejidades_funciones=[5])
    r = construir_reporte_archivo(m, MI_REF, cambios_anuales=None, delta_t_horas=None)
    assert r.tiene_datos_interes is False
    assert r.interes_anual_usd is None
    assert r.payback_anios is None
    assert r.roi_4_anios_porc is None
    # pero el MI/deuda/costo estructural sí se calculan igual
    assert r.deuda_horas is not None
    print("OK archivo sin config de interés:", r)


if __name__ == "__main__":
    test_cursos_screen_dart()
    test_academic_repo_go()
    test_course_handler_go()
    test_archivo_sin_config_de_interes()
    print("\n✅ Todos los tests pasaron - las fórmulas replican el documento de clase.")
