from datetime import date, datetime, timedelta, timezone
from typing import Dict, List

from app.core import senhas
from app.models.beneficio import Beneficio, Parceiro, Trilha
from app.models.cliente import Cliente
from app.models.dica import BlocoLista, BlocoParagrafo, Dica, ItemLista
from app.models.fatura import Fatura
from app.models.indicacao import Indicacao
from app.models.notificacao import Notificacao
from app.models.pedido import CATALOGO_ETAPAS, Etapa, Pedido

_BRT = timezone(timedelta(hours=-3))

SENHA_DEV = "bulbe-dev-123"
_hash_senha_dev = None


def _dt(ano, mes, dia, hora=9, minuto=0) -> datetime:
    return datetime(ano, mes, dia, hora, minuto, tzinfo=_BRT)


def _etapas(situacoes, iniciadas, concluidas) -> List[Etapa]:
    return [
        Etapa(ordem, chave, nome, descricao, situacoes[i], iniciadas[i], concluidas[i])
        for i, (ordem, chave, nome, descricao) in enumerate(CATALOGO_ETAPAS)
    ]


def clientes() -> List[Cliente]:
    global _hash_senha_dev
    # O hash é caro e reiniciar_estado() roda a cada teste: calcula uma vez por processo.
    if _hash_senha_dev is None:
        _hash_senha_dev = senhas.gerar_hash(SENHA_DEV)
    return [
        Cliente(id="cli_3b9e1f42", nome="Ana Souza", email="ana@exemplo.com.br", cpf="52998224725",
                telefone="+5531999998888", senha_hash=_hash_senha_dev),
        Cliente(id="cli_8d21c7a0", nome="Bruno Lima", email="bruno@exemplo.com.br", cpf="11144477735",
                telefone="+5531988887777", senha_hash=_hash_senha_dev),
    ]


def pedidos() -> List[Pedido]:
    pedido_a = Pedido(
        id="ped_7f3a9c21",
        cliente_id="cli_3b9e1f42",
        numero_instalacao="3013588579",
        distribuidora="CEMIG",
        situacao="em_andamento",
        criado_em=_dt(2026, 6, 2, 9, 14),
        previsao_proxima_atualizacao=date(2026, 9, 15),
        etapas=_etapas(
            ["em_andamento", "pendente", "pendente", "pendente"],
            [_dt(2026, 6, 2, 9, 14), None, None, None],
            [None, None, None, None],
        ),
        consultado_em=_dt(2026, 8, 23, 14, 30),
    )
    pedido_b = Pedido(
        id="ped_c41e88d2",
        cliente_id="cli_8d21c7a0",
        numero_instalacao="3013591122",
        distribuidora="CEMIG",
        situacao="aprovado",
        criado_em=_dt(2026, 3, 10, 10, 5),
        previsao_proxima_atualizacao=None,
        etapas=_etapas(
            ["concluida"] * 4,
            [_dt(2026, 3, 10, 10, 5), _dt(2026, 3, 24, 11, 0), _dt(2026, 4, 2, 15, 30), _dt(2026, 7, 14, 9, 0)],
            [_dt(2026, 3, 24, 11, 0), _dt(2026, 4, 2, 15, 30), _dt(2026, 7, 14, 9, 0), _dt(2026, 7, 14, 9, 0)],
        ),
        consultado_em=_dt(2026, 8, 23, 14, 30),
    )
    return [pedido_a, pedido_b]


def faturas() -> List[Fatura]:
    def fatura(sufixo, competencia, vencimento, consumo, valor, economia, situacao):
        id_ = f"fat_{sufixo}"
        return Fatura(
            id=id_, cliente_id="cli_8d21c7a0", pedido_id="ped_c41e88d2", competencia=competencia,
            vencimento=vencimento, valor_centavos=valor, economia_centavos=economia, consumo_kwh=consumo,
            situacao=situacao, linha_digitavel=f"001900000901234567890123456789012345678901{competencia[-2:]}",
            url_pdf=f"https://cdn.bulbe.com.br/faturas/{id_}.pdf",
        )

    return [
        fatura("08a2ce31", "2026-08", date(2026, 9, 10), 241, 28800, 5080, "paga"),
        fatura("1b7d4e92", "2026-09", date(2026, 10, 10), 249, 29750, 5250, "paga"),
        fatura("2c9f5a03", "2026-10", date(2026, 11, 10), 255, 30600, 5400, "aberta"),
    ]


