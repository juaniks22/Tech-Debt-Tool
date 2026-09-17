# Herramienta de Deuda Técnica — SGA-practicas

Analiza el repo con herramientas estándar de la industria y calcula
Índice de Mantenibilidad, deuda técnica, costo de reparación, interés
anual, payback y ROI — replicando el cálculo validado en clase para
`course_handler.go`, `academic_repo.go` y `cursos_screen.dart`.

## Qué usa por debajo

| Métrica | Go | Dart |
|---|---|---|
| LOC | [`gocloc`](https://github.com/hhatto/gocloc) | [`dcm`](https://pub.dev/packages/dart_code_metrics) |
| Complejidad ciclomática | [`gocyclo`](https://github.com/fzipp/gocyclo) | `dcm` |
| Índice de Mantenibilidad | calculado localmente (misma fórmula que en clase) | reportado directo por `dcm` |

El script **verifica e instala automáticamente** `gocloc`, `gocyclo` y
`dcm` si no los tenés (necesita Go y/o Dart SDK instalados para eso).

## Requisitos previos

- Python 3.10+
- Go SDK (si vas a analizar archivos `.go`) — https://go.dev/dl/
- Dart SDK (si vas a analizar archivos `.dart`) — https://dart.dev/get-dart

## Instalación

```bash
cd tech-debt-tool
pip install -r requirements.txt
```

## Uso

### 1. Generar la plantilla de configuración

Los datos de **cambios anuales** y **Δt** (tiempo extra por mala
calidad) son estimaciones humanas del equipo — no algo que el código
pueda calcular solo. Generá la plantilla:

```bash
python src/main.py --init-config
```

Esto crea `intereses.yaml`. Completalo con los datos reales, por
ejemplo:

```yaml
archivos:
  - ruta: "internal/repository/academic_repo.go"
    cambios_anuales: 14
    delta_t_horas: 2.5
  - ruta: "internal/handler/course_handler.go"
    cambios_anuales: 10
    delta_t_horas: 2.0
  - ruta: "lib/screens/cursos_screen.dart"
    cambios_anuales: 24
    delta_t_horas: 5.0
```

**Importante:** la `ruta` tiene que coincidir con la que reportan
`gocloc`/`dcm` (relativa a la raíz del repo). Corré el script una vez
sin config para ver qué rutas te tira, y después completá el YAML.

### 2. Correr el análisis

```bash
python src/main.py --repo "C:\Users\juani\OneDrive\Documentos\PROJECTS\SGA-practicas"
```

El script **detecta automáticamente** si el repo tiene subcarpetas `backend/` (Go) y `frontend/lib/` (Dart/Flutter) como en `SGA-practicas`. Si tu estructura es distinta, podés especificarlas a mano:

```bash
python src/main.py --repo /ruta/al/repo --go-path backend --dart-path frontend/lib
```

Otras opciones útiles:

```bash
--solo-config                 # muestra únicamente los archivos configurados en intereses.yaml
--metodo-estimacion [git|fijo]# método para archivos sin config (default: git, cuenta commits en el último año)
--default-cambios 10          # cambios anuales fijos si no están en config ni en git (default: 10)
--default-delta-t 2.0         # horas de fricción por cambio para archivos con deuda (default: 2.0h)
--skip-dart                   # analizar solo Go
--skip-go                     # analizar solo Dart
--mi-referencia 20.0          # MI de referencia para calcular deuda (default: 20.0 para gate Aprobado; 60.0 para Excelencia)
--config otro.yaml            # usar otro archivo de intereses
--out-json reporte.json       # nombre del export JSON
--out-csv reporte.csv         # nombre del export CSV
--out-md reporte.md           # nombre del export Markdown (ideal para PRs / CI)
```

### 3. Leer el reporte

Sale una tabla en consola con semáforo de 3 niveles según el estado de mantenibilidad:
- 🔴 **Crítico ($MI < 20$):** No aprobado, alta deuda y fricción.
- 🟢 **Aprobado ($20 \le MI < 60$):** Calidad mínima operativa cumplida.
- 🟢 **Excelente ($MI \ge 60$):** Arquitectura limpia y modular.

Y se exporta a `reporte_deuda.json` / `reporte_deuda.csv` / `reporte_deuda.md` con **todas las métricas financieras calculadas para cada archivo** (`interes_anual_usd`, `payback_anios`, `roi_4_anios_porc` y `fuente_interes`).

## Estimación de Fricción e Interés Financiero

1. **Archivos en `intereses.yaml`:** Usan las estimaciones humanas provistas por el equipo (máxima prioridad).
2. **Archivos limpios/aprobados ($MI \ge 20$):** Tienen deuda $0\text{ h}$, costo $\$0$, e interés anual $\$0$ (no sufren fricción por mala calidad).
3. **Archivos con deuda sin config explícita:**
   - **Por defecto (`--metodo-estimacion git`):** El script consulta el historial de commits del último año en Git para determinar cuántas veces se tocó el archivo, y aplica $\Delta t$ estimado (default $2.0\text{ h}$).
   - **Opción fija (`--metodo-estimacion fijo`):** Utiliza valores fijos configurables (`--default-cambios 10 --default-delta-t 2.0`).

## Estructura (Arquitectura Hexagonal / Ports & Adapters)

```
src/
  domain/                      # Dominio puro (cero dependencias externas)
    models.py                  # Dataclasses (FileMetric, DebtReport, FinancialParams)
    calculator.py              # Fórmulas de MI, deuda, costo, interés, payback, ROI
  application/                 # Casos de uso y puertos
    ports.py                   # Protocolos (CodeAnalyzer, FrictionProvider, ReportExporter)
    analyze_use_case.py        # Orquestación del análisis y agregación global
  infrastructure/              # Adaptadores de infraestructura
    analyzers/                 # GoAnalyzer, DartAnalyzer, AnalyzerRegistry (Strategy)
    friction/                  # YamlProvider, GitProvider, FixedProvider, CompositeProvider
    reporters/                 # ConsoleReporter, JsonReporter, CsvReporter, MarkdownReporter
    tools/                     # ProcessRunner y verificación de binarios
  config.py                    # Constantes y parámetros globales
  main.py                      # CLI y Composition Root
tests/
  unit/                        # Tests unitarios puros (dominio, use case, markdown)
  test_contra_documento_clase.py # Valida contra los números exactos de clase
  test_reporte_end_to_end.py   # Prueba el reporte completo simulado
```

## Nota sobre el parser de `dcm`

El parseo del JSON de `dcm` en `infrastructure/analyzers/dart_analyzer.py` está basado
en el formato documentado (`records[].metrics`), pero las versiones de
`dart_code_metrics` cambiaron su output entre releases. La primera vez
que lo corras, si tira error de parseo, pegame el JSON crudo que
devuelve `dcm analyze lib --reporter=json` y ajusto el parser al toque.
