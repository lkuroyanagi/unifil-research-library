import streamlit as st
import sys
import uuid
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_utils import load_sources, load_gaps, save_gaps, get_inferred_gaps, THEMATIC_CLUSTERS, GitHubSaveError


def is_editor():
    return st.session_state.get("editor_mode", False)

STATUS_COLORS = {
    "Open": "#c8952a",
    "Being addressed": "#1a5c9c",
    "Filled": "#2a7a2a",
}

def show():
    sources = load_sources()
    manual_gaps = load_gaps()
    auto_gaps = get_inferred_gaps(sources)

    st.markdown("""
    <div class="library-header">
        <div>
            <p class="library-subtitle">Research Coverage Assessment</p>
            <h1 class="library-title">Gaps Register</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.9rem; color:#5a6a7a; margin-bottom:1.5rem; max-width:640px;">
        This register tracks known gaps in the research corpus — both those identified manually
        and those inferred automatically from thematic cluster coverage. Use it to guide future source collection.
    </div>
    """, unsafe_allow_html=True)

    # Summary metrics
    total_manual = len(manual_gaps)
    total_auto = len(auto_gaps)
    open_count = len([g for g in manual_gaps if g.get("status") == "Open"]) + total_auto

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-number">{total_manual}</div>
            <div class="metric-label">Manual gaps</div>
        </div>
        <div class="metric-card">
            <div class="metric-number">{total_auto}</div>
            <div class="metric-label">Auto-inferred gaps</div>
        </div>
        <div class="metric-card">
            <div class="metric-number">{open_count}</div>
            <div class="metric-label">Open gaps</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <style>
    [data-testid="stHorizontalBlock"] { gap: 0rem !important; }
    </style>
    """, unsafe_allow_html=True)

    col_gaps, col_add = st.columns([2, 1])

    with col_gaps:
        st.markdown('<div style="font-family:\'Playfair Display\',serif; font-size:1.1rem; font-weight:600; color:#1a3a5c; margin-bottom:0.8rem;">Identified Gaps</div>', unsafe_allow_html=True)

        for g in manual_gaps:
            gap_id = g["id"]
            edit_key = f"gap_editing_{gap_id}"
            status = g.get("status", "Open")

            if st.session_state.get(edit_key):
                with st.form(f"gap_edit_form_{gap_id}"):
                    st.markdown(f'<div style="font-size:0.78rem; font-weight:600; color:#1a3a5c; margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:0.06em;">Editing gap</div>', unsafe_allow_html=True)
                    new_title = st.text_input("Gap title", value=g['title'], key=f"gap_edit_title_{gap_id}")
                    new_desc = st.text_area("Description", value=g.get('description', ''), height=100, key=f"gap_edit_desc_{gap_id}")
                    new_clusters = st.multiselect(
                        "Related thematic clusters", THEMATIC_CLUSTERS,
                        default=g.get('thematic_clusters', []),
                        key=f"gap_edit_clusters_{gap_id}"
                    )
                    new_status = st.selectbox(
                        "Status", ["Open", "Being addressed", "Filled"],
                        index=["Open", "Being addressed", "Filled"].index(status),
                        key=f"gap_edit_status_{gap_id}"
                    )
                    col_save, col_cancel, _ = st.columns([1, 1, 3])
                    with col_save:
                        save_clicked = st.form_submit_button("Save")
                    with col_cancel:
                        cancel_clicked = st.form_submit_button("Cancel")

                if save_clicked:
                    for gap in manual_gaps:
                        if gap["id"] == gap_id:
                            gap["title"] = new_title
                            gap["description"] = new_desc
                            gap["thematic_clusters"] = new_clusters
                            gap["status"] = new_status
                            break
                    try:
                        save_gaps(manual_gaps)
                    except GitHubSaveError as e:
                        st.error(str(e))
                        st.stop()
                    st.session_state[edit_key] = False
                    st.rerun()
                if cancel_clicked:
                    st.session_state[edit_key] = False
                    st.rerun()
            else:
                status_color = STATUS_COLORS.get(status, "#888")
                clusters_html = "".join([f'<span class="tag tag-cluster" style="font-size:0.7rem;">{c}</span>' for c in g.get("thematic_clusters", [])])

                st.markdown(f"""
                <div class="gap-card">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.4rem;">
                        <div class="gap-title">{g['title']}</div>
                        <span style="font-size:0.75rem; font-weight:600; color:{status_color}; white-space:nowrap; margin-left:1rem;">{status}</span>
                    </div>
                    <div class="gap-desc">{g.get('description','')}</div>
                    <div style="margin-top:0.6rem;">{clusters_html}</div>
                    <div style="font-size:0.72rem; color:#aaa; margin-top:0.4rem;">Added by {g.get('added_by','—')} · {g.get('date_added','')}</div>
                </div>
                """, unsafe_allow_html=True)

                col_status, col_edit, col_del = st.columns([5.5, 0.8, 0.7])
                with col_status:
                    new_status = st.selectbox(
                        "Update status",
                        ["Open", "Being addressed", "Filled"],
                        index=["Open", "Being addressed", "Filled"].index(status),
                        key=f"status_{gap_id}",
                        label_visibility="collapsed"
                    )
                    if new_status != status:
                        for gap in manual_gaps:
                            if gap["id"] == gap_id:
                                gap["status"] = new_status
                        try:
                            save_gaps(manual_gaps)
                        except GitHubSaveError as e:
                            st.error(str(e))
                            st.stop()
                        st.rerun()
                with col_edit:
                    if is_editor() and st.button("Edit", key=f"gap_edit_btn_{gap_id}"):
                        st.session_state[edit_key] = True
                        st.rerun()
                with col_del:
                    if is_editor() and st.button("🗑", key=f"gap_del_btn_{gap_id}"):
                        manual_gaps = [g for g in manual_gaps if g["id"] != gap_id]
                        try:
                            save_gaps(manual_gaps)
                        except GitHubSaveError as e:
                            st.error(str(e))
                            st.stop()
                        st.rerun()

        # Auto-inferred gaps
        if auto_gaps:
            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            st.markdown("""
            <div style="font-family:'Playfair Display',serif; font-size:1.1rem; font-weight:600; color:#1a3a5c; margin-bottom:0.4rem;">Auto-inferred Gaps</div>
            <div style="font-size:0.82rem; color:#8a9ab0; margin-bottom:0.8rem;">Clusters with fewer than 2 sources in the corpus.</div>
            """, unsafe_allow_html=True)

            for g in auto_gaps:
                clusters_html = "".join([f'<span class="tag tag-cluster" style="font-size:0.7rem;">{c}</span>' for c in g.get("thematic_clusters", [])])
                st.markdown(f"""
                <div class="gap-card gap-auto">
                    <div class="gap-title">{g['title']}</div>
                    <div class="gap-desc">{g.get('description','')}</div>
                    <div style="margin-top:0.5rem;">{clusters_html}</div>
                </div>
                """, unsafe_allow_html=True)

    with col_add:
        if is_editor():
            st.markdown("""
            <div style="font-family:'Playfair Display',serif; font-size:1.1rem; font-weight:600;
                 color:#1a3a5c; margin-bottom:0.8rem;">Add a Gap Manually</div>
            """, unsafe_allow_html=True)

            with st.form("add_gap_form", clear_on_submit=True):
                gap_title = st.text_input("Gap title *", placeholder="e.g. Civilian perspectives from South Lebanon")
                gap_desc = st.text_area("Description *", placeholder="Describe what is missing and why it matters…", height=100)
                gap_clusters = st.multiselect("Related thematic clusters", THEMATIC_CLUSTERS)
                gap_author = st.text_input("Added by", placeholder="Your name")

                submitted = st.form_submit_button("Add to register")
                if submitted:
                    if gap_title and gap_desc:
                        new_gap = {
                            "id": f"gap_{uuid.uuid4().hex[:8]}",
                            "title": gap_title,
                            "description": gap_desc,
                            "thematic_clusters": gap_clusters,
                            "status": "Open",
                            "source": "Manual",
                            "added_by": gap_author or "Anonymous",
                            "date_added": str(date.today())
                        }
                        manual_gaps.append(new_gap)
                        try:
                            save_gaps(manual_gaps)
                        except GitHubSaveError as e:
                            st.error(str(e))
                            st.stop()
                        st.success("Gap added to register.")
                        st.rerun()
                    else:
                        st.error("Please provide a title and description.")
