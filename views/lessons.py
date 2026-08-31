import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_utils import load_sources, save_sources, THEMATIC_CLUSTERS, GitHubSaveError


def is_editor():
    return st.session_state.get("editor_mode", False)

def get_all_lessons(sources, clusters=None, tag_filter=None, search=None):
    lessons = []
    for s in sources:
        for idx, l in enumerate(s.get("lessons_learned", [])):
            text = l.get("text", "")
            tag = l.get("tag", "")
            source_clusters = s.get("thematic_clusters", [])

            if clusters and not any(c in source_clusters for c in clusters):
                continue
            if tag_filter and tag not in tag_filter:
                continue
            if search and search.lower() not in text.lower():
                continue

            lessons.append({
                "text": text,
                "tag": tag,
                "lesson_idx": idx,
                "source_id": s.get("id", ""),
                "source_title": s.get("title", ""),
                "source_author": s.get("author", ""),
                "source_year": s.get("year", ""),
                "source_type": s.get("source_type", ""),
                "thematic_clusters": source_clusters,
            })
    return lessons


def show():
    sources = load_sources()
    all_lessons = get_all_lessons(sources)

    st.markdown("""
    <div class="library-header">
        <div>
            <p class="library-subtitle">Extracted from the Corpus</p>
            <h1 class="library-title">Lessons Learned</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.9rem; color:#5a6a7a; margin-bottom:1.5rem; max-width:680px;">
        All lessons learned candidates extracted from the corpus, organised by theme.
        <span style="color:#2a7a2a; font-weight:600;">Source-derived</span> lessons come directly from what authors argue.
        <span style="color:#8b3a1a; font-weight:600;">Analytical inferences</span> are conclusions drawn by the researcher from the source material.
    </div>
    """, unsafe_allow_html=True)

    # Metrics
    n_total = len(all_lessons)
    n_sd = sum(1 for l in all_lessons if l["tag"] == "SOURCE-DERIVED")
    n_ai = sum(1 for l in all_lessons if l["tag"] == "ANALYTICAL INFERENCE")
    n_sources = len(set(l["source_id"] for l in all_lessons))

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-number">{n_total}</div>
            <div class="metric-label">Total LL candidates</div>
        </div>
        <div class="metric-card">
            <div class="metric-number">{n_sd}</div>
            <div class="metric-label">Source-derived</div>
        </div>
        <div class="metric-card">
            <div class="metric-number">{n_ai}</div>
            <div class="metric-label">Analytical inferences</div>
        </div>
        <div class="metric-card">
            <div class="metric-number">{n_sources}</div>
            <div class="metric-label">Contributing sources</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Add lesson form ───────────────────────────────────────────────────────
    if is_editor():
        source_options = {s.get("id", ""): f"{s.get('author', 'Unknown')}, {s.get('year', '')} — {s.get('title', '')[:60]}" for s in sources}
        source_ids = list(source_options.keys())
        source_labels = list(source_options.values())
        with st.expander("+ Add new lesson learned"):
            with st.form("ll_add_form"):
                add_source_idx = st.selectbox(
                    "Source",
                    range(len(source_labels)),
                    format_func=lambda i: source_labels[i],
                    key="ll_add_source",
                )
                add_text = st.text_area("Lesson text", height=100, key="ll_add_text", placeholder="Enter the lesson learned…")
                add_tag = st.selectbox(
                    "Type",
                    ["SOURCE-DERIVED", "ANALYTICAL INFERENCE"],
                    key="ll_add_tag",
                )
                col_add, col_cancel, _ = st.columns([1, 1, 4])
                with col_add:
                    add_clicked = st.form_submit_button("Add lesson")
                with col_cancel:
                    add_cancel = st.form_submit_button("Cancel")

            if add_clicked and add_text.strip():
                sid = source_ids[add_source_idx]
                for s in sources:
                    if s.get("id") == sid:
                        if "lessons_learned" not in s:
                            s["lessons_learned"] = []
                        s["lessons_learned"].append({"text": add_text.strip(), "tag": add_tag})
                        break
                try:
                    save_sources(sources)
                except GitHubSaveError as e:
                    st.error(str(e))
                    st.stop()
                for k in ("ll_add_source", "ll_add_text", "ll_add_tag"):
                    st.session_state.pop(k, None)
                st.rerun()
            elif add_clicked and not add_text.strip():
                st.warning("Please enter a lesson text before saving.")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Filters ───────────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1.5])
    with col_f1:
        search = st.text_input("Search lessons", placeholder="e.g. force protection, civilian, mandate…", key="ll_search")
    with col_f2:
        tag_filter = st.multiselect(
            "Type",
            ["SOURCE-DERIVED", "ANALYTICAL INFERENCE"],
            key="ll_tag"
        )
    with col_f3:
        cluster_filter = st.multiselect(
            "Thematic cluster",
            THEMATIC_CLUSTERS,
            key="ll_cluster"
        )

    filtered = get_all_lessons(
        sources,
        clusters=cluster_filter if cluster_filter else None,
        tag_filter=tag_filter if tag_filter else None,
        search=search if search else None,
    )

    st.markdown(f'<div style="font-size:0.82rem; color:#6b7c8d; margin: 0.8rem 0; letter-spacing:0.04em; text-transform:uppercase;">{len(filtered)} lesson{"s" if len(filtered)!=1 else ""} shown</div>', unsafe_allow_html=True)

    # ── View toggle ───────────────────────────────────────────────────────────
    view_mode = st.radio(
        "View as",
        ["By theme", "Flat list"],
        horizontal=True,
        key="ll_view"
    )

    if view_mode == "By theme":
        cluster_lessons = {c: [] for c in THEMATIC_CLUSTERS}
        untagged = []
        for l in filtered:
            placed = False
            for c in l["thematic_clusters"]:
                if c in cluster_lessons:
                    cluster_lessons[c].append(l)
                    placed = True
            if not placed:
                untagged.append(l)

        # Use a global render counter so duplicate lessons across clusters get unique keys
        render_idx = 0
        for cluster, lessons in cluster_lessons.items():
            if not lessons:
                continue
            st.markdown(f"""
            <div style="font-family:'Playfair Display',serif; font-size:1.1rem; font-weight:600;
                 color:#1a3a5c; margin: 1.5rem 0 0.8rem 0; padding-bottom:0.3rem;
                 border-bottom:2px solid #1a3a5c;">{cluster}
                 <span style="font-size:0.8rem; font-weight:400; color:#8a9ab0; margin-left:0.5rem;">{len(lessons)}</span>
            </div>
            """, unsafe_allow_html=True)
            for l in lessons:
                render_lesson_card(l, sources, render_idx)
                render_idx += 1

        if untagged:
            st.markdown('<div style="font-family:\'Playfair Display\',serif; font-size:1rem; font-weight:600; color:#8a9ab0; margin:1.5rem 0 0.8rem 0;">Other</div>', unsafe_allow_html=True)
            for l in untagged:
                render_lesson_card(l, sources, render_idx)
                render_idx += 1

    else:
        if not filtered:
            st.markdown('<div style="font-size:0.9rem; color:#8a9ab0; padding:2rem 0;">No lessons match the current filters.</div>', unsafe_allow_html=True)
        for i, l in enumerate(filtered):
            render_lesson_card(l, sources, i)


