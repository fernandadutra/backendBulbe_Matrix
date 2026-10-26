from fastapi import APIRouter, Depends, Query

from app.core.estado import repositorios
from app.core.paginacao import ParametrosPaginacao, paginar, parametros_paginacao
from app.core.seguranca import obter_cliente_atual
from app.models.cliente import Cliente
from app.models.notificacao import Notificacao
from app.schemas.comum import respostas_de_erro
from app.schemas.notificacao import (
    NotificacaoRequisicao,
    NotificacaoResposta,
    PaginaNotificacoes,
    ReferenciaNotificacao,
)
from app.services import notificacao_service

router = APIRouter(prefix="/notificacoes", tags=["Notificações"])


def _notificacao(n: Notificacao) -> NotificacaoResposta:
    return NotificacaoResposta(
        id=n.id,
        tipo=n.tipo,
        titulo=n.titulo,
        mensagem=n.mensagem,
        lida=n.lida,
        criada_em=n.criada_em,
        referencia=ReferenciaNotificacao(tipo=n.referencia_tipo, id=n.referencia_id),
    )


@router.get(
    "",
    response_model=PaginaNotificacoes,
    summary="Listar notificações do cliente",
    responses=respostas_de_erro(400, 401),
)
def listar_notificacoes(
    apenas_nao_lidas: bool = Query(default=False, description="Quando verdadeiro, devolve só as não lidas."),
    paginacao: ParametrosPaginacao = Depends(parametros_paginacao),
    cliente: Cliente = Depends(obter_cliente_atual),
):
    resultado = notificacao_service.listar_notificacoes(cliente, apenas_nao_lidas, repositorios.notificacoes)
    fatia, total = paginar(resultado.notificacoes, paginacao)
    return PaginaNotificacoes(
        dados=[_notificacao(n) for n in fatia],
        nao_lidas=resultado.nao_lidas,
        pagina=paginacao.pagina,
        limite=paginacao.limite,
        total=total,
    )


@router.patch(
    "/{id}",
    response_model=NotificacaoResposta,
    summary="Marcar uma notificação como lida ou não lida",
    responses=respostas_de_erro(400, 401, 404),
)
def atualizar_notificacao(id: str, dados: NotificacaoRequisicao, cliente: Cliente = Depends(obter_cliente_atual)):
    return _notificacao(notificacao_service.atualizar_notificacao(id, cliente, dados.lida, repositorios.notificacoes))
