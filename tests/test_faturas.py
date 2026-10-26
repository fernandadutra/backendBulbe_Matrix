from datetime import date, datetime

from app.core import relogio
from app.core.estado import repositorios
from app.models.cliente import Cliente
from app.models.fatura import Fatura
from app.models.pedido import Pedido
from tests.conftest import CLIENTE_A, CLIENTE_B, EMAIL_B, PEDIDO_B, SENHA_DEV, cabecalho_de

FATURA_AGO = "fat_08a2ce31"
FATURA_SET = "fat_1b7d4e92"
FATURA_OUT = "fat_2c9f5a03"
INSTALACAO_B = "3013591122"
MOTIVO_FATURA = "Disponível para clientes com fatura Bulbe ativa."


def _get(cliente_http, caminho, cliente_id=CLIENTE_B, **params):
    return cliente_http.get(caminho, headers=cabecalho_de(cliente_id), params=params)


def _adicionar_fatura(competencia, vencimento, consumo=250, situacao="aberta", cliente_id=CLIENTE_B, pedido_id=PEDIDO_B):
    fatura = Fatura(
        id=f"fat_teste_{competencia}", cliente_id=cliente_id, pedido_id=pedido_id, competencia=competencia,
        vencimento=vencimento, valor_centavos=30000, economia_centavos=5000, consumo_kwh=consumo,
        situacao=situacao, linha_digitavel="001", url_pdf="https://cdn.bulbe.com.br/faturas/teste.pdf",
    )
    repositorios.pedidos._faturas.append(fatura)
    return fatura


def _cliente_novo(cliente_id, situacao_pedido=None):
    repositorios.clientes.salvar(Cliente(id=cliente_id, nome="Novo Cliente"))
    if situacao_pedido:
        repositorios.pedidos.salvar(Pedido(
            id=f"ped_{cliente_id}", cliente_id=cliente_id, numero_instalacao="9990001111", distribuidora="CEMIG",
            situacao=situacao_pedido, criado_em=datetime(2026, 5, 1, 9, 0, tzinfo=relogio.FUSO),
            previsao_proxima_atualizacao=None,
        ))


def _avancar_para(dia):
    momento = datetime(dia.year, dia.month, dia.day, 10, 0, tzinfo=relogio.FUSO)
    relogio.definir_relogio(lambda: momento)


# GET /faturas

def test_faturas_do_bruno_no_formato_do_contrato(cliente_http):
    r = _get(cliente_http, "/api/v1/faturas")
    assert r.status_code == 200
    corpo = r.json()
    assert [f["id"] for f in corpo["dados"]] == [FATURA_OUT, FATURA_SET, FATURA_AGO]
    assert corpo["dados"][0] == {
        "id": FATURA_OUT, "competencia": "2026-10", "vencimento": "2026-11-10", "valor_centavos": 30600,
        "economia_centavos": 5400, "situacao": "aberta",
        "linha_digitavel": corpo["dados"][0]["linha_digitavel"],
        "url_pdf": f"https://cdn.bulbe.com.br/faturas/{FATURA_OUT}.pdf",
    }
    assert (corpo["pagina"], corpo["limite"], corpo["total"]) == (1, 20, 3)
    assert corpo["estado_vazio"] is None


def test_faturas_filtra_por_situacao(cliente_http):
    assert _get(cliente_http, "/api/v1/faturas", situacao="paga").json()["total"] == 2
    assert [f["id"] for f in _get(cliente_http, "/api/v1/faturas", situacao="aberta").json()["dados"]] == [FATURA_OUT]


def test_faturas_filtro_sem_resultado_nao_traz_estado_vazio(cliente_http):
    corpo = _get(cliente_http, "/api/v1/faturas", situacao="vencida").json()
    assert corpo["dados"] == []
    assert corpo["total"] == 0
    assert corpo["estado_vazio"] is None


def test_faturas_situacao_invalida_400(cliente_http):
    r = _get(cliente_http, "/api/v1/faturas", situacao="xyz")
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "PARAMETRO_INVALIDO"
    assert r.json()["erro"]["detalhes"][0]["campo"] == "situacao"


def test_faturas_paginacao(cliente_http):
    corpo = _get(cliente_http, "/api/v1/faturas", limite=2, pagina=2).json()
    assert [f["id"] for f in corpo["dados"]] == [FATURA_AGO]
    assert (corpo["pagina"], corpo["limite"], corpo["total"]) == (2, 2, 3)


