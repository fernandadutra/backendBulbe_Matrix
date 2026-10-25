from datetime import timedelta

from app.core import config, relogio
from tests.conftest import CLIENTE_A, CLIENTE_B, cabecalho_de

CORPO = {"valor_fatura_centavos": 35000, "consumo_kwh": 249, "distribuidora": "CEMIG"}


def test_simulacao_anonima_numeros_da_spec(cliente_http):
    r = cliente_http.post("/api/v1/simulacoes", json=CORPO)
    assert r.status_code == 201
    c = r.json()
    assert c["id"].startswith("sim_") and len(c["id"]) == 12
    assert c["calculado_em"] == "2026-10-21T10:00:00-03:00"
    assert c["percentual_desconto"] == 0.15
    assert c["valor_sem_desconto_centavos"] == 35000
    assert c["valor_com_bulbe_centavos"] == 29750
    assert c["economia_mensal_centavos"] == 5250
    assert c["economia_anual_centavos"] == 63000
    assert c["rotulos"] == {
        "economia_mensal": "Você vai economizar por mês",
        "economia_anual": "Sua economia anual estimada",
        "valor_sem_desconto": "Sem desconto, tarifa cheia",
        "valor_com_bulbe": "Com Bulbe, até 15% desconto",
    }
    assert c["memoria_calculo"] == {
        "consumo_total_kwh": 249,
        "linhas": [{
            "fonte": "Bulbe Energia", "consumo_kwh": 249, "valor_centavos": 35000,
            "valor_com_desconto_centavos": 29750, "possui_desconto": True,
        }],
        "subtotal": {"rotulo": "Subtotal", "consumo_kwh": 249, "valor_centavos": 35000},
        "observacao": "A taxa de economia é de até 15% e varia conforme o frete da distribuidora.",
    }


def test_simulacao_so_com_valor_usa_cemig_e_consumo_nulo(cliente_http):
    r = cliente_http.post("/api/v1/simulacoes", json={"valor_fatura_centavos": 5001})
    assert r.status_code == 201
    assert r.json()["memoria_calculo"]["consumo_total_kwh"] is None
    # 5001 * 15 / 100 = 750,15 arredonda para 750
    assert r.json()["economia_mensal_centavos"] == 750


def test_arredondamento_meio_para_cima(cliente_http):
    # 5010 * 15 / 100 = 751,5 sobe para 752
    r = cliente_http.post("/api/v1/simulacoes", json={"valor_fatura_centavos": 5010})
    assert r.json()["economia_mensal_centavos"] == 752


def test_limites_da_faixa_aceitos(cliente_http):
    for valor in (5000, 500000):
        assert cliente_http.post("/api/v1/simulacoes", json={"valor_fatura_centavos": valor}).status_code == 201


def test_faixa_invalida_422(cliente_http):
    for valor in (4999, 500001):
        r = cliente_http.post("/api/v1/simulacoes", json={"valor_fatura_centavos": valor})
        assert r.status_code == 422
        erro = r.json()["erro"]
        assert erro["codigo"] == "CONSUMO_FORA_DA_FAIXA"
        assert erro["mensagem"] == "O valor da fatura deve estar entre R$ 50,00 e R$ 5.000,00."
        assert erro["detalhes"][0]["campo"] == "valor_fatura_centavos"


def test_consumo_zero_ou_negativo_422(cliente_http):
    for consumo in (0, -3):
        r = cliente_http.post("/api/v1/simulacoes", json={**CORPO, "consumo_kwh": consumo})
        assert r.status_code == 422
        assert r.json()["erro"]["codigo"] == "CONSUMO_FORA_DA_FAIXA"
        assert r.json()["erro"]["detalhes"][0]["campo"] == "consumo_kwh"


def test_distribuidora_nao_atendida_422_e_minuscula_aceita(cliente_http):
    r = cliente_http.post("/api/v1/simulacoes", json={**CORPO, "distribuidora": "Enel"})
    assert r.status_code == 422
    assert r.json()["erro"]["codigo"] == "DISTRIBUIDORA_NAO_ATENDIDA"
    assert r.json()["erro"]["mensagem"] == "Por enquanto a Bulbe atende apenas clientes da CEMIG."
    assert cliente_http.post("/api/v1/simulacoes", json={**CORPO, "distribuidora": "cemig"}).status_code == 201


def test_distribuidora_vazia_ou_so_espacos_422(cliente_http):
    for valor in ("", "   "):
        r = cliente_http.post("/api/v1/simulacoes", json={**CORPO, "distribuidora": valor})
        assert r.status_code == 422
        assert r.json()["erro"]["codigo"] == "DISTRIBUIDORA_NAO_ATENDIDA"


def test_distribuidora_ausente_usa_cemig(cliente_http):
    corpo = {"valor_fatura_centavos": 35000}
    r = cliente_http.post("/api/v1/simulacoes", json=corpo)
    assert r.status_code == 201


def test_corpo_invalido_400_no_envelope(cliente_http):
    for corpo in ({}, {"valor_fatura_centavos": "abc"}, {"valor_fatura_centavos": "35000"}, {"valor_fatura_centavos": 350.5}, {**CORPO, "consumo_kwh": "x"}):
        r = cliente_http.post("/api/v1/simulacoes", json=corpo)
        assert r.status_code == 400, corpo
        erro = r.json()["erro"]
        assert erro["codigo"] == "CORPO_INVALIDO"
        assert erro["detalhes"] and {"campo", "problema"} == set(erro["detalhes"][0])


def test_json_malformado_400(cliente_http):
    r = cliente_http.post("/api/v1/simulacoes", content="{nao e json", headers={"Content-Type": "application/json"})
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "CORPO_INVALIDO"


