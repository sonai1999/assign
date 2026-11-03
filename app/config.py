import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Enterprise Inventory Orchestrator"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./enterprise_inventory.db")
    API_KEY_SECRET: str = os.getenv(
        "API_KEY_SECRET", "super-secret-enterprise-key")

    class Config:
        env_file = ".env"


settings = Settings()
