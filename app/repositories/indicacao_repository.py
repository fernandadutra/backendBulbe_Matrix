from typing import Dict, Iterable, List, Optional

from app.models.indicacao import Indicacao


class IndicacaoRepository:
    def __init__(self, indicacoes: Iterable[Indicacao], codigos: Dict[str, str]):
        self._indicacoes: List[Indicacao] = list(indicacoes)
        self._codigos: Dict[str, str] = dict(codigos)  # cliente_id -> código

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
