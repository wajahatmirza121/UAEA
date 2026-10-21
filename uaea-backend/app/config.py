"""Application settings — all values from env / .env file."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://uaea:uaea@localhost:5432/uaea"
    database_url_sync: str = "postgresql+psycopg2://uaea:uaea@localhost:5432/uaea"

    # LLM (Groq — free fast inference, OpenAI-compatible API)
    llm_api_key: str = "gsk-REPLACE-ME"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    # llama-3.3-70b-versatile was shut down by Groq on 16 Aug 2026; Groq's
    # recommended replacement is openai/gpt-oss-120b.
    llm_model: str = "openai/gpt-oss-120b"
    # Tried in order if the main model is decommissioned / rate-limited.
    llm_fallback_models: str = "qwen/qwen3.8-27b,openai/gpt-oss-20b"
    # gpt-oss models are reasoning models; "low" keeps replies fast.
    llm_reasoning_effort: str = "low"
    llm_temperature: float = 0.2
    llm_timeout_seconds: float = 30.0

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

    # ── OTP / WhatsApp ────────────────────────────────────────────────────
    # Every demo student record carries this WhatsApp number.
    demo_student_phone: str = "+923333797617"
    otp_length: int = 6
    otp_ttl_seconds: int = 300            # code valid for 5 minutes
    otp_max_attempts: int = 5
    otp_resend_cooldown_seconds: int = 30
    otp_max_per_hour: int = 6             # per roll number
    otp_access_minutes: int = 15          # how long a verified session can see that record
    otp_secret: str = "change-me-otp-pepper"
    # Show the code inside the chat reply (ONLY for local demos without WhatsApp).
    otp_dev_echo: bool = False

    # whatsapp_provider: console | twilio | meta
    whatsapp_provider: str = "console"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"   # Twilio sandbox number
    meta_wa_token: str = ""
    meta_wa_phone_number_id: str = ""
    meta_wa_api_version: str = "v21.0"
    meta_wa_template: str = ""            # approved AUTHENTICATION template name; empty = plain text
    meta_wa_template_lang: str = "en_US"

    # Date the assistant treats as "today" (blank = real date). Handy for demos.
    today_override: str = ""
    timezone: str = "Asia/Karachi"

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