def test_token_invalido_no_post_401(cliente_http):
    r = cliente_http.post("/api/v1/simulacoes", json=CORPO, headers={"Authorization": "Bearer lixo"})
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_INVALIDO"


def test_historico_so_traz_simulacoes_da_logada(cliente_http):
    h = cabecalho_de(CLIENTE_A)
    cliente_http.post("/api/v1/simulacoes", json=CORPO)  # anônima
    logada = cliente_http.post("/api/v1/simulacoes", json={"valor_fatura_centavos": 20000}, headers=h).json()
    cliente_http.post("/api/v1/simulacoes", json=CORPO, headers=cabecalho_de(CLIENTE_B))

    r = cliente_http.get("/api/v1/simulacoes", headers=h)
    assert r.status_code == 200
    assert r.json() == {
        "dados": [{
            "id": logada["id"], "calculado_em": "2026-10-21T10:00:00-03:00",
            "valor_sem_desconto_centavos": 20000, "economia_mensal_centavos": 3000,
        }],
        "pagina": 1, "limite": 20, "total": 1,
    }


def test_historico_mais_recentes_primeiro_e_paginado(cliente_http):
    h = cabecalho_de(CLIENTE_A)
    ids = []
    for minuto in range(3):
        relogio.definir_relogio(lambda m=minuto: _em(m))
        ids.append(cliente_http.post("/api/v1/simulacoes", json=CORPO, headers=h).json()["id"])
    r = cliente_http.get("/api/v1/simulacoes?limite=2", headers=h).json()
    assert [s["id"] for s in r["dados"]] == [ids[2], ids[1]]
    assert r["total"] == 3
    pagina2 = cliente_http.get("/api/v1/simulacoes?limite=2&pagina=2", headers=h).json()
    assert [s["id"] for s in pagina2["dados"]] == [ids[0]]


def _em(minutos):
    from datetime import datetime, timedelta
    return datetime(2026, 10, 21, 10, 0, tzinfo=relogio.FUSO) + timedelta(minutes=minutos)


def test_historico_sem_token_401_e_paginacao_invalida_400(cliente_http):
    assert cliente_http.get("/api/v1/simulacoes").status_code == 401
    assert cliente_http.get("/api/v1/simulacoes?limite=500", headers=cabecalho_de(CLIENTE_A)).status_code == 400


def test_obter_simulacao_da_propria_cliente(cliente_http):
    h = cabecalho_de(CLIENTE_A)
    criada = cliente_http.post("/api/v1/simulacoes", json=CORPO, headers=h).json()
    r = cliente_http.get(f"/api/v1/simulacoes/{criada['id']}", headers=h)
    assert r.status_code == 200
    assert r.json() == criada


def test_obter_simulacao_sem_token_401(cliente_http):
    criada = cliente_http.post("/api/v1/simulacoes", json=CORPO).json()
    assert cliente_http.get(f"/api/v1/simulacoes/{criada['id']}").status_code == 401


def test_obter_simulacao_de_outro_anonima_ou_inexistente_404(cliente_http):
    de_a = cliente_http.post("/api/v1/simulacoes", json=CORPO, headers=cabecalho_de(CLIENTE_A)).json()
    anonima = cliente_http.post("/api/v1/simulacoes", json=CORPO).json()
    h = cabecalho_de(CLIENTE_B)
    for sim_id in (de_a["id"], anonima["id"], "sim_00000000"):
        r = cliente_http.get(f"/api/v1/simulacoes/{sim_id}", headers=h)
        assert r.status_code == 404
        assert r.json()["erro"]["codigo"] == "SIMULACAO_NAO_ENCONTRADA"


def test_limite_de_requisicoes_429(cliente_http, monkeypatch):
    monkeypatch.setattr(config, "LIMITE_SIMULACOES_POR_MINUTO", 3)
    for _ in range(3):
        assert cliente_http.post("/api/v1/simulacoes", json=CORPO).status_code == 201
    r = cliente_http.post("/api/v1/simulacoes", json=CORPO)
    assert r.status_code == 429
    assert r.json()["erro"]["codigo"] == "LIMITE_DE_REQUISICOES"
    assert int(r.headers["retry-after"]) >= 1
    # Passada a janela de 60s, volta a aceitar.
    relogio.definir_relogio(lambda: _em(2))
    assert cliente_http.post("/api/v1/simulacoes", json=CORPO).status_code == 201


def test_limite_vale_antes_da_validacao(cliente_http, monkeypatch):
    monkeypatch.setattr(config, "LIMITE_SIMULACOES_POR_MINUTO", 1)
    cliente_http.post("/api/v1/simulacoes", json=CORPO)
    assert cliente_http.post("/api/v1/simulacoes", json={}).status_code == 429


def test_limite_libera_depois_de_60s_e_descarta_ip_ocioso(cliente_http, monkeypatch):
    from app.core import limite_requisicoes
    monkeypatch.setattr(config, "LIMITE_SIMULACOES_POR_MINUTO", 1)
    limite_requisicoes._acessos["1.2.3.4"].append(relogio.agora().timestamp())
    assert cliente_http.post("/api/v1/simulacoes", json=CORPO).status_code == 201
    assert cliente_http.post("/api/v1/simulacoes", json=CORPO).status_code == 429
    assert set(limite_requisicoes._acessos) == {"1.2.3.4", "testclient"}
    relogio.definir_relogio(lambda: _em(1) + timedelta(seconds=1))
    assert cliente_http.post("/api/v1/simulacoes", json=CORPO).status_code == 201
    assert set(limite_requisicoes._acessos) == {"testclient"}
