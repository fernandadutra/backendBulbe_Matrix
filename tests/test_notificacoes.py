from datetime import datetime

from app.core import relogio
from app.core.estado import repositorios
from app.main import app
from app.models.pedido import Etapa
from app.services import notificacao_service
from app.services.integracao_cemig import IntegracaoIndisponivel, obter_integracao_cemig
from tests.conftest import CLIENTE_A, CLIENTE_B, PEDIDO_A, PEDIDO_B, cabecalho_de

URL = "/api/v1/notificacoes"
PDF = b"%PDF-1.7 conteudo da fatura"


class IntegracaoFalsa:
    def __init__(self, etapas=None, indisponivel=False):
        self.etapas, self.indisponivel = etapas, indisponivel

    def consultar(self, pedido):
        if self.indisponivel:
            raise IntegracaoIndisponivel()
        return self.etapas


def _usar_integracao(integracao):
    app.dependency_overrides[obter_integracao_cemig] = lambda: integracao


def _etapas_na_segunda():
    inicio = datetime(2026, 10, 1, tzinfo=relogio.FUSO)
    return [
        Etapa(1, "analise_bulbe", "Em análise pela Bulbe", "d1", "concluida", concluida_em=inicio),
        Etapa(2, "enviado_cemig", "Enviado para Cemig", "d2", "em_andamento", iniciada_em=inicio),
        Etapa(3, "analise_cemig", "Em análise pela Cemig", "d3", "pendente"),
        Etapa(4, "aprovado", "Aprovado", "d4", "pendente"),
    ]


def _listar(cliente_http, cliente_id=CLIENTE_A, **params):
    return cliente_http.get(URL, params=params, headers=cabecalho_de(cliente_id))


def _marcar(cliente_http, notificacao_id, corpo, cliente_id=CLIENTE_A):
    return cliente_http.patch(f"{URL}/{notificacao_id}", json=corpo, headers=cabecalho_de(cliente_id))


def _status(cliente_http, pedido_id=PEDIDO_A, cliente_id=CLIENTE_A):
    return cliente_http.get(f"/api/v1/pedidos/{pedido_id}/status", headers=cabecalho_de(cliente_id))


def _concluir_adesao(cliente_http, whatsapp, email="paulo@exemplo.com.br"):
    corpo = {"nome": "Paulo Andrade", "email": email, "whatsapp": whatsapp, "aceite_comunicacoes": True}
    r = cliente_http.post("/api/v1/interessados", json=corpo).json()
    cab = {"Authorization": f"Bearer {r['token_fluxo']}"}
    adesao_id = cliente_http.post("/api/v1/adesoes", json={"interessado_id": r["id"]}, headers=cab).json()["id"]
    negocio = {
        "numero_instalacao": "3013588579", "distribuidora": "CEMIG", "titular_nome": "Paulo Andrade",
        "titular_documento": "390.533.447-05", "cep": "30140-071", "classe_consumo": "residencial",
    }
    cliente_http.patch(f"/api/v1/adesoes/{adesao_id}", json={"etapa": "negocio", "dados": negocio}, headers=cab)
    cliente_http.post(
        f"/api/v1/adesoes/{adesao_id}/anexos", data={"tipo": "fatura_energia"},
        files={"arquivo": ("fatura.pdf", PDF, "application/pdf")}, headers=cab,
    )
    aceite = {
        "aceite_termo_adesao": True, "aceite_politica_privacidade": True,
        "versao_documentos": "2026-07-01", "aceito_em": "2026-10-21T10:00:00-03:00",
    }
    cliente_http.post(f"/api/v1/adesoes/{adesao_id}/aceites", json=aceite, headers=cab)
    corpo = {"senha": "senha-segura-1", "aceite_compartilhamento_dados": True}
    return cliente_http.post(f"/api/v1/adesoes/{adesao_id}/submissao", json=corpo, headers=cab)


# GET /notificacoes


