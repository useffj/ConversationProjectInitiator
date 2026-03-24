"""
phases/phase3_workspace.py
──────────────────────────
Phase 3: The Knowledge Area Workspace
Context-locked to the approved Project Charter.  Users can navigate all 10 PMI
Knowledge Areas; the AI pre-fills documents (Risk Register, Stakeholder Grid,
etc.) and provides Human-in-the-Loop (HITL) refinement of casual entries into
formal PMP-compliant language using the Cause-Event-Impact framework.
"""
from __future__ import annotations

import streamlit as st

from core.llm_client import chat_completion
from core.prompts import (
    HITL_REFINEMENT_PROMPT,
    KNOWLEDGE_AREA_PROMPTS,
    RISK_REGISTER_PROMPT,
    STAKEHOLDER_GRID_PROMPT,
)
from utils.exporters import build_full_report, markdown_to_docx_bytes, markdown_to_pdf_bytes

PMI_KNOWLEDGE_AREAS: list[str] = [
    "Integration Management",
    "Scope Management",
    "Schedule Management",
    "Cost Management",
    "Quality Management",
    "Resource Management",
    "Communications Management",
    "Risk Management",
    "Procurement Management",
    "Stakeholder Engagement",
]

_AREA_ICONS: dict[str, str] = {
    "Integration Management": "🔗",
    "Scope Management": "📐",
    "Schedule Management": "📅",
    "Cost Management": "💰",
    "Quality Management": "🏆",
    "Resource Management": "👥",
    "Communications Management": "📡",
    "Risk Management": "⚠️",
    "Procurement Management": "🤝",
    "Stakeholder Engagement": "🌐",
}

_GENERATION_SYSTEM = (
    "You are a PMP documentation specialist. "
    "Generate thorough, professional project management documents in Markdown. "
    "Use tables, numbered lists, and headers as appropriate. "
    "No preamble, no meta-commentary."
)


# ── Document generation ───────────────────────────────────────────────────────

def _charter_summary() -> str:
    charter = st.session_state.get("charter_markdown", "")
    return charter[:3500] if len(charter) > 3500 else charter


