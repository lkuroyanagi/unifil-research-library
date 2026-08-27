import streamlit as st
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

sys.path.insert(0, str(Path(__file__).parent))


def is_editor():
    return st.session_state.get("editor_mode", False)


def check_editor_password(pwd):
    try:
        correct = st.secrets["EDITOR_PASSWORD"]
    except Exception:
        correct = "unifil2026"  # local fallback
    return pwd == correct

st.set_page_config(
    page_title="UNIFIL Research Library",
    page_icon="🇺🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* ── Sidebar ─────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #1B2A4A !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
    min-width: 260px !important;
    max-width: 260px !important;
}
[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}

/* Nav radio items */
[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 1px !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    font-size: 9px !important;
    font-weight: 400 !important;
    color: #CBD5E1 !important;
    padding: 8px 10px !important;
    border-radius: 5px !important;
    cursor: pointer !important;
    transition: background 0.12s !important;
    letter-spacing: 0 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(255,255,255,0.04) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: rgba(255,255,255,0.08) !important;
    font-weight: 600 !important;
    color: #fff !important;
    border-left: 3px solid #0077B6 !important;
    padding-left: 7px !important;
}
/* Hide native radio circles */
[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] {
    display: none !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08) !important;
}

/* ── Main content background ─────────────────────────────────────── */
[data-testid="stMain"] {
    background: #F5F4F0;
}
.main .block-container {
    background: #F5F4F0;
}

/* ── Design tokens ───────────────────────────────────────────────── */
/* Used by non-library pages that still use Streamlit widgets */

/* Tags */
.tag {
    display: inline-block;
    background: #ECEAE4;
    color: #4A5568;
    border-radius: 3px;
    font-size: 0.72rem;
    padding: 3px 10px;
    margin: 2px;
    font-family: 'IBM Plex Sans', sans-serif;
}
.tag-cluster {
    background: #EAF1F9;
    color: #3B6B9E;
}
.tag-actor {
    background: #f5ede0;
    color: #7a4510;
    border: 1px solid #d4a96a;
}
.tag-lesson-sd {
    background: #E8F5EE;
    color: #2E7D5A;
}
.tag-lesson-ai {
    background: #FEF3E2;
    color: #B45309;
}

/* Detail panel */
.detail-section-title {
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #9A968E;
    border-bottom: 1px solid #E8E5DE;
    padding-bottom: 0.3rem;
    margin: 1.2rem 0 0.5rem 0;
}
.detail-body {
    font-size: 0.9rem;
    color: #374151;
    line-height: 1.6;
}

/* Metric cards (other pages) */
.metric-row {
    display: flex;
    gap: 10px;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: #fff;
    border: 1px solid #E8E5DE;
    border-radius: 6px;
    padding: 20px 24px;
    flex: 1;
}
.metric-number {
    font-size: 2rem;
    font-weight: 700;
    color: #1a1a2e;
    line-height: 1;
    font-variant-numeric: tabular-nums;
}
.metric-label {
    font-size: 0.68rem;
    color: #8A8880;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 6px;
    font-weight: 600;
}

/* Filter panel (other pages) */
.filter-panel {
    background: #FAFAF8;
    border: 1px solid #E8E5DE;
    border-radius: 6px;
    padding: 1rem;
    margin-bottom: 1rem;
}

/* Bias flag */
.bias-flag {
    background: #fff8ec;
    border: 1px solid #e6c87a;
    border-left: 3px solid #0077B6;
    border-radius: 3px;
    padding: 0.7rem 1rem;
    font-size: 0.86rem;
    color: #374151;
    line-height: 1.5;
}

/* Gap card */
.gap-card {
    background: white;
    border: 1px solid #E8E5DE;
    border-left: 4px solid #0077B6;
    border-radius: 6px;
    padding: 1rem 1.3rem;
    margin-bottom: 0.7rem;
}
.gap-auto { border-left-color: #9ab8d0; }
.gap-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #1a1a2e;
    margin: 0 0 0.3rem 0;
}
.gap-desc {
    font-size: 0.85rem;
    color: #5A6475;
    line-height: 1.5;
}

/* Divider */
.section-divider {
    border: none;
    border-top: 1px solid #E8E5DE;
    margin: 1.5rem 0;
}

/* Scrollable containers */
.source-list-container, .source-grid-container {
    padding-right: 0.3rem;
}

