import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_utils import load_sources, get_cluster_coverage, THEMATIC_CLUSTERS


def show():
    sources = load_sources()
    coverage = get_cluster_coverage(sources)

    st.markdown("""
    <div class="library-header">
        <div>
            <p class="library-subtitle">Navigation by Theme</p>
            <h1 class="library-title">Themes</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.9rem; color:#5a6a7a; margin-bottom:1.5rem; max-width:640px;">
        Browse the research corpus by thematic cluster. Each cluster shows the sources mapped to it, 
        their key arguments, and emerging patterns. Clusters with fewer than 2 sources are flagged as coverage gaps.
    </div>
    """, unsafe_allow_html=True)

    # ── Cluster overview grid ─────────────────────────────────────────────────
    if "selected_cluster" not in st.session_state:
        st.session_state.selected_cluster = None

    # Summary grid
    if st.session_state.selected_cluster is None:
        # Invisible button overlaid on each card makes the whole card clickable
        st.markdown("""
        <style>
        div[class*="st-key-clcard_"] { position: relative; }
        div[class*="st-key-clcard_"] div[data-testid="stElementContainer"]:has(div[data-testid="stButton"]) {
            position: absolute; inset: 0; z-index: 1; margin: 0;
            width: auto !important; height: auto !important;
        }
        div[class*="st-key-clcard_"] div[data-testid="stButton"],
        div[class*="st-key-clcard_"] div[data-testid="stButton"] button {
            width: 100%; height: 100%; min-height: 0; margin: 0; padding: 0;
        }
        div[class*="st-key-clcard_"] div[data-testid="stButton"] button {
            opacity: 0; cursor: pointer;
        }
        div[class*="st-key-clcard_"]:hover .cluster-card { background: #f6f8fb !important; }
        div[class*="st-key-clcard_"]:hover .cluster-card-arrow { color: #1a3a5c !important; }
        </style>
        """, unsafe_allow_html=True)
        cols = st.columns(3)
        for i, cluster in enumerate(THEMATIC_CLUSTERS):
            srcs = coverage.get(cluster, [])
            n = len(srcs)
            gap_badge = ' <span style="color:#c8952a; font-size:0.72rem;">thin</span>' if n < 2 else ""
            strength = min(n / 5.0, 1.0)
            bar_width = max(int(strength * 100), 4)

            with cols[i % 3]:
                with st.container(key=f"clcard_{i}"):
                    st.markdown(f"""
                    <div class="cluster-card" style="position:relative; background:white; border:1px solid #ddd8cc; border-top:3px solid {'#1a3a5c' if n >= 2 else '#c8952a'};
                         border-radius:4px; padding:1rem; margin-bottom:0.8rem; min-height:110px;">
                        <div style="font-family:'Playfair Display',serif; font-size:1rem; font-weight:600; color:#1a3a5c;
                             line-height:1.3; margin-bottom:0.5rem;">{cluster}{gap_badge}</div>
                        <div style="font-size:0.78rem; color:#8a9ab0; margin-bottom:0.5rem;">{n} source{"s" if n!=1 else ""}</div>
                        <div style="background:#eef2f7; border-radius:2px; height:4px; width:100%;">
                            <div style="background:#1a3a5c; height:4px; border-radius:2px; width:{bar_width}%;"></div>
                        </div>
                        <div class="cluster-card-arrow" style="position:absolute; bottom:0.65rem; right:0.8rem; color:#b0bcc9; font-size:0.85rem;">→</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"Explore →", key=f"cluster_{i}"):
                        st.session_state.selected_cluster = cluster
                        st.rerun()
    else:
        # ── Individual cluster view ───────────────────────────────────────────
        cluster = st.session_state.selected_cluster
        srcs = coverage.get(cluster, [])

        if st.button("← Back to all themes"):
            st.session_state.selected_cluster = None
            st.rerun()

        st.markdown(f"""
        <div style="margin:1rem 0 1.5rem 0;">
            <div style="font-family:'Playfair Display',serif; font-size:1.8rem; font-weight:700; color:#1a3a5c;">{cluster}</div>
            <div style="font-size:0.88rem; color:#8a9ab0; margin-top:0.3rem;">{len(srcs)} source{"s" if len(srcs)!=1 else ""} in this cluster</div>
        </div>
        """, unsafe_allow_html=True)

        if not srcs:
            st.markdown("""
            <div style="background:#fff8ec; border:1px solid #e6c87a; border-left:3px solid #c8952a; 
                 border-radius:3px; padding:1rem; font-size:0.9rem; color:#5a3a0a;">
                No sources are currently mapped to this cluster. This is a documented research gap.
            </div>
            """, unsafe_allow_html=True)
            return

        col_list, col_args = st.columns([1, 1.6])

        with col_list:
            st.markdown('<div style="font-family:\'Playfair Display\',serif; font-size:1rem; font-weight:600; color:#1a3a5c; margin-bottom:0.8rem;">Sources</div>', unsafe_allow_html=True)
            
            if "cluster_selected_source" not in st.session_state:
                st.session_state.cluster_selected_source = None

            for s in srcs:
                is_sel = st.session_state.cluster_selected_source == s["id"]
                bg = "#fdf7ee" if is_sel else "white"
                border = "#c8952a" if is_sel else "#1a3a5c"
                st.markdown(f"""
                <div style="background:{bg}; border:1px solid #ddd8cc; border-left:3px solid {border};
                     border-radius:3px; padding:0.8rem 1rem; margin-bottom:0.5rem;">
                    <div style="font-family:'Playfair Display',serif; font-size:0.88rem; font-weight:600; color:#1a3a5c;">{s['title']}</div>
                    <div style="font-size:0.78rem; color:#8a9ab0;">{s['author']} · {s['year']}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("View arguments →", key=f"carg_{s['id']}"):
                    st.session_state.cluster_selected_source = s["id"]
                    st.rerun()

        with col_args:
            sel_id = st.session_state.get("cluster_selected_source")
            if sel_id:
                sel = next((s for s in srcs if s["id"] == sel_id), None)
                if sel:
                    st.markdown(f"""
                    <div style="font-family:'Playfair Display',serif; font-size:1rem; font-weight:600; 
                         color:#1a3a5c; margin-bottom:0.8rem;">{sel['title']}</div>
                    """, unsafe_allow_html=True)

                    st.markdown('<div class="detail-section-title">Key Arguments</div>', unsafe_allow_html=True)
                    for arg in sel.get("key_arguments", []):
                        st.markdown(f"""
                        <div style="padding:0.6rem 0.8rem 0.6rem 1rem; border-left:2px solid #c8d4e0; 
                             margin-bottom:0.5rem; font-size:0.88rem; color:#2a2a2a; line-height:1.5;">
                            {arg}
                        </div>
                        """, unsafe_allow_html=True)

                    lessons = [l for l in sel.get("lessons_learned", [])]
                    if lessons:
                        st.markdown('<div class="detail-section-title">Lessons Learned Candidates</div>', unsafe_allow_html=True)
                        for l in lessons:
                            tag_class = "tag-lesson-sd" if l.get("tag") == "SOURCE-DERIVED" else "tag-lesson-ai"
                            st.markdown(f"""
                            <div style="padding:0.6rem; background:#fafaf8; border:1px solid #e0dbd2; border-radius:3px; margin-bottom:0.5rem;">
                                <span class="tag {tag_class}">{l.get('tag','')}</span>
                                <div style="font-size:0.85rem; color:#2a2a2a; margin-top:0.35rem; line-height:1.5;">{l['text']}</div>
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding:3rem 1rem; text-align:center; color:#8a9ab0;">
                    <div style="font-size:0.9rem;">Select a source to view its arguments and lessons for this theme</div>
                </div>
                """, unsafe_allow_html=True)
