import os
from dotenv import load_dotenv

# env laden
try:
    load_dotenv()
except Exception:
    pass

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-5-2025-08-07")

TIMEOUT = int(os.getenv("TIMEOUT", "180"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "0"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4000"))

assert OPENAI_API_KEY, "OPENAI_API_KEY in .env setzen"
