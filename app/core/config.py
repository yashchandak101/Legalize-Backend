import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def _fix_db_url(url):
    if url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


_db_url = os.getenv("DATABASE_URL")
if not _db_url:
    # Fallback to SQLite for development if DATABASE_URL is not set
    print("WARNING: DATABASE_URL not set, using SQLite for development")
    _db_url = "sqlite:///legalize_dev.db"

# Additional PostgreSQL configuration for Render
if _db_url and _db_url.startswith("postgresql://"):
    # PostgreSQL-specific settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
    }
else:
    # SQLite settings for development - remove pool options
    SQLALCHEMY_ENGINE_OPTIONS = {}


class Config:
    """Flask configuration for Legalize project"""

    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))

    DATABASE_URL = _fix_db_url(_db_url)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = SQLALCHEMY_ENGINE_OPTIONS

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_hex(32))
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MIN", 30))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 7))
    )

    PROPAGATE_EXCEPTIONS = True
    JSON_SORT_KEYS = False


class TestingConfig(Config):
    TESTING = True
    DATABASE_URL = _fix_db_url(_db_url)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = SQLALCHEMY_ENGINE_OPTIONS