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

Por default busca código Go en la raíz del repo y Dart en `lib/`. Si tu
estructura es distinta:

```bash
python src/main.py --repo /ruta/al/repo --go-path backend --dart-path frontend/lib
```

Otras opciones útiles:

```bash
--skip-dart              # analizar solo Go
--skip-go                # analizar solo Dart
--mi-referencia 20        # MI de referencia para el cálculo de deuda (default 20)
--config otro.yaml         # usar otro archivo de intereses
--out-json reporte.json    # nombre del export JSON
--out-csv reporte.csv      # nombre del export CSV
```

### 3. Leer el reporte

Sale una tabla en consola con semáforo 🟢/🔴 según los umbrales dados
en clase (CC Dart ≤4, CC Go ≤10, MI ≥60%), y se exporta a
`reporte_deuda.json` / `reporte_deuda.csv` para llevar historial entre
corridas (por ejemplo, versionando el CSV y viendo cómo baja la deuda
sprint a sprint).

## Decisión pendiente (a propósito, no la tomé por vos)

La clase dio dos referencias distintas para MI:
- El documento de ejemplo usa `MI_referencia = 20` fijo para calcular deuda.
- La consigna dice "MI ≥60% es aceptable".

El script usa 20 por default (para no romper el ejemplo ya validado),
pero es un **parámetro** (`--mi-referencia`). Si el equipo decide que
debería variar por lenguaje o usar 60, ajustalo ahí — no está
hardcodeado.

Lo mismo con los umbrales de CC por lenguaje (Dart ≤4, Go ≤10): el
script los usa **solo para el semáforo visual**, no para alterar el
cálculo de deuda. Eso también quedó como decisión abierta tuya.

## Estructura

```
src/
  config.py           # constantes + carga del YAML de intereses
  tool_runner.py       # chequeo/instalación/ejecución de gocloc, gocyclo, dcm
  metrics.py            # modelo de métricas crudas + fórmula de MI para Go
  debt_calculator.py    # fórmulas de deuda/costo/interés/payback/ROI
  report.py              # tabla consola + export CSV/JSON
  main.py                 # CLI
tests/
  test_contra_documento_clase.py   # valida contra los números exactos de clase
  test_reporte_end_to_end.py        # prueba el reporte completo simulado
```

## Nota sobre el parser de `dcm`

El parseo del JSON de `dcm` en `tool_runner.py`/`main.py` está basado
en el formato documentado (`records[].metrics`), pero las versiones de
`dart_code_metrics` cambiaron su output entre releases. La primera vez
que lo corras, si tira error de parseo, pegame el JSON crudo que
devuelve `dcm analyze lib --reporter=json` y ajusto el parser al toque.
