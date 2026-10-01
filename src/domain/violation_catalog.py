"""
Catálogo interno de reglas técnicas de violación y costos de remediación
para el modelo de deuda técnica SQALE (ISO/IEC 25010).
"""
from __future__ import annotations

from typing import List, Optional
from src.domain.architecture import ModuleMetrics, Violation
from src.domain.models import FileMetric


# Tiempos de remediación por defecto (en minutos)
TIEMPO_REMEDIACION = {
    "CC_ALTA": 30.0,          # Refactorizar o dividir función con alta complejidad
    "FUNCION_LARGA": 20.0,    # Extraer métodos / modularizar función extensa
    "ARCHIVO_LARGO": 60.0,    # Descomponer archivo masivo en múltiples unidades
    "IMPORT_CIRCULAR": 120.0, # Desacoplar módulos acoplados cíclicamente
    "ZONA_DOLOR": 180.0,      # Introducir interfaces y desacoplar módulo rígido
    "ZONA_INUTILIDAD": 90.0,  # Simplificar abstracciones innecesarias sin consumidores
}

# Umbrales configurables
UMBRAL_CC_POR_LENGUAJE = {
    "go": 7,
    "dart": 4,
}
UMBRAL_LOC_FUNCION = 50
UMBRAL_LOC_ARCHIVO = 300


def evaluar_violaciones_archivo(
    metrica: FileMetric,
    umbral_cc_override: Optional[int] = None,
    umbral_loc_archivo: int = UMBRAL_LOC_ARCHIVO,
) -> list[Violation]:
    """Evalúa violaciones a nivel de archivo individual."""
    violaciones: list[Violation] = []
    lenguaje = metrica.lenguaje.lower()
    umbral_cc = umbral_cc_override or UMBRAL_CC_POR_LENGUAJE.get(lenguaje, 10)

    # 1. Regla: Archivo demasiado largo
    if metrica.loc > umbral_loc_archivo:
        violaciones.append(
            Violation(
                regla="ARCHIVO_LARGO",
                categoria_sqale="Mantenibilidad",
                archivo=metrica.ruta,
                detalle=f"Archivo con {metrica.loc} LOC (umbral: {umbral_loc_archivo})",
                remediacion_minutos=TIEMPO_REMEDIACION["ARCHIVO_LARGO"],
            )
        )

    # 2. Regla: Complejidad ciclomática por función alta
    if metrica.complejidad_por_funcion:
        for idx, cc in enumerate(metrica.complejidad_por_funcion, 1):
            if cc > umbral_cc:
                violaciones.append(
                    Violation(
                        regla="CC_ALTA",
                        categoria_sqale="Mantenibilidad",
                        archivo=metrica.ruta,
                        detalle=f"Función #{idx} con CC={cc} (umbral {lenguaje}: {umbral_cc})",
                        remediacion_minutos=TIEMPO_REMEDIACION["CC_ALTA"],
                    )
                )
    elif metrica.complejidad_ciclomatica > umbral_cc:
        # Fallback si el analizador no reportó desglose por función
        violaciones.append(
            Violation(
                regla="CC_ALTA",
                categoria_sqale="Mantenibilidad",
                archivo=metrica.ruta,
                detalle=f"Complejidad total {metrica.complejidad_ciclomatica} supera umbral de {umbral_cc}",
                remediacion_minutos=TIEMPO_REMEDIACION["CC_ALTA"],
            )
        )

    return violaciones


def evaluar_violaciones_modulos(
    modulos: list[ModuleMetrics],
    ciclos_detectados: list[list[str]],
) -> list[Violation]:
    """Evalúa violaciones arquitectónicas a nivel de límites lógicos y acoplamientos."""
    violaciones: list[Violation] = []

    # 1. Imports circulares entre módulos
    for ciclo in ciclos_detectados:
        ciclo_str = " -> ".join(ciclo)
        violaciones.append(
            Violation(
                regla="IMPORT_CIRCULAR",
                categoria_sqale="Fiabilidad",
                archivo=ciclo[0] if ciclo else "arquitectura",
                detalle=f"Acoplamiento circular detectado: {ciclo_str}",
                remediacion_minutos=TIEMPO_REMEDIACION["IMPORT_CIRCULAR"],
            )
        )

    # 2. Zonas arquitectónicas de riesgo
    for m in modulos:
        if m.zona == "ZONA_DOLOR":
            violaciones.append(
                Violation(
                    regla="ZONA_DOLOR",
                    categoria_sqale="Mantenibilidad",
                    archivo=m.ruta,
                    detalle=f"Módulo '{m.nombre}' en Zona de Dolor (D={m.distancia_d:.2f}, I={m.inestabilidad:.2f}, A={m.abstraccion:.2f})",
                    remediacion_minutos=TIEMPO_REMEDIACION["ZONA_DOLOR"],
                )
            )
        elif m.zona == "ZONA_INUTILIDAD":
            violaciones.append(
                Violation(
                    regla="ZONA_INUTILIDAD",
                    categoria_sqale="Mantenibilidad",
                    archivo=m.ruta,
                    detalle=f"Módulo '{m.nombre}' en Zona de Inutilidad (D={m.distancia_d:.2f}, I={m.inestabilidad:.2f}, A={m.abstraccion:.2f})",
                    remediacion_minutos=TIEMPO_REMEDIACION["ZONA_INUTILIDAD"],
                )
            )

    return violaciones