def test_faturas_aberta_vencida_aparece_como_vencida(cliente_http):
    _avancar_para(date(2026, 11, 11))
    corpo = _get(cliente_http, "/api/v1/faturas", situacao="vencida").json()
    assert [f["id"] for f in corpo["dados"]] == [FATURA_OUT]
    assert corpo["dados"][0]["situacao"] == "vencida"
    assert _get(cliente_http, "/api/v1/faturas", situacao="aberta").json()["total"] == 0


def test_faturas_da_ana_aguardando_homologacao(cliente_http):
    r = _get(cliente_http, "/api/v1/faturas", CLIENTE_A)
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["dados"] == []
    assert corpo["total"] == 0
    assert corpo["estado_vazio"] == {
        "chave": "aguardando_homologacao",
        "titulo": "Oops... Não encontrei nenhuma fatura.",
        "mensagem": "Seu pedido ainda está em análise pela Cemig. A primeira fatura chega depois da aprovação.",
        "acao_sugerida": {"rotulo": "Ver status do pedido", "destino": "status-pedido"},
    }


def test_faturas_pedido_aprovado_sem_fatura(cliente_http):
    _cliente_novo("cli_aprovado", "aprovado")
    estado = _get(cliente_http, "/api/v1/faturas", "cli_aprovado").json()["estado_vazio"]
    assert estado["chave"] == "homologado_sem_fatura"
    assert estado["acao_sugerida"] is None


def test_faturas_cliente_sem_pedido(cliente_http):
    _cliente_novo("cli_sem_pedido")
    estado = _get(cliente_http, "/api/v1/faturas", "cli_sem_pedido").json()["estado_vazio"]
    assert estado["chave"] == "sem_instalacao"
    assert estado["acao_sugerida"] == {"rotulo": "Simular economia", "destino": "simular-desconto"}


def test_faturas_so_pedido_reprovado_conta_como_sem_instalacao(cliente_http):
    _cliente_novo("cli_reprovado", "reprovado")
    assert _get(cliente_http, "/api/v1/faturas", "cli_reprovado").json()["estado_vazio"]["chave"] == "sem_instalacao"


def test_faturas_sem_token_401(cliente_http):
    r = cliente_http.get("/api/v1/faturas")
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_AUSENTE"


# GET /faturas/{id}

def test_fatura_por_id_no_formato_do_item(cliente_http):
    r = _get(cliente_http, f"/api/v1/faturas/{FATURA_AGO}")
    assert r.status_code == 200
    assert r.json() == _get(cliente_http, "/api/v1/faturas", situacao="paga").json()["dados"][1]
    assert r.json()["situacao"] == "paga"


def test_fatura_de_outro_cliente_404(cliente_http):
    r = _get(cliente_http, f"/api/v1/faturas/{FATURA_AGO}", CLIENTE_A)
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "FATURA_NAO_ENCONTRADA"


def test_fatura_inexistente_404(cliente_http):
    r = _get(cliente_http, "/api/v1/faturas/fat_nao_existe")
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "FATURA_NAO_ENCONTRADA"


def test_fatura_por_id_aberta_vencida(cliente_http):
    _avancar_para(date(2026, 11, 11))
    assert _get(cliente_http, f"/api/v1/faturas/{FATURA_OUT}").json()["situacao"] == "vencida"


def test_fatura_por_id_sem_token_401(cliente_http):
    assert cliente_http.get(f"/api/v1/faturas/{FATURA_AGO}").status_code == 401


# GET /consumo

def test_consumo_mensal_do_bruno(cliente_http):
    r = _get(cliente_http, "/api/v1/consumo")
    assert r.status_code == 200
    assert r.json() == {
        "instalacao": INSTALACAO_B,
        "granularidade": "mensal",
        "serie": [
            {"competencia": "2026-08", "consumo_kwh": 241, "valor_pago_centavos": 28800, "economia_centavos": 5080},
            {"competencia": "2026-09", "consumo_kwh": 249, "valor_pago_centavos": 29750, "economia_centavos": 5250},
            {"competencia": "2026-10", "consumo_kwh": 255, "valor_pago_centavos": 30600, "economia_centavos": 5400},
        ],
        "totais": {"economia_acumulada_centavos": 15730, "consumo_medio_kwh": 248},
        "estado_vazio": None,
    }


