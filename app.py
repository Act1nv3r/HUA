"""
HU Analyzer Platform — Actinver
Plataforma web para análisis recurrente de Historias de Usuario.
POs suben Excel → IA analiza → Descarga resultado + resumen ejecutivo.

Seguridad: Ver SECURITY.md
"""

import os
import tempfile
import threading
import time
import streamlit as st
from hu_analyzer import run, get_next_output_path, count_hus_to_analyze, get_hu_speed
from config import get_api_key, validate_upload, MAX_FILE_SIZE_BYTES, MAX_HUS_PER_RUN
from word_converter import word_to_excel_file, add_word_as_sheet_to_excel, merge_excel_files
from hu_analyzer import get_common_headers_from_excel

# Modo producción: no exponer stack traces al usuario
PRODUCTION = os.environ.get("HU_ANALYZER_PRODUCTION", "0") == "1"

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="HU Analyzer | Actinver",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilos Actinver Brandbook 2025 — Fondo oscuro
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    /* Fondo principal — Azul Grandeza + gradiente */
    .stApp {
        background: linear-gradient(180deg, #0A0E12 0%, #1A2433 100%);
    }
    /* Headers */
    .main-header {
        font-family: 'Poppins', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    .sub-header {
        font-family: 'Poppins', sans-serif;
        color: #ADB5C2;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    
    /* Cards y métricas */
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
    }
    div[data-testid="stMetric"] {
        background: rgba(26, 36, 51, 0.8);
        border: 1px solid rgba(230, 199, 138, 0.3);
        border-radius: 12px;
        padding: 1rem;
    }
    
    /* DataFrames */
    [data-testid="stDataFrame"] {
        background: rgba(26, 36, 51, 0.6);
        border: 1px solid rgba(230, 199, 138, 0.2);
        border-radius: 8px;
    }
    
    /* Botones primarios — Sunset */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #E6C78A 0%, #D4B56A 100%) !important;
        color: #0A0E12 !important;
        font-weight: 600;
        border: none;
        border-radius: 8px;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #EAD2A1 0%, #E6C78A 100%) !important;
        color: #0A0E12 !important;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        background: rgba(26, 36, 51, 0.8);
        border: 2px dashed rgba(230, 199, 138, 0.4);
        border-radius: 12px;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #E6C78A;
    }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background: #1A2433 !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(230, 199, 138, 0.3);
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #E6C78A, #314566) !important;
    }
    
    /* Info boxes */
    [data-testid="stAlert"] {
        background: rgba(26, 36, 51, 0.9);
        border: 1px solid rgba(230, 199, 138, 0.3);
        color: #FFFFFF;
    }
    
    /* Ocultar sidebar */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="stSidebar"] + div { margin-left: 0 !important; }
    [data-testid="stMain"] { max-width: 100% !important; }
    
    /* Loader animado junto a Estado del análisis */
    .analysis-loader {
        display: inline-block;
        animation: spin 1s linear infinite;
        margin-right: 8px;
        vertical-align: middle;
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)


# Límite de HUs (0 = todas)
limit = None

# ═══════════════════════════════════════════════════════════════════════════
# VERSIONES DE EVALUACIÓN
# ═══════════════════════════════════════════════════════════════════════════

