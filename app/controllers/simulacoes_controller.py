from typing import Optional

from fastapi import APIRouter, Depends, status

from app.core.estado import repositorios
from app.core.limite_requisicoes import limitar_simulacoes
from app.core.paginacao import ParametrosPaginacao, paginar, parametros_paginacao
from app.core.seguranca import obter_cliente_atual, obter_cliente_opcional
from app.models.cliente import Cliente
from app.models.simulacao import Simulacao
from app.schemas.comum import Paginacao, respostas_de_erro
from app.schemas.simulacao import (
    LinhaMemoriaCalculo,
    MemoriaCalculo,
    RotulosSimulacao,
    SimulacaoRequisicao,
    SimulacaoResposta,
    SimulacaoResumo,
    SubtotalMemoriaCalculo,
)
from app.services import simulacao_service

router = APIRouter(prefix="/simulacoes", tags=["Simulações"])

OBSERVACAO = "A taxa de economia é de até 15% e varia conforme o frete da distribuidora."


def _para_resposta(s: Simulacao) -> SimulacaoResposta:
    # O rateio por fonte (CEMIG e Bulbe) aguarda a regra da Bulbe (observação 3 da lista de endpoints).
    # Até lá, a memória traz uma única linha da Bulbe Energia.
    return SimulacaoResposta(
        id=s.id,
        calculado_em=s.calculado_em,
        percentual_desconto=s.percentual_desconto,
        valor_sem_desconto_centavos=s.valor_sem_desconto_centavos,
        valor_com_bulbe_centavos=s.valor_com_bulbe_centavos,
        economia_mensal_centavos=s.economia_mensal_centavos,
        economia_anual_centavos=s.economia_anual_centavos,
        rotulos=RotulosSimulacao(
            economia_mensal="Você vai economizar por mês",
            economia_anual="Sua economia anual estimada",
            valor_sem_desconto="Sem desconto, tarifa cheia",
            valor_com_bulbe=f"Com Bulbe, até {round(s.percentual_desconto * 100)}% desconto",
        ),
        memoria_calculo=MemoriaCalculo(
            consumo_total_kwh=s.consumo_kwh,
            linhas=[
                LinhaMemoriaCalculo(
                    fonte="Bulbe Energia",
                    consumo_kwh=s.consumo_kwh,
                    valor_centavos=s.valor_sem_desconto_centavos,
                    valor_com_desconto_centavos=s.valor_com_bulbe_centavos,
                    possui_desconto=True,
                )
            ],
            subtotal=SubtotalMemoriaCalculo(
                rotulo="Subtotal", consumo_kwh=s.consumo_kwh, valor_centavos=s.valor_sem_desconto_centavos
            ),
            observacao=OBSERVACAO,
        ),
    )


@router.post(
    "",
    response_model=SimulacaoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Calcular economia estimada",
    description="Público. Com token válido, a simulação é vinculada ao cliente e aparece no histórico.",
    responses=respostas_de_erro(400, 401, 422, 429),
    dependencies=[Depends(limitar_simulacoes)],
)
def criar_simulacao(
    dados: SimulacaoRequisicao,
    cliente: Optional[Cliente] = Depends(obter_cliente_opcional),
):
    simulacao = simulacao_service.criar_simulacao(
        dados.valor_fatura_centavos, dados.consumo_kwh, dados.distribuidora, cliente, repositorios.simulacoes
    )
    return _para_resposta(simulacao)


@router.get(
    "",
    response_model=Paginacao[SimulacaoResumo],
    summary="Listar histórico de simulações do cliente",
    responses=respostas_de_erro(400, 401),
)
def listar_simulacoes(
    paginacao: ParametrosPaginacao = Depends(parametros_paginacao),
    cliente: Cliente = Depends(obter_cliente_atual),
):
    simulacoes = simulacao_service.listar_simulacoes(cliente, repositorios.simulacoes)
    fatia, total = paginar(simulacoes, paginacao)
    dados = [
        SimulacaoResumo(
            id=s.id,
            calculado_em=s.calculado_em,
            valor_sem_desconto_centavos=s.valor_sem_desconto_centavos,
            economia_mensal_centavos=s.economia_mensal_centavos,
        )
        for s in fatia
    ]
    return Paginacao[SimulacaoResumo](dados=dados, pagina=paginacao.pagina, limite=paginacao.limite, total=total)


@router.get(
    "/{id}",
    response_model=SimulacaoResposta,
    summary="Obter simulação com memória de cálculo",
    responses=respostas_de_erro(401, 404),
)
def obter_simulacao(id: str, cliente: Cliente = Depends(obter_cliente_atual)):
    return _para_resposta(simulacao_service.obter_simulacao(id, cliente, repositorios.simulacoes))
