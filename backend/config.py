import os
from datetime import timedelta
from dotenv import load_dotenv

# Pull values from a local .env file (see .env.example) into the process
# environment. In production these would be set as real environment
# variables instead of a checked-in file.
load_dotenv()


class Config:
    """Default configuration - used when the app runs normally (python app.py)."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # --- Database connection ---
    # Built from separate DB_* parts (rather than one DATABASE_URL) so the
    # same .env file maps 1:1 onto whatever MySQL instance is running,
    # whether that's local MySQL or an AWS RDS endpoint.
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "student_hub")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # SQLAlchemy's own change-tracking, not needed on top of the ORM

    # --- JWT auth ---
    # Must be a fixed value (not regenerated per process) or every restart of
    # the dev server would invalidate every previously-issued token.
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "12"))
    )

    # --- Outgoing email for bin collection reminders (see reminders.py) ---
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Irish International Student Hub")


class TestConfig(Config):
    """
    Configuration used by the Pytest suite (see tests/conftest.py).

    Points at an in-memory SQLite database instead of MySQL so the tests can
    run anywhere without a real database server, and disables anything that
    would make tests slower or flakier (e.g. real outgoing email).
    """

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-jwt-secret"
    SMTP_USERNAME = ""  # keeps reminders.py in its "print instead of send" branch
    SMTP_PASSWORD = ""
