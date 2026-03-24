import os
from dotenv import load_dotenv

# Load .env file for local development (no-op if file doesn't exist)
load_dotenv()


def _get_secret(key: str, default: str = "") -> str:
    """Check Streamlit Cloud secrets first, then fall back to env/.env."""
    try:
        import streamlit as st
        value = st.secrets.get(key)
        if value:
            return str(value)
    except Exception:
        pass
    return os.getenv(key, default)


GOOGLE_API_KEY: str = _get_secret("GOOGLE_API_KEY")
GOOGLE_MODEL: str = _get_secret("GOOGLE_MODEL", "gemini-1.5-flash")
MAX_TOKENS: int = int(_get_secret("MAX_TOKENS", "2000"))
TEMPERATURE: float = float(_get_secret("TEMPERATURE", "0.7"))

APP_TITLE = "Conversational Project Initiator"
APP_SUBTITLE = "A PMP-Certified AI Governance Engine for 0→1 Project Discovery"
