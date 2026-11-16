from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CitizenAssist AI"
    max_upload_mb: int = 20
    allowed_origins: list[str] = ["http://localhost:5173"]

    # AI provider selection: "groq" (default) or "gemini"
    ai_provider: str = "groq"

    # Groq AI Provider configuration (Milestone 6)
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_timeout_seconds: float = 30.0

    # Gemini AI Provider configuration (Milestone 5)
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    gemini_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
