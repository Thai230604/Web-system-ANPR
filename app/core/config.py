# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DB_HOST : str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD : str= os.getenv("DB_PASSWORD", "password")
    DB_NAME: str = os.getenv("DB_NAME", "fastapi-cicd")

    # Tạo connection string
    DATABASE_URL: str = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    # DATABASE_URL: str = "postgresql://postgres:123456@localhost:5432/anpr"
    SECRET_KEY: str= os.getenv("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"   # 👉 Cho phép bỏ qua các biến không khai báo
    )

settings = Settings()