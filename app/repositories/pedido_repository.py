from datetime import datetime
from typing import Iterable, List, Optional

from app.models.fatura import Fatura
from app.models.pedido import Etapa, Pedido


class PedidoRepository:
    def __init__(self, pedidos: Iterable[Pedido], faturas: Iterable[Fatura] = ()):
        self._pedidos = list(pedidos)
        self._faturas = list(faturas)

    def listar_por_cliente(self, cliente_id: str) -> List[Pedido]:
        do_cliente = [p for p in self._pedidos if p.cliente_id == cliente_id]
        return sorted(do_cliente, key=lambda p: p.criado_em, reverse=True)

    def obter(self, pedido_id: str) -> Optional[Pedido]:
        return next((p for p in self._pedidos if p.id == pedido_id), None)

    def cliente_tem_pedido_aprovado(self, cliente_id: str) -> bool:
        return any(p.cliente_id == cliente_id and p.situacao == "aprovado" for p in self._pedidos)

    def salvar_consulta(self, pedido: Pedido, etapas: List[Etapa], consultado_em: datetime) -> None:
        pedido.etapas = etapas
        pedido.consultado_em = consultado_em

    def salvar(self, pedido: Pedido) -> None:
        self._pedidos.append(pedido)

    def listar_faturas_por_cliente(self, cliente_id: str) -> List[Fatura]:
        do_cliente = [f for f in self._faturas if f.cliente_id == cliente_id]
        return sorted(do_cliente, key=lambda f: f.competencia, reverse=True)

    def obter_fatura(self, fatura_id: str) -> Optional[Fatura]:
        return next((f for f in self._faturas if f.id == fatura_id), None)
