# backend/config.py
import os
from dotenv import load_dotenv

# ───────────────────────────────────────────────
# 🌍 Load Environment Variables
# ───────────────────────────────────────────────
load_dotenv()


class Config:
    """
    Central configuration class for the SE Textile Unified Backend.
    Handles Flask, Database, AI integrations, File Management, and API keys.
    """

    # ───────────────────────────────────────────────
    # CORE SETTINGS
    # ───────────────────────────────────────────────
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # ───────────────────────────────────────────────
    # DATABASE CONFIGURATION
    # ───────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'se_textile.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ───────────────────────────────────────────────
    # AI & API INTEGRATIONS
    # ───────────────────────────────────────────────
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    MAPMYINDIA_KEY = os.getenv("MAPMYINDIA_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Warn if missing critical AI keys
    if not GEMINI_API_KEY:
        print("⚠️  [Warning] GEMINI_API_KEY not set — AI text/caption features will be limited.")
    if not MAPMYINDIA_KEY:
        print("⚠️  [Warning] MAPMYINDIA_KEY not set — location features will be disabled.")

    # ───────────────────────────────────────────────
    # FILE MANAGEMENT
    # ───────────────────────────────────────────────
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    FAISS_INDEX_PATH = os.getenv(
        "FAISS_INDEX_PATH",
        os.path.join(DATA_DIR, "faiss", "index.faiss")
    )

    # Ensure necessary directories exist
    for path in [UPLOAD_FOLDER, os.path.dirname(FAISS_INDEX_PATH)]:
        os.makedirs(path, exist_ok=True)

    # ───────────────────────────────────────────────
    # FILE LIMITS & FORMATS
    # ───────────────────────────────────────────────
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", 16)) * 1024 * 1024
    ALLOWED_EXTENSIONS = {"csv", "xlsx", "png", "jpg", "jpeg", "pdf"}

    # ───────────────────────────────────────────────
    # FLASK ENVIRONMENT SETTINGS
    # ───────────────────────────────────────────────
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() in ["1", "true", "yes"]
    TESTING = os.getenv("TESTING", "False").lower() in ["1", "true", "yes"]

    # ───────────────────────────────────────────────
    # SERVER SETTINGS
    # ───────────────────────────────────────────────
    PORT = int(os.getenv("PORT", 8000))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")  # supports multiple origins via CORS(app, ...)


# Export ready-to-use config instance
config = Config()
