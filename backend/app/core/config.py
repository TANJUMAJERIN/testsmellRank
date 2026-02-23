from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    mongodb_url: str
    database_name: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Email (Gmail SMTP — only used in local dev)
    mail_username: Optional[str] = None
    mail_password: Optional[str] = None
    mail_from: Optional[str] = None
    mail_from_name: str = "Test Smell Rank"

    # Resend HTTP API — used in production (Render blocks SMTP)
    resend_api_key: Optional[str] = None
    resend_from: str = "onboarding@resend.dev"

    # Public frontend URL (used to build survey links)
    frontend_url: str = "http://localhost:5173"

    class Config:
        env_file = ".env"

settings = Settings()
