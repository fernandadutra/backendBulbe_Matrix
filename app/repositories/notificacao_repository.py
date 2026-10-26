from typing import Iterable, List, Optional

from app.models.notificacao import Notificacao


class NotificacaoRepository:
    def __init__(self, notificacoes: Iterable[Notificacao]):
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
