# 🏗️ Conversational Project Initiator
### A PMP-Certified AI Governance Engine for 0→1 Project Discovery

---

## 1. Executive Summary

The **Conversational Project Initiator** is an AI-powered strategic tool designed to bridge the gap between "messy" early-stage project ideas and rigorous, PMI-standard documentation. It replaces static, intimidating templates with a high-value, guided interview. By leveraging Natural Language Processing (NLP), the system validates project data in real-time, ensuring that project charters and risk registers are **SMART** (Specific, Measurable, Achievable, Relevant, Time-bound) before they are ever formalized.

---

## 2. Product Strategy & User Experience (The "Flow")

The application is structured into three progressive phases to ensure data integrity and user engagement:

### Phase 1 — The Strategic Interview (Onboarding)

**The Persona:** A Senior PMP Consultant with 20+ years of experience.

**The Method:** Instead of a long form, the AI asks 8 targeted questions sequentially:

| # | Section | Question Focus |
|---|---------|---------------|
| 1 | **Background** | Why is this project being undertaken? |
| 2 | **Goals** | What are 3 specific & measurable outcomes? |
| 3 | **Scope** | What is included (and explicitly excluded)? |
| 4 | **Stakeholders** | Who are the key players (Sponsor, PM, Client)? |
| 5 | **Milestones** | What are the critical dates? |
| 6 | **Budget** | What are the non-recurring and monthly expenses? |
| 7 | **Constraints/Assumptions** | What are the boundaries and "knowns"? |
| 8 | **Risks** | What are the high-level threats to success? |

### Phase 2 — Automated Synthesis

- **The Output:** The system aggregates the interview data into a professional Markdown Project Charter.
- **The Validation:** The AI flags vague inputs (e.g., *"make more money"*) and prompts for metrics before allowing the user to proceed.

### Phase 3 — The Knowledge Area Workspace (Context-Locked)

- Once the Charter is signed off, the project context is **"locked"** in session memory.
- Users can navigate through the **10 PMI Knowledge Areas** (e.g., Risk Management, Stakeholder Engagement).
- **AI Drafting:** The system pre-fills a Risk Register or Stakeholder Power/Interest Grid based on the Charter.
- **HITL (Human-in-the-Loop):** Users can edit casual entries, and the AI "polishes" them into professional PMP language.
  > *Example:* "Bad weather" → "Due to adverse weather conditions, construction may be delayed by 14 days, resulting in a 5% budget overrun."

---

## 3. Technical Implementation Stack

| Layer | Technology |
|-------|-----------|
| **Language** | Python 3.11+ |
| **Frontend / UI** | Streamlit |
| **Core Logic** | LangChain (state management & conversational memory) |
| **AI Engine** | Google Gemini (AI Studio API) |
| **Storage** | `st.session_state` (runtime) · Markdown / JSON (export) |
| **Security** | `python-dotenv` — API key masking via environment variables |

---

## 4. Technical Architecture

### A. Stateful Conversation Loop

The app tracks the `current_step` (1–8). Streamlit's stateless nature is addressed by a **Session State Manager** storing:

| Key | Type | Purpose |
|-----|------|---------|
| `user_answers` | `dict` | Raw input for each of the 8 sections |
| `ai_feedback` | `dict` | AI-refined versions of those answers |
| `chat_history` | `list` | Full conversation history per session |
| `is_charter_complete` | `bool` | Unlocks the Knowledge Area Workspace |
| `charter_markdown` | `str` | The generated project charter |
| `knowledge_area_data` | `dict` | Generated documents per knowledge area |
| `hitl_refined` | `dict` | Last HITL-polished statement per area |

### B. Prompt Engineering Strategy

**System Prompt**
> *"You are a PMP Mentor. Be professional, direct, and slightly critical to ensure high-quality documentation. Do not let the user provide one-word answers."*

**Validation Prompt**
> Each answer is scored 1–10 against SMART criteria. Scores below 6 are rejected with targeted follow-up questions referencing specific PMI/PMBOK concepts.

**Synthesis Prompt**
> *"Take the following 8 inputs and generate a professional Markdown Project Charter using the attached template structure."*

**Refinement Prompt (Cause-Event-Impact)**
> *"Convert the following user edit into a formal PMP-compliant statement using the 'Cause-Event-Impact' format."*

---

## 5. Project Structure

```
ConversationProjectInitiator/
├── app.py                      ← Streamlit entry point, phase router, sidebar
├── requirements.txt
├── .env.example                ← API key template (copy → .env)
├── .gitignore
├── .streamlit/
│   └── config.toml             ← Blue/white PMP-brand theme
├── config/
│   └── settings.py             ← dotenv loader, model/token configuration
├── core/
│   ├── session_manager.py      ← 8 interview questions + session-state defaults
│   ├── llm_client.py           ← Gemini wrapper (blocking + streaming)
│   └── prompts.py              ← All prompts: validation, synthesis, HITL, 10 KA templates
├── phases/
│   ├── phase1_interview.py     ← Sequential chat interview with live LLM validation
│   ├── phase2_synthesis.py     ← Streaming charter generation, manual edit, download
│   └── phase3_workspace.py     ← 10 PMI Knowledge Areas + HITL entry refinement
└── utils/
    ├── validators.py           ← SMART heuristics (specific / measurable / time-bound)
    └── exporters.py            ← Full-report .md & raw-data .json builders
```

---

## 6. Setup & Installation

### Prerequisites
- Python 3.11+
- A [Google AI Studio API key](https://aistudio.google.com/app/apikey)

### Steps

```bash
# 1. Clone or enter the project directory
cd ConversationProjectInitiator

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
cp .env.example .env
# Open .env and set:  GOOGLE_API_KEY=...

# 5. Launch the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 7. Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | ✅ | — | Your Google AI Studio key |
| `GOOGLE_MODEL` | ❌ | `gemini-2.5-flash` | Model name override |
| `MAX_TOKENS` | ❌ | `2000` | Maximum tokens per completion |
| `TEMPERATURE` | ❌ | `0.7` | Sampling temperature (0 = deterministic) |

---

## 8. Portfolio Value Proposition

This project explicitly demonstrates the following high-level competencies:

| Competency | Demonstration |
|-----------|--------------|
| **Product Thinking** | Solving the "Blank Page Problem" for project managers via a guided, conversational UX |
| **AI Implementation** | NLP-based data validation + generative AI for structured document output |
| **PM Expertise** | Deep integration of the 10 PMI Knowledge Areas into a modern tech stack |
| **Responsible AI** | Guardrails against hallucinations; Human-in-the-Loop oversight for critical project decisions |
| **Security** | API keys never logged or hardcoded; `.env` excluded from version control |

---

## 9. The 10 PMI Knowledge Areas

The Phase 3 workspace covers all knowledge areas defined in the PMBOK Guide:

1. Integration Management
2. Scope Management
3. Schedule Management
4. Cost Management
5. Quality Management
6. Resource Management
7. Communications Management
8. **Risk Management** ← Pre-filled Risk Register with Cause-Event-Impact analysis
9. Procurement Management
10. **Stakeholder Engagement** ← Pre-filled Power/Interest Grid and Engagement Matrix

---

## *Built with Python · Streamlit · Google Gemini*
