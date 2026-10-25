URL = "/api/v1/ajuda/dicas"


def test_dica_de_status_do_pedido_completa(cliente_http):
    r = cliente_http.get(f"{URL}?tela=status-pedido")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["tela"] == "status-pedido"
    assert corpo["atualizado_em"] == "2026-08-20T11:00:00-03:00"
    assert len(corpo["dicas"]) == 1
    dica = corpo["dicas"][0]
    assert dica["elemento"] == "titulo-status"
    assert dica["titulo"] == "Como funciona o acompanhamento"
    assert dica["rotulo_acessivel"] == "Entender as etapas do pedido"
    paragrafo, lista, prazo = dica["blocos"]
    assert paragrafo == {
        "tipo": "paragrafo", "titulo": None,
        "texto": "Seu pedido passa por 4 etapas até a liberação dos benefícios Bulbe.",
    }
    assert lista["tipo"] == "lista" and lista["ordenada"] is False
    assert [i["titulo"] for i in lista["itens"]] == [
        "Em análise pela Bulbe", "Enviado para a Cemig", "Em análise pela Cemig", "Aprovado",
    ]
    assert lista["itens"][1]["texto"] == "Depois da primeira análise, o pedido é enviado para a Cemig."
    assert prazo["titulo"] == "Prazo do processo"
    assert prazo["texto"].startswith("O processo pode levar até 90 dias.")


def test_dica_do_simulador_tem_lista_ordenada(cliente_http):
    corpo = cliente_http.get(f"{URL}?tela=simular-desconto").json()
    blocos = corpo["dicas"][0]["blocos"]
    listas = [b for b in blocos if b["tipo"] == "lista"]
    assert len(listas) == 1 and listas[0]["ordenada"] is True
    assert len(listas[0]["itens"]) == 2
    assert all(i["titulo"] is None for i in listas[0]["itens"])
    assert corpo["dicas"][0]["elemento"] == "titulo-simulacao"


def test_filtro_por_elemento(cliente_http):
    r = cliente_http.get(f"{URL}?tela=status-pedido&elemento=titulo-status")
    assert len(r.json()["dicas"]) == 1
    r = cliente_http.get(f"{URL}?tela=status-pedido&elemento=outro")
    assert r.status_code == 200
    assert r.json()["dicas"] == [] and r.json()["atualizado_em"] is None


def test_tela_sem_dica_200_vazio(cliente_http):
    r = cliente_http.get(f"{URL}?tela=beneficios")
    assert r.status_code == 200
    assert r.json() == {"tela": "beneficios", "atualizado_em": None, "dicas": []}


def test_sem_tela_400(cliente_http):
    r = cliente_http.get(URL)
    assert r.status_code == 400
    erro = r.json()["erro"]
    assert erro["codigo"] == "PARAMETRO_INVALIDO"
    assert erro["detalhes"] == [{"campo": "tela", "problema": "campo obrigatório"}]


def test_tela_desconhecida_400(cliente_http):
    r = cliente_http.get(f"{URL}?tela=configuracoes")
    assert r.status_code == 400
    assert r.json()["erro"]["detalhes"][0] == {"campo": "tela", "problema": "tela desconhecida"}


def test_cache_control_presente(cliente_http):
    r = cliente_http.get(f"{URL}?tela=status-pedido")
    assert r.headers["cache-control"] == "public, max-age=300"
    assert cliente_http.get(f"{URL}?tela=beneficios").headers["cache-control"] == "public, max-age=300"


def test_funciona_sem_token(cliente_http):
    assert "authorization" not in cliente_http.headers
    assert cliente_http.get(f"{URL}?tela=status-pedido").status_code == 200
