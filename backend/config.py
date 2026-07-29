#import Library
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load enivronment variable pulling values from a local .env file (see .env.example)
load_dotenv()


class Config:
    # Default Configuration

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-zeal-secret")

    # Database Configuration
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "student_hub")

    # connect to the MySQL database
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # SQLAlchemy's own change-tracking, not needed on top of the ORM

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-zeal-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "12"))
    )

