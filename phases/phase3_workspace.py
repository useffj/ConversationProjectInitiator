"""
phases/phase3_workspace.py
──────────────────────────
Phase 3: Knowledge Area Engine
Renders all 10 PMI knowledge areas with editable tables and cached AI generation.
"""
from __future__ import annotations

import json
import re
from typing import Any

import streamlit as st

from core.llm_client import chat_completion
from core.prompts import HITL_REFINEMENT_PROMPT
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

_PMP_MENTOR_SYSTEM = (
    "You are a Senior PMP Mentor with deep PMBOK expertise. "
    "Return practical, implementation-ready outputs using precise PMI terminology. "
    "No preamble and no markdown code fences unless asked."
)


def get_project_context() -> str:
    """Join raw user answers and AI-refined charter inputs into one reference string."""
    user_answers: dict[str, str] = st.session_state.get("user_answers", {})
    ai_feedback: dict[str, str] = st.session_state.get("ai_feedback", {})
    charter: str = st.session_state.get("charter_markdown", "")

    lines: list[str] = ["PROJECT CONTEXT (USER INPUT + AI REFINEMENT)"]
    for key, value in user_answers.items():
        lines.append(f"- User [{key}]: {value}")

    for key, value in ai_feedback.items():
        lines.append(f"- Refined [{key}]: {value}")

    if charter:
        lines.append("\nAPPROVED CHARTER\n")
        lines.append(charter)

    return "\n".join(lines).strip()