def render_lesson_card(l, sources, render_idx: int = 0):
    tag = l.get("tag", "")
    is_sd = tag == "SOURCE-DERIVED"
    tag_class = "tag-lesson-sd" if is_sd else "tag-lesson-ai"
    border_color = "#9ac99a" if is_sd else "#c99a8a"
    bg_color = "#f8fdf8" if is_sd else "#fdf8f6"
    source_id = l.get("source_id", "")
    lesson_idx = l.get("lesson_idx", 0)
    # Include render_idx so a lesson shown under multiple themes gets unique widget keys
    card_key = f"{source_id}_{lesson_idx}_{render_idx}"
    edit_key = f"ll_editing_{source_id}_{lesson_idx}"

    clusters_html = "".join([
        f'<span class="tag tag-cluster" style="font-size:0.68rem;">{c}</span>'
        for c in l.get("thematic_clusters", [])[:2]
    ])

    st.markdown(f"""
    <div style="background:{bg_color}; border:1px solid #e0dbd2; border-left:3px solid {border_color};
         border-radius:3px; padding:0.9rem 1.1rem; margin-bottom:0.3rem;">
        <div style="margin-bottom:0.5rem;">
            <span class="tag {tag_class}">{tag}</span>
        </div>
        <div style="font-size:0.92rem; color:#1c1c1c; line-height:1.6; margin-bottom:0.6rem;">
            {l['text']}
        </div>
        <div style="display:flex; align-items:center; gap:0.8rem; flex-wrap:wrap;">
            <span style="font-size:0.75rem; color:#8a9ab0; font-style:italic;">
                — {l['source_author']}, {l['source_year']} · {l['source_type']}
            </span>
            {clusters_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get(edit_key):
        with st.form(f"ll_edit_form_{card_key}"):
            new_text = st.text_area("Lesson text", value=l['text'], height=100, key=f"ll_edit_text_{card_key}")
            new_tag = st.selectbox(
                "Type",
                ["SOURCE-DERIVED", "ANALYTICAL INFERENCE"],
                index=0 if tag == "SOURCE-DERIVED" else 1,
                key=f"ll_edit_tag_{card_key}"
            )
            col_save, col_cancel, _ = st.columns([1, 1, 4])
            with col_save:
                save_clicked = st.form_submit_button("Save")
            with col_cancel:
                cancel_clicked = st.form_submit_button("Cancel")

        if save_clicked:
            for s in sources:
                if s.get("id") == source_id:
                    s["lessons_learned"][lesson_idx]["text"] = new_text
                    s["lessons_learned"][lesson_idx]["tag"] = new_tag
                    break
            try:
                save_sources(sources)
            except GitHubSaveError as e:
                st.error(str(e))
                st.stop()
            st.session_state[edit_key] = False
            st.rerun()
        if cancel_clicked:
            st.session_state[edit_key] = False
            st.rerun()
    elif is_editor():
        _, col_edit, col_del = st.columns([7, 1.2, 0.8])
        with col_edit:
            if st.button("Edit", key=f"ll_edit_btn_{card_key}"):
                st.session_state[edit_key] = True
                st.rerun()
        with col_del:
            if st.button("🗑", key=f"ll_del_btn_{card_key}"):
                for s in sources:
                    if s.get("id") == source_id:
                        del s["lessons_learned"][lesson_idx]
                        break
                try:
                    save_sources(sources)
                except GitHubSaveError as e:
                    st.error(str(e))
                    st.stop()
                st.rerun()

    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
