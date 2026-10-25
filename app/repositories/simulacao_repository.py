from typing import List, Optional

from app.models.simulacao import Simulacao


class SimulacaoRepository:
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
