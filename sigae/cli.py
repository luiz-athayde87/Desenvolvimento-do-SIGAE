"""Entrada de linha de comando para execução local e de produção."""

from __future__ import annotations

import argparse

from waitress import serve

from . import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor do simulador SIGAE")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=5000, type=int)
    parser.add_argument(
        "--dev", action="store_true", help="Usa o servidor de desenvolvimento Flask"
    )
    args = parser.parse_args()
    app = create_app()
    if args.dev:
        app.run(host=args.host, port=args.port, debug=True)
    else:
        serve(app, host=args.host, port=args.port, threads=8)


if __name__ == "__main__":
    main()
