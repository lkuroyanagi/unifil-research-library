import streamlit as st
from pathlib import Path

_BASE = Path(__file__).parent.parent

def show_pdf(file_path, filename):
    with open(file_path, "rb") as f:
        pdf_bytes = f.read()
    st.download_button(
        label="⬇ Download PDF",
        data=pdf_bytes,
        file_name=filename,
        mime="application/pdf",
    )

def show():
    st.markdown("""
    <div class="library-header">
        <h1 class="library-title">Resolutions</h1>
    </div>
    <div style="font-size:0.9rem; color:#5a6a7a;
         margin-bottom:1.5rem; max-width:680px;">
        Key Security Council resolutions shaping
        UNIFIL's mandate, 1978–2006.
    </div>
    """, unsafe_allow_html=True)

    # ── SCR 425 & 426 (1978) ─────────────────────────────
    st.markdown("""
    <div style="font-family:'Playfair Display',serif;
         font-size:1.1rem; font-weight:700; color:#1a1a2e;
         padding:1rem 0 0.5rem 0;
         border-bottom:1px solid #E8E5DE;
         margin-bottom:1rem;">
        Resolutions 425 &amp; 426 (1978)
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.82rem; color:#5a6a7a;
         margin-bottom:0.8rem;">
        Adopted 19 March 1978 · Established UNIFIL
    </div>
    """, unsafe_allow_html=True)

    import pandas as pd
    df_425 = pd.DataFrame([
        ["Confirm Israeli withdrawal",
         "Call on Israel to cease military action and withdraw forthwith from all Lebanese territory."],
        ["Restore international peace",
         "Restore peace and security in southern Lebanon."],
        ["Support Lebanese authority",
         "Assist the Government of Lebanon in ensuring the return of its effective authority in the area."],
        ["Force composition",
         "Composed of personnel drawn from Member States; initial authorised strength ~4,000 troops (later ~6,000 per SCR 427)."],
        ["Reporting",
         "Secretary-General to report to the Council within 24 hours on implementation."],
    ], columns=["Mandated Task", "Detail"])

    st.dataframe(
        df_425,
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Read the original resolutions →"):
        pdf_path = _BASE / "data" / "pdfs" / "scr_425_426.pdf"
        st.markdown(
            "Original UN document: "
            "[SCR 425/426](https://undocs.org/S/RES/425(1978))"
        )
        if pdf_path.exists():
            show_pdf(str(pdf_path), "scr_425_426.pdf")
        else:
            st.warning("PDF file not found. Please ensure scr_425_426.pdf is in data/pdfs/")

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── SCR 1701 (2006) ──────────────────────────────────
    st.markdown("""
    <div style="font-family:'Playfair Display',serif;
         font-size:1.1rem; font-weight:700; color:#1a1a2e;
         padding:1rem 0 0.5rem 0;
         border-bottom:1px solid #E8E5DE;
         margin-bottom:1rem;">
        Resolution 1701 (2006)
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:0.82rem; color:#5a6a7a;
         margin-bottom:0.8rem;">
        Adopted 11 August 2006 · Enhanced UNIFIL mandate
        · Force ceiling raised to 15,000
    </div>
    """, unsafe_allow_html=True)

    df_1701 = pd.DataFrame([
        ["Monitor cessation of hostilities",
         "Monitor the full cessation of hostilities between Hezbollah and Israel."],
        ["Support LAF deployment",
         "Accompany and support the Lebanese Armed Forces as they deploy throughout the South, including along the Blue Line, as Israel withdraws."],
        ["Coordinate with parties",
         "Coordinate activities with the Government of Lebanon and the Government of Israel."],
        ["Humanitarian access",
         "Extend assistance to help ensure humanitarian access to civilian populations and the voluntary and safe return of displaced persons."],
        ["Area free of armed personnel",
         "Assist LAF in establishing an area between the Blue Line and the Litani River free of any armed personnel, assets and weapons other than those of the Government of Lebanon and UNIFIL."],
        ["Border security",
         "Assist the Government of Lebanon, at its request, in securing its borders and other entry points to prevent unauthorised entry of arms or related materiel."],
        ["Force protection",
         "Protect UN personnel, facilities, installations and equipment; ensure the security and freedom of movement of UN and humanitarian personnel."],
        ["Civilian protection",
         "Protect civilians under imminent threat of physical violence (paragraph 12 — 'all necessary action')."],
        ["Maritime Task Force",
         "Assist the Government of Lebanon in securing its borders at sea — legal basis for the deployment of the MTF, the UN's first maritime peacekeeping component."],
        ["Force ceiling",
         "Expanded to a maximum of 15,000 troops, from the original ~2,000 authorised under SCR 425/426."],
    ], columns=["Mandated Task", "Detail"])

    st.dataframe(
        df_1701,
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Read the original resolution →"):
        pdf_path = _BASE / "data" / "pdfs" / "scr_1701.pdf"
        st.markdown(
            "Original UN document: "
            "[SCR 1701](https://undocs.org/S/RES/1701(2006))"
        )
        if pdf_path.exists():
            show_pdf(str(pdf_path), "scr_1701.pdf")
        else:
            st.warning("PDF file not found. Please ensure scr_1701.pdf is in data/pdfs/")
