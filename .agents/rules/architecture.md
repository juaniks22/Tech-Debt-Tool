# Directrices de Arquitectura para Tech-Debt-Tool

El proyecto implementa **Arquitectura Hexagonal (Ports & Adapters)** combinada con el patrón **Strategy/Registry**. Todo nuevo desarrollo o refactorización debe respetar estas directrices:

## 1. Capas y Responsabilidades

### Dominio (`src/domain/`)
- **Modelos (`models.py`)**: Dataclasses (`FileMetric`, `DebtReport`, `FinancialParams`, `FrictionEstimate`).
- **Lógica Financiera (`calculator.py`)**: Fórmulas matemáticas y financieras puras de Índice de Mantenibilidad (MI), deuda técnica en horas, costo de reparación en USD, interés anual en USD, payback en años y ROI proyectado a 4 años.
- **Regla de oro**: Cero dependencias externas (`subprocess`, `git`, `yaml`, `sys`). Todo cálculo del dominio debe ser testeable sin I/O.

### Aplicación / Casos de Uso (`src/application/`)
- **Puertos (`ports.py`)**: Interfaces abstractas (`typing.Protocol` o `abc.ABC`):
  - `CodeAnalyzer`: Interfaz para analizadores de lenguajes (`name`, `supported_extensions`, `can_analyze`, `analyze`).
  - `FrictionProvider`: Interfaz para cálculo/estimación de cambios anuales y $\Delta t$.
  - `ReportExporter`: Interfaz para exportar reportes (Consola, JSON, CSV, Markdown).
- **Casos de uso (`analyze_use_case.py`)**: `AnalyzeRepositoryUseCase` orquesta la detección de lenguajes, ejecución de analizadores registrados, asociación con fricción estimada, cálculo de reportes financieros y despacho a exportadores.

### Infraestructura (`src/infrastructure/`)
- **Analizadores (`analyzers/`)**: Implementaciones concretas (`GoAnalyzer`, `DartAnalyzer`, y futuros como `PythonAnalyzer`). Se gestionan mediante un `AnalyzerRegistry`.
- **Fricción (`friction/`)**: `YamlFrictionProvider`, `GitCommitFrictionProvider`, `FixedDefaultFrictionProvider` y `CompositeFrictionProvider` (cadena de fallback: archivos sin deuda $MI \ge 20 \to 0$ fricción; luego YAML; luego Git; luego fijo).
- **Exportadores (`reporters/`)**: `ConsoleReporter`, `JsonReporter`, `CsvReporter`, `MarkdownReporter`.
- **Herramientas de Sistema (`tools/`)**: `ProcessRunner` para invocación segura de subprocess con encoding y resolución de PATH.

### Presentación / Entrada (`src/main.py`)
- Punto de entrada CLI y Composition Root (Inversión de Control).
- Debe mantener 100% de retrocompatibilidad con las banderas existentes (`--repo`, `--go-path`, `--dart-path`, `--solo-config`, `--metodo-estimacion`, etc.), habilitando además `--out-md` para exportar a Markdown.

### Convención de Imports
- Toda importación interna debe referenciar directamente a las capas canónicas (`src.domain`, `src.application`, `src.infrastructure`). La raíz de `src/` se mantiene limpia conteniendo únicamente `__init__.py`, `config.py`, `main.py` y los paquetes de capas.
