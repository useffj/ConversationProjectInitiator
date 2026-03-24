# ─────────────────────────────────────────────────────────────────────────────
# core/prompts.py  — All LLM prompt templates for the Conversational Project
#                    Initiator.  Keep each prompt versioned and documented.
# ─────────────────────────────────────────────────────────────────────────────

# ── Phase 1 ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are a Senior PMP Consultant and Strategic Advisor with 20+ years of experience \
leading complex projects across technology, finance, and infrastructure sectors. \
You hold a current Project Management Professional (PMP) certification and are deeply \
fluent in the PMBOK Guide (7th Edition).

Your role is to conduct a structured project discovery interview. Your demeanor is:
- Professional and authoritative — you do not accept vague or incomplete answers.
- Constructive rather than harsh — guide the user toward better answers, not just reject theirs.
- Specific in your feedback — reference PMI standards, SMART criteria, or PMBOK concepts when critiquing.
- Efficient — keep responses focused and actionable.

RULES YOU MUST FOLLOW:
1. Never accept one-word or single-sentence answers for substantive questions.
2. Validate that answers meet SMART criteria where applicable (Goals, Milestones, Budget).
3. If an answer is vague, explain WHY it is insufficient and ask one targeted follow-up question.
4. If an answer is acceptable, briefly confirm it and provide a polished, refined version.
5. Do NOT fabricate specific data or invent details the user has not provided.\
"""

VALIDATION_PROMPT_TEMPLATE = """\
You are a strict PMP documentation reviewer assessing an interview response for quality and completeness.

QUESTION ASKED:
{question}

PMBOK SECTION: {section}

USER'S RESPONSE:
{user_response}

Evaluate this response against PMP standards and SMART criteria where applicable.

Respond in EXACTLY this JSON format (no markdown fences, no extra keys):
{{
  "is_valid": true,
  "quality_score": 8,
  "issues": [],
  "refined_version": "A polished, PMP-compliant restatement. Preserve the user's intent — elevate the language.",
  "feedback_message": "Your message to the user. If valid (score ≥ 6), confirm what was strong. If invalid, include at least one specific follow-up question referencing a PMI concept."
}}

SCORING GUIDE:
1–3  = Wholly insufficient (too vague, missing key data, one-liners)
4–5  = Partial — missing measurability, timeline, or specificity; is_valid must be false
6–7  = Acceptable — meets minimum PMI standards; is_valid = true
8–9  = Strong — SMART, well-structured, professional language
10   = Exemplary — could go directly into an executive charter\
"""

# ── Phase 2 ──────────────────────────────────────────────────────────────────

SYNTHESIS_PROMPT = """\
You are generating a formal Project Charter in Markdown format for executive presentation.

Using the validated project interview data below, produce a comprehensive Project Charter \
that adheres to PMI PMBOK standards. Be formal, precise, and thorough. \
Infer the Project Title from the background and goals; do NOT label it as 'Unknown'.

PROJECT DATA:
{project_data}

Generate the charter using EXACTLY this structure — do not omit any section:

# PROJECT CHARTER

## {project_title_placeholder}

---

## 1. Project Overview
| Field | Details |
|-------|---------|
| **Document Version** | 1.0 |
| **Status** | Draft |
| **Date Prepared** | {date} |
| **Prepared By** | Conversational Project Initiator |

---

## 2. Business Case & Project Justification
[2–3 sentences synthesising the background into a formal business case, \
referencing the strategic opportunity or problem this project addresses.]

---

## 3. Project Objectives (SMART)
[Numbered list of 3 SMART objectives. Each must state: metric, baseline, target, deadline.]

---

## 4. Scope Statement

### In Scope
[Bulleted list of explicit inclusions]

### Out of Scope
[Bulleted list of explicit exclusions — be specific to prevent scope creep]

---

## 5. Stakeholder Register (Summary)
| ID | Role | Name / Organisation | Primary Interest | Engagement Level |
|----|------|---------------------|-----------------|-----------------|
[One row per stakeholder. Engagement level: High / Medium / Low]

