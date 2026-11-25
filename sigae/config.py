"""Configuração do SIGAE por ambiente."""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path


class Config:
    ENV = os.getenv("SIGAE_ENV", "development")
    SECRET_KEY = os.getenv("SIGAE_SECRET_KEY", "dev-only-change-me")
    DATABASE = os.getenv("SIGAE_DATABASE", str(Path("instance") / "sigae.db"))
    AUTH_REQUIRED = os.getenv("SIGAE_AUTH_REQUIRED", "false").lower() == "true"
    DEMO_USER = os.getenv("SIGAE_DEMO_USER", "operador")
    DEMO_PASSWORD = os.getenv("SIGAE_DEMO_PASSWORD", "sigae-demo")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = ENV == "production"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    JSON_SORT_KEYS = False


class TestConfig(Config):
    TESTING = True
    AUTH_REQUIRED = False
    SECRET_KEY = "test-secret"
