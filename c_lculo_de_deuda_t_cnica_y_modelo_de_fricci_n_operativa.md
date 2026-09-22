# Cálculo de Deuda Técnica y Modelo de Fricción Operativa

---

## 1. Conceptos Financieros y Calibración de ROI

### Calibración Tasa de Éxito ROI
En la industria del software, asumir un 100% de éxito en un cálculo financiero de retorno es considerado poco realista. La tasa de éxito aceptada en proyectos de refactorización de código ronda el 65% o 70%. De hecho, estudios de mercado recientes muestran que los proyectos de refactorización incremental tienen una tasa de éxito promedio del 65%, mientras que los proyectos de reescritura total caen drásticamente a un 21%.

### Índice de Deuda Técnica y Fórmulas Financieras
* **Interés Anual (\$):**
  $$\text{Interés Anual (\$)} = N \cdot (T_{\text{Real}} - T_{\text{Ideal}}) \cdot \text{Costo Hora de Desarrollo (\$/Hora)}$$
  $$\text{Interés Anual (\$)} = \text{Cambios} \cdot (T_{\text{Real}} - \text{Eficiencia Ideal}) \cdot \text{Costo Hora de Desarrollo (\$/Hora)}$$

* **Costo de Reparación (\$):**
  $$\text{Costo de Reparación (\$)} = \text{Deuda Técnica (Horas)} \cdot \text{Costo Hora de Desarrollo (\$/Hora)}$$

* **Tiempo de Payback:**
  $$\text{Tiempo de Payback} = \frac{\text{Costo de Reparación}}{\text{Interés Anual}}$$

* **Retorno de Inversión (ROI):**
  $$ROI = 100 \cdot \frac{(\text{Interés Anual} \cdot (TP + 1)) - \text{Costo de Reparación}}{\text{Costo de Reparación}}$$

---

## 2. Modelo de Fricción Operativa y Brecha Indexada

### Relación de Brecha Indexada (*Index Gap Ratio*)
Mide la distancia proporcional que separa un valor actual o real de un valor de referencia (o meta) que se ajusta dinámicamente a lo largo del tiempo.

$$\text{Relación de Brecha Indexada} = \frac{\text{Valor de Referencia Indexado} - \text{Valor Actual}}{\text{Valor de Referencia Indexado}}$$

En la fórmula de fricción, el término de la brecha indexada corresponde a:

$$\frac{MI_{\text{Umbral}} - MI_{\text{Actual}}}{MI_{\text{Umbral}}}$$

### Modelo de Fricción
$$T_{\text{Real}} = T_{\text{Clean}} \cdot F$$

$$F(MI) = 1 + \left(\frac{MI_{\text{Umbral}} - MI_{\text{Actual}}}{MI_{\text{Umbral}}}\right)^2 \cdot C$$

### Factor de Velocidad Base ($K_{\text{Dinámico}}$)
$$K_{\text{Dinámico}} = \left[ 0.01 - \left(\frac{EF}{5}\right) \cdot 0.0067 \right] \cdot TCF$$

* **Equipo inexperto ($EF = 0$):** Velocidad base de 6 minutos por línea ($K = 0.01 - 0 = 0.01$).
* **Equipo de alto rendimiento ($EF = 5$):** Velocidad base se acelera a 2 minutos por línea ($K = 0.01 - 0.0067 = 0.0033$).

### Deuda Técnica en Horas
$$\text{Deuda Técnica (Horas)} = \max(0, (20 - MI) \cdot LOC \cdot K)$$

*Donde $LOC$ es el número de líneas de código (excluyendo líneas en blanco y comentarios), y $K$ es el factor de corrección (por ejemplo, $0.01$ por línea en zona roja).*

---

## 3. Índice de Mantenibilidad (MI) y Comparativa de la Industria

### Calibración Empírica del Índice de Mantenibilidad de Microsoft
$$MI = \max\left(0, \frac{171 - 25 \cdot \ln(LOC) - 0.23 \cdot G}{171} \cdot 100\right)$$

* $MI$: Índice de mantenibilidad.
* $LOC$: Líneas de código (sin contar líneas en blanco y comentarios).
* $G$: Complejidad Ciclomática (número de caminos).

### Comparativa Estándar de la Industria vs. Microsoft

| Estado | Rango SonarQube | Rango Microsoft (Visual Studio) |
| :--- | :--- | :--- |
| **Verde** | 85 a 100 | 20 a 100 |
| **Amarillo** | 65 a 84 | 10 a 19 |

