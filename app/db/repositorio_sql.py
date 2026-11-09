"""Peças comuns a todos os repositórios SQL."""

from contextlib import contextmanager
from typing import Any, Iterator

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.unidade_de_trabalho import UnidadeDeTrabalho, unidade_de_trabalho


class RepositorioSql:
    """Base dos repositórios SQL.

    Todo método segue o mesmo padrão:
    1. ``with self._unidade() as u``: entra na unidade de trabalho da requisição
       (ou abre uma só para esta chamada, fora de requisição);
    2. consulta ou grava usando ``u.sessao``;
    3. converte a linha (modelo SQLAlchemy) para a dataclass do domínio e a
       registra com ``u.rastrear``, para que alterações feitas pelo service
       voltem ao banco no fim da requisição.

    Nenhum objeto do SQLAlchemy sai do repositório.
    """

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    @contextmanager
    def _unidade(self) -> Iterator[UnidadeDeTrabalho]:
        with unidade_de_trabalho(self._session_factory) as unidade:
            unidade.sincronizar()
            yield unidade


def proxima_ordem(sessao: Session, modelo: Any) -> int:
    """Próximo valor de ordem_gravacao da tabela (1, 2, 3...)."""
    return (sessao.scalar(select(func.max(modelo.ordem_gravacao))) or 0) + 1


def copiar_campos(modelo: Any, **campos: Any) -> None:
    """Atribui só o que mudou: o SQLAlchemy então gera UPDATE apenas das colunas alteradas."""
    for nome, valor in campos.items():
        if getattr(modelo, nome) != valor:
            setattr(modelo, nome, valor)
