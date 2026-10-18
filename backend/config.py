"""Application configuration, read from environment variables (.env supported)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _split(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'shop.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Gemini (key stays on the backend only; never returned by any endpoint)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_TIMEOUT_SECONDS = int(os.getenv("GEMINI_TIMEOUT_SECONDS", "20"))

    # CORS: only the configured frontend origins are allowed
    CORS_ORIGINS = _split(
        os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    )

    # Request-size limit (bytes)
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(64 * 1024)))

    # Input limits
    MAX_QUERY_LENGTH = 500
    MAX_CHAT_LENGTH = 1000
    MAX_REVIEW_TEXT_LENGTH = 8000
    MAX_CART_QUANTITY = 10

    # Demo user (no real authentication in this app)
    DEMO_USER_ID = "demo-user"

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    GEMINI_API_KEY = ""