CONFIG_VERSIONS = {
    "v1": {
        "label":       "v1.0 — Evaluación Técnica Completa",
        "badge_color": "#2E75B6",
        "description": "Evalúa las 6 dimensiones técnicas. Ideal cuando el Tech Owner ya participó en la definición.",
        "audience":    "Tech Owner + PO · Etapa: Refinamiento",
        "model":       "claude-sonnet-4-20250514",
        "max_tokens":  2000,
        "dimensions": {
            "funcional": "Definición Funcional",
            "ux_ui":     "UX / UI & Frontend",
            "backend":   "Backend & Microservicios",
            "seguridad": "Seguridad & Regulatorio",
            "qa":        "QA & Criterios de Prueba",
            "negocio":   "Negocio & KPIs",
        },
        "weights": {
            "funcional": 0.30,
            "ux_ui":     0.15,
            "backend":   0.25,
            "seguridad": 0.15,
            "qa":        0.10,
            "negocio":   0.05,
        },
        "system_prompt": (
            "Eres un Senior Fullstack Developer y Product Manager con 15 años "
            "en banca digital mexicana. Evalúas Historias de Usuario del área de Productos "
            "Digitales de Actinver, institución financiera regulada por CNBV, Banxico y SHCP. "
            "Las HUs van a fábricas de desarrollo especializadas (Back/Micros, Arquitectura, "
            "Front-end, QA) a través de prerefinamiento y refinamiento. Tu misión es detectar "
            "exactamente qué falta para que el equipo técnico pueda estimar y construir sin "
            "ambigüedades ni preguntas básicas durante el prerefinamiento. "
            "Contexto de sistemas: Core bancario COBIS; integraciones RENAPO/INE/SAT/Buró/SPEI/"
            "biométricos; regulatorio CUB Art.51 BIS 6/PUI/LFPDPPP/PLD-AML; "
            "productos Onboarding N4/Cuenta Remunerada/Crédito Simple/TDC Actinver. "
            "Responde ÚNICAMENTE con JSON válido. Sin texto antes ni después del JSON."
        ),
    },
    "v2": {
        "label":       "v2.0 — Definición Funcional · PO",
        "badge_color": "#375623",
        "description": "Calibrada para POs nuevos. Evalúa solo lo que el PO puede controlar. El Tech Owner completa en refinamiento.",
        "audience":    "PO + Analista Funcional · Etapa: Definición",
        "model":       "claude-haiku-4-5-20251001",
        "max_tokens":  1400,
        "dimensions": {
            "funcional": "Definición Funcional",
            "flujo":     "Flujo Operativo",
            "negocio":   "Negocio & Valor",
            "ux_ui":     "UX / UI",
            "backend":   "Backend & Integraciones",
            "seguridad": "Seguridad & Regulatorio",
        },
        "weights": {
            "funcional": 0.45,
            "flujo":     0.25,
            "negocio":   0.15,
            "ux_ui":     0.08,
            "backend":   0.04,
            "seguridad": 0.03,
        },
        "system_prompt": (
            "Eres un coach experto en metodologías ágiles y Product Management "
            "en banca digital mexicana. Tu rol es guiar a Product Owners nuevos de Actinver "
            "(institución financiera regulada por CNBV, Banxico y SHCP) para que definan "
            "correctamente sus Historias de Usuario antes de entrar a sesiones de prerefinamiento. "
            "CONTEXTO CLAVE: Los POs son nuevos y están aprendiendo a documentar HUs. "
            "En esta etapa SOLO se evalúa la definición funcional. El detalle técnico "
            "lo completará el Tech Owner en refinamiento. "
            "Productos en scope: Onboarding N4, Cuenta Remunerada, Crédito Simple, TDC Actinver. "
            "Regulatorio: CNBV/CUB, PLD/AML, LFPDPPP — solo verificar si aplica, sin detalles técnicos. "
            "NO pidas al PO: endpoints, schemas de API, timeouts, cifrado, datos de prueba técnicos ni wireframes. "
            "TONO: Directo, motivador y claro. Sin jerga técnica. "
            "Responde ÚNICAMENTE con JSON válido. Sin texto antes ni después del JSON."
        ),
    },
}

# ═══════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════

