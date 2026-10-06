# =============================================================================
# CyberLearn — Configuration centrale (Pydantic Settings)
# Toutes les valeurs proviennent des variables d'environnement (.env)
# =============================================================================

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Application ──────────────────────────────────────────────────────────
    app_name: str = "CyberLearn — Jeu Intelligent"
    app_version: str = "1.0.0"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # ─── Base de données ──────────────────────────────────────────────────────
    database_url: str
    database_url_sync: str

    # ─── Redis ────────────────────────────────────────────────────────────────
    redis_url: str

    # ─── JWT ──────────────────────────────────────────────────────────────────
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # ─── CORS ─────────────────────────────────────────────────────────────────
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]

    # ─── Service IA ───────────────────────────────────────────────────────────
    ai_service_url: str = "http://ai:8001"

    # ─── Sécurité ─────────────────────────────────────────────────────────────
    bcrypt_rounds: int = 12
    rate_limit_auth_per_minute: int = 5
    rate_limit_submit_per_session: int = 10

    # ─── Âge minimum (PEGI 18+) ───────────────────────────────────────────────
    minimum_age: int = 18

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
