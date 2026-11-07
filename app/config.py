import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./talenthub.db")
    secret_key: str = os.getenv("SECRET_KEY", "dev-only-secret-change-me-in-production")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    coordinator_username: str = os.getenv("COORDINATOR_USERNAME", "coordinator")
    coordinator_password: str = os.getenv("COORDINATOR_PASSWORD", "Coordinator@123")


settings = Settings()
