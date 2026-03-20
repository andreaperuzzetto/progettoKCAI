from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://pepe@localhost:5432/kcai"
    app_name: str = "Restaurant Intelligence Platform"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    openai_api_key: str = ""
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id: str = ""           # legacy (starter plan)
    stripe_price_id_starter: str = ""   # 49€/mese
    stripe_price_id_pro: str = ""       # 99€/mese
    stripe_price_id_premium: str = ""   # 199€/mese
    # Email (SMTP)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()

