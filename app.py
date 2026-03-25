"""
app.py — Conversational Project Initiator
──────────────────────────────────────────
Main Streamlit entry point.  Handles:
  • Session initialisation
  • Phase routing  (1 → Interview, 2 → Synthesis, 3 → Workspace)
  • Persistent sidebar with progress, API-key check, and reset
"""
from __future__ import annotations

# Load .env BEFORE any module that reads env vars
from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from config.settings import APP_TITLE, APP_SUBTITLE, get_google_api_key
from core.session_manager import init_session_state, INTERVIEW_QUESTIONS
from phases.phase1_interview import render_phase1
from phases.phase2_synthesis import render_phase2
from phases.phase3_workspace import render_phase3

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Shrink default top padding */
    .block-container { padding-top: 1.5rem; }
    /* Slightly heavier sidebar font */
    section[data-testid="stSidebar"] { font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ── Sidebar ───────────────────────────────────────────────────────────────────

def _render_sidebar() -> None:
    with st.sidebar:
        st.image(
            "https://img.shields.io/badge/PMP-Certified%20AI-1E6FFF?style=for-the-badge",
            width="stretch",
        )
        st.title("Project Initiator")
        st.caption(APP_SUBTITLE)
        st.divider()

        phase: int = st.session_state.phase

        # Phase progress
        phase_labels = {
            1: "Strategic Interview",
            2: "Charter Synthesis",
            3: "Knowledge Workspace",
        }
        for p, label in phase_labels.items():
            if p < phase:
                st.success(f"✓ Phase {p}: {label}")
            elif p == phase:
                st.info(f"▶ Phase {p}: {label}")
            else:
                st.markdown(f"&nbsp;&nbsp;&nbsp;Phase {p}: {label}")

        # Interview sub-progress (Phase 1 only)
        if phase == 1:
            st.divider()
            step = st.session_state.current_step
            total = len(INTERVIEW_QUESTIONS)
            st.caption(f"Interview progress: **{min(step, total)}/{total}** questions")
            st.progress(min(step, total) / total)

        # Reset
        st.divider()
        if st.button("🔄 Start New Project", width="stretch"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()


# ── Landing / API-key guard ───────────────────────────────────────────────────

def _render_welcome() -> None:
    """Shown only when no API key is present."""
    st.title(f"🏗️ {APP_TITLE}")
    st.subheader(APP_SUBTITLE)
    st.divider()
    st.error("### ⚠️ Google AI Studio API Key Required")
    st.markdown(
        """
        This application requires a Google AI Studio API key to function.

        **Streamlit Cloud deployment:**
        1. Open your app's settings → **Secrets**.
        2. Add the following and click **Save**:
           ```toml
           GOOGLE_API_KEY = "your-google-ai-studio-key"
           ```
        3. The app will restart automatically.

        **Local development:**
        1. Copy `.env.example` to `.env` in the project root.
        2. Add your key: `GOOGLE_API_KEY=your-google-ai-studio-key`
        3. Restart the server: `streamlit run app.py`

        > Your key is **never** logged or transmitted beyond the official Google Generative AI API endpoint.
        """
    )


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    init_session_state()

    if not get_google_api_key():
        _render_welcome()
        return

    _render_sidebar()

    # Page header
    st.markdown(f"# 🏗️ {APP_TITLE}")
    st.markdown(
        "The Conversational Project Initiator is an AI-powered strategic tool designed to "
        "bridge the gap between \"messy\" early-stage project ideas and rigorous, PMI-standard "
        "documentation. It replaces static, intimidating templates with a high-value, guided "
        "interview. By leveraging AI, the system validates project data in real-time, ensuring "
        "that project charters and risk registers are SMART (Specific, Measurable, Achievable, "
        "Relevant, Time-bound) before they are ever formalized. " \
        "Proceed below to answer the interview questions"
    )
    st.divider()

    # Phase router
    phase: int = st.session_state.phase
    if phase == 1:
        render_phase1()
    elif phase == 2:
        render_phase2()
    elif phase == 3:
        render_phase3()
    else:
        st.error(f"Unknown phase: {phase}. Please reset the session.")


if __name__ == "__main__":
    main()
