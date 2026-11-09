"""
Conexão com o banco de dados.

- engine: o "cano" até o banco. Existe um só por aplicação.
- SessionLocal: fábrica de sessões. Cada requisição abre a sua (ver unidade_de_trabalho.py).
- Base: classe-mãe de todos os modelos (tabelas).
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL

# O SQLite, por padrão, só aceita a conexão na thread que a criou.
# O FastAPI usa várias threads, então liberamos essa checagem.
_E_SQLITE = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if _E_SQLITE else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

if _E_SQLITE:

    @event.listens_for(engine, "connect")
    def _ligar_chaves_estrangeiras(conexao, _registro):
        # O SQLite só confere as chaves estrangeiras quando pedimos, conexão a conexão.
        cursor = conexao.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# expire_on_commit=False mantém os valores acessíveis depois do commit:
# o repositório converte a linha para o modelo do domínio logo após gravar.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass
