from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://pepe@localhost:5432/kcai"
    app_name: str = "Restaurant Intelligence Platform"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    model_config = {"env_file": ".env"}


settings = Settings()
