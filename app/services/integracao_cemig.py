from typing import List, Optional, Protocol

from app.models.pedido import Etapa, Pedido


class IntegracaoIndisponivel(Exception):
    """A consulta à CEMIG falhou."""


class IntegracaoCemig(Protocol):
    def consultar(self, pedido: Pedido) -> Optional[List[Etapa]]:
        """Devolve as etapas atualizadas ou None se não há novidade.

        Qualquer exceção levantada aqui (IntegracaoIndisponivel, timeout, resposta inesperada)
        é tratada como indisponibilidade: o cliente recebe o último dado guardado ou 503.
        """
        ...


class SemIntegracaoCemig:
    # Hoje a atualização das etapas é manual (ponto 4 das observações da lista de endpoints).
    def consultar(self, pedido: Pedido) -> Optional[List[Etapa]]:
        return None


def obter_integracao_cemig() -> IntegracaoCemig:
    return SemIntegracaoCemig()
