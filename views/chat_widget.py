"""
Floating chat widget for the UNIFIL Research Library.

Renders a collapsed chat bubble in the bottom-right corner of every page that
expands into a Q&A panel. Questions are answered from the corpus via
utils.chat_utils.answer_question, with expandable source references.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.chat_utils import answer_question, get_source

_CSS = """
<style>
/* Floating bubble (collapsed) */
div[class*="st-key-unifil_chat_bubble"] {
    position: fixed; bottom: 22px; right: 22px; z-index: 1000; width: 60px;
}
div[class*="st-key-unifil_chat_bubble"] button {
    width: 60px !important; height: 60px !important; border-radius: 50% !important;
    background: #0077B6 !important; color: #fff !important; border: none !important;
    font-size: 24px !important; padding: 0 !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.25) !important;
}
div[class*="st-key-unifil_chat_bubble"] button:hover {
    background: #1B2A4A !important; color: #fff !important;
}

/* Panel (expanded) */
div[class*="st-key-unifil_chat_panel"] {
    position: fixed; bottom: 22px; right: 22px; z-index: 1000;
    width: 372px; max-width: calc(100vw - 32px);
    background: #F5F4F0; border: 1px solid #E8E5DE; border-radius: 12px;
    box-shadow: 0 8px 30px rgba(0,0,0,0.22);
    padding: 12px 14px 14px 14px;
}
/* Enlarged panel variant (keyed unifil_chat_panel_lg) */
div[class*="st-key-unifil_chat_panel_lg"] {
    width: 640px;
}
/* Compact typography inside chat messages */
div[class*="st-key-unifil_chat_panel"] [data-testid="stChatMessage"] {
    padding: 2px 0; gap: 0.5rem;
}
div[class*="st-key-unifil_chat_panel"] [data-testid="stChatMessage"] p,
div[class*="st-key-unifil_chat_panel"] [data-testid="stChatMessage"] li {
    font-size: 0.8rem !important; line-height: 1.45 !important;
    margin-bottom: 0.3rem !important;
}
div[class*="st-key-unifil_chat_panel"] [data-testid="stChatMessage"] h1,
div[class*="st-key-unifil_chat_panel"] [data-testid="stChatMessage"] h2,
div[class*="st-key-unifil_chat_panel"] [data-testid="stChatMessage"] h3 {
    font-size: 0.88rem !important; font-weight: 700 !important;
    padding: 0 !important; margin: 0.5rem 0 0.25rem 0 !important;
}
div[class*="st-key-unifil_chat_panel"] [data-testid="stChatMessage"] [data-testid="stChatMessageAvatarCustom"],
div[class*="st-key-unifil_chat_panel"] [data-testid="stChatMessage"] img {
    width: 24px !important; height: 24px !important; font-size: 14px !important;
}
/* References expander: compact */
div[class*="st-key-unifil_chat_panel"] [data-testid="stExpander"] summary p {
    font-size: 0.75rem !important;
}
div[class*="st-key-unifil_chat_panel"] [data-testid="stExpander"] p {
    font-size: 0.75rem !important; margin-bottom: 0.25rem !important;
}
/* Header */
.chat-title {
    font-family: 'IBM Plex Sans', sans-serif; font-weight: 700;
    font-size: 15px; color: #1B2A4A; line-height: 1.2;
}
.chat-sub {
    font-size: 11px; color: #8A8880; text-transform: uppercase;
    letter-spacing: 0.06em; margin-top: 2px;
}
/* Close button — compact, not the big pill style */
div[class*="st-key-unifil_chat_panel"] div[data-testid="stButton"] button {
    padding: 2px 8px !important; font-size: 15px !important; min-height: 0 !important;
}
/* Send button — navy accent, full width */
div[class*="st-key-unifil_chat_panel"] div[data-testid="stFormSubmitButton"] button {
    background: #0077B6 !important; color: #fff !important; border: none !important;
    width: 100% !important;
}
div[class*="st-key-unifil_chat_panel"] div[data-testid="stFormSubmitButton"] button:hover {
    background: #1B2A4A !important; color: #fff !important;
}
</style>
"""


def _render_references(source_ids):
    with st.expander(f"📚 {len(source_ids)} reference{'s' if len(source_ids) != 1 else ''}"):
        for sid in source_ids:
            s = get_source(sid)
            if not s:
                continue
            meta = " · ".join(
                x for x in [s.get("author", ""), str(s.get("year", "")),
                            s.get("publisher", "")] if x
            )
            st.markdown(f"**{s.get('title', '')}**  \n<span style='font-size:0.8rem;color:#5A6475;'>{meta}</span>",
                        unsafe_allow_html=True)


def render_chat_widget():
    ss = st.session_state
    ss.setdefault("chat_open", False)
    ss.setdefault("chat_expanded", False)
    ss.setdefault("chat_history", [])   # list of {role, content, sources?}
    ss.setdefault("chat_pending", False)

    st.markdown(_CSS, unsafe_allow_html=True)

    # ── Collapsed: bubble button ──────────────────────────────────────────────
    if not ss.chat_open:
        with st.container(key="unifil_chat_bubble"):
            if st.button("💬", key="chat_open_btn", help="Ask about the UNIFIL research library"):
                ss.chat_open = True
                st.rerun()
        return

    # ── Expanded: panel (larger key variant when enlarged) ────────────────────
    panel_key = "unifil_chat_panel_lg" if ss.chat_expanded else "unifil_chat_panel"
    history_height = 520 if ss.chat_expanded else 330
    with st.container(key=panel_key):
        head_l, head_m, head_r = st.columns([5, 1, 1])
        with head_l:
            st.markdown(
                "<div class='chat-title'>Research Assistant</div>"
                "<div class='chat-sub'>Ask about the corpus</div>",
                unsafe_allow_html=True,
            )
        with head_m:
            size_icon = "⤡" if ss.chat_expanded else "⤢"
            size_help = "Shrink" if ss.chat_expanded else "Expand"
            if st.button(size_icon, key="chat_size_btn", help=size_help):
                ss.chat_expanded = not ss.chat_expanded
                st.rerun()
        with head_r:
            if st.button("✕", key="chat_close_btn", help="Close"):
                ss.chat_open = False
                st.rerun()

        # Message history (scrollable fixed-height region)
        with st.container(height=history_height):
            if not ss.chat_history and not ss.chat_pending:
                st.markdown(
                    "<div style='font-size:0.85rem;color:#5A6475;line-height:1.5;'>"
                    "Hi — I can answer questions from the UNIFIL library: its sources, "
                    "timeline, research gaps, and actors. Try <em>“What do sources say "
                    "about the Tripartite mechanism?”</em></div>",
                    unsafe_allow_html=True,
                )
            for m in ss.chat_history:
                avatar = "🧑" if m["role"] == "user" else "🇺🇳"
                with st.chat_message(m["role"], avatar=avatar):
                    st.markdown(m["content"])
                    if m["role"] == "assistant" and m.get("sources"):
                        _render_references(m["sources"])
            if ss.chat_pending:
                with st.chat_message("assistant", avatar="🇺🇳"):
                    st.markdown("_Searching the corpus…_")

        # Process a pending question (runs while the "Searching…" bubble is shown)
        if ss.chat_pending:
            try:
                answer, cites = answer_question(
                    [{"role": m["role"], "content": m["content"]} for m in ss.chat_history]
                )
            except Exception as e:  # surface API/network errors in-widget
                answer, cites = (f"Sorry — I couldn't answer that right now. ({e})", [])
            ss.chat_history.append({"role": "assistant", "content": answer, "sources": cites})
            ss.chat_pending = False
            st.rerun()

        # Input (only rendered when idle, so no double-submit)
        with st.form("unifil_chat_form", clear_on_submit=True):
            q = st.text_input(
                "Ask", label_visibility="collapsed",
                placeholder="Ask about the UNIFIL library…",
            )
            submitted = st.form_submit_button("Send")
        if submitted and q.strip():
            ss.chat_history.append({"role": "user", "content": q.strip()})
            ss.chat_pending = True
            st.rerun()
