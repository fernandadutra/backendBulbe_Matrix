"""
Testes das migrations (Alembic).

O schema dos bancos de desenvolvimento e produção é criado SOMENTE pelas
migrations da pasta migrations/. Os outros testes usam create_all, que é mais
rápido. Estes testes garantem que as duas coisas dão o mesmo resultado: se
alguém mudar app/db/models.py e esquecer de gerar a migration, falha aqui.
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from app.db.database import Base

RAIZ = Path(__file__).resolve().parent.parent


@pytest.fixture
def banco_migrado(tmp_path):
    url = f"sqlite:///{tmp_path / 'migrations.db'}"
    config = Config(str(RAIZ / "alembic.ini"))
    config.set_main_option("script_location", str(RAIZ / "migrations"))
    config.set_main_option("sqlalchemy.url", url)
    config.attributes["configurar_log"] = False
    command.upgrade(config, "head")
    engine = create_engine(url)
    yield config, engine
    engine.dispose()


def test_upgrade_head_cria_todas_as_tabelas_dos_modelos(banco_migrado):
    _, engine = banco_migrado
    tabelas = set(inspect(engine).get_table_names())
    assert set(Base.metadata.tables) <= tabelas
    assert "alembic_version" in tabelas


def test_migrations_estao_em_dia_com_os_modelos(banco_migrado):
    _, engine = banco_migrado
    with engine.connect() as conexao:
        diferencas = compare_metadata(MigrationContext.configure(conexao), Base.metadata)
    assert diferencas == [], f"Gere uma migration: alembic revision --autogenerate -m '...'\n{diferencas}"


def test_downgrade_base_desfaz_tudo(banco_migrado):
    config, engine = banco_migrado
    command.downgrade(config, "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}
