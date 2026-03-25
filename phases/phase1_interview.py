"""
phases/phase1_interview.py
──────────────────────────
Phase 1: The Strategic Interview
Conducts the 8-question sequential interview, validates each response via
the LLM using SMART/PMP criteria, and stores both raw and refined answers
in session state.
"""
from __future__ import annotations

import streamlit as st

from core.llm_client import chat_completion
from core.session_manager import INTERVIEW_QUESTIONS
from utils.validators import check_smart

# ── Helpers ───────────────────────────────────────────────────────────────────

_VALIDATOR_SYSTEM = (
    "You are a Senior PMP consultant. "
    "Review the user's answer and return a polished PMP-compliant rewrite only. "
    "Do not add commentary, labels, or markdown fences."
)

_COACH_SYSTEM = (
    "You are a Senior PMP mentor conducting a live interview. "
    "Be conversational, practical, and specific. "
    "Use prior user answers as context when helpful."
)


def _is_clarification_request(user_input: str) -> bool:
    text = user_input.strip().lower()
    return (
        "?" in text
        or text.startswith("i'm not sure")
        or text.startswith("im not sure")
        or text.startswith("can you")
        or text.startswith("what do you think")
        or text.startswith("help me")
    )


def _is_refinement_addition_request(user_input: str) -> bool:
    text = user_input.strip().lower()
    return (
        "add" in text
        or "include" in text
        or "also" in text
        or "expand" in text
        or "update" in text
    )


def _build_context_snapshot() -> str:
    """Build compact context from previously captured interview answers."""
    answers = st.session_state.get("user_answers", {})
    if not answers:
        return "No prior answers yet."

    lines: list[str] = []
    for q in INTERVIEW_QUESTIONS:
        qid = q["id"]
        if qid in answers:
            lines.append(f"- {q['title']}: {answers[qid]}")
    return "\n".join(lines) if lines else "No prior answers yet."


