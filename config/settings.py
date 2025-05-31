from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "pcos_assistant"
    secret_key: str = "your-secret-key-here-make-it-very-long-and-random-for-security"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    huggingface_api_token: str = ""
    frontend_url: str = "http://localhost:3000"
    
    class Config:
        env_file = ".env"

settings = Settings()