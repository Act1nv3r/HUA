# HU Analyzer — Actinver Digital Products

Analiza **definición funcional** y **capas tecnológicas involucradas** de HUs con IA (Claude).
La información técnica detallada se revisa en **prerefinamiento y refinamiento**.

Genera:
- **Columnas de análisis** agregadas directamente a tu Excel de HUs
- **Hoja de Síntesis Ejecutiva** con scores, brechas y dashboard por iniciativa

---

## 🚀 Desarrollo local (quick start)

```bash
cd hu-analyzer
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edita .streamlit/secrets.toml y agrega tu ANTHROPIC_API_KEY

./run_local.sh
# o: streamlit run app.py
```

Abre http://localhost:8501 — Sube archivo(s) → Analiza → Descarga resultado.

### Opciones de carga

| Opción | Descripción |
|--------|-------------|
| **Excel consolidado** | Un Excel con varias pestañas (una por iniciativa) |
| **Varios Excels** | Cada iniciativa en un archivo Excel separado → se consolidan en uno |
| **Excel + Word** | Excel como base + archivos Word → se extraen HUs y se agregan como pestañas |
| **Solo Word** | Uno o más .docx → se convierten a Excel y se consolidan |

El resultado siempre es **un solo Excel consolidado** con todas las iniciativas en pestañas y el **Executive Summary** incluye todas.

**Guía completa:** Ver [DEV.md](DEV.md)

### Desplegar en Streamlit Cloud

