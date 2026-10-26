from datetime import timedelta

from app.core import relogio
from app.core.estado import repositorios
from app.services import adesao_service
from tests.conftest import AGORA_CONGELADA, CLIENTE_A, EMAIL_A, cabecalho_de

PDF = b"%PDF-1.7 conteudo da fatura"
PNG = b"\x89PNG\r\n\x1a\n conteudo"
JPEG = b"\xff\xd8\xff\xe0 conteudo"
SENHA_NOVA = "senha-segura-1"


def _interessado(cliente_http, email="maria@exemplo.com.br", **extra):
    corpo = {"nome": "Maria Souza", "email": email, "whatsapp": "+5531999998888", "aceite_comunicacoes": True, **extra}
    return cliente_http.post("/api/v1/interessados", json=corpo)


def _fluxo(cliente_http, email="maria@exemplo.com.br"):
    r = _interessado(cliente_http, email).json()
    return r["id"], {"Authorization": f"Bearer {r['token_fluxo']}"}


def _abrir(cliente_http, email="maria@exemplo.com.br"):
    interessado_id, cab = _fluxo(cliente_http, email)
    r = cliente_http.post("/api/v1/adesoes", json={"interessado_id": interessado_id}, headers=cab)
    return r.json()["id"], cab


def _negocio(cliente_http, adesao_id, cab, **dados):
    base = {
        "numero_instalacao": "3013588579",
        "distribuidora": "CEMIG",
        "titular_nome": "Maria Souza",
        "titular_documento": "390.533.447-05",
        "cep": "30140-071",
        "classe_consumo": "residencial",
    }
    return cliente_http.patch(
        f"/api/v1/adesoes/{adesao_id}", json={"etapa": "negocio", "dados": {**base, **dados}}, headers=cab
    )


def _anexar(cliente_http, adesao_id, cab, conteudo=PDF, tipo="fatura_energia", nome="fatura.pdf"):
    return cliente_http.post(
        f"/api/v1/adesoes/{adesao_id}/anexos",
        data={"tipo": tipo},
        files={"arquivo": (nome, conteudo, "application/pdf")},
        headers=cab,
    )


def _aceitar(cliente_http, adesao_id, cab, **extra):
    corpo = {
        "aceite_termo_adesao": True,
        "aceite_politica_privacidade": True,
        "versao_documentos": "2026-07-01",
        "aceito_em": "2026-10-21T10:00:00-03:00",
        **extra,
    }
    return cliente_http.post(f"/api/v1/adesoes/{adesao_id}/aceites", json=corpo, headers=cab)


def _submeter(cliente_http, adesao_id, cab, senha=SENHA_NOVA, compartilhamento=True):
    corpo = {"senha": senha, "aceite_compartilhamento_dados": compartilhamento}
    return cliente_http.post(f"/api/v1/adesoes/{adesao_id}/submissao", json=corpo, headers=cab)


def _adesao_completa(cliente_http, email="maria@exemplo.com.br", **negocio):
    adesao_id, cab = _abrir(cliente_http, email)
    _negocio(cliente_http, adesao_id, cab, **negocio)
    _anexar(cliente_http, adesao_id, cab)
    _aceitar(cliente_http, adesao_id, cab)
    return adesao_id, cab


# Interessados


def test_registrar_interessado_201_no_formato_do_contrato(cliente_http):
    r = _interessado(cliente_http)
    assert r.status_code == 201
    c = r.json()
    assert c["id"].startswith("int_")
    assert c["situacao"] == "novo"
    assert c["token_fluxo"].startswith("tfl_")
    assert c["expira_em"] == (AGORA_CONGELADA + timedelta(hours=24)).isoformat()


def test_interessado_com_simulacao_existente(cliente_http):
    simulacao = cliente_http.post(
        "/api/v1/simulacoes", json={"valor_fatura_centavos": 35000}, headers=cabecalho_de(CLIENTE_A)
    ).json()
    assert _interessado(cliente_http, simulacao_id=simulacao["id"]).status_code == 201