---

## 4. Documento 1: "Trabajo de clase de ESET2" (~22 páginas)

### Página 18

#### 4.1. Fundamentación Matemática

El modelo matemático propuesto para el factor de fricción es:

$$F(MI) = 1 + \left(\frac{MI_{\text{Umbral}} - MI_{\text{Actual}}}{MI_{\text{Umbral}}}\right)^2 \cdot C$$

Para hallar el valor de $C$ nos apoyaremos en las condiciones de contorno (límites físicos) del desarrollo de software.

* El límite óptimo, si el código cumple con el estándar ideal de mantenibilidad $MI = 75$, la brecha indexada se anula obteniendo máxima eficiencia, cero fricción,

> **[⚠️ GAP: Falta texto intermedio entre pág 18 y pág 19]**

---

### Página 19

...y las bases de datos de productividad de Capers Jones demuestran que, un desarrollador tarda 4 veces más en modificar un software en estado de caos comparado con uno diseñado bajo buenas prácticas.

Tomando esto en consideración e igualando el límite del modelo con la evidencia empírica, resulta:

$$F(MI) = 1 + \left(\frac{75 - 0}{75}\right)^2 \cdot C = 1 + C$$

Luego:

$$4 = 1 + C \Rightarrow C = 3$$

El valor $C = 3$ es el único peso matemático que permite escalar el factor de fricción desde la eficiencia óptima ($1\text{x}$) hasta el techo histórico de pérdida de productividad ($4\text{x}$).

Por otra parte, la constante $C = 3$ es un techo asintótico de productividad. Determina que en el estado de máxima entropía de un sistema, el 75% del salario integrado del desarrollador se destina a pagar el impuesto de la deuda técnica. Solo el 25% restante se transforma en valor neto.

Si el desarrollador pasa su día completo (6 a 8 horas reales de trabajo) atrapado en un código con un $MI = 0$ (donde el factor de fricción es $4.0\text{x}$), podemos calcular cuánto tiempo neto produjo:

> **[⚠️ GAP: Falta el resultado explícito de ese cálculo]**

En un código con $MI = 0$, el 75% de cualquier bloque de tiempo se destruye en fricción operativa, dejando solo un 25% para la creación de valor real.

#### Recálculo del Escenario Real (caso Golang)
Apliquemos este modelo dinámico al caso de estudio anterior basado en un archivo Golang ($LOC = 166$, $G = 25$, $MI = 21.90$). Asumamos que para una tarea en código limpio el tiempo es de 6 horas y mantenemos 10 intervenciones anuales.

* **Paso A: Calcular el Factor de Fricción Operativa**
  * Fórmula:
    $$F(MI) = 1 + \left(\frac{MI_{\text{Umbral}} - MI_{\text{Actual}}}{MI_{\text{Umbral}}}\right)^2 \cdot C$$
  * Cálculo:
    $$F(MI) = 1 + \left(\frac{75 - 21.90}{75}\right)^2 \cdot 3 = 2.5$$

---

### Página 20

El modelo determina que intervenir este archivo de Go cuesta 2.5 veces más tiempo que si estuviera con un índice de mantenibilidad de 75.

* **Paso B: Tiempo de Intervención Real y Sobrecosto**
  * Fórmula:
    $$T_{\text{real}} = T_{\text{clean}} \cdot F$$
    $$\text{Fricción Pura} = T_{\text{real}} - T_{\text{clean}}$$
  * Cálculo:
    $$T_{\text{real}} = 6 \text{ horas} \cdot 2.5 = 15 \text{ horas}$$
    $$\text{Fricción Pura} = 15 - 6 = 9 \text{ horas}$$

* **Paso C: Interés Anual**
  Tomando 10 intervenciones anuales y un salario integrado de USD 35, el interés anual se sitúa en:
  * Fórmula:
    $$\text{Interés Anual (\$)} = N \cdot (\text{Fricción Pura en Horas}) \cdot \text{Hora de Desarrollo (\$/Hora)}$$
  * Cálculo:
    $$\text{Interés Anual (\$)} = 10 \cdot 9 \cdot 35 = \text{USD } 3.150$$

#### Impacto en el Caso de Negocio - Nuevo Escenario Financiero
Al refinar el interés con nuestra fórmula de fricción operativa, el escenario financiero se torna más drástico:
* **Capital de la Deuda (Inversión):** USD 3.085,11 (las 88,15 horas calculadas con el umbral $MI = 75$).
* **Interés Anual Ajustado por Fricción:** USD 3.150,00 (90 horas anuales de desperdicio operativo).

