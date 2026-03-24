import streamlit as st

# ── Interview question bank ──────────────────────────────────────────────────

INTERVIEW_QUESTIONS: list[dict] = [
    {
        "id": "background",
        "title": "Project Background & Justification",
        "question": (
            "Let's start by establishing strategic context. **Why is this project being undertaken?** "
            "What business problem, opportunity, or strategic imperative is driving it? "
            "Please be specific — avoid generic statements like 'to improve efficiency.'"
        ),
        "hint": "Consider: What gap exists today? What happens if this project is NOT executed?",
        "section": "Background & Justification",
    },
    {
        "id": "goals",
        "title": "Project Goals & Objectives",
        "question": (
            "What are **3 specific and measurable outcomes** you expect this project to deliver? "
            "Each goal must include a metric, a target value, and a deadline — "
            "these are the SMART criteria your charter will be evaluated against."
        ),
        "hint": (
            "Example: 'Reduce customer onboarding time from 5 days to 2 days by Q3 2026, "
            "improving CSAT scores by 15%.'"
        ),
        "section": "Goals & Objectives",
    },
    {
        "id": "scope",
        "title": "Scope Definition",
        "question": (
            "Define the project scope precisely. What is **explicitly included** in this engagement? "
            "Equally important — what is **explicitly excluded**? "
            "A crisp scope statement is your primary defence against scope creep."
        ),
        "hint": "Use 'In Scope:' and 'Out of Scope:' sections in your response.",
        "section": "Scope Management",
    },
    {
        "id": "stakeholders",
        "title": "Key Stakeholders",
        "question": (
            "Identify the **key stakeholders** for this project. "
            "Who holds budget authority (Sponsor)? Who is the Project Manager? "
            "Who are the primary clients or end-users? Any other critical parties whose buy-in is required?"
        ),
        "hint": "Format: Name / Role — their primary interest or expectation from this project.",
        "section": "Stakeholder Management",
    },
    {
        "id": "milestones",
        "title": "Critical Milestones & Timeline",
        "question": (
            "What are the **critical milestones** for this project? "
            "List each major deliverable with its target completion date. "
            "Include the project start date and the final go-live or completion date."
        ),
        "hint": (
            "Example: 'M1: Requirements sign-off — April 15 | "
            "M2: UAT complete — June 30 | M3: Go-live — August 1'"
        ),
        "section": "Schedule Management",
    },
    {
        "id": "budget",
        "title": "Budget Overview",
        "question": (
            "Provide a high-level budget breakdown. "
            "What are the **non-recurring costs** (one-time: equipment, licenses, implementation) "
            "and the **recurring costs** (ongoing: subscriptions, staff, maintenance)? "
            "Include a total project budget figure if known."
        ),
        "hint": "Currency and ballpark figures are acceptable at this discovery stage.",
        "section": "Cost Management",
    },
    {
        "id": "constraints",
        "title": "Constraints & Assumptions",
        "question": (
            "Every project operates within hard boundaries. "
            "What are the key **constraints** (non-negotiable limits: regulatory, technical, resource, time) "
            "and **assumptions** (things believed to be true but not yet confirmed)?"
        ),
        "hint": (
            "Constraints narrow your options. "
            "Assumptions, if proven wrong, immediately become risks."
        ),
        "section": "Integration Management",
    },
    {
        "id": "risks",
        "title": "High-Level Risk Assessment",
        "question": (
            "What are the **3–5 biggest threats** to this project's success? "
            "For each risk describe: (1) the risk event, (2) its likelihood (Low / Medium / High), "
            "and (3) its potential impact on scope, schedule, or budget."
        ),
        "hint": (
            "Cast a wide net — think across categories: "
            "technical, resource/staffing, external/market, regulatory, and schedule."
        ),
        "section": "Risk Management",
    },
]

# ── Session-state bootstrap ──────────────────────────────────────────────────

def init_session_state() -> None:
    """Initialise all session-state keys with safe defaults (idempotent)."""
    defaults: dict = {
        "phase": 1,
        "current_step": 0,
        "user_answers": {},        # raw user text per question id
        "ai_feedback": {},         # AI-refined version per question id
        "chat_history": [],        # list of {"role": str, "content": str}
        "is_charter_complete": False,
        "charter_markdown": "",
        "current_knowledge_area": "Risk Management",
        "knowledge_area_data": {},  # {area: generated_markdown}
        "hitl_refined": {},         # {area: last refined statement}
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
