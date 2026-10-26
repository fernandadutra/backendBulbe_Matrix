import os
from datetime import datetime

# PBKDF2 com 600 mil iterações custa ~0,2 s por hash; nos testes a segurança do hash não importa.
os.environ.setdefault("BULBE_PBKDF2_ITERACOES", "1000")

import pytest
from fastapi.testclient import TestClient

from app.core import relogio
from app.core.estado import reiniciar_estado
from app.core.seguranca import emitir_token
from app.main import app
from app.repositories.dados_iniciais import SENHA_DEV  # noqa: F401  (reexportada para os testes)

AGORA_CONGELADA = datetime(2026, 10, 21, 10, 0, tzinfo=relogio.FUSO)

CLIENTE_A = "cli_3b9e1f42"
CLIENTE_B = "cli_8d21c7a0"
PEDIDO_A = "ped_7f3a9c21"
PEDIDO_B = "ped_c41e88d2"
EMAIL_A = "ana@exemplo.com.br"
CPF_A = "52998224725"
EMAIL_B = "bruno@exemplo.com.br"


@pytest.fixture(autouse=True)
def estado_limpo():
    reiniciar_estado()
    relogio.definir_relogio(lambda: AGORA_CONGELADA)
    yield
    app.dependency_overrides.clear()
    reiniciar_estado()


@pytest.fixture
def cliente_http():
    return TestClient(app)


def cabecalho_de(cliente_id: str, minutos: int = 60) -> dict:
    return {"Authorization": f"Bearer {emitir_token(cliente_id, minutos)}"}