Para publicar la app en [share.streamlit.io](https://share.streamlit.io), sigue la guía paso a paso: **[DEPLOY.md](DEPLOY.md)**

---

## ¿Qué evalúa? (enfoque funcional)

| Dimensión | Peso | Qué mide |
|---|---|---|
| **Definición Funcional** | 35% | Happy path, flujos alternos, reglas de negocio, mensajes de error, casos edge |
| **Capas Tecnológicas** | 25% | Identificación de capas involucradas: UI, Backend, Integraciones, Seguridad |
| **UX / UI (funcional)** | 15% | Estados de pantalla, validaciones, flujos de usuario |
| **Integraciones/Sistemas** | 10% | Qué sistemas intervienen (RENAPO, SAT, Core Bancario...) — identificación funcional |
| **Regulatorio & Seguridad** | 8% | Qué aspectos regulatorios aplican (CUB, PLD/AML) — identificación |
| **Criterios de Aceptación** | 7% | Criterios testeables y medibles |

### Escala de scoring

| Score | Nivel | Significado |
|---|---|---|
| 90–100 | 🟢 Excelente | Lista para prerefinamiento sin dudas |
| 75–89 | 🔵 Completo | Lista con pequeñas clarificaciones |
| 55–74 | 🟡 Aceptable | Requiere trabajo antes del prerefinamiento |
| 30–54 | 🟠 Incompleto | Trabajo significativo requerido |
| 0–29 | 🔴 Crítico | No lista — falta información fundamental |

---

## Instalación

```bash
# 1. Instalar dependencias
pip install anthropic openpyxl

# 2. Configurar API Key de Anthropic
# Windows:
set ANTHROPIC_API_KEY=sk-ant-...

# Mac / Linux:
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Uso

### Plataforma web (recomendado para POs)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
streamlit run app.py
```

Sube Excel → Analiza con IA → Descarga resultado + resumen ejecutivo.

### Línea de comandos

```bash
# Analizar todas las hojas (guarda en Output/ con v1.0, v2.0...)
python3 hu_analyzer.py --input HUs_Compilado.xlsx

# Especificar archivo de salida manualmente
python hu_analyzer.py --input HUs_Compilado.xlsx --output HUs_Analizadas.xlsx

# Analizar solo una iniciativa
python hu_analyzer.py --input HUs_Compilado.xlsx --sheet "Onboarding"
python hu_analyzer.py --input HUs_Compilado.xlsx --sheet "Cuenta Remunerada"
python hu_analyzer.py --input HUs_Compilado.xlsx --sheet "Crédito Simple"

# Prueba rápida con las primeras N HUs
python3 hu_analyzer.py --input HUs_Compilado.xlsx --limit 5
```

---

## Estructura del Excel de entrada

El script espera el formato estándar de Actinver:

```
Fila 1-7:  Metadata (Proceso, Tipo de HU, etc.)
Fila 8:    Encabezados de columnas
           → No. HU | Etapa/Módulo | Titulo | Historia de Usuario |
             Descripción/Objetivo | Requerimientos UX/UI |
             Criterios de Aceptación | Reglas de Negocio | Observaciones
Fila 9+:   Datos de HUs (ID que empiece con "HU")
```

---

## Output generado

Los archivos se guardan por defecto en la carpeta **`Output/`** con numeración consecutiva:
- `HUs_Compilado_analizado_v1.0.xlsx` (primera ejecución)
- `HUs_Compilado_analizado_v2.0.xlsx` (segunda ejecución)
- `HUs_Compilado_analizado_v3.0.xlsx` (tercera ejecución)
- ...

### En cada hoja de HUs (columnas nuevas a la derecha)

| Columna | Contenido |
|---|---|
| SCORE TOTAL | Número 0-100 con color semafórico |
| NIVEL | 🟢🔵🟡🟠🔴 con color |
| SCORE por dimensión | Funcional, Capas Tec., UX/UI, Integr., Regulat., Criterios |
| CAPAS TECNOLÓGICAS INVOLUCRADAS | Lista de capas: UI, Backend, RENAPO, etc. |
| RESUMEN EJECUTIVO | Estado de definición funcional y readiness |
| BRECHAS (×6) | Elementos faltantes por dimensión (funcional) |
| PREGUNTAS PARA PREREFINAMIENTO | Clarificaciones que el PO debe resolver antes |

### Hoja "📊 Síntesis Ejecutiva" (primera hoja)

- **Sección A** — Métricas globales (promedio, máx, mín, distribución por nivel)
- **Sección B** — Tabla comparativa de scores por iniciativa y dimensión
- **Sección C** — Brechas consolidadas: dimensiones más débiles y top brechas recurrentes
- **Sección D** — Leyenda de scoring y pesos

---

## Ajustes de configuración

El script **detecta automáticamente** la fila de encabezados en cada hoja (busca columnas como ID, Título, Descripción en las primeras 15 filas). Esto permite que hojas con estructura distinta (p. ej. Onboarding con headers en fila 1) se procesen correctamente.

Si una hoja no sigue el layout estándar, edita estas constantes como fallback:

```python
HEADER_ROW    = 8   # Fila por defecto si no se detectan encabezados
DATA_START_ROW = 9  # Primera fila con datos (header_row + 1)
```

Si quieres cambiar los pesos de las dimensiones (deben sumar 1.0):

```python
DIMENSION_WEIGHTS = {
    "funcional":      0.35,   # Definición funcional
    "capas_tec":      0.25,   # Capas tecnológicas involucradas
    "ux_ui":          0.15,   # UX/UI funcional
    "integraciones":  0.10,   # Sistemas involucrados
    "regulatorio":    0.08,   # Aspectos regulatorios
    "criterios":      0.07,   # Criterios de aceptación
}
```

---

## Estimación de costo y tiempo

| HUs | Tiempo estimado | Costo API aprox. |
|---|---|---|
| 10 HUs | ~3 min | ~$0.05 USD |
| 50 HUs | ~15 min | ~$0.25 USD |
| 100 HUs | ~30 min | ~$0.50 USD |

---

## Troubleshooting

**Error: ANTHROPIC_API_KEY no configurada**
```bash
export ANTHROPIC_API_KEY=sk-ant-tu-key-aqui
```

**Error: Hoja no encontrada**
```bash
# Verifica el nombre exacto de la hoja (sensible a mayúsculas/espacios)
python hu_analyzer.py --input HUs_Compilado.xlsx --sheet "Cuenta Remunerada"
```

**Rate limit de API**
El script tiene reintentos automáticos con espera progresiva.
Si persiste, usa `--limit` para procesar en lotes.

**El script no encuentra las HUs**
- El script detecta automáticamente la fila de encabezados por hoja. Si alguna hoja no se procesa bien, verifica que tenga columnas como "ID", "Título" o "Descripción" en las primeras filas.
- Los IDs de HU no deben estar vacíos ni ser "Ejemplo".