---

### Página 20 (Versión alternativa)

#### Índice de Mantenibilidad (MI) Estándar de la Industria
Si bien Microsoft fija de forma muy laxa el piso del índice de mantenibilidad en 20 puntos, las herramientas modernas de calidad técnica de código (como SonarQube, NDepend) manejan umbrales mucho más estrictos para determinar la calidad.

* **MI 85 (Verde) Alta Calidad Técnica - Código de Excelencia:** Es el estándar dorado de la industria. El código es atómico, altamente modular, con cobertura óptima y duplicaciones nulas.
* **MI 75 (Verde) Límite Técnico Recomendado:** Es el valor que elegimos para consolidar la métrica desarrollada aquí. Representa un excelente equilibrio: código de producción.

---

### Página 21

Muchos estudios globales como *The Developer Coefficient* de Stripe demuestran que los desarrolladores gastan, en promedio, entre un 30% y un 33% de su semana laboral lidiando con código con deuda técnica. Esto se traduce aproximadamente a unas 13.4 horas semanales por desarrollador.

Para el modelo de estimación de intereses basado en el número de intervenciones anuales, la industria adopta estimaciones base diferentes según la naturaleza de la arquitectura:

#### Backend: Enfoque en Complejidad Lógica y Datos
Las intervenciones en el Backend suelen requerir más tiempo de análisis debido al manejo de estado, consistencia de datos, integraciones externas (APIs, DOs) y concurrencia.
* **Estimación Estándar sobre Código Limpio ($MI = 75$):** 6 a 8 horas por intervención (promedio sugerido: 7 horas).
* **Intervenciones Estándar:** 12 a 18 intervenciones al año (promedio sugerido: 10).
* **Horas Totales Anuales:** 10 intervenciones $\cdot$ 7 horas = 70 horas anuales en código limpio.

#### Frontend: Enfoque en UI, Estado Local y Layout
El ciclo de desarrollo en Frontend es tradicionalmente más ágil y visual. Modificar componentes de UI suele ser más rápido, aunque las interfaces modernas manejadas por estado (Flutter, React, Vue) aumentan la fricción.
* **Estimación Estándar sobre Código Limpio ($MI = 75$):** 3 a 4 horas por intervención (promedio sugerido: 4 horas).
* **Intervenciones Estándar:** 24 a 36 intervenciones al año (promedio sugerido: 30).
* **Horas Totales Anuales:** 30 intervenciones $\cdot$ 4 horas = 120 horas anuales en código limpio.

#### Implicaciones de un Modelo de Fricción Dinámico
Las horas de trabajo reales no son fijas, sino que se estiran elásticamente a medida que se reduce la calidad del código. Intervenir un componente de Backend limpio debería demorar 7 horas. Si el código está en $MI = 75$, el programador tarda 7 horas; pero si el $MI$ disminuye, el tiempo real se incrementa según el modelo de fricción.

---

## 5. Documento 2: "Proyecto Diseño e Implementación..." (8 páginas)

### Página 3

Aproximaciones matemáticas para simplificar la fórmula tradicional como métricas que sustituyen de manera eficiente y de cálculo más simple al índice de mantenibilidad.

#### 1 - La aproximación matemática: Sustituir Halstead por LOC
A nivel estadístico, el Volumen de Halstead y las líneas de código están estrechamente correlacionadas (a más líneas de código, más operadores y operandos, son covariantes). De donde una versión aproximada podría reemplazar el término $\ln(V)$ por una función del número de líneas $LOC$. Una aproximación muy común para no perder la escala de Microsoft es:

$$MI = \max\left(0, \frac{171 - 25 \cdot \ln(LOC) - 0.23 \cdot G}{171} \cdot 100\right)$$

*Donde $G$ es la Complejidad Ciclomática (número de caminos).*

---

## 6. Resumen de Observaciones y Gaps de Compilación

1. **Gap 1 (Pág. 18 → 19):** Falta el texto de conexión entre *"la..."* (pág. 18) y *"brecha indexada se anula..."* (pág. 19).
2. **Gap 2 (Pág. 19):** Falta el resultado numérico explícito del cálculo del tiempo neto producido para $MI = 0$.
3. **Inconsistencia de Pagina 20:** Existen dos versiones de la página 20 debido a repaginación o diferentes versiones del documento original (una aborda el caso práctico en Go y la otra describe los rangos de MI de la industria).