"""Entrada de linha de comando para execução local e de produção."""

from __future__ import annotations

import argparse
import os

from . import create_app
from .config import get_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor do simulador SIGAE")
    parser.add_argument("--host", default=os.getenv("SIGAE_HOST", "127.0.0.1"))
    parser.add_argument("--port", default=int(os.getenv("SIGAE_PORT", "5000")), type=int)
    parser.add_argument(
        "--dev", action="store_true", help="Usa o servidor de desenvolvimento Flask"
    )
    parser.add_argument("--threads", default=8, type=int, help="Threads do waitress")
    parser.add_argument(
        "--env", default=os.getenv("SIGAE_ENV", "development"), help="Ambiente de configuração"
    )
    args = parser.parse_args()

    if not (1 <= args.port <= 65535):
        parser.error("--port deve estar entre 1 e 65535")
    if args.threads < 1:
        parser.error("--threads deve ser maior que zero")

    app = create_app(get_config(args.env))
    if args.dev:
        app.run(host=args.host, port=args.port, debug=True)
    else:
        from waitress import serve

        serve(app, host=args.host, port=args.port, threads=args.threads)


if __name__ == "__main__":
    main()
