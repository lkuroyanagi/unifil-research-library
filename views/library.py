import json
import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_utils import (
    load_sources, get_all_tags, get_all_actors,
    get_all_countries, THEMATIC_CLUSTERS, SOURCE_TYPES
)


def is_editor():
    return st.session_state.get("editor_mode", False)

MISSION_START = 1978
MISSION_END   = 2026


def _build_density_chart(sources):
    """Bar chart: number of sources published in each 4-year bucket."""
    bucket = 4
    years, counts, colors = [], [], []
    y = MISSION_START
    while y < MISSION_END:
        y_end = min(y + bucket, MISSION_END)
        count = sum(1 for s in sources if y <= s.get("year", 0) < y_end)
        years.append(y)
        counts.append(max(count, 0.05))
        colors.append("#1a3a5c" if count >= 2 else ("#9ab8d0" if count == 1 else "#e0dbd2"))
        y += bucket

    fig = go.Figure(go.Bar(
        x=years, y=counts, marker_color=colors,
        width=bucket * 0.85,
        customdata=[max(0, int(c)) for c in counts],
        hovertemplate="%{x}: %{customdata} source(s)<extra></extra>",
    ))
    fig.update_layout(
        height=90,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f5f3ee",
        xaxis=dict(
            range=[MISSION_START - 1, MISSION_END + 1], showgrid=False,
            tickmode="linear", tick0=1978, dtick=8,
            tickfont=dict(size=10, color="#8a9ab0"), zeroline=False,
        ),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig

DATA_PATH = Path(__file__).parent.parent / "data" / "sources.json"

_TYPE_CONFIG = {
    "Think Tank / Policy Brief": {"color": "#3B6B9E", "bg": "#EAF1F9"},
    "Academic / Book":           {"color": "#2E7D5A", "bg": "#E8F5EE"},
    "UN/NGO Statement":          {"color": "#C0392B", "bg": "#FDECEA"},
    "Opinion / Media":           {"color": "#B45309", "bg": "#FEF3E2"},
    "UN Official Publication":   {"color": "#5B4CB8", "bg": "#F0EDFB"},
    "Other":                     {"color": "#5A6475", "bg": "#F0F1F3"},
}


def _card_html(s):
    stype = normalize_source_type(s.get("source_type", ""))
    cfg = _TYPE_CONFIG.get(stype, _TYPE_CONFIG["Other"])
    abstract = s.get("abstract", "")
    if len(abstract) > 220:
        abstract = abstract[:220] + "…"
    tags_html = "".join(
        f'<span style="display:inline-block;padding:3px 10px;border-radius:3px;'
        f'font-size:11px;color:#4A5568;background:#ECEAE4;margin:2px;">{t}</span>'
        for t in s.get("tags", [])[:6]
    )
    ll = len(s.get("lessons_learned", []))
    actors = len(s.get("actors", []))
    return f"""
    <div style="background:#fff;border:1px solid #E8E5DE;border-radius:6px;
                padding:20px 22px;margin-bottom:4px;">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;
                  gap:10px;margin-bottom:10px;">
        <span style="display:inline-block;padding:2px 8px;border-radius:3px;font-size:11px;
                     font-weight:500;color:{cfg['color']};background:{cfg['bg']};">{stype}</span>
        <span style="font-size:11px;color:#9A968E;">{s.get('year', '')}</span>
      </div>
      <div style="font-size:14px;font-weight:600;color:#1a1a2e;line-height:1.4;
                  margin-bottom:3px;">{s.get('title', '')}</div>
      <div style="font-size:11px;color:#9A968E;font-family:'IBM Plex Mono',monospace;
                  margin-bottom:8px;">{s['id']}</div>
      <div style="font-size:12px;color:#5A6475;font-weight:500;margin-bottom:8px;">
        {s.get('author', '')}</div>
      <div style="font-size:12.5px;color:#6B7280;line-height:1.55;margin-bottom:8px;">
        {abstract}</div>
      {f'<div style="margin-bottom:8px;">{tags_html}</div>' if tags_html else ''}
      <div style="display:flex;gap:16px;align-items:center;padding-top:8px;border-top:1px solid #F0EDE6;
                  font-size:11px;color:#5A6475;">
        <span><strong style="color:#1a1a2e;">{ll}</strong> LL Candidates</span>
        <span><strong style="color:#1a1a2e;">{actors}</strong> Actors</span>
        <span class="source-card-arrow" style="margin-left:auto;color:#9A968E;opacity:0.75;
              font-size:15px;line-height:1;">→</span>
      </div>
    </div>
    """


# ── Helpers ───────────────────────────────────────────────────────────────────

def normalize_source_type(raw: str) -> str:
    if not raw:
        return "Other"
    t = raw.lower()
    if any(k in t for k in ("think tank", "policy brief")):
        return "Think Tank / Policy Brief"
    if any(k in t for k in ("academic", "journal", "book")):
        return "Academic / Book"
    if any(k in t for k in ("un/ngo", "ngo statement")):
        return "UN/NGO Statement"
    if t == "ngo":
        return "UN/NGO Statement"
    if any(k in t for k in ("opinion", "media", "primary")):
        return "Opinion / Media"
    if any(k in t for k in ("un official", "un document", "un publication")):
        return "UN Official Publication"
    return "Other"


def save_source(updated):
    sources = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for i, s in enumerate(sources):
        if s["id"] == updated["id"]:
            sources[i] = updated
            break
    DATA_PATH.write_text(json.dumps(sources, indent=2, ensure_ascii=False), encoding="utf-8")


def _tag_input(label, sid, field_key, initial_items):
    opts_key    = f"e_{field_key}_opts_{sid}"
    ms_key      = f"e_{field_key}_ms_{sid}"
    pending_key = f"e_{field_key}_pending_{sid}"

    if opts_key not in st.session_state:
        st.session_state[opts_key] = list(initial_items)
    if ms_key not in st.session_state:
        st.session_state[ms_key] = list(st.session_state[opts_key])

    # Merge pending additions before widget renders (avoids post-instantiation mutation error)
    if st.session_state.get(pending_key):
        for item in st.session_state[pending_key]:
            if item not in st.session_state[ms_key]:
                st.session_state[ms_key] = list(st.session_state[ms_key]) + [item]
        st.session_state[pending_key] = []

    st.markdown(
        f'<div style="font-size:0.85rem;font-weight:600;color:#1a1a2e;'
        f'border-bottom:1px solid #E8E5DE;padding-bottom:0.25rem;'
        f'margin:1rem 0 0.4rem 0;">{label}</div>',
        unsafe_allow_html=True,
    )

    st.multiselect(
        label,
        options=st.session_state[opts_key],
        key=ms_key,
        label_visibility="collapsed",
    )

    with st.form(key=f"add_{field_key}_{sid}", clear_on_submit=True):
        new_val = st.text_input("Add", placeholder="Type and press Enter to add…", label_visibility="collapsed", key=ms_key + "_new")
        if st.form_submit_button("Add"):
            item = new_val.strip()
            if item:
                if item not in st.session_state[opts_key]:
                    st.session_state[opts_key].append(item)
                if pending_key not in st.session_state:
                    st.session_state[pending_key] = []
                if item not in st.session_state[pending_key] and item not in st.session_state.get(ms_key, []):
                    st.session_state[pending_key].append(item)
                st.rerun()

    return list(st.session_state.get(ms_key, []))


# ── Edit form (Streamlit widgets — unchanged logic) ───────────────────────────

def render_source_edit(s, all_tags):
    sid = s["id"]

    st.markdown('<div style="font-size:0.75rem;font-weight:600;color:#0077B6;letter-spacing:0.06em;margin-bottom:1rem;">EDIT MODE</div>', unsafe_allow_html=True)

    title  = st.text_input("Title",  value=s.get("title", ""),  key=f"e_title_{sid}")
    author = st.text_input("Author", value=s.get("author", ""), key=f"e_author_{sid}")

    ec1, ec2 = st.columns([1, 2])
    with ec1:
        year = st.number_input("Year", value=int(s.get("year", 2000)), min_value=1900, max_value=2030, step=1, key=f"e_year_{sid}")
    with ec2:
        current_type = s.get("source_type", "")
        type_options = SOURCE_TYPES if current_type in SOURCE_TYPES else [current_type] + SOURCE_TYPES
        source_type = st.selectbox("Source type", type_options, index=type_options.index(current_type), key=f"e_stype_{sid}")

    abstract = st.text_area("Abstract", value=s.get("abstract", ""), height=130, key=f"e_abstract_{sid}")

    st.markdown('<div style="font-size:0.85rem;font-weight:600;color:#1a1a2e;border-bottom:1px solid #E8E5DE;padding-bottom:0.25rem;margin:1rem 0 0.6rem 0;">Key Arguments</div>', unsafe_allow_html=True)
    args_count_key = f"e_args_count_{sid}"
    existing_args = s.get("key_arguments", [])
    if args_count_key not in st.session_state:
        st.session_state[args_count_key] = max(len(existing_args), 1)
    n_args = st.session_state[args_count_key]
    for ai in range(n_args):
        k = f"e_arg_{sid}_{ai}"
        if k not in st.session_state:
            st.session_state[k] = existing_args[ai] if ai < len(existing_args) else ""
    for ai in range(n_args):
        nc, tc, dc = st.columns([0.35, 8.5, 0.5])
        with nc:
            st.markdown(f'<div style="font-size:0.78rem;color:#8A8880;padding-top:0.7rem;text-align:right;">{ai + 1}</div>', unsafe_allow_html=True)
        with tc:
            st.text_area(f"Argument {ai + 1}", key=f"e_arg_{sid}_{ai}", height=80, label_visibility="collapsed")
        with dc:
            st.markdown('<div style="padding-top:0.5rem;"></div>', unsafe_allow_html=True)
            if st.button("×", key=f"e_arg_del_{sid}_{ai}", help="Delete argument"):
                vals = [st.session_state.get(f"e_arg_{sid}_{i}", "") for i in range(n_args)]
                vals.pop(ai)
                for i in range(n_args):
                    st.session_state.pop(f"e_arg_{sid}_{i}", None)
                st.session_state[args_count_key] = max(n_args - 1, 1)
                for i, v in enumerate(vals):
                    st.session_state[f"e_arg_{sid}_{i}"] = v
                if not vals:
                    st.session_state[f"e_arg_{sid}_0"] = ""
                updated = dict(s)
                updated["key_arguments"] = [v.strip() for v in vals if v.strip()]
                save_source(updated)
                st.rerun()
    mc1, mc2, mc3, mc4 = st.columns([0.35, 2.4, 1.5, 1.5])
    with mc2:
        if st.button("+ Add argument", key=f"e_addarg_{sid}"):
            st.session_state[args_count_key] = n_args + 1
            st.session_state[f"e_arg_{sid}_{n_args}"] = ""
            st.rerun()
    if n_args > 1:
        with mc3:
            arg_from = st.number_input("From", min_value=1, max_value=n_args, step=1, key=f"e_arg_from_{sid}", label_visibility="collapsed")
        with mc4:
            arg_to = st.number_input("To position", min_value=1, max_value=n_args, step=1, key=f"e_arg_to_{sid}", label_visibility="collapsed")
        st.markdown('<div style="font-size:0.72rem;color:#8A8880;margin:-0.4rem 0 0.3rem 0;">Move item [from] → [to position]</div>', unsafe_allow_html=True)
        if st.button("Move", key=f"e_arg_move_{sid}"):
            fi, ti_ = int(arg_from) - 1, int(arg_to) - 1
            if fi != ti_:
                vals = [st.session_state[f"e_arg_{sid}_{i}"] for i in range(n_args)]
                item = vals.pop(fi)
                vals.insert(ti_, item)
                for i in range(n_args):
                    del st.session_state[f"e_arg_{sid}_{i}"]
                for i, v in enumerate(vals):
                    st.session_state[f"e_arg_{sid}_{i}"] = v
                st.rerun()

    tags = _tag_input("Tags", sid, "tags", s.get("tags", []))
    thematic_clusters = _tag_input("Thematic Clusters", sid, "clusters", s.get("thematic_clusters", []))

    actors_raw = st.text_area(
        "Actors (comma-separated)",
        value=", ".join(s.get("actors", [])),
        height=68,
        key=f"e_actors_{sid}"
    )

    bias_flag = st.text_area("Bias flag", value=s.get("bias_flag", ""), height=90, key=f"e_bias_{sid}")

    notes_raw = st.text_area(
        "Analytical notes (one per line)",
        value="\n".join(s.get("analytical_notes", [])),
        height=100,
        key=f"e_notes_{sid}"
    )

    st.markdown('<div style="font-size:0.85rem;font-weight:600;color:#1a1a2e;border-bottom:1px solid #E8E5DE;padding-bottom:0.25rem;margin:1rem 0 0.6rem 0;">Lessons Learned</div>', unsafe_allow_html=True)
    lessons_in = s.get("lessons_learned", [])
    n_lessons = len(lessons_in)
    tag_opts = ["SOURCE-DERIVED", "ANALYTICAL INFERENCE"]
    for li, lesson in enumerate(lessons_in):
        tk = f"e_ll_text_{sid}_{li}"
        gk = f"e_ll_tag_{sid}_{li}"
        if tk not in st.session_state:
            st.session_state[tk] = lesson.get("text", "")
        if gk not in st.session_state:
            st.session_state[gk] = lesson.get("tag", "SOURCE-DERIVED")
    for li in range(n_lessons):
        nc, lc1, lc2 = st.columns([0.35, 3, 1.2])
        with nc:
            st.markdown(f'<div style="font-size:0.78rem;color:#8A8880;padding-top:0.6rem;text-align:right;">{li + 1}</div>', unsafe_allow_html=True)
        with lc1:
            st.text_area(f"Lesson {li + 1}", key=f"e_ll_text_{sid}_{li}", height=72, label_visibility="collapsed")
        with lc2:
            st.selectbox(f"Tag {li + 1}", tag_opts, key=f"e_ll_tag_{sid}_{li}", label_visibility="collapsed")
    if n_lessons > 1:
        lm1, lm2, lm3, lm4 = st.columns([0.35, 2.4, 1.5, 1.5])
        with lm2:
            ll_from = st.number_input("From", min_value=1, max_value=n_lessons, step=1, key=f"e_ll_from_{sid}", label_visibility="collapsed")
        with lm3:
            ll_to = st.number_input("To position", min_value=1, max_value=n_lessons, step=1, key=f"e_ll_to_{sid}", label_visibility="collapsed")
        with lm4:
            st.markdown('<div style="padding-top:0.35rem;"></div>', unsafe_allow_html=True)
            if st.button("Move", key=f"e_ll_move_{sid}"):
                fi, ti_ = int(ll_from) - 1, int(ll_to) - 1
                if fi != ti_:
                    texts = [st.session_state[f"e_ll_text_{sid}_{i}"] for i in range(n_lessons)]
                    tgs   = [st.session_state[f"e_ll_tag_{sid}_{i}"]  for i in range(n_lessons)]
                    txt_item = texts.pop(fi); tags_item = tgs.pop(fi)
                    texts.insert(ti_, txt_item); tgs.insert(ti_, tags_item)
                    for i in range(n_lessons):
                        del st.session_state[f"e_ll_text_{sid}_{i}"]
                        del st.session_state[f"e_ll_tag_{sid}_{i}"]
                    for i in range(n_lessons):
                        st.session_state[f"e_ll_text_{sid}_{i}"] = texts[i]
                        st.session_state[f"e_ll_tag_{sid}_{i}"]  = tgs[i]
                    st.rerun()
        st.markdown('<div style="font-size:0.72rem;color:#8A8880;margin:-0.4rem 0 0.3rem 0;">Move lesson [from] → [to position]</div>', unsafe_allow_html=True)

    st.markdown('<div style="font-size:0.85rem;font-weight:600;color:#1a1a2e;border-bottom:1px solid #E8E5DE;padding-bottom:0.25rem;margin:1rem 0 0.6rem 0;">Timeline Events</div>', unsafe_allow_html=True)
    te_count_key = f"e_te_count_{sid}"
    timeline_in = s.get("timeline_events", [])
    if te_count_key not in st.session_state:
        st.session_state[te_count_key] = max(len(timeline_in), 1)
    n_te = st.session_state[te_count_key]
    edited_timeline = []
    for ti in range(n_te):
        tc1, tc2 = st.columns([1, 3])
        with tc1:
            default_date = timeline_in[ti].get("date", "") if ti < len(timeline_in) else ""
            te_date = st.text_input(f"Date {ti + 1}", value=default_date, placeholder="e.g. 2006-08", key=f"e_te_date_{sid}_{ti}", label_visibility="collapsed")
        with tc2:
            default_event = timeline_in[ti].get("event", "") if ti < len(timeline_in) else ""
            te_event = st.text_input(f"Event {ti + 1}", value=default_event, placeholder="Event description…", key=f"e_te_event_{sid}_{ti}", label_visibility="collapsed")
        edited_timeline.append({"date": te_date, "event": te_event})
    if st.button("+ Add event", key=f"e_addte_{sid}"):
        st.session_state[te_count_key] = n_te + 1
        st.rerun()

    st.markdown('<div style="margin-top:1rem;"></div>', unsafe_allow_html=True)
    btn_col1, btn_col2, _ = st.columns([1, 1, 2])
    with btn_col1:
        save_clicked = st.button("💾 Save", key=f"e_save_{sid}")
    with btn_col2:
        cancel_clicked = st.button("Cancel", key=f"e_cancel_{sid}")

    if save_clicked:
        updated = dict(s)
        updated["title"]   = title
        updated["author"]  = author
        updated["year"]    = int(year)
        updated["source_type"] = source_type
        updated["abstract"] = abstract
        updated["key_arguments"] = [
            st.session_state[f"e_arg_{sid}_{i}"].strip()
            for i in range(st.session_state.get(f"e_args_count_{sid}", 0))
            if st.session_state.get(f"e_arg_{sid}_{i}", "").strip()
        ]
        updated["tags"]              = sorted(set(tags))
        updated["thematic_clusters"] = list(dict.fromkeys(thematic_clusters))
        updated["actors"]            = [a.strip() for a in actors_raw.split(",") if a.strip()]
        updated["bias_flag"]         = bias_flag
        updated["analytical_notes"]  = [ln.strip() for ln in notes_raw.splitlines() if ln.strip()]
        updated["lessons_learned"]   = [
            {"text": st.session_state[f"e_ll_text_{sid}_{i}"], "tag": st.session_state[f"e_ll_tag_{sid}_{i}"]}
            for i in range(len(s.get("lessons_learned", [])))
            if st.session_state.get(f"e_ll_text_{sid}_{i}", "").strip()
        ]
        updated["timeline_events"] = [e for e in edited_timeline if e["event"].strip()]
        save_source(updated)
        # Keep selected_source_id so user returns to detail view, not grid
        st.session_state.editing_source_id = None
        n_a = st.session_state.pop(f"e_args_count_{sid}", 0)
        for i in range(n_a):
            st.session_state.pop(f"e_arg_{sid}_{i}", None)
        n_l = len(s.get("lessons_learned", []))
        for i in range(n_l):
            st.session_state.pop(f"e_ll_text_{sid}_{i}", None)
            st.session_state.pop(f"e_ll_tag_{sid}_{i}", None)
        st.session_state.pop(f"e_te_count_{sid}", None)
        for _fk in ("tags", "clusters"):
            st.session_state.pop(f"e_{_fk}_opts_{sid}", None)
            st.session_state.pop(f"e_{_fk}_ms_{sid}", None)
        st.success("Saved.")
        st.rerun()

    if cancel_clicked:
        st.session_state.selected_source_id = None
        st.session_state.editing_source_id = None
        n_a = st.session_state.pop(f"e_args_count_{sid}", 0)
        for i in range(n_a):
            st.session_state.pop(f"e_arg_{sid}_{i}", None)
        n_l = len(s.get("lessons_learned", []))
        for i in range(n_l):
            st.session_state.pop(f"e_ll_text_{sid}_{i}", None)
            st.session_state.pop(f"e_ll_tag_{sid}_{i}", None)
        st.session_state.pop(f"e_te_count_{sid}", None)
        for _fk in ("tags", "clusters"):
            st.session_state.pop(f"e_{_fk}_opts_{sid}", None)
            st.session_state.pop(f"e_{_fk}_ms_{sid}", None)
        st.rerun()


# ── Detail view (Streamlit full-page) ────────────────────────────────────────

def render_source_detail(s):
    st.markdown(f"""
    <div style="padding:0.5rem 0 1rem 0;">
      <div style="font-size:1.4rem;font-weight:700;color:#1a1a2e;line-height:1.3;margin-bottom:0.4rem;">{s['title']}</div>
      <div style="font-size:0.88rem;color:#5A6475;margin-bottom:0.3rem;font-family:'IBM Plex Mono',monospace;">{s['id']}</div>
      <div style="font-size:0.9rem;color:#5A6475;margin-bottom:1rem;">{s['author']} · {s['year']} · {s.get('source_type','')} · {s.get('publisher','')}</div>
    </div>
    """, unsafe_allow_html=True)

    clusters = s.get('thematic_clusters', [])
    if clusters:
        st.markdown('<div style="font-size:0.78rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#9A968E;margin:1.2rem 0 0.5rem 0;">Thematic Clusters</div>', unsafe_allow_html=True)
        chips = "".join([
            f'<span style="display:inline-block;background:#ECEAE4;color:#4A5568;border-radius:3px;font-size:0.72rem;padding:3px 10px;margin:2px;">{c}</span>'
            for c in clusters
        ])
        st.markdown(f'<div style="margin-bottom:0.8rem;">{chips}</div>', unsafe_allow_html=True)

    tags = s.get('tags', [])
    if tags:
        st.markdown('<div style="font-size:0.78rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#9A968E;margin:1rem 0 0.5rem 0;">Tags</div>', unsafe_allow_html=True)
        chips = "".join([
            f'<span style="display:inline-block;background:#ECEAE4;color:#4A5568;border-radius:3px;font-size:0.72rem;padding:3px 10px;margin:2px;">{t}</span>'
            for t in tags
        ])
        st.markdown(f'<div style="margin-bottom:1rem;">{chips}</div>', unsafe_allow_html=True)

    actors = s.get("actors", [])
    if actors:
        st.markdown('<div style="font-size:0.78rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#9A968E;margin:1rem 0 0.5rem 0;">Key Actors</div>', unsafe_allow_html=True)
        chips = "".join([
            f'<span style="display:inline-block;background:#f5ede0;color:#7a4510;border:1px solid #d4a96a;border-radius:3px;font-size:0.72rem;padding:3px 10px;margin:2px;">{a}</span>'
            for a in actors
        ])
        st.markdown(f'<div style="margin-bottom:1rem;">{chips}</div>', unsafe_allow_html=True)

    st.markdown('<div style="font-size:0.78rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#9A968E;margin:1rem 0 0.5rem 0;">Abstract</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:0.9rem;color:#374151;line-height:1.7;">{s.get("abstract","")}</div>', unsafe_allow_html=True)

    key_args = s.get("key_arguments", [])
    if key_args:
        st.markdown('<div style="font-size:0.78rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#9A968E;margin:1.2rem 0 0.5rem 0;">Key Arguments</div>', unsafe_allow_html=True)
        for arg in key_args:
            st.markdown(f'<div style="font-size:0.88rem;color:#374151;line-height:1.6;padding:0.5rem 0.8rem;border-left:2px solid #E8E5DE;margin-bottom:0.5rem;">— {arg}</div>', unsafe_allow_html=True)

    if s.get("bias_flag"):
        st.markdown('<div style="font-size:0.78rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#9A968E;margin:1.2rem 0 0.5rem 0;">Bias Assessment</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="background:#fff8ec;border:1px solid #e6c87a;border-left:3px solid #0077B6;border-radius:3px;padding:0.7rem 1rem;font-size:0.86rem;color:#374151;line-height:1.5;">{s["bias_flag"]}</div>', unsafe_allow_html=True)

    notes = s.get("analytical_notes", [])
    if notes:
        st.markdown('<div style="font-size:0.78rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#9A968E;margin:1.2rem 0 0.5rem 0;">Analytical Notes</div>', unsafe_allow_html=True)
        for note in notes:
            st.markdown(f'<div style="font-size:0.88rem;color:#374151;line-height:1.6;padding:0.5rem 0.8rem;border-left:2px solid #E8E5DE;margin-bottom:0.5rem;">{note}</div>', unsafe_allow_html=True)

    lessons = s.get("lessons_learned", [])
    if lessons:
        st.markdown('<div style="font-size:0.78rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#9A968E;margin:1.2rem 0 0.5rem 0;">Lessons Learned Candidates</div>', unsafe_allow_html=True)
        for l in lessons:
            tag_class = "SOURCE-DERIVED" if l.get("tag") == "SOURCE-DERIVED" else "ANALYTICAL INFERENCE"
            tag_color = "#2E7D5A" if l.get("tag") == "SOURCE-DERIVED" else "#B45309"
            tag_bg    = "#E8F5EE" if l.get("tag") == "SOURCE-DERIVED" else "#FEF3E2"
            st.markdown(f"""
            <div style="margin-bottom:0.7rem;padding:0.7rem;background:#F9F8F5;border:1px solid #E8E5DE;border-radius:4px;">
              <span style="display:inline-block;padding:2px 8px;border-radius:3px;font-size:0.68rem;font-weight:600;color:{tag_color};background:{tag_bg};margin-bottom:0.4rem;">{tag_class}</span>
              <div style="font-size:0.88rem;color:#374151;line-height:1.6;">{l['text']}</div>
            </div>
            """, unsafe_allow_html=True)

    timeline = s.get("timeline_events", [])
    if timeline:
        st.markdown('<div style="font-size:0.78rem;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;color:#9A968E;margin:1.2rem 0 0.5rem 0;">Timeline Events</div>', unsafe_allow_html=True)
        for e in timeline:
            st.markdown(f"""
            <div style="display:flex;gap:1rem;margin-bottom:0.4rem;font-size:0.88rem;">
              <span style="font-weight:600;color:#1a1a2e;min-width:60px;">{e.get('date','')}</span>
              <span style="color:#374151;">{e.get('event','')}</span>
            </div>
            """, unsafe_allow_html=True)

    coverage = s.get("timeline_coverage", [])
    if isinstance(coverage, dict):
        cov_start, cov_end = coverage.get("start", ""), coverage.get("end", "")
        if cov_start or cov_end:
            st.markdown(f'<div style="margin-top:1rem;font-size:0.8rem;color:#8A8880;">Period covered: {cov_start}–{cov_end}</div>', unsafe_allow_html=True)
    elif isinstance(coverage, list) and len(coverage) == 2:
        st.markdown(f'<div style="margin-top:1rem;font-size:0.8rem;color:#8A8880;">Period covered: {coverage[0]}–{coverage[1]}</div>', unsafe_allow_html=True)


# ── HTML component builder ────────────────────────────────────────────────────

_LIBRARY_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://unpkg.com/react@18.3.1/umd/react.production.min.js" crossorigin="anonymous"></script>
<script src="https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js" crossorigin="anonymous"></script>
<script src="https://unpkg.com/@babel/standalone@7.29.0/babel.min.js" crossorigin="anonymous"></script>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body,#root{height:100%;overflow:hidden;}
body{font-family:'IBM Plex Sans',sans-serif;background:#F5F4F0;color:#1a1a2e;-webkit-font-smoothing:antialiased;}
::-webkit-scrollbar{width:6px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:#c8c5bc;border-radius:3px;}
input:focus{outline:none;}
button{font-family:'IBM Plex Sans',sans-serif;}
@keyframes slideIn{from{transform:translateX(40px);opacity:.5;}to{transform:none;opacity:1;}}
</style>
</head>
<body>
<div id="root"></div>
<script type="text/babel">
const {useState,useEffect,useRef,useCallback} = React;

const SOURCES    = __SOURCES_JSON__;
const ALL_CLUSTERS = __CLUSTERS_JSON__;
const ALL_COUNTRIES = __COUNTRIES_JSON__;
const STATS      = __STATS_JSON__;
const MIN_YEAR   = __MIN_YEAR__;
const MAX_YEAR   = __MAX_YEAR__;
const ACCENT     = '#0077B6';

const TYPE_CONFIG = {
  "Think Tank / Policy Brief": {color:"#3B6B9E",bg:"#EAF1F9"},
  "Academic / Book":           {color:"#2E7D5A",bg:"#E8F5EE"},
  "UN/NGO Statement":          {color:"#C0392B",bg:"#FDECEA"},
  "Opinion / Media":           {color:"#B45309",bg:"#FEF3E2"},
  "UN Official Publication":   {color:"#5B4CB8",bg:"#F0EDFB"},
  "Other":                     {color:"#5A6475",bg:"#F0F1F3"},
};
const ALL_TYPES = Object.keys(TYPE_CONFIG);

function openInStreamlit(sourceId) {
  try {
    const base = window.parent.location.href.split('?')[0];
    window.parent.location.href = base + '?source_id=' + encodeURIComponent(sourceId);
  } catch(e) {}
}

/* ── Icons ─────────────────────────────────────────────────────────── */
const Icon = ({name, size=16, color="currentColor"}) => {
  const icons = {
    search:       <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><circle cx="6.5" cy="6.5" r="4.5"/><path d="M10.5 10.5L14 14"/></svg>,
    chevronDown:  <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 6l4 4 4-4"/></svg>,
    close:        <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><path d="M4 4l8 8M12 4l-8 8"/></svg>,
    externalLink: <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M6 3H3v10h10v-3M9 3h4v4M13 3L7 9"/></svg>,
    user:         <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><circle cx="8" cy="5" r="3"/><path d="M2 14c0-3.3 2.7-6 6-6s6 2.7 6 6"/></svg>,
    calendar:     <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="3" width="12" height="11" rx="1"/><path d="M2 7h12M6 1v4M10 1v4"/></svg>,
    globe:        <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><circle cx="8" cy="8" r="6"/><path d="M8 2c-2 2-2 10 0 12M8 2c2 2 2 10 0 12M2 8h12"/></svg>,
    filter:       <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><path d="M2 4h12M4 8h8M6 12h4"/></svg>,
    lightbulb:    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round"><path d="M6 14h4M7 12h2M5.5 9.5C4.5 8.8 4 7.8 4 6.5a4 4 0 118 0c0 1.3-.5 2.3-1.5 3L9 11H7L6 9.5z"/></svg>,
    edit:         <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M11 2l3 3-8 8H3v-3l8-8z"/></svg>,
  };
  return icons[name] || null;
};

/* ── TypeBadge ──────────────────────────────────────────────────────── */
function TypeBadge({type}) {
  const cfg = TYPE_CONFIG[type] || TYPE_CONFIG["Other"];
  return (
    <span style={{display:"inline-block",padding:"2px 8px",borderRadius:"3px",fontSize:"11px",fontWeight:500,color:cfg.color,background:cfg.bg,whiteSpace:"nowrap"}}>
      {type}
    </span>
  );
}

/* ── Tag chip ───────────────────────────────────────────────────────── */
function Tag({label}) {
  return (
    <span style={{display:"inline-block",padding:"3px 10px",borderRadius:"3px",fontSize:"11px",color:"#4A5568",background:"#ECEAE4",whiteSpace:"nowrap"}}>
      {label}
    </span>
  );
}

/* ── Stat card ──────────────────────────────────────────────────────── */
function StatCard({value, label}) {
  return (
    <div style={{flex:1,padding:"20px 24px",background:"#fff",borderRadius:"6px",border:"1px solid #E8E5DE"}}>
      <div style={{fontSize:"32px",fontWeight:700,color:"#1a1a2e",lineHeight:1,fontVariantNumeric:"tabular-nums"}}>{value}</div>
      <div style={{fontSize:"11px",fontWeight:600,letterSpacing:"0.08em",color:"#8A8880",textTransform:"uppercase",marginTop:"6px"}}>{label}</div>
    </div>
  );
}

/* ── MultiSelect dropdown ───────────────────────────────────────────── */
function MultiSelectFilter({label, options, selected, onChange}) {
  const [open, setOpen] = useState(false);
  const ref = useRef();
  useEffect(() => {
    const h = e => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  const toggle = opt => {
    onChange(selected.includes(opt) ? selected.filter(x => x !== opt) : [...selected, opt]);
  };
  const has = selected.length > 0;

  return (
    <div ref={ref} style={{position:"relative"}}>
      <button onClick={() => setOpen(o => !o)} style={{
        display:"flex",alignItems:"center",gap:"6px",
        padding:"7px 10px 7px 12px",
        background:has?"#EAF1F9":"#FAFAF8",
        border:`1px solid ${has?"#3B6B9E":"#DDD9D0"}`,
        borderRadius:"5px",cursor:"pointer",whiteSpace:"nowrap",
      }}>
        <span style={{fontSize:"10px",fontWeight:600,letterSpacing:"0.06em",textTransform:"uppercase",color:has?"#3B6B9E":"#9A968E"}}>{label}</span>
        {has && <span style={{background:"#3B6B9E",color:"#fff",borderRadius:"10px",fontSize:"10px",fontWeight:700,padding:"1px 6px",lineHeight:1.4}}>{selected.length}</span>}
        <Icon name="chevronDown" size={13} color={has?"#3B6B9E":"#9A968E"} />
      </button>
      {open && (
        <div style={{
          position:"absolute",top:"calc(100% + 5px)",left:0,zIndex:100,
          background:"#fff",border:"1px solid #DDD9D0",borderRadius:"7px",
          boxShadow:"0 8px 28px rgba(0,0,0,0.11)",minWidth:"210px",
          padding:"6px 0",maxHeight:"280px",overflowY:"auto",
        }}>
          {options.map(o => {
            const checked = selected.includes(o);
            return (
              <div key={o} onClick={() => toggle(o)}
                onMouseEnter={e => e.currentTarget.style.background = checked?"#EAF1F9":"#F5F4F0"}
                onMouseLeave={e => e.currentTarget.style.background = checked?"#F0F4F9":"transparent"}
                style={{
                  padding:"8px 14px",fontSize:"13px",cursor:"pointer",
                  display:"flex",alignItems:"center",gap:"10px",
                  background:checked?"#F0F4F9":"transparent",
                  color:checked?"#1B3A5C":"#2D3748",
                  fontWeight:checked?500:400,transition:"background 0.1s",
                }}>
                <div style={{
                  width:"15px",height:"15px",borderRadius:"3px",flexShrink:0,
                  border:`1.5px solid ${checked?"#3B6B9E":"#C5C0B8"}`,
                  background:checked?"#3B6B9E":"#fff",
                  display:"flex",alignItems:"center",justifyContent:"center",
                }}>
                  {checked && <svg width="9" height="7" viewBox="0 0 9 7" fill="none"><path d="M1 3l2.5 2.5L8 1" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></svg>}
                </div>
                {o}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ── Range slider ───────────────────────────────────────────────────── */
function RangeSlider({min, max, value, onChange}) {
  const [lo, hi] = value;
  const pct = v => ((v - min) / (max - min)) * 100;
  return (
    <div>
      <div style={{fontSize:"10px",fontWeight:600,letterSpacing:"0.06em",textTransform:"uppercase",color:"#9A968E",marginBottom:"6px"}}>Year Range</div>
      <div style={{display:"flex",alignItems:"center",gap:"8px"}}>
        <span style={{fontSize:"12px",color:"#1a1a2e",fontWeight:500,minWidth:"32px",fontVariantNumeric:"tabular-nums"}}>{lo}</span>
        <div style={{flex:1,position:"relative",height:"20px",display:"flex",alignItems:"center"}}>
          <div style={{position:"absolute",left:0,right:0,height:"3px",background:"#DDD9D0",borderRadius:"2px"}} />
          <div style={{position:"absolute",left:`${pct(lo)}%`,right:`${100-pct(hi)}%`,height:"3px",background:ACCENT,borderRadius:"2px"}} />
          <div style={{position:"absolute",left:`${pct(lo)}%`,transform:"translateX(-50%)",width:"14px",height:"14px",borderRadius:"50%",background:"#fff",border:`2px solid ${ACCENT}`,boxShadow:"0 1px 4px rgba(0,0,0,.15)",pointerEvents:"none",zIndex:2}} />
          <div style={{position:"absolute",left:`${pct(hi)}%`,transform:"translateX(-50%)",width:"14px",height:"14px",borderRadius:"50%",background:"#fff",border:`2px solid ${ACCENT}`,boxShadow:"0 1px 4px rgba(0,0,0,.15)",pointerEvents:"none",zIndex:2}} />
          <input type="range" min={min} max={max} value={lo}
            onChange={e => onChange([Math.min(Number(e.target.value), hi-1), hi])}
            style={{position:"absolute",left:0,right:0,width:"100%",opacity:0,height:"100%",cursor:"pointer",zIndex:3}} />
          <input type="range" min={min} max={max} value={hi}
            onChange={e => onChange([lo, Math.max(Number(e.target.value), lo+1)])}
            style={{position:"absolute",left:0,right:0,width:"100%",opacity:0,height:"100%",cursor:"pointer",zIndex:3}} />
        </div>
        <span style={{fontSize:"12px",color:"#1a1a2e",fontWeight:500,minWidth:"32px",textAlign:"right",fontVariantNumeric:"tabular-nums"}}>{hi}</span>
      </div>
    </div>
  );
}

/* ── Source card ────────────────────────────────────────────────────── */
function SourceCard({source}) {
  const [hovered, setHovered] = useState(false);
  return (
    <div
      onClick={() => openInStreamlit(source.id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background:"#fff",
        border:`1px solid ${hovered?"#B8C8D8":"#E8E5DE"}`,
        borderRadius:"6px",
        padding:"20px 22px",
        cursor:"pointer",
        transition:"all 0.18s",
        transform:hovered?"translateY(-2px)":"none",
        boxShadow:hovered?"0 6px 20px rgba(0,0,60,.08)":"0 1px 3px rgba(0,0,0,.04)",
        display:"flex",flexDirection:"column",gap:"10px",
      }}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",gap:"10px"}}>
        <TypeBadge type={source.type} />
        <span style={{fontSize:"11px",color:"#9A968E",fontVariantNumeric:"tabular-nums",flexShrink:0}}>{source.year}</span>
      </div>
      <div>
        <div style={{fontSize:"14px",fontWeight:600,color:"#1a1a2e",lineHeight:1.4,marginBottom:"3px"}}>{source.title}</div>
        <div style={{fontSize:"11px",color:"#9A968E",fontFamily:"'IBM Plex Mono',monospace"}}>{source.ref}</div>
      </div>
      <div style={{fontSize:"12px",color:"#5A6475",fontWeight:500}}>{source.author}</div>
      <p style={{fontSize:"12.5px",color:"#6B7280",lineHeight:1.55,display:"-webkit-box",WebkitLineClamp:3,WebkitBoxOrient:"vertical",overflow:"hidden",margin:0}}>{source.abstract}</p>
      {source.tags.length > 0 && (
        <div style={{display:"flex",flexWrap:"wrap",gap:"4px"}}>
          {source.tags.map(t => <Tag key={t} label={t} />)}
        </div>
      )}
      <div style={{display:"flex",gap:"16px",paddingTop:"8px",borderTop:"1px solid #F0EDE6",marginTop:"2px"}}>
        <div style={{display:"flex",alignItems:"center",gap:"5px"}}>
          <Icon name="lightbulb" size={12} color={ACCENT} />
          <span style={{fontSize:"11px",color:"#5A6475"}}><strong style={{color:"#1a1a2e"}}>{source.llCandidates}</strong> LL Candidates</span>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:"5px"}}>
          <Icon name="user" size={12} color={ACCENT} />
          <span style={{fontSize:"11px",color:"#5A6475"}}><strong style={{color:"#1a1a2e"}}>{source.actorsIndexed}</strong> Actors</span>
        </div>
      </div>
    </div>
  );
}


/* ── Main App ────────────────────────────────────────────────────────── */
function App() {
  const [search,       setSearch]       = useState("");
  const [selClusters,  setSelClusters]  = useState([]);
  const [selTypes,     setSelTypes]     = useState([]);
  const [selCountries, setSelCountries] = useState([]);
  const [yearRange,    setYearRange]    = useState([MIN_YEAR, MAX_YEAR]);
  const cardsRef = useRef(null);
  const handleWheel = useCallback(e => {
    if (cardsRef.current) {
      cardsRef.current.scrollTop += e.deltaY;
    }
  }, []);

  const filtered = SOURCES.filter(s => {
    if (selClusters.length > 0 && !selClusters.some(c => (s.clusters||[]).includes(c))) return false;
    if (selTypes.length > 0 && !selTypes.includes(s.type)) return false;
    if (selCountries.length > 0 && !selCountries.includes(s.country)) return false;
    if (s.year < yearRange[0] || s.year > yearRange[1]) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!s.title.toLowerCase().includes(q) &&
          !s.author.toLowerCase().includes(q) &&
          !(s.tags||[]).some(t => t.toLowerCase().includes(q)) &&
          !(s.clusters||[]).some(c => c.toLowerCase().includes(q))) return false;
    }
    return true;
  });

  const hasFilters = selClusters.length>0 || selTypes.length>0 || selCountries.length>0 ||
                     search!=="" || yearRange[0]!==MIN_YEAR || yearRange[1]!==MAX_YEAR;

  const allChips = [
    ...selClusters.map(v  => ({label:v, group:"CLUSTER", onRemove:()=>setSelClusters(selClusters.filter(x=>x!==v))})),
    ...selTypes.map(v     => ({label:v, group:"TYPE",    onRemove:()=>setSelTypes(selTypes.filter(x=>x!==v))})),
    ...selCountries.map(v => ({label:v, group:"COUNTRY", onRemove:()=>setSelCountries(selCountries.filter(x=>x!==v))})),
  ];

  const clearAll = () => { setSearch(""); setSelClusters([]); setSelTypes([]); setSelCountries([]); setYearRange([MIN_YEAR, MAX_YEAR]); };

  return (
    <div onWheel={handleWheel} style={{height:"100vh",display:"flex",flexDirection:"column",overflow:"hidden",background:"#F5F4F0"}}>

      {/* Fixed header */}
      <div style={{flexShrink:0,padding:"2px 32px 0"}}>

        {/* Page title row */}
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"4px"}}>
          <div style={{display:"flex",alignItems:"baseline",gap:"10px"}}>
            <h1 style={{fontSize:"18px",fontWeight:700,color:"#1a1a2e",margin:0}}>Source Library</h1>
            <div style={{fontSize:"10px",fontWeight:600,letterSpacing:"0.08em",textTransform:"uppercase",color:"#9A968E"}}>UNIFIL Research Library</div>
          </div>
          <div style={{fontSize:"11px",color:"#9A968E"}}>Last updated: April 2026</div>
        </div>

        {/* Stats row */}
        <div style={{display:"flex",gap:"10px",marginBottom:"8px"}}>
          <StatCard value={STATS.total}   label="SOURCES" />
          <StatCard value={STATS.themes}  label="THEMES COVERED" />
          <StatCard value={STATS.lessons} label="LL CANDIDATES" />
          <StatCard value={STATS.actors}  label="ACTORS INDEXED" />
        </div>

        {/* Filter row 1 */}
        <div style={{background:"#fff",border:"1px solid #E8E5DE",borderRadius:"6px 6px 0 0",padding:"12px 16px",display:"flex",gap:"12px",alignItems:"center",borderBottom:"1px solid #F0EDE6"}}>
          <div style={{flex:1,position:"relative"}}>
            <div style={{position:"absolute",left:"10px",top:"50%",transform:"translateY(-50%)",pointerEvents:"none"}}>
              <Icon name="search" size={14} color="#9A968E" />
            </div>
            <input value={search} onChange={e=>setSearch(e.target.value)}
              placeholder="Search titles, authors, tags\u2026"
              style={{width:"100%",padding:"8px 10px 8px 32px",border:"1px solid #DDD9D0",borderRadius:"5px",fontSize:"13px",color:"#1a1a2e",background:"#FAFAF8",fontFamily:"inherit"}} />
          </div>
          <div style={{flexShrink:0,width:"220px"}}>
            <RangeSlider min={MIN_YEAR} max={MAX_YEAR} value={yearRange} onChange={setYearRange} />
          </div>
        </div>

        {/* Filter row 2 */}
        <div style={{background:"#FAFAF8",border:"1px solid #E8E5DE",borderRadius:"0 0 6px 6px",borderTop:"none",padding:"10px 16px",marginBottom:"14px",display:"flex",gap:"8px",alignItems:"center",flexWrap:"wrap"}}>
          <MultiSelectFilter label="Cluster" options={ALL_CLUSTERS} selected={selClusters} onChange={setSelClusters} />
          <MultiSelectFilter label="Type"    options={ALL_TYPES}    selected={selTypes}    onChange={setSelTypes} />
          <MultiSelectFilter label="Country" options={ALL_COUNTRIES} selected={selCountries} onChange={setSelCountries} />

          {allChips.length > 0 && (
            <div style={{display:"flex",gap:"6px",flexWrap:"wrap",alignItems:"center",marginLeft:"4px"}}>
              <div style={{width:"1px",height:"20px",background:"#DDD9D0",marginRight:"2px"}} />
              {allChips.map((chip,i) => (
                <div key={i} style={{display:"flex",alignItems:"center",gap:"5px",background:"#fff",border:"1px solid #B8C8D8",borderRadius:"4px",padding:"3px 8px 3px 10px"}}>
                  <span style={{fontSize:"9px",color:"#7A9AB8",textTransform:"uppercase",fontWeight:600,letterSpacing:"0.05em",marginRight:"2px"}}>{chip.group}</span>
                  <span style={{fontSize:"12px",color:"#1B3A5C",fontWeight:500}}>{chip.label}</span>
                  <button onClick={chip.onRemove} style={{background:"none",border:"none",cursor:"pointer",padding:"0 2px",display:"flex",alignItems:"center"}}>
                    <Icon name="close" size={11} color="#7A9AB8" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {hasFilters && (
            <button onClick={clearAll} style={{marginLeft:"auto",padding:"5px 12px",background:"transparent",border:"1px solid #DDD9D0",borderRadius:"4px",fontSize:"11.5px",color:"#8A8880",cursor:"pointer",display:"flex",alignItems:"center",gap:"4px",whiteSpace:"nowrap"}}>
              <Icon name="close" size={11} color="#8A8880" /> Clear all
            </button>
          )}
        </div>

        {/* Result count + legend */}
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:"14px"}}>
          <div style={{fontSize:"12px",color:"#8A8880"}}>
            <strong style={{color:"#1a1a2e"}}>{filtered.length}</strong> source{filtered.length!==1?"s":""} found
          </div>
          <div style={{display:"flex",gap:"12px",flexWrap:"wrap"}}>
            {Object.entries(TYPE_CONFIG).map(([t,c]) => (
              <div key={t} onClick={()=>setSelTypes(selTypes.includes(t)?selTypes.filter(x=>x!==t):[...selTypes,t])}
                style={{display:"flex",alignItems:"center",gap:"5px",cursor:"pointer",opacity:selTypes.length>0&&!selTypes.includes(t)?0.35:1,transition:"opacity .15s"}}>
                <div style={{width:"8px",height:"8px",borderRadius:"2px",background:c.color,flexShrink:0}} />
                <span style={{fontSize:"11px",color:"#5A6475"}}>{t}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Scrollable cards area */}
      <div ref={cardsRef} style={{flex:1,overflowY:"auto",padding:"0 32px 32px"}}>
        {filtered.length === 0 ? (
          <div style={{textAlign:"center",padding:"60px 20px",color:"#8A8880",fontSize:"14px"}}>No sources match the current filters.</div>
        ) : (
          <div style={{display:"grid",gridTemplateColumns:"repeat(2,1fr)",gap:"14px"}}>
            {filtered.map(s => <SourceCard key={s.id} source={s} />)}
          </div>
        )}
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
</script>
</body>
</html>"""


def build_library_html(sources, all_clusters, all_countries, stats):
    all_years = [s["year"] for s in sources if s.get("year")]
    min_year = min(all_years) if all_years else 1980
    max_year = max(all_years) if all_years else 2026

    return (
        _LIBRARY_HTML
        .replace("__SOURCES_JSON__",   json.dumps(sources, ensure_ascii=False))
        .replace("__CLUSTERS_JSON__",  json.dumps(sorted(all_clusters), ensure_ascii=False))
        .replace("__COUNTRIES_JSON__", json.dumps(sorted(all_countries), ensure_ascii=False))
        .replace("__STATS_JSON__",     json.dumps(stats, ensure_ascii=False))
        .replace("__MIN_YEAR__",       str(min_year))
        .replace("__MAX_YEAR__",       str(max_year))
    )


# ── Main entry point ──────────────────────────────────────────────────────────

def show():
    sources   = load_sources()
    all_tags  = get_all_tags(sources)
    all_actors = get_all_actors(sources)
    all_countries = get_all_countries(sources)

    # Session state init
    if "selected_source_id" not in st.session_state:
        st.session_state.selected_source_id = None
    if "editing_source_id" not in st.session_state:
        st.session_state.editing_source_id = None

    # ── Detail / edit view ────────────────────────────────────────────────────
    if st.session_state.selected_source_id:
        selected = next((s for s in sources if s["id"] == st.session_state.selected_source_id), None)
        if not selected:
            st.session_state.selected_source_id = None
            st.rerun()

        is_editing = st.session_state.editing_source_id == selected["id"]

        with st.container():
            if st.button("← Back to sources", key="back_to_grid"):
                st.session_state.selected_source_id = None
                st.session_state.editing_source_id = None
                st.rerun()

            if not is_editing and is_editor():
                if st.button("✎ Edit", key="edit_detail"):
                    st.session_state.editing_source_id = selected["id"]
                    st.rerun()

            st.markdown('<hr style="border:none;border-top:1px solid #E8E5DE;margin:1rem 0;">', unsafe_allow_html=True)

            if is_editing and is_editor():
                render_source_edit(selected, all_tags)
            else:
                if is_editing:
                    st.session_state.editing_source_id = None
                render_source_detail(selected)

        return

    # ── Browse view ───────────────────────────────────────────────────────────
    all_clusters = sorted(set(c for s in sources for c in s.get("thematic_clusters", [])))
    all_types    = sorted(_TYPE_CONFIG.keys())

    # Stats row
    _stats = [
        (len(sources),                                                              "Sources"),
        (len(set(c for s in sources for c in s.get("thematic_clusters", []))),    "Themes Covered"),
        (sum(len(s.get("lessons_learned", [])) for s in sources),                 "LL Candidates"),
        (len(all_actors),                                                           "Actors Indexed"),
    ]
    _stat_cells = ""
    for i, (v, lbl) in enumerate(_stats):
        border = "" if i == len(_stats) - 1 else "border-right:1px solid #DDD9D0;"
        _stat_cells += (
            f'<div style="flex:1;padding:22px 0 18px 0;text-align:center;{border}">'
            f'<div style="font-size:44px;font-weight:700;letter-spacing:-2px;color:#1a1a2e;line-height:1;">{v}</div>'
            f'<div style="font-size:11px;font-weight:500;letter-spacing:0.08em;text-transform:uppercase;color:#8A8F99;margin-top:7px;">{lbl}</div>'
            f'</div>'
        )
    st.markdown(
        f'<div style="display:flex;margin:18px 0 20px 0;border:1px solid #DDD9D0;border-radius:10px;overflow:hidden;background:#FAFAF8;">'
        f'{_stat_cells}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Actor list for filter (from actors_profiles.json)
    _actors_path = Path(__file__).parent.parent / "data" / "actors_profiles.json"
    _all_actor_names = []
    if _actors_path.exists():
        _all_actor_names = sorted(
            {a["name"] for a in json.loads(_actors_path.read_text(encoding="utf-8")) if a.get("name")},
            key=str.casefold,
        )

    # Filters
    fc1, fc2, fc3, fc4 = st.columns([2, 2, 1, 1])
    with fc1:
        search = st.text_input("Search", placeholder="Title, author, tag…", label_visibility="collapsed")
    with fc2:
        sel_clusters = st.multiselect("Clusters", all_clusters, label_visibility="collapsed",
                                      placeholder="Filter by cluster…")
    with fc3:
        sel_types = st.multiselect("Types", all_types, label_visibility="collapsed",
                                   placeholder="Filter by type…")
    with fc4:
        sel_actors = st.multiselect("Actors", _all_actor_names, label_visibility="collapsed",
                                    placeholder="Filter by actor…")

    st.markdown("**Sources published per period**")
    st.plotly_chart(_build_density_chart(sources), use_container_width=True,
                    config={"displayModeBar": False})
    st.markdown("""
    <div style="display:flex; gap:1.5rem; font-size:0.75rem; color:#8a9ab0;
         margin-bottom:1rem; margin-top:-1rem;">
        <span><span style="display:inline-block;width:10px;height:10px;background:#1a3a5c;
            border-radius:1px;margin-right:4px;vertical-align:middle;"></span>2+ sources</span>
        <span><span style="display:inline-block;width:10px;height:10px;background:#9ab8d0;
            border-radius:1px;margin-right:4px;vertical-align:middle;"></span>1 source</span>
        <span><span style="display:inline-block;width:10px;height:10px;background:#e0dbd2;
            border-radius:1px;margin-right:4px;vertical-align:middle;"></span>None published</span>
    </div>
    """, unsafe_allow_html=True)
    year_range = st.slider(
        "Publication year range",
        min_value=MISSION_START, max_value=MISSION_END,
        value=(MISSION_START, MISSION_END),
        step=1, format="%d",
        key="lib_year_range",
    )
    y_start, y_end = year_range

    # Filter sources
    filtered = []
    for s in sources:
        if s.get("year", 0) < y_start or s.get("year", 0) > y_end:
            continue
        if search:
            q = search.lower()
            haystack = (s.get("title", "") + s.get("author", "") +
                        " ".join(s.get("tags", [])) + " ".join(s.get("thematic_clusters", []))).lower()
            if q not in haystack:
                continue
        if sel_clusters and not any(c in s.get("thematic_clusters", []) for c in sel_clusters):
            continue
        if sel_types and normalize_source_type(s.get("source_type", "")) not in sel_types:
            continue
        if sel_actors:
            src_actors = [a.lower() for a in s.get("actors", [])]
            if not any(a.lower() in src_actors for a in sel_actors):
                continue
        filtered.append(s)

    st.markdown(f"**{len(filtered)}** source{'s' if len(filtered) != 1 else ''} found")

    # Card grid — 2 columns. The open button is overlaid invisibly on the
    # arrow in each card's bottom-right corner (see CSS below).
    st.markdown("""
    <style>
    div[class*="st-key-srccard_"] { position: relative; }
    div[class*="st-key-srccard_"] div[data-testid="stElementContainer"]:has(div[data-testid="stButton"]) {
        position: absolute; right: 0; bottom: 4px; z-index: 1; margin: 0;
        width: 52px !important; height: 46px !important;
    }
    div[class*="st-key-srccard_"] div[data-testid="stButton"],
    div[class*="st-key-srccard_"] div[data-testid="stButton"] button {
        width: 100%; height: 100%; min-height: 0; margin: 0; padding: 0;
    }
    div[class*="st-key-srccard_"] div[data-testid="stButton"] button {
        opacity: 0; cursor: pointer;
    }
    div[class*="st-key-srccard_"]:has(button:hover) .source-card-arrow {
        color: #1a1a2e !important; opacity: 1 !important;
    }
    </style>
    """, unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    for i, s in enumerate(filtered):
        col = col_a if i % 2 == 0 else col_b
        with col:
            with st.container(key=f"srccard_{s['id']}"):
                st.markdown(_card_html(s), unsafe_allow_html=True)
                if st.button("Open →", key=f"open_{s['id']}"):
                    st.session_state.selected_source_id = s["id"]
                    st.rerun()