def test_interessado_com_simulacao_inexistente_400(cliente_http):
    r = _interessado(cliente_http, simulacao_id="sim_00000000")
    assert r.status_code == 400
    assert r.json()["erro"]["detalhes"][0]["campo"] == "simulacao_id"


def test_interessado_com_email_invalido_400(cliente_http):
    r = _interessado(cliente_http, email="sem-arroba")
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "CORPO_INVALIDO"


def test_interessado_sem_campo_obrigatorio_400(cliente_http):
    r = cliente_http.post("/api/v1/interessados", json={"nome": "Maria", "email": "m@exemplo.com.br"})
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "CORPO_INVALIDO"


def test_interessado_com_email_repetido_409(cliente_http):
    _interessado(cliente_http)
    r = _interessado(cliente_http, email="MARIA@exemplo.com.br")
    assert r.status_code == 409
    assert r.json()["erro"]["codigo"] == "EMAIL_JA_CADASTRADO"


def test_interessado_com_email_de_cliente_409(cliente_http):
    assert _interessado(cliente_http, email=EMAIL_A).status_code == 409


def test_token_fluxo_guardado_so_como_hash(cliente_http):
    token = _interessado(cliente_http).json()["token_fluxo"]
    guardado = next(iter(repositorios.adesoes._interessados.values()))
    assert token not in vars(guardado).values()


# Token de fluxo


def test_adesao_sem_token_401(cliente_http):
    r = cliente_http.post("/api/v1/adesoes", json={"interessado_id": "int_x"})
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_AUSENTE"


def test_token_de_fluxo_invalido_401(cliente_http):
    r = cliente_http.post(
        "/api/v1/adesoes", json={"interessado_id": "int_x"}, headers={"Authorization": "Bearer tfl_falso"}
    )
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_INVALIDO"


def test_token_de_fluxo_expirado_401(cliente_http):
    interessado_id, cab = _fluxo(cliente_http)
    futuro = AGORA_CONGELADA + timedelta(hours=25)
    relogio.definir_relogio(lambda: futuro)
    r = cliente_http.post("/api/v1/adesoes", json={"interessado_id": interessado_id}, headers=cab)
    assert r.status_code == 401


