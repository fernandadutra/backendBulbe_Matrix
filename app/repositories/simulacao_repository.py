"""
Camada de Persistência, repositórios de Simulação.
Mesmo padrão dos demais: contrato, versão em memória e versão SQL.
"""

from typing import List, Optional, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import SimulacaoModel
from app.db.repositorio_sql import RepositorioSql, copiar_campos, proxima_ordem
from app.models.simulacao import Simulacao

_CAMPOS = (
    "cliente_id", "calculado_em", "distribuidora", "consumo_kwh", "percentual_desconto",
    "valor_sem_desconto_centavos", "valor_com_bulbe_centavos", "economia_mensal_centavos", "economia_anual_centavos",
)


class SimulacaoRepository(Protocol):
    def salvar(self, simulacao: Simulacao) -> Simulacao: ...
    def obter(self, simulacao_id: str) -> Optional[Simulacao]: ...
    def listar_por_cliente(self, cliente_id: str) -> List[Simulacao]: ...


class InMemorySimulacaoRepository:
    def __init__(self):
        self._simulacoes: List[Simulacao] = []

    def salvar(self, simulacao: Simulacao) -> Simulacao:
        self._simulacoes.append(simulacao)
        return simulacao

    def obter(self, simulacao_id: str) -> Optional[Simulacao]:
        return next((s for s in self._simulacoes if s.id == simulacao_id), None)

    def listar_por_cliente(self, cliente_id: str) -> List[Simulacao]:
        # Mais recentes primeiro. Em empate de horário, vale a ordem de gravação.
        do_cliente = [s for s in reversed(self._simulacoes) if s.cliente_id == cliente_id]
        return sorted(do_cliente, key=lambda s: s.calculado_em, reverse=True)


def _para_dominio(m: SimulacaoModel) -> Simulacao:
    return Simulacao(id=m.id, **{c: getattr(m, c) for c in _CAMPOS})


def _gravar(sessao: Session, s: Simulacao) -> None:
    modelo = sessao.get(SimulacaoModel, s.id)
    if modelo is None:
        modelo = SimulacaoModel(id=s.id, ordem_gravacao=proxima_ordem(sessao, SimulacaoModel))
        sessao.add(modelo)
    copiar_campos(modelo, **{c: getattr(s, c) for c in _CAMPOS})


class SqlSimulacaoRepository(RepositorioSql):
    def _entregar(self, u, modelo):
        if modelo is None:
            return None
        return u.obter(Simulacao, modelo.id) or u.rastrear(_para_dominio(modelo), modelo.id, _gravar)

    def salvar(self, simulacao: Simulacao) -> Simulacao:
        with self._unidade() as u:
            _gravar(u.sessao, simulacao)
            u.sessao.flush()
            return u.rastrear(simulacao, simulacao.id, _gravar)

    def obter(self, simulacao_id: str) -> Optional[Simulacao]:
        with self._unidade() as u:
            return self._entregar(u, u.sessao.get(SimulacaoModel, simulacao_id))

    def listar_por_cliente(self, cliente_id: str) -> List[Simulacao]:
        # Mais recentes primeiro. Em empate de horário, vale a ordem de gravação.
        with self._unidade() as u:
            consulta = (
                select(SimulacaoModel)
                .where(SimulacaoModel.cliente_id == cliente_id)
                .order_by(SimulacaoModel.calculado_em.desc(), SimulacaoModel.ordem_gravacao.desc())
            )
            return [self._entregar(u, m) for m in u.sessao.scalars(consulta)]
