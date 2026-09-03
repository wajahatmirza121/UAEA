"""Application settings — all values from env / .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://uaea:uaea@localhost:5432/uaea"
    database_url_sync: str = "postgresql+psycopg2://uaea:uaea@localhost:5432/uaea"

    # LLM (Groq — free fast inference, OpenAI-compatible API)
    llm_api_key: str = "gsk-REPLACE-ME"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.3-70b-versatile"

    # Embeddings
    embedding_provider: str = "openai"
    embedding_api_key: str = "sk-REPLACE-ME"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 384

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Rate limiting
    rate_limit_per_ip: str = "60/minute"
    rate_limit_per_session: str = "30/minute"

    # Admin
    admin_api_key: str = "uaea-admin-dev-key-change-in-production"

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