st.markdown('<p class="main-header">📊 HU Analyzer</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">Sube Excel y/o Word de HUs → La IA analiza definición funcional y capas tecnológicas → Descarga el resultado con análisis completo</p>',
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════
# UPLOAD
# ═══════════════════════════════════════════════════════════════════════════

uploaded_files = st.file_uploader(
    "Sube archivo(s) Excel y/o Word de HUs",
    type=["xlsx", "docx"],
    accept_multiple_files=True,
    help=f"Excel consolidado (varias pestañas) O varios Excels (uno por iniciativa) O Excel + Word. Todo se consolida en un solo archivo. Máx {MAX_FILE_SIZE_BYTES // (1024*1024)} MB por archivo.",
    key="hu_file_uploader",
)
if not uploaded_files:
    st.info("👆 Sube uno o más archivos Excel y/o Word para comenzar el análisis.")
    st.stop()

# Validar cada archivo
for f in uploaded_files:
    ok, err_msg = validate_upload(f)
    if not ok:
        st.error(f"❌ {f.name}: {err_msg}")
        st.stop()

# Preparar Excel unificado para análisis
excel_files = [f for f in uploaded_files if f.name.lower().endswith(".xlsx")]
word_files = [f for f in uploaded_files if f.name.lower().endswith(".docx")]

file_id = ""
base_excel_path = ""

with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
    base_excel_path = tmp.name

try:
    if excel_files and word_files:
        # Excel(es) + Word: consolidar Excels, luego agregar Words como hojas con formato común
        excel_paths = []
        for ef in excel_files:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
            tmp.write(ef.getvalue())
            tmp.close()
            excel_paths.append(tmp.name)
        if len(excel_paths) == 1:
            with open(base_excel_path, "wb") as f:
                f.write(open(excel_paths[0], "rb").read())
        else:
            merge_excel_files(excel_paths, base_excel_path)
        for p in excel_paths:
            if os.path.exists(p):
                os.unlink(p)
        common_headers = get_common_headers_from_excel(base_excel_path)
        for wf in word_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as wt:
                wt.write(wf.getvalue())
                wt_path = wt.name
            try:
                add_word_as_sheet_to_excel(
                    base_excel_path, wt_path,
                    initiative_name=os.path.splitext(wf.name)[0],
                    common_headers=common_headers if common_headers else None,
                )
            finally:
                if os.path.exists(wt_path):
                    os.unlink(wt_path)
        file_id = " + ".join(ef.name for ef in excel_files) + " + " + ", ".join(w.name for w in word_files)
    elif excel_files:
        # Solo Excel(es): consolidar todos en uno
        if len(excel_files) == 1:
            with open(base_excel_path, "wb") as f:
                f.write(excel_files[0].getvalue())
        else:
            excel_paths = []
            for ef in excel_files:
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
                tmp.write(ef.getvalue())
                tmp.close()
                excel_paths.append(tmp.name)
            merge_excel_files(excel_paths, base_excel_path)
            for p in excel_paths:
                if os.path.exists(p):
                    os.unlink(p)
        file_id = " + ".join(ef.name for ef in excel_files)
    elif word_files:
        # Solo Word(s): convertir a Excel consolidado
        first_word = word_files[0]
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as wt:
            wt.write(first_word.getvalue())
            wt_path = wt.name
        try:
            word_to_excel_file(wt_path, base_excel_path)
            common_headers = get_common_headers_from_excel(base_excel_path)
            for wf in word_files[1:]:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as wt2:
                    wt2.write(wf.getvalue())
                    wt2_path = wt2.name
                try:
                    add_word_as_sheet_to_excel(
                        base_excel_path, wt2_path,
                        initiative_name=os.path.splitext(wf.name)[0],
                        common_headers=common_headers if common_headers else None,
                    )
                finally:
                    if os.path.exists(wt2_path):
                        os.unlink(wt2_path)
        finally:
            if os.path.exists(wt_path):
                os.unlink(wt_path)
        file_id = ", ".join(w.name for w in word_files)
    else:
        st.error("No se encontraron archivos válidos.")
        st.stop()
except Exception as e:
    st.error(f"Error al procesar archivos: {e}")
    if PRODUCTION:
        pass
    else:
        st.exception(e)
    st.stop()

if not file_id:
    st.stop()

# Objeto compatible con el flujo de análisis (path ya está en base_excel_path)
class _UploadedExcel:
    def __init__(self, path, name):
        self._path = path
        self.name = name
    def getvalue(self):
        with open(self._path, "rb") as f:
            return f.read()

uploaded_file = _UploadedExcel(base_excel_path, file_id)

# ═══════════════════════════════════════════════════════════════════════════
# HISTÓRICO (opcional)
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("---")
with st.expander("📜 **Histórico (opcional)** — Comparar con análisis anterior", expanded=True):
    st.caption("Sube el Excel del último análisis para que la IA identifique mejoras y compare scores.")
    prev_uploaded = st.file_uploader(
        "Archivo analizado anterior",
        type=["xlsx"],
        help="Excel de un análisis previo. La IA comparará cada HU, identificará mejoras y generará un nuevo score.",
        key="prev_file_uploader",
    )

prev_analysis_path = None
if prev_uploaded:
    ok_prev, err_prev = validate_upload(prev_uploaded)
    if ok_prev:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp_prev:
            tmp_prev.write(prev_uploaded.getvalue())
            prev_analysis_path = tmp_prev.name
        st.success(f"✓ Histórico cargado: {prev_uploaded.name}")
    else:
        st.warning(f"⚠ {err_prev}")

# Reset si cambia el archivo
if "last_file" not in st.session_state:
    st.session_state.last_file = None
if file_id != st.session_state.get("last_file"):
    st.session_state.last_file = file_id
    st.session_state.analysis_done = False
    st.session_state.summary = None


# ═══════════════════════════════════════════════════════════════════════════
# ANÁLISIS
# ═══════════════════════════════════════════════════════════════════════════

if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "summary" not in st.session_state:
    st.session_state.summary = None
if "output_path" not in st.session_state:
    st.session_state.output_path = None
if "selected_version" not in st.session_state:
    st.session_state.selected_version = "v2"   # default: v2.0

# ── Switch de versión ──────────────────────────────────────────────────────
st.markdown("---")

sw_col1, sw_col2, sw_col3 = st.columns([1, 2, 1])
with sw_col2:
    version_options = {
        "v1": "🔵  v1.0 — Evaluación Técnica Completa",
        "v2": "🟢  v2.0 — Definición Funcional · PO",
    }
    _ver = st.session_state.selected_version
    _idx = list(version_options.keys()).index(_ver) if _ver in version_options else 1
    selected_label = st.radio(
        "Modo de evaluación",
        options=list(version_options.values()),
        index=_idx,
        horizontal=True,
        key="version_radio",
        help="v1.0: evalúa las 6 dimensiones técnicas completas (Tech Owner incluido). v2.0: solo evalúa lo que el PO puede definir en esta etapa.",
    )
    # Sincronizar selección con session_state
    for k, v in version_options.items():
        if v == selected_label:
            st.session_state.selected_version = k

    cfg = CONFIG_VERSIONS[st.session_state.selected_version]

    # Badge informativo de la versión activa
    badge_html = f"""
    <div style="
        margin-top: 0.75rem;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        border-left: 4px solid {cfg['badge_color']};
        background: rgba(26,36,51,0.8);
        font-family: 'Poppins', sans-serif;
    ">
        <div style="font-size:0.8rem; color:#ADB5C2; margin-bottom:0.2rem;">
            {cfg['audience']}
        </div>
        <div style="font-size:0.9rem; color:#FFFFFF;">
            {cfg['description']}
        </div>
        <div style="font-size:0.75rem; color:#ADB5C2; margin-top:0.4rem;">
            Modelo: <code style="color:{cfg['badge_color']};">{cfg['model']}</code>
            &nbsp;·&nbsp; max_tokens: {cfg['max_tokens']}
            &nbsp;·&nbsp; Dimensiones: {', '.join(cfg['dimensions'].keys())}
        </div>
    </div>
    """
    st.markdown(badge_html, unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    analyze_btn = st.button("🔍 Analizar HUs con IA", type="primary", use_container_width=True)

if analyze_btn and uploaded_file:
    api_key = get_api_key()
    if not api_key:
        st.error("❌ **ANTHROPIC_API_KEY** no configurada. Configúrala en Secrets (Streamlit Cloud) o variables de entorno.")
        st.code("ANTHROPIC_API_KEY = \"sk-ant-...\"", language="toml")
        st.stop()

    os.environ["ANTHROPIC_API_KEY"] = api_key

    # ── Aplicar config de versión activa ──────────────────────────────────
    import hu_analyzer as _hua
    _cfg = CONFIG_VERSIONS[st.session_state.selected_version]
    _hua.DIMENSIONS        = _cfg["dimensions"]
    _hua.DIMENSION_WEIGHTS = _cfg["weights"]
    _hua.SYSTEM_PROMPT     = _cfg["system_prompt"]
    _hua.ACTIVE_MODEL      = _cfg["model"]
    _hua.ACTIVE_MAX_TOKENS = _cfg["max_tokens"]

    effective_limit = limit
    if effective_limit is not None and effective_limit > MAX_HUS_PER_RUN:
        effective_limit = MAX_HUS_PER_RUN

    path_to_use = base_excel_path
    original_name = uploaded_file.name
    if " + " in original_name:
        original_name = original_name.split(" + ")[0]
    elif ", " in original_name:
        original_name = original_name.split(", ")[0] + ".xlsx"
    output_path = get_next_output_path(path_to_use, original_filename=original_name)

    # Análisis de alto nivel: contar HUs a analizar
    total_hus = count_hus_to_analyze(path_to_use, limit=effective_limit)
    if total_hus == 0:
        st.warning("No se encontraron HUs para analizar en el archivo.")
        st.stop()
    hu_speed_initial = get_hu_speed()

    # Inicializar estado de progreso
    st.session_state.analysis_completed = 0
    st.session_state.analysis_total = total_hus
    st.session_state.analysis_hu_speed = hu_speed_initial or 0
    st.session_state.analysis_last_hu_time = 0
    st.session_state.analysis_eta_sec = 0
    st.session_state.analysis_summary = None
    st.session_state.analysis_error = None
    st.session_state.analysis_done = False
    st.session_state.analysis_running = True
    st.session_state.analysis_temp_paths = [base_excel_path, prev_analysis_path] if prev_analysis_path else [base_excel_path]

    # Dict compartido (evita "missing ScriptRunContext" al no usar st.session_state desde el thread)
    progress_data = {
        "completed": 0, "total": total_hus, "hu_speed": hu_speed_initial or 0,
        "last_time": 0, "eta_sec": 0, "summary": None, "error": None, "done": False,
    }

    def _progress_cb(completed, total, hu_speed, last_time, eta):
        progress_data["completed"] = completed
        progress_data["total"] = total
        progress_data["hu_speed"] = hu_speed
        progress_data["last_time"] = last_time
        progress_data["eta_sec"] = eta

    def _run_analysis():
        try:
            summary = run(
                path_to_use,
                output_path,
                limit=effective_limit,
                silent=True,
                previous_analysis_path=prev_analysis_path,
                progress_callback=_progress_cb,
            )
            progress_data["summary"] = summary
            progress_data["output_path"] = output_path
        except Exception as e:
            err_msg = str(e).lower()
            if "insufficient credits" in err_msg or "credit" in err_msg and "blocked" in err_msg:
                progress_data["error"] = "game_over"
            else:
                progress_data["error"] = e
        finally:
            progress_data["done"] = True

    th = threading.Thread(target=_run_analysis)
    th.start()

    # Barra de progreso en bucle (actualización en tiempo real)
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    while th.is_alive():
        c = progress_data["completed"]
        t = progress_data["total"]
        speed = progress_data["hu_speed"]
        last_t = progress_data["last_time"]
        eta = progress_data["eta_sec"]
        pct = c / t if t else 0
        eta_str = f"{int(eta // 60)}m {int(eta % 60)}s" if eta > 0 else "calculando..."

        with progress_placeholder.container():
            st.markdown(
                '<h3 style="display:flex; align-items:center;">'
                '<span class="analysis-loader">⏳</span> Estado del análisis</h3>',
                unsafe_allow_html=True,
            )
            st.progress(pct, text=f"Analizando HUs: {c} / {t} completadas")
        with status_placeholder.container():
            st.markdown(f"**Progreso:** {c} / {t} HUs analizadas · **Faltan:** {t - c}")
            st.markdown(f"**HU Speed Analysis:** {speed:.1f}s por HU · **Última HU:** {last_t:.1f}s · **ETA:** {eta_str}")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Completadas", f"{c} / {t}", f"{t - c} restantes")
            with m2:
                st.metric("HU Speed Analysis", f"{speed:.1f}s", "promedio por HU")
            with m3:
                st.metric("Tiempo estimado", eta_str, "")
        time.sleep(1)

    th.join()
    # Copiar resultados a session_state (en el hilo principal) para el resto de la app
    st.session_state.analysis_done = progress_data["done"]
    st.session_state.analysis_summary = progress_data.get("summary")
    st.session_state.analysis_output_path = progress_data.get("output_path")
    st.session_state.analysis_error = progress_data.get("error")
    st.session_state.analysis_running = False
    st.rerun()

if st.session_state.get("analysis_done") and st.session_state.get("analysis_error"):
    err = st.session_state.analysis_error
    st.session_state.analysis_done = False
    st.session_state.analysis_running = False
    if st.session_state.get("analysis_temp_paths"):
        for p in st.session_state.analysis_temp_paths:
            if p and os.path.exists(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass
        st.session_state.analysis_temp_paths = []
    if err == "game_over":
        st.markdown(
            '<div style="text-align:center; padding:2rem; font-size:3rem; font-weight:bold; color:#ff4b4b;">🎮 GAME OVER</div>',
            unsafe_allow_html=True,
        )
        st.error("Se te acabaron los tokens o el crédito de tu cuenta Anthropic. Recarga en [Anthropic Console](https://console.anthropic.com/) → Plans & Billing.")
        st.stop()
    else:
        raise err

if st.session_state.get("analysis_done") and st.session_state.get("analysis_summary"):
    st.session_state.summary = st.session_state.analysis_summary
    st.session_state.output_path = st.session_state.analysis_output_path
    st.session_state.analysis_done = False
    st.session_state.analysis_running = False
    if st.session_state.get("analysis_temp_paths"):
        for p in st.session_state.analysis_temp_paths:
            if p and os.path.exists(p):
                try:
                    os.unlink(p)
                except OSError:
                    pass
        st.session_state.analysis_temp_paths = []
    st.success("✅ Análisis completado")
    st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# RESUMEN Y DESCARGA
# ═══════════════════════════════════════════════════════════════════════════

if st.session_state.get("summary") and st.session_state.get("output_path"):
    summary = st.session_state.summary
    output_path = st.session_state.output_path

    if st.button("🔄 Nuevo análisis"):
        st.session_state.analysis_done = False
        st.session_state.summary = None
        st.session_state.output_path = None
        st.session_state.last_file = None
        st.rerun()

    st.markdown("---")
    st.markdown("## 📈 Resumen del análisis")

    # KPIs principales (con defaults por si faltan keys)
    total = summary.get("total_hus", 0)
    avg = summary.get("avg_score", 0)
    exc = summary.get("excelentes", 0)
    inc = summary.get("incompletas", 0)
    crit = summary.get("criticas", 0)

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("HUs analizadas", total)
    with k2:
        st.metric("Score promedio", f"{avg}/100")
    with k3:
        st.metric("🟢 Excelentes", exc)
    with k4:
        st.metric("🟠 En progreso", inc)
    with k5:
        st.metric("🔴 Por definir", crit)

    # Análisis ejecutivo por iniciativa
    executive = summary.get("executive_by_initiative") or {}
    by_sheet = summary.get("by_sheet") or {}
    if by_sheet:
        st.markdown("### 📋 Análisis ejecutivo por iniciativa")
        st.caption("Resumen estilo elevador: cómo van las iniciativas de cada PO, qué mejoró y si hay errores en la data.")
        for sheet_name in by_sheet.keys():
            # Buscar análisis (puede haber variación en el nombre)
            analisis = executive.get(sheet_name)
            if not analisis:
                analisis = next((v for k, v in executive.items() if sheet_name.strip() in k or k.strip() in sheet_name), None)
            if analisis:
                with st.expander(f"**{sheet_name}**", expanded=True):
                    st.markdown(analisis)
            else:
                with st.expander(f"**{sheet_name}**", expanded=False):
                    st.info("No se generó análisis ejecutivo para esta iniciativa.")

    # Distribución por nivel
    st.markdown("### Distribución por nivel de completitud")
    dist_col1, dist_col2 = st.columns(2)
    with dist_col1:
        import pandas as pd
        dist_df = pd.DataFrame([
            {"Nivel": "🟢 Excelente (90-100)", "HUs": exc, "Estado": "Lista para prerefinamiento"},
            {"Nivel": "🔵 Completa (75-89)", "HUs": summary.get("completas", 0), "Estado": "Clarificaciones opcionales"},
            {"Nivel": "🟡 Aceptable (55-74)", "HUs": summary.get("aceptables", 0), "Estado": "Conviene definir más"},
            {"Nivel": "🟠 En progreso (30-54)", "HUs": inc, "Estado": "Fortalecer definición"},
            {"Nivel": "🔴 Por definir (0-29)", "HUs": crit, "Estado": "Oportunidad de definir más"},
        ])
        st.dataframe(dist_df, use_container_width=True, hide_index=True)
    with dist_col2:
        if summary.get("by_sheet"):
            sheet_df = pd.DataFrame([
                {"Iniciativa": k, "HUs": v["count"], "Score prom.": v["avg"]}
                for k, v in summary["by_sheet"].items()
            ])
            st.dataframe(sheet_df, use_container_width=True, hide_index=True)
        else:
            st.info("Sin datos por iniciativa.")

    # Descarga
    st.markdown("---")
    st.markdown("### 📥 Descargar resultado")
    if output_path and os.path.exists(output_path):
        try:
            with open(output_path, "rb") as f:
                file_bytes = f.read()
            st.download_button(
                label="⬇️ Descargar Excel analizado",
                data=file_bytes,
                file_name=os.path.basename(output_path),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )
        except Exception as e:
            st.error(f"Error al leer archivo: {e}")
    else:
        st.warning("El archivo de salida no se encontró.")
