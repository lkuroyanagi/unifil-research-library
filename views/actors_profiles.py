import json
import streamlit as st
from pathlib import Path


def is_editor():
    return st.session_state.get("editor_mode", False)

DATA_PATH = Path(__file__).parent.parent / "data" / "actors_profiles.json"

ALPHABET = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

# The six canonical actor categories, in the order they should appear
# throughout the UI (filter dropdown, edit dropdown, etc.).
CATEGORIES = [
    "UN & International",
    "Non-State Armed Groups",
    "Lebanese Political",
    "Israeli Actors",
    "Palestinian Actors",
    "International Actors",
]

CATEGORY_COLORS = {
    "UN & International":     "#1a3a5c",
    "Non-State Armed Groups": "#dc2626",
    "Lebanese Political":     "#d97706",
    "Israeli Actors":         "#64b5f6",
    "Palestinian Actors":     "#7b3fa0",
    "International Actors":   "#16a34a",
}


def first_sentence(text):
    if not text:
        return ""
    for sep in (". ", "! ", "? "):
        idx = text.find(sep)
        if idx != -1:
            return text[: idx + 1]
    return text[:160] + ("…" if len(text) > 160 else "")


def show():
    actors = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    actors_sorted = sorted(actors, key=lambda x: x["name"].upper())
    all_categories = CATEGORIES

    # ── Page-scoped CSS ───────────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* ── Custom HTML accordion card ─────────────────────────────── */
    details.ap-card {
        background: white;
        border: 1px solid #ddd8cc;
        /* border-left is set per-card via inline style */
        border-radius: 4px;
        margin-bottom: 0.55rem;
        box-shadow: none;
        overflow: hidden;
    }
    details.ap-card summary {
        padding: 0.72rem 1rem;
        cursor: pointer;
        list-style: none;
        display: flex;
        align-items: center;
        gap: 0.6rem;
        font-family: 'Playfair Display', serif;
        font-size: 0.95rem;
        font-weight: 700;
        color: #1a3a5c;
        user-select: none;
        line-height: 1.3;
    }
    details.ap-card summary:hover { background: #fafaf7; }
    details.ap-card summary::marker,
    details.ap-card summary::-webkit-details-marker { display: none; }
    details.ap-card summary::before {
        content: '›';
        font-size: 1.25rem;
        color: #8a9ab0;
        transition: transform 0.15s ease;
        flex-shrink: 0;
        line-height: 1;
    }
    details.ap-card[open] summary::before { transform: rotate(90deg); }
    details.ap-card > .ap-card-body {
        padding: 0.1rem 1rem 0.9rem 1rem;
        border-top: 1px solid #eeebe4;
    }

    /* Expander for edit mode — keep existing style */
    div[data-testid="stExpander"] {
        background: white !important;
        border: 1px solid #ddd8cc !important;
        border-left: 3px solid #c8d4e0 !important;
        border-radius: 4px !important;
        margin-bottom: 0.55rem !important;
        box-shadow: none !important;
    }
    div[data-testid="stExpander"] summary {
        padding: 0.75rem 1rem !important;
    }
    div[data-testid="stExpander"] summary p {
        font-family: 'Playfair Display', serif !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #1a3a5c !important;
        margin: 0 !important;
    }
    div[data-testid="stExpander"] > details > div[data-testid="stExpanderDetails"] {
        padding: 0 1rem 0.9rem 1rem !important;
    }

    /* Letter divider */
    .ap-letter {
        font-family: 'Playfair Display', serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: #1a3a5c;
        border-bottom: 2px solid #ddd8cc;
        padding-bottom: 0.15rem;
        margin: 1.4rem 0 0.75rem 0;
        opacity: 0.9;
    }
    /* A–Z index */
    .ap-index {
        position: sticky;
        top: 60px;
        padding-top: 0.5rem;
    }
    .ap-index-label {
        font-size: 0.62rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #8a9ab0;
        font-weight: 600;
        text-align: center;
        margin-bottom: 0.6rem;
    }
    .ap-index a {
        display: block;
        text-align: center;
        font-size: 0.78rem;
        font-weight: 600;
        color: #1a3a5c;
        text-decoration: none;
        padding: 0.18rem 0;
        border-radius: 3px;
        letter-spacing: 0.02em;
        line-height: 1.4;
    }
    .ap-index a:hover { background: rgba(26,58,92,0.08); }
    .ap-index .ap-dim {
        display: block;
        text-align: center;
        font-size: 0.78rem;
        color: #d4dbe4;
        padding: 0.18rem 0;
        line-height: 1.4;
        cursor: default;
        user-select: none;
    }
    /* Card internals */
    .ap-cat-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: #8a9ab0;
        font-weight: 600;
        margin: 0.6rem 0 0.35rem 0;
    }
    .ap-full-desc {
        font-size: 0.88rem;
        color: #2a2a2a;
        line-height: 1.6;
    }
    /* Tighten Edit button spacing */
    .ap-edit-row { margin-top: -0.3rem; margin-bottom: 0.25rem; }
    </style>
    """, unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="library-header">
        <div>
            <p class="library-subtitle">UN DPO · Policy & Best Practices Service</p>
            <h1 class="library-title">Actors</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)

    n_cats = len(set(a["category"] for a in actors))
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-number">{len(actors)}</div>
            <div class="metric-label">Actors profiled</div>
        </div>
        <div class="metric-card">
            <div class="metric-number">{n_cats}</div>
            <div class="metric-label">Categories</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Search + category filter ──────────────────────────────────────────────
    col_search, col_cat = st.columns([2, 1])
    with col_search:
        search = st.text_input(
            "Search",
            placeholder="Search by name or description…",
            key="ap3_search",
            label_visibility="collapsed",
        )
    with col_cat:
        cat_filter = st.multiselect(
            "Category",
            all_categories,
            key="ap3_cat",
            label_visibility="collapsed",
            placeholder="Filter by category…",
        )

    actors_base = [a for a in actors_sorted if a.get("category") in cat_filter] if cat_filter else actors_sorted

    by_letter: dict[str, list] = {}
    for a in actors_base:
        letter = a["name"][0].upper()
        by_letter.setdefault(letter, []).append(a)
    letters_with_actors = set(by_letter.keys())

    st.markdown('<div style="margin-top:0.5rem;"></div>', unsafe_allow_html=True)

    col_index, col_main = st.columns([0.65, 5.35])

    with col_index:
        index_html = '<div class="ap-index"><div class="ap-index-label">A–Z</div>'
        for letter in ALPHABET:
            if letter in letters_with_actors:
                index_html += f'<a href="#ap-{letter}">{letter}</a>'
            else:
                index_html += f'<span class="ap-dim">{letter}</span>'
        index_html += "</div>"
        st.markdown(index_html, unsafe_allow_html=True)

    with col_main:
        is_searching = bool(search.strip())

        if is_searching:
            q = search.strip().lower()
            results = [
                a for a in actors_base
                if q in a["name"].lower() or q in a.get("description", "").lower()
            ]
            count = len(results)
            st.markdown(
                f'<div style="font-size:0.82rem;color:#6b7c8d;margin-bottom:0.9rem;'
                f'letter-spacing:0.04em;text-transform:uppercase;">'
                f'{count} result{"s" if count != 1 else ""} for &ldquo;{search.strip()}&rdquo;</div>',
                unsafe_allow_html=True,
            )
            if results:
                _render_grid(results, all_categories)
            else:
                st.markdown(
                    '<div style="padding:2rem;text-align:center;color:#8a9ab0;">No actors found.</div>',
                    unsafe_allow_html=True,
                )
        else:
            count_label = f"{len(actors_base)} actor{'s' if len(actors_base) != 1 else ''}"
            if cat_filter:
                count_label += f" · {', '.join(cat_filter)}"
            st.markdown(
                f'<div style="font-size:0.82rem;color:#6b7c8d;margin-bottom:0.5rem;'
                f'letter-spacing:0.04em;text-transform:uppercase;">{count_label}</div>',
                unsafe_allow_html=True,
            )
            if not actors_base:
                st.markdown(
                    '<div style="padding:2rem;text-align:center;color:#8a9ab0;">No actors in this category.</div>',
                    unsafe_allow_html=True,
                )
            for letter in ALPHABET:
                if letter not in by_letter:
                    continue
                st.markdown(
                    f'<div id="ap-{letter}" class="ap-letter">{letter}</div>',
                    unsafe_allow_html=True,
                )
                _render_grid(by_letter[letter], all_categories)


def save_actors(actors):
    DATA_PATH.write_text(json.dumps(actors, indent=2, ensure_ascii=False), encoding="utf-8")


def _render_grid(actor_list: list, all_categories: list):
    for i in range(0, len(actor_list), 2):
        pair = actor_list[i: i + 2]
        cols = st.columns(2, gap="small")
        for ci, actor in enumerate(pair):
            with cols[ci]:
                _render_card(actor, all_categories)


def _render_card(actor: dict, all_categories: list):
    name = actor["name"]
    cat = actor.get("category", "")
    full = actor.get("description", "")
    color = CATEGORY_COLORS.get(cat, "#78909c")
    edit_key = f"ap_editing_{name}"

    if st.session_state.get(edit_key):
        # Edit mode: Streamlit expander + form
        with st.expander(name, expanded=True):
            # Preserve the canonical order; only append a stray legacy value
            # (shouldn't occur post-cleanup, but keeps old data editable).
            cat_options = all_categories + ([cat] if cat and cat not in all_categories else [])
            with st.form(f"ap_edit_form_{name}"):
                new_desc = st.text_area("Description", value=full, height=130, key=f"ap_desc_{name}")
                new_cat = st.selectbox(
                    "Category",
                    cat_options,
                    index=cat_options.index(cat) if cat in cat_options else 0,
                    key=f"ap_cat_{name}",
                )
                col_save, col_cancel, _ = st.columns([1, 1, 3])
                with col_save:
                    save_clicked = st.form_submit_button("Save")
                with col_cancel:
                    cancel_clicked = st.form_submit_button("Cancel")

            if save_clicked:
                actors = json.loads(DATA_PATH.read_text(encoding="utf-8"))
                for a in actors:
                    if a["name"] == name:
                        a["description"] = new_desc
                        a["category"] = new_cat
                        break
                save_actors(actors)
                st.session_state[edit_key] = False
                st.rerun()
            if cancel_clicked:
                st.session_state[edit_key] = False
                st.rerun()
    else:
        # View mode: pure HTML <details> card — border color baked into inline style
        safe_name = name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        safe_cat = cat.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        safe_full = full.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        st.markdown(
            f'<details class="ap-card" style="border-left: 3px solid {color};">'
            f'<summary>{safe_name}</summary>'
            f'<div class="ap-card-body">'
            f'<div class="ap-cat-label">{safe_cat}</div>'
            f'<div class="ap-full-desc">{safe_full}</div>'
            f'</div></details>',
            unsafe_allow_html=True,
        )
        if is_editor():
            st.markdown('<div class="ap-edit-row"></div>', unsafe_allow_html=True)
            if st.button("Edit", key=f"ap_edit_btn_{name}"):
                st.session_state[edit_key] = True
                st.rerun()