def test_ana_recebe_o_formato_do_contrato(cliente_http):
    r = _listar(cliente_http)
    assert r.status_code == 200
    assert r.json() == {
        "dados": [{
            "id": "not_c410aa7b", "tipo": "pedido_criado", "titulo": "Recebemos seu pedido",
            "mensagem": notificacao_service.MENSAGEM_PEDIDO_CRIADO, "lida": False,
            "criada_em": "2026-06-02T09:14:00-03:00", "referencia": {"tipo": "pedido", "id": PEDIDO_A},
        }],
        "nao_lidas": 1, "pagina": 1, "limite": 20, "total": 1,
    }


def test_bruno_recebe_duas_lidas_mais_recente_primeiro(cliente_http):
    corpo = _listar(cliente_http, CLIENTE_B).json()
    assert [n["tipo"] for n in corpo["dados"]] == ["fatura_emitida", "mudanca_etapa_pedido"]
    assert all(n["lida"] for n in corpo["dados"])
    assert (corpo["nao_lidas"], corpo["total"]) == (0, 2)
    assert corpo["dados"][0]["referencia"] == {"tipo": "fatura", "id": "fat_2c9f5a03"}


def test_texto_da_semente_e_igual_ao_que_o_service_gera(cliente_http):
    semeada = _listar(cliente_http, CLIENTE_B).json()["dados"][1]
    gerada = notificacao_service.notificar(
        CLIENTE_B, "mudanca_etapa_pedido", "pedido", PEDIDO_B, repositorios.notificacoes, "Aprovado"
    )
    assert (semeada["titulo"], semeada["mensagem"]) == (gerada.titulo, gerada.mensagem)
    ana = _listar(cliente_http).json()["dados"][0]
    pedido_criado = notificacao_service.notificar(
        CLIENTE_A, "pedido_criado", "pedido", PEDIDO_A, repositorios.notificacoes
    )
    assert (ana["titulo"], ana["mensagem"]) == (pedido_criado.titulo, pedido_criado.mensagem)


def test_apenas_nao_lidas_do_bruno_vem_vazio(cliente_http):
    corpo = _listar(cliente_http, CLIENTE_B, apenas_nao_lidas="true").json()
    assert (corpo["dados"], corpo["total"], corpo["nao_lidas"]) == ([], 0, 0)


def test_apenas_nao_lidas_da_ana_traz_a_notificacao(cliente_http):
    corpo = _listar(cliente_http, apenas_nao_lidas="true").json()
    assert [n["id"] for n in corpo["dados"]] == ["not_c410aa7b"]


def test_apenas_nao_lidas_invalido_400(cliente_http):
    r = _listar(cliente_http, apenas_nao_lidas="abc")
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "PARAMETRO_INVALIDO"
    assert r.json()["erro"]["detalhes"] == [{"campo": "apenas_nao_lidas", "problema": "deve ser true ou false"}]


def test_paginacao_mantem_o_total_de_nao_lidas(cliente_http):
    _marcar(cliente_http, "not_5a1c9e07", {"lida": False}, CLIENTE_B)
    corpo = _listar(cliente_http, CLIENTE_B, limite=1).json()
    assert (len(corpo["dados"]), corpo["total"], corpo["nao_lidas"]) == (1, 2, 1)


def test_ana_nao_ve_notificacoes_do_bruno(cliente_http):
    ids = {n["id"] for n in _listar(cliente_http).json()["dados"]}
    assert ids.isdisjoint({"not_5a1c9e07", "not_7d3b2f18"})


def test_lista_sem_token_401(cliente_http):
    r = cliente_http.get(URL)
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_AUSENTE"


# PATCH /notificacoes/{id}


def test_marcar_como_lida_e_desfazer(cliente_http):
    r = _marcar(cliente_http, "not_c410aa7b", {"lida": True})
    assert r.status_code == 200
    assert r.json()["lida"] is True and r.json()["id"] == "not_c410aa7b"
    assert _listar(cliente_http).json()["nao_lidas"] == 0
    assert _marcar(cliente_http, "not_c410aa7b", {"lida": False}).json()["lida"] is False
    assert _listar(cliente_http).json()["nao_lidas"] == 1


