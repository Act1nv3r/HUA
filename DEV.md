# Desarrollo local — HU Analyzer

Guía para correr la plataforma localmente durante el desarrollo. Cuando esté lista, harás push a GitHub y despliegue a Streamlit.

---

## 1. Requisitos

- Python 3.10+
- Cuenta Anthropic con API key

---

## 2. Configuración inicial (una sola vez)

### Opción A: Usar secrets.toml (recomendado)

```bash
cd hu-analyzer

# Copiar plantilla de secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Editar y agregar tu API key
# Abre .streamlit/secrets.toml y reemplaza con tu clave real
```

Contenido de `.streamlit/secrets.toml`:
```toml
ANTHROPIC_API_KEY = "sk-ant-api03-tu-clave-aqui"
```

### Soporte Word (.docx)

Puedes subir archivos Word además de Excel. El contenido se convierte a formato Excel estándar:
- **Solo Word:** se crea un Excel con una hoja por cada documento.
- **Excel + Word:** el Word se agrega como nueva hoja (iniciativa) al Excel.
- El Word debe tener tablas con columnas como ID, Título, Descripción, o párrafos con formato HU-001, etc.

### Opción B: Variable de entorno

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-tu-clave-aqui
```

---

## 3. Instalar dependencias

```bash
cd hu-analyzer
pip install -r requirements.txt
```

O con entorno virtual (recomendado):

```bash
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

---

## 4. Ejecutar la plataforma

### Con el script

```bash
chmod +x run_local.sh
./run_local.sh
```

### Manualmente

```bash
streamlit run app.py
```

Se abrirá en **http://localhost:8501**

---

## 5. Uso local

1. **Ruta del archivo** (recomendado): Selecciona esta opción e ingresa la ruta completa, ej. `/Users/tu_usuario/Desktop/HUs_Compilado.xlsx`
2. **Subir archivo**: Arrastra o selecciona el Excel (puede dar "Connection lost" en algunos entornos)
3. **Límite de HUs**: Usa 5 para prueba rápida, 0 para todas
4. Clic en **Analizar HUs con IA**
5. Descarga el resultado y/o haz **Nuevo análisis** para empezar de nuevo

---

## 6. Estructura del proyecto

```
hu-analyzer/
├── app.py              # Plataforma Streamlit (punto de entrada)
├── hu_analyzer.py      # Lógica de análisis con IA
├── config.py           # Configuración y seguridad
├── requirements.txt
├── run_local.sh        # Script para correr local
├── .streamlit/
│   ├── config.toml     # Tema y configuración UI
│   ├── secrets.toml     # API key (NO commitear)
│   └── secrets.toml.example
├── Output/             # Archivos generados (v1.0, v2.0...)
├── DEV.md              # Esta guía
└── SECURITY.md         # Análisis de riesgos
```

---

## 7. Probar el análisis

1. Coloca un Excel de HUs en la carpeta (o úsalo desde cualquier ruta).
2. En la plataforma: sube el archivo.
3. Configura "Límite de HUs" en 5 para prueba rápida.
4. Clic en "Analizar HUs con IA".
5. Espera el resultado y descarga el Excel analizado.

---

## 8. Modo desarrollo vs producción

- **Local:** Se muestran stack traces completos en errores (útil para debug).
- **Producción:** `HU_ANALYZER_PRODUCTION=1` oculta detalles técnicos al usuario.

Para probar modo producción local:
```bash
HU_ANALYZER_PRODUCTION=1 streamlit run app.py
```

---

## 9. "Connection lost" al subir archivo

Si ves "Connection lost. Please wait for the app to reconnect":

- **Causa común:** El proyecto está en OneDrive/CloudStorage. La sincronización puede reiniciar Streamlit.
- **Solución 1:** Ya está configurado `fileWatcherType = "none"` en `.streamlit/config.toml`.
- **Solución 2:** Copia el proyecto a una carpeta local (ej. `~/hu-analyzer`) y ejecuta desde ahí.
- **Solución 3:** Usa **"Ruta del archivo"** en lugar de subir — ingresa la ruta completa del Excel.
- **Solución 4:** Reinicia Streamlit y vuelve a intentar.

---

## 10. Rendimiento (análisis paralelo)

El análisis procesa varias HUs en paralelo para reducir el tiempo total. Por defecto: **5 HUs simultáneas** (compatible con Tier 1 de Anthropic ~50 RPM).

- **100 HUs:** ~4–8 min (antes ~15–25 min)
- **Ajustar:** Edita `MAX_CONCURRENT_ANALYSIS` en `config.py`. Si tienes Tier 2+ (1000 RPM), puedes subir a 10–15.

---

## 11. Próximos pasos (cuando esté listo)

1. **Git:** `git init`, commit, push a repo (privado recomendado).
2. **Streamlit Cloud:** Conectar repo, configurar Secrets, desplegar.
3. **Privacidad:** App privada en Streamlit (solo invitados).

Ver README y SECURITY.md para despliegue.