def test_jwt_de_cliente_nao_abre_adesao_401(cliente_http):
    r = cliente_http.post("/api/v1/adesoes", json={"interessado_id": "int_x"}, headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 401


def test_token_de_fluxo_nao_vale_nas_rotas_de_cliente_401(cliente_http):
    _, cab = _fluxo(cliente_http)
    assert cliente_http.get("/api/v1/pedidos", headers=cab).status_code == 401


def test_adesao_de_outro_interessado_404(cliente_http):
    adesao_id, _ = _abrir(cliente_http)
    _, cab_outro = _fluxo(cliente_http, "outro@exemplo.com.br")
    r = _negocio(cliente_http, adesao_id, cab_outro)
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "ADESAO_NAO_ENCONTRADA"


# Adesão e etapas


def test_abrir_adesao_201_com_contato_concluido(cliente_http):
    interessado_id, cab = _fluxo(cliente_http)
    r = cliente_http.post("/api/v1/adesoes", json={"interessado_id": interessado_id}, headers=cab)
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["id"].startswith("ade_")
    assert {k: v for k, v in corpo.items() if k != "id"} == {
        "situacao": "em_preenchimento",
        "etapa_atual": "contato",
        "etapas_concluidas": ["contato"],
        "etapas_pendentes": ["negocio", "termos", "confirmacao"],
    }


def test_abrir_de_novo_devolve_a_mesma_adesao(cliente_http):
    interessado_id, cab = _fluxo(cliente_http)
    corpo = {"interessado_id": interessado_id}
    primeira = cliente_http.post("/api/v1/adesoes", json=corpo, headers=cab).json()
    segunda = cliente_http.post("/api/v1/adesoes", json=corpo, headers=cab).json()
    assert primeira["id"] == segunda["id"]


def test_abrir_com_outro_interessado_404(cliente_http):
    outro_id, _ = _fluxo(cliente_http, "outro@exemplo.com.br")
    _, cab = _fluxo(cliente_http)
    r = cliente_http.post("/api/v1/adesoes", json={"interessado_id": outro_id}, headers=cab)
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "INTERESSADO_NAO_ENCONTRADO"


def test_patch_negocio_200_marca_etapa_concluida(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = _negocio(cliente_http, adesao_id, cab)
    assert r.status_code == 200
    assert r.json()["etapas_concluidas"] == ["contato", "negocio"]
    assert r.json()["etapa_atual"] == "negocio"


def test_distribuidora_diferente_de_cemig_422(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = _negocio(cliente_http, adesao_id, cab, distribuidora="Enel")
    assert r.status_code == 422
    assert r.json()["erro"]["codigo"] == "DISTRIBUIDORA_NAO_ATENDIDA"


def test_instalacao_com_9_digitos_422(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = _negocio(cliente_http, adesao_id, cab, numero_instalacao="301358857")
    assert r.status_code == 422
    assert r.json()["erro"]["codigo"] == "INSTALACAO_INVALIDA"


def test_cep_invalido_400(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = _negocio(cliente_http, adesao_id, cab, cep="123")
    assert r.status_code == 400
    assert r.json()["erro"]["detalhes"][0]["campo"] == "dados.cep"


def test_documento_e_classe_invalidos_400(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = _negocio(cliente_http, adesao_id, cab, titular_documento="123", classe_consumo="espacial")
    assert r.status_code == 400
    assert len(r.json()["erro"]["detalhes"]) == 2


def test_negocio_sem_campo_400(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = cliente_http.patch(
        f"/api/v1/adesoes/{adesao_id}", json={"etapa": "negocio", "dados": {"cep": "30140071"}}, headers=cab
    )
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "CORPO_INVALIDO"


def test_etapa_desconhecida_400(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = cliente_http.patch(f"/api/v1/adesoes/{adesao_id}", json={"etapa": "outra", "dados": {}}, headers=cab)
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "CORPO_INVALIDO"


def test_etapa_termos_via_patch_400(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = cliente_http.patch(f"/api/v1/adesoes/{adesao_id}", json={"etapa": "termos", "dados": {}}, headers=cab)
    assert r.status_code == 400
    assert "/aceites" in r.json()["erro"]["detalhes"][0]["problema"]


def test_patch_contato_atualiza_o_nome(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    dados = {"nome": "Maria da Silva", "whatsapp": "+5531977776666"}
    r = cliente_http.patch(f"/api/v1/adesoes/{adesao_id}", json={"etapa": "contato", "dados": dados}, headers=cab)
    assert r.status_code == 200
    interessado = next(iter(repositorios.adesoes._interessados.values()))
    assert (interessado.nome, interessado.whatsapp) == ("Maria da Silva", "+5531977776666")


def test_adesao_inexistente_404(cliente_http):
    _, cab = _fluxo(cliente_http)
    assert _negocio(cliente_http, "ade_00000000", cab).status_code == 404


# Anexo


def test_anexo_pdf_201_no_formato_do_contrato(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = _anexar(cliente_http, adesao_id, cab)
    assert r.status_code == 201
    c = r.json()
    assert c["id"].startswith("anx_")
    assert (c["tipo"], c["nome_arquivo"], c["tamanho_bytes"], c["situacao"]) == (
        "fatura_energia",
        "fatura.pdf",
        len(PDF),
        "recebido",
    )
    assert c["dados_extraidos"] is None
    assert "conteudo" not in r.text


def test_anexo_png_e_jpeg_201(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    assert _anexar(cliente_http, adesao_id, cab, PNG, nome="fatura.png").status_code == 201
    assert _anexar(cliente_http, adesao_id, cab, JPEG, nome="fatura.jpg").status_code == 201


def test_anexo_pdf_com_bytes_de_texto_415(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = _anexar(cliente_http, adesao_id, cab, b"isto e apenas texto")
    assert r.status_code == 415
    assert r.json()["erro"]["codigo"] == "FORMATO_NAO_SUPORTADO"


def test_anexo_vazio_422(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = _anexar(cliente_http, adesao_id, cab, b"")
    assert r.status_code == 422
    assert r.json()["erro"]["codigo"] == "ARQUIVO_ILEGIVEL"


def test_anexo_acima_do_limite_413(cliente_http, monkeypatch):
    monkeypatch.setattr(adesao_service, "TAMANHO_MAXIMO_ANEXO_BYTES", 100)
    adesao_id, cab = _abrir(cliente_http)
    assert _anexar(cliente_http, adesao_id, cab, PDF + b"x" * 100).status_code == 413
    assert _anexar(cliente_http, adesao_id, cab, PDF.ljust(100, b"x")).status_code == 201


def test_anexo_com_tipo_errado_400(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    assert _anexar(cliente_http, adesao_id, cab, tipo="rg").status_code == 400


def test_anexo_sem_arquivo_400(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = cliente_http.post(f"/api/v1/adesoes/{adesao_id}/anexos", data={"tipo": "fatura_energia"}, headers=cab)
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "CORPO_INVALIDO"


# Aceite


def test_aceite_201_marca_termos_concluido(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = _aceitar(cliente_http, adesao_id, cab)
    assert r.status_code == 201
    assert "termos" in r.json()["etapas_concluidas"]


def test_aceite_incompleto_400(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = _aceitar(cliente_http, adesao_id, cab, aceite_politica_privacidade=False)
    assert r.status_code == 400
    assert r.json()["erro"]["detalhes"][0]["campo"] == "aceite_politica_privacidade"


def test_aceite_com_versao_antiga_422(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = _aceitar(cliente_http, adesao_id, cab, versao_documentos="2025-01-01")
    assert r.status_code == 422
    assert r.json()["erro"]["codigo"] == "VERSAO_DOCUMENTOS_DESATUALIZADA"


def test_segundo_aceite_409(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    _aceitar(cliente_http, adesao_id, cab)
    r = _aceitar(cliente_http, adesao_id, cab)
    assert r.status_code == 409
    assert r.json()["erro"]["codigo"] == "ACEITE_JA_REGISTRADO"


def test_aceite_guarda_ip_e_user_agent(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    _aceitar(cliente_http, adesao_id, {**cab, "User-Agent": "teste-agente/1.0"})
    aceite = repositorios.adesoes.obter_adesao(adesao_id).aceite
    assert aceite.user_agent == "teste-agente/1.0"
    assert aceite.ip
    assert aceite.versao_documentos == "2026-07-01"
    assert aceite.registrado_em == AGORA_CONGELADA


# Submissão


def test_submissao_201_no_formato_do_contrato(cliente_http):
    adesao_id, cab = _adesao_completa(cliente_http)
    r = _submeter(cliente_http, adesao_id, cab)
    assert r.status_code == 201
    c = r.json()
    assert c["adesao_id"] == adesao_id
    assert c["cliente_id"].startswith("cli_")
    assert c["pedido_id"].startswith("ped_")
    assert c["situacao"] == "submetida"
    assert c["prazo_estimado_dias"] == {"minimo": 90, "maximo": 120}
    assert "90 a 120 dias" in c["mensagem"]


def test_submissao_com_pendencias_422_lista_cada_uma(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    r = _submeter(cliente_http, adesao_id, cab)
    assert r.status_code == 422
    assert r.json()["erro"]["codigo"] == "SUBMISSAO_INVALIDA"
    assert [d["campo"] for d in r.json()["erro"]["detalhes"]] == ["negocio", "anexo", "termos"]


def test_submissao_sem_anexo_422(cliente_http):
    adesao_id, cab = _abrir(cliente_http)
    _negocio(cliente_http, adesao_id, cab)
    _aceitar(cliente_http, adesao_id, cab)
    r = _submeter(cliente_http, adesao_id, cab)
    assert [d["campo"] for d in r.json()["erro"]["detalhes"]] == ["anexo"]


def test_submissao_com_senha_curta_422(cliente_http):
    adesao_id, cab = _adesao_completa(cliente_http)
    r = _submeter(cliente_http, adesao_id, cab, senha="curta")
    assert r.status_code == 422
    assert r.json()["erro"]["detalhes"][0]["campo"] == "senha"


def test_submissao_sem_compartilhamento_422(cliente_http):
    adesao_id, cab = _adesao_completa(cliente_http)
    r = _submeter(cliente_http, adesao_id, cab, compartilhamento=False)
    assert r.status_code == 422
    assert r.json()["erro"]["detalhes"][0]["campo"] == "aceite_compartilhamento_dados"


def test_submissao_com_cpf_de_cliente_409(cliente_http):
    adesao_id, cab = _adesao_completa(cliente_http, titular_documento="52998224725")
    r = _submeter(cliente_http, adesao_id, cab)
    assert r.status_code == 409
    assert r.json()["erro"]["codigo"] == "CPF_JA_CADASTRADO"


def test_escritas_depois_da_submissao_409(cliente_http):
    adesao_id, cab = _adesao_completa(cliente_http)
    assert _submeter(cliente_http, adesao_id, cab).status_code == 201
    assert _submeter(cliente_http, adesao_id, cab).status_code == 409
    assert _negocio(cliente_http, adesao_id, cab).status_code == 409
    assert _anexar(cliente_http, adesao_id, cab).status_code == 409
    r = _aceitar(cliente_http, adesao_id, cab)
    assert r.status_code == 409
    assert r.json()["erro"]["codigo"] == "ADESAO_JA_SUBMETIDA"


def test_ponta_a_ponta_com_login_pedido_e_perfil(cliente_http):
    adesao_id, cab = _adesao_completa(cliente_http)
    submissao = _submeter(cliente_http, adesao_id, cab).json()
    login = cliente_http.post("/api/v1/sessoes", json={"identificador": "maria@exemplo.com.br", "senha": SENHA_NOVA})
    assert login.status_code == 201
    assert login.json()["cliente"]["id"] == submissao["cliente_id"]
    assert login.json()["cliente"]["possui_pedido_em_andamento"] is True
    jwt = {"Authorization": f"Bearer {login.json()['token_acesso']}"}
    assert [p["id"] for p in cliente_http.get("/api/v1/pedidos", headers=jwt).json()["dados"]] == [submissao["pedido_id"]]
    status = cliente_http.get(f"/api/v1/pedidos/{submissao['pedido_id']}/status", headers=jwt)
    assert status.status_code == 200
    assert status.json()["etapa_atual"]["ordem"] == 1
    assert status.json()["etapa_atual"]["situacao"] == "em_andamento"
    instalacao = cliente_http.get("/api/v1/perfil", headers=jwt).json()["instalacoes"][0]
    assert (instalacao["numero"], instalacao["principal"]) == ("3013588579", True)
    assert cliente_http.post("/api/v1/sessoes", json={"identificador": "39053344705", "senha": SENHA_NOVA}).status_code == 201


def test_titular_com_cnpj_entra_so_por_email(cliente_http):
    adesao_id, cab = _adesao_completa(cliente_http, titular_documento="11.222.333/0001-81")
    assert _submeter(cliente_http, adesao_id, cab).status_code == 201
    por_email = cliente_http.post("/api/v1/sessoes", json={"identificador": "maria@exemplo.com.br", "senha": SENHA_NOVA})
    assert por_email.status_code == 201
    por_cpf = cliente_http.post("/api/v1/sessoes", json={"identificador": "11222333000181", "senha": SENHA_NOVA})
    assert por_cpf.status_code == 401


def test_senha_do_novo_cliente_guardada_so_como_hash(cliente_http):
    adesao_id, cab = _adesao_completa(cliente_http)
    cliente_id = _submeter(cliente_http, adesao_id, cab).json()["cliente_id"]
    assert repositorios.clientes.obter(cliente_id).senha_hash != SENHA_NOVA
