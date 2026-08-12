from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator
import json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    APP_NAME: str = "NutriAPI"
    APP_ENV: str = "local"
    APP_VERSION: str = "0.1.0"

    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "nutriapp"

    UPLOADS_DIR: str = "uploads"

    # Placeholders seguros para desarrollo local. En prod deben venir por entorno.
    JWT_SECRET: str = "local-dev-change-me"
    JWT_REFRESH_SECRET: str = "local-dev-refresh-change-me"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MIN: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 14

    # Aceptará [], lista JSON o CSV "a,b,c"
    CORS_ORIGINS: List[str] = Field(default_factory=list)
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-service-account.json"
    NOTIFY_BEFORE_MINUTES: int = 30

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://127.0.0.1:8000/google/oauth/callback"
    GOOGLE_SCOPES: list[str] = ["https://www.googleapis.com/auth/calendar"]
    APP_OAUTH_SUCCESS_REDIRECT: str = "vitta://oauth/success"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            # Si viene como JSON: ["a","b"]
            if s.startswith("["):
                try:
                    return json.loads(s)
                except Exception:
                    # si falla, sigue con CSV
                    pass
            # CSV: a,b,c
            return [i.strip() for i in s.split(",") if i.strip()]
        return v

    @model_validator(mode="after")
    def validate_security_baseline(self):
        app_env = self.APP_ENV.lower()
        if app_env in ("prod", "production", "staging"):
            placeholder_secrets = {
                "local-dev-change-me",
                "local-dev-refresh-change-me",
                "change_me",
                "change_me_too",
                "dev",
                "dev_refresh",
            }
            if self.JWT_SECRET in placeholder_secrets:
                raise ValueError("JWT_SECRET must be set from environment outside local dev.")
            if self.JWT_REFRESH_SECRET in placeholder_secrets:
                raise ValueError(
                    "JWT_REFRESH_SECRET must be set from environment outside local dev."
                )

        has_google_id = bool(self.GOOGLE_CLIENT_ID.strip())
        has_google_secret = bool(self.GOOGLE_CLIENT_SECRET.strip())
        if has_google_id != has_google_secret:
            raise ValueError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set together."
            )

        return self

settings = Settings()
