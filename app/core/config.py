from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
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

    JWT_SECRET: str = "dev"
    JWT_REFRESH_SECRET: str = "dev_refresh"
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MIN: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 14

    # Aceptará [], lista JSON o CSV "a,b,c"
    CORS_ORIGINS: List[str] = Field(default_factory=list)

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

settings = Settings()
