"""Testes da conta da economia, direto na função, sem passar pela API.

Os testes de tests/test_simulacoes.py conferem o resultado pela rota.
Aqui a regra do desconto é conferida sozinha, para que uma mudança futura
(por exemplo, a base do cálculo que a Bulbe ainda vai confirmar) quebre
um teste curto e fácil de ler.
"""
import pytest

from app.services.simulacao_service import (
    PERCENTUAL_DESCONTO,
    VALOR_MAXIMO_CENTAVOS,
    VALOR_MINIMO_CENTAVOS,
    calcular_economia,
)


@pytest.mark.parametrize(
    "fatura, economia_mensal, valor_com_bulbe",
    [
        (5000, 750, 4250),          # menor valor aceito: R$ 50,00
        (12345, 1852, 10493),       # 18,5175 sobe para 18,52
        (35000, 5250, 29750),       # exemplo da spec: R$ 350,00
        (50001, 7500, 42501),       # 75,0015 fica em 75,00
        (500000, 75000, 425000),    # maior valor aceito: R$ 5.000,00
    ],
)
def test_valores_conferidos_a_mao(fatura, economia_mensal, valor_com_bulbe):
    resultado = calcular_economia(fatura)

    assert resultado.economia_mensal_centavos == economia_mensal
    assert resultado.valor_com_bulbe_centavos == valor_com_bulbe


def test_percentual_do_desconto_e_15_por_cento():
    assert PERCENTUAL_DESCONTO == 0.15


@pytest.mark.parametrize(
    "fatura, economia_mensal",
    [
        (5033, 755),   # 754,95 centavos sobe para 755
        (5036, 755),   # 755,40 centavos desce para 755
        (5037, 756),   # 755,55 centavos sobe para 756
    ],
)
def test_arredondamento_meio_para_cima_em_centavos(fatura, economia_mensal):
    assert calcular_economia(fatura).economia_mensal_centavos == economia_mensal


def test_economia_anual_e_doze_vezes_a_mensal():
    for fatura in (VALOR_MINIMO_CENTAVOS, 12345, 35000, VALOR_MAXIMO_CENTAVOS):
        resultado = calcular_economia(fatura)

        assert resultado.economia_anual_centavos == resultado.economia_mensal_centavos * 12


def test_economia_mais_valor_com_bulbe_sempre_fecha_a_fatura():
    # Em toda a faixa aceita, o que o cliente paga mais o que economiza é a fatura original.
    for fatura in range(VALOR_MINIMO_CENTAVOS, VALOR_MAXIMO_CENTAVOS + 1, 997):
        resultado = calcular_economia(fatura)

        assert resultado.economia_mensal_centavos + resultado.valor_com_bulbe_centavos == fatura


def test_economia_nunca_passa_de_15_por_cento_mais_meio_centavo():
    for fatura in range(VALOR_MINIMO_CENTAVOS, VALOR_MAXIMO_CENTAVOS + 1, 997):
        economia = calcular_economia(fatura).economia_mensal_centavos

        assert economia <= fatura * PERCENTUAL_DESCONTO + 0.5
