"""
Camada de Persistência, repositórios de Notificação.
Mesmo padrão dos demais: contrato, versão em memória e versão SQL.
"""

from typing import Iterable, List, Optional, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import NotificacaoModel
from app.db.repositorio_sql import RepositorioSql, copiar_campos, proxima_ordem
from app.models.notificacao import Notificacao

_CAMPOS = ("cliente_id", "tipo", "titulo", "mensagem", "lida", "criada_em", "referencia_tipo", "referencia_id")


class NotificacaoRepository(Protocol):
    def listar_por_cliente(self, cliente_id: str) -> List[Notificacao]: ...
    def obter(self, notificacao_id: str) -> Optional[Notificacao]: ...
    def salvar(self, notificacao: Notificacao) -> Notificacao: ...


class InMemoryNotificacaoRepository:
    def __init__(self, notificacoes: Iterable[Notificacao] = ()):
        self._notificacoes: List[Notificacao] = list(notificacoes)

    def listar_por_cliente(self, cliente_id: str) -> List[Notificacao]:
        # Mais recentes primeiro. Em empate de data, vale a ordem de gravação.
        do_cliente = [n for n in reversed(self._notificacoes) if n.cliente_id == cliente_id]
        return sorted(do_cliente, key=lambda n: n.criada_em, reverse=True)

    def obter(self, notificacao_id: str) -> Optional[Notificacao]:
        return next((n for n in self._notificacoes if n.id == notificacao_id), None)

    def salvar(self, notificacao: Notificacao) -> Notificacao:
        self._notificacoes.append(notificacao)
        return notificacao


def _para_dominio(m: NotificacaoModel) -> Notificacao:
    return Notificacao(id=m.id, **{c: getattr(m, c) for c in _CAMPOS})


def _gravar(sessao: Session, n: Notificacao) -> None:
    modelo = sessao.get(NotificacaoModel, n.id)
    if modelo is None:
        modelo = NotificacaoModel(id=n.id, ordem_gravacao=proxima_ordem(sessao, NotificacaoModel))
        sessao.add(modelo)
    copiar_campos(modelo, **{c: getattr(n, c) for c in _CAMPOS})


class SqlNotificacaoRepository(RepositorioSql):
    def _entregar(self, u, modelo):
        if modelo is None:
            return None
        return u.obter(Notificacao, modelo.id) or u.rastrear(_para_dominio(modelo), modelo.id, _gravar)

    def listar_por_cliente(self, cliente_id: str) -> List[Notificacao]:
        # Mais recentes primeiro. Em empate de data, vale a ordem de gravação.
        with self._unidade() as u:
            consulta = (
                select(NotificacaoModel)
                .where(NotificacaoModel.cliente_id == cliente_id)
                .order_by(NotificacaoModel.criada_em.desc(), NotificacaoModel.ordem_gravacao.desc())
            )
            return [self._entregar(u, m) for m in u.sessao.scalars(consulta)]

    def obter(self, notificacao_id: str) -> Optional[Notificacao]:
        with self._unidade() as u:
            return self._entregar(u, u.sessao.get(NotificacaoModel, notificacao_id))

    def salvar(self, notificacao: Notificacao) -> Notificacao:
        with self._unidade() as u:
            _gravar(u.sessao, notificacao)
            u.sessao.flush()
            return u.rastrear(notificacao, notificacao.id, _gravar)
