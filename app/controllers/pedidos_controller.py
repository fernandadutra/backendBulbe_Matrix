from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.estado import repositorios
from app.core.paginacao import ParametrosPaginacao, paginar, parametros_paginacao
from app.core.seguranca import obter_cliente_atual
from app.models.cliente import Cliente
from app.schemas.comum import Paginacao, respostas_de_erro
from app.schemas.pedido import EtapaAtualPedido, EtapaPedido, PedidoResumo, PrazoEstimado, StatusPedido
from app.services import pedido_service
from app.services.integracao_cemig import IntegracaoCemig, obter_integracao_cemig

router = APIRouter(prefix="/pedidos", tags=["Jornada do Cliente"])


@router.get(
    "",
    response_model=Paginacao[PedidoResumo],
    summary="Listar pedidos do cliente",
    responses=respostas_de_erro(400, 401),
)
def listar_pedidos(
    situacao: Optional[str] = Query(
        default=None,
        description="Filtra por situação do pedido.",
        json_schema_extra={"enum": ["em_andamento", "aprovado", "reprovado"]},
    ),
    paginacao: ParametrosPaginacao = Depends(parametros_paginacao),
    cliente: Cliente = Depends(obter_cliente_atual),
):
    pedidos = pedido_service.listar_pedidos(cliente, situacao, repositorios.pedidos)
    fatia, total = paginar(pedidos, paginacao)
    dados = []
    for p in fatia:
        etapa = p.etapa_atual
        dados.append(
            PedidoResumo(
                id=p.id,
                numero_instalacao=p.numero_instalacao,
                distribuidora=p.distribuidora,
                situacao=p.situacao,
                etapa_atual_ordem=etapa.ordem if etapa else None,
                etapa_atual_nome=etapa.nome if etapa else None,
                criado_em=p.criado_em,
            )
        )
    return Paginacao[PedidoResumo](dados=dados, pagina=paginacao.pagina, limite=paginacao.limite, total=total)


@router.get(
    "/{id}/status",
    response_model=StatusPedido,
    summary="Acompanhar status da homologação",
    responses=respostas_de_erro(401, 404, 503),
)
def obter_status_pedido(
    id: str,
    cliente: Cliente = Depends(obter_cliente_atual),
    integracao: IntegracaoCemig = Depends(obter_integracao_cemig),
):
    status = pedido_service.obter_status(id, cliente, repositorios.pedidos, integracao, repositorios.notificacoes)
    pedido = status.pedido
    atual = pedido.etapa_atual
    return StatusPedido(
        pedido_id=pedido.id,
        numero_instalacao=pedido.numero_instalacao,
        situacao=pedido.situacao,
        etapa_atual=EtapaAtualPedido(
            ordem=atual.ordem, chave=atual.chave, nome=atual.nome, descricao=atual.descricao,
            situacao=atual.situacao, iniciada_em=atual.iniciada_em,
        ) if atual else None,
        etapas=[
            EtapaPedido(
                ordem=e.ordem, chave=e.chave, nome=e.nome, descricao=e.descricao,
                situacao=e.situacao, concluida_em=e.concluida_em,
            )
            for e in status.etapas
        ],
        previsao_proxima_atualizacao=pedido.previsao_proxima_atualizacao,
        prazo_estimado_dias=PrazoEstimado(**pedido_service.PRAZO_ESTIMADO_DIAS),
        consultado_em=status.consultado_em,
        dado_desatualizado=status.dado_desatualizado,
    )
