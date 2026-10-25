from datetime import datetime, timedelta

import jwt

from app.core import relogio
from app.main import app
from app.models.pedido import Etapa
from app.services.integracao_cemig import IntegracaoIndisponivel, obter_integracao_cemig
from tests.conftest import CLIENTE_A, CLIENTE_B, PEDIDO_A, PEDIDO_B, cabecalho_de


class IntegracaoFalsa:
    def __init__(self, etapas=None, indisponivel=False, erro=None):
        self.etapas, self.indisponivel, self.erro = etapas, indisponivel, erro

    def consultar(self, pedido):
        if self.erro is not None:
            raise self.erro
        if self.indisponivel:
            raise IntegracaoIndisponivel()
        return self.etapas


def usar_integracao(integracao):
    app.dependency_overrides[obter_integracao_cemig] = lambda: integracao


def test_lista_pedidos_formato_da_spec(cliente_http):
    r = cliente_http.get("/api/v1/pedidos", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 200
    assert r.json() == {
        "dados": [{
            "id": PEDIDO_A, "numero_instalacao": "3013588579", "distribuidora": "CEMIG",
            "situacao": "em_andamento", "etapa_atual_ordem": 1,
            "etapa_atual_nome": "Em análise pela Bulbe", "criado_em": "2026-06-02T09:14:00-03:00",
        }],
        "pagina": 1, "limite": 20, "total": 1,
    }


def test_lista_nunca_traz_pedido_de_outro_cliente(cliente_http):
    r = cliente_http.get("/api/v1/pedidos", headers=cabecalho_de(CLIENTE_B))
    assert [p["id"] for p in r.json()["dados"]] == [PEDIDO_B]
    assert r.json()["dados"][0]["etapa_atual_ordem"] == 4


def test_lista_sem_token_401(cliente_http):
    r = cliente_http.get("/api/v1/pedidos")
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_AUSENTE"
    assert r.headers["www-authenticate"] == "Bearer"


def test_lista_token_invalido_401(cliente_http):
    r = cliente_http.get("/api/v1/pedidos", headers={"Authorization": "Bearer lixo"})
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_INVALIDO"


def test_lista_token_expirado_401(cliente_http):
    r = cliente_http.get("/api/v1/pedidos", headers=cabecalho_de(CLIENTE_A, minutos=-5))
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_INVALIDO"


def test_lista_token_de_cliente_inexistente_401(cliente_http):
    r = cliente_http.get("/api/v1/pedidos", headers=cabecalho_de("cli_00000000"))
    assert r.status_code == 401


def test_filtro_situacao_valido(cliente_http):
    h = cabecalho_de(CLIENTE_A)
    assert cliente_http.get("/api/v1/pedidos?situacao=em_andamento", headers=h).json()["total"] == 1
    assert cliente_http.get("/api/v1/pedidos?situacao=aprovado", headers=h).json()["total"] == 0


def test_filtro_situacao_invalido_400(cliente_http):
    r = cliente_http.get("/api/v1/pedidos?situacao=xyz", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 400
    erro = r.json()["erro"]
    assert erro["codigo"] == "PARAMETRO_INVALIDO"
    assert erro["detalhes"][0]["campo"] == "situacao"


def test_paginacao_invalida_400(cliente_http):
    h = cabecalho_de(CLIENTE_A)
    for consulta in ("pagina=0", "limite=0", "limite=101", "pagina=abc"):
        r = cliente_http.get(f"/api/v1/pedidos?{consulta}", headers=h)
        assert r.status_code == 400, consulta
        assert r.json()["erro"]["codigo"] == "PARAMETRO_INVALIDO"
        assert r.json()["erro"]["detalhes"]


def test_status_formato_da_spec(cliente_http):
    r = cliente_http.get(f"/api/v1/pedidos/{PEDIDO_A}/status", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 200
    corpo = r.json()
    assert list(corpo) == [
        "pedido_id", "numero_instalacao", "situacao", "etapa_atual", "etapas",
        "previsao_proxima_atualizacao", "prazo_estimado_dias", "consultado_em", "dado_desatualizado",
    ]
    assert corpo["etapa_atual"] == {
        "ordem": 1, "chave": "analise_bulbe", "nome": "Em análise pela Bulbe",
        "descricao": "Sua solicitação está sendo analisada pela equipe Bulbe.",
        "situacao": "em_andamento", "iniciada_em": "2026-06-02T09:14:00-03:00",
    }
    assert [e["chave"] for e in corpo["etapas"]] == ["analise_bulbe", "enviado_cemig", "analise_cemig", "aprovado"]
    assert [e["situacao"] for e in corpo["etapas"]] == ["em_andamento", "pendente", "pendente", "pendente"]
    assert corpo["etapas"][0] == {
        "ordem": 1, "chave": "analise_bulbe", "nome": "Em análise pela Bulbe",
        "descricao": "Sua solicitação está sendo analisada pela equipe Bulbe.",
        "situacao": "em_andamento", "concluida_em": None,
    }
    assert corpo["previsao_proxima_atualizacao"] == "2026-09-15"
    assert corpo["prazo_estimado_dias"] == {"minimo": 90, "maximo": 120}
    assert corpo["consultado_em"] == "2026-08-23T14:30:00-03:00"
    assert corpo["dado_desatualizado"] is False


def test_status_pedido_aprovado_etapa_atual_e_a_ultima(cliente_http):
    corpo = cliente_http.get(f"/api/v1/pedidos/{PEDIDO_B}/status", headers=cabecalho_de(CLIENTE_B)).json()
    assert corpo["situacao"] == "aprovado"
    assert corpo["etapa_atual"]["ordem"] == 4
    assert corpo["etapa_atual"]["situacao"] == "concluida"
    assert all(e["situacao"] == "concluida" and e["concluida_em"] for e in corpo["etapas"])


def test_status_sem_token_401(cliente_http):
    assert cliente_http.get(f"/api/v1/pedidos/{PEDIDO_A}/status").status_code == 401


def test_status_pedido_de_outro_cliente_e_inexistente_dao_a_mesma_resposta(cliente_http):
    h = cabecalho_de(CLIENTE_B)
    de_outro = cliente_http.get(f"/api/v1/pedidos/{PEDIDO_A}/status", headers=h)
    inexistente = cliente_http.get("/api/v1/pedidos/ped_00000000/status", headers=h)
    assert de_outro.status_code == inexistente.status_code == 404
    assert de_outro.json() == inexistente.json()
    assert de_outro.json()["erro"]["codigo"] == "PEDIDO_NAO_ENCONTRADO"


def test_status_integracao_devolve_dados_e_salva_consulta(cliente_http):
    novas = [
        Etapa(1, "analise_bulbe", "Em análise pela Bulbe", "d1", "concluida", concluida_em=datetime(2026, 10, 1, tzinfo=relogio.FUSO)),
        Etapa(2, "enviado_cemig", "Enviado para Cemig", "d2", "em_andamento", iniciada_em=datetime(2026, 10, 1, tzinfo=relogio.FUSO)),
        Etapa(3, "analise_cemig", "Em análise pela Cemig", "d3", "pendente"),
        Etapa(4, "aprovado", "Aprovado", "d4", "pendente"),
    ]
    usar_integracao(IntegracaoFalsa(etapas=novas))
    h = cabecalho_de(CLIENTE_A)
    corpo = cliente_http.get(f"/api/v1/pedidos/{PEDIDO_A}/status", headers=h).json()
    assert corpo["etapa_atual"]["ordem"] == 2
    assert corpo["consultado_em"] == "2026-10-21T10:00:00-03:00"
    assert corpo["dado_desatualizado"] is False

    # Se a integração cair depois, a consulta salva é devolvida como desatualizada.
    usar_integracao(IntegracaoFalsa(indisponivel=True))
    corpo = cliente_http.get(f"/api/v1/pedidos/{PEDIDO_A}/status", headers=h).json()
    assert corpo["etapa_atual"]["ordem"] == 2
    assert corpo["consultado_em"] == "2026-10-21T10:00:00-03:00"
    assert corpo["dado_desatualizado"] is True


def test_status_integracao_sem_novidade_usa_ultima_consulta(cliente_http):
    usar_integracao(IntegracaoFalsa(etapas=None))
    corpo = cliente_http.get(f"/api/v1/pedidos/{PEDIDO_A}/status", headers=cabecalho_de(CLIENTE_A)).json()
    assert corpo["consultado_em"] == "2026-08-23T14:30:00-03:00"
    assert corpo["dado_desatualizado"] is False


def test_status_indisponivel_com_cache_200_desatualizado(cliente_http):
    usar_integracao(IntegracaoFalsa(indisponivel=True))
    r = cliente_http.get(f"/api/v1/pedidos/{PEDIDO_A}/status", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 200
    assert r.json()["dado_desatualizado"] is True
    assert r.json()["consultado_em"] == "2026-08-23T14:30:00-03:00"


def test_status_indisponivel_sem_cache_503(cliente_http):
    from app.core.estado import repositorios
    repositorios.pedidos.obter(PEDIDO_A).consultado_em = None
    usar_integracao(IntegracaoFalsa(indisponivel=True))
    r = cliente_http.get(f"/api/v1/pedidos/{PEDIDO_A}/status", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 503
    assert r.json()["erro"]["codigo"] == "INTEGRACAO_INDISPONIVEL"


def test_status_erro_inesperado_da_integracao_com_cache_200_desatualizado(cliente_http):
    usar_integracao(IntegracaoFalsa(erro=RuntimeError("timeout")))
    r = cliente_http.get(f"/api/v1/pedidos/{PEDIDO_A}/status", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 200
    assert r.json()["dado_desatualizado"] is True


def test_status_erro_inesperado_da_integracao_sem_cache_503(cliente_http):
    from app.core.estado import repositorios
    repositorios.pedidos.obter(PEDIDO_A).consultado_em = None
    usar_integracao(IntegracaoFalsa(erro=RuntimeError("timeout")))
    r = cliente_http.get(f"/api/v1/pedidos/{PEDIDO_A}/status", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 503
    assert r.json()["erro"]["codigo"] == "INTEGRACAO_INDISPONIVEL"


def test_status_sem_consulta_guardada_e_integracao_sem_dados_503(cliente_http):
    from app.core.estado import repositorios
    repositorios.pedidos.obter(PEDIDO_A).consultado_em = None
    usar_integracao(IntegracaoFalsa(etapas=None))
    r = cliente_http.get(f"/api/v1/pedidos/{PEDIDO_A}/status", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 503
    assert r.json()["erro"]["codigo"] == "INTEGRACAO_INDISPONIVEL"


def _status_com(cliente_http, cabecalho):
    return cliente_http.get("/api/v1/pedidos", headers=cabecalho)


def test_cabecalho_com_esquema_basic_401(cliente_http):
    r = _status_com(cliente_http, {"Authorization": "Basic abc"})
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_INVALIDO"


def test_bearer_vazio_401(cliente_http):
    r = _status_com(cliente_http, {"Authorization": "Bearer "})
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_INVALIDO"


def _claims(**extra):
    agora = int(relogio.agora().timestamp())
    return {"sub": CLIENTE_A, "iat": agora, "exp": agora + 3600, **extra}


def test_token_assinado_com_outro_segredo_401(cliente_http):
    token = jwt.encode(_claims(), "outro-segredo-qualquer-com-tamanho-ok", algorithm="HS256")
    r = _status_com(cliente_http, {"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_INVALIDO"


def test_token_com_alg_none_401(cliente_http):
    token = jwt.encode(_claims(), key=None, algorithm="none")
    r = _status_com(cliente_http, {"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_INVALIDO"


def test_token_sem_sub_401(cliente_http):
    from app.core import config
    claims = _claims()
    del claims["sub"]
    token = jwt.encode(claims, config.JWT_SEGREDO, algorithm=config.JWT_ALGORITMO)
    r = _status_com(cliente_http, {"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_INVALIDO"
