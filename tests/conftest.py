"""
Fixtures compartilhadas por todos os arquivos de teste.

Os testes usam um banco SEPARADO (bulbe_test.db), nunca o banco de
desenvolvimento (bulbe.db). Por isso a variável de ambiente é definida aqui,
ANTES de qualquer import de "app": o engine é criado quando app.db.database
é importado.
"""

import os
from datetime import datetime

ARQUIVO_BANCO_DE_TESTE = "bulbe_test.db"
os.environ["BULBE_DATABASE_URL"] = f"sqlite:///./{ARQUIVO_BANCO_DE_TESTE}"
# PBKDF2 com 600 mil iterações custa ~0,2 s por hash; nos testes a segurança do hash não importa.
os.environ.setdefault("BULBE_PBKDF2_ITERACOES", "1000")

import pytest
from sqlalchemy import event
from fastapi.testclient import TestClient

from app.core import relogio
from app.core.estado import reiniciar_estado
from app.core.seguranca import emitir_token
from app.db import seed
from app.db.database import Base, engine
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


@event.listens_for(engine, "connect")
def _banco_de_teste_sem_fsync(conexao, _registro):
    # O banco de teste é descartável: não precisa esperar o disco a cada commit.
    conexao.execute("PRAGMA synchronous=OFF")


def limpar_banco() -> None:
    """Apaga as linhas de todas as tabelas (filhas antes das mães, por causa das chaves estrangeiras)."""
    with engine.begin() as conexao:
        for tabela in reversed(Base.metadata.sorted_tables):
            conexao.execute(tabela.delete())


@pytest.fixture(scope="session", autouse=True)
def banco_de_teste():
    """Cria as tabelas do banco de teste uma vez e, ao final de toda a execução, apaga o arquivo.

    Nos testes usamos create_all, que é mais rápido; os bancos de desenvolvimento e
    produção são criados SOMENTE pelas migrations (tests/test_migrations.py garante
    que as duas coisas dão o mesmo schema).
    """
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    engine.dispose()
    if os.path.exists(ARQUIVO_BANCO_DE_TESTE):
        os.remove(ARQUIVO_BANCO_DE_TESTE)


@pytest.fixture(autouse=True)
def estado_limpo(banco_de_teste):
    """Roda antes de CADA teste: esvazia o banco e grava os dados de demonstração.

    Assim um teste nunca depende do que outro deixou gravado.
    """
    limpar_banco()
    reiniciar_estado()
    seed.popular()
    relogio.definir_relogio(lambda: AGORA_CONGELADA)
    yield
    app.dependency_overrides.clear()
    reiniciar_estado()


@pytest.fixture
def cliente_http():
    return TestClient(app)


def cabecalho_de(cliente_id: str, minutos: int = 60) -> dict:
    return {"Authorization": f"Bearer {emitir_token(cliente_id, minutos)}"}
