from pydantic_settings import BaseSettings
from typing import Optional
import secrets
import warnings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/collabers"
    SECRET_KEY: str = "secretkeyiwillchangelater" #change this later in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@collabers.com"
    
    FRONTEND_URL: str = "http://localhost:1712"
    
    # Set to True in production to enforce secure settings
    PRODUCTION: bool = False
    
    class Config:
        env_file = ".env"


settings = Settings()

# Security validation on startup
_INSECURE_SECRET_KEYS = {
    "secretkeyiwillchangelater",
    "changeme",
    "secret",
    "development",
}

if settings.SECRET_KEY in _INSECURE_SECRET_KEYS:
    if settings.PRODUCTION:
        raise RuntimeError(
            "CRITICAL: SECRET_KEY must be changed in production "
            "Generate a secure key"
        )
    else:
        warnings.warn(
            "WARNING: Using insecure SECRET_KEY. Set a secure SECRET_KEY in .env for production.",
            UserWarning
        )