---

## 6. High-Level Milestone Schedule
| # | Milestone | Target Date | Key Deliverable |
|---|-----------|-------------|----------------|
[One row per milestone]

---

## 7. Budget Summary
| Category | Type | Estimated Cost |
|----------|------|----------------|
[Itemised rows]
| | **Total Estimated Budget** | **[Total]** |

---

## 8. Constraints & Assumptions

### Constraints
[Bulleted list — hard limits the project must operate within]

### Assumptions
[Bulleted list — things believed true; if wrong, they become risks]

---

## 9. High-Level Risk Summary
| Risk ID | Risk Description | Likelihood | Impact | Category |
|---------|-----------------|------------|--------|----------|
[One row per risk — use Cause-Event-Impact phrasing in the description]

---

## 10. Charter Authorization
| Role | Name | Signature | Date |
|------|------|-----------|------|
| Project Sponsor | [From data] | ___________________ | __________ |
| Project Manager | [From data] | ___________________ | __________ |
| Reviewed By | ___________________ | ___________________ | __________ |

---
*Generated by the Conversational Project Initiator — A PMP-Certified AI Governance Engine.*\
"""

# ── Phase 3 — Knowledge Area document generators ─────────────────────────────

RISK_REGISTER_PROMPT = """\
You are a PMP Risk Management specialist. Generate a comprehensive Risk Register \
in formal Markdown format.

PROJECT CHARTER SUMMARY:
{charter_summary}

RISKS IDENTIFIED IN INTERVIEW:
{risks_data}

Produce a Risk Register with the following columns:
- **Risk ID** (R-001, R-002 …)
- **Risk Description** (Cause-Event-Impact format: "Due to [cause], [event] may occur, \
resulting in [impact].")
- **Category** (Technical / Schedule / Resource / External / Regulatory / Financial)
- **Probability** (Low / Medium / High)
- **Impact** (Low / Medium / High)
- **Risk Score** (1–9: Low=1, Medium=2, High=3; Probability × Impact)
- **Risk Owner** (infer from stakeholder data or mark TBD)
- **Mitigation Strategy** (proactive action to reduce probability or impact)
- **Contingency Plan** (reactive action if risk materialises)
- **Status** (Open)

Requirements:
- Expand on the user's stated risks using Cause-Event-Impact format.
- Identify at least 4 additional risks implied by the project context.
- Generate a minimum of 8 risks total.
- Sort by Risk Score descending (highest first).
- Add a brief Risk Management Approach section before the table.\
"""

STAKEHOLDER_GRID_PROMPT = """\
You are a PMP Stakeholder Engagement specialist. Generate a Stakeholder Analysis \
and Engagement Plan in formal Markdown format.

PROJECT CHARTER SUMMARY:
{charter_summary}

STAKEHOLDERS FROM INTERVIEW:
{stakeholders_data}

Generate the following sections:

### 1. Power / Interest Grid
Classify each stakeholder into one of four quadrants:
- **Manage Closely** (High Power, High Interest)
- **Keep Satisfied** (High Power, Low Interest)
- **Keep Informed** (Low Power, High Interest)
- **Monitor** (Low Power, Low Interest)

### 2. Stakeholder Register
| ID | Name / Role | Power (H/M/L) | Interest (H/M/L) | Quadrant | Engagement Strategy | Communication Frequency | Preferred Channel |
|----|-------------|---------------|-----------------|----------|--------------------|-----------------------|------------------|

### 3. Tailored Engagement Strategies
For each "Manage Closely" stakeholder, write a 2–3 sentence engagement plan \
referencing PMI's Stakeholder Engagement Assessment Matrix.

### 4. Communication Cadence Summary
A brief schedule of standing meetings, status reports, and escalation paths.\
"""

HITL_REFINEMENT_PROMPT = """\
You are a PMP documentation specialist applying the Cause-Event-Impact framework.

