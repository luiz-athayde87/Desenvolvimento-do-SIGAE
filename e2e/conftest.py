from __future__ import annotations

import threading

import pytest
from werkzeug.serving import make_server

from sigae import create_app


@pytest.fixture(scope="session")
def live_url():
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": ":memory:",
            "SECRET_KEY": "e2e-secret",
            "AUTH_REQUIRED": False,
            "DEMO_USER": "operador",
            "DEMO_PASSWORD": "senha-segura",
        }
    )
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        app.extensions["sigae_database"].close()
