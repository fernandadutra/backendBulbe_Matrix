"""
Camada de Persistência, repositórios do Indique e ganhe (indicações e códigos).
Mesmo padrão dos demais: contrato, versão em memória e versão SQL.
"""

from typing import Dict, Iterable, List, Optional, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CodigoIndicacaoModel, IndicacaoModel
from app.db.repositorio_sql import RepositorioSql, copiar_campos, proxima_ordem
from app.models.indicacao import Indicacao

_CAMPOS = ("cliente_id", "nome", "whatsapp", "situacao", "indicada_em", "convertida_em")


class IndicacaoRepository(Protocol):
    def listar_por_cliente(self, cliente_id: str) -> List[Indicacao]: ...
    def por_whatsapp(self, whatsapp: str) -> Optional[Indicacao]: ...
    def salvar(self, indicacao: Indicacao) -> Indicacao: ...
    def codigo_do_cliente(self, cliente_id: str) -> Optional[str]: ...
    def cliente_do_codigo(self, codigo: str) -> Optional[str]: ...
    def salvar_codigo(self, cliente_id: str, codigo: str) -> None: ...


class InMemoryIndicacaoRepository:
    def __init__(self, indicacoes: Iterable[Indicacao] = (), codigos: Optional[Dict[str, str]] = None):
        self._indicacoes: List[Indicacao] = list(indicacoes)
        self._codigos: Dict[str, str] = dict(codigos or {})  # cliente_id -> código

    def listar_por_cliente(self, cliente_id: str) -> List[Indicacao]:
        # Mais recentes primeiro. Em empate de data, vale a ordem de gravação.
        do_cliente = [i for i in reversed(self._indicacoes) if i.cliente_id == cliente_id]
        return sorted(do_cliente, key=lambda i: i.indicada_em, reverse=True)

    def por_whatsapp(self, whatsapp: str) -> Optional[Indicacao]:
        return next((i for i in self._indicacoes if i.whatsapp == whatsapp), None)

    def salvar(self, indicacao: Indicacao) -> Indicacao:
        self._indicacoes.append(indicacao)
        return indicacao

    def codigo_do_cliente(self, cliente_id: str) -> Optional[str]:
        return self._codigos.get(cliente_id)

    def cliente_do_codigo(self, codigo: str) -> Optional[str]:
        return next((c for c, cod in self._codigos.items() if cod == codigo), None)

    def salvar_codigo(self, cliente_id: str, codigo: str) -> None:
        self._codigos[cliente_id] = codigo


def _para_dominio(m: IndicacaoModel) -> Indicacao:
    return Indicacao(id=m.id, **{c: getattr(m, c) for c in _CAMPOS})


def _gravar(sessao: Session, i: Indicacao) -> None:
    modelo = sessao.get(IndicacaoModel, i.id)
    if modelo is None:
        modelo = IndicacaoModel(id=i.id, ordem_gravacao=proxima_ordem(sessao, IndicacaoModel))
        sessao.add(modelo)
    copiar_campos(modelo, **{c: getattr(i, c) for c in _CAMPOS})


class SqlIndicacaoRepository(RepositorioSql):
    def _entregar(self, u, modelo):
        if modelo is None:
            return None
        return u.obter(Indicacao, modelo.id) or u.rastrear(_para_dominio(modelo), modelo.id, _gravar)

    def listar_por_cliente(self, cliente_id: str) -> List[Indicacao]:
        # Mais recentes primeiro. Em empate de data, vale a ordem de gravação.
        with self._unidade() as u:
            consulta = (
                select(IndicacaoModel)
                .where(IndicacaoModel.cliente_id == cliente_id)
                .order_by(IndicacaoModel.indicada_em.desc(), IndicacaoModel.ordem_gravacao.desc())
            )
            return [self._entregar(u, m) for m in u.sessao.scalars(consulta)]

    def por_whatsapp(self, whatsapp: str) -> Optional[Indicacao]:
        # A primeira gravada, como na versão em memória.
        with self._unidade() as u:
            consulta = (
                select(IndicacaoModel)
                .where(IndicacaoModel.whatsapp == whatsapp)
                .order_by(IndicacaoModel.ordem_gravacao)
            )
            return self._entregar(u, u.sessao.scalars(consulta).first())

    def salvar(self, indicacao: Indicacao) -> Indicacao:
        with self._unidade() as u:
            _gravar(u.sessao, indicacao)
            u.sessao.flush()
            return u.rastrear(indicacao, indicacao.id, _gravar)

    def codigo_do_cliente(self, cliente_id: str) -> Optional[str]:
        with self._unidade() as u:
            modelo = u.sessao.get(CodigoIndicacaoModel, cliente_id)
            return modelo.codigo if modelo else None

    def cliente_do_codigo(self, codigo: str) -> Optional[str]:
        with self._unidade() as u:
            consulta = select(CodigoIndicacaoModel.cliente_id).where(CodigoIndicacaoModel.codigo == codigo)
            return u.sessao.scalars(consulta).first()

    def salvar_codigo(self, cliente_id: str, codigo: str) -> None:
        with self._unidade() as u:
            modelo = u.sessao.get(CodigoIndicacaoModel, cliente_id)
            if modelo is None:
                u.sessao.add(CodigoIndicacaoModel(cliente_id=cliente_id, codigo=codigo))
            else:
                modelo.codigo = codigo
            u.sessao.flush()
