"""
Configuration settings for ResumeMatch AI.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if available
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

HOST: str = os.getenv("HOST", "0.0.0.0")
PORT: int = int(os.getenv("PORT", "8000"))
DATABASE_PATH: str = os.getenv("DATABASE_PATH", str(BASE_DIR / "app_data.db"))
MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

# AI / LLM Configuration
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "").strip()
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

# Supabase Cloud Database Configuration
SUPABASE_URL: str = os.getenv("SUPABASE_URL", os.getenv("PROJECT_URL", "")).strip()
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", os.getenv("PUBLISHABLE_KEY", "")).strip()

def is_openai_available() -> bool:
    return bool(OPENAI_API_KEY and len(OPENAI_API_KEY) > 10)

def is_gemini_available() -> bool:
    return bool(GEMINI_API_KEY and len(GEMINI_API_KEY) > 10)

def is_llm_available() -> bool:
    return is_openai_available() or is_gemini_available()

def is_supabase_available() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY and len(SUPABASE_URL) > 10 and len(SUPABASE_KEY) > 10)
