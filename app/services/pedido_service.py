import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from app.core import relogio
from app.core.erros import ErroApi
from app.models.cliente import Cliente
from app.models.pedido import SITUACOES_PEDIDO, Etapa, Pedido
from app.repositories.pedido_repository import PedidoRepository
from app.services.integracao_cemig import IntegracaoCemig

PRAZO_ESTIMADO_DIAS = {"minimo": 90, "maximo": 120}


@dataclass
class StatusDoPedido:
    pedido: Pedido
    etapas: List[Etapa]
    consultado_em: datetime
    dado_desatualizado: bool


def listar_pedidos(cliente: Cliente, situacao: Optional[str], repositorio: PedidoRepository) -> List[Pedido]:
    if situacao is not None and situacao not in SITUACOES_PEDIDO:
        raise ErroApi(
            400,
            "PARAMETRO_INVALIDO",
            "A situação informada não existe. Use em_andamento, aprovado ou reprovado.",
            [{"campo": "situacao", "problema": "valor fora de em_andamento, aprovado, reprovado"}],
        )
    pedidos = repositorio.listar_por_cliente(cliente.id)
    if situacao:
        pedidos = [p for p in pedidos if p.situacao == situacao]
    return pedidos


def obter_status(
    pedido_id: str, cliente: Cliente, repositorio: PedidoRepository, integracao: IntegracaoCemig
) -> StatusDoPedido:
    pedido = repositorio.obter(pedido_id)
    # Pedido de outro cliente recebe a mesma resposta de pedido inexistente.
    if pedido is None or pedido.cliente_id != cliente.id:
        raise ErroApi(404, "PEDIDO_NAO_ENCONTRADO", "Não encontramos esse pedido. Confira o número ou volte à lista de pedidos.")

    desatualizado = False
    try:
        etapas = integracao.consultar(pedido)
    except Exception:
        # Qualquer falha da integração (timeout, resposta inesperada) conta como indisponibilidade.
        logging.getLogger("bulbe").exception("Falha ao consultar a Cemig para o pedido %s", pedido.id)
        etapas = None
        desatualizado = True

    if etapas is not None:
        repositorio.salvar_consulta(pedido, etapas, relogio.agora())

    if pedido.consultado_em is None:
        raise ErroApi(
            503,
            "INTEGRACAO_INDISPONIVEL",
            "Não conseguimos consultar a Cemig agora e ainda não há uma consulta anterior deste pedido. Tente de novo em alguns minutos.",
        )

    return StatusDoPedido(
        pedido=pedido,
        etapas=pedido.etapas,
        consultado_em=pedido.consultado_em,
        dado_desatualizado=desatualizado,
    )
