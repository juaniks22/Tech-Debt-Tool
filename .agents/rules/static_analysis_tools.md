# Herramientas de Análisis Estático (Go / Dart / Windows)

Reglas y consideraciones operativas aprendidas sobre las herramientas de análisis estático en este entorno:

## 1. gocloc (Conteo de Líneas de Código en Go / Dart)
- **Modo por archivo**: Siempre se debe pasar la bandera `--by-file` (o `/by-file`). Sin esta bandera, `gocloc` sólo genera totales agrupados por lenguaje y omite la lista detallada de archivos.
- **Formato del JSON**: En la lista `"files"`, la clave que contiene el path del archivo se denomina `"name"` (no `"filename"`).

## 2. dart_code_metrics / metrics (Dart / Flutter)
- **Deprecación y mensaje inicial**: La versión CLI libre de `dart_code_metrics` (`metrics.BAT`) emite un banner de texto de deprecación antes de entregar el payload JSON. Cualquier deserializador debe ubicar el primer carácter `{` antes de llamar a `json.loads`.
- **Estructura del payload**: Cada registro en `"records"` contiene la clave `"path"` con la ruta del archivo, y las métricas de complejidad ciclomática se encuentran desglosadas dentro de `"functions"` y `"classes"`.

## 3. Normalización de Rutas en Windows
- Tanto `gocloc` como `gocyclo` y `metrics` devuelven rutas utilizando separadores de barra invertida (`\`) en Windows.
- Para realizar comparaciones, búsquedas o matches con archivos de configuración (YAML/JSON), normalizar siempre utilizando `Path(ruta).as_posix()`.
