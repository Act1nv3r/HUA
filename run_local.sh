#!/bin/bash
# HU Analyzer — Ejecutar localmente para desarrollo
# Uso: ./run_local.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "📂 HU Analyzer — Modo desarrollo local"
echo "   Directorio: $SCRIPT_DIR"
echo ""

# Verificar que app.py existe
if [ ! -f app.py ]; then
    echo "❌ Error: app.py no encontrado. Ejecuta desde la carpeta hu-analyzer."
    exit 1
fi

# Crear Output si no existe
mkdir -p Output

# Verificar dependencias
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📦 Instalando dependencias..."
    pip install -r requirements.txt
fi

# Cargar API key desde secrets si existe
if [ -f .streamlit/secrets.toml ]; then
    echo "✓ secrets.toml encontrado"
else
    echo "⚠️  Crea .streamlit/secrets.toml con tu ANTHROPIC_API_KEY"
    echo "   cp .streamlit/secrets.toml.example .streamlit/secrets.toml"
    echo "   Luego edita y agrega tu API key."
    echo ""
    echo "   O exporta la variable: export ANTHROPIC_API_KEY=sk-ant-..."
    echo ""
fi

echo "🚀 Iniciando Streamlit en http://localhost:8501"
echo "   Presiona Ctrl+C para detener"
echo ""

streamlit run app.py --server.port 8501 --server.address localhost