def _extract_json_array(raw_text: str) -> list[dict[str, str]]:
    """Parse an LLM response into a JSON array of objects."""
    text = (raw_text or "").strip()
    if not text:
        return []

    def _as_list(candidate: str) -> list[dict[str, str]]:
        parsed = json.loads(candidate)
        if isinstance(parsed, list):
            return [row for row in parsed if isinstance(row, dict)]
        return []

    try:
        return _as_list(text)
    except Exception:
        pass

    fence_match = re.search(r"```json\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        try:
            return _as_list(fence_match.group(1).strip())
        except Exception:
            pass

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return _as_list(candidate)
        except Exception:
            pass

    return []


@st.cache_data(show_spinner=False)
def _cached_generate_rows(
    area: str,
    context: str,
    columns: tuple[str, ...],
    instruction: str,
    min_rows: int,
) -> list[dict[str, str]]:
    cols = ", ".join(columns)
    prompt = (
        f"{instruction}\n\n"
        f"Project reference:\n{context}\n\n"
        f"Return ONLY a JSON array with at least {min_rows} rows and EXACT keys: {cols}. "
        "All values must be short strings."
    )
    messages = [
        {"role": "system", "content": _PMP_MENTOR_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    raw = chat_completion(messages, temperature=0.3, max_tokens=1800)
    parsed = _extract_json_array(raw)

    clean_rows: list[dict[str, str]] = []
    for row in parsed:
        clean_rows.append({col: str(row.get(col, "")).strip() for col in columns})

    if clean_rows:
        return clean_rows

    # Safe fallback to editable blank rows if parsing fails.
    return [{col: "" for col in columns} for _ in range(min_rows)]


@st.cache_data(show_spinner=False)
def _cached_generate_text(area: str, context: str, instruction: str) -> str:
    messages = [
        {"role": "system", "content": _PMP_MENTOR_SYSTEM},
        {
            "role": "user",
            "content": f"{instruction}\n\nProject reference:\n{context}",
        },
    ]
    return chat_completion(messages, temperature=0.4, max_tokens=2200).strip()


def _table_markdown(title: str, rows: list[dict[str, Any]], columns: list[str]) -> str:
    header = f"## {title}\n\n"
    if not rows:
        return header + "_No rows provided._\n"

    table_lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        table_lines.append("| " + " | ".join(str(row.get(col, "")).strip() for col in columns) + " |")
    return header + "\n".join(table_lines) + "\n"


def _save_area_markdown(area: str, content: str) -> None:
    st.session_state.knowledge_area_data[area] = content


def _render_integration(context: str) -> None:
    area = "Integration Management"
    st.markdown("#### Final Project Charter")
    charter = st.session_state.get("charter_markdown", "")
    if not charter:
        charter = _cached_generate_text(
            area,
            context,
            "Synthesize a concise project charter summary in markdown with PMBOK structure.",
        )
    st.markdown(charter)
    _save_area_markdown(area, charter)


def _render_scope(context: str) -> None:
    area = "Scope Management"
    st.markdown("#### Work Breakdown Structure (3 Levels)")
    key = "ka_scope_wbs"
    if key not in st.session_state:
        st.session_state[key] = _cached_generate_text(
            area,
            context,
            (
                "Create a 3-level Work Breakdown Structure as a nested markdown list. "
                "Use level numbering format 1.0, 1.1, 1.1.1 and include 3-6 top-level work packages."
            ),
        )

    edited = st.text_area(
        "WBS (editable)",
        value=st.session_state[key],
        height=360,
        key="editor_scope_wbs",
    )
    st.session_state[key] = edited
    st.markdown(edited)
    _save_area_markdown(area, f"## Work Breakdown Structure\n\n{edited}\n")


def _render_schedule(context: str) -> None:
    area = "Schedule Management"
    cols = ("Milestone", "Estimated Duration", "Predecessors")
    key = "ka_schedule_rows"
    if key not in st.session_state:
        st.session_state[key] = _cached_generate_rows(
            area,
            context,
            cols,
            "Build a milestone list based on the charter and project goals.",
            min_rows=6,
        )

    st.markdown("#### Milestone List")
    edited = st.data_editor(
        st.session_state[key],
        num_rows="dynamic",
        width="stretch",
        key="editor_schedule_rows",
    )
    st.session_state[key] = edited
    _save_area_markdown(area, _table_markdown("Milestone List", edited, list(cols)))


def _render_cost(context: str) -> None:
    area = "Cost Management"
    cols = ("Category", "Estimated Cost", "Basis")
    key = "ka_cost_rows"
    if key not in st.session_state:
        generated = _cached_generate_rows(
            area,
            context,
            cols,
            (
                "Create a budget table with at least Labor, Materials, and Contingency categories. "
                "Add realistic placeholder costs aligned with project scale."
            ),
            min_rows=3,
        )
        # Ensure required categories exist even if the model omits one.
        existing = {str(row.get("Category", "")).strip().lower() for row in generated}
        for category in ["Labor", "Materials", "Contingency"]:
            if category.lower() not in existing:
                generated.append({"Category": category, "Estimated Cost": "", "Basis": ""})
        st.session_state[key] = generated

    st.markdown("#### Budget Table")
    edited = st.data_editor(
        st.session_state[key],
        num_rows="dynamic",
        width="stretch",
        key="editor_cost_rows",
    )
    st.session_state[key] = edited
    _save_area_markdown(area, _table_markdown("Budget Table", edited, list(cols)))


def _render_quality(context: str) -> None:
    area = "Quality Management"
    kpi_cols = ("Quality Metric", "Target", "Measurement Method", "Frequency")
    kpi_key = "ka_quality_kpi_rows"
    plan_key = "ka_quality_qc_plan"

    if kpi_key not in st.session_state:
        st.session_state[kpi_key] = _cached_generate_rows(
            area,
            context,
            kpi_cols,
            "Provide exactly 3 quality KPIs aligned with PMBOK quality management.",
            min_rows=3,
        )
    if plan_key not in st.session_state:
        st.session_state[plan_key] = _cached_generate_text(
            area,
            context,
            "Write a concise Quality Control plan (120-180 words) with control activities and acceptance gates.",
        )

    st.markdown("#### Quality Metrics (KPIs)")
    edited_kpis = st.data_editor(
        st.session_state[kpi_key],
        num_rows="dynamic",
        width="stretch",
        key="editor_quality_kpis",
    )
    st.session_state[kpi_key] = edited_kpis

    qc_plan = st.text_area(
        "Quality Control Plan",
        value=st.session_state[plan_key],
        height=180,
        key="editor_quality_plan",
    )
    st.session_state[plan_key] = qc_plan

    markdown = _table_markdown("Quality Metrics", edited_kpis, list(kpi_cols))
    markdown += "\n## Quality Control Plan\n\n" + qc_plan + "\n"
    _save_area_markdown(area, markdown)


def _render_resource(context: str) -> None:
    area = "Resource Management"
    cols = (
        "Role",
        "Initiation",
        "Planning",
        "Execution",
        "Monitoring & Controlling",
        "Closing",
    )
    key = "ka_resource_rows"
    if key not in st.session_state:
        st.session_state[key] = _cached_generate_rows(
            area,
            context,
            cols,
            "Create a staffing plan showing role allocation by project phase.",
            min_rows=5,
        )

    st.markdown("#### Staffing Plan")
    edited = st.data_editor(
        st.session_state[key],
        num_rows="dynamic",
        width="stretch",
        key="editor_resource_rows",
    )
    st.session_state[key] = edited
    _save_area_markdown(area, _table_markdown("Staffing Plan", edited, list(cols)))


def _render_communications(context: str) -> None:
    area = "Communications Management"
    cols = ("Audience", "Message", "Frequency", "Channel", "Owner")
    key = "ka_comm_rows"
    if key not in st.session_state:
        st.session_state[key] = _cached_generate_rows(
            area,
            context,
            cols,
            "Create a PMBOK communication matrix for primary stakeholders.",
            min_rows=6,
        )

    st.markdown("#### Communication Matrix")
    edited = st.data_editor(
        st.session_state[key],
        num_rows="dynamic",
        width="stretch",
        key="editor_comm_rows",
    )
    st.session_state[key] = edited
    _save_area_markdown(area, _table_markdown("Communication Matrix", edited, list(cols)))


def _render_risk(context: str) -> None:
    area = "Risk Management"
    cols = ("Risk Type", "Description", "Probability", "Impact", "Response Strategy")
    key = "ka_risk_rows"
    if key not in st.session_state:
        rows = _cached_generate_rows(
            area,
            context,
            cols,
            (
                "Identify 3 Threats (negative risks) and 2 Opportunities (positive risks). "
                "Use concise cause-event-impact language and practical response strategies. "
                "Probability and Impact must be Low/Medium/High."
            ),
            min_rows=5,
        )
        # Enforce at least 3 threats and 2 opportunities if model output is sparse.
        threats = [r for r in rows if str(r.get("Risk Type", "")).strip().lower() == "threat"]
        opportunities = [
            r for r in rows if str(r.get("Risk Type", "")).strip().lower() == "opportunity"
        ]
        while len(threats) < 3:
            row = {
                "Risk Type": "Threat",
                "Description": "",
                "Probability": "Medium",
                "Impact": "Medium",
                "Response Strategy": "",
            }
            rows.append(row)
            threats.append(row)
        while len(opportunities) < 2:
            row = {
                "Risk Type": "Opportunity",
                "Description": "",
                "Probability": "Medium",
                "Impact": "Medium",
                "Response Strategy": "",
            }
            rows.append(row)
            opportunities.append(row)
        st.session_state[key] = rows

    st.markdown("#### Risk Register (Threats and Opportunities)")
    edited = st.data_editor(
        st.session_state[key],
        num_rows="dynamic",
        width="stretch",
        key="editor_risk_rows",
    )
    st.session_state[key] = edited
    _save_area_markdown(area, _table_markdown("Risk Register", edited, list(cols)))


def _render_procurement(context: str) -> None:
    area = "Procurement Management"
    cols = ("Resource", "Decision", "Rationale", "Supplier/Team", "Contract Type")
    key = "ka_procurement_rows"
    if key not in st.session_state:
        st.session_state[key] = _cached_generate_rows(
            area,
            context,
            cols,
            (
                "Create a make-or-buy analysis for primary project resources. "
                "Decision must be either Make or Buy with PMBOK-oriented rationale."
            ),
            min_rows=5,
        )

    st.markdown("#### Make-or-Buy Analysis")
    edited = st.data_editor(
        st.session_state[key],
        num_rows="dynamic",
        width="stretch",
        key="editor_procurement_rows",
    )
    st.session_state[key] = edited
    _save_area_markdown(area, _table_markdown("Make-or-Buy Analysis", edited, list(cols)))


def _render_stakeholders(context: str) -> None:
    area = "Stakeholder Engagement"
    cols = ("Role", "Power", "Interest", "Grid Position", "Engagement Strategy")
    key = "ka_stakeholder_rows"
    if key not in st.session_state:
        st.session_state[key] = _cached_generate_rows(
            area,
            context,
            cols,
            (
                "Generate a power/interest grid with a specific engagement strategy for each role "
                "found in the charter context. Grid Position must be one of: Manage Closely, "
                "Keep Satisfied, Keep Informed, Monitor."
            ),
            min_rows=5,
        )

    st.markdown("#### Power/Interest Grid")
    edited = st.data_editor(
        st.session_state[key],
        num_rows="dynamic",
        width="stretch",
        key="editor_stakeholder_rows",
    )
    st.session_state[key] = edited
    _save_area_markdown(area, _table_markdown("Power/Interest Grid", edited, list(cols)))


def _render_sidebar_nav() -> None:
    with st.sidebar:
        st.divider()
        st.subheader("PMI Knowledge Areas")
        for area in PMI_KNOWLEDGE_AREAS:
            icon = _AREA_ICONS.get(area, "📋")
            is_active = area == st.session_state.current_knowledge_area
            if is_active:
                st.markdown(f"**→ {icon} {area}**")
            else:
                if st.button(
                    f"{icon} {area}",
                    key=f"nav_{area}",
                    width="stretch",
                ):
                    st.session_state.current_knowledge_area = area
                    st.rerun()

        if st.session_state.knowledge_area_data:
            st.divider()
            full_report = build_full_report(st.session_state)
            st.download_button(
                "Download Full Report (.docx)",
                data=markdown_to_docx_bytes(full_report),
                file_name="project_documentation.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                width="stretch",
            )
            st.download_button(
                "Download Full Report (.pdf)",
                data=markdown_to_pdf_bytes(full_report),
                file_name="project_documentation.pdf",
                mime="application/pdf",
                width="stretch",
            )


def _refine_entry(user_input: str, doc_type: str, area: str) -> str:
    project_context = get_project_context()[:1800]
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
                "You are a Senior PMP Mentor. "
                "Return only the refined statement in formal PMBOK language."
            ),
        },
        {"role": "user", "content": prompt},
    ]
    return chat_completion(messages, temperature=0.3)


