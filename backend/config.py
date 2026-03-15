from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://pepe@localhost:5432/kcai"
    app_name: str = "Restaurant Intelligence Platform"

    model_config = {"env_file": ".env"}


settings = Settings()