def _respond_to_clarification(question_data: dict, user_input: str) -> str:
    """Provide conversational guidance when the user asks a follow-up question."""
    prompt = (
        "The user asked a clarification question during an interview step.\n\n"
        f"Current interview section: {question_data['title']}\n"
        f"Current interview question: {question_data['question']}\n\n"
        "Prior interview context:\n"
        f"{_build_context_snapshot()}\n\n"
        f"User's follow-up: {user_input}\n\n"
        "Respond as a helpful PMP mentor in 3-6 sentences and end with a direct "
        "prompt for what they should answer next for this specific section."
    )
    response = chat_completion(
        [
            {"role": "system", "content": _COACH_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
    ).strip()
    return response or "Good question. Share your best draft for this section, and I will refine it."


def _append_to_refined_answer(question_data: dict, existing_refined: str, user_request: str) -> str:
    """Append user-requested additions while preserving the existing refined text."""
    prompt = (
        "You are updating a refined charter section.\n\n"
        "Task: Keep the existing refined answer intact, then append additional details "
        "that satisfy the user's request.\n"
        "Do not remove existing content.\n"
        "Do not rewrite from scratch.\n"
        "Return one combined polished answer.\n\n"
        f"Section: {question_data['title']}\n"
        f"Current refined answer:\n{existing_refined}\n\n"
        f"User requested addition:\n{user_request}"
    )
    response = chat_completion(
        [
            {"role": "system", "content": _COACH_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    ).strip()
    return response or (existing_refined + "\n\n" + user_request)


def _score_answer(user_response: str) -> int:
    """Heuristic 1-10 quality score focused on SMART signals and specificity."""
    words = len(user_response.split())
    smart = check_smart(user_response)

    score = 4
    score += smart["score"] * 2  # up to +6

    if words >= 25:
        score += 1
    if words < 10:
        score -= 3

    return max(1, min(10, score))


def _build_improvement_tip(question_data: dict, user_response: str, score: int) -> str:
    """Generate one concrete improvement suggestion when score < 10."""
    if score >= 10:
        return ""

    prompt = (
        "Provide one concise, practical suggestion (1-2 sentences) to improve this "
        "interview answer toward a 10/10 PMP-quality response.\n\n"
        f"Section: {question_data['title']}\n"
        f"Question: {question_data['question']}\n"
        f"Current answer: {user_response}\n\n"
        "Focus on what specific detail is missing (metric, date, owner, scope boundary, "
        "budget figure, or risk impact)."
    )
    tip = chat_completion(
        [
            {"role": "system", "content": _COACH_SYSTEM},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    ).strip()

    if not tip:
        tip = "Consider adding at least one metric and a target date to strengthen this section."
    return tip


def _validate_answer(question_data: dict, user_response: str) -> dict:
    """
    Ask the LLM for a polished rewrite and always accept the user's input.
    If the answer is short (<10 words), include a soft note for later charter detail.
    """
    prompt = (
        "Question:\n"
        f"{question_data['question']}\n\n"
        "Section:\n"
        f"{question_data['section']}\n\n"
        "User response:\n"
        f"{user_response}\n\n"
        "Rewrite this into concise, professional PMP language while preserving intent."
    )
    messages = [
        {"role": "system", "content": _VALIDATOR_SYSTEM},
        {"role": "user", "content": prompt},
    ]
    refined = chat_completion(messages, temperature=0.2).strip()
    if not refined:
        refined = user_response

    score = _score_answer(user_response)
    if len(user_response.split()) < 10:
        feedback_message = (
            "Got it. Note: This section is a bit thin; we might want to add more "
            "detail to the final Charter later."
        )
    else:
        feedback_message = "Response accepted and captured for synthesis."

    improvement_tip = _build_improvement_tip(question_data, user_response, score)

    return {
        "is_valid": True,
        "quality_score": score,
        "issues": [],
        "refined_version": refined,
        "feedback_message": feedback_message,
        "improvement_tip": improvement_tip,
    }


def _skip_question(q: dict) -> None:
    """Store a placeholder for development / demo purposes and advance."""
    placeholder = f"[Placeholder — {q['title']}]"
    st.session_state.user_answers[q["id"]] = placeholder
    st.session_state.ai_feedback[q["id"]] = placeholder
    st.session_state.current_step += 1
    st.rerun()


# ── Main render ───────────────────────────────────────────────────────────────

def render_phase1() -> None:
    step: int = st.session_state.current_step
    questions = INTERVIEW_QUESTIONS
    st.session_state.setdefault("phase1_last_prompt_step", -1)

    # Guard — all questions answered; hand off to Phase 2
    if step >= len(questions):
        st.session_state.phase = 2
        st.rerun()
        return

    q = questions[step]

    # ── Header ────────────────────────────────────────────────────────────────
    st.subheader("Phase 1 — Strategic Interview")
    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(f"**Section {step + 1} of {len(questions)}**")
        st.markdown(
            f"<h2 style='margin: 0.2rem 0 0.6rem 0; font-weight: 800;'>"
            f"Question {step + 1}: {q['title']}"
            "</h2>",
            unsafe_allow_html=True,
        )
    with col_b:
        st.progress((step) / len(questions))

    st.divider()

    # ── Chat history ──────────────────────────────────────────────────────────
    # Inject the current question as the latest assistant message if not already shown
    question_msg = (
        f"**{q['title']}**\n\n{q['question']}\n\n> 💡 *{q['hint']}*"
    )
    history = st.session_state.chat_history
    if st.session_state.phase1_last_prompt_step != step:
        history.append({"role": "assistant", "content": question_msg})
        st.session_state.phase1_last_prompt_step = step

    for msg in history:
        avatar = "🤵" if msg["role"] == "assistant" else "👤"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    st.divider()

    # ── Input form ────────────────────────────────────────────────────────────
    with st.form(key=f"q_form_{step}", clear_on_submit=True):
        user_input: str = st.text_area(
            label="Your response",
            placeholder="Provide a detailed, specific answer…",
            height=130,
            label_visibility="collapsed",
        )
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col2:
            submitted = st.form_submit_button(
                "Submit →", width="stretch", type="primary"
            )
        with col3:
            next_question = st.form_submit_button(
                "Next Question", width="stretch", type="secondary"
            )
        with col4:
            skipped = st.form_submit_button(
                "Skip ⏭", width="stretch", type="secondary"
            )

    if next_question:
        if q["id"] not in st.session_state.user_answers:
            st.warning("Submit at least one response before moving to the next question.")
            return
        st.session_state.current_step += 1
        st.rerun()

    if skipped:
        _skip_question(q)

    if submitted:
        if not user_input.strip():
            st.warning("Please provide a response before submitting.")
            return

        # Refinement-addition mode: keep original refined answer and append new details.
        if q["id"] in st.session_state.ai_feedback and _is_refinement_addition_request(user_input):
            history.append({"role": "user", "content": user_input.strip()})
            with st.spinner("Adding your requested details to the refined answer..."):
                combined = _append_to_refined_answer(
                    q,
                    st.session_state.ai_feedback[q["id"]],
                    user_input.strip(),
                )
            st.session_state.ai_feedback[q["id"]] = combined
            st.session_state[f"edited_refined_{q['id']}_{step}"] = combined
            history.append(
                {
                    "role": "assistant",
                    "content": (
                        "✅ Updated. I kept the original refined version and added your "
                        "requested details.\n\n"
                        f"**Revised refined version for your charter:**\n> {combined}"
                    ),
                }
            )
            st.rerun()

        # Conversational clarification mode — answer user question without
        # locking in this step as their final response.
        if _is_clarification_request(user_input):
            history.append({"role": "user", "content": user_input.strip()})
            with st.spinner("Thinking through your question..."):
                reply = _respond_to_clarification(q, user_input.strip())
            history.append({"role": "assistant", "content": reply})
            st.rerun()

        # Record user message in history
        history.append({"role": "user", "content": user_input.strip()})

        with st.spinner("Reviewing your response against PMI standards…"):
            validation = _validate_answer(q, user_input.strip())

        score: int = validation.get("quality_score", 7)
        feedback: str = validation.get("feedback_message", "")
        refined: str = validation.get("refined_version", user_input.strip())
        tip: str = validation.get("improvement_tip", "")

        tip_block = f"\n\n**How to make this a 10/10 answer:**\n{tip}" if tip and score < 10 else ""

        ai_msg = (
            f"✅ **Response Accepted** (Quality Score: **{score}/10**)\n\n"
            f"{feedback}\n\n"
            f"**Refined version for your charter:**\n> {refined}"
            f"{tip_block}"
        )
        st.session_state.user_answers[q["id"]] = user_input.strip()
        st.session_state.ai_feedback[q["id"]] = refined

        history.append({"role": "assistant", "content": ai_msg})
        st.rerun()

    # Persistent editor: user can refine the stored answer before moving on.
    if q["id"] in st.session_state.ai_feedback:
        st.divider()
        st.markdown("### ✏️ Review & Edit Refined Answer")
        default_refined = st.session_state.ai_feedback[q["id"]]
        editor_key = f"edited_refined_{q['id']}_{step}"
        if editor_key not in st.session_state:
            st.session_state[editor_key] = default_refined

        edited_refined = st.text_area(
            "Refined answer",
            key=editor_key,
            height=120,
            label_visibility="collapsed",
        )
        col_save, col_reset = st.columns(2)
        with col_save:
            if st.button("💾 Save Refined Answer", type="primary", width="stretch"):
                st.session_state.ai_feedback[q["id"]] = edited_refined.strip() or default_refined
                st.success("Refined answer updated.")
        with col_reset:
            if st.button("↺ Reset to Last Saved", width="stretch"):
                st.session_state[editor_key] = st.session_state.ai_feedback[q["id"]]
                st.rerun()
