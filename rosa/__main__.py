# SPDX-FileCopyrightText: 2026 CDT
# SPDX-License-Identifier: MIT
import argparse
from .server import serve


def main():
    parser = argparse.ArgumentParser(description="ROSA · consola de simulación local")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", default="rosa-demo.sqlite3")
    parser.add_argument("--ollama-model", default=None, help="Nombre de un modelo ya instalado en Ollama")
    args = parser.parse_args()
    serve(args.port, args.db, args.ollama_model)


if __name__ == "__main__":
    main()
