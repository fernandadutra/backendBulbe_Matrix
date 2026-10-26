from dataclasses import dataclass
from typing import List, Optional

from app.core import relogio
from app.core.erros import ErroApi
from app.core.ids import gerar_id
from app.models.cliente import Cliente
from app.models.notificacao import Notificacao
from app.repositories.notificacao_repository import NotificacaoRepository

TITULO_MUDANCA_ETAPA = "Seu pedido avançou de etapa"
MENSAGEM_MUDANCA_ETAPA = "Seu pedido está agora em: {etapa}."
TITULO_PEDIDO_CRIADO = "Recebemos seu pedido"
MENSAGEM_PEDIDO_CRIADO = "Sua adesão foi recebida e a homologação junto à Cemig já começou. Acompanhe cada etapa pelo app."
TITULO_INDICACAO_CONVERTIDA = "Sua indicação virou cliente"
MENSAGEM_INDICACAO_CONVERTIDA = "Uma pessoa que você indicou concluiu a adesão. Seu crédito de indicação foi atualizado."


@dataclass
class NotificacoesDoCliente:
    notificacoes: List[Notificacao]
    nao_lidas: int


def notificar(
    cliente_id: str, tipo: str, referencia_tipo: str, referencia_id: str,
    repositorio: NotificacaoRepository, etapa_nome: Optional[str] = None,
) -> Notificacao:
    """Único ponto que escolhe título e mensagem; os eventos só dizem o que aconteceu."""
    textos = {
        "mudanca_etapa_pedido": (TITULO_MUDANCA_ETAPA, MENSAGEM_MUDANCA_ETAPA.format(etapa=etapa_nome)),
        "pedido_criado": (TITULO_PEDIDO_CRIADO, MENSAGEM_PEDIDO_CRIADO),
        "indicacao_convertida": (TITULO_INDICACAO_CONVERTIDA, MENSAGEM_INDICACAO_CONVERTIDA),
    }
    titulo, mensagem = textos[tipo]
    return repositorio.salvar(
        Notificacao(
            id=gerar_id("not"), cliente_id=cliente_id, tipo=tipo, titulo=titulo, mensagem=mensagem,
            lida=False, criada_em=relogio.agora(), referencia_tipo=referencia_tipo, referencia_id=referencia_id,
        )
    )


def listar_notificacoes(
    cliente: Cliente, apenas_nao_lidas: bool, repositorio: NotificacaoRepository
) -> NotificacoesDoCliente:
    todas = repositorio.listar_por_cliente(cliente.id)
    # O badge precisa do total de não lidas, qualquer que seja a página ou o filtro.
    nao_lidas = [n for n in todas if not n.lida]
    return NotificacoesDoCliente(nao_lidas if apenas_nao_lidas else todas, len(nao_lidas))


def atualizar_notificacao(
    notificacao_id: str, cliente: Cliente, lida: bool, repositorio: NotificacaoRepository
) -> Notificacao:
    notificacao = repositorio.obter(notificacao_id)
    # Notificação de outro cliente recebe a mesma resposta de notificação inexistente.
    if notificacao is None or notificacao.cliente_id != cliente.id:
        raise ErroApi(404, "NOTIFICACAO_NAO_ENCONTRADA", "Não encontramos essa notificação. Volte à lista para ver as suas notificações.")
    notificacao.lida = lida
    return notificacao
