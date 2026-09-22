# Tech-Debt-Tool — Referencia de Fórmulas y Modelo de Cálculo

> **Propósito de este documento:** proveer contexto matemático completo para agentes de IA que trabajen sobre este repositorio. Describe las fórmulas exactas que implementa [`src/domain/calculator.py`](src/domain/calculator.py), los parámetros configurables y el significado de cada campo del reporte.

---

## Índice

1. [Modelo Activo por Defecto: Dinámico vs Clásico](#1-modelo-activo-por-defecto-dinámico-vs-clásico)
2. [Métricas de Código Fuente (Entradas)](#2-métricas-de-código-fuente-entradas)
3. [Índice de Mantenibilidad (MI)](#3-índice-de-mantenibilidad-mi)
4. [Factor de Velocidad Base K Dinámico](#4-factor-de-velocidad-base-k-dinámico)
5. [Deuda Técnica en Horas](#5-deuda-técnica-en-horas)
6. [Modelo de Fricción Operativa F(MI)](#6-modelo-de-fricción-operativa-fmi)
7. [Interés Anual por Fricción](#7-interés-anual-por-fricción)
8. [Costo de Reparación (Capital de la Deuda)](#8-costo-de-reparación-capital-de-la-deuda)
9. [Período de Recuperación (Payback)](#9-período-de-recuperación-payback)
10. [Retorno de Inversión (ROI Nominal y Ajustado)](#10-retorno-de-inversión-roi-nominal-y-ajustado)
11. [Semáforo de Estado por MI](#11-semáforo-de-estado-por-mi)
12. [Baselines por Capa Arquitectural](#12-baselines-por-capa-arquitectural)
13. [Cadena de Resolución de Fricción](#13-cadena-de-resolución-de-fricción)
14. [Diccionario de Campos del Reporte (CSV / JSON)](#14-diccionario-de-campos-del-reporte-csv--json)
15. [Parámetros Configurables](#15-parámetros-configurables)
16. [Caso de Estudio Numérico (Golang, Pág. 19-20)](#16-caso-de-estudio-numérico-golang-pág-19-20)

---

## 1. Modelo Activo por Defecto: Dinámico vs Clásico

La herramienta soporta dos modos de cálculo seleccionables con `--modelo`:

| Parámetro | Modelo **Dinámico** (default) | Modelo **Clásico** |
|---|---|---|
| `--modelo` | `dinamico` | `clasico` |
| MI de referencia default | `75.0` | `20.0` |
| Estado Crítico | $MI < 50$ | $MI < 20$ |
| Estado Excelente | $MI \ge 75$ | $MI \ge 60$ |
| Factor K | Calculado con $EF$ y $TCF$ | Fijo en `0.01` |
| $\Delta t$ | Calculado vía $F(MI)$ si no viene del YAML | Siempre manual / YAML / Git |
| ROI Ajustado por riesgo | ✅ Sí (65%) | ❌ No |
| Factor de fricción $F(MI)$ | ✅ Calculado | ❌ No aplica |

> **Retrocompatibilidad:** Para reproducir exactamente los cálculos del documento de clase, usar `--modelo clasico --mi-referencia 20.0`. Los tests en `test_contra_documento_clase.py` validan esto automáticamente.

---

## 2. Métricas de Código Fuente (Entradas)

| Variable | Símbolo | Descripción | Fuente |
|---|---|---|---|
| Líneas de código | $LOC$ | Líneas efectivas (sin blancos ni comentarios) | `gocloc` (Go), `dcm` (Dart) |
| Complejidad ciclomática | $CC$ (o $G$) | Número de caminos de flujo independientes en el archivo | `gocyclo` (Go), `dcm` (Dart) |

---

## 3. Índice de Mantenibilidad (MI)

Fórmula calibrada por Microsoft / Visual Studio (aproximación sin Volumen de Halstead):

$$MI = \max\left(0,\ \frac{171 - 25 \cdot \ln(LOC) - 0.23 \cdot CC}{171} \cdot 100\right)$$

- **Fuente:** [`calcular_mi(loc, cc)`](src/domain/calculator.py) — calculado localmente para Go; reportado directamente por `dcm` para Dart.
- **Caso borde:** si $LOC \le 0$, se devuelve $MI = 100$ (no hay código que mantener).
- **Escala:** $[0, 100]$ — a mayor valor, más mantenible.

---

## 4. Factor de Velocidad Base K Dinámico

$$K_{\text{dinámico}} = \left[ 0.01 - \left(\frac{EF}{5}\right) \cdot 0.0067 \right] \cdot TCF$$

| Valor de $EF$ | Descripción | $K$ resultante | Tiempo por línea |
|---|---|---|---|
| `0.0` (default) | Equipo inexperto | `0.01` | 6 min/línea |
| `2.5` | Equipo promedio | `0.00665` | ~4 min/línea |
| `5.0` | Alto rendimiento | `0.0033` | 2 min/línea |

- **Parámetros CLI:** `--team-experience EF` (alias `--ef`), `--tcf TCF`
- **Fuente:** [`calcular_k_dinamico(ef, tcf)`](src/domain/calculator.py)
- En **modelo clásico**, $K$ es siempre `0.01` fijo.

---

## 5. Deuda Técnica en Horas

$$\text{Deuda (h)} = \max\left(0,\ (MI_{\text{umbral}} - MI) \cdot LOC \cdot K\right)$$

- $MI_{\text{umbral}}$ es el MI de referencia configurado (default `75.0` en modo dinámico, `20.0` en modo clásico).
- $K$ es el factor de velocidad base (dinámico o fijo según modelo).
- Interpreta cuántas horas de trabajo tomaría llevar el código desde su estado actual $MI$ hasta el umbral de calidad $MI_{\text{umbral}}$.
- **Fuente:** [`calcular_deuda_horas(mi, loc, mi_referencia, factor_k)`](src/domain/calculator.py)

---

## 6. Modelo de Fricción Operativa F(MI)

> **Solo en modo dinámico.** Basado en la evidencia empírica de Capers Jones: desarrollar en código con $MI = 0$ cuesta hasta **4 veces más** que en código limpio.

### Factor de Fricción

$$F(MI) = 1 + \left(\frac{MI_{\text{umbral}} - MI}{MI_{\text{umbral}}}\right)^2 \cdot C$$

Donde $C = 3$ es el único valor que satisface simultáneamente:
- $F(MI_{\text{umbral}}) = 1.0$ → Código limpio / Eficiencia óptima
- $F(0) = 1 + (1)^2 \cdot 3 = 4.0$ → Techo de pérdida de productividad (Capers Jones)

### Tiempo de Intervención Real

$$T_{\text{real}} = T_{\text{clean}} \cdot F(MI)$$

### Fricción Pura por Cambio ($\Delta t$)

$$\Delta t = T_{\text{real}} - T_{\text{clean}} = T_{\text{clean}} \cdot (F(MI) - 1)$$

- $T_{\text{clean}}$ es el tiempo de intervención en código limpio ($MI = MI_{\text{umbral}}$).
- Puede ser provisto en `intereses.yaml` (campo `t_clean_horas`) o tomado del baseline de capa.
- **Fuente:** [`calcular_factor_friccion(mi, mi_umbral, c)`](src/domain/calculator.py), [`calcular_friccion_operativa(mi, t_clean, mi_umbral, c)`](src/domain/calculator.py)

### Relación de Brecha Indexada (Índice de Fricción)

$$\text{Brecha Indexada} = \frac{MI_{\text{umbral}} - MI_{\text{actual}}}{MI_{\text{umbral}}}$$

Esta es la raíz de la fórmula de fricción. Mide la distancia proporcional entre el estado actual del código y el objetivo de calidad, normalizada al umbral.

---

## 7. Interés Anual por Fricción

$$\text{Interés Anual} = N \cdot \Delta t \cdot \text{Tarifa}$$

- $N$ = número de intervenciones anuales al archivo (`cambios_anuales`)
- $\Delta t$ = fricción pura por cambio en horas (derivada de $F(MI)$ o provista en YAML)
- $\text{Tarifa}$ = costo por hora de desarrollo en USD (`--tarifa-usd`, default `$30.00`)
- **Fuente:** [`calcular_interes_anual(cambios_anuales, delta_t_horas, costo_hora_usd)`](src/domain/calculator.py)

---

## 8. Costo de Reparación (Capital de la Deuda)

$$\text{Costo de Reparación} = \text{Deuda (h)} \cdot \text{Tarifa}$$

Es el capital a invertir para llevar el archivo desde $MI_{\text{actual}}$ hasta $MI_{\text{umbral}}$.

- **Fuente:** [`calcular_costo_reparacion(deuda_horas, costo_hora_usd)`](src/domain/calculator.py)

---

## 9. Período de Recuperación (Payback)

$$\text{Payback (años)} = \frac{\text{Costo de Reparación}}{\text{Interés Anual}}$$

Indica en cuántos años la inversión en refactorización se paga sola con el ahorro acumulado en fricción.

- Si $\text{Interés Anual} = 0$ y $\text{Costo} > 0$ → `None` (nunca se recupera)
- **Fuente:** [`calcular_payback_anios(costo_reparacion, interes_anual)`](src/domain/calculator.py)

---

## 10. Retorno de Inversión (ROI Nominal y Ajustado)

### ROI Nominal (4 años)

$$ROI_{\text{nominal}} = 100 \cdot \frac{(\text{Interés Anual} \cdot \text{Años}) - \text{Costo de Reparación}}{\text{Costo de Reparación}}$$

- Proyección a `anios_proyeccion` años (default: **4 años**).
- Campo: `roi_4_anios_porc`
- **Fuente:** [`calcular_roi_4_anios(costo_reparacion, interes_anual, anios)`](src/domain/calculator.py)

### ROI Ajustado por Riesgo (solo modelo dinámico)

$$ROI_{\text{ajustado}} = 100 \cdot \frac{(\text{Interés Anual} \cdot \text{Años} \cdot p_{\text{éxito}}) - \text{Costo de Reparación}}{\text{Costo de Reparación}}$$

- $p_{\text{éxito}} = 0.65$ por defecto: probabilidad empírica de éxito de proyectos de **refactorización incremental** (estudios de mercado de la industria de software).
- Para **reescrituras totales** la tasa cae a ~21%.
- Campo: `roi_ajustado_porc`
- **Parámetro CLI:** `--tasa-exito 0.65`
- **Fuente:** [`calcular_roi_ajustado_riesgo(costo_reparacion, interes_anual, anios, tasa_exito)`](src/domain/calculator.py)

---

## 11. Semáforo de Estado por MI

### Modelo Dinámico (default)

| Estado | Rango MI | Ícono | Fricción típica |
|---|---|---|---|
| **EXCELENTE** | $MI \ge 75$ | 🟢 | $F(MI) = 1.0\text{x}$ (sin fricción) |
| **APROBADO** | $50 \le MI < 75$ | 🟡 | $1.0\text{x} < F(MI) \le 1.33\text{x}$ |
| **CRITICO** | $MI < 50$ | 🔴 | $F(MI) > 1.33\text{x}$ hasta $4.0\text{x}$ |

### Modelo Clásico (--modelo clasico)

| Estado | Rango MI | Fuente |
|---|---|---|
| **EXCELENTE** | $MI \ge 60$ | Microsoft Visual Studio |
| **APROBADO** | $20 \le MI < 60$ | Microsoft Visual Studio |
| **CRITICO** | $MI < 20$ | Microsoft Visual Studio |

---

## 12. Baselines por Capa Arquitectural

En modo dinámico, si no hay un $\Delta t$ explícito, la herramienta asigna baselines según la capa detectada por el lenguaje:

| Capa | Lenguajes | $T_{\text{clean}}$ default | $N$ default |
|---|---|---|---|
| **Backend** | Go, Python, etc. | `7.0 h` | `10 intervenciones/año` |
| **Frontend** | Dart / Flutter | `4.0 h` | `30 intervenciones/año` |

- Estos valores reflejan que el ciclo de desarrollo en Frontend es más ágil, pero más frecuente.
- Se pueden sobreescribir por archivo en `intereses.yaml` (campo `t_clean_horas` o `cambios_anuales`).
- **Parámetros CLI:** `--t-clean-backend 7.0`, `--t-clean-frontend 4.0`
- **Fuente:** Pág. 21 del documento de especificación técnica de clase.

---

## 13. Cadena de Resolución de Fricción

La herramienta aplica el siguiente orden de prioridad para determinar $N$, $\Delta t$ y $T_{\text{clean}}$ de cada archivo:

```
1. intereses.yaml        (máxima prioridad — estimaciones humanas explícitas)
2. Sin deuda técnica     (deuda_horas = 0 → fricción $0, interés $0)
3. Git commit count      (conteo de commits en el último año para N; T_clean del baseline de capa)
4. Baseline fijo de capa (fallback final — Backend: 7h/10 | Frontend: 4h/30)
```

El campo `fuente_interes` en el reporte indica cuál se aplicó:

| Valor | Significado |
|---|---|
| `yaml` | Provisto por el equipo en `intereses.yaml` |
| `sin_deuda` | $MI \ge MI_{\text{umbral}}$, no hay deuda activa |
| `git` | $N$ determinado por conteo de commits en git log |
| `fijo` | Fallback con baselines de capa |
| `ninguna` | Sin datos suficientes para calcular interés |

---

## 14. Diccionario de Campos del Reporte (CSV / JSON)

| Campo | Tipo | Descripción |
|---|---|---|
| `ruta` | str | Ruta relativa al archivo analizado |
| `lenguaje` | str | `go` \| `dart` |
| `loc` | int | Líneas de código efectivas (sin blancos ni comentarios) |
| `complejidad_ciclomatica` | int | Complejidad ciclomática total del archivo ($CC$) |
| `mi` | float | Índice de Mantenibilidad calculado (0–100) |
| `estado_mi` | str | `CRITICO` \| `APROBADO` \| `EXCELENTE` |
| `deuda_horas` | float | Horas de trabajo para llegar a $MI_{\text{umbral}}$ |
| `costo_reparacion_usd` | float | Capital de la deuda en USD |
| `factor_friccion` | float \| null | $F(MI)$ — multiplicador de tiempo (solo modelo dinámico) |
| `t_clean_horas` | float \| null | Tiempo de intervención en código limpio (horas) |
| `t_real_horas` | float \| null | Tiempo de intervención real = $T_{\text{clean}} \cdot F(MI)$ |
| `delta_t_horas` | float \| null | Fricción pura por cambio = $T_{\text{real}} - T_{\text{clean}}$ |
| `interes_anual_usd` | float \| null | Costo anual por fricción en USD |
| `payback_anios` | float \| null | Años para recuperar la inversión de refactorización |
| `roi_4_anios_porc` | float \| null | ROI nominal a 4 años (%) |
| `roi_ajustado_porc` | float \| null | ROI ajustado al 65% de probabilidad de éxito (%) |
| `modelo_calculo` | str | `dinamico` \| `clasico` |
| `tiene_datos_interes` | bool | `True` si se calcularon métricas financieras |
| `fuente_interes` | str | Origen de $N$ y $\Delta t$ — ver tabla de cadena de resolución |

---

## 15. Parámetros Configurables

### CLI (`src/main.py`)

| Flag | Default | Descripción |
|---|---|---|
| `--modelo` | `dinamico` | Selección de modelo de cálculo |
| `--mi-referencia` | `75.0` (din) / `20.0` (cl) | MI umbral de referencia |
| `--team-experience` / `--ef` | `0.0` | Factor de experiencia del equipo $EF$ (0–5) |
| `--tcf` | `1.0` | Technical Complexity Factor |
| `--tasa-exito` | `0.65` | Probabilidad de éxito para ROI ajustado |
| `--tarifa-usd` | `30.0` | Costo por hora de desarrollo en USD |
| `--t-clean-backend` | `7.0` | $T_{\text{clean}}$ default para archivos Go/backend |
| `--t-clean-frontend` | `4.0` | $T_{\text{clean}}$ default para archivos Dart/frontend |
| `--metodo-estimacion` | `git` | `git` (commits del último año) \| `fijo` |
| `--default-cambios` | auto por capa | $N$ fijo para archivos sin config ni Git |
| `--default-delta-t` | auto por $F(MI)$ | $\Delta t$ fijo (anula el cálculo dinámico) |

### `intereses.yaml`

```yaml
archivos:
  - ruta: "backend/internal/adapter/postgres/academic_repo.go"
    cambios_anuales: 14    # N — intervenciones anuales (obligatorio)
    delta_t_horas: 2.5     # Δt manual (opcional — si no va, se calcula vía F(MI))
    t_clean_horas: 7.0     # T_clean override (opcional)
```

---

## 16. Caso de Estudio Numérico (Golang, Pág. 19-20)

Archivo Go hipotético con métricas:
- $LOC = 166$, $CC = 25$, Tarifa = $\$35/\text{h}$, $N = 10$ intervenciones anuales.

**Paso 1 — MI:**
$$MI = \frac{171 - 25 \cdot \ln(166) - 0.23 \cdot 25}{171} \cdot 100 = 21.90$$

**Paso 2 — Factor de Fricción:**
$$F(MI) = 1 + \left(\frac{75 - 21.90}{75}\right)^2 \cdot 3 = 2.50\text{x}$$

**Paso 3 — Tiempo Real e Interés:**
$$T_{\text{real}} = 6\text{h} \cdot 2.50 = 15\text{h} \qquad \Delta t = 15 - 6 = 9\text{h}$$
$$\text{Interés Anual} = 10 \cdot 9 \cdot 35 = \$3{,}150$$

**Paso 4 — Deuda y Costo de Reparación:**
$$\text{Deuda (h)} = (75 - 21.90) \cdot 166 \cdot 0.01 = 88.15\text{h}$$
$$\text{Costo de Reparación} = 88.15 \cdot 35 = \$3{,}085.11$$

**Paso 5 — Payback y ROI:**
$$\text{Payback} = \frac{3{,}085.11}{3{,}150} = 0.98\text{ años}$$
$$ROI_{\text{nominal}} = 100 \cdot \frac{(3{,}150 \cdot 4) - 3{,}085.11}{3{,}085.11} = +308\%$$
$$ROI_{\text{ajustado}} = 100 \cdot \frac{(3{,}150 \cdot 4 \cdot 0.65) - 3{,}085.11}{3{,}085.11} = +166\%$$

---

## Referencias

| Fuente | Detalle |
|---|---|
| [`src/domain/calculator.py`](src/domain/calculator.py) | Implementación de todas las fórmulas |
| [`src/domain/models.py`](src/domain/models.py) | Entidades: `FileMetric`, `FinancialParams`, `DebtReport` |
| [`c_lculo_de_deuda_t_cnica_y_modelo_de_fricci_n_operativa.md`](c_lculo_de_deuda_t_cnica_y_modelo_de_fricci_n_operativa.md) | Documento de especificación matemática (notas de clase, ESET2) |
| [`tests/test_contra_documento_clase.py`](tests/test_contra_documento_clase.py) | Valida retrocompatibilidad con los números de clase |
| [`tests/unit/test_nuevo_modelo_dinamico.py`](tests/unit/test_nuevo_modelo_dinamico.py) | Valida el modelo de fricción operativa contra el caso de Go de pág. 19-20 |
| Capers Jones — *Applied Software Measurement* | Base empírica del techo $F(MI)_{\max} = 4.0\text{x}$ |
| Stripe — *The Developer Coefficient* | 30–33% del tiempo semanal perdido en deuda técnica |
| Estudios de refactorización incremental | Tasa de éxito del 65% (vs 21% en reescritura total) |
