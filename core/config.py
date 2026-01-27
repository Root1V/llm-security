import logging
from pydantic_settings import BaseSettings
from pydantic import Field

import secrets

class Settings(BaseSettings):
    SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32)
    )
    JWT_ALGORITHM: str = "HS256"
    
    TOKEN_CACHE_SIZE: int = 100
    TOKEN_TTL_SECONDS: int = 3600

    class Config:
        env_file = "settings.env"
        env_file_encoding = "utf-8"

settings = Settings()
