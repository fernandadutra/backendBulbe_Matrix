from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.core.estado import repositorios
from app.core.paginacao import ParametrosPaginacao, paginar, parametros_paginacao
from app.core.seguranca import obter_cliente_atual
from app.models.cliente import Cliente
from app.models.fatura import Fatura
from app.schemas.comum import respostas_de_erro
from app.schemas.fatura import (
    AcaoSugerida,
    ConsumoResposta,
    EstadoVazioComAcao,
    FaturaResposta,
    PaginaFaturas,
    PontoConsumo,
    TotaisConsumo,
)
from app.services import fatura_service

router = APIRouter(tags=["Faturas e Consumo"])

ESTADOS_VAZIOS = {
    "sem_instalacao": EstadoVazioComAcao(
        chave="sem_instalacao",
        titulo="Oops... Não encontrei nenhuma fatura.",
        mensagem="Você ainda não tem uma instalação vinculada. Simule sua economia e faça o pedido para começar.",
        acao_sugerida=AcaoSugerida(rotulo="Simular economia", destino="simular-desconto"),
    ),
    "aguardando_homologacao": EstadoVazioComAcao(
        chave="aguardando_homologacao",
        titulo="Oops... Não encontrei nenhuma fatura.",
        mensagem="Seu pedido ainda está em análise pela Cemig. A primeira fatura chega depois da aprovação.",
        acao_sugerida=AcaoSugerida(rotulo="Ver status do pedido", destino="status-pedido"),
    ),
    "homologado_sem_fatura": EstadoVazioComAcao(
        chave="homologado_sem_fatura",
        titulo="Sua primeira fatura ainda não chegou.",
        mensagem="Seu pedido foi aprovado. A primeira fatura Bulbe aparece aqui assim que for emitida.",
    ),
}


def _estado_vazio(chave: Optional[str]) -> Optional[EstadoVazioComAcao]:
    return ESTADOS_VAZIOS[chave] if chave else None


def _fatura(f: Fatura, situacao: str) -> FaturaResposta:
    return FaturaResposta(
        id=f.id,
        competencia=f.competencia,
        vencimento=f.vencimento,
        valor_centavos=f.valor_centavos,
        economia_centavos=f.economia_centavos,
        situacao=situacao,
        linha_digitavel=f.linha_digitavel,
        url_pdf=f.url_pdf,
    )


@router.get(
    "/faturas",
    response_model=PaginaFaturas,
    summary="Listar faturas do cliente",
    responses=respostas_de_erro(400, 401),
)
def listar_faturas(
    situacao: Optional[str] = Query(
        default=None,
        description="Filtra por situação da fatura.",
        json_schema_extra={"enum": ["aberta", "paga", "vencida"]},
    ),
    paginacao: ParametrosPaginacao = Depends(parametros_paginacao),
    cliente: Cliente = Depends(obter_cliente_atual),
):
    resultado = fatura_service.listar_faturas(cliente, situacao, repositorios.pedidos)
    fatia, total = paginar(resultado.faturas, paginacao)
    return PaginaFaturas(
        dados=[_fatura(f, resultado.situacoes[f.id]) for f in fatia],
        pagina=paginacao.pagina,
        limite=paginacao.limite,
        total=total,
        estado_vazio=_estado_vazio(resultado.estado_vazio),
    )


@router.get(
    "/faturas/{id}",
    response_model=FaturaResposta,
    summary="Obter uma fatura",
    responses=respostas_de_erro(401, 404),
)
def obter_fatura(id: str, cliente: Cliente = Depends(obter_cliente_atual)):
    fatura, situacao = fatura_service.obter_fatura(id, cliente, repositorios.pedidos)
    return _fatura(fatura, situacao)


@router.get(
    "/consumo",
    response_model=ConsumoResposta,
    summary="Consultar série de consumo e economia",
    responses=respostas_de_erro(400, 401),
)
def consultar_consumo(
    instalacao: Optional[str] = Query(default=None, description="Número da instalação. Padrão: a principal."),
    de: Optional[str] = Query(default=None, description="Primeira competência, no formato AAAA-MM."),
    ate: Optional[str] = Query(default=None, description="Última competência, no formato AAAA-MM."),
    granularidade: str = Query(default="mensal", json_schema_extra={"enum": ["mensal", "anual"]}),
    cliente: Cliente = Depends(obter_cliente_atual),
):
    consumo = fatura_service.consultar_consumo(cliente, instalacao, de, ate, granularidade, repositorios.pedidos)
    return ConsumoResposta(
        instalacao=consumo.instalacao,
        granularidade=consumo.granularidade,
        serie=[
            PontoConsumo(
                competencia=p.competencia,
                consumo_kwh=p.consumo_kwh,
                valor_pago_centavos=p.valor_pago_centavos,
                economia_centavos=p.economia_centavos,
            )
            for p in consumo.serie
        ],
        totais=TotaisConsumo(
            economia_acumulada_centavos=consumo.economia_acumulada, consumo_medio_kwh=consumo.consumo_medio
        ),
        estado_vazio=_estado_vazio(consumo.estado_vazio),
    )
