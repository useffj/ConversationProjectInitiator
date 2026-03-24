import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL: str = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "2000"))
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))

APP_TITLE = "Conversational Project Initiator"
APP_SUBTITLE = "A PMP-Certified AI Governance Engine for 0→1 Project Discovery"
