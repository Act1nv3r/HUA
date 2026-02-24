"""
Configuración de seguridad y límites — HU Analyzer Platform
Ver SECURITY.md para análisis de riesgos.
"""

import re


class AnthropicGameOverError(Exception):
    """Se acabaron tokens/créditos en la cuenta Anthropic."""


# ═══════════════════════════════════════════════════════════════════════════
# LÍMITES DE SEGURIDAD
# ═══════════════════════════════════════════════════════════════════════════

# Tamaño máximo de archivo subido (bytes) — 25 MB
MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024

# Límite máximo de HUs por análisis (evitar costos excesivos)
MAX_HUS_PER_RUN = 200

# HUs analizadas en paralelo (5 = Tier 1 ~50 RPM; 10+ si tienes Tier 2+)
MAX_CONCURRENT_ANALYSIS = 5

# Tipos de archivo permitidos
ALLOWED_EXTENSIONS = {".xlsx", ".docx"}


def sanitize_filename(name: str) -> str:
    """Elimina caracteres peligrosos para evitar path traversal."""
    if not name or not isinstance(name, str):
        return "upload.xlsx"
    # Quitar path, solo nombre base
    base = name.split("/")[-1].split("\\")[-1]
    # Solo alfanuméricos, guiones, puntos
    safe = re.sub(r"[^\w\-\.]", "_", base)
    return safe[:100] if safe else "upload.xlsx"


def get_api_key():
    """
    Obtiene API key de forma segura:
    1. st.secrets (Streamlit Cloud)
    2. .streamlit/secrets.toml (CLI y local)
    3. Variable de entorno ANTHROPIC_API_KEY
    """
    try:
        import streamlit as st
        if hasattr(st, "secrets") and st.secrets:
            key = st.secrets.get("ANTHROPIC_API_KEY") or st.secrets.get("anthropic_api_key")
            if key:
                return str(key).strip()
    except Exception:
        pass
    import os
    key = os.environ.get("ANTHROPIC_API_KEY") or ""
    if not key:
        # Cargar desde .streamlit/secrets.toml cuando se ejecuta por CLI
        script_dir = os.path.dirname(os.path.abspath(__file__))
        secrets_path = os.path.join(script_dir, ".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            try:
                with open(secrets_path, "r", encoding="utf-8") as f:
                    content = f.read()
                import re
                m = re.search(r'ANTHROPIC_API_KEY\s*=\s*["\']([^"\']+)["\']', content)
                if m:
                    key = m.group(1).strip()
            except Exception:
                pass
    return key.strip()


def validate_upload(file, max_size: int = MAX_FILE_SIZE_BYTES) -> tuple[bool, str]:
    """
    Valida archivo subido. Retorna (ok, error_message).
    """
    if file is None:
        return False, "No se recibió ningún archivo."

    # Tamaño (Streamlit UploadedFile tiene .size, sino usamos len de bytes)
    size = getattr(file, "size", None) or len(file.getvalue()) if hasattr(file, "getvalue") else 0
    if size > max_size:
        return False, f"El archivo excede el tamaño máximo permitido ({max_size // (1024*1024)} MB)."

    # Extensión
    name = getattr(file, "name", "") or "upload"
    name_lower = name.lower().strip()
    if not (name_lower.endswith(".xlsx") or name_lower.endswith(".docx")):
        return False, "Solo se permiten archivos Excel (.xlsx) o Word (.docx)."

    return True, ""
