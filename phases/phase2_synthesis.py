"""
phases/phase2_synthesis.py
──────────────────────────
Phase 2: Automated Charter Synthesis
Aggregates the 8 validated interview answers into a professional Markdown
Project Charter, streams it to the UI, and lets the user approve, edit,
or regenerate before proceeding to the Knowledge Area Workspace.
"""
from __future__ import annotations

from datetime import date

import streamlit as st

from core.llm_client import stream_completion
from core.prompts import SYNTHESIS_PROMPT
from utils.exporters import markdown_to_docx_bytes, markdown_to_pdf_bytes

_SYNTHESIS_SYSTEM = (
    "You are a PMP documentation specialist. "
    "Generate formal project documentation in Markdown format only. "
    "No preamble, no meta-commentary, no markdown code fences — raw Markdown only. "
    "You must output all sections 1 through 10 completely. "
    "Do not skip or abbreviate sections due to length."
)

_SECTION_LABELS: list[tuple[str, str]] = [
    ("BACKGROUND & JUSTIFICATION", "background"),
    ("PROJECT GOALS & OBJECTIVES", "goals"),
    ("SCOPE DEFINITION", "scope"),
    ("KEY STAKEHOLDERS", "stakeholders"),
    ("MILESTONES & TIMELINE", "milestones"),
    ("BUDGET OVERVIEW", "budget"),
    ("CONSTRAINTS & ASSUMPTIONS", "constraints"),
    ("HIGH-LEVEL RISKS", "risks"),
]

_REQUIRED_CHARTER_SECTIONS: list[str] = [
    "## 1. Project Overview",
    "## 2. Business Case & Project Justification",
    "## 3. Project Objectives (SMART)",
    "## 4. Scope Statement",
    "## 5. Stakeholder Register (Summary)",
    "## 6. High-Level Milestone Schedule",
    "## 7. Budget Summary",
    "## 8. Constraints & Assumptions",
    "## 9. High-Level Risk Summary",
    "## 10. Charter Authorization",
]


def _missing_sections(charter_text: str) -> list[str]:
    return [section for section in _REQUIRED_CHARTER_SECTIONS if section not in charter_text]


def _build_project_data() -> str:
    """
    Concatenate all AI-refined answers (falling back to raw user input)
    into a structured string for the synthesis prompt.
    """
    refined = st.session_state.ai_feedback
    raw = st.session_state.user_answers
    parts: list[str] = []

    for label, key in _SECTION_LABELS:
        content = refined.get(key) or raw.get(key, "[Not provided]")
        parts.append(f"### {label}\n{content}")

    return "\n\n".join(parts)


def _stream_charter() -> str:
    """Stream the charter from the LLM and render it in-place. Returns full text."""
    project_data = _build_project_data()
    prompt = SYNTHESIS_PROMPT.format(
        project_data=project_data,
        date=date.today().strftime("%B %d, %Y"),
        project_title_placeholder="[Project Title — infer from Background & Goals]",
    )
    prompt += (
        "\n\nSTRICT COMPLETENESS REQUIREMENTS:\n"
        "- Include all sections 1 to 10 from the template.\n"
        "- Include all stakeholder rows present in the interview data.\n"
        "- Do not stop early; complete the entire charter.\n"
    )
    messages = [
        {"role": "system", "content": _SYNTHESIS_SYSTEM},
        {"role": "user", "content": prompt},
    ]

    placeholder = st.empty()
    full_text = ""
    for chunk in stream_completion(messages, temperature=0.3, max_tokens=6000):
        full_text += chunk
        placeholder.markdown(full_text + "▌")   # streaming cursor

    # If the model truncates mid-document, request continuation from first missing section.
    retry_count = 0
    while retry_count < 2:
        missing = _missing_sections(full_text)
        if not missing:
            break

        continue_prompt = (
            "The previous charter output was truncated before all required sections were completed.\n\n"
            f"First missing section: {missing[0]}\n"
            "Continue the charter from that section onward.\n"
            "Do not repeat earlier sections.\n"
            "Return markdown only.\n\n"
            "Already generated charter:\n"
            f"{full_text}\n\n"
            "Original project data:\n"
            f"{project_data}"
        )
        cont_messages = [
            {"role": "system", "content": _SYNTHESIS_SYSTEM},
            {"role": "user", "content": continue_prompt},
        ]

        continuation = ""
        for chunk in stream_completion(cont_messages, temperature=0.2, max_tokens=4000):
            continuation += chunk
            placeholder.markdown((full_text + "\n\n" + continuation) + "▌")

        if continuation.strip():
            full_text = full_text.rstrip() + "\n\n" + continuation.strip()

        retry_count += 1

    placeholder.markdown(full_text)             # final render, no cursor
    return full_text


# ── Main render ───────────────────────────────────────────────────────────────

def render_phase2() -> None:
    st.subheader("Phase 2 — Project Charter Synthesis")
    st.caption(
        "Your 8-section interview is complete. "
        "Review the AI-generated charter below, then approve to unlock the Knowledge Area Workspace."
    )
    st.divider()

    # Generate charter on first visit; display cached version on subsequent renders
    if not st.session_state.charter_markdown:
        st.info("⚙️ Generating your Project Charter — this may take 20–40 seconds…")
        charter = _stream_charter()
        st.session_state.charter_markdown = charter
    else:
        st.markdown(st.session_state.charter_markdown)

    st.divider()

    # ── Action bar ────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button(
            "✅ Approve Charter & Continue →",
            type="primary",
            width="stretch",
        ):
            st.session_state.is_charter_complete = True
            st.session_state.phase = 3
            st.rerun()

    with col2:
        if st.button("🔄 Regenerate", width="stretch"):
            st.session_state.charter_markdown = ""
            st.rerun()

    with col3:
        st.download_button(
            label="⬇️ Charter (.docx)",
            data=markdown_to_docx_bytes(st.session_state.charter_markdown),
            file_name="project_charter.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            width="stretch",
        )

    with col4:
        st.download_button(
            label="⬇️ Charter (.pdf)",
            data=markdown_to_pdf_bytes(st.session_state.charter_markdown),
            file_name="project_charter.pdf",
            mime="application/pdf",
            width="stretch",
        )

    # ── Manual edit expander ──────────────────────────────────────────────────
    with st.expander("✏️ Edit Charter Manually"):
        st.caption("Make direct changes to the Markdown, then save.")
        edited = st.text_area(
            "Charter Markdown",
            value=st.session_state.charter_markdown,
            height=500,
            label_visibility="collapsed",
        )
        if st.button("💾 Save Edits", type="secondary"):
            st.session_state.charter_markdown = edited
            st.success("Charter updated.")
            st.rerun()