def test_consumo_filtra_um_mes(cliente_http):
    corpo = _get(cliente_http, "/api/v1/consumo", de="2026-09", ate="2026-09").json()
    assert [p["competencia"] for p in corpo["serie"]] == ["2026-09"]
    assert corpo["totais"] == {"economia_acumulada_centavos": 5250, "consumo_medio_kwh": 249}


def test_consumo_anual_soma_os_valores(cliente_http):
    corpo = _get(cliente_http, "/api/v1/consumo", granularidade="anual").json()
    assert corpo["granularidade"] == "anual"
    assert corpo["serie"] == [
        {"competencia": "2026", "consumo_kwh": 745, "valor_pago_centavos": 89150, "economia_centavos": 15730}
    ]
    assert corpo["totais"]["consumo_medio_kwh"] == 248


def test_consumo_media_arredonda_para_o_inteiro_mais_proximo(cliente_http):
    _adicionar_fatura("2026-11", date(2026, 12, 10), consumo=250)
    # 995 kWh em 4 faturas: 248,75 arredonda para 249.
    assert _get(cliente_http, "/api/v1/consumo").json()["totais"]["consumo_medio_kwh"] == 249


def test_consumo_instalacao_informada(cliente_http):
    corpo = _get(cliente_http, "/api/v1/consumo", instalacao=INSTALACAO_B).json()
    assert corpo["instalacao"] == INSTALACAO_B
    assert len(corpo["serie"]) == 3


def test_consumo_instalacao_de_outro_cliente_400(cliente_http):
    r = _get(cliente_http, "/api/v1/consumo", instalacao="3013588579")
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "PARAMETRO_INVALIDO"
    assert r.json()["erro"]["detalhes"][0]["campo"] == "instalacao"


def test_consumo_competencia_invalida_400(cliente_http):
    r = _get(cliente_http, "/api/v1/consumo", de="2026-13")
    assert r.status_code == 400
    assert r.json()["erro"]["detalhes"][0]["campo"] == "de"
    assert _get(cliente_http, "/api/v1/consumo", ate="outubro").status_code == 400


def test_consumo_de_depois_de_ate_400(cliente_http):
    r = _get(cliente_http, "/api/v1/consumo", de="2026-10", ate="2026-08")
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "PARAMETRO_INVALIDO"


def test_consumo_granularidade_invalida_400(cliente_http):
    r = _get(cliente_http, "/api/v1/consumo", granularidade="semanal")
    assert r.status_code == 400
    assert r.json()["erro"]["detalhes"][0]["campo"] == "granularidade"


def test_consumo_da_ana_serie_vazia_com_estado_vazio(cliente_http):
    corpo = _get(cliente_http, "/api/v1/consumo", CLIENTE_A).json()
    assert corpo["instalacao"] == "3013588579"
    assert corpo["serie"] == []
    assert corpo["totais"] == {"economia_acumulada_centavos": 0, "consumo_medio_kwh": 0}
    assert corpo["estado_vazio"]["chave"] == "aguardando_homologacao"


def test_consumo_cliente_sem_pedido(cliente_http):
    _cliente_novo("cli_sem_pedido")
    corpo = _get(cliente_http, "/api/v1/consumo", "cli_sem_pedido").json()
    assert corpo["instalacao"] is None
    assert corpo["estado_vazio"]["chave"] == "sem_instalacao"


def test_consumo_sem_token_401(cliente_http):
    assert cliente_http.get("/api/v1/consumo").status_code == 401


# Regra fatura_ativa e login

def test_bruno_tem_trilha_experience_desbloqueada(cliente_http):
    dados = _get(cliente_http, "/api/v1/trilhas").json()["dados"]
    experience = next(t for t in dados if t["chave"] == "experience")
    assert experience["desbloqueada"] is True
    assert experience["motivo_bloqueio"] is None


def test_fatura_vencida_bloqueia_a_trilha_experience(cliente_http):
    _adicionar_fatura("2026-07", date(2026, 8, 10))
    dados = _get(cliente_http, "/api/v1/trilhas").json()["dados"]
    experience = next(t for t in dados if t["chave"] == "experience")
    assert experience["desbloqueada"] is False
    assert experience["motivo_bloqueio"] == MOTIVO_FATURA


def test_login_do_bruno_informa_fatura_emitida(cliente_http):
    r = cliente_http.post("/api/v1/sessoes", json={"identificador": EMAIL_B, "senha": SENHA_DEV})
    assert r.status_code == 201
    assert r.json()["cliente"]["possui_fatura_emitida"] is True