def parceiros() -> List[Parceiro]:
    def logo(slug):
        return f"https://cdn.bulbe.com.br/parceiros/{slug}.png"

    return [
        Parceiro("par_inter", "Inter", logo("inter"), "#ff7200", destaque=True),
        Parceiro("par_livelo", "Livelo", logo("livelo"), "#f62791"),
        Parceiro("par_frossard", "Canal do Frossard", logo("frossard"), "#ffc100"),
        Parceiro("par_araujo", "Araújo", logo("araujo"), "#0f1f6b", destaque=True),
    ]


def trilhas() -> List[Trilha]:
    def icone(chave):
        return f"https://cdn.bulbe.com.br/trilhas/{chave}.svg"

    return [
        Trilha("connect", "Bulbe Connect", "Cliente possui acesso imediato a benefícios e parceiros.",
               "livre", "verde", icone("connect")),
        Trilha("movement", "Bulbe Movement", "Novas experiências serão liberadas ao longo da sua jornada.",
               "pedido_aprovado", "azul", icone("movement")),
        Trilha("experience", "Bulbe Experience", "Uma experiência ainda mais exclusiva aguarda você.",
               "fatura_ativa", "laranja", icone("experience")),
    ]


def beneficios() -> List[Beneficio]:
    def acesso(slug):
        return f"https://parceiros.bulbe.com.br/{slug}/redirecionamento"

    return [
        Beneficio(
            id="ben_inter_cashback", trilha="connect", parceiro_id="par_inter",
            titulo="Até 77% de cashback!",
            descricao="Cashback em compras realizadas pelo app do Inter.",
            regras_de_uso="Válido para novas contas abertas pelo link Bulbe. Cashback creditado em até 60 dias.",
            tipo="uso_unico", regra_acesso="livre",
            validade_inicio=date(2026, 8, 1), validade_fim=date(2026, 12, 31), ativo=True,
            dias_validade_resgate=7,
            instrucoes="Abra o app do Inter e finalize a abertura da conta em até 7 dias para garantir o cashback.",
            prefixo_codigo="INTER", url_acesso=acesso("inter"),
        ),
        # texto provisório: o frontend só traz nome e oferta, confirmar com a Bulbe (instrucoes)
        Beneficio(
            id="ben_livelo_pontos", trilha="connect", parceiro_id="par_livelo",
            titulo="12 pontos por R$ 1,00",
            descricao="Acúmulo de pontos Livelo nas faturas Bulbe.",
            regras_de_uso="Pontuação creditada após o pagamento da fatura.",
            tipo="recorrente", regra_acesso="pedido_aprovado",
            validade_inicio=date(2026, 8, 1), validade_fim=None, ativo=True,
            dias_validade_resgate=7,
            instrucoes="Acesse o link para vincular sua conta Livelo. Os pontos são creditados após o pagamento da fatura.",
            prefixo_codigo="LIVELO", url_acesso=acesso("livelo"),
        ),
        # texto provisório: o frontend só traz nome e oferta, confirmar com a Bulbe
        Beneficio(
            id="ben_frossard_economia", trilha="connect", parceiro_id="par_frossard",
            titulo="Economia em dobro",
            descricao="Oferta exclusiva para clientes Bulbe no Canal do Frossard.",
            regras_de_uso="As condições da oferta são definidas pelo parceiro. Confira os detalhes ao acessar.",
            tipo="uso_unico", regra_acesso="livre",
            validade_inicio=date(2026, 8, 1), validade_fim=None, ativo=True,
            dias_validade_resgate=7,
            instrucoes="Acesse a oferta pelo link e siga as orientações do Canal do Frossard.",
            prefixo_codigo="FROSSARD", url_acesso=acesso("frossard"),
        ),
        # texto provisório: o frontend só traz nome e oferta, confirmar com a Bulbe
        Beneficio(
            id="ben_araujo_descontos", trilha="connect", parceiro_id="par_araujo",
            titulo="Descontos exclusivos",
            descricao="Desconto exclusivo para clientes Bulbe nas lojas Araújo.",
            regras_de_uso="As condições do desconto são definidas pelo parceiro. Confira os detalhes ao acessar.",
            tipo="uso_unico", regra_acesso="livre",
            validade_inicio=date(2026, 8, 1), validade_fim=None, ativo=True,
            dias_validade_resgate=7,
            instrucoes="Acesse a oferta pelo link e siga as orientações da Araújo.",
            prefixo_codigo="ARAUJO", url_acesso=acesso("araujo"),
        ),
    ]


