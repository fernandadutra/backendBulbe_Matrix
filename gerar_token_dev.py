"""Imprime um token JWT de desenvolvimento para um cliente da semente.

Uso: .venv/bin/python gerar_token_dev.py [cliente_id]
Sem argumento, usa cli_3b9e1f42 (Ana Souza). Outro cliente: cli_8d21c7a0 (Bruno Lima).
"""
import sys

from app.core.seguranca import emitir_token

if __name__ == "__main__":
    print(emitir_token(sys.argv[1] if len(sys.argv) > 1 else "cli_3b9e1f42", minutos=60 * 24))
