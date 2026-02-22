from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_url: str
    database_name: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Developer survey settings
    gmail_user: str = ""
    gmail_app_password: str = ""
    frontend_url: str = "http://localhost:5173"
    survey_response_threshold: float = 0.5

    class Config:
        env_file = ".env"

settings = Settings()
