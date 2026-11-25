"""Configuração do SIGAE por ambiente."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


class Config:
    ENV = os.getenv("SIGAE_ENV", "development").strip().lower()
    SECRET_KEY = os.getenv("SIGAE_SECRET_KEY", "dev-only-change-me")
    DATABASE = os.getenv("SIGAE_DATABASE", str(Path("instance") / "sigae.db"))
    AUTH_REQUIRED = _env_bool("SIGAE_AUTH_REQUIRED", False)
    DEMO_USER = os.getenv("SIGAE_DEMO_USER", "operador")
    DEMO_PASSWORD = os.getenv("SIGAE_DEMO_PASSWORD", "sigae-demo")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = ENV == "production"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=_env_int("SIGAE_SESSION_HOURS", 8))
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = _env_int("SIGAE_MAX_CONTENT_LENGTH", 16 * 1024 * 1024)

    @classmethod
    def validate(cls) -> None:
        if cls.ENV == "production" and cls.SECRET_KEY == "dev-only-change-me":
            raise RuntimeError("SIGAE_SECRET_KEY deve ser definido em produção.")
        if cls.ENV == "production" and cls.DEMO_PASSWORD == "sigae-demo":
            raise RuntimeError("SIGAE_DEMO_PASSWORD deve ser alterado em produção.")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


class TestConfig(Config):
    TESTING = True
    AUTH_REQUIRED = False
    SECRET_KEY = "test-secret"


CONFIGS = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestConfig,
}


def get_config(env: str | None = None) -> type[Config]:
    env = (env or os.getenv("SIGAE_ENV", "development")).strip().lower()
    return CONFIGS.get(env, Config)
