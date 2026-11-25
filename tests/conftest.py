from __future__ import annotations

import pytest

from sigae import create_app


@pytest.fixture()
def app():
    application = create_app(
        {
            "TESTING": True,
            "DATABASE": ":memory:",
            "SECRET_KEY": "test-secret",
            "AUTH_REQUIRED": False,
            "DEMO_USER": "operador",
            "DEMO_PASSWORD": "senha-segura",
        }
    )
    yield application
    application.extensions["sigae_database"].close()


@pytest.fixture()
def client(app):
    return app.test_client()
