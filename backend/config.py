# backend/config.py
import os
from dotenv import load_dotenv


# Load Environment Variables
load_dotenv()


class Config:
    """
    Central configuration class for the SE Textile Unified Backend.
    Handles Flask, Database, AI integrations, File Management, and API keys.
    """

    # CORE SETTINGS
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "instance")
    os.makedirs(DATA_DIR, exist_ok=True)
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

    # DATABASE CONFIGURATION
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(DATA_DIR, 'se_textile.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # AI & API INTEGRATIONS
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    MAPMYINDIA_KEY = os.getenv("MAPMYINDIA_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # FILE MANAGEMENT
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    FAISS_INDEX_PATH = os.getenv(
        "FAISS_INDEX_PATH",
        os.path.join(DATA_DIR, "faiss", "index.faiss")
    )

    # Ensure necessary directories exist
    for path in [UPLOAD_FOLDER, os.path.dirname(FAISS_INDEX_PATH), DATA_DIR]:
        os.makedirs(path, exist_ok=True)

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_EXPIRATION_DAYS = int(os.getenv("JWT_EXPIRATION_DAYS", 7))
    JWT_ALGORITHM = "HS256"

    # Password Policy
    PASSWORD_MIN_LENGTH = int(os.getenv("PASSWORD_MIN_LENGTH", 8))
    PASSWORD_REQUIRE_LETTER = os.getenv("PASSWORD_REQUIRE_LETTER", "True").lower() == "true"
    PASSWORD_REQUIRE_NUMBER = os.getenv("PASSWORD_REQUIRE_NUMBER", "True").lower() == "true"

    # FILE LIMITS & FORMATS
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", 16)) * 1024 * 1024
    ALLOWED_EXTENSIONS = {"csv", "xlsx", "png", "jpg", "jpeg", "pdf"}

    # FLASK ENVIRONMENT SETTINGS
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() in ["1", "true", "yes"]
    TESTING = os.getenv("TESTING", "False").lower() in ["1", "true", "yes"]

    # SERVER SETTINGS
    PORT = int(os.getenv("PORT", 8000))
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    
    # IMAGE SERVING CONFIGURATION
    # Base URL for serving images (use production domain in production)
    API_BASE_URL = os.getenv("API_BASE_URL", f"http://127.0.0.1:{PORT}")
    
    # Image serving paths
    STATIC_IMAGE_PATH = "/uploads"  # URL path prefix for uploaded images
    DATASET_IMAGE_PATH = "/datasets"  # URL path prefix for dataset images
    
    # Fallback placeholder images
    PLACEHOLDER_IMAGE_SERVICE = os.getenv("PLACEHOLDER_IMAGE_SERVICE", "https://placehold.co")
    USE_PLACEHOLDER_IMAGES = os.getenv("USE_PLACEHOLDER_IMAGES", "True").lower() == "true"


# Export ready-to-use config instance
config = Config()
