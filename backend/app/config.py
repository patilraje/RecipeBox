from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
LOCAL_ENV = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_ENV), str(LOCAL_ENV)),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    mealdb_base_url: str = "https://www.themealdb.com/api/json/v1/1"
    maximum_missing_default: int = 2
    # Google AI Studio (Gemini) — https://aistudio.google.com/apikey
    google_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2"




settings = Settings()