def test_corpo_sem_lida_400(cliente_http):
    r = _marcar(cliente_http, "not_c410aa7b", {})
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "CORPO_INVALIDO"
    assert r.json()["erro"]["detalhes"] == [{"campo": "lida", "problema": "campo obrigatório"}]


def test_lida_com_tipo_errado_400(cliente_http):
    for valor in ("sim", 1):
        r = _marcar(cliente_http, "not_c410aa7b", {"lida": valor})
        assert r.status_code == 400
        assert r.json()["erro"]["codigo"] == "CORPO_INVALIDO"
        assert r.json()["erro"]["detalhes"] == [{"campo": "lida", "problema": "deve ser true ou false"}]


def test_notificacao_de_outro_cliente_404(cliente_http):
    r = _marcar(cliente_http, "not_5a1c9e07", {"lida": False})
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "NOTIFICACAO_NAO_ENCONTRADA"
    assert _listar(cliente_http, CLIENTE_B).json()["nao_lidas"] == 0


def test_notificacao_inexistente_404(cliente_http):
    r = _marcar(cliente_http, "not_00000000", {"lida": True})
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "NOTIFICACAO_NAO_ENCONTRADA"


def test_patch_sem_token_401(cliente_http):
    r = cliente_http.patch(f"{URL}/not_c410aa7b", json={"lida": True})
    assert r.status_code == 401


# Eventos


def test_mudanca_de_etapa_gera_notificacao_sem_duplicar(cliente_http):
    _usar_integracao(IntegracaoFalsa(etapas=_etapas_na_segunda()))
    assert _status(cliente_http).status_code == 200
    corpo = _listar(cliente_http).json()
    assert (corpo["total"], corpo["nao_lidas"]) == (2, 2)
    nova = corpo["dados"][0]
    assert nova["tipo"] == "mudanca_etapa_pedido"
    assert nova["titulo"] == "Seu pedido avançou de etapa"
    assert "Enviado para Cemig" in nova["mensagem"]
    assert nova["referencia"] == {"tipo": "pedido", "id": PEDIDO_A}
    assert nova["criada_em"] == "2026-10-21T10:00:00-03:00"
    _status(cliente_http)
    assert _listar(cliente_http).json()["total"] == 2


def test_integracao_indisponivel_nao_gera_notificacao(cliente_http):
    _usar_integracao(IntegracaoFalsa(indisponivel=True))
    r = _status(cliente_http)
    assert r.status_code == 200 and r.json()["dado_desatualizado"] is True
    assert _listar(cliente_http).json()["total"] == 1


def test_integracao_sem_etapas_nao_gera_notificacao(cliente_http):
    _usar_integracao(IntegracaoFalsa(etapas=None))
    _status(cliente_http)
    assert _listar(cliente_http).json()["total"] == 1


def test_submissao_cria_pedido_criado_para_o_cliente_novo(cliente_http):
    r = _concluir_adesao(cliente_http, "+5531955554444")
    assert r.status_code == 201
    corpo = _listar(cliente_http, r.json()["cliente_id"]).json()
    assert (corpo["total"], corpo["nao_lidas"]) == (1, 1)
    assert corpo["dados"][0]["tipo"] == "pedido_criado"
    assert corpo["dados"][0]["referencia"] == {"tipo": "pedido", "id": r.json()["pedido_id"]}


def test_indicacao_convertida_notifica_quem_indicou(cliente_http):
    # Carla Lima é a indicação pendente da Ana na semente.
    assert _concluir_adesao(cliente_http, "+5531977773333").status_code == 201
    corpo = _listar(cliente_http).json()
    assert (corpo["total"], corpo["nao_lidas"]) == (2, 2)
    assert corpo["dados"][0]["tipo"] == "indicacao_convertida"
    assert corpo["dados"][0]["referencia"]["tipo"] == "indicacao"
    assert corpo["dados"][0]["referencia"]["id"] == "ind_a12"


def test_submissao_sem_indicacao_nao_notifica_ninguem(cliente_http):
    _concluir_adesao(cliente_http, "+5531955554444")
    assert _listar(cliente_http).json()["total"] == 1
    assert _listar(cliente_http, CLIENTE_B).json()["total"] == 2
