from app.core.estado import repositorios
from app.services import indicacao_service
from tests.conftest import AGORA_CONGELADA, CLIENTE_A, CLIENTE_B, cabecalho_de

URL = "/api/v1/indicacoes"
PDF = b"%PDF-1.7 conteudo da fatura"


def _indicar(cliente_http, cliente_id=CLIENTE_B, nome="Paulo Andrade", whatsapp="+5531955554444"):
    return cliente_http.post(URL, json={"nome": nome, "whatsapp": whatsapp}, headers=cabecalho_de(cliente_id))


def _painel(cliente_http, cliente_id):
    return cliente_http.get(URL, headers=cabecalho_de(cliente_id)).json()


def _indicar_varias(cliente_http, quantidade, cliente_id=CLIENTE_B):
    for n in range(quantidade):
        assert _indicar(cliente_http, cliente_id, f"Pessoa {n}", f"+55319444400{n:02d}").status_code == 201


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


# GET /indicacoes


def test_ana_recebe_o_formato_do_contrato(cliente_http):
    r = cliente_http.get(URL, headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 200
    c = r.json()
    assert c["codigo"] == "ANA50"
    assert c["url_compartilhamento"] == "https://bulbe.com.br/indique/ANA50"
    assert c["recompensa_por_indicacao_centavos"] == 5000
    assert (c["total_indicacoes"], c["indicacoes_convertidas"], c["credito_acumulado_centavos"]) == (3, 2, 10000)
    assert c["faixa_atual"] == {
        "chave": "economia_com_indicacoes",
        "nome": "Economia + indicações",
        "proxima_faixa": "top_indicador",
        "indicacoes_para_proxima_faixa": 7,
    }
    assert [i["situacao"] for i in c["indicacoes"]] == ["pendente", "convertida", "convertida"]


def test_nomes_chegam_ofuscados(cliente_http):
    itens = _painel(cliente_http, CLIENTE_A)["indicacoes"]
    assert {i["nome_ofuscado"] for i in itens} == {"Jo** S****", "Ma**** P******", "Ca*** L***"}
    assert set(itens[0]) == {"id", "nome_ofuscado", "situacao", "indicada_em"}
    assert "Silva" not in str(itens) and "Pereira" not in str(itens)


def test_bruno_comeca_sem_indicacoes_e_ganha_codigo(cliente_http):
    c = _painel(cliente_http, CLIENTE_B)
    assert c["codigo"] == "BRUNO50"
    assert (c["total_indicacoes"], c["credito_acumulado_centavos"], c["indicacoes"]) == (0, 0, [])
    assert c["faixa_atual"]["chave"] == "comece_a_indicar"
    assert c["faixa_atual"]["proxima_faixa"] == "primeira_indicacao"
    assert c["faixa_atual"]["indicacoes_para_proxima_faixa"] == 1
    assert _painel(cliente_http, CLIENTE_B)["codigo"] == "BRUNO50"


def test_codigo_em_colisao_ganha_sufixo(cliente_http):
    repositorios.indicacoes.salvar_codigo(CLIENTE_A, "BRUNO50")
    codigo = _painel(cliente_http, CLIENTE_B)["codigo"]
    assert codigo != "BRUNO50" and codigo.startswith("BRUNO50") and len(codigo) == 9


def test_codigo_sem_acento():
    assert indicacao_service._codigo_base("Érica Souza") == "ERICA50"


def test_listar_sem_token_401(cliente_http):
    r = cliente_http.get(URL)
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_AUSENTE"


def test_cada_cliente_ve_so_as_proprias_indicacoes(cliente_http):
    _indicar(cliente_http)
    assert _painel(cliente_http, CLIENTE_A)["total_indicacoes"] == 3
    assert _painel(cliente_http, CLIENTE_B)["total_indicacoes"] == 1


# POST /indicacoes


def test_indicar_201_com_whatsapp_mascarado(cliente_http):
    r = _indicar(cliente_http, whatsapp="+55 (31) 98877-6655", nome="  João Silva ")
    assert r.status_code == 201
    c = r.json()
    assert c["id"].startswith("ind_")
    assert c["nome_ofuscado"] == "Jo** S****"
    assert c["situacao"] == "pendente"
    assert c["indicada_em"] == AGORA_CONGELADA.date().isoformat()
    assert repositorios.indicacoes.por_whatsapp("+5531988776655") is not None


def test_indicar_aparece_no_painel(cliente_http):
    _indicar(cliente_http)
    c = _painel(cliente_http, CLIENTE_B)
    assert c["total_indicacoes"] == 1
    assert c["faixa_atual"]["chave"] == "primeira_indicacao"
    assert c["credito_acumulado_centavos"] == 0


def test_indicar_corpo_invalido_400(cliente_http):
    for corpo in ({"nome": "  ", "whatsapp": "+5531955554444"}, {"nome": "Paulo", "whatsapp": "31955554444"}, {"nome": "Paulo"}):
        r = cliente_http.post(URL, json=corpo, headers=cabecalho_de(CLIENTE_B))
        assert r.status_code == 400
        assert r.json()["erro"]["codigo"] == "CORPO_INVALIDO"


def test_indicar_detalha_os_campos_invalidos(cliente_http):
    r = _indicar(cliente_http, nome="", whatsapp="123")
    assert {d["campo"] for d in r.json()["erro"]["detalhes"]} == {"nome", "whatsapp"}


def test_indicar_sem_token_401(cliente_http):
    assert cliente_http.post(URL, json={"nome": "Paulo", "whatsapp": "+5531955554444"}).status_code == 401


def test_contato_ja_indicado_409_inclusive_por_outro_cliente(cliente_http):
    assert _indicar(cliente_http).status_code == 201
    for cliente_id in (CLIENTE_B, CLIENTE_A):
        r = _indicar(cliente_http, cliente_id, whatsapp="+55 31 95555-4444")
        assert r.status_code == 409
        assert r.json()["erro"]["codigo"] == "CONTATO_JA_INDICADO"


def test_contato_que_ja_e_cliente_409(cliente_http):
    for whatsapp in ("+5531988887777", "+5531999998888"):
        r = _indicar(cliente_http, CLIENTE_B, whatsapp=whatsapp)
        assert r.status_code == 409
        assert r.json()["erro"]["codigo"] == "CONTATO_JA_CLIENTE"


def test_limite_de_dez_pendentes_422(cliente_http):
    _indicar_varias(cliente_http, 10)
    r = _indicar(cliente_http)
    assert r.status_code == 422
    assert r.json()["erro"]["codigo"] == "LIMITE_DE_INDICACOES"


def test_faixa_top_com_dez_indicacoes(cliente_http):
    _indicar_varias(cliente_http, 10)
    faixa = _painel(cliente_http, CLIENTE_B)["faixa_atual"]
    assert faixa == {"chave": "top_indicador", "nome": "TOP indicador", "proxima_faixa": None, "indicacoes_para_proxima_faixa": 0}


# Regra do WhatsApp no 2.2


def test_interessado_com_whatsapp_curto_400(cliente_http):
    corpo = {"nome": "Maria", "email": "maria@exemplo.com.br", "whatsapp": "319999988", "aceite_comunicacoes": True}
    r = cliente_http.post("/api/v1/interessados", json=corpo)
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "CORPO_INVALIDO"
    assert [d["campo"] for d in r.json()["erro"]["detalhes"]] == ["whatsapp"]


def test_interessado_com_whatsapp_mascarado_e_guardado_normalizado(cliente_http):
    corpo = {"nome": "Maria", "email": "maria@exemplo.com.br", "whatsapp": "+55 (31) 99999-8888", "aceite_comunicacoes": True}
    r = cliente_http.post("/api/v1/interessados", json=corpo)
    assert r.status_code == 201
    assert repositorios.adesoes.interessado_por_email("maria@exemplo.com.br").whatsapp == "+5531999998888"


def _abrir_adesao(cliente_http):
    corpo = {"nome": "Maria", "email": "maria@exemplo.com.br", "whatsapp": "+5531999998888", "aceite_comunicacoes": True}
    r = cliente_http.post("/api/v1/interessados", json=corpo).json()
    cab = {"Authorization": f"Bearer {r['token_fluxo']}"}
    adesao_id = cliente_http.post("/api/v1/adesoes", json={"interessado_id": r["id"]}, headers=cab).json()["id"]
    return adesao_id, cab


def test_etapa_contato_com_whatsapp_curto_400(cliente_http):
    adesao_id, cab = _abrir_adesao(cliente_http)
    dados = {"nome": "Maria", "whatsapp": "319999988"}
    r = cliente_http.patch(f"/api/v1/adesoes/{adesao_id}", json={"etapa": "contato", "dados": dados}, headers=cab)
    assert r.status_code == 400
    assert [d["campo"] for d in r.json()["erro"]["detalhes"]] == ["dados.whatsapp"]
    assert repositorios.adesoes.interessado_por_email("maria@exemplo.com.br").whatsapp == "+5531999998888"


def test_etapa_contato_guarda_whatsapp_normalizado(cliente_http):
    adesao_id, cab = _abrir_adesao(cliente_http)
    dados = {"nome": "Maria", "whatsapp": "+55 (31) 97777-6666"}
    r = cliente_http.patch(f"/api/v1/adesoes/{adesao_id}", json={"etapa": "contato", "dados": dados}, headers=cab)
    assert r.status_code == 200
    assert repositorios.adesoes.interessado_por_email("maria@exemplo.com.br").whatsapp == "+5531977776666"


# Conversão na submissão da adesão


def test_submissao_converte_a_indicacao_do_mesmo_whatsapp(cliente_http):
    _indicar(cliente_http, CLIENTE_B, whatsapp="+5531955554444")
    assert _concluir_adesao(cliente_http, "+55 (31) 95555-4444").status_code == 201
    c = _painel(cliente_http, CLIENTE_B)
    assert c["indicacoes"][0]["situacao"] == "convertida"
    assert (c["indicacoes_convertidas"], c["credito_acumulado_centavos"]) == (1, 5000)


def test_submissao_sem_indicacao_nao_altera_nada(cliente_http):
    _indicar(cliente_http, CLIENTE_B, whatsapp="+5531955554444")
    assert _concluir_adesao(cliente_http, "+5531966665555").status_code == 201
    assert _painel(cliente_http, CLIENTE_B)["credito_acumulado_centavos"] == 0
    assert _painel(cliente_http, CLIENTE_A)["credito_acumulado_centavos"] == 10000
