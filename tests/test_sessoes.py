from datetime import timedelta

from app.core import config, relogio
from tests.conftest import AGORA_CONGELADA, CPF_A, EMAIL_A, EMAIL_B, SENHA_DEV, cabecalho_de, CLIENTE_A, CLIENTE_B


def _login(cliente_http, identificador=EMAIL_A, senha=SENHA_DEV):
    return cliente_http.post("/api/v1/sessoes", json={"identificador": identificador, "senha": senha})


def _renovar(cliente_http, token):
    return cliente_http.post("/api/v1/sessoes/renovacao", json={"token_renovacao": token})


def _encerrar(cliente_http, token, cabecalho):
    return cliente_http.request("DELETE", "/api/v1/sessoes", json={"token_renovacao": token}, headers=cabecalho)


def test_login_201_no_formato_do_contrato(cliente_http):
    r = _login(cliente_http)
    assert r.status_code == 201
    c = r.json()
    assert c["tipo_token"] == "Bearer"
    assert c["expira_em_segundos"] == 900
    assert c["token_renovacao"].startswith("trn_")
    assert c["cliente"] == {
        "id": CLIENTE_A,
        "nome": "Ana Souza",
        "possui_pedido_em_andamento": True,
        "possui_fatura_emitida": False,
    }
    pedidos = cliente_http.get("/api/v1/pedidos", headers={"Authorization": f"Bearer {c['token_acesso']}"})
    assert pedidos.status_code == 200


def test_login_por_cpf_com_e_sem_mascara(cliente_http):
    assert _login(cliente_http, CPF_A).status_code == 201
    assert _login(cliente_http, "529.982.247-25").status_code == 201


def test_login_com_email_em_maiusculas(cliente_http):
    assert _login(cliente_http, "ANA@Exemplo.com.br").status_code == 201


def test_pedido_em_andamento_so_para_quem_tem(cliente_http):
    assert _login(cliente_http, EMAIL_B).json()["cliente"]["possui_pedido_em_andamento"] is False


def test_credencial_invalida_tem_a_mesma_resposta(cliente_http):
    senha_errada = _login(cliente_http, senha="errada")
    inexistente = _login(cliente_http, "ninguem@exemplo.com.br")
    assert senha_errada.status_code == inexistente.status_code == 401
    assert senha_errada.json() == inexistente.json()
    assert senha_errada.json()["erro"]["codigo"] == "CREDENCIAIS_INVALIDAS"


def test_corpo_sem_senha_400(cliente_http):
    r = cliente_http.post("/api/v1/sessoes", json={"identificador": EMAIL_A})
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "CORPO_INVALIDO"


def test_sexta_tentativa_recebe_429_mesmo_com_senha_correta(cliente_http):
    for _ in range(5):
        assert _login(cliente_http, senha="errada").status_code == 401
    r = _login(cliente_http)
    assert r.status_code == 429
    assert r.json()["erro"]["codigo"] == "LIMITE_DE_TENTATIVAS"
    assert int(r.headers["retry-after"]) >= 1


def test_login_volta_depois_da_janela_de_falhas(cliente_http):
    for _ in range(5):
        _login(cliente_http, senha="errada")
    relogio.definir_relogio(lambda: AGORA_CONGELADA + timedelta(minutes=15))
    assert _login(cliente_http).status_code == 201


def test_login_bem_sucedido_zera_as_falhas(cliente_http):
    for _ in range(4):
        _login(cliente_http, senha="errada")
    assert _login(cliente_http).status_code == 201
    for _ in range(4):
        assert _login(cliente_http, senha="errada").status_code == 401


def test_falhas_de_um_identificador_nao_bloqueiam_outro(cliente_http):
    for _ in range(5):
        _login(cliente_http, senha="errada")
    assert _login(cliente_http, EMAIL_B).status_code == 201


def test_limite_de_login_por_ip_429(cliente_http, monkeypatch):
    monkeypatch.setattr(config, "LIMITE_LOGIN_POR_IP_POR_MINUTO", 2)
    for _ in range(2):
        assert _login(cliente_http).status_code == 201
    r = _login(cliente_http)
    assert r.status_code == 429
    assert r.json()["erro"]["codigo"] == "LIMITE_DE_TENTATIVAS"
    assert int(r.headers["retry-after"]) >= 1
    relogio.definir_relogio(lambda: AGORA_CONGELADA + timedelta(minutes=2))
    assert _login(cliente_http).status_code == 201


def test_limite_de_login_descarta_ip_e_identificador_ociosos(cliente_http):
    from app.core import limite_requisicoes
    limite_requisicoes._acessos_login["1.2.3.4"].append(relogio.agora().timestamp())
    limite_requisicoes._falhas_login["fulano@exemplo.com.br"].append(relogio.agora().timestamp())
    relogio.definir_relogio(lambda: AGORA_CONGELADA + timedelta(minutes=16))
    _login(cliente_http, senha="errada")
    assert set(limite_requisicoes._acessos_login) == {"testclient"}
    assert set(limite_requisicoes._falhas_login) == {EMAIL_A}


def test_renovacao_201_com_token_novo(cliente_http):
    antigo = _login(cliente_http).json()["token_renovacao"]
    r = _renovar(cliente_http, antigo)
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["token_renovacao"].startswith("trn_") and corpo["token_renovacao"] != antigo
    assert corpo["expira_em_segundos"] == 900
    assert corpo["cliente"]["id"] == CLIENTE_A


def test_reuso_do_token_antigo_revoga_a_sessao(cliente_http):
    antigo = _login(cliente_http).json()["token_renovacao"]
    novo = _renovar(cliente_http, antigo).json()["token_renovacao"]
    r = _renovar(cliente_http, antigo)
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_RENOVACAO_INVALIDO"
    assert _renovar(cliente_http, novo).status_code == 401


def test_renovacao_com_token_inexistente_401(cliente_http):
    r = _renovar(cliente_http, "trn_naoexiste")
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_RENOVACAO_INVALIDO"


def test_renovacao_com_token_expirado_401(cliente_http):
    token = _login(cliente_http).json()["token_renovacao"]
    relogio.definir_relogio(lambda: AGORA_CONGELADA + timedelta(days=31))
    assert _renovar(cliente_http, token).status_code == 401


def test_renovacao_sem_corpo_400(cliente_http):
    r = cliente_http.post("/api/v1/sessoes/renovacao", json={})
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "CORPO_INVALIDO"


def test_encerrar_204_e_invalida_a_renovacao(cliente_http):
    corpo = _login(cliente_http).json()
    cabecalho = {"Authorization": f"Bearer {corpo['token_acesso']}"}
    assert _encerrar(cliente_http, corpo["token_renovacao"], cabecalho).status_code == 204
    assert _renovar(cliente_http, corpo["token_renovacao"]).status_code == 401


def test_encerrar_sem_bearer_401(cliente_http):
    r = cliente_http.request("DELETE", "/api/v1/sessoes", json={"token_renovacao": "trn_x"})
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_AUSENTE"


def test_encerrar_com_token_de_outro_cliente_nao_revoga(cliente_http):
    da_ana = _login(cliente_http).json()["token_renovacao"]
    r = _encerrar(cliente_http, da_ana, cabecalho_de(CLIENTE_B))
    assert r.status_code == 204
    assert _renovar(cliente_http, da_ana).status_code == 201