def _generate_document(area: str) -> str:
    """
    Call the LLM (blocking, with spinner at call site) to produce the
    knowledge-area document.  Returns the full Markdown string.
    """
    summary = _charter_summary()

    if area == "Risk Management":
        risks_raw = st.session_state.ai_feedback.get(
            "risks", st.session_state.user_answers.get("risks", "")
        )
        prompt = RISK_REGISTER_PROMPT.format(
            charter_summary=summary, risks_data=risks_raw
        )
    elif area == "Stakeholder Engagement":
        stake_raw = st.session_state.ai_feedback.get(
            "stakeholders",
            st.session_state.user_answers.get("stakeholders", ""),
        )
        prompt = STAKEHOLDER_GRID_PROMPT.format(
            charter_summary=summary, stakeholders_data=stake_raw
        )
    else:
        template = KNOWLEDGE_AREA_PROMPTS.get(area, "")
        if not template:
            return f"# {area}\n\n*No template available for this area.*"
        prompt = template.format(charter_summary=summary)

    messages = [
        {"role": "system", "content": _GENERATION_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    return chat_completion(messages, temperature=0.5, max_tokens=2500)


# ── HITL refinement ───────────────────────────────────────────────────────────

def _refine_entry(user_input: str, doc_type: str, area: str) -> str:
    project_context = _charter_summary()[:600]
    prompt = HITL_REFINEMENT_PROMPT.format(
        document_type=doc_type,
        knowledge_area=area,
        user_input=user_input,
        project_context=project_context,
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a PMP documentation specialist. "
                "Return only the refined statement — nothing else."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    return chat_completion(messages, temperature=0.3)


# ── Sidebar navigation ────────────────────────────────────────────────────────

def _render_sidebar_nav() -> None:
    with st.sidebar:
        st.divider()
        st.subheader("📚 PMI Knowledge Areas")
        for area in PMI_KNOWLEDGE_AREAS:
            icon = _AREA_ICONS.get(area, "📋")
            is_active = area == st.session_state.current_knowledge_area
            if is_active:
                st.markdown(f"**→ {icon} {area}**")
            else:
                if st.button(
                    f"{icon} {area}",
                    key=f"nav_{area}",
                    use_container_width=True,
                ):
                    st.session_state.current_knowledge_area = area
                    st.rerun()

        # Download full report when at least one area has been generated
        if st.session_state.knowledge_area_data:
            st.divider()
            full_report = build_full_report(st.session_state)
            st.download_button(
                "⬇️ Full Report (.docx)",
                data=markdown_to_docx_bytes(full_report),
                file_name="project_documentation.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
            st.download_button(
                "⬇️ Full Report (.pdf)",
                data=markdown_to_pdf_bytes(full_report),
                file_name="project_documentation.pdf",
                mime="application/pdf",
                use_container_width=True,
            )


# ── Main render ───────────────────────────────────────────────────────────────

def render_phase3() -> None:
    _render_sidebar_nav()

    area: str = st.session_state.current_knowledge_area
    icon = _AREA_ICONS.get(area, "📋")

    # ── Page header
    col_title, col_back = st.columns([4, 1])
    with col_title:
        st.subheader(f"Phase 3 — Knowledge Area Workspace")
        st.markdown(f"### {icon} {area}")
    with col_back:
        st.write("")  # vertical spacer
        if st.button("← Charter", use_container_width=True):
            st.session_state.phase = 2
            st.rerun()

    st.caption("Context locked to your approved Project Charter.")
    st.divider()

    # ── Generate or display document
    area_data: dict = st.session_state.knowledge_area_data

    if area not in area_data:
        with st.spinner(f"Generating {area} document from your Charter…"):
            content = _generate_document(area)
            area_data[area] = content
        st.markdown(content)
    else:
        st.markdown(area_data[area])

    # ── Action row
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            f"⬇️ {area} (.docx)",
            data=markdown_to_docx_bytes(area_data.get(area, "")),
            file_name=f"{area.lower().replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
    with col2:
        st.download_button(
            f"⬇️ {area} (.pdf)",
            data=markdown_to_pdf_bytes(area_data.get(area, "")),
            file_name=f"{area.lower().replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with col3:
        if st.button("🔄 Regenerate Document", use_container_width=True):
            area_data.pop(area, None)
            st.rerun()

    # ── HITL Refinement ───────────────────────────────────────────────────────
    st.divider()
    with st.expander("✏️ Human-in-the-Loop (HITL) Refinement", expanded=False):
        st.markdown(
            "**Add or refine entries in plain language — the AI will convert them "
            "to formal PMP-compliant statements using the Cause-Event-Impact framework.**"
        )
        st.caption(
            "Example → type: *'The main developer might quit'*  "
            "→ AI returns: *'Due to unplanned attrition of the Lead Developer, resource "
            "availability may be critically reduced, resulting in a potential 3-week schedule "
            "delay and a 12% budget overrun for backfill and knowledge transfer costs.'*"
        )

        hitl_input: str = st.text_area(
            "Informal entry:",
            height=80,
            placeholder="Describe a risk, assumption, issue, or any entry in plain language…",
            key=f"hitl_input_{area}",
        )
        doc_type: str = st.text_input(
            "Document type:",
            value=f"{area} Document",
            key=f"hitl_doctype_{area}",
        )

        if st.button("🪄 Polish with AI", type="primary", key=f"hitl_polish_{area}"):
            if hitl_input.strip():
                with st.spinner("Applying Cause-Event-Impact framework…"):
                    refined = _refine_entry(hitl_input.strip(), doc_type, area)
                st.session_state.hitl_refined[area] = refined
            else:
                st.warning("Please enter some text to refine.")

        # Show refined result and append option (persists via session state)
        refined_result: str = st.session_state.hitl_refined.get(area, "")
        if refined_result:
            st.success("**Refined (PMP-compliant) Statement:**")
            st.markdown(f"> {refined_result}")

            if st.button(
                "➕ Append to Document", key=f"hitl_append_{area}", type="secondary"
            ):
                current_doc = area_data.get(area, "")
                area_data[area] = (
                    current_doc
                    + f"\n\n---\n**[Added via HITL Refinement]**\n\n{refined_result}"
                )
                st.session_state.hitl_refined[area] = ""  # clear after appending
                st.success("Entry appended to the document.")
                st.rerun()
