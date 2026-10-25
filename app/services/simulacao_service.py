from dataclasses import dataclass
from typing import List, Optional

from app.core import relogio
from app.core.erros import ErroApi
from app.core.ids import gerar_id
from app.models.cliente import Cliente
from app.models.simulacao import Simulacao
from app.repositories.simulacao_repository import SimulacaoRepository

PERCENTUAL_DESCONTO = 0.15
VALOR_MINIMO_CENTAVOS = 5000
VALOR_MAXIMO_CENTAVOS = 500000
DISTRIBUIDORA_ATENDIDA = "CEMIG"


@dataclass
class ResultadoCalculo:
    economia_mensal_centavos: int
    valor_com_bulbe_centavos: int
    economia_anual_centavos: int


def calcular_economia(valor_centavos: int) -> ResultadoCalculo:
    # Tudo em inteiros: arredondamento meio para cima sem passar por ponto flutuante.
    percentual_inteiro = round(PERCENTUAL_DESCONTO * 100)
    economia_mensal = (valor_centavos * percentual_inteiro + 50) // 100
    return ResultadoCalculo(
        economia_mensal_centavos=economia_mensal,
        valor_com_bulbe_centavos=valor_centavos - economia_mensal,
        economia_anual_centavos=economia_mensal * 12,
    )


def criar_simulacao(
    valor_fatura_centavos: int,
    consumo_kwh: Optional[int],
    distribuidora: Optional[str],
    cliente: Optional[Cliente],
    repositorio: SimulacaoRepository,
) -> Simulacao:
    if distribuidora is None:
        distribuidora = DISTRIBUIDORA_ATENDIDA
    if distribuidora.strip().upper() != DISTRIBUIDORA_ATENDIDA:
        raise ErroApi(
            422,
            "DISTRIBUIDORA_NAO_ATENDIDA",
            "Por enquanto a Bulbe atende apenas clientes da CEMIG.",
            [{"campo": "distribuidora", "problema": "distribuidora não atendida"}],
        )
    if not VALOR_MINIMO_CENTAVOS <= valor_fatura_centavos <= VALOR_MAXIMO_CENTAVOS:
        problema = "abaixo do mínimo aceito" if valor_fatura_centavos < VALOR_MINIMO_CENTAVOS else "acima do máximo aceito"
        raise ErroApi(
            422,
            "CONSUMO_FORA_DA_FAIXA",
            "O valor da fatura deve estar entre R$ 50,00 e R$ 5.000,00.",
            [{"campo": "valor_fatura_centavos", "problema": problema}],
        )
    if consumo_kwh is not None and consumo_kwh <= 0:
        raise ErroApi(
            422,
            "CONSUMO_FORA_DA_FAIXA",
            "O consumo informado deve ser maior que zero.",
            [{"campo": "consumo_kwh", "problema": "deve ser maior que zero"}],
        )

    calculo = calcular_economia(valor_fatura_centavos)
    simulacao = Simulacao(
        id=gerar_id("sim"),
        cliente_id=cliente.id if cliente else None,
        calculado_em=relogio.agora(),
        distribuidora=DISTRIBUIDORA_ATENDIDA,
        consumo_kwh=consumo_kwh,
        percentual_desconto=PERCENTUAL_DESCONTO,
        valor_sem_desconto_centavos=valor_fatura_centavos,
        valor_com_bulbe_centavos=calculo.valor_com_bulbe_centavos,
        economia_mensal_centavos=calculo.economia_mensal_centavos,
        economia_anual_centavos=calculo.economia_anual_centavos,
    )
    return repositorio.salvar(simulacao)


def listar_simulacoes(cliente: Cliente, repositorio: SimulacaoRepository) -> List[Simulacao]:
    return repositorio.listar_por_cliente(cliente.id)


def obter_simulacao(simulacao_id: str, cliente: Cliente, repositorio: SimulacaoRepository) -> Simulacao:
    simulacao = repositorio.obter(simulacao_id)
    if simulacao is None or simulacao.cliente_id != cliente.id:
        raise ErroApi(404, "SIMULACAO_NAO_ENCONTRADA", "Não encontramos essa simulação. Confira o código ou volte ao histórico.")
    return simulacao