/* ── Streamlit widget overrides ──────────────────────────────────── */
.stButton > button {
    background: transparent !important;
    border: 1px solid #c8d0d8 !important;
    color: #4a5a6a !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 4px 12px !important;
    border-radius: 3px !important;
    box-shadow: none !important;
}
.stButton > button:hover {
    border-color: #1a3a5c !important;
    color: #1a3a5c !important;
    background: transparent !important;
}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 4px;
    border-color: #DDD9D0;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.9rem;
    background: #FAFAF8;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #0077B6 !important;
    box-shadow: 0 0 0 2px rgba(0,119,182,0.15) !important;
}
div[data-testid="stExpander"] {
    border: 1px solid #E8E5DE;
    border-radius: 6px;
    background: #fff;
}
[data-testid="stSelectbox"] > div > div {
    border-color: #DDD9D0;
    border-radius: 4px;
    background: #FAFAF8;
}
[data-testid="stMultiSelect"] > div > div {
    border-color: #DDD9D0;
    border-radius: 4px;
    background: #FAFAF8;
}

/* Library header (detail/edit view) */
.library-header { padding: 1.5rem 0 1rem; margin-bottom: 1.5rem; border-bottom: 1px solid #E8E5DE; }
.library-title  { font-size: 1.6rem; font-weight: 700; color: #1a1a2e; }
.library-subtitle { font-size: 0.72rem; color: #9A968E; text-transform: uppercase; letter-spacing: 0.08em; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:22px 20px 18px; border-bottom:1px solid rgba(255,255,255,0.06);">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
            <div style="width:28px; height:28px; border-radius:50%; background:#0077B6; display:flex; align-items:center; justify-content:center; flex-shrink:0;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <circle cx="12" cy="12" r="9" stroke="white" stroke-width="1.5"/>
                    <path d="M12 3c-2.5 2.5-2.5 15.5 0 18M12 3c2.5 2.5 2.5 15.5 0 18M3 12h18" stroke="white" stroke-width="1.5"/>
                </svg>
            </div>
            <span style="font-size:14px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:rgba(255,255,255,0.5); font-family:'IBM Plex Sans',sans-serif;">UNIFIL</span>
        </div>
        <div style="font-size:22px; font-weight:700; color:#fff; margin-top:8px; letter-spacing:-0.3px; font-family:'IBM Plex Sans',sans-serif;">Lessons Learned</div>
    </div>
    <div style="height:10px;"></div>
    """, unsafe_allow_html=True)

    st.markdown('<hr style="border-color:rgba(255,255,255,0.08); margin:0 0 0 0; display:none;">', unsafe_allow_html=True)
    
    page = st.radio(
        "Navigate",
        [
            "Sources",
            "➕ Add Source",
            "Resolutions",
            "Themes",
            "Timeline",
            "Actors",
            "Lessons Learned",
            "Research Gaps",
            "Mind Map",
        ],
        label_visibility="collapsed"
    )

    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

    st.sidebar.markdown("---")
    if is_editor():
        st.sidebar.markdown(
            '<div style="font-size:0.72rem; color:#4a9a4a; padding:4px 0;">',
            unsafe_allow_html=True,
        )
        st.sidebar.markdown("✓ Editor mode active")
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
        if st.sidebar.button("Lock", key="lock_btn"):
            st.session_state.editor_mode = False
            st.rerun()
    else:
        with st.sidebar.expander("🔒 Editor login"):
            pwd = st.text_input("Password", type="password", key="editor_pwd_input")
            if st.button("Unlock", key="unlock_btn"):
                if check_editor_password(pwd):
                    st.session_state.editor_mode = True
                    st.rerun()
                else:
                    st.error("Incorrect password")

# ── Page routing ──────────────────────────────────────────────────────────────
if page == "Sources":
    from views.library import show
    show()
elif page == "➕ Add Source":
    from views.add_source import show
    show()
elif page == "Resolutions":
    from views.mandates import show
    show()
elif page == "Themes":
    from views.thematic import show
    show()
elif page == "Timeline":
    from views.timeline import show
    show()
elif page == "Actors":
    from views.actors_profiles import show
    show()
elif page == "Lessons Learned":
    from views.lessons import show
    show()
elif page == "Research Gaps":
    from views.gaps import show
    show()
elif page == "Mind Map":
    from views.mindmap import show
    show()

# ── Floating chat widget (all pages) ──────────────────────────────────────────
from views.chat_widget import render_chat_widget
render_chat_widget()
