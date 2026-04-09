from __future__ import annotations

import streamlit as st

try:
    from google import genai
    from google.genai import types

    _USE_NEW_GENAI = True
except Exception:  # pragma: no cover - compatibility fallback
    import google.generativeai as legacy_genai

    _USE_NEW_GENAI = False

from config.settings import get_google_api_key, GOOGLE_MODEL, MAX_TOKENS, TEMPERATURE


def _get_model(model_name: str):
    key = get_google_api_key()
    if not key:
        st.error(
            "⚠️ **Google API key not found.** "
            "Set `GOOGLE_API_KEY` in your Streamlit Cloud secrets (cloud) "
            "or copy `.env.example` to `.env` and set it there (local)."
        )
        st.stop()
    if _USE_NEW_GENAI:
        return genai.Client(api_key=key)
    legacy_genai.configure(api_key=key)
    return legacy_genai.GenerativeModel(model_name=model_name)


def _messages_to_prompt(messages: list[dict]) -> str:
    """Convert role-tagged chat messages to a single Gemini prompt string."""
    chunks: list[str] = []
    for message in messages:
        role = (message.get("role") or "user").upper()
        content = message.get("content") or ""
        chunks.append(f"[{role}]\n{content}")
    return "\n\n".join(chunks)


def _stop_with_llm_error(exc: Exception, model_name: str) -> None:
    """Surface Gemini errors in the UI instead of crashing the Streamlit app."""
    raw_message = str(exc).strip() or exc.__class__.__name__
    lower_message = raw_message.lower()

    hints: list[str] = []
    if any(token in lower_message for token in ("404", "not found", "unsupported", "unknown model")):
        hints.append(
            "Set `GOOGLE_MODEL` to a currently available Gemini Developer API model, "
            "such as `gemini-2.5-flash`."
        )
    if any(token in lower_message for token in ("403", "permission", "api key", "unauthorized")):
        hints.append(
            "Verify that your `GOOGLE_API_KEY` secret is valid for Google AI Studio "
            "and available in the current deployment."
        )

    hint_text = f"\n\n{hints[0]}" if hints else ""
    st.error(
        "⚠️ **Google Gemini request failed.**\n\n"
        f"Model: `{model_name}`\n\n"
        f"Details: {raw_message}"
        f"{hint_text}"
    )
    st.stop()


def chat_completion(
    messages: list[dict],
    model: str = GOOGLE_MODEL,
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
) -> str:
    """Blocking chat completion — returns the full response string."""
    prompt = _messages_to_prompt(messages)
    llm = _get_model(model)
    try:
        if _USE_NEW_GENAI:
            response = llm.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
        else:
            response = llm.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )
        return response.text or ""
    except Exception as exc:
        _stop_with_llm_error(exc, model)


def stream_completion(
    messages: list[dict],
    model: str = GOOGLE_MODEL,
    temperature: float = TEMPERATURE,
    max_tokens: int = MAX_TOKENS,
):
    """Streaming chat completion — yields text chunks as they arrive."""
    prompt = _messages_to_prompt(messages)
    llm = _get_model(model)
    try:
        if _USE_NEW_GENAI:
            stream = llm.models.generate_content_stream(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
        else:
            stream = llm.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
                stream=True,
            )
        for chunk in stream:
            delta = getattr(chunk, "text", None)
            if delta:
                yield delta
    except Exception as exc:
        _stop_with_llm_error(exc, model)
