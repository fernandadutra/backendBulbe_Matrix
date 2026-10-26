from fastapi import APIRouter, Depends, status

from app.core.estado import repositorios
from app.core.seguranca import obter_cliente_atual
from app.models.cliente import Cliente
from app.models.indicacao import Indicacao
from app.schemas.comum import respostas_de_erro
from app.schemas.indicacao import FaixaIndicacao, IndicacaoItem, IndicacaoRequisicao, PainelIndicacoes
from app.services import indicacao_service

router = APIRouter(prefix="/indicacoes", tags=["Indique e ganhe"])


def _item(indicacao: Indicacao) -> IndicacaoItem:
    return IndicacaoItem(
        id=indicacao.id,
        nome_ofuscado=indicacao_service.ofuscar_nome(indicacao.nome),
        situacao=indicacao.situacao,
        indicada_em=indicacao.indicada_em,
    )


def _painel(painel: indicacao_service.PainelDeIndicacoes) -> PainelIndicacoes:
    return PainelIndicacoes(
        codigo=painel.codigo,
        url_compartilhamento=indicacao_service.URL_COMPARTILHAMENTO.format(codigo=painel.codigo),
        recompensa_por_indicacao_centavos=indicacao_service.RECOMPENSA_POR_INDICACAO_CENTAVOS,
        total_indicacoes=painel.total,
        indicacoes_convertidas=painel.convertidas,
        credito_acumulado_centavos=painel.credito_centavos,
        faixa_atual=FaixaIndicacao(
            chave=painel.faixa[0],
            nome=painel.faixa[1],
            proxima_faixa=painel.proxima_faixa,
            indicacoes_para_proxima_faixa=painel.para_proxima,
        ),
        indicacoes=[_item(i) for i in painel.indicacoes],
    )


@router.get(
    "",
    response_model=PainelIndicacoes,
    summary="Consultar indicações do cliente",
    responses=respostas_de_erro(401),
)
def obter_indicacoes(cliente: Cliente = Depends(obter_cliente_atual)):
    return _painel(indicacao_service.painel(cliente, repositorios.indicacoes))


@router.post(
    "",
    response_model=IndicacaoItem,
    status_code=status.HTTP_201_CREATED,
    summary="Indicar um contato",
    responses=respostas_de_erro(400, 401, 409, 422),
)
def indicar_contato(dados: IndicacaoRequisicao, cliente: Cliente = Depends(obter_cliente_atual)):
    indicacao = indicacao_service.indicar(
        cliente, dados.nome, dados.whatsapp, repositorios.indicacoes, repositorios.clientes
    )
    return _item(indicacao)