def render_phase3() -> None:
    _render_sidebar_nav()

    area: str = st.session_state.current_knowledge_area
    icon = _AREA_ICONS.get(area, "📋")
    project_context = get_project_context()

    col_title, col_back = st.columns([4, 1])
    with col_title:
        st.subheader("Phase 3 - Knowledge Area Workspace")
        st.markdown(f"### {icon} {area}")
    with col_back:
        st.write("")
        if st.button("<- Charter", width="stretch"):
            st.session_state.phase = 2
            st.rerun()

    st.caption("Reference context uses both your original answers and AI-refined charter language.")
    st.divider()

    if area == "Integration Management":
        _render_integration(project_context)
    elif area == "Scope Management":
        _render_scope(project_context)
    elif area == "Schedule Management":
        _render_schedule(project_context)
    elif area == "Cost Management":
        _render_cost(project_context)
    elif area == "Quality Management":
        _render_quality(project_context)
    elif area == "Resource Management":
        _render_resource(project_context)
    elif area == "Communications Management":
        _render_communications(project_context)
    elif area == "Risk Management":
        _render_risk(project_context)
    elif area == "Procurement Management":
        _render_procurement(project_context)
    elif area == "Stakeholder Engagement":
        _render_stakeholders(project_context)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        content = st.session_state.knowledge_area_data.get(area, "")
        st.download_button(
            f"Download {area} (.docx)",
            data=markdown_to_docx_bytes(content),
            file_name=f"{area.lower().replace(' ', '_')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            width="stretch",
        )
    with col2:
        content = st.session_state.knowledge_area_data.get(area, "")
        st.download_button(
            f"Download {area} (.pdf)",
            data=markdown_to_pdf_bytes(content),
            file_name=f"{area.lower().replace(' ', '_')}.pdf",
            mime="application/pdf",
            width="stretch",
        )

    st.divider()
    with st.expander("Human-in-the-Loop (HITL) Refinement", expanded=False):
        st.markdown(
            "Add or refine entries in plain language. The AI rewrites them in formal PMP style "
            "using Cause-Event-Impact where applicable."
        )
        hitl_input: str = st.text_area(
            "Informal entry:",
            height=80,
            placeholder="Describe a risk, assumption, issue, or statement in plain language...",
            key=f"hitl_input_{area}",
        )
        doc_type: str = st.text_input(
            "Document type:",
            value=f"{area} Document",
            key=f"hitl_doctype_{area}",
        )

        if st.button("Polish with AI", type="primary", key=f"hitl_polish_{area}"):
            if hitl_input.strip():
                with st.spinner("Applying PMP refinement..."):
                    refined = _refine_entry(hitl_input.strip(), doc_type, area)
                st.session_state.hitl_refined[area] = refined
            else:
                st.warning("Please enter text to refine.")

        refined_result: str = st.session_state.hitl_refined.get(area, "")
        if refined_result:
            st.success("Refined statement:")
            st.markdown(f"> {refined_result}")

            if st.button("Append to Knowledge Area", key=f"hitl_append_{area}"):
                current_doc = st.session_state.knowledge_area_data.get(area, "")
                st.session_state.knowledge_area_data[area] = (
                    current_doc + f"\n\n---\n**Added via HITL Refinement**\n\n{refined_result}"
                )
                st.session_state.hitl_refined[area] = ""
                st.success("Entry appended.")
                st.rerun()