def dicas() -> List[Dica]:
    atualizado = _dt(2026, 8, 20, 11, 0)
    return [
        Dica(
            tela="status-pedido", elemento="titulo-status",
            titulo="Como funciona o acompanhamento",
            rotulo_acessivel="Entender as etapas do pedido",
            atualizado_em=atualizado,
            blocos=[
                BlocoParagrafo("Seu pedido passa por 4 etapas até a liberação dos benefícios Bulbe."),
                BlocoLista([
                    ItemLista("Nossa equipe confere os dados enviados e verifica se está tudo certo com o pedido.", "Em análise pela Bulbe"),
                    ItemLista("Depois da primeira análise, o pedido é enviado para a Cemig.", "Enviado para a Cemig"),
                    ItemLista("A Cemig avalia e aprova o processo.", "Em análise pela Cemig"),
                    ItemLista("Após a aprovação, os benefícios ficam disponíveis no ecossistema Bulbe.", "Aprovado"),
                ]),
                BlocoParagrafo(
                    "O processo pode levar até 90 dias. Esse tempo depende da análise e do retorno de cada etapa.",
                    "Prazo do processo",
                ),
            ],
        ),
        Dica(
            tela="simular-desconto", elemento="titulo-simulacao",
            titulo="Como funciona o desconto",
            rotulo_acessivel="Como funciona a simulação",
            atualizado_em=atualizado,
            blocos=[
                BlocoParagrafo("O desconto é aplicado só sobre o valor da energia que você consumiu na conta da Cemig."),
                BlocoParagrafo("Outras cobranças, como taxa de iluminação pública, custo mínimo da conta e impostos (PIS e COFINS), não entram no desconto."),
                BlocoParagrafo("Como funciona na prática:"),
                BlocoLista([
                    ItemLista("Tiramos os impostos e a taxa de iluminação do valor da energia."),
                    ItemLista("Depois disso, aplicamos até 15% de desconto."),
                ], ordenada=True),
                BlocoParagrafo("Esse valor com desconto é a sua Tarifa Bulbe."),
            ],
        ),
    ]


def indicacoes() -> List[Indicacao]:
    return [
        Indicacao("ind_a10", "cli_3b9e1f42", "João Silva", "+5531977771111", "convertida", date(2026, 7, 2), _dt(2026, 7, 9)),
        Indicacao("ind_a11", "cli_3b9e1f42", "Marcos Pereira", "+5531977772222", "convertida", date(2026, 7, 20), _dt(2026, 7, 28)),
        Indicacao("ind_a12", "cli_3b9e1f42", "Carla Lima", "+5531977773333", "pendente", date(2026, 8, 11)),
    ]


def codigos_de_indicacao() -> Dict[str, str]:
    return {"cli_3b9e1f42": "ANA50"}


def notificacoes() -> List[Notificacao]:
    # Os textos repetem o que notificacao_service.notificar geraria; um teste garante a igualdade.
    return [
        Notificacao(
            "not_5a1c9e07", "cli_8d21c7a0", "mudanca_etapa_pedido", "Seu pedido avançou de etapa",
            "Seu pedido está agora em: Aprovado.", True, _dt(2026, 7, 14, 9, 0), "pedido", "ped_c41e88d2",
        ),
        Notificacao(
            "not_7d3b2f18", "cli_8d21c7a0", "fatura_emitida", "Sua fatura de outubro chegou",
            "Sua fatura de outubro já está disponível. Vence em 10 de novembro.", True, _dt(2026, 10, 12, 8, 0),
            "fatura", "fat_2c9f5a03",
        ),
        Notificacao(
            "not_c410aa7b", "cli_3b9e1f42", "pedido_criado", "Recebemos seu pedido",
            "Sua adesão foi recebida e a homologação junto à Cemig já começou. Acompanhe cada etapa pelo app.",
            False, _dt(2026, 6, 2, 9, 14), "pedido", "ped_7f3a9c21",
        ),
    ]
