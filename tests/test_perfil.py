from tests.conftest import CLIENTE_A, CLIENTE_B, PEDIDO_A, PEDIDO_B, cabecalho_de


def test_perfil_no_formato_do_contrato(cliente_http):
    r = cliente_http.get("/api/v1/perfil", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 200
    assert r.json() == {
        "id": CLIENTE_A,
        "nome": "Ana Souza",
        "email": "ana@exemplo.com.br",
        "telefone": "+5531999998888",
        "instalacoes": [
            {"numero": "3013588579", "distribuidora": "CEMIG", "pedido_id": PEDIDO_A, "principal": True},
        ],
    }


def test_perfil_mostra_so_a_instalacao_do_cliente(cliente_http):
    r = cliente_http.get("/api/v1/perfil", headers=cabecalho_de(CLIENTE_B))
    assert [i["pedido_id"] for i in r.json()["instalacoes"]] == [PEDIDO_B]


def test_perfil_sem_token_401(cliente_http):
    r = cliente_http.get("/api/v1/perfil")
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_AUSENTE"


def test_perfil_nao_expoe_senha(cliente_http):
    r = cliente_http.get("/api/v1/perfil", headers=cabecalho_de(CLIENTE_A))
    assert "senha" not in r.text
    assert "cpf" not in r.json()