CONTEXT: This entry is for a {document_type} in the {knowledge_area} knowledge area.
PROJECT CONTEXT: {project_context}

ORIGINAL (INFORMAL) ENTRY:
{user_input}

Convert this into a formal, PMP-compliant statement. \
Apply the Cause-Event-Impact format where applicable:
"Due to [Cause], [Event] may occur, resulting in [Impact] with [quantified consequence]."

Return ONLY the refined statement — no explanation, no preamble, no markdown fences.\
"""

# Knowledge-area-specific generation prompts (used as templates)
KNOWLEDGE_AREA_PROMPTS: dict[str, str] = {
    "Integration Management": (
        "Generate a Change Management Plan and Project Integration approach for the following project. "
        "Include: (1) Integrated Change Control process with a change request workflow, "
        "(2) Configuration Management approach, (3) Lessons Learned strategy, "
        "(4) Project closure criteria.\n\nPROJECT CHARTER:\n{charter_summary}"
    ),
    "Scope Management": (
        "Generate a Scope Management Plan and Work Breakdown Structure (WBS) for the following project. "
        "Include: (1) Scope planning approach, (2) WBS as a numbered outline to Level 3, "
        "(3) WBS Dictionary summary table, (4) Scope change control process.\n\n"
        "PROJECT CHARTER:\n{charter_summary}"
    ),
    "Schedule Management": (
        "Generate a Schedule Management Plan for the following project. "
        "Include: (1) Scheduling methodology and tools, "
        "(2) Milestone table with predecessor dependencies, "
        "(3) Schedule compression techniques (fast-tracking / crashing thresholds), "
        "(4) Schedule baseline and variance thresholds.\n\n"
        "PROJECT CHARTER:\n{charter_summary}"
    ),
    "Cost Management": (
        "Generate a Cost Management Plan for the following project. "
        "Include: (1) Cost estimating approach, (2) Cost baseline breakdown by phase, "
        "(3) Contingency reserve analysis (use 10–15% rule with justification), "
        "(4) Management reserve policy, (5) Earned Value Management (EVM) thresholds (CPI/SPI).\n\n"
        "PROJECT CHARTER:\n{charter_summary}"
    ),
    "Quality Management": (
        "Generate a Quality Management Plan for the following project. "
        "Include: (1) Quality standards and compliance requirements, "
        "(2) Quality metrics and acceptance criteria table, "
        "(3) Quality Assurance activities and schedule, "
        "(4) Quality Control checklist, (5) Continuous improvement approach.\n\n"
        "PROJECT CHARTER:\n{charter_summary}"
    ),
    "Resource Management": (
        "Generate a Resource Management Plan for the following project. "
        "Include: (1) RACI Matrix for key deliverables, "
        "(2) Resource histogram description by project phase, "
        "(3) Team development approach (Tuckman model), "
        "(4) Recognition and reward strategy, (5) Virtual team considerations.\n\n"
        "PROJECT CHARTER:\n{charter_summary}"
    ),
    "Communications Management": (
        "Generate a Communications Management Plan for the following project. "
        "Include: (1) Stakeholder communication matrix "
        "(who receives what information, when, via which channel, in what format), "
        "(2) Meeting cadence and agenda structure, "
        "(3) Escalation path, (4) Information distribution methods.\n\n"
        "PROJECT CHARTER:\n{charter_summary}"
    ),
    "Risk Management": "",   # handled by RISK_REGISTER_PROMPT
    "Procurement Management": (
        "Generate a Procurement Management Plan for the following project. "
        "Include: (1) Make-or-buy analysis for key deliverables, "
        "(2) Vendor selection criteria and weighting, "
        "(3) Contract type recommendations with rationale (FFP / T&M / Cost-Plus), "
        "(4) Solicitation process and timeline, (5) Contract closure approach.\n\n"
        "PROJECT CHARTER:\n{charter_summary}"
    ),
    "Stakeholder Engagement": "",  # handled by STAKEHOLDER_GRID_PROMPT
}
